import React, { useState } from 'react';
import { ArrowRight, Utensils } from 'lucide-react';
import { CuisineCode, RecipeSummary } from '../../../shared/api/types';

export interface RecipeCardProps {
  recipe: RecipeSummary;
  onSelectRecipe?: (recipeId: string) => void;
}

const RECIPE_BLURB_BY_SLUG: Record<string, string> = {
  'canh-ca-chua-trung':
    'Canh nóng thanh nhẹ với vân trứng mềm tơi và vị chua dịu từ cà chua chín.',
  'dau-hu-sot-ca-chua':
    'Đậu hũ chiên vàng ngoài giòn trong mềm quyện sốt cà chua sánh đậm đưa cơm.',
  'thit-heo-kho-trung':
    'Thịt heo kho mềm đậm vị nước mắm truyền thống cùng trứng cút béo bùi.',
  'bo-luc-lac-hanh-tay':
    'Thịt bò áp chảo lửa lớn săn mềm bên ngoài, mọng ngọt bên trong với hành tây.',
  'salad-dua-leo-ca-chua-kieu-au':
    'Salad thanh mát phối dưa leo giòn, cà chua bi và sốt chanh tỏi cân vị.',
  'uc-ga-ap-chao-bo-toi':
    'Ức gà áp chảo vàng ươm áo lớp bơ tỏi thơm lừng, giữ trọn độ mềm mọng.',
  'bap-xao-bo-toi-kieu-my':
    'Hạt bắp ngọt giòn đảo nhanh cùng bơ tỏi dậy mùi, béo nhẹ làm món ăn kèm.',
  'tom-xao-bong-cai-xanh':
    'Tôm tươi săn ngọt xào giòn bông cải xanh, thanh đạm và giữ trọn sắc xanh.',
};

const CUISINE_DESC_MAP: Record<CuisineCode, string> = {
  VN: 'Hương vị cơm nhà Việt Nam hài hòa, nguyên liệu tươi ngon dễ chuẩn bị',
  EU: 'Phong cách ẩm thực Châu Âu thanh lịch, cân bằng dưỡng chất mỗi ngày',
  US: 'Phong cách chế biến hiện đại, gọn gàng và phù hợp bữa ăn bận rộn',
};

export const RecipeCard: React.FC<RecipeCardProps> = ({
  recipe,
  onSelectRecipe,
}) => {
  const [imageError, setImageError] = useState(false);

  const descriptionText =
    RECIPE_BLURB_BY_SLUG[recipe.slug] ??
    `${CUISINE_DESC_MAP[recipe.cuisine_code]}, hoàn thiện trọn vị trong ${recipe.total_minutes} phút.`;

  return (
    <article
      data-testid={`recipe-card-${recipe.slug}`}
      className="group relative flex flex-col items-center pt-14"
    >
      {/* Đĩa món ăn tròn nổi chồng lên nửa trên thẻ chuẩn NEWTASTE */}
      <div className="relative z-10 -mb-14 h-32 w-32 shrink-0 overflow-hidden rounded-full bg-[#181512] ring-4 ring-[#FFF8F0] shadow-[0_12px_28px_rgba(24,21,18,0.16)] transition duration-300 group-hover:scale-105 sm:h-36 sm:w-36">
        {recipe.cover_image_url && !imageError ? (
          <img
            src={recipe.cover_image_url}
            alt={recipe.name_vi}
            loading="lazy"
            onError={() => setImageError(true)}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full flex-col items-center justify-center gap-1 bg-[#2A2421] text-[#EA6D27]">
            <Utensils className="h-6 w-6" aria-hidden="true" />
            <span className="font-serif text-[11px] font-bold">FoodVision</span>
          </div>
        )}
      </div>

      {/* Thân thẻ trắng kem #FFF8F0 cắt chéo chiếc lá chuẩn NEWTASTE */}
      <div className="relative flex w-full flex-1 flex-col items-center justify-between rounded-tl-[28px] rounded-br-[28px] rounded-tr-[6px] rounded-bl-[6px] bg-[#FFF8F0] px-5 pb-6 pt-16 text-center shadow-[0_10px_28px_rgba(24,21,18,0.06)] transition duration-200 group-hover:-translate-y-1 group-hover:shadow-[0_16px_36px_rgba(24,21,18,0.1)] sm:pt-20">
        <div>
          <h3 className="line-clamp-2 min-h-[3rem] font-serif text-[19px] font-bold leading-snug text-[#181512] transition group-hover:text-[#9E3D08]">
            {onSelectRecipe ? (
              <button
                type="button"
                data-testid={`open-recipe-${recipe.slug}`}
                onClick={() => onSelectRecipe(recipe.id)}
                className="text-center after:absolute after:inset-0 after:content-[''] focus:outline-none"
              >
                {recipe.name_vi}
              </button>
            ) : (
              recipe.name_vi
            )}
          </h3>

          <p className="mt-2.5 line-clamp-3 text-[12px] leading-relaxed text-[#595047]">
            {descriptionText}
          </p>
        </div>

        <div className="mt-4 flex flex-col items-center gap-1.5">
          <p className="text-[12px] font-semibold tabular-nums text-[#9E3D08]">
            {recipe.total_minutes} phút · Sơ chế {recipe.prep_minutes}p
          </p>

          {onSelectRecipe && (
            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-[#181512] opacity-85 transition group-hover:text-[#9E3D08] group-hover:opacity-100">
              <span>Xem công thức</span>
              <ArrowRight className="h-3 w-3" aria-hidden="true" />
            </span>
          )}
        </div>
      </div>
    </article>
  );
};
