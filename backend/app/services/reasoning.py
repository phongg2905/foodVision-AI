r"""Component 04 (TP 04): Rule-Based Open-World 3-Valued Reasoning & Hard Constraints.

Implements:
1. Strict input validation separating main ingredients (ingredient_ids, category != 'pantry')
   and excluded pantry seasonings (excluded_pantry_ids, category == 'pantry').
   Raises HTTP 422 INVALID_INGREDIENTS with details (`invalid_ids`, `invalid_ingredient_ids`, `reason`)
   on any violation (`TC-11`, `TC-37`, `api-conventions.md` Error #4).
2. Open-World 3-valued state assignment for each ingredient i:
   - confirmed_available: i in U or i in (Pantry \ X)
   - confirmed_missing  : i in X or i in M_main (explicitly marked missing)
   - unknown            : main ingredient not in U and not in M_main
3. Hard constraints filtering (before scoring):
   - Verified recipe status == 'published' (TP 10) and |R_main| >= 1 (BR-01)
   - At least 1 matched main ingredient: |(R_main U O_main) n U| >= 1 (C > 0)
   - Cuisine filter: cuisine_code in cuisine_codes (when cuisine_codes is non-empty)
   - Time filter: total_minutes = prep_minutes + cook_minutes <= max_total_minutes
   - DietOK(r, u): no ingredient in r carries an allergen in excluded_allergen_ids
   - EquipOK(r, u): required_equipment is subset of available_equipment (when specified)
4. Classification into 4 v1.1 states (BLOCKED, READY, UNKNOWN, MISSING_CONFIRMED)
   and deterministic mapping to v1.0 contract enum ("ready", "missing").
"""

from __future__ import annotations

from app.core.database import CatalogRepository, IngredientRecord, RecipeRecord
from app.core.errors import AppError
from app.schemas.reasoning import (
    AvailabilityV1,
    IngredientTriState,
    ReasoningInput,
    RecipeReasoningEvaluation,
    RecipeReasoningStatus,
)


def validate_and_resolve_ingredients(
    repo: CatalogRepository,
    ingredient_ids: list[str],
    excluded_pantry_ids: list[str] | None = None,
) -> tuple[list[str], list[str], dict[str, IngredientRecord]]:
    """Validate ingredient_ids (main) and excluded_pantry_ids (pantry) against active catalog.

    Enforces FR-05, FR-06, BR-04, TC-11, TC-37, and `api-conventions.md` Error #4:
    - ingredient_ids must have >= 1 item, all existing, is_active=True, and category != 'pantry'.
    - excluded_pantry_ids (optional) must all exist, is_active=True, and category == 'pantry'.
    - Any violation raises 422 INVALID_INGREDIENTS with `invalid_ids`, `invalid_ingredient_ids`,
      and `reason` in ("empty_main_ingredients", "pantry_in_main_list",
      "non_pantry_in_excluded_list", "unknown_or_inactive_id").
    """
    excluded_pantry_ids = excluded_pantry_ids or []
    if not ingredient_ids:
        raise AppError(
            status_code=422,
            code="INVALID_INGREDIENTS",
            message="Danh sách nguyên liệu chính (ingredient_ids) phải có ít nhất 1 phần tử.",
            details={
                "invalid_ids": [],
                "invalid_ingredient_ids": [],
                "reason": "empty_main_ingredients",
            },
        )

    dedup_main = list(dict.fromkeys(ingredient_ids))
    dedup_pantry = list(dict.fromkeys(excluded_pantry_ids))

    all_requested = list(dict.fromkeys(dedup_main + dedup_pantry))
    found_map = repo.get_ingredients_by_ids(all_requested)

    invalid_ids: list[str] = []
    reason: str | None = None

    for iid in dedup_main:
        rec = found_map.get(iid)
        if rec is None or not rec.is_active:
            invalid_ids.append(iid)
            if reason is None:
                reason = "unknown_or_inactive_id"
        elif rec.category == "pantry":
            invalid_ids.append(iid)
            if reason is None:
                reason = "pantry_in_main_list"

    for pid in dedup_pantry:
        rec = found_map.get(pid)
        if rec is None or not rec.is_active:
            if pid not in invalid_ids:
                invalid_ids.append(pid)
            if reason is None:
                reason = "unknown_or_inactive_id"
        elif rec.category != "pantry":
            if pid not in invalid_ids:
                invalid_ids.append(pid)
            if reason is None:
                reason = "non_pantry_in_excluded_list"

    if invalid_ids:
        raise AppError(
            status_code=422,
            code="INVALID_INGREDIENTS",
            message="Một hoặc nhiều UUID nguyên liệu không tồn tại, đang ngưng hoạt động hoặc sai phân nhóm chính/pantry.",
            details={
                "invalid_ids": invalid_ids,
                "invalid_ingredient_ids": invalid_ids,
                "reason": reason or "unknown_or_inactive_id",
            },
        )

    return dedup_main, dedup_pantry, found_map


def evaluate_recipe_reasoning(
    recipe: RecipeRecord,
    params: ReasoningInput,
    active_pantry_ids: set[str],
) -> RecipeReasoningEvaluation:
    """Evaluate a single recipe under TP 04 Open-World 3-Valued Reasoning & Hard Constraints."""
    u_set = set(params.ingredient_ids)
    x_set = set(params.excluded_pantry_ids)
    m_main_set = set(params.missing_ingredient_ids)
    available_pantry = active_pantry_ids - x_set
    confirmed_available_all = u_set | available_pantry
    confirmed_missing_all = x_set | m_main_set

    # Partition recipe ingredients into R_main, O_main, R_pantry, O_pantry
    r_main: list[str] = []
    o_main: list[str] = []
    r_pantry: list[str] = []

    ingredient_states: dict[str, IngredientTriState] = {}

    for ri in recipe.ingredients:
        iid = ri.ingredient_id
        if iid in confirmed_available_all or (ri.category == "pantry" and iid not in x_set):
            ingredient_states[iid] = "confirmed_available"
        elif iid in confirmed_missing_all:
            ingredient_states[iid] = "confirmed_missing"
        else:
            ingredient_states[iid] = "unknown"

        if ri.category == "pantry":
            if ri.is_required:
                r_pantry.append(iid)
        else:
            if ri.is_required:
                r_main.append(iid)
            else:
                o_main.append(iid)

    matched_req_main = [iid for iid in r_main if iid in u_set]
    matched_opt_main = [iid for iid in o_main if iid in u_set]
    matched_main_ids = sorted(set(matched_req_main + matched_opt_main))

    missing_req_main = [iid for iid in r_main if iid not in u_set]
    missing_pantry = [iid for iid in r_pantry if iid in x_set]
    missing_required_ids = sorted(set(missing_req_main + missing_pantry))
    missing_optional_ids = sorted(iid for iid in o_main if iid not in u_set)

    # Hard constraints check (`recommendation-design.md` Section 4 & Section 8)
    blocked_reasons: list[str] = []

    if recipe.status != "published":
        blocked_reasons.append("not_published")

    if not r_main:
        blocked_reasons.append("missing_required_main_ingredient")

    has_main_overlap = len(matched_main_ids) >= 1
    if not has_main_overlap:
        blocked_reasons.append("no_matched_main_ingredient")

    cuisine_ok = (
        not params.cuisine_codes or recipe.cuisine_code in params.cuisine_codes
    )
    if not cuisine_ok:
        blocked_reasons.append("cuisine_mismatch")

    time_ok = (
        params.max_total_minutes is None
        or recipe.total_minutes <= params.max_total_minutes
    )
    if not time_ok:
        blocked_reasons.append("exceeds_max_total_minutes")

    excluded_allergens = set(params.excluded_allergen_ids)
    diet_ok = not bool(excluded_allergens & set(recipe.allergen_ids))
    if not diet_ok:
        blocked_reasons.append("allergen_violation")

    if params.available_equipment is not None:
        avail_equip = {eq.lower() for eq in params.available_equipment}
        req_equip = {eq.lower() for eq in recipe.required_equipment}
        equip_ok = req_equip.issubset(avail_equip)
    else:
        equip_ok = True
    if not equip_ok:
        blocked_reasons.append("missing_required_equipment")

    if blocked_reasons:
        status_v1_1: RecipeReasoningStatus = "BLOCKED"
        availability_v1_0: AvailabilityV1 | None = None
    elif len(missing_required_ids) == 0:
        status_v1_1 = "READY"
        availability_v1_0 = "ready"
    else:
        # Distinguish MISSING_CONFIRMED vs UNKNOWN in v1.1 while mapping both to "missing" in v1.0
        has_confirmed_missing_req = bool(missing_pantry) or any(
            iid in m_main_set for iid in missing_req_main
        )
        status_v1_1 = "MISSING_CONFIRMED" if has_confirmed_missing_req else "UNKNOWN"
        availability_v1_0 = "missing"

    return RecipeReasoningEvaluation(
        recipe_id=recipe.id,
        status_v1_1=status_v1_1,
        availability_v1_0=availability_v1_0,
        diet_ok=diet_ok,
        equip_ok=equip_ok,
        time_ok=time_ok,
        cuisine_ok=cuisine_ok,
        has_main_overlap=has_main_overlap,
        matched_main_ids=matched_main_ids,
        matched_optional_main_ids=sorted(matched_opt_main),
        missing_required_main_ids=sorted(missing_req_main),
        missing_pantry_ids=sorted(missing_pantry),
        missing_required_ingredient_ids=missing_required_ids,
        missing_optional_ingredient_ids=missing_optional_ids,
        ingredient_states=ingredient_states,
        blocked_reasons=blocked_reasons,
    )


def filter_candidate_recipes(
    repo: CatalogRepository,
    params: ReasoningInput,
) -> list[tuple[RecipeRecord, RecipeReasoningEvaluation]]:
    """Validate inputs, run TP 04 3-state reasoning on all published recipes, and filter hard constraints."""
    dedup_main, dedup_pantry, _ = validate_and_resolve_ingredients(
        repo=repo,
        ingredient_ids=params.ingredient_ids,
        excluded_pantry_ids=params.excluded_pantry_ids,
    )
    normalized_params = params.model_copy(
        update={
            "ingredient_ids": dedup_main,
            "excluded_pantry_ids": dedup_pantry,
        }
    )

    active_pantry_ids = set(repo.get_active_pantry_ingredients().keys())
    published_recipes = repo.get_all_published_recipes()

    feasible: list[tuple[RecipeRecord, RecipeReasoningEvaluation]] = []
    for rec in published_recipes:
        ev = evaluate_recipe_reasoning(rec, normalized_params, active_pantry_ids)
        if ev.status_v1_1 == "BLOCKED":
            continue
        if not normalized_params.include_missing and ev.availability_v1_0 != "ready":
            continue
        feasible.append((rec, ev))

    return feasible
