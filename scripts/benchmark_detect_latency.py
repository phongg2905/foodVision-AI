"""End-to-end API latency benchmark for `POST /api/v1/ai/detect` (`PERF-01`, `NFR-02`).

Executes `>= 30` consecutive HTTP multipart inference requests over real test-split
photographs and portrait EXIF fixtures using non-blocking `httpx.AsyncClient` ASGI
transport, reporting `p50`, `p95`, `p99`, mean latency, and peak memory allocation.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import os
from pathlib import Path
import platform
import sys
import time
import tracemalloc
from typing import Any

import httpx
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))


@dataclass(slots=True, frozen=True)
class LatencyBenchmarkReport:
    """Structured telemetry and percentile latency metrics for PERF-01."""

    num_requests: int
    warmup_requests: int
    concurrency: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    mean_ms: float
    min_ms: float
    max_ms: float
    target_cpu_p95_ms: float
    passes_cpu_target: bool
    peak_tracemalloc_mib: float
    environment: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "num_requests": self.num_requests,
            "warmup_requests": self.warmup_requests,
            "concurrency": self.concurrency,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
            "mean_ms": self.mean_ms,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
            "p50_seconds": round(self.p50_ms / 1000.0, 4),
            "p95_seconds": round(self.p95_ms / 1000.0, 4),
            "target_cpu_p95_ms": self.target_cpu_p95_ms,
            "passes_cpu_target": self.passes_cpu_target,
            "peak_tracemalloc_mib": self.peak_tracemalloc_mib,
            "environment": self.environment,
        }


def collect_runtime_environment(max_concurrent_inferences: int) -> dict[str, Any]:
    import PIL
    import torch
    import ultralytics

    return {
        "os": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "python_version": platform.python_version(),
        "pytorch_version": torch.__version__,
        "ultralytics_version": ultralytics.__version__,
        "pillow_version": PIL.__version__,
        "cpu_logical_cores": os.cpu_count() or 1,
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "max_concurrent_inferences": max_concurrent_inferences,
    }


def _load_sample_jpegs(dataset_dir: Path, max_samples: int = 30) -> list[tuple[str, bytes]]:
    samples: list[tuple[str, bytes]] = []
    exif_dir = dataset_dir / "exif_orientation_fixtures"
    if exif_dir.exists():
        with os.scandir(exif_dir) as it:
            for entry in sorted(it, key=lambda e: e.name):
                if entry.name.endswith(".jpg") and entry.stat().st_size > 0:
                    samples.append((entry.name, Path(entry.path).read_bytes()))

    test_img_dir = dataset_dir / "images" / "test"
    if test_img_dir.exists():
        with os.scandir(test_img_dir) as it:
            jpg_paths = sorted(
                e.path for e in it if e.name.endswith(".jpg") and e.stat().st_size > 0
            )
        for p_str in jpg_paths[: max(0, max_samples - len(samples))]:
            p = Path(p_str)
            samples.append((p.name, p.read_bytes()))

    if not samples:
        from io import BytesIO
        from PIL import Image

        buf = BytesIO()
        Image.new("RGB", (320, 240), color=(205, 60, 45)).save(buf, format="JPEG")
        samples.append(("fallback_bench.jpg", buf.getvalue()))

    return samples


# THUẬT TOÁN: Đo Độ trễ Đầu-Cuối Bất đồng bộ PERF-01 (Warmup + N Consecutive ASGI Requests)
# Cơ chế: Khởi động ấm bộ đệm singleton model qua K lượt đầu, sau đó đo chính xác đồng hồ đơn điệu
#         time.perf_counter_ns() trên >= 30 lượt POST /api/v1/ai/detect liên tiếp và tính phân vị NumPy.
# Complexity: Time O(N_req * T_infer), Space O(N_req).
async def _async_benchmark_detect(
    *,
    dataset_dir: Path,
    num_requests: int = 30,
    warmup_requests: int = 3,
) -> LatencyBenchmarkReport:
    from app.core.config import get_settings
    from app.core.database import InMemoryCatalogRepository, get_catalog_repo
    from app.main import app

    cfg = get_settings()
    payloads = _load_sample_jpegs(dataset_dir, max_samples=max(10, num_requests))
    transport = httpx.ASGITransport(app=app)

    override_applied = False
    active_repo = get_catalog_repo()
    if not active_repo.check_health() or active_repo.get_active_ai_model() is None:
        mem_repo = InMemoryCatalogRepository()
        app.dependency_overrides[get_catalog_repo] = lambda: mem_repo
        override_applied = True

    tracemalloc.start()
    latencies_ms = np.empty(num_requests, dtype=np.float64)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            for w_idx in range(warmup_requests):
                fname, raw = payloads[w_idx % len(payloads)]
                resp = await client.post(
                    "/api/v1/ai/detect",
                    files={"file": (fname, raw, "image/jpeg")},
                )
                if resp.status_code != 200:
                    raise RuntimeError(
                        f"Warmup request failed ({resp.status_code}): {resp.text}"
                    )

            for r_idx in range(num_requests):
                fname, raw = payloads[r_idx % len(payloads)]
                t0_ns = time.perf_counter_ns()
                resp = await client.post(
                    "/api/v1/ai/detect",
                    files={"file": (fname, raw, "image/jpeg")},
                )
                elapsed_ms = (time.perf_counter_ns() - t0_ns) / 1_000_000.0
                if resp.status_code != 200:
                    raise RuntimeError(
                        f"Benchmark request #{r_idx} failed ({resp.status_code}): {resp.text}"
                    )
                latencies_ms[r_idx] = elapsed_ms

        _cur, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
        if override_applied:
            app.dependency_overrides.pop(get_catalog_repo, None)

    p50, p95, p99 = np.percentile(latencies_ms, [50.0, 95.0, 99.0]).tolist()
    target_ms = 10_000.0
    return LatencyBenchmarkReport(
        num_requests=num_requests,
        warmup_requests=warmup_requests,
        concurrency=1,
        p50_ms=round(float(p50), 2),
        p95_ms=round(float(p95), 2),
        p99_ms=round(float(p99), 2),
        mean_ms=round(float(np.mean(latencies_ms)), 2),
        min_ms=round(float(np.min(latencies_ms)), 2),
        max_ms=round(float(np.max(latencies_ms)), 2),
        target_cpu_p95_ms=target_ms,
        passes_cpu_target=bool(p95 <= target_ms),
        peak_tracemalloc_mib=round(peak_bytes / (1024.0 * 1024.0), 2),
        environment=collect_runtime_environment(cfg.max_concurrent_inferences),
    )


def run_detect_latency_benchmark(
    *,
    dataset_dir: Path,
    num_requests: int = 30,
    warmup_requests: int = 3,
) -> LatencyBenchmarkReport:
    """Synchronous entrypoint executing the async PERF-01 benchmark."""
    if num_requests < 30:
        raise ValueError("PERF-01 requires at least 30 measured requests")
    return asyncio.run(
        _async_benchmark_detect(
            dataset_dir=dataset_dir,
            num_requests=num_requests,
            warmup_requests=warmup_requests,
        )
    )
