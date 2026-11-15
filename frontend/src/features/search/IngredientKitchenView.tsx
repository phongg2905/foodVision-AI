import React, { useEffect, useState } from 'react';
import { Check, CheckCircle2 } from 'lucide-react';
import { Ingredient, RecommendDraftPayload } from '../../shared/api/types';
import { listPantryIngredients } from '../../shared/api/ingredientsApi';
import {
  MOCK_MAIN_INGREDIENTS,
  MOCK_PANTRY_INGREDIENTS,
} from '../../shared/api/mockData';
import { matchesIngredientQuery } from '../../shared/utils/vietnamese';
import { IngredientSearchBox } from './components/IngredientSearchBox';
import { SelectedIngredientsList } from './components/SelectedIngredientsList';
import { PantryToggleBar } from './components/PantryToggleBar';

export interface IngredientKitchenViewProps {
  selectedIngredients: Ingredient[];
  onSelectedIngredientsChange: (ingredients: Ingredient[]) => void;
  excludedPantryIds: string[];
  onExcludedPantryIdsChange: (ids: string[]) => void;
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
  onTriggerRecommend,
}) => {
  const [pantryItems, setPantryItems] = useState<Ingredient[]>(
    MOCK_PANTRY_INGREDIENTS
  );
  const [isSearching, setIsSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>(
    {}
  );
  const [submittedPayload, setSubmittedPayload] =
    useState<RecommendDraftPayload | null>(null);

  const selectedIdSet = new Set(selectedIngredients.map((item) => item.id));
  const ingredientBySlug = new Map(
    MOCK_MAIN_INGREDIENTS.map((item) => [item.slug, item])
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

  const currentDraftPayload: RecommendDraftPayload = {
    ingredient_ids: selectedIngredients.map((item) => item.id),
    excluded_pantry_ids: excludedPantryIds,
  };

  const handleRecommendClick = () => {
    if (!canRecommend) return;
    setSubmittedPayload(currentDraftPayload);
    onTriggerRecommend?.(currentDraftPayload);
  };

  return (
    <div className="space-y-6">
      {/* Tiêu đề trang ngắn gọn, tinh tế */}
      <div className="pt-1 text-center">
        <h1 className="font-serif text-3xl font-bold tracking-tight text-[#181512] sm:text-4xl">
          Tủ Bếp Nguyên Liệu
        </h1>
        <p className="mx-auto mt-1.5 max-w-lg text-xs text-[#6E655C] sm:text-sm">
          Chọn nguyên liệu sẵn có ở bàn bên trái và kiểm tra phiếu bếp bên phải
          để nhận gợi ý món ngon.
        </p>
      </div>

      {/* =====================================================================
          UNIFIED 2-PANEL KITCHEN (CO GIÃN THÔNG MINH CHO DỮ LIỆU LỚN)
          - Khối Trái (8/12): Bàn Chọn Nguyên Liệu hợp nhất
            + Mặc định mỗi nhóm hiển thị 6 nguyên liệu thông dụng nhất + các nguyên liệu đã chọn; phần còn lại gọn trong chip "+X xem thêm".
            + Khi gõ từ khóa vào ô Search, các nhóm bên dưới tự động lọc trực tiếp các chip khớp từ khóa.
          - Khối Phải (4/12, Sticky): Phiếu Bếp hợp nhất chia 3 ngăn.
         ===================================================================== */}
      <div className="grid grid-cols-1 items-start gap-7 lg:grid-cols-12">
        {/* KHỐI TRÁI (8/12): BÀN CHỌN NGUYÊN LIỆU HỢP NHẤT */}
        <div
          aria-label="Phân loại nguyên liệu theo nhóm"
          className="rounded-[28px] border border-[#DFD3C3] bg-white p-5 shadow-[0_14px_40px_rgba(24,21,18,0.05)] sm:p-7 lg:col-span-8"
        >
          {/* Phần đầu Bàn Nguyên Liệu: Ô Search Box gọn gàng */}
          <div className="border-b border-[#EFE8DF] pb-5">
            <IngredientSearchBox
              selectedIngredients={selectedIngredients}
              onAddIngredient={handleAddIngredient}
              onSearchingChange={setIsSearching}
              onQueryChange={setSearchQuery}
            />
          </div>

          {/* Phần thân Bàn Nguyên Liệu: Chia 6 nhóm thực phẩm chuẩn bếp Việt dạng lưới 2 cột cân đối */}
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

              // Khi chưa mở rộng và không đang gõ tìm kiếm:
              // Hiển thị 6 nguyên liệu đầu + bất kỳ nguyên liệu nào ở phần ẩn nhưng đã được người dùng chọn
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
                  {/* Tiêu đề nhóm thuần chữ (Typographic Header), không icon */}
                  <h2 className="mb-3 font-serif text-[17px] font-bold text-[#181512]">
                    {group.title}
                  </h2>

                  {/* Các chip nguyên liệu (Mục 6 — muc6-tags-2) + Chip "+X xem thêm / Thu gọn" */}
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
                              ? 'bg-[#6E7781] text-white shadow-sm hover:bg-[#586069]'
                              : 'bg-[#EAECEE] text-[#374151] hover:bg-[#DCE0E5]'
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

        {/* KHỐI PHẢI (4/12, Sticky): PHIẾU BẾP HỢP NHẤT (1 THẺ DUY NHẤT CHIA 3 NGĂN) */}
        <aside
          aria-label="Phiếu bếp tổng hợp nguyên liệu và gia vị"
          className="rounded-[28px] border border-[#DFD3C3] bg-white p-5 shadow-[0_14px_40px_rgba(24,21,18,0.05)] sm:p-7 lg:sticky lg:top-6 lg:col-span-4"
        >
          {/* Ngăn 1: Nguyên liệu đã chọn */}
          <SelectedIngredientsList
            selectedIngredients={selectedIngredients}
            onRemoveIngredient={handleRemoveIngredient}
            onClearAll={handleClearAllIngredients}
          />

          {/* Đường kẻ nét đứt ngăn cách như phiếu bếp */}
          <hr className="my-5 border-t border-dashed border-[#DFD3C3]" />

          {/* Ngăn 2: 5 Gia vị sẵn có trong bếp */}
          <PantryToggleBar
            pantryItems={pantryItems}
            excludedPantryIds={excludedPantryIds}
            onTogglePantryItem={handleTogglePantryItem}
            onResetPantryDefault={handleResetPantryDefault}
          />

          {/* Đường kẻ nét đứt ngăn cách */}
          <hr className="my-5 border-t border-dashed border-[#DFD3C3]" />

          {/* Ngăn 3: Hành động Gợi ý món ăn */}
          <section aria-label="Hành động gợi ý món ăn">
            <button
              type="button"
              data-testid="recommend-submit-btn"
              disabled={!canRecommend}
              onClick={handleRecommendClick}
              className="inline-flex w-full items-center justify-center rounded-full bg-[#E87838] px-6 py-3.5 text-[14px] font-semibold text-white shadow-sm transition hover:bg-[#D16426] disabled:cursor-not-allowed disabled:bg-[#E4E4E7] disabled:text-[#A1A1AA]"
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
