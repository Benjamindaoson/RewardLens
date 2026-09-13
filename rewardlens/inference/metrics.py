"""Audit metrics from pairwise judgments. Synthetic-safe; writes nothing itself."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable


def _pref(row: dict[str, Any]) -> str | None:
    pref = row.get("parsed_preference")
    if pref in {"A", "B"}:
        return pref
    return None


def group_triplets(rows: Iterable[dict[str, Any]]) -> dict[tuple[str, str], dict[str, dict[str, Any]]]:
    grouped: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        if row.get("status") != "ok":
            continue
        key = (str(row.get("model_id")), str(row.get("triplet_id")))
        grouped[key][str(row.get("variant"))] = row
    return grouped


def compute_audit_metrics(
    judgments: Iterable[dict[str, Any]],
    expected: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    """expected[triplet_id] = {base, relevant, irrelevant, factor}"""
    grouped = group_triplets(judgments)
    by_model_factor: dict[tuple[str, str], dict[str, list[int]]] = defaultdict(
        lambda: {
            "base_correct": [],
            "pfc": [],
            "psc": [],
            "pfc_cond": [],
            "psc_cond": [],
        }
    )
    for (model_id, triplet_id), variants in grouped.items():
        if not {"base", "relevant", "irrelevant"} <= set(variants):
            continue
        gold = expected.get(triplet_id)
        if not gold:
            continue
        factor = str(gold.get("factor") or variants["base"].get("factor"))
        base_pred = _pref(variants["base"])
        rel_pred = _pref(variants["relevant"])
        irr_pred = _pref(variants["irrelevant"])
        if None in (base_pred, rel_pred, irr_pred):
            continue
        base_ok = int(base_pred == gold["base"])
        rel_ok = int(rel_pred == gold["relevant"])
        irr_ok = int(irr_pred == gold["irrelevant"])
        # Frozen confirmatory definitions:
        # PFC = P(base correct AND relevant correct)
        # PSC = P(base correct AND irrelevant correct)
        # PFC_cond = P(relevant correct | base correct)
        # PSC_cond = P(irrelevant correct | base correct)
        pfc = int(base_ok and rel_ok)
        psc = int(base_ok and irr_ok)
        bucket = by_model_factor[(model_id, factor)]
        bucket["base_correct"].append(base_ok)
        bucket["pfc"].append(pfc)
        bucket["psc"].append(psc)
        if base_ok:
            bucket["pfc_cond"].append(rel_ok)
            bucket["psc_cond"].append(irr_ok)

    rows = []
    for (model_id, factor), bucket in sorted(by_model_factor.items()):
        n = len(bucket["pfc"])
        n_cond = len(bucket["pfc_cond"])
        mean = lambda xs: (sum(xs) / len(xs)) if xs else None
        rows.append(
            {
                "model_id": model_id,
                "factor": factor,
                "n": n,
                "n_cond": n_cond,
                "base_acc": mean(bucket["base_correct"]),
                "PFC": mean(bucket["pfc"]),
                "PSC": mean(bucket["psc"]),
                "PFC_cond": mean(bucket["pfc_cond"]),
                "PSC_cond": mean(bucket["psc_cond"]),
                "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases",
            }
        )
    return rows


def accuracy_from_static(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[int]] = defaultdict(list)
    for row in rows:
        if row.get("status") != "ok":
            continue
        pred = _pref(row)
        gold = row.get("expected_preference") or row.get("gold_preference")
        if pred is None or gold not in {"A", "B"}:
            continue
        grouped[(str(row.get("model_id")), str(row.get("factor")))].append(int(pred == gold))
    out = []
    for (model_id, factor), vals in sorted(grouped.items()):
        out.append(
            {
                "model_id": model_id,
                "factor": factor,
                "A": sum(vals) / len(vals) if vals else None,
                "n": len(vals),
            }
        )
    return out
