"""Dual-backend device probe: CUDA and ROCm/HIP.

ROCm PyTorch still uses torch.cuda.* APIs. Record torch.version.hip separately.
Never assume NVIDIA-only.
"""

from __future__ import annotations

import json
import os
import platform
from typing import Any


def _safe_torch():
    try:
        import torch
    except Exception as exc:  # pragma: no cover
        return None, str(exc)
    return torch, None


def probe_device() -> dict[str, Any]:
    torch, err = _safe_torch()
    report: dict[str, Any] = {
        "hostname": platform.node(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "torch_import_ok": torch is not None,
        "torch_import_error": err,
        "torch_version": None,
        "torch_hip_version": None,
        "torch_cuda_version": None,
        "cuda_available": False,
        "hip_available": False,
        "backend": "cpu",
        "device_count": 0,
        "devices": [],
        "bf16_supported": False,
        "default_dtype_plan": "bfloat16",
        "default_attn": "sdpa_or_eager",
        "flash_attn_default": False,
        "bitsandbytes_default": False,
    }
    if torch is None:
        return report
    report["torch_version"] = str(torch.__version__)
    hip = getattr(getattr(torch, "version", None), "hip", None)
    cuda_ver = getattr(getattr(torch, "version", None), "cuda", None)
    report["torch_hip_version"] = None if hip in (None, "") else str(hip)
    report["torch_cuda_version"] = None if cuda_ver in (None, "") else str(cuda_ver)
    cuda_available = bool(getattr(torch, "cuda", None) and torch.cuda.is_available())
    report["cuda_available"] = cuda_available
    report["hip_available"] = bool(report["torch_hip_version"])
    if cuda_available:
        report["backend"] = "rocm" if report["hip_available"] else "cuda"
        report["device_count"] = int(torch.cuda.device_count())
        for idx in range(report["device_count"]):
            props = torch.cuda.get_device_properties(idx)
            total = int(getattr(props, "total_memory", 0))
            report["devices"].append(
                {
                    "index": idx,
                    "name": torch.cuda.get_device_name(idx),
                    "total_memory_bytes": total,
                    "total_memory_gb": round(total / (1024 ** 3), 3),
                    "major": getattr(props, "major", None),
                    "minor": getattr(props, "minor", None),
                }
            )
        try:
            report["bf16_supported"] = bool(torch.cuda.is_bf16_supported())
        except Exception:
            report["bf16_supported"] = report["backend"] in {"cuda", "rocm"}
    else:
        report["backend"] = "cpu"
        report["bf16_supported"] = False
    if report["devices"]:
        report["primary_device_name"] = report["devices"][0]["name"]
        report["primary_vram_gb"] = report["devices"][0]["total_memory_gb"]
    else:
        report["primary_device_name"] = "cpu"
        report["primary_vram_gb"] = 0.0
    return report


def format_probe_text(report: dict[str, Any]) -> str:
    lines = [
        "torch version: %s" % report.get("torch_version"),
        "HIP version: %s" % report.get("torch_hip_version"),
        "CUDA version: %s" % report.get("torch_cuda_version"),
        "backend: %s" % report.get("backend"),
        "device name: %s" % report.get("primary_device_name"),
        "VRAM: %s GB" % report.get("primary_vram_gb"),
        "bf16 support: %s" % report.get("bf16_supported"),
    ]
    return "\n".join(lines)


def write_probe(path: str, report: dict[str, Any] | None = None) -> dict[str, Any]:
    report = report or probe_device()
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    return report
