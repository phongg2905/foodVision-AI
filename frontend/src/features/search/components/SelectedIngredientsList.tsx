import React from 'react';
import { Check, X, Trash2 } from 'lucide-react';
import { Ingredient } from '../../../shared/api/types';

export interface SelectedIngredientsListProps {
  selectedIngredients: Ingredient[];
  onRemoveIngredient: (ingredientId: string) => void;
  onClearAll: () => void;
}

export const SelectedIngredientsList: React.FC<
  SelectedIngredientsListProps
> = ({ selectedIngredients, onRemoveIngredient, onClearAll }) => {
  return (
    <section aria-label="Danh sách nguyên liệu chính đã chọn">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <h2 className="font-serif text-[18px] font-bold text-[#181512]">
            Nguyên liệu đã chọn
          </h2>
          <span className="inline-flex h-6 min-w-[24px] items-center justify-center rounded-full bg-[#E87838]/15 px-2 text-xs font-bold text-[#E87838] tabular-nums">
            {selectedIngredients.length}
          </span>
        </div>

        {selectedIngredients.length > 0 && (
          <button
            type="button"
            onClick={onClearAll}
            className="inline-flex items-center gap-1 text-[12px] font-semibold text-[#E87838] transition hover:underline"
          >
            <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Bỏ chọn hết</span>
          </button>
        )}
      </div>

      {selectedIngredients.length === 0 ? (
        <p
          data-testid="selected-ingredients-empty"
          className="mt-3 rounded-2xl border border-dashed border-[#DFD3C3] bg-[#FAF7F2] px-4 py-4 text-center text-[13px] text-[#6E655C]"
        >
          Chưa có nguyên liệu nào. Hãy bấm chọn từ bàn nguyên liệu bên trái.
        </p>
      ) : (
        <ul
          data-testid="selected-ingredients-chips"
          className="mt-3.5 flex flex-wrap gap-2"
        >
          {selectedIngredients.map((item) => (
            <li
              key={item.id}
              data-testid={`selected-chip-${item.slug}`}
              className="inline-flex"
            >
              <button
                type="button"
                aria-label={`Xóa ${item.name_vi}`}
                onClick={() => onRemoveIngredient(item.id)}
                className="group inline-flex items-center gap-1.5 rounded-full bg-[#6E7781] px-3.5 py-1.5 text-[13px] font-medium text-white transition hover:bg-[#586069]"
              >
                <Check
                  className="h-3.5 w-3.5 shrink-0 stroke-[2.5]"
                  aria-hidden="true"
                />
                <span>{item.name_vi}</span>
                <X
                  className="ml-0.5 h-3.5 w-3.5 opacity-75 group-hover:opacity-100"
                  aria-hidden="true"
                />
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
};
