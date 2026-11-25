import { apiPostWithFallback } from './client';
import {
  MOCK_PANTRY_INGREDIENTS,
  MOCK_RECIPE_DETAILS,
  MOCK_RECIPE_SCORING_META,
  getIngredientNameById,
} from './mockData';
import {
  AvailabilityStatus,
  ReasoningStatus,
  RecommendRequest,
  RecommendResponse,
  RecommendationItem,
  RecipeDetail,
} from './types';

function roundTo2(value: number): number {
  return Math.round(value * 100) / 100;
}

function roundTo6(value: number): number {
  return Math.round(value * 1_000_000) / 1_000_000;
}

function dedupeIds<T extends string>(ids: T[] | undefined): T[] {
  if (!ids || ids.length === 0) return [];
  return Array.from(new Set(ids));
}

function buildSanitizedRequestBody(request: RecommendRequest): RecommendRequest {
  const dedupIngredients = dedupeIds(request.ingredient_ids);
  const ingredientSet = new Set(dedupIngredients);
  const dedupMain = dedupeIds(request.main_ingredient_ids).filter((id) =>
    ingredientSet.has(id)
  );
  const desiredHours =
    typeof request.desired_hours === 'number' && request.desired_hours > 0
      ? request.desired_hours
      : 100.0;

  const payload: RecommendRequest = {
    ingredient_ids: dedupIngredients,
    main_ingredient_ids: dedupMain,
    desired_hours: desiredHours,
    excluded_pantry_ids: dedupeIds(request.excluded_pantry_ids),
    cuisine_codes: dedupeIds(request.cuisine_codes),
    max_total_minutes: request.max_total_minutes ?? null,
    include_missing: request.include_missing ?? true,
    diversify: request.diversify ?? false,
    limit: Math.min(Math.max(request.limit ?? 20, 1), 50),
  };

  // Không tự gán mặc định allergic_ingredient_ids / kitchen_spice_ids / favorite_ingredient_ids
  // để Backend (model_fields_set) tự nạp user_preferences nếu User đã đăng nhập.
  if (request.allergic_ingredient_ids !== undefined) {
    payload.allergic_ingredient_ids = dedupeIds(
      request.allergic_ingredient_ids
    );
  }
  if (request.kitchen_spice_ids !== undefined) {
    payload.kitchen_spice_ids =
      request.kitchen_spice_ids === null
        ? null
        : dedupeIds(request.kitchen_spice_ids);
  }
  if (request.favorite_ingredient_ids !== undefined) {
    payload.favorite_ingredient_ids = dedupeIds(
      request.favorite_ingredient_ids
    );
  }
  if (request.scan_id !== undefined) {
    payload.scan_id = request.scan_id;
  }

  return payload;
}

function compareRecommendationTieBreak(
  a: RecommendationItem,
  b: RecommendationItem
): number {
  if (a.score !== b.score) {
    return b.score - a.score;
  }
  if (
    a.missing_required_ingredient_ids.length !==
    b.missing_required_ingredient_ids.length
  ) {
    return (
      a.missing_required_ingredient_ids.length -
      b.missing_required_ingredient_ids.length
    );
  }
  if (a.recipe.total_minutes !== b.recipe.total_minutes) {
    return a.recipe.total_minutes - b.recipe.total_minutes;
  }
  return a.recipe.id.localeCompare(b.recipe.id);
}

function computeRecipeSimilarity(idA: string, idB: string): number {
  if (idA === idB) return 1.0;
  const recA = MOCK_RECIPE_DETAILS[idA];
  const recB = MOCK_RECIPE_DETAILS[idB];
  if (!recA || !recB) return 0.0;

  const metaA = MOCK_RECIPE_SCORING_META[idA];
  const metaB = MOCK_RECIPE_SCORING_META[idB];

  const methodSim =
    metaA?.cookingMethod && metaA.cookingMethod === metaB?.cookingMethod
      ? 1.0
      : 0.0;
  const cuisineSim = recA.cuisine_code === recB.cuisine_code ? 1.0 : 0.0;

  const mainA = new Set(
    recA.ingredients
      .filter((ri) => ri.category !== 'pantry')
      .map((ri) => ri.ingredient_id)
  );
  const mainB = new Set(
    recB.ingredients
      .filter((ri) => ri.category !== 'pantry')
      .map((ri) => ri.ingredient_id)
  );
  const unionSet = new Set([...mainA, ...mainB]);
  let intersectionCount = 0;
  mainA.forEach((id) => {
    if (mainB.has(id)) intersectionCount += 1;
  });
  const ingSim = unionSet.size > 0 ? intersectionCount / unionSet.size : 0.0;

  return 0.4 * methodSim + 0.2 * cuisineSim + 0.4 * ingSim;
}

function rerankWithMmr(
  items: RecommendationItem[],
  topK: number,
  lambdaMmr = 0.7
): RecommendationItem[] {
  const selectPool = (
    pool: RecommendationItem[],
    kLimit: number
  ): RecommendationItem[] => {
    if (pool.length === 0 || kLimit <= 0) return [];
    const remaining = [...pool].sort(compareRecommendationTieBreak);
    const selected: RecommendationItem[] = [remaining.shift()!];

    while (remaining.length > 0 && selected.length < kLimit) {
      let bestIndex = 0;
      let bestMmr = -Infinity;

      for (let idx = 0; idx < remaining.length; idx += 1) {
        const cand = remaining[idx];
        const maxSim = Math.max(
          ...selected.map((sel) =>
            computeRecipeSimilarity(cand.recipe.id, sel.recipe.id)
          )
        );
        const mmrVal =
          lambdaMmr * (cand.score / 100.0) - (1.0 - lambdaMmr) * maxSim;

        if (
          mmrVal > bestMmr + 1e-9 ||
          (Math.abs(mmrVal - bestMmr) <= 1e-9 &&
            compareRecommendationTieBreak(cand, remaining[bestIndex]) < 0)
        ) {
          bestMmr = mmrVal;
          bestIndex = idx;
        }
      }

      const [chosen] = remaining.splice(bestIndex, 1);
      selected.push(chosen);
    }

    return selected;
  };

  const readyPool = items.filter((item) => item.availability === 'ready');
  const missingPool = items.filter((item) => item.availability === 'missing');

  const selectedReady = selectPool(readyPool, topK);
  const remainingSlots = topK - selectedReady.length;
  const selectedMissing =
    remainingSlots > 0 ? selectPool(missingPool, remainingSlots) : [];

  return [...selectedReady, ...selectedMissing];
}

function scoreMockRecipe(
  recipe: RecipeDetail,
  sanitized: RecommendRequest
): RecommendationItem | null {
  const uList = sanitized.ingredient_ids;
  const uSet = new Set(uList);
  const excludedSet = new Set(sanitized.excluded_pantry_ids ?? []);
  const allergicSet = new Set(sanitized.allergic_ingredient_ids ?? []);
  const favSet = new Set(sanitized.favorite_ingredient_ids ?? []);
  const mainSet = new Set(sanitized.main_ingredient_ids ?? []);

  // Lọc cứng nền ẩm thực và thời gian tối đa
  const cuisineCodes = sanitized.cuisine_codes ?? [];
  if (
    cuisineCodes.length > 0 &&
    !cuisineCodes.includes(recipe.cuisine_code)
  ) {
    return null;
  }
  if (
    typeof sanitized.max_total_minutes === 'number' &&
    recipe.total_minutes > sanitized.max_total_minutes
  ) {
    return null;
  }

  // Lọc cứng dị ứng nguyên liệu
  if (recipe.ingredients.some((ri) => allergicSet.has(ri.ingredient_id))) {
    return null;
  }

  // Tập gia vị pantry sẵn có
  const basePantryIds =
    sanitized.kitchen_spice_ids !== undefined &&
    sanitized.kitchen_spice_ids !== null
      ? new Set(sanitized.kitchen_spice_ids)
      : new Set(MOCK_PANTRY_INGREDIENTS.map((item) => item.id));

  const availablePantryIds = new Set<string>();
  basePantryIds.forEach((id) => {
    if (!excludedSet.has(id)) {
      availablePantryIds.add(id);
    }
  });

  const confirmedAvailableAll = new Set<string>([
    ...uSet,
    ...availablePantryIds,
  ]);

  const matchedMainIds: string[] = [];
  const missingRequiredIds: string[] = [];
  const missingOptionalIds: string[] = [];
  let hasMissingPantry = false;

  for (const ri of recipe.ingredients) {
    if (ri.category === 'pantry') {
      if (ri.is_required && !availablePantryIds.has(ri.ingredient_id)) {
        missingRequiredIds.push(ri.ingredient_id);
        hasMissingPantry = true;
      }
    } else if (uSet.has(ri.ingredient_id)) {
      matchedMainIds.push(ri.ingredient_id);
    } else if (ri.is_required) {
      missingRequiredIds.push(ri.ingredient_id);
    } else {
      missingOptionalIds.push(ri.ingredient_id);
    }
  }

  // Bắt buộc khớp tối thiểu 1 nguyên liệu chính (`C > 0`)
  if (matchedMainIds.length === 0) {
    return null;
  }

  const availability: AvailabilityStatus =
    missingRequiredIds.length === 0 ? 'ready' : 'missing';

  if (sanitized.include_missing === false && availability !== 'ready') {
    return null;
  }

  const reasoningStatus: ReasoningStatus =
    availability === 'ready'
      ? 'READY'
      : hasMissingPantry
        ? 'MISSING_CONFIRMED'
        : 'UNKNOWN';

  // Tiêu chí 1: Weighted Coverage C (`4-2-1-0`)
  const meta = MOCK_RECIPE_SCORING_META[recipe.id];
  let totalWeight = 0;
  let matchedWeight = 0;
  for (const ri of recipe.ingredients) {
    if (!ri.is_required) continue;
    const explicitW = meta?.rolesByIngredientId[ri.ingredient_id]?.weight;
    const w =
      explicitW !== undefined && explicitW > 0
        ? explicitW
        : ri.category === 'pantry'
          ? 1
          : 2;
    totalWeight += w;
    if (confirmedAvailableAll.has(ri.ingredient_id)) {
      matchedWeight += w;
    }
  }
  const cVal = totalWeight > 0 ? matchedWeight / totalWeight : 0.0;

  // Tiêu chí 2: Main Ingredient Role G (`0.7 / 0.3` split)
  const dishRoleMap = new Map<string, number>();
  for (const ri of recipe.ingredients) {
    const dRole =
      meta?.rolesByIngredientId[ri.ingredient_id]?.dishRole ?? 'sub';
    dishRoleMap.set(ri.ingredient_id, dRole === 'main' ? 1.0 : 0.5);
  }
  const uMain = uList.filter((id) => mainSet.has(id));
  const uSub = uList.filter((id) => !mainSet.has(id));
  let gVal = 0;
  if (uMain.length === 0 || uSub.length === 0) {
    gVal =
      uList.reduce((acc, id) => acc + (dishRoleMap.get(id) ?? 0), 0) /
      uList.length;
  } else {
    const wMain = 0.7 / uMain.length;
    const wSub = 0.3 / uSub.length;
    const mainSum = uMain.reduce(
      (acc, id) => acc + wMain * (dishRoleMap.get(id) ?? 0),
      0
    );
    const subSum = uSub.reduce(
      (acc, id) => acc + wSub * (dishRoleMap.get(id) ?? 0),
      0
    );
    gVal = mainSum + subSum;
  }

  // Tiêu chí 3: Time Score T
  const tHours = Math.max(1, recipe.total_minutes) / 60.0;
  const tVal = Math.min(1.0, (sanitized.desired_hours ?? 100.0) / tHours);

  // Tiêu chí 4: Preference Score P (`0.5` trung lập khi chưa chọn favorite)
  let pVal = 0.5;
  if (favSet.size > 0) {
    const recipeIngIds = new Set(
      recipe.ingredients.map((ri) => ri.ingredient_id)
    );
    let favHits = 0;
    favSet.forEach((id) => {
      if (recipeIngIds.has(id)) favHits += 1;
    });
    pVal = favHits / favSet.size;
  }

  const contribC = roundTo2(50.0 * cVal);
  const contribG = roundTo2(25.0 * gVal);
  const contribT = roundTo2(15.0 * tVal);
  const contribP = roundTo2(10.0 * pVal);
  const totalScore = roundTo2(contribC + contribG + contribT + contribP);

  const matchedNames = matchedMainIds.map((id) => getIngredientNameById(id));
  const missingNames = missingRequiredIds.map((id) =>
    getIngredientNameById(id)
  );
  const explanationVi =
    availability === 'ready'
      ? `Đủ nguyên liệu bắt buộc để nấu ngay (${matchedNames.join(', ')}); hoàn thành trong ${recipe.total_minutes} phút.`
      : `Đã có ${matchedNames.join(', ')}; cần chuẩn bị thêm: ${missingNames.join(', ')} (tổng thời gian ${recipe.total_minutes} phút).`;

  return {
    recipe: {
      id: recipe.id,
      slug: recipe.slug,
      name_vi: recipe.name_vi,
      cuisine_code: recipe.cuisine_code,
      prep_minutes: recipe.prep_minutes,
      cook_minutes: recipe.cook_minutes,
      total_minutes: recipe.total_minutes,
      cover_image_url: recipe.cover_image_url,
    },
    availability,
    reasoning_status: reasoningStatus,
    score: totalScore,
    matched_ingredient_ids: matchedMainIds,
    missing_required_ingredient_ids: missingRequiredIds,
    missing_optional_ingredient_ids: missingOptionalIds,
    score_breakdown: {
      C: roundTo6(cVal),
      G: roundTo6(gVal),
      T: roundTo6(tVal),
      P: roundTo6(pVal),
    },
    score_contributions: {
      C: contribC,
      G: contribG,
      T: contribT,
      P: contribP,
    },
    explanation_vi: explanationVi,
  };
}

/**
 * Bộ gợi ý dự phòng chạy chuẩn thuật toán ADR-013 (`C, G, T, P` & MMR)
 * trên kho dữ liệu `MOCK_RECIPE_DETAILS` khi Backend chưa khởi chạy.
 */
export function computeMockRecommendations(
  request: RecommendRequest
): RecommendResponse {
  const sanitized = buildSanitizedRequestBody(request);
  if (sanitized.ingredient_ids.length === 0) {
    return {
      items: [],
      total: 0,
      limit: sanitized.limit ?? 20,
    };
  }

  const scored: RecommendationItem[] = [];
  for (const recipe of Object.values(MOCK_RECIPE_DETAILS)) {
    const item = scoreMockRecipe(recipe, sanitized);
    if (item !== null) {
      scored.push(item);
    }
  }

  scored.sort((a, b) => {
    const groupDiff =
      (a.availability === 'ready' ? 0 : 1) -
      (b.availability === 'ready' ? 0 : 1);
    if (groupDiff !== 0) return groupDiff;
    return compareRecommendationTieBreak(a, b);
  });

  const limit = sanitized.limit ?? 20;
  const pageItems = sanitized.diversify
    ? rerankWithMmr(scored, limit)
    : scored.slice(0, limit);

  return {
    items: pageItems,
    total: scored.length,
    limit,
  };
}

/**
 * Gọi POST /api/v1/recommendations theo hợp đồng OpenAPI v1.1.0 (`ADR-013`).
 */
export async function postRecommendations(
  request: RecommendRequest,
  signal?: AbortSignal
): Promise<RecommendResponse> {
  const sanitizedBody = buildSanitizedRequestBody(request);
  return apiPostWithFallback<RecommendRequest, RecommendResponse>(
    '/recommendations',
    sanitizedBody,
    () => computeMockRecommendations(sanitizedBody),
    signal
  );
}
