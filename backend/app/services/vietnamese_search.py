"""Component 13 (TP 13): Vietnamese String Normalization & Trigram Search.

Implements:
1. norm_vi(s): casefold, đ/Đ -> d, Unicode NFD decomposition stripping Mn combining marks,
   and whitespace normalization (matching public.norm_vi(text) in PostgreSQL).
2. trigram_similarity(a, b): PostgreSQL pg_trgm-compatible 3-gram Jaccard similarity.
3. 4-tier search ranking (docs/02-architecture/database-design.md Section 3.2):
   - Tier 1: Exact match on slug, name_vi, or accented alias.
   - Tier 2: Exact match on normalized string (norm_vi(name_vi) == norm_vi(q) or normalized_alias == norm_vi(q)).
   - Tier 3: Substring or pg_trgm similarity >= threshold.
   - Tier 4: Candidate list for explicit user disambiguation (never auto-maps ambiguous queries silently).
"""

from __future__ import annotations

import re
import unicodedata
from typing import TypeVar

T = TypeVar("T")

_WHITESPACE_RE = re.compile(r"\s+")


def norm_vi(text: str) -> str:
    """Normalize Vietnamese text: lowercase, đ->d, strip NFD combining marks, collapse spaces."""
    if not text:
        return ""
    lowered = text.casefold().replace("đ", "d").replace("Đ", "d")
    decomposed = unicodedata.normalize("NFD", lowered)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    normalized = unicodedata.normalize("NFC", stripped)
    return _WHITESPACE_RE.sub(" ", normalized).strip()


def _trigrams(normalized_text: str) -> set[str]:
    """Generate PostgreSQL pg_trgm style padded trigrams for each word."""
    if not normalized_text:
        return set()
    grams: set[str] = set()
    for word in re.findall(r"[a-z0-9]+", normalized_text):
        padded = f"  {word} "
        for i in range(len(padded) - 2):
            grams.add(padded[i : i + 3])
    return grams


def trigram_similarity(a: str, b: str) -> float:
    """Compute pg_trgm-compatible trigram similarity in [0.0, 1.0]."""
    ta = _trigrams(norm_vi(a))
    tb = _trigrams(norm_vi(b))
    if not ta or not tb:
        return 0.0
    union_len = len(ta | tb)
    if union_len == 0:
        return 0.0
    return len(ta & tb) / union_len


def rank_ingredient_candidates(
    query: str,
    items: list[T],
    threshold: float = 0.30,
) -> list[tuple[T, int, float]]:
    """Rank active ingredients according to the 4-tier priority order in TP 13.

    Returns list of (item, tier, similarity_score) sorted by (tier ASC, -score DESC, slug ASC).
    """
    q_raw = query.strip().casefold()
    q_norm = norm_vi(query)
    if not q_norm:
        return []

    results: list[tuple[T, int, float]] = []
    for item in items:
        slug = getattr(item, "slug", "").casefold()
        name_vi = getattr(item, "name_vi", "")
        aliases: list[str] = list(getattr(item, "aliases", []) or [])

        name_norm = norm_vi(name_vi)
        alias_norms = [norm_vi(a) for a in aliases]

        sim_scores = [trigram_similarity(q_norm, name_norm)] + [
            trigram_similarity(q_norm, an) for an in alias_norms
        ]
        max_sim = max(sim_scores) if sim_scores else 0.0

        # Tier 1: Exact slug, exact accented name_vi, or exact accented alias
        if (
            q_raw == slug
            or q_raw == name_vi.casefold()
            or any(q_raw == a.casefold() for a in aliases)
        ):
            results.append((item, 1, 1.0))
            continue

        # Tier 2: Exact normalized match (e.g., "dau phu" -> "Đậu hũ", "ca chua" -> "Cà chua")
        if q_norm == name_norm or any(q_norm == an for an in alias_norms):
            results.append((item, 2, max(max_sim, 0.99)))
            continue

        # Tier 3: Substring match on normalized text or trigram similarity >= threshold
        has_substring = q_norm in name_norm or any(q_norm in an for an in alias_norms)
        if has_substring or max_sim >= threshold:
            score = max(max_sim, 0.50 if has_substring else max_sim)
            results.append((item, 3, round(score, 4)))

    results.sort(key=lambda entry: (entry[1], -entry[2], getattr(entry[0], "slug", "")))
    return results

