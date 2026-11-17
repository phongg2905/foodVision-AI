import React from 'react';
import {
  Clock,
  Filter,
  RotateCcw,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';
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

const DURATION_OPTIONS: Array<{ value: MaxDurationFilter; label: string }> = [
  { value: null, label: 'Mọi thời gian' },
  { value: 15, label: '≤ 15 phút' },
  { value: 30, label: '≤ 30 phút' },
  { value: 60, label: '≤ 60 phút' },
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
      className="rounded-tl-[22px] rounded-br-[22px] rounded-tr-[6px] rounded-bl-[6px] border border-[#D8C6B2] bg-[#FFF8F0] px-4 py-3.5 shadow-[0_10px_28px_rgba(24,21,18,0.06)] sm:px-5 sm:py-4"
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        {/* Cột 1: Chọn nền ẩm thực (Hỗ trợ đa chọn cuisine_codes[]) */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1.5 text-[12px] font-bold text-[#181512]">
            <Filter className="h-3.5 w-3.5 text-[#9E3D08]" aria-hidden="true" />
            <span>Ẩm thực:</span>
          </span>

          <button
            type="button"
            data-testid="filter-cuisine-all"
            aria-pressed={cuisineCodes.length === 0}
            onClick={() => onCuisineCodesChange([])}
            className={`inline-flex min-h-[36px] items-center justify-center rounded-full px-3.5 py-1.5 text-[12px] font-semibold transition ${
              cuisineCodes.length === 0
                ? 'bg-[#181512] text-[#FFF8F0]'
                : 'border border-[#D8C6B2] bg-[#F7EFE5] text-[#4A4037] hover:border-[#181512]'
            }`}
          >
            Tất cả
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
                className={`inline-flex min-h-[36px] items-center justify-center rounded-full px-3.5 py-1.5 text-[12px] font-semibold transition ${
                  isActive
                    ? 'bg-[#C65112] text-white shadow-sm'
                    : 'border border-[#D8C6B2] bg-[#F7EFE5] text-[#4A4037] hover:border-[#EA6D27] hover:text-[#9E3D08]'
                }`}
              >
                {pill.label}
              </button>
            );
          })}
        </div>

        {/* Cột 2: Giới hạn thời gian tối đa & Các công tắc Nấu ngay / Đổi vị đa dạng */}
        <div className="flex flex-wrap items-center gap-2.5">
          <label className="inline-flex min-h-[36px] items-center gap-1.5 rounded-full border border-[#D8C6B2] bg-[#F7EFE5] px-3.5 py-1.5 text-[12px] font-semibold text-[#181512]">
            <Clock className="h-3.5 w-3.5 text-[#9E3D08]" aria-hidden="true" />
            <span className="text-[#595047]">Giới hạn:</span>
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
              className="cursor-pointer bg-transparent pr-1 text-[12px] font-semibold text-[#181512] focus:outline-none"
            >
              {DURATION_OPTIONS.map((opt) => (
                <option key={opt.value ?? 'ALL'} value={opt.value ?? ''}>
                  {opt.label}
                </option>
              ))}
            </select>
          </label>

          <label
            data-testid="toggle-only-ready"
            className={`inline-flex min-h-[36px] cursor-pointer items-center gap-2 rounded-full border px-3.5 py-1.5 text-[12px] font-semibold transition select-none ${
              !includeMissing
                ? 'border-[#0E6B4F] bg-[#E7F8F2] text-[#0E6B4F]'
                : 'border-[#D8C6B2] bg-[#F7EFE5] text-[#4A4037] hover:border-[#0E6B4F]'
            }`}
          >
            <input
              type="checkbox"
              aria-label="Chỉ hiện món nấu được ngay"
              checked={!includeMissing}
              onChange={(e) => onIncludeMissingChange(!e.target.checked)}
              className="sr-only"
            />
            <CheckCircle2 className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            <span>Chỉ hiện món nấu ngay</span>
          </label>

          <label
            data-testid="toggle-mmr-diversify"
            title="Đa dạng hóa thực đơn theo thuật toán MMR"
            className={`inline-flex min-h-[36px] cursor-pointer items-center gap-2 rounded-full border px-3.5 py-1.5 text-[12px] font-semibold transition select-none ${
              diversify
                ? 'border-[#C65112] bg-[#C65112] text-white'
                : 'border-[#D8C6B2] bg-[#F7EFE5] text-[#4A4037] hover:border-[#C65112] hover:text-[#9E3D08]'
            }`}
          >
            <input
              type="checkbox"
              aria-label="Đa dạng hóa thực đơn (MMR)"
              checked={diversify}
              onChange={(e) => onDiversifyChange(e.target.checked)}
              className="sr-only"
            />
            <Sparkles className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            <span>Đổi vị đa dạng</span>
          </label>
        </div>
      </div>

      {/* Hàng tóm tắt số lượng + Đặt lại bộ lọc */}
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-[#E4D5C3] pt-2.5">
        <p className="text-[13px] text-[#595047]">
          Tìm thấy{' '}
          <strong className="font-bold text-[#181512] tabular-nums">
            {totalCount}
          </strong>{' '}
          món phù hợp (
          <span className="font-semibold text-[#0E6B4F] tabular-nums">
            {readyCount} nấu được ngay
          </span>{' '}
          ·{' '}
          <span className="font-semibold text-[#9E3D08] tabular-nums">
            {missingCount} còn thiếu nguyên liệu
          </span>
          )
        </p>

        {hasActiveFilter && (
          <button
            type="button"
            data-testid="reset-recommend-filters"
            onClick={onResetFilters}
            className="inline-flex min-h-[36px] items-center gap-1.5 rounded-full px-2.5 text-[12px] font-semibold text-[#9E3D08] transition hover:underline"
          >
            <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Đặt lại bộ lọc</span>
          </button>
        )}
      </div>
    </section>
  );
};
