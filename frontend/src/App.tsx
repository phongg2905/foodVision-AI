import React, { useEffect, useRef, useState } from 'react';
import { Ingredient, RecommendationItem } from './shared/api/types';
import { ActiveTab, AppLayout } from './shared/components/AppLayout';
import { RecipeCatalogView } from './features/recipes/RecipeCatalogView';
import { RecipeDetailView } from './features/recipes/RecipeDetailView';
import { IngredientKitchenView } from './features/search/IngredientKitchenView';
import { RecommendationResultsView } from './features/recommend';

interface ActiveRecipeDetailState {
  recipeId: string;
  returnTab: ActiveTab;
  recommendationItem?: RecommendationItem;
}

interface KitchenDraftStorage {
  selectedIngredients?: Ingredient[];
  excludedPantryIds?: string[];
  mainIngredientIds?: string[];
  desiredMinutes?: number | null;
}

const KITCHEN_DRAFT_STORAGE_KEY = 'foodvision_kitchen_draft_v1';

function isValidTab(value: string | null): value is ActiveTab {
  return value === 'catalog' || value === 'kitchen' || value === 'recommendations';
}

function parseRouteFromLocation(): {
  tab: ActiveTab;
  detail: ActiveRecipeDetailState | null;
} {
  if (typeof window === 'undefined') {
    return { tab: 'catalog', detail: null };
  }
  try {
    const params = new URLSearchParams(window.location.search);
    const rawTab = params.get('tab');
    const recipeId = params.get('recipe');
    const tab: ActiveTab = isValidTab(rawTab) ? rawTab : 'catalog';

    if (recipeId && recipeId.trim().length > 0) {
      return {
        tab,
        detail: {
          recipeId: recipeId.trim(),
          returnTab: tab,
        },
      };
    }

    return { tab, detail: null };
  } catch {
    return { tab: 'catalog', detail: null };
  }
}

function buildRouteUrl(
  tab: ActiveTab,
  detail: ActiveRecipeDetailState | null
): string {
  const basePath =
    typeof window !== 'undefined' && window.location.pathname
      ? window.location.pathname
      : '/';

  if (detail) {
    const params = new URLSearchParams();
    params.set('tab', detail.returnTab);
    params.set('recipe', detail.recipeId);
    return `${basePath}?${params.toString()}`;
  }

  if (tab === 'catalog') {
    return basePath;
  }

  const params = new URLSearchParams();
  params.set('tab', tab);
  return `${basePath}?${params.toString()}`;
}

function pushRouteHistory(
  tab: ActiveTab,
  detail: ActiveRecipeDetailState | null
): void {
  if (typeof window === 'undefined' || !window.history?.pushState) return;
  try {
    const targetUrl = buildRouteUrl(tab, detail);
    const currentUrl = `${window.location.pathname || '/'}${window.location.search || ''}`;
    if (targetUrl !== currentUrl) {
      window.history.pushState({ tab, recipeId: detail?.recipeId ?? null }, '', targetUrl);
    }
  } catch {
    // Bỏ qua trong môi trường hạn chế History API
  }
}

function loadKitchenDraft(): KitchenDraftStorage {
  if (typeof window === 'undefined') return {};
  try {
    const raw = window.sessionStorage?.getItem(KITCHEN_DRAFT_STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as KitchenDraftStorage;
    return {
      selectedIngredients: Array.isArray(parsed.selectedIngredients)
        ? parsed.selectedIngredients
        : [],
      excludedPantryIds: Array.isArray(parsed.excludedPantryIds)
        ? parsed.excludedPantryIds
        : [],
      mainIngredientIds: Array.isArray(parsed.mainIngredientIds)
        ? parsed.mainIngredientIds
        : [],
      desiredMinutes:
        typeof parsed.desiredMinutes === 'number' || parsed.desiredMinutes === null
          ? parsed.desiredMinutes
          : null,
    };
  } catch {
    return {};
  }
}

function safeScrollToTop(): void {
  try {
    if (
      typeof window !== 'undefined' &&
      typeof window.scrollTo === 'function' &&
      !window.navigator?.userAgent?.includes('jsdom')
    ) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  } catch {
    // Bỏ qua trong môi trường test
  }
}

export const App: React.FC = () => {
  const initialRoute = useRef(parseRouteFromLocation()).current;
  const initialDraft = useRef(loadKitchenDraft()).current;
  const recommendationCacheRef = useRef<Map<string, RecommendationItem>>(
    new Map()
  );

  const [activeTab, setActiveTab] = useState<ActiveTab>(initialRoute.tab);
  const [selectedIngredients, setSelectedIngredients] = useState<Ingredient[]>(
    () => initialDraft.selectedIngredients ?? []
  );
  // Mặc định cả 5 gia vị sẵn có trong bếp đều được bật -> excludedPantryIds = [] (FR-05, ADR-008)
  const [excludedPantryIds, setExcludedPantryIds] = useState<string[]>(
    () => initialDraft.excludedPantryIds ?? []
  );
  const [mainIngredientIds, setMainIngredientIds] = useState<string[]>(
    () => initialDraft.mainIngredientIds ?? []
  );
  const [desiredMinutes, setDesiredMinutes] = useState<number | null>(
    () => initialDraft.desiredMinutes ?? null
  );
  const [activeRecipeDetail, setActiveRecipeDetail] =
    useState<ActiveRecipeDetailState | null>(initialRoute.detail);

  // Đồng bộ nút Back / Forward vật lý của trình duyệt (popstate)
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handlePopState = () => {
      const next = parseRouteFromLocation();
      setActiveTab(next.tab);
      if (next.detail) {
        const cachedItem =
          next.detail.returnTab === 'recommendations'
            ? recommendationCacheRef.current.get(next.detail.recipeId)
            : undefined;
        setActiveRecipeDetail({
          ...next.detail,
          recommendationItem: cachedItem,
        });
      } else {
        setActiveRecipeDetail(null);
      }
      safeScrollToTop();
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  // Lưu tạm danh sách nguyên liệu & tùy chọn bếp trong phiên làm việc (giữ trạng thái khi F5)
  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      const payload: KitchenDraftStorage = {
        selectedIngredients,
        excludedPantryIds,
        mainIngredientIds,
        desiredMinutes,
      };
      window.sessionStorage?.setItem(
        KITCHEN_DRAFT_STORAGE_KEY,
        JSON.stringify(payload)
      );
    } catch {
      // Bỏ qua nếu trình duyệt chặn sessionStorage
    }
  }, [selectedIngredients, excludedPantryIds, mainIngredientIds, desiredMinutes]);

  const handleTabChange = (tab: ActiveTab) => {
    setActiveRecipeDetail(null);
    setActiveTab(tab);
    pushRouteHistory(tab, null);
    safeScrollToTop();
  };

  const handleTriggerRecommend = () => {
    setActiveRecipeDetail(null);
    setActiveTab('recommendations');
    pushRouteHistory('recommendations', null);
    safeScrollToTop();
  };

  const handleOpenRecipeDetail = (
    recipeId: string,
    returnTab: ActiveTab,
    recommendationItem?: RecommendationItem
  ) => {
    if (recommendationItem) {
      recommendationCacheRef.current.set(recipeId, recommendationItem);
    }
    const nextDetail: ActiveRecipeDetailState = {
      recipeId,
      returnTab,
      recommendationItem,
    };
    setActiveRecipeDetail(nextDetail);
    pushRouteHistory(returnTab, nextDetail);
    safeScrollToTop();
  };

  const handleBackFromDetail = () => {
    const returnTab = activeRecipeDetail?.returnTab ?? activeTab;
    setActiveRecipeDetail(null);
    setActiveTab(returnTab);
    pushRouteHistory(returnTab, null);
    safeScrollToTop();
  };

  return (
    <AppLayout
      activeTab={activeRecipeDetail ? activeRecipeDetail.returnTab : activeTab}
      onTabChange={handleTabChange}
      selectedMainCount={selectedIngredients.length}
    >
      {activeRecipeDetail ? (
        <RecipeDetailView
          recipeId={activeRecipeDetail.recipeId}
          backLabel={
            activeRecipeDetail.returnTab === 'recommendations'
              ? 'Quay lại Danh sách gợi ý'
              : 'Quay lại Danh mục công thức'
          }
          recommendationContext={activeRecipeDetail.recommendationItem}
          onBack={handleBackFromDetail}
        />
      ) : activeTab === 'catalog' ? (
        <RecipeCatalogView
          onSelectRecipe={(recipeId) =>
            handleOpenRecipeDetail(recipeId, 'catalog')
          }
        />
      ) : activeTab === 'kitchen' ? (
        <IngredientKitchenView
          selectedIngredients={selectedIngredients}
          onSelectedIngredientsChange={setSelectedIngredients}
          excludedPantryIds={excludedPantryIds}
          onExcludedPantryIdsChange={setExcludedPantryIds}
          mainIngredientIds={mainIngredientIds}
          onMainIngredientIdsChange={setMainIngredientIds}
          desiredMinutes={desiredMinutes}
          onDesiredMinutesChange={setDesiredMinutes}
          onTriggerRecommend={handleTriggerRecommend}
        />
      ) : (
        <RecommendationResultsView
          selectedIngredients={selectedIngredients}
          excludedPantryIds={excludedPantryIds}
          mainIngredientIds={mainIngredientIds}
          onMainIngredientIdsChange={setMainIngredientIds}
          desiredMinutes={desiredMinutes}
          onDesiredMinutesChange={setDesiredMinutes}
          onBackToKitchen={() => handleTabChange('kitchen')}
          onSelectRecipe={(recipeId, item) =>
            handleOpenRecipeDetail(recipeId, 'recommendations', item)
          }
        />
      )}
    </AppLayout>
  );
};

export default App;
