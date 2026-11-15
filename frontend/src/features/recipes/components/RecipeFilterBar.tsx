import React from 'react';
import {
  Search,
  Clock,
  Globe2,
  ChevronDown,
  RotateCcw,
} from 'lucide-react';
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
  { value: null, label: 'Tất cả ẩm thực' },
  { value: 'VN', label: 'Món Việt (VN)' },
  { value: 'EU', label: 'Món Âu (EU)' },
  { value: 'US', label: 'Món Mỹ (US)' },
];

const DURATION_OPTIONS: Array<{ value: MaxDurationFilter; label: string }> = [
  { value: null, label: 'Mọi thời gian' },
  { value: 15, label: '≤ 15 phút' },
  { value: 30, label: '≤ 30 phút' },
  { value: 60, label: '≤ 60 phút' },
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
    <section aria-label="Bộ lọc tra cứu công thức">
      {/* Tiêu đề Hero phong cách chữ Serif đậm của New Taste ("We provide the best Recipes for you") */}
      <div className="pb-6 pt-2 text-center">
        <h1 className="font-serif text-3xl font-bold tracking-tight text-[#181512] sm:text-4xl">
          Công Thức Đặc Biệt Cho Bạn
        </h1>
        <p className="mx-auto mt-2 max-w-xl text-xs leading-relaxed text-[#6E655C] sm:text-sm">
          Dù bạn là đầu bếp gia đình hay người mới bắt đầu vào bếp, hãy khám phá
          ngay những công thức nấu ăn chuẩn vị từ nguyên liệu gần gũi mỗi ngày.
        </p>
      </div>

      {/* MỤC 3 — DUY NHẤT 1 Thanh Tìm kiếm & Bộ lọc 4 Cột Nổi Ngang (Seatwave Floating Search Bar — Không lặp lại bộ lọc bên dưới) */}
      <div className="mx-auto max-w-6xl">
        <div className="rounded-2xl border border-[#DFD3C3] bg-white px-5 py-4 shadow-[0_12px_34px_rgba(24,21,18,0.06)] sm:px-7 sm:py-5">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-12 lg:items-center lg:divide-x lg:divide-[#EBE4DA]">
            {/* Cột 1: Tìm tên món ăn */}
            <div className="flex items-center gap-3.5 lg:col-span-4 lg:pr-5">
              <Search
                className="h-5 w-5 shrink-0 text-[#181512]"
                aria-hidden="true"
              />
              <div className="min-w-0 flex-1">
                <label
                  htmlFor="recipe-search-input"
                  className="block text-[12px] font-bold text-[#181512]"
                >
                  Tìm tên món ăn
                </label>
                <input
                  id="recipe-search-input"
                  type="search"
                  value={searchQuery}
                  onChange={(e) => onSearchQueryChange(e.target.value)}
                  placeholder="VD: canh cà chua, bò lúc lắc..."
                  aria-label="Tìm tên món ăn"
                  maxLength={100}
                  className="mt-0.5 w-full border-0 bg-transparent p-0 text-[13px] text-[#181512] placeholder:text-[#9A9086] focus:outline-none focus:ring-0"
                />
              </div>
            </div>

            {/* Cột 2: Chọn nền ẩm thực */}
            <div className="flex items-center gap-3.5 border-t border-[#EFECE6] pt-3.5 lg:col-span-3 lg:border-t-0 lg:px-6 lg:pt-0">
              <Globe2
                className="h-5 w-5 shrink-0 text-[#181512]"
                aria-hidden="true"
              />
              <div className="relative min-w-0 flex-1">
                <label
                  htmlFor="cuisine-select"
                  className="block text-[12px] font-bold text-[#181512]"
                >
                  Chọn nền ẩm thực
                </label>
                <div className="relative mt-0.5 flex items-center">
                  <select
                    id="cuisine-select"
                    aria-label="Chọn nền ẩm thực"
                    value={selectedCuisine ?? ''}
                    onChange={(e) =>
                      onCuisineChange(
                        e.target.value ? (e.target.value as CuisineCode) : null
                      )
                    }
                    className="w-full cursor-pointer appearance-none bg-transparent pr-5 text-[13px] text-[#6E655C] focus:outline-none"
                  >
                    {CUISINE_OPTIONS.map((opt) => (
                      <option key={opt.value ?? 'ALL'} value={opt.value ?? ''}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                  <ChevronDown
                    className="pointer-events-none absolute right-0 h-4 w-4 text-[#6E655C]"
                    aria-hidden="true"
                  />
                </div>
              </div>
            </div>

            {/* Cột 3: Thời gian nấu */}
            <div className="flex items-center gap-3.5 border-t border-[#EFECE6] pt-3.5 lg:col-span-3 lg:border-t-0 lg:px-6 lg:pt-0">
              <Clock
                className="h-5 w-5 shrink-0 text-[#181512]"
                aria-hidden="true"
              />
              <div className="relative min-w-0 flex-1">
                <label
                  htmlFor="duration-select"
                  className="block text-[12px] font-bold text-[#181512]"
                >
                  Thời gian nấu
                </label>
                <div className="relative mt-0.5 flex items-center">
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
                    className="w-full cursor-pointer appearance-none bg-transparent pr-5 text-[13px] text-[#6E655C] focus:outline-none"
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
                    className="pointer-events-none absolute right-0 h-4 w-4 text-[#6E655C]"
                    aria-hidden="true"
                  />
                </div>
              </div>
            </div>

            {/* Cột 4: Nút Pill Tìm kiếm màu Cam #E87838 của New Taste */}
            <div className="border-t border-[#EFECE6] pt-3.5 lg:col-span-2 lg:border-t-0 lg:pl-6 lg:pt-0">
              <button
                type="button"
                onClick={() => onSearchQueryChange(searchQuery.trim())}
                className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-[#E87838] px-5 py-3 text-[13px] font-semibold text-white shadow-sm transition hover:bg-[#D16426]"
              >
                <Search className="h-4 w-4" aria-hidden="true" />
                <span>Tìm kiếm</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Hàng thông tin số lượng kết quả gọn gàng */}
      <div className="mt-6 flex items-center justify-between px-2">
        <p className="text-[14px] text-[#6E655C]">
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
            className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-[#E87838] transition hover:underline"
          >
            <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Xóa bộ lọc</span>
          </button>
        )}
      </div>
    </section>
  );
};
