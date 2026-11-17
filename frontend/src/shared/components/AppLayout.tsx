import React from 'react';
import { Search, X } from 'lucide-react';
import { BotanicalDecor } from './BotanicalDecor';

export type ActiveTab = 'catalog' | 'kitchen' | 'recommendations';

export interface AppLayoutProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  selectedMainCount: number;
  quickSearchQuery?: string;
  onQuickSearchChange?: (query: string) => void;
  onQuickSearchSubmit?: () => void;
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  activeTab,
  onTabChange,
  selectedMainCount,
  quickSearchQuery = '',
  onQuickSearchChange,
  onQuickSearchSubmit,
  children,
}) => {
  const isKitchenStudio =
    activeTab === 'kitchen' || activeTab === 'recommendations';

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-[#E8D8C6] text-[#181512]">
      {/* Nét thảo mộc mảnh tinh tế ở góc trang đúng chất NEWTASTE */}
      <BotanicalDecor
        variant="header-arcs"
        className="pointer-events-none absolute left-0 top-0 h-40 w-64 text-[#A7927A]/35"
      />
      <BotanicalDecor
        variant="rosemary"
        className="pointer-events-none fixed -left-14 top-1/3 hidden h-52 w-52 text-[#9A856E]/20 2xl:block"
      />
      <BotanicalDecor
        variant="basil"
        className="pointer-events-none fixed -right-14 bottom-20 hidden h-56 w-56 text-[#9A856E]/20 2xl:block"
      />

      {/* HEADER TỐI GIẢN CHUẨN MOCKUP A (Không icon thừa) */}
      <header className="relative z-20 bg-transparent">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-5 sm:px-6 lg:px-8">
          {/* Trái: Wordmark serif thanh lịch */}
          <button
            type="button"
            onClick={() => onTabChange('catalog')}
            className="inline-flex shrink-0 items-baseline gap-2 whitespace-nowrap text-left transition hover:opacity-85 focus:outline-none"
          >
            <span className="font-serif text-[27px] font-bold tracking-tight text-[#B4490E] sm:text-[30px]">
              FoodVision
            </span>
          </button>

          {/* Giữa: 2 Không gian chính bằng chữ Serif có gạch chân cam đất */}
          <nav
            aria-label="Điều hướng chính"
            className="hidden items-center gap-10 lg:flex"
          >
            <button
              type="button"
              data-testid="nav-tab-catalog"
              aria-current={activeTab === 'catalog' ? 'page' : undefined}
              onClick={() => onTabChange('catalog')}
              className={`relative inline-flex min-h-[40px] shrink-0 items-center whitespace-nowrap py-1.5 font-serif text-[17px] transition ${
                activeTab === 'catalog'
                  ? 'font-bold text-[#181512]'
                  : 'font-medium text-[#4A4037] hover:text-[#181512]'
              }`}
            >
              Khám phá công thức
              {activeTab === 'catalog' && (
                <span className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full bg-[#B4490E]" />
              )}
            </button>

            <button
              type="button"
              data-testid="nav-tab-kitchen"
              aria-current={isKitchenStudio ? 'page' : undefined}
              onClick={() => onTabChange('kitchen')}
              className={`relative inline-flex min-h-[40px] shrink-0 items-center gap-2 whitespace-nowrap py-1.5 font-serif text-[17px] transition ${
                isKitchenStudio
                  ? 'font-bold text-[#181512]'
                  : 'font-medium text-[#4A4037] hover:text-[#181512]'
              }`}
            >
              <span>Gợi ý từ tủ bếp</span>
              {selectedMainCount > 0 && (
                <span
                  data-testid="nav-selected-badge"
                  className="inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-[#B4490E] px-1.5 font-sans text-[11px] font-bold text-white tabular-nums"
                >
                  {selectedMainCount}
                </span>
              )}
              {isKitchenStudio && (
                <span className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full bg-[#B4490E]" />
              )}
            </button>
          </nav>

          {/* Phải: Duy nhất ô tìm kiếm nhanh thanh thoát, không nút trùng lặp */}
          {onQuickSearchChange && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                onQuickSearchSubmit?.();
              }}
              className="hidden min-h-[40px] shrink-0 items-center gap-2 rounded-full bg-[#FFF8F0] px-4 py-1.5 shadow-[0_4px_14px_rgba(24,21,18,0.05)] transition focus-within:ring-2 focus-within:ring-[#B4490E] sm:flex sm:w-56 lg:w-60 xl:w-64"
            >
              <Search
                className="h-3.5 w-3.5 shrink-0 text-[#6B5E52]"
                aria-hidden="true"
              />
              <input
                type="search"
                value={quickSearchQuery}
                onChange={(e) => onQuickSearchChange(e.target.value)}
                placeholder="Tìm món ăn..."
                aria-label="Tìm nhanh công thức trên thanh đầu trang"
                className="w-full border-0 bg-transparent p-0 text-[13px] text-[#181512] placeholder:text-[#6B5E52] focus:outline-none focus:ring-0"
              />
              {quickSearchQuery.length > 0 && (
                <button
                  type="button"
                  aria-label="Xóa tìm nhanh"
                  onClick={() => onQuickSearchChange('')}
                  className="inline-flex h-5 w-5 items-center justify-center rounded-full text-[#595047] hover:text-[#181512]"
                >
                  <X className="h-3 w-3" aria-hidden="true" />
                </button>
              )}
            </form>
          )}
        </div>

        {/* Thanh điều hướng 2 cột cân đối cho Mobile & Tablet (< lg) */}
        <nav
          aria-label="Điều hướng di động"
          className="grid grid-cols-2 border-y border-[#CDB9A2]/80 px-2 lg:hidden"
        >
          <button
            type="button"
            aria-current={activeTab === 'catalog' ? 'page' : undefined}
            onClick={() => onTabChange('catalog')}
            className={`relative flex min-h-[44px] items-center justify-center px-2 text-center font-serif text-[15px] transition ${
              activeTab === 'catalog'
                ? 'font-bold text-[#181512]'
                : 'font-medium text-[#4A4037]'
            }`}
          >
            <span>Khám phá công thức</span>
            {activeTab === 'catalog' && (
              <span className="absolute bottom-0 left-6 right-6 h-[2px] rounded-full bg-[#B4490E]" />
            )}
          </button>

          <button
            type="button"
            aria-current={isKitchenStudio ? 'page' : undefined}
            onClick={() => onTabChange('kitchen')}
            className={`relative flex min-h-[44px] items-center justify-center gap-1.5 px-2 text-center font-serif text-[15px] tabular-nums transition ${
              isKitchenStudio
                ? 'font-bold text-[#181512]'
                : 'font-medium text-[#4A4037]'
            }`}
          >
            <span>Gợi ý từ tủ bếp</span>
            {selectedMainCount > 0 && (
              <span className="inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-[#B4490E] px-1.5 font-sans text-[11px] font-bold text-white">
                {selectedMainCount}
              </span>
            )}
            {isKitchenStudio && (
              <span className="absolute bottom-0 left-6 right-6 h-[2px] rounded-full bg-[#B4490E]" />
            )}
          </button>
        </nav>
      </header>

      {/* Nội dung chính */}
      <main className="relative z-10 mx-auto max-w-7xl px-4 pb-16 pt-3 sm:px-6 lg:px-8">
        {children}
      </main>

      {/* FOOTER BIÊN TẬP TỐI GIẢN (Không hộp thừa, không nút mạng xã hội giả) */}
      <footer className="relative z-10 border-t border-[#CDB9A2]">
        <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 gap-8 md:grid-cols-12">
            <div className="md:col-span-5">
              <span className="font-serif text-[22px] font-bold tracking-tight text-[#B4490E]">
                FoodVision
              </span>
              <p className="mt-2.5 max-w-[42ch] text-[13px] leading-relaxed text-[#4A4037]">
                Trợ lý bếp thông minh giúp gia đình Việt tận dụng nguyên liệu
                sẵn có trong tủ lạnh và lên thực đơn tròn vị mỗi ngày.
              </p>
            </div>

            <div className="md:col-span-3">
              <h3 className="font-serif text-[16px] font-bold text-[#181512]">
                Điều hướng
              </h3>
              <ul className="mt-2 space-y-1 text-[13px] text-[#4A4037]">
                <li>
                  <button
                    type="button"
                    onClick={() => onTabChange('catalog')}
                    className="inline-flex min-h-[34px] items-center transition hover:text-[#B4490E]"
                  >
                    Khám phá công thức
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => onTabChange('kitchen')}
                    className="inline-flex min-h-[34px] items-center transition hover:text-[#B4490E]"
                  >
                    Gợi ý từ tủ bếp
                  </button>
                </li>
              </ul>
            </div>

            <div className="md:col-span-4">
              <h3 className="font-serif text-[16px] font-bold text-[#181512]">
                Nguyên tắc minh bạch
              </h3>
              <p className="mt-2.5 text-[13px] leading-relaxed text-[#4A4037]">
                Chỉ truy xuất công thức đã kiểm duyệt định lượng, tự động đối
                chiếu 5 gia vị cơ bản và tuân thủ miễn trừ dinh dưỡng an toàn
                (BR-03).
              </p>
            </div>
          </div>

          <div className="mt-8 flex flex-col items-center justify-between gap-2 border-t border-[#CDB9A2]/70 pt-5 text-[12px] text-[#595047] sm:flex-row">
            <span>© 2026 FoodVision AI.</span>
            <span>Dữ liệu công thức kiểm duyệt · Chính sách BR-03</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
