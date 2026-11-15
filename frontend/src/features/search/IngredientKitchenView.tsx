import React, { useEffect, useState } from 'react';
import { Check, CheckCircle2, Clock } from 'lucide-react';
import { Ingredient, RecommendDraftPayload } from '../../shared/api/types';
import {
  listPantryIngredients,
  searchMainIngredients,
} from '../../shared/api/ingredientsApi';
import {
  MOCK_MAIN_INGREDIENTS,
  MOCK_PANTRY_INGREDIENTS,
} from '../../shared/api/mockData';
import { matchesIngredientQuery } from '../../shared/utils/vietnamese';
import { IngredientSearchBox } from './components/IngredientSearchBox';
import { SelectedIngredientsList } from './components/SelectedIngredientsList';
import { PantryToggleBar } from './components/PantryToggleBar';
import { DesiredTimeSelector } from '../../shared/components/DesiredTimeSelector';

export interface IngredientKitchenViewProps {
  selectedIngredients: Ingredient[];
  onSelectedIngredientsChange: (ingredients: Ingredient[]) => void;
  excludedPantryIds: string[];
  onExcludedPantryIdsChange: (ids: string[]) => void;
  mainIngredientIds?: string[];
  onMainIngredientIdsChange?: (ids: string[]) => void;
  desiredMinutes?: number | null;
  onDesiredMinutesChange?: (minutes: number | null) => void;
  onTriggerRecommend?: (payload: RecommendDraftPayload) => void;
}

interface CulinaryGroupConfig {
  id: string;
  title: string;
  slugs: string[];
}

const DEFAULT_VISIBLE_LIMIT = 6;

/**
 * Phân loại 6 nhóm nguyên liệu chuẩn thói quen mở tủ lạnh & nấu bữa cơm Việt:
 * Mỗi nhóm ưu tiên xếp 6 nguyên liệu thông dụng nhất lên đầu; phần còn lại tự động thu gọn vào nút "+X xem thêm".
 */
const CULINARY_GROUPS: CulinaryGroupConfig[] = [
  {
    id: 'meat-poultry',
    title: 'Thịt & Gia cầm',
    slugs: [
      'thit-heo',
      'thit-ba-chi',
      'suon-heo',
      'thit-bo',
      'uc-ga',
      'thit-ga-ta',
      'thit-bam',
      'thit-vit',
      'cha-lua',
    ],
  },
  {
    id: 'seafood',
    title: 'Tôm, Cá & Hải sản',
    slugs: [
      'tom-tuoi',
      'ca-hoi',
      'ca-basa',
      'muc-tuoi',
      'ngheu-tuoi',
      'cua-bien',
      'ca-thu',
      'cha-ca',
      'oc-buou',
    ],
  },
  {
    id: 'eggs-tofu',
    title: 'Trứng & Đậu',
    slugs: [
      'dau-hu',
      'trung-ga',
      'trung-cut',
      'trung-vit',
      'dau-hu-non',
      'tau-hu-ky',
      'trung-muoi',
    ],
  },
  {
    id: 'leafy-greens',
    title: 'Rau xanh & Các loại cải',
    slugs: [
      'rau-muong',
      'cai-thia',
      'bap-cai',
      'bong-cai-xanh',
      'xa-lach',
      'rau-ngot',
      'cai-ngot',
      'rau-mong-toi',
    ],
  },
  {
    id: 'roots-fruits-mushrooms',
    title: 'Củ, Quả & Nấm',
    slugs: [
      'ca-chua',
      'ca-rot',
      'khoai-tay',
      'dua-leo',
      'bap',
      'hanh-tay',
      'thom',
      'nam-huong',
      'nam-kim-cham',
    ],
  },
  {
    id: 'aromatics-herbs',
    title: 'Hành, Tỏi & Rau thơm',
    slugs: [
      'hanh-la',
      'hanh-tim',
      'toi',
      'gung',
      'sa-cay',
      'ot-sung',
      'ngo-ri',
      'la-chanh',
      'rau-ram',
    ],
  },
];

export const IngredientKitchenView: React.FC<IngredientKitchenViewProps> = ({
  selectedIngredients,
  onSelectedIngredientsChange,
  excludedPantryIds,
  onExcludedPantryIdsChange,
  mainIngredientIds: controlledMainIds,
  onMainIngredientIdsChange,
  desiredMinutes: controlledDesiredMinutes,
  onDesiredMinutesChange,
  onTriggerRecommend,
}) => {
  const [catalogIngredients, setCatalogIngredients] = useState<Ingredient[]>(
    MOCK_MAIN_INGREDIENTS
  );
  const [pantryItems, setPantryItems] = useState<Ingredient[]>(
    MOCK_PANTRY_INGREDIENTS
  );
  const [internalMainIds, setInternalMainIds] = useState<string[]>([]);
  const [internalDesiredMinutes, setInternalDesiredMinutes] = useState<
    number | null
  >(null);
  const [isSearching, setIsSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>(
    {}
  );
  const [submittedPayload, setSubmittedPayload] =
    useState<RecommendDraftPayload | null>(null);

  const activeMainIds = controlledMainIds ?? internalMainIds;
  const setActiveMainIds = (nextIds: string[]) => {
    if (onMainIngredientIdsChange) {
      onMainIngredientIdsChange(nextIds);
    } else {
      setInternalMainIds(nextIds);
    }
  };

  const activeDesiredMinutes =
    controlledDesiredMinutes !== undefined
      ? controlledDesiredMinutes
      : internalDesiredMinutes;
  const setActiveDesiredMinutes = (minutes: number | null) => {
    if (onDesiredMinutesChange) {
      onDesiredMinutesChange(minutes);
    } else {
      setInternalDesiredMinutes(minutes);
    }
  };

  const selectedIdSet = new Set(selectedIngredients.map((item) => item.id));
  const ingredientBySlug = new Map(
    catalogIngredients.map((item) => [item.slug, item])
  );

  useEffect(() => {
    let isCancelled = false;

    listPantryIngredients()
      .then((res) => {
        if (!isCancelled && res.items.length > 0) {
          setPantryItems(res.items);
        }
      })
      .catch(() => {
        // Fallback giữ nguyên 5 gia vị chuẩn trong MOCK_PANTRY_INGREDIENTS
      });

    // Đồng bộ UUID thực từ Backend (nếu Backend đang chạy) để khớp catalog live
    searchMainIngredients('', 50, 0)
      .then((res) => {
        if (isCancelled || res.items.length === 0) return;
        const liveBySlug = new Map(
          res.items.map((item) => [item.slug, item] as const)
        );
        setCatalogIngredients((prev) => {
          const merged = prev.map((item) => liveBySlug.get(item.slug) ?? item);
          const knownSlugs = new Set(merged.map((item) => item.slug));
          for (const liveItem of res.items) {
            if (!knownSlugs.has(liveItem.slug)) {
              merged.push(liveItem);
            }
          }
          return merged;
        });
      })
      .catch(() => {
        // Giữ nguyên bộ từ điển offline khi Backend chưa khởi chạy
      });

    return () => {
      isCancelled = true;
    };
  }, []);

  const handleAddIngredient = (candidate: Ingredient) => {
    if (selectedIngredients.some((item) => item.id === candidate.id)) {
      return;
    }
    onSelectedIngredientsChange([...selectedIngredients, candidate]);
    setSubmittedPayload(null);
  };

  const handleRemoveIngredient = (ingredientId: string) => {
    onSelectedIngredientsChange(
      selectedIngredients.filter((item) => item.id !== ingredientId)
    );
    if (activeMainIds.includes(ingredientId)) {
      setActiveMainIds(activeMainIds.filter((id) => id !== ingredientId));
    }
    setSubmittedPayload(null);
  };

  const handleToggleIngredient = (candidate: Ingredient) => {
    if (selectedIdSet.has(candidate.id)) {
      handleRemoveIngredient(candidate.id);
    } else {
      handleAddIngredient(candidate);
    }
  };

  const handleClearAllIngredients = () => {
    onSelectedIngredientsChange([]);
    setActiveMainIds([]);
    setSubmittedPayload(null);
  };

  const handleToggleMainIngredient = (ingredientId: string) => {
    const exists = activeMainIds.includes(ingredientId);
    const updated = exists
      ? activeMainIds.filter((id) => id !== ingredientId)
      : [...activeMainIds, ingredientId];
    setActiveMainIds(updated);
    setSubmittedPayload(null);
  };

  const handleTogglePantryItem = (pantryId: string) => {
    const exists = excludedPantryIds.includes(pantryId);
    const updated = exists
      ? excludedPantryIds.filter((id) => id !== pantryId)
      : [...excludedPantryIds, pantryId];
    onExcludedPantryIdsChange(updated);
    setSubmittedPayload(null);
  };

  const handleResetPantryDefault = () => {
    onExcludedPantryIdsChange([]);
    setSubmittedPayload(null);
  };

  const toggleGroupExpand = (groupId: string) => {
    setExpandedGroups((prev) => ({
      ...prev,
      [groupId]: !prev[groupId],
    }));
  };

  const canRecommend = selectedIngredients.length > 0;
  const validMainIds = activeMainIds.filter((id) => selectedIdSet.has(id));
  const computedDesiredHours =
    typeof activeDesiredMinutes === 'number' && activeDesiredMinutes > 0
      ? Math.round((activeDesiredMinutes / 60) * 10000) / 10000
      : undefined;

  const currentDraftPayload: RecommendDraftPayload = {
    ingredient_ids: selectedIngredients.map((item) => item.id),
    excluded_pantry_ids: excludedPantryIds,
    ...(validMainIds.length > 0 ? { main_ingredient_ids: validMainIds } : {}),
    ...(computedDesiredHours !== undefined
      ? { desired_hours: computedDesiredHours }
      : {}),
  };

  const handleRecommendClick = () => {
    if (!canRecommend) return;
    setSubmittedPayload(currentDraftPayload);
    onTriggerRecommend?.(currentDraftPayload);
  };

  return (
    <div className="space-y-6">
      <div className="pt-1 text-center">
        <h1 className="font-serif text-3xl font-bold tracking-tight text-[#181512] sm:text-4xl">
          Tủ Bếp Nguyên Liệu
        </h1>
        <p className="mx-auto mt-1.5 max-w-lg text-xs text-[#6E655C] sm:text-sm">
          Chọn nguyên liệu sẵn có ở bàn bên trái và kiểm tra phiếu bếp bên phải
          để nhận gợi ý món ngon.
        </p>
      </div>

      <div className="grid grid-cols-1 items-start gap-7 lg:grid-cols-12">
        {/* KHỐI TRÁI (8/12): BÀN CHỌN NGUYÊN LIỆU HỢP NHẤT */}
        <div
          aria-label="Phân loại nguyên liệu theo nhóm"
          className="rounded-bl-[16px] rounded-br-[28px] rounded-tl-[28px] rounded-tr-[16px] border border-[#DFD3C3] bg-white p-5 shadow-[0_14px_40px_rgba(24,21,18,0.05)] sm:p-7 lg:col-span-8"
        >
          <div className="border-b border-[#EFE8DF] pb-5">
            <IngredientSearchBox
              selectedIngredients={selectedIngredients}
              onAddIngredient={handleAddIngredient}
              onSearchingChange={setIsSearching}
              onQueryChange={setSearchQuery}
            />
          </div>

          <div className="mt-6 grid grid-cols-1 gap-x-8 gap-y-7 sm:grid-cols-2">
            {CULINARY_GROUPS.map((group) => {
              const allItemsInGroup = group.slugs
                .map((slug) => ingredientBySlug.get(slug))
                .filter((item): item is Ingredient => Boolean(item));

              const filteredItems = isSearching
                ? allItemsInGroup.filter((item) =>
                    matchesIngredientQuery(item, searchQuery)
                  )
                : allItemsInGroup;

              if (isSearching && filteredItems.length === 0) {
                return null;
              }

              const isExpanded = !!expandedGroups[group.id];
              const defaultSlice = filteredItems.slice(
                0,
                DEFAULT_VISIBLE_LIMIT
              );
              const selectedBeyondLimit = filteredItems
                .slice(DEFAULT_VISIBLE_LIMIT)
                .filter((item) => selectedIdSet.has(item.id));

              const visibleItems =
                isSearching || isExpanded
                  ? filteredItems
                  : [...defaultSlice, ...selectedBeyondLimit];

              const hiddenCount = isSearching
                ? 0
                : Math.max(
                    0,
                    filteredItems.length -
                      (defaultSlice.length + selectedBeyondLimit.length)
                  );

              const canToggleMore =
                !isSearching && filteredItems.length > DEFAULT_VISIBLE_LIMIT;

              return (
                <section
                  key={group.id}
                  aria-label={group.title}
                  className="border-b border-[#F2ECE4] pb-6 last:border-b-0 last:pb-0 sm:[&:nth-last-child(-n+2)]:border-b-0 sm:[&:nth-last-child(-n+2)]:pb-0"
                >
                  <h2 className="mb-3 font-serif text-[17px] font-bold text-[#181512]">
                    {group.title}
                  </h2>

                  <div className="flex flex-wrap gap-2">
                    {visibleItems.map((item) => {
                      const isSelected = selectedIdSet.has(item.id);
                      return (
                        <button
                          key={item.id}
                          type="button"
                          data-testid={
                            isSearching
                              ? `pantry-category-chip-${item.slug}`
                              : `suggestion-item-${item.slug}`
                          }
                          aria-pressed={isSelected}
                          onClick={() => handleToggleIngredient(item)}
                          className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-[13px] font-medium transition ${
                            isSelected
                              ? 'bg-[#2E2620] text-white shadow-sm hover:bg-[#181512]'
                              : 'bg-[#F4EFE7] text-[#3B3027] hover:bg-[#EAE1D3]'
                          }`}
                        >
                          {isSelected && (
                            <Check
                              className="h-3.5 w-3.5 shrink-0 stroke-[2.5]"
                              aria-hidden="true"
                            />
                          )}
                          <span>{item.name_vi}</span>
                        </button>
                      );
                    })}

                    {canToggleMore && (isExpanded || hiddenCount > 0) && (
                      <button
                        type="button"
                        onClick={() => toggleGroupExpand(group.id)}
                        className="inline-flex items-center rounded-full border border-dashed border-[#C7B9A5] bg-[#FAF7F2] px-3.5 py-2 text-[12px] font-semibold text-[#6E655C] transition hover:border-[#181512] hover:text-[#181512]"
                      >
                        {isExpanded ? 'Thu gọn' : `+${hiddenCount} xem thêm`}
                      </button>
                    )}
                  </div>
                </section>
              );
            })}
          </div>
        </div>

        {/* KHỐI PHẢI (4/12, Sticky): PHIẾU BẾP HỢP NHẤT */}
        <aside
          aria-label="Phiếu bếp tổng hợp nguyên liệu và gia vị"
          className="rounded-bl-[16px] rounded-br-[28px] rounded-tl-[28px] rounded-tr-[16px] border border-[#DFD3C3] bg-white p-5 shadow-[0_14px_40px_rgba(24,21,18,0.05)] sm:p-7 lg:sticky lg:top-6 lg:col-span-4"
        >
          {/* Ngăn 1: Nguyên liệu đã chọn + chọn ưu tiên món chính (tùy chọn) */}
          <SelectedIngredientsList
            selectedIngredients={selectedIngredients}
            onRemoveIngredient={handleRemoveIngredient}
            onClearAll={handleClearAllIngredients}
            mainIngredientIds={activeMainIds}
            onToggleMainIngredient={handleToggleMainIngredient}
          />

          <hr className="my-5 border-t border-dashed border-[#DFD3C3]" />

          {/* Ngăn 2: 5 Gia vị sẵn có trong bếp */}
          <PantryToggleBar
            pantryItems={pantryItems}
            excludedPantryIds={excludedPantryIds}
            onTogglePantryItem={handleTogglePantryItem}
            onResetPantryDefault={handleResetPantryDefault}
          />

          <hr className="my-5 border-t border-dashed border-[#DFD3C3]" />

          {/* Ngăn 3: Tùy chọn Thời gian mong muốn */}
          <section aria-label="Thời gian nấu mong muốn">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-1.5">
                <Clock
                  className="h-4 w-4 text-[#E87838]"
                  aria-hidden="true"
                />
                <h2 className="font-serif text-[16px] font-bold text-[#181512]">
                  Thời gian mong muốn
                </h2>
              </div>
              <span className="text-[11px] font-medium text-[#6E655C]">
                Tùy chọn
              </span>
            </div>

            <div className="mt-2.5">
              <DesiredTimeSelector
                desiredMinutes={activeDesiredMinutes}
                onDesiredMinutesChange={(minutes) => {
                  setActiveDesiredMinutes(minutes);
                  setSubmittedPayload(null);
                }}
                testIdPrefix="desired-time-preset"
                activeTone="saffron"
                compact
              />
            </div>
          </section>

          <hr className="my-5 border-t border-dashed border-[#DFD3C3]" />

          {/* Ngăn 4: Hành động Gợi ý món ăn */}
          <section aria-label="Hành động gợi ý món ăn">
            <button
              type="button"
              data-testid="recommend-submit-btn"
              disabled={!canRecommend}
              onClick={handleRecommendClick}
              className="inline-flex w-full items-center justify-center rounded-full bg-[#E87838] px-6 py-3.5 text-[14px] font-semibold text-white shadow-sm transition hover:bg-[#D16426] disabled:cursor-not-allowed disabled:bg-[#EAE1D3] disabled:text-[#8C8277]"
            >
              <span>
                Gợi ý món ăn
                {canRecommend
                  ? ` (${currentDraftPayload.ingredient_ids.length} nguyên liệu)`
                  : ''}
              </span>
            </button>

            {!canRecommend && (
              <p
                data-testid="recommend-disabled-hint"
                className="mt-2.5 text-center text-xs text-[#6E655C]"
              >
                Chọn ít nhất 1 nguyên liệu chính để nhận gợi ý món ăn.
              </p>
            )}

            {submittedPayload && (
              <div
                data-testid="recommend-payload-preview"
                className="mt-3 flex items-center justify-center gap-1.5 text-xs font-semibold text-[#1E8E6E]"
              >
                <CheckCircle2 className="h-4 w-4 shrink-0" aria-hidden="true" />
                <span>
                  Đã sẵn sàng tìm món từ {submittedPayload.ingredient_ids.length}{' '}
                  nguyên liệu đã chọn
                </span>
              </div>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
};
