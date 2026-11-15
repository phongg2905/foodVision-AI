"""Input validation, safe path containment, and dimension guard mixin for YOLODetector."""

from __future__ import annotations

from PIL import Image

from pathlib import Path

import numpy as np

from app.ai.image_processor import ProcessedImage, preprocess_uploaded_image
from app.core.errors import AppError, ErrorCode
from .config import DetectorConfig
from .exceptions import (
    DetectorConfigurationError,
    ImageDecodeError,
    ImagePathNotAllowedError,
    ImageTooLargeError,
    UnsupportedImageFormatError,
)


class _DetectorInputGuardMixin:
    """Mixin providing config validation, path confinement, and image decode checks."""

    _config: DetectorConfig

    @staticmethod
    def _validate_scalar_config(cfg: DetectorConfig) -> None:
        if not cfg.model_version or not cfg.model_version.strip():
            raise DetectorConfigurationError(
                "Chưa cấu hình phiên bản mô hình AI (ACTIVE_MODEL_VERSION).",
                details={"reason": "missing_model_version"},
            )
        if not (0.0 <= cfg.confidence_threshold <= 1.0):
            raise DetectorConfigurationError(
                "Ngưỡng confidence_threshold phải nằm trong đoạn [0.0, 1.0].",
                details={"confidence_threshold": cfg.confidence_threshold},
            )
        if not (0.0 <= cfg.review_threshold <= 1.0):
            raise DetectorConfigurationError(
                "Ngưỡng xác nhận HITL review_threshold phải nằm trong đoạn [0.0, 1.0].",
                details={"review_threshold": cfg.review_threshold},
            )
        if cfg.timeout_ms <= 0:
            raise DetectorConfigurationError(
                "Thời gian chờ suy luận timeout_ms phải lớn hơn 0.",
                details={"timeout_ms": cfg.timeout_ms},
            )
        if cfg.max_upload_bytes <= 0 or cfg.max_image_pixels <= 0:
            raise DetectorConfigurationError(
                "Giới hạn kích thước ảnh cấu hình phải lớn hơn 0.",
                details={
                    "max_upload_bytes": cfg.max_upload_bytes,
                    "max_image_pixels": cfg.max_image_pixels,
                },
            )
        if cfg.min_image_dimension < 1:
            raise DetectorConfigurationError(
                "Kích thước ảnh tối thiểu min_image_dimension phải >= 1.",
                details={"min_image_dimension": cfg.min_image_dimension},
            )
        if (
            cfg.max_image_dimension is not None
            and cfg.max_image_dimension < cfg.min_image_dimension
        ):
            raise DetectorConfigurationError(
                "max_image_dimension không được nhỏ hơn min_image_dimension.",
                details={
                    "min_image_dimension": cfg.min_image_dimension,
                    "max_image_dimension": cfg.max_image_dimension,
                },
            )
        if cfg.nms_iou_threshold is not None and not (
            0.0 < cfg.nms_iou_threshold <= 1.0
        ):
            raise DetectorConfigurationError(
                "Ngưỡng nms_iou_threshold phải nằm trong khoảng (0.0, 1.0].",
                details={"nms_iou_threshold": cfg.nms_iou_threshold},
            )

    # ==========================================================================
    # THUẬT TOÁN: Kiểm định nguồn ảnh an toàn, chống Path Traversal & Bomb ảnh
    # - Ý tưởng (`FR-03`, `NFR-06`, `NFR-14`, `ADR-010`):
    #   1. Với đường dẫn tệp: chuẩn hóa canonical path (`resolve`) và đối chiếu
    #      `Path.is_relative_to(allowed_dir)` để chặn tuyệt đối Path Traversal /
    #      symlink thoát ra ngoài thư mục được cấp phép; kiểm tra `st_size` trước
    #      khi đọc vào RAM.
    #   2. Với luồng `bytes`: xác thực dung lượng `<= max_upload_bytes`, chữ ký
    #      nhị phân magic bytes (JPEG/PNG/WebP), bắt riêng `DecompressionBombError`,
    #      xoay thẳng ảnh theo `EXIF Orientation`, xóa sạch `EXIF/GPS` trong RAM.
    #   3. Kiểm tra biên kích thước khung hình `(min_image_dimension, max_image_dimension,
    #      max_image_pixels)` trước khi đưa vào mô hình suy luận.
    # ==========================================================================
    def _validate_decoded_dimensions(self, width: int, height: int) -> None:
        if width < self._config.min_image_dimension or (
            height < self._config.min_image_dimension
        ):
            raise ImageDecodeError(
                "Kích thước ảnh quá nhỏ để nhận diện nguyên liệu.",
                details={
                    "reason": "image_dimensions_too_small",
                    "width": width,
                    "height": height,
                    "min_dimension": self._config.min_image_dimension,
                },
            )
        if self._config.max_image_dimension is not None and (
            width > self._config.max_image_dimension
            or height > self._config.max_image_dimension
        ):
            raise ImageDecodeError(
                "Chiều rộng hoặc chiều cao ảnh vượt quá giới hạn cấu hình.",
                details={
                    "reason": "image_dimensions_too_large",
                    "width": width,
                    "height": height,
                    "max_dimension": self._config.max_image_dimension,
                },
            )
        if (width * height) > self._config.max_image_pixels:
            raise ImageDecodeError(
                "Tổng số điểm ảnh vượt quá giới hạn an toàn.",
                details={
                    "reason": "image_pixels_exceed_limit",
                    "width": width,
                    "height": height,
                    "max_image_pixels": self._config.max_image_pixels,
                },
            )

    def _decode_and_validate_bytes(
        self, image_bytes: bytes | bytearray | memoryview
    ) -> ProcessedImage:
        if not isinstance(image_bytes, (bytes, bytearray, memoryview)):
            raise ImageDecodeError(
                "Dữ liệu đầu vào phải là luồng bytes ảnh hợp lệ.",
                details={"reason": "invalid_bytes_type"},
            )
        raw_bytes = bytes(image_bytes)
        if not raw_bytes:
            raise ImageDecodeError(
                "Tệp ảnh tải lên rỗng hoặc không đọc được.",
                details={"reason": "empty_image_bytes"},
            )
        if len(raw_bytes) > self._config.max_upload_bytes:
            raise ImageTooLargeError(
                "Dung lượng ảnh vượt quá giới hạn cho phép.",
                details={
                    "max_bytes": self._config.max_upload_bytes,
                    "actual_bytes": len(raw_bytes),
                },
            )

        try:
            processed = preprocess_uploaded_image(
                raw_bytes,
                max_upload_bytes=self._config.max_upload_bytes,
                max_image_pixels=self._config.max_image_pixels,
            )
        except Image.DecompressionBombError as exc:
            raise ImageDecodeError(
                "Ảnh vượt quá ngưỡng điểm ảnh an toàn (Decompression Bomb).",
                details={"reason": "decompression_bomb"},
            ) from exc
        except AppError as exc:
            if exc.status_code == 413:
                raise ImageTooLargeError(exc.message, details=exc.details) from exc
            if exc.status_code == 415:
                raise UnsupportedImageFormatError(
                    exc.message, details=exc.details
                ) from exc
            raise ImageDecodeError(exc.message, details=exc.details) from exc
        finally:
            del raw_bytes

        self._validate_decoded_dimensions(processed.width, processed.height)
        return processed

    # ==========================================================================
    # THUẬT TOÁN: Kiểm tra Đường dẫn Chống Path Traversal & Đọc Tệp Có Trần Dung lượng
    # - Từ chối chuỗi rỗng, byte NULL hoặc giao thức mạng (`://`); phân giải đường dẫn tuyệt đối
    #   và đối chiếu `is_relative_to` với danh sách trắng `allowed_image_dirs` trước khi đọc.
    # ==========================================================================
    def _read_allowed_path(self, image_path: str | Path) -> ProcessedImage:
        if not isinstance(image_path, (str, Path)):
            raise ImageDecodeError(
                "Đường dẫn ảnh không hợp lệ.",
                details={"reason": "invalid_path_type"},
            )
        raw_str = str(image_path).strip()
        if not raw_str or "\x00" in raw_str or "://" in raw_str:
            raise ImagePathNotAllowedError(
                "Đường dẫn tệp ảnh không hợp lệ hoặc không được phép.",
                details={"reason": "malformed_or_remote_path"},
            )
        if not self._config.allowed_image_dirs:
            raise ImagePathNotAllowedError(
                "Chưa cấu hình danh sách thư mục ảnh được phép (allowed_image_dirs).",
                details={"reason": "no_allowed_image_dirs_configured"},
            )

        resolved_path = Path(raw_str).expanduser().resolve(strict=False)
        if not any(
            resolved_path.is_relative_to(allowed_root)
            for allowed_root in self._config.allowed_image_dirs
        ):
            raise ImagePathNotAllowedError(
                "Đường dẫn ảnh nằm ngoài phạm vi thư mục được cấp phép.",
                details={"reason": "path_outside_allowed_directories"},
            )

        if not resolved_path.exists() or not resolved_path.is_file():
            raise ImageDecodeError(
                "Tệp ảnh không tồn tại hoặc không phải tệp hợp lệ.",
                details={"reason": "image_file_not_found"},
            )

        try:
            stat_size = resolved_path.stat().st_size
        except OSError as exc:
            raise ImageDecodeError(
                "Không thể truy cập thông tin tệp ảnh.",
                details={"reason": "image_stat_failed"},
            ) from exc

        if stat_size <= 0:
            raise ImageDecodeError(
                "Tệp ảnh rỗng (0 bytes).",
                details={"reason": "empty_image_file"},
            )
        if stat_size > self._config.max_upload_bytes:
            raise ImageTooLargeError(
                "Dung lượng tệp ảnh vượt quá giới hạn cho phép.",
                details={
                    "max_bytes": self._config.max_upload_bytes,
                    "actual_bytes": stat_size,
                },
            )

        raw_bytes = b""
        try:
            with resolved_path.open("rb") as handle:
                raw_bytes = handle.read(self._config.max_upload_bytes + 1)
            return self._decode_and_validate_bytes(raw_bytes)
        except AppError:
            raise
        except OSError as exc:
            raise ImageDecodeError(
                "Không thể đọc dữ liệu từ tệp ảnh.",
                details={"reason": "image_read_failed"},
            ) from exc
        finally:
            del raw_bytes

    def _validate_rgb_ndarray(self, rgb_image: np.ndarray) -> ProcessedImage:
        if not isinstance(rgb_image, np.ndarray):
            raise ImageDecodeError(
                "Mảng điểm ảnh đầu vào phải là numpy.ndarray.",
                details={"reason": "invalid_ndarray_type"},
            )
        if rgb_image.ndim != 3 or rgb_image.shape[2] != 3:
            raise ImageDecodeError(
                "Ảnh đầu vào phải là mảng RGB 3 kênh có kích thước (H, W, 3).",
                details={"reason": "invalid_rgb_shape", "shape": list(rgb_image.shape)},
            )
        height, width = int(rgb_image.shape[0]), int(rgb_image.shape[1])
        self._validate_decoded_dimensions(width, height)
        if not np.isfinite(rgb_image).all():
            raise ImageDecodeError(
                "Mảng điểm ảnh chứa giá trị NaN hoặc vô cực.",
                details={"reason": "non_finite_pixels"},
            )
        clean_rgb = (
            rgb_image
            if rgb_image.dtype == np.uint8
            else np.clip(rgb_image, 0, 255).astype(np.uint8)
        )
        return ProcessedImage(
            rgb_array=clean_rgb,
            width=width,
            height=height,
            mime_type="image/raw-rgb",
        )
