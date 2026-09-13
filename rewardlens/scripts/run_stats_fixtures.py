#!/usr/bin/env python3
"""Run confirmatory statistics on synthetic fixtures. Never writes official outputs/ without --allow-official."""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from stats import accuracy_matched_pairs, cluster_bootstrap, factor_specificity, incremental_validity  # noqa: E402


def fixture_table() -> list[dict]:
    families = ["qwen_vl", "gemma", "molmo", "specialized_vl_reward"]
    a_vals = [0.62, 0.71, 0.64, 0.69, 0.58, 0.73, 0.60, 0.68]
    pfc_vals = [0.31, 0.55, 0.40, 0.22, 0.61, 0.48, 0.35, 0.52]
    psc_vals = [0.70, 0.44, 0.63, 0.58, 0.41, 0.66, 0.50, 0.47]
    u_vals = [0.51, 0.66, 0.57, 0.49, 0.63, 0.70, 0.54, 0.61]
    table = []
    n = 0
    for fam in families:
        for _k in range(2):
            table.append(
                {
                    "model_id": "m%d" % n,
                    "family": fam,
                    "factor": "count",
                    "A": a_vals[n],
                    "PFC": pfc_vals[n],
                    "PSC": psc_vals[n],
                    "U": u_vals[n],
                    "synthetic": True,
                }
            )
            n += 1
    return table


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=os.path.join(ROOT, "tests", "fixtures", "stats_run"))
    parser.add_argument("--allow-official", action="store_true")
    args = parser.parse_args()
    out_dir = os.path.abspath(args.out_dir)
    if ("outputs" in out_dir.replace("\\", "/").split("/")) and not args.allow_official:
        raise SystemExit("Refusing to write synthetic stats under outputs/ without --allow-official")
    os.makedirs(out_dir, exist_ok=True)
    table = fixture_table()
    pairs = accuracy_matched_pairs(table)
    inc = incremental_validity(table)
    matrix = []
    for af in ("count", "attribute", "presence", "spatial"):
        for df in ("count", "attribute", "presence", "spatial"):
            matrix.append({"audit_factor": af, "downstream_factor": df, "score": 0.8 if af == df else 0.2})
    spec = factor_specificity(matrix)
    boot = cluster_bootstrap(table, stat_fn=lambda rows: sum(r["U"] for r in rows) / len(rows), n_boot=50)
    payload = {
        "synthetic": True,
        "fixture": True,
        "note": "No scientific conclusion. Code-path verification only.",
        "accuracy_matched_pairs": pairs,
        "incremental_validity": inc,
        "factor_specificity": spec,
        "cluster_bootstrap": boot,
    }
    path = os.path.join(out_dir, "stats_fixture_report.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(json.dumps({"out": path, "n_families": inc.get("n_families"), "diag": spec.get("diagonal_mean"), "off": spec.get("off_diagonal_mean")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
