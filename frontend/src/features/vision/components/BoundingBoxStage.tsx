import React from 'react';
import {
  Detection,
  REVIEW_CONFIDENCE_THRESHOLD,
} from '../../../shared/api/types';

export interface BoundingBoxStageProps {
  imageUrl: string;
  imageAlt: string;
  detections: Detection[];
  exifOrientation: number;
  highlightedIngredientId?: string | null;
  confirmedUncertainIds?: Set<string>;
  relabelByOriginalId?: Record<string, { id: string; name_vi: string }>;
}

function clamp01(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(1, value));
}

/**
 * Hiển thị trực tiếp bức ảnh thực (không lồng hộp nền thừa) theo đúng chiều EXIF
 * (image-orientation: from-image) và vẽ khung giới hạn mảnh tinh tế bám khít 100% diện tích ảnh.
 */
export const BoundingBoxStage: React.FC<BoundingBoxStageProps> = ({
  imageUrl,
  imageAlt,
  detections,
  exifOrientation,
  highlightedIngredientId = null,
  confirmedUncertainIds,
  relabelByOriginalId = {},
}) => {
  const isExifRotated = exifOrientation > 1;

  return (
    <div className="flex flex-col items-center">
      <div
        data-testid="bbox-upright-stage"
        data-exif-orientation={exifOrientation}
        className="relative inline-block max-w-full overflow-hidden rounded-[14px] bg-[#181512] shadow-[0_12px_30px_rgba(24,21,18,0.14)]"
      >
        <img
          src={imageUrl}
          alt={imageAlt}
          data-testid="bbox-preview-image"
          style={{ imageOrientation: 'from-image' }}
          className="block max-h-[320px] w-auto max-w-full select-none"
        />

        <div
          data-testid="bbox-overlay-layer"
          className="pointer-events-none absolute inset-0"
        >
          {detections.map((det, idx) => {
            const x1 = clamp01(det.bbox.x1);
            const y1 = clamp01(det.bbox.y1);
            const x2 = Math.max(x1 + 0.02, clamp01(det.bbox.x2));
            const y2 = Math.max(y1 + 0.02, clamp01(det.bbox.y2));

            const originalId = det.ingredient_id ?? '';
            const relabeled = originalId
              ? relabelByOriginalId[originalId]
              : undefined;
            const effectiveId = relabeled?.id ?? originalId;
            const displayName =
              relabeled?.name_vi ?? det.ingredient_name ?? det.class_name;

            const isRawUncertain =
              det.needs_confirmation ||
              det.confidence < REVIEW_CONFIDENCE_THRESHOLD;
            const isConfirmedByUser =
              Boolean(originalId) &&
              Boolean(confirmedUncertainIds?.has(originalId));
            const showAsWarning = isRawUncertain && !isConfirmedByUser;

            const isHighlighted =
              Boolean(highlightedIngredientId) &&
              effectiveId === highlightedIngredientId;

            return (
              <div
                key={`${det.class_index}-${idx}`}
                data-testid={`bbox-item-${idx}`}
                data-needs-confirmation={showAsWarning ? 'true' : 'false'}
                style={{
                  left: `${(x1 * 100).toFixed(2)}%`,
                  top: `${(y1 * 100).toFixed(2)}%`,
                  width: `${((x2 - x1) * 100).toFixed(2)}%`,
                  height: `${((y2 - y1) * 100).toFixed(2)}%`,
                }}
                className={`absolute rounded-[6px] transition-all ${
                  showAsWarning
                    ? 'border-[1.5px] border-dashed border-[#FFF8F0] bg-[#B4490E]/20'
                    : 'border-[1.5px] border-[#FFF8F0]/90'
                } ${isHighlighted ? 'ring-2 ring-[#B4490E]' : ''}`}
              >
                <span
                  className={`inline-block max-w-full truncate rounded-br-[5px] px-1.5 py-0.5 text-[10.5px] font-medium leading-tight ${
                    showAsWarning
                      ? 'bg-[#B4490E] text-white'
                      : 'bg-[#181512]/85 text-[#FFF8F0]'
                  }`}
                >
                  {displayName}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {isExifRotated && (
        <p
          data-testid="exif-orientation-badge"
          className="mt-2 text-center text-[12px] text-[#595047]"
        >
          Ảnh chụp dọc đã được tự động xoay thẳng chiều hiển thị
        </p>
      )}
    </div>
  );
};
