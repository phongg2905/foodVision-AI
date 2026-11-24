import React, { useEffect, useState } from 'react';
import { ChevronDown } from 'lucide-react';
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

interface StarterCombo {
  id: string;
  title: string;
  subtitle: string;
  slugs: string[];
}

const STUDIO_STARTER_COMBOS: StarterCombo[] = [
  {
    id: 'combo-tofu',
    title: 'Bữa chay thanh đạm',
    subtitle: 'Đậu hũ · Cà chua · Hành lá',
    slugs: ['dau-hu', 'ca-chua', 'hanh-la'],
  },
  {
    id: 'combo-egg-soup',
    title: 'Canh mây 15 phút',
    subtitle: 'Trứng gà · Cà chua · Hành lá',
    slugs: ['trung-ga', 'ca-chua', 'hanh-la'],
  },
  {
    id: 'combo-beef',
    title: 'Đổi vị giàu đạm',
    subtitle: 'Thịt bò · Hành tây · Tỏi',
    slugs: ['thit-bo', 'hanh-tay', 'toi'],
  },
];

type StudioAvailabilityTab = 'all' | 'ready' | 'missing';

export interface RecommendationResultsViewProps {
  selectedIngredients: Ingredient[];
  excludedPantryIds: string[];
  mainIngredientIds: string[];
  onMainIngredientIdsChange: (ids: string[]) => void;
  desiredMinutes: number | null;
  onDesiredMinutesChange: (minutes: number | null) => void;
  scanId?: string | null;
  onBackToKitchen: () => void;
  onSelectRecipe: (recipeId: string, item: RecommendationItem) => void;
  embeddedInStudio?: boolean;
  onApplyStarterSlugs?: (slugs: string[]) => void;
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
  scanId = null,
  onBackToKitchen,
  onSelectRecipe,
  embeddedInStudio = false,
  onApplyStarterSlugs,
}) => {
  const [cuisineCodes, setCuisineCodes] = useState<CuisineCode[]>([]);
  const [maxTotalMinutes, setMaxTotalMinutes] =
    useState<MaxDurationFilter>(null);
  const [includeMissing, setIncludeMissing] = useState(true);
  const [diversify, setDiversify] = useState(false);
  const [studioTab, setStudioTab] = useState<StudioAvailabilityTab>('all');

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
      include_missing: embeddedInStudio ? true : includeMissing,
      diversify,
      limit: 20,
      ...(scanId ? { scan_id: scanId } : {}),
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
    scanId,
    retryTick,
    embeddedInStudio,
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
    setStudioTab('all');
  };

  const readyItems = items.filter((item) => item.availability === 'ready');
  const missingItems = items.filter((item) => item.availability === 'missing');
  const mainSet = new Set(mainIngredientIds);

  if (selectedIngredients.length === 0) {
    return (
      <div
        data-testid="recommend-requires-ingredient"
        className="mx-auto max-w-3xl py-10 text-center"
      >
        <h2 className="font-serif text-[26px] font-bold text-[#181512]">
          Chọn nguyên liệu để mở thực đơn gợi ý
        </h2>

        <p className="mx-auto mt-2 max-w-[50ch] text-[14px] leading-relaxed text-[#4A4037]">
          Gõ tìm hoặc tích chọn nguyên liệu ở thanh tủ bếp phía trên, hệ thống
          sẽ tự động xếp hạng các món nấu được ngay và món còn thiếu.
        </p>

        {onApplyStarterSlugs ? (
          <div className="mt-7">
            <p className="text-[12.5px] font-medium text-[#595047]">
              Hoặc thử nhanh một giỏ nguyên liệu mẫu:
            </p>
            <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
              {STUDIO_STARTER_COMBOS.map((combo) => (
                <button
                  key={combo.id}
                  type="button"
                  data-testid={`starter-${combo.id}`}
                  onClick={() => onApplyStarterSlugs(combo.slugs)}
                  className="group flex flex-col items-start justify-between rounded-[16px] bg-[#FFF8F0] p-4 text-left shadow-[0_8px_22px_rgba(24,21,18,0.05)] transition hover:-translate-y-0.5 hover:shadow-[0_12px_28px_rgba(24,21,18,0.09)]"
                >
                  <div>
                    <span className="block font-serif text-[17px] font-bold text-[#181512] group-hover:text-[#B4490E]">
                      {combo.title}
                    </span>
                    <p className="mt-1 text-[12px] text-[#595047]">
                      {combo.subtitle}
                    </p>
                  </div>
                  <span className="mt-3 text-[12px] font-semibold text-[#B4490E]">
                    Thử giỏ này →
                  </span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <button
            type="button"
            onClick={onBackToKitchen}
            className="mt-6 inline-flex min-h-[40px] items-center rounded-full bg-[#B4490E] px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-[#963B0A]"
          >
            Mở Tủ bếp nguyên liệu
          </button>
        )}
      </div>
    );
  }

  /* =========================================================================
     CHẾ ĐỘ STUDIO (MOCKUP PHƯƠNG ÁN A): DẢI TAB CHỮ MẢNH + LƯỚI 4 CỘT ĐỒNG BỘ
     ========================================================================= */
  if (embeddedInStudio) {
    const displayedItems =
      studioTab === 'ready'
        ? readyItems
        : studioTab === 'missing'
          ? missingItems
          : items;

    const selectedCuisineSingle = cuisineCodes[0] ?? '';
    const hasStudioFilter =
      cuisineCodes.length > 0 ||
      maxTotalMinutes !== null ||
      diversify ||
      studioTab !== 'all';

    return (
      <div className="space-y-6">
        {/* Dải lọc chữ biên tập tối giản chuẩn Mockup A (không đóng hộp, không icon thừa) */}
        <div className="flex flex-col gap-3 border-b border-[#CDB9A2] pb-3 lg:flex-row lg:items-center lg:justify-between">
          {/* Trái: 3 Tab chữ gạch chân cam đất */}
          <div
            role="tablist"
            aria-label="Phân nhóm thực đơn gợi ý"
            className="flex flex-wrap items-center gap-x-6 gap-y-2"
          >
            <button
              type="button"
              role="tab"
              data-testid="studio-tab-all"
              aria-selected={studioTab === 'all'}
              onClick={() => setStudioTab('all')}
              className={`relative pb-1.5 text-[14px] tabular-nums transition lg:-mb-[13px] lg:pb-3 ${
                studioTab === 'all'
                  ? 'font-bold text-[#181512]'
                  : 'font-medium text-[#595047] hover:text-[#181512]'
              }`}
            >
              Tất cả ({items.length})
              {studioTab === 'all' && (
                <span className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full bg-[#B4490E]" />
              )}
            </button>

            <button
              type="button"
              role="tab"
              data-testid="studio-tab-ready"
              aria-selected={studioTab === 'ready'}
              onClick={() => setStudioTab('ready')}
              className={`relative pb-1.5 text-[14px] tabular-nums transition lg:-mb-[13px] lg:pb-3 ${
                studioTab === 'ready'
                  ? 'font-bold text-[#181512]'
                  : 'font-medium text-[#595047] hover:text-[#181512]'
              }`}
            >
              Nấu được ngay ({readyItems.length})
              {studioTab === 'ready' && (
                <span className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full bg-[#B4490E]" />
              )}
            </button>

            <button
              type="button"
              role="tab"
              data-testid="studio-tab-missing"
              aria-selected={studioTab === 'missing'}
              onClick={() => setStudioTab('missing')}
              className={`relative pb-1.5 text-[14px] tabular-nums transition lg:-mb-[13px] lg:pb-3 ${
                studioTab === 'missing'
                  ? 'font-bold text-[#181512]'
                  : 'font-medium text-[#595047] hover:text-[#181512]'
              }`}
            >
              Còn thiếu nguyên liệu ({missingItems.length})
              {studioTab === 'missing' && (
                <span className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full bg-[#B4490E]" />
              )}
            </button>
          </div>

          {/* Phải: Dropdown chữ mảnh Ẩm thực / Giới hạn / Đổi vị */}
          <div className="flex flex-wrap items-center gap-4 text-[13.5px]">
            <div className="relative inline-flex items-center">
              <select
                aria-label="Lọc theo nền ẩm thực"
                data-testid="studio-cuisine-select"
                value={selectedCuisineSingle}
                onChange={(e) => {
                  const val = e.target.value as CuisineCode | '';
                  setCuisineCodes(val ? [val] : []);
                }}
                className="min-h-[34px] cursor-pointer appearance-none bg-transparent pr-5 font-medium text-[#3B3027] focus:outline-none"
              >
                <option value="">Ẩm thực: Tất cả</option>
                <option value="VN">Ẩm thực: Món Việt</option>
                <option value="EU">Ẩm thực: Món Âu</option>
                <option value="US">Ẩm thực: Món Mỹ</option>
              </select>
              <ChevronDown
                className="pointer-events-none absolute right-0 h-3.5 w-3.5 text-[#595047]"
                aria-hidden="true"
              />
            </div>

            <div className="relative inline-flex items-center">
              <select
                aria-label="Thời gian nấu tối đa"
                data-testid="filter-max-minutes"
                value={maxTotalMinutes ?? ''}
                onChange={(e) =>
                  setMaxTotalMinutes(
                    e.target.value
                      ? (Number(e.target.value) as MaxDurationFilter)
                      : null
                  )
                }
                className="min-h-[34px] cursor-pointer appearance-none bg-transparent pr-5 font-medium text-[#3B3027] focus:outline-none"
              >
                <option value="">Giới hạn: Mọi mốc</option>
                <option value="15">Giới hạn: ≤ 15 phút</option>
                <option value="30">Giới hạn: ≤ 30 phút</option>
                <option value="60">Giới hạn: ≤ 60 phút</option>
              </select>
              <ChevronDown
                className="pointer-events-none absolute right-0 h-3.5 w-3.5 text-[#595047]"
                aria-hidden="true"
              />
            </div>

            <label
              data-testid="toggle-mmr-diversify"
              className={`inline-flex min-h-[34px] cursor-pointer items-center rounded-full px-3 py-1 text-[12.5px] font-medium transition select-none ${
                diversify
                  ? 'bg-[#181512] text-[#FFF8F0]'
                  : 'bg-[#EFE2D2]/80 text-[#4A4037] hover:bg-[#EFE2D2]'
              }`}
            >
              <input
                type="checkbox"
                aria-label="Đa dạng hóa thực đơn (MMR)"
                checked={diversify}
                onChange={(e) => setDiversify(e.target.checked)}
                className="sr-only"
              />
              <span>Đổi vị đa dạng</span>
            </label>

            {hasStudioFilter && (
              <button
                type="button"
                data-testid="reset-recommend-filters"
                onClick={handleResetFilters}
                className="text-[12.5px] font-semibold text-[#B4490E] hover:underline"
              >
                Đặt lại
              </button>
            )}
          </div>
        </div>

        {errorMessage && (
          <div
            role="alert"
            className="flex items-center justify-between gap-3 rounded-[14px] bg-[#FFF8F0] p-4 text-sm text-[#8F2D0A]"
          >
            <span>{errorMessage}</span>
            <button
              type="button"
              onClick={() => setRetryTick((n) => n + 1)}
              className="rounded-full bg-[#B4490E] px-4 py-1.5 text-xs font-semibold text-white"
            >
              Thử lại
            </button>
          </div>
        )}

        {isLoading ? (
          <div
            aria-label="Đang tính toán gợi ý món ăn"
            className="grid grid-cols-1 gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-4"
          >
            {Array.from({ length: 4 }).map((_, idx) => (
              <div key={idx} className="flex flex-col items-center pt-16">
                <div className="z-10 -mb-16 h-36 w-36 animate-pulse rounded-full bg-[#D6C3AE]" />
                <div className="h-56 w-full animate-pulse rounded-tl-[26px] rounded-br-[26px] rounded-tr-[6px] rounded-bl-[6px] bg-[#FFF8F0]" />
              </div>
            ))}
          </div>
        ) : displayedItems.length === 0 ? (
          <div
            data-testid="recommendations-empty-state"
            className="py-14 text-center"
          >
            <h2 className="font-serif text-xl font-bold text-[#181512]">
              Chưa có món ăn khớp bộ lọc hiện tại
            </h2>
            <p className="mx-auto mt-1.5 max-w-md text-sm text-[#4A4037]">
              Thử chuyển sang tab Tất cả hoặc nới rộng điều kiện ẩm thực và thời
              gian.
            </p>
            <button
              type="button"
              onClick={handleResetFilters}
              className="mt-5 inline-flex min-h-[38px] items-center rounded-full bg-[#B4490E] px-5 py-2 text-xs font-semibold text-white transition hover:bg-[#963B0A]"
            >
              Đặt lại bộ lọc
            </button>
          </div>
        ) : (
          /* LƯỚI 4 CỘT LIỀN MẠCH ĐỒNG BỘ 100% TRANG CHỦ CHUẨN MOCKUP A */
          <div
            data-testid="recommend-studio-grid"
            className="grid grid-cols-1 gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-4"
          >
            {displayedItems.map((item) => (
              <RecommendationCard
                key={item.recipe.id}
                item={item}
                knownIngredients={selectedIngredients}
                onSelectRecipe={onSelectRecipe}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  /* =========================================================================
     CHẾ ĐỘ ĐỘC LẬP (GIỮ TƯƠNG THÍCH 100% VỚI BÀI TEST ĐƠN VỊ TC-09..TC-35)
     ========================================================================= */
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="font-serif text-3xl font-bold leading-tight tracking-tight text-[#181512] sm:text-4xl">
            Gợi Ý Món Ăn Cho Bữa Hôm Nay
          </h1>
          <p className="mt-1 max-w-[65ch] text-sm leading-relaxed text-[#4A4037]">
            Xếp hạng theo độ phủ nguyên liệu, ưu tiên món chính và thời gian
            mong muốn.
          </p>
        </div>

        <button
          type="button"
          data-testid="back-to-kitchen-btn"
          onClick={onBackToKitchen}
          className="inline-flex min-h-[38px] shrink-0 items-center justify-center self-start rounded-full bg-[#FFF8F0] px-4 py-1.5 text-[12.5px] font-semibold text-[#B4490E] transition hover:text-[#181512] sm:self-auto"
        >
          ← Chỉnh lại nguyên liệu &amp; gia vị
        </button>
      </div>

      <section
        aria-label="Tinh chỉnh nguyên liệu chính và thời gian mong muốn"
        className="rounded-[18px] bg-[#FFF8F0] px-5 py-4 shadow-[0_8px_22px_rgba(24,21,18,0.05)]"
      >
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-12 lg:items-center">
          <div className="lg:col-span-6">
            <p className="text-[12.5px] font-semibold text-[#181512]">
              Nguyên liệu đang có (bấm ★ để ưu tiên món chính):
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {selectedIngredients.map((item) => {
                const isMain = mainSet.has(item.id);
                return (
                  <button
                    key={item.id}
                    type="button"
                    data-testid={`quick-main-${item.slug}`}
                    aria-pressed={isMain}
                    onClick={() => handleToggleMain(item.id)}
                    className={`inline-flex min-h-[34px] items-center gap-1 rounded-full px-3.5 py-1 text-[12.5px] transition ${
                      isMain
                        ? 'bg-[#F4DEC9] font-semibold text-[#9E3D08]'
                        : 'bg-[#EFE2D2] font-medium text-[#181512]'
                    }`}
                  >
                    <span>{isMain ? '★' : '☆'}</span>
                    <span>{item.name_vi}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="border-t border-[#E4D5C3] pt-3 lg:col-span-6 lg:border-l lg:border-t-0 lg:pl-5 lg:pt-0">
            <p className="mb-2 text-[12.5px] font-semibold text-[#181512]">
              Ưu tiên thời gian nấu:
            </p>
            <DesiredTimeSelector
              desiredMinutes={desiredMinutes}
              onDesiredMinutesChange={onDesiredMinutesChange}
              testIdPrefix="quick-desired-time"
              activeTone="espresso"
            />
          </div>
        </div>
      </section>

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

      {items.length === 0 && !isLoading ? (
        <div
          data-testid="recommendations-empty-state"
          className="py-12 text-center"
        >
          <h2 className="font-serif text-xl font-bold text-[#181512]">
            Chưa có công thức khớp điều kiện lọc hiện tại
          </h2>
          <button
            type="button"
            onClick={handleResetFilters}
            className="mt-4 inline-flex min-h-[38px] items-center rounded-full bg-[#B4490E] px-5 py-2 text-xs font-semibold text-white"
          >
            Đặt lại bộ lọc
          </button>
        </div>
      ) : (
        <div className="space-y-8">
          <section
            data-testid="recommend-ready-section"
            aria-label="Món nấu được ngay"
          >
            <h2 className="mb-4 font-serif text-[22px] font-bold text-[#181512]">
              Nấu được ngay ({readyItems.length})
            </h2>
            {readyItems.length > 0 ? (
              <div className="grid grid-cols-1 gap-x-6 gap-y-8 sm:grid-cols-2 lg:grid-cols-4">
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
                className="text-sm text-[#595047]"
              >
                Chưa có món đủ 100% nguyên liệu.
              </p>
            )}
          </section>

          {includeMissing && missingItems.length > 0 && (
            <section
              data-testid="recommend-missing-section"
              aria-label="Món còn thiếu nguyên liệu"
              className="border-t border-[#CDB9A2] pt-6"
            >
              <h2 className="mb-4 font-serif text-[22px] font-bold text-[#181512]">
                Còn thiếu nguyên liệu ({missingItems.length})
              </h2>
              <div className="grid grid-cols-1 gap-x-6 gap-y-8 sm:grid-cols-2 lg:grid-cols-4">
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
