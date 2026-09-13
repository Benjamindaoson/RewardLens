#!/usr/bin/env python3
"""Text-only candidate-pool QC. Never fabricates a model score."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.common import write_json  # noqa: E402
from lib.jsonl_io import read_jsonl  # noqa: E402


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", str(text).lower())


def check_item(item: dict) -> dict:
    flags = []
    gold = str(item.get("gold_answer") or item.get("gold") or item.get("answer") or "")
    ca = str(item.get("candidate_a") or "")
    cb = str(item.get("candidate_b") or "")
    if item.get("candidates"):
        texts = []
        for c in item["candidates"]:
            texts.append(c.get("text") if isinstance(c, dict) else c)
        if len(texts) != len(set(str(t).lower() for t in texts if t is not None)):
            flags.append("duplicate_candidates")
        if gold and gold.lower() not in {str(t).lower() for t in texts if t is not None}:
            flags.append("gold_missing_from_pool")
        gold_hits = [i for i, t in enumerate(texts) if t is not None and str(t).lower() == gold.lower()]
        if len(gold_hits) > 1:
            flags.append("gold_duplication")
        if item.get("gold_index") is not None:
            try:
                gi = int(item["gold_index"])
                if gi < 0 or gi >= len(texts) or str(texts[gi] or "").lower() != gold.lower():
                    flags.append("invalid_gold_index")
            except (TypeError, ValueError):
                flags.append("invalid_gold_index")
        n_expected = int(item.get("n_pool") or 0)
        n_filled = sum(1 for t in texts if t)
        if n_expected and n_filled != n_expected:
            flags.append("invalid_candidate_count")
        lengths = [len(str(t)) for t in texts if t]
        if lengths and max(lengths) - min(lengths) >= 12:
            flags.append("length_gap")
        punct = [bool(re.search(r"[.!?]$", str(t))) for t in texts if t]
        if any(punct) and not all(punct):
            flags.append("punctuation_asymmetry")
        if any(t is None or not str(t).strip() for t in texts):
            flags.append("empty_candidate")
    else:
        if ca.lower() == cb.lower():
            flags.append("duplicate_candidates")
        if abs(len(ca) - len(cb)) >= 12:
            flags.append("length_gap")
        if bool(re.search(r"[.!?]$", ca)) != bool(re.search(r"[.!?]$", cb)):
            flags.append("punctuation_asymmetry")
        if item.get("expected_preference") not in {"A", "B", None}:
            flags.append("invalid_preference_label")
        if gold and {ca.lower(), cb.lower()} == {gold.lower()}:
            flags.append("gold_duplication")
    return {"item_id": item.get("item_id") or item.get("question_id"), "factor": item.get("factor"), "flags": flags, "n_flags": len(flags)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--csv", default=None)
    parser.add_argument("--run-text-baseline", action="store_true")
    parser.add_argument("--text-model", default=None, help="Must exist; refuse to fake.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    items = read_jsonl(args.manifest)
    rows = [check_item(it) for it in items]
    answers = Counter(str(it.get("gold_answer") or it.get("gold") or it.get("answer") or "").lower() for it in items)
    factors = Counter(str(it.get("factor") or "") for it in items)
    a_first = 0
    n_pair = 0
    gold_positions = Counter()
    for it in items:
        if "candidate_a" in it and it.get("expected_preference"):
            n_pair += 1
            if it["expected_preference"] == "A":
                a_first += 1
        if it.get("gold_index") is not None:
            gold_positions[str(it["gold_index"])] += 1
        elif it.get("candidates"):
            gold = str(it.get("gold_answer") or it.get("gold") or "").lower()
            for i, c in enumerate(it["candidates"]):
                text = (c.get("text") if isinstance(c, dict) else c) or ""
                if str(text).lower() == gold:
                    gold_positions[str(i)] += 1
                    break
    report = {
        "n": len(items),
        "n_flagged": sum(r["n_flags"] > 0 for r in rows),
        "flag_counts": dict(Counter(flag for r in rows for flag in r["flags"])),
        "answer_frequency_head": answers.most_common(20),
        "factor_distribution": dict(factors),
        "gold_position_distribution": dict(gold_positions),
        "candidate_A_is_gold_rate": (a_first / n_pair) if n_pair else None,
        "items": rows,
        "text_only_baseline": None,
    }
    if args.run_text_baseline:
        if not args.text_model:
            report["text_only_baseline"] = {
                "status": "NOT_RUN",
                "reason": "no text model provided; refusing to fabricate baseline scores",
            }
        else:
            report["text_only_baseline"] = {
                "status": "NOT_RUN",
                "reason": "text model %s was named but this CPU host does not execute unofficial judges here"
                % args.text_model,
            }
    write_json(args.out, report)
    csv_path = args.csv or os.path.splitext(args.out)[0] + ".csv"
    os.makedirs(os.path.dirname(os.path.abspath(csv_path)) or ".", exist_ok=True)
    with open(csv_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["item_id", "factor", "n_flags", "flags"])
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "item_id": row["item_id"],
                    "factor": row.get("factor"),
                    "n_flags": row["n_flags"],
                    "flags": " | ".join(row["flags"]),
                }
            )
    print(json.dumps({k: report[k] for k in report if k != "items"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
