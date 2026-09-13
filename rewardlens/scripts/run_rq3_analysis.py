#!/usr/bin/env python3
"""RQ3 confirmatory analysis. Within-column standardize, then diagonal vs off-diagonal."""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from stats import FACTORS, factor_specificity  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", default=os.path.join(ROOT, "tests", "fixtures", "rq2_rq3_matrix.json"))
    parser.add_argument("--config", default=os.path.join(ROOT, "configs", "rq3_analysis.json"))
    parser.add_argument("--out", default=os.path.join(ROOT, "tests", "fixtures", "rq3_analysis_out.json"))
    parser.add_argument("--gqa-only-3factor", action="store_true")
    parser.add_argument("--allow-official", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out = os.path.abspath(args.out)
    if ("outputs" in out.replace("\\", "/").split("/")) and not args.allow_official:
        raise SystemExit("refusing to write RQ3 under outputs/ without --allow-official")
    with open(args.config, "r", encoding="utf-8") as handle:
        config = json.load(handle)
    with open(args.matrix, "r", encoding="utf-8") as handle:
        matrix = json.load(handle)
    if isinstance(matrix, dict):
        matrix = matrix.get("rows") or matrix.get("matrix") or []
    primary = factor_specificity(matrix)
    gqa_only = None
    if args.gqa_only_3factor or True:
        three = ("attribute", "spatial", "presence")
        sub = [r for r in matrix if r.get("audit_factor") in three and r.get("downstream_factor") in three]
        # Temporary 3x3 using the same function would still iterate FACTORS including count.
        # Build a local grid manually for sensitivity only.
        from stats import _mean, _zscore

        grid = {af: {df: None for df in three} for af in three}
        for row in sub:
            grid[str(row["audit_factor"])][str(row["downstream_factor"])] = float(row["score"])
        zgrid = {af: {df: None for df in three} for af in three}
        for df in three:
            col = [grid[af][df] for af in three]
            zcol = _zscore(col)
            for i, af in enumerate(three):
                zgrid[af][df] = zcol[i]
        zdiag = [zgrid[f][f] for f in three if zgrid[f][f] is not None]
        zoff = [zgrid[af][df] for af in three for df in three if af != df and zgrid[af][df] is not None]
        gqa_only = {
            "role": "sensitivity_only",
            "does_not_replace_primary_4factor": True,
            "factors": list(three),
            "column_standardized": {
                "diagonal_mean": _mean(zdiag),
                "off_diagonal_mean": _mean(zoff),
                "diagonal_minus_off": None if not zdiag or not zoff else _mean(zdiag) - _mean(zoff),
            },
        }
    result = {
        "config": config,
        "primary_4factor": primary,
        "confirmatory_summary": primary.get("column_standardized"),
        "gqa_only_3factor_sensitivity": gqa_only,
        "synthetic_or_fixture": not args.allow_official,
        "note": "Use column_standardized for confirmatory diagonal vs off-diagonal. Standardization does not remove Count=TallyQA vs GQA source confounding.",
    }
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps({"out": out, "confirmatory": result["confirmatory_summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
