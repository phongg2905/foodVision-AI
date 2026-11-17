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
      <nav
        aria-label="Phân trang danh sách công thức"
        className="inline-flex flex-wrap items-center justify-center gap-4 rounded-tl-[20px] rounded-br-[20px] rounded-tr-[6px] rounded-bl-[6px] border border-[#D8C6B2] bg-[#FFF8F0] px-7 py-3.5 shadow-[0_8px_28px_rgba(24,21,18,0.06)] sm:gap-6 sm:px-9"
      >
        <button
          type="button"
          disabled={!canGoPrev}
          onClick={() => onOffsetChange(Math.max(0, offset - limit))}
          className="inline-flex min-h-[40px] items-center gap-1.5 px-2 text-[13px] font-semibold text-[#9E3D08] transition hover:text-[#181512] disabled:cursor-not-allowed disabled:opacity-40"
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
                className={`inline-flex h-10 w-10 items-center justify-center rounded-lg text-[13px] font-semibold tabular-nums transition ${
                  isCurrent
                    ? 'bg-[#C65112] text-white shadow-sm'
                    : 'bg-[#F4EAE0] text-[#181512] hover:bg-[#E8D8C6]'
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
          className="inline-flex min-h-[40px] items-center gap-1.5 px-2 text-[13px] font-semibold text-[#9E3D08] transition hover:text-[#181512] disabled:cursor-not-allowed disabled:opacity-40"
        >
          <span>Trang sau</span>
          <ChevronRight className="h-4 w-4" aria-hidden="true" />
        </button>
      </nav>
    </div>
  );
};
