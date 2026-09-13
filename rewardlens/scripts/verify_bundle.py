#!/usr/bin/env python3
"""Verify a GPU bundle: manifests, images, hashes, configs, scripts, GQA split."""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.common import write_json  # noqa: E402
from lib.hashutil import sha256_file  # noqa: E402
from lib.jsonl_io import read_jsonl  # noqa: E402

REQUIRED_SCRIPTS = [
    "inference/run_probe.py",
    "inference/run_signal_gate.py",
    "inference/run_full_audit.py",
    "inference/run_static.py",
    "inference/run_downstream.py",
    "inference/run_worker.py",
    "scripts/run_gpu_preflight.sh",
    "scripts/run_signal_pipeline.sh",
    "scripts/run_full_pipeline.sh",
    "scripts/merge_worker_results.py",
    "scripts/estimate_gpu_time.py",
    "models/model_registry.json",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--report", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bundle = os.path.abspath(args.bundle)
    errors = []
    warnings = []
    if not os.path.isdir(bundle):
        print("BUNDLE_MISSING", bundle)
        return 2
    code_root = os.path.join(bundle, "rewardlens")
    if not os.path.isdir(code_root):
        code_root = os.path.join(bundle, "code", "rewardlens")
    for rel in REQUIRED_SCRIPTS:
        path = os.path.join(code_root, rel)
        if not os.path.isfile(path):
            errors.append("missing script %s" % rel)
    manifests_dir = os.path.join(bundle, "manifests")
    image_missing = []
    n_images = 0
    static_ids = set()
    down_ids = set()
    if os.path.isdir(manifests_dir):
        for name in os.listdir(manifests_dir):
            if not name.endswith(".jsonl"):
                continue
            path = os.path.join(manifests_dir, name)
            rows = read_jsonl(path)
            for row in rows:
                if name.startswith("gqa_static"):
                    static_ids.add(str(row.get("image_id")))
                if name.startswith("gqa_down"):
                    down_ids.add(str(row.get("image_id")))
                img = row.get("image_path")
                if not img:
                    continue
                n_images += 1
                candidates = [
                    img,
                    os.path.join(bundle, "images", os.path.relpath(img, PROJECT)) if os.path.isabs(img) else os.path.join(bundle, "images", img),
                    os.path.join(bundle, img) if not os.path.isabs(img) else img,
                ]
                if not any(os.path.isfile(c) for c in candidates):
                    image_missing.append(img)
    inter = sorted(static_ids & down_ids - {"None"})
    if inter:
        errors.append("static/downstream image overlap n=%d sample=%s" % (len(inter), inter[:5]))
    if image_missing:
        errors.append("missing images n=%d sample=%s" % (len(image_missing), image_missing[:5]))
    sums = os.path.join(bundle, "SHA256SUMS.txt")
    hash_ok = None
    if os.path.isfile(sums):
        hash_ok = True
        with open(sums, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                digest, rel = line.split(None, 1)
                path = os.path.join(bundle, rel.strip())
                if not os.path.isfile(path):
                    hash_ok = False
                    errors.append("checksum path missing %s" % rel)
                    continue
                if sha256_file(path) != digest:
                    hash_ok = False
                    errors.append("checksum mismatch %s" % rel)
    else:
        warnings.append("SHA256SUMS.txt missing")
    for cfg in (
        os.path.join(code_root, "models", "model_registry.json"),
        os.path.join(code_root, "configs", "gpu_worker_0.yaml"),
    ):
        if os.path.isfile(cfg) and cfg.endswith(".json"):
            json.load(open(cfg, encoding="utf-8"))
    report = {
        "bundle": bundle,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "n_manifest_image_refs": n_images,
        "hash_ok": hash_ok,
        "static_downstream_intersection": len(inter),
    }
    out = args.report or os.path.join(bundle, "bundle_verify.json")
    write_json(out, report)
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
