import React, { useState } from 'react';
import { CuisineCode, RecipeSummary } from '../../../shared/api/types';
import { resolveRecipeCoverUrl } from '../../../shared/utils/recipeCover';

export interface RecipeCardProps {
  recipe: RecipeSummary;
  onSelectRecipe?: (recipeId: string) => void;
}

const RECIPE_BLURB_BY_SLUG: Record<string, string> = {
  'canh-ca-chua-trung':
    'Canh nóng thanh nhẹ với vân trứng mềm tơi và vị chua dịu từ cà chua chín.',
  'dau-hu-sot-ca-chua':
    'Đậu hũ chiên vàng ngoài giòn trong mềm quyện sốt cà chua sánh đậm đưa cơm.',
  'thit-kho-trung':
    'Thịt ba chỉ kho mềm đậm vị nước mắm truyền thống cùng trứng gà béo bùi.',
  'trung-xao-ca-chua':
    'Trứng gà đảo tơi mềm quyện sốt cà chua mọng ngọt, hoàn thiện nhanh trong 15 phút.',
  'mi-y-sot-ca-chua-thit-bam':
    'Sợi mì Ý dai mềm áo đẫm sốt thịt bò băm cà chua ninh thơm kiểu Âu.',
  'bong-cai-xanh-nam-ap-chao-bo-toi':
    'Bông cải xanh giòn ngọt áp chảo cùng nấm tươi và bơ tỏi dậy hương.',
  'burger-bo-pho-mai-kieu-my':
    'Nhân bò băm áp chảo mọng nước phủ phô mai Cheddar tan chảy kẹp bánh mềm.',
  'bap-ngot-khoai-tay-dut-lo-bo-toi':
    'Khoai tây và hạt bắp ngọt đút lò vàng ươm quyện bơ lạt tỏi thơm.',
  'bo-xao-ot-chuong-hanh-tay':
    'Thịt bò áp chảo lửa lớn săn mềm bên ngoài, mọng ngọt bên trong với ớt chuông hành tây.',
  'bap-ngot-ap-chao-bo-toi-kieu-my':
    'Hạt bắp ngọt giòn đảo nhanh cùng bơ tỏi dậy mùi, béo nhẹ làm món ăn kèm.',
  'bo-xao-bong-cai-xanh-nam':
    'Thịt bò thái mỏng xào nhanh tay cùng bông cải xanh giòn và nấm ngọt tự nhiên.',
  'thit-heo-ham-khoai-tay-ca-rot':
    'Thịt heo hầm mềm ngọt nước cùng khoai tây bở bùi và cà rốt thanh dịu.',
};

const CUISINE_LABELS: Record<CuisineCode, string> = {
  VN: 'Món Việt',
  EU: 'Món Âu',
  US: 'Món Mỹ',
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
  const resolvedCoverUrl = resolveRecipeCoverUrl(
    recipe.slug,
    recipe.cover_image_url
  );

  const descriptionText =
    RECIPE_BLURB_BY_SLUG[recipe.slug] ??
    `${CUISINE_DESC_MAP[recipe.cuisine_code]}, hoàn thiện trọn vị trong ${recipe.total_minutes} phút.`;

  return (
    <article
      data-testid={`recipe-card-${recipe.slug}`}
      className="group relative flex flex-col items-center pt-16"
    >
      {/* Đĩa món ăn tròn lớn chồng lên đỉnh thẻ đồng bộ 100% với trang Gợi ý từ tủ bếp */}
      <div className="relative z-10 -mb-16 h-36 w-36 shrink-0 overflow-hidden rounded-full bg-[#181512] ring-4 ring-[#FFF8F0] shadow-[0_12px_26px_rgba(24,21,18,0.16)] transition duration-300 group-hover:scale-[1.03]">
        {resolvedCoverUrl && !imageError ? (
          <img
            src={resolvedCoverUrl}
            alt={recipe.name_vi}
            loading="lazy"
            onError={() => setImageError(true)}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-[#2A2421] font-serif text-xs font-bold text-[#EFE2D2]">
            FoodVision
          </div>
        )}
      </div>

      {/* Thân thẻ trắng kem #FFF8F0 căn lề trái thanh lịch chuẩn Mockup A */}
      <div className="relative flex w-full flex-1 flex-col justify-between rounded-tl-[26px] rounded-br-[26px] rounded-tr-[6px] rounded-bl-[6px] bg-[#FFF8F0] px-5 pb-5 pt-20 text-left shadow-[0_10px_28px_rgba(24,21,18,0.06)] transition duration-200 group-hover:-translate-y-1 group-hover:shadow-[0_16px_36px_rgba(24,21,18,0.1)]">
        <div>
          <h3 className="line-clamp-2 min-h-[3.2rem] font-serif text-[19px] font-bold leading-snug text-[#181512] transition group-hover:text-[#B4490E]">
            {onSelectRecipe ? (
              <button
                type="button"
                data-testid={`open-recipe-${recipe.slug}`}
                onClick={() => onSelectRecipe(recipe.id)}
                className="text-left after:absolute after:inset-0 after:content-[''] focus:outline-none"
              >
                {recipe.name_vi}
              </button>
            ) : (
              recipe.name_vi
            )}
          </h3>

          <p className="mt-1 text-[12.5px] font-medium tabular-nums text-[#595047]">
            {CUISINE_LABELS[recipe.cuisine_code]} · {recipe.total_minutes} phút
            (Sơ chế {recipe.prep_minutes}p)
          </p>

          <p className="mt-2 line-clamp-2 text-[13px] leading-relaxed text-[#4A4037]">
            {descriptionText}
          </p>
        </div>

        {onSelectRecipe && (
          <div className="mt-4 pt-1">
            <span className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-[#B4490E] transition group-hover:text-[#181512]">
              <span>Xem công thức</span>
              <span aria-hidden="true">→</span>
            </span>
          </div>
        )}
      </div>
    </article>
  );
};
