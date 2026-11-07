"""PostgreSQL database connection and repository abstraction for FoodVision AI.

Supports:
1. Supabase Transaction Pooler (port 6543, pgbouncer=true) with prepare_threshold=None.
2. Direct PostgreSQL connection (port 5432).
3. Pluggable Repository dependency injection for deterministic testing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from app.core.config import settings
from app.core.seed_fixtures import (
    build_default_seed_ingredients,
    build_default_seed_recipes,
)
from app.schemas.catalog import Ingredient, IngredientCategory, NutritionTag
from app.schemas.recipes import (
    CuisineCode,
    NutritionEvidence,
    RecipeDetail,
    RecipeIngredientView,
    RecipeStepView,
    RecipeSummary,
)
from app.services.vietnamese_search import norm_vi, rank_ingredient_candidates


def sanitize_psycopg_dsn(url: str) -> str:
    """Strip pgbouncer=true query param which psycopg does not recognize natively."""
    if not url:
        return ""
    parsed = urlparse(url)
    query_pairs = [(k, v) for k, v in parse_qsl(parsed.query) if k.lower() != "pgbouncer"]
    return urlunparse(parsed._replace(query=urlencode(query_pairs)))


def is_db_configured() -> bool:
    url = settings.database_url or settings.direct_url
    return bool(url and "[YOUR-PASSWORD]" not in url)


@dataclass
class IngredientRecord:
    id: str
    slug: str
    name_vi: str
    category: IngredientCategory
    is_active: bool = True
    fdc_id: str | None = None
    aliases: list[str] = field(default_factory=list)
    allergen_ids: list[str] = field(default_factory=list)

    def to_schema(self) -> Ingredient:
        return Ingredient(
            id=self.id,
            slug=self.slug,
            name_vi=self.name_vi,
            category=self.category,
            is_active=self.is_active,
        )


@dataclass
class RecipeIngredientRecord:
    ingredient_id: str
    name_vi: str
    category: IngredientCategory
    is_required: bool
    role: str = "essential"
    weight: float = 1.0
    grams: float | None = None
    display_quantity: str | None = None
    sort_order: int = 0

    def to_view(self) -> RecipeIngredientView:
        return RecipeIngredientView(
            ingredient_id=self.ingredient_id,
            name_vi=self.name_vi,
            category=self.category,
            is_required=self.is_required,
            display_quantity=self.display_quantity,
            sort_order=self.sort_order,
        )


@dataclass
class RecipeStepRecord:
    step_no: int
    instruction: str
    estimated_minutes: int | None = None

    def to_view(self) -> RecipeStepView:
        return RecipeStepView(
            step_no=self.step_no,
            instruction=self.instruction,
            estimated_minutes=self.estimated_minutes,
        )


@dataclass
class NutritionEvidenceRecord:
    tag_id: str
    tag_code: str
    tag_name_vi: str
    tag_description: str
    tag_is_active: bool
    source_urls: list[str]
    note: str | None = None

    def to_view(self) -> NutritionEvidence:
        return NutritionEvidence(
            tag=NutritionTag(
                id=self.tag_id,
                code=self.tag_code,
                name_vi=self.tag_name_vi,
                description=self.tag_description,
                is_active=self.tag_is_active,
            ),
            source_urls=self.source_urls,
            note=self.note,
        )


@dataclass
class RecipeRecord:
    id: str
    slug: str
    name_vi: str
    cuisine_code: CuisineCode
    prep_minutes: int
    cook_minutes: int
    status: str = "published"
    description: str | None = None
    country_code: str | None = None
    cooking_method: str | None = None
    required_equipment: list[str] = field(default_factory=list)
    base_servings: int = 2
    quality_score: float = 1.0
    cover_image_url: str | None = None
    source_name: str | None = None
    source_url: str | None = None
    content_license: str | None = None
    ingredients: list[RecipeIngredientRecord] = field(default_factory=list)
    steps: list[RecipeStepRecord] = field(default_factory=list)
    nutrition_evidence: list[NutritionEvidenceRecord] = field(default_factory=list)
    allergen_ids: list[str] = field(default_factory=list)

    @property
    def total_minutes(self) -> int:
        return self.prep_minutes + self.cook_minutes

    def to_summary(self) -> RecipeSummary:
        return RecipeSummary(
            id=self.id,
            slug=self.slug,
            name_vi=self.name_vi,
            cuisine_code=self.cuisine_code,
            prep_minutes=self.prep_minutes,
            cook_minutes=self.cook_minutes,
            total_minutes=self.total_minutes,
            cover_image_url=self.cover_image_url,
        )

    def to_detail(self) -> RecipeDetail:
        return RecipeDetail(
            id=self.id,
            slug=self.slug,
            name_vi=self.name_vi,
            cuisine_code=self.cuisine_code,
            prep_minutes=self.prep_minutes,
            cook_minutes=self.cook_minutes,
            total_minutes=self.total_minutes,
            cover_image_url=self.cover_image_url,
            description=self.description,
            country_code=self.country_code,
            ingredients=[ing.to_view() for ing in self.ingredients],
            steps=[st.to_view() for st in self.steps],
            nutrition_evidence=[ne.to_view() for ne in self.nutrition_evidence],
            source_name=self.source_name,
            source_url=self.source_url,
            content_license=self.content_license,
        )


@dataclass
class ScanSessionRecord:
    id: str
    user_id: str
    model_id: str
    ingredient_ids: list[str] = field(default_factory=list)


class CatalogRepository(Protocol):
    """Repository interface for Stage 1 & Stage 2 Catalog, Recipes, Reasoning, and Scan Sessions."""

    def check_health(self) -> bool: ...

    def list_active_ingredients(
        self,
        q: str | None = None,
        category: str | None = None,
        exclude_pantry: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[IngredientRecord], int]: ...

    def get_ingredients_by_ids(self, ingredient_ids: list[str]) -> dict[str, IngredientRecord]: ...

    def get_active_pantry_ingredients(self) -> dict[str, IngredientRecord]: ...

    def list_published_recipes(
        self,
        q: str | None = None,
        cuisine_code: str | None = None,
        max_total_minutes: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[RecipeRecord], int]: ...

    def get_published_recipe_by_id(self, recipe_id: str) -> RecipeRecord | None: ...

    def get_all_published_recipes(self) -> list[RecipeRecord]: ...

    def verify_and_sync_scan_ingredients(
        self,
        scan_id: str,
        user_id: str | None,
        ingredient_ids: list[str],
    ) -> bool: ...


class InMemoryCatalogRepository:
    """In-memory store pre-populated with canonical baseline fixtures for testing & dev fallback."""

    def __init__(
        self,
        ingredients: list[IngredientRecord] | None = None,
        recipes: list[RecipeRecord] | None = None,
        scan_sessions: list[ScanSessionRecord] | None = None,
    ) -> None:
        seed_ings = build_default_seed_ingredients() if ingredients is None else ingredients
        seed_recs = build_default_seed_recipes() if recipes is None else recipes
        self._ingredients: dict[str, IngredientRecord] = {ing.id: ing for ing in seed_ings}
        self._recipes: dict[str, RecipeRecord] = {rec.id: rec for rec in seed_recs}
        self._scan_sessions: dict[str, ScanSessionRecord] = {
            ss.id: ss for ss in (scan_sessions or [])
        }

    def register_scan_session(self, scan_session: ScanSessionRecord) -> None:
        self._scan_sessions[scan_session.id] = scan_session

    def get_scan_session(self, scan_id: str) -> ScanSessionRecord | None:
        return self._scan_sessions.get(scan_id)

    def verify_and_sync_scan_ingredients(
        self,
        scan_id: str,
        user_id: str | None,
        ingredient_ids: list[str],
    ) -> bool:
        if not user_id:
            return False
        session = self._scan_sessions.get(scan_id)
        if session is None or session.user_id != user_id:
            return False
        session.ingredient_ids = list(ingredient_ids)
        return True

    def check_health(self) -> bool:
        return True

    def list_active_ingredients(
        self,
        q: str | None = None,
        category: str | None = None,
        exclude_pantry: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[IngredientRecord], int]:
        candidates = [ing for ing in self._ingredients.values() if ing.is_active]
        if category:
            candidates = [ing for ing in candidates if ing.category == category]
        if exclude_pantry:
            candidates = [ing for ing in candidates if ing.category != "pantry"]

        if q and q.strip():
            ranked = rank_ingredient_candidates(
                query=q,
                items=candidates,
                threshold=settings.trgm_similarity_threshold,
            )
            candidates = [item for item, _tier, _score in ranked]
        else:
            candidates.sort(key=lambda x: (x.slug, x.id))

        total = len(candidates)
        return candidates[offset : offset + limit], total

    def get_ingredients_by_ids(self, ingredient_ids: list[str]) -> dict[str, IngredientRecord]:
        return {
            iid: self._ingredients[iid]
            for iid in ingredient_ids
            if iid in self._ingredients
        }

    def get_active_pantry_ingredients(self) -> dict[str, IngredientRecord]:
        return {
            ing.id: ing
            for ing in self._ingredients.values()
            if ing.is_active and ing.category == "pantry"
        }

    def list_published_recipes(
        self,
        q: str | None = None,
        cuisine_code: str | None = None,
        max_total_minutes: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[RecipeRecord], int]:
        items = [r for r in self._recipes.values() if r.status == "published"]
        if cuisine_code:
            items = [r for r in items if r.cuisine_code == cuisine_code]
        if max_total_minutes is not None:
            items = [r for r in items if r.total_minutes <= max_total_minutes]
        if q and q.strip():
            nq = norm_vi(q)
            items = [
                r
                for r in items
                if nq in norm_vi(r.name_vi) or nq in r.slug.lower()
            ]
        items.sort(key=lambda r: (r.total_minutes, r.id))
        total = len(items)
        return items[offset : offset + limit], total

    def get_published_recipe_by_id(self, recipe_id: str) -> RecipeRecord | None:
        rec = self._recipes.get(recipe_id)
        if not rec or rec.status != "published":
            return None
        return rec

    def get_all_published_recipes(self) -> list[RecipeRecord]:
        return [r for r in self._recipes.values() if r.status == "published"]


def _row_to_ingredient(row: dict[str, Any]) -> IngredientRecord:
    """Convert a PostgreSQL dict row into a typed IngredientRecord."""
    return IngredientRecord(
        id=row["id"],
        slug=row["slug"],
        name_vi=row["name_vi"],
        category=row["category"],
        is_active=bool(row["is_active"]),
        fdc_id=row.get("fdc_id"),
    )


class PostgresCatalogRepository:
    """PostgreSQL repository executing queries against Supabase PostgreSQL >= 15."""

    def __init__(self, dsn: str) -> None:
        self._dsn = sanitize_psycopg_dsn(dsn)

    def _connect(self):
        import psycopg
        from psycopg.rows import dict_row

        # prepare_threshold=None ensures full compatibility with Supabase PgBouncer transaction pooler (port 6543)
        return psycopg.connect(self._dsn, row_factory=dict_row, prepare_threshold=None)

    def check_health(self) -> bool:
        try:
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute("SELECT 1 AS ok")
                row = cur.fetchone()
                return bool(row and row["ok"] == 1)
        except Exception:
            return False

    def list_active_ingredients(
        self,
        q: str | None = None,
        category: str | None = None,
        exclude_pantry: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[IngredientRecord], int]:
        where_clauses = ["i.is_active = true"]
        named_params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }

        if category:
            where_clauses.append("i.category = %(category)s")
            named_params["category"] = category
        if exclude_pantry:
            where_clauses.append("i.category <> 'pantry'")

        where_sql = " AND ".join(where_clauses)

        with self._connect() as conn, conn.cursor() as cur:
            if q and q.strip():
                named_params.update(
                    {
                        "q_raw": q.strip(),
                        "nq": norm_vi(q),
                        "thr": settings.trgm_similarity_threshold,
                    }
                )
                sql = f"""
                    WITH matched AS (
                        SELECT
                            i.id::text AS id,
                            i.slug,
                            i.name_vi,
                            i.category,
                            i.is_active,
                            i.fdc_id,
                            MIN(
                                CASE
                                    WHEN lower(i.slug) = lower(%(q_raw)s)
                                         OR lower(i.name_vi) = lower(%(q_raw)s)
                                         OR lower(a.alias) = lower(%(q_raw)s) THEN 1
                                    WHEN public.norm_vi(i.name_vi) = %(nq)s
                                         OR a.normalized_alias = %(nq)s THEN 2
                                    WHEN similarity(public.norm_vi(i.name_vi), %(nq)s) >= %(thr)s
                                         OR similarity(COALESCE(a.normalized_alias, ''), %(nq)s) >= %(thr)s THEN 3
                                    ELSE 4
                                END
                            ) AS match_tier,
                            GREATEST(
                                similarity(public.norm_vi(i.name_vi), %(nq)s),
                                COALESCE(MAX(similarity(a.normalized_alias, %(nq)s)), 0.0)
                            ) AS sim_score
                        FROM public.ingredients i
                        LEFT JOIN public.ingredient_aliases a ON a.ingredient_id = i.id
                        WHERE {where_sql}
                          AND (
                              lower(i.slug) = lower(%(q_raw)s)
                              OR public.norm_vi(i.name_vi) LIKE '%%' || %(nq)s || '%%'
                              OR a.normalized_alias LIKE '%%' || %(nq)s || '%%'
                              OR similarity(public.norm_vi(i.name_vi), %(nq)s) >= %(thr)s
                              OR similarity(COALESCE(a.normalized_alias, ''), %(nq)s) >= %(thr)s
                          )
                        GROUP BY i.id, i.slug, i.name_vi, i.category, i.is_active, i.fdc_id
                    )
                    SELECT *, COUNT(*) OVER() AS total_count
                    FROM matched
                    ORDER BY match_tier ASC, sim_score DESC, slug ASC
                    LIMIT %(limit)s OFFSET %(offset)s
                """
                cur.execute(sql, named_params)
                rows = cur.fetchall()
            else:
                sql = f"""
                    SELECT
                        i.id::text AS id,
                        i.slug,
                        i.name_vi,
                        i.category,
                        i.is_active,
                        i.fdc_id,
                        COUNT(*) OVER() AS total_count
                    FROM public.ingredients i
                    WHERE {where_sql}
                    ORDER BY i.slug ASC, i.id ASC
                    LIMIT %(limit)s OFFSET %(offset)s
                """
                cur.execute(sql, named_params)
                rows = cur.fetchall()

        total = int(rows[0]["total_count"]) if rows else 0
        return [_row_to_ingredient(r) for r in rows], total

    def get_ingredients_by_ids(self, ingredient_ids: list[str]) -> dict[str, IngredientRecord]:
        if not ingredient_ids:
            return {}
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::text AS id, slug, name_vi, category, is_active, fdc_id
                FROM public.ingredients
                WHERE id::text = ANY(%s)
                """,
                (ingredient_ids,),
            )
            rows = cur.fetchall()
        return {r["id"]: _row_to_ingredient(r) for r in rows}

    def get_active_pantry_ingredients(self) -> dict[str, IngredientRecord]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::text AS id, slug, name_vi, category, is_active, fdc_id
                FROM public.ingredients
                WHERE is_active = true AND category = 'pantry'
                """
            )
            rows = cur.fetchall()
        return {r["id"]: _row_to_ingredient(r) for r in rows}

    def list_published_recipes(
        self,
        q: str | None = None,
        cuisine_code: str | None = None,
        max_total_minutes: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[RecipeRecord], int]:
        where_clauses = ["r.status = 'published'"]
        params: list[Any] = []
        if cuisine_code:
            where_clauses.append("r.cuisine_code = %s")
            params.append(cuisine_code)
        if max_total_minutes is not None:
            where_clauses.append("(r.prep_minutes + r.cook_minutes) <= %s")
            params.append(max_total_minutes)
        if q and q.strip():
            nq = norm_vi(q)
            where_clauses.append(
                "(public.norm_vi(r.name_vi) LIKE '%%' || %s || '%%' OR similarity(public.norm_vi(r.name_vi), %s) >= %s)"
            )
            params.extend([nq, nq, settings.trgm_similarity_threshold])

        where_sql = " AND ".join(where_clauses)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    r.id::text AS id,
                    r.slug,
                    r.name_vi,
                    r.cuisine_code,
                    r.prep_minutes,
                    r.cook_minutes,
                    r.cover_image_path,
                    COUNT(*) OVER() AS total_count
                FROM public.recipes r
                WHERE {where_sql}
                ORDER BY (r.prep_minutes + r.cook_minutes) ASC, r.id ASC
                LIMIT %s OFFSET %s
                """,
                [*params, limit, offset],
            )
            rows = cur.fetchall()

        total = int(rows[0]["total_count"]) if rows else 0
        items = [
            RecipeRecord(
                id=r["id"],
                slug=r["slug"],
                name_vi=r["name_vi"],
                cuisine_code=r["cuisine_code"],
                prep_minutes=int(r["prep_minutes"]),
                cook_minutes=int(r["cook_minutes"]),
                cover_image_url=r.get("cover_image_path"),
            )
            for r in rows
        ]
        return items, total

    def get_published_recipe_by_id(self, recipe_id: str) -> RecipeRecord | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    r.id::text AS id,
                    r.slug,
                    r.name_vi,
                    r.description,
                    r.cuisine_code,
                    r.country_code,
                    r.cooking_method,
                    r.required_equipment,
                    r.base_servings,
                    r.prep_minutes,
                    r.cook_minutes,
                    r.quality_score,
                    r.cover_image_path,
                    r.source_name,
                    r.source_url,
                    r.content_license,
                    r.status
                FROM public.recipes r
                WHERE r.id::text = %s AND r.status = 'published'
                """,
                (recipe_id,),
            )
            r = cur.fetchone()
            if not r:
                return None

            cur.execute(
                """
                SELECT
                    ri.ingredient_id::text AS ingredient_id,
                    i.name_vi,
                    i.category,
                    ri.is_required,
                    ri.role,
                    ri.weight::float AS weight,
                    ri.grams::float AS grams,
                    ri.display_quantity,
                    ri.sort_order
                FROM public.recipe_ingredients ri
                JOIN public.ingredients i ON i.id = ri.ingredient_id
                WHERE ri.recipe_id::text = %s
                ORDER BY ri.sort_order ASC, i.name_vi ASC
                """,
                (recipe_id,),
            )
            ing_rows = cur.fetchall()

            cur.execute(
                """
                SELECT step_no, instruction, estimated_minutes
                FROM public.recipe_steps
                WHERE recipe_id::text = %s
                ORDER BY step_no ASC
                """,
                (recipe_id,),
            )
            step_rows = cur.fetchall()

            cur.execute(
                """
                SELECT
                    nt.id::text AS tag_id,
                    nt.code,
                    nt.name_vi,
                    nt.description,
                    nt.is_active,
                    array_agg(DISTINCT intag.source_url) AS source_urls,
                    MAX(intag.note) AS note
                FROM public.recipe_ingredients ri
                JOIN public.ingredient_nutrition_tags intag ON intag.ingredient_id = ri.ingredient_id
                JOIN public.nutrition_tags nt ON nt.id = intag.nutrition_tag_id
                WHERE ri.recipe_id::text = %s AND nt.is_active = true
                GROUP BY nt.id, nt.code, nt.name_vi, nt.description, nt.is_active
                ORDER BY nt.code ASC
                """,
                (recipe_id,),
            )
            nutr_rows = cur.fetchall()

        return RecipeRecord(
            id=r["id"],
            slug=r["slug"],
            name_vi=r["name_vi"],
            description=r.get("description"),
            cuisine_code=r["cuisine_code"],
            country_code=r.get("country_code"),
            cooking_method=r.get("cooking_method"),
            required_equipment=list(r.get("required_equipment") or []),
            base_servings=int(r.get("base_servings") or 2),
            prep_minutes=int(r["prep_minutes"]),
            cook_minutes=int(r["cook_minutes"]),
            quality_score=float(r.get("quality_score") or 1.0),
            cover_image_url=r.get("cover_image_path"),
            source_name=r.get("source_name"),
            source_url=r.get("source_url"),
            content_license=r.get("content_license"),
            status=r["status"],
            ingredients=[
                RecipeIngredientRecord(
                    ingredient_id=ir["ingredient_id"],
                    name_vi=ir["name_vi"],
                    category=ir["category"],
                    is_required=bool(ir["is_required"]),
                    role=ir["role"],
                    weight=float(ir["weight"]),
                    grams=float(ir["grams"]) if ir.get("grams") is not None else None,
                    display_quantity=ir.get("display_quantity"),
                    sort_order=int(ir["sort_order"]),
                )
                for ir in ing_rows
            ],
            steps=[
                RecipeStepRecord(
                    step_no=int(sr["step_no"]),
                    instruction=sr["instruction"],
                    estimated_minutes=int(sr["estimated_minutes"]) if sr.get("estimated_minutes") is not None else None,
                )
                for sr in step_rows
            ],
            nutrition_evidence=[
                NutritionEvidenceRecord(
                    tag_id=nr["tag_id"],
                    tag_code=nr["code"],
                    tag_name_vi=nr["name_vi"],
                    tag_description=nr["description"],
                    tag_is_active=bool(nr["is_active"]),
                    source_urls=list(nr["source_urls"] or []),
                    note=nr.get("note"),
                )
                for nr in nutr_rows
            ],
        )

    def get_all_published_recipes(self) -> list[RecipeRecord]:
        items, _ = self.list_published_recipes(limit=1000, offset=0)
        detailed: list[RecipeRecord] = []
        for summary in items:
            detail = self.get_published_recipe_by_id(summary.id)
            if detail:
                detailed.append(detail)
        return detailed

    def verify_and_sync_scan_ingredients(
        self,
        scan_id: str,
        user_id: str | None,
        ingredient_ids: list[str],
    ) -> bool:
        if not user_id:
            return False
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id::text AS user_id
                FROM public.scan_sessions
                WHERE id::text = %s
                """,
                (scan_id,),
            )
            row = cur.fetchone()
            if not row or row["user_id"] != user_id:
                return False

            cur.execute(
                "DELETE FROM public.scan_ingredients WHERE scan_session_id::text = %s",
                (scan_id,),
            )
            for iid in ingredient_ids:
                cur.execute(
                    """
                    INSERT INTO public.scan_ingredients (scan_session_id, ingredient_id, provenance)
                    VALUES (%s::uuid, %s::uuid, 'corrected')
                    ON CONFLICT (scan_session_id, ingredient_id) DO NOTHING
                    """,
                    (scan_id, iid),
                )
            conn.commit()
        return True


_default_repo: CatalogRepository | None = None

# Backward-compatible aliases for seed fixture builders
_default_seed_ingredients = build_default_seed_ingredients
_default_seed_recipes = build_default_seed_recipes


def get_catalog_repo() -> CatalogRepository:
    global _default_repo
    if _default_repo is not None:
        return _default_repo
    if is_db_configured():
        _default_repo = PostgresCatalogRepository(settings.database_url or settings.direct_url)
    else:
        _default_repo = InMemoryCatalogRepository()
    return _default_repo


def set_catalog_repo(repo: CatalogRepository | None) -> None:
    global _default_repo
    _default_repo = repo
