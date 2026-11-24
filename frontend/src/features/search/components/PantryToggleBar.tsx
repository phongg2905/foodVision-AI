import React from 'react';
import { Check } from 'lucide-react';
import { Ingredient } from '../../../shared/api/types';

export interface PantryToggleBarProps {
  pantryItems: Ingredient[];
  excludedPantryIds: string[];
  onTogglePantryItem: (pantryId: string) => void;
  onResetPantryDefault: () => void;
}

export const PantryToggleBar: React.FC<PantryToggleBarProps> = ({
  pantryItems,
  excludedPantryIds,
  onTogglePantryItem,
  onResetPantryDefault,
}) => {
  const excludedSet = new Set(excludedPantryIds);

  return (
    <section aria-label="Thanh 5 gia vị sẵn có trong bếp">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="font-serif text-[16px] font-bold text-[#181512]">
            5 Gia vị sẵn có trong bếp
          </h2>
          <p className="mt-0.5 text-[12px] text-[#595047]">
            Mặc định luôn có sẵn, bỏ tích nếu bếp đang hết:
          </p>
        </div>

        {excludedPantryIds.length > 0 && (
          <button
            type="button"
            onClick={onResetPantryDefault}
            className="inline-flex min-h-[34px] shrink-0 items-center rounded-full px-2.5 text-[12px] font-semibold text-[#B4490E] transition hover:bg-[#F5EADF]"
          >
            Chọn lại tất cả
          </button>
        )}
      </div>

      <div
        role="group"
        aria-label="Danh sách 5 gia vị cơ bản"
        className="mt-3 flex flex-wrap gap-2"
      >
        {pantryItems.map((item) => {
          const isAvailable = !excludedSet.has(item.id);

          return (
            <label
              key={item.id}
              data-testid={`pantry-toggle-${item.slug}`}
              className={`group inline-flex min-h-[36px] cursor-pointer items-center gap-2 rounded-full px-3.5 py-1.5 transition select-none focus-within:ring-2 focus-within:ring-[#B4490E] ${
                isAvailable
                  ? 'bg-[#EFE2D2] text-[#181512] hover:bg-[#E5D4BF]'
                  : 'bg-[#F7EFE5] text-[#7A6D60] hover:bg-[#EFE2D2]'
              }`}
            >
              <input
                type="checkbox"
                checked={isAvailable}
                onChange={() => onTogglePantryItem(item.id)}
                className="sr-only"
              />

              <span
                aria-hidden="true"
                className={`inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-[4px] transition ${
                  isAvailable
                    ? 'bg-[#B4490E] text-white'
                    : 'border border-[#C4B19C] bg-transparent text-transparent'
                }`}
              >
                <Check className="h-3 w-3 stroke-[3]" />
              </span>

              <span
                className={`text-[13px] font-medium transition ${
                  isAvailable ? '' : 'line-through decoration-[#9A8B7C]'
                }`}
              >
                {item.name_vi}
              </span>
            </label>
          );
        })}
      </div>
    </section>
  );
};
