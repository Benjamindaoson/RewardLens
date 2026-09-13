#!/usr/bin/env python3
"""Formal QC for one or more controlled-factor directories."""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.common import VARIANTS, load_json, make_contact_sheet, write_json  # noqa: E402
from lib.controlled_qc import qc_triplet  # noqa: E402
from lib.jsonl_io import read_jsonl, write_jsonl  # noqa: E402


def load_manifests(output_dir: str) -> list[dict]:
    path = os.path.join(output_dir, "pilot_manifest.jsonl")
    return read_jsonl(path)


def triplet_complete(output_dir: str, manifest: dict) -> bool:
    for variant in VARIANTS:
        if not os.path.isfile(os.path.join(output_dir, manifest[variant]["image"])):
            return False
        if not os.path.isfile(os.path.join(output_dir, manifest[variant]["scene"])):
            return False
    return True


def write_csv(path: str, rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fields = ["factor", "triplet_id", "status", "n_flags", "flags"]
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "factor": row["factor"],
                    "triplet_id": row["triplet_id"],
                    "status": row["status"],
                    "n_flags": len(row.get("flags") or []),
                    "flags": " | ".join(row.get("flags") or []),
                }
            )


def maybe_contact_sheet(output_dir: str, manifest: dict) -> str | None:
    image_ok = all(os.path.isfile(os.path.join(output_dir, manifest[v]["image"])) for v in VARIANTS)
    if not image_ok:
        return None
    spec = {
        "triplet_id": manifest["triplet_id"],
        "factor": manifest["factor"],
        "seed": manifest.get("seed"),
        "question": manifest.get("question"),
        "candidate_a": manifest.get("candidate_a"),
        "candidate_b": manifest.get("candidate_b"),
    }
    try:
        return make_contact_sheet(output_dir, spec, manifest)
    except Exception as exc:
        print("CONTACT_SHEET_SKIP", manifest["triplet_id"], exc, flush=True)
        return None


def qc_directory(output_dir: str, *, sample_pass: int, seed: int) -> dict:
    manifests = load_manifests(output_dir)
    rows = []
    incomplete = 0
    for manifest in manifests:
        if not triplet_complete(output_dir, manifest):
            incomplete += 1
            continue
        rows.append(qc_triplet(output_dir, manifest))
    summary = {
        "output_dir": output_dir,
        "n_manifest_rows": len(manifests),
        "n_incomplete": incomplete,
        "n_qc": len(rows),
        "PASS": sum(r["status"] == "PASS" for r in rows),
        "BORDERLINE": sum(r["status"] == "BORDERLINE" for r in rows),
        "FAIL": sum(r["status"] == "FAIL" for r in rows),
        "note": "FAIL/BORDERLINE rows are retained. Inference default uses PASS only.",
        "triplets": rows,
    }
    write_json(os.path.join(output_dir, "qc_report.json"), summary)
    write_csv(os.path.join(output_dir, "qc_summary.csv"), rows)
    bad = [r for r in rows if r["status"] != "PASS"]
    write_jsonl(os.path.join(output_dir, "badcases.jsonl"), bad)

    rng = random.Random(seed)
    pass_rows = [r for r in rows if r["status"] == "PASS"]
    rng.shuffle(pass_rows)
    sheet_dir = os.path.join(output_dir, "qc_contact_sheets")
    os.makedirs(sheet_dir, exist_ok=True)
    selected_ids = {r["triplet_id"] for r in pass_rows[:sample_pass]}
    selected_ids.update(r["triplet_id"] for r in bad)
    id_to_manifest = {m["triplet_id"]: m for m in manifests}
    written = []
    for tid in sorted(selected_ids):
        manifest = id_to_manifest.get(tid)
        if not manifest:
            continue
        path = maybe_contact_sheet(output_dir, manifest)
        if path:
            dest = os.path.join(sheet_dir, "%s_%s.png" % (next(r["status"] for r in rows if r["triplet_id"] == tid), tid))
            try:
                if os.path.abspath(path) != os.path.abspath(dest):
                    import shutil

                    shutil.copy2(path, dest)
            except Exception:
                dest = path
            written.append(dest)
    summary["qc_contact_sheets"] = written
    write_json(os.path.join(output_dir, "qc_report.json"), summary)
    print(
        "QC",
        output_dir,
        "complete",
        summary["n_qc"],
        "PASS",
        summary["PASS"],
        "BORDERLINE",
        summary["BORDERLINE"],
        "FAIL",
        summary["FAIL"],
        "incomplete",
        incomplete,
        flush=True,
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", action="append", dest="output_dirs")
    parser.add_argument("--sample-pass", type=int, default=12)
    parser.add_argument("--seed", type=int, default=20260912)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dirs = args.output_dirs or []
    if not dirs:
        raise SystemExit("pass --output-dir")
    reports = [qc_directory(os.path.abspath(d), sample_pass=args.sample_pass, seed=args.seed) for d in dirs]
    combined = {
        "n_dirs": len(reports),
        "PASS": sum(r["PASS"] for r in reports),
        "BORDERLINE": sum(r["BORDERLINE"] for r in reports),
        "FAIL": sum(r["FAIL"] for r in reports),
        "dirs": [
            {
                "output_dir": r["output_dir"],
                "PASS": r["PASS"],
                "BORDERLINE": r["BORDERLINE"],
                "FAIL": r["FAIL"],
                "n_qc": r["n_qc"],
                "n_incomplete": r["n_incomplete"],
            }
            for r in reports
        ],
    }
    print(json.dumps(combined, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
