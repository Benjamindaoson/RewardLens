"""Descriptive, conditional audit metrics and genuinely shared-support pairs."""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Any

from .protocol import assemble_triplets


def _correct(row: dict[str, Any]) -> bool:
    return row["prediction"] == row["gold"]


def audit_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str, str], list[dict[str, dict[str, Any]]]] = defaultdict(list)
    for (model, _), triplet in assemble_triplets(rows).items():
        b = triplet["base"]
        key = (model, b["split"], b["domain"], b["factor"], b["shift_type"])
        groups[key].append(triplet)

    result = []
    for (model, split, domain, factor, shift), ts in sorted(groups.items()):
        base_correct = [t for t in ts if _correct(t["base"])]
        denom = len(base_correct)
        result.append({
            "model_id": model,
            "model_family": ts[0]["base"]["model_family"],
            "split": split, "domain": domain, "factor": factor,
            "shift_type": shift,
            "n_triplets": len(ts), "n_base_correct": denom,
            "base_accuracy": denom / len(ts),
            "ra": (sum(_correct(t["relevant"]) for t in base_correct) / denom) if denom else None,
            "ii": (sum(_correct(t["irrelevant"]) for t in base_correct) / denom) if denom else None,
            "n_base_a": sum(t["base"]["gold"] == "A" for t in ts),
            "n_base_b": sum(t["base"]["gold"] == "B" for t in ts),
            "n_abstain": sum(
                t[v]["prediction"] == "ABSTAIN" for t in ts for v in ("base", "relevant", "irrelevant")
            ),
        })
    return result


def matched_pairs(rows: list[dict[str, Any]], *, tolerance: float = 0.01) -> list[dict[str, Any]]:
    """Compare judges matched *only* on independent static accuracy.

    Each input: model_id, split, domain, factor, accuracy (fraction), n_static.
    No audit results influence pair selection; use shared_support_gaps below
    only *after* freezing matched pairs.
    """
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for field in ("model_id", "split", "domain", "factor", "accuracy", "n_static"):
            if field not in row:
                raise ValueError(f"static score missing {field}")
        a = float(row["accuracy"])
        if not 0 <= a <= 1 or int(row["n_static"]) < 1:
            raise ValueError("bad static accuracy or denominator")
        groups[(str(row["split"]), str(row["domain"]), str(row["factor"]))].append(row)
    out = []
    for (split, domain, factor), model_rows in sorted(groups.items()):
        seen = set()
        for m in model_rows:
            if m["model_id"] in seen:
                raise ValueError(f"duplicate static score {m['model_id']} {domain}/{factor}")
            seen.add(m["model_id"])
        for a, b in combinations(sorted(model_rows, key=lambda r: r["model_id"]), 2):
            delta = abs(float(a["accuracy"]) - float(b["accuracy"]))
            if delta <= tolerance + 1e-12:
                out.append({"split": split, "domain": domain, "factor": factor,
                            "model_a": a["model_id"], "model_b": b["model_id"],
                            "delta_static_accuracy": delta})
    return out


def shared_support_gaps(observations: list[dict[str, Any]], pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compute RA/II on the *same* base-correct image triplets per judge pair.

    This avoids spurious gaps caused solely by different base-correct sets.
    Does not silently equate different audit domains or split assignments.
    """
    ts = assemble_triplets(observations)
    out = []
    for pair in pairs:
        a, b = pair["model_a"], pair["model_b"]
        subset = []
        for (model, tid), atrip in ts.items():
            if model != a or (b, tid) not in ts:
                continue
            btrip = ts[(b, tid)]
            base = atrip["base"]
            if (base["split"], base["domain"], base["factor"]) != (
                pair["split"], pair["domain"], pair["factor"]
            ):
                continue
            if _correct(atrip["base"]) and _correct(btrip["base"]):
                subset.append((atrip, btrip))
        n = len(subset)
        ra_a = sum(_correct(x["relevant"]) for x, _ in subset)
        ra_b = sum(_correct(y["relevant"]) for _, y in subset)
        ii_a = sum(_correct(x["irrelevant"]) for x, _ in subset)
        ii_b = sum(_correct(y["irrelevant"]) for _, y in subset)
        out.append({**pair, "n_shared_base_correct": n,
                    "ra_a_shared": ra_a / n if n else None,
                    "ra_b_shared": ra_b / n if n else None,
                    "ii_a_shared": ii_a / n if n else None,
                    "ii_b_shared": ii_b / n if n else None,
                    "delta_ra_shared": abs(ra_a - ra_b) / n if n else None,
                    "delta_ii_shared": abs(ii_a - ii_b) / n if n else None,
                    "only_a_relevant_correct": sum(_correct(x["relevant"]) and not _correct(y["relevant"]) for x, y in subset),
                    "only_b_relevant_correct": sum(_correct(y["relevant"]) and not _correct(x["relevant"]) for x, y in subset),
                    "both_relevant_correct": sum(_correct(x["relevant"]) and _correct(y["relevant"]) for x, y in subset)})
    return out
