import React, { useState } from 'react';
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
  const [activeTab, setActiveTab] = useState<ActiveTab>('catalog');
  const [selectedIngredients, setSelectedIngredients] = useState<Ingredient[]>(
    []
  );
  // Mặc định cả 5 gia vị sẵn có trong bếp đều được bật -> excludedPantryIds = [] (FR-05, ADR-008)
  const [excludedPantryIds, setExcludedPantryIds] = useState<string[]>([]);
  const [mainIngredientIds, setMainIngredientIds] = useState<string[]>([]);
  const [desiredMinutes, setDesiredMinutes] = useState<number | null>(null);
  const [activeRecipeDetail, setActiveRecipeDetail] =
    useState<ActiveRecipeDetailState | null>(null);

  const handleTabChange = (tab: ActiveTab) => {
    setActiveRecipeDetail(null);
    setActiveTab(tab);
    safeScrollToTop();
  };

  const handleTriggerRecommend = () => {
    setActiveRecipeDetail(null);
    setActiveTab('recommendations');
    safeScrollToTop();
  };

  const handleOpenRecipeDetail = (
    recipeId: string,
    returnTab: ActiveTab,
    recommendationItem?: RecommendationItem
  ) => {
    setActiveRecipeDetail({
      recipeId,
      returnTab,
      recommendationItem,
    });
    safeScrollToTop();
  };

  const handleBackFromDetail = () => {
    const returnTab = activeRecipeDetail?.returnTab ?? activeTab;
    setActiveRecipeDetail(null);
    setActiveTab(returnTab);
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
