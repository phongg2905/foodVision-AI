import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  listPantryIngredients,
  searchMainIngredients,
} from './shared/api/ingredientsApi';
import {
  MOCK_MAIN_INGREDIENTS,
  MOCK_PANTRY_INGREDIENTS,
} from './shared/api/mockData';
import { Ingredient, RecommendationItem } from './shared/api/types';

const STARTER_SLUG_FALLBACKS: Record<string, string[]> = {
  'thit-heo': ['thit-ba-chi', 'thit-heo-song'],
  'uc-ga': ['thit-ga-song'],
  'tom-tuoi': ['tom'],
  bap: ['bap-ngot'],
  'hat-tieu': ['tieu-xay'],
};

function resolveIngredientBySlug(
  slug: string,
  bySlug: Map<string, Ingredient>
): Ingredient | undefined {
  const direct = bySlug.get(slug);
  if (direct) return direct;
  const aliases = STARTER_SLUG_FALLBACKS[slug] ?? [];
  for (const alt of aliases) {
    const found = bySlug.get(alt);
    if (found) return found;
  }
  return undefined;
}
import { ActiveTab, AppLayout } from './shared/components/AppLayout';
import { RecipeCatalogView } from './features/recipes/RecipeCatalogView';
import { RecipeDetailView } from './features/recipes/RecipeDetailView';
import { IngredientKitchenView } from './features/search/IngredientKitchenView';
import { RecommendationResultsView } from './features/recommend';

interface ActiveRecipeDetailState {
  recipeId: string;
  returnTab: 'catalog' | 'kitchen';
  recommendationItem?: RecommendationItem;
}

interface KitchenDraftStorage {
  selectedIngredients?: Ingredient[];
  excludedPantryIds?: string[];
  mainIngredientIds?: string[];
  desiredMinutes?: number | null;
}

const KITCHEN_DRAFT_STORAGE_KEY = 'foodvision_kitchen_draft_v1';

function normalizeSpaceTab(rawTab: string | null): 'catalog' | 'kitchen' {
  if (rawTab === 'kitchen' || rawTab === 'recommendations') {
    return 'kitchen';
  }
  return 'catalog';
}

function parseRouteFromLocation(): {
  tab: 'catalog' | 'kitchen';
  detail: ActiveRecipeDetailState | null;
} {
  if (typeof window === 'undefined') {
    return { tab: 'catalog', detail: null };
  }
  try {
    const params = new URLSearchParams(window.location.search);
    const tab = normalizeSpaceTab(params.get('tab'));
    const recipeId = params.get('recipe');

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
  tab: 'catalog' | 'kitchen',
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
  params.set('tab', 'kitchen');
  return `${basePath}?${params.toString()}`;
}

function pushRouteHistory(
  tab: 'catalog' | 'kitchen',
  detail: ActiveRecipeDetailState | null
): void {
  if (typeof window === 'undefined' || !window.history?.pushState) return;
  try {
    const targetUrl = buildRouteUrl(tab, detail);
    const currentUrl = `${window.location.pathname || '/'}${window.location.search || ''}`;
    if (targetUrl !== currentUrl) {
      window.history.pushState(
        { tab, recipeId: detail?.recipeId ?? null },
        '',
        targetUrl
      );
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
        typeof parsed.desiredMinutes === 'number' ||
        parsed.desiredMinutes === null
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

function safeScrollElementIntoView(elementId: string): void {
  try {
    if (
      typeof document !== 'undefined' &&
      !window.navigator?.userAgent?.includes('jsdom')
    ) {
      const target = document.getElementById(elementId);
      if (target && typeof target.scrollIntoView === 'function') {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
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

  const [activeTab, setActiveTab] = useState<'catalog' | 'kitchen'>(
    initialRoute.tab
  );
  const [catalogSearchQuery, setCatalogSearchQuery] = useState('');
  const [liveMainIngredients, setLiveMainIngredients] = useState<Ingredient[]>(
    MOCK_MAIN_INGREDIENTS
  );
  const [livePantryIngredients, setLivePantryIngredients] = useState<
    Ingredient[]
  >(MOCK_PANTRY_INGREDIENTS);
  const [selectedIngredients, setSelectedIngredients] = useState<Ingredient[]>(
    () => initialDraft.selectedIngredients ?? []
  );
  const [excludedPantryIds, setExcludedPantryIds] = useState<string[]>(
    () => initialDraft.excludedPantryIds ?? []
  );
  const [mainIngredientIds, setMainIngredientIds] = useState<string[]>(
    () => initialDraft.mainIngredientIds ?? []
  );
  const [desiredMinutes, setDesiredMinutes] = useState<number | null>(
    () => initialDraft.desiredMinutes ?? null
  );
  const [activeScanId, setActiveScanId] = useState<string | null>(null);
  const [activeRecipeDetail, setActiveRecipeDetail] =
    useState<ActiveRecipeDetailState | null>(initialRoute.detail);

  const knownCatalogIngredients = useMemo(
    () => [...liveMainIngredients, ...livePantryIngredients],
    [liveMainIngredients, livePantryIngredients]
  );

  // Đồng bộ danh mục nguyên liệu & gia vị thật từ Backend và tự chuẩn hóa UUID cũ lưu trong sessionStorage
  useEffect(() => {
    let isCancelled = false;

    Promise.all([
      searchMainIngredients('', 50, 0).catch(() => null),
      listPantryIngredients().catch(() => null),
    ]).then(([mainRes, pantryRes]) => {
      if (isCancelled) return;

      if (mainRes && mainRes.items.length > 0) {
        const liveMain = mainRes.items.filter(
          (item) => item.category !== 'pantry' && item.is_active
        );
        if (liveMain.length > 0) {
          setLiveMainIngredients(liveMain);
        }

        const byId = new Map(liveMain.map((item) => [item.id, item] as const));
        const bySlug = new Map(
          liveMain.map((item) => [item.slug, item] as const)
        );
        const remappedIdPairs = new Map<string, string>();

        setSelectedIngredients((prev) => {
          if (prev.length === 0) return prev;
          let changed = false;
          const next: Ingredient[] = [];
          const seen = new Set<string>();

          for (const item of prev) {
            const matched =
              byId.get(item.id) ?? resolveIngredientBySlug(item.slug, bySlug);
            if (!matched) {
              changed = true;
              continue;
            }
            if (matched.id !== item.id) {
              changed = true;
              remappedIdPairs.set(item.id, matched.id);
            }
            if (!seen.has(matched.id)) {
              seen.add(matched.id);
              next.push(matched);
            } else {
              changed = true;
            }
          }
          return changed ? next : prev;
        });

        setMainIngredientIds((prev) => {
          if (prev.length === 0) return prev;
          const mapped = Array.from(
            new Set(
              prev
                .map((id) => remappedIdPairs.get(id) ?? id)
                .filter((id) => byId.has(id))
            )
          );
          if (
            mapped.length === prev.length &&
            mapped.every((id, idx) => id === prev[idx])
          ) {
            return prev;
          }
          return mapped;
        });
      }

      if (pantryRes && pantryRes.items.length > 0) {
        const livePantry = pantryRes.items.filter(
          (item) => item.category === 'pantry' && item.is_active
        );
        if (livePantry.length > 0) {
          setLivePantryIngredients(livePantry);
        }

        const livePantryById = new Set(livePantry.map((item) => item.id));
        const livePantryBySlug = new Map(
          livePantry.map((item) => [item.slug, item] as const)
        );
        const mockPantryById = new Map(
          MOCK_PANTRY_INGREDIENTS.map((item) => [item.id, item] as const)
        );

        setExcludedPantryIds((prev) => {
          if (prev.length === 0) return prev;
          const mapped: string[] = [];
          for (const id of prev) {
            if (livePantryById.has(id)) {
              mapped.push(id);
              continue;
            }
            const oldMock = mockPantryById.get(id);
            if (oldMock) {
              const liveMatch = resolveIngredientBySlug(
                oldMock.slug,
                livePantryBySlug
              );
              if (liveMatch) {
                mapped.push(liveMatch.id);
              }
            }
          }
          const uniqueMapped = Array.from(new Set(mapped));
          if (
            uniqueMapped.length === prev.length &&
            uniqueMapped.every((id, idx) => id === prev[idx])
          ) {
            return prev;
          }
          return uniqueMapped;
        });
      }
    });

    return () => {
      isCancelled = true;
    };
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handlePopState = () => {
      const next = parseRouteFromLocation();
      setActiveTab(next.tab);
      if (next.detail) {
        const cachedItem =
          next.detail.returnTab === 'kitchen'
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
  }, [
    selectedIngredients,
    excludedPantryIds,
    mainIngredientIds,
    desiredMinutes,
  ]);

  const handleTabChange = (nextRawTab: ActiveTab) => {
    const nextTab = normalizeSpaceTab(nextRawTab);
    setActiveRecipeDetail(null);
    setActiveTab(nextTab);
    pushRouteHistory(nextTab, null);
    safeScrollToTop();
  };

  const handleQuickSearchChange = (query: string) => {
    setCatalogSearchQuery(query);
    if (
      query.trim().length > 0 &&
      (activeTab !== 'catalog' || activeRecipeDetail)
    ) {
      setActiveRecipeDetail(null);
      setActiveTab('catalog');
      pushRouteHistory('catalog', null);
    }
  };

  const handleQuickSearchSubmit = () => {
    setActiveRecipeDetail(null);
    setActiveTab('catalog');
    pushRouteHistory('catalog', null);
    safeScrollElementIntoView('special-recipes');
  };

  const handleApplyStarterSlugs = (slugs: string[]) => {
    const bySlug = new Map(
      liveMainIngredients.map((item) => [item.slug, item] as const)
    );
    const matched = slugs
      .map((slug) => resolveIngredientBySlug(slug, bySlug))
      .filter((item): item is Ingredient => Boolean(item));
    if (matched.length === 0) return;

    const deduped = Array.from(
      new Map(matched.map((item) => [item.id, item] as const)).values()
    );
    setSelectedIngredients(deduped);
    setMainIngredientIds([deduped[0].id]);
    setActiveScanId(null);
    setActiveRecipeDetail(null);
    setActiveTab('kitchen');
    pushRouteHistory('kitchen', null);
    safeScrollToTop();
  };

  const handleTriggerRecommend = () => {
    setActiveRecipeDetail(null);
    setActiveTab('kitchen');
    pushRouteHistory('kitchen', null);
    safeScrollElementIntoView('live-recommendations-panel');
  };

  const handleOpenRecipeDetail = (
    recipeId: string,
    returnTab: 'catalog' | 'kitchen',
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
      quickSearchQuery={catalogSearchQuery}
      onQuickSearchChange={handleQuickSearchChange}
      onQuickSearchSubmit={handleQuickSearchSubmit}
    >
      {activeRecipeDetail ? (
        <RecipeDetailView
          recipeId={activeRecipeDetail.recipeId}
          backLabel={
            activeRecipeDetail.returnTab === 'kitchen'
              ? 'Quay lại Gợi ý từ tủ bếp'
              : 'Quay lại Khám phá công thức'
          }
          recommendationContext={activeRecipeDetail.recommendationItem}
          onBack={handleBackFromDetail}
        />
      ) : activeTab === 'catalog' ? (
        <RecipeCatalogView
          externalSearchQuery={catalogSearchQuery}
          onExternalSearchQueryChange={setCatalogSearchQuery}
          onOpenKitchen={() => handleTabChange('kitchen')}
          onApplyStarterSlugs={handleApplyStarterSlugs}
          onSelectRecipe={(recipeId) =>
            handleOpenRecipeDetail(recipeId, 'catalog')
          }
        />
      ) : (
        /* KHÔNG GIAN 2 CHUẨN MOCKUP A: THANH TỦ BẾP NGANG GỌN PHÍA TRÊN + LƯỚI 4 CỘT ĐỒNG BỘ TRANG CHỦ */
        <div
          data-testid="kitchen-studio-workspace"
          className="space-y-8 pt-2"
        >
          <h1 className="sr-only">Gợi ý từ tủ bếp</h1>

          <IngredientKitchenView
            studioMode
            selectedIngredients={selectedIngredients}
            onSelectedIngredientsChange={setSelectedIngredients}
            excludedPantryIds={excludedPantryIds}
            onExcludedPantryIdsChange={setExcludedPantryIds}
            mainIngredientIds={mainIngredientIds}
            onMainIngredientIdsChange={setMainIngredientIds}
            desiredMinutes={desiredMinutes}
            onDesiredMinutesChange={setDesiredMinutes}
            scanId={activeScanId}
            onScanIdChange={setActiveScanId}
            onTriggerRecommend={handleTriggerRecommend}
          />

          <div id="live-recommendations-panel" className="scroll-mt-5">
            <RecommendationResultsView
              embeddedInStudio
              selectedIngredients={selectedIngredients}
              knownCatalogIngredients={knownCatalogIngredients}
              excludedPantryIds={excludedPantryIds}
              mainIngredientIds={mainIngredientIds}
              onMainIngredientIdsChange={setMainIngredientIds}
              desiredMinutes={desiredMinutes}
              onDesiredMinutesChange={setDesiredMinutes}
              scanId={activeScanId}
              onBackToKitchen={() => safeScrollToTop()}
              onApplyStarterSlugs={handleApplyStarterSlugs}
              onSelectRecipe={(recipeId, item) =>
                handleOpenRecipeDetail(recipeId, 'kitchen', item)
              }
            />
          </div>
        </div>
      )}
    </AppLayout>
  );
};

export default App;
