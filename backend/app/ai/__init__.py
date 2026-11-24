"""Perception layer: EXIF-safe image processor, YOLO detector, and CLIP fallback."""

from app.ai.clip_fallback import CLIPFallbackRanker, compute_cosine_similarity
from app.ai.image_processor import ProcessedImage, preprocess_uploaded_image
from app.ai.yolo_detector import (
    LabelMappingEntry,
    YOLODetector,
    aggregate_suggested_ingredients,
    compute_iou,
    needs_hitl_review,
)

__all__ = [
    "CLIPFallbackRanker",
    "LabelMappingEntry",
    "ProcessedImage",
    "YOLODetector",
    "aggregate_suggested_ingredients",
    "compute_cosine_similarity",
    "compute_iou",
    "needs_hitl_review",
    "preprocess_uploaded_image",
]

