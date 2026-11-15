"""Canonical food class mapping normalization and JSON loader."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
from pathlib import Path
from typing import Any
from uuid import UUID

from .exceptions import DetectorConfigurationError, InvalidClassMappingError
from .models import ClassMappingInput, LabelMappingEntry

# ==============================================================================
# THUẬT TOÁN: Chuẩn hóa và kiểm định ánh xạ nhãn thực phẩm (Strict Food Class Mapping)
# - Ý tưởng (`ADR-006`, `BR-04`, `BR-12`):
#   * Không bao giờ mặc định các lớp COCO/YOLO gốc là nguyên liệu thực phẩm.
#   * Mọi `class_id` phải là số nguyên không âm, ánh xạ tới nhãn thực phẩm không rỗng.
#   * Khi `strict=True`, từ chối ngay ánh xạ trỏ tới `pantry` hoặc nguyên liệu `inactive`
#     bằng mã lỗi `400 INVALID_LABEL_MAPPING`.
# - Độ phức tạp: O(C) với C là số lớp được cấu hình.
# ==============================================================================
def _parse_int_class_id(raw_key: Any) -> int:
    if isinstance(raw_key, bool):
        raise InvalidClassMappingError(
            "Chỉ số class_id trong bảng ánh xạ nhãn không hợp lệ.",
            details={"class_id": raw_key, "reason": "boolean_not_allowed"},
        )
    try:
        cls_id = int(raw_key)
    except (TypeError, ValueError) as exc:
        raise InvalidClassMappingError(
            "Chỉ số class_id trong bảng ánh xạ nhãn phải là số nguyên không âm.",
            details={"class_id": str(raw_key)},
        ) from exc
    if cls_id < 0:
        raise InvalidClassMappingError(
            "Chỉ số class_id trong bảng ánh xạ nhãn không được âm.",
            details={"class_id": cls_id},
        )
    return cls_id


def _coerce_mapping_entry(
    cls_id: int,
    raw_val: LabelMappingEntry | str | Mapping[str, Any],
) -> LabelMappingEntry:
    if isinstance(raw_val, LabelMappingEntry):
        if raw_val.class_index != cls_id:
            raise InvalidClassMappingError(
                "Khóa class_id không khớp với trường class_index của LabelMappingEntry.",
                details={"key_class_id": cls_id, "entry_class_index": raw_val.class_index},
            )
        return raw_val

    if isinstance(raw_val, str):
        label = raw_val.strip()
        return LabelMappingEntry(class_index=cls_id, class_name=label)

    if isinstance(raw_val, Mapping):
        raw_label = raw_val.get("label") or raw_val.get("class_name") or ""
        raw_ing_id = raw_val.get("ingredient_id")
        ing_uuid = (
            raw_ing_id
            if isinstance(raw_ing_id, UUID) or raw_ing_id is None
            else UUID(str(raw_ing_id))
        )
        category = raw_val.get("category")
        is_pantry = bool(raw_val.get("is_pantry", False)) or category == "pantry"
        is_active = bool(raw_val.get("is_active", True))
        return LabelMappingEntry(
            class_index=cls_id,
            class_name=str(raw_label).strip(),
            ingredient_id=ing_uuid,
            ingredient_name_vi=(
                str(raw_val["ingredient_name_vi"]).strip()
                if raw_val.get("ingredient_name_vi")
                else (
                    str(raw_val["name_vi"]).strip()
                    if raw_val.get("name_vi")
                    else None
                )
            ),
            is_pantry=is_pantry,
            is_active=is_active,
            category=str(category) if category is not None else None,
        )

    raise InvalidClassMappingError(
        "Định dạng phần tử ánh xạ nhãn thực phẩm không hợp lệ.",
        details={"class_id": cls_id, "type": type(raw_val).__name__},
    )


# ==============================================================================
# THUẬT TOÁN: Chuẩn hóa & Kiểm định Bảng Ánh xạ Nhãn Thực phẩm (Label Mapping Validator)
# - Chuyển đổi linh hoạt cấu trúc ánh xạ từ dict/list sang bảng chỉ mục `dict[int, LabelMappingEntry]`.
# - Chặn trùng lặp `class_id`, loại bỏ nhãn không hoạt động (`is_active=False`) hoặc thuộc nhóm
#   gia vị nền (`category == 'pantry'`) theo đúng quy tắc `ADR-006` và `ADR-008`.
# ==============================================================================
def normalize_class_mapping(
    class_mapping: ClassMappingInput | None,
    *,
    strict: bool = True,
) -> dict[int, LabelMappingEntry]:
    """Validate and normalize food class mapping into `dict[int, LabelMappingEntry]`."""
    if class_mapping is None:
        return {}

    normalized: dict[int, LabelMappingEntry] = {}
    items: list[tuple[int, LabelMappingEntry | str | Mapping[str, Any]]] = []

    if isinstance(class_mapping, Mapping):
        for raw_k, raw_v in class_mapping.items():
            items.append((_parse_int_class_id(raw_k), raw_v))
    elif isinstance(class_mapping, Sequence) and not isinstance(
        class_mapping, (str, bytes, bytearray)
    ):
        for raw_item in class_mapping:
            if isinstance(raw_item, LabelMappingEntry):
                cls_id = _parse_int_class_id(raw_item.class_index)
                items.append((cls_id, raw_item))
            elif isinstance(raw_item, Mapping):
                raw_idx = (
                    raw_item.get("class_id")
                    if "class_id" in raw_item
                    else raw_item.get("class_index")
                )
                cls_id = _parse_int_class_id(raw_idx)
                items.append((cls_id, raw_item))
            else:
                raise InvalidClassMappingError(
                    "Danh sách ánh xạ nhãn chứa phần tử không hợp lệ.",
                    details={"type": type(raw_item).__name__},
                )
    else:
        raise InvalidClassMappingError(
            "Cấu trúc bảng ánh xạ nhãn không hợp lệ.",
            details={"type": type(class_mapping).__name__},
        )

    for cls_id, raw_entry in items:
        if cls_id in normalized:
            raise InvalidClassMappingError(
                "Trùng lặp class_id trong bảng ánh xạ nhãn.",
                details={"class_id": cls_id},
            )
        entry = _coerce_mapping_entry(cls_id, raw_entry)
        if not entry.class_name:
            raise InvalidClassMappingError(
                "Tên nhãn nguyên liệu trong ánh xạ không được để trống.",
                details={"class_id": cls_id},
            )
        is_pantry_entry = entry.is_pantry or entry.category == "pantry"
        if strict and (is_pantry_entry or not entry.is_active):
            raise InvalidClassMappingError(
                "Nhãn YOLO chỉ được ánh xạ tới nguyên liệu chính đang hoạt động (không thuộc nhóm pantry).",
                details={
                    "class_id": cls_id,
                    "label": entry.class_name,
                    "is_pantry": is_pantry_entry,
                    "is_active": entry.is_active,
                },
            )
        normalized[cls_id] = entry

    return normalized


def load_class_mapping_from_json_file(mapping_path: str | Path) -> dict[int, LabelMappingEntry]:
    """Load and validate a food class mapping JSON file from disk."""
    resolved = _resolve_artifact_path(mapping_path)
    if not resolved.is_file():
        raise DetectorConfigurationError(
            "Không tìm thấy tệp cấu hình ánh xạ nhãn thực phẩm.",
            details={"reason": "missing_class_mapping_file", "path": str(resolved)},
        )
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DetectorConfigurationError(
            "Tệp cấu hình ánh xạ nhãn thực phẩm không đọc được hoặc sai cú pháp JSON.",
            details={"reason": "invalid_class_mapping_json", "path": str(resolved)},
        ) from exc
    return normalize_class_mapping(payload, strict=True)


def _resolve_artifact_path(raw_path: str | Path) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute() or candidate.exists():
        return candidate.resolve(strict=False)
    backend_root = Path(__file__).resolve().parents[3]
    in_backend = backend_root / candidate
    if in_backend.exists():
        return in_backend.resolve(strict=False)
    repo_root = backend_root.parent
    in_repo = repo_root / candidate
    if in_repo.exists():
        return in_repo.resolve(strict=False)
    return in_backend.resolve(strict=False)
