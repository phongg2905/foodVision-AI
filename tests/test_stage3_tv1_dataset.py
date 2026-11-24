"""Stage 3 Automated Verification Suite for TV1 (Minh Thanh - Card #19 fVvygYRs).

Verifies all 4 checklist items of Card #19:
1. 20 canonical classes (`0..19`) matching `docs/04-ai-model/label-catalog.md`,
   strictly 0% `pantry` classes (`BR-12`, `ADR-008`), and NFR-11 class locking.
2. `70/15/15` stratified split grouped by `scene_id` / `session_id` with zero scene
   leakage across `train`, `val`, `test`.
3. `>= 10%` hard-negative / OOD images (empty `.txt` labels) and portrait
   `EXIF Orientation != 1` test fixtures (`Orientation in {3, 6, 8}`, `TC-43`).
4. `validate_dataset.py` verifies normalized `[0, 1]` bounding boxes, paired images,
   and cryptographic SHA-256 lock on `dataset_ready_manifest.json` (`NFR-11`).
"""

from __future__ import annotations

import json
import shutil
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.prepare_yolo_dataset import (  # noqa: E402
    build_yolo_dataset,
    parse_and_remap_label_file,
)
from scripts.validate_dataset import (  # noqa: E402
    DatasetValidationReport,
    validate_dataset_directory,
    validate_yolo_yaml_config,
)
from scripts.yolo_dataset_core import (  # noqa: E402
    CANONICAL_CLASSES,
    DEFAULT_OUT_DIR,
    DEFAULT_TRACKED_MANIFEST,
    DEFAULT_TRACKED_YAML,
    FORBIDDEN_PANTRY_RAW_INDICES,
    assign_scenes_stratified,
    assign_scenes_to_splits,
    extract_scene_id,
    sanitize_yolo_bbox,
)


def test_canonical_20_classes_yaml_and_zero_pantry_exclusion() -> None:
    raw_yaml = (
        REPO_ROOT
        / "datasets"
        / "raw"
        / "food-ingredients-roboflow-v1"
        / "food_ingredients_v1.yaml"
    )
    assert DEFAULT_TRACKED_YAML.exists()
    for y_path in (DEFAULT_TRACKED_YAML, raw_yaml):
        if y_path.exists():
            report = DatasetValidationReport()
            validate_yolo_yaml_config(y_path, report)
            assert report.is_valid, f"YAML validation failed for {y_path}: {report.errors}"


# THUẬT TOÁN: Kiểm chứng trích xuất scene_id bất biến trước hậu tố .rf.<hash> và chia tập
# phân tầng đa nhãn 70/15/15 đảm bảo 0% giao thoa scene_id đồng thời phân phối lớp hiếm vào cả 3 tập.
def test_extract_scene_id_and_stratified_group_split_prevent_scene_leakage() -> None:
    stem_a1 = "kitchen_session_01_frame1_jpg.rf.edb1f2ea7f54b2c52304df7c2cc391cd"
    stem_a2 = "kitchen_session_01_frame1_jpg.rf.99999999999999999999999999999999"
    assert extract_scene_id(stem_a1) == extract_scene_id(stem_a2)
    assert extract_scene_id(stem_a1) == "kitchen_session_01_frame1"

    scenes = [f"scene_{i:04d}" for i in range(200)]
    split_map = assign_scenes_to_splits(scenes)
    assert sum(1 for sp in split_map.values() if sp == "train") == 140
    assert sum(1 for sp in split_map.values() if sp == "val") == 30
    assert sum(1 for sp in split_map.values() if sp == "test") == 30

    strat_input: dict[str, Counter[int]] = {}
    for idx in range(100):
        c: Counter[int] = Counter({0: 3})
        if idx < 10:
            c[9] = 4  # rare class present in 10 scenes
        strat_input[f"strat_scene_{idx:03d}"] = c

    strat_map = assign_scenes_stratified(strat_input)
    tr_s = {s for s, sp in strat_map.items() if sp == "train"}
    va_s = {s for s, sp in strat_map.items() if sp == "val"}
    te_s = {s for s, sp in strat_map.items() if sp == "test"}

    assert len(tr_s) == 70
    assert len(va_s) == 15
    assert len(te_s) == 15
    assert (tr_s & va_s) == set()
    assert (tr_s & te_s) == set()
    assert (va_s & te_s) == set()
    # Rare class 9 must appear in train, val, and test
    for subset in (tr_s, va_s, te_s):
        assert sum(strat_input[s][9] for s in subset) > 0


def test_parse_and_remap_label_file_drops_pantry_and_non_target_subclasses() -> None:
    scratch_dir = REPO_ROOT / "datasets" / "processed" / "_pytest_scratch_remap"
    shutil.rmtree(scratch_dir, ignore_errors=True)
    scratch_dir.mkdir(parents=True, exist_ok=True)
    try:
        lbl_file = scratch_dir / "sample_jpg.rf.abc123.txt"
        # 108 = Tomato (0), 31 = Chicken (12), 32 = Chicken Gizzards (OOD -1),
        # 79 = Paneer white cheese (OOD -1), 94 = Salt (pantry -2), 102 = Sugar (pantry -2)
        lbl_file.write_text(
            "108 0.500000 0.500000 0.400000 0.400000\n"
            "31 0.250000 0.300000 0.200000 0.200000\n"
            "32 0.400000 0.400000 0.200000 0.200000\n"
            "79 0.600000 0.600000 0.200000 0.200000\n"
            "94 0.100000 0.100000 0.100000 0.100000\n"
            "102 0.800000 0.800000 0.150000 0.150000\n",
            encoding="utf-8",
        )
        boxes, dropped_pantry = parse_and_remap_label_file(lbl_file)
        assert dropped_pantry == 2
        assert len(boxes) == 2
        assert boxes[0][0] == 0   # tomato
        assert boxes[1][0] == 12  # raw_chicken (only 31, not 32)
        assert sanitize_yolo_bbox(0.5, 0.5, 0.0, 0.4) is None
    finally:
        shutil.rmtree(scratch_dir, ignore_errors=True)


# THUẬT TOÁN: Kiểm thử tích hợp toàn trình xây dựng + kiểm định dataset trên thư mục giả lập
# có ảnh JPEG thật, bao gồm cả luồng khóa NFR-11 và luồng bổ sung mẫu thật (--supplement-dir).
def test_build_and_validate_yolo_dataset_end_to_end_and_supplement_promotion() -> None:
    scratch_dir = REPO_ROOT / "datasets" / "processed" / "_pytest_scratch_e2e"
    shutil.rmtree(scratch_dir, ignore_errors=True)
    raw_dir = scratch_dir / "raw_roboflow"
    sup_dir = scratch_dir / "custom_supplement"
    out_dir = scratch_dir / "processed_v1"
    (raw_dir / "train" / "labels").mkdir(parents=True, exist_ok=True)
    (raw_dir / "train" / "images").mkdir(parents=True, exist_ok=True)
    (sup_dir / "train" / "labels").mkdir(parents=True, exist_ok=True)
    (sup_dir / "train" / "images").mkdir(parents=True, exist_ok=True)

    try:
        sample_jpg = scratch_dir / "seed_rgb.jpg"
        Image.new("RGB", (128, 128), color=(210, 50, 45)).save(sample_jpg, format="JPEG")

        # 45 positive scenes -> 90 Tomato boxes (>= 80), 90 Egg boxes (>= 80), 45 Tofu boxes (< 80)
        for i in range(45):
            stem = f"pos_scene_{i:03d}_jpg.rf.hash{i:03d}"
            shutil.copyfile(sample_jpg, raw_dir / "train" / "images" / f"{stem}.jpg")
            (raw_dir / "train" / "labels" / f"{stem}.txt").write_text(
                "108 0.500000 0.500000 0.300000 0.300000\n"
                "108 0.250000 0.250000 0.200000 0.200000\n"
                "43 0.700000 0.700000 0.200000 0.200000\n"
                "43 0.300000 0.700000 0.200000 0.200000\n"
                "107 0.500000 0.200000 0.180000 0.180000\n"
                "94 0.100000 0.100000 0.100000 0.100000\n",
                encoding="utf-8",
            )

        # 25 pure OOD scenes (Apple id=1)
        for j in range(25):
            stem = f"ood_scene_{j:03d}_jpg.rf.hash{j:03d}"
            shutil.copyfile(sample_jpg, raw_dir / "train" / "images" / f"{stem}.jpg")
            (raw_dir / "train" / "labels" / f"{stem}.txt").write_text(
                "1 0.400000 0.400000 0.250000 0.250000\n",
                encoding="utf-8",
            )

        # Run 1: without supplement -> tomato (0) & egg (1) locked (K=2), tofu (11) deferred (45 < 80)
        manifest_1 = build_yolo_dataset(
            raw_dir=raw_dir,
            out_dir=out_dir,
            supplement_dir=None,
            copy_images=True,
        )
        assert manifest_1["status"] == "dataset_ready"
        assert manifest_1["locked_eval_class_count"] == 2
        assert "11" in manifest_1["deferred_under_threshold_classes"]
        assert manifest_1["deferred_under_threshold_classes"]["11"]["count"] == 45
        assert manifest_1["dropped_pantry_boxes_count"] == 45
        assert len(FORBIDDEN_PANTRY_RAW_INDICES) == 4

        report_1 = validate_dataset_directory(dataset_dir=out_dir, require_nonempty_images=True)
        assert report_1.is_valid, f"Validation failed: {report_1.errors}"
        assert report_1.overall_ood_ratio >= 0.10
        assert {3, 6, 8}.issubset(set(report_1.exif_orientations_found))

        # Run 2: add 20 real supplement scenes for canonical class 11 (tofu, 2 boxes each = +40 -> 85 >= 80)
        for k in range(20):
            s_stem = f"vn_kitchen_tofu_{k:03d}_jpg.rf.sup{k:03d}"
            shutil.copyfile(sample_jpg, sup_dir / "train" / "images" / f"{s_stem}.jpg")
            (sup_dir / "train" / "labels" / f"{s_stem}.txt").write_text(
                "11 0.450000 0.450000 0.300000 0.300000\n"
                "11 0.750000 0.550000 0.220000 0.220000\n",
                encoding="utf-8",
            )

        manifest_2 = build_yolo_dataset(
            raw_dir=raw_dir,
            out_dir=out_dir,
            supplement_dir=sup_dir,
            copy_images=True,
        )
        assert manifest_2["locked_eval_class_count"] == 3
        assert "11" in manifest_2["locked_eval_classes"]
        report_2 = validate_dataset_directory(dataset_dir=out_dir, require_nonempty_images=True)
        assert report_2.is_valid, f"Supplemented validation failed: {report_2.errors}"
    finally:
        shutil.rmtree(scratch_dir, ignore_errors=True)


def test_tracked_manifest_and_full_processed_dataset_integrity() -> None:
    assert DEFAULT_TRACKED_MANIFEST.exists()
    manifest = json.loads(DEFAULT_TRACKED_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["status"] == "dataset_ready"
    assert manifest["candidate_class_count"] == 20
    assert manifest["locked_eval_class_count"] >= 15
    assert manifest["dropped_pantry_boxes_count"] == 386
    assert set(manifest["locked_classes"].values()) == set(CANONICAL_CLASSES.values())

    if (DEFAULT_OUT_DIR / "dataset_ready_manifest.json").exists():
        report = validate_dataset_directory(
            dataset_dir=DEFAULT_OUT_DIR,
            require_nonempty_images=True,
        )
        assert report.is_valid, f"Processed dataset invalid: {report.errors}"
