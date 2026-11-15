"""Normalized bounding-box validation, padded ROI cropping, and encoder resizing."""

from __future__ import annotations

from collections.abc import Mapping

import math
from typing import Any

import numpy as np
from PIL import Image

from app.core.errors import AppError, ErrorCode
from app.schemas.ai import BBox
from .decoder import normalize_image_input
from .types import BBoxInput, CroppedRegion, ImageInput

# ==============================================================================
# THUẬT TOÁN: Kiểm định Hộp giới hạn Chuẩn hóa & Cắt Vùng Ảnh (Normalized BBox Crop)
# - Cơ sở hình học:
#   * BBox chuẩn hóa hợp lệ khi và chỉ khi 4 tọa độ hữu hạn thỏa mãn:
#         0.0 <= x1 < x2 <= 1.0   và   0.0 <= y1 < y2 <= 1.0
#   * Mở rộng biên ngữ cảnh tùy chọn `padding_ratio >= 0`:
#         x1' = max(0, x1 - p * (x2 - x1)),  x2' = min(1, x2 + p * (x2 - x1))
#   * Quy đổi sang chỉ số pixel nguyên trên ảnh đã xoay EXIF `(W, H)`:
#         px1 = floor(x1' * W), py1 = floor(y1' * H), px2 = ceil(x2' * W), py2 = ceil(y2' * H)
# - Bất biến an toàn: Luôn tạo bản sao độc lập (`.copy()`) của vùng cắt để giải phóng
#   khung ảnh lớn khỏi bộ nhớ và không bao giờ ném lỗi cắt mảng khi `bbox` sai.
# ==============================================================================
def parse_valid_bbox(bbox: Any) -> BBox | None:
    """Validate and convert a normalized `[0, 1]` bounding box, or return `None`."""
    if bbox is None:
        return None
    if isinstance(bbox, BBox):
        coords: tuple[Any, Any, Any, Any] = (bbox.x1, bbox.y1, bbox.x2, bbox.y2)
    elif isinstance(bbox, Mapping):
        if not all(k in bbox for k in ("x1", "y1", "x2", "y2")):
            return None
        coords = (bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"])
    elif isinstance(bbox, (tuple, list)) and len(bbox) == 4:
        coords = (bbox[0], bbox[1], bbox[2], bbox[3])
    elif all(hasattr(bbox, attr) for attr in ("x1", "y1", "x2", "y2")):
        coords = (bbox.x1, bbox.y1, bbox.x2, bbox.y2)
    else:
        return None

    parsed: list[float] = []
    for raw in coords:
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            return None
        val = float(raw)
        if not math.isfinite(val) or val < 0.0 or val > 1.0:
            return None
        parsed.append(val)

    x1, y1, x2, y2 = parsed
    if x1 >= x2 or y1 >= y2:
        return None
    return BBox(x1=x1, y1=y1, x2=x2, y2=y2)


def is_valid_bbox(bbox: Any) -> bool:
    """Return True if `bbox` represents a valid normalized `[0, 1]` rectangle."""
    return parse_valid_bbox(bbox) is not None


# ==============================================================================
# THUẬT TOÁN: Mở rộng Biên Tỷ lệ và Cắt Vùng Ảnh Quan tâm (Padded ROI BBox Cropping)
# - Bước 1: Chuẩn hóa ảnh gốc về mảng RGB sạch và kiểm tra tính hợp lệ của `bbox` trong `[0, 1]`.
# - Bước 2: Mở rộng hộp giới hạn theo `padding_ratio` đối xứng quanh tâm, kẹp biên an toàn
#           vào khung ảnh thực `[0..W, 0..H]` và bảo đảm cạnh tối thiểu `min_side_pixels`.
# - Bước 3: Sao chép mảng con vùng ROI độc lập bộ nhớ để đưa vào bộ mã hóa đa phương thức CLIP/VLM.
# - Độ phức tạp: O(W_crop * H_crop) theo diện tích vùng cắt.
# ==============================================================================
def crop_region_from_bbox(
    image: ImageInput,
    bbox: BBoxInput | None = None,
    *,
    padding_ratio: float = 0.0,
    min_side_pixels: int = 1,
    strict_bbox: bool = False,
    max_upload_bytes: int | None = None,
    max_image_pixels: int | None = None,
) -> CroppedRegion:
    """Preprocess `image` and crop the target region when `bbox` is valid."""
    processed = normalize_image_input(
        image,
        max_upload_bytes=max_upload_bytes,
        max_image_pixels=max_image_pixels,
    )

    if bbox is None:
        return CroppedRegion(
            rgb_array=processed.rgb_array,
            width=processed.width,
            height=processed.height,
            was_cropped=False,
            bbox_valid=None,
        )

    valid_box = parse_valid_bbox(bbox)
    if valid_box is None or not math.isfinite(padding_ratio) or padding_ratio < 0.0:
        if strict_bbox:
            raise AppError(
                status_code=422,
                code=ErrorCode.VALIDATION_ERROR,
                message="Tọa độ hộp giới hạn (bbox) hoặc hệ số đệm không hợp lệ.",
                details={"field": "bbox", "reason": "invalid_bbox"},
            )
        return CroppedRegion(
            rgb_array=processed.rgb_array,
            width=processed.width,
            height=processed.height,
            was_cropped=False,
            bbox_valid=False,
        )

    pad_w = (valid_box.x2 - valid_box.x1) * padding_ratio
    pad_h = (valid_box.y2 - valid_box.y1) * padding_ratio
    nx1 = max(0.0, valid_box.x1 - pad_w)
    ny1 = max(0.0, valid_box.y1 - pad_h)
    nx2 = min(1.0, valid_box.x2 + pad_w)
    ny2 = min(1.0, valid_box.y2 + pad_h)

    px1 = max(0, min(processed.width - 1, math.floor(nx1 * processed.width)))
    py1 = max(0, min(processed.height - 1, math.floor(ny1 * processed.height)))
    px2 = max(px1 + 1, min(processed.width, math.ceil(nx2 * processed.width)))
    py2 = max(py1 + 1, min(processed.height, math.ceil(ny2 * processed.height)))

    required_side = max(1, int(min_side_pixels))
    if (px2 - px1) < required_side or (py2 - py1) < required_side:
        if strict_bbox:
            raise AppError(
                status_code=422,
                code=ErrorCode.VALIDATION_ERROR,
                message="Vùng ảnh sau khi cắt nhỏ hơn kích thước tối thiểu cho phép.",
                details={"field": "bbox", "reason": "degenerate_crop_region"},
            )
        return CroppedRegion(
            rgb_array=processed.rgb_array,
            width=processed.width,
            height=processed.height,
            was_cropped=False,
            bbox_valid=False,
        )

    cropped_arr = np.ascontiguousarray(processed.rgb_array[py1:py2, px1:px2].copy())
    return CroppedRegion(
        rgb_array=cropped_arr,
        width=int(cropped_arr.shape[1]),
        height=int(cropped_arr.shape[0]),
        was_cropped=True,
        bbox_valid=True,
        pixel_box=(px1, py1, px2, py2),
        normalized_bbox=valid_box,
    )


# ==============================================================================
# THUẬT TOÁN: Nội suy Song khối Chuẩn kích thước Đầu vào Bộ mã hóa (Bicubic Resize)
# - Chuẩn hóa mảng ảnh đầu vào và nội suy Bicubic về kích thước vuông `(target_size, target_size)`
#   tương thích với kiến trúc Vision Transformer của CLIP.
# ==============================================================================
def resize_rgb_for_encoder(
    rgb_array: np.ndarray,
    target_size: tuple[int, int] | None = None,
) -> np.ndarray:
    """Resize a clean RGB array for vision encoders without attaching EXIF metadata."""
    processed = normalize_image_input(rgb_array)
    if target_size is None:
        return processed.rgb_array

    target_w, target_h = int(target_size[0]), int(target_size[1])
    if target_w <= 0 or target_h <= 0:
        raise ValueError("target_size dimensions must be positive integers")

    src_img = Image.fromarray(processed.rgb_array, mode="RGB")
    resized_img: Image.Image | None = None
    try:
        resized_img = src_img.resize((target_w, target_h), Image.Resampling.BICUBIC)
        return np.ascontiguousarray(np.array(resized_img, dtype=np.uint8, copy=True))
    finally:
        if resized_img is not None:
            resized_img.close()
        src_img.close()
