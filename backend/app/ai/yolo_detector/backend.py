"""Ultralytics YOLO runtime inference adapter and PyTorch checkpoint runner."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from contextlib import nullcontext
import logging
from pathlib import Path
import pickle
import threading
from typing import Any

import numpy as np
from PIL import Image

from .exceptions import DetectorConfigurationError, ModelWeightsNotFoundError
from .models import RawBoxPrediction

logger = logging.getLogger(__name__)


class _PyTorchCheckpointAdapter:
    """Adapter executing FoodVision v1 PyTorch `.pt` checkpoints (`foodvision-yolo-v1`)."""

    def __init__(self, checkpoint: dict[str, Any]) -> None:
        import torch
        import torch.nn as nn

        nc = int(checkpoint.get("nc", 20))
        self.backbone = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(16),
            nn.SiLU(),
            nn.Conv2d(16, 32, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.SiLU(),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.SiLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.class_head = nn.Linear(64, nc)
        self.box_head = nn.Linear(64, 4)

        state_dict = checkpoint.get("state_dict")
        if not isinstance(state_dict, dict):
            raise ValueError("Missing state_dict in checkpoint")

        module = nn.Module()
        module.backbone = self.backbone
        module.class_head = self.class_head
        module.box_head = self.box_head
        module.load_state_dict(state_dict)
        module.eval()
        self._module = module
        self._torch = torch

    # THUẬT TOÁN: Suy luận tiến trên checkpoint PyTorch 20 lớp và quy đổi [cx, cy, w, h] sang [x1, y1, x2, y2]
    def predict(
        self,
        rgb_image: np.ndarray,
        *,
        conf: float,
    ) -> list[RawBoxPrediction]:
        torch = self._torch
        with Image.fromarray(rgb_image) as pil_img:
            resized = pil_img.resize((64, 64))
            chw = np.ascontiguousarray(
                np.transpose(np.asarray(resized, dtype=np.float32) * (1.0 / 255.0), (2, 0, 1))
            )
            tensor = torch.from_numpy(chw).unsqueeze(0)

        with torch.inference_mode():
            feat = self._module.backbone(tensor).flatten(1)
            logits = self._module.class_head(feat)
            probs = torch.softmax(logits, dim=-1)[0]
            box_xywh = torch.sigmoid(self._module.box_head(feat))[0].tolist()

        top_prob, top_cls = torch.max(probs, dim=0)
        score = float(top_prob.item())
        cls_id = int(top_cls.item())
        if score < conf:
            return []

        cx, cy, bw, bh = [float(v) for v in box_xywh]
        bw = max(0.10, min(0.80, bw))
        bh = max(0.10, min(0.80, bh))
        x1 = max(0.0, min(0.95, cx - bw / 2.0))
        y1 = max(0.0, min(0.95, cy - bh / 2.0))
        x2 = max(x1 + 0.05, min(1.0, cx + bw / 2.0))
        y2 = max(y1 + 0.05, min(1.0, cy + bh / 2.0))
        return [
            RawBoxPrediction(
                class_id=cls_id,
                confidence=score,
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                normalized=True,
            )
        ]


class UltralyticsYOLOBackend:
    """Lazy-loading YOLO inference adapter supporting Ultralytics and PyTorch `.pt` weights."""

    def __init__(self, artifact_path: Path | None) -> None:
        self._artifact_path = artifact_path
        self._model: Any = None
        self._torch: Any = None
        self._pt_adapter: _PyTorchCheckpointAdapter | None = None
        self._load_lock = threading.Lock()
        self._predict_lock = threading.Lock()

    @property
    def is_loaded(self) -> bool:
        return self._model is not None or self._pt_adapter is not None

    # ==========================================================================
    # THUẬT TOÁN: Nạp Trễ Trọng số YOLO An toàn Đa luồng (Double-Checked Locking)
    # - Dùng khóa `_load_lock` kiểm tra kép tránh nạp trùng model khi có nhiều request đồng thời,
    #   xác minh tệp trọng số tồn tại và khác rỗng trước khi nạp bằng Ultralytics hoặc PyTorch.
    # ==========================================================================
    def load(self) -> None:
        """Lazily verify local weights and initialize YOLO or PyTorch checkpoint."""
        if self.is_loaded:
            return
        with self._load_lock:
            if self.is_loaded:
                return
            if self._artifact_path is None or not str(self._artifact_path).strip():
                raise ModelWeightsNotFoundError(
                    "Chưa cấu hình đường dẫn tệp trọng số mô hình YOLO (MODEL_ARTIFACT_PATH).",
                    details={"reason": "missing_model_path"},
                )
            if not self._artifact_path.exists() or not self._artifact_path.is_file():
                raise ModelWeightsNotFoundError(
                    "Không tìm thấy tệp trọng số mô hình nhận diện AI. Vui lòng kiểm tra cấu hình hoặc nhập nguyên liệu thủ công.",
                    details={
                        "reason": "missing_model_weights",
                        "artifact_path": str(self._artifact_path),
                    },
                )
            file_size = self._artifact_path.stat().st_size
            if file_size <= 0:
                raise ModelWeightsNotFoundError(
                    "Tệp trọng số mô hình YOLO rỗng (0 bytes).",
                    details={
                        "reason": "empty_model_weights",
                        "artifact_path": str(self._artifact_path),
                    },
                )

            if file_size < 1_000_000:
                try:
                    import torch

                    raw_ckpt = torch.load(
                        str(self._artifact_path),
                        map_location="cpu",
                        weights_only=False,
                    )
                    if (
                        isinstance(raw_ckpt, dict)
                        and raw_ckpt.get("format_version") == "foodvision-yolo-v1"
                    ):
                        self._pt_adapter = _PyTorchCheckpointAdapter(raw_ckpt)
                        return
                except (
                    ImportError,
                    RuntimeError,
                    OSError,
                    pickle.UnpicklingError,
                    KeyError,
                    TypeError,
                    ValueError,
                ) as probe_err:
                    logger.debug(
                        "Checkpoint is not foodvision-yolo-v1 dict format (%s); falling back to Ultralytics loader.",
                        type(probe_err).__name__,
                    )

            try:
                import torch
                from ultralytics import YOLO
            except ImportError as exc:
                raise DetectorConfigurationError(
                    "Không thể nạp tệp trọng số mô hình nhận diện AI (thiếu ultralytics hoặc định dạng .pt không hợp lệ).",
                    details={"reason": "ultralytics_not_installed"},
                ) from exc

            try:
                self._model = YOLO(str(self._artifact_path))
                self._torch = torch
            except Exception as exc:
                raise DetectorConfigurationError(
                    "Không thể khởi tạo mô hình nhận diện AI từ tệp trọng số đã cấu hình.",
                    details={
                        "reason": "model_load_failed",
                        "artifact_path": str(self._artifact_path),
                    },
                ) from exc

    # ==========================================================================
    # THUẬT TOÁN: Suy luận Tiến YOLO & Trích xuất Hộp Chuẩn hóa `[0, 1]`
    # - Chạy forward pass dưới khóa `_predict_lock`, đọc tensor `boxes.cls`, `boxes.conf`
    #   và tọa độ chuẩn hóa `xyxyn` sang danh sách `RawBoxPrediction`.
    # ==========================================================================
    def predict_raw(
        self,
        rgb_image: np.ndarray,
        *,
        confidence_threshold: float,
    ) -> list[RawBoxPrediction]:
        """Execute forward pass and return raw normalized predictions."""
        self.load()
        with self._predict_lock:
            if self._pt_adapter is not None:
                return self._pt_adapter.predict(
                    rgb_image, conf=confidence_threshold
                )
            # Ultralytics interprets NumPy ndarrays as OpenCV BGR; convert RGB -> BGR.
            bgr_image = (
                np.ascontiguousarray(rgb_image[:, :, ::-1])
                if rgb_image.ndim == 3 and rgb_image.shape[2] == 3
                else rgb_image
            )
            inference_ctx = (
                self._torch.inference_mode()
                if self._torch is not None
                else nullcontext()
            )
            with inference_ctx:
                results = self._model.predict(
                    source=bgr_image,
                    conf=confidence_threshold,
                    verbose=False,
                )

        if not results or results[0].boxes is None:
            return []

        boxes = results[0].boxes
        if len(boxes) == 0:
            return []

        cls_list = boxes.cls.detach().cpu().to(dtype=int).tolist()
        conf_list = boxes.conf.detach().cpu().tolist()
        xyxyn_list = boxes.xyxyn.detach().cpu().tolist()
        return [
            RawBoxPrediction(
                class_id=int(cls_id),
                confidence=float(raw_conf),
                x1=float(coords[0]),
                y1=float(coords[1]),
                x2=float(coords[2]),
                y2=float(coords[3]),
                normalized=True,
            )
            for cls_id, raw_conf, coords in zip(cls_list, conf_list, xyxyn_list, strict=True)
        ]


class _CallableBackendAdapter:
    """Internal adapter allowing plain callables `(rgb_image, conf) -> boxes` in tests."""

    def __init__(
        self, fn: Callable[[np.ndarray, float], Sequence[RawBoxPrediction]]
    ) -> None:
        self._fn = fn

    def load(self) -> None:
        return None

    def predict_raw(
        self,
        rgb_image: np.ndarray,
        *,
        confidence_threshold: float,
    ) -> Sequence[RawBoxPrediction]:
        return self._fn(rgb_image, confidence_threshold)
