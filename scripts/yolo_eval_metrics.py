"""Vectorized COCO/VOC object detection evaluation metrics and NFR-11 auditor.

Computes pairwise IoU matrices, 10-threshold COCO Average Precision (`mAP@50`,
`mAP@50:95` via 101-point interpolation), Precision/Recall/F1, and `(K+1) x (K+1)`
Confusion Matrix entirely in contiguous C/SIMD `NumPy` (`float32`/`int32`) arrays.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

IOU_THRESHOLDS_COCO: np.ndarray = np.linspace(0.50, 0.95, 10, dtype=np.float32)
RECALL_GRID_101: np.ndarray = np.linspace(0.0, 1.0, 101, dtype=np.float32)


@dataclass(slots=True, frozen=True)
class ClassEvalMetrics:
    """Immutable per-class evaluation summary locked under NFR-11."""

    class_index: int
    class_name: str
    n_test_gt: int
    n_predictions: int
    tp_at_50: int
    fp_at_50: int
    fn_at_50: int
    precision: float
    recall: float
    f1: float
    ap50: float
    ap50_95: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "class_index": self.class_index,
            "class_name": self.class_name,
            "n_test": self.n_test_gt,
            "n_predictions": self.n_predictions,
            "tp_at_50": self.tp_at_50,
            "fp_at_50": self.fp_at_50,
            "fn_at_50": self.fn_at_50,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "ap50": self.ap50,
            "ap50_95": self.ap50_95,
        }


@dataclass(slots=True, frozen=True)
class DetectionEvalSummary:
    """Aggregated independent test-split evaluation report (`AI-01`, `AI-02`, `NFR-11`)."""

    locked_class_indices: tuple[int, ...]
    locked_class_names: tuple[str, ...]
    total_test_images: int
    ood_test_images: int
    ood_false_positive_images: int
    hitl_uncertain_detections: int
    total_detections: int
    precision: float
    recall: float
    f1: float
    map50: float
    map50_95: float
    per_class: tuple[ClassEvalMetrics, ...]
    confusion_matrix: list[list[int]]
    confusion_labels: tuple[str, ...]
    top_confused_pairs: list[dict[str, Any]]


# THUẬT TOÁN: Ma trận IoU Vector hóa Toàn phần (Vectorized Pairwise Box IoU)
# Cơ chế: Broadcasting NumPy (P, 1, 4) x (1, G, 4) trên vùng nhớ liên tục float32.
# Complexity: Time O(P * G) tại tầng C/SIMD, Space O(P * G).
def compute_iou_matrix_vec(pred_xyxy: np.ndarray, gt_xyxy: np.ndarray) -> np.ndarray:
    """Compute `(P, G)` IoU matrix between predicted and ground-truth `xyxy` boxes."""
    if pred_xyxy.size == 0 or gt_xyxy.size == 0:
        return np.zeros((pred_xyxy.shape[0], gt_xyxy.shape[0]), dtype=np.float32)

    p = np.ascontiguousarray(pred_xyxy, dtype=np.float32)
    g = np.ascontiguousarray(gt_xyxy, dtype=np.float32)

    inter_x1 = np.maximum(p[:, None, 0], g[None, :, 0])
    inter_y1 = np.maximum(p[:, None, 1], g[None, :, 1])
    inter_x2 = np.minimum(p[:, None, 2], g[None, :, 2])
    inter_y2 = np.minimum(p[:, None, 3], g[None, :, 3])

    inter_w = np.maximum(np.float32(0.0), inter_x2 - inter_x1)
    inter_h = np.maximum(np.float32(0.0), inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area_p = np.maximum(np.float32(0.0), p[:, 2] - p[:, 0]) * np.maximum(
        np.float32(0.0), p[:, 3] - p[:, 1]
    )
    area_g = np.maximum(np.float32(0.0), g[:, 2] - g[:, 0]) * np.maximum(
        np.float32(0.0), g[:, 3] - g[:, 1]
    )
    union = area_p[:, None] + area_g[None, :] - inter_area
    return np.where(union > np.float32(0.0), inter_area / union, np.float32(0.0))


# THUẬT TOÁN: Nội suy 101 Điểm COCO Average Precision (101-Point Interpolated AP)
# Cơ chế: Tích lũy bao lồi đơn điệu giảm trên đường cong Precision-Recall bằng np.maximum.accumulate
#         và tra cứu nhị phân np.searchsorted trên lưới 101 mốc Recall [0.00..1.00].
# Complexity: Time O(P log P), Space O(P).
def compute_ap_101pt_vec(tp_flags: np.ndarray, confidences: np.ndarray, n_gt: int) -> float:
    """Compute COCO 101-point interpolated Average Precision for a single class & IoU threshold."""
    if n_gt <= 0 or tp_flags.size == 0:
        return 0.0

    order = np.argsort(-confidences, kind="mergesort")
    tp_sorted = tp_flags[order].astype(np.float32)
    fp_sorted = np.float32(1.0) - tp_sorted

    tp_cum = np.cumsum(tp_sorted, dtype=np.float32)
    fp_cum = np.cumsum(fp_sorted, dtype=np.float32)

    recall = tp_cum / np.float32(n_gt)
    precision = tp_cum / np.maximum(tp_cum + fp_cum, np.float32(1e-9))

    mrec = np.concatenate(([np.float32(0.0)], recall, [np.float32(1.0)]))
    mpre = np.concatenate(([np.float32(1.0)], precision, [np.float32(0.0)]))
    mpre = np.flip(np.maximum.accumulate(np.flip(mpre)))

    idx = np.searchsorted(mrec, RECALL_GRID_101, side="left")
    interp = np.where(idx < mpre.size, mpre[np.minimum(idx, mpre.size - 1)], np.float32(0.0))
    return float(np.mean(interp))


# THUẬT TOÁN: Ghép cặp Dự đoán - Nhãn chuẩn Đa Ngưỡng IoU & Ma trận Nhầm lẫn (COCO Matching + Confusion Matrix)
# Cơ chế:
# - Với mỗi ảnh kiểm thử, tính 1 lần duy nhất ma trận IoU (P, G) cho toàn bộ hộp trong ảnh.
# - Ánh xạ ghép cặp một-một tham lam theo độ tự tin giảm dần cho đồng thời 10 ngưỡng IoU [0.50..0.95] (cùng lớp)
#   và dựng ma trận nhầm lẫn (K+1) x (K+1) tại ngưỡng IoU = 0.50 (hàng = GT, cột = Pred, chỉ số K = background).
# - Tuân thủ NFR-11: giữ cố định toàn bộ K lớp trong locked_eval_classes làm mẫu số tính mAP.
# Complexity: Time O(sum_img P_img * G_img + P_total log P_total), Space O(P_total * 10 + K^2).
def evaluate_detections_nfr11(
    *,
    locked_eval_classes: dict[int, str],
    gt_by_image: list[tuple[np.ndarray, np.ndarray, bool]],
    pred_by_image: list[tuple[np.ndarray, np.ndarray, np.ndarray]],
    confusion_iou_threshold: float = 0.50,
    review_threshold: float = 0.80,
    op_conf_threshold: float = 0.0,
) -> DetectionEvalSummary:
    """Evaluate predictions over frozen test split without post-hoc class dropping (`NFR-11`)."""
    if not locked_eval_classes:
        raise ValueError("locked_eval_classes must be non-empty under NFR-11")
    if len(gt_by_image) != len(pred_by_image):
        raise ValueError("gt_by_image and pred_by_image lengths must match")

    sorted_locked_ids = tuple(sorted(locked_eval_classes.keys()))
    locked_names = tuple(locked_eval_classes[cid] for cid in sorted_locked_ids)
    k_count = len(sorted_locked_ids)
    cid_to_pos = {cid: pos for pos, cid in enumerate(sorted_locked_ids)}
    bg_pos = k_count

    conf_mat = np.zeros((k_count + 1, k_count + 1), dtype=np.int32)
    gt_counts_per_cid: dict[int, int] = {cid: 0 for cid in sorted_locked_ids}
    pred_tp_records: dict[int, list[np.ndarray]] = {cid: [] for cid in sorted_locked_ids}
    pred_conf_records: dict[int, list[np.ndarray]] = {cid: [] for cid in sorted_locked_ids}

    total_images = len(gt_by_image)
    ood_images = 0
    ood_fp_images = 0
    total_preds = 0
    uncertain_preds = 0
    n_thr = IOU_THRESHOLDS_COCO.size

    for (gt_cls, gt_boxes, is_ood), (pr_cls, pr_conf, pr_boxes) in zip(
        gt_by_image, pred_by_image, strict=True
    ):
        if is_ood:
            ood_images += 1

        # Filter to locked evaluation classes so deferred <80 manual-fallback classes never distort K
        gt_mask = np.isin(gt_cls, sorted_locked_ids) if gt_cls.size > 0 else np.zeros(0, dtype=bool)
        g_cls = gt_cls[gt_mask]
        g_box = gt_boxes[gt_mask]

        pr_mask = np.isin(pr_cls, sorted_locked_ids) if pr_cls.size > 0 else np.zeros(0, dtype=bool)
        p_cls = pr_cls[pr_mask]
        p_conf = pr_conf[pr_mask]
        p_box = pr_boxes[pr_mask]

        op_thr = np.float32(op_conf_threshold)
        if p_conf.size > 0:
            order = np.argsort(-p_conf, kind="mergesort")
            p_cls = p_cls[order]
            p_conf = p_conf[order]
            p_box = p_box[order]
            op_sel = p_conf >= op_thr
            op_conf = p_conf[op_sel]
            if is_ood and op_conf.size > 0:
                ood_fp_images += 1
            total_preds += int(op_conf.size)
            uncertain_preds += int(np.count_nonzero(op_conf < np.float32(review_threshold)))
        else:
            op_sel = np.zeros(0, dtype=bool)

        for cid in g_cls.tolist():
            gt_counts_per_cid[int(cid)] += 1

        if p_cls.size == 0 and g_cls.size == 0:
            continue
        if p_cls.size == 0:
            for cid in g_cls.tolist():
                conf_mat[cid_to_pos[int(cid)], bg_pos] += 1
            continue
        if g_cls.size == 0:
            for cid in p_cls[op_sel].tolist():
                conf_mat[bg_pos, cid_to_pos[int(cid)]] += 1
            for cid in sorted_locked_ids:
                c_sel = p_cls == cid
                if np.any(c_sel):
                    pred_tp_records[cid].append(
                        np.zeros((int(np.count_nonzero(c_sel)), n_thr), dtype=np.float32)
                    )
                    pred_conf_records[cid].append(p_conf[c_sel])
            continue

        iou_mat = compute_iou_matrix_vec(p_box, g_box)

        # 1. Per-class multi-threshold COCO matching across 10 IoU thresholds [0.50..0.95]
        tp_matrix = np.zeros((p_cls.size, n_thr), dtype=np.float32)
        same_class = p_cls[:, None] == g_cls[None, :]
        class_iou = np.where(same_class, iou_mat, np.float32(-1.0))

        for t_idx in range(n_thr):
            thr = float(IOU_THRESHOLDS_COCO[t_idx])
            gt_taken = np.zeros(g_cls.size, dtype=bool)
            for p_idx in range(p_cls.size):
                row = np.where(~gt_taken, class_iou[p_idx], np.float32(-1.0))
                best_g = int(np.argmax(row))
                if row[best_g] >= thr:
                    tp_matrix[p_idx, t_idx] = 1.0
                    gt_taken[best_g] = True

        for cid in sorted_locked_ids:
            c_sel = p_cls == cid
            if np.any(c_sel):
                pred_tp_records[cid].append(tp_matrix[c_sel])
                pred_conf_records[cid].append(p_conf[c_sel])

        # 2. Cross-class Confusion Matrix at IoU = 0.50 (rows = ground truth, cols = prediction >= op_conf_threshold)
        gt_matched_cm = np.zeros(g_cls.size, dtype=bool)
        for p_idx in np.flatnonzero(op_sel).tolist():
            avail_iou = np.where(~gt_matched_cm, iou_mat[p_idx], np.float32(-1.0))
            best_g = int(np.argmax(avail_iou))
            p_pos = cid_to_pos[int(p_cls[p_idx])]
            if avail_iou[best_g] >= confusion_iou_threshold:
                g_pos = cid_to_pos[int(g_cls[best_g])]
                conf_mat[g_pos, p_pos] += 1
                gt_matched_cm[best_g] = True
            else:
                conf_mat[bg_pos, p_pos] += 1

        for g_idx in np.flatnonzero(~gt_matched_cm).tolist():
            conf_mat[cid_to_pos[int(g_cls[g_idx])], bg_pos] += 1

    per_class_results: list[ClassEvalMetrics] = []
    op_thr_f = np.float32(op_conf_threshold)
    for cid in sorted_locked_ids:
        n_gt = gt_counts_per_cid[cid]
        if pred_conf_records[cid]:
            all_tp = np.concatenate(pred_tp_records[cid], axis=0)
            all_cf = np.concatenate(pred_conf_records[cid], axis=0)
            op_mask = all_cf >= op_thr_f
            n_pr = int(np.count_nonzero(op_mask))
            tp50 = int(np.sum(all_tp[op_mask, 0]))
            fp50 = n_pr - tp50
            fn50 = max(0, n_gt - tp50)
            prec = tp50 / float(n_pr) if n_pr > 0 else 0.0
            rec = tp50 / float(n_gt) if n_gt > 0 else 0.0
            f1 = (2.0 * prec * rec / (prec + rec)) if (prec + rec) > 0.0 else 0.0
            ap50 = compute_ap_101pt_vec(all_tp[:, 0], all_cf, n_gt)
            aps = [compute_ap_101pt_vec(all_tp[:, j], all_cf, n_gt) for j in range(n_thr)]
            ap50_95 = float(np.mean(aps))
        else:
            n_pr = 0
            tp50 = 0
            fp50 = 0
            fn50 = n_gt
            prec = 0.0
            rec = 0.0
            f1 = 0.0
            ap50 = 0.0
            ap50_95 = 0.0

        per_class_results.append(
            ClassEvalMetrics(
                class_index=cid,
                class_name=locked_eval_classes[cid],
                n_test_gt=n_gt,
                n_predictions=n_pr,
                tp_at_50=tp50,
                fp_at_50=fp50,
                fn_at_50=fn50,
                precision=round(prec, 4),
                recall=round(rec, 4),
                f1=round(f1, 4),
                ap50=round(ap50, 4),
                ap50_95=round(ap50_95, 4),
            )
        )

    # Strict NFR-11 mean over ALL K locked classes (zero post-hoc dropping of weak classes)
    mean_p = float(np.mean([m.precision for m in per_class_results]))
    mean_r = float(np.mean([m.recall for m in per_class_results]))
    mean_f1 = (2.0 * mean_p * mean_r / (mean_p + mean_r)) if (mean_p + mean_r) > 0.0 else 0.0
    map50 = float(np.mean([m.ap50 for m in per_class_results]))
    map50_95 = float(np.mean([m.ap50_95 for m in per_class_results]))

    off_diag = conf_mat[:k_count, :k_count].copy()
    np.fill_diagonal(off_diag, 0)
    confused_pairs: list[dict[str, Any]] = []
    if np.any(off_diag > 0):
        flat_order = np.argsort(-off_diag.ravel())
        for flat_idx in flat_order[:8].tolist():
            cnt = int(off_diag.ravel()[flat_idx])
            if cnt <= 0:
                break
            r_pos, c_pos = divmod(flat_idx, k_count)
            confused_pairs.append(
                {
                    "gt_class": locked_names[r_pos],
                    "pred_class": locked_names[c_pos],
                    "count": cnt,
                }
            )

    return DetectionEvalSummary(
        locked_class_indices=sorted_locked_ids,
        locked_class_names=locked_names,
        total_test_images=total_images,
        ood_test_images=ood_images,
        ood_false_positive_images=ood_fp_images,
        hitl_uncertain_detections=uncertain_preds,
        total_detections=total_preds,
        precision=round(mean_p, 4),
        recall=round(mean_r, 4),
        f1=round(mean_f1, 4),
        map50=round(map50, 4),
        map50_95=round(map50_95, 4),
        per_class=tuple(per_class_results),
        confusion_matrix=conf_mat.tolist(),
        confusion_labels=(*locked_names, "background"),
        top_confused_pairs=confused_pairs,
    )
