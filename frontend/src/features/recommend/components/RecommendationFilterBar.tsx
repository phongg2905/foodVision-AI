import React from 'react';
import { ChevronDown } from 'lucide-react';
import { CuisineCode, MaxDurationFilter } from '../../../shared/api/types';

export interface RecommendationFilterBarProps {
  cuisineCodes: CuisineCode[];
  onCuisineCodesChange: (codes: CuisineCode[]) => void;
  maxTotalMinutes: MaxDurationFilter;
  onMaxTotalMinutesChange: (minutes: MaxDurationFilter) => void;
  includeMissing: boolean;
  onIncludeMissingChange: (include: boolean) => void;
  diversify: boolean;
  onDiversifyChange: (diversify: boolean) => void;
  onResetFilters: () => void;
  totalCount: number;
  readyCount: number;
  missingCount: number;
}

const CUISINE_PILLS: Array<{ code: CuisineCode; label: string }> = [
  { code: 'VN', label: 'Món Việt' },
  { code: 'EU', label: 'Món Âu' },
  { code: 'US', label: 'Món Mỹ' },
];

export const RecommendationFilterBar: React.FC<
  RecommendationFilterBarProps
> = ({
  cuisineCodes,
  onCuisineCodesChange,
  maxTotalMinutes,
  onMaxTotalMinutesChange,
  includeMissing,
  onIncludeMissingChange,
  diversify,
  onDiversifyChange,
  onResetFilters,
  totalCount,
  readyCount,
  missingCount,
}) => {
  const hasActiveFilter =
    cuisineCodes.length > 0 ||
    maxTotalMinutes !== null ||
    !includeMissing ||
    diversify;

  const toggleCuisine = (code: CuisineCode) => {
    if (cuisineCodes.includes(code)) {
      onCuisineCodesChange(cuisineCodes.filter((c) => c !== code));
    } else {
      onCuisineCodesChange([...cuisineCodes, code]);
    }
  };

  return (
    <section
      aria-label="Bộ lọc danh sách gợi ý món ăn"
      className="border-b border-[#CDB9A2] pb-3.5"
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-1.5">
          <button
            type="button"
            data-testid="filter-cuisine-all"
            aria-pressed={cuisineCodes.length === 0}
            onClick={() => onCuisineCodesChange([])}
            className={`inline-flex min-h-[34px] items-center rounded-full px-3.5 py-1 text-[12.5px] font-medium transition ${
              cuisineCodes.length === 0
                ? 'bg-[#181512] text-[#FFF8F0]'
                : 'bg-[#FFF8F0]/80 text-[#3B3027] hover:bg-[#FFF8F0]'
            }`}
          >
            Tất cả ẩm thực
          </button>

          {CUISINE_PILLS.map((pill) => {
            const isActive = cuisineCodes.includes(pill.code);
            return (
              <button
                key={pill.code}
                type="button"
                data-testid={`filter-cuisine-${pill.code}`}
                aria-pressed={isActive}
                onClick={() => toggleCuisine(pill.code)}
                className={`inline-flex min-h-[34px] items-center rounded-full px-3.5 py-1 text-[12.5px] font-medium transition ${
                  isActive
                    ? 'bg-[#B4490E] text-white'
                    : 'bg-[#FFF8F0]/80 text-[#3B3027] hover:bg-[#FFF8F0]'
                }`}
              >
                {pill.label}
              </button>
            );
          })}
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <div className="relative inline-flex items-center rounded-full bg-[#FFF8F0]/85 px-3.5 py-1 text-[12.5px]">
            <select
              aria-label="Thời gian nấu tối đa"
              data-testid="filter-max-minutes"
              value={maxTotalMinutes ?? ''}
              onChange={(e) =>
                onMaxTotalMinutesChange(
                  e.target.value
                    ? (Number(e.target.value) as MaxDurationFilter)
                    : null
                )
              }
              className="min-h-[26px] cursor-pointer appearance-none bg-transparent pr-5 font-medium text-[#181512] focus:outline-none"
            >
              <option value="">Giới hạn: Mọi mốc</option>
              <option value="15">Giới hạn: ≤ 15 phút</option>
              <option value="30">Giới hạn: ≤ 30 phút</option>
              <option value="60">Giới hạn: ≤ 60 phút</option>
            </select>
            <ChevronDown
              className="pointer-events-none absolute right-2.5 h-3.5 w-3.5 text-[#595047]"
              aria-hidden="true"
            />
          </div>

          <label
            data-testid="toggle-only-ready"
            className={`inline-flex min-h-[34px] cursor-pointer items-center rounded-full px-3.5 py-1 text-[12.5px] font-medium transition select-none ${
              !includeMissing
                ? 'bg-[#181512] text-[#FFF8F0]'
                : 'bg-[#FFF8F0]/85 text-[#3B3027] hover:bg-[#FFF8F0]'
            }`}
          >
            <input
              type="checkbox"
              aria-label="Chỉ hiện món nấu được ngay"
              checked={!includeMissing}
              onChange={(e) => onIncludeMissingChange(!e.target.checked)}
              className="sr-only"
            />
            <span>Chỉ món nấu ngay</span>
          </label>

          <label
            data-testid="toggle-mmr-diversify"
            className={`inline-flex min-h-[34px] cursor-pointer items-center rounded-full px-3.5 py-1 text-[12.5px] font-medium transition select-none ${
              diversify
                ? 'bg-[#B4490E] text-white'
                : 'bg-[#FFF8F0]/85 text-[#3B3027] hover:bg-[#FFF8F0]'
            }`}
          >
            <input
              type="checkbox"
              aria-label="Đa dạng hóa thực đơn (MMR)"
              checked={diversify}
              onChange={(e) => onDiversifyChange(e.target.checked)}
              className="sr-only"
            />
            <span>Đổi vị đa dạng</span>
          </label>
        </div>
      </div>

      <div className="mt-2.5 flex flex-wrap items-center justify-between gap-2 text-[13px] text-[#4A4037]">
        <p>
          Tìm thấy{' '}
          <strong className="font-bold text-[#181512] tabular-nums">
            {totalCount}
          </strong>{' '}
          món ({readyCount} nấu được ngay · {missingCount} còn thiếu nguyên liệu)
        </p>

        {hasActiveFilter && (
          <button
            type="button"
            data-testid="reset-recommend-filters"
            onClick={onResetFilters}
            className="font-semibold text-[#B4490E] hover:underline"
          >
            Đặt lại bộ lọc
          </button>
        )}
      </div>
    </section>
  );
};
