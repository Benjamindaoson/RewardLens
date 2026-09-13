#!/usr/bin/env python3
"""Freeze RewardLens-CLEVR audit items. Does not drop FAIL rows from the full freeze."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.common import VARIANTS, load_json, write_json  # noqa: E402
from lib.hashutil import sha256_file, sha256_json  # noqa: E402
from lib.jsonl_io import read_jsonl, write_jsonl  # noqa: E402

AUDIT_VERSION = "rewardlens_clevr_controlled_v1"
FACTORS = ("count", "attribute", "presence", "spatial")
SCALE_DIRS = {
    "count": os.path.join(PROJECT, "outputs", "count_scale_v1"),
    "attribute": os.path.join(PROJECT, "outputs", "attribute_scale_v1"),
    "presence": os.path.join(PROJECT, "outputs", "presence_scale_v1"),
    "spatial": os.path.join(PROJECT, "outputs", "spatial_scale_v1"),
}
CONFIGS = {
    "count": os.path.join(ROOT, "configs", "count_scale_v1.json"),
    "attribute": os.path.join(ROOT, "configs", "attribute_scale_v1.json"),
    "presence": os.path.join(ROOT, "configs", "presence_scale_v1.json"),
    "spatial": os.path.join(ROOT, "configs", "spatial_scale_v1.json"),
}


def triplet_complete(output_dir: str, manifest: dict) -> bool:
    for variant in VARIANTS:
        if not os.path.isfile(os.path.join(output_dir, manifest[variant]["image"])):
            return False
        if not os.path.isfile(os.path.join(output_dir, manifest[variant]["scene"])):
            return False
    return True


def qc_status_map(output_dir: str) -> dict[str, dict]:
    report_path = os.path.join(output_dir, "qc_report.json")
    if not os.path.isfile(report_path):
        return {}
    report = load_json(report_path)
    return {row["triplet_id"]: row for row in report.get("triplets", [])}


def freeze_factor(factor: str, output_dir: str) -> tuple[list[dict], dict]:
    manifests = read_jsonl(os.path.join(output_dir, "pilot_manifest.jsonl"))
    qc_map = qc_status_map(output_dir)
    items = []
    generated = 0
    for manifest in manifests:
        if not triplet_complete(output_dir, manifest):
            continue
        generated += 1
        qc = qc_map.get(manifest["triplet_id"], {})
        status = qc.get("status", "UNSCORED")
        for variant in VARIANTS:
            item_id = "%s:%s" % (manifest["triplet_id"], variant)
            items.append(
                {
                    "item_id": item_id,
                    "triplet_id": manifest["triplet_id"],
                    "factor": factor,
                    "variant": variant,
                    "image_path": os.path.normpath(os.path.join(output_dir, manifest[variant]["image"])),
                    "scene_path": os.path.normpath(os.path.join(output_dir, manifest[variant]["scene"])),
                    "question": manifest["question"],
                    "candidate_a": manifest["candidate_a"],
                    "candidate_b": manifest["candidate_b"],
                    "expected_preference": manifest[variant]["preferred"],
                    "seed": manifest.get("seed"),
                    "render_seed": manifest.get("render_seed"),
                    "qc_status": status,
                    "qc_flags": qc.get("flags") or [],
                    "matching_contract": manifest.get("matching_contract"),
                    "source_dir": output_dir,
                    "source_manifest": manifest,
                }
            )
    usable = [it for it in items if it["qc_status"] == "PASS"]
    summary = {
        "factor": factor,
        "source_dir": output_dir,
        "generated_triplets": generated,
        "target_triplets": 500,
        "PASS": sum(1 for it in items if it["variant"] == "base" and it["qc_status"] == "PASS"),
        "BORDERLINE": sum(1 for it in items if it["variant"] == "base" and it["qc_status"] == "BORDERLINE"),
        "FAIL": sum(1 for it in items if it["variant"] == "base" and it["qc_status"] == "FAIL"),
        "UNSCORED": sum(1 for it in items if it["variant"] == "base" and it["qc_status"] == "UNSCORED"),
        "final_usable_N": sum(1 for it in items if it["variant"] == "base" and it["qc_status"] == "PASS"),
        "n_items": len(items),
        "n_pass_items": len(usable),
        "complete": generated >= 500,
    }
    return items, summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=os.path.join(PROJECT, "outputs", "controlled_v1"))
    parser.add_argument("--require-complete", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    all_items = []
    summaries = []
    config_hashes = {}
    for factor in FACTORS:
        items, summary = freeze_factor(factor, SCALE_DIRS[factor])
        if args.require_complete and not summary["complete"]:
            raise SystemExit("factor %s incomplete: %s / 500" % (factor, summary["generated_triplets"]))
        all_items.extend(items)
        summaries.append(summary)
        config_hashes[factor] = sha256_file(CONFIGS[factor]) if os.path.isfile(CONFIGS[factor]) else None

    full_path = os.path.join(out_dir, "audit_manifest.jsonl")
    pass_path = os.path.join(out_dir, "audit_manifest_pass.jsonl")
    write_jsonl(full_path, all_items)
    write_jsonl(pass_path, [it for it in all_items if it["qc_status"] == "PASS"])

    dataset_summary = {
        "audit_dataset_version": AUDIT_VERSION,
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "factors": summaries,
        "generated": sum(s["generated_triplets"] for s in summaries),
        "PASS": sum(s["PASS"] for s in summaries),
        "BORDERLINE": sum(s["BORDERLINE"] for s in summaries),
        "FAIL": sum(s["FAIL"] for s in summaries),
        "final_usable_N": sum(s["final_usable_N"] for s in summaries),
        "target_triplets": 2000,
        "target_pngs": 6000,
        "fail_rows_retained": True,
        "partial": any(not s["complete"] for s in summaries),
    }
    write_json(os.path.join(out_dir, "dataset_summary.json"), dataset_summary)
    csv_path = os.path.join(out_dir, "dataset_summary.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["factor", "generated_triplets", "PASS", "BORDERLINE", "FAIL", "final_usable_N", "complete"],
        )
        writer.writeheader()
        for row in summaries:
            writer.writerow({k: row[k] for k in writer.fieldnames})

    freeze_meta = {
        "audit_dataset_version": AUDIT_VERSION,
        "generation_config_hash": config_hashes,
        "generation_config_hash_combined": sha256_json(config_hashes),
        "manifest_hash": sha256_file(full_path),
        "pass_manifest_hash": sha256_file(pass_path),
        "n_items": len(all_items),
        "n_pass_items": sum(1 for it in all_items if it["qc_status"] == "PASS"),
        "partial": dataset_summary["partial"],
        "policy": "FAIL/BORDERLINE retained in audit_manifest.jsonl; default inference uses PASS only",
    }
    write_json(os.path.join(out_dir, "freeze_meta.json"), freeze_meta)
    print(json.dumps({"out_dir": out_dir, **dataset_summary, "freeze_meta": freeze_meta}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
