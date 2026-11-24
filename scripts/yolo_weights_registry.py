"""Weights SHA-256 computation, registry manifest builder, and seed synchronizer.

Provides streaming C-speed SHA-256 hashing (`hashlib.file_digest`), artifact manifest
generation (`backend/configs/yolo_model_artifact.json`), GPU checkpoint import
validation, and automatic synchronization of `SHA-256` digests into `supabase/seed.sql`
and `backend/app/core/seed_fixtures.py` for Card #20 (`c5rVF4w5`).
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_MANIFEST = REPO_ROOT / "backend" / "configs" / "dataset_ready_manifest.json"
DEFAULT_WEIGHTS_PATH = REPO_ROOT / "backend" / "weights" / "yolo" / "ingredients_best.pt"
LEGACY_WEIGHTS_PATH = REPO_ROOT / "backend" / "weights" / "ingredients_best.pt"
DEFAULT_ARTIFACT_MANIFEST = REPO_ROOT / "backend" / "configs" / "yolo_model_artifact.json"
SEED_FIXTURES_PATH = REPO_ROOT / "backend" / "app" / "core" / "seed_fixtures.py"
SEED_SQL_PATH = REPO_ROOT / "supabase" / "seed.sql"

CANONICAL_20_CLASSES: dict[int, dict[str, str]] = {
    0: {"class_name": "tomato", "slug": "ca-chua", "name_vi": "Cà chua", "ingredient_id": "11111111-1111-4111-8111-111111111101", "category": "vegetable"},
    1: {"class_name": "egg", "slug": "trung-ga", "name_vi": "Trứng gà", "ingredient_id": "11111111-1111-4111-8111-111111111102", "category": "protein"},
    2: {"class_name": "potato", "slug": "khoai-tay", "name_vi": "Khoai tây", "ingredient_id": "11111111-1111-4111-8111-111111111202", "category": "vegetable"},
    3: {"class_name": "carrot", "slug": "ca-rot", "name_vi": "Cà rốt", "ingredient_id": "11111111-1111-4111-8111-111111111203", "category": "vegetable"},
    4: {"class_name": "onion", "slug": "hanh-tay", "name_vi": "Hành tây", "ingredient_id": "11111111-1111-4111-8111-111111111204", "category": "vegetable"},
    5: {"class_name": "garlic", "slug": "toi", "name_vi": "Tỏi", "ingredient_id": "11111111-1111-4111-8111-111111111205", "category": "spice"},
    6: {"class_name": "chili_pepper", "slug": "ot", "name_vi": "Ớt", "ingredient_id": "11111111-1111-4111-8111-111111111206", "category": "spice"},
    7: {"class_name": "cucumber", "slug": "dua-leo", "name_vi": "Dưa leo", "ingredient_id": "11111111-1111-4111-8111-111111111207", "category": "vegetable"},
    8: {"class_name": "cabbage", "slug": "bap-cai", "name_vi": "Bắp cải", "ingredient_id": "11111111-1111-4111-8111-111111111208", "category": "vegetable"},
    9: {"class_name": "broccoli", "slug": "bong-cai-xanh", "name_vi": "Bông cải xanh", "ingredient_id": "11111111-1111-4111-8111-111111111209", "category": "vegetable"},
    10: {"class_name": "mushroom", "slug": "nam", "name_vi": "Nấm", "ingredient_id": "11111111-1111-4111-8111-111111111210", "category": "vegetable"},
    11: {"class_name": "tofu", "slug": "dau-hu", "name_vi": "Đậu hũ", "ingredient_id": "11111111-1111-4111-8111-111111111103", "category": "protein"},
    12: {"class_name": "raw_chicken", "slug": "thit-ga-song", "name_vi": "Thịt gà sống", "ingredient_id": "11111111-1111-4111-8111-111111111212", "category": "protein"},
    13: {"class_name": "raw_pork", "slug": "thit-heo-song", "name_vi": "Thịt heo sống", "ingredient_id": "11111111-1111-4111-8111-111111111213", "category": "protein"},
    14: {"class_name": "raw_shrimp", "slug": "tom", "name_vi": "Tôm tươi", "ingredient_id": "11111111-1111-4111-8111-111111111214", "category": "seafood"},
    15: {"class_name": "whole_fish", "slug": "ca-nguyen-con", "name_vi": "Cá nguyên con", "ingredient_id": "11111111-1111-4111-8111-111111111215", "category": "seafood"},
    16: {"class_name": "ginger", "slug": "gung", "name_vi": "Gừng", "ingredient_id": "11111111-1111-4111-8111-111111111216", "category": "spice"},
    17: {"class_name": "scallion", "slug": "hanh-la", "name_vi": "Hành lá", "ingredient_id": "11111111-1111-4111-8111-111111111105", "category": "spice"},
    18: {"class_name": "bell_pepper", "slug": "ot-chuong", "name_vi": "Ớt chuông", "ingredient_id": "11111111-1111-4111-8111-111111111218", "category": "vegetable"},
    19: {"class_name": "sweet_corn", "slug": "bap-ngot", "name_vi": "Bắp ngọt", "ingredient_id": "11111111-1111-4111-8111-111111111219", "category": "vegetable"},
}

_SEED_FIXTURE_SHA_RE = re.compile(r'(MODEL_YOLO_V1_SHA256\s*=\s*")[0-9a-f]{64}(")')
_SEED_SQL_SHA_RE = re.compile(r"(--\s*SHA-256\s*\(64 hex\):\s*)[0-9a-f]{64}")


# THUẬT TOÁN: Tính mã băm mật mã SHA-256 theo luồng C-level (hashlib.file_digest)
# giúp đọc tệp trọng số .pt lớn với bộ nhớ đệm O(1) mà không nạp toàn bộ byte vào RAM Python.
def compute_file_sha256(file_path: Path) -> tuple[str, int]:
    size_bytes = file_path.stat().st_size
    with open(file_path, "rb") as fh:
        digest = hashlib.file_digest(fh, "sha256").hexdigest()
    return digest, size_bytes


# THUẬT TOÁN: Đồng bộ nguyên tử mã băm SHA-256 (64 ký tự hex) của tệp trọng số mới
# vào cả seed_fixtures.py (Backend InMemory) và supabase/seed.sql (Database Seed).
def sync_weights_sha256_across_repo(weights_sha256: str) -> None:
    if len(weights_sha256) != 64:
        raise ValueError(f"Expected 64-char hex SHA-256, got: {weights_sha256}")

    if SEED_FIXTURES_PATH.exists():
        old_py = SEED_FIXTURES_PATH.read_text(encoding="utf-8")
        new_py = _SEED_FIXTURE_SHA_RE.sub(rf"\g<1>{weights_sha256}\g<2>", old_py)
        if new_py != old_py:
            SEED_FIXTURES_PATH.write_text(new_py, encoding="utf-8")

    if SEED_SQL_PATH.exists():
        old_sql = SEED_SQL_PATH.read_text(encoding="utf-8")
        new_sql = _SEED_SQL_SHA_RE.sub(rf"\g<1>{weights_sha256}", old_sql)
        if new_sql != old_sql:
            SEED_SQL_PATH.write_text(new_sql, encoding="utf-8")


def read_dataset_manifest_meta() -> tuple[str, int]:
    if not DEFAULT_DATASET_MANIFEST.exists():
        return "", 20
    ds_meta = json.loads(DEFAULT_DATASET_MANIFEST.read_text(encoding="utf-8"))
    sha = str(ds_meta.get("manifest_sha256", ""))
    locked_eval = int(ds_meta.get("locked_eval_class_count", ds_meta.get("locked_class_count", 20)))
    return sha, locked_eval


# THUẬT TOÁN: Xuất tệp đặc tả quản trị mô hình yolo_model_artifact.json chứa đầy đủ
# siêu dữ liệu huấn luyện, khóa lớp NFR-11, ánh xạ 20 nhãn chuẩn và mã băm SHA-256.
def write_yolo_artifact_manifest(
    *,
    weights_path: Path,
    artifact_manifest_path: Path,
    hyperparameters: dict[str, Any],
    training_metrics: dict[str, Any],
    training_backend: str,
    sync_repo_seeds: bool = True,
) -> dict[str, Any]:
    if weights_path.resolve() != LEGACY_WEIGHTS_PATH.resolve():
        LEGACY_WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(weights_path, LEGACY_WEIGHTS_PATH)

    weights_sha256, weights_size_bytes = compute_file_sha256(weights_path)
    dataset_sha256, locked_eval_k = read_dataset_manifest_meta()

    artifact_manifest: dict[str, Any] = {
        "model_id": "55555555-5555-4555-8555-555555555501",
        "version": "yolo11n-foodvision-v1.0",
        "family": str(hyperparameters.get("model_family", "yolo11n")),
        "training_backend": training_backend,
        "dataset_version": "food-ingredients-v1.0",
        "dataset_manifest_sha256": dataset_sha256,
        "locked_eval_class_count": locked_eval_k,
        "artifact_ref": "weights/yolo/ingredients_best.pt",
        "weights_sha256": weights_sha256,
        "weights_size_bytes": weights_size_bytes,
        "class_count": 20,
        "confidence_threshold": 0.25,
        "review_threshold": 0.80,
        "status": "active",
        "hyperparameters": hyperparameters,
        "pilot_metrics": training_metrics,
        "labels": [
            {
                "class_index": idx,
                "class_name": info["class_name"],
                "slug": info["slug"],
                "name_vi": info["name_vi"],
                "ingredient_id": info["ingredient_id"],
                "category": info["category"],
            }
            for idx, info in sorted(CANONICAL_20_CLASSES.items())
        ],
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }

    artifact_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_manifest_path.write_text(
        json.dumps(artifact_manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if sync_repo_seeds and weights_path.resolve() == DEFAULT_WEIGHTS_PATH.resolve():
        sync_weights_sha256_across_repo(weights_sha256)

    return artifact_manifest


# THUẬT TOÁN: Nhập khẩu và xác thực tệp trọng số Ultralytics YOLO (.pt) huấn luyện từ GPU
# (Google Colab / Kaggle T4), sao chép về kho trọng số chuẩn và tự động đồng bộ mã băm SHA-256.
def import_external_yolo_weights(
    source_pt_path: Path,
    *,
    weights_path: Path = DEFAULT_WEIGHTS_PATH,
    artifact_manifest_path: Path = DEFAULT_ARTIFACT_MANIFEST,
    hyperparameters: dict[str, Any] | None = None,
    sync_repo_seeds: bool = True,
) -> dict[str, Any]:
    if not source_pt_path.exists() or source_pt_path.stat().st_size <= 0:
        raise FileNotFoundError(f"Valid .pt weights file not found: {source_pt_path}")

    weights_path.parent.mkdir(parents=True, exist_ok=True)
    if source_pt_path.resolve() != weights_path.resolve():
        shutil.copyfile(source_pt_path, weights_path)

    inferred_family = "yolo11s" if (
        "11s" in source_pt_path.name.lower()
        or "_s640" in source_pt_path.name.lower()
        or source_pt_path.stat().st_size > 12_000_000
    ) else "yolo11n"
    hparams = hyperparameters or {
        "model_family": inferred_family,
        "imgsz": 640,
        "epochs": 55 if inferred_family == "yolo11s" else 100,
        "patience": 15 if inferred_family == "yolo11s" else 20,
        "mosaic": 0.7,
        "mixup": 0.05 if inferred_family == "yolo11s" else 0.1,
        "copy_paste": 0.15 if inferred_family == "yolo11s" else 0.0,
        "cos_lr": True if inferred_family == "yolo11s" else False,
        "confidence_threshold": 0.25,
        "review_threshold": 0.80,
        "nms_iou_threshold": 0.50,
    }
    return write_yolo_artifact_manifest(
        weights_path=weights_path,
        artifact_manifest_path=artifact_manifest_path,
        hyperparameters=hparams,
        training_metrics={"imported_from": source_pt_path.name},
        training_backend="ultralytics_gpu_imported",
        sync_repo_seeds=sync_repo_seeds,
    )
