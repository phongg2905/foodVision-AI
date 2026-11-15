import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export interface RecipePaginationProps {
  total: number;
  limit: number;
  offset: number;
  onOffsetChange: (newOffset: number) => void;
}

export const RecipePagination: React.FC<RecipePaginationProps> = ({
  total,
  limit,
  offset,
  onOffsetChange,
}) => {
  if (total <= limit) {
    return null;
  }

  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.ceil(total / limit);
  const canGoPrev = offset > 0;
  const canGoNext = offset + limit < total;

  const pageNumbers = Array.from({ length: totalPages }, (_, idx) => idx + 1);

  return (
    <div className="mt-12 flex justify-center">
      {/* MỤC 4 — Thanh Phân trang bám sát mẫu muc4-page-1-dribbble-pagination-ui.jpg (Dòng thứ 5) phối màu New Taste */}
      <nav
        aria-label="Phân trang danh sách công thức"
        className="inline-flex flex-wrap items-center justify-center gap-4 rounded-2xl border border-[#DFD3C3] bg-white px-7 py-3.5 shadow-[0_8px_30px_rgba(24,21,18,0.05)] sm:gap-6 sm:px-9"
      >
        <button
          type="button"
          disabled={!canGoPrev}
          onClick={() => onOffsetChange(Math.max(0, offset - limit))}
          className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-[#E87838] transition hover:text-[#D16426] disabled:cursor-not-allowed disabled:opacity-40"
        >
          <ChevronLeft className="h-4 w-4" aria-hidden="true" />
          <span>Trang trước</span>
        </button>

        <div className="flex items-center gap-2">
          {pageNumbers.map((page) => {
            const isCurrent = page === currentPage;
            return (
              <button
                key={page}
                type="button"
                aria-current={isCurrent ? 'page' : undefined}
                onClick={() => onOffsetChange((page - 1) * limit)}
                className={`inline-flex h-9 w-9 items-center justify-center rounded-lg text-[13px] font-semibold tabular-nums transition ${
                  isCurrent
                    ? 'bg-[#E87838] text-white shadow-sm'
                    : 'bg-[#F7F2EA] text-[#181512] hover:bg-[#EFE6D8]'
                }`}
              >
                {page}
              </button>
            );
          })}
        </div>

        <button
          type="button"
          disabled={!canGoNext}
          onClick={() => onOffsetChange(offset + limit)}
          className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-[#E87838] transition hover:text-[#D16426] disabled:cursor-not-allowed disabled:opacity-40"
        >
          <span>Trang sau</span>
          <ChevronRight className="h-4 w-4" aria-hidden="true" />
        </button>
      </nav>
    </div>
  );
};
