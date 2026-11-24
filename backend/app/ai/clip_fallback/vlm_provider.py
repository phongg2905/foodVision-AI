"""OpenAI-compatible VLM transport provider and KB resolution helper."""

from __future__ import annotations

import re
from collections.abc import Mapping
from .candidates import _env_float
from app.core.config import get_settings
import math
import os

import base64
from collections.abc import Sequence
from io import BytesIO
import json
from typing import Any
from uuid import UUID

import numpy as np
from PIL import Image

from .models import (
    FallbackConfig,
    FallbackModelError,
    InitialYOLOPrediction,
    KBCandidateIngredient,
    ProviderAssessment,
    RankedCandidate,
    ScoreMetricType,
    _coerce_uuid,
)

# ==============================================================================
# THUẬT TOÁN: Chấm điểm Ứng viên Đóng bằng VLM (Closed-Set VLM Candidate Scoring)
# - Ý tưởng: Gửi ảnh vùng cắt (PNG base64 trong RAM) cùng danh sách đóng các mã
#   `ingredient_id` hợp lệ từ Knowledge Base tới VLM qua transport được tiêm (DI)
#   hoặc HTTP; chỉ giữ các `ingredient_id` thuộc tập KB đầu vào, loại bỏ hoàn toàn
#   nhãn tự sinh ngoài danh mục để bảo toàn bất biến không tự thêm nhãn mới.
# ==============================================================================
class OpenAICompatibleVLMProvider:
    """Swappable Vision-Language Model provider supporting HTTP or injected DI transport."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        model_name: str | None = None,
        api_key: str | None = None,
        timeout_sec: float | None = None,
        transport: Callable[[dict[str, Any]], Mapping[str, Any]] | None = None,
    ) -> None:
        self._base_url = (base_url or os.getenv("VLM_API_BASE_URL") or "").strip().rstrip("/")
        self._model_name = (model_name or os.getenv("VLM_MODEL_NAME") or "").strip()
        self._api_key = (
            api_key or os.getenv("VLM_API_KEY") or os.getenv("OLLAMA_API_KEY") or ""
        ).strip() or None
        env_timeout = _env_float("VLM_TIMEOUT_SEC")
        self._timeout_sec = (
            float(timeout_sec)
            if timeout_sec is not None
            else (
                env_timeout
                if env_timeout is not None
                else float(get_settings().inference_timeout_ms) / 1000.0
            )
        )
        self._transport = transport

    @property
    def model_source(self) -> str:
        return f"vlm:{self._model_name}" if self._model_name else "vlm:unconfigured"

    def assess_candidates(
        self,
        rgb_image: np.ndarray,
        candidates: Sequence[KBCandidateIngredient],
    ) -> ProviderAssessment:
        if not self._model_name:
            raise FallbackModelError("VLM model_name is not configured")
        if self._transport is None and not self._base_url:
            raise FallbackModelError("VLM base_url or DI transport is required")

        allowed_ids = {cand.ingredient_id for cand in candidates}
        kb_catalog_payload = [
            {
                "ingredient_id": str(c.ingredient_id),
                "slug": c.slug,
                "name_vi": c.name_vi,
                "aliases": list(c.aliases),
            }
            for c in candidates
        ]
        image_b64, image_mime = _encode_rgb_for_vlm(rgb_image)
        request_body: dict[str, Any] = {
            "model": self._model_name,
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a kitchen food ingredient identifier. Return strict JSON with keys: "
                        "is_non_food (bool: true ONLY if zero food ingredients exist anywhere in the image; "
                        "false whenever any food ingredient is visible, even with knives or cutting boards), "
                        "is_out_of_distribution (bool: true ONLY if food is present but matches none of the catalog), "
                        "candidates (list of {ingredient_id, score} restricted strictly to matching catalog IDs "
                        "visible in the image, with score in [0.5, 0.99] reflecting visual match strength)."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": json.dumps({"catalog": kb_catalog_payload}, ensure_ascii=False)},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{image_mime};base64,{image_b64}"},
                        },
                    ],
                },
            ],
        }
        if "gemini" in self._model_name.lower() and "lite" not in self._model_name.lower():
            request_body["reasoning_effort"] = "low"

        try:
            raw_resp = (
                self._transport(request_body)
                if self._transport is not None
                else self._post_http(request_body)
            )
            parsed = _extract_vlm_json(raw_resp)
            scores_by_id: dict[UUID, float] = {}
            for entry in parsed.get("candidates") or []:
                if not isinstance(entry, Mapping):
                    continue
                cand_id = _coerce_uuid(entry.get("ingredient_id"))
                raw_score = entry.get("score")
                if cand_id in allowed_ids and isinstance(raw_score, (int, float)):
                    val = float(raw_score)
                    if math.isfinite(val):
                        scores_by_id[cand_id] = max(-1.0, min(1.0, val))

            has_strong_food = any(v >= 0.5 for v in scores_by_id.values())
            return ProviderAssessment(
                scores_by_id=scores_by_id,
                model_source=self.model_source,
                score_type=ScoreMetricType.PROVIDER_RELEVANCE,
                is_non_food=bool(parsed.get("is_non_food", False)) and not has_strong_food,
                is_out_of_distribution=bool(parsed.get("is_out_of_distribution", False)) and not has_strong_food,
            )
        except FallbackModelError:
            raise
        except Exception as exc:
            raise FallbackModelError("VLM candidate assessment failed") from exc

    def _post_http(self, request_body: dict[str, Any]) -> Mapping[str, Any]:
        import httpx

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        with httpx.Client(timeout=self._timeout_sec) as client:
            resp = client.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=request_body,
            )
            if resp.status_code == 400 and (
                "response_format" in request_body or "reasoning_effort" in request_body
            ):
                fallback_body = {
                    k: v
                    for k, v in request_body.items()
                    if k not in {"response_format", "reasoning_effort"}
                }
                resp = client.post(
                    f"{self._base_url}/chat/completions",
                    headers=headers,
                    json=fallback_body,
                )
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, Mapping):
                raise FallbackModelError("Unexpected VLM JSON envelope")
            return data


def _encode_rgb_for_vlm(rgb_image: np.ndarray, max_side: int = 448) -> tuple[str, str]:
    buf = BytesIO()
    pil_img = Image.fromarray(rgb_image)
    try:
        w, h = pil_img.size
        if max(w, h) > max_side:
            pil_img.thumbnail((max_side, max_side), Image.Resampling.BILINEAR)
        pil_img.save(buf, format="JPEG", quality=85)
        return base64.b64encode(buf.getvalue()).decode("ascii"), "image/jpeg"
    finally:
        pil_img.close()
        buf.close()


_THINK_TAG_RE = re.compile(r"<think>.*?</think>", flags=re.DOTALL | re.IGNORECASE)
_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", flags=re.IGNORECASE)


def _extract_vlm_json(raw_resp: Mapping[str, Any]) -> Mapping[str, Any]:
    if "candidates" in raw_resp or "is_non_food" in raw_resp:
        return raw_resp
    choices = raw_resp.get("choices")
    if isinstance(choices, Sequence) and choices:
        msg = choices[0].get("message", {}) if isinstance(choices[0], Mapping) else {}
        content = msg.get("content", "") if isinstance(msg, Mapping) else ""
        if isinstance(content, str) and content.strip():
            cleaned = _THINK_TAG_RE.sub("", content).strip()
            cleaned = _CODE_FENCE_RE.sub("", cleaned).strip()
            if not cleaned.startswith("{"):
                start = cleaned.find("{")
                end = cleaned.rfind("}")
                if start != -1 and end != -1 and end > start:
                    cleaned = cleaned[start : end + 1]
            loaded = json.loads(cleaned)
            if isinstance(loaded, Mapping):
                return loaded
    raise FallbackModelError("Unable to parse structured VLM JSON output")


# ==============================================================================
# THUẬT TOÁN: Đối chiếu Nhãn YOLO với Danh mục Cơ sở Tri thức Đang Hoạt động
# - Ánh xạ dự đoán YOLO sang bản ghi KB theo thứ tự ưu tiên: khớp `ingredient_id` trực tiếp ->
#   khớp tên chuẩn hóa `slug` / `name_vi` / `aliases`; phát hiện nhãn chưa phân giải để kích hoạt CLIP.
# ==============================================================================
def _resolve_yolo_with_kb(
    yolo_input: Any,
    yolo_pred: InitialYOLOPrediction,
    kb_candidates: Sequence[KBCandidateIngredient],
) -> InitialYOLOPrediction:
    """Resolve plain-text YOLO class names against active KB candidates when unambiguous."""
    if not kb_candidates:
        return yolo_pred

    kb_by_id = {c.ingredient_id: c for c in kb_candidates}
    if yolo_pred.ingredient_id is not None:
        if yolo_pred.ingredient_id not in kb_by_id:
            return InitialYOLOPrediction(
                class_index=yolo_pred.class_index,
                class_name=yolo_pred.class_name,
                ingredient_id=yolo_pred.ingredient_id,
                ingredient_name=yolo_pred.ingredient_name,
                confidence=yolo_pred.confidence,
                bbox=yolo_pred.bbox,
                needs_confirmation=yolo_pred.needs_confirmation,
                is_unresolved=True,
            )
        return yolo_pred

    explicit_null_id = (
        (isinstance(yolo_input, Mapping) and "ingredient_id" in yolo_input and yolo_input["ingredient_id"] is None)
        or (
            yolo_input is not None
            and not isinstance(yolo_input, (str, Mapping, InitialYOLOPrediction))
            and hasattr(yolo_input, "ingredient_id")
            and getattr(yolo_input, "ingredient_id") is None
        )
    )
    if explicit_null_id or yolo_pred.display_label is None:
        return yolo_pred

    needle = yolo_pred.display_label.strip().casefold()
    matches = [
        c
        for c in kb_candidates
        if needle
        in {
            c.slug.strip().casefold(),
            c.name_vi.strip().casefold(),
            *(a.strip().casefold() for a in c.aliases if a.strip()),
        }
    ]
    if len(matches) == 1:
        matched = matches[0]
        return InitialYOLOPrediction(
            class_index=yolo_pred.class_index,
            class_name=yolo_pred.class_name or matched.slug,
            ingredient_id=matched.ingredient_id,
            ingredient_name=matched.name_vi,
            confidence=yolo_pred.confidence,
            bbox=yolo_pred.bbox,
            needs_confirmation=yolo_pred.needs_confirmation,
            is_unresolved=yolo_pred.is_unresolved,
        )
    return yolo_pred
