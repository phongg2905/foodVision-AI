"""Admin CMS & Nutrition Tag Repository Mixins (`FR-09a`, `FR-13`..`FR-17`, `BR-01`..`BR-12`, `ADR-013`)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from app.core.errors import AppError
from app.schemas.admin import (
    AILabel,
    AILabelCreate,
    AILabelPatch,
    AIModel,
    AIModelCreate,
    AdminRecipeDetail,
    AdminRecipeView,
    AuditLog,
    IngredientCreate,
    IngredientPatch,
    IngredientTagMapRequest,
    NutritionTagCreate,
    NutritionTagPatch,
    RecipeCreate,
    RecipeIngredientInput,
    RecipePatch,
    scrub_audit_payload,
)
from app.schemas.catalog import Ingredient, IngredientCategory, NutritionTag
from app.schemas.recipes import NutritionEvidence
from app.services.vietnamese_search import norm_vi, rank_ingredient_candidates

if TYPE_CHECKING:
    from app.core.database import (
        IngredientRecord,
        RecipeIngredientRecord,
        RecipeRecord,
        RecipeStepRecord,
    )

DEFAULT_ADMIN_ID = "00000000-0000-4000-8000-000000000001"

_ROLE_DEFAULT_WEIGHT: dict[str, float] = {
    "core": 4.0,
    "secondary": 2.0,
    "spice": 1.0,
    "optional": 0.0,
}


@dataclass
class NutritionTagRecord:
    id: str
    code: str
    name_vi: str
    description: str
    is_active: bool = True

    def to_schema(self) -> NutritionTag:
        return NutritionTag(
            id=self.id,
            code=self.code,
            name_vi=self.name_vi,
            description=self.description,
            is_active=self.is_active,
        )


@dataclass
class IngredientTagLinkRecord:
    ingredient_id: str
    nutrition_tag_id: str
    source_url: str
    note: str | None = None


@dataclass
class AdminAIModelRecord:
    id: str
    version: str
    family: str
    dataset_version: str
    artifact_ref: str
    status: str = "draft"
    confidence_threshold: float = 0.25
    class_count: int = 20
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_schema(self) -> AIModel:
        return AIModel(
            id=self.id,
            version=self.version,
            family=self.family,
            dataset_version=self.dataset_version,
            status=self.status,  # type: ignore[arg-type]
            confidence_threshold=round(float(self.confidence_threshold), 4),
        )


@dataclass
class AdminAILabelRecord:
    id: str
    model_id: str
    class_index: int
    class_name: str
    ingredient_id: str

    def to_schema(self) -> AILabel:
        return AILabel(
            id=self.id,
            model_id=self.model_id,
            class_index=self.class_index,
            class_name=self.class_name,
            ingredient_id=self.ingredient_id,
        )


# Backward-compatible aliases within admin_repo module
AIModelRecord = AdminAIModelRecord
AILabelRecord = AdminAILabelRecord


@dataclass
class AuditLogRecord:
    id: str
    actor_id: str
    action: str
    entity_type: str
    entity_id: str
    before_json: dict[str, Any] | None = None
    after_json: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_schema(self) -> AuditLog:
        return AuditLog(
            id=self.id,
            actor_id=self.actor_id,
            action=self.action,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            created_at=self.created_at,
        )


def resolve_recipe_ingredient_defaults(
    inp: RecipeIngredientInput,
    ing_category: IngredientCategory,
) -> tuple[str, str, float]:
    """Resolve `(role, dish_role, weight)` according to `ADR-013` (`4-2-1-0` & `main/sub`)."""
    if not inp.is_required:
        role = "optional"
        dish_role = inp.dish_role or "sub"
        weight = float(inp.weight) if inp.weight is not None else 0.0
        return role, dish_role, weight

    if inp.role is not None:
        role = inp.role
    else:
        role = "spice" if ing_category == "pantry" else "core"

    if inp.dish_role is not None:
        dish_role = inp.dish_role
    else:
        dish_role = "main" if (role == "core" and ing_category != "pantry") else "sub"

    weight = float(inp.weight) if inp.weight is not None else _ROLE_DEFAULT_WEIGHT[role]
    return role, dish_role, weight


def check_recipe_publishable_reasons(
    prep_minutes: int,
    cook_minutes: int,
    ingredients: list[RecipeIngredientRecord],
    steps: list[RecipeStepRecord],
    ingredient_lookup: dict[str, IngredientRecord],
) -> list[str]:
    """Evaluate all 4 `BR-01` + `BR-05` + `ADR-013` publishability invariants."""
    reasons: list[str] = []

    # 1. At least 1 step
    if not steps:
        reasons.append("missing_steps")

    # 2. At least 1 required non-pantry ingredient & positive total required weight
    has_required_main = any(ri.is_required and ri.category != "pantry" for ri in ingredients)
    total_req_weight = sum(
        float(ri.weight) for ri in ingredients if ri.is_required and ri.role != "optional"
    )
    if not has_required_main or total_req_weight <= 0:
        reasons.append("missing_required_main_ingredient")

    # 3. Every linked ingredient must exist and currently be active (`is_active = true`)
    has_inactive = any(
        (ingredient_lookup.get(ri.ingredient_id) is None or not ingredient_lookup[ri.ingredient_id].is_active)
        for ri in ingredients
    )
    if has_inactive:
        reasons.append("inactive_ingredient")

    # 4. Positive total time & no individual step exceeds `prep_minutes + cook_minutes`
    total_minutes = prep_minutes + cook_minutes
    if total_minutes <= 0 or any(
        st.estimated_minutes is not None and st.estimated_minutes > total_minutes
        for st in steps
    ):
        reasons.append("step_exceeds_total_minutes")

    return reasons


def build_default_nutrition_tags() -> list[NutritionTagRecord]:
    return [
        NutritionTagRecord(
            id="33333333-3333-4333-8333-333333333301",
            code="HIGH_PROTEIN_PLANT",
            name_vi="Giàu đạm thực vật",
            description="Cung cấp protein thực vật lành mạnh từ đậu nành.",
            is_active=True,
        ),
        NutritionTagRecord(
            id="33333333-3333-4333-8333-333333333302",
            code="LYCOPENE_ANTIOXIDANT",
            name_vi="Giàu chất chống oxy hóa",
            description="Cung cấp lycopene và vitamin tự nhiên từ rau quả tươi.",
            is_active=True,
        ),
        NutritionTagRecord(
            id="33333333-3333-4333-8333-333333333399",
            code="ARCHIVED_TAG",
            name_vi="Nhãn dinh dưỡng tạm ẩn",
            description="Nhãn không còn hiển thị công khai.",
            is_active=False,
        ),
    ]


# ==============================================================================
# IN-MEMORY ADMIN MIXIN
# ==============================================================================


class InMemoryAdminMixin:
    """In-memory Admin CMS & NutritionTag operations for deterministic unit/integration testing."""

    _ingredients: dict[str, IngredientRecord]
    _recipes: dict[str, RecipeRecord]
    _profiles: dict[str, str]
    _nutrition_tags: dict[str, NutritionTagRecord]
    _ingredient_nutrition_tags: dict[str, list[IngredientTagLinkRecord]]
    _ai_models: dict[str, AdminAIModelRecord]
    _ai_labels: dict[str, AdminAILabelRecord]
    _audit_logs: list[AuditLogRecord]

    def _init_admin_state(self) -> None:
        self._profiles = {DEFAULT_ADMIN_ID: "admin"}
        self._nutrition_tags = {t.id: t for t in build_default_nutrition_tags()}
        self._ingredient_nutrition_tags = {
            "11111111-1111-4111-8111-111111111103": [
                IngredientTagLinkRecord(
                    ingredient_id="11111111-1111-4111-8111-111111111103",
                    nutrition_tag_id="33333333-3333-4333-8333-333333333301",
                    source_url="https://fdc.nal.usda.gov/",
                    note="Đậu hũ cung cấp đạm thực vật.",
                )
            ]
        }
        self._ai_models = {}
        self._ai_labels = {}
        self._audit_logs = []

    def _sync_active_ai_model_to_admin(self, active_model: Any) -> None:
        """Populate in-memory Admin `_ai_models` and `_ai_labels` from a runtime `AIModelRecord` (`A5`)."""
        if active_model is None:
            return
        for other in self._ai_models.values():
            if other.id != active_model.id and other.status == "active" and active_model.status == "active":
                other.status = "archived"
        self._ai_models[active_model.id] = AdminAIModelRecord(
            id=active_model.id,
            version=active_model.version,
            family=active_model.family,
            dataset_version=active_model.dataset_version,
            artifact_ref=active_model.artifact_ref,
            status=active_model.status,
            confidence_threshold=float(active_model.confidence_threshold),
            class_count=int(active_model.class_count),
        )
        for lbl in getattr(active_model, "labels_by_index", {}).values():
            self._ai_labels[lbl.id] = AdminAILabelRecord(
                id=lbl.id,
                model_id=lbl.model_id,
                class_index=int(lbl.class_index),
                class_name=lbl.class_name,
                ingredient_id=lbl.ingredient_id,
            )

    def set_profile_role(self, user_id: str, role: str) -> None:
        self._profiles[user_id] = role

    def get_profile_role(self, user_id: str) -> str | None:
        return self._profiles.get(user_id, "user")

    def _record_audit(
        self,
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        before_json: dict[str, Any] | None = None,
        after_json: dict[str, Any] | None = None,
    ) -> None:
        self._audit_logs.insert(
            0,
            AuditLogRecord(
                id=str(uuid.uuid4()),
                actor_id=actor_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                before_json=scrub_audit_payload(before_json) if before_json is not None else None,
                after_json=scrub_audit_payload(after_json) if after_json is not None else None,
                created_at=datetime.now(timezone.utc),
            ),
        )

    def _compute_recipe_nutrition_evidence(self, rec: RecipeRecord) -> list[NutritionEvidence]:
        grouped: dict[str, tuple[NutritionTagRecord, list[str], str | None]] = {}
        has_dynamic = False
        for ri in rec.ingredients:
            links = self._ingredient_nutrition_tags.get(ri.ingredient_id, [])
            if links:
                has_dynamic = True
            for lnk in links:
                tag = self._nutrition_tags.get(lnk.nutrition_tag_id)
                if tag is None or not tag.is_active:
                    continue
                if tag.id not in grouped:
                    grouped[tag.id] = (tag, [lnk.source_url], lnk.note)
                else:
                    _, urls, existing_note = grouped[tag.id]
                    if lnk.source_url not in urls:
                        urls.append(lnk.source_url)
                    grouped[tag.id] = (tag, urls, existing_note or lnk.note)
        if has_dynamic:
            return [
                NutritionEvidence(tag=t.to_schema(), source_urls=urls, note=note)
                for t, urls, note in sorted(grouped.values(), key=lambda x: x[0].code)
            ]
        return [ne.to_view() for ne in rec.nutrition_evidence if ne.tag_is_active]

    def _recipe_to_admin_view(self, rec: RecipeRecord) -> AdminRecipeView:
        return AdminRecipeView(
            id=rec.id,
            slug=rec.slug,
            name_vi=rec.name_vi,
            status=rec.status,  # type: ignore[arg-type]
            updated_at=rec.updated_at,
        )

    def _recipe_to_admin_detail(self, rec: RecipeRecord) -> AdminRecipeDetail:
        return AdminRecipeDetail(
            id=rec.id,
            slug=rec.slug,
            name_vi=rec.name_vi,
            cuisine_code=rec.cuisine_code,
            prep_minutes=rec.prep_minutes,
            cook_minutes=rec.cook_minutes,
            total_minutes=rec.total_minutes,
            cover_image_url=rec.cover_image_url,
            description=rec.description,
            country_code=rec.country_code,
            ingredients=[ing.to_view() for ing in rec.ingredients],
            steps=[st.to_view() for st in rec.steps],
            nutrition_evidence=self._compute_recipe_nutrition_evidence(rec),
            source_name=rec.source_name,
            source_url=rec.source_url,
            content_license=rec.content_license,
            status=rec.status,  # type: ignore[arg-type]
            author_id=rec.author_id,
            updated_at=rec.updated_at,
        )

    def _build_recipe_sublists(
        self,
        ing_inputs: list[RecipeIngredientInput],
        step_inputs: list[ Any],
    ) -> tuple[list[RecipeIngredientRecord], list[RecipeStepRecord], list[str]]:
        from app.core.database import RecipeIngredientRecord, RecipeStepRecord

        built_ings: list[RecipeIngredientRecord] = []
        allergen_set: set[str] = set()
        for idx, inp in enumerate(ing_inputs):
            ing_rec = self._ingredients.get(inp.ingredient_id)
            if ing_rec is None:
                raise AppError(
                    status_code=422,
                    code="INVALID_INGREDIENTS",
                    message="Nguyên liệu gắn với công thức không tồn tại trong danh mục.",
                    details={
                        "invalid_ids": [inp.ingredient_id],
                        "reason": "unknown_or_inactive_id",
                    },
                )
            role, dish_role, weight = resolve_recipe_ingredient_defaults(inp, ing_rec.category)
            built_ings.append(
                RecipeIngredientRecord(
                    ingredient_id=ing_rec.id,
                    name_vi=ing_rec.name_vi,
                    category=ing_rec.category,
                    is_required=inp.is_required,
                    role=role,
                    dish_role=dish_role,
                    weight=weight,
                    grams=inp.grams,
                    display_quantity=inp.display_quantity,
                    sort_order=inp.sort_order if inp.sort_order else idx + 1,
                )
            )
            allergen_set.update(ing_rec.allergen_ids)

        built_ings.sort(key=lambda r: (r.sort_order, r.name_vi))
        built_steps = [
            RecipeStepRecord(
                step_no=st.step_no,
                instruction=st.instruction,
                estimated_minutes=st.estimated_minutes,
            )
            for st in sorted(step_inputs, key=lambda s: s.step_no)
        ]
        return built_ings, built_steps, sorted(allergen_set)

    # ---- Public & Admin Nutrition Tags ----

    def list_active_nutrition_tags(self) -> list[NutritionTag]:
        tags = [t for t in self._nutrition_tags.values() if t.is_active]
        tags.sort(key=lambda t: t.code)
        return [t.to_schema() for t in tags]

    def admin_list_nutrition_tags(self) -> list[NutritionTag]:
        tags = sorted(self._nutrition_tags.values(), key=lambda t: t.code)
        return [t.to_schema() for t in tags]

    def admin_create_nutrition_tag(
        self, payload: NutritionTagCreate, actor_id: str
    ) -> NutritionTag:
        if any(t.code.lower() == payload.code.lower() for t in self._nutrition_tags.values()):
            raise AppError(
                status_code=409,
                code="DUPLICATE_SLUG",
                message=f"Mã nhãn dinh dưỡng '{payload.code}' đã tồn tại.",
                details={"field": "code", "value": payload.code},
            )
        rec = NutritionTagRecord(
            id=str(uuid.uuid4()),
            code=payload.code,
            name_vi=payload.name_vi,
            description=payload.description,
            is_active=payload.is_active,
        )
        self._nutrition_tags[rec.id] = rec
        out = rec.to_schema()
        self._record_audit(
            actor_id=actor_id,
            action="create",
            entity_type="nutrition_tags",
            entity_id=rec.id,
            after_json=out.model_dump(),
        )
        return out

    def admin_patch_nutrition_tag(
        self, tag_id: str, payload: NutritionTagPatch, actor_id: str
    ) -> NutritionTag:
        rec = self._nutrition_tags.get(tag_id)
        if rec is None:
            raise AppError(
                status_code=404,
                code="NOT_FOUND",
                message="Không tìm thấy nhãn dinh dưỡng.",
                details={"nutrition_tag_id": tag_id},
            )
        before = rec.to_schema().model_dump()
        if payload.name_vi is not None:
            rec.name_vi = payload.name_vi
        if payload.description is not None:
            rec.description = payload.description
        if payload.is_active is not None:
            rec.is_active = payload.is_active

        # Synchronize cached RecipeRecord.nutrition_evidence across all in-memory recipes (`A5`)
        from app.core.database import NutritionEvidenceRecord

        for recipe in self._recipes.values():
            updated_ev: list[NutritionEvidenceRecord] = []
            for ne in recipe.nutrition_evidence:
                if ne.tag_id == tag_id:
                    updated_ev.append(
                        NutritionEvidenceRecord(
                            tag_id=rec.id,
                            tag_code=rec.code,
                            tag_name_vi=rec.name_vi,
                            tag_description=rec.description,
                            tag_is_active=rec.is_active,
                            source_urls=list(ne.source_urls),
                            note=ne.note,
                        )
                    )
                else:
                    updated_ev.append(ne)
            recipe.nutrition_evidence = [e for e in updated_ev if e.tag_is_active]
            if any(
                any(lnk.nutrition_tag_id == tag_id for lnk in self._ingredient_nutrition_tags.get(ri.ingredient_id, []))
                for ri in recipe.ingredients
            ):
                dyn = self._compute_recipe_nutrition_evidence(recipe)
                recipe.nutrition_evidence = [
                    NutritionEvidenceRecord(
                        tag_id=ev.tag.id,
                        tag_code=ev.tag.code,
                        tag_name_vi=ev.tag.name_vi,
                        tag_description=ev.tag.description,
                        tag_is_active=ev.tag.is_active,
                        source_urls=list(ev.source_urls),
                        note=ev.note,
                    )
                    for ev in dyn
                ]

        out = rec.to_schema()
        self._record_audit(
            actor_id=actor_id,
            action="patch",
            entity_type="nutrition_tags",
            entity_id=rec.id,
            before_json=before,
            after_json=out.model_dump(),
        )
        return out

    def admin_set_ingredient_nutrition_tags(
        self,
        ingredient_id: str,
        payload: IngredientTagMapRequest,
        actor_id: str,
    ) -> list[NutritionEvidence]:
        ing = self._ingredients.get(ingredient_id)
        if ing is None:
            raise AppError(
                status_code=404,
                code="NOT_FOUND",
                message="Không tìm thấy nguyên liệu.",
                details={"ingredient_id": ingredient_id},
            )
        for item in payload.tags:
            if item.nutrition_tag_id not in self._nutrition_tags:
                raise AppError(
                    status_code=422,
                    code="VALIDATION_ERROR",
                    message="Một hoặc nhiều nutrition_tag_id không tồn tại.",
                    details={"field": "nutrition_tag_id", "value": item.nutrition_tag_id},
                )

        new_links = [
            IngredientTagLinkRecord(
                ingredient_id=ingredient_id,
                nutrition_tag_id=item.nutrition_tag_id,
                source_url=item.source_url,
                note=item.note,
            )
            for item in payload.tags
        ]
        self._ingredient_nutrition_tags[ingredient_id] = new_links

        # Keep RecipeRecord.nutrition_evidence synchronized for public GET /recipes/{id} (TC-25)
        from app.core.database import NutritionEvidenceRecord

        for rec in self._recipes.values():
            if any(ri.ingredient_id == ingredient_id for ri in rec.ingredients):
                dyn = self._compute_recipe_nutrition_evidence(rec)
                rec.nutrition_evidence = [
                    NutritionEvidenceRecord(
                        tag_id=ev.tag.id,
                        tag_code=ev.tag.code,
                        tag_name_vi=ev.tag.name_vi,
                        tag_description=ev.tag.description,
                        tag_is_active=ev.tag.is_active,
                        source_urls=list(ev.source_urls),
                        note=ev.note,
                    )
                    for ev in dyn
                ]

        evidences = [
            NutritionEvidence(
                tag=self._nutrition_tags[lnk.nutrition_tag_id].to_schema(),
                source_urls=[lnk.source_url],
                note=lnk.note,
            )
            for lnk in new_links
        ]
        self._record_audit(
            actor_id=actor_id,
            action="set_nutrition_tags",
            entity_type="ingredients",
            entity_id=ingredient_id,
            after_json={"tags": [t.model_dump() for t in payload.tags]},
        )
        return evidences

    # ---- Admin Recipes ----

    def admin_list_recipes(
        self,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[AdminRecipeView], int]:
        items = list(self._recipes.values())
        if status:
            items = [r for r in items if r.status == status]
        items.sort(key=lambda r: (r.updated_at, r.id), reverse=True)
        total = len(items)
        return [self._recipe_to_admin_view(r) for r in items[offset : offset + limit]], total

    def admin_get_recipe(self, recipe_id: str) -> AdminRecipeDetail:
        rec = self._recipes.get(recipe_id)
        if rec is None:
            raise AppError(
                status_code=404,
                code="RECIPE_NOT_FOUND",
                message="Không tìm thấy công thức.",
                details={"recipe_id": recipe_id},
            )
        return self._recipe_to_admin_detail(rec)

    def admin_create_recipe(self, payload: RecipeCreate, actor_id: str) -> AdminRecipeView:
        from app.core.database import RecipeRecord

        if any(r.slug.lower() == payload.slug.lower() for r in self._recipes.values()):
            raise AppError(
                status_code=409,
                code="DUPLICATE_SLUG",
                message=f"Slug công thức '{payload.slug}' đã tồn tại.",
                details={"field": "slug", "value": payload.slug},
            )

        built_ings, built_steps, allergens = self._build_recipe_sublists(
            payload.ingredients, payload.steps
        )
        now = datetime.now(timezone.utc)
        rec = RecipeRecord(
            id=str(uuid.uuid4()),
            slug=payload.slug,
            name_vi=payload.name_vi,
            description=payload.description,
            cuisine_code=payload.cuisine_code,
            country_code=payload.country_code,
            prep_minutes=payload.prep_minutes,
            cook_minutes=payload.cook_minutes,
            status="draft",
            cover_image_url=payload.cover_image_path,
            source_name=payload.source_name,
            source_url=payload.source_url,
            content_license=payload.content_license,
            ingredients=built_ings,
            steps=built_steps,
            allergen_ids=allergens,
            author_id=actor_id,
            updated_at=now,
        )
        self._recipes[rec.id] = rec
        view = self._recipe_to_admin_view(rec)
        self._record_audit(
            actor_id=actor_id,
            action="create",
            entity_type="recipes",
            entity_id=rec.id,
            after_json=view.model_dump(),
        )
        return view

    def admin_patch_recipe(
        self, recipe_id: str, payload: RecipePatch, actor_id: str
    ) -> AdminRecipeView:
        rec = self._recipes.get(recipe_id)
        if rec is None:
            raise AppError(
                status_code=404,
                code="RECIPE_NOT_FOUND",
                message="Không tìm thấy công thức.",
                details={"recipe_id": recipe_id},
            )

        if payload.slug is not None and any(
            r.id != recipe_id and r.slug.lower() == payload.slug.lower()
            for r in self._recipes.values()
        ):
            raise AppError(
                status_code=409,
                code="DUPLICATE_SLUG",
                message=f"Slug công thức '{payload.slug}' đã tồn tại.",
                details={"field": "slug", "value": payload.slug},
            )

        next_prep = payload.prep_minutes if payload.prep_minutes is not None else rec.prep_minutes
        next_cook = payload.cook_minutes if payload.cook_minutes is not None else rec.cook_minutes
        if next_prep + next_cook <= 0:
            raise AppError(
                status_code=422,
                code="VALIDATION_ERROR",
                message="Tổng thời gian chế biến (prep_minutes + cook_minutes) bắt buộc > 0.",
                details={"field": "cook_minutes", "reason": "non_positive_total_minutes"},
            )

        next_ings = rec.ingredients
        next_allergens = rec.allergen_ids
        next_steps = rec.steps

        if payload.ingredients is not None or payload.steps is not None:
            if payload.ingredients is not None:
                tmp_ings, _, next_allergens = self._build_recipe_sublists(
                    payload.ingredients, []
                )
                next_ings = tmp_ings
            if payload.steps is not None:
                _, tmp_steps, _ = self._build_recipe_sublists([], payload.steps)
                next_steps = tmp_steps

        # BR-01 & TC-38(4): If currently published, patched state MUST remain publishable!
        if rec.status == "published":
            reasons = check_recipe_publishable_reasons(
                prep_minutes=next_prep,
                cook_minutes=next_cook,
                ingredients=next_ings,
                steps=next_steps,
                ingredient_lookup=self._ingredients,
            )
            if reasons:
                raise AppError(
                    status_code=400,
                    code="RECIPE_NOT_PUBLISHABLE",
                    message="Không thể lưu thay đổi làm công thức đang published vi phạm điều kiện xuất bản (BR-01).",
                    details={"recipe_id": recipe_id, "reasons": reasons},
                )

        before = self._recipe_to_admin_view(rec).model_dump()
        fields_set = payload.model_fields_set
        if "slug" in fields_set and payload.slug is not None:
            rec.slug = payload.slug
        if "name_vi" in fields_set and payload.name_vi is not None:
            rec.name_vi = payload.name_vi
        if "description" in fields_set:
            rec.description = payload.description
        if "cuisine_code" in fields_set and payload.cuisine_code is not None:
            rec.cuisine_code = payload.cuisine_code
        if "country_code" in fields_set:
            rec.country_code = payload.country_code
        rec.prep_minutes = next_prep
        rec.cook_minutes = next_cook
        if "cover_image_path" in fields_set:
            rec.cover_image_url = payload.cover_image_path
        if "source_name" in fields_set:
            rec.source_name = payload.source_name
        if "source_url" in fields_set:
            rec.source_url = payload.source_url
        if "content_license" in fields_set:
            rec.content_license = payload.content_license
        rec.ingredients = next_ings
        rec.steps = next_steps
        rec.allergen_ids = next_allergens
        rec.updated_at = datetime.now(timezone.utc)

        view = self._recipe_to_admin_view(rec)
        self._record_audit(
            actor_id=actor_id,
            action="patch",
            entity_type="recipes",
            entity_id=rec.id,
            before_json=before,
            after_json=view.model_dump(),
        )
        return view

    def admin_set_recipe_status(
        self, recipe_id: str, target_status: str, actor_id: str
    ) -> AdminRecipeView:
        rec = self._recipes.get(recipe_id)
        if rec is None:
            raise AppError(
                status_code=404,
                code="RECIPE_NOT_FOUND",
                message="Không tìm thấy công thức.",
                details={"recipe_id": recipe_id},
            )
        if target_status == "published":
            reasons = check_recipe_publishable_reasons(
                prep_minutes=rec.prep_minutes,
                cook_minutes=rec.cook_minutes,
                ingredients=rec.ingredients,
                steps=rec.steps,
                ingredient_lookup=self._ingredients,
            )
            if reasons:
                raise AppError(
                    status_code=400,
                    code="RECIPE_NOT_PUBLISHABLE",
                    message="Công thức chưa thỏa mãn đầy đủ 4 điều kiện xuất bản (BR-01).",
                    details={"recipe_id": recipe_id, "reasons": reasons},
                )

        before = self._recipe_to_admin_view(rec).model_dump()
        rec.status = target_status
        rec.updated_at = datetime.now(timezone.utc)
        view = self._recipe_to_admin_view(rec)
        self._record_audit(
            actor_id=actor_id,
            action=f"status:{target_status}",
            entity_type="recipes",
            entity_id=rec.id,
            before_json=before,
            after_json=view.model_dump(),
        )
        return view

    # ---- Admin Ingredients ----

    def admin_list_ingredients(
        self,
        q: str | None = None,
        category: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Ingredient], int]:
        candidates = list(self._ingredients.values())
        if category:
            candidates = [ing for ing in candidates if ing.category == category]
        if q and q.strip():
            ranked = rank_ingredient_candidates(q, candidates)
            ordered = [r[0] for r in ranked]
        else:
            ordered = sorted(candidates, key=lambda x: (norm_vi(x.name_vi), x.id))
        total = len(ordered)
        return [r.to_schema() for r in ordered[offset : offset + limit]], total

    def admin_create_ingredient(
        self, payload: IngredientCreate, actor_id: str
    ) -> Ingredient:
        from app.core.database import IngredientRecord

        if any(i.slug.lower() == payload.slug.lower() for i in self._ingredients.values()):
            raise AppError(
                status_code=409,
                code="DUPLICATE_SLUG",
                message=f"Slug nguyên liệu '{payload.slug}' đã tồn tại.",
                details={"field": "slug", "value": payload.slug},
            )
        rec = IngredientRecord(
            id=str(uuid.uuid4()),
            slug=payload.slug,
            name_vi=payload.name_vi,
            category=payload.category,
            is_active=payload.is_active,
            aliases=list(payload.aliases),
        )
        self._ingredients[rec.id] = rec
        out = rec.to_schema()
        self._record_audit(
            actor_id=actor_id,
            action="create",
            entity_type="ingredients",
            entity_id=rec.id,
            after_json={**out.model_dump(), "aliases": list(rec.aliases)},
        )
        return out

    def admin_patch_ingredient(
        self, ingredient_id: str, payload: IngredientPatch, actor_id: str
    ) -> Ingredient:
        rec = self._ingredients.get(ingredient_id)
        if rec is None:
            raise AppError(
                status_code=404,
                code="NOT_FOUND",
                message="Không tìm thấy nguyên liệu.",
                details={"ingredient_id": ingredient_id},
            )
        if payload.slug is not None and any(
            i.id != ingredient_id and i.slug.lower() == payload.slug.lower()
            for i in self._ingredients.values()
        ):
            raise AppError(
                status_code=409,
                code="DUPLICATE_SLUG",
                message=f"Slug nguyên liệu '{payload.slug}' đã tồn tại.",
                details={"field": "slug", "value": payload.slug},
            )

        deactivating = payload.is_active is False and rec.is_active is True
        changing_cat = payload.category is not None and payload.category != rec.category
        if deactivating or changing_cat:
            affected_recipes = sorted(
                r.id
                for r in self._recipes.values()
                if r.status == "published"
                and any(ri.ingredient_id == ingredient_id for ri in r.ingredients)
            )
            affected_models = sorted(
                {
                    lbl.model_id
                    for lbl in self._ai_labels.values()
                    if lbl.ingredient_id == ingredient_id
                    and self._ai_models.get(lbl.model_id) is not None
                    and self._ai_models[lbl.model_id].status in ("draft", "active")
                }
            )
            if affected_recipes or affected_models:
                raise AppError(
                    status_code=400,
                    code="INGREDIENT_IN_USE",
                    message="Không thể tắt hoạt động hoặc đổi phân loại nguyên liệu đang được dùng trong công thức published hoặc model AI draft/active.",
                    details={
                        "ingredient_id": ingredient_id,
                        "affected_published_recipe_ids": affected_recipes,
                        "affected_active_or_draft_model_ids": affected_models,
                    },
                )

        before = {**rec.to_schema().model_dump(), "aliases": list(rec.aliases)}
        if payload.slug is not None:
            rec.slug = payload.slug
        if payload.name_vi is not None:
            rec.name_vi = payload.name_vi
        if payload.category is not None:
            rec.category = payload.category
            # Sync cached category inside in-memory recipes referencing this ingredient
            for r in self._recipes.values():
                for ri in r.ingredients:
                    if ri.ingredient_id == ingredient_id:
                        ri.category = payload.category
        if payload.is_active is not None:
            rec.is_active = payload.is_active
        if payload.aliases is not None:
            rec.aliases = list(payload.aliases)

        out = rec.to_schema()
        self._record_audit(
            actor_id=actor_id,
            action="patch",
            entity_type="ingredients",
            entity_id=rec.id,
            before_json=before,
            after_json={**out.model_dump(), "aliases": list(rec.aliases)},
        )
        return out

    # ---- Admin AI Models & Labels ----

    def admin_list_ai_models(
        self, limit: int = 20, offset: int = 0
    ) -> tuple[list[AIModel], int]:
        models = sorted(
            self._ai_models.values(), key=lambda m: (m.created_at, m.id), reverse=True
        )
        total = len(models)
        return [m.to_schema() for m in models[offset : offset + limit]], total

    def admin_register_ai_model(
        self, payload: AIModelCreate, actor_id: str
    ) -> AIModel:
        if any(m.version.lower() == payload.version.lower() for m in self._ai_models.values()):
            raise AppError(
                status_code=409,
                code="DUPLICATE_SLUG",
                message=f"Phiên bản model '{payload.version}' đã tồn tại.",
                details={"field": "version", "value": payload.version},
            )
        rec = AIModelRecord(
            id=str(uuid.uuid4()),
            version=payload.version,
            family=payload.family,
            dataset_version=payload.dataset_version,
            artifact_ref=payload.artifact_ref,
            status="draft",
            confidence_threshold=payload.confidence_threshold,
            class_count=payload.class_count,
        )
        self._ai_models[rec.id] = rec
        out = rec.to_schema()
        self._record_audit(
            actor_id=actor_id,
            action="create",
            entity_type="ai_models",
            entity_id=rec.id,
            after_json=out.model_dump(),
        )
        return out

    def admin_set_ai_model_status(
        self, model_id: str, target_status: str, actor_id: str
    ) -> AIModel:
        model = self._ai_models.get(model_id)
        if model is None:
            raise AppError(
                status_code=404,
                code="NOT_FOUND",
                message="Không tìm thấy phiên bản mô hình AI.",
                details={"model_id": model_id},
            )

        if target_status == "draft" and model.status in ("active", "archived"):
            raise AppError(
                status_code=400,
                code="MODEL_IMMUTABLE",
                message="Không thể chuyển mô hình đã active/archived quay lại trạng thái draft.",
                details={"model_id": model_id, "status": model.status},
            )

        before = model.to_schema().model_dump()

        if target_status == "active":
            labels_by_idx = {
                lbl.class_index: lbl
                for lbl in self._ai_labels.values()
                if lbl.model_id == model_id
            }
            unmapped = [
                idx for idx in range(model.class_count) if idx not in labels_by_idx
            ]
            invalid_mapped: list[int] = []
            for idx, lbl in sorted(labels_by_idx.items()):
                ing = self._ingredients.get(lbl.ingredient_id)
                if ing is None or not ing.is_active or ing.category == "pantry":
                    invalid_mapped.append(idx)

            if unmapped or invalid_mapped:
                raise AppError(
                    status_code=400,
                    code="MODEL_NOT_ACTIVATABLE",
                    message="Mô hình chưa đủ điều kiện kích hoạt do thiếu ánh xạ lớp hoặc trỏ tới nguyên liệu pantry/inactive.",
                    details={
                        "model_id": model_id,
                        "unmapped_class_indices": unmapped,
                        "invalid_mapped_class_indices": invalid_mapped,
                    },
                )

            # Demote previous active model atomically
            for other in self._ai_models.values():
                if other.id != model_id and other.status == "active":
                    other.status = "archived"
            model.status = "active"

            # Synchronize runtime `_active_ai_model` consumed by `/api/v1/ai/detect` (`A5`)
            from app.core.database import (
                AILabelRecord as RuntimeAILabelRecord,
                AIModelRecord as RuntimeAIModelRecord,
            )

            runtime_labels: dict[int, RuntimeAILabelRecord] = {}
            for idx, lbl in sorted(labels_by_idx.items()):
                ing = self._ingredients[lbl.ingredient_id]
                runtime_labels[idx] = RuntimeAILabelRecord(
                    id=lbl.id,
                    model_id=lbl.model_id,
                    class_index=lbl.class_index,
                    class_name=lbl.class_name,
                    ingredient_id=lbl.ingredient_id,
                    ingredient_name_vi=ing.name_vi,
                    category=ing.category,
                    is_active=ing.is_active,
                )
            setattr(
                self,
                "_active_ai_model",
                RuntimeAIModelRecord(
                    id=model.id,
                    version=model.version,
                    family=model.family,
                    dataset_version=model.dataset_version,
                    artifact_ref=model.artifact_ref,
                    class_count=model.class_count,
                    confidence_threshold=model.confidence_threshold,
                    review_threshold=0.80,
                    status="active",
                    labels_by_index=runtime_labels,
                ),
            )
        else:
            model.status = target_status
            if not any(m.status == "active" for m in self._ai_models.values()):
                setattr(self, "_active_ai_model", None)

        out = model.to_schema()
        self._record_audit(
            actor_id=actor_id,
            action=f"status:{target_status}",
            entity_type="ai_models",
            entity_id=model.id,
            before_json=before,
            after_json=out.model_dump(),
        )
        return out

    def admin_list_ai_labels(
        self,
        model_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[AILabel], int]:
        labels = list(self._ai_labels.values())
        if model_id:
            labels = [lbl for lbl in labels if lbl.model_id == model_id]
        labels.sort(key=lambda l: (l.model_id, l.class_index))
        total = len(labels)
        return [l.to_schema() for l in labels[offset : offset + limit]], total

    def _validate_label_target_ingredient(self, ingredient_id: str) -> None:
        ing = self._ingredients.get(ingredient_id)
        if ing is None or not ing.is_active or ing.category == "pantry":
            raise AppError(
                status_code=400,
                code="INVALID_LABEL_MAPPING",
                message="Chỉ cho phép ánh xạ nhãn AI tới nguyên liệu đang hoạt động (is_active=true) và không thuộc nhóm pantry.",
                details={
                    "ingredient_id": ingredient_id,
                    "reason": "pantry_or_inactive_ingredient_not_allowed",
                },
            )

    def admin_create_ai_label(
        self, payload: AILabelCreate, actor_id: str
    ) -> AILabel:
        model = self._ai_models.get(payload.model_id)
        if model is None:
            raise AppError(
                status_code=404,
                code="NOT_FOUND",
                message="Không tìm thấy phiên bản mô hình AI.",
                details={"model_id": payload.model_id},
            )
        if model.status != "draft":
            raise AppError(
                status_code=400,
                code="MODEL_IMMUTABLE",
                message="Chỉ cho phép thêm/sửa ánh xạ nhãn trên mô hình đang ở trạng thái draft.",
                details={"model_id": model.id, "status": model.status},
            )
        if payload.class_index >= model.class_count:
            raise AppError(
                status_code=422,
                code="VALIDATION_ERROR",
                message=f"class_index ({payload.class_index}) vượt quá class_count ({model.class_count}) của mô hình.",
                details={"field": "class_index", "max_allowed": model.class_count - 1},
            )
        self._validate_label_target_ingredient(payload.ingredient_id)

        if any(
            l.model_id == payload.model_id and l.class_index == payload.class_index
            for l in self._ai_labels.values()
        ):
            raise AppError(
                status_code=409,
                code="DUPLICATE_SLUG",
                message=f"class_index {payload.class_index} đã được ánh xạ trên mô hình này.",
                details={"field": "class_index", "value": payload.class_index},
            )

        rec = AILabelRecord(
            id=str(uuid.uuid4()),
            model_id=payload.model_id,
            class_index=payload.class_index,
            class_name=payload.class_name,
            ingredient_id=payload.ingredient_id,
        )
        self._ai_labels[rec.id] = rec
        out = rec.to_schema()
        self._record_audit(
            actor_id=actor_id,
            action="create",
            entity_type="ai_labels",
            entity_id=rec.id,
            after_json=out.model_dump(),
        )
        return out

    def admin_patch_ai_label(
        self, label_id: str, payload: AILabelPatch, actor_id: str
    ) -> AILabel:
        lbl = self._ai_labels.get(label_id)
        if lbl is None:
            raise AppError(
                status_code=404,
                code="NOT_FOUND",
                message="Không tìm thấy bản ghi ánh xạ nhãn AI.",
                details={"label_id": label_id},
            )
        model = self._ai_models.get(lbl.model_id)
        if model is None or model.status != "draft":
            raise AppError(
                status_code=400,
                code="MODEL_IMMUTABLE",
                message="Chỉ cho phép sửa ánh xạ nhãn trên mô hình đang ở trạng thái draft.",
                details={
                    "model_id": lbl.model_id,
                    "status": model.status if model else "unknown",
                },
            )
        self._validate_label_target_ingredient(payload.ingredient_id)

        before = lbl.to_schema().model_dump()
        lbl.ingredient_id = payload.ingredient_id
        out = lbl.to_schema()
        self._record_audit(
            actor_id=actor_id,
            action="patch",
            entity_type="ai_labels",
            entity_id=lbl.id,
            before_json=before,
            after_json=out.model_dump(),
        )
        return out

    # ---- Admin Audit Logs ----

    def admin_list_audit_logs(
        self, limit: int = 20, offset: int = 0
    ) -> tuple[list[AuditLog], int]:
        total = len(self._audit_logs)
        return [l.to_schema() for l in self._audit_logs[offset : offset + limit]], total


# ==============================================================================
# POSTGRESQL ADMIN MIXIN (Live Supabase PostgreSQL >= 15)
# ==============================================================================


class PostgresAdminMixin:
    """PostgreSQL Admin CMS & NutritionTag operations against Supabase PostgreSQL >= 15."""

    def _connect(self):  # pragma: no cover - implemented on PostgresCatalogRepository
        raise NotImplementedError

    def get_profile_role(self, user_id: str) -> str | None:
        if not user_id:
            return None
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT role FROM public.profiles WHERE id::text = %s",
                (user_id,),
            )
            row = cur.fetchone()
        return row["role"] if row else None

    def _insert_audit_cur(
        self,
        cur: Any,
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        before_json: dict[str, Any] | None = None,
        after_json: dict[str, Any] | None = None,
    ) -> None:
        from psycopg.types.json import Jsonb

        cur.execute(
            """
            INSERT INTO public.audit_logs (
                actor_id, action, entity_type, entity_id, before_json, after_json
            )
            VALUES (%s::uuid, %s, %s, %s::uuid, %s, %s)
            """,
            (
                actor_id,
                action,
                entity_type,
                entity_id,
                Jsonb(scrub_audit_payload(before_json)) if before_json is not None else None,
                Jsonb(scrub_audit_payload(after_json)) if after_json is not None else None,
            ),
        )

    # ---- Public & Admin Nutrition Tags ----

    def list_active_nutrition_tags(self) -> list[NutritionTag]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::text AS id, code, name_vi, description, is_active
                FROM public.nutrition_tags
                WHERE is_active = true
                ORDER BY code ASC
                """
            )
            rows = cur.fetchall()
        return [NutritionTag(**r) for r in rows]

    def admin_list_nutrition_tags(self) -> list[NutritionTag]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::text AS id, code, name_vi, description, is_active
                FROM public.nutrition_tags
                ORDER BY code ASC
                """
            )
            rows = cur.fetchall()
        return [NutritionTag(**r) for r in rows]

    def admin_create_nutrition_tag(
        self, payload: NutritionTagCreate, actor_id: str
    ) -> NutritionTag:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM public.nutrition_tags WHERE lower(code) = lower(%s)",
                (payload.code,),
            )
            if cur.fetchone():
                raise AppError(
                    status_code=409,
                    code="DUPLICATE_SLUG",
                    message=f"Mã nhãn dinh dưỡng '{payload.code}' đã tồn tại.",
                    details={"field": "code", "value": payload.code},
                )
            cur.execute(
                """
                INSERT INTO public.nutrition_tags (code, name_vi, description, is_active)
                VALUES (%s, %s, %s, %s)
                RETURNING id::text AS id, code, name_vi, description, is_active
                """,
                (payload.code, payload.name_vi, payload.description, payload.is_active),
            )
            row = cur.fetchone()
            out = NutritionTag(**row)
            self._insert_audit_cur(
                cur,
                actor_id=actor_id,
                action="create",
                entity_type="nutrition_tags",
                entity_id=out.id,
                after_json=out.model_dump(),
            )
            conn.commit()
        return out

    def admin_patch_nutrition_tag(
        self, tag_id: str, payload: NutritionTagPatch, actor_id: str
    ) -> NutritionTag:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::text AS id, code, name_vi, description, is_active
                FROM public.nutrition_tags
                WHERE id::text = %s
                FOR UPDATE
                """,
                (tag_id,),
            )
            row = cur.fetchone()
            if not row:
                raise AppError(
                    status_code=404,
                    code="NOT_FOUND",
                    message="Không tìm thấy nhãn dinh dưỡng.",
                    details={"nutrition_tag_id": tag_id},
                )
            before = dict(row)
            next_name = payload.name_vi if payload.name_vi is not None else row["name_vi"]
            next_desc = payload.description if payload.description is not None else row["description"]
            next_active = payload.is_active if payload.is_active is not None else row["is_active"]

            cur.execute(
                """
                UPDATE public.nutrition_tags
                SET name_vi = %s, description = %s, is_active = %s
                WHERE id::text = %s
                RETURNING id::text AS id, code, name_vi, description, is_active
                """,
                (next_name, next_desc, next_active, tag_id),
            )
            updated = NutritionTag(**cur.fetchone())
            self._insert_audit_cur(
                cur,
                actor_id=actor_id,
                action="patch",
                entity_type="nutrition_tags",
                entity_id=updated.id,
                before_json=before,
                after_json=updated.model_dump(),
            )
            conn.commit()
        return updated

    def admin_set_ingredient_nutrition_tags(
        self,
        ingredient_id: str,
        payload: IngredientTagMapRequest,
        actor_id: str,
    ) -> list[NutritionEvidence]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id::text AS id FROM public.ingredients WHERE id::text = %s",
                (ingredient_id,),
            )
            if not cur.fetchone():
                raise AppError(
                    status_code=404,
                    code="NOT_FOUND",
                    message="Không tìm thấy nguyên liệu.",
                    details={"ingredient_id": ingredient_id},
                )

            tag_map: dict[str, NutritionTag] = {}
            if payload.tags:
                tag_ids = [t.nutrition_tag_id for t in payload.tags]
                cur.execute(
                    """
                    SELECT id::text AS id, code, name_vi, description, is_active
                    FROM public.nutrition_tags
                    WHERE id::text = ANY(%s)
                    """,
                    (tag_ids,),
                )
                for r in cur.fetchall():
                    tag_map[r["id"]] = NutritionTag(**r)
                for t in payload.tags:
                    if t.nutrition_tag_id not in tag_map:
                        raise AppError(
                            status_code=422,
                            code="VALIDATION_ERROR",
                            message="Một hoặc nhiều nutrition_tag_id không tồn tại.",
                            details={"field": "nutrition_tag_id", "value": t.nutrition_tag_id},
                        )

            cur.execute(
                "DELETE FROM public.ingredient_nutrition_tags WHERE ingredient_id::text = %s",
                (ingredient_id,),
            )
            evidences: list[NutritionEvidence] = []
            for t in payload.tags:
                cur.execute(
                    """
                    INSERT INTO public.ingredient_nutrition_tags (
                        ingredient_id, nutrition_tag_id, source_url, note, reviewed_at
                    )
                    VALUES (%s::uuid, %s::uuid, %s, %s, now())
                    """,
                    (ingredient_id, t.nutrition_tag_id, t.source_url, t.note),
                )
                evidences.append(
                    NutritionEvidence(
                        tag=tag_map[t.nutrition_tag_id],
                        source_urls=[t.source_url],
                        note=t.note,
                    )
                )

            self._insert_audit_cur(
                cur,
                actor_id=actor_id,
                action="set_nutrition_tags",
                entity_type="ingredients",
                entity_id=ingredient_id,
                after_json={"tags": [t.model_dump() for t in payload.tags]},
            )
            conn.commit()
        return evidences

    # ---- Admin Recipes ----

    def _fetch_recipe_state_cur(self, cur: Any, recipe_id: str) -> dict[str, Any] | None:
        cur.execute(
            """
            SELECT
                id::text AS id,
                slug,
                name_vi,
                description,
                cuisine_code,
                country_code,
                prep_minutes,
                cook_minutes,
                cover_image_path,
                source_name,
                source_url,
                content_license,
                status,
                author_id::text AS author_id,
                updated_at
            FROM public.recipes
            WHERE id::text = %s
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
                i.is_active,
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
        return {"recipe": r, "ingredients": ing_rows, "steps": step_rows, "nutrition": nutr_rows}

    def admin_list_recipes(
        self,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[AdminRecipeView], int]:
        where_sql = "WHERE status = %(status)s" if status else ""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    id::text AS id,
                    slug,
                    name_vi,
                    status,
                    updated_at,
                    COUNT(*) OVER() AS total_count
                FROM public.recipes
                {where_sql}
                ORDER BY updated_at DESC, id DESC
                LIMIT %(limit)s OFFSET %(offset)s
                """,
                params,
            )
            rows = cur.fetchall()
        total = int(rows[0]["total_count"]) if rows else 0
        items = [
            AdminRecipeView(
                id=r["id"],
                slug=r["slug"],
                name_vi=r["name_vi"],
                status=r["status"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]
        return items, total

    def admin_get_recipe(self, recipe_id: str) -> AdminRecipeDetail:
        from app.schemas.recipes import RecipeIngredientView, RecipeStepView

        with self._connect() as conn, conn.cursor() as cur:
            state = self._fetch_recipe_state_cur(cur, recipe_id)
        if not state:
            raise AppError(
                status_code=404,
                code="RECIPE_NOT_FOUND",
                message="Không tìm thấy công thức.",
                details={"recipe_id": recipe_id},
            )
        r = state["recipe"]
        return AdminRecipeDetail(
            id=r["id"],
            slug=r["slug"],
            name_vi=r["name_vi"],
            cuisine_code=r["cuisine_code"],
            prep_minutes=int(r["prep_minutes"]),
            cook_minutes=int(r["cook_minutes"]),
            total_minutes=int(r["prep_minutes"]) + int(r["cook_minutes"]),
            cover_image_url=r.get("cover_image_path"),
            description=r.get("description"),
            country_code=r.get("country_code"),
            ingredients=[
                RecipeIngredientView(
                    ingredient_id=ir["ingredient_id"],
                    name_vi=ir["name_vi"],
                    category=ir["category"],
                    is_required=bool(ir["is_required"]),
                    display_quantity=ir.get("display_quantity"),
                    sort_order=int(ir["sort_order"]),
                )
                for sr in [state["ingredients"]]
                for ir in sr
            ],
            steps=[
                RecipeStepView(
                    step_no=int(st["step_no"]),
                    instruction=st["instruction"],
                    estimated_minutes=st.get("estimated_minutes"),
                )
                for st in state["steps"]
            ],
            nutrition_evidence=[
                NutritionEvidence(
                    tag=NutritionTag(
                        id=nr["tag_id"],
                        code=nr["code"],
                        name_vi=nr["name_vi"],
                        description=nr["description"],
                        is_active=bool(nr["is_active"]),
                    ),
                    source_urls=list(nr["source_urls"] or []),
                    note=nr.get("note"),
                )
                for nr in state["nutrition"]
            ],
            source_name=r.get("source_name"),
            source_url=r.get("source_url"),
            content_license=r.get("content_license"),
            status=r["status"],
            author_id=r["author_id"],
            updated_at=r["updated_at"],
        )

    def _resolve_pg_recipe_sublists_cur(
        self,
        cur: Any,
        ing_inputs: list[RecipeIngredientInput],
        step_inputs: list[Any],
    ) -> tuple[list[RecipeIngredientRecord], list[RecipeStepRecord], dict[str, IngredientRecord]]:
        from app.core.database import IngredientRecord, RecipeIngredientRecord, RecipeStepRecord

        ing_lookup: dict[str, IngredientRecord] = {}
        if ing_inputs:
            ids = [it.ingredient_id for it in ing_inputs]
            cur.execute(
                """
                SELECT id::text AS id, slug, name_vi, category, is_active, fdc_id
                FROM public.ingredients
                WHERE id::text = ANY(%s)
                """,
                (ids,),
            )
            for row in cur.fetchall():
                ing_lookup[row["id"]] = IngredientRecord(
                    id=row["id"],
                    slug=row["slug"],
                    name_vi=row["name_vi"],
                    category=row["category"],
                    is_active=bool(row["is_active"]),
                    fdc_id=row.get("fdc_id"),
                )
            missing_ids = [iid for iid in ids if iid not in ing_lookup]
            if missing_ids:
                raise AppError(
                    status_code=422,
                    code="INVALID_INGREDIENTS",
                    message="Nguyên liệu gắn với công thức không tồn tại trong danh mục.",
                    details={"invalid_ids": missing_ids, "reason": "unknown_or_inactive_id"},
                )

        built_ings: list[RecipeIngredientRecord] = []
        for idx, inp in enumerate(ing_inputs):
            ing_rec = ing_lookup[inp.ingredient_id]
            role, dish_role, weight = resolve_recipe_ingredient_defaults(inp, ing_rec.category)
            built_ings.append(
                RecipeIngredientRecord(
                    ingredient_id=ing_rec.id,
                    name_vi=ing_rec.name_vi,
                    category=ing_rec.category,
                    is_required=inp.is_required,
                    role=role,
                    dish_role=dish_role,
                    weight=weight,
                    grams=inp.grams,
                    display_quantity=inp.display_quantity,
                    sort_order=inp.sort_order if inp.sort_order else idx + 1,
                )
            )

        built_steps = [
            RecipeStepRecord(
                step_no=st.step_no,
                instruction=st.instruction,
                estimated_minutes=st.estimated_minutes,
            )
            for st in sorted(step_inputs, key=lambda s: s.step_no)
        ]
        return built_ings, built_steps, ing_lookup

    def admin_create_recipe(self, payload: RecipeCreate, actor_id: str) -> AdminRecipeView:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM public.recipes WHERE lower(slug) = lower(%s)",
                (payload.slug,),
            )
            if cur.fetchone():
                raise AppError(
                    status_code=409,
                    code="DUPLICATE_SLUG",
                    message=f"Slug công thức '{payload.slug}' đã tồn tại.",
                    details={"field": "slug", "value": payload.slug},
                )

            built_ings, built_steps, _ = self._resolve_pg_recipe_sublists_cur(
                cur, payload.ingredients, payload.steps
            )
            cur.execute(
                """
                INSERT INTO public.recipes (
                    slug, name_vi, description, cuisine_code, country_code,
                    prep_minutes, cook_minutes, cover_image_path,
                    source_name, source_url, content_license, status, author_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'draft', %s::uuid)
                RETURNING id::text AS id, slug, name_vi, status, updated_at
                """,
                (
                    payload.slug,
                    payload.name_vi,
                    payload.description,
                    payload.cuisine_code,
                    payload.country_code,
                    payload.prep_minutes,
                    payload.cook_minutes,
                    payload.cover_image_path,
                    payload.source_name,
                    payload.source_url,
                    payload.content_license,
                    actor_id,
                ),
            )
            rec_row = cur.fetchone()
            rid = rec_row["id"]

            for ri in built_ings:
                cur.execute(
                    """
                    INSERT INTO public.recipe_ingredients (
                        recipe_id, ingredient_id, is_required, role, dish_role,
                        weight, grams, display_quantity, sort_order
                    )
                    VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        rid,
                        ri.ingredient_id,
                        ri.is_required,
                        ri.role,
                        ri.dish_role,
                        ri.weight,
                        ri.grams,
                        ri.display_quantity,
                        ri.sort_order,
                    ),
                )
            for st in built_steps:
                cur.execute(
                    """
                    INSERT INTO public.recipe_steps (recipe_id, step_no, instruction, estimated_minutes)
                    VALUES (%s::uuid, %s, %s, %s)
                    """,
                    (rid, st.step_no, st.instruction, st.estimated_minutes),
                )

            view = AdminRecipeView(**rec_row)
            self._insert_audit_cur(
                cur,
                actor_id=actor_id,
                action="create",
                entity_type="recipes",
                entity_id=rid,
                after_json=view.model_dump(),
            )
            conn.commit()
        return view

    def admin_patch_recipe(
        self, recipe_id: str, payload: RecipePatch, actor_id: str
    ) -> AdminRecipeView:
        from app.core.database import IngredientRecord, RecipeIngredientRecord, RecipeStepRecord

        with self._connect() as conn, conn.cursor() as cur:
            state = self._fetch_recipe_state_cur(cur, recipe_id)
            if not state:
                raise AppError(
                    status_code=404,
                    code="RECIPE_NOT_FOUND",
                    message="Không tìm thấy công thức.",
                    details={"recipe_id": recipe_id},
                )
            r = state["recipe"]
            if payload.slug is not None:
                cur.execute(
                    "SELECT 1 FROM public.recipes WHERE lower(slug) = lower(%s) AND id::text <> %s",
                    (payload.slug, recipe_id),
                )
                if cur.fetchone():
                    raise AppError(
                        status_code=409,
                        code="DUPLICATE_SLUG",
                        message=f"Slug công thức '{payload.slug}' đã tồn tại.",
                        details={"field": "slug", "value": payload.slug},
                    )

            next_prep = payload.prep_minutes if payload.prep_minutes is not None else int(r["prep_minutes"])
            next_cook = payload.cook_minutes if payload.cook_minutes is not None else int(r["cook_minutes"])
            if next_prep + next_cook <= 0:
                raise AppError(
                    status_code=422,
                    code="VALIDATION_ERROR",
                    message="Tổng thời gian chế biến (prep_minutes + cook_minutes) bắt buộc > 0.",
                    details={"field": "cook_minutes", "reason": "non_positive_total_minutes"},
                )

            if payload.ingredients is not None:
                next_ings, _, ing_lookup = self._resolve_pg_recipe_sublists_cur(
                    cur, payload.ingredients, []
                )
            else:
                next_ings = [
                    RecipeIngredientRecord(
                        ingredient_id=ir["ingredient_id"],
                        name_vi=ir["name_vi"],
                        category=ir["category"],
                        is_required=bool(ir["is_required"]),
                        role=ir["role"],
                        dish_role=ir["dish_role"],
                        weight=float(ir["weight"]),
                        grams=ir.get("grams"),
                        display_quantity=ir.get("display_quantity"),
                        sort_order=int(ir["sort_order"]),
                    )
                    for ir in state["ingredients"]
                ]
                ing_lookup = {
                    ir["ingredient_id"]: IngredientRecord(
                        id=ir["ingredient_id"],
                        slug=ir["ingredient_id"],
                        name_vi=ir["name_vi"],
                        category=ir["category"],
                        is_active=bool(ir["is_active"]),
                    )
                    for ir in state["ingredients"]
                }

            if payload.steps is not None:
                _, next_steps, _ = self._resolve_pg_recipe_sublists_cur(cur, [], payload.steps)
            else:
                next_steps = [
                    RecipeStepRecord(
                        step_no=int(st["step_no"]),
                        instruction=st["instruction"],
                        estimated_minutes=st.get("estimated_minutes"),
                    )
                    for st in state["steps"]
                ]

            if r["status"] == "published":
                reasons = check_recipe_publishable_reasons(
                    prep_minutes=next_prep,
                    cook_minutes=next_cook,
                    ingredients=next_ings,
                    steps=next_steps,
                    ingredient_lookup=ing_lookup,
                )
                if reasons:
                    raise AppError(
                        status_code=400,
                        code="RECIPE_NOT_PUBLISHABLE",
                        message="Không thể lưu thay đổi làm công thức đang published vi phạm điều kiện xuất bản (BR-01).",
                        details={"recipe_id": recipe_id, "reasons": reasons},
                    )

            fields_set = payload.model_fields_set
            cur.execute(
                """
                UPDATE public.recipes
                SET slug = %s,
                    name_vi = %s,
                    description = %s,
                    cuisine_code = %s,
                    country_code = %s,
                    prep_minutes = %s,
                    cook_minutes = %s,
                    cover_image_path = %s,
                    source_name = %s,
                    source_url = %s,
                    content_license = %s,
                    updated_at = now()
                WHERE id::text = %s
                RETURNING id::text AS id, slug, name_vi, status, updated_at
                """,
                (
                    payload.slug if ("slug" in fields_set and payload.slug is not None) else r["slug"],
                    payload.name_vi if ("name_vi" in fields_set and payload.name_vi is not None) else r["name_vi"],
                    payload.description if "description" in fields_set else r.get("description"),
                    payload.cuisine_code if ("cuisine_code" in fields_set and payload.cuisine_code is not None) else r["cuisine_code"],
                    payload.country_code if "country_code" in fields_set else r.get("country_code"),
                    next_prep,
                    next_cook,
                    payload.cover_image_path if "cover_image_path" in fields_set else r.get("cover_image_path"),
                    payload.source_name if "source_name" in fields_set else r.get("source_name"),
                    payload.source_url if "source_url" in fields_set else r.get("source_url"),
                    payload.content_license if "content_license" in fields_set else r.get("content_license"),
                    recipe_id,
                ),
            )
            updated_row = cur.fetchone()

            if payload.ingredients is not None:
                cur.execute(
                    "DELETE FROM public.recipe_ingredients WHERE recipe_id::text = %s",
                    (recipe_id,),
                )
                for ri in next_ings:
                    cur.execute(
                        """
                        INSERT INTO public.recipe_ingredients (
                            recipe_id, ingredient_id, is_required, role, dish_role,
                            weight, grams, display_quantity, sort_order
                        )
                        VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            recipe_id,
                            ri.ingredient_id,
                            ri.is_required,
                            ri.role,
                            ri.dish_role,
                            ri.weight,
                            ri.grams,
                            ri.display_quantity,
                            ri.sort_order,
                        ),
                    )

            if payload.steps is not None:
                cur.execute(
                    "DELETE FROM public.recipe_steps WHERE recipe_id::text = %s",
                    (recipe_id,),
                )
                for st in next_steps:
                    cur.execute(
                        """
                        INSERT INTO public.recipe_steps (recipe_id, step_no, instruction, estimated_minutes)
                        VALUES (%s::uuid, %s, %s, %s)
                        """,
                        (recipe_id, st.step_no, st.instruction, st.estimated_minutes),
                    )

            view = AdminRecipeView(**updated_row)
            self._insert_audit_cur(
                cur,
                actor_id=actor_id,
                action="patch",
                entity_type="recipes",
                entity_id=recipe_id,
                before_json={"slug": r["slug"], "status": r["status"]},
                after_json=view.model_dump(),
            )
            conn.commit()
        return view

    def admin_set_recipe_status(
        self, recipe_id: str, target_status: str, actor_id: str
    ) -> AdminRecipeView:
        from app.core.database import IngredientRecord, RecipeIngredientRecord, RecipeStepRecord

        with self._connect() as conn, conn.cursor() as cur:
            state = self._fetch_recipe_state_cur(cur, recipe_id)
            if not state:
                raise AppError(
                    status_code=404,
                    code="RECIPE_NOT_FOUND",
                    message="Không tìm thấy công thức.",
                    details={"recipe_id": recipe_id},
                )
            r = state["recipe"]
            if target_status == "published":
                ings = [
                    RecipeIngredientRecord(
                        ingredient_id=ir["ingredient_id"],
                        name_vi=ir["name_vi"],
                        category=ir["category"],
                        is_required=bool(ir["is_required"]),
                        role=ir["role"],
                        dish_role=ir["dish_role"],
                        weight=float(ir["weight"]),
                        grams=ir.get("grams"),
                        display_quantity=ir.get("display_quantity"),
                        sort_order=int(ir["sort_order"]),
                    )
                    for ir in state["ingredients"]
                ]
                lookup = {
                    ir["ingredient_id"]: IngredientRecord(
                        id=ir["ingredient_id"],
                        slug=ir["ingredient_id"],
                        name_vi=ir["name_vi"],
                        category=ir["category"],
                        is_active=bool(ir["is_active"]),
                    )
                    for ir in state["ingredients"]
                }
                steps = [
                    RecipeStepRecord(
                        step_no=int(st["step_no"]),
                        instruction=st["instruction"],
                        estimated_minutes=st.get("estimated_minutes"),
                    )
                    for st in state["steps"]
                ]
                reasons = check_recipe_publishable_reasons(
                    prep_minutes=int(r["prep_minutes"]),
                    cook_minutes=int(r["cook_minutes"]),
                    ingredients=ings,
                    steps=steps,
                    ingredient_lookup=lookup,
                )
                if reasons:
                    raise AppError(
                        status_code=400,
                        code="RECIPE_NOT_PUBLISHABLE",
                        message="Công thức chưa thỏa mãn đầy đủ 4 điều kiện xuất bản (BR-01).",
                        details={"recipe_id": recipe_id, "reasons": reasons},
                    )

            cur.execute(
                """
                UPDATE public.recipes
                SET status = %s, updated_at = now()
                WHERE id::text = %s
                RETURNING id::text AS id, slug, name_vi, status, updated_at
                """,
                (target_status, recipe_id),
            )
            view = AdminRecipeView(**cur.fetchone())
            self._insert_audit_cur(
                cur,
                actor_id=actor_id,
                action=f"status:{target_status}",
                entity_type="recipes",
                entity_id=recipe_id,
                before_json={"status": r["status"]},
                after_json=view.model_dump(),
            )
            conn.commit()
        return view

    # ---- Admin Ingredients ----

    def admin_list_ingredients(
        self,
        q: str | None = None,
        category: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Ingredient], int]:
        where_clauses: list[str] = ["TRUE"]
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if category:
            where_clauses.append("i.category = %(category)s")
            params["category"] = category
        if q and q.strip():
            params["nq"] = norm_vi(q)
            where_clauses.append(
                """(
                    public.norm_vi(i.name_vi) LIKE '%%' || %(nq)s || '%%'
                    OR lower(i.slug) LIKE '%%' || %(nq)s || '%%'
                    OR EXISTS (
                        SELECT 1 FROM public.ingredient_aliases ia
                        WHERE ia.ingredient_id = i.id
                          AND (ia.normalized_alias LIKE '%%' || %(nq)s || '%%' OR similarity(ia.normalized_alias, %(nq)s) >= 0.3)
                    )
                    OR similarity(public.norm_vi(i.name_vi), %(nq)s) >= 0.3
                )"""
            )
        where_sql = " AND ".join(where_clauses)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    i.id::text AS id,
                    i.slug,
                    i.name_vi,
                    i.category,
                    i.is_active,
                    COUNT(*) OVER() AS total_count
                FROM public.ingredients i
                WHERE {where_sql}
                ORDER BY public.norm_vi(i.name_vi) ASC, i.id ASC
                LIMIT %(limit)s OFFSET %(offset)s
                """,
                params,
            )
            rows = cur.fetchall()
        total = int(rows[0]["total_count"]) if rows else 0
        items = [
            Ingredient(
                id=r["id"],
                slug=r["slug"],
                name_vi=r["name_vi"],
                category=r["category"],
                is_active=bool(r["is_active"]),
            )
            for r in rows
        ]
        return items, total

    def admin_create_ingredient(
        self, payload: IngredientCreate, actor_id: str
    ) -> Ingredient:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM public.ingredients WHERE lower(slug) = lower(%s)",
                (payload.slug,),
            )
            if cur.fetchone():
                raise AppError(
                    status_code=409,
                    code="DUPLICATE_SLUG",
                    message=f"Slug nguyên liệu '{payload.slug}' đã tồn tại.",
                    details={"field": "slug", "value": payload.slug},
                )
            cur.execute(
                """
                INSERT INTO public.ingredients (slug, name_vi, category, is_active)
                VALUES (%s, %s, %s, %s)
                RETURNING id::text AS id, slug, name_vi, category, is_active
                """,
                (payload.slug, payload.name_vi, payload.category, payload.is_active),
            )
            row = cur.fetchone()
            iid = row["id"]

            for alias in payload.aliases:
                cur.execute(
                    """
                    INSERT INTO public.ingredient_aliases (ingredient_id, alias, normalized_alias, locale)
                    VALUES (%s::uuid, %s, public.norm_vi(%s), 'vi')
                    ON CONFLICT (ingredient_id, normalized_alias, locale) DO NOTHING
                    """,
                    (iid, alias, alias),
                )

            out = Ingredient(
                id=iid,
                slug=row["slug"],
                name_vi=row["name_vi"],
                category=row["category"],
                is_active=bool(row["is_active"]),
            )
            self._insert_audit_cur(
                cur,
                actor_id=actor_id,
                action="create",
                entity_type="ingredients",
                entity_id=iid,
                after_json={**out.model_dump(), "aliases": list(payload.aliases)},
            )
            conn.commit()
        return out

    def admin_patch_ingredient(
        self, ingredient_id: str, payload: IngredientPatch, actor_id: str
    ) -> Ingredient:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::text AS id, slug, name_vi, category, is_active
                FROM public.ingredients
                WHERE id::text = %s
                FOR UPDATE
                """,
                (ingredient_id,),
            )
            cur_row = cur.fetchone()
            if not cur_row:
                raise AppError(
                    status_code=404,
                    code="NOT_FOUND",
                    message="Không tìm thấy nguyên liệu.",
                    details={"ingredient_id": ingredient_id},
                )

            if payload.slug is not None:
                cur.execute(
                    "SELECT 1 FROM public.ingredients WHERE lower(slug) = lower(%s) AND id::text <> %s",
                    (payload.slug, ingredient_id),
                )
                if cur.fetchone():
                    raise AppError(
                        status_code=409,
                        code="DUPLICATE_SLUG",
                        message=f"Slug nguyên liệu '{payload.slug}' đã tồn tại.",
                        details={"field": "slug", "value": payload.slug},
                    )

            deactivating = payload.is_active is False and bool(cur_row["is_active"]) is True
            changing_cat = payload.category is not None and payload.category != cur_row["category"]
            if deactivating or changing_cat:
                cur.execute(
                    """
                    SELECT DISTINCT r.id::text AS id
                    FROM public.recipe_ingredients ri
                    JOIN public.recipes r ON r.id = ri.recipe_id
                    WHERE ri.ingredient_id::text = %s AND r.status = 'published'
                    ORDER BY 1
                    """,
                    (ingredient_id,),
                )
                affected_recipes = [r["id"] for r in cur.fetchall()]

                cur.execute(
                    """
                    SELECT DISTINCT m.id::text AS id
                    FROM public.ai_labels al
                    JOIN public.ai_models m ON m.id = al.model_id
                    WHERE al.ingredient_id::text = %s AND m.status IN ('draft', 'active')
                    ORDER BY 1
                    """,
                    (ingredient_id,),
                )
                affected_models = [r["id"] for r in cur.fetchall()]

                if affected_recipes or affected_models:
                    raise AppError(
                        status_code=400,
                        code="INGREDIENT_IN_USE",
                        message="Không thể tắt hoạt động hoặc đổi phân loại nguyên liệu đang được dùng trong công thức published hoặc model AI draft/active.",
                        details={
                            "ingredient_id": ingredient_id,
                            "affected_published_recipe_ids": affected_recipes,
                            "affected_active_or_draft_model_ids": affected_models,
                        },
                    )

            cur.execute(
                """
                UPDATE public.ingredients
                SET slug = %s,
                    name_vi = %s,
                    category = %s,
                    is_active = %s
                WHERE id::text = %s
                RETURNING id::text AS id, slug, name_vi, category, is_active
                """,
                (
                    payload.slug if payload.slug is not None else cur_row["slug"],
                    payload.name_vi if payload.name_vi is not None else cur_row["name_vi"],
                    payload.category if payload.category is not None else cur_row["category"],
                    payload.is_active if payload.is_active is not None else bool(cur_row["is_active"]),
                    ingredient_id,
                ),
            )
            upd = cur.fetchone()

            if payload.aliases is not None:
                cur.execute(
                    "DELETE FROM public.ingredient_aliases WHERE ingredient_id::text = %s",
                    (ingredient_id,),
                )
                for alias in payload.aliases:
                    cur.execute(
                        """
                        INSERT INTO public.ingredient_aliases (ingredient_id, alias, normalized_alias, locale)
                        VALUES (%s::uuid, %s, public.norm_vi(%s), 'vi')
                        ON CONFLICT (ingredient_id, normalized_alias, locale) DO NOTHING
                        """,
                        (ingredient_id, alias, alias),
                    )

            out = Ingredient(
                id=upd["id"],
                slug=upd["slug"],
                name_vi=upd["name_vi"],
                category=upd["category"],
                is_active=bool(upd["is_active"]),
            )
            self._insert_audit_cur(
                cur,
                actor_id=actor_id,
                action="patch",
                entity_type="ingredients",
                entity_id=ingredient_id,
                before_json=dict(cur_row),
                after_json=out.model_dump(),
            )
            conn.commit()
        return out

    # ---- Admin AI Models & Labels ----

    def admin_list_ai_models(
        self, limit: int = 20, offset: int = 0
    ) -> tuple[list[AIModel], int]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id::text AS id,
                    version,
                    family,
                    dataset_version,
                    status,
                    confidence_threshold::float AS confidence_threshold,
                    COUNT(*) OVER() AS total_count
                FROM public.ai_models
                ORDER BY created_at DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
            rows = cur.fetchall()
        total = int(rows[0]["total_count"]) if rows else 0
        items = [
            AIModel(
                id=r["id"],
                version=r["version"],
                family=r["family"],
                dataset_version=r["dataset_version"],
                status=r["status"],
                confidence_threshold=float(r["confidence_threshold"]),
            )
            for r in rows
        ]
        return items, total

    def admin_register_ai_model(
        self, payload: AIModelCreate, actor_id: str
    ) -> AIModel:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM public.ai_models WHERE lower(version) = lower(%s)",
                (payload.version,),
            )
            if cur.fetchone():
                raise AppError(
                    status_code=409,
                    code="DUPLICATE_SLUG",
                    message=f"Phiên bản model '{payload.version}' đã tồn tại.",
                    details={"field": "version", "value": payload.version},
                )
            cur.execute(
                """
                INSERT INTO public.ai_models (
                    version, family, dataset_version, artifact_ref,
                    class_count, confidence_threshold, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'draft')
                RETURNING id::text AS id, version, family, dataset_version, status, confidence_threshold::float AS confidence_threshold
                """,
                (
                    payload.version,
                    payload.family,
                    payload.dataset_version,
                    payload.artifact_ref,
                    payload.class_count,
                    payload.confidence_threshold,
                ),
            )
            out = AIModel(**cur.fetchone())
            self._insert_audit_cur(
                cur,
                actor_id=actor_id,
                action="create",
                entity_type="ai_models",
                entity_id=out.id,
                after_json=out.model_dump(),
            )
            conn.commit()
        return out

    def admin_set_ai_model_status(
        self, model_id: str, target_status: str, actor_id: str
    ) -> AIModel:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::text AS id, version, family, dataset_version, status, confidence_threshold::float AS confidence_threshold
                FROM public.ai_models
                WHERE id::text = %s
                FOR UPDATE
                """,
                (model_id,),
            )
            m_row = cur.fetchone()
            if not m_row:
                raise AppError(
                    status_code=404,
                    code="NOT_FOUND",
                    message="Không tìm thấy phiên bản mô hình AI.",
                    details={"model_id": model_id},
                )
            if target_status == "draft" and m_row["status"] in ("active", "archived"):
                raise AppError(
                    status_code=400,
                    code="MODEL_IMMUTABLE",
                    message="Không thể chuyển mô hình đã active/archived quay lại trạng thái draft.",
                    details={"model_id": model_id, "status": m_row["status"]},
                )

            if target_status == "active":
                cur.execute(
                    "SELECT public.activate_ai_model(%s::uuid) AS res",
                    (model_id,),
                )
                rpc_res = cur.fetchone()["res"]
                if not rpc_res.get("ok"):
                    conn.rollback()
                    raise AppError(
                        status_code=400,
                        code="MODEL_NOT_ACTIVATABLE",
                        message="Mô hình chưa đủ điều kiện kích hoạt do thiếu ánh xạ lớp hoặc trỏ tới nguyên liệu pantry/inactive.",
                        details={
                            "model_id": model_id,
                            "unmapped_class_indices": rpc_res.get("unmapped_class_indices", []),
                            "invalid_mapped_class_indices": rpc_res.get("invalid_mapped_class_indices", []),
                        },
                    )
            else:
                cur.execute(
                    "UPDATE public.ai_models SET status = %s WHERE id::text = %s",
                    (target_status, model_id),
                )

            cur.execute(
                """
                SELECT id::text AS id, version, family, dataset_version, status, confidence_threshold::float AS confidence_threshold
                FROM public.ai_models
                WHERE id::text = %s
                """,
                (model_id,),
            )
            out = AIModel(**cur.fetchone())
            self._insert_audit_cur(
                cur,
                actor_id=actor_id,
                action=f"status:{target_status}",
                entity_type="ai_models",
                entity_id=model_id,
                before_json=dict(m_row),
                after_json=out.model_dump(),
            )
            conn.commit()
        return out

    def admin_list_ai_labels(
        self,
        model_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[AILabel], int]:
        where_sql = "WHERE model_id::text = %(model_id)s" if model_id else ""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if model_id:
            params["model_id"] = model_id
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    id::text AS id,
                    model_id::text AS model_id,
                    class_index,
                    class_name,
                    ingredient_id::text AS ingredient_id,
                    COUNT(*) OVER() AS total_count
                FROM public.ai_labels
                {where_sql}
                ORDER BY model_id ASC, class_index ASC
                LIMIT %(limit)s OFFSET %(offset)s
                """,
                params,
            )
            rows = cur.fetchall()
        total = int(rows[0]["total_count"]) if rows else 0
        items = [
            AILabel(
                id=r["id"],
                model_id=r["model_id"],
                class_index=int(r["class_index"]),
                class_name=r["class_name"],
                ingredient_id=r["ingredient_id"],
            )
            for r in rows
        ]
        return items, total

    def _pg_validate_label_ingredient_cur(self, cur: Any, ingredient_id: str) -> None:
        cur.execute(
            "SELECT is_active, category FROM public.ingredients WHERE id::text = %s",
            (ingredient_id,),
        )
        ing = cur.fetchone()
        if not ing or not bool(ing["is_active"]) or ing["category"] == "pantry":
            raise AppError(
                status_code=400,
                code="INVALID_LABEL_MAPPING",
                message="Chỉ cho phép ánh xạ nhãn AI tới nguyên liệu đang hoạt động (is_active=true) và không thuộc nhóm pantry.",
                details={
                    "ingredient_id": ingredient_id,
                    "reason": "pantry_or_inactive_ingredient_not_allowed",
                },
            )

    def admin_create_ai_label(
        self, payload: AILabelCreate, actor_id: str
    ) -> AILabel:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id::text AS id, status, class_count FROM public.ai_models WHERE id::text = %s FOR UPDATE",
                (payload.model_id,),
            )
            m = cur.fetchone()
            if not m:
                raise AppError(
                    status_code=404,
                    code="NOT_FOUND",
                    message="Không tìm thấy phiên bản mô hình AI.",
                    details={"model_id": payload.model_id},
                )
            if m["status"] != "draft":
                raise AppError(
                    status_code=400,
                    code="MODEL_IMMUTABLE",
                    message="Chỉ cho phép thêm/sửa ánh xạ nhãn trên mô hình đang ở trạng thái draft.",
                    details={"model_id": payload.model_id, "status": m["status"]},
                )
            if payload.class_index >= int(m["class_count"]):
                raise AppError(
                    status_code=422,
                    code="VALIDATION_ERROR",
                    message=f"class_index ({payload.class_index}) vượt quá class_count ({m['class_count']}) của mô hình.",
                    details={"field": "class_index", "max_allowed": int(m["class_count"]) - 1},
                )
            self._pg_validate_label_ingredient_cur(cur, payload.ingredient_id)

            cur.execute(
                "SELECT 1 FROM public.ai_labels WHERE model_id::text = %s AND class_index = %s",
                (payload.model_id, payload.class_index),
            )
            if cur.fetchone():
                raise AppError(
                    status_code=409,
                    code="DUPLICATE_SLUG",
                    message=f"class_index {payload.class_index} đã được ánh xạ trên mô hình này.",
                    details={"field": "class_index", "value": payload.class_index},
                )

            cur.execute(
                """
                INSERT INTO public.ai_labels (model_id, class_index, class_name, ingredient_id)
                VALUES (%s::uuid, %s, %s, %s::uuid)
                RETURNING id::text AS id, model_id::text AS model_id, class_index, class_name, ingredient_id::text AS ingredient_id
                """,
                (payload.model_id, payload.class_index, payload.class_name, payload.ingredient_id),
            )
            out = AILabel(**cur.fetchone())
            self._insert_audit_cur(
                cur,
                actor_id=actor_id,
                action="create",
                entity_type="ai_labels",
                entity_id=out.id,
                after_json=out.model_dump(),
            )
            conn.commit()
        return out

    def admin_patch_ai_label(
        self, label_id: str, payload: AILabelPatch, actor_id: str
    ) -> AILabel:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    al.id::text AS id,
                    al.model_id::text AS model_id,
                    al.class_index,
                    al.class_name,
                    al.ingredient_id::text AS ingredient_id,
                    m.status AS model_status
                FROM public.ai_labels al
                JOIN public.ai_models m ON m.id = al.model_id
                WHERE al.id::text = %s
                FOR UPDATE
                """,
                (label_id,),
            )
            row = cur.fetchone()
            if not row:
                raise AppError(
                    status_code=404,
                    code="NOT_FOUND",
                    message="Không tìm thấy bản ghi ánh xạ nhãn AI.",
                    details={"label_id": label_id},
                )
            if row["model_status"] != "draft":
                raise AppError(
                    status_code=400,
                    code="MODEL_IMMUTABLE",
                    message="Chỉ cho phép sửa ánh xạ nhãn trên mô hình đang ở trạng thái draft.",
                    details={"model_id": row["model_id"], "status": row["model_status"]},
                )
            self._pg_validate_label_ingredient_cur(cur, payload.ingredient_id)

            cur.execute(
                """
                UPDATE public.ai_labels
                SET ingredient_id = %s::uuid
                WHERE id::text = %s
                RETURNING id::text AS id, model_id::text AS model_id, class_index, class_name, ingredient_id::text AS ingredient_id
                """,
                (payload.ingredient_id, label_id),
            )
            out = AILabel(**cur.fetchone())
            self._insert_audit_cur(
                cur,
                actor_id=actor_id,
                action="patch",
                entity_type="ai_labels",
                entity_id=out.id,
                before_json={"ingredient_id": row["ingredient_id"]},
                after_json=out.model_dump(),
            )
            conn.commit()
        return out

    # ---- Admin Audit Logs ----

    def admin_list_audit_logs(
        self, limit: int = 20, offset: int = 0
    ) -> tuple[list[AuditLog], int]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id::text AS id,
                    actor_id::text AS actor_id,
                    action,
                    entity_type,
                    entity_id::text AS entity_id,
                    created_at,
                    COUNT(*) OVER() AS total_count
                FROM public.audit_logs
                ORDER BY created_at DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
            rows = cur.fetchall()
        total = int(rows[0]["total_count"]) if rows else 0
        items = [AuditLog(**{k: v for k, v in r.items() if k != "total_count"}) for r in rows]
        return items, total
