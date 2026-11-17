import React from 'react';
import {
  ChefHat,
  Globe,
  Mail,
  Share2,
  Sparkles,
} from 'lucide-react';
import { BotanicalDecor } from './BotanicalDecor';

export type ActiveTab = 'catalog' | 'kitchen' | 'recommendations';

export interface AppLayoutProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  selectedMainCount: number;
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  activeTab,
  onTabChange,
  selectedMainCount,
  children,
}) => {
  return (
    <div className="relative min-h-screen overflow-x-hidden bg-[#E8D8C6] text-[#181512]">
      {/* Đường cong & nhánh thảo mộc nét mảnh nền chuẩn NEWTASTE */}
      <BotanicalDecor
        variant="header-arcs"
        className="pointer-events-none absolute left-0 top-0 h-44 w-72 text-[#A7927A]/45"
      />
      <BotanicalDecor
        variant="rosemary"
        className="pointer-events-none fixed -left-8 top-1/3 hidden h-56 w-56 text-[#9A856E]/20 xl:block"
      />
      <BotanicalDecor
        variant="basil"
        className="pointer-events-none fixed -right-10 bottom-24 hidden h-60 w-60 text-[#9A856E]/20 xl:block"
      />

      {/* HEADER CHUẨN NEWTASTE */}
      <header className="relative z-10 bg-transparent">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-6 sm:px-6 lg:px-8">
          {/* Trái: Biểu tượng đầu bếp nét mảnh & Logo serif David Libre */}
          <button
            type="button"
            onClick={() => onTabChange('catalog')}
            className="inline-flex shrink-0 items-center gap-2.5 whitespace-nowrap text-left transition hover:opacity-90 focus:outline-none"
          >
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-tl-[14px] rounded-br-[14px] rounded-tr-[4px] rounded-bl-[4px] border border-[#EA6D27]/50 bg-[#FFF8F0]/75 text-[#C65112]">
              <ChefHat className="h-5 w-5 stroke-[1.75]" aria-hidden="true" />
            </span>
            <span className="font-serif text-[26px] font-bold tracking-tight text-[#C65112] sm:text-[30px]">
              FoodVision
            </span>
          </button>

          {/* Giữa: Điều hướng Serif thanh lịch chuẩn NEWTASTE (chỉ bung full nav từ lg 1024px để tránh chồng/xuống dòng ở tablet 768px) */}
          <nav
            aria-label="Điều hướng chính"
            className="hidden items-center gap-6 lg:flex xl:gap-8"
          >
            <button
              type="button"
              data-testid="nav-tab-catalog"
              aria-current={activeTab === 'catalog' ? 'page' : undefined}
              onClick={() => onTabChange('catalog')}
              className={`relative inline-flex min-h-[38px] shrink-0 items-center whitespace-nowrap py-1.5 font-serif text-[16px] font-medium transition ${
                activeTab === 'catalog'
                  ? 'font-bold text-[#9E3D08]'
                  : 'text-[#181512] hover:text-[#9E3D08]'
              }`}
            >
              Tra cứu công thức
              {activeTab === 'catalog' && (
                <span className="absolute -bottom-0.5 left-0 right-0 h-[2px] rounded-full bg-[#EA6D27]" />
              )}
            </button>

            <button
              type="button"
              data-testid="nav-tab-kitchen"
              aria-current={activeTab === 'kitchen' ? 'page' : undefined}
              onClick={() => onTabChange('kitchen')}
              className={`relative inline-flex min-h-[38px] shrink-0 items-center gap-2 whitespace-nowrap py-1.5 font-serif text-[16px] font-medium transition ${
                activeTab === 'kitchen'
                  ? 'font-bold text-[#9E3D08]'
                  : 'text-[#181512] hover:text-[#9E3D08]'
              }`}
            >
              <span>Chọn nguyên liệu &amp; Bếp</span>
              {selectedMainCount > 0 && (
                <span
                  data-testid="nav-selected-badge"
                  className="inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-[#C65112] px-1.5 font-sans text-[11px] font-bold text-white tabular-nums"
                >
                  {selectedMainCount}
                </span>
              )}
              {activeTab === 'kitchen' && (
                <span className="absolute -bottom-0.5 left-0 right-0 h-[2px] rounded-full bg-[#EA6D27]" />
              )}
            </button>

            <button
              type="button"
              data-testid="nav-tab-recommendations"
              aria-current={
                activeTab === 'recommendations' ? 'page' : undefined
              }
              onClick={() => onTabChange('recommendations')}
              className={`relative inline-flex min-h-[38px] shrink-0 items-center whitespace-nowrap py-1.5 font-serif text-[16px] font-medium transition ${
                activeTab === 'recommendations'
                  ? 'font-bold text-[#9E3D08]'
                  : 'text-[#181512] hover:text-[#9E3D08]'
              }`}
            >
              Gợi ý món ăn
              {activeTab === 'recommendations' && (
                <span className="absolute -bottom-0.5 left-0 right-0 h-[2px] rounded-full bg-[#EA6D27]" />
              )}
            </button>
          </nav>

          {/* Phải: Cặp nút cắt chéo chiếc lá Đen Espresso + Cam Persimmon */}
          <div className="flex shrink-0 items-center gap-2.5">
            <button
              type="button"
              onClick={() => onTabChange('kitchen')}
              className="hidden min-h-[40px] items-center justify-center whitespace-nowrap rounded-tl-[12px] rounded-br-[12px] rounded-tr-[4px] rounded-bl-[4px] bg-[#181512] px-4 py-2 text-xs font-semibold text-[#FFF8F0] shadow-[0_6px_16px_rgba(24,21,18,0.16)] transition hover:bg-[#2E2720] sm:inline-flex tabular-nums"
            >
              Tủ bếp{selectedMainCount > 0 ? ` (${selectedMainCount})` : ''}
            </button>

            <button
              type="button"
              onClick={() => onTabChange('recommendations')}
              title="Mở danh sách gợi ý món ăn phù hợp với gian bếp"
              aria-label="Mở gợi ý món ăn"
              className="inline-flex min-h-[40px] items-center justify-center gap-1.5 whitespace-nowrap rounded-tl-[12px] rounded-br-[12px] rounded-tr-[4px] rounded-bl-[4px] bg-[#C65112] px-3.5 py-2 text-xs font-semibold text-white shadow-[0_6px_16px_rgba(198,81,18,0.22)] transition hover:bg-[#A8430D]"
            >
              <Sparkles className="h-4 w-4 shrink-0" aria-hidden="true" />
              <span className="hidden sm:inline">Gợi ý món</span>
            </button>
          </div>
        </div>

        {/* Thanh điều hướng gọn 1 hàng cân đối trên thiết bị di động & tablet (< lg) */}
        <nav
          aria-label="Điều hướng di động"
          className="grid grid-cols-3 border-t border-[#D8C6B2] px-2 lg:hidden"
        >
          <button
            type="button"
            aria-current={activeTab === 'catalog' ? 'page' : undefined}
            onClick={() => onTabChange('catalog')}
            className={`relative flex min-h-[44px] items-center justify-center px-1 text-center font-serif text-[14px] transition ${
              activeTab === 'catalog'
                ? 'font-bold text-[#9E3D08]'
                : 'font-medium text-[#595047]'
            }`}
          >
            <span>Tra cứu</span>
            {activeTab === 'catalog' && (
              <span className="absolute bottom-0 left-3 right-3 h-[2px] rounded-full bg-[#EA6D27]" />
            )}
          </button>
          <button
            type="button"
            aria-current={activeTab === 'kitchen' ? 'page' : undefined}
            onClick={() => onTabChange('kitchen')}
            className={`relative flex min-h-[44px] items-center justify-center px-1 text-center font-serif text-[14px] tabular-nums transition ${
              activeTab === 'kitchen'
                ? 'font-bold text-[#9E3D08]'
                : 'font-medium text-[#595047]'
            }`}
          >
            <span>Tủ bếp ({selectedMainCount})</span>
            {activeTab === 'kitchen' && (
              <span className="absolute bottom-0 left-3 right-3 h-[2px] rounded-full bg-[#EA6D27]" />
            )}
          </button>
          <button
            type="button"
            aria-current={activeTab === 'recommendations' ? 'page' : undefined}
            onClick={() => onTabChange('recommendations')}
            className={`relative flex min-h-[44px] items-center justify-center px-1 text-center font-serif text-[14px] transition ${
              activeTab === 'recommendations'
                ? 'font-bold text-[#9E3D08]'
                : 'font-medium text-[#595047]'
            }`}
          >
            <span>Gợi ý món</span>
            {activeTab === 'recommendations' && (
              <span className="absolute bottom-0 left-3 right-3 h-[2px] rounded-full bg-[#EA6D27]" />
            )}
          </button>
        </nav>
      </header>

      {/* Nội dung chính */}
      <main className="relative z-10 mx-auto max-w-7xl px-4 pb-12 pt-2 sm:px-6 lg:px-8">
        {children}
      </main>

      {/* FOOTER 2 TẦNG CHUẨN NEWTASTE (#FFF8F0 trên nền #E8D8C6) */}
      <footer className="relative z-10 mt-14 px-4 pb-10 pt-2 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl rounded-b-[26px] rounded-t-[6px] border border-[#D8C6B2] bg-[#FFF8F0] px-6 py-9 shadow-[0_12px_34px_rgba(24,21,18,0.06)] sm:px-12 sm:py-11">
          {/* Tầng 1: 4 cột thoáng đãng */}
          <div className="grid grid-cols-1 gap-8 md:grid-cols-12">
            {/* Cột 1: Thương hiệu */}
            <div className="md:col-span-5">
              <div className="inline-flex items-center gap-2.5">
                <ChefHat
                  className="h-6 w-6 stroke-[1.75] text-[#C65112]"
                  aria-hidden="true"
                />
                <span className="font-serif text-[22px] font-bold tracking-tight text-[#C65112]">
                  FoodVision
                </span>
              </div>
              <p className="mt-3 max-w-[38ch] text-[13px] leading-relaxed text-[#595047]">
                FoodVision AI là trợ lý bếp thông minh giúp bạn khám phá công
                thức chuẩn vị và tận dụng tối đa nguyên liệu sẵn có mỗi ngày.
              </p>
            </div>

            {/* Cột 2: Điều hướng */}
            <div className="md:col-span-2">
              <h3 className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#181512]">
                ĐIỀU HƯỚNG
              </h3>
              <ul className="mt-3 space-y-1 text-[13px] text-[#595047]">
                <li>
                  <button
                    type="button"
                    onClick={() => onTabChange('catalog')}
                    className="inline-flex min-h-[34px] items-center transition hover:text-[#9E3D08]"
                  >
                    Tra cứu công thức
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => onTabChange('kitchen')}
                    className="inline-flex min-h-[34px] items-center transition hover:text-[#9E3D08]"
                  >
                    Tủ bếp nguyên liệu
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => onTabChange('recommendations')}
                    className="inline-flex min-h-[34px] items-center transition hover:text-[#9E3D08]"
                  >
                    Gợi ý món ăn
                  </button>
                </li>
              </ul>
            </div>

            {/* Cột 3: Món ngon tiêu biểu */}
            <div className="md:col-span-3">
              <h3 className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#181512]">
                MÓN NGON TIÊU BIỂU
              </h3>
              <ul className="mt-3.5 space-y-2.5 text-[13px] text-[#595047]">
                <li>Đậu hũ sốt cà chua</li>
                <li>Canh cà chua trứng</li>
                <li>Ức gà áp chảo sốt bơ tỏi</li>
                <li>Bò lúc lắc xào hành tây</li>
              </ul>
            </div>

            {/* Cột 4: Kết nối */}
            <div className="md:col-span-2">
              <h3 className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#181512]">
                KẾT NỐI
              </h3>
              <div className="mt-3.5 flex items-center gap-2.5">
                <a
                  href="#top"
                  aria-label="Cộng đồng FoodVision"
                  onClick={(e) => {
                    e.preventDefault();
                    onTabChange('catalog');
                  }}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-[#181512] text-[#181512] transition hover:border-[#C65112] hover:text-[#C65112]"
                >
                  <Globe className="h-4 w-4 stroke-[1.75]" aria-hidden="true" />
                </a>
                <a
                  href="#kitchen"
                  aria-label="Chia sẻ công thức FoodVision"
                  onClick={(e) => {
                    e.preventDefault();
                    onTabChange('kitchen');
                  }}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-[#181512] text-[#181512] transition hover:border-[#C65112] hover:text-[#C65112]"
                >
                  <Share2 className="h-4 w-4 stroke-[1.75]" aria-hidden="true" />
                </a>
                <span
                  aria-label="Hỗ trợ qua thư điện tử"
                  className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-[#181512] text-[#181512]"
                >
                  <Mail className="h-4 w-4 stroke-[1.75]" aria-hidden="true" />
                </span>
              </div>
            </div>
          </div>

          {/* Tầng 2: Bản quyền & Pháp lý */}
          <div className="mt-8 flex flex-col items-center justify-between gap-3 border-t border-[#E4D5C3] pt-6 text-[12px] text-[#595047] sm:flex-row">
            <span>© 2026 FoodVision AI. Bảo lưu mọi quyền.</span>
            <div className="flex flex-wrap items-center gap-6">
              <span>Miễn trừ dinh dưỡng (BR-03)</span>
              <span>Giấy phép nội dung</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
