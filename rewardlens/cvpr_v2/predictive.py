"""Small-N-aware, family-held-out test of incremental shift prediction.

This is an *evaluation harness*, not evidence that the proposed method works.
Performance claims require independent, real model-level results with adequate
numbers of families and shifts. The target shift_loss must never be a feature.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

BASE_FEATURES = ("static_accuracy", "in_distribution_utility")
ADDITIONAL_FEATURES = ("ra", "ii")


def compare_predictors(records: list[dict[str, Any]], *, ridge_alpha: float = 1.0) -> dict[str, Any]:
    """Frozen leave-one-model-family-out (LOFO) ridge comparison.

    M0 and M1 use identical samples, folds, scaling and regularization.
    Only M1 has access to counterfactual features.
    """
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("predictive evaluation requires numpy") from exc
    fields = ("model_id", "model_family", "domain", "shift_type", "shift_loss") + BASE_FEATURES + ADDITIONAL_FEATURES
    if not records:
        raise ValueError("no predictive records")
    for r in records:
        missing = [k for k in fields if k not in r]
        if missing:
            raise ValueError(f"missing predictive fields: {missing}")
        for key in ("shift_loss",) + BASE_FEATURES + ADDITIONAL_FEATURES:
            if not np.isfinite(float(r[key])):
                raise ValueError(f"non-finite {key}")
    families = sorted(set(str(r["model_family"]) for r in records))
    if len(families) < 4:
        raise ValueError("at least four distinct families required for LOFO sanity check")
    if ridge_alpha <= 0:
        raise ValueError("ridge_alpha must be positive")

    def fit_predict(train: list[dict[str, Any]], test: list[dict[str, Any]], features: tuple[str, ...]) -> list[float]:
        x = np.array([[float(r[k]) for k in features] for r in train])
        z = np.array([[float(r[k]) for k in features] for r in test])
        y = np.array([float(r["shift_loss"]) for r in train])
        mean, std = x.mean(axis=0), x.std(axis=0)
        std[std < 1e-12] = 1.0
        x = (x - mean) / std
        z = (z - mean) / std
        x = np.column_stack([np.ones(len(train)), x])
        z = np.column_stack([np.ones(len(test)), z])
        penalty = np.diag([0.0] + [ridge_alpha] * len(features))
        coefs = np.linalg.solve(x.T @ x + penalty, x.T @ y)
        return [float(v) for v in z @ coefs]

    out = []
    for family in families:
        train = [r for r in records if str(r["model_family"]) != family]
        test = [r for r in records if str(r["model_family"]) == family]
        if not train or not test:
            raise ValueError("empty train/test family fold")
        p0 = fit_predict(train, test, BASE_FEATURES)
        p1 = fit_predict(train, test, BASE_FEATURES + ADDITIONAL_FEATURES)
        for r, b, v in zip(test, p0, p1):
            target = float(r["shift_loss"])
            out.append({"model_id": r["model_id"], "model_family": family,
                        "domain": r["domain"], "shift_type": r["shift_type"],
                        "target_shift_loss": target, "baseline_prediction": b,
                        "counterfactual_prediction": v,
                        "baseline_absolute_error": abs(target - b),
                        "counterfactual_absolute_error": abs(target - v)})
    by_family = defaultdict(list)
    for r in out:
        by_family[r["model_family"]].append(r)
    family_summary = []
    for family, rr in sorted(by_family.items()):
        b = sum(x["baseline_absolute_error"] for x in rr) / len(rr)
        c = sum(x["counterfactual_absolute_error"] for x in rr) / len(rr)
        family_summary.append({"family": family, "n_outcomes": len(rr),
                               "mae_baseline": b, "mae_counterfactual": c,
                               "delta_mae": b - c})
    macro_b = sum(r["mae_baseline"] for r in family_summary) / len(family_summary)
    macro_c = sum(r["mae_counterfactual"] for r in family_summary) / len(family_summary)
    return {"protocol": "LOFO ridge, train-only standardization, family macro average",
            "n_families": len(families), "n_outcomes": len(records),
            "ridge_alpha": ridge_alpha, "baseline_features": BASE_FEATURES,
            "additional_features": ADDITIONAL_FEATURES,
            "mae_baseline": macro_b, "mae_counterfactual": macro_c,
            "delta_mae": macro_b - macro_c,
            "conclusion": "descriptive only; no significance or generalization claim",
            "family_results": family_summary, "held_out_predictions": out}
