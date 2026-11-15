import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  ArrowLeft,
  Clock,
  RotateCcw,
  SearchX,
  Star,
  UtensilsCrossed,
} from 'lucide-react';
import { postRecommendations } from '../../shared/api/recommendationsApi';
import {
  CuisineCode,
  Ingredient,
  MaxDurationFilter,
  RecommendationItem,
} from '../../shared/api/types';
import { RecommendationCard } from './components/RecommendationCard';
import { RecommendationFilterBar } from './components/RecommendationFilterBar';
import { DesiredTimeSelector } from '../../shared/components/DesiredTimeSelector';

export interface RecommendationResultsViewProps {
  selectedIngredients: Ingredient[];
  excludedPantryIds: string[];
  mainIngredientIds: string[];
  onMainIngredientIdsChange: (ids: string[]) => void;
  desiredMinutes: number | null;
  onDesiredMinutesChange: (minutes: number | null) => void;
  onBackToKitchen: () => void;
  onSelectRecipe: (recipeId: string, item: RecommendationItem) => void;
}

export const RecommendationResultsView: React.FC<
  RecommendationResultsViewProps
> = ({
  selectedIngredients,
  excludedPantryIds,
  mainIngredientIds,
  onMainIngredientIdsChange,
  desiredMinutes,
  onDesiredMinutesChange,
  onBackToKitchen,
  onSelectRecipe,
}) => {
  const [cuisineCodes, setCuisineCodes] = useState<CuisineCode[]>([]);
  const [maxTotalMinutes, setMaxTotalMinutes] =
    useState<MaxDurationFilter>(null);
  const [includeMissing, setIncludeMissing] = useState(true);
  const [diversify, setDiversify] = useState(false);

  const [items, setItems] = useState<RecommendationItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [retryTick, setRetryTick] = useState(0);

  const ingredientIdsKey = selectedIngredients.map((item) => item.id).join(',');
  const mainIdsKey = mainIngredientIds.join(',');
  const pantryIdsKey = excludedPantryIds.join(',');
  const cuisineKey = cuisineCodes.join(',');

  useEffect(() => {
    if (selectedIngredients.length === 0) {
      setItems([]);
      setErrorMessage(null);
      setIsLoading(false);
      return;
    }

    let isCancelled = false;
    setIsLoading(true);
    setErrorMessage(null);

    const desiredHours =
      typeof desiredMinutes === 'number' && desiredMinutes > 0
        ? Math.round((desiredMinutes / 60) * 10000) / 10000
        : 100.0;

    postRecommendations({
      ingredient_ids: selectedIngredients.map((item) => item.id),
      main_ingredient_ids: mainIngredientIds,
      desired_hours: desiredHours,
      excluded_pantry_ids: excludedPantryIds,
      cuisine_codes: cuisineCodes,
      max_total_minutes: maxTotalMinutes,
      include_missing: includeMissing,
      diversify,
      limit: 20,
    })
      .then((res) => {
        if (!isCancelled) {
          setItems(res.items);
        }
      })
      .catch((err: unknown) => {
        if (!isCancelled) {
          setErrorMessage(
            err instanceof Error
              ? err.message
              : 'Không thể tải danh sách gợi ý món ăn.'
          );
        }
      })
      .finally(() => {
        if (!isCancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [
    ingredientIdsKey,
    mainIdsKey,
    pantryIdsKey,
    desiredMinutes,
    cuisineKey,
    maxTotalMinutes,
    includeMissing,
    diversify,
    retryTick,
    selectedIngredients,
    mainIngredientIds,
    excludedPantryIds,
    cuisineCodes,
  ]);

  const handleToggleMain = (ingredientId: string) => {
    if (mainIngredientIds.includes(ingredientId)) {
      onMainIngredientIdsChange(
        mainIngredientIds.filter((id) => id !== ingredientId)
      );
    } else {
      onMainIngredientIdsChange([...mainIngredientIds, ingredientId]);
    }
  };

  const handleResetFilters = () => {
    setCuisineCodes([]);
    setMaxTotalMinutes(null);
    setIncludeMissing(true);
    setDiversify(false);
  };

  const readyItems = items.filter((item) => item.availability === 'ready');
  const missingItems = items.filter((item) => item.availability === 'missing');
  const mainSet = new Set(mainIngredientIds);

  if (selectedIngredients.length === 0) {
    return (
      <div className="space-y-6 py-6">
        <div className="text-center">
          <h1 className="font-serif text-3xl font-bold tracking-tight text-[#181512] sm:text-4xl">
            Gợi Ý Món Ăn Thông Minh
          </h1>
          <p className="mx-auto mt-2 max-w-lg text-sm text-[#6E655C]">
            Hãy chọn ít nhất 1 nguyên liệu chính trong Tủ bếp để nhận danh sách
            món ăn phù hợp nhất với gian bếp của bạn.
          </p>
        </div>

        <div
          data-testid="recommend-requires-ingredient"
          className="mx-auto flex max-w-xl flex-col items-center rounded-bl-[16px] rounded-br-[30px] rounded-tl-[30px] rounded-tr-[16px] border border-[#DFD3C3] bg-white px-6 py-12 text-center shadow-[0_14px_40px_rgba(24,21,18,0.05)]"
        >
          <span className="flex h-14 w-14 items-center justify-center rounded-full bg-[#FDF0E7] text-[#E87838]">
            <UtensilsCrossed className="h-6 w-6" aria-hidden="true" />
          </span>
          <h2 className="mt-4 font-serif text-xl font-bold text-[#181512]">
            Chưa có nguyên liệu nào được chọn
          </h2>
          <p className="mt-2 max-w-md text-sm text-[#6E655C]">
            Quay lại Tủ bếp để chọn nhanh thịt, cá, trứng, rau củ sẵn có; hệ
            thống sẽ tự động phân nhóm món nấu được ngay và món còn thiếu.
          </p>
          <button
            type="button"
            onClick={onBackToKitchen}
            className="mt-6 inline-flex items-center gap-2 rounded-full bg-[#E87838] px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-[#D16426]"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            <span>Mở Tủ bếp nguyên liệu</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-7">
      {/* Đầu trang: Quay lại & Tiêu đề */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <button
            type="button"
            data-testid="back-to-kitchen-btn"
            onClick={onBackToKitchen}
            className="inline-flex items-center gap-1.5 rounded-full border border-[#DFD3C3] bg-white px-4 py-1.5 text-[12px] font-semibold text-[#181512] transition hover:border-[#E87838] hover:text-[#C2591B]"
          >
            <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Chỉnh lại nguyên liệu &amp; gia vị</span>
          </button>

          <h1 className="mt-3 font-serif text-3xl font-bold tracking-tight text-[#181512] sm:text-4xl">
            Gợi Ý Món Ăn Cho Bữa Hôm Nay
          </h1>
          <p className="mt-1.5 max-w-2xl text-xs leading-relaxed text-[#6E655C] sm:text-sm">
            Xếp hạng dựa trên độ phủ nguyên liệu, ưu tiên món chính và thời gian
            mong muốn của bạn.
          </p>
        </div>
      </div>

      {/* Bảng Tinh chỉnh Nhanh: Nguyên liệu chính ưu tiên & Thời gian mong muốn */}
      <section
        aria-label="Tinh chỉnh nguyên liệu chính và thời gian mong muốn"
        className="rounded-bl-[16px] rounded-br-[28px] rounded-tl-[28px] rounded-tr-[16px] border border-[#DFD3C3] bg-white p-5 shadow-[0_10px_28px_rgba(24,21,18,0.05)]"
      >
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-12 lg:items-center">
          <div className="lg:col-span-7">
            <p className="text-[12px] font-bold text-[#181512]">
              Nguyên liệu đang có (bấm ★ để ưu tiên làm món chính):
            </p>
            <div className="mt-2.5 flex flex-wrap gap-2">
              {selectedIngredients.map((item) => {
                const isMain = mainSet.has(item.id);
                return (
                  <button
                    key={item.id}
                    type="button"
                    data-testid={`quick-main-${item.slug}`}
                    aria-pressed={isMain}
                    onClick={() => handleToggleMain(item.id)}
                    className={`inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[12px] font-semibold transition ${
                      isMain
                        ? 'bg-[#E87838] text-white shadow-sm'
                        : 'border border-[#DFD3C3] bg-[#FAF7F2] text-[#2E2620] hover:border-[#E87838]'
                    }`}
                  >
                    <Star
                      className={`h-3.5 w-3.5 ${
                        isMain ? 'fill-white text-white' : 'text-[#C2591B]'
                      }`}
                      aria-hidden="true"
                    />
                    <span>{item.name_vi}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="border-t border-[#EFE8DF] pt-4 lg:col-span-5 lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0">
            <div className="flex items-center justify-between gap-2">
              <span className="inline-flex items-center gap-1.5 text-[12px] font-bold text-[#181512]">
                <Clock
                  className="h-3.5 w-3.5 text-[#E87838]"
                  aria-hidden="true"
                />
                <span>Thời gian mong muốn:</span>
              </span>
              <span className="text-[11px] font-medium text-[#6E655C] tabular-nums">
                {desiredMinutes ? `${desiredMinutes} phút` : 'Mặc định (linh hoạt)'}
              </span>
            </div>

            <div className="mt-2.5">
              <DesiredTimeSelector
                desiredMinutes={desiredMinutes}
                onDesiredMinutesChange={onDesiredMinutesChange}
                testIdPrefix="quick-desired-time"
                activeTone="espresso"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Thanh Bộ lọc Kết quả */}
      <RecommendationFilterBar
        cuisineCodes={cuisineCodes}
        onCuisineCodesChange={setCuisineCodes}
        maxTotalMinutes={maxTotalMinutes}
        onMaxTotalMinutesChange={setMaxTotalMinutes}
        includeMissing={includeMissing}
        onIncludeMissingChange={setIncludeMissing}
        diversify={diversify}
        onDiversifyChange={setDiversify}
        onResetFilters={handleResetFilters}
        totalCount={items.length}
        readyCount={readyItems.length}
        missingCount={missingItems.length}
      />

      {/* Lỗi API */}
      {errorMessage && (
        <div
          role="alert"
          className="flex flex-col items-start justify-between gap-3 rounded-2xl border border-[#F2C7A8] bg-[#FDF0E7] p-4 text-sm text-[#9A3D0E] sm:flex-row sm:items-center"
        >
          <div className="flex items-center gap-2.5">
            <AlertCircle className="h-5 w-5 shrink-0" aria-hidden="true" />
            <span>{errorMessage}</span>
          </div>
          <button
            type="button"
            onClick={() => setRetryTick((n) => n + 1)}
            className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-[#E87838] px-4 py-1.5 text-xs font-semibold text-white transition hover:bg-[#D16426]"
          >
            <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Thử lại</span>
          </button>
        </div>
      )}

      {/* Trạng thái Loading */}
      {isLoading ? (
        <div
          aria-label="Đang tính toán gợi ý món ăn"
          className="grid grid-cols-1 gap-x-6 gap-y-10 md:grid-cols-2 xl:grid-cols-3"
        >
          {Array.from({ length: 3 }).map((_, idx) => (
            <div key={idx} className="flex flex-col items-center pt-14">
              <div className="z-10 -mb-14 h-32 w-32 animate-pulse rounded-full bg-[#DFD3C3]" />
              <div className="h-72 w-full animate-pulse rounded-bl-[14px] rounded-br-[30px] rounded-tl-[30px] rounded-tr-[14px] bg-white shadow-sm" />
            </div>
          ))}
        </div>
      ) : items.length === 0 ? (
        <div
          data-testid="recommendations-empty-state"
          className="flex flex-col items-center justify-center rounded-bl-[16px] rounded-br-[30px] rounded-tl-[30px] rounded-tr-[16px] border border-[#DFD3C3] bg-white px-6 py-14 text-center shadow-[0_10px_28px_rgba(24,21,18,0.05)]"
        >
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-[#FAF7F2] text-[#E87838]">
            <SearchX className="h-6 w-6" aria-hidden="true" />
          </span>
          <h2 className="mt-4 font-serif text-xl font-bold text-[#181512]">
            Chưa có công thức phù hợp với điều kiện hiện tại
          </h2>
          <p className="mt-1.5 max-w-md text-sm text-[#6E655C]">
            Không có món nào khớp bộ lọc hoặc bạn đang bật chế độ chỉ hiện món
            nấu được ngay. Hãy đặt lại bộ lọc hoặc bổ sung thêm nguyên liệu.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <button
              type="button"
              onClick={handleResetFilters}
              className="inline-flex items-center gap-2 rounded-full bg-[#E87838] px-5 py-2.5 text-xs font-semibold text-white transition hover:bg-[#D16426]"
            >
              <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
              <span>Đặt lại bộ lọc</span>
            </button>
            <button
              type="button"
              onClick={onBackToKitchen}
              className="inline-flex items-center gap-2 rounded-full border border-[#DFD3C3] bg-[#FAF7F2] px-5 py-2.5 text-xs font-semibold text-[#181512] transition hover:border-[#181512]"
            >
              <span>Thêm nguyên liệu khác</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-10">
          {/* KHU VỰC 1: NẤU ĐƯỢC NGAY (`ready`) */}
          <section
            data-testid="recommend-ready-section"
            aria-label="Món nấu được ngay"
          >
            <div className="mb-5 flex flex-wrap items-center justify-between gap-2 border-b border-[#DFD3C3] pb-3">
              <div className="flex items-center gap-2.5">
                <h2 className="font-serif text-2xl font-bold text-[#181512]">
                  Nấu được ngay
                </h2>
                <span className="inline-flex h-7 min-w-[28px] items-center justify-center rounded-full bg-[#E7F8F2] px-2.5 text-xs font-bold text-[#157358] tabular-nums">
                  {readyItems.length}
                </span>
              </div>
              <p className="text-xs text-[#574D44]">
                Đủ toàn bộ nguyên liệu chính &amp; gia vị bắt buộc
              </p>
            </div>

            {readyItems.length > 0 ? (
              <div className="grid grid-cols-1 gap-x-6 gap-y-8 md:grid-cols-2 xl:grid-cols-3">
                {readyItems.map((item) => (
                  <RecommendationCard
                    key={item.recipe.id}
                    item={item}
                    knownIngredients={selectedIngredients}
                    onSelectRecipe={onSelectRecipe}
                  />
                ))}
              </div>
            ) : (
              <p
                data-testid="ready-section-empty-note"
                className="rounded-2xl border border-dashed border-[#DFD3C3] bg-white px-5 py-5 text-center text-sm text-[#6E655C]"
              >
                Hiện chưa có công thức nào đủ 100% nguyên liệu; hãy tham khảo các
                món chỉ còn thiếu ít nguyên liệu bên dưới.
              </p>
            )}
          </section>

          {/* KHU VỰC 2: CÒN THIẾU NGUYÊN LIỆU (`missing`) */}
          {includeMissing && missingItems.length > 0 && (
            <section
              data-testid="recommend-missing-section"
              aria-label="Món còn thiếu nguyên liệu"
            >
              <div className="mb-5 flex flex-wrap items-center justify-between gap-2 border-b border-[#DFD3C3] pb-3">
                <div className="flex items-center gap-2.5">
                  <h2 className="font-serif text-2xl font-bold text-[#181512]">
                    Còn thiếu nguyên liệu
                  </h2>
                  <span className="inline-flex h-7 min-w-[28px] items-center justify-center rounded-full bg-[#FDF0E7] px-2.5 text-xs font-bold text-[#C2591B] tabular-nums">
                    {missingItems.length}
                  </span>
                </div>
                <p className="text-xs text-[#574D44]">
                  Đã liệt kê rõ nguyên liệu hoặc gia vị cần mua thêm
                </p>
              </div>

              <div className="grid grid-cols-1 gap-x-6 gap-y-8 md:grid-cols-2 xl:grid-cols-3">
                {missingItems.map((item) => (
                  <RecommendationCard
                    key={item.recipe.id}
                    item={item}
                    knownIngredients={selectedIngredients}
                    onSelectRecipe={onSelectRecipe}
                  />
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
};
