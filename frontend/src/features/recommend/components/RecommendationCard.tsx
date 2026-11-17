import React, { useState } from 'react';
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

  const missingNames = item.missing_required_ingredient_ids.map((id) =>
    getIngredientNameById(id, knownIngredients)
  );
  const firstMissing = missingNames[0] ?? '';
  const extraMissingCount = Math.max(0, missingNames.length - 1);

  return (
    <article
      data-testid={`recommendation-card-${recipe.slug}`}
      className="group relative flex flex-col items-center pt-16"
    >
      {/* Đĩa món ăn tròn lớn 144px đồng bộ 100% với Trang chủ chuẩn Mockup A */}
      <div className="relative z-10 -mb-16 h-36 w-36 shrink-0 overflow-hidden rounded-full bg-[#181512] ring-4 ring-[#FFF8F0] shadow-[0_12px_26px_rgba(24,21,18,0.16)] transition duration-300 group-hover:scale-[1.03]">
        {recipe.cover_image_url && !imageError ? (
          <img
            src={recipe.cover_image_url}
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

      {/* Thân thẻ trắng kem #FFF8F0 tối giản, đơn sắc ấm chuẩn Mockup A */}
      <div className="relative flex w-full flex-1 flex-col justify-between rounded-tl-[26px] rounded-br-[26px] rounded-tr-[6px] rounded-bl-[6px] bg-[#FFF8F0] px-5 pb-5 pt-20 text-left shadow-[0_10px_28px_rgba(24,21,18,0.06)] transition duration-200 group-hover:-translate-y-1 group-hover:shadow-[0_16px_36px_rgba(24,21,18,0.1)]">
        <div>
          {/* Cặp nhãn trạng thái & điểm số đồng bộ gam cát ấm #EFE2D2 (không icon thừa, không xanh chói) */}
          <div className="flex items-center justify-between gap-2">
            <span
              data-testid={`availability-badge-${recipe.slug}`}
              className={`inline-flex max-w-[62%] items-center truncate rounded-full px-2.5 py-0.5 text-[11.5px] font-medium ${
                isReady
                  ? 'bg-[#EADBC8] font-semibold text-[#181512]'
                  : 'bg-[#EFE2D2] text-[#4A4037]'
              }`}
            >
              {isReady ? (
                <span>Nấu được ngay</span>
              ) : (
                <span className="truncate">
                  Thêm: {firstMissing}
                  {extraMissingCount > 0 ? ` +${extraMissingCount}` : ''}
                </span>
              )}
            </span>

            <span
              data-testid={`recommendation-score-${recipe.slug}`}
              className="shrink-0 rounded-full bg-[#EFE2D2] px-2.5 py-0.5 text-[11.5px] font-semibold text-[#181512] tabular-nums"
            >
              {formatScoreValue(item.score)} điểm
            </span>
          </div>

          {/* Tên món & thời gian */}
          <h3 className="mt-3 line-clamp-2 min-h-[3.2rem] font-serif text-[19px] font-bold leading-snug text-[#181512] transition group-hover:text-[#B4490E]">
            {recipe.name_vi}
          </h3>

          <p className="mt-1 text-[12.5px] font-medium text-[#595047] tabular-nums">
            {CUISINE_LABELS[recipe.cuisine_code]} · {recipe.total_minutes} phút
          </p>

          {/* Lời giải thích biên tập 2 dòng gọn nhẹ */}
          <p className="mt-2 line-clamp-2 text-[13px] leading-relaxed text-[#4A4037]">
            {item.explanation_vi}
          </p>

          {/* Dữ liệu ngữ nghĩa ẩn cho trình đọc màn hình & kiểm thử tự động (không làm rối bề mặt thẻ) */}
          {missingNames.length > 0 && (
            <div
              data-testid={`missing-ingredients-${recipe.slug}`}
              className="sr-only"
            >
              {missingNames.map((name) => (
                <span key={name}>Thiếu: {name} </span>
              ))}
            </div>
          )}

          <div data-testid={`score-xai-${recipe.slug}`} className="sr-only">
            <span>Độ phủ {formatScoreValue(item.score_contributions.C)} </span>
            <span>
              Món chính {formatScoreValue(item.score_contributions.G)}{' '}
            </span>
            <span>
              Thời gian {formatScoreValue(item.score_contributions.T)}{' '}
            </span>
            <span>Vị quen {formatScoreValue(item.score_contributions.P)}</span>
          </div>
        </div>

        {/* Liên kết chữ Xem công thức → thanh thoát chuẩn Mockup A (phủ vùng bấm toàn thẻ) */}
        <div className="mt-4 pt-1">
          <button
            type="button"
            data-testid={`view-recipe-detail-${recipe.slug}`}
            onClick={() => onSelectRecipe(recipe.id, item)}
            className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-[#B4490E] transition after:absolute after:inset-0 after:content-[''] group-hover:text-[#181512] focus:outline-none"
          >
            <span>Xem công thức</span>
            <span aria-hidden="true">→</span>
          </button>
        </div>
      </div>
    </article>
  );
};
