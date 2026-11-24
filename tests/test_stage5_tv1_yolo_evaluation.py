"""Stage 5 Automated Verification Suite for TV1 (Minh Thanh - Card #13 t4kdIXx5).

Verifies all 4 checklist items of Card #13 (`[GD5 - TP12a]`):
1. Independent `split='test'` evaluation (`AI-01`, `AI-02`) with vectorized COCO metrics.
2. Aggregate `Precision`, `Recall`, `F1`, `mAP@50`, `mAP@50:95` & `(K+1) x (K+1)` Confusion Matrix.
3. Full per-class `AP@50`, `Recall`, `N_test` across all `K` locked `dataset_ready` classes
   with strict `NFR-11` zero post-hoc class dropping and `AI-03` HITL uncertainty tracking.
4. `PERF-01` `>= 30` consecutive `POST /api/v1/ai/detect` `p50`/`p95` latency benchmark and
   synchronization into `docs/04-ai-model/dataset-and-evaluation.md`.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

from scripts.benchmark_detect_latency import run_detect_latency_benchmark  # noqa: E402
from scripts.evaluate_yolo_test import (  # noqa: E402
    DEFAULT_EVAL_DOC_MD,
    DEFAULT_EVAL_REPORT_JSON,
)
from scripts.yolo_dataset_core import DEFAULT_OUT_DIR, DEFAULT_TRACKED_MANIFEST  # noqa: E402
from scripts.yolo_eval_metrics import (  # noqa: E402
    compute_ap_101pt_vec,
    compute_iou_matrix_vec,
    evaluate_detections_nfr11,
)


# THUẬT TOÁN: Kiểm chứng Ma trận IoU Vector hóa (`MATH-01`) & Nội suy 101 Điểm COCO AP
# Cơ chế: Đối chiếu giá trị giải tích chính xác 64/136 và đường cong Precision-Recall đơn điệu.
# Complexity: Time O(1), Space O(1).
def test_vectorized_iou_matrix_and_coco_101pt_ap_math() -> None:
    pred = np.array([[0.10, 0.10, 0.20, 0.20], [0.50, 0.50, 0.70, 0.70]], dtype=np.float32)
    gt = np.array([[0.12, 0.12, 0.22, 0.22], [0.50, 0.50, 0.70, 0.70]], dtype=np.float32)

    iou_mat = compute_iou_matrix_vec(pred, gt)
    assert iou_mat.shape == (2, 2)
    assert float(iou_mat[0, 0]) == pytest.approx(64.0 / 136.0, abs=1e-6)
    assert float(iou_mat[1, 1]) == pytest.approx(1.0, abs=1e-6)
    assert float(iou_mat[0, 1]) == 0.0

    ap_perfect = compute_ap_101pt_vec(
        np.array([1.0, 1.0], dtype=np.float32),
        np.array([0.95, 0.85], dtype=np.float32),
        n_gt=2,
    )
    assert ap_perfect == pytest.approx(1.0, abs=1e-6)

    ap_zero = compute_ap_101pt_vec(
        np.zeros(0, dtype=np.float32),
        np.zeros(0, dtype=np.float32),
        n_gt=3,
    )
    assert ap_zero == 0.0


# THUẬT TOÁN: Kiểm chứng Bất biến Minh bạch NFR-11 (Cấm Loại bỏ Lớp Yếu Hậu Kiểm) & Ma trận Nhầm lẫn
# Cơ chế: Giả lập 3 lớp khóa (lớp 9 có AP=0.0), xác minh mẫu số mAP cố định K=3 và đếm đúng FP/FN/HITL.
# Complexity: Time O(1), Space O(1).
def test_nfr11_forbids_dropping_weak_classes_and_builds_confusion_matrix() -> None:
    locked = {0: "tomato", 1: "egg", 9: "broccoli"}

    # Image 1: GT has tomato(0) + broccoli(9); Pred detects tomato(0, conf=0.91) perfectly, misses broccoli
    gt_1 = (
        np.array([0, 9], dtype=np.int32),
        np.array([[0.1, 0.1, 0.4, 0.4], [0.5, 0.5, 0.8, 0.8]], dtype=np.float32),
        False,
    )
    pr_1 = (
        np.array([0], dtype=np.int32),
        np.array([0.91], dtype=np.float32),
        np.array([[0.1, 0.1, 0.4, 0.4]], dtype=np.float32),
    )

    # Image 2: GT has egg(1) + tomato(0); Pred detects egg(1, conf=0.88) and misclassifies tomato box as egg(1, conf=0.62 < 0.80 HITL)
    gt_2 = (
        np.array([1, 0], dtype=np.int32),
        np.array([[0.1, 0.1, 0.3, 0.3], [0.6, 0.6, 0.9, 0.9]], dtype=np.float32),
        False,
    )
    pr_2 = (
        np.array([1, 1], dtype=np.int32),
        np.array([0.88, 0.62], dtype=np.float32),
        np.array([[0.1, 0.1, 0.3, 0.3], [0.6, 0.6, 0.9, 0.9]], dtype=np.float32),
    )

    # Image 3: Pure OOD hard negative; Pred emits 1 uncertain FP tomato(0, conf=0.55 < 0.80 HITL)
    gt_3 = (np.zeros(0, dtype=np.int32), np.zeros((0, 4), dtype=np.float32), True)
    pr_3 = (
        np.array([0], dtype=np.int32),
        np.array([0.55], dtype=np.float32),
        np.array([[0.2, 0.2, 0.5, 0.5]], dtype=np.float32),
    )

    summary = evaluate_detections_nfr11(
        locked_eval_classes=locked,
        gt_by_image=[gt_1, gt_2, gt_3],
        pred_by_image=[pr_1, pr_2, pr_3],
        review_threshold=0.80,
    )

    assert len(summary.per_class) == 3
    by_cid = {m.class_index: m for m in summary.per_class}
    assert by_cid[9].n_test_gt == 1
    assert by_cid[9].ap50 == 0.0
    assert by_cid[9].fn_at_50 == 1

    # NFR-11: mean mAP@50 MUST average across all K=3 classes (including broccoli=0.0)
    expected_map50 = round(
        (by_cid[0].ap50 + by_cid[1].ap50 + by_cid[9].ap50) / 3.0, 4
    )
    assert summary.map50 == pytest.approx(expected_map50, abs=1e-4)

    # OOD & HITL checks (AI-02, AI-03)
    assert summary.ood_test_images == 1
    assert summary.ood_false_positive_images == 1
    assert summary.total_detections == 4
    assert summary.hitl_uncertain_detections == 2  # conf 0.62 and 0.55 < 0.80

    # Confusion Matrix shape is (K+1) x (K+1) = 4 x 4; tomato->egg confusion recorded
    assert len(summary.confusion_matrix) == 4
    assert summary.confusion_matrix[0][1] == 1  # GT tomato (pos 0) predicted as egg (pos 1)
    assert summary.top_confused_pairs[0] == {
        "gt_class": "tomato",
        "pred_class": "egg",
        "count": 1,
    }


def test_perf01_30_consecutive_detect_requests_meet_latency_sla() -> None:
    with pytest.raises(ValueError, match="at least 30"):
        run_detect_latency_benchmark(dataset_dir=DEFAULT_OUT_DIR, num_requests=10)

    bench = run_detect_latency_benchmark(
        dataset_dir=DEFAULT_OUT_DIR,
        num_requests=30,
        warmup_requests=2,
    )
    assert bench.num_requests == 30
    assert 0.0 < bench.p50_ms <= bench.p95_ms <= bench.max_ms
    assert bench.passes_cpu_target is True
    assert bench.p95_ms <= 10_000.0


def test_tracked_yolo_evaluation_report_and_dataset_evaluation_docs_synced() -> None:
    assert DEFAULT_EVAL_REPORT_JSON.exists()
    assert DEFAULT_EVAL_DOC_MD.exists()

    ds_manifest = json.loads(DEFAULT_TRACKED_MANIFEST.read_text(encoding="utf-8"))
    expected_locked = ds_manifest["locked_eval_classes"]
    expected_deferred = ds_manifest["deferred_under_threshold_classes"]

    report = json.loads(DEFAULT_EVAL_REPORT_JSON.read_text(encoding="utf-8"))
    assert report["nfr11_compliant"] is True
    assert report["post_hoc_dropped_classes"] == []
    assert report["dataset_manifest_sha256"] == ds_manifest["manifest_sha256"]

    ev = report["evaluation"]
    assert ev["locked_eval_class_count"] == len(expected_locked) == 20
    assert len(ev["per_class"]) == len(expected_locked)
    assert len(ev["confusion_matrix"]) == len(expected_locked) + 1  # K locked + 1 background

    perf = report["perf01_latency"]
    assert perf["num_requests"] >= 30
    assert perf["passes_cpu_target"] is True

    doc_text = DEFAULT_EVAL_DOC_MD.read_text(encoding="utf-8")
    assert "_Chưa thực nghiệm_" not in doc_text
    for cls_name in expected_locked.values():
        assert f"`{cls_name}`" in doc_text
    for def_info in expected_deferred.values():
        assert f"`{def_info['name']}`" in doc_text
