"""Binary magic-byte validation, EXIF transpose, GPS stripping & ndarray normalization."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.errors import AppError, ErrorCode
from .types import ALLOWED_MIME_TYPES, ImageInput, ProcessedImage, _resolve_limits

# ==============================================================================
# THUẬT TOÁN: Kiểm tra chữ ký nhị phân (Magic-Bytes Signature Verification)
# - Ý tưởng: Không tin phần mở rộng tên tệp (`.jpg`) hoặc header `Content-Type` do
#   client gửi lên; đọc trực tiếp các byte đầu tiên của luồng dữ liệu nhị phân:
#   * JPEG: bắt đầu bằng `FF D8 FF`
#   * PNG : bắt đầu bằng `89 50 4E 47 0D 0A 1A 0A`
#   * WebP: bắt đầu bằng `RIFF` (byte 0..3) và `WEBP` (byte 8..11)
# - Đầu ra: Chuỗi MIME chuẩn nếu hợp lệ; ném `415 UNSUPPORTED_IMAGE_TYPE` nếu sai.
# - Độ phức tạp: O(1) — chỉ kiểm tra tối đa 12 byte đầu tiên.
# ==============================================================================
def detect_image_magic_mime(raw_bytes: bytes) -> str:
    """Verify binary magic bytes and return canonical MIME type."""
    if len(raw_bytes) >= 3 and raw_bytes[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if len(raw_bytes) >= 8 and raw_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if (
        len(raw_bytes) >= 12
        and raw_bytes[:4] == b"RIFF"
        and raw_bytes[8:12] == b"WEBP"
    ):
        return "image/webp"

    raise AppError(
        status_code=415,
        code=ErrorCode.UNSUPPORTED_IMAGE_TYPE,
        message="Định dạng ảnh không được hỗ trợ (chỉ chấp nhận JPEG, PNG, WebP).",
        details={"allowed_types": ALLOWED_MIME_TYPES},
    )


# ==============================================================================
# THUẬT TOÁN: Tiền xử lý ảnh an toàn quyền riêng tư (EXIF Transpose & Strip GPS)
# - Ý tưởng:
#   1. Kiểm tra trần dung lượng byte (`<= max_upload_bytes`) -> `413` nếu vượt ngưỡng.
#   2. Xác thực magic bytes -> `415` nếu định dạng ngoài JPEG/PNG/WebP.
#   3. Giải mã ảnh trong RAM với giới hạn tổng điểm ảnh chống Decompression Bomb.
#   4. Đọc thẻ `EXIF Orientation` bằng `ImageOps.exif_transpose` để xoay ma trận
#      điểm ảnh về đúng chiều thẳng đứng (upright) giúp tọa độ `bbox` chuẩn xác.
#   5. Chuyển sang không gian màu `RGB` thuần túy và trích xuất mảng `numpy` mới,
#      loại bỏ hoàn toàn mọi thẻ metadata `EXIF`, tọa độ `GPS` và thông tin thiết bị.
# - Bất biến an toàn: Giải phóng buffer tạm ngay trong khối `finally`.
# ==============================================================================
def preprocess_uploaded_image(
    raw_bytes: bytes,
    *,
    max_upload_bytes: int | None = None,
    max_image_pixels: int | None = None,
) -> ProcessedImage:
    """Validate, EXIF-orient, strip GPS metadata, and decode an image to RGB."""
    limit_bytes, limit_pixels = _resolve_limits(max_upload_bytes, max_image_pixels)

    if not raw_bytes:
        raise AppError(
            status_code=422,
            code=ErrorCode.INVALID_IMAGE,
            message="Tệp ảnh tải lên rỗng hoặc không đọc được.",
            details={"reason": "corrupted_or_unreadable_image"},
        )

    if len(raw_bytes) > limit_bytes:
        raise AppError(
            status_code=413,
            code=ErrorCode.IMAGE_TOO_LARGE,
            message="Dung lượng ảnh vượt quá giới hạn cho phép.",
            details={"max_bytes": limit_bytes},
        )

    mime_type = detect_image_magic_mime(raw_bytes)
    buffer = BytesIO(raw_bytes)
    upright_img: Image.Image | None = None
    rgb_img: Image.Image | None = None
    try:
        with Image.open(buffer) as img:
            width, height = img.size
            if width <= 0 or height <= 0 or (width * height) > limit_pixels:
                raise AppError(
                    status_code=422,
                    code=ErrorCode.INVALID_IMAGE,
                    message="Kích thước điểm ảnh không hợp lệ hoặc vượt giới hạn an toàn.",
                    details={"reason": "corrupted_or_unreadable_image"},
                )
            upright_img = ImageOps.exif_transpose(img)
            rgb_img = upright_img.convert("RGB")
            clean_array = np.ascontiguousarray(
                np.array(rgb_img, dtype=np.uint8, copy=True)
            )
            final_height, final_width = clean_array.shape[:2]
    except AppError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
        raise AppError(
            status_code=422,
            code=ErrorCode.INVALID_IMAGE,
            message="Dữ liệu ảnh bị hỏng hoặc không thể giải mã sang RGB.",
            details={"reason": "corrupted_or_unreadable_image"},
        ) from exc
    finally:
        if rgb_img is not None:
            rgb_img.close()
        if upright_img is not None:
            upright_img.close()
        buffer.close()

    return ProcessedImage(
        rgb_array=clean_array,
        width=final_width,
        height=final_height,
        mime_type=mime_type,
    )


# ==============================================================================
# THUẬT TOÁN: Chuẩn hóa Đa Định dạng Đầu vào sang Khung RGB Sạch (RGB Normalization)
# - Ý tưởng: Chấp nhận luồng byte thô, `ProcessedImage`, `PIL.Image` hoặc mảng `numpy`
#   (grayscale HxW, RGB HxWx3, RGBA HxWx4, kiểu `uint8` [0, 255] hoặc `float` [0, 1]),
#   kiểm tra tính hữu hạn và trần điểm ảnh, xoay EXIF nếu là `PIL.Image`, rồi sao chép
#   sang mảng liên tục `uint8` (H, W, 3) hoàn toàn không chứa metadata nhạy cảm.
# - Độ phức tạp: O(H * W) theo kích thước ảnh đầu vào.
# ==============================================================================
def normalize_image_input(
    image: ImageInput,
    *,
    max_upload_bytes: int | None = None,
    max_image_pixels: int | None = None,
) -> ProcessedImage:
    """Convert supported raw/decoded image inputs into a clean RGB `ProcessedImage`."""
    limit_bytes, limit_pixels = _resolve_limits(max_upload_bytes, max_image_pixels)

    if isinstance(image, (str, Path)):
        img_path = Path(image)
        if not img_path.is_file():
            raise AppError(
                status_code=422,
                code=ErrorCode.INVALID_IMAGE,
                message="Đường dẫn tệp ảnh đầu vào không tồn tại.",
                details={"reason": "missing_image_file"},
            )
        return preprocess_uploaded_image(
            img_path.read_bytes(),
            max_upload_bytes=limit_bytes,
            max_image_pixels=limit_pixels,
        )

    if isinstance(image, (bytes, bytearray, memoryview)):
        return preprocess_uploaded_image(
            bytes(image),
            max_upload_bytes=limit_bytes,
            max_image_pixels=limit_pixels,
        )

    if isinstance(image, ProcessedImage):
        return _normalize_ndarray(
            image.rgb_array,
            limit_pixels=limit_pixels,
            mime_type=image.mime_type or "image/raw-rgb",
        )

    if isinstance(image, Image.Image):
        width, height = image.size
        if width <= 0 or height <= 0 or (width * height) > limit_pixels:
            raise AppError(
                status_code=422,
                code=ErrorCode.INVALID_IMAGE,
                message="Kích thước điểm ảnh không hợp lệ hoặc vượt giới hạn an toàn.",
                details={"reason": "invalid_image_dimensions"},
            )
        upright_img: Image.Image | None = None
        rgb_img: Image.Image | None = None
        try:
            upright_img = ImageOps.exif_transpose(image)
            rgb_img = upright_img.convert("RGB")
            arr = np.ascontiguousarray(np.array(rgb_img, dtype=np.uint8, copy=True))
        except Exception as exc:
            raise AppError(
                status_code=422,
                code=ErrorCode.INVALID_IMAGE,
                message="Không thể chuyển đổi đối tượng ảnh sang RGB.",
                details={"reason": "corrupted_or_unreadable_image"},
            ) from exc
        finally:
            if rgb_img is not None:
                rgb_img.close()
            if upright_img is not None and upright_img is not image:
                upright_img.close()
        return ProcessedImage(
            rgb_array=arr,
            width=int(arr.shape[1]),
            height=int(arr.shape[0]),
            mime_type="image/raw-rgb",
        )

    if isinstance(image, np.ndarray):
        return _normalize_ndarray(
            image, limit_pixels=limit_pixels, mime_type="image/raw-rgb"
        )

    raise AppError(
        status_code=422,
        code=ErrorCode.INVALID_IMAGE,
        message="Kiểu dữ liệu ảnh đầu vào không được hỗ trợ.",
        details={"reason": "unsupported_image_container"},
    )


# ==============================================================================
# THUẬT TOÁN: Chuẩn hóa Tensor Điểm ảnh Đa Kênh về Mảng RGB uint8 Liên tục
# - Kiểm tra chiều không gian 2D (grayscale) hoặc 3D (1/3/4 kênh), khử giá trị NaN/Inf.
# - Chuyển đổi dải số thực `[0.0, 1.0]` hoặc `[0.0, 255.0]` sang `uint8` có làm tròn,
#   loại bỏ kênh Alpha nếu là RGBA và ép bộ nhớ liên tục (`np.ascontiguousarray`).
# - Độ phức tạp: O(W * H * C) theo kích thước khung ảnh đầu vào.
# ==============================================================================
def _normalize_ndarray(
    array: np.ndarray,
    *,
    limit_pixels: int,
    mime_type: str,
) -> ProcessedImage:
    """Validate and convert a NumPy image array to contiguous `uint8` `(H, W, 3)` RGB."""
    if array.ndim == 2:
        working = np.stack([array, array, array], axis=-1)
    elif array.ndim == 3 and array.shape[2] == 4:
        working = array[:, :, :3]
    elif array.ndim == 3 and array.shape[2] == 3:
        working = array
    else:
        raise AppError(
            status_code=422,
            code=ErrorCode.INVALID_IMAGE,
            message="Mảng điểm ảnh phải có kích thước (H, W), (H, W, 3) hoặc (H, W, 4).",
            details={"reason": "invalid_array_shape"},
        )

    height, width = int(working.shape[0]), int(working.shape[1])
    if height <= 0 or width <= 0 or (height * width) > limit_pixels:
        raise AppError(
            status_code=422,
            code=ErrorCode.INVALID_IMAGE,
            message="Kích thước vùng ảnh rỗng hoặc vượt giới hạn điểm ảnh an toàn.",
            details={"reason": "invalid_image_dimensions"},
        )

    if working.dtype == np.bool_ or not np.issubdtype(working.dtype, np.number):
        raise AppError(
            status_code=422,
            code=ErrorCode.INVALID_IMAGE,
            message="Kiểu phần tử mảng ảnh không hợp lệ.",
            details={"reason": "invalid_array_dtype"},
        )

    if np.issubdtype(working.dtype, np.floating):
        if not np.all(np.isfinite(working)):
            raise AppError(
                status_code=422,
                code=ErrorCode.INVALID_IMAGE,
                message="Mảng ảnh chứa giá trị NaN hoặc vô cực.",
                details={"reason": "non_finite_pixels"},
            )
        min_v, max_v = float(np.min(working)), float(np.max(working))
        if min_v < 0.0 or max_v > 255.0:
            raise AppError(
                status_code=422,
                code=ErrorCode.INVALID_IMAGE,
                message="Giá trị điểm ảnh thực nằm ngoài miền hợp lệ [0, 255].",
                details={"reason": "pixel_range_out_of_bounds"},
            )
        scaled = working * 255.0 if max_v <= 1.0 else working
        clean = np.ascontiguousarray(np.rint(scaled).clip(0, 255).astype(np.uint8))
    elif working.dtype == np.uint8:
        clean = np.ascontiguousarray(working.copy())
    else:
        min_v, max_v = int(np.min(working)), int(np.max(working))
        if min_v < 0 or max_v > 255:
            raise AppError(
                status_code=422,
                code=ErrorCode.INVALID_IMAGE,
                message="Giá trị điểm ảnh nguyên nằm ngoài miền [0, 255].",
                details={"reason": "pixel_range_out_of_bounds"},
            )
        clean = np.ascontiguousarray(working.astype(np.uint8, copy=True))

    return ProcessedImage(
        rgb_array=clean,
        width=width,
        height=height,
        mime_type=mime_type,
    )
