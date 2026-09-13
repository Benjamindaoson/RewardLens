#!/usr/bin/env python3
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
from lib.gqa_mapping import (  # noqa: E402
    find_gqa_question_files,
    find_scene_graph_files,
    load_questions_file,
    load_scene_graphs,
    map_corpus,
)
from lib.jsonl_io import write_jsonl  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gqa-dir", default=os.path.join(PROJECT, "datasets", "gqa"))
    parser.add_argument("--questions-json", action="append", dest="questions")
    parser.add_argument("--out-dir", default=os.path.join(PROJECT, "datasets", "gqa", "derived"))
    parser.add_argument("--max-items", type=int, default=0)
    parser.add_argument("--seed", type=int, default=20260912)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    qfiles = args.questions or find_gqa_question_files(args.gqa_dir)
    if not qfiles:
        print("NO_GQA_QUESTIONS", args.gqa_dir, flush=True)
        write_json(
            os.path.join(args.out_dir, "gqa_factor_mapping_report.json"),
            {"status": "MISSING_QUESTIONS", "gqa_dir": args.gqa_dir},
        )
        return 2
    scenes = load_scene_graphs(find_scene_graph_files(args.gqa_dir))
    all_mapped = []
    reports = []
    for path in qfiles:
        questions = load_questions_file(path)
        split_name = os.path.splitext(os.path.basename(path))[0]
        mapped, report = map_corpus(
            questions,
            scenes,
            split_name=split_name,
            max_items=args.max_items,
            seed=args.seed,
        )
        report["source"] = path
        reports.append(report)
        all_mapped.extend(mapped)
        print("MAPPED", path, "n", len(mapped), "counts", report["counts"], flush=True)

    out_jsonl = os.path.join(args.out_dir, "gqa_factor_mapping.jsonl")
    write_jsonl(out_jsonl, all_mapped)
    combined = {
        "n_mapped": len(all_mapped),
        "sources": reports,
        "counts": {},
        "human_qc_candidates": {},
    }
    from collections import Counter

    counts = Counter(r["factor"] for r in all_mapped)
    combined["counts"] = dict(counts)
    for report in reports:
        for factor, rows in (report.get("human_qc_candidates") or {}).items():
            combined["human_qc_candidates"].setdefault(factor, [])
            existing = {r["question_id"] for r in combined["human_qc_candidates"][factor]}
            for row in rows:
                if row["question_id"] not in existing and len(combined["human_qc_candidates"][factor]) < 50:
                    combined["human_qc_candidates"][factor].append(row)
    write_json(os.path.join(args.out_dir, "gqa_factor_mapping_report.json"), combined)
    import csv

    csv_path = os.path.join(args.out_dir, "mapping_stats.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["factor", "n"])
        for factor, n in sorted(combined["counts"].items()):
            writer.writerow([factor, n])
        writer.writerow(["mapped_total", combined["n_mapped"]])
    processed = os.path.join(PROJECT, "datasets", "processed", "gqa")
    os.makedirs(processed, exist_ok=True)
    for name in ("gqa_factor_mapping.jsonl", "gqa_factor_mapping_report.json", "mapping_stats.csv"):
        src = os.path.join(args.out_dir, name)
        if os.path.isfile(src):
            import shutil

            shutil.copy2(src, os.path.join(processed, name))
    print("WROTE", out_jsonl, "n", len(all_mapped), dict(counts), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
