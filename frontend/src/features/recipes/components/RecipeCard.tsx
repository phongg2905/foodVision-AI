import React, { useState } from 'react';
import { ArrowRight, Utensils } from 'lucide-react';
import { CuisineCode, RecipeSummary } from '../../../shared/api/types';

export interface RecipeCardProps {
  recipe: RecipeSummary;
  onSelectRecipe?: (recipeId: string) => void;
}

const CUISINE_DESC_MAP: Record<CuisineCode, string> = {
  VN: 'Hương vị truyền thống Việt Nam đậm đà, nguyên liệu tươi ngon dễ chuẩn bị',
  EU: 'Phong cách ẩm thực Châu Âu thanh lịch, cân bằng dinh dưỡng và tinh tế',
  US: 'Phong cách ẩm thực hiện đại, giàu năng lượng và chế biến nhanh gọn',
};

export const RecipeCard: React.FC<RecipeCardProps> = ({
  recipe,
  onSelectRecipe,
}) => {
  const [imageError, setImageError] = useState(false);

  const descriptionText = `${CUISINE_DESC_MAP[recipe.cuisine_code]}, hoàn thiện nhanh trong ${recipe.total_minutes} phút (sơ chế ${recipe.prep_minutes}p, nấu ${recipe.cook_minutes}p).`;

  return (
    <article
      data-testid={`recipe-card-${recipe.slug}`}
      className="group relative flex flex-col items-center pt-14"
    >
      {/* MỤC 2 — Đĩa món ăn hình tròn nổi chồng lên nửa trên của thẻ (NEWTASTE) */}
      <div className="relative z-10 -mb-14 h-32 w-32 shrink-0 overflow-hidden rounded-full border-4 border-white bg-[#181512] shadow-[0_12px_28px_rgba(24,21,18,0.18)] transition duration-300 group-hover:scale-105 sm:h-36 sm:w-36">
        {recipe.cover_image_url && !imageError ? (
          <img
            src={recipe.cover_image_url}
            alt={recipe.name_vi}
            loading="lazy"
            onError={() => setImageError(true)}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full flex-col items-center justify-center gap-1 bg-[#2A2421] text-[#E87838]">
            <Utensils className="h-6 w-6" aria-hidden="true" />
            <span className="font-serif text-[10px] font-bold">New Taste</span>
          </div>
        )}
      </div>

      {/* Thân thẻ trắng bo góc bất đối xứng */}
      <div className="relative flex w-full flex-1 flex-col items-center justify-between rounded-bl-[12px] rounded-br-[30px] rounded-tl-[30px] rounded-tr-[12px] border border-[#E6DACB] bg-white px-5 pb-7 pt-16 text-center shadow-[0_10px_26px_rgba(24,21,18,0.05)] transition duration-200 group-hover:-translate-y-1 group-hover:shadow-[0_16px_34px_rgba(24,21,18,0.09)] sm:pt-20">
        <div>
          <h3 className="line-clamp-2 font-serif text-[16px] font-bold leading-snug text-[#181512] transition group-hover:text-[#E87838]">
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

          <p className="mt-2.5 line-clamp-3 text-[12px] leading-relaxed text-[#6E655C]">
            {descriptionText}
          </p>
        </div>

        <div className="mt-3 flex flex-col items-center gap-1.5">
          <p className="text-[11px] font-semibold tabular-nums text-[#C2591B]">
            {recipe.total_minutes} phút • Sơ chế {recipe.prep_minutes}p
          </p>

          {onSelectRecipe && (
            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-[#181512] opacity-80 transition group-hover:text-[#E87838] group-hover:opacity-100">
              <span>Xem công thức</span>
              <ArrowRight className="h-3 w-3" aria-hidden="true" />
            </span>
          )}
        </div>
      </div>
    </article>
  );
};
