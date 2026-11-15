"""Parallel batched I/O and EXIF fixture builders for FoodVision AI YOLO v1 dataset.

Implements multi-threaded directory scanning via os.scandir(), O(1) class-index
remapping, zero-copy NTFS hardlink batch writing, and real-photo EXIF Orientation
({3, 6, 8}) portrait fixture generation for Card #19 (fVvygYRs).
"""

from __future__ import annotations

import os
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from scripts.yolo_dataset_core import (
    CANONICAL_CLASSES,
    LUT_PANTRY,
    RAW_CLASS_LUT,
    RAW_NUM_CLASSES,
    SCAN_BATCH_SIZE,
    extract_scene_id,
    link_or_copy_file,
    sanitize_yolo_bbox,
)

BoxTuple = tuple[int, float, float, float, float]
PosRecord = tuple[str, Path, Path, list[BoxTuple]]
NegRecord = tuple[str, Path, Path]


# THUẬT TOÁN: Đọc tệp nhãn thô và ánh xạ về chỉ số chuẩn (0..19) trong thời gian O(B)
# nhờ bảng tra cứu trực tiếp RAW_CLASS_LUT kích thước 120, đồng thời đếm và loại bỏ
# triệt để các hộp gia vị nền (pantry) theo BR-12 / ADR-008.
def parse_and_remap_label_file(
    label_path: Path | str,
    *,
    already_canonical: bool = False,
) -> tuple[list[BoxTuple], int]:
    remapped_boxes: list[BoxTuple] = []
    dropped_pantry_count = 0
    with open(label_path, "r", encoding="utf-8", errors="ignore") as fh:
        for raw_line in fh:
            parts = raw_line.split()
            if len(parts) < 5:
                continue
            raw_cls = int(parts[0])
            if already_canonical:
                if raw_cls not in CANONICAL_CLASSES:
                    continue
                target_cls = raw_cls
            else:
                if raw_cls < 0 or raw_cls >= RAW_NUM_CLASSES:
                    continue
                mapped = RAW_CLASS_LUT[raw_cls]
                if mapped == LUT_PANTRY:
                    dropped_pantry_count += 1
                    continue
                if mapped < 0:
                    continue
                target_cls = mapped

            bbox = sanitize_yolo_bbox(
                float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
            )
            if bbox is not None:
                remapped_boxes.append((target_cls, bbox[0], bbox[1], bbox[2], bbox[3]))
    return remapped_boxes, dropped_pantry_count


# THUẬT TOÁN: Quét song song theo lô (Batched Parallel Directory Scan) sử dụng os.scandir
# và ThreadPoolExecutor nhằm giảm độ trễ mở tệp NTFS trên hàng chục nghìn tệp nhãn nhỏ.
def scan_label_batch(
    batch: tuple[Path, list[str], bool],
) -> tuple[list[PosRecord], list[NegRecord], Counter[int], int]:
    images_dir, label_paths, already_canonical = batch
    pos_out: list[PosRecord] = []
    neg_out: list[NegRecord] = []
    cls_counts: Counter[int] = Counter()
    pantry_dropped = 0

    for lbl_str in label_paths:
        lbl_path = Path(lbl_str)
        stem = lbl_path.stem
        sid = extract_scene_id(stem)
        src_img = images_dir / f"{stem}.jpg"
        boxes, dropped = parse_and_remap_label_file(
            lbl_str, already_canonical=already_canonical
        )
        pantry_dropped += dropped
        if boxes:
            for c_idx, *_ in boxes:
                cls_counts[c_idx] += 1
            pos_out.append((sid, lbl_path, src_img, boxes))
        else:
            neg_out.append((sid, lbl_path, src_img))
    return pos_out, neg_out, cls_counts, pantry_dropped


def collect_scan_batches(
    base_dir: Path,
    splits: tuple[str, ...],
    *,
    already_canonical: bool,
) -> list[tuple[Path, list[str], bool]]:
    batches: list[tuple[Path, list[str], bool]] = []
    for r_split in splits:
        lbl_dir = base_dir / r_split / "labels"
        img_dir = base_dir / r_split / "images"
        if not lbl_dir.exists():
            continue
        with os.scandir(lbl_dir) as it:
            txt_files = sorted(entry.path for entry in it if entry.name.endswith(".txt"))
        for idx in range(0, len(txt_files), SCAN_BATCH_SIZE):
            batches.append((img_dir, txt_files[idx : idx + SCAN_BATCH_SIZE], already_canonical))
    return batches


# THUẬT TOÁN: Ghi lô nhãn chuẩn hóa (.txt) và liên kết cứng (os.link) tệp ảnh gốc (.jpg)
# song song theo lô để tối đa hóa băng thông I/O mà không nhân đôi dung lượng đĩa.
def write_output_batch(
    tasks: list[tuple[Path, Path, Path, str, bool]],
) -> None:
    for src_img, dst_img, dst_lbl, label_text, allow_placeholder in tasks:
        dst_lbl.write_text(label_text, encoding="utf-8")
        link_or_copy_file(src_img, dst_img, allow_empty_placeholder=allow_placeholder)


# THUẬT TOÁN: Sinh bộ ảnh kiểm thử dọc có gắn cờ EXIF Orientation != 1 ({3, 6, 8}) từ ảnh
# cà chua thực tế bằng phép biến đổi nghịch đảo pixel + ghi thẻ EXIF 0x0112 (TC-43, ADR-010).
def create_exif_orientation_fixtures(
    out_dir: Path,
    sample_tomato_image: Path | None = None,
) -> list[dict[str, Any]]:
    exif_dir = out_dir / "exif_orientation_fixtures"
    exif_dir.mkdir(parents=True, exist_ok=True)
    orientation_tag = 0x0112
    fixtures: list[dict[str, Any]] = []

    base_img: Image.Image | None = None
    has_real_source = False
    if sample_tomato_image is not None and sample_tomato_image.exists():
        if sample_tomato_image.stat().st_size > 0:
            with Image.open(sample_tomato_image) as loaded:
                base_img = loaded.convert("RGB")
                has_real_source = True

    if base_img is None:
        base_img = Image.new("RGB", (240, 320), color=(235, 64, 52))
        draw = ImageDraw.Draw(base_img)
        draw.ellipse([50, 80, 190, 220], fill=(220, 30, 20), outline=(255, 255, 255))

    inverse_ops = {
        3: Image.Transpose.ROTATE_180,
        6: Image.Transpose.ROTATE_90,
        8: Image.Transpose.ROTATE_270,
    }
    for orientation, transpose_op in inverse_ops.items():
        transformed = base_img.transpose(transpose_op)
        exif = transformed.getexif()
        exif[orientation_tag] = orientation
        fixture_path = exif_dir / f"tomato_exif_orientation_{orientation}.jpg"
        transformed.save(fixture_path, format="JPEG", exif=exif.tobytes(), quality=92)
        fixtures.append(
            {
                "filename": fixture_path.name,
                "exif_orientation": orientation,
                "target_class_index": 0,
                "target_class_name": "tomato",
                "source_type": "real_dataset_photo" if has_real_source else "fallback_fixture",
            }
        )
    base_img.close()
    return fixtures
