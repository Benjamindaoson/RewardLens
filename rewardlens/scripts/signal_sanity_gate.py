#!/usr/bin/env python3
"""Engineering sanity gate after signal-gate JSONL. Not a scientific-positive test."""

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
from lib.jsonl_io import read_jsonl  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-root", default=os.path.join(PROJECT, "outputs", "runs"))
    parser.add_argument("--out", default=os.path.join(PROJECT, "outputs", "signal_sanity_gate.json"))
    parser.add_argument("--min-parse-rate", type=float, default=0.80)
    parser.add_argument("--floor", type=float, default=0.05)
    parser.add_argument("--ceiling", type=float, default=0.95)
    return parser.parse_args()


def collect_signal_rows(runs_root: str) -> list[dict]:
    rows = []
    if not os.path.isdir(runs_root):
        return rows
    for root, _dirs, files in os.walk(runs_root):
        for name in files:
            if name in {"signal_gate.jsonl", "probe.jsonl"}:
                rows.extend(read_jsonl(os.path.join(root, name)))
    return rows


def main() -> int:
    args = parse_args()
    rows = collect_signal_rows(args.runs_root)
    by_model = {}
    for row in rows:
        by_model.setdefault(row.get("model_id") or "unknown", []).append(row)
    model_stats = {}
    reasons = []
    for model_id, items in by_model.items():
        n = len(items)
        n_ok = sum(1 for r in items if r.get("status") == "ok")
        parse_rate = n_ok / n if n else 0.0
        prefs = [r.get("parsed_preference") for r in items if r.get("status") == "ok"]
        a_rate = sum(1 for p in prefs if p == "A") / len(prefs) if prefs else None
        model_stats[model_id] = {"n": n, "parse_rate": parse_rate, "a_rate": a_rate}
        if parse_rate < args.min_parse_rate:
            reasons.append("%s parse_rate %.3f < %.3f" % (model_id, parse_rate, args.min_parse_rate))
    a_rates = [s["a_rate"] for s in model_stats.values() if s["a_rate"] is not None]
    if a_rates and all(r <= args.floor for r in a_rates):
        reasons.append("catastrophic floor: every model A-rate <= %.2f" % args.floor)
    if a_rates and all(r >= args.ceiling for r in a_rates):
        reasons.append("catastrophic ceiling: every model A-rate >= %.2f" % args.ceiling)
    payload = {
        "status": "PASS" if not reasons and model_stats else ("FAIL" if reasons else "WAITING"),
        "n_models": len(model_stats),
        "model_stats": model_stats,
        "reasons": reasons,
        "policy": "Engineering usability only. Hypothesis support is not required.",
    }
    write_json(args.out, payload)
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
