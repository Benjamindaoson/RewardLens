#!/usr/bin/env python3
"""Extract GQA metadata, map factors, split, build static+downstream, inventory images.

Does not download the full GQA image zip. Images are acquired only after freeze.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.common import write_json  # noqa: E402
from lib.jsonl_io import read_jsonl  # noqa: E402

GQA_DIR = os.path.join(PROJECT, "datasets", "gqa")
DERIVED = os.path.join(GQA_DIR, "derived")
PROCESSED = os.path.join(PROJECT, "datasets", "processed", "gqa")
QUESTIONS_ZIP = os.path.join(GQA_DIR, "questions1.2.zip")
SCENE_ZIP = os.path.join(GQA_DIR, "sceneGraphs.zip")
EXPECTED_Q_BYTES = 1498616372


def run(cmd: list[str]) -> int:
    print("RUN", " ".join(cmd), flush=True)
    return subprocess.run(cmd).returncode


def copy_if(src: str, dst: str) -> None:
    if os.path.isfile(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)


def extract_if_needed(zip_path: str, dest_dir: str) -> None:
    marker = os.path.join(dest_dir, ".extracted_ok")
    if os.path.isfile(marker):
        return
    os.makedirs(dest_dir, exist_ok=True)
    print("TESTZIP", zip_path, flush=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        bad = zf.testzip()
        if bad:
            raise RuntimeError("zip integrity failed: %s in %s" % (bad, zip_path))
        zf.extractall(dest_dir)
    with open(marker, "w", encoding="utf-8") as handle:
        handle.write(datetime.now(timezone.utc).isoformat())
    print("EXTRACT_OK", dest_dir, flush=True)


def write_mapping_stats(report_path: str, csv_path: str) -> None:
    report = json.load(open(report_path, encoding="utf-8"))
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["factor", "n"])
        for factor, n in sorted((report.get("counts") or {}).items()):
            writer.writerow([factor, n])
        writer.writerow(["mapped_total", report.get("n_mapped")])
        writer.writerow(["keyword_fallback_n", report.get("keyword_fallback_n")])


def relink_static_images(manifest_path: str, images_dir: str) -> None:
    if not os.path.isfile(manifest_path):
        return
    rows = read_jsonl(manifest_path)
    out = []
    for row in rows:
        iid = str(row.get("image_id") or "")
        cand = os.path.join(images_dir, "%s.jpg" % iid)
        row["image_path"] = cand if os.path.isfile(cand) else row.get("image_path")
        out.append(row)
    from lib.jsonl_io import write_jsonl

    write_jsonl(manifest_path, out)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-factor", type=int, default=200)
    parser.add_argument("--skip-images", action="store_true")
    parser.add_argument("--max-map-items", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.makedirs(DERIVED, exist_ok=True)
    os.makedirs(PROCESSED, exist_ok=True)
    if not os.path.isfile(QUESTIONS_ZIP):
        print("QUESTIONS_ZIP_MISSING", flush=True)
        return 2
    qsize = os.path.getsize(QUESTIONS_ZIP)
    if qsize < EXPECTED_Q_BYTES:
        print("QUESTIONS_ZIP_INCOMPLETE", qsize, "expected", EXPECTED_Q_BYTES, flush=True)
        return 2
    extract_if_needed(QUESTIONS_ZIP, os.path.join(GQA_DIR, "questions"))
    if os.path.isfile(SCENE_ZIP) and os.path.getsize(SCENE_ZIP) > 0:
        try:
            extract_if_needed(SCENE_ZIP, os.path.join(GQA_DIR, "sceneGraphs"))
        except Exception as exc:
            print("SCENE_GRAPH_EXTRACT_WARN", exc, flush=True)
    else:
        print("SCENE_GRAPHS_NOT_READY continuing with questions-only mapping", flush=True)

    map_cmd = [
        sys.executable,
        os.path.join(ROOT, "scripts", "map_gqa_factors.py"),
        "--gqa-dir",
        GQA_DIR,
        "--out-dir",
        DERIVED,
    ]
    if args.max_map_items:
        map_cmd.extend(["--max-items", str(args.max_map_items)])
    if run(map_cmd) != 0:
        return 1
    report_path = os.path.join(DERIVED, "gqa_factor_mapping_report.json")
    write_mapping_stats(report_path, os.path.join(DERIVED, "mapping_stats.csv"))
    write_mapping_stats(report_path, os.path.join(PROCESSED, "mapping_stats.csv"))

    if run([sys.executable, os.path.join(ROOT, "scripts", "split_gqa_images.py")]) != 0:
        return 1
    split_report = os.path.join(DERIVED, "gqa_split_report.json")
    if os.path.isfile(split_report):
        payload = json.load(open(split_report, encoding="utf-8"))
        write_json(
            os.path.join(DERIVED, "split_validation.json"),
            {
                **payload,
                "static_image_ids_path": os.path.join(DERIVED, "static_image_ids.json"),
                "downstream_image_ids_path": os.path.join(DERIVED, "downstream_image_ids.json"),
                "intersection_must_be_empty": True,
            },
        )

    if run(
        [
            sys.executable,
            os.path.join(ROOT, "scripts", "build_gqa_static.py"),
            "--per-factor",
            str(args.per_factor),
        ]
    ) != 0:
        return 1
    if run(
        [
            sys.executable,
            os.path.join(ROOT, "scripts", "build_gqa_downstream.py"),
            "--per-factor",
            str(args.per_factor),
        ]
    ) != 0:
        return 1

    for name in (
        "gqa_factor_mapping.jsonl",
        "gqa_factor_mapping_report.json",
        "mapping_stats.csv",
        "gqa_static_manifest.jsonl",
        "gqa_downstream_manifest.jsonl",
        "static_image_ids.json",
        "downstream_image_ids.json",
        "split_validation.json",
        "natural_distractor_jobs.jsonl",
    ):
        copy_if(os.path.join(DERIVED, name), os.path.join(PROCESSED, name))

    qc_static = os.path.join(DERIVED, "candidate_pool_qc.json")
    qc_down = os.path.join(DERIVED, "candidate_pool_qc_downstream.json")
    run(
        [
            sys.executable,
            os.path.join(ROOT, "scripts", "candidate_shortcut_qc.py"),
            "--manifest",
            os.path.join(DERIVED, "gqa_static_manifest.jsonl"),
            "--out",
            qc_static,
            "--csv",
            os.path.join(DERIVED, "candidate_pool_qc.csv"),
        ]
    )
    run(
        [
            sys.executable,
            os.path.join(ROOT, "scripts", "candidate_shortcut_qc.py"),
            "--manifest",
            os.path.join(DERIVED, "gqa_downstream_manifest.jsonl"),
            "--out",
            qc_down,
            "--csv",
            os.path.join(DERIVED, "candidate_pool_qc_downstream.csv"),
        ]
    )

    ids_cmd = [
        sys.executable,
        os.path.join(ROOT, "scripts", "acquire_gqa_images.py"),
        "--ids-json",
        os.path.join(DERIVED, "required_gqa_image_ids.json"),
        "--inventory",
        os.path.join(DERIVED, "gqa_image_inventory.json"),
    ]
    if args.skip_images:
        ids_cmd.append("--dry-run")
    img_code = run(ids_cmd)
    relink_static_images(os.path.join(DERIVED, "gqa_static_manifest.jsonl"), os.path.join(GQA_DIR, "images"))
    copy_if(os.path.join(DERIVED, "required_gqa_image_ids.json"), os.path.join(PROCESSED, "required_gqa_image_ids.json"))
    copy_if(os.path.join(DERIVED, "gqa_image_inventory.json"), os.path.join(PROCESSED, "gqa_image_inventory.json"))
    print("GQA_FAST_PIPELINE_DONE", "images_status", img_code, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
