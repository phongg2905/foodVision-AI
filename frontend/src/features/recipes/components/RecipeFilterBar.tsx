import React from 'react';
import {
  Search,
  Clock,
  Globe2,
  ChevronDown,
  RotateCcw,
} from 'lucide-react';
import { CuisineCode, MaxDurationFilter } from '../../../shared/api/types';
import { BotanicalDecor } from '../../../shared/components/BotanicalDecor';

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
  { value: 'VN', label: 'Món Việt' },
  { value: 'EU', label: 'Món Âu' },
  { value: 'US', label: 'Món Mỹ' },
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
      {/* Tiêu đề Hero phong cách chữ Serif đậm David Libre của NEWTASTE kèm nét thảo mộc */}
      <div className="relative pb-6 pt-2 text-center">
        <BotanicalDecor
          variant="basil"
          className="pointer-events-none absolute left-4 top-0 hidden h-20 w-20 text-[#9A856E]/35 md:block lg:left-24"
        />
        <BotanicalDecor
          variant="rosemary"
          className="pointer-events-none absolute right-4 top-0 hidden h-20 w-20 text-[#9A856E]/35 md:block lg:right-24"
        />

        <h1 className="relative font-serif text-3xl font-bold tracking-tight text-[#181512] sm:text-4xl">
          Công Thức Đặc Biệt Cho Bạn
        </h1>
        <p className="relative mx-auto mt-2 max-w-[60ch] text-xs leading-relaxed text-[#595047] sm:text-sm">
          Dù bạn là đầu bếp gia đình hay người mới bắt đầu vào bếp, hãy khám phá
          ngay những công thức nấu ăn chuẩn vị từ nguyên liệu gần gũi mỗi ngày.
        </p>
      </div>

      {/* Thanh Tìm kiếm & Bộ lọc 4 Cột Nổi Ngang trên nền trắng kem #FFF8F0 */}
      <div className="mx-auto max-w-6xl">
        <div className="rounded-tl-[24px] rounded-br-[24px] rounded-tr-[6px] rounded-bl-[6px] border border-[#D8C6B2] bg-[#FFF8F0] px-5 py-4 shadow-[0_12px_32px_rgba(24,21,18,0.06)] sm:px-7 sm:py-5">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-12 lg:items-center lg:divide-x lg:divide-[#E4D5C3]">
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
                  className="mt-0.5 w-full border-0 bg-transparent p-0 text-[13px] text-[#181512] placeholder:text-[#7D7064] focus:outline-none focus:ring-0"
                />
              </div>
            </div>

            {/* Cột 2: Chọn nền ẩm thực */}
            <div className="flex items-center gap-3.5 border-t border-[#E9DCCE] pt-3.5 lg:col-span-3 lg:border-t-0 lg:px-6 lg:pt-0">
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
                    className="w-full cursor-pointer appearance-none bg-transparent pr-5 text-[13px] text-[#595047] focus:outline-none"
                  >
                    {CUISINE_OPTIONS.map((opt) => (
                      <option key={opt.value ?? 'ALL'} value={opt.value ?? ''}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                  <ChevronDown
                    className="pointer-events-none absolute right-0 h-4 w-4 text-[#595047]"
                    aria-hidden="true"
                  />
                </div>
              </div>
            </div>

            {/* Cột 3: Thời gian nấu */}
            <div className="flex items-center gap-3.5 border-t border-[#E9DCCE] pt-3.5 lg:col-span-3 lg:border-t-0 lg:px-6 lg:pt-0">
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
                    className="w-full cursor-pointer appearance-none bg-transparent pr-5 text-[13px] text-[#595047] focus:outline-none"
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
                    className="pointer-events-none absolute right-0 h-4 w-4 text-[#595047]"
                    aria-hidden="true"
                  />
                </div>
              </div>
            </div>

            {/* Cột 4: Nút Tìm kiếm cắt chéo chiếc lá #C65112 (WCAG AA chữ trắng 4.58:1) */}
            <div className="border-t border-[#E9DCCE] pt-3.5 lg:col-span-2 lg:border-t-0 lg:pl-6 lg:pt-0">
              <button
                type="button"
                onClick={() => onSearchQueryChange(searchQuery.trim())}
                className="inline-flex min-h-[42px] w-full items-center justify-center gap-2 rounded-tl-[14px] rounded-br-[14px] rounded-tr-[4px] rounded-bl-[4px] bg-[#C65112] px-5 py-2.5 text-[13px] font-semibold text-white shadow-sm transition hover:bg-[#A8430D]"
              >
                <Search className="h-4 w-4" aria-hidden="true" />
                <span>Tìm kiếm</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Hàng thông tin số lượng kết quả */}
      <div className="mt-6 flex items-center justify-between px-2">
        <p className="text-[14px] text-[#595047]">
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
            className="inline-flex min-h-[36px] items-center gap-1.5 rounded-full px-2.5 text-[13px] font-semibold text-[#9E3D08] transition hover:underline"
          >
            <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Xóa bộ lọc</span>
          </button>
        )}
      </div>
    </section>
  );
};
