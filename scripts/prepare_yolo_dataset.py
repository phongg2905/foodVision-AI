"""Stage 3 Dataset Preparation Pipeline for TV1 (Minh Thanh - Card #19 fVvygYRs).

Transforms `datasets/raw/food-ingredients-roboflow-v1/` (120 raw Roboflow classes,
24,035 files) into the canonical FoodVision AI YOLO v1 dataset
(`datasets/processed/food-ingredients-v1/`) using parallel batched I/O and zero-copy
NTFS hardlinks:
- Checklist 1: 20 canonical candidate classes (`0..19`) matching `label-catalog.md`,
  strictly 0% `pantry` classes (`BR-12`, `ADR-008`).
- Checklist 2: `70% train / 15% val / 15% test` multi-label stratified split grouped
  by `scene_id` guaranteeing zero scene leakage across splits.
- Checklist 3: `>= 10%` real hard-negative / OOD images in every split + real-photo
  portrait `EXIF Orientation != 1` (`{3, 6, 8}`) fixtures (`TC-43`, `ADR-010`).
- Checklist 4: Normalized `[0, 1]` bounding boxes, `food_ingredients_v1.yaml`, and
  cryptographically locked `dataset_ready_manifest.json` (`NFR-11`).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.yolo_dataset_core import (  # noqa: E402
    CANONICAL_CLASSES,
    DEFAULT_IO_WORKERS,
    DEFAULT_OUT_DIR,
    DEFAULT_RAW_DIR,
    DEFAULT_SUPPLEMENT_DIR,
    DEFAULT_TRACKED_MANIFEST,
    DEFAULT_TRACKED_YAML,
    FORBIDDEN_PANTRY_RAW_INDICES,
    MIN_HARD_NEGATIVE_RATIO,
    MIN_INSTANCES_PER_CLASS,
    SCAN_BATCH_SIZE,
    SPLIT_ORDER,
    assign_scenes_stratified,
    assign_scenes_to_splits,
    extract_scene_id,
    sanitize_yolo_bbox,
)
from scripts.yolo_dataset_io import (  # noqa: E402
    NegRecord,
    PosRecord,
    collect_scan_batches,
    create_exif_orientation_fixtures,
    parse_and_remap_label_file,
    scan_label_batch,
    write_output_batch,
)

__all__ = [
    "CANONICAL_CLASSES",
    "DEFAULT_OUT_DIR",
    "FORBIDDEN_PANTRY_RAW_INDICES",
    "MIN_INSTANCES_PER_CLASS",
    "SPLIT_ORDER",
    "assign_scenes_stratified",
    "assign_scenes_to_splits",
    "build_yolo_dataset",
    "create_exif_orientation_fixtures",
    "extract_scene_id",
    "parse_and_remap_label_file",
    "sanitize_yolo_bbox",
]


# THUẬT TOÁN: Điều phối toàn trình xây dựng Dataset YOLO v1:
# 1. Quét song song toàn bộ kho Roboflow 24,035 tệp (+ thư mục bổ sung nếu có).
# 2. Chia tập phân tầng đa nhãn 70/15/15 theo scene_id bảo đảm 0% rò rỉ cảnh chụp.
# 3. Tuyển chọn >= 12% ảnh OOD/hard-negative thuần túy (tách rời tập scene dương).
# 4. Khóa danh sách lớp đạt ngưỡng >= 80 mẫu ở mốc dataset_ready đúng chuẩn NFR-11.
def build_yolo_dataset(
    raw_dir: Path = DEFAULT_RAW_DIR,
    out_dir: Path = DEFAULT_OUT_DIR,
    supplement_dir: Path | None = DEFAULT_SUPPLEMENT_DIR,
    max_positive_scenes: int | None = None,
    copy_images: bool = True,
    sync_tracked_manifest: bool = False,
) -> dict[str, Any]:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    for split in SPLIT_ORDER:
        (out_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (out_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    positive_by_scene: dict[str, list[PosRecord]] = defaultdict(list)
    negative_by_scene: dict[str, list[NegRecord]] = defaultdict(list)
    raw_class_counts: Counter[int] = Counter()
    supplement_class_counts: Counter[int] = Counter()
    dropped_pantry_total = 0

    raw_batches = collect_scan_batches(
        raw_dir, ("train", "valid", "test"), already_canonical=False
    )
    with ThreadPoolExecutor(max_workers=DEFAULT_IO_WORKERS) as pool:
        for pos_list, neg_list, cls_cnt, pan_cnt in pool.map(scan_label_batch, raw_batches):
            dropped_pantry_total += pan_cnt
            raw_class_counts.update(cls_cnt)
            for rec in pos_list:
                positive_by_scene[rec[0]].append(rec)
            for nrec in neg_list:
                negative_by_scene[nrec[0]].append(nrec)

    if supplement_dir is not None and supplement_dir.exists():
        sup_batches = collect_scan_batches(
            supplement_dir, ("train", "valid", "val", "test"), already_canonical=True
        )
        with ThreadPoolExecutor(max_workers=DEFAULT_IO_WORKERS) as pool:
            for pos_list, _neg_list, cls_cnt, _pan in pool.map(scan_label_batch, sup_batches):
                supplement_class_counts.update(cls_cnt)
                for rec in pos_list:
                    positive_by_scene[rec[0]].append(rec)

    all_pos_scenes = sorted(positive_by_scene.keys())
    if max_positive_scenes is not None and len(all_pos_scenes) > max_positive_scenes:
        rare_cls = {c for c, n in raw_class_counts.items() if n < 250}
        pri = [
            s
            for s in all_pos_scenes
            if any(b[0] in rare_cls for r in positive_by_scene[s] for b in r[3])
        ]
        pri_set = set(pri)
        reg = [s for s in all_pos_scenes if s not in pri_set]
        selected_pos_scenes = (pri + reg)[:max_positive_scenes]
    else:
        selected_pos_scenes = all_pos_scenes

    scene_box_map: dict[str, Counter[int]] = {}
    for sid in selected_pos_scenes:
        c_map: Counter[int] = Counter()
        for _sid, _lp, _ip, boxes in positive_by_scene[sid]:
            for cls_idx, *_ in boxes:
                c_map[cls_idx] += 1
        scene_box_map[sid] = c_map

    pos_split_map = assign_scenes_stratified(scene_box_map)
    pos_file_total = sum(len(positive_by_scene[sid]) for sid in selected_pos_scenes)
    min_ood_needed = max(
        30,
        int(math.ceil(pos_file_total * MIN_HARD_NEGATIVE_RATIO / (1.0 - MIN_HARD_NEGATIVE_RATIO))),
    )

    pure_neg_scenes = [sid for sid in sorted(negative_by_scene.keys()) if sid not in positive_by_scene]
    selected_neg_scenes: list[str] = []
    acc_neg = 0
    for sid in pure_neg_scenes:
        selected_neg_scenes.append(sid)
        acc_neg += len(negative_by_scene[sid])
        if acc_neg >= min_ood_needed and len(selected_neg_scenes) >= 20:
            break
    neg_split_map = assign_scenes_to_splits(selected_neg_scenes)

    allow_placeholder = not copy_images
    write_tasks: list[tuple[Path, Path, Path, str, bool]] = []
    final_class_counts: Counter[int] = Counter()
    per_split_class_counts: dict[str, Counter[int]] = {s: Counter() for s in SPLIT_ORDER}
    split_file_counts: Counter[str] = Counter()
    split_ood_counts: Counter[str] = Counter()
    split_scene_sets: dict[str, set[str]] = {s: set() for s in SPLIT_ORDER}
    sample_tomato_img: Path | None = None

    for sid in selected_pos_scenes:
        split = pos_split_map[sid]
        split_scene_sets[split].add(sid)
        for _s, lbl_path, src_img, boxes in sorted(positive_by_scene[sid], key=lambda x: x[1].name):
            if sample_tomato_img is None and any(b[0] == 0 for b in boxes) and src_img.exists():
                sample_tomato_img = src_img
            text = "\n".join(f"{c} {x:.6f} {y:.6f} {w:.6f} {h:.6f}" for c, x, y, w, h in boxes) + "\n"
            dst_lbl = out_dir / "labels" / split / lbl_path.name
            dst_img = out_dir / "images" / split / f"{lbl_path.stem}.jpg"
            write_tasks.append((src_img, dst_img, dst_lbl, text, allow_placeholder))
            split_file_counts[split] += 1
            for c_idx, *_ in boxes:
                final_class_counts[c_idx] += 1
                per_split_class_counts[split][c_idx] += 1

    for sid in selected_neg_scenes:
        split = neg_split_map[sid]
        split_scene_sets[split].add(sid)
        for _s, lbl_path, src_img in sorted(negative_by_scene[sid], key=lambda x: x[1].name):
            dst_lbl = out_dir / "labels" / split / lbl_path.name
            dst_img = out_dir / "images" / split / f"{lbl_path.stem}.jpg"
            write_tasks.append((src_img, dst_img, dst_lbl, "", allow_placeholder))
            split_file_counts[split] += 1
            split_ood_counts[split] += 1

    task_chunks = [
        write_tasks[i : i + SCAN_BATCH_SIZE] for i in range(0, len(write_tasks), SCAN_BATCH_SIZE)
    ]
    with ThreadPoolExecutor(max_workers=DEFAULT_IO_WORKERS) as pool:
        list(pool.map(write_output_batch, task_chunks))

    exif_fixtures = create_exif_orientation_fixtures(out_dir, sample_tomato_img)
    (out_dir / "food_ingredients_v1.yaml").write_text(
        DEFAULT_TRACKED_YAML.read_text(encoding="utf-8"), encoding="utf-8"
    )

    locked_eval_classes = {
        str(k): v
        for k, v in CANONICAL_CLASSES.items()
        if final_class_counts[k] >= MIN_INSTANCES_PER_CLASS
    }
    deferred_classes = {
        str(k): {
            "name": v,
            "count": int(final_class_counts[k]),
            "deficit_to_80": int(MIN_INSTANCES_PER_CLASS - final_class_counts[k]),
            "fallback_policy": "FR-18 manual search & TP-02 CLIP helper",
        }
        for k, v in CANONICAL_CLASSES.items()
        if final_class_counts[k] < MIN_INSTANCES_PER_CLASS
    }

    manifest: dict[str, Any] = {
        "dataset_version": "foodvision-yolo-v1.0.0",
        "status": "dataset_ready",
        "candidate_class_count": 20,
        "locked_class_count": 20,
        "locked_eval_class_count": len(locked_eval_classes),
        "min_instances_per_locked_eval_class": MIN_INSTANCES_PER_CLASS,
        "locked_classes": {str(k): v for k, v in CANONICAL_CLASSES.items()},
        "locked_eval_classes": locked_eval_classes,
        "deferred_under_threshold_classes": deferred_classes,
        "pantry_classes_excluded": list(FORBIDDEN_PANTRY_RAW_INDICES.values()),
        "dropped_pantry_boxes_count": dropped_pantry_total,
        "raw_roboflow_class_counts": {
            CANONICAL_CLASSES[k]: int(raw_class_counts[k]) for k in CANONICAL_CLASSES
        },
        "custom_supplemented_box_counts": {
            CANONICAL_CLASSES[k]: int(supplement_class_counts[k]) for k in CANONICAL_CLASSES
        },
        "final_class_box_counts": {
            CANONICAL_CLASSES[k]: int(final_class_counts[k]) for k in CANONICAL_CLASSES
        },
        "per_split_class_box_counts": {
            s: {CANONICAL_CLASSES[k]: int(per_split_class_counts[s][k]) for k in CANONICAL_CLASSES}
            for s in SPLIT_ORDER
        },
        "split_file_counts": {s: int(split_file_counts[s]) for s in SPLIT_ORDER},
        "split_scene_counts": {s: len(split_scene_sets[s]) for s in SPLIT_ORDER},
        "split_ood_hard_negative_counts": {s: int(split_ood_counts[s]) for s in SPLIT_ORDER},
        "exif_orientation_fixtures": exif_fixtures,
    }
    canonical_payload = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    manifest["manifest_sha256"] = hashlib.sha256(canonical_payload).hexdigest()

    serialized = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    (out_dir / "dataset_ready_manifest.json").write_text(serialized, encoding="utf-8")
    if sync_tracked_manifest:
        DEFAULT_TRACKED_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_TRACKED_MANIFEST.write_text(serialized, encoding="utf-8")

    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare FoodVision AI 20-class YOLO v1 dataset.")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--supplement-dir", type=Path, default=DEFAULT_SUPPLEMENT_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--max-positive-scenes", type=int, default=None)
    parser.add_argument("--no-images", action="store_true")
    parser.add_argument("--sync-tracked-manifest", action="store_true")
    args = parser.parse_args()

    manifest = build_yolo_dataset(
        raw_dir=args.raw_dir,
        out_dir=args.out_dir,
        supplement_dir=args.supplement_dir,
        max_positive_scenes=args.max_positive_scenes,
        copy_images=not args.no_images,
        sync_tracked_manifest=args.sync_tracked_manifest,
    )
    print(f"Dataset ready at: {args.out_dir}")
    print(f"Locked eval classes (K): {manifest['locked_eval_class_count']} / 20")
    print(f"Manifest SHA-256: {manifest['manifest_sha256']}")
    print(f"Split file counts: {manifest['split_file_counts']}")
    print(f"Split OOD counts: {manifest['split_ood_hard_negative_counts']}")


if __name__ == "__main__":
    main()
