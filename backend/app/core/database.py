"""PostgreSQL database connection and repository abstraction for FoodVision AI.

Supports:
1. Supabase Transaction Pooler (port 6543, pgbouncer=true) with prepare_threshold=None.
2. Direct PostgreSQL connection (port 5432).
3. Pluggable Repository dependency injection for deterministic testing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from uuid import uuid4

from app.core.config import settings
from app.core.seed_fixtures import (
    MODEL_YOLO_V1_SHA256,
    build_default_seed_ai_model,
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
    if os.getenv("USE_IN_MEMORY_CATALOG", "").strip().lower() in {"1", "true", "yes", "on"}:
        return False
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
    role: str = "core"
    dish_role: str = "main"
    weight: float = 4.0
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

    @property
    def total_hours(self) -> float:
        return float(max(1, self.total_minutes)) / 60.0

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
    detections: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class AILabelRecord:
    id: str
    model_id: str
    class_index: int
    class_name: str
    ingredient_id: str
    ingredient_name_vi: str
    category: IngredientCategory
    is_active: bool = True


@dataclass
class AIModelRecord:
    id: str
    version: str
    family: str
    dataset_version: str
    artifact_ref: str
    weights_sha256: str = MODEL_YOLO_V1_SHA256
    class_count: int = 20
    confidence_threshold: float = 0.25
    review_threshold: float = 0.80
    status: str = "active"
    labels_by_index: dict[int, AILabelRecord] = field(default_factory=dict)


@dataclass
class UserPreferencesRecord:
    user_id: str
    allergic_ingredient_ids: list[str] = field(default_factory=list)
    kitchen_spice_ids: list[str] = field(default_factory=list)
    favorite_ingredient_ids: list[str] = field(default_factory=list)
    excluded_allergen_ids: list[str] = field(default_factory=list)
    available_equipment: list[str] | None = None
    updated_at: datetime | None = None


class CatalogRepository(Protocol):
    # CONFLICT-RESOLVED: Unify Stage 1..3 repository protocol (PR #12 preferences + Stage 3 AI models/scan sessions).
    """Repository interface for Stage 1..3 Catalog, Recipes, Reasoning, Preferences, AI Models, and Scan Sessions."""

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

    # CONFLICT-RESOLVED: Retain both PR #12 user_preferences methods and Stage 3 AI model/scan session methods.
    def get_user_preferences(self, user_id: str) -> UserPreferencesRecord | None: ...

    def upsert_user_preferences(self, prefs: UserPreferencesRecord) -> UserPreferencesRecord: ...

    def get_active_ai_model(self) -> AIModelRecord | None: ...

    def create_scan_session(
        self,
        user_id: str,
        model_id: str,
        detections: list[dict[str, Any]] | None = None,
        ingredient_ids: list[str] | None = None,
    ) -> ScanSessionRecord: ...

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
        # CONFLICT-RESOLVED: Support both user_preferences (PR #12) and active_ai_model (Stage 3) in InMemoryCatalogRepository.
        user_preferences: list[UserPreferencesRecord] | None = None,
        active_ai_model: AIModelRecord | None = ...,  # type: ignore[assignment]
    ) -> None:
        seed_ings = build_default_seed_ingredients() if ingredients is None else ingredients
        seed_recs = build_default_seed_recipes() if recipes is None else recipes
        self._ingredients: dict[str, IngredientRecord] = {ing.id: ing for ing in seed_ings}
        self._recipes: dict[str, RecipeRecord] = {rec.id: rec for rec in seed_recs}
        self._scan_sessions: dict[str, ScanSessionRecord] = {
            ss.id: ss for ss in (scan_sessions or [])
        }
        self._user_preferences: dict[str, UserPreferencesRecord] = {
            up.user_id: up for up in (user_preferences or [])
        }
        self._active_ai_model: AIModelRecord | None = (
            build_default_seed_ai_model()
            if active_ai_model is ...
            else active_ai_model
        )
        self._personalization_engine: Any = None

    @property
    def personalization_engine(self) -> Any:
        if self._personalization_engine is None:
            from app.intelligence.personalization import (
                InMemoryPersonalizationRepository,
                PersonalizationEngine,
            )

            self._personalization_engine = PersonalizationEngine(
                repository=InMemoryPersonalizationRepository()
            )
        return self._personalization_engine

    def set_personalization_engine(self, engine: Any) -> None:
        self._personalization_engine = engine

    def get_user_preferences(self, user_id: str) -> UserPreferencesRecord | None:
        return self._user_preferences.get(user_id)

    def upsert_user_preferences(self, prefs: UserPreferencesRecord) -> UserPreferencesRecord:
        stored = UserPreferencesRecord(
            user_id=prefs.user_id,
            allergic_ingredient_ids=list(prefs.allergic_ingredient_ids),
            kitchen_spice_ids=list(prefs.kitchen_spice_ids),
            favorite_ingredient_ids=list(prefs.favorite_ingredient_ids),
            excluded_allergen_ids=list(prefs.excluded_allergen_ids),
            available_equipment=list(prefs.available_equipment)
            if prefs.available_equipment is not None
            else None,
            updated_at=prefs.updated_at or datetime.now(timezone.utc),
        )
        self._user_preferences[prefs.user_id] = stored
        return stored

    def get_active_ai_model(self) -> AIModelRecord | None:
        if self._active_ai_model is None or self._active_ai_model.status != "active":
            return None
        return self._active_ai_model

    def set_active_ai_model(self, model: AIModelRecord | None) -> None:
        self._active_ai_model = model

    def register_scan_session(self, scan_session: ScanSessionRecord) -> None:
        self._scan_sessions[scan_session.id] = scan_session

    def create_scan_session(
        self,
        user_id: str,
        model_id: str,
        detections: list[dict[str, Any]] | None = None,
        ingredient_ids: list[str] | None = None,
    ) -> ScanSessionRecord:
        record = ScanSessionRecord(
            id=str(uuid4()),
            user_id=user_id,
            model_id=model_id,
            ingredient_ids=list(ingredient_ids or []),
            detections=list(detections or []),
        )
        self._scan_sessions[record.id] = record
        return record

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


class _PostgresPersonalizationRepository:
    """PostgreSQL-backed `UserPersonalizationRepository` reading/writing `public.user_preferences`."""

    # THUẬT TOÁN: Kho Lưu trữ Trọng số Hồi quy Logistic (`TP 08`) trên PostgreSQL (`user_preferences`)
    # Cơ chế: Đồng bộ cột `lr_weights`, `feedback_count`, `lr_model_version` theo từng `user_id` UUID
    #         với cơ chế UPSERT idempotent và giữ cache `recipe_feedback_timestamps` chống phát lại `ADR-012`.
    # Complexity: Time O(1) mỗi truy vấn khóa chính `user_id`, Space O(U * R_feedback) cho bộ nhớ đệm mốc thời gian.
    def __init__(self, connect_fn: Any) -> None:
        self._connect = connect_fn
        self._timestamps_by_user: dict[Any, dict[str, str]] = {}

    def get_user_model_state(self, user_id: Any) -> Any:
        from app.intelligence.personalization.config import _ensure_uuid
        from app.intelligence.personalization.constants import (
            FEATURE_SCHEMA_VERSION,
            _DISABLED_MODEL_SENTINEL,
        )
        from app.intelligence.personalization.models import UserModelState

        uid = _ensure_uuid(user_id, field_name="user_id")
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT lr_weights, feedback_count, lr_model_version, updated_at
                FROM public.user_preferences
                WHERE user_id = %s::uuid
                """,
                (str(uid),),
            )
            row = cur.fetchone()
        if not row:
            return None

        raw_version: str | None = row.get("lr_model_version")
        raw_weights = row.get("lr_weights")
        is_enabled = raw_version != _DISABLED_MODEL_SENTINEL
        theta_tuple: tuple[float, ...] | None = None
        schema_ver: str | None = None
        if isinstance(raw_weights, list) and len(raw_weights) > 0:
            theta_tuple = tuple(float(v) for v in raw_weights)
            schema_ver = FEATURE_SCHEMA_VERSION

        return UserModelState(
            user_id=uid,
            theta_user=theta_tuple,
            feedback_count=int(row.get("feedback_count") or 0),
            model_version=None if raw_version == _DISABLED_MODEL_SENTINEL else raw_version,
            schema_version=schema_ver,
            personalization_enabled=is_enabled,
            recipe_feedback_timestamps=dict(self._timestamps_by_user.get(uid, {})),
            updated_at=row.get("updated_at"),
        )

    def save_user_model_state(self, state: Any) -> Any:
        from psycopg.types.json import Jsonb

        from app.intelligence.personalization.config import _ensure_uuid
        from app.intelligence.personalization.constants import (
            DEFAULT_PERSONALIZATION_MODEL_VERSION,
            _DISABLED_MODEL_SENTINEL,
        )
        from app.intelligence.personalization.models import UserModelState

        uid = _ensure_uuid(state.user_id, field_name="state.user_id")
        version_tag = (
            _DISABLED_MODEL_SENTINEL
            if not state.personalization_enabled
            else (state.model_version or DEFAULT_PERSONALIZATION_MODEL_VERSION)
        )
        weights_payload = list(state.theta_user) if state.theta_user is not None else []
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.user_preferences (
                    user_id, lr_weights, feedback_count, lr_model_version
                )
                VALUES (%s::uuid, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE
                SET lr_weights = EXCLUDED.lr_weights,
                    feedback_count = EXCLUDED.feedback_count,
                    lr_model_version = EXCLUDED.lr_model_version,
                    updated_at = now()
                RETURNING updated_at
                """,
                (str(uid), Jsonb(weights_payload), int(state.feedback_count), version_tag),
            )
            ret = cur.fetchone()
            conn.commit()
        self._timestamps_by_user[uid] = dict(state.recipe_feedback_timestamps)
        return UserModelState(
            user_id=uid,
            theta_user=tuple(weights_payload) if weights_payload else None,
            feedback_count=int(state.feedback_count),
            model_version=None if not state.personalization_enabled else version_tag,
            schema_version=state.schema_version if weights_payload else None,
            personalization_enabled=state.personalization_enabled,
            recipe_feedback_timestamps=dict(state.recipe_feedback_timestamps),
            updated_at=ret["updated_at"] if ret else datetime.now(timezone.utc),
        )

    def reset_user_model_state(
        self,
        user_id: Any,
        *,
        disable_personalization: bool = False,
    ) -> Any:
        from psycopg.types.json import Jsonb

        from app.intelligence.personalization.config import _ensure_uuid
        from app.intelligence.personalization.constants import (
            DEFAULT_PERSONALIZATION_MODEL_VERSION,
            _DISABLED_MODEL_SENTINEL,
        )
        from app.intelligence.personalization.models import UserModelState

        uid = _ensure_uuid(user_id, field_name="user_id")
        version_tag = (
            _DISABLED_MODEL_SENTINEL
            if disable_personalization
            else DEFAULT_PERSONALIZATION_MODEL_VERSION
        )
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.user_preferences (
                    user_id, lr_weights, feedback_count, lr_model_version
                )
                VALUES (%s::uuid, %s, 0, %s)
                ON CONFLICT (user_id) DO UPDATE
                SET lr_weights = EXCLUDED.lr_weights,
                    feedback_count = 0,
                    lr_model_version = EXCLUDED.lr_model_version,
                    updated_at = now()
                RETURNING updated_at
                """,
                (str(uid), Jsonb([]), version_tag),
            )
            ret = cur.fetchone()
            conn.commit()
        self._timestamps_by_user[uid] = {}
        return UserModelState(
            user_id=uid,
            theta_user=None,
            feedback_count=0,
            model_version=None,
            schema_version=None,
            personalization_enabled=not disable_personalization,
            recipe_feedback_timestamps={},
            updated_at=ret["updated_at"] if ret else datetime.now(timezone.utc),
        )


class PostgresCatalogRepository:
    """PostgreSQL repository executing queries against Supabase PostgreSQL >= 15."""

    def __init__(self, dsn: str) -> None:
        self._dsn = sanitize_psycopg_dsn(dsn)
        self._personalization_engine: Any = None

    @property
    def personalization_engine(self) -> Any:
        if self._personalization_engine is None:
            from app.intelligence.personalization import PersonalizationEngine

            self._personalization_engine = PersonalizationEngine(
                repository=_PostgresPersonalizationRepository(self._connect)
            )
        return self._personalization_engine

    def set_personalization_engine(self, engine: Any) -> None:
        self._personalization_engine = engine

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
                    ri.dish_role,
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

            cur.execute(
                """
                SELECT allergen_code
                FROM public.recipe_allergens
                WHERE recipe_id::text = %s
                ORDER BY allergen_code ASC
                """,
                (recipe_id,),
            )
            allergen_rows = cur.fetchall()

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
            allergen_ids=[ar["allergen_code"] for ar in allergen_rows],
            ingredients=[
                RecipeIngredientRecord(
                    ingredient_id=ir["ingredient_id"],
                    name_vi=ir["name_vi"],
                    category=ir["category"],
                    is_required=bool(ir["is_required"]),
                    role=ir["role"],
                    dish_role=ir.get("dish_role") or ("main" if ir["role"] in ("core", "primary") else "sub"),
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
        """Batch-fetch all published recipes, their ingredients, and allergens in 3 SQL queries (zero N+1)."""
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
                WHERE r.status = 'published'
                ORDER BY (r.prep_minutes + r.cook_minutes) ASC, r.id ASC
                """
            )
            recipe_rows = cur.fetchall()
            if not recipe_rows:
                return []

            recipe_ids = [r["id"] for r in recipe_rows]

            cur.execute(
                """
                SELECT
                    ri.recipe_id::text AS recipe_id,
                    ri.ingredient_id::text AS ingredient_id,
                    i.name_vi,
                    i.category,
                    ri.is_required,
                    ri.role,
                    ri.dish_role,
                    ri.weight::float AS weight,
                    ri.grams::float AS grams,
                    ri.display_quantity,
                    ri.sort_order
                FROM public.recipe_ingredients ri
                JOIN public.ingredients i ON i.id = ri.ingredient_id
                WHERE ri.recipe_id::text = ANY(%s)
                ORDER BY ri.recipe_id, ri.sort_order ASC, i.name_vi ASC
                """,
                (recipe_ids,),
            )
            all_ing_rows = cur.fetchall()

            cur.execute(
                """
                SELECT recipe_id::text AS recipe_id, allergen_code
                FROM public.recipe_allergens
                WHERE recipe_id::text = ANY(%s)
                ORDER BY recipe_id, allergen_code ASC
                """,
                (recipe_ids,),
            )
            all_allergen_rows = cur.fetchall()

        ings_by_recipe: dict[str, list[RecipeIngredientRecord]] = {rid: [] for rid in recipe_ids}
        for ir in all_ing_rows:
            ings_by_recipe[ir["recipe_id"]].append(
                RecipeIngredientRecord(
                    ingredient_id=ir["ingredient_id"],
                    name_vi=ir["name_vi"],
                    category=ir["category"],
                    is_required=bool(ir["is_required"]),
                    role=ir["role"],
                    dish_role=ir.get("dish_role")
                    or ("main" if ir["role"] in ("core", "primary") else "sub"),
                    weight=float(ir["weight"]),
                    grams=float(ir["grams"]) if ir.get("grams") is not None else None,
                    display_quantity=ir.get("display_quantity"),
                    sort_order=int(ir["sort_order"]),
                )
            )

        allergens_by_recipe: dict[str, list[str]] = {rid: [] for rid in recipe_ids}
        for ar in all_allergen_rows:
            allergens_by_recipe[ar["recipe_id"]].append(ar["allergen_code"])

        return [
            RecipeRecord(
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
                ingredients=ings_by_recipe.get(r["id"], []),
                allergen_ids=allergens_by_recipe.get(r["id"], []),
            )
            for r in recipe_rows
        ]

    def get_user_preferences(self, user_id: str) -> UserPreferencesRecord | None:
        if not user_id:
            return None
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    user_id::text AS user_id,
                    allergic_ingredient_ids,
                    kitchen_spice_ids,
                    favorite_ingredient_ids,
                    excluded_allergen_ids,
                    available_equipment,
                    updated_at
                FROM public.user_preferences
                WHERE user_id::text = %s
                """,
                (user_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return UserPreferencesRecord(
            user_id=row["user_id"],
            allergic_ingredient_ids=list(row.get("allergic_ingredient_ids") or []),
            kitchen_spice_ids=list(row.get("kitchen_spice_ids") or []),
            favorite_ingredient_ids=list(row.get("favorite_ingredient_ids") or []),
            excluded_allergen_ids=list(row.get("excluded_allergen_ids") or []),
            available_equipment=(
                list(row["available_equipment"])
                if row.get("available_equipment") is not None
                else None
            ),
            updated_at=row.get("updated_at"),
        )

    def upsert_user_preferences(self, prefs: UserPreferencesRecord) -> UserPreferencesRecord:
        from psycopg.types.json import Jsonb

        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.user_preferences (
                    user_id,
                    allergic_ingredient_ids,
                    kitchen_spice_ids,
                    favorite_ingredient_ids,
                    excluded_allergen_ids,
                    available_equipment
                )
                VALUES (%s::uuid, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE
                SET allergic_ingredient_ids = EXCLUDED.allergic_ingredient_ids,
                    kitchen_spice_ids = EXCLUDED.kitchen_spice_ids,
                    favorite_ingredient_ids = EXCLUDED.favorite_ingredient_ids,
                    excluded_allergen_ids = EXCLUDED.excluded_allergen_ids,
                    available_equipment = EXCLUDED.available_equipment,
                    updated_at = now()
                RETURNING updated_at
                """,
                (
                    prefs.user_id,
                    Jsonb(list(prefs.allergic_ingredient_ids)),
                    Jsonb(list(prefs.kitchen_spice_ids)),
                    Jsonb(list(prefs.favorite_ingredient_ids)),
                    Jsonb(list(prefs.excluded_allergen_ids)),
                    Jsonb(list(prefs.available_equipment))
                    if prefs.available_equipment is not None
                    else None,
                ),
            )
            ret = cur.fetchone()
            conn.commit()
        prefs.updated_at = ret["updated_at"] if ret else datetime.now(timezone.utc)
        return prefs

    def get_active_ai_model(self) -> AIModelRecord | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id::text AS id,
                    version,
                    family,
                    dataset_version,
                    artifact_ref,
                    class_count,
                    confidence_threshold::float AS confidence_threshold,
                    review_threshold::float AS review_threshold,
                    status
                FROM public.ai_models
                WHERE status = 'active'
                LIMIT 1
                """
            )
            m = cur.fetchone()
            if not m:
                return None

            cur.execute(
                """
                SELECT
                    l.id::text AS id,
                    l.model_id::text AS model_id,
                    l.class_index,
                    l.class_name,
                    l.ingredient_id::text AS ingredient_id,
                    i.name_vi AS ingredient_name_vi,
                    i.category,
                    i.is_active
                FROM public.ai_labels l
                JOIN public.ingredients i ON i.id = l.ingredient_id
                WHERE l.model_id::text = %s
                ORDER BY l.class_index ASC
                """,
                (m["id"],),
            )
            lbl_rows = cur.fetchall()

        labels_by_idx = {
            int(r["class_index"]): AILabelRecord(
                id=r["id"],
                model_id=r["model_id"],
                class_index=int(r["class_index"]),
                class_name=r["class_name"],
                ingredient_id=r["ingredient_id"],
                ingredient_name_vi=r["ingredient_name_vi"],
                category=r["category"],
                is_active=bool(r["is_active"]),
            )
            for r in lbl_rows
        }
        return AIModelRecord(
            id=m["id"],
            version=m["version"],
            family=m["family"],
            dataset_version=m["dataset_version"],
            artifact_ref=m["artifact_ref"],
            class_count=int(m["class_count"]),
            confidence_threshold=float(m["confidence_threshold"]),
            review_threshold=float(m["review_threshold"]),
            status=m["status"],
            labels_by_index=labels_by_idx,
        )

    def create_scan_session(
        self,
        user_id: str,
        model_id: str,
        detections: list[dict[str, Any]] | None = None,
        ingredient_ids: list[str] | None = None,
    ) -> ScanSessionRecord:
        scan_id = str(uuid4())
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.scan_sessions (id, user_id, model_id)
                VALUES (%s::uuid, %s::uuid, %s::uuid)
                """,
                (scan_id, user_id, model_id),
            )
            if detections:
                cur.executemany(
                    """
                    INSERT INTO public.scan_detections (
                        scan_session_id, ai_label_id, confidence,
                        x1, y1, x2, y2, needs_confirmation
                    )
                    VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s)
                    """,
                    [
                        (
                            scan_id,
                            det["ai_label_id"],
                            det["confidence"],
                            det["x1"],
                            det["y1"],
                            det["x2"],
                            det["y2"],
                            det.get("needs_confirmation", False),
                        )
                        for det in detections
                    ],
                )
            if ingredient_ids:
                cur.executemany(
                    """
                    INSERT INTO public.scan_ingredients (scan_session_id, ingredient_id, provenance)
                    VALUES (%s::uuid, %s::uuid, 'detected')
                    ON CONFLICT (scan_session_id, ingredient_id) DO NOTHING
                    """,
                    [(scan_id, iid) for iid in ingredient_ids],
                )
            conn.commit()
        return ScanSessionRecord(
            id=scan_id,
            user_id=user_id,
            model_id=model_id,
            ingredient_ids=list(ingredient_ids or []),
            detections=list(detections or []),
        )

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
            if ingredient_ids:
                cur.executemany(
                    """
                    INSERT INTO public.scan_ingredients (scan_session_id, ingredient_id, provenance)
                    VALUES (%s::uuid, %s::uuid, 'corrected')
                    ON CONFLICT (scan_session_id, ingredient_id) DO NOTHING
                    """,
                    [(scan_id, iid) for iid in ingredient_ids],
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
