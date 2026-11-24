"""Core constants and speed-optimized primitives for FoodVision AI YOLO v1 dataset.

Provides O(1) class-index lookup tables, cached scene_id normalization, bounding-box
sanitization, deterministic multi-label stratified 70/15/15 scene splitting, and
zero-copy NTFS hardlink helpers for Card #19 (fVvygYRs).
"""

from __future__ import annotations

import hashlib
import math
import os
import re
import shutil
from collections import Counter
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = REPO_ROOT / "datasets" / "raw" / "food-ingredients-roboflow-v1"
DEFAULT_SUPPLEMENT_DIR = REPO_ROOT / "datasets" / "raw" / "custom-supplement-v1"
DEFAULT_OUT_DIR = REPO_ROOT / "datasets" / "processed" / "food-ingredients-v1"
DEFAULT_TRACKED_YAML = REPO_ROOT / "backend" / "configs" / "food_ingredients_v1.yaml"
DEFAULT_TRACKED_MANIFEST = REPO_ROOT / "backend" / "configs" / "dataset_ready_manifest.json"

CANONICAL_CLASSES: dict[int, str] = {
    0: "tomato",
    1: "egg",
    2: "potato",
    3: "carrot",
    4: "onion",
    5: "garlic",
    6: "chili_pepper",
    7: "cucumber",
    8: "cabbage",
    9: "broccoli",
    10: "mushroom",
    11: "tofu",
    12: "raw_chicken",
    13: "raw_pork",
    14: "raw_shrimp",
    15: "whole_fish",
    16: "ginger",
    17: "scallion",
    18: "bell_pepper",
    19: "sweet_corn",
}

# Raw Roboflow class index (0..119) -> Canonical FoodVision AI class_index (0..19).
# Strictly maps 31 ('Chicken') -> 12 ('raw_chicken') and excludes 32 ('Chicken Gizzards'),
# 79 ('Paneer' white cheese, OOD hard negative per label-catalog.md), 110 ('Tree Tomato' /
# Solanum betaceum), and 0 ('Akabare Khursani' round cherry chili) to eliminate domain noise.
ROBOFLOW_TO_CANONICAL: dict[int, int] = {
    108: 0,   # Tomato -> tomato (710; replaced Tree Tomato with clean CC-BY-4.0 supplement)
    43: 1,    # Egg -> egg (2,081)
    85: 2,    # Potato -> potato (1,479)
    26: 3,    # Carrot -> carrot (451)
    74: 4,    # Onion -> onion (400)
    49: 5,    # Garlic -> garlic (683)
    34: 6,    # Chili Pepper -Khursani- -> chili_pepper (2,937; excluded Akabare round chili)
    42: 7,    # Cucumber -> cucumber (437)
    24: 8,    # Cabbage -> cabbage (829)
    21: 9,    # Broccoli -> broccoli (211)
    69: 10,   # Mushroom -> mushroom (2,539)
    107: 11,  # Tofu -> tofu (41)
    31: 12,   # Chicken -> raw_chicken (52)
    84: 13,   # Pork -> raw_pork (376)
    46: 15,   # Fish -> whole_fish (6)
    50: 16,   # Ginger -> ginger (23)
    75: 17,   # Onion Leaves -> scallion (811)
    25: 18,   # Capsicum -> bell_pepper (1,130)
    39: 19,   # Corn -> sweet_corn (433)
}

# Forbidden pantry indices in raw Roboflow data.yaml (BR-12, ADR-008)
FORBIDDEN_PANTRY_RAW_INDICES: dict[int, str] = {
    73: "Olive Oil",
    94: "Salt",
    97: "Soy Sauce",
    102: "Sugar",
}

RAW_NUM_CLASSES = 120
LUT_OOD = -1
LUT_PANTRY = -2

# THUẬT TOÁN: Bảng tra cứu trực tiếp mảng tĩnh O(1) (Direct-Index Lookup Table) kích thước 120
# thay cho nhiều phép băm dict/set trên từng dòng nhãn:
# - Giá trị >= 0: mã lớp chuẩn (0..19) của FoodVision AI.
# - Giá trị -2 (LUT_PANTRY): lớp gia vị nền bị cấm theo BR-12 / ADR-008.
# - Giá trị -1 (LUT_OOD): lớp ngoài danh mục mục tiêu, dùng làm mẫu đối chứng âm (OOD).
def _build_raw_class_lut() -> tuple[int, ...]:
    table = [LUT_OOD] * RAW_NUM_CLASSES
    for raw_idx, target_idx in ROBOFLOW_TO_CANONICAL.items():
        table[raw_idx] = target_idx
    for pantry_idx in FORBIDDEN_PANTRY_RAW_INDICES:
        table[pantry_idx] = LUT_PANTRY
    return tuple(table)


RAW_CLASS_LUT: tuple[int, ...] = _build_raw_class_lut()

SPLIT_ORDER: tuple[str, str, str] = ("train", "val", "test")
TARGET_RATIOS: dict[str, float] = {"train": 0.70, "val": 0.15, "test": 0.15}
MIN_INSTANCES_PER_CLASS = 80
MIN_HARD_NEGATIVE_RATIO = 0.12
DEFAULT_IO_WORKERS = min(32, (os.cpu_count() or 4) * 4)
SCAN_BATCH_SIZE = 256

_EXT_SUFFIX_RE = re.compile(r"_(?:jpg|jpeg|png|webp)$", re.IGNORECASE)
_NON_ALNUM_RE = re.compile(r"[^a-z0-9_-]+")


# THUẬT TOÁN: Trích xuất định danh cảnh chụp gốc (scene_id / session_id) tốc độ cao O(L)
# kết hợp str.partition(".rf."), biểu thức chính quy biên dịch sẵn và bộ nhớ đệm LRU
# nhằm gom mọi biến thể tăng cường của cùng một ảnh gốc vào chung một nhóm chống rò rỉ.
@lru_cache(maxsize=65536)
def extract_scene_id(filename_stem: str) -> str:
    base = filename_stem.partition(".rf.")[0].lower()
    base = _EXT_SUFFIX_RE.sub("", base)
    normalized = _NON_ALNUM_RE.sub("_", base).strip("_")
    return normalized or "scene_unknown"


# THUẬT TOÁN: Kiểm tra và cắt biên hộp giới hạn YOLO (x_center, y_center, width, height)
# về đoạn chuẩn hóa [0.0, 1.0], loại bỏ hộp suy biến có chiều rộng hoặc chiều cao <= 1e-4.
def sanitize_yolo_bbox(
    xc: float, yc: float, w: float, h: float
) -> tuple[float, float, float, float] | None:
    if not (math.isfinite(xc) and math.isfinite(yc) and math.isfinite(w) and math.isfinite(h)):
        return None
    half_w = w * 0.5
    half_h = h * 0.5
    x1 = 0.0 if (xc - half_w) < 0.0 else (1.0 if (xc - half_w) > 1.0 else (xc - half_w))
    y1 = 0.0 if (yc - half_h) < 0.0 else (1.0 if (yc - half_h) > 1.0 else (yc - half_h))
    x2 = 0.0 if (xc + half_w) < 0.0 else (1.0 if (xc + half_w) > 1.0 else (xc + half_w))
    y2 = 0.0 if (yc + half_h) < 0.0 else (1.0 if (yc + half_h) > 1.0 else (yc + half_h))
    new_w = x2 - x1
    new_h = y2 - y1
    if new_w <= 1e-4 or new_h <= 1e-4:
        return None
    return (
        round(x1 + new_w * 0.5, 6),
        round(y1 + new_h * 0.5, 6),
        round(new_w, 6),
        round(new_h, 6),
    )


# THUẬT TOÁN: Phân chia nhóm scene_id tất định bằng băm mật mã SHA-256 theo đúng tỷ lệ
# 70% train / 15% val / 15% test, bảo đảm giao giữa ba tập scene_id luôn bằng rỗng.
def assign_scenes_to_splits(scene_ids: list[str]) -> dict[str, str]:
    sorted_scenes = sorted(
        set(scene_ids),
        key=lambda sid: hashlib.sha256(f"foodvision_v1::{sid}".encode("utf-8")).hexdigest(),
    )
    n_total = len(sorted_scenes)
    n_train = int(round(n_total * TARGET_RATIOS["train"]))
    n_val = int(round(n_total * TARGET_RATIOS["val"]))
    assignment: dict[str, str] = {}
    for idx, sid in enumerate(sorted_scenes):
        if idx < n_train:
            assignment[sid] = "train"
        elif idx < n_train + n_val:
            assignment[sid] = "val"
        else:
            assignment[sid] = "test"
    return assignment


# THUẬT TOÁN: Phân tầng đa nhãn theo nhóm cảnh chụp (Iterative Greedy Multi-Label Scene
# Stratification, lấy cảm hứng từ Sechidis et al. ECML-PKDD 2011):
# - Sắp xếp các scene ưu tiên theo lớp hiếm nhất xuất hiện trong scene (phá hòa tất định bằng SHA-256).
# - Gán từng scene vào tập s thuộc {train, val, test} còn hạn ngạch sao cho cực đại hóa độ thiếu hụt
#   tương đối (relative deficit) của các lớp hiếm và số lượng scene mục tiêu 70/15/15.
# - Bảo đảm đồng thời: (1) 0% rò rỉ scene_id, (2) tỷ lệ scene 70/15/15 chính xác, (3) phân phối đều lớp.
def assign_scenes_stratified(
    scene_box_counts: dict[str, Counter[int]],
) -> dict[str, str]:
    if not scene_box_counts:
        return {}

    unique_scenes = list(scene_box_counts.keys())
    n_total = len(unique_scenes)
    if n_total < 3:
        return assign_scenes_to_splits(unique_scenes)

    n_train = int(round(n_total * TARGET_RATIOS["train"]))
    n_val = int(round(n_total * TARGET_RATIOS["val"]))
    n_test = max(0, n_total - n_train - n_val)
    quotas = {"train": n_train, "val": n_val, "test": n_test}

    global_cls_totals: Counter[int] = Counter()
    for cnts in scene_box_counts.values():
        global_cls_totals.update(cnts)

    def _scene_sort_key(sid: str) -> tuple[int, int, str]:
        cnts = scene_box_counts[sid]
        rarest = min((global_cls_totals[c] for c in cnts if cnts[c] > 0), default=10**9)
        digest = hashlib.sha256(f"foodvision_v1::{sid}".encode("utf-8")).hexdigest()
        return (rarest, -sum(cnts.values()), digest)

    ordered_scenes = sorted(unique_scenes, key=_scene_sort_key)
    assigned_scenes: Counter[str] = Counter()
    assigned_boxes: dict[str, Counter[int]] = {s: Counter() for s in SPLIT_ORDER}
    split_priority = {"test": 0, "val": 1, "train": 2}
    assignment: dict[str, str] = {}

    for sid in ordered_scenes:
        cnts = scene_box_counts[sid]
        candidates = [s for s in SPLIT_ORDER if assigned_scenes[s] < quotas[s]]
        if not candidates:
            candidates = list(SPLIT_ORDER)

        best_split = candidates[0]
        best_score = -1e18
        for sp in candidates:
            ratio = TARGET_RATIOS[sp]
            scene_need = (quotas[sp] - assigned_scenes[sp]) / max(1, quotas[sp])
            class_need = 0.0
            if cnts:
                for cls_idx, c_val in cnts.items():
                    desired_cls = max(1.0, global_cls_totals[cls_idx] * ratio)
                    deficit_ratio = (desired_cls - assigned_boxes[sp][cls_idx]) / desired_cls
                    rarity_weight = 1.0 / math.sqrt(max(1, global_cls_totals[cls_idx]))
                    class_need += deficit_ratio * rarity_weight * math.log1p(c_val)
            score = class_need * 10.0 + scene_need - split_priority[sp] * 1e-6
            if score > best_score:
                best_score = score
                best_split = sp

        assignment[sid] = best_split
        assigned_scenes[best_split] += 1
        assigned_boxes[best_split].update(cnts)

    return assignment


# THUẬT TOÁN: Liên kết tệp ảnh tốc độ cao không sao chép dữ liệu (Zero-Copy NTFS Hardlink os.link)
# kèm cơ chế tự động chuyển sang shutil.copyfile nếu khác phân vùng ổ đĩa.
def link_or_copy_file(
    src_path: Path,
    dst_path: Path,
    *,
    allow_empty_placeholder: bool = False,
) -> bool:
    if src_path.exists():
        if dst_path.exists():
            dst_path.unlink()
        try:
            os.link(src_path, dst_path)
        except OSError:
            shutil.copyfile(src_path, dst_path)
        return True
    if allow_empty_placeholder:
        dst_path.write_bytes(b"")
        return False
    raise FileNotFoundError(f"Missing source image file: {src_path}")
