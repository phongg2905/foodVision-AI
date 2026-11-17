import React, { useState } from 'react';
import { ArrowRight, Check, ShoppingBasket, Utensils } from 'lucide-react';
import { getIngredientNameById } from '../../../shared/api/mockData';
import {
  CuisineCode,
  Ingredient,
  RecommendationItem,
} from '../../../shared/api/types';
import { formatScoreValue } from '../../../shared/utils/formatters';

export interface RecommendationCardProps {
  item: RecommendationItem;
  knownIngredients: Ingredient[];
  onSelectRecipe: (recipeId: string, item: RecommendationItem) => void;
}

const CUISINE_LABELS: Record<CuisineCode, string> = {
  VN: 'Món Việt',
  EU: 'Món Âu',
  US: 'Món Mỹ',
};

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  item,
  knownIngredients,
  onSelectRecipe,
}) => {
  const [imageError, setImageError] = useState(false);
  const { recipe } = item;
  const isReady = item.availability === 'ready';

  return (
    <article
      data-testid={`recommendation-card-${recipe.slug}`}
      className="group relative flex flex-col items-center pt-12 sm:pt-14"
    >
      {/* Đĩa món ăn tròn nổi chuẩn NEWTASTE */}
      <div className="relative z-10 -mb-12 h-28 w-28 shrink-0 overflow-hidden rounded-full bg-[#181512] ring-4 ring-[#FFF8F0] shadow-[0_12px_28px_rgba(24,21,18,0.16)] transition duration-300 group-hover:scale-105 sm:-mb-14 sm:h-32 sm:w-32">
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

      {/* Thân thẻ trắng kem #FFF8F0 cắt chéo chiếc lá thoáng sạch chuẩn NEWTASTE */}
      <div className="flex w-full flex-1 flex-col justify-between rounded-tl-[28px] rounded-br-[28px] rounded-tr-[6px] rounded-bl-[6px] bg-[#FFF8F0] px-5 pb-5 pt-14 shadow-[0_10px_28px_rgba(24,21,18,0.06)] transition duration-200 group-hover:-translate-y-1 group-hover:shadow-[0_16px_36px_rgba(24,21,18,0.1)] sm:pt-16">
        <div>
          {/* Hàng trạng thái & Điểm MCDA */}
          <div className="flex items-center justify-between gap-2">
            <span
              data-testid={`availability-badge-${recipe.slug}`}
              className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-[11px] font-bold ${
                isReady
                  ? 'bg-[#E7F8F2] text-[#0E6B4F]'
                  : 'bg-[#F7E8D9] text-[#9E3D08]'
              }`}
            >
              {isReady ? (
                <>
                  <Check className="h-3 w-3 stroke-[2.5]" aria-hidden="true" />
                  <span>Nấu được ngay</span>
                </>
              ) : (
                <>
                  <ShoppingBasket className="h-3 w-3" aria-hidden="true" />
                  <span className="tabular-nums">
                    Thiếu {item.missing_required_ingredient_ids.length} nguyên liệu
                  </span>
                </>
              )}
            </span>

            <span
              data-testid={`recommendation-score-${recipe.slug}`}
              className="rounded-full border border-[#DECDBE] bg-[#FAF3EB] px-2.5 py-0.5 text-[12px] font-bold text-[#181512] tabular-nums"
            >
              {formatScoreValue(item.score)} điểm
            </span>
          </div>

          {/* Tên món & thời gian */}
          <div className="mt-2.5 text-center">
            <h3 className="font-serif text-[20px] font-bold leading-snug text-[#181512]">
              {recipe.name_vi}
            </h3>
            <p className="mt-0.5 text-[12px] font-medium text-[#595047] tabular-nums">
              {CUISINE_LABELS[recipe.cuisine_code]} · {recipe.total_minutes} phút
              (Sơ chế {recipe.prep_minutes}p, nấu {recipe.cook_minutes}p)
            </p>
          </div>

          {/* Lời giải thích biên tập trực tiếp trên nền thẻ #FFF8F0 */}
          <p className="mt-2 text-center text-[12px] leading-relaxed text-[#4A4037]">
            {item.explanation_vi}
          </p>

          {/* Nguyên liệu đã khớp & cần chuẩn bị thêm */}
          {(item.matched_ingredient_ids.length > 0 ||
            item.missing_required_ingredient_ids.length > 0) && (
            <div className="mt-2.5 space-y-2 border-t border-[#EAE0D3] pt-2.5">
              {item.matched_ingredient_ids.length > 0 && (
                <div>
                  <p className="text-[11px] font-bold text-[#0E6B4F]">
                    Nguyên liệu đã có:
                  </p>
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    {item.matched_ingredient_ids.map((id) => (
                      <span
                        key={id}
                        className="inline-flex items-center gap-1 rounded-full bg-[#E7F8F2] px-2.5 py-0.5 text-[11px] font-semibold text-[#0E6B4F]"
                      >
                        <Check
                          className="h-3 w-3 stroke-[2.5]"
                          aria-hidden="true"
                        />
                        <span>{getIngredientNameById(id, knownIngredients)}</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {item.missing_required_ingredient_ids.length > 0 && (
                <div data-testid={`missing-ingredients-${recipe.slug}`}>
                  <p className="text-[11px] font-bold text-[#9E3D08]">
                    Cần chuẩn bị thêm:
                  </p>
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    {item.missing_required_ingredient_ids.map((id) => (
                      <span
                        key={id}
                        className="inline-flex items-center rounded-full border border-[#DFC2A7] bg-[#FAF1E7] px-2.5 py-0.5 text-[11px] font-semibold text-[#9E3D08]"
                      >
                        <span className="sr-only">Thiếu: </span>
                        <span>{getIngredientNameById(id, knownIngredients)}</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Dải phân rã 4 tiêu chí XAI (C, G, T, P) vạch chia mảnh chuẩn NEWTASTE */}
          <div
            data-testid={`score-xai-${recipe.slug}`}
            className="mt-3 grid grid-cols-2 gap-y-1.5 border-y border-[#E6DACB] py-2 text-center sm:grid-cols-4 sm:gap-y-0 sm:divide-x sm:divide-[#E6DACB]"
          >
            <div className="border-r border-[#E6DACB] px-1 sm:border-r-0">
              <span className="block text-[10px] font-medium text-[#595047]">
                Độ phủ
              </span>
              <span className="text-[12px] font-bold text-[#181512] tabular-nums">
                {formatScoreValue(item.score_contributions.C)}
              </span>
            </div>
            <div className="px-1">
              <span className="block text-[10px] font-medium text-[#595047]">
                Món chính
              </span>
              <span className="text-[12px] font-bold text-[#181512] tabular-nums">
                {formatScoreValue(item.score_contributions.G)}
              </span>
            </div>
            <div className="border-r border-[#E6DACB] px-1 sm:border-r-0">
              <span className="block text-[10px] font-medium text-[#595047]">
                Thời gian
              </span>
              <span className="text-[12px] font-bold text-[#181512] tabular-nums">
                {formatScoreValue(item.score_contributions.T)}
              </span>
            </div>
            <div className="px-1">
              <span className="block text-[10px] font-medium text-[#595047]">
                Vị quen
              </span>
              <span className="text-[12px] font-bold text-[#181512] tabular-nums">
                {formatScoreValue(item.score_contributions.P)}
              </span>
            </div>
          </div>
        </div>

        {/* Nút Xem chi tiết công thức dáng cắt chéo chiếc lá #C65112 */}
        <button
          type="button"
          data-testid={`view-recipe-detail-${recipe.slug}`}
          onClick={() => onSelectRecipe(recipe.id, item)}
          className="mt-4 inline-flex min-h-[42px] w-full items-center justify-center gap-2 rounded-tl-[14px] rounded-br-[14px] rounded-tr-[4px] rounded-bl-[4px] bg-[#C65112] px-5 py-2.5 text-[13px] font-semibold text-white shadow-sm transition hover:bg-[#A8430D]"
        >
          <span>Xem chi tiết công thức</span>
          <ArrowRight className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </article>
  );
};
