#!/usr/bin/env python3
"""Read-only snapshot of Blender / QC / freeze gates. Does not restart jobs."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in __import__("sys").path:
    __import__("sys").path.insert(0, ROOT)

from lib.common import write_json  # noqa: E402
from lib.freeze_controlled import FACTORS, SCALE_DIRS  # noqa: E402

SCALE_TO_FACTOR = {os.path.basename(path): factor for factor, path in SCALE_DIRS.items()}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_qc(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return {
            "PASS": int(payload.get("PASS") or 0),
            "BORDERLINE": int(payload.get("BORDERLINE") or 0),
            "FAIL": int(payload.get("FAIL") or 0),
            "n_qc": int(payload.get("n_qc") or 0),
            "n_incomplete": int(payload.get("n_incomplete") or 0),
            "n_new": int(payload.get("n_new") or 0),
            "qc_read_ok": True,
        }
    except Exception as exc:
        return {"PASS": None, "BORDERLINE": None, "FAIL": None, "qc_read_ok": False, "error": str(exc)}


def latest_png(image_dir: str) -> dict:
    latest_name = None
    latest_t = 0.0
    n = 0
    if not os.path.isdir(image_dir):
        return {"n_png": 0, "latest": None, "latest_mtime": None}
    for name in os.listdir(image_dir):
        if not name.lower().endswith(".png"):
            continue
        n += 1
        path = os.path.join(image_dir, name)
        mtime = os.path.getmtime(path)
        if mtime >= latest_t:
            latest_t = mtime
            latest_name = name
    return {
        "n_png": n,
        "triplets_approx": n // 3,
        "latest": latest_name,
        "latest_mtime": datetime.fromtimestamp(latest_t, timezone.utc).isoformat() if latest_name else None,
    }


def cim_processes() -> list[dict]:
    cmd = (
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.Name -eq 'blender.exe' -or $_.Name -eq 'python.exe' } | "
        "Select-Object ProcessId,Name,CreationDate,CommandLine | ConvertTo-Json -Depth 3"
    )
    try:
        raw = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", cmd],
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        payload = json.loads(raw) if raw.strip() else []
        if isinstance(payload, dict):
            payload = [payload]
        return payload
    except Exception as exc:
        return [{"error": str(exc)}]


def classify(proc: dict) -> dict:
    cmd = str(proc.get("CommandLine") or "")
    low = cmd.lower()
    factor = None
    role = "other"
    if "blender.exe" in low:
        role = "blender"
        for key, factor_name in SCALE_TO_FACTOR.items():
            if key.replace("\\", "/").lower() in low.replace("\\", "/"):
                factor = factor_name
        if "clevr_count_renderer" in low:
            factor = "count"
    elif "generate_count_pilot.py" in low:
        role = "render_driver"
        factor = "count"
    elif "generate_controlled_pilot.py" in low:
        role = "render_driver"
        if "--factor attribute" in low:
            factor = "attribute"
        elif "--factor presence" in low:
            factor = "presence"
        elif "--factor spatial" in low:
            factor = "spatial"
    elif "watch_fast_track.py" in low:
        role = "fast_track_watcher"
    elif "watch_signal_gate.py" in low:
        role = "signal_watcher"
    elif "autopep8" in low or "lsp_server" in low:
        role = "editor_lsp"
    created = proc.get("CreationDate")
    runtime = None
    try:
        if created:
            # CIM datetime like 20260912204150.123456+480
            stamp = str(created).split(".")[0]
            dt = datetime.strptime(stamp, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
            runtime = (datetime.now(timezone.utc) - dt).total_seconds()
    except Exception:
        runtime = None
    return {
        "pid": proc.get("ProcessId"),
        "name": proc.get("Name"),
        "role": role,
        "factor": factor,
        "runtime_sec_approx": runtime,
        "command": cmd,
        "healthy": role in {"blender", "render_driver", "fast_track_watcher"} and "error" not in low,
    }


def main() -> int:
    procs = [classify(p) for p in cim_processes() if isinstance(p, dict) and p.get("ProcessId")]
    factors = {}
    for factor in FACTORS:
        png = latest_png(os.path.join(SCALE_DIRS[factor], "images"))
        qc = read_qc(os.path.join(SCALE_DIRS[factor], "qc_report.json"))
        missing_png = max(0, (qc.get("n_qc") or 0) * 3 - png["n_png"]) if qc.get("qc_read_ok") else None
        factors[factor] = {
            **png,
            **qc,
            "ready_200": bool(qc.get("PASS") is not None and qc["PASS"] >= 200),
            "missing_png_vs_qc": missing_png,
        }
    snapshot = {
        "captured_at": utc_now(),
        "do_not_restart_healthy": True,
        "signal_gate_frozen": os.path.isfile(os.path.join(PROJECT, "outputs", "signal_gate_v1", "hashes.json")),
        "fast_track_frozen": os.path.isfile(os.path.join(PROJECT, "outputs", "fast_track_audit_v1", "hashes.json")),
        "factors": factors,
        "processes": procs,
        "blender_n": sum(1 for p in procs if p.get("role") == "blender"),
        "driver_n": sum(1 for p in procs if p.get("role") == "render_driver"),
        "fast_track_watcher_n": sum(1 for p in procs if p.get("role") == "fast_track_watcher"),
    }
    out_dir = os.path.join(PROJECT, "reports", "runs")
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    write_json(os.path.join(out_dir, "blender_watch_%s.json" % stamp), snapshot)
    write_json(os.path.join(PROJECT, "outputs", "blender_watch_latest.json"), snapshot)
    print(json.dumps({k: snapshot[k] for k in snapshot if k != "processes"}, indent=2))
    for proc in procs:
        if proc.get("role") in {"blender", "render_driver", "fast_track_watcher", "signal_watcher"}:
            print("PROC", proc.get("pid"), proc.get("role"), proc.get("factor"), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
