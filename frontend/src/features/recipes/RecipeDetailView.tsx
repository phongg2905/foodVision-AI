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

export interface RecipeDetailViewProps {
  recipeId: string;
  backLabel: string;
  recommendationContext?: RecommendationItem;
  onBack: () => void;
}

const CUISINE_BADGE_MAP: Record<CuisineCode, string> = {
  VN: 'Món Việt (VN)',
  EU: 'Món Âu (EU)',
  US: 'Món Mỹ (US)',
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
        <div className="h-9 w-52 animate-pulse rounded-full bg-[#DFD3C3]" />
        <div className="grid grid-cols-1 items-center gap-8 lg:grid-cols-12">
          <div className="mx-auto aspect-square w-64 animate-pulse rounded-full bg-[#DFD3C3] sm:w-80 lg:col-span-5" />
          <div className="space-y-4 lg:col-span-7">
            <div className="h-10 w-3/4 animate-pulse rounded-xl bg-[#DFD3C3]" />
            <div className="h-20 w-full animate-pulse rounded-xl bg-white/70" />
            <div className="h-20 w-full animate-pulse rounded-xl bg-white" />
          </div>
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
          className="inline-flex items-center gap-1.5 rounded-full border border-[#DFD3C3] bg-white px-4 py-2 text-xs font-semibold text-[#181512] transition hover:border-[#E87838] hover:text-[#C2591B]"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
          <span>{backLabel}</span>
        </button>

        <div
          role="alert"
          data-testid="recipe-detail-error"
          className="rounded-bl-[16px] rounded-br-[28px] rounded-tl-[28px] rounded-tr-[16px] border border-[#F2C7A8] bg-white p-8 text-center shadow-[0_12px_34px_rgba(24,21,18,0.05)]"
        >
          <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[#FDF0E7] text-[#C2591B]">
            <AlertCircle className="h-6 w-6" aria-hidden="true" />
          </span>
          <h1 className="mt-4 font-serif text-2xl font-bold text-[#181512]">
            Không tìm thấy công thức món ăn
          </h1>
          <p className="mx-auto mt-2 max-w-md text-sm text-[#6E655C]">
            {errorMessage ??
              'Công thức không tồn tại hoặc chưa được xuất bản công khai.'}
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <button
              type="button"
              onClick={onBack}
              className="inline-flex items-center gap-2 rounded-full bg-[#E87838] px-5 py-2.5 text-xs font-semibold text-white transition hover:bg-[#D16426]"
            >
              <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
              <span>{backLabel}</span>
            </button>
            <button
              type="button"
              onClick={() => setRetryTick((n) => n + 1)}
              className="inline-flex items-center gap-2 rounded-full border border-[#DFD3C3] bg-[#FAF7F2] px-5 py-2.5 text-xs font-semibold text-[#181512] transition hover:border-[#181512]"
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

  return (
    <article
      data-testid={`recipe-detail-view-${recipe.slug}`}
      className="space-y-9 py-2"
    >
      {/* Thanh điều hướng quay lại */}
      <div className="flex items-center justify-between gap-3">
        <button
          type="button"
          data-testid="recipe-detail-back-btn"
          onClick={onBack}
          className="inline-flex items-center gap-2 rounded-full border border-[#DFD3C3] bg-white px-4 py-2 text-xs font-semibold text-[#181512] transition hover:border-[#E87838] hover:text-[#C2591B]"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
          <span>{backLabel}</span>
        </button>

        <span className="rounded-full border border-[#DFD3C3] bg-white px-3.5 py-1.5 text-xs font-bold text-[#C2591B]">
          {CUISINE_BADGE_MAP[recipe.cuisine_code]}
          {recipe.country_code && recipe.country_code !== recipe.cuisine_code
            ? ` · ${recipe.country_code}`
            : ''}
        </span>
      </div>

      {/* ===================================================================
          HERO 2 CỘT CHUẨN "CHICKEN PASTA" CỦA NEWTASTE
         =================================================================== */}
      <section
        aria-label="Tổng quan món ăn"
        className="grid grid-cols-1 items-center gap-8 lg:grid-cols-12 lg:gap-12"
      >
        {/* Cột trái: Đĩa món ăn tròn lớn viền trắng dày */}
        <div className="flex justify-center lg:col-span-5">
          <div className="aspect-square w-64 overflow-hidden rounded-full border-[6px] border-white bg-[#181512] shadow-[0_18px_44px_rgba(24,21,18,0.16)] sm:w-80 lg:w-full lg:max-w-[360px]">
            {recipe.cover_image_url && !imageError ? (
              <img
                src={recipe.cover_image_url}
                alt={recipe.name_vi}
                onError={() => setImageError(true)}
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="flex h-full w-full flex-col items-center justify-center gap-2 bg-[#2A2421] text-[#E87838]">
                <Utensils className="h-10 w-10" aria-hidden="true" />
                <span className="font-serif text-sm font-bold">
                  FoodVision AI
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Cột phải: Tiêu đề Serif + Mô tả + Dải Thông số vạch chia dọc */}
        <div className="space-y-6 lg:col-span-7">
          <div>
            <h1 className="font-serif text-3xl font-bold leading-tight tracking-tight text-[#181512] sm:text-4xl lg:text-[42px]">
              {recipe.name_vi}
            </h1>

            {recipe.description && (
              <p className="mt-3 max-w-[65ch] text-[15px] leading-relaxed text-[#4A4139]">
                {recipe.description}
              </p>
            )}
          </div>

          {/* Dải 4 Thông số Vạch Chia Dọc kiểu NEWTASTE */}
          <div
            data-testid="recipe-time-strip"
            className="grid grid-cols-2 divide-y divide-[#DFD3C3] overflow-hidden rounded-bl-[14px] rounded-br-[24px] rounded-tl-[24px] rounded-tr-[14px] border border-[#DFD3C3] bg-white sm:grid-cols-4 sm:divide-x sm:divide-y-0"
          >
            <div className="px-4 py-4 text-center">
              <span className="block text-[11px] font-bold uppercase tracking-wider text-[#6E655C]">
                Nguyên liệu
              </span>
              <span className="mt-1 block font-serif text-2xl font-bold text-[#181512] tabular-nums">
                {recipe.ingredients.length}
              </span>
              <span className="text-[11px] text-[#6E655C]">thành phần</span>
            </div>

            <div className="px-4 py-4 text-center">
              <span className="block text-[11px] font-bold uppercase tracking-wider text-[#6E655C]">
                Sơ chế
              </span>
              <span className="mt-1 block font-serif text-2xl font-bold text-[#181512] tabular-nums">
                {recipe.prep_minutes}
              </span>
              <span className="text-[11px] text-[#6E655C]">phút</span>
            </div>

            <div className="px-4 py-4 text-center">
              <span className="block text-[11px] font-bold uppercase tracking-wider text-[#6E655C]">
                Nấu &amp; chờ
              </span>
              <span className="mt-1 block font-serif text-2xl font-bold text-[#181512] tabular-nums">
                {recipe.cook_minutes}
              </span>
              <span className="text-[11px] text-[#6E655C]">phút</span>
            </div>

            <div className="bg-[#FAF7F2] px-4 py-4 text-center">
              <span className="block text-[11px] font-bold uppercase tracking-wider text-[#C2591B]">
                Tổng cộng
              </span>
              <span className="mt-1 block font-serif text-2xl font-bold text-[#C2591B] tabular-nums">
                {recipe.total_minutes}
              </span>
              <span className="text-[11px] text-[#6E655C]">phút</span>
            </div>
          </div>

          {/* Ghi chú BR-05 */}
          <p
            data-testid="cook-time-br05-note"
            className="flex items-start gap-2 text-[12px] leading-relaxed text-[#574D44]"
          >
            <Clock
              className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#E87838]"
              aria-hidden="true"
            />
            <span>
              Thời gian nấu đã bao gồm cả thời gian ướp và chờ chế biến (nếu
              công thức có bước ướp).
            </span>
          </p>

          {/* Ngữ cảnh gợi ý (khi mở từ RecommendationResultsView) */}
          {recommendationContext && (
            <div
              data-testid="detail-recommendation-summary"
              className="rounded-2xl border border-[#DFD3C3] bg-white px-4 py-3.5 text-[13px] text-[#181512]"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-bold text-[#157358]">
                  Độ phù hợp gian bếp:{' '}
                  <span className="tabular-nums">
                    {Math.round(recommendationContext.score * 100) / 100} điểm
                  </span>
                </span>
                <span className="text-xs font-semibold text-[#C2591B]">
                  {recommendationContext.availability === 'ready'
                    ? 'Có thể nấu ngay'
                    : `Cần thêm ${recommendationContext.missing_required_ingredient_ids.length} nguyên liệu`}
                </span>
              </div>
              <p className="mt-1 text-xs text-[#574D44]">
                {recommendationContext.explanation_vi}
              </p>
            </div>
          )}
        </div>
      </section>

      {/* ===================================================================
          KHỐI NHÃN DINH DƯỠNG ĐỊNH TÍNH & TUYÊN BỐ MIỄN TRỪ BR-03 (TC-15)
         =================================================================== */}
      <section
        aria-label="Nhãn dinh dưỡng tham khảo và miễn trừ trách nhiệm"
        data-testid="nutrition-evidence-section"
        className="overflow-hidden rounded-bl-[16px] rounded-br-[28px] rounded-tl-[28px] rounded-tr-[16px] border border-[#DFD3C3] bg-white shadow-[0_12px_34px_rgba(24,21,18,0.05)]"
      >
        <div className="bg-[#E87838] px-6 py-3.5 text-white">
          <h2 className="font-serif text-lg font-bold">
            Nhãn Dinh Dưỡng Tham Khảo
          </h2>
        </div>

        <div className="space-y-5 p-5 sm:p-6">
          {recipe.nutrition_evidence.length > 0 ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {recipe.nutrition_evidence.map((ev) => (
                <div
                  key={ev.tag.id}
                  data-testid={`nutrition-tag-${ev.tag.code}`}
                  className="rounded-2xl border border-[#EFE6D8] bg-[#FAF7F2] p-4"
                >
                  <span className="inline-flex rounded-full bg-[#E87838] px-3 py-1 text-[12px] font-bold text-white">
                    {ev.tag.name_vi}
                  </span>

                  {ev.tag.description && (
                    <p className="mt-2.5 text-[13px] leading-relaxed text-[#4A4139]">
                      {ev.tag.description}
                    </p>
                  )}

                  {ev.note && (
                    <p className="mt-1.5 text-[12px] italic text-[#6E655C]">
                      {ev.note}
                    </p>
                  )}

                  {ev.source_urls.length > 0 && (
                    <div className="mt-3 flex flex-wrap items-center gap-2">
                      <span className="text-[11px] font-semibold text-[#574D44]">
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
                            className="inline-flex items-center gap-1 rounded-full border border-[#DFD3C3] bg-white px-2.5 py-0.5 text-[11px] font-semibold text-[#C2591B] transition hover:border-[#E87838] hover:underline"
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
              ))}
            </div>
          ) : (
            <p
              data-testid="nutrition-empty-note"
              className="rounded-2xl border border-dashed border-[#DFD3C3] bg-[#FAF7F2] px-4 py-3.5 text-[13px] text-[#574D44]"
            >
              Công thức này hiện chưa có nhãn dinh dưỡng định tính được kiểm
              duyệt.
            </p>
          )}

          {/* BẮT BUỘC HIỂN THỊ NGUYÊN VĂN TUYÊN BỐ MIỄN TRỪ BR-03 */}
          <div
            data-testid="nutrition-disclaimer"
            className="flex items-start gap-3 rounded-2xl border border-[#F2C7A8] bg-[#FDF0E7] p-4 text-[13px] leading-relaxed text-[#6E3414]"
          >
            <Info
              className="mt-0.5 h-4 w-4 shrink-0 text-[#C2591B]"
              aria-hidden="true"
            />
            <p>{MANDATORY_NUTRITION_DISCLAIMER}</p>
          </div>
        </div>
      </section>

      {/* ===================================================================
          KHỐI NGUYÊN LIỆU & GIA VỊ CẦN CHUẨN BỊ (TÁCH RIÊNG CATEGORY='pantry')
         =================================================================== */}
      <div className="grid grid-cols-1 items-start gap-7 lg:grid-cols-12">
        {/* Cột 1: Nguyên liệu chính/phụ (`category !== 'pantry'`) */}
        <section
          aria-label="Nguyên liệu chính và phụ"
          data-testid="recipe-main-ingredients"
          className="overflow-hidden rounded-bl-[16px] rounded-br-[28px] rounded-tl-[28px] rounded-tr-[16px] border border-[#DFD3C3] bg-white shadow-[0_12px_34px_rgba(24,21,18,0.05)] lg:col-span-7"
        >
          <div className="flex items-center justify-between bg-[#E87838] px-6 py-3.5 text-white">
            <h2 className="font-serif text-lg font-bold">Nguyên Liệu</h2>
            <span className="rounded-full bg-white/20 px-2.5 py-0.5 text-xs font-bold tabular-nums">
              {mainIngredients.length} mục
            </span>
          </div>

          {mainIngredients.length === 0 ? (
            <p className="p-6 text-sm text-[#6E655C]">
              Chưa cập nhật danh sách nguyên liệu.
            </p>
          ) : (
            <ul className="divide-y divide-[#F2ECE4] px-6 py-2">
              {mainIngredients.map((item) => {
                const isMatched = matchedIdSet.has(item.ingredient_id);
                const isMissing = missingIdSet.has(item.ingredient_id);

                return (
                  <li
                    key={`${item.ingredient_id}-${item.sort_order}`}
                    className="flex flex-wrap items-center justify-between gap-2 py-3.5"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[15px] font-semibold text-[#181512]">
                        {item.name_vi}
                      </span>

                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                          item.is_required
                            ? 'bg-[#FAF7F2] text-[#574D44]'
                            : 'border border-dashed border-[#DFD3C3] text-[#6E655C]'
                        }`}
                      >
                        {item.is_required ? 'Bắt buộc' : 'Tùy chọn'}
                      </span>

                      {isMatched && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-[#E7F8F2] px-2 py-0.5 text-[10px] font-bold text-[#157358]">
                          <Check className="h-3 w-3 stroke-[2.5]" />
                          <span>Đã có</span>
                        </span>
                      )}

                      {isMissing && (
                        <span className="rounded-full bg-[#FDF0E7] px-2 py-0.5 text-[10px] font-bold text-[#C2591B]">
                          Cần chuẩn bị
                        </span>
                      )}
                    </div>

                    <span className="text-[14px] font-medium text-[#4A4139] tabular-nums">
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
          className="overflow-hidden rounded-bl-[16px] rounded-br-[28px] rounded-tl-[28px] rounded-tr-[16px] border border-[#DFD3C3] bg-white shadow-[0_12px_34px_rgba(24,21,18,0.05)] lg:col-span-5"
        >
          <div className="flex items-center justify-between bg-[#E87838] px-6 py-3.5 text-white">
            <h2 className="font-serif text-lg font-bold">
              Gia Vị Cần Chuẩn Bị
            </h2>
            <span className="rounded-full bg-white/20 px-2.5 py-0.5 text-xs font-bold tabular-nums">
              {pantryIngredients.length} mục
            </span>
          </div>

          {pantryIngredients.length === 0 ? (
            <p className="p-6 text-sm text-[#6E655C]">
              Không yêu cầu gia vị cơ bản.
            </p>
          ) : (
            <ul className="divide-y divide-[#F2ECE4] px-6 py-2">
              {pantryIngredients.map((item) => {
                const isMissing = missingIdSet.has(item.ingredient_id);
                return (
                  <li
                    key={`${item.ingredient_id}-${item.sort_order}`}
                    className="flex items-center justify-between gap-2 py-3.5"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-[15px] font-semibold text-[#181512]">
                        {item.name_vi}
                      </span>
                      {isMissing && (
                        <span className="rounded-full bg-[#FDF0E7] px-2 py-0.5 text-[10px] font-bold text-[#C2591B]">
                          Đang thiếu
                        </span>
                      )}
                    </div>

                    <span className="text-[14px] font-medium text-[#4A4139] tabular-nums">
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
          KHỐI CÁC BƯỚC CHẾ BIẾN ĐÁNH SỐ THỨ TỰ
         =================================================================== */}
      <section
        aria-label="Các bước chế biến"
        className="overflow-hidden rounded-bl-[16px] rounded-br-[28px] rounded-tl-[28px] rounded-tr-[16px] border border-[#DFD3C3] bg-white shadow-[0_12px_34px_rgba(24,21,18,0.05)]"
      >
        <div className="flex items-center justify-between bg-[#E87838] px-6 py-3.5 text-white">
          <h2 className="font-serif text-lg font-bold">Các Bước Chế Biến</h2>
          <span className="rounded-full bg-white/20 px-2.5 py-0.5 text-xs font-bold tabular-nums">
            {sortedSteps.length} bước
          </span>
        </div>

        <ol
          data-testid="recipe-steps-list"
          className="divide-y divide-[#F2ECE4] p-5 sm:p-6"
        >
          {sortedSteps.map((step) => (
            <li
              key={step.step_no}
              className="flex items-start gap-4 py-4 first:pt-1 last:pb-1"
            >
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#E87838] font-serif text-sm font-bold text-white tabular-nums">
                {step.step_no}
              </span>

              <div className="flex-1 space-y-1.5">
                <p className="max-w-[70ch] text-[15px] leading-relaxed text-[#181512]">
                  {step.instruction}
                </p>

                {step.estimated_minutes !== null && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-[#FAF7F2] px-2.5 py-0.5 text-[11px] font-semibold text-[#574D44] tabular-nums">
                    <Clock className="h-3 w-3 text-[#E87838]" aria-hidden="true" />
                    <span>Ước tính {step.estimated_minutes} phút</span>
                  </span>
                )}
              </div>
            </li>
          ))}
        </ol>
      </section>

      {/* ===================================================================
          NGUỒN THAM KHẢO & GIẤY PHÉP (LEGAL-01)
         =================================================================== */}
      {(recipe.source_name || recipe.source_url || recipe.content_license) && (
        <footer
          data-testid="recipe-source-footer"
          className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[#DFD3C3] bg-white px-5 py-4 text-xs text-[#574D44]"
        >
          <div className="flex flex-wrap items-center gap-2">
            <BookOpen className="h-4 w-4 text-[#E87838]" aria-hidden="true" />
            <span className="font-semibold text-[#181512]">
              Nguồn công thức:
            </span>
            <span>{recipe.source_name ?? 'Biên soạn nội bộ FoodVision'}</span>
            {isSafeHttpUrl(recipe.source_url) && (
              <a
                href={recipe.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 font-semibold text-[#C2591B] hover:underline"
              >
                <span>Liên kết gốc</span>
                <ExternalLink className="h-3 w-3" aria-hidden="true" />
              </a>
            )}
          </div>

          {recipe.content_license && (
            <span className="rounded-full bg-[#FAF7F2] px-3 py-1 font-semibold text-[#181512]">
              Giấy phép: {recipe.content_license}
            </span>
          )}
        </footer>
      )}
    </article>
  );
};
