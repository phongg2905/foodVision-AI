import React, { useEffect, useState } from 'react';
import { SearchX, RotateCcw } from 'lucide-react';
import {
  CuisineCode,
  MaxDurationFilter,
  RecipeSummary,
} from '../../shared/api/types';
import { listRecipes } from '../../shared/api/recipesApi';
import { RecipeFilterBar } from './components/RecipeFilterBar';
import { RecipeCard } from './components/RecipeCard';
import { RecipePagination } from './components/RecipePagination';

export interface RecipeCatalogViewProps {
  pageSize?: number;
  onSelectRecipe?: (recipeId: string) => void;
}

export const RecipeCatalogView: React.FC<RecipeCatalogViewProps> = ({
  pageSize = 8,
  onSelectRecipe,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [selectedCuisine, setSelectedCuisine] = useState<CuisineCode | null>(
    null
  );
  const [selectedMaxMinutes, setSelectedMaxMinutes] =
    useState<MaxDurationFilter>(null);
  const [offset, setOffset] = useState(0);

  const [recipes, setRecipes] = useState<RecipeSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedQuery(searchQuery);
      setOffset(0);
    }, 200);
    return () => window.clearTimeout(timer);
  }, [searchQuery]);

  useEffect(() => {
    let isCancelled = false;
    setIsLoading(true);
    setErrorMessage(null);

    listRecipes({
      q: debouncedQuery,
      cuisine_code: selectedCuisine,
      max_total_minutes: selectedMaxMinutes,
      limit: pageSize,
      offset,
    })
      .then((response) => {
        if (isCancelled) return;
        setRecipes(response.items);
        setTotal(response.total);
      })
      .catch((err: unknown) => {
        if (isCancelled) return;
        setErrorMessage(
          err instanceof Error
            ? err.message
            : 'Không thể tải danh sách công thức món ăn.'
        );
      })
      .finally(() => {
        if (!isCancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [debouncedQuery, selectedCuisine, selectedMaxMinutes, pageSize, offset]);

  const handleCuisineChange = (cuisine: CuisineCode | null) => {
    setSelectedCuisine(cuisine);
    setOffset(0);
  };

  const handleMaxMinutesChange = (minutes: MaxDurationFilter) => {
    setSelectedMaxMinutes(minutes);
    setOffset(0);
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setDebouncedQuery('');
    setSelectedCuisine(null);
    setSelectedMaxMinutes(null);
    setOffset(0);
  };

  return (
    <div className="space-y-6">
      <RecipeFilterBar
        searchQuery={searchQuery}
        onSearchQueryChange={setSearchQuery}
        selectedCuisine={selectedCuisine}
        onCuisineChange={handleCuisineChange}
        selectedMaxMinutes={selectedMaxMinutes}
        onMaxMinutesChange={handleMaxMinutesChange}
        onResetFilters={handleResetFilters}
        totalCount={total}
      />

      {errorMessage && (
        <div
          role="alert"
          className="rounded-tl-[18px] rounded-br-[18px] rounded-tr-[6px] rounded-bl-[6px] border border-[#D48A6A] bg-[#FFF8F0] p-4 text-sm text-[#8F2D0A]"
        >
          {errorMessage}
        </div>
      )}

      {isLoading ? (
        <div
          aria-label="Đang tải danh sách công thức"
          className="grid grid-cols-1 gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-4"
        >
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="flex flex-col items-center pt-14">
              <div className="z-10 -mb-14 h-32 w-32 animate-pulse rounded-full bg-[#D6C3AE]" />
              <div className="h-52 w-full animate-pulse rounded-tl-[28px] rounded-br-[28px] rounded-tr-[6px] rounded-bl-[6px] bg-[#FFF8F0] shadow-sm" />
            </div>
          ))}
        </div>
      ) : recipes.length === 0 ? (
        <div
          data-testid="recipes-empty-state"
          className="flex flex-col items-center justify-center rounded-tl-[28px] rounded-br-[28px] rounded-tr-[6px] rounded-bl-[6px] border border-[#D8C6B2] bg-[#FFF8F0] px-6 py-14 text-center shadow-[0_8px_24px_rgba(24,21,18,0.05)]"
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#F4EAE0] text-[#9E3D08]">
            <SearchX className="h-6 w-6" aria-hidden="true" />
          </div>
          <h3 className="mt-4 font-serif text-lg font-bold text-[#181512]">
            Không tìm thấy công thức phù hợp
          </h3>
          <p className="mt-1 max-w-md text-sm text-[#595047]">
            Thử tìm kiếm với từ khóa khác hoặc mở rộng bộ lọc nền ẩm thực và
            thời gian chế biến.
          </p>
          <button
            type="button"
            onClick={handleResetFilters}
            className="mt-5 inline-flex items-center gap-2 rounded-tl-[14px] rounded-br-[14px] rounded-tr-[4px] rounded-bl-[4px] bg-[#C65112] px-6 py-2.5 text-xs font-semibold text-white transition hover:bg-[#A8430D]"
          >
            <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
            Xóa bộ lọc
          </button>
        </div>
      ) : (
        <>
          {/* Lưới 4 cột chuẩn "Our Special Recipes" của web-6-newtaste-recipe-website.jpg */}
          <div
            data-testid="recipe-catalog-grid"
            className="grid grid-cols-1 gap-x-6 gap-y-8 sm:grid-cols-2 lg:grid-cols-4"
          >
            {recipes.map((recipe) => (
              <RecipeCard
                key={recipe.id}
                recipe={recipe}
                onSelectRecipe={onSelectRecipe}
              />
            ))}
          </div>

          <RecipePagination
            total={total}
            limit={pageSize}
            offset={offset}
            onOffsetChange={setOffset}
          />
        </>
      )}
    </div>
  );
};
