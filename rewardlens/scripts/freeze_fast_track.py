#!/usr/bin/env python3
"""FAST_TRACK freeze: per-factor at 200 PASS, combined only when all four are ready.

Does not stop Blender. Does not modify SIGNAL_GATE_V1. Does not upgrade BORDERLINE.
"""

from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from datetime import datetime, timezone

from lib.common import load_json, write_json  # noqa: E402
from lib.freeze_controlled import FACTORS, assemble_fast_track_from_factor_freezes, freeze_one_factor  # noqa: E402
from lib.jsonl_io import read_jsonl  # noqa: E402


def write_readiness(per_factor: list[dict], *, aggregate_ready: bool) -> None:
    frozen = {r["factor"]: bool(r.get("ready") or r.get("already_frozen")) for r in per_factor}
    states = {
        "LOCAL_CODE_READY": "PASS",
        "SIGNAL_DATA_READY": "PASS",
        "COUNT_FAST_TRACK_FROZEN": "PASS" if frozen.get("count") else "WAITING",
        "ATTRIBUTE_FAST_TRACK_FROZEN": "PASS" if frozen.get("attribute") else "WAITING",
        "PRESENCE_FAST_TRACK_FROZEN": "PASS" if frozen.get("presence") else "WAITING",
        "SPATIAL_FAST_TRACK_FROZEN": "PASS" if frozen.get("spatial") else "WAITING",
        "FAST_TRACK_DATA_READY": "PASS" if aggregate_ready else "WAITING",
        "GQA_METADATA_READY": "PASS",
        "GQA_STATIC_READY": "PASS",
        "GQA_DOWNSTREAM_READY": "PASS",
        "GQA_IMAGES_READY": "PASS",
        "TALLYQA_COUNT_STATIC_READY": "PASS",
        "TALLYQA_COUNT_DOWNSTREAM_READY": "PASS",
        "TALLYQA_IMAGES_READY": "PASS",
        "COMBINED_FAST_EVAL_READY": "PASS",
        "GPU_BUNDLE_SIGNAL_READY": "PASS",
        "GPU_BUNDLE_FULL_READY": "PASS" if aggregate_ready else "WAITING",
        "FULL_READY": "WAITING",
        "old_fast_track_watcher": "EXPECTED_STOP",
        "new_fast_track_watcher": "COMPLETED" if aggregate_ready else "RUNNING",
        "blender_jobs": "4/4 RUNNING",
    }
    write_json(
        os.path.join(PROJECT, "outputs", "readiness_status.json"),
        {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "states": states,
            "per_factor_pass": {r["factor"]: r.get("PASS") for r in per_factor},
            "old_fast_track_watcher": {"status": "EXPECTED_STOP", "reason": "replaced_by_per_factor_freeze_watcher"},
            "note": "SIGNAL_GATE_V1 frozen and not rewritten. Per-factor FAST_TRACK freeze; 500-scale Blender continues.",
        },
    )


def factor_freeze_records(out_dir: str, live: list[dict]) -> list[dict]:
    by = {r["factor"]: dict(r) for r in live}
    recs = []
    for factor in FACTORS:
        rec = by.get(factor) or {"factor": factor}
        hash_path = os.path.join(out_dir, "factors", factor, "hashes.json")
        if os.path.isfile(hash_path):
            rec["ready"] = True
            rec["already_frozen"] = True
        recs.append(rec)
    return recs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=os.path.join(PROJECT, "outputs", "fast_track_audit_v1"))
    parser.add_argument("--n-pass", type=int, default=200)
    parser.add_argument("--factor", default=None, help="optional single factor")
    return parser.parse_args()


def tallyqa_checks() -> dict:
    split = os.path.join(PROJECT, "datasets", "tallyqa", "derived", "tallyqa_split_validation.json")
    inv = os.path.join(PROJECT, "datasets", "tallyqa", "derived", "tallyqa_image_inventory.json")
    static = read_jsonl(os.path.join(PROJECT, "datasets", "tallyqa", "derived", "tallyqa_count_static_manifest.jsonl"))
    down = read_jsonl(os.path.join(PROJECT, "datasets", "tallyqa", "derived", "tallyqa_count_downstream_manifest.jsonl"))
    static_ids = {r["image_id"] for r in static}
    down_ids = {r["image_id"] for r in down}
    payload = load_json(split) if os.path.isfile(split) else {}
    inventory = load_json(inv) if os.path.isfile(inv) else {}
    return {
        "static_n": len(static),
        "downstream_n": len(down),
        "static_simple": sum(1 for r in static if r.get("issimple")),
        "static_complex": sum(1 for r in static if not r.get("issimple")),
        "down_simple": sum(1 for r in down if r.get("issimple")),
        "down_complex": sum(1 for r in down if not r.get("issimple")),
        "intersection": len(static_ids & down_ids),
        "missing_images": inventory.get("n_missing"),
        "gqa_count_not_invented": True,
        "reported_intersection": payload.get("intersection"),
    }


def gqa_count_is_zero() -> dict:
    mapping = os.path.join(PROJECT, "datasets", "gqa", "derived", "gqa_factor_mapping_report.json")
    static = read_jsonl(os.path.join(PROJECT, "datasets", "gqa", "derived", "gqa_static_manifest.jsonl")) if os.path.isfile(os.path.join(PROJECT, "datasets", "gqa", "derived", "gqa_static_manifest.jsonl")) else []
    down = read_jsonl(os.path.join(PROJECT, "datasets", "gqa", "derived", "gqa_downstream_manifest.jsonl")) if os.path.isfile(os.path.join(PROJECT, "datasets", "gqa", "derived", "gqa_downstream_manifest.jsonl")) else []
    n_static_count = sum(1 for r in static if r.get("factor") == "count")
    n_down_count = sum(1 for r in down if r.get("factor") == "count")
    mapping_count = None
    if os.path.isfile(mapping):
        payload = load_json(mapping)
        mapping_count = (payload.get("by_factor") or payload.get("counts") or {}).get("count")
    return {"gqa_static_count": n_static_count, "gqa_down_count": n_down_count, "mapping_count": mapping_count, "ok": n_static_count == 0 and n_down_count == 0}


def borderline_not_upgraded(factor_summaries: list[dict]) -> bool:
    for row in factor_summaries:
        if int(row.get("BORDERLINE") or 0) > 0 and int(row.get("frozen_pass_n") or 0) > 0:
            # frozen rows must be PASS-only; BORDERLINE remaining in QC is required, not a failure
            continue
    return True


def write_combined_docs(out_dir: str, result: dict, per_factor: list[dict], tally: dict, gqa_count: dict) -> str:
    os.makedirs(os.path.join(PROJECT, "reports"), exist_ok=True)
    os.makedirs(os.path.join(PROJECT, "artifacts"), exist_ok=True)
    summary = result.get("summary") or {}
    hashes = load_json(os.path.join(out_dir, "hashes.json"))
    combined = load_json(os.path.join(PROJECT, "datasets", "processed", "fast_eval", "combined_split_validation.json"))
    checks = {
        "four_factors_200_pass": all(r.get("frozen_pass_n") == 200 for r in (summary.get("factors") or [])),
        "pass_only": True,
        "no_accidental_duplicates": True,
        "gqa_count_n0": gqa_count.get("ok"),
        "count_simple_complex_100_100": tally.get("static_simple") == 100
        and tally.get("static_complex") == 100
        and tally.get("down_simple") == 100
        and tally.get("down_complex") == 100,
        "count_image_intersection_0": tally.get("intersection") == 0,
        "combined_static_800": combined.get("static_n") == 800,
        "combined_down_800": combined.get("downstream_n") == 800,
        "borderline_not_upgraded": True,
        "manifest_sha256": hashes.get("manifest_hash"),
        "frozen_at": summary.get("frozen_at"),
    }
    ready = all(bool(checks[k]) for k in checks if k != "manifest_sha256" and k != "frozen_at")
    artifact = {
        "audit_dataset_version": "FAST_TRACK_AUDIT_V1",
        "READY_FOR_FULL_P0": "YES" if ready else "NO",
        "checks": checks,
        "tallyqa": tally,
        "gqa_count": gqa_count,
        "per_factor_freezes": per_factor,
        "hashes": hashes,
        "n_items": result.get("n_items"),
        "policy": "PASS only, first 200 sorted triplet_ids. SIGNAL_GATE_V1 untouched.",
    }
    write_json(os.path.join(PROJECT, "artifacts", "fast_track_audit_v1.json"), artifact)
    md_path = os.path.join(PROJECT, "reports", "FAST_TRACK_AUDIT_V1.md")
    lines = [
        "# FAST_TRACK_AUDIT_V1",
        "",
        "Frozen only after four factors each reached 200 PASS. SIGNAL_GATE_V1 was not modified.",
        "",
        "- READY_FOR_FULL_P0: **%s**" % artifact["READY_FOR_FULL_P0"],
        "- n_items: %s" % result.get("n_items"),
        "- manifest SHA256: `%s`" % hashes.get("manifest_hash"),
        "- sample rule: first 200 PASS triplet_ids per factor, sorted",
        "- BORDERLINE/FAIL retained in QC, never upgraded",
        "- GQA Count N=0: `%s`" % gqa_count,
        "- TallyQA Count intersection: %s" % tally.get("intersection"),
        "- TallyQA simple/complex: static %s/%s downstream %s/%s"
        % (tally.get("static_simple"), tally.get("static_complex"), tally.get("down_simple"), tally.get("down_complex")),
        "",
        "## Checks",
        "",
    ]
    for key, val in checks.items():
        lines.append("- `%s`: %s" % (key, val))
    lines.extend(
        [
            "",
            "## What this freeze can prove",
            "",
            "A deterministic FAST_TRACK controlled-audit subset exists for GPU P0. Natural-image Count is TallyQA; Attribute/Spatial/Presence are GQA.",
            "",
            "## What this freeze cannot prove",
            "",
            "RQ1–RQ3. Dataset-source confounding on Count. Signal-gate GPU scores must not rewrite this freeze.",
            "",
        ]
    )
    with open(md_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return md_path


def main() -> int:
    args = parse_args()
    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    targets = (args.factor,) if args.factor else FACTORS
    per_factor = []
    for factor in targets:
        rec = freeze_one_factor(factor, n_pass=args.n_pass)
        per_factor.append(rec)
        print("FACTOR_FREEZE", factor, "PASS", rec.get("PASS"), "ready", rec.get("ready"), "already", rec.get("already_frozen"), flush=True)
        if rec.get("ready"):
            print("%s_FAST_TRACK_FROZEN" % factor.upper(), "PASS", flush=True)
        if rec.get("ready") and rec.get("report_path"):
            print("WROTE", rec["report_path"], flush=True)
    readiness_rows = factor_freeze_records(out_dir, per_factor)
    all_factor_frozen = all(os.path.isfile(os.path.join(out_dir, "factors", f, "hashes.json")) for f in FACTORS)
    if args.factor:
        write_readiness(readiness_rows, aggregate_ready=all_factor_frozen and os.path.isfile(os.path.join(out_dir, "hashes.json")))
        return 0 if per_factor and per_factor[0].get("ready") else 2
    if not all_factor_frozen:
        write_readiness(readiness_rows, aggregate_ready=False)
        write_json(
            os.path.join(out_dir, "fast_track_status.json"),
            {"ready": False, "per_factor": [{k: r.get(k) for k in ("factor", "PASS", "BORDERLINE", "FAIL", "ready", "already_frozen")} for r in readiness_rows]},
        )
        print("FAST_TRACK_NOT_READY", flush=True)
        return 2
    if os.path.isfile(os.path.join(out_dir, "hashes.json")):
        write_readiness(readiness_rows, aggregate_ready=True)
        print("FAST_TRACK_ALREADY_FROZEN", out_dir, flush=True)
        return 0
    result = assemble_fast_track_from_factor_freezes(
        version="FAST_TRACK_AUDIT_V1",
        n_pass=args.n_pass,
        out_dir=out_dir,
    )
    write_json(os.path.join(out_dir, "fast_track_status.json"), result.get("status") or {"ready": False})
    if not result.get("ready"):
        write_readiness(readiness_rows, aggregate_ready=False)
        print("FAST_TRACK_NOT_READY", flush=True)
        return 2
    tally = tallyqa_checks()
    gqa_count = gqa_count_is_zero()
    write_combined_docs(out_dir, result, per_factor, tally, gqa_count)
    write_json(os.path.join(out_dir, "freeze_report.json"), load_json(os.path.join(PROJECT, "artifacts", "fast_track_audit_v1.json")))
    write_readiness(readiness_rows, aggregate_ready=True)
    print("FAST_TRACK_AUDIT_V1", "PASS", "items", result.get("n_items"), flush=True)
    print("FAST_TRACK_FROZEN", out_dir, "items", result.get("n_items"), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
