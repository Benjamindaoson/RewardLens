#!/usr/bin/env python3
"""CLI wrappers around confirmatory stats. Refuse official-output writes of synthetic data."""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from inference.metrics import accuracy_from_static, compute_audit_metrics  # noqa: E402
from lib.jsonl_io import read_jsonl  # noqa: E402
from stats import (  # noqa: E402
    accuracy_matched_pairs,
    cluster_bootstrap,
    factor_specificity,
    incremental_validity,
    incremental_validity_factorwise,
)


def _guard_out(path: str, allow_official: bool) -> None:
    abspath = os.path.abspath(path)
    official = os.path.abspath(os.path.join(PROJECT, "outputs"))
    if abspath.startswith(official + os.sep) and not allow_official:
        raise SystemExit("refusing to write %s under outputs/ without --allow-official (protects against synthetic leakage)" % path)


def load_expected(path: str) -> dict:
    expected = {}
    for row in read_jsonl(path):
        tid = row["triplet_id"]
        expected.setdefault(tid, {"factor": row.get("factor")})
        if row.get("variant") in {"base", "relevant", "irrelevant"}:
            expected[tid][row["variant"]] = row["expected_preference"]
    return expected


def cmd_audit_metrics(args):
    _guard_out(args.out, args.allow_official)
    judgments = read_jsonl(args.judgments)
    expected = load_expected(args.expected)
    rows = compute_audit_metrics(judgments, expected)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2)
    print("WROTE", args.out, "n", len(rows))


def cmd_static_a(args):
    _guard_out(args.out, args.allow_official)
    rows = accuracy_from_static(read_jsonl(args.judgments))
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2)


def cmd_matched(args):
    _guard_out(args.out, args.allow_official)
    with open(args.table, "r", encoding="utf-8") as handle:
        table = json.load(handle)
    out = accuracy_matched_pairs(table)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=2)


def cmd_incremental(args):
    _guard_out(args.out, args.allow_official)
    with open(args.table, "r", encoding="utf-8") as handle:
        table = json.load(handle)
    factors = {str(r.get("factor")) for r in table if r.get("factor")}
    if len(factors) > 1:
        out = incremental_validity_factorwise(table)
    else:
        out = incremental_validity(table)
        out["note"] = "single-factor table; RQ2 remains U_f ~ A_f. Do not pool TallyQA Count U with GQA U."
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=2)


def cmd_specificity(args):
    _guard_out(args.out, args.allow_official)
    with open(args.table, "r", encoding="utf-8") as handle:
        table = json.load(handle)
    out = factor_specificity(table)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=2)


def cmd_bootstrap(args):
    _guard_out(args.out, args.allow_official)
    with open(args.table, "r", encoding="utf-8") as handle:
        table = json.load(handle)
    key = args.stat_key
    out = cluster_bootstrap(table, stat_fn=lambda rows: sum(float(r[key]) for r in rows) / len(rows), n_boot=args.n_boot)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-official", action="store_true")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("audit-metrics")
    p.add_argument("--judgments", required=True)
    p.add_argument("--expected", required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("static-A")
    p.add_argument("--judgments", required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("matched-pairs")
    p.add_argument("--table", required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("incremental")
    p.add_argument("--table", required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("specificity")
    p.add_argument("--table", required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("bootstrap")
    p.add_argument("--table", required=True)
    p.add_argument("--stat-key", default="U")
    p.add_argument("--n-boot", type=int, default=200)
    p.add_argument("--out", required=True)

    args = parser.parse_args()
    {
        "audit-metrics": cmd_audit_metrics,
        "static-A": cmd_static_a,
        "matched-pairs": cmd_matched,
        "incremental": cmd_incremental,
        "specificity": cmd_specificity,
        "bootstrap": cmd_bootstrap,
    }[args.cmd](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
