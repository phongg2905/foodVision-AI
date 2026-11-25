import React, { useEffect, useRef, useState } from 'react';
import { Camera, Check, ChevronDown, Star, X } from 'lucide-react';
import { Ingredient, RecommendDraftPayload } from '../../shared/api/types';
import {
  listPantryIngredients,
  searchMainIngredients,
} from '../../shared/api/ingredientsApi';
import {
  MOCK_MAIN_INGREDIENTS,
  MOCK_PANTRY_INGREDIENTS,
} from '../../shared/api/mockData';
import { IngredientSearchBox } from './components/IngredientSearchBox';
import { SelectedIngredientsList } from './components/SelectedIngredientsList';
import { PantryToggleBar } from './components/PantryToggleBar';
import { DesiredTimeSelector } from '../../shared/components/DesiredTimeSelector';
import { VisionScanPanel } from '../vision/VisionScanPanel';

export interface IngredientKitchenViewProps {
  selectedIngredients: Ingredient[];
  onSelectedIngredientsChange: (ingredients: Ingredient[]) => void;
  excludedPantryIds: string[];
  onExcludedPantryIdsChange: (ids: string[]) => void;
  mainIngredientIds?: string[];
  onMainIngredientIdsChange?: (ids: string[]) => void;
  desiredMinutes?: number | null;
  onDesiredMinutesChange?: (minutes: number | null) => void;
  scanId?: string | null;
  onScanIdChange?: (scanId: string | null) => void;
  onTriggerRecommend?: (payload: RecommendDraftPayload) => void;
  studioMode?: boolean;
}

const POPULAR_SLUGS = [
  'dau-hu',
  'ca-chua',
  'trung-ga',
  'thit-ba-chi',
  'thit-heo-song',
  'thit-bo',
  'thit-ga-song',
  'tom',
  'bap-ngot',
  'dua-leo',
  'bong-cai-xanh',
  'hanh-la',
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
  scanId: controlledScanId,
  onScanIdChange,
  onTriggerRecommend,
  studioMode = false,
}) => {
  const barRef = useRef<HTMLDivElement | null>(null);
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
  const [internalScanId, setInternalScanId] = useState<string | null>(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [openPopover, setOpenPopover] = useState<
    'none' | 'pantry' | 'time' | 'camera'
  >('none');
  const [showQuickPick, setShowQuickPick] = useState<boolean>(
    () => selectedIngredients.length === 0
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

  const activeScanId =
    controlledScanId !== undefined ? controlledScanId : internalScanId;
  const setActiveScanId = (nextScanId: string | null) => {
    if (onScanIdChange) {
      onScanIdChange(nextScanId);
    } else {
      setInternalScanId(nextScanId);
    }
  };

  const selectedIdSet = new Set(selectedIngredients.map((item) => item.id));
  const mainIdSet = new Set(activeMainIds);
  const ingredientBySlug = new Map(
    catalogIngredients.map((item) => [item.slug, item])
  );

  useEffect(() => {
    const handleOutside = (e: MouseEvent) => {
      if (barRef.current && !barRef.current.contains(e.target as Node)) {
        // Không tự đóng khay camera khi người dùng đang duyệt xác nhận HITL
        setOpenPopover((prev) => (prev === 'camera' ? 'camera' : 'none'));
      }
    };
    document.addEventListener('mousedown', handleOutside);
    return () => document.removeEventListener('mousedown', handleOutside);
  }, []);

  useEffect(() => {
    let isCancelled = false;

    listPantryIngredients()
      .then((res) => {
        if (isCancelled) return;
        const filteredPantry = res.items.filter(
          (item) => item.category === 'pantry' && item.is_active
        );
        if (filteredPantry.length > 0) {
          setPantryItems(filteredPantry);
        }
      })
      .catch(() => {});

    searchMainIngredients('', 50, 0)
      .then((res) => {
        if (isCancelled) return;
        // Thay thế hoàn toàn bằng danh mục live từ Backend và lọc cứng category !== 'pantry' (F1)
        const filteredMain = res.items.filter(
          (item) => item.category !== 'pantry' && item.is_active
        );
        if (filteredMain.length > 0) {
          setCatalogIngredients(filteredMain);
        }
      })
      .catch(() => {});

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
    setActiveScanId(null);
    setSubmittedPayload(null);
  };

  const focusVietnameseSearchInput = () => {
    window.setTimeout(() => {
      const input = barRef.current?.querySelector<HTMLInputElement>(
        'input[aria-label="Nhập tên nguyên liệu chính"]'
      );
      input?.focus();
    }, 0);
  };

  const handleConfirmHitlIngredients = (
    confirmedIngredients: Ingredient[],
    nextScanId: string | null
  ) => {
    // Khử trùng lặp UUID tuyệt đối khi hợp nhất vào tủ bếp (TC-08)
    const mergedMap = new Map<string, Ingredient>();
    for (const existing of selectedIngredients) {
      mergedMap.set(existing.id, existing);
    }
    for (const confirmed of confirmedIngredients) {
      if (confirmed.category !== 'pantry') {
        mergedMap.set(confirmed.id, confirmed);
      }
    }
    const mergedList = Array.from(mergedMap.values());
    onSelectedIngredientsChange(mergedList);
    setActiveScanId(nextScanId);
    setShowQuickPick(false);
    setOpenPopover('none');
    setSubmittedPayload(null);
  };

  const handleFallbackToManualSearch = () => {
    setActiveScanId(null);
    setOpenPopover('none');
    focusVietnameseSearchInput();
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
    ...(activeScanId ? { scan_id: activeScanId } : {}),
  };

  const handleRecommendClick = () => {
    if (!canRecommend) return;
    setSubmittedPayload(currentDraftPayload);
    onTriggerRecommend?.(currentDraftPayload);
  };

  const popularItems = POPULAR_SLUGS.map((slug) =>
    ingredientBySlug.get(slug)
  )
    .filter((item): item is Ingredient => Boolean(item))
    .slice(0, 12);

  const availablePantryCount = Math.max(
    0,
    pantryItems.length - excludedPantryIds.length
  );

  /* =========================================================================
     CHẾ ĐỘ STUDIO (MOCKUP PHƯƠNG ÁN A): THANH TỦ BẾP NGANG GỌN 2 DÒNG Ở TRÊN
     ========================================================================= */
  if (studioMode) {
    return (
      <section
        ref={barRef}
        aria-label="Thanh tủ bếp thông minh"
        className="relative mx-auto max-w-5xl rounded-[22px] bg-[#FFF8F0] px-5 py-4 shadow-[0_12px_34px_rgba(24,21,18,0.06)] sm:px-6 sm:py-5"
      >
        {/* DÒNG 1: Ô tìm kiếm nguyên liệu + Nút viền Quét ảnh AI */}
        <div className="flex flex-col gap-2.5 sm:flex-row sm:items-center">
          <div className="min-w-0 flex-1">
            <IngredientSearchBox
              selectedIngredients={selectedIngredients}
              onAddIngredient={handleAddIngredient}
              onDropdownOpenChange={setIsDropdownOpen}
            />
          </div>

          <button
            type="button"
            data-testid="kitchen-camera-mode-tab"
            aria-expanded={openPopover === 'camera'}
            onClick={() =>
              setOpenPopover((prev) => (prev === 'camera' ? 'none' : 'camera'))
            }
            className={`inline-flex min-h-[44px] shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-full border px-5 py-2 text-[13.5px] font-medium transition ${
              openPopover === 'camera'
                ? 'border-[#181512] bg-[#181512] text-[#FFF8F0]'
                : 'border-[#B89F86] bg-transparent text-[#3B3027] hover:border-[#181512] hover:text-[#181512]'
            }`}
          >
            <Camera className="h-4 w-4 stroke-[1.75]" aria-hidden="true" />
            <span>Quét ảnh AI</span>
          </button>
        </div>

        {/* Khay Quét ảnh AI, vẽ BBox EXIF & Xác nhận HITL (TP 14 — Thẻ #22) */}
        {openPopover === 'camera' && (
          <VisionScanPanel
            catalogIngredients={catalogIngredients}
            onConfirmHitlIngredients={handleConfirmHitlIngredients}
            onFallbackToManual={handleFallbackToManualSearch}
            onClose={() => setOpenPopover('none')}
          />
        )}

        {/* DÒNG 2: Bên trái là Tag nguyên liệu đã chọn — Bên phải là 2 nút xổ Gia vị & Thời gian */}
        <div className="mt-3.5 flex flex-wrap items-center justify-between gap-3">
          {/* Cụm tag nguyên liệu đã chọn + Nút bật/tắt gợi ý chọn nhanh */}
          <div className="flex flex-wrap items-center gap-2">
            {selectedIngredients.map((item) => {
              const isMain = mainIdSet.has(item.id);
              return (
                <span
                  key={item.id}
                  data-testid={`selected-chip-${item.slug}`}
                  className={`inline-flex min-h-[34px] items-center rounded-full text-[13px] transition ${
                    isMain
                      ? 'bg-[#F4DEC9] font-semibold text-[#9E3D08]'
                      : 'bg-[#EFE2D2] font-medium text-[#181512]'
                  }`}
                >
                  <button
                    type="button"
                    data-testid={`toggle-main-${item.slug}`}
                    aria-pressed={isMain}
                    aria-label={`Ưu tiên ${item.name_vi} làm nguyên liệu chính`}
                    title="Bấm để đặt hoặc bỏ ưu tiên làm nguyên liệu chính"
                    onClick={() => handleToggleMainIngredient(item.id)}
                    className="inline-flex min-h-[34px] items-center gap-1 pl-3.5 pr-2"
                  >
                    {isMain && (
                      <Star
                        className="h-3.5 w-3.5 shrink-0 fill-current"
                        aria-hidden="true"
                      />
                    )}
                    <span>{item.name_vi}</span>
                  </button>
                  <button
                    type="button"
                    aria-label={`Xóa ${item.name_vi}`}
                    onClick={() => handleRemoveIngredient(item.id)}
                    className="inline-flex min-h-[34px] items-center pr-3 pl-1 text-[#595047] transition hover:text-[#181512]"
                  >
                    <X className="h-3.5 w-3.5" aria-hidden="true" />
                  </button>
                </span>
              );
            })}

            <button
              type="button"
              data-testid="toggle-quick-ingredients"
              aria-expanded={showQuickPick}
              onClick={() => setShowQuickPick((prev) => !prev)}
              className="inline-flex min-h-[34px] items-center gap-1 rounded-full px-2.5 text-[12.5px] font-medium text-[#595047] transition hover:bg-[#F5EADF] hover:text-[#181512]"
            >
              <span>{showQuickPick ? 'Ẩn gợi ý' : '+ Chọn nhanh'}</span>
              <ChevronDown
                className={`h-3.5 w-3.5 transition-transform ${
                  showQuickPick ? 'rotate-180' : ''
                }`}
                aria-hidden="true"
              />
            </button>

            {selectedIngredients.length > 1 && (
              <button
                type="button"
                onClick={handleClearAllIngredients}
                className="inline-flex min-h-[34px] items-center rounded-full px-2 text-[12px] text-[#7A6D60] transition hover:text-[#B4490E]"
              >
                Xóa hết
              </button>
            )}
          </div>

          {/* Cụm 2 nút Dropdown gọn sạch bên phải chuẩn Mockup A */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              data-testid="studio-pantry-trigger"
              aria-expanded={openPopover === 'pantry'}
              onClick={() =>
                setOpenPopover((prev) =>
                  prev === 'pantry' ? 'none' : 'pantry'
                )
              }
              className={`inline-flex min-h-[34px] items-center gap-1.5 rounded-full border px-3.5 py-1 text-[12.5px] font-medium tabular-nums transition ${
                openPopover === 'pantry'
                  ? 'border-[#181512] bg-[#F5EADF] text-[#181512]'
                  : 'border-[#D5C2AC] bg-[#FFFDF9] text-[#3B3027] hover:border-[#181512]'
              }`}
            >
              <span>
                Gia vị sẵn có: {availablePantryCount}/{pantryItems.length}
              </span>
              <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />
            </button>

            <button
              type="button"
              data-testid="studio-time-trigger"
              aria-expanded={openPopover === 'time'}
              onClick={() =>
                setOpenPopover((prev) => (prev === 'time' ? 'none' : 'time'))
              }
              className={`inline-flex min-h-[34px] items-center gap-1.5 rounded-full border px-3.5 py-1 text-[12.5px] font-medium tabular-nums transition ${
                openPopover === 'time'
                  ? 'border-[#181512] bg-[#F5EADF] text-[#181512]'
                  : 'border-[#D5C2AC] bg-[#FFFDF9] text-[#3B3027] hover:border-[#181512]'
              }`}
            >
              <span>
                Thời gian:{' '}
                {activeDesiredMinutes
                  ? `≤ ${activeDesiredMinutes} phút`
                  : 'Mọi mốc'}
              </span>
              <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />
            </button>
          </div>
        </div>

        {/* Khay gợi ý chọn nhanh nguyên liệu (Mở sẵn khi giỏ trống, thu gọn gọn gàng khi cần) */}
        {showQuickPick && (
          <div className="mt-3 border-t border-[#EAE0D3] pt-3">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="mr-1 text-[12px] text-[#595047]">
                Nguyên liệu phổ biến:
              </span>
              {popularItems.map((item) => {
                const isSelected = selectedIdSet.has(item.id);
                return (
                  <button
                    key={item.id}
                    type="button"
                    data-testid={
                      isDropdownOpen
                        ? `category-chip-${item.slug}`
                        : `suggestion-item-${item.slug}`
                    }
                    aria-pressed={isSelected}
                    onClick={() => handleToggleIngredient(item)}
                    className={`inline-flex min-h-[32px] items-center rounded-full px-3 py-1 text-[12.5px] transition ${
                      isSelected
                        ? 'bg-[#181512] font-medium text-[#FFF8F0]'
                        : 'bg-[#F5EADF] text-[#3B3027] hover:bg-[#E8D8C6]'
                    }`}
                  >
                    {isSelected ? (
                      <>
                        <Check
                          className="mr-1 h-3.5 w-3.5 shrink-0"
                          aria-hidden="true"
                        />
                        <span>{item.name_vi}</span>
                      </>
                    ) : (
                      <span>+ {item.name_vi}</span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Popover chỉnh 5 Gia vị cơ bản */}
        {openPopover === 'pantry' && (
          <div className="mt-3 rounded-[14px] border border-[#E4D5C3] bg-[#FAF3EB] p-4">
            <PantryToggleBar
              pantryItems={pantryItems}
              excludedPantryIds={excludedPantryIds}
              onTogglePantryItem={handleTogglePantryItem}
              onResetPantryDefault={handleResetPantryDefault}
            />
          </div>
        )}

        {/* Popover chỉnh Thời gian mong muốn */}
        {openPopover === 'time' && (
          <div className="mt-3 rounded-[14px] border border-[#E4D5C3] bg-[#FAF3EB] p-4">
            <p className="mb-2 text-[12.5px] font-semibold text-[#181512]">
              Thời gian nấu mong muốn (tính điểm ưu tiên):
            </p>
            <DesiredTimeSelector
              desiredMinutes={activeDesiredMinutes}
              onDesiredMinutesChange={(minutes) => {
                setActiveDesiredMinutes(minutes);
              }}
              testIdPrefix="desired-time-preset"
              activeTone="saffron"
              compact
            />
          </div>
        )}
      </section>
    );
  }

  /* =========================================================================
     CHẾ ĐỘ ĐỘC LẬP (DÙNG CHO BÀI TEST ĐƠN VỊ INGREDIENTKITCHENVIEW)
     ========================================================================= */
  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <div className="rounded-[22px] bg-[#FFF8F0] p-5 shadow-[0_12px_34px_rgba(24,21,18,0.06)] sm:p-6">
        <IngredientSearchBox
          selectedIngredients={selectedIngredients}
          onAddIngredient={handleAddIngredient}
          onDropdownOpenChange={setIsDropdownOpen}
        />

        <div className="mt-4 flex flex-wrap gap-1.5">
          {popularItems.map((item) => {
            const isSelected = selectedIdSet.has(item.id);
            return (
              <button
                key={item.id}
                type="button"
                data-testid={
                  isDropdownOpen
                    ? `category-chip-${item.slug}`
                    : `suggestion-item-${item.slug}`
                }
                aria-pressed={isSelected}
                onClick={() => handleToggleIngredient(item)}
                className={`inline-flex min-h-[36px] items-center rounded-full px-3.5 py-1.5 text-[13px] font-medium transition ${
                  isSelected
                    ? 'bg-[#181512] text-[#FFF8F0]'
                    : 'bg-[#F5EADF] text-[#3B3027] hover:bg-[#E8D8C6]'
                }`}
              >
                {item.name_vi}
              </button>
            );
          })}
        </div>

        <hr className="my-5 border-t border-[#EAE0D3]" />

        <SelectedIngredientsList
          selectedIngredients={selectedIngredients}
          onRemoveIngredient={handleRemoveIngredient}
          onClearAll={handleClearAllIngredients}
          mainIngredientIds={activeMainIds}
          onToggleMainIngredient={handleToggleMainIngredient}
        />

        <hr className="my-5 border-t border-[#EAE0D3]" />

        <PantryToggleBar
          pantryItems={pantryItems}
          excludedPantryIds={excludedPantryIds}
          onTogglePantryItem={handleTogglePantryItem}
          onResetPantryDefault={handleResetPantryDefault}
        />

        <hr className="my-5 border-t border-[#EAE0D3]" />

        <DesiredTimeSelector
          desiredMinutes={activeDesiredMinutes}
          onDesiredMinutesChange={setActiveDesiredMinutes}
          testIdPrefix="desired-time-preset"
          activeTone="saffron"
          compact
        />

        <div className="mt-5">
          <button
            type="button"
            data-testid="recommend-submit-btn"
            disabled={!canRecommend}
            onClick={handleRecommendClick}
            className="inline-flex min-h-[44px] w-full items-center justify-center rounded-full bg-[#B4490E] px-6 py-2.5 text-[14px] font-semibold text-white transition hover:bg-[#963B0A] disabled:cursor-not-allowed disabled:bg-[#E2D4C3] disabled:text-[#595047]"
          >
            Gợi ý món ăn
            {canRecommend
              ? ` (${currentDraftPayload.ingredient_ids.length} nguyên liệu)`
              : ''}
          </button>

          {!canRecommend && (
            <p
              data-testid="recommend-disabled-hint"
              className="mt-2 text-center text-xs text-[#595047]"
            >
              Chọn ít nhất 1 nguyên liệu chính để nhận gợi ý món ăn.
            </p>
          )}

          {submittedPayload && (
            <p
              data-testid="recommend-payload-preview"
              className="mt-2 text-center text-xs font-semibold text-[#B4490E]"
            >
              Đã sẵn sàng tìm món từ {submittedPayload.ingredient_ids.length}{' '}
              nguyên liệu đã chọn
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
