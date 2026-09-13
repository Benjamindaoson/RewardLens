#!/usr/bin/env python3
"""Deterministic merge of independent worker JSONL shards. Detect duplicate item_ids."""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.common import write_json  # noqa: E402
from lib.hashutil import sha256_file  # noqa: E402
from lib.jsonl_io import read_jsonl, write_jsonl  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--out-jsonl", required=True)
    parser.add_argument("--report", default=None)
    parser.add_argument("--fail-on-conflict", action="store_true")
    return parser.parse_args()


def merge_rows(paths: list[str]) -> tuple[list[dict], dict]:
    seen: dict[str, dict] = {}
    source: dict[str, str] = {}
    duplicates = []
    conflicts = []
    n_in = 0
    for path in paths:
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        for row in read_jsonl(path):
            n_in += 1
            item_id = str(row.get("item_id") or "")
            model_id = str(row.get("model_id") or "")
            key = "%s::%s" % (model_id, item_id)
            if key in seen:
                duplicates.append({"key": key, "first": source[key], "second": path})
                a = seen[key]
                if a.get("parsed_preference") != row.get("parsed_preference") or a.get("status") != row.get("status"):
                    conflicts.append({"key": key, "first": source[key], "second": path})
                continue
            seen[key] = row
            source[key] = path
    rows = [seen[k] for k in sorted(seen)]
    report = {
        "n_input_files": len(paths),
        "n_input_rows": n_in,
        "n_merged": len(rows),
        "n_duplicates": len(duplicates),
        "n_conflicts": len(conflicts),
        "duplicates": duplicates[:50],
        "conflicts": conflicts[:50],
        "inputs": paths,
    }
    return rows, report


def main() -> int:
    args = parse_args()
    rows, report = merge_rows(args.inputs)
    write_jsonl(args.out_jsonl, rows)
    report["out_jsonl"] = args.out_jsonl
    report["out_sha256"] = sha256_file(args.out_jsonl)
    report_path = args.report or (os.path.splitext(args.out_jsonl)[0] + "_merge_report.json")
    write_json(report_path, report)
    print(json.dumps({k: report[k] for k in report if k not in {"duplicates", "conflicts"}}, indent=2))
    if args.fail_on_conflict and report["n_conflicts"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
