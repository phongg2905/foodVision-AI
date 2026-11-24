"""Stage 4 User Features & Tier-2 USDA Nutrition Repository Mixins (`InMemory` + `PostgreSQL`).

Covers:
- `FR-10`, `TC-17`, `TC-18`, `SEC-01`: Idempotent `/favorites` (`201`/`200`/`204`) isolated by `user_id`
- `FR-11`, `ADR-012`, `TC-19`, `TC-45`, `SEC-06`: Context-aware `/feedback` upsert on `UNIQUE NULLS NOT DISTINCT (user_id, recipe_id, scan_session_id)`
- `FR-12`, `TC-20`, `TC-28`, `TC-47`, `SEC-06`: Opt-in `/scan-sessions` (`GET`, `GET/{id}`, `DELETE/{id}` with cascade deletion of session-bound feedback)
- `TP 11`, `ADR-004`, `MATH-07`: USDA per-100g `ingredient_nutrients` lookup
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.core.errors import AppError
from app.schemas.user_features import (
    BBox,
    Detection,
    FavoriteView,
    FeedbackCreate,
    FeedbackView,
    ScanSessionDetail,
    ScanSessionSummary,
)
from app.services.nutrition import IngredientNutrient100g
from app.services.personalization_lr import FeedbackSample


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def build_default_seed_nutrients() -> dict[str, IngredientNutrient100g]:
    """Canonical USDA FoodData Central per-100g fixtures matching `supabase/seed.sql` (`MATH-07`)."""
    rows = [
        ("11111111-1111-4111-8111-111111111101", 18.00, 0.88, 0.20, 3.89, "https://fdc.nal.usda.gov/food-details/170457/nutrients"),  # Cà chua
        ("11111111-1111-4111-8111-111111111102", 144.00, 12.56, 9.51, 0.72, "https://fdc.nal.usda.gov/food-details/171287/nutrients"),  # Trứng gà
        ("11111111-1111-4111-8111-111111111103", 76.00, 8.08, 4.78, 1.87, "https://fdc.nal.usda.gov/food-details/172475/nutrients"),  # Đậu hũ
        ("11111111-1111-4111-8111-111111111104", 518.00, 9.34, 53.01, 0.00, "https://fdc.nal.usda.gov/food-details/167814/nutrients"),  # Thịt ba chỉ
        ("11111111-1111-4111-8111-111111111105", 32.00, 1.83, 0.19, 7.34, "https://fdc.nal.usda.gov/food-details/170005/nutrients"),  # Hành lá
        ("11111111-1111-4111-8111-111111111106", 0.00, 0.00, 0.00, 0.00, "https://fdc.nal.usda.gov/food-details/173468/nutrients"),  # Muối
        ("11111111-1111-4111-8111-111111111107", 35.00, 5.07, 0.01, 3.64, "https://fdc.nal.usda.gov/food-details/172235/nutrients"),  # Nước mắm
        ("11111111-1111-4111-8111-111111111108", 884.00, 0.00, 100.00, 0.00, "https://fdc.nal.usda.gov/food-details/171028/nutrients"),  # Dầu ăn
        ("11111111-1111-4111-8111-111111111109", 387.00, 0.00, 0.00, 99.98, "https://fdc.nal.usda.gov/food-details/169655/nutrients"),  # Đường
        ("11111111-1111-4111-8111-111111111110", 251.00, 10.39, 3.26, 63.95, "https://fdc.nal.usda.gov/food-details/170931/nutrients"),  # Tiêu xay
    ]
    return {
        iid: IngredientNutrient100g(
            ingredient_id=iid,
            kcal_100g=kcal,
            protein_100g=prot,
            fat_100g=fat,
            carb_100g=carb,
            source_url=url,
        )
        for iid, kcal, prot, fat, carb, url in rows
    }


@dataclass
class FavoriteRecord:
    user_id: str
    recipe_id: str
    created_at: datetime


@dataclass
class FeedbackRecord:
    id: str
    user_id: str
    recipe_id: str
    scan_session_id: str | None
    rating: int
    note: str | None
    created_at: datetime
    updated_at: datetime


class InMemoryUserMixin:
    """In-memory implementation of Stage 4 User Features & Tier-2 USDA Nutrition."""

    _ingredients: dict[str, Any]
    _recipes: dict[str, Any]
    _scan_sessions: dict[str, Any]
    _ai_models: dict[str, Any]

    def _init_user_state(self) -> None:
        self._favorites: dict[tuple[str, str], FavoriteRecord] = {}
        self._feedback_by_context: dict[tuple[str, str, str | None], FeedbackRecord] = {}
        self._ingredient_nutrients: dict[str, IngredientNutrient100g] = build_default_seed_nutrients()

    # --- USDA Nutrients ---
    def get_ingredient_nutrients_by_ids(
        self, ingredient_ids: list[str]
    ) -> dict[str, IngredientNutrient100g]:
        return {
            iid: self._ingredient_nutrients[iid]
            for iid in ingredient_ids
            if iid in self._ingredient_nutrients
        }

    # --- Favorites (`FR-10`) ---
    def list_user_favorites(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> tuple[list[FavoriteView], int]:
        rows: list[FavoriteView] = []
        user_favs = [fav for (uid, _rid), fav in self._favorites.items() if uid == user_id]
        user_favs.sort(key=lambda f: (f.created_at, f.recipe_id), reverse=True)
        for fav in user_favs:
            rec = self._recipes.get(fav.recipe_id)
            if rec is None or rec.status != "published":
                continue
            rows.append(
                FavoriteView(
                    recipe_id=fav.recipe_id,
                    created_at=fav.created_at,
                    recipe=rec.to_summary(),
                )
            )
        total = len(rows)
        return rows[offset : offset + limit], total

    def add_user_favorite(self, user_id: str, recipe_id: str) -> tuple[FavoriteView, bool]:
        rec = self._recipes.get(recipe_id)
        if rec is None or rec.status != "published":
            raise AppError(
                status_code=404,
                code="RECIPE_NOT_FOUND",
                message="Không tìm thấy công thức món ăn hoặc công thức chưa được xuất bản.",
                details={"recipe_id": recipe_id},
            )
        key = (user_id, recipe_id)
        existing = self._favorites.get(key)
        if existing is not None:
            return (
                FavoriteView(
                    recipe_id=recipe_id,
                    created_at=existing.created_at,
                    recipe=rec.to_summary(),
                ),
                False,
            )
        now = _now_utc()
        created = FavoriteRecord(user_id=user_id, recipe_id=recipe_id, created_at=now)
        self._favorites[key] = created
        return (
            FavoriteView(
                recipe_id=recipe_id,
                created_at=created.created_at,
                recipe=rec.to_summary(),
            ),
            True,
        )

    def remove_user_favorite(self, user_id: str, recipe_id: str) -> None:
        self._favorites.pop((user_id, recipe_id), None)

    # --- Feedback Upsert (`FR-11`, `ADR-012`) ---
    def upsert_user_feedback(
        self, user_id: str, payload: FeedbackCreate
    ) -> tuple[FeedbackView, bool]:
        rec = self._recipes.get(payload.recipe_id)
        if rec is None or rec.status != "published":
            raise AppError(
                status_code=404,
                code="RECIPE_NOT_FOUND",
                message="Không tìm thấy công thức món ăn hoặc công thức chưa được xuất bản.",
                details={"recipe_id": payload.recipe_id},
            )

        if payload.scan_id is not None:
            ss = self._scan_sessions.get(payload.scan_id)
            if ss is None or ss.user_id != user_id:
                raise AppError(
                    status_code=404,
                    code="SCAN_NOT_OWNED",
                    message="Không tìm thấy phiên quét hoặc phiên quét không thuộc chủ sở hữu.",
                    details={"scan_id": payload.scan_id},
                )

        ctx_key = (user_id, payload.recipe_id, payload.scan_id)
        now = _now_utc()
        existing = self._feedback_by_context.get(ctx_key)
        if existing is not None:
            existing.rating = payload.rating
            existing.note = payload.note
            existing.updated_at = now
            return (
                FeedbackView(
                    id=existing.id,
                    recipe_id=existing.recipe_id,
                    rating=existing.rating,
                    created_at=existing.created_at,
                ),
                False,
            )

        fb = FeedbackRecord(
            id=str(uuid.uuid4()),
            user_id=user_id,
            recipe_id=payload.recipe_id,
            scan_session_id=payload.scan_id,
            rating=payload.rating,
            note=payload.note,
            created_at=now,
            updated_at=now,
        )
        self._feedback_by_context[ctx_key] = fb
        return (
            FeedbackView(
                id=fb.id,
                recipe_id=fb.recipe_id,
                rating=fb.rating,
                created_at=fb.created_at,
            ),
            True,
        )

    def get_user_feedback_samples(self, user_id: str) -> list[FeedbackSample]:
        return [
            FeedbackSample(
                user_id=fb.user_id,
                recipe_id=fb.recipe_id,
                rating=fb.rating,
                updated_at=fb.updated_at,
            )
            for fb in self._feedback_by_context.values()
            if fb.user_id == user_id
        ]

    # --- Opt-in Scan History (`FR-12`, `TC-20`, `TC-28`, `TC-47`) ---
    def _resolve_model_version(self, model_id: str) -> str:
        mdl = getattr(self, "_ai_models", {}).get(model_id)
        if mdl is not None:
            return str(mdl.version)
        return "yolov8-seed-v1"

    def create_scan_session_with_detections(
        self,
        user_id: str,
        model_id: str,
        detections: list[Detection] | None = None,
        confirmed_ingredient_ids: list[str] | None = None,
        scan_id: str | None = None,
    ) -> str:
        from app.core.database import ScanSessionRecord

        sid = scan_id or str(uuid.uuid4())
        dets = list(detections or [])
        if confirmed_ingredient_ids is not None:
            ing_ids = list(confirmed_ingredient_ids)
        else:
            seen: set[str] = set()
            ing_ids = []
            for d in dets:
                if d.ingredient_id and d.ingredient_id not in seen:
                    seen.add(d.ingredient_id)
                    ing_ids.append(d.ingredient_id)

        rec = ScanSessionRecord(
            id=sid,
            user_id=user_id,
            model_id=model_id,
            ingredient_ids=ing_ids,
            detections=dets,
            created_at=_now_utc(),
        )
        self._scan_sessions[sid] = rec
        return sid

    def list_user_scan_sessions(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> tuple[list[ScanSessionSummary], int]:
        sessions = [ss for ss in self._scan_sessions.values() if ss.user_id == user_id]
        sessions.sort(key=lambda s: (s.created_at, s.id), reverse=True)
        total = len(sessions)
        items = [
            ScanSessionSummary(
                id=s.id,
                model_version=self._resolve_model_version(s.model_id),
                created_at=s.created_at,
                ingredients_count=len(s.ingredient_ids),
            )
            for s in sessions[offset : offset + limit]
        ]
        return items, total

    def get_user_scan_session_detail(self, user_id: str, scan_id: str) -> ScanSessionDetail:
        ss = self._scan_sessions.get(scan_id)
        if ss is None or ss.user_id != user_id:
            raise AppError(
                status_code=404,
                code="SCAN_NOT_OWNED",
                message="Không tìm thấy phiên quét hoặc phiên quét không thuộc chủ sở hữu.",
                details={"scan_id": scan_id},
            )
        return ScanSessionDetail(
            id=ss.id,
            model_version=self._resolve_model_version(ss.model_id),
            created_at=ss.created_at,
            detections=list(ss.detections),
            confirmed_ingredient_ids=list(ss.ingredient_ids),
        )

    def delete_user_scan_session(self, user_id: str, scan_id: str) -> None:
        ss = self._scan_sessions.get(scan_id)
        if ss is None or ss.user_id != user_id:
            raise AppError(
                status_code=404,
                code="SCAN_NOT_OWNED",
                message="Không tìm thấy phiên quét hoặc phiên quét không thuộc chủ sở hữu.",
                details={"scan_id": scan_id},
            )
        del self._scan_sessions[scan_id]
        # ADR-012 ON DELETE CASCADE: remove feedback bound to `scan_id`, keep `scan_id = None` untouched!
        to_delete = [
            ctx_key
            for ctx_key, fb in self._feedback_by_context.items()
            if fb.scan_session_id == scan_id
        ]
        for ctx_key in to_delete:
            del self._feedback_by_context[ctx_key]


class PostgresUserMixin:
    """PostgreSQL >= 15 implementation of Stage 4 User Features & Tier-2 USDA Nutrition."""

    def _connect(self):  # pragma: no cover - implemented on PostgresCatalogRepository
        raise NotImplementedError

    # --- USDA Nutrients ---
    def get_ingredient_nutrients_by_ids(
        self, ingredient_ids: list[str]
    ) -> dict[str, IngredientNutrient100g]:
        if not ingredient_ids:
            return {}
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    ingredient_id::text AS ingredient_id,
                    kcal_100g,
                    protein_100g,
                    fat_100g,
                    carb_100g,
                    source_url
                FROM public.ingredient_nutrients
                WHERE ingredient_id::text = ANY(%s)
                """,
                (ingredient_ids,),
            )
            rows = cur.fetchall()
        return {
            r["ingredient_id"]: IngredientNutrient100g(
                ingredient_id=r["ingredient_id"],
                kcal_100g=float(r["kcal_100g"]),
                protein_100g=float(r["protein_100g"]),
                fat_100g=float(r["fat_100g"]),
                carb_100g=float(r["carb_100g"]),
                source_url=str(r["source_url"]),
            )
            for r in rows
        }

    # --- Favorites (`FR-10`) ---
    def list_user_favorites(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> tuple[list[FavoriteView], int]:
        from app.schemas.recipes import RecipeSummary

        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    f.recipe_id::text AS recipe_id,
                    f.created_at,
                    r.slug,
                    r.name_vi,
                    r.cuisine_code,
                    r.prep_minutes,
                    r.cook_minutes,
                    r.cover_image_path,
                    COUNT(*) OVER() AS total_count
                FROM public.favorites f
                JOIN public.recipes r ON r.id = f.recipe_id
                WHERE f.user_id = %s::uuid
                  AND r.status = 'published'
                ORDER BY f.created_at DESC, f.recipe_id ASC
                LIMIT %s OFFSET %s
                """,
                (user_id, limit, offset),
            )
            rows = cur.fetchall()

        total = int(rows[0]["total_count"]) if rows else 0
        items = [
            FavoriteView(
                recipe_id=r["recipe_id"],
                created_at=r["created_at"],
                recipe=RecipeSummary(
                    id=r["recipe_id"],
                    slug=r["slug"],
                    name_vi=r["name_vi"],
                    cuisine_code=r["cuisine_code"],
                    prep_minutes=int(r["prep_minutes"]),
                    cook_minutes=int(r["cook_minutes"]),
                    total_minutes=int(r["prep_minutes"]) + int(r["cook_minutes"]),
                    cover_image_url=r.get("cover_image_path"),
                ),
            )
            for r in rows
        ]
        return items, total

    def add_user_favorite(self, user_id: str, recipe_id: str) -> tuple[FavoriteView, bool]:
        from app.schemas.recipes import RecipeSummary

        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id::text AS id,
                    slug,
                    name_vi,
                    cuisine_code,
                    prep_minutes,
                    cook_minutes,
                    cover_image_path
                FROM public.recipes
                WHERE id = %s::uuid
                  AND status = 'published'
                """,
                (recipe_id,),
            )
            rec_row = cur.fetchone()
            if not rec_row:
                raise AppError(
                    status_code=404,
                    code="RECIPE_NOT_FOUND",
                    message="Không tìm thấy công thức món ăn hoặc công thức chưa được xuất bản.",
                    details={"recipe_id": recipe_id},
                )

            cur.execute(
                """
                INSERT INTO public.favorites (user_id, recipe_id)
                VALUES (%s::uuid, %s::uuid)
                ON CONFLICT (user_id, recipe_id) DO NOTHING
                RETURNING created_at
                """,
                (user_id, recipe_id),
            )
            inserted = cur.fetchone()
            if inserted is not None:
                is_created = True
                created_at = inserted["created_at"]
            else:
                is_created = False
                cur.execute(
                    """
                    SELECT created_at
                    FROM public.favorites
                    WHERE user_id = %s::uuid AND recipe_id = %s::uuid
                    """,
                    (user_id, recipe_id),
                )
                ex = cur.fetchone()
                created_at = ex["created_at"] if ex else _now_utc()
            conn.commit()

        summary = RecipeSummary(
            id=rec_row["id"],
            slug=rec_row["slug"],
            name_vi=rec_row["name_vi"],
            cuisine_code=rec_row["cuisine_code"],
            prep_minutes=int(rec_row["prep_minutes"]),
            cook_minutes=int(rec_row["cook_minutes"]),
            total_minutes=int(rec_row["prep_minutes"]) + int(rec_row["cook_minutes"]),
            cover_image_url=rec_row.get("cover_image_path"),
        )
        return FavoriteView(recipe_id=recipe_id, created_at=created_at, recipe=summary), is_created

    def remove_user_favorite(self, user_id: str, recipe_id: str) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM public.favorites
                WHERE user_id = %s::uuid AND recipe_id = %s::uuid
                """,
                (user_id, recipe_id),
            )
            conn.commit()

    # --- Feedback Upsert (`FR-11`, `ADR-012`) ---
    def upsert_user_feedback(
        self, user_id: str, payload: FeedbackCreate
    ) -> tuple[FeedbackView, bool]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::text AS id
                FROM public.recipes
                WHERE id = %s::uuid AND status = 'published'
                """,
                (payload.recipe_id,),
            )
            if not cur.fetchone():
                raise AppError(
                    status_code=404,
                    code="RECIPE_NOT_FOUND",
                    message="Không tìm thấy công thức món ăn hoặc công thức chưa được xuất bản.",
                    details={"recipe_id": payload.recipe_id},
                )

            if payload.scan_id is not None:
                cur.execute(
                    """
                    SELECT user_id::text AS user_id
                    FROM public.scan_sessions
                    WHERE id = %s::uuid
                    """,
                    (payload.scan_id,),
                )
                ss_row = cur.fetchone()
                if not ss_row or ss_row["user_id"] != user_id:
                    raise AppError(
                        status_code=404,
                        code="SCAN_NOT_OWNED",
                        message="Không tìm thấy phiên quét hoặc phiên quét không thuộc chủ sở hữu.",
                        details={"scan_id": payload.scan_id},
                    )

            # Check prior existence in transaction (`IS NOT DISTINCT FROM` matches `UNIQUE NULLS NOT DISTINCT`)
            cur.execute(
                """
                SELECT id::text AS id
                FROM public.recommendation_feedback
                WHERE user_id = %s::uuid
                  AND recipe_id = %s::uuid
                  AND scan_session_id IS NOT DISTINCT FROM %s::uuid
                FOR UPDATE
                """,
                (user_id, payload.recipe_id, payload.scan_id),
            )
            existed = cur.fetchone() is not None

            cur.execute(
                """
                INSERT INTO public.recommendation_feedback (
                    user_id,
                    recipe_id,
                    scan_session_id,
                    rating,
                    note
                )
                VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s)
                ON CONFLICT ON CONSTRAINT uq_feedback_user_recipe_scan DO UPDATE
                SET rating = EXCLUDED.rating,
                    note = EXCLUDED.note,
                    updated_at = now()
                RETURNING
                    id::text AS id,
                    recipe_id::text AS recipe_id,
                    rating,
                    created_at
                """,
                (
                    user_id,
                    payload.recipe_id,
                    payload.scan_id,
                    payload.rating,
                    payload.note,
                ),
            )
            fb_row = cur.fetchone()
            conn.commit()

        assert fb_row is not None
        return (
            FeedbackView(
                id=fb_row["id"],
                recipe_id=fb_row["recipe_id"],
                rating=int(fb_row["rating"]),
                created_at=fb_row["created_at"],
            ),
            not existed,
        )

    def get_user_feedback_samples(self, user_id: str) -> list[FeedbackSample]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    user_id::text AS user_id,
                    recipe_id::text AS recipe_id,
                    rating,
                    updated_at
                FROM public.recommendation_feedback
                WHERE user_id = %s::uuid
                ORDER BY updated_at ASC
                """,
                (user_id,),
            )
            rows = cur.fetchall()
        return [
            FeedbackSample(
                user_id=r["user_id"],
                recipe_id=r["recipe_id"],
                rating=int(r["rating"]),
                updated_at=r["updated_at"],
            )
            for r in rows
        ]

    # --- Opt-in Scan History (`FR-12`, `TC-20`, `TC-28`, `TC-47`) ---
    def create_scan_session_with_detections(
        self,
        user_id: str,
        model_id: str,
        detections: list[Detection] | None = None,
        confirmed_ingredient_ids: list[str] | None = None,
        scan_id: str | None = None,
    ) -> str:
        sid = scan_id or str(uuid.uuid4())
        dets = list(detections or [])
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.scan_sessions (id, user_id, model_id)
                VALUES (%s::uuid, %s::uuid, %s::uuid)
                RETURNING id::text AS id
                """,
                (sid, user_id, model_id),
            )
            if dets:
                cur.execute(
                    """
                    SELECT id::text AS id, class_index
                    FROM public.ai_labels
                    WHERE model_id = %s::uuid
                    """,
                    (model_id,),
                )
                lbl_by_idx = {int(r["class_index"]): r["id"] for r in cur.fetchall()}
                for d in dets:
                    lbl_id = lbl_by_idx.get(d.class_index)
                    if not lbl_id:
                        continue
                    cur.execute(
                        """
                        INSERT INTO public.scan_detections (
                            scan_session_id,
                            ai_label_id,
                            confidence,
                            needs_confirmation,
                            x1, y1, x2, y2
                        )
                        VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            sid,
                            lbl_id,
                            d.confidence,
                            d.needs_confirmation,
                            d.bbox.x1,
                            d.bbox.y1,
                            d.bbox.x2,
                            d.bbox.y2,
                        ),
                    )

            if confirmed_ingredient_ids is not None:
                ing_ids = list(confirmed_ingredient_ids)
                prov = "corrected"
            else:
                seen: set[str] = set()
                ing_ids = []
                for d in dets:
                    if d.ingredient_id and d.ingredient_id not in seen:
                        seen.add(d.ingredient_id)
                        ing_ids.append(d.ingredient_id)
                prov = "ai"

            for iid in ing_ids:
                cur.execute(
                    """
                    INSERT INTO public.scan_ingredients (scan_session_id, ingredient_id, provenance)
                    VALUES (%s::uuid, %s::uuid, %s)
                    ON CONFLICT (scan_session_id, ingredient_id) DO NOTHING
                    """,
                    (sid, iid, prov),
                )
            conn.commit()
        return sid

    def list_user_scan_sessions(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> tuple[list[ScanSessionSummary], int]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    ss.id::text AS id,
                    m.version AS model_version,
                    ss.created_at,
                    (
                        SELECT COUNT(*)
                        FROM public.scan_ingredients si
                        WHERE si.scan_session_id = ss.id
                    ) AS ingredients_count,
                    COUNT(*) OVER() AS total_count
                FROM public.scan_sessions ss
                JOIN public.ai_models m ON m.id = ss.model_id
                WHERE ss.user_id = %s::uuid
                ORDER BY ss.created_at DESC, ss.id ASC
                LIMIT %s OFFSET %s
                """,
                (user_id, limit, offset),
            )
            rows = cur.fetchall()

        total = int(rows[0]["total_count"]) if rows else 0
        items = [
            ScanSessionSummary(
                id=r["id"],
                model_version=str(r["model_version"]),
                created_at=r["created_at"],
                ingredients_count=int(r["ingredients_count"]),
            )
            for r in rows
        ]
        return items, total

    def get_user_scan_session_detail(self, user_id: str, scan_id: str) -> ScanSessionDetail:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    ss.id::text AS id,
                    ss.user_id::text AS user_id,
                    m.version AS model_version,
                    ss.created_at
                FROM public.scan_sessions ss
                JOIN public.ai_models m ON m.id = ss.model_id
                WHERE ss.id = %s::uuid
                """,
                (scan_id,),
            )
            ss_row = cur.fetchone()
            if not ss_row or ss_row["user_id"] != user_id:
                raise AppError(
                    status_code=404,
                    code="SCAN_NOT_OWNED",
                    message="Không tìm thấy phiên quét hoặc phiên quét không thuộc chủ sở hữu.",
                    details={"scan_id": scan_id},
                )

            cur.execute(
                """
                SELECT
                    al.class_index,
                    al.class_name,
                    al.ingredient_id::text AS ingredient_id,
                    i.name_vi AS ingredient_name,
                    sd.confidence,
                    sd.needs_confirmation,
                    sd.x1,
                    sd.y1,
                    sd.x2,
                    sd.y2
                FROM public.scan_detections sd
                JOIN public.ai_labels al ON al.id = sd.ai_label_id
                LEFT JOIN public.ingredients i ON i.id = al.ingredient_id
                WHERE sd.scan_session_id = %s::uuid
                ORDER BY sd.confidence DESC, al.class_index ASC
                """,
                (scan_id,),
            )
            det_rows = cur.fetchall()

            cur.execute(
                """
                SELECT ingredient_id::text AS ingredient_id
                FROM public.scan_ingredients
                WHERE scan_session_id = %s::uuid
                ORDER BY ingredient_id ASC
                """,
                (scan_id,),
            )
            confirmed_ids = [r["ingredient_id"] for r in cur.fetchall()]

        detections = [
            Detection(
                class_index=int(d["class_index"]),
                class_name=str(d["class_name"]),
                ingredient_id=d.get("ingredient_id"),
                ingredient_name=d.get("ingredient_name"),
                confidence=float(d["confidence"]),
                needs_confirmation=bool(d["needs_confirmation"]),
                bbox=BBox(
                    x1=float(d["x1"]),
                    y1=float(d["y1"]),
                    x2=float(d["x2"]),
                    y2=float(d["y2"]),
                ),
            )
            for d in det_rows
        ]
        return ScanSessionDetail(
            id=ss_row["id"],
            model_version=str(ss_row["model_version"]),
            created_at=ss_row["created_at"],
            detections=detections,
            confirmed_ingredient_ids=confirmed_ids,
        )

    def delete_user_scan_session(self, user_id: str, scan_id: str) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id::text AS user_id
                FROM public.scan_sessions
                WHERE id = %s::uuid
                """,
                (scan_id,),
            )
            row = cur.fetchone()
            if not row or row["user_id"] != user_id:
                raise AppError(
                    status_code=404,
                    code="SCAN_NOT_OWNED",
                    message="Không tìm thấy phiên quét hoặc phiên quét không thuộc chủ sở hữu.",
                    details={"scan_id": scan_id},
                )
            cur.execute(
                "DELETE FROM public.scan_sessions WHERE id = %s::uuid",
                (scan_id,),
            )
            conn.commit()
