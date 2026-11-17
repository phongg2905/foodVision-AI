import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  ArrowLeft,
  BookOpen,
  Check,
  Clock,
  ExternalLink,
  Info,
  RotateCcw,
  Utensils,
} from 'lucide-react';
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
        <div className="h-9 w-52 animate-pulse rounded-tl-[12px] rounded-br-[12px] rounded-tr-[4px] rounded-bl-[4px] bg-[#D6C3AE]" />
        <div className="grid grid-cols-1 items-start gap-8 lg:grid-cols-12">
          <div className="space-y-4 lg:col-span-7">
            <div className="h-12 w-3/4 animate-pulse rounded-xl bg-[#D6C3AE]" />
            <div className="h-24 w-full animate-pulse rounded-xl bg-[#FFF8F0]/70" />
            <div className="h-24 w-full animate-pulse rounded-xl bg-[#FFF8F0]" />
          </div>
          <div className="mx-auto aspect-square w-64 animate-pulse rounded-tl-[32px] rounded-br-[32px] rounded-tr-[8px] rounded-bl-[8px] bg-[#D6C3AE] sm:w-80 lg:col-span-5" />
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
          className="inline-flex items-center gap-1.5 rounded-tl-[12px] rounded-br-[12px] rounded-tr-[4px] rounded-bl-[4px] border border-[#D4C1AC] bg-[#FFF8F0] px-4 py-2 text-xs font-semibold text-[#9E3D08] transition hover:border-[#EA6D27] hover:text-[#181512]"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
          <span>{backLabel}</span>
        </button>

        <div
          role="alert"
          data-testid="recipe-detail-error"
          className="rounded-tl-[28px] rounded-br-[28px] rounded-tr-[6px] rounded-bl-[6px] border border-[#DFC7AF] bg-[#FFF8F0] p-8 text-center shadow-[0_12px_34px_rgba(24,21,18,0.06)]"
        >
          <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[#F7E8D9] text-[#9E3D08]">
            <AlertCircle className="h-6 w-6" aria-hidden="true" />
          </span>
          <h1 className="mt-4 font-serif text-2xl font-bold text-[#181512]">
            Không tìm thấy công thức món ăn
          </h1>
          <p className="mx-auto mt-2 max-w-md text-sm text-[#595047]">
            {errorMessage ??
              'Công thức không tồn tại hoặc chưa được xuất bản công khai.'}
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <button
              type="button"
              onClick={onBack}
              className="inline-flex items-center gap-2 rounded-tl-[14px] rounded-br-[14px] rounded-tr-[4px] rounded-bl-[4px] bg-[#C65112] px-5 py-2.5 text-xs font-semibold text-white transition hover:bg-[#A8430D]"
            >
              <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
              <span>{backLabel}</span>
            </button>
            <button
              type="button"
              onClick={() => setRetryTick((n) => n + 1)}
              className="inline-flex items-center gap-2 rounded-tl-[14px] rounded-br-[14px] rounded-tr-[4px] rounded-bl-[4px] border border-[#D4C1AC] bg-[#F7EFE5] px-5 py-2.5 text-xs font-semibold text-[#181512] transition hover:border-[#181512]"
            >
              <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
              <span>Thử lại</span>
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
      className="space-y-10 py-2"
    >
      {/* Thanh điều hướng quay lại */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <button
          type="button"
          data-testid="recipe-detail-back-btn"
          onClick={onBack}
          className="inline-flex min-h-[40px] items-center gap-2 rounded-tl-[12px] rounded-br-[12px] rounded-tr-[4px] rounded-bl-[4px] border border-[#D4C1AC] bg-[#FFF8F0] px-4 py-2 text-xs font-semibold text-[#9E3D08] transition hover:border-[#EA6D27] hover:text-[#181512]"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
          <span>{backLabel}</span>
        </button>

        <span className="rounded-[7px] border border-[#6E6052]/60 bg-[#FFF8F0]/75 px-3.5 py-1 text-xs font-semibold text-[#181512]">
          {CUISINE_BADGE_MAP[recipe.cuisine_code]}
        </span>
      </div>

      {/* ===================================================================
          HERO 2 CỘT CHUẨN "CHICKEN PASTA" CỦA NEWTASTE (Trái Thông tin — Phải Ảnh)
         =================================================================== */}
      <section
        aria-label="Tổng quan món ăn"
        className="grid grid-cols-1 items-start gap-9 lg:grid-cols-12 lg:gap-12"
      >
        {/* Cột trái: Tiêu đề + Thông số vạch dọc mở trên nền kem + Huy chương dinh dưỡng */}
        <div className="space-y-7 lg:col-span-7">
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

          {/* Dải 4 Thông số Vạch Chia cân xứng (2x2 chữ thập ở Mobile, 4 cột dọc ở sm+) */}
          <div
            data-testid="recipe-time-strip"
            className="grid grid-cols-2 border-y border-[#BDA992]/70 py-2 sm:grid-cols-4 sm:divide-x sm:divide-[#BDA992] sm:border-y-0 sm:py-1"
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

            <div className="border-r border-[#BDA992]/70 px-3 py-3 text-center sm:border-r-0 sm:py-0">
              <span className="block font-serif text-3xl font-bold text-[#181512] tabular-nums sm:text-[34px]">
                {recipe.cook_minutes}
              </span>
              <span className="mt-1 block text-[11px] font-bold uppercase tracking-[0.08em] text-[#595047]">
                PHÚT NẤU
              </span>
            </div>

            <div className="px-3 py-3 text-center sm:py-0">
              <span className="block font-serif text-3xl font-bold text-[#9E3D08] tabular-nums sm:text-[34px]">
                {recipe.total_minutes}
              </span>
              <span className="mt-1 block text-[11px] font-bold uppercase tracking-[0.08em] text-[#9E3D08]">
                TỔNG PHÚT
              </span>
            </div>
          </div>

          {/* Ghi chú BR-05 */}
          <p
            data-testid="cook-time-br05-note"
            className="flex items-start gap-2 text-[12px] leading-relaxed text-[#595047]"
          >
            <Clock
              className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#9E3D08]"
              aria-hidden="true"
            />
            <span>
              Thời gian nấu đã bao gồm cả thời gian ướp và chờ chế biến (nếu
              công thức có bước ướp).
            </span>
          </p>

          {/* Ngữ cảnh gợi ý khi mở từ RecommendationResultsView */}
          {recommendationContext && (
            <div
              data-testid="detail-recommendation-summary"
              className="rounded-tl-[20px] rounded-br-[20px] rounded-tr-[6px] rounded-bl-[6px] border border-[#D8C6B2] bg-[#FFF8F0] px-4 py-3.5 text-[13px] text-[#181512] shadow-[0_6px_18px_rgba(24,21,18,0.04)]"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-bold text-[#0E6B4F]">
                  Độ phù hợp gian bếp:{' '}
                  <span className="tabular-nums">
                    {formatScoreValue(recommendationContext.score)} điểm
                  </span>
                </span>
                <span className="text-xs font-semibold text-[#9E3D08]">
                  {recommendationContext.availability === 'ready'
                    ? 'Có thể nấu ngay'
                    : `Cần thêm ${recommendationContext.missing_required_ingredient_ids.length} nguyên liệu`}
                </span>
              </div>
              <p className="mt-1 text-xs text-[#595047]">
                {recommendationContext.explanation_vi}
              </p>
            </div>
          )}

          {/* Khối NHÃN DINH DƯỠNG chuẩn Tag cam nghệ + Huy chương tròn + Miễn trừ BR-03 */}
          <section
            aria-label="Nhãn dinh dưỡng tham khảo và miễn trừ trách nhiệm"
            data-testid="nutrition-evidence-section"
            className="space-y-4"
          >
            <div>
              <h2 className="inline-block rounded-[6px] bg-[#F59E28] px-3.5 py-1 font-serif text-[16px] font-bold uppercase tracking-wide text-[#181512]">
                Nhãn dinh dưỡng tham khảo
              </h2>
            </div>

            {recipe.nutrition_evidence.length > 0 ? (
              <div className="space-y-3">
                {recipe.nutrition_evidence.map((ev) => (
                  <div
                    key={ev.tag.id}
                    data-testid={`nutrition-tag-${ev.tag.code}`}
                    className="flex flex-col items-start gap-4 rounded-tl-[20px] rounded-br-[20px] rounded-tr-[6px] rounded-bl-[6px] border border-[#DECDBE] bg-[#FFF8F0]/90 p-4 sm:flex-row sm:items-center"
                  >
                    {/* Huy chương tròn định tính đặc trưng NEWTASTE (không bịa kcal/gram) */}
                    <div className="flex h-[76px] w-[76px] shrink-0 flex-col items-center justify-center rounded-full border-[1.5px] border-[#C66B30] bg-[#DFA880]/75 px-1.5 text-center shadow-[0_4px_12px_rgba(24,21,18,0.06)]">
                      <span className="text-[11px] font-bold leading-tight text-[#181512]">
                        {ev.tag.name_vi}
                      </span>
                    </div>

                    <div className="min-w-0 flex-1 space-y-1.5">
                      {ev.tag.description && (
                        <p className="text-[13px] leading-relaxed text-[#3F362E]">
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
                          <span className="text-[11px] font-semibold text-[#595047]">
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
                                className="inline-flex min-h-[34px] items-center gap-1 rounded-full border border-[#D4C1AC] bg-[#FFF8F0] px-3 py-1.5 text-[11px] font-semibold text-[#9E3D08] transition hover:border-[#EA6D27] hover:underline"
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
                className="rounded-tl-[16px] rounded-br-[16px] rounded-tr-[6px] rounded-bl-[6px] border border-dashed border-[#BDA992] bg-[#FFF8F0]/75 px-4 py-3 text-[13px] text-[#595047]"
              >
                Công thức này hiện chưa có nhãn dinh dưỡng định tính được kiểm
                duyệt.
              </p>
            )}

            {/* BẮT BUỘC HIỂN THỊ NGUYÊN VĂN TUYÊN BỐ MIỄN TRỪ BR-03 */}
            <div
              data-testid="nutrition-disclaimer"
              className="flex items-start gap-3 rounded-tl-[18px] rounded-br-[18px] rounded-tr-[6px] rounded-bl-[6px] border border-[#D8C2AA] bg-[#FFF8F0] p-4 text-[13px] leading-relaxed text-[#5C2D12]"
            >
              <Info
                className="mt-0.5 h-4 w-4 shrink-0 text-[#9E3D08]"
                aria-hidden="true"
              />
              <p>{MANDATORY_NUTRITION_DISCLAIMER}</p>
            </div>
          </section>
        </div>

        {/* Cột phải: Ảnh món ăn chụp từ trên xuống nổi bật bên phải chuẩn NEWTASTE */}
        <div className="lg:col-span-5">
          <div className="relative mx-auto w-full max-w-[400px] lg:sticky lg:top-8">
            <BotanicalDecor
              variant="rosemary"
              className="pointer-events-none absolute -right-7 -top-7 h-28 w-28 text-[#8B7660]/45"
            />
            <BotanicalDecor
              variant="basil"
              className="pointer-events-none absolute -bottom-7 -left-7 h-28 w-28 text-[#8B7660]/40"
            />

            <div className="relative z-10 aspect-[4/3] w-full overflow-hidden rounded-tl-[32px] rounded-br-[32px] rounded-tr-[8px] rounded-bl-[8px] border-[5px] border-[#FFF8F0] bg-[#181512] shadow-[0_20px_46px_rgba(24,21,18,0.18)] sm:aspect-square">
              {recipe.cover_image_url && !imageError ? (
                <img
                  src={recipe.cover_image_url}
                  alt={recipe.name_vi}
                  onError={() => setImageError(true)}
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="flex h-full w-full flex-col items-center justify-center gap-2 bg-[#2A2421] text-[#EA6D27]">
                  <Utensils className="h-10 w-10" aria-hidden="true" />
                  <span className="font-serif text-sm font-bold">
                    FoodVision AI
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ===================================================================
          KHỐI NGUYÊN LIỆU & GIA VỊ CẦN CHUẨN BỊ (Mở trực tiếp trên nền kem #E8D8C6)
         =================================================================== */}
      <div className="grid grid-cols-1 items-start gap-8 border-t border-[#BDA992]/70 pt-8 lg:grid-cols-12">
        {/* Cột 1: Nguyên liệu chính/phụ (`category !== 'pantry'`) */}
        <section
          aria-label="Nguyên liệu chính và phụ"
          data-testid="recipe-main-ingredients"
          className="lg:col-span-7"
        >
          <div className="mb-4">
            <h2 className="inline-block rounded-[6px] bg-[#F59E28] px-3.5 py-1 font-serif text-[16px] font-bold uppercase tracking-wide text-[#181512]">
              Nguyên liệu •{' '}
              <span className="tabular-nums">{mainIngredients.length}</span>
            </h2>
          </div>

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
                      <span
                        className="h-1.5 w-1.5 shrink-0 rounded-full bg-[#181512]"
                        aria-hidden="true"
                      />
                      <span className="text-[15px] font-semibold text-[#181512]">
                        {item.name_vi}
                      </span>

                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                          item.is_required
                            ? 'bg-[#FFF8F0] text-[#595047]'
                            : 'border border-dashed border-[#BDA992] text-[#595047]'
                        }`}
                      >
                        {item.is_required ? 'Bắt buộc' : 'Tùy chọn'}
                      </span>

                      {isMatched && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-[#E7F8F2] px-2 py-0.5 text-[10px] font-bold text-[#0E6B4F]">
                          <Check className="h-3 w-3 stroke-[2.5]" />
                          <span>Đã có</span>
                        </span>
                      )}

                      {isMissing && (
                        <span className="rounded-full bg-[#FFF8F0] px-2 py-0.5 text-[10px] font-bold text-[#9E3D08]">
                          Cần chuẩn bị
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

        {/* Cột 2: Gia vị cần chuẩn bị (`category === 'pantry'`) */}
        <section
          aria-label="Gia vị cần chuẩn bị"
          data-testid="recipe-pantry-ingredients"
          className="lg:col-span-5"
        >
          <div className="mb-4">
            <h2 className="inline-block rounded-[6px] bg-[#F59E28] px-3.5 py-1 font-serif text-[16px] font-bold uppercase tracking-wide text-[#181512]">
              Gia vị cần chuẩn bị •{' '}
              <span className="tabular-nums">{pantryIngredients.length}</span>
            </h2>
          </div>

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
                      <span
                        className="h-1.5 w-1.5 shrink-0 rounded-full bg-[#181512]"
                        aria-hidden="true"
                      />
                      <span className="text-[15px] font-semibold text-[#181512]">
                        {item.name_vi}
                      </span>
                      {isMissing && (
                        <span className="rounded-full bg-[#FFF8F0] px-2 py-0.5 text-[10px] font-bold text-[#9E3D08]">
                          Đang thiếu
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

      {/* ===================================================================
          KHỐI CÁC BƯỚC CHẾ BIẾN ĐÁNH SỐ THỨ TỰ CHUẨN NEWTASTE
         =================================================================== */}
      <section
        aria-label="Các bước chế biến"
        className="border-t border-[#BDA992]/70 pt-8"
      >
        <div>
          <h2 className="inline-block rounded-[6px] bg-[#F59E28] px-3.5 py-1 font-serif text-[16px] font-bold uppercase tracking-wide text-[#181512]">
            Các bước chế biến •{' '}
            <span className="tabular-nums">{sortedSteps.length} bước</span>
          </h2>
        </div>

        <ol
          data-testid="recipe-steps-list"
          className="mt-5 divide-y divide-[#D5C3AE]/75"
        >
          {sortedSteps.map((step) => (
            <li
              key={step.step_no}
              className="flex items-start gap-3 py-4 first:pt-1 last:pb-1"
            >
              <span className="w-7 shrink-0 font-serif text-[19px] font-bold text-[#181512] tabular-nums">
                {step.step_no}.
              </span>

              <div className="flex-1 space-y-2">
                <p className="max-w-[72ch] text-[15px] leading-relaxed text-[#181512]">
                  {step.instruction}
                </p>

                {step.estimated_minutes !== null && (
                  <span className="inline-flex items-center gap-1 rounded-full border border-[#D8C6B2] bg-[#FFF8F0] px-2.5 py-0.5 text-[11px] font-semibold text-[#595047] tabular-nums">
                    <Clock
                      className="h-3 w-3 text-[#9E3D08]"
                      aria-hidden="true"
                    />
                    <span>Ước tính {step.estimated_minutes} phút</span>
                  </span>
                )}
              </div>
            </li>
          ))}
        </ol>
      </section>

      {/* ===================================================================
          KHỐI THẺ CÔNG THỨC (RECIPE TAGS) & NGUỒN THAM KHẢO (LEGAL-01)
         =================================================================== */}
      <section
        aria-label="Thẻ công thức và nguồn tham khảo"
        className="space-y-5 border-t border-[#BDA992]/70 pt-8"
      >
        <div>
          <h2 className="inline-block rounded-[6px] bg-[#F59E28] px-3.5 py-1 font-serif text-[16px] font-bold uppercase tracking-wide text-[#181512]">
            Thẻ công thức
          </h2>

          <div className="mt-3.5 flex flex-wrap gap-2">
            {recipeTags.map((tagLabel) => (
              <span
                key={tagLabel}
                className="rounded-[7px] border border-[#6E6052] bg-[#FFF8F0]/55 px-3 py-1 text-xs font-medium text-[#181512]"
              >
                {tagLabel}
              </span>
            ))}
          </div>
        </div>

        {(recipe.source_name || recipe.source_url || recipe.content_license) && (
          <footer
            data-testid="recipe-source-footer"
            className="flex flex-wrap items-center justify-between gap-3 rounded-tl-[18px] rounded-br-[18px] rounded-tr-[6px] rounded-bl-[6px] border border-[#D8C6B2] bg-[#FFF8F0] px-5 py-4 text-xs text-[#595047]"
          >
            <div className="flex flex-wrap items-center gap-2">
              <BookOpen
                className="h-4 w-4 text-[#9E3D08]"
                aria-hidden="true"
              />
              <span className="font-semibold text-[#181512]">
                Nguồn công thức:
              </span>
              <span>{recipe.source_name ?? 'Biên soạn nội bộ FoodVision'}</span>
              {isSafeHttpUrl(recipe.source_url) && (
                <a
                  href={recipe.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex min-h-[34px] items-center gap-1 rounded-full px-2 py-1 font-semibold text-[#9E3D08] hover:underline"
                >
                  <span>Liên kết gốc</span>
                  <ExternalLink className="h-3 w-3" aria-hidden="true" />
                </a>
              )}
            </div>

            {recipe.content_license && (
              <span className="rounded-full border border-[#DECDBE] bg-[#F7EFE5] px-3 py-1 font-semibold text-[#181512]">
                Giấy phép: {recipe.content_license}
              </span>
            )}
          </footer>
        )}
      </section>
    </article>
  );
};
