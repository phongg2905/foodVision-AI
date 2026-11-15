import React, { useState } from 'react';
import { ArrowRight, Check, ShoppingBasket, Utensils } from 'lucide-react';
import { getIngredientNameById } from '../../../shared/api/mockData';
import {
  CuisineCode,
  Ingredient,
  RecommendationItem,
} from '../../../shared/api/types';

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

function formatScoreValue(value: number): string {
  const rounded = Math.round(value * 100) / 100;
  return Number.isInteger(rounded * 10)
    ? rounded.toFixed(1)
    : rounded.toFixed(2);
}

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
      className="group relative flex flex-col items-center pt-14"
    >
      {/* Đĩa món ăn tròn nổi chuẩn NEWTASTE */}
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
            <span className="font-serif text-[10px] font-bold">FoodVision</span>
          </div>
        )}
      </div>

      {/* Thân thẻ trắng bo góc bất đối xứng */}
      <div className="flex w-full flex-1 flex-col justify-between rounded-bl-[14px] rounded-br-[30px] rounded-tl-[30px] rounded-tr-[14px] border border-[#E6DACB] bg-white px-5 pb-6 pt-16 shadow-[0_10px_28px_rgba(24,21,18,0.05)] transition duration-200 group-hover:-translate-y-1 group-hover:shadow-[0_16px_36px_rgba(24,21,18,0.1)] sm:pt-20">
        <div>
          {/* Hàng trạng thái & Điểm MCDA */}
          <div className="flex items-center justify-between gap-2">
            <span
              data-testid={`availability-badge-${recipe.slug}`}
              className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-[11px] font-bold ${
                isReady
                  ? 'bg-[#E7F8F2] text-[#157358]'
                  : 'bg-[#FDF0E7] text-[#C2591B]'
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
              className="rounded-full border border-[#DFD3C3] bg-[#FAF7F2] px-2.5 py-1 text-[12px] font-bold text-[#181512] tabular-nums"
            >
              {formatScoreValue(item.score)} điểm
            </span>
          </div>

          {/* Tên món & thời gian */}
          <div className="mt-3 text-center">
            <h3 className="font-serif text-[18px] font-bold leading-snug text-[#181512]">
              {recipe.name_vi}
            </h3>
            <p className="mt-1 text-[12px] font-medium text-[#6E655C] tabular-nums">
              {CUISINE_LABELS[recipe.cuisine_code]} · {recipe.total_minutes} phút
              (Sơ chế {recipe.prep_minutes}p, nấu {recipe.cook_minutes}p)
            </p>
          </div>

          {/* Lời giải thích tiếng Việt */}
          <p className="mt-3 rounded-2xl bg-[#FAF7F2] px-3.5 py-2.5 text-[12px] leading-relaxed text-[#4A4139]">
            {item.explanation_vi}
          </p>

          {/* Nguyên liệu đã khớp */}
          {item.matched_ingredient_ids.length > 0 && (
            <div className="mt-3">
              <p className="text-[11px] font-bold text-[#157358]">
                Nguyên liệu đã có:
              </p>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {item.matched_ingredient_ids.map((id) => (
                  <span
                    key={id}
                    className="inline-flex items-center gap-1 rounded-full bg-[#E7F8F2] px-2.5 py-0.5 text-[11px] font-semibold text-[#157358]"
                  >
                    <Check className="h-3 w-3 stroke-[2.5]" aria-hidden="true" />
                    <span>{getIngredientNameById(id, knownIngredients)}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Nguyên liệu / gia vị còn thiếu bắt buộc */}
          {item.missing_required_ingredient_ids.length > 0 && (
            <div
              data-testid={`missing-ingredients-${recipe.slug}`}
              className="mt-3"
            >
              <p className="text-[11px] font-bold text-[#C2591B]">
                Cần chuẩn bị thêm:
              </p>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {item.missing_required_ingredient_ids.map((id) => (
                  <span
                    key={id}
                    className="inline-flex items-center rounded-full border border-[#F2C7A8] bg-[#FDF0E7] px-2.5 py-0.5 text-[11px] font-semibold text-[#C2591B]"
                  >
                    Thiếu: {getIngredientNameById(id, knownIngredients)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Phân rã 4 tiêu chí XAI (C, G, T, P) */}
          <div
            data-testid={`score-xai-${recipe.slug}`}
            className="mt-4 grid grid-cols-4 divide-x divide-[#EFE6D8] rounded-xl border border-[#EFE6D8] bg-[#FAF7F2] py-2 text-center"
          >
            <div>
              <span className="block text-[10px] font-medium text-[#6E655C]">
                Độ phủ
              </span>
              <span className="text-[12px] font-bold text-[#181512] tabular-nums">
                {formatScoreValue(item.score_contributions.C)}
              </span>
            </div>
            <div>
              <span className="block text-[10px] font-medium text-[#6E655C]">
                Món chính
              </span>
              <span className="text-[12px] font-bold text-[#181512] tabular-nums">
                {formatScoreValue(item.score_contributions.G)}
              </span>
            </div>
            <div>
              <span className="block text-[10px] font-medium text-[#6E655C]">
                Thời gian
              </span>
              <span className="text-[12px] font-bold text-[#181512] tabular-nums">
                {formatScoreValue(item.score_contributions.T)}
              </span>
            </div>
            <div>
              <span className="block text-[10px] font-medium text-[#6E655C]">
                Vị quen
              </span>
              <span className="text-[12px] font-bold text-[#181512] tabular-nums">
                {formatScoreValue(item.score_contributions.P)}
              </span>
            </div>
          </div>
        </div>

        {/* Nút Xem chi tiết công thức */}
        <button
          type="button"
          data-testid={`view-recipe-detail-${recipe.slug}`}
          onClick={() => onSelectRecipe(recipe.id, item)}
          className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-full bg-[#E87838] px-5 py-2.5 text-[13px] font-semibold text-white shadow-sm transition hover:bg-[#D16426]"
        >
          <span>Xem chi tiết công thức</span>
          <ArrowRight className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </article>
  );
};
