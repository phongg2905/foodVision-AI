import React from 'react';
import { Menu, ArrowRight, ExternalLink, UtensilsCrossed } from 'lucide-react';

export type ActiveTab = 'catalog' | 'kitchen';

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
    <div className="min-h-screen overflow-x-hidden bg-[#EFE6D8] text-[#181512]">
      {/* MỤC 1A — Website Header (Bố cục Fodium + Màu & Chữ của web-6-newtaste-recipe-website.jpg) */}
      <header className="bg-[#EFE6D8]">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-6 sm:px-6 lg:px-8">
          {/* Trái: Logo Serif chữ Cam Spiced Orange (#E87838) */}
          <button
            type="button"
            onClick={() => onTabChange('catalog')}
            className="text-left focus:outline-none"
          >
            <span className="font-serif text-[28px] font-bold tracking-tight text-[#E87838] transition hover:opacity-90 sm:text-[32px]">
              FoodVision
            </span>
          </button>

          {/* Giữa: Menu chữ thoáng, gạch chân cam #E87838 ở mục đang chọn (giống Home trong New Taste) */}
          <nav
            aria-label="Điều hướng chính"
            className="hidden items-center gap-10 md:flex"
          >
            <button
              type="button"
              data-testid="nav-tab-catalog"
              aria-current={activeTab === 'catalog' ? 'page' : undefined}
              onClick={() => onTabChange('catalog')}
              className={`relative py-1 text-[12px] font-semibold uppercase tracking-[0.16em] transition ${
                activeTab === 'catalog'
                  ? 'text-[#E87838]'
                  : 'text-[#181512] hover:text-[#E87838]'
              }`}
            >
              Tra cứu công thức
              {activeTab === 'catalog' && (
                <span className="absolute -bottom-1 left-0 right-0 h-[2px] rounded-full bg-[#E87838]" />
              )}
            </button>

            <button
              type="button"
              data-testid="nav-tab-kitchen"
              aria-current={activeTab === 'kitchen' ? 'page' : undefined}
              onClick={() => onTabChange('kitchen')}
              className={`relative inline-flex items-center gap-2 py-1 text-[12px] font-semibold uppercase tracking-[0.16em] transition ${
                activeTab === 'kitchen'
                  ? 'text-[#E87838]'
                  : 'text-[#181512] hover:text-[#E87838]'
              }`}
            >
              <span>Chọn nguyên liệu &amp; Bếp</span>
              {selectedMainCount > 0 && (
                <span
                  data-testid="nav-selected-badge"
                  className="inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-[#E87838] px-1.5 text-[10px] font-bold tracking-normal text-white tabular-nums"
                >
                  {selectedMainCount}
                </span>
              )}
              {activeTab === 'kitchen' && (
                <span className="absolute -bottom-1 left-0 right-0 h-[2px] rounded-full bg-[#E87838]" />
              )}
            </button>
          </nav>

          {/* Phải: Nút đen Espresso (#181512) + Nút vuông cam (#E87838) đồng điệu với cặp nút Discover / Create Recipe của New Taste */}
          <div className="flex items-center gap-2.5">
            <button
              type="button"
              onClick={() => onTabChange('kitchen')}
              className="hidden items-center justify-center rounded-lg bg-[#181512] px-5 py-2.5 text-xs font-semibold text-white shadow-sm transition hover:bg-[#2E2924] sm:inline-flex"
            >
              Tủ bếp{selectedMainCount > 0 ? ` (${selectedMainCount})` : ''}
            </button>

            <button
              type="button"
              onClick={() =>
                onTabChange(activeTab === 'catalog' ? 'kitchen' : 'catalog')
              }
              title="Chuyển nhanh chế độ Tra cứu / Tủ bếp"
              aria-label="Chuyển chế độ hiển thị"
              className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-[#E87838] text-white shadow-sm transition hover:bg-[#D16426]"
            >
              <Menu className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </div>

        {/* Thanh điều hướng rút gọn trên màn hình nhỏ (Mobile) */}
        <div className="flex items-center justify-center gap-6 border-t border-[#DFD3C3] py-2.5 md:hidden">
          <button
            type="button"
            onClick={() => onTabChange('catalog')}
            className={`text-[11px] font-semibold uppercase tracking-[0.15em] ${
              activeTab === 'catalog' ? 'text-[#E87838]' : 'text-[#6E655C]'
            }`}
          >
            Tra cứu công thức
          </button>
          <button
            type="button"
            onClick={() => onTabChange('kitchen')}
            className={`text-[11px] font-semibold uppercase tracking-[0.15em] ${
              activeTab === 'kitchen' ? 'text-[#E87838]' : 'text-[#6E655C]'
            }`}
          >
            Chọn nguyên liệu ({selectedMainCount})
          </button>
        </div>
      </header>

      {/* Nội dung chính */}
      <main className="mx-auto max-w-7xl px-4 pb-12 pt-2 sm:px-6 lg:px-8">
        {children}
      </main>

      {/* MỤC 1B — Website Footer (Bố cục 3 tầng web-footer-6 nổi bật trên nền kem hạnh nhân #EFE6D8 của New Taste) */}
      <footer className="mt-16 px-4 pb-12 pt-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl rounded-[28px] border border-[#DFD3C3] bg-white px-6 py-10 shadow-[0_14px_40px_rgba(24,21,18,0.05)] sm:px-12 sm:py-12">
          {/* Tầng 1: Cột giới thiệu bên trái + 3 cột liên kết có tiêu đề gạch chân */}
          <div className="grid grid-cols-1 gap-10 pb-10 md:grid-cols-12">
            <div className="md:col-span-4">
              <h3 className="font-serif text-[16px] font-bold text-[#181512]">
                Về chúng tôi
              </h3>
              <p className="mt-3 max-w-xs text-[13px] leading-relaxed text-[#6E655C]">
                FoodVision AI là nền tảng tra cứu công thức nấu ăn và gợi ý món
                ngon thông minh từ nguyên liệu sẵn có trong gian bếp gia đình
                Việt.
              </p>
              <div className="mt-6">
                <h4 className="font-serif text-[15px] font-bold text-[#181512]">
                  Liên hệ
                </h4>
                <p className="mt-1.5 text-[13px] text-[#6E655C]">
                  hello@foodvision.ai
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-8 sm:grid-cols-3 md:col-span-8">
              <div>
                <h4 className="inline-block border-b-[1.5px] border-[#181512] pb-0.5 font-serif text-[15px] font-bold text-[#181512]">
                  Khám phá Bếp
                </h4>
                <ul className="mt-4 space-y-3 text-[13px] text-[#6E655C]">
                  <li>
                    <button
                      type="button"
                      onClick={() => onTabChange('catalog')}
                      className="font-medium text-[#E87838] transition hover:underline"
                    >
                      Danh mục Công thức
                    </button>
                  </li>
                  <li>
                    <button
                      type="button"
                      onClick={() => onTabChange('kitchen')}
                      className="transition hover:text-[#181512]"
                    >
                      Tìm kiếm Nguyên liệu
                    </button>
                  </li>
                  <li>
                    <button
                      type="button"
                      onClick={() => onTabChange('kitchen')}
                      className="transition hover:text-[#181512]"
                    >
                      Gia vị Cơ bản trong Bếp
                    </button>
                  </li>
                  <li>
                    <button
                      type="button"
                      onClick={() => onTabChange('kitchen')}
                      className="inline-flex items-center gap-1.5 font-medium text-[#E87838] transition hover:underline"
                    >
                      <span>Gợi ý Món ăn</span>
                      <ExternalLink className="h-3 w-3" aria-hidden="true" />
                    </button>
                  </li>
                </ul>
              </div>

              <div>
                <h4 className="inline-block border-b-[1.5px] border-[#181512] pb-0.5 font-serif text-[15px] font-bold text-[#181512]">
                  Nền Ẩm thực
                </h4>
                <ul className="mt-4 space-y-3 text-[13px] text-[#6E655C]">
                  <li>Ẩm thực Việt Nam</li>
                  <li>Ẩm thực Châu Âu</li>
                  <li>Ẩm thực Hiện đại</li>
                  <li className="inline-flex items-center gap-1.5 font-medium text-[#E87838]">
                    <span>Bộ sưu tập Theo mùa</span>
                    <ExternalLink className="h-3 w-3" aria-hidden="true" />
                  </li>
                </ul>
              </div>

              <div>
                <h4 className="inline-block border-b-[1.5px] border-[#181512] pb-0.5 font-serif text-[15px] font-bold text-[#181512]">
                  Món Ngon Nổi Bật
                </h4>
                <ul className="mt-4 space-y-3 text-[13px] text-[#6E655C]">
                  <li>Canh cà chua trứng</li>
                  <li>Đậu hũ nhồi thịt sốt cà</li>
                  <li>Bò lúc lắc xào hành tây</li>
                  <li>Salad dưa leo cà chua</li>
                  <li>Ức gà áp chảo sốt bơ tỏi</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Tầng 2: Logo + Lời mời nhận bản tin + Ô nhập Email & Nút Pill cam #E87838 */}
          <div className="flex flex-col gap-5 border-t border-[#EFECE6] py-8 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-3">
              <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-[#E87838] text-white">
                <UtensilsCrossed className="h-4 w-4" aria-hidden="true" />
              </span>
              <span className="font-serif text-[20px] font-bold tracking-tight text-[#181512]">
                FoodVision
              </span>
            </div>

            <p className="max-w-md text-[15px] font-medium leading-snug text-[#181512]">
              Nhận thực đơn công thức món ngon hàng tuần dành riêng cho gian bếp
              của bạn.
            </p>

            <div className="flex flex-col gap-2.5 sm:flex-row sm:items-center">
              <input
                type="email"
                placeholder="Email của bạn*"
                aria-label="Email đăng ký nhận công thức"
                className="rounded-full border border-[#DFD3C3] bg-[#FAF7F2] px-5 py-2.5 text-[13px] text-[#181512] placeholder:text-[#9A9086] focus:border-[#E87838] focus:outline-none sm:w-60"
              />
              <button
                type="button"
                className="inline-flex items-center justify-center gap-2 rounded-full bg-[#E87838] px-6 py-2.5 text-[13px] font-semibold text-white transition hover:bg-[#D16426]"
              >
                <span>Đăng ký miễn phí</span>
                <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
              </button>
            </div>
          </div>

          {/* Tầng 3: Bản quyền + Điều khoản + 3 nút tròn mạng xã hội */}
          <div className="flex flex-col items-center justify-between gap-4 border-t border-[#EFECE6] pt-7 text-[11px] text-[#6E655C] sm:flex-row">
            <span className="tracking-wide">
              ©2026 FOODVISION AI. ALL RIGHTS RESERVED.
            </span>

            <div className="flex items-center gap-7 text-[12px] font-medium text-[#181512]">
              <span>Điều khoản</span>
              <span>Bảo mật</span>
              <span>Cookies</span>
            </div>

            <div className="flex items-center gap-2.5">
              {['in', 'f', '𝕏'].map((social) => (
                <span
                  key={social}
                  className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-[#DFD3C3] text-[11px] font-semibold text-[#181512] transition hover:border-[#E87838] hover:text-[#E87838]"
                >
                  {social}
                </span>
              ))}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
