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
      {/* MỤC 7 — Bám sát 100% cột trái "Checkboxes" của mẫu muc7-pantry-9-pinterest-checkbox-cards-kit.jpg */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <h2 className="font-serif text-[17px] font-bold tracking-tight text-[#181512]">
            5 Gia vị sẵn có trong bếp
          </h2>
          <p className="mt-0.5 text-[12px] text-[#6E655C]">
            Mặc định luôn có sẵn, bỏ tích nếu bếp đang hết:
          </p>
        </div>

        {excludedPantryIds.length > 0 && (
          <button
            type="button"
            onClick={onResetPantryDefault}
            className="shrink-0 text-[12px] font-semibold text-[#00C48C] transition hover:underline"
          >
            Chọn lại tất cả
          </button>
        )}
      </div>

      <div
        role="group"
        aria-label="Danh sách 5 gia vị cơ bản"
        className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3"
      >
        {pantryItems.map((item) => {
          const isAvailable = !excludedSet.has(item.id);

          return (
            <label
              key={item.id}
              data-testid={`pantry-toggle-${item.slug}`}
              className="group inline-flex cursor-pointer items-center gap-3 py-0.5 select-none focus-within:outline-none"
            >
              <input
                type="checkbox"
                checked={isAvailable}
                onChange={() => onTogglePantryItem(item.id)}
                className="sr-only"
              />

              {/* Ô vuông bo góc: Xanh ngọc #00C48C khi Checked; Xám nhạt #D5D9DD khi Unchecked và hiện tích trắng khi Hover */}
              <span
                aria-hidden="true"
                className={`inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-[6px] transition group-focus-within:ring-2 group-focus-within:ring-[#00C48C] group-focus-within:ring-offset-2 ${
                  isAvailable
                    ? 'bg-[#00C48C] text-white'
                    : 'bg-[#D5D9DD] text-transparent group-hover:text-white'
                }`}
              >
                <Check className="h-3.5 w-3.5 stroke-[3]" />
              </span>

              {/* Tên gia vị: Xanh teal #1E8E6E khi Checked; Xanh đen #243447 khi Unchecked */}
              <span
                className={`text-[14px] font-medium transition ${
                  isAvailable ? 'text-[#1E8E6E]' : 'text-[#243447]'
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
