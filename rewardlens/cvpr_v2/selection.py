"""Cost-aware, held-out judge-selection evaluation (not a trained policy)."""
from __future__ import annotations

from collections import defaultdict
from typing import Any
import math

FIELDS = (
    "task_id", "domain", "shift_type", "split", "model_id",
    "static_accuracy", "predicted_ood_utility", "true_ood_utility",
    "inference_cost", "static_audit_cost", "counterfactual_audit_cost",
)


def selection_regret(records: list[dict[str, Any]], *, budget: float) -> dict[str, Any]:
    """Evaluate two policies with genuinely policy-specific costs.

    true_ood_utility scores choices AFTER ranking by predictor/static features.
    Both policy budgets are the same; audit costs include amortized overhead.
    External split receipts must verify predictor independence from test data.
    """
    if not math.isfinite(budget) or budget <= 0:
        raise ValueError("budget must be finite and positive")
    groups = defaultdict(list)
    for r in records:
        for f in FIELDS:
            if f not in r:
                raise ValueError(f"selection record missing {f}")
        if r["split"] != "test":
            raise ValueError("selection only accepts held-out test rows")
        for f in ("static_accuracy", "predicted_ood_utility", "true_ood_utility",
                  "inference_cost", "static_audit_cost", "counterfactual_audit_cost"):
            if not math.isfinite(float(r[f])):
                raise ValueError(f"non-finite {f}")
        if any(float(r[f]) < 0 for f in ("inference_cost", "static_audit_cost", "counterfactual_audit_cost")):
            raise ValueError("costs must be non-negative")
        if not 0 <= float(r["static_accuracy"]) <= 1:
            raise ValueError("static accuracy must be between zero and one")
        groups[(str(r["task_id"]), str(r["domain"]), str(r["shift_type"]))].append(r)
    if not groups:
        raise ValueError("no task rows")

    def choose(rows, score_key, extra_cost):
        eligible = [r for r in rows if float(r["inference_cost"]) + float(r[extra_cost]) <= budget]
        if not eligible:
            return None
        return max(eligible, key=lambda r: (float(r[score_key]),
            -(float(r["inference_cost"]) + float(r[extra_cost])), str(r["model_id"])))

    task_results = []
    for (task, domain, shift), items in sorted(groups.items()):
        ids = [str(r["model_id"]) for r in items]
        if len(set(ids)) != len(ids):
            raise ValueError(f"duplicate model in held-out task {task}")
        static = choose(items, "static_accuracy", "static_audit_cost")
        cf = choose(items, "predicted_ood_utility", "counterfactual_audit_cost")
        if static is None or cf is None:
            raise ValueError(f"no feasible judge for one strategy in task {task}")
        feasible_any = [r for r in items if
            min(float(r["inference_cost"]) + float(r["static_audit_cost"]),
                float(r["inference_cost"]) + float(r["counterfactual_audit_cost"])) <= budget]
        oracle = max(float(r["true_ood_utility"]) for r in feasible_any)
        task_results.append({
            "task_id": task, "domain": domain, "shift_type": shift,
            "n_candidates": len(items), "budget": budget,
            "static_selected": static["model_id"], "cf_selected": cf["model_id"],
            "static_utility": float(static["true_ood_utility"]),
            "cf_utility": float(cf["true_ood_utility"]),
            "static_cost": float(static["inference_cost"]) + float(static["static_audit_cost"]),
            "cf_cost": float(cf["inference_cost"]) + float(cf["counterfactual_audit_cost"]),
            "oracle_utility_union_feasible": oracle,
            "static_regret": oracle - float(static["true_ood_utility"]),
            "cf_regret": oracle - float(cf["true_ood_utility"]),
            "regret_improvement": float(cf["true_ood_utility"]) - float(static["true_ood_utility"]),
        })
    n = len(task_results)
    return {
        "n_tasks": n, "budget": budget,
        "mean_static_regret": sum(r["static_regret"] for r in task_results) / n,
        "mean_cf_regret": sum(r["cf_regret"] for r in task_results) / n,
        "mean_regret_improvement": sum(r["regret_improvement"] for r in task_results) / n,
        "cf_wins": sum(r["regret_improvement"] > 0 for r in task_results),
        "cf_losses": sum(r["regret_improvement"] < 0 for r in task_results),
        "ties": sum(r["regret_improvement"] == 0 for r in task_results),
        "caution": "descriptive policy evaluation; held-out provenance and costs require external verification",
        "tasks": task_results,
    }
