import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import { ApiClientError } from '../../shared/api/client';
import { detectIngredientsFromImage } from '../../shared/api/aiDetectApi';
import { DetectResponse, Ingredient } from '../../shared/api/types';
import { BoundingBoxStage } from './components/BoundingBoxStage';
import {
  createDemoScanFile,
  DemoFixtureKind,
} from './utils/demoScanFixtures';

export interface VisionScanPanelProps {
  catalogIngredients: Ingredient[];
  onConfirmHitlIngredients: (
    confirmedIngredients: Ingredient[],
    scanId: string | null
  ) => void;
  onFallbackToManual: () => void;
  onClose: () => void;
}

interface ErrorState {
  status: number;
  code: string;
  message: string;
  canRetry: boolean;
}

/**
 * Hộp thoại Nhận diện nguyên liệu qua ảnh (TP 01, TP 02, TP 14 — Thẻ #22):
 * Thiết kế mặt phẳng biên tập NEWTASTE: không lồng hộp chồng hộp, ngôn ngữ đời thường tự nhiên,
 * danh sách nguyên liệu phân cách bằng đường kẻ mảnh tinh tế.
 */
export const VisionScanPanel: React.FC<VisionScanPanelProps> = ({
  catalogIngredients,
  onConfirmHitlIngredients,
  onFallbackToManual,
  onClose,
}) => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const cameraInputRef = useRef<HTMLInputElement | null>(null);
  const previewUrlRef = useRef<string | null>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [exifOrientation, setExifOrientation] = useState<number>(1);
  const [isScanning, setIsScanning] = useState(false);
  const [errorState, setErrorState] = useState<ErrorState | null>(null);
  const [detectResult, setDetectResult] = useState<DetectResponse | null>(null);

  const [checkedClearIds, setCheckedClearIds] = useState<Set<string>>(
    () => new Set()
  );
  const [checkedUncertainIds, setCheckedUncertainIds] = useState<Set<string>>(
    () => new Set()
  );
  const [relabelMap, setRelabelMap] = useState<Record<string, string>>({});
  const [hoveredIngredientId, setHoveredIngredientId] = useState<string | null>(
    null
  );

  const validNonPantryIngredients = catalogIngredients.filter(
    (item) => item.category !== 'pantry' && item.is_active
  );
  const ingredientById = new Map(
    validNonPantryIngredients.map((item) => [item.id, item] as const)
  );

  const revokeCurrentPreview = () => {
    if (
      previewUrlRef.current &&
      typeof URL !== 'undefined' &&
      typeof URL.revokeObjectURL === 'function'
    ) {
      URL.revokeObjectURL(previewUrlRef.current);
      previewUrlRef.current = null;
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      revokeCurrentPreview();
    };
  }, [onClose]);

  const runDetection = async (file: File) => {
    setSelectedFile(file);
    setErrorState(null);
    setDetectResult(null);
    setIsScanning(true);

    try {
      const { response, inspection } = await detectIngredientsFromImage(file, {
        saveHistory: false,
      });

      revokeCurrentPreview();
      const nextUrl =
        typeof URL !== 'undefined' && typeof URL.createObjectURL === 'function'
          ? URL.createObjectURL(file)
          : 'data:image/gif;base64,R0lGODlhAQABAAAAACw=';
      previewUrlRef.current = nextUrl;

      setPreviewUrl(nextUrl);
      setExifOrientation(inspection.exifOrientation);
      setDetectResult(response);

      setCheckedClearIds(
        new Set(response.clear_ingredients.map((item) => item.ingredient_id))
      );
      setCheckedUncertainIds(new Set());
      setRelabelMap({});
    } catch (err: unknown) {
      if (err instanceof ApiClientError) {
        const canRetry = err.status >= 500 || err.status === 429;
        setErrorState({
          status: err.status,
          code: err.code,
          message: err.message,
          canRetry,
        });
      } else {
        setErrorState({
          status: 500,
          code: 'NETWORK_ERROR',
          message:
            'Chưa kết nối được dịch vụ nhận diện ảnh. Bạn có thể thử lại hoặc tự gõ tên nguyên liệu.',
          canRetry: true,
        });
      }
    } finally {
      setIsScanning(false);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    void runDetection(file);
  };

  const handleLoadDemoFixture = async (kind: DemoFixtureKind) => {
    const demoFile = await createDemoScanFile(kind);
    await runDetection(demoFile);
  };

  const handleToggleClear = (id: string) => {
    setCheckedClearIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleToggleUncertain = (originalId: string) => {
    setCheckedUncertainIds((prev) => {
      const next = new Set(prev);
      if (next.has(originalId)) {
        next.delete(originalId);
      } else {
        next.add(originalId);
      }
      return next;
    });
  };

  const handleRelabelUncertain = (originalId: string, nextTargetId: string) => {
    setRelabelMap((prev) => ({
      ...prev,
      [originalId]: nextTargetId,
    }));
    setCheckedUncertainIds((prev) => {
      const next = new Set(prev);
      next.add(originalId);
      return next;
    });
  };

  const resolvedConfirmedIngredients: Ingredient[] = (() => {
    if (!detectResult) return [];
    const seenIds = new Set<string>();
    const list: Ingredient[] = [];

    const pushById = (id: string, fallbackNameVi: string) => {
      if (!id || seenIds.has(id)) return;
      const found = ingredientById.get(id);
      if (found) {
        seenIds.add(found.id);
        list.push(found);
      } else {
        seenIds.add(id);
        list.push({
          id,
          slug: id,
          name_vi: fallbackNameVi,
          category: 'other',
          is_active: true,
        });
      }
    };

    for (const item of detectResult.clear_ingredients) {
      if (checkedClearIds.has(item.ingredient_id)) {
        pushById(item.ingredient_id, item.name_vi);
      }
    }

    for (const item of detectResult.uncertain_ingredients) {
      if (checkedUncertainIds.has(item.ingredient_id)) {
        const targetId = relabelMap[item.ingredient_id] ?? item.ingredient_id;
        const targetObj = ingredientById.get(targetId);
        pushById(targetId, targetObj?.name_vi ?? item.name_vi);
      }
    }

    return list;
  })();

  const relabelOverlayInfo: Record<string, { id: string; name_vi: string }> = {};
  Object.entries(relabelMap).forEach(([origId, targetId]) => {
    const found = ingredientById.get(targetId);
    if (found) {
      relabelOverlayInfo[origId] = { id: found.id, name_vi: found.name_vi };
    }
  });

  const handleApplyHitl = () => {
    if (resolvedConfirmedIngredients.length === 0 || !detectResult) return;
    onConfirmHitlIngredients(resolvedConfirmedIngredients, detectResult.scan_id);
  };

  const handleResetScan = () => {
    revokeCurrentPreview();
    setPreviewUrl(null);
    setSelectedFile(null);
    setDetectResult(null);
    setErrorState(null);
    setExifOrientation(1);
  };

  const hasDetections =
    Boolean(detectResult) &&
    ((detectResult?.clear_ingredients.length ?? 0) > 0 ||
      (detectResult?.uncertain_ingredients.length ?? 0) > 0);

  const dialogNode = (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="vision-dialog-title"
      data-testid="vision-scan-panel"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#181512]/45 p-4 backdrop-blur-[2px]"
    >
      <div className="relative max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-[20px] bg-[#FFF8F0] p-6 shadow-[0_24px_64px_rgba(24,21,18,0.24)] sm:p-8">
        {/* Thanh đầu hộp thoại sạch gọn */}
        <div className="flex items-center justify-between gap-4 border-b border-[#E5D6C5] pb-4">
          <h2
            id="vision-dialog-title"
            className="font-serif text-[23px] font-bold text-[#181512] sm:text-[26px]"
          >
            Nhận diện nguyên liệu qua ảnh
          </h2>

          <button
            type="button"
            aria-label="Đóng hộp thoại quét ảnh"
            onClick={onClose}
            className="inline-flex h-9 w-9 items-center justify-center rounded-full text-[#595047] transition hover:bg-[#EFE2D2] hover:text-[#181512]"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        {/* Input tệp ẩn */}
        <input
          ref={fileInputRef}
          type="file"
          data-testid="vision-file-input"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleFileInputChange}
          className="sr-only"
        />
        <input
          ref={cameraInputRef}
          type="file"
          data-testid="vision-camera-input"
          accept="image/jpeg,image/png,image/webp"
          capture="environment"
          onChange={handleFileInputChange}
          className="sr-only"
        />

        {/* TRẠNG THÁI 1: VÙNG TẢI ẢNH MỞ THOÁNG */}
        {!detectResult && !isScanning && !errorState && (
          <div
            data-testid="vision-dropzone"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const dropped = e.dataTransfer.files?.[0];
              if (dropped) {
                void runDetection(dropped);
              }
            }}
            className="mt-6 rounded-[14px] border border-dashed border-[#C7B29B] px-6 py-10 text-center transition hover:border-[#B4490E]"
          >
            <p className="font-serif text-[20px] font-bold text-[#181512]">
              Kéo thả ảnh nguyên liệu vào đây
            </p>
            <p className="mx-auto mt-1.5 max-w-md text-[13.5px] leading-relaxed text-[#595047]">
              Chụp rổ rau củ, bàn bếp hoặc ngăn mát tủ lạnh (JPG, PNG, WebP tối
              đa 5 MB). Bạn luôn được xem và chỉnh lại danh sách trước khi tìm
              món.
            </p>

            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
              <button
                type="button"
                data-testid="vision-select-file-btn"
                onClick={() => fileInputRef.current?.click()}
                className="inline-flex min-h-[42px] items-center justify-center rounded-tl-[12px] rounded-br-[12px] rounded-tr-[4px] rounded-bl-[4px] bg-[#B4490E] px-6 py-2 text-[13.5px] font-semibold text-white transition hover:bg-[#963B0A]"
              >
                Chọn ảnh từ máy
              </button>

              <button
                type="button"
                data-testid="vision-open-camera-btn"
                onClick={() => cameraInputRef.current?.click()}
                className="inline-flex min-h-[42px] items-center justify-center rounded-tl-[12px] rounded-br-[12px] rounded-tr-[4px] rounded-bl-[4px] border border-[#B89F86] px-5 py-2 text-[13.5px] font-medium text-[#181512] transition hover:border-[#181512]"
              >
                Mở máy ảnh
              </button>
            </div>

            <div className="mt-7 flex flex-wrap items-center justify-center gap-x-4 gap-y-1.5 text-[12.5px] text-[#595047]">
              <span>Thử nhanh bằng ảnh mẫu:</span>
              <button
                type="button"
                data-testid="demo-fixture-basket-hitl"
                onClick={() => void handleLoadDemoFixture('basket-hitl')}
                className="font-medium text-[#B4490E] underline-offset-4 hover:underline"
              >
                Rổ rau củ trên bàn
              </button>
              <span aria-hidden="true" className="text-[#C7B29B]">
                ·
              </span>
              <button
                type="button"
                data-testid="demo-fixture-portrait-exif"
                onClick={() => void handleLoadDemoFixture('portrait-exif')}
                className="font-medium text-[#B4490E] underline-offset-4 hover:underline"
              >
                Ảnh chụp dọc điện thoại
              </button>
              <span aria-hidden="true" className="text-[#C7B29B]">
                ·
              </span>
              <button
                type="button"
                data-testid="demo-fixture-blur-empty"
                onClick={() => void handleLoadDemoFixture('blur-empty')}
                className="font-medium text-[#B4490E] underline-offset-4 hover:underline"
              >
                Ảnh thiếu sáng
              </button>
            </div>
          </div>
        )}

        {/* TRẠNG THÁI 2: ĐANG NHẬN DIỆN */}
        {isScanning && (
          <div
            data-testid="vision-scanning-state"
            aria-live="polite"
            className="py-14 text-center"
          >
            <p className="font-serif text-[20px] font-bold text-[#181512]">
              Đang nhận diện nguyên liệu trong ảnh...
            </p>
            <p className="mt-1.5 text-[13.5px] text-[#595047]">
              Vui lòng đợi trong giây lát.
            </p>
          </div>
        )}

        {/* TRẠNG THÁI 3: LỖI TỆP HOẶC HẾT THỜI GIAN CHỜ */}
        {errorState && !isScanning && (
          <div
            role="alert"
            data-testid="vision-error-banner"
            data-error-code={errorState.code}
            className="mt-6 py-4"
          >
            <h3 className="font-serif text-[19px] font-bold text-[#181512]">
              Chưa thể đọc nguyên liệu từ ảnh này
            </h3>
            <p className="mt-1.5 max-w-[58ch] text-[14px] leading-relaxed text-[#4A4037]">
              {errorState.message}
            </p>

            <div className="mt-5 flex flex-wrap items-center gap-3">
              {errorState.canRetry && selectedFile && (
                <button
                  type="button"
                  data-testid="vision-retry-btn"
                  onClick={() => void runDetection(selectedFile)}
                  className="inline-flex min-h-[40px] items-center rounded-tl-[12px] rounded-br-[12px] rounded-tr-[4px] rounded-bl-[4px] bg-[#B4490E] px-5 py-2 text-[13px] font-semibold text-white transition hover:bg-[#963B0A]"
                >
                  Thử lại
                </button>
              )}

              <button
                type="button"
                data-testid="fallback-manual-input-btn"
                onClick={onFallbackToManual}
                className="inline-flex min-h-[40px] items-center rounded-tl-[12px] rounded-br-[12px] rounded-tr-[4px] rounded-bl-[4px] bg-[#181512] px-5 py-2 text-[13px] font-semibold text-[#FFF8F0] transition hover:bg-[#2E2720]"
              >
                Tự gõ tên nguyên liệu
              </button>

              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="inline-flex min-h-[40px] items-center px-3 py-2 text-[13px] font-medium text-[#595047] underline-offset-4 hover:text-[#181512] hover:underline"
              >
                Chọn ảnh khác
              </button>
            </div>
          </div>
        )}

        {/* TRẠNG THÁI 4: KẾT QUẢ QUÉT — 2 CỘT MẶT PHẲNG, KHÔNG HỘP LỒNG HỘP */}
        {detectResult && previewUrl && !isScanning && (
          <div className="mt-6 grid grid-cols-1 items-start gap-7 md:grid-cols-12">
            {/* Cột trái: Bức ảnh thực tế + khung nhận diện mảnh */}
            <div className="md:col-span-6">
              <BoundingBoxStage
                imageUrl={previewUrl}
                imageAlt={selectedFile?.name || 'Ảnh nguyên liệu'}
                detections={detectResult.detections}
                exifOrientation={exifOrientation}
                highlightedIngredientId={hoveredIngredientId}
                confirmedUncertainIds={checkedUncertainIds}
                relabelByOriginalId={relabelOverlayInfo}
              />

              <div className="mt-3 text-center">
                <button
                  type="button"
                  data-testid="vision-change-image-btn"
                  onClick={handleResetScan}
                  className="text-[13px] font-medium text-[#B4490E] underline-offset-4 hover:underline"
                >
                  Chọn ảnh khác
                </button>
              </div>
            </div>

            {/* Cột phải: Một danh sách phẳng duy nhất ngăn bằng đường kẻ mảnh */}
            <div className="md:col-span-6">
              {!hasDetections ? (
                <div data-testid="hitl-empty-detections" className="py-2">
                  <h3 className="font-serif text-[20px] font-bold text-[#181512]">
                    Chưa nhìn rõ nguyên liệu trong ảnh
                  </h3>
                  <p className="mt-2 text-[13.5px] leading-relaxed text-[#4A4037]">
                    Ảnh hơi tối, mờ hoặc nguyên liệu bị che khuất. Bạn có thể tự
                    gõ tên nguyên liệu vào ô tìm kiếm để tìm món ngay.
                  </p>

                  <div className="mt-5 flex flex-wrap items-center gap-3">
                    <button
                      type="button"
                      data-testid="fallback-manual-input-btn"
                      onClick={onFallbackToManual}
                      className="inline-flex min-h-[40px] items-center rounded-tl-[12px] rounded-br-[12px] rounded-tr-[4px] rounded-bl-[4px] bg-[#B4490E] px-5 py-2 text-[13px] font-semibold text-white transition hover:bg-[#963B0A]"
                    >
                      Tự gõ tên nguyên liệu
                    </button>
                    <button
                      type="button"
                      onClick={handleResetScan}
                      className="inline-flex min-h-[40px] items-center px-3 py-2 text-[13px] font-medium text-[#595047] underline-offset-4 hover:text-[#181512] hover:underline"
                    >
                      Thử ảnh khác
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  <p className="text-[13.5px] text-[#4A4037]">
                    Kiểm tra lại các nguyên liệu tìm thấy trong ảnh trước khi
                    đưa vào tủ bếp:
                  </p>

                  {/* Danh sách phẳng thống nhất (không lồng hộp con) */}
                  <div className="mt-3 divide-y divide-[#E6D8C7] border-y border-[#E6D8C7]">
                    {detectResult.clear_ingredients.map((item) => {
                      const isChecked = checkedClearIds.has(item.ingredient_id);
                      return (
                        <label
                          key={item.ingredient_id}
                          data-testid={`hitl-clear-item-${item.ingredient_id}`}
                          onMouseEnter={() =>
                            setHoveredIngredientId(item.ingredient_id)
                          }
                          onMouseLeave={() => setHoveredIngredientId(null)}
                          className="flex min-h-[46px] cursor-pointer items-center justify-between gap-3 py-2.5 select-none"
                        >
                          <span className="flex items-center gap-3">
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={() =>
                                handleToggleClear(item.ingredient_id)
                              }
                              className="h-4 w-4 rounded border-[#B89F86] accent-[#B4490E]"
                            />
                            <span className="text-[15px] font-medium text-[#181512]">
                              {item.name_vi}
                            </span>
                          </span>

                          <span className="text-[12.5px] text-[#6B5E52] tabular-nums">
                            {Math.round(item.max_confidence * 100)}%
                          </span>
                        </label>
                      );
                    })}

                    {detectResult.uncertain_ingredients.length > 0 && (
                      <div
                        data-testid="hitl-uncertain-alert"
                        className="divide-y divide-[#E6D8C7]"
                      >
                        {detectResult.uncertain_ingredients.map(
                          (item, uIdx) => {
                            const isConfirmed = checkedUncertainIds.has(
                              item.ingredient_id
                            );
                            const selectedTargetId =
                              relabelMap[item.ingredient_id] ??
                              item.ingredient_id;

                            return (
                              <div
                                key={item.ingredient_id}
                                data-testid={`hitl-uncertain-item-${item.ingredient_id}`}
                                onMouseEnter={() =>
                                  setHoveredIngredientId(selectedTargetId)
                                }
                                onMouseLeave={() => setHoveredIngredientId(null)}
                                className="flex items-center justify-between gap-3 py-2.5"
                              >
                                <label className="inline-flex min-h-[32px] min-w-0 cursor-pointer items-center gap-3">
                                  <input
                                    type="checkbox"
                                    data-testid={`hitl-confirm-checkbox-${item.ingredient_id}`}
                                    checked={isConfirmed}
                                    onChange={() =>
                                      handleToggleUncertain(item.ingredient_id)
                                    }
                                    className="h-4 w-4 shrink-0 rounded border-[#B89F86] accent-[#B4490E]"
                                  />
                                  <span className="min-w-0">
                                    <span className="block truncate text-[15px] font-medium text-[#181512]">
                                      {relabelOverlayInfo[item.ingredient_id]
                                        ?.name_vi ?? item.name_vi}
                                    </span>
                                    <span
                                      data-testid={
                                        uIdx === 0
                                          ? 'hitl-review-badge'
                                          : undefined
                                      }
                                      className="block text-[11.5px] font-medium text-[#B4490E]"
                                    >
                                      Cần kiểm tra lại
                                    </span>
                                  </span>
                                </label>

                                <select
                                  aria-label={`Đổi nhãn cho ${item.name_vi}`}
                                  data-testid={`hitl-relabel-select-${item.ingredient_id}`}
                                  value={selectedTargetId}
                                  onChange={(e) =>
                                    handleRelabelUncertain(
                                      item.ingredient_id,
                                      e.target.value
                                    )
                                  }
                                  className="min-h-[30px] max-w-[125px] shrink-0 cursor-pointer border-b border-[#CDB9A2] bg-transparent py-0.5 text-right text-[12.5px] font-medium text-[#595047] focus:border-[#B4490E] focus:text-[#181512] focus:outline-none"
                                >
                                  {!ingredientById.has(item.ingredient_id) && (
                                    <option value={item.ingredient_id}>
                                      {item.name_vi}
                                    </option>
                                  )}
                                  {validNonPantryIngredients.map((cand) => (
                                    <option key={cand.id} value={cand.id}>
                                      {cand.name_vi}
                                    </option>
                                  ))}
                                </select>
                              </div>
                            );
                          }
                        )}
                      </div>
                    )}
                  </div>

                  {/* Hàng nút chốt tối giản dưới cùng */}
                  <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
                    <button
                      type="button"
                      onClick={onFallbackToManual}
                      className="text-[13px] font-medium text-[#595047] underline-offset-4 hover:text-[#181512] hover:underline"
                    >
                      Tự gõ thêm nguyên liệu
                    </button>

                    <button
                      type="button"
                      data-testid="hitl-apply-btn"
                      disabled={resolvedConfirmedIngredients.length === 0}
                      onClick={handleApplyHitl}
                      className={`inline-flex min-h-[42px] items-center justify-center rounded-tl-[12px] rounded-br-[12px] rounded-tr-[4px] rounded-bl-[4px] px-6 py-2 text-[13.5px] font-semibold tabular-nums transition ${
                        resolvedConfirmedIngredients.length > 0
                          ? 'bg-[#B4490E] text-white shadow-[0_8px_20px_rgba(180,73,14,0.2)] hover:bg-[#963B0A]'
                          : 'cursor-not-allowed bg-[#E5D6C5] text-[#8A7D70]'
                      }`}
                    >
                      Thêm vào tủ bếp ({resolvedConfirmedIngredients.length})
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  if (typeof document !== 'undefined' && document.body) {
    return createPortal(dialogNode, document.body);
  }
  return dialogNode;
};
