import React from 'react';
import { BotanicalDecor } from '../../../shared/components/BotanicalDecor';

export interface QuickStarterPreset {
  id: string;
  label: string;
  slugs: string[];
}

export const HERO_STARTER_PRESETS: QuickStarterPreset[] = [
  {
    id: 'tofu-tomato',
    label: 'Đậu hũ · Cà chua',
    slugs: ['dau-hu', 'ca-chua', 'hanh-la'],
  },
  {
    id: 'egg-soup',
    label: 'Trứng gà · Cà chua',
    slugs: ['trung-ga', 'ca-chua', 'hanh-la'],
  },
  {
    id: 'beef-onion',
    label: 'Thịt bò · Hành tây',
    slugs: ['thit-bo', 'hanh-tay', 'toi'],
  },
];

export interface NewtasteHeroProps {
  onOpenKitchen: () => void;
  onApplyPreset?: (slugs: string[]) => void;
}

export const NewtasteHero: React.FC<NewtasteHeroProps> = ({
  onOpenKitchen,
  onApplyPreset,
}) => {
  const handleScrollToCatalog = () => {
    const el = document.getElementById('special-recipes');
    if (el && typeof el.scrollIntoView === 'function') {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <section
      aria-label="Giới thiệu FoodVision AI"
      className="relative pb-10 pt-2 sm:pb-14 sm:pt-4"
    >
      <div className="grid grid-cols-1 items-center gap-10 lg:grid-cols-12 lg:gap-8">
        {/* Cột trái: Typography thuần khiết, không icon trang trí thừa */}
        <div className="lg:col-span-6">
          <h1 className="max-w-[16ch] font-serif text-[34px] font-bold leading-[1.12] tracking-[-0.02em] text-[#181512] sm:text-[44px] lg:text-[48px]">
            Biến nguyên liệu sẵn có thành bữa ngon tròn vị
          </h1>

          <p className="mt-4 max-w-[54ch] text-[15px] leading-relaxed text-[#4A4037]">
            Nhập vài nguyên liệu đang có trong tủ lạnh, FoodVision AI tự động
            đối chiếu gia vị bếp và xếp hạng ngay những món bạn nấu được liền
            hôm nay.
          </p>

          <div className="mt-7 flex flex-wrap items-center gap-3.5">
            <button
              type="button"
              onClick={handleScrollToCatalog}
              className="inline-flex min-h-[44px] items-center justify-center rounded-tl-[14px] rounded-br-[14px] rounded-tr-[4px] rounded-bl-[4px] bg-[#181512] px-6 py-2.5 text-[13.5px] font-semibold text-[#FFF8F0] shadow-[0_10px_24px_rgba(24,21,18,0.16)] transition hover:bg-[#2E2720]"
            >
              Khám phá thực đơn
            </button>

            <button
              type="button"
              data-testid="hero-open-kitchen-btn"
              onClick={onOpenKitchen}
              className="inline-flex min-h-[44px] items-center justify-center rounded-tl-[14px] rounded-br-[14px] rounded-tr-[4px] rounded-bl-[4px] bg-[#B4490E] px-6 py-2.5 text-[13.5px] font-semibold text-white shadow-[0_10px_24px_rgba(180,73,14,0.22)] transition hover:bg-[#963B0A]"
            >
              Chọn nguyên liệu sẵn có
            </button>
          </div>

          {onApplyPreset && (
            <div className="mt-6 flex flex-wrap items-center gap-2">
              <span className="text-[12.5px] text-[#595047]">Thử nhanh:</span>
              {HERO_STARTER_PRESETS.map((preset) => (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => onApplyPreset(preset.slugs)}
                  className="inline-flex min-h-[34px] items-center rounded-full bg-[#EFE2D2] px-3.5 py-1 text-[12px] font-medium text-[#3B3027] transition hover:bg-[#FFF8F0] hover:text-[#B4490E]"
                >
                  {preset.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Cột phải: Bộ 3 khung ảnh ẩm thực cắt lá xếp lớp đặc trưng từ trang bìa NEWTASTE */}
        <div className="relative mx-auto w-full max-w-[540px] lg:col-span-6">
          <BotanicalDecor
            variant="rosemary"
            className="pointer-events-none absolute -right-6 -top-8 h-28 w-28 text-[#8B7660]/40"
          />
          <BotanicalDecor
            variant="basil"
            className="pointer-events-none absolute -bottom-8 right-2 h-32 w-32 text-[#8B7660]/35"
          />

          <div className="relative z-10 grid grid-cols-12 items-center gap-2.5 sm:gap-3.5">
            <div className="col-span-3 -mr-3 overflow-hidden rounded-tl-[24px] rounded-br-[24px] rounded-tr-[6px] rounded-bl-[6px] bg-[#181512] shadow-[0_14px_30px_rgba(24,21,18,0.16)]">
              <img
                src="https://images.unsplash.com/photo-1547592166-23ac45744acd?auto=format&fit=crop&w=500&q=80"
                alt="Canh cà chua trứng thanh nhẹ"
                className="aspect-[3/5] h-full w-full object-cover opacity-95"
              />
            </div>

            <div className="relative z-20 col-span-6 overflow-hidden rounded-tl-[34px] rounded-br-[34px] rounded-tr-[8px] rounded-bl-[8px] bg-[#181512] ring-4 ring-[#E8D8C6] shadow-[0_22px_48px_rgba(24,21,18,0.22)]">
              <img
                src="https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=800&q=80"
                alt="Bàn tiệc món Việt ấm cúng"
                className="aspect-[4/5] h-full w-full object-cover"
              />
            </div>

            <div className="col-span-3 -ml-3 overflow-hidden rounded-tl-[24px] rounded-br-[24px] rounded-tr-[6px] rounded-bl-[6px] bg-[#181512] shadow-[0_14px_30px_rgba(24,21,18,0.16)]">
              <img
                src="https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=500&q=80"
                alt="Salad rau củ tươi mát"
                className="aspect-[3/5] h-full w-full object-cover opacity-95"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
