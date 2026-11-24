import React from 'react';
import { Search, ChevronDown } from 'lucide-react';
import { CuisineCode, MaxDurationFilter } from '../../../shared/api/types';

export interface RecipeFilterBarProps {
  searchQuery: string;
  onSearchQueryChange: (value: string) => void;
  selectedCuisine: CuisineCode | null;
  onCuisineChange: (value: CuisineCode | null) => void;
  selectedMaxMinutes: MaxDurationFilter;
  onMaxMinutesChange: (value: MaxDurationFilter) => void;
  onResetFilters: () => void;
  totalCount: number;
}

const CUISINE_OPTIONS: Array<{ value: CuisineCode | null; label: string }> = [
  { value: null, label: 'Ẩm thực: Tất cả' },
  { value: 'VN', label: 'Ẩm thực: Món Việt' },
  { value: 'EU', label: 'Ẩm thực: Món Âu' },
  { value: 'US', label: 'Ẩm thực: Món Mỹ' },
];

const DURATION_OPTIONS: Array<{ value: MaxDurationFilter; label: string }> = [
  { value: null, label: 'Thời gian: Mọi mốc' },
  { value: 15, label: 'Thời gian: ≤ 15 phút' },
  { value: 30, label: 'Thời gian: ≤ 30 phút' },
  { value: 60, label: 'Thời gian: ≤ 60 phút' },
];

export const RecipeFilterBar: React.FC<RecipeFilterBarProps> = ({
  searchQuery,
  onSearchQueryChange,
  selectedCuisine,
  onCuisineChange,
  selectedMaxMinutes,
  onMaxMinutesChange,
  onResetFilters,
  totalCount,
}) => {
  const hasActiveFilter =
    searchQuery.trim().length > 0 ||
    selectedCuisine !== null ||
    selectedMaxMinutes !== null;

  return (
    <section
      id="special-recipes"
      aria-label="Bộ lọc tra cứu công thức"
      className="scroll-mt-6 border-t border-[#CDB9A2]/80 pt-10"
    >
      <div className="pb-6 text-center">
        <h2 className="font-serif text-[30px] font-bold tracking-tight text-[#181512] sm:text-[36px]">
          Công Thức Đặc Biệt Cho Bạn
        </h2>
        <p className="mx-auto mt-1.5 max-w-[56ch] text-[14px] leading-relaxed text-[#4A4037]">
          Tuyển chọn thực đơn Việt, Âu, Mỹ đã kiểm duyệt định lượng và thời gian
          chế biến rõ ràng cho gian bếp gia đình.
        </p>
      </div>

      {/* Thanh Tìm kiếm & Lọc sạch không icon rườm rà */}
      <div className="mx-auto max-w-4xl">
        <div className="rounded-[18px] bg-[#FFF8F0] px-4 py-3 shadow-[0_10px_28px_rgba(24,21,18,0.06)] sm:px-5">
          <div className="grid grid-cols-1 gap-2.5 md:grid-cols-12 md:items-center md:divide-x md:divide-[#E4D5C3]">
            <div className="flex min-h-[40px] items-center gap-2.5 px-1 md:col-span-6 md:pr-4">
              <Search
                className="h-4 w-4 shrink-0 text-[#6B5E52]"
                aria-hidden="true"
              />
              <input
                id="recipe-search-input"
                type="search"
                value={searchQuery}
                onChange={(e) => onSearchQueryChange(e.target.value)}
                placeholder="Tìm tên món: canh cà chua, bò lúc lắc..."
                aria-label="Tìm tên món ăn"
                maxLength={100}
                className="w-full border-0 bg-transparent p-0 text-[14px] text-[#181512] placeholder:text-[#6B5E52] focus:outline-none focus:ring-0"
              />
            </div>

            <div className="relative flex min-h-[40px] items-center border-t border-[#EAE0D3] pt-2.5 md:col-span-3 md:border-t-0 md:px-4 md:pt-0">
              <select
                id="cuisine-select"
                aria-label="Chọn nền ẩm thực"
                value={selectedCuisine ?? ''}
                onChange={(e) =>
                  onCuisineChange(
                    e.target.value ? (e.target.value as CuisineCode) : null
                  )
                }
                className="min-h-[38px] w-full cursor-pointer appearance-none bg-transparent pr-6 text-[13.5px] font-medium text-[#181512] focus:outline-none"
              >
                {CUISINE_OPTIONS.map((opt) => (
                  <option key={opt.value ?? 'ALL'} value={opt.value ?? ''}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <ChevronDown
                className="pointer-events-none absolute right-1 h-4 w-4 text-[#595047] md:right-3"
                aria-hidden="true"
              />
            </div>

            <div className="relative flex min-h-[40px] items-center border-t border-[#EAE0D3] pt-2.5 md:col-span-3 md:border-t-0 md:pl-4 md:pt-0">
              <select
                id="duration-select"
                aria-label="Chọn thời gian nấu tối đa"
                value={selectedMaxMinutes ?? ''}
                onChange={(e) =>
                  onMaxMinutesChange(
                    e.target.value
                      ? (Number(e.target.value) as MaxDurationFilter)
                      : null
                  )
                }
                className="min-h-[38px] w-full cursor-pointer appearance-none bg-transparent pr-6 text-[13.5px] font-medium text-[#181512] focus:outline-none"
              >
                {DURATION_OPTIONS.map((opt) => (
                  <option
                    key={opt.value ?? 'ALL_TIME'}
                    value={opt.value ?? ''}
                  >
                    {opt.label}
                  </option>
                ))}
              </select>
              <ChevronDown
                className="pointer-events-none absolute right-1 h-4 w-4 text-[#595047]"
                aria-hidden="true"
              />
            </div>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-2 px-1">
          <p className="text-[13px] text-[#4A4037]">
            Hiển thị{' '}
            <strong className="font-bold text-[#181512] tabular-nums">
              {totalCount}
            </strong>{' '}
            công thức món ăn
          </p>

          {hasActiveFilter && (
            <button
              type="button"
              onClick={onResetFilters}
              className="inline-flex min-h-[36px] items-center rounded-full px-3 text-[12.5px] font-semibold text-[#B4490E] transition hover:bg-[#FFF8F0]/70 hover:underline"
            >
              Xóa bộ lọc
            </button>
          )}
        </div>
      </div>
    </section>
  );
};
