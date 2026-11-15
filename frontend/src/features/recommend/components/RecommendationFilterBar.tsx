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
      className="rounded-bl-[16px] rounded-br-[28px] rounded-tl-[28px] rounded-tr-[16px] border border-[#DFD3C3] bg-white p-4 shadow-[0_10px_28px_rgba(24,21,18,0.05)] sm:p-5"
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        {/* Cột 1: Chọn nền ẩm thực (Hỗ trợ đa chọn cuisine_codes[]) */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1.5 text-[12px] font-bold text-[#181512]">
            <Filter className="h-3.5 w-3.5 text-[#E87838]" aria-hidden="true" />
            <span>Ẩm thực:</span>
          </span>

          <button
            type="button"
            data-testid="filter-cuisine-all"
            aria-pressed={cuisineCodes.length === 0}
            onClick={() => onCuisineCodesChange([])}
            className={`rounded-full px-3 py-1.5 text-[12px] font-semibold transition ${
              cuisineCodes.length === 0
                ? 'bg-[#181512] text-white'
                : 'border border-[#DFD3C3] bg-[#FAF7F2] text-[#4A4139] hover:border-[#181512]'
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
                className={`rounded-full px-3 py-1.5 text-[12px] font-semibold transition ${
                  isActive
                    ? 'bg-[#E87838] text-white shadow-sm'
                    : 'border border-[#DFD3C3] bg-[#FAF7F2] text-[#4A4139] hover:border-[#E87838] hover:text-[#C2591B]'
                }`}
              >
                {pill.label}
              </button>
            );
          })}
        </div>

        {/* Cột 2: Thời gian tối đa & Các công tắc Nấu ngay / Đa dạng MMR */}
        <div className="flex flex-wrap items-center gap-3">
          <label className="inline-flex items-center gap-2 rounded-full border border-[#DFD3C3] bg-[#FAF7F2] px-3.5 py-1.5 text-[12px] font-semibold text-[#181512]">
            <Clock className="h-3.5 w-3.5 text-[#E87838]" aria-hidden="true" />
            <span className="sr-only">Thời gian nấu tối đa</span>
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
                <option
                  key={opt.value ?? 'ALL'}
                  value={opt.value ?? ''}
                >
                  {opt.label}
                </option>
              ))}
            </select>
          </label>

          <label
            data-testid="toggle-only-ready"
            className={`inline-flex cursor-pointer items-center gap-2 rounded-full border px-3.5 py-1.5 text-[12px] font-semibold transition select-none ${
              !includeMissing
                ? 'border-[#1E8E6E] bg-[#E7F8F2] text-[#157358]'
                : 'border-[#DFD3C3] bg-[#FAF7F2] text-[#4A4139] hover:border-[#1E8E6E]'
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
            className={`inline-flex cursor-pointer items-center gap-2 rounded-full border px-3.5 py-1.5 text-[12px] font-semibold transition select-none ${
              diversify
                ? 'border-[#E87838] bg-[#FDF0E7] text-[#C2591B]'
                : 'border-[#DFD3C3] bg-[#FAF7F2] text-[#4A4139] hover:border-[#E87838]'
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
            <span>Đa dạng thực đơn (MMR)</span>
          </label>
        </div>
      </div>

      {/* Hàng tóm tắt số lượng + Đặt lại bộ lọc */}
      <div className="mt-3.5 flex flex-wrap items-center justify-between gap-2 border-t border-[#EFE8DF] pt-3">
        <p className="text-[13px] text-[#574D44]">
          Tìm thấy{' '}
          <strong className="font-bold text-[#181512] tabular-nums">
            {totalCount}
          </strong>{' '}
          món phù hợp (
          <span className="font-semibold text-[#157358] tabular-nums">
            {readyCount} nấu được ngay
          </span>{' '}
          ·{' '}
          <span className="font-semibold text-[#C2591B] tabular-nums">
            {missingCount} còn thiếu nguyên liệu
          </span>
          )
        </p>

        {hasActiveFilter && (
          <button
            type="button"
            data-testid="reset-recommend-filters"
            onClick={onResetFilters}
            className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-[#C2591B] transition hover:underline"
          >
            <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Đặt lại bộ lọc</span>
          </button>
        )}
      </div>
    </section>
  );
};
