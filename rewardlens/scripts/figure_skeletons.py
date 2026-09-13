#!/usr/bin/env python3
"""Figure 2-5 interfaces. Refuse official figures from missing/synthetic numbers.

When --schema-only, write empty CSV/LaTeX/Markdown shells with no fake values.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)


def require_real(path: str) -> dict:
    if not os.path.isfile(path):
        raise SystemExit("NO_REAL_RESULTS: %s missing. Refusing to invent Figure numbers." % path)
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if payload.get("synthetic") or payload.get("fixture"):
        raise SystemExit("NO_REAL_RESULTS: %s is marked synthetic/fixture" % path)
    return payload


def write_schema(out_base: str, columns: list[str]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(out_base)) or ".", exist_ok=True)
    csv_path = out_base + ".csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
    with open(out_base + ".md", "w", encoding="utf-8") as handle:
        handle.write("| " + " | ".join(columns) + " |\n")
        handle.write("| " + " | ".join(["---"] * len(columns)) + " |\n")
        handle.write("| " + " | ".join(["[TBD]"] * len(columns)) + " |\n")
    with open(out_base + ".tex", "w", encoding="utf-8") as handle:
        handle.write("% schema only; no fabricated numbers\n")
        handle.write("\\begin{tabular}{" + "c" * len(columns) + "}\n")
        handle.write(" & ".join(columns) + " \\\\\n")
        handle.write("\\end{tabular}\n")
    print("SCHEMA", csv_path)


def figure2(data_path: str, out_path: str) -> None:
    require_real(data_path)
    raise SystemExit("Figure 2 renderer is wired but real accuracy-matched pairs are not available yet.")


def figure3(data_path: str, out_path: str) -> None:
    require_real(data_path)
    raise SystemExit("Figure 3 renderer is wired but real model x factor scores are not available yet.")


def figure4(data_path: str, out_path: str) -> None:
    require_real(data_path)
    raise SystemExit("Figure 4 renderer is wired but real specificity matrix scores are not available yet.")


def figure5(data_path: str, out_path: str) -> None:
    require_real(data_path)
    raise SystemExit("Figure 5 renderer is wired but real incremental-validity scores are not available yet.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--figure", required=True, choices=["2", "3", "4", "5", "all-schema"])
    parser.add_argument("--data", default="")
    parser.add_argument("--out", required=True)
    parser.add_argument("--schema-only", action="store_true")
    args = parser.parse_args()
    schemas = {
        "2": ["model_a", "model_b", "factor", "delta_A_pp", "delta_PFC", "delta_PSC"],
        "3": ["model_id", "family", "factor", "A", "PFC", "PSC"],
        "4": ["audit_factor", "downstream_factor", "score"],
        "5": ["held_out_family", "M0_MAE", "M1_MAE", "delta", "spearman"],
    }
    if args.figure == "all-schema" or args.schema_only:
        for key, cols in schemas.items():
            write_schema(args.out + "_fig" + key, cols)
        return 0
    {
        "2": figure2,
        "3": figure3,
        "4": figure4,
        "5": figure5,
    }[args.figure](args.data, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
