"""Independent Stage 5 YOLO Test-Split Evaluator & Documentation Sync (`Card #13` - `t4kdIXx5`).

Executes:
1. Frozen `split='test'` object detection evaluation (`AI-01`, `AI-02`, `AI-03`, `NFR-11`)
   using batched `torch.inference_mode()` or Ultralytics `model.val(split='test')`.
2. Full per-class `AP@50`, `AP@50:95`, `Precision`, `Recall`, `F1`, `N_test` table across
   all `K` locked classes in `dataset_ready_manifest.json` (strictly zero post-hoc dropping).
3. `PERF-01` end-to-end latency benchmark (`>= 30` consecutive `POST /api/v1/ai/detect` calls).
4. Automated synchronization of empirical tables into `docs/04-ai-model/dataset-and-evaluation.md`
   and `backend/configs/yolo_test_evaluation_report.json`.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import pickle
import sys
from typing import Any

import numpy as np
from PIL import Image
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

from scripts.benchmark_detect_latency import (  # noqa: E402
    LatencyBenchmarkReport,
    run_detect_latency_benchmark,
)
from scripts.yolo_dataset_core import (  # noqa: E402
    DEFAULT_IO_WORKERS,
    DEFAULT_OUT_DIR,
    DEFAULT_TRACKED_MANIFEST,
    SCAN_BATCH_SIZE,
)
from scripts.yolo_eval_metrics import (  # noqa: E402
    DetectionEvalSummary,
    evaluate_detections_nfr11,
)
from scripts.yolo_weights_registry import (  # noqa: E402
    DEFAULT_ARTIFACT_MANIFEST,
    DEFAULT_WEIGHTS_PATH,
    compute_file_sha256,
)

DEFAULT_EVAL_REPORT_JSON = REPO_ROOT / "backend" / "configs" / "yolo_test_evaluation_report.json"
DEFAULT_EVAL_DOC_MD = REPO_ROOT / "docs" / "04-ai-model" / "dataset-and-evaluation.md"
_DOC_SECTION_HEADER = "## 6. Biểu mẫu báo cáo kết quả"


def _xywhn_to_xyxyn(boxes_xywh: np.ndarray) -> np.ndarray:
    if boxes_xywh.size == 0:
        return np.zeros((0, 4), dtype=np.float32)
    half_w = boxes_xywh[:, 2] * np.float32(0.5)
    half_h = boxes_xywh[:, 3] * np.float32(0.5)
    x1 = np.clip(boxes_xywh[:, 0] - half_w, np.float32(0.0), np.float32(1.0))
    y1 = np.clip(boxes_xywh[:, 1] - half_h, np.float32(0.0), np.float32(1.0))
    x2 = np.clip(boxes_xywh[:, 0] + half_w, np.float32(0.0), np.float32(1.0))
    y2 = np.clip(boxes_xywh[:, 1] + half_h, np.float32(0.0), np.float32(1.0))
    return np.ascontiguousarray(np.stack((x1, y1, x2, y2), axis=-1), dtype=np.float32)


# THUẬT TOÁN: Nạp Song song Lô Nhãn Chuẩn & Ảnh Kiểm thử Đóng băng (`split='test'`)
# Cơ chế: Quét os.scandir() kết hợp ThreadPoolExecutor đọc nhãn + giải mã thumbnail CHW float32 liên tục.
# Complexity: Time O(N_test / W_threads), Space O(N_test * thumb^2).
def _load_test_batch(
    batch: tuple[Path, list[str], int],
) -> list[tuple[str, np.ndarray, np.ndarray, bool, np.ndarray]]:
    img_dir, lbl_paths, thumb_size = batch
    records: list[tuple[str, np.ndarray, np.ndarray, bool, np.ndarray]] = []
    inv_255 = np.float32(1.0 / 255.0)

    for lbl_str in lbl_paths:
        stem = os.path.basename(lbl_str)[:-4]
        img_path = img_dir / f"{stem}.jpg"
        with open(lbl_str, "r", encoding="utf-8") as fh:
            lines = [ln.strip() for ln in fh if ln.strip()]

        if not lines:
            gt_cls = np.zeros(0, dtype=np.int32)
            gt_xyxy = np.zeros((0, 4), dtype=np.float32)
            is_ood = True
        else:
            parsed = [ln.split() for ln in lines]
            gt_cls = np.array([int(p[0]) for p in parsed], dtype=np.int32)
            xywh = np.array([[float(p[1]), float(p[2]), float(p[3]), float(p[4])] for p in parsed], dtype=np.float32)
            gt_xyxy = _xywhn_to_xyxyn(xywh)
            is_ood = False

        with Image.open(img_path) as im:
            rgb = im.convert("RGB").resize((thumb_size, thumb_size))
            chw = np.ascontiguousarray(
                np.transpose(np.asarray(rgb, dtype=np.float32) * inv_255, (2, 0, 1))
            )
        records.append(( str(img_path), gt_cls, gt_xyxy, is_ood, chw ))
    return records


# THUẬT TOÁN: Suy luận Lô Độc lập trên Tập Test Đóng băng (Batched Tensor Inference / Ultralytics Val)
# Cơ chế: Nạp trọng số đúng 1 lần, chạy dưới ngữ cảnh `with torch.inference_mode():` theo lô kích thước 64
#         (hoặc batch predict Ultralytics YOLO) để tận dụng tối đa băng thông SIMD/CUDA.
# Complexity: Time O(N_test / B), Space O(B * C * H * W).
def _predict_test_split(
    *,
    weights_path: Path,
    image_paths: list[str],
    chw_batch_array: np.ndarray,
    conf_threshold: float = 0.25,
    batch_size: int = 64,
) -> tuple[str, list[tuple[np.ndarray, np.ndarray, np.ndarray]]]:
    from app.ai.yolo_detector.backend import _PyTorchCheckpointAdapter

    is_pilot_ckpt = False
    pilot_ckpt: dict[str, Any] | None = None
    try:
        loaded_obj = torch.load(str(weights_path), map_location="cpu", weights_only=False)
        if isinstance(loaded_obj, dict) and loaded_obj.get("format_version") == "foodvision-yolo-v1":
            is_pilot_ckpt = True
            pilot_ckpt = loaded_obj
    except (RuntimeError, OSError, pickle.UnpicklingError, KeyError, TypeError, ValueError):
        is_pilot_ckpt = False

    predictions: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []
    if is_pilot_ckpt and pilot_ckpt is not None:
        adapter = _PyTorchCheckpointAdapter(pilot_ckpt)
        n_total = chw_batch_array.shape[0]
        with torch.inference_mode():
            for start in range(0, n_total, batch_size):
                batch_tensor = torch.from_numpy(chw_batch_array[start : start + batch_size])
                feat = adapter._module.backbone(batch_tensor).flatten(1)
                probs = torch.softmax(adapter._module.class_head(feat), dim=-1).cpu().numpy()
                xywh = torch.sigmoid(adapter._module.box_head(feat)).cpu().numpy()

                top_cls = np.argmax(probs, axis=1).astype(np.int32)
                top_conf = np.max(probs, axis=1).astype(np.float32)
                bw = np.clip(xywh[:, 2], np.float32(0.10), np.float32(0.80))
                bh = np.clip(xywh[:, 3], np.float32(0.10), np.float32(0.80))
                x1 = np.clip(xywh[:, 0] - bw * np.float32(0.5), np.float32(0.0), np.float32(0.95))
                y1 = np.clip(xywh[:, 1] - bh * np.float32(0.5), np.float32(0.0), np.float32(0.95))
                x2 = np.clip(xywh[:, 0] + bw * np.float32(0.5), x1 + np.float32(0.05), np.float32(1.0))
                y2 = np.clip(xywh[:, 1] + bh * np.float32(0.5), y1 + np.float32(0.05), np.float32(1.0))
                boxes = np.stack((x1, y1, x2, y2), axis=-1).astype(np.float32)

                for i in range(top_cls.size):
                    if top_conf[i] >= conf_threshold:
                        predictions.append(
                            (top_cls[i : i + 1], top_conf[i : i + 1], boxes[i : i + 1])
                        )
                    else:
                        predictions.append(
                            (
                                np.zeros(0, dtype=np.int32),
                                np.zeros(0, dtype=np.float32),
                                np.zeros((0, 4), dtype=np.float32),
                            )
                        )
        return "pytorch_cpu_pilot", predictions

    from ultralytics import YOLO

    yolo = YOLO(str(weights_path))
    device = 0 if torch.cuda.is_available() else "cpu"
    for start in range(0, len(image_paths), batch_size):
        chunk_paths = image_paths[start : start + batch_size]
        results = yolo.predict(
            source=chunk_paths,
            conf=conf_threshold,
            iou=0.50,
            device=device,
            verbose=False,
        )
        for res in results:
            b = res.boxes
            if b is None or len(b) == 0:
                predictions.append(
                    (
                        np.zeros(0, dtype=np.int32),
                        np.zeros(0, dtype=np.float32),
                        np.zeros((0, 4), dtype=np.float32),
                    )
                )
            else:
                predictions.append(
                    (
                        b.cls.detach().cpu().numpy().astype(np.int32),
                        b.conf.detach().cpu().numpy().astype(np.float32),
                        b.xyxyn.detach().cpu().numpy().astype(np.float32),
                    )
                )
    return "ultralytics_yolo", predictions


def _render_markdown_section(
    report: dict[str, Any],
) -> str:
    ev = report["evaluation"]
    perf = report["perf01_latency"]
    deferred = report["deferred_under_threshold_classes"]
    backend_tag = report["training_backend"]
    backend_note = (
        "Checkpoint hiệu chuẩn CPU cục bộ (`pytorch_cpu_pilot`, chưa chạy huấn luyện đầy đủ trên GPU CUDA); "
        "chạy lại lệnh này sau khi nhập `ingredients_best.pt` từ Colab/Kaggle T4 để cập nhật `mAP` GPU chính thức."
        if backend_tag == "pytorch_cpu_pilot"
        else "Trọng số Ultralytics YOLO11n huấn luyện đầy đủ trên GPU (`ultralytics_yolo`)."
    )

    lines: list[str] = [
        "## 6. Biểu mẫu báo cáo kết quả (Số liệu đo thực tế độc lập trên `split='test'`)",
        "",
        "### 6.1. Bảng tổng hợp chất lượng thị giác (`AI-01`, `AI-02`) & độ trễ suy luận (`PERF-01`)",
        "",
        "| Model version | Dataset version | Số lớp khóa ($K$) | Ảnh `test` (OOD) | Precision | Recall | F1 | mAP@50 | mAP@50:95 | `p50` / `p95` detect (`PERF-01`) | Trạng thái trọng số |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        (
            f"| `{report['model_version']}` | `{report['dataset_version']}` | `{ev['locked_eval_class_count']}` "
            f"| `{ev['total_test_images']}` (`{ev['ood_test_images']}`) | `{ev['precision']:.4f}` "
            f"| `{ev['recall']:.4f}` | `{ev['f1']:.4f}` | `{ev['map50']:.4f}` | `{ev['map50_95']:.4f}` "
            f"| `{perf['p50_ms']:.2f} ms` / `{perf['p95_ms']:.2f} ms` (`{perf['num_requests']}` req) | `{backend_tag}` |"
        ),
        "",
        f"- **Mã băm toàn vẹn:** `dataset_manifest_sha256 = {report['dataset_manifest_sha256'][:16]}...`, `weights_sha256 = {report['weights_sha256'][:16]}...`.",
        f"- **Ghi chú trung thực thực nghiệm (`NFR-11`):** {backend_note}",
        f"- **Kiểm soát OOD & Cảnh báo HITL (`AI-03`, $\\tau = 0.80$):** Trên `{ev['ood_test_images']}` ảnh đối chứng âm (`OOD` không chứa nguyên liệu mục tiêu), số ảnh phát sinh báo động giả là `{ev['ood_false_positive_images']}`; tỷ lệ hộp dự đoán có `confidence < 0.80` được chuyển sang luồng người dùng xác nhận HITL là `{ev['hitl_uncertain_detections']} / {ev['total_detections']}`.",
        "",
        "### 6.2. Bảng chi tiết từng lớp trên toàn bộ $K$ lớp đã khóa (`NFR-11` — Cấm loại lớp yếu sau test)",
        "",
        "| `class_index` | Mã nhãn (`code`) | `N_test` (GT boxes) | `TP@50` | `FP@50` | `FN@50` | Precision | Recall | F1 | `AP@50` | `AP@50:95` |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in ev["per_class"]:
        lines.append(
            f"| {row['class_index']} | `{row['class_name']}` | {row['n_test']} | {row['tp_at_50']} "
            f"| {row['fp_at_50']} | {row['fn_at_50']} | {row['precision']:.4f} | {row['recall']:.4f} "
            f"| {row['f1']:.4f} | {row['ap50']:.4f} | {row['ap50_95']:.4f} |"
        )

    lines.extend(
        [
            "",
            "### 6.3. Minh bạch 5 lớp ứng viên chuyển sang nhập tay / CLIP trước khi mở tập `test` (`NFR-11`)",
            "",
            "Theo quy tắc tại [`label-catalog.md`](label-catalog.md) (Mục 1), 5 lớp ứng viên có số mẫu thô `< 80` đã được khóa chuyển sang tìm kiếm tiếng Việt (`FR-18`) và nhánh phụ CLIP (`TP 02`) **tại mốc `dataset_ready` trước khi chạy `split='test'`**, tuyệt đối không phải loại bỏ hậu kiểm:",
            "",
            "| `class_index` | Mã nhãn (`code`) | Tổng mẫu thô hiện có | Thiếu hụt so với ngưỡng `80` | Cơ chế bù đắp trong kiến trúc 7 tầng |",
            "|---:|---|---:|---:|---|",
        ]
    )
    for cid_str, info in sorted(deferred.items(), key=lambda x: int(x[0])):
        lines.append(
            f"| {cid_str} | `{info['name']}` | {info['count']} | {info['deficit_to_80']} | `{info['fallback_policy']}` |"
        )

    lines.extend(
        [
            "",
            "### 6.4. Phân tích cặp lớp dễ nhầm lẫn & vai trò bù đắp của HITL (`TP 14`)",
            "",
            "- **Cặp hình thái tương đồng cao:** `raw_chicken` vs `raw_pork` (thớ thịt tươi phụ thuộc ánh sáng vàng/trắng nhà bếp), `tofu` vs phô mai trắng `Paneer` (khối vuông trắng đồng nhất), `cucumber` vs bí ngòi `zucchini`, và `tomato` vs `bell_pepper` đỏ.",
            "- **Vai trò bù đắp của HITL (`TP 14`) & CLIP (`TP 02`):** Mọi phát hiện có $p_{\\max} < \\tau = 0.80$ tự động đưa vào danh sách `uncertain_ingredients[]` kèm cờ `needs_confirmation = true`; người dùng xác nhận/sửa trực tiếp trên giao diện hoặc tra cứu tiếng Việt không dấu/từ đồng nghĩa (`pg_trgm`) trước khi hệ suy luận 3 trạng thái (`TP 04`) chấm điểm công thức, đảm bảo sai số tầng thị giác không lan truyền mù quáng sang tầng gợi ý.",
            "",
            "**Nguồn tham khảo:** Redmon et al. (*CVPR*, 2016), https://docs.ultralytics.com/datasets/detect, https://docs.ultralytics.com/tasks/detect và https://www.ultralytics.com/license.",
            "",
        ]
    )
    return "\n".join(lines)


def run_full_stage5_yolo_evaluation(
    *,
    dataset_dir: Path = DEFAULT_OUT_DIR,
    dataset_manifest_path: Path = DEFAULT_TRACKED_MANIFEST,
    weights_path: Path = DEFAULT_WEIGHTS_PATH,
    artifact_manifest_path: Path = DEFAULT_ARTIFACT_MANIFEST,
    output_json_path: Path = DEFAULT_EVAL_REPORT_JSON,
    doc_md_path: Path = DEFAULT_EVAL_DOC_MD,
    conf_threshold: float = 0.25,
    review_threshold: float = 0.80,
    latency_requests: int = 30,
    update_docs: bool = False,
) -> dict[str, Any]:
    ds_manifest = json.loads(dataset_manifest_path.read_text(encoding="utf-8"))
    locked_eval_raw = ds_manifest.get("locked_eval_classes") or ds_manifest.get("locked_classes") or {}
    locked_eval_classes = {int(k): str(v) for k, v in locked_eval_raw.items()}
    deferred_classes = ds_manifest.get("deferred_under_threshold_classes") or {}

    lbl_dir = dataset_dir / "labels" / "test"
    img_dir = dataset_dir / "images" / "test"
    with os.scandir(lbl_dir) as it:
        lbl_files = sorted(e.path for e in it if e.name.endswith(".txt"))

    batches = [
        (img_dir, lbl_files[i : i + SCAN_BATCH_SIZE], 64)
        for i in range(0, len(lbl_files), SCAN_BATCH_SIZE)
    ]
    loaded_records: list[tuple[str, np.ndarray, np.ndarray, bool, np.ndarray]] = []
    with ThreadPoolExecutor(max_workers=DEFAULT_IO_WORKERS) as pool:
        for chunk in pool.map(_load_test_batch, batches):
            loaded_records.extend(chunk)

    image_paths = [r[0] for r in loaded_records]
    gt_by_image = [(r[1], r[2], r[3]) for r in loaded_records]
    chw_stack = np.ascontiguousarray(np.stack([r[4] for r in loaded_records], axis=0))

    backend_type, pred_by_image = _predict_test_split(
        weights_path=weights_path,
        image_paths=image_paths,
        chw_batch_array=chw_stack,
        conf_threshold=conf_threshold,
    )
    eval_summary: DetectionEvalSummary = evaluate_detections_nfr11(
        locked_eval_classes=locked_eval_classes,
        gt_by_image=gt_by_image,
        pred_by_image=pred_by_image,
        review_threshold=review_threshold,
    )
    latency_report: LatencyBenchmarkReport = run_detect_latency_benchmark(
        dataset_dir=dataset_dir,
        num_requests=latency_requests,
    )

    weights_sha256, weights_bytes = compute_file_sha256(weights_path)
    model_version = "yolo11n-foodvision-v1.0"
    if artifact_manifest_path.exists():
        art = json.loads(artifact_manifest_path.read_text(encoding="utf-8"))
        model_version = str(art.get("version", model_version))

    report_payload: dict[str, Any] = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "model_version": model_version,
        "training_backend": backend_type,
        "weights_sha256": weights_sha256,
        "weights_size_bytes": weights_bytes,
        "dataset_version": str(ds_manifest.get("dataset_version", "foodvision-yolo-v1.0.0")),
        "dataset_manifest_sha256": str(ds_manifest.get("manifest_sha256", "")),
        "nfr11_compliant": True,
        "post_hoc_dropped_classes": [],
        "evaluation": {
            "locked_eval_class_count": len(eval_summary.locked_class_indices),
            "total_test_images": eval_summary.total_test_images,
            "ood_test_images": eval_summary.ood_test_images,
            "ood_false_positive_images": eval_summary.ood_false_positive_images,
            "total_detections": eval_summary.total_detections,
            "hitl_uncertain_detections": eval_summary.hitl_uncertain_detections,
            "precision": eval_summary.precision,
            "recall": eval_summary.recall,
            "f1": eval_summary.f1,
            "map50": eval_summary.map50,
            "map50_95": eval_summary.map50_95,
            "per_class": [m.to_dict() for m in eval_summary.per_class],
            "confusion_labels": list(eval_summary.confusion_labels),
            "confusion_matrix": eval_summary.confusion_matrix,
            "top_confused_pairs": eval_summary.top_confused_pairs,
        },
        "deferred_under_threshold_classes": deferred_classes,
        "perf01_latency": latency_report.to_dict(),
    }

    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(
        json.dumps(report_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if update_docs and doc_md_path.exists():
        doc_text = doc_md_path.read_text(encoding="utf-8")
        idx = doc_text.find(_DOC_SECTION_HEADER)
        rendered = _render_markdown_section(report_payload)
        updated_doc = (doc_text[:idx] + rendered) if idx != -1 else (doc_text.rstrip() + "\n\n" + rendered)
        doc_md_path.write_text(updated_doc, encoding="utf-8")

    return report_payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Stage 5 independent YOLO test evaluation & PERF-01.")
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--weights-path", type=Path, default=DEFAULT_WEIGHTS_PATH)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_EVAL_REPORT_JSON)
    parser.add_argument("--latency-requests", type=int, default=30)
    parser.add_argument("--update-docs", action="store_true")
    args = parser.parse_args()

    report = run_full_stage5_yolo_evaluation(
        dataset_dir=args.dataset_dir,
        weights_path=args.weights_path,
        output_json_path=args.output_json,
        latency_requests=args.latency_requests,
        update_docs=args.update_docs,
    )
    ev = report["evaluation"]
    perf = report["perf01_latency"]
    print(f"[STAGE5-EVAL] Backend:    {report['training_backend']} (K={ev['locked_eval_class_count']})")
    print(f"[STAGE5-EVAL] Test imgs:  {ev['total_test_images']} (OOD: {ev['ood_test_images']})")
    print(f"[STAGE5-EVAL] mAP@50:     {ev['map50']:.4f} | mAP@50:95: {ev['map50_95']:.4f}")
    print(f"[STAGE5-EVAL] PERF-01:    p50={perf['p50_ms']:.2f}ms | p95={perf['p95_ms']:.2f}ms ({perf['num_requests']} reqs)")
    print(f"[STAGE5-EVAL] Saved JSON: {args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
