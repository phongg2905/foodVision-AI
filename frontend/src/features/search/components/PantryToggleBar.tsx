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
      <div className="flex items-start justify-between gap-2">
        <div>
          <h2 className="font-serif text-[18px] font-bold tracking-tight text-[#181512]">
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
            className="inline-flex min-h-[36px] shrink-0 items-center rounded-full px-2 text-[12px] font-semibold text-[#0E6B4F] transition hover:underline"
          >
            Chọn lại tất cả
          </button>
        )}
      </div>

      <div
        role="group"
        aria-label="Danh sách 5 gia vị cơ bản"
        className="mt-3 grid grid-cols-2 gap-2"
      >
        {pantryItems.map((item) => {
          const isAvailable = !excludedSet.has(item.id);

          return (
            <label
              key={item.id}
              data-testid={`pantry-toggle-${item.slug}`}
              className="group inline-flex min-h-[40px] cursor-pointer items-center gap-3 rounded-xl px-2.5 py-2 transition select-none hover:bg-[#F7EFE5] focus-within:outline-none"
            >
              <input
                type="checkbox"
                checked={isAvailable}
                onChange={() => onTogglePantryItem(item.id)}
                className="sr-only"
              />

              <span
                aria-hidden="true"
                className={`inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-[6px] transition group-focus-within:ring-2 group-focus-within:ring-[#0E6B4F] group-focus-within:ring-offset-2 ${
                  isAvailable
                    ? 'bg-[#0E6B4F] text-white'
                    : 'bg-[#D8CABB] text-transparent group-hover:text-[#FFF8F0]'
                }`}
              >
                <Check className="h-3.5 w-3.5 stroke-[3]" />
              </span>

              <span
                className={`text-[14px] font-medium transition ${
                  isAvailable ? 'text-[#0E6B4F]' : 'text-[#3B3027]'
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
