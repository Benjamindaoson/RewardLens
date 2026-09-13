#!/usr/bin/env python3
"""Write reports/CURRENT_PRE_GPU_STATUS.md from live gates. Read-only of SIGNAL_GATE_V1."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.common import load_json  # noqa: E402
from lib.freeze_controlled import FACTORS, SCALE_DIRS  # noqa: E402


def qc(factor: str) -> dict:
    path = os.path.join(SCALE_DIRS[factor], "qc_report.json")
    try:
        payload = load_json(path)
        return {k: payload.get(k) for k in ("PASS", "BORDERLINE", "FAIL", "n_qc", "n_incomplete")}
    except Exception as exc:
        return {"error": str(exc)}


def main() -> int:
    snap_path = os.path.join(PROJECT, "outputs", "blender_watch_latest.json")
    snap = load_json(snap_path) if os.path.isfile(snap_path) else {}
    signal = os.path.isfile(os.path.join(PROJECT, "outputs", "signal_gate_v1", "hashes.json"))
    fast = os.path.isfile(os.path.join(PROJECT, "outputs", "fast_track_audit_v1", "hashes.json"))
    tally = load_json(os.path.join(PROJECT, "datasets", "tallyqa", "derived", "tallyqa_split_validation.json"))
    inv = load_json(os.path.join(PROJECT, "datasets", "tallyqa", "derived", "tallyqa_image_inventory.json"))
    factors = {f: qc(f) for f in FACTORS}
    n200 = [f for f, rec in factors.items() if (rec.get("PASS") or 0) >= 200]
    blocker = "FAST_TRACK 200 PASS / factor (controlled audit)" if not fast else "none"
    next_task = "Keep FAST_TRACK watcher; do not start other development." if not fast else "Build full P0 GPU bundle, verify SHA256, then wait for GPU."
    lines = [
        "# CURRENT_PRE_GPU_STATUS",
        "",
        "Updated: %s" % datetime.now(timezone.utc).isoformat(),
        "",
        "- SIGNAL_GATE_V1 = **FROZEN**" if signal else "- SIGNAL_GATE_V1 = NOT FROZEN",
        "- SIGNAL_GATE_GPU = **READY**" if signal else "- SIGNAL_GATE_GPU = NOT READY",
        "- FAST_TRACK_AUDIT_V1 = **FROZEN**" if fast else "- FAST_TRACK_AUDIT_V1 = **IN_PROGRESS**",
        "- FULL_P0_GPU = **READY**" if fast else "- FULL_P0_GPU = **NOT_READY**",
        "",
        "## Unique blocking dependency",
        "",
        blocker,
        "",
        "## Next allowed task",
        "",
        next_task,
        "",
        "## Factor PASS (QC cache; BORDERLINE not upgraded)",
        "",
    ]
    for factor in FACTORS:
        rec = factors[factor]
        png = ((snap.get("factors") or {}).get(factor) or {}).get("n_png")
        lines.append("- %s: PASS=%s BORDERLINE=%s FAIL=%s png=%s ready_200=%s" % (factor, rec.get("PASS"), rec.get("BORDERLINE"), rec.get("FAIL"), png, factor in n200))
    lines.extend(
        [
            "",
            "## Count natural-image freeze (already done)",
            "",
            "- static/downstream intersection: %s" % tally.get("intersection"),
            "- simple/complex static: %s/%s" % (tally.get("static_simple"), tally.get("static_complex")),
            "- simple/complex downstream: %s/%s" % (tally.get("down_simple"), tally.get("down_complex")),
            "- images missing: %s" % inv.get("n_missing"),
            "- GQA Count remains N=0",
            "",
            "## Blender",
            "",
            "- blender_n: %s" % snap.get("blender_n"),
            "- driver_n: %s" % snap.get("driver_n"),
            "- fast_track_watcher_n: %s" % snap.get("fast_track_watcher_n"),
            "- do_not_restart_healthy: true",
            "",
        ]
    )
    os.makedirs(os.path.join(PROJECT, "reports"), exist_ok=True)
    path = os.path.join(PROJECT, "reports", "CURRENT_PRE_GPU_STATUS.md")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    print(path)
    print(json.dumps({"signal": signal, "fast": fast, "n200": n200, "factors": factors, "blocker": blocker}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
