import React, { useState } from 'react';
import { Ingredient } from './shared/api/types';
import { ActiveTab, AppLayout } from './shared/components/AppLayout';
import { RecipeCatalogView } from './features/recipes/RecipeCatalogView';
import { IngredientKitchenView } from './features/search/IngredientKitchenView';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('catalog');
  const [selectedIngredients, setSelectedIngredients] = useState<Ingredient[]>(
    []
  );
  // Mặc định cả 5 gia vị sẵn có trong bếp đều được bật -> excludedPantryIds = [] (FR-05, ADR-008)
  const [excludedPantryIds, setExcludedPantryIds] = useState<string[]>([]);

  return (
    <AppLayout
      activeTab={activeTab}
      onTabChange={setActiveTab}
      selectedMainCount={selectedIngredients.length}
    >
      {activeTab === 'catalog' ? (
        <RecipeCatalogView />
      ) : (
        <IngredientKitchenView
          selectedIngredients={selectedIngredients}
          onSelectedIngredientsChange={setSelectedIngredients}
          excludedPantryIds={excludedPantryIds}
          onExcludedPantryIdsChange={setExcludedPantryIds}
        />
      )}
    </AppLayout>
  );
};

export default App;
