import React, { useEffect, useState } from 'react';
import { ExternalLink } from 'lucide-react';
import { getRecipeById } from '../../shared/api/recipesApi';
import {
  CuisineCode,
  RecommendationItem,
  RecipeDetail,
} from '../../shared/api/types';
import { BotanicalDecor } from '../../shared/components/BotanicalDecor';
import { formatScoreValue } from '../../shared/utils/formatters';

export interface RecipeDetailViewProps {
  recipeId: string;
  backLabel: string;
  recommendationContext?: RecommendationItem;
  onBack: () => void;
}

const CUISINE_BADGE_MAP: Record<CuisineCode, string> = {
  VN: 'Món Việt',
  EU: 'Món Âu',
  US: 'Món Mỹ',
};

const MANDATORY_NUTRITION_DISCLAIMER =
  'Thông tin dinh dưỡng chỉ mang tính tham khảo ở mức nguyên liệu (ước tính khi có khối lượng chuẩn), không suy diễn từ ảnh chụp, không thay thế tư vấn y tế và người dùng cần tự kiểm tra thành phần dị ứng thực phẩm.';

function isSafeHttpUrl(rawUrl: string | null | undefined): rawUrl is string {
  if (!rawUrl) return false;
  return /^https?:\/\//i.test(rawUrl.trim());
}

export const RecipeDetailView: React.FC<RecipeDetailViewProps> = ({
  recipeId,
  backLabel,
  recommendationContext,
  onBack,
}) => {
  const [recipe, setRecipe] = useState<RecipeDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [imageError, setImageError] = useState(false);
  const [retryTick, setRetryTick] = useState(0);

  useEffect(() => {
    let isCancelled = false;
    setIsLoading(true);
    setErrorMessage(null);
    setImageError(false);

    getRecipeById(recipeId)
      .then((detail) => {
        if (!isCancelled) {
          setRecipe(detail);
        }
      })
      .catch((err: unknown) => {
        if (!isCancelled) {
          setRecipe(null);
          setErrorMessage(
            err instanceof Error
              ? err.message
              : 'Không thể tải thông tin chi tiết công thức.'
          );
        }
      })
      .finally(() => {
        if (!isCancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [recipeId, retryTick]);

  const matchedIdSet = new Set(
    recommendationContext?.matched_ingredient_ids ?? []
  );
  const missingIdSet = new Set(
    recommendationContext?.missing_required_ingredient_ids ?? []
  );

  if (isLoading) {
    return (
      <div
        aria-label="Đang tải chi tiết công thức"
        className="space-y-8 py-4"
      >
        <div className="h-8 w-44 animate-pulse rounded-[8px] bg-[#D6C3AE]" />
        <div className="grid grid-cols-1 items-center gap-10 lg:grid-cols-12">
          <div className="space-y-4 lg:col-span-7">
            <div className="h-12 w-3/4 animate-pulse rounded-[8px] bg-[#D6C3AE]" />
            <div className="h-20 w-full animate-pulse rounded-[8px] bg-[#DFCDB8]" />
            <div className="h-24 w-full animate-pulse rounded-[8px] bg-[#DFCDB8]" />
          </div>
          <div className="mx-auto aspect-square w-64 animate-pulse rounded-full bg-[#D6C3AE] sm:w-80 lg:col-span-5" />
        </div>
      </div>
    );
  }

  if (errorMessage || !recipe) {
    return (
      <div className="space-y-6 py-4">
        <button
          type="button"
          data-testid="recipe-detail-back-btn"
          onClick={onBack}
          className="inline-flex min-h-[38px] items-center gap-1.5 rounded-full px-2 text-[13px] font-semibold text-[#B4490E] transition hover:text-[#181512]"
        >
          <span aria-hidden="true">←</span>
          <span>{backLabel}</span>
        </button>

        <div
          role="alert"
          data-testid="recipe-detail-error"
          className="mx-auto max-w-lg py-10 text-center"
        >
          <h1 className="font-serif text-2xl font-bold text-[#181512]">
            Không tìm thấy công thức món ăn
          </h1>
          <p className="mx-auto mt-2 max-w-md text-sm text-[#4A4037]">
            {errorMessage ??
              'Công thức không tồn tại hoặc chưa được xuất bản công khai.'}
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <button
              type="button"
              onClick={onBack}
              className="inline-flex min-h-[40px] items-center rounded-full bg-[#B4490E] px-5 py-2 text-xs font-semibold text-white transition hover:bg-[#963B0A]"
            >
              {backLabel}
            </button>
            <button
              type="button"
              onClick={() => setRetryTick((n) => n + 1)}
              className="inline-flex min-h-[40px] items-center rounded-full bg-[#FFF8F0] px-4 py-2 text-xs font-semibold text-[#181512] transition hover:bg-[#F5EADF]"
            >
              Thử lại
            </button>
          </div>
        </div>
      </div>
    );
  }

  const sortedIngredients = [...recipe.ingredients].sort(
    (a, b) => a.sort_order - b.sort_order
  );
  const mainIngredients = sortedIngredients.filter(
    (item) => item.category !== 'pantry'
  );
  const pantryIngredients = sortedIngredients.filter(
    (item) => item.category === 'pantry'
  );
  const sortedSteps = [...recipe.steps].sort((a, b) => a.step_no - b.step_no);

  const recipeTags = [
    CUISINE_BADGE_MAP[recipe.cuisine_code],
    `Hoàn thiện ${recipe.total_minutes} phút`,
    ...recipe.nutrition_evidence.map((ev) => ev.tag.name_vi),
  ];

  return (
    <article
      data-testid={`recipe-detail-view-${recipe.slug}`}
      className="space-y-9 py-2"
    >
      {/* Hàng quay lại tối giản trên mặt giấy */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#CDB9A2]/80 pb-3">
        <button
          type="button"
          data-testid="recipe-detail-back-btn"
          onClick={onBack}
          className="inline-flex min-h-[38px] items-center gap-1.5 text-[13.5px] font-semibold text-[#B4490E] transition hover:text-[#181512]"
        >
          <span aria-hidden="true">←</span>
          <span>{backLabel}</span>
        </button>

        <span className="rounded-full bg-[#EFE2D2] px-3.5 py-1 text-xs font-semibold text-[#3B3027]">
          {CUISINE_BADGE_MAP[recipe.cuisine_code]}
        </span>
      </div>

      {/* HERO 2 CỘT MẶT GIẤY MỞ — ĐỒNG BỘ BẢNG MÀU ÊM DỊU */}
      <section
        aria-label="Tổng quan món ăn"
        className="grid grid-cols-1 items-center gap-10 lg:grid-cols-12 lg:gap-12"
      >
        <div className="space-y-6 lg:col-span-7">
          <div>
            <h1 className="font-serif text-3xl font-bold leading-tight tracking-tight text-[#181512] sm:text-4xl lg:text-[42px]">
              {recipe.name_vi}
            </h1>

            {recipe.description && (
              <p className="mt-3 max-w-[65ch] text-[15px] leading-relaxed text-[#4A4037]">
                {recipe.description}
              </p>
            )}
          </div>

          <div
            data-testid="recipe-time-strip"
            className="grid grid-cols-2 border-y border-[#BDA992]/80 py-2 sm:grid-cols-4 sm:divide-x sm:divide-[#BDA992] sm:border-y-0 sm:py-1"
          >
            <div className="border-b border-r border-[#BDA992]/70 px-3 py-3 text-center sm:border-b-0 sm:border-r-0 sm:py-0 sm:first:pl-0">
              <span className="block font-serif text-3xl font-bold text-[#181512] tabular-nums sm:text-[34px]">
                {recipe.ingredients.length}
              </span>
              <span className="mt-1 block text-[11px] font-bold uppercase tracking-[0.08em] text-[#595047]">
                NGUYÊN LIỆU
              </span>
            </div>

            <div className="border-b border-[#BDA992]/70 px-3 py-3 text-center sm:border-b-0 sm:py-0">
              <span className="block font-serif text-3xl font-bold text-[#181512] tabular-nums sm:text-[34px]">
                {recipe.prep_minutes}
              </span>
              <span className="mt-1 block text-[11px] font-bold uppercase tracking-[0.08em] text-[#595047]">
                PHÚT SƠ CHẾ
              </span>
            </div>

            <div className="border-r border-[#BDA992]/70 px-3 py-3 text-center sm:border-b-0 sm:py-0">
              <span className="block font-serif text-3xl font-bold text-[#181512] tabular-nums sm:text-[34px]">
                {recipe.cook_minutes}
              </span>
              <span className="mt-1 block text-[11px] font-bold uppercase tracking-[0.08em] text-[#595047]">
                PHÚT NẤU
              </span>
            </div>

            <div className="px-3 py-3 text-center sm:py-0">
              <span className="block font-serif text-3xl font-bold text-[#B4490E] tabular-nums sm:text-[34px]">
                {recipe.total_minutes}
              </span>
              <span className="mt-1 block text-[11px] font-bold uppercase tracking-[0.08em] text-[#B4490E]">
                TỔNG PHÚT
              </span>
            </div>
          </div>

          <p
            data-testid="cook-time-br05-note"
            className="text-[12.5px] leading-relaxed text-[#595047]"
          >
            Thời gian nấu đã bao gồm cả thời gian ướp và chờ chế biến (nếu công
            thức có bước ướp).
          </p>

          {recommendationContext && (
            <div
              data-testid="detail-recommendation-summary"
              className="border-y border-[#CDB9A2] py-3.5 text-[13px] text-[#181512]"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-bold text-[#181512]">
                  Độ phù hợp gian bếp:{' '}
                  <span className="text-[#B4490E] tabular-nums">
                    {formatScoreValue(recommendationContext.score)} điểm
                  </span>
                </span>
                <span className="rounded-full bg-[#EFE2D2] px-3 py-0.5 text-xs font-semibold text-[#3B3027]">
                  {recommendationContext.availability === 'ready'
                    ? 'Đủ nguyên liệu nấu ngay'
                    : `Cần thêm ${recommendationContext.missing_required_ingredient_ids.length} nguyên liệu`}
                </span>
              </div>

              <p className="mt-1.5 text-[12.5px] text-[#4A4037]">
                {recommendationContext.explanation_vi}
              </p>

              <div className="mt-2.5 flex flex-wrap gap-x-5 gap-y-1 text-[12px] text-[#595047] tabular-nums">
                <span>
                  Độ phủ:{' '}
                  <strong className="text-[#181512]">
                    {formatScoreValue(recommendationContext.score_contributions.C)}
                  </strong>
                </span>
                <span>
                  Món chính:{' '}
                  <strong className="text-[#181512]">
                    {formatScoreValue(recommendationContext.score_contributions.G)}
                  </strong>
                </span>
                <span>
                  Thời gian:{' '}
                  <strong className="text-[#181512]">
                    {formatScoreValue(recommendationContext.score_contributions.T)}
                  </strong>
                </span>
                <span>
                  Vị quen:{' '}
                  <strong className="text-[#181512]">
                    {formatScoreValue(recommendationContext.score_contributions.P)}
                  </strong>
                </span>
              </div>
            </div>
          )}

          {/* NHÃN DINH DƯỠNG ÊM DỊU (Không dùng băng vàng chói) */}
          <section
            aria-label="Nhãn dinh dưỡng tham khảo và miễn trừ trách nhiệm"
            data-testid="nutrition-evidence-section"
            className="space-y-4 pt-1"
          >
            <h2 className="font-serif text-[20px] font-bold text-[#181512]">
              Nhãn dinh dưỡng tham khảo
            </h2>

            {recipe.nutrition_evidence.length > 0 ? (
              <div className="space-y-4">
                {recipe.nutrition_evidence.map((ev) => (
                  <div
                    key={ev.tag.id}
                    data-testid={`nutrition-tag-${ev.tag.code}`}
                    className="flex flex-col items-start gap-4 sm:flex-row sm:items-center"
                  >
                    <div className="flex h-[72px] w-[72px] shrink-0 flex-col items-center justify-center rounded-full border border-[#B89F86] bg-[#EFE2D2] px-2 text-center">
                      <span className="text-[11px] font-bold leading-tight text-[#181512]">
                        {ev.tag.name_vi}
                      </span>
                    </div>

                    <div className="min-w-0 flex-1 space-y-1">
                      {ev.tag.description && (
                        <p className="text-[13.5px] leading-relaxed text-[#3B3027]">
                          {ev.tag.description}
                        </p>
                      )}

                      {ev.note && (
                        <p className="text-[12px] italic text-[#595047]">
                          {ev.note}
                        </p>
                      )}

                      {ev.source_urls.length > 0 && (
                        <div className="flex flex-wrap items-center gap-2 pt-0.5">
                          <span className="text-[11.5px] font-semibold text-[#595047]">
                            Nguồn dẫn chứng:
                          </span>
                          {ev.source_urls
                            .filter((url) => isSafeHttpUrl(url))
                            .map((url, idx) => (
                              <a
                                key={`${ev.tag.id}-src-${idx}`}
                                href={url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex min-h-[34px] items-center gap-1 rounded-full bg-[#FFF8F0]/80 px-3 py-1 text-[11.5px] font-semibold text-[#B4490E] transition hover:bg-[#FFF8F0] hover:underline"
                              >
                                <span>Tham khảo #{idx + 1}</span>
                                <ExternalLink
                                  className="h-3 w-3"
                                  aria-hidden="true"
                                />
                              </a>
                            ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p
                data-testid="nutrition-empty-note"
                className="text-[13.5px] italic text-[#595047]"
              >
                Công thức này hiện chưa có nhãn dinh dưỡng định tính được kiểm
                duyệt.
              </p>
            )}

            <p
              data-testid="nutrition-disclaimer"
              className="border-t border-[#CDB9A2]/80 pt-3 text-[12.5px] leading-relaxed text-[#4A4037]"
            >
              {MANDATORY_NUTRITION_DISCLAIMER}
            </p>
          </section>
        </div>

        {/* Cột phải: Đĩa món ăn tròn lớn */}
        <div className="lg:col-span-5">
          <div className="relative mx-auto w-full max-w-[380px]">
            <BotanicalDecor
              variant="rosemary"
              className="pointer-events-none absolute -right-6 -top-6 h-28 w-28 text-[#8B7660]/40"
            />
            <BotanicalDecor
              variant="basil"
              className="pointer-events-none absolute -bottom-6 -left-6 h-28 w-28 text-[#8B7660]/35"
            />

            <div className="relative z-10 aspect-square w-full overflow-hidden rounded-full bg-[#181512] ring-[6px] ring-[#FFF8F0] shadow-[0_24px_52px_rgba(24,21,18,0.18)]">
              {recipe.cover_image_url && !imageError ? (
                <img
                  src={recipe.cover_image_url}
                  alt={recipe.name_vi}
                  onError={() => setImageError(true)}
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center bg-[#2A2421] font-serif text-sm font-bold text-[#EFE2D2]">
                  FoodVision AI
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* KHỐI NGUYÊN LIỆU & GIA VỊ */}
      <div className="grid grid-cols-1 items-start gap-8 border-t border-[#CDB9A2] pt-8 lg:grid-cols-12">
        <section
          aria-label="Nguyên liệu chính và phụ"
          data-testid="recipe-main-ingredients"
          className="lg:col-span-7"
        >
          <h2 className="mb-4 font-serif text-[21px] font-bold text-[#181512]">
            Nguyên liệu ({mainIngredients.length})
          </h2>

          {mainIngredients.length === 0 ? (
            <p className="py-3 text-sm text-[#595047]">
              Chưa cập nhật danh sách nguyên liệu.
            </p>
          ) : (
            <ul className="divide-y divide-[#D5C3AE]/80">
              {mainIngredients.map((item) => {
                const isMatched = matchedIdSet.has(item.ingredient_id);
                const isMissing = missingIdSet.has(item.ingredient_id);

                return (
                  <li
                    key={`${item.ingredient_id}-${item.sort_order}`}
                    className="flex flex-wrap items-center justify-between gap-2 py-3"
                  >
                    <div className="flex flex-wrap items-center gap-2.5">
                      <span className="text-[15px] font-semibold text-[#181512]">
                        {item.name_vi}
                      </span>

                      <span className="rounded-full bg-[#EFE2D2] px-2.5 py-0.5 text-[11px] font-medium text-[#595047]">
                        {item.is_required ? 'Bắt buộc' : 'Tùy chọn'}
                      </span>

                      {isMatched && (
                        <span className="rounded-full bg-[#FFF8F0] px-2.5 py-0.5 text-[11px] font-semibold text-[#181512]">
                          Đã có trong bếp
                        </span>
                      )}

                      {isMissing && (
                        <span className="rounded-full bg-[#F4DEC9] px-2.5 py-0.5 text-[11px] font-semibold text-[#B4490E]">
                          Cần mua thêm
                        </span>
                      )}
                    </div>

                    <span className="text-[14px] font-medium text-[#3F362E] tabular-nums">
                      {item.display_quantity ?? 'Vừa đủ'}
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        <section
          aria-label="Gia vị cần chuẩn bị"
          data-testid="recipe-pantry-ingredients"
          className="lg:col-span-5"
        >
          <h2 className="mb-4 font-serif text-[21px] font-bold text-[#181512]">
            Gia vị cần chuẩn bị ({pantryIngredients.length})
          </h2>

          {pantryIngredients.length === 0 ? (
            <p className="py-3 text-sm text-[#595047]">
              Không yêu cầu gia vị cơ bản.
            </p>
          ) : (
            <ul className="divide-y divide-[#D5C3AE]/80">
              {pantryIngredients.map((item) => {
                const isMissing = missingIdSet.has(item.ingredient_id);
                return (
                  <li
                    key={`${item.ingredient_id}-${item.sort_order}`}
                    className="flex items-center justify-between gap-2 py-3"
                  >
                    <div className="flex items-center gap-2.5">
                      <span className="text-[15px] font-semibold text-[#181512]">
                        {item.name_vi}
                      </span>
                      {isMissing && (
                        <span className="rounded-full bg-[#F4DEC9] px-2.5 py-0.5 text-[11px] font-semibold text-[#B4490E]">
                          Đang hết
                        </span>
                      )}
                    </div>

                    <span className="text-[14px] font-medium text-[#3F362E] tabular-nums">
                      {item.display_quantity ?? 'Vừa đủ'}
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      </div>

      {/* KHỐI CÁC BƯỚC CHẾ BIẾN */}
      <section
        aria-label="Các bước chế biến"
        className="border-t border-[#CDB9A2] pt-8"
      >
        <h2 className="font-serif text-[21px] font-bold text-[#181512]">
          Các bước chế biến ({sortedSteps.length} bước)
        </h2>

        <ol
          data-testid="recipe-steps-list"
          className="mt-4 divide-y divide-[#D5C3AE]/75"
        >
          {sortedSteps.map((step) => (
            <li
              key={step.step_no}
              className="flex items-start gap-3.5 py-4 first:pt-1 last:pb-1"
            >
              <span className="w-6 shrink-0 font-serif text-[19px] font-bold text-[#B4490E] tabular-nums">
                {step.step_no}.
              </span>

              <div className="flex-1 space-y-1">
                <p className="max-w-[72ch] text-[15px] leading-relaxed text-[#181512]">
                  {step.instruction}
                </p>

                {step.estimated_minutes !== null && (
                  <p className="text-[12px] font-medium text-[#595047] tabular-nums">
                    Ước tính {step.estimated_minutes} phút
                  </p>
                )}
              </div>
            </li>
          ))}
        </ol>
      </section>

      {/* THẺ CÔNG THỨC & NGUỒN THAM KHẢO */}
      <section
        aria-label="Thẻ công thức và nguồn tham khảo"
        className="space-y-5 border-t border-[#CDB9A2] pt-8"
      >
        <div className="flex flex-wrap gap-2">
          {recipeTags.map((tagLabel) => (
            <span
              key={tagLabel}
              className="rounded-full bg-[#EFE2D2] px-3.5 py-1 text-xs font-medium text-[#3B3027]"
            >
              {tagLabel}
            </span>
          ))}
        </div>

        {(recipe.source_name || recipe.source_url || recipe.content_license) && (
          <div
            data-testid="recipe-source-footer"
            className="flex flex-wrap items-center justify-between gap-3 border-t border-[#D5C3AE] pt-4 text-xs text-[#4A4037]"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold text-[#181512]">
                Nguồn công thức:
              </span>
              <span>{recipe.source_name ?? 'Biên soạn nội bộ FoodVision'}</span>
              {isSafeHttpUrl(recipe.source_url) && (
                <a
                  href={recipe.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex min-h-[34px] items-center gap-1 px-1.5 font-semibold text-[#B4490E] hover:underline"
                >
                  <span>Liên kết gốc</span>
                  <ExternalLink className="h-3 w-3" aria-hidden="true" />
                </a>
              )}
            </div>

            {recipe.content_license && (
              <span className="rounded-full bg-[#EFE2D2] px-3 py-1 font-medium text-[#3B3027]">
                Giấy phép: {recipe.content_license}
              </span>
            )}
          </div>
        )}
      </section>
    </article>
  );
};
