"""Stage 3 Automated Dataset Validator for TV1 (Minh Thanh - Card #19 fVvygYRs).

Verifies all 4 checklist requirements of Card #19 on a prepared YOLO dataset using
batched parallel directory scanning:
1. 20 canonical classes (`0..19`) matching `label-catalog.md`, zero `pantry` classes
   (`BR-12`, `ADR-008`), and `>= 80` real instances for every locked evaluation class.
2. `70/15/15` split by `scene_id` / `session_id` with zero scene leakage across splits.
3. `>= 10%` hard-negative / OOD images (empty `.txt` labels) and portrait
   `EXIF Orientation != 1` test fixtures (`Orientation in {3, 6, 8}`).
4. Normalized bounding box coordinates in `[0, 1]` and tamper-evident `dataset_ready`
   manifest (`NFR-11`).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.yolo_dataset_core import (  # noqa: E402
    CANONICAL_CLASSES,
    DEFAULT_IO_WORKERS,
    DEFAULT_OUT_DIR,
    MIN_INSTANCES_PER_CLASS,
    SCAN_BATCH_SIZE,
    SPLIT_ORDER,
    extract_scene_id,
)

FORBIDDEN_PANTRY_SLUGS: frozenset[str] = frozenset(
    {
        "salt",
        "muoi",
        "sugar",
        "duong",
        "fish_sauce",
        "nuoc_mam",
        "nuoc-mam",
        "cooking_oil",
        "olive_oil",
        "dau_an",
        "dau-an",
        "black_pepper",
        "hat_tieu",
        "hat-tieu",
        "soy_sauce",
        "water",
        "nuoc",
    }
)


@dataclass
class DatasetValidationReport:
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    class_box_counts: dict[int, int] = field(default_factory=dict)
    locked_eval_class_count: int = 0
    deferred_class_count: int = 0
    split_file_counts: dict[str, int] = field(default_factory=dict)
    split_scene_counts: dict[str, int] = field(default_factory=dict)
    split_ood_counts: dict[str, int] = field(default_factory=dict)
    overall_ood_ratio: float = 0.0
    exif_orientations_found: list[int] = field(default_factory=list)
    manifest_sha256: str = ""


# THUẬT TOÁN: Kiểm tra tệp cấu hình YAML của Ultralytics YOLO đảm bảo đúng 20 lớp chuẩn
# (0..19) trong label-catalog.md và tuyệt đối không chứa bất kỳ nhãn gia vị nền (pantry) nào.
def validate_yolo_yaml_config(yaml_path: Path, report: DatasetValidationReport) -> None:
    if not yaml_path.exists():
        report.is_valid = False
        report.errors.append(f"Missing YOLO config file: {yaml_path}")
        return

    cfg = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        report.is_valid = False
        report.errors.append("YAML config is not a valid mapping")
        return

    if cfg.get("nc") != 20:
        report.is_valid = False
        report.errors.append(f"Expected nc=20 in {yaml_path.name}, got {cfg.get('nc')}")

    names = cfg.get("names", {})
    normalized_names: dict[int, str] = (
        {int(k): str(v) for k, v in names.items()}
        if isinstance(names, dict)
        else {idx: str(v) for idx, v in enumerate(names)}
    )
    if normalized_names != CANONICAL_CLASSES:
        report.is_valid = False
        report.errors.append("YAML class names (0..19) do not match label-catalog.md")

    for cls_name in normalized_names.values():
        if cls_name.lower() in FORBIDDEN_PANTRY_SLUGS:
            report.is_valid = False
            report.errors.append(f"Forbidden pantry class found in YAML: {cls_name}")


# THUẬT TOÁN: Kiểm định song song từng lô tệp nhãn (.txt) và tệp ảnh ghép cặp (.jpg),
# xác minh miền tọa độ chuẩn hóa [0, 1], diện tích dương và trích xuất tập scene_id.
def _validate_label_batch(
    batch: tuple[str, Path, list[str], bool],
) -> tuple[str, int, int, set[str], Counter[int], list[str]]:
    split, img_dir, lbl_paths, require_nonempty_images = batch
    file_count = 0
    ood_count = 0
    scenes: set[str] = set()
    cls_counts: Counter[int] = Counter()
    errs: list[str] = []

    for lbl_str in lbl_paths:
        file_count += 1
        fname = os.path.basename(lbl_str)
        stem = fname[:-4]
        scenes.add(extract_scene_id(stem))

        img_path = img_dir / f"{stem}.jpg"
        if not img_path.exists():
            errs.append(f"{split}/{fname}: missing paired image {img_path.name}")
        elif require_nonempty_images and img_path.stat().st_size == 0:
            errs.append(f"{split}/{fname}: paired image {img_path.name} is empty (0 bytes)")

        with open(lbl_str, "r", encoding="utf-8") as fh:
            lines = [ln.strip() for ln in fh if ln.strip()]

        if not lines:
            ood_count += 1
            continue

        for line_no, ln in enumerate(lines, start=1):
            parts = ln.split()
            if len(parts) != 5:
                errs.append(f"{fname}:{line_no} invalid token count")
                continue
            cls_id = int(parts[0])
            xc, yc, w, h = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
            if cls_id not in CANONICAL_CLASSES:
                errs.append(f"{fname}:{line_no} invalid class_id={cls_id}")
                continue
            if not (0.0 <= xc <= 1.0 and 0.0 <= yc <= 1.0 and 0.0 < w <= 1.0 and 0.0 < h <= 1.0):
                errs.append(f"{fname}:{line_no} bbox out of [0,1]: ({xc},{yc},{w},{h})")
                continue
            if (
                (xc - w * 0.5) < -1e-4
                or (yc - h * 0.5) < -1e-4
                or (xc + w * 0.5) > 1.0001
                or (yc + h * 0.5) > 1.0001
            ):
                errs.append(f"{fname}:{line_no} bbox corners exceed [0,1]: ({xc},{yc},{w},{h})")
                continue
            cls_counts[cls_id] += 1

    return split, file_count, ood_count, scenes, cls_counts, errs


# THUẬT TOÁN: Kiểm định toàn diện thư mục dataset theo 4 mục Checklist của Thẻ #19:
# 1. Cấu hình 20 lớp không chứa pantry + kiểm tra khóa lớp NFR-11 (>= 80 mẫu trên mỗi lớp khóa).
# 2. Không rò rỉ scene_id giữa train / val / test và tỷ lệ chia nhóm 70/15/15.
# 3. Tỷ lệ mẫu âm khó / OOD >= 10% và bộ ảnh dọc có cờ EXIF Orientation thuộc {3, 6, 8}.
# 4. Đối chiếu mã băm toàn vẹn SHA-256 của tệp dataset_ready_manifest.json.
def validate_dataset_directory(
    dataset_dir: Path = DEFAULT_OUT_DIR,
    min_instances_per_class: int = MIN_INSTANCES_PER_CLASS,
    min_ood_ratio: float = 0.10,
    require_nonempty_images: bool = False,
) -> DatasetValidationReport:
    report = DatasetValidationReport()
    validate_yolo_yaml_config(dataset_dir / "food_ingredients_v1.yaml", report)

    class_counts: Counter[int] = Counter({idx: 0 for idx in CANONICAL_CLASSES})
    scenes_by_split: dict[str, set[str]] = {s: set() for s in SPLIT_ORDER}
    files_by_split: Counter[str] = Counter()
    ood_by_split: Counter[str] = Counter()

    batches: list[tuple[str, Path, list[str], bool]] = []
    for split in SPLIT_ORDER:
        lbl_dir = dataset_dir / "labels" / split
        img_dir = dataset_dir / "images" / split
        if not lbl_dir.exists():
            report.is_valid = False
            report.errors.append(f"Missing split label directory: {lbl_dir}")
            continue
        with os.scandir(lbl_dir) as it:
            txt_paths = sorted(entry.path for entry in it if entry.name.endswith(".txt"))
        for idx in range(0, len(txt_paths), SCAN_BATCH_SIZE):
            batches.append(
                (split, img_dir, txt_paths[idx : idx + SCAN_BATCH_SIZE], require_nonempty_images)
            )

    with ThreadPoolExecutor(max_workers=DEFAULT_IO_WORKERS) as pool:
        for split, f_cnt, o_cnt, sc_set, c_cnt, b_errs in pool.map(_validate_label_batch, batches):
            files_by_split[split] += f_cnt
            ood_by_split[split] += o_cnt
            scenes_by_split[split].update(sc_set)
            class_counts.update(c_cnt)
            if b_errs:
                report.is_valid = False
                report.errors.extend(b_errs[:20])

    report.class_box_counts = {idx: int(class_counts[idx]) for idx in CANONICAL_CLASSES}
    report.split_file_counts = {s: int(files_by_split[s]) for s in SPLIT_ORDER}
    report.split_scene_counts = {s: len(scenes_by_split[s]) for s in SPLIT_ORDER}
    report.split_ood_counts = {s: int(ood_by_split[s]) for s in SPLIT_ORDER}

    for i, s1 in enumerate(SPLIT_ORDER):
        for s2 in SPLIT_ORDER[i + 1 :]:
            overlap = scenes_by_split[s1] & scenes_by_split[s2]
            if overlap:
                report.is_valid = False
                report.errors.append(
                    f"Scene leakage detected between {s1} and {s2}: {len(overlap)} overlapping scenes"
                )

    total_scenes = sum(len(scenes_by_split[s]) for s in SPLIT_ORDER)
    if total_scenes > 0:
        tr_r = len(scenes_by_split["train"]) / total_scenes
        va_r = len(scenes_by_split["val"]) / total_scenes
        te_r = len(scenes_by_split["test"]) / total_scenes
        if not (0.65 <= tr_r <= 0.75 and 0.10 <= va_r <= 0.20 and 0.10 <= te_r <= 0.20):
            report.is_valid = False
            report.errors.append(
                f"Scene split ratios ({tr_r:.2%}/{va_r:.2%}/{te_r:.2%}) deviate from 70/15/15"
            )

    total_files = sum(files_by_split.values())
    total_ood = sum(ood_by_split.values())
    report.overall_ood_ratio = (total_ood / total_files) if total_files > 0 else 0.0
    if report.overall_ood_ratio < min_ood_ratio:
        report.is_valid = False
        report.errors.append(
            f"Overall OOD / hard-negative ratio {report.overall_ood_ratio:.2%} is below {min_ood_ratio:.0%}"
        )

    exif_dir = dataset_dir / "exif_orientation_fixtures"
    orientation_tag = 0x0112
    found_orientations: list[int] = []
    if exif_dir.exists():
        for img_path in sorted(exif_dir.glob("*.jpg")):
            with Image.open(img_path) as im:
                ori = int(im.getexif().get(orientation_tag, 1))
                if ori != 1:
                    found_orientations.append(ori)
    report.exif_orientations_found = sorted(set(found_orientations))
    if not {3, 6, 8}.issubset(set(report.exif_orientations_found)):
        report.is_valid = False
        report.errors.append(
            f"Missing required EXIF Orientation != 1 fixtures (found: {report.exif_orientations_found})"
        )

    manifest_path = dataset_dir / "dataset_ready_manifest.json"
    if not manifest_path.exists():
        report.is_valid = False
        report.errors.append("Missing dataset_ready_manifest.json (NFR-11)")
        return report

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    recorded_sha = str(manifest.get("manifest_sha256", ""))
    manifest_copy = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    expected_sha = hashlib.sha256(
        json.dumps(manifest_copy, indent=2, sort_keys=True).encode("utf-8")
    ).hexdigest()
    report.manifest_sha256 = recorded_sha
    if manifest.get("status") != "dataset_ready" or recorded_sha != expected_sha:
        report.is_valid = False
        report.errors.append("Tampered or invalid dataset_ready_manifest.json SHA-256")

    locked_eval = manifest.get("locked_eval_classes") or manifest.get("locked_classes") or {}
    deferred = manifest.get("deferred_under_threshold_classes") or {}
    report.locked_eval_class_count = len(locked_eval)
    report.deferred_class_count = len(deferred)

    for cls_key, cls_name in locked_eval.items():
        cid = int(cls_key)
        if class_counts[cid] < min_instances_per_class:
            report.is_valid = False
            report.errors.append(
                f"Locked eval class {cid} ({cls_name}) has {class_counts[cid]} boxes (< {min_instances_per_class})"
            )

    for cid, cls_name in CANONICAL_CLASSES.items():
        s_key = str(cid)
        if s_key not in locked_eval and s_key not in deferred:
            report.is_valid = False
            report.errors.append(
                f"Class {cid} ({cls_name}) missing from both locked_eval_classes and deferred_under_threshold_classes"
            )

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate FoodVision AI YOLO v1 dataset.")
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--require-nonempty-images", action="store_true")
    args = parser.parse_args()

    report = validate_dataset_directory(
        dataset_dir=args.dataset_dir,
        require_nonempty_images=args.require_nonempty_images,
    )
    print(f"Validation status: {'PASS' if report.is_valid else 'FAIL'}")
    print(f"Locked eval classes (K): {report.locked_eval_class_count} (deferred: {report.deferred_class_count})")
    print(f"Split file counts: {report.split_file_counts}")
    print(f"Split scene counts: {report.split_scene_counts}")
    print(f"Overall OOD ratio: {report.overall_ood_ratio:.2%}")
    print(f"EXIF orientations verified: {report.exif_orientations_found}")
    print(f"Manifest SHA-256: {report.manifest_sha256}")
    if not report.is_valid:
        for err in report.errors:
            print(f"  ERROR: {err}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
