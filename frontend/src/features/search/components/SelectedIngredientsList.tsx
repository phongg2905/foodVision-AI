import React from 'react';
import { Check, Star, X } from 'lucide-react';
import { Ingredient } from '../../../shared/api/types';

export interface SelectedIngredientsListProps {
  selectedIngredients: Ingredient[];
  onRemoveIngredient: (ingredientId: string) => void;
  onClearAll: () => void;
  mainIngredientIds?: string[];
  onToggleMainIngredient?: (ingredientId: string) => void;
}

export const SelectedIngredientsList: React.FC<
  SelectedIngredientsListProps
> = ({
  selectedIngredients,
  onRemoveIngredient,
  onClearAll,
  mainIngredientIds = [],
  onToggleMainIngredient,
}) => {
  const mainSet = new Set(mainIngredientIds);

  return (
    <section aria-label="Danh sách nguyên liệu chính đã chọn">
      <div className="flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <h2 className="whitespace-nowrap font-serif text-[17px] font-bold text-[#181512]">
            Nguyên liệu trong tủ bếp
          </h2>
          <span className="inline-flex h-6 min-w-[24px] shrink-0 items-center justify-center rounded-full bg-[#F5EADF] px-2 text-xs font-bold text-[#9E3D08] tabular-nums">
            {selectedIngredients.length}
          </span>
        </div>

        {selectedIngredients.length > 0 && (
          <button
            type="button"
            onClick={onClearAll}
            className="inline-flex min-h-[36px] shrink-0 items-center whitespace-nowrap rounded-[8px] px-2 text-[12px] font-semibold text-[#9E3D08] transition hover:bg-[#F5EADF]"
          >
            Bỏ chọn hết
          </button>
        )}
      </div>

      {selectedIngredients.length === 0 ? (
        <p
          data-testid="selected-ingredients-empty"
          className="mt-2.5 rounded-[8px] bg-[#F5EADF] px-3.5 py-3 text-[12.5px] text-[#4A4037]"
        >
          Chưa chọn nguyên liệu nào. Hãy tìm hoặc tích nhanh nguyên liệu phía
          trên.
        </p>
      ) : (
        <>
          <ul
            data-testid="selected-ingredients-chips"
            className="mt-3 flex flex-wrap gap-1.5"
          >
            {selectedIngredients.map((item) => {
              const isMain = mainSet.has(item.id);
              return (
                <li
                  key={item.id}
                  data-testid={`selected-chip-${item.slug}`}
                  className={`inline-flex min-h-[36px] items-stretch overflow-hidden rounded-[8px] text-[13px] font-medium transition ${
                    isMain
                      ? 'bg-[#C65112] text-white shadow-sm'
                      : 'bg-[#2B241E] text-[#FFF8F0]'
                  }`}
                >
                  {onToggleMainIngredient ? (
                    <button
                      type="button"
                      data-testid={`toggle-main-${item.slug}`}
                      aria-label={`Ưu tiên ${item.name_vi} làm nguyên liệu chính`}
                      aria-pressed={isMain}
                      title={
                        isMain
                          ? 'Đang ưu tiên làm món chính (bấm để bỏ)'
                          : 'Bấm để ưu tiên làm món chính'
                      }
                      onClick={() => onToggleMainIngredient(item.id)}
                      className={`inline-flex min-h-[36px] items-center gap-1.5 py-1.5 pl-3 pr-2.5 transition ${
                        isMain ? 'hover:bg-[#A8430D]' : 'hover:bg-[#3B322A]'
                      }`}
                    >
                      <Star
                        className={`h-3.5 w-3.5 shrink-0 ${
                          isMain ? 'fill-white text-white' : 'text-[#F3C19D]'
                        }`}
                        aria-hidden="true"
                      />
                      <span>{item.name_vi}</span>
                      {isMain && (
                        <span className="rounded-[4px] bg-white/20 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide">
                          Chính
                        </span>
                      )}
                    </button>
                  ) : (
                    <span className="inline-flex min-h-[36px] items-center gap-1.5 py-1.5 pl-3 pr-2">
                      <Check
                        className="h-3.5 w-3.5 shrink-0 stroke-[2.5]"
                        aria-hidden="true"
                      />
                      <span>{item.name_vi}</span>
                    </span>
                  )}

                  <button
                    type="button"
                    aria-label={`Xóa ${item.name_vi}`}
                    onClick={() => onRemoveIngredient(item.id)}
                    className={`inline-flex min-h-[36px] min-w-[36px] items-center justify-center border-l px-2 transition ${
                      isMain
                        ? 'border-white/25 text-white/90 hover:bg-[#963906] hover:text-white'
                        : 'border-white/15 text-[#E8D8C6] hover:bg-[#181512] hover:text-white'
                    }`}
                  >
                    <X className="h-3.5 w-3.5" aria-hidden="true" />
                  </button>
                </li>
              );
            })}
          </ul>

          {onToggleMainIngredient && (
            <p className="mt-2 text-[11px] leading-relaxed text-[#595047]">
              Bấm{' '}
              <Star
                className="mx-0.5 inline h-3 w-3 fill-current text-[#9E3D08]"
                aria-hidden="true"
              />{' '}
              trên nguyên liệu muốn ưu tiên làm món chính (tùy chọn).
            </p>
          )}
        </>
      )}
    </section>
  );
};
