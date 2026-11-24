"""Balanced CC-BY-4.0 Dataset Supplement Ingestor for FoodVision AI YOLO v1.1.

Ingests verified open-license (`CC BY 4.0` / `CC BY 2.0`) object detection sources into
`datasets/raw/custom-supplement-v1/train/{images,labels}` using canonical class indices
(`0..19`, strictly zero `pantry` classes per `BR-12` and `ADR-008`):
1. Roboflow Universe `food-ingredients-2alny` v5 (`CC BY 4.0`, raw 1x 640px, 16 canonical classes)
2. Roboflow Universe `sages/tofu-47uo2` v1 (`CC BY 4.0`, `tofu`)
3. Roboflow Universe `blxm/fish-yjekd` v1 (`CC BY 4.0`, raw 1x whole market fish -> `whole_fish`)
4. Google Open Images Dataset v7 (`CC BY 4.0 / CC BY 2.0`, `Broccoli` `/m/0hkxq`)

Applies strict scene deduplication (max 1 image per unique `scene_id` per source),
multi-class-first balanced sampling (`seed=42`), normalized `[0, 1]` bbox sanitization,
and exports an `ADR-005` attribution log (`backend/configs/dataset_attribution_v1_1.json`).
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import io
import json
from pathlib import Path, PurePosixPath
import random
import shutil
import sys
from typing import Any
import zipfile

import httpx
from PIL import Image, ImageOps, UnidentifiedImageError

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.yolo_dataset_core import (  # noqa: E402
    CANONICAL_CLASSES,
    DEFAULT_IO_WORKERS,
    DEFAULT_SUPPLEMENT_DIR,
    sanitize_yolo_bbox,
)

DEFAULT_DOWNLOADS_DIR = Path(r"D:\Download\Chrome")
DEFAULT_ATTRIBUTION_JSON = REPO_ROOT / "backend" / "configs" / "dataset_attribution_v1_1.json"

# Direct O(1) lookup tables from verified CC BY 4.0 Roboflow source class IDs -> canonical 0..19
RF_FOOD_ING_V5_MAP: dict[int, int] = {
    19: 0,   # tomato -> tomato
    7: 1,    # egg -> egg
    15: 2,   # potato -> potato
    3: 3,    # carrot -> carrot
    13: 4,   # onion -> onion
    9: 5,    # garlic -> garlic
    17: 6,   # small_pepper -> chili_pepper
    6: 7,    # cucumber -> cucumber
    2: 8,    # cabbage -> cabbage
    18: 11,  # tofu -> tofu
    5: 12,   # chicken -> raw_chicken
    14: 13,  # pork -> raw_pork
    16: 14,  # shrimp -> raw_shrimp
    8: 15,   # fish -> whole_fish
    10: 16,  # ginger -> ginger
    1: 18,   # bell_pepper -> bell_pepper
}

RF_TOFU_V1_MAP: dict[int, int] = {0: 11}
RF_FISH_V1_MAP: dict[int, int] = {0: 15, 1: 15, 2: 15, 3: 15}

# Target scene budget per canonical class from supplement sources (balanced to prevent domination)
CLASS_SCENE_QUOTA: dict[int, int] = {
    0: 220,   # tomato (replaces noisy Tree Tomato)
    1: 120,   # egg
    2: 160,   # potato
    3: 260,   # carrot (fixes weak AP@50)
    4: 120,   # onion
    5: 260,   # garlic (fixes weak AP@50)
    6: 140,   # chili_pepper (replaces noisy Akabare)
    7: 200,   # cucumber (fixes 1-scene test variance)
    8: 140,   # cabbage
    9: 80,    # broccoli (Open Images v7 unique scenes)
    11: 340,  # tofu (food-ingredients v5 + sages/tofu)
    12: 300,  # raw_chicken
    13: 200,  # raw_pork
    14: 210,  # raw_shrimp (all available clean scenes)
    15: 340,  # whole_fish (food-ingredients v5 + blxm/fish)
    16: 280,  # ginger
    18: 160,  # bell_pepper
}


@dataclass(slots=True, frozen=True)
class ZipSceneCandidate:
    """Single deduplicated source scene candidate inside a Roboflow ZIP archive."""

    source_prefix: str
    scene_id: str
    img_member: str
    boxes: tuple[tuple[int, float, float, float, float], ...]
    class_set: frozenset[int]
    is_pure: bool


# THUẬT TOÁN: Trích xuất & Lọc Ứng viên Cảnh Gốc Độc lập từ Kho ZIP Roboflow (`O(N_entries)`)
# Cơ chế:
# - Quét một lượt danh mục tệp trong ZIP, ánh xạ O(1) sang cặp (image_member, label_member).
# - Khử trùng lặp augmentation `.rf.<hash>` bằng cách giữ tối đa 1 ảnh đại diện cho mỗi `scene_id`.
# - Ưu tiên ảnh thuần nhãn chuẩn (`is_pure = True`, 0 vật thể ngoài danh mục) và ảnh đa nguyên liệu.
# Độ phức tạp: Time O(N_files + N_boxes), Space O(N_unique_scenes).
def _scan_zip_candidates(
    zip_path: Path,
    source_prefix: str,
    class_map: dict[int, int],
    *,
    allow_impure_classes: frozenset[int] = frozenset(),
) -> list[ZipSceneCandidate]:
    candidates_by_scene: dict[str, ZipSceneCandidate] = {}
    with zipfile.ZipFile(zip_path, "r") as zf:
        img_lookup: dict[tuple[str, str], str] = {}
        lbl_members: list[tuple[str, str, str]] = []

        for info in zf.infolist():
            fn = info.filename
            if info.is_dir():
                continue
            parts = PurePosixPath(fn).parts
            if len(parts) < 3:
                continue
            split_dir, kind_dir = parts[0], parts[1]
            stem = PurePosixPath(fn).stem
            if kind_dir == "images" and fn.lower().endswith((".jpg", ".jpeg", ".png")):
                img_lookup[(split_dir, stem)] = fn
            elif kind_dir == "labels" and fn.endswith(".txt"):
                lbl_members.append((split_dir, stem, fn))

        for split_dir, stem, lbl_fn in sorted(lbl_members):
            img_fn = img_lookup.get((split_dir, stem))
            if img_fn is None:
                continue
            raw_scene = stem.split(".rf.")[0]
            if raw_scene in candidates_by_scene and candidates_by_scene[raw_scene].is_pure:
                continue

            text = zf.read(lbl_fn).decode("utf-8", errors="ignore")
            mapped_boxes: list[tuple[int, float, float, float, float]] = []
            has_unmapped = False
            for line in text.splitlines():
                toks = line.strip().split()
                if len(toks) < 5:
                    continue
                raw_cid = int(toks[0])
                canon_cid = class_map.get(raw_cid)
                if canon_cid is None:
                    has_unmapped = True
                    continue
                box = sanitize_yolo_bbox(
                    float(toks[1]),
                    float(toks[2]),
                    float(toks[3]),
                    float(toks[4]),
                )
                if box is not None:
                    mapped_boxes.append((canon_cid, *box))

            if not mapped_boxes:
                continue
            cset = frozenset(b[0] for b in mapped_boxes)
            is_pure = not has_unmapped
            if not is_pure and not (cset & allow_impure_classes):
                continue

            cand = ZipSceneCandidate(
                source_prefix=source_prefix,
                scene_id=raw_scene,
                img_member=img_fn,
                boxes=tuple(mapped_boxes),
                class_set=cset,
                is_pure=is_pure,
            )
            prev = candidates_by_scene.get(raw_scene)
            if prev is None or (cand.is_pure and not prev.is_pure) or (
                cand.is_pure == prev.is_pure and len(cand.class_set) > len(prev.class_set)
            ):
                candidates_by_scene[raw_scene] = cand

    return list(candidates_by_scene.values())


# THUẬT TOÁN: Chọn Mẫu Cân bằng Ưu tiên Ảnh Đa Nguyên liệu & Lớp Hiếm (`Greedy Quota Sampling`)
# Cơ chế: Sắp xếp tất định (seed=42) ưu tiên: (1) ảnh thuần nhãn chuẩn, (2) chứa lớp đang thiếu nhất,
#         (3) nhiều lớp trong cùng một khung hình, rồi lấy đến khi đủ hạn mức `CLASS_SCENE_QUOTA`.
# Độ phức tạp: Time O(S log S), Space O(S).
def _select_balanced_candidates(
    candidates: list[ZipSceneCandidate],
    current_class_scenes: Counter[int],
    quotas: dict[int, int],
    *,
    seed: int = 42,
) -> list[ZipSceneCandidate]:
    rng = random.Random(seed)
    shuffled = list(candidates)
    rng.shuffle(shuffled)
    shuffled.sort(
        key=lambda c: (
            0 if c.is_pure else 1,
            -len(c.class_set),
            min(quotas.get(cid, 0) - current_class_scenes[cid] for cid in c.class_set),
        ),
        reverse=False,
    )

    selected: list[ZipSceneCandidate] = []
    # Two-pass: pass 1 focuses strictly on scenes containing at least one under-quota class
    for cand in shuffled:
        if any(current_class_scenes[cid] < quotas.get(cid, 0) for cid in cand.class_set):
            selected.append(cand)
            for cid in cand.class_set:
                current_class_scenes[cid] += 1
    return selected


def _write_selected_from_zip(
    zip_path: Path,
    selected: list[ZipSceneCandidate],
    out_img_dir: Path,
    out_lbl_dir: Path,
) -> tuple[int, Counter[int]]:
    written = 0
    box_counts: Counter[int] = Counter()
    with zipfile.ZipFile(zip_path, "r") as zf:
        for idx, cand in enumerate(selected):
            safe_scene = "".join(
                ch if (ch.isalnum() or ch in ("-", "_")) else "_"
                for ch in cand.scene_id[:48]
            ).strip("_") or f"s{idx:05d}"
            out_stem = f"{cand.source_prefix}_{idx:05d}_{safe_scene}"
            raw_bytes = zf.read(cand.img_member)

            # Ensure valid RGB JPEG (converts PNG if any, strips broken streams cleanly)
            try:
                with Image.open(io.BytesIO(raw_bytes)) as im:
                    rgb = ImageOps.exif_transpose(im).convert("RGB")
                    if min(rgb.size) < 64:
                        continue
                    rgb.save(out_img_dir / f"{out_stem}.jpg", format="JPEG", quality=90)
            except (UnidentifiedImageError, OSError):
                continue

            lbl_lines = [
                f"{cid} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}"
                for cid, xc, yc, bw, bh in cand.boxes
            ]
            (out_lbl_dir / f"{out_stem}.txt").write_text(
                "\n".join(lbl_lines) + "\n", encoding="utf-8"
            )
            written += 1
            for b in cand.boxes:
                box_counts[b[0]] += 1
    return written, box_counts


# THUẬT TOÁN: Tải Song song Ảnh & BBox Bông Cải Xanh từ Google Open Images v7 (`CC BY 4.0 / 2.0`)
# Cơ chế: Đọc CSV chú thích chính thức cho `/m/0hkxq` (`Broccoli`, lọc `IsGroupOf == 0`), tải song song
#         qua `ThreadPoolExecutor` từ bucket S3 công khai và chuyển tọa độ `[XMin, XMax, YMin, YMax]` -> YOLO.
# Độ phức tạp: Time O(N_broc / W_threads), Space O(N_broc).
def _ingest_openimages_broccoli(
    out_img_dir: Path,
    out_lbl_dir: Path,
    *,
    max_images: int = 80,
) -> tuple[int, int]:
    csv_sources = (
        ("validation", "https://storage.googleapis.com/openimages/v5/validation-annotations-bbox.csv"),
        ("test", "https://storage.googleapis.com/openimages/v5/test-annotations-bbox.csv"),
    )
    tasks: list[tuple[str, str, list[tuple[float, float, float, float]]]] = []

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for split_name, csv_url in csv_sources:
            if len(tasks) >= max_images:
                break
            resp = client.get(csv_url)
            if resp.status_code != 200:
                continue
            by_img: dict[str, list[tuple[float, float, float, float]]] = defaultdict(list)
            for row in csv.DictReader(io.StringIO(resp.text)):
                if row.get("LabelName") != "/m/0hkxq":
                    continue
                if row.get("IsGroupOf", "0") == "1" or row.get("IsDepiction", "0") == "1":
                    continue
                x1, x2 = float(row["XMin"]), float(row["XMax"])
                y1, y2 = float(row["YMin"]), float(row["YMax"])
                box = sanitize_yolo_bbox((x1 + x2) * 0.5, (y1 + y2) * 0.5, x2 - x1, y2 - y1)
                if box is not None and box[2] * box[3] >= 0.015:
                    by_img[row["ImageID"]].append(box)
            for img_id in sorted(by_img.keys()):
                tasks.append((split_name, img_id, by_img[img_id]))
                if len(tasks) >= max_images:
                    break

    def _download_one(
        item: tuple[str, str, list[tuple[float, float, float, float]]],
    ) -> int:
        split_name, img_id, boxes = item
        url = f"https://s3.amazonaws.com/open-images-dataset/{split_name}/{img_id}.jpg"
        try:
            with httpx.Client(timeout=15.0, follow_redirects=True) as c:
                r = c.get(url)
                if r.status_code != 200 or len(r.content) < 2048:
                    return 0
            with Image.open(io.BytesIO(r.content)) as im:
                rgb = ImageOps.exif_transpose(im).convert("RGB")
                if min(rgb.size) < 128:
                    return 0
                if max(rgb.size) > 640:
                    rgb.thumbnail((640, 640), Image.Resampling.BILINEAR)
                stem = f"oidv7_broc_{split_name}_{img_id}"
                rgb.save(out_img_dir / f"{stem}.jpg", format="JPEG", quality=90)
                lines = [f"9 {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}" for xc, yc, bw, bh in boxes]
                (out_lbl_dir / f"{stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
                return len(boxes)
        except (httpx.HTTPError, UnidentifiedImageError, OSError):
            return 0

    written_imgs = 0
    written_boxes = 0
    with ThreadPoolExecutor(max_workers=min(12, DEFAULT_IO_WORKERS)) as pool:
        for n_boxes in pool.map(_download_one, tasks):
            if n_boxes > 0:
                written_imgs += 1
                written_boxes += n_boxes
    return written_imgs, written_boxes


def run_supplement_ingestion(
    downloads_dir: Path = DEFAULT_DOWNLOADS_DIR,
    out_supplement_dir: Path = DEFAULT_SUPPLEMENT_DIR,
    attribution_json_path: Path = DEFAULT_ATTRIBUTION_JSON,
    *,
    include_openimages_broccoli: bool = True,
) -> dict[str, Any]:
    if out_supplement_dir.exists():
        shutil.rmtree(out_supplement_dir)
    out_img_dir = out_supplement_dir / "train" / "images"
    out_lbl_dir = out_supplement_dir / "train" / "labels"
    out_img_dir.mkdir(parents=True, exist_ok=True)
    out_lbl_dir.mkdir(parents=True, exist_ok=True)

    current_class_scenes: Counter[int] = Counter()
    total_boxes_by_class: Counter[int] = Counter()
    sources_meta: list[dict[str, Any]] = []

    zip_specs = [
        (
            downloads_dir / "food ingredients.v5i.yolov11.zip",
            "rf2alny",
            RF_FOOD_ING_V5_MAP,
            frozenset({14, 15, 11}),  # allow impure only for rarest shrimp/fish/tofu if needed
            {
                "name": "food ingredients (v5, 1x raw 640px)",
                "author": "My workspace (Roboflow Universe)",
                "license": "CC BY 4.0",
                "source_url": "https://universe.roboflow.com/my-workspace-idgwe/food-ingredients-2alny/dataset/5",
            },
        ),
        (
            downloads_dir / "Fish.v1i.yolov11.zip",
            "rffish",
            RF_FISH_V1_MAP,
            frozenset(),
            {
                "name": "Fish (v1, 1x raw whole market fish)",
                "author": "blxm (Roboflow Universe)",
                "license": "CC BY 4.0",
                "source_url": "https://universe.roboflow.com/blxm/fish-yjekd/dataset/1",
            },
        ),
        (
            downloads_dir / "Tofu.v1i.yolov11.zip",
            "rftofu",
            RF_TOFU_V1_MAP,
            frozenset(),
            {
                "name": "Tofu (v1)",
                "author": "SAGES (Roboflow Universe)",
                "license": "CC BY 4.0",
                "source_url": "https://universe.roboflow.com/sages/tofu-47uo2/dataset/1",
            },
        ),
    ]

    for zip_path, prefix, cmap, allow_impure, meta in zip_specs:
        if not zip_path.exists():
            continue
        cands = _scan_zip_candidates(
            zip_path, prefix, cmap, allow_impure_classes=allow_impure
        )
        selected = _select_balanced_candidates(
            cands, current_class_scenes, CLASS_SCENE_QUOTA, seed=42
        )
        written_imgs, b_cnt = _write_selected_from_zip(
            zip_path, selected, out_img_dir, out_lbl_dir
        )
        total_boxes_by_class.update(b_cnt)
        sources_meta.append(
            {
                **meta,
                "ingested_images": written_imgs,
                "ingested_boxes": int(sum(b_cnt.values())),
                "classes_contributed": {
                    CANONICAL_CLASSES[cid]: int(n) for cid, n in sorted(b_cnt.items())
                },
            }
        )

    if include_openimages_broccoli:
        oid_imgs, oid_boxes = _ingest_openimages_broccoli(
            out_img_dir, out_lbl_dir, max_images=CLASS_SCENE_QUOTA[9]
        )
        if oid_imgs > 0:
            total_boxes_by_class[9] += oid_boxes
            current_class_scenes[9] += oid_imgs
            sources_meta.append(
                {
                    "name": "Google Open Images Dataset v7 (Broccoli /m/0hkxq)",
                    "author": "Google / Flickr Contributors",
                    "license": "CC BY 4.0 / CC BY 2.0",
                    "source_url": "https://storage.googleapis.com/openimages/web/index.html",
                    "ingested_images": oid_imgs,
                    "ingested_boxes": oid_boxes,
                    "classes_contributed": {"broccoli": oid_boxes},
                }
            )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "supplement_dir": str(out_supplement_dir.relative_to(REPO_ROOT)).replace("\\", "/"),
        "adr_compliance": "ADR-005 (CC BY 4.0 / CC BY 2.0 verified open licenses only)",
        "total_ingested_images": sum(s["ingested_images"] for s in sources_meta),
        "total_ingested_boxes": int(sum(total_boxes_by_class.values())),
        "boxes_by_canonical_class": {
            f"{cid}:{CANONICAL_CLASSES[cid]}": int(total_boxes_by_class[cid])
            for cid in sorted(CANONICAL_CLASSES)
        },
        "sources": sources_meta,
    }
    attribution_json_path.parent.mkdir(parents=True, exist_ok=True)
    attribution_json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest verified CC-BY-4.0 dataset supplements.")
    parser.add_argument("--downloads-dir", type=Path, default=DEFAULT_DOWNLOADS_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_SUPPLEMENT_DIR)
    parser.add_argument("--skip-openimages", action="store_true")
    args = parser.parse_args()

    rep = run_supplement_ingestion(
        downloads_dir=args.downloads_dir,
        out_supplement_dir=args.out_dir,
        include_openimages_broccoli=not args.skip_openimages,
    )
    print(f"[INGEST] Total supplement images: {rep['total_ingested_images']}")
    print(f"[INGEST] Total supplement boxes:  {rep['total_ingested_boxes']}")
    for k, v in rep["boxes_by_canonical_class"].items():
        if v > 0:
            print(f"  {k:18s}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
