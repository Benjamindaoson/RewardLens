"""Confirmatory statistics. Operate on in-memory tables only.

Never write synthetic numbers into official outputs/.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

import math


FACTORS = ("count", "attribute", "presence", "spatial")


def _mean(xs: list[float]) -> float | None:
    return sum(xs) / len(xs) if xs else None


def _fit_ols(y: list[float], columns: list[list[float]]) -> dict[str, Any]:
    """Ordinary least squares with intercept. Pure Python, no extra deps."""
    n = len(y)
    k = len(columns) + 1
    xs = [[1.0] + [col[i] for col in columns] for i in range(n)]
    xtx = [[0.0] * k for _ in range(k)]
    xty = [0.0] * k
    for i in range(n):
        for a in range(k):
            xty[a] += xs[i][a] * y[i]
            for b in range(k):
                xtx[a][b] += xs[i][a] * xs[i][b]
    beta = _solve(xtx, xty)
    fitted = [sum(beta[j] * xs[i][j] for j in range(k)) for i in range(n)]
    resid = [y[i] - fitted[i] for i in range(n)]
    mae = sum(abs(r) for r in resid) / n
    rmse = math.sqrt(sum(r * r for r in resid) / n)
    y_mean = sum(y) / n
    ss_tot = sum((yi - y_mean) ** 2 for yi in y)
    ss_res = sum(r * r for r in resid)
    r2 = None if ss_tot == 0 else 1.0 - ss_res / ss_tot
    return {"beta": beta, "mae": mae, "rmse": rmse, "r2": r2, "n": n}


def _solve(a: list[list[float]], b: list[float]) -> list[float]:
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for i in range(n):
        pivot = i
        for r in range(i + 1, n):
            if abs(m[r][i]) > abs(m[pivot][i]):
                pivot = r
        m[i], m[pivot] = m[pivot], m[i]
        if abs(m[i][i]) < 1e-12:
            raise ValueError("singular matrix")
        div = m[i][i]
        for c in range(i, n + 1):
            m[i][c] /= div
        for r in range(n):
            if r == i:
                continue
            factor = m[r][i]
            for c in range(i, n + 1):
                m[r][c] -= factor * m[i][c]
    return [row[-1] for row in m]


def accuracy_matched_pairs(
    rows: list[dict[str, Any]],
    *,
    a_key: str = "A",
    dep_keys: tuple[str, ...] = ("PFC", "PSC"),
    thresholds_pp: tuple[float, ...] = (1.0, 2.0, 3.0),
) -> dict[str, Any]:
    by_factor: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_factor[str(row["factor"])].append(row)
    out = {}
    for factor, items in by_factor.items():
        pairs = []
        for i, a in enumerate(items):
            for b in items[i + 1 :]:
                if a["model_id"] == b["model_id"]:
                    continue
                delta_a = abs(float(a[a_key]) - float(b[a_key])) * 100.0
                rec = {
                    "model_a": a["model_id"],
                    "model_b": b["model_id"],
                    "delta_A_pp": delta_a,
                    "factor": factor,
                }
                for key in dep_keys:
                    rec["delta_%s" % key] = float(a[key]) - float(b[key])
                pairs.append(rec)
        bands = {}
        for thr in thresholds_pp:
            selected = [p for p in pairs if p["delta_A_pp"] <= thr]
            bands[str(thr)] = {
                "n_pairs": len(selected),
                "mean_abs_delta_PFC": _mean([abs(p["delta_PFC"]) for p in selected]) if selected else None,
                "mean_abs_delta_PSC": _mean([abs(p["delta_PSC"]) for p in selected]) if selected else None,
            }
        out[factor] = {"n_models": len(items), "bands": bands}
    return out


def incremental_validity_factorwise(
    rows: list[dict[str, Any]],
    *,
    family_key: str = "family",
    u_key: str = "U",
    a_key: str = "A",
    factor_key: str = "factor",
) -> dict[str, Any]:
    """Fit U_f ~ A_f separately. Do not pool raw TallyQA Count U with GQA U."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    datasets: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        factor = str(row.get(factor_key) or row.get("downstream_factor") or "unknown")
        grouped[factor].append(row)
        if row.get("dataset"):
            datasets[factor].add(str(row["dataset"]))
    by_factor = {}
    for factor in FACTORS:
        if factor not in grouped:
            continue
        by_factor[factor] = incremental_validity(
            grouped[factor],
            family_key=family_key,
            u_key=u_key,
            a_key=a_key,
        )
        by_factor[factor]["n_rows"] = len(grouped[factor])
        by_factor[factor]["datasets"] = sorted(datasets.get(factor) or [])
    return {
        "by_factor": by_factor,
        "do_not_pool_raw_U": True,
        "outcome_datasets": {
            "count": "tallyqa",
            "attribute": "gqa",
            "spatial": "gqa",
            "presence": "gqa",
        },
        "note": "RQ2 is factor-wise. Count utility is TallyQA; Attribute/Spatial/Presence utility is GQA. Raw U is not pooled.",
    }


def incremental_validity(
    rows: list[dict[str, Any]],
    *,
    family_key: str = "family",
    u_key: str = "U",
    a_key: str = "A",
) -> dict[str, Any]:
    families = sorted({str(r[family_key]) for r in rows})
    lofo = []
    for held in families:
        train = [r for r in rows if str(r[family_key]) != held]
        test = [r for r in rows if str(r[family_key]) == held]
        if len(train) < 3 or not test:
            continue
        y_train = [float(r[u_key]) for r in train]
        a_train = [float(r[a_key]) for r in train]
        pfc_train = [float(r["PFC"]) for r in train]
        psc_train = [float(r["PSC"]) for r in train]
        try:
            m0 = _fit_ols(y_train, [a_train])
            m1 = _fit_ols(y_train, [a_train, pfc_train, psc_train])
        except ValueError as exc:
            lofo.append(
                {
                    "held_out_family": held,
                    "n_train": len(train),
                    "n_test": len(test),
                    "skipped": True,
                    "reason": str(exc),
                    "note": "fold skipped; confirmatory still factor-wise LOFO, not a pooled fit",
                }
            )
            continue

        def predict(beta, row, cols):
            vals = [1.0] + [float(row[c]) for c in cols]
            return sum(beta[i] * vals[i] for i in range(len(beta)))

        def metrics(beta, cols):
            preds = [predict(beta, r, cols) for r in test]
            y = [float(r[u_key]) for r in test]
            mae = sum(abs(preds[i] - y[i]) for i in range(len(y))) / len(y)
            rmse = math.sqrt(sum((preds[i] - y[i]) ** 2 for i in range(len(y))) / len(y))
            return {"mae": mae, "rmse": rmse}

        m0_test = metrics(m0["beta"], [a_key])
        m1_test = metrics(m1["beta"], [a_key, "PFC", "PSC"])
        lofo.append(
            {
                "held_out_family": held,
                "n_train": len(train),
                "n_test": len(test),
                "M0_test": m0_test,
                "M1_test": m1_test,
                "delta_mae": m0_test["mae"] - m1_test["mae"],
                "delta_rmse": m0_test["rmse"] - m1_test["rmse"],
                "M0_in_sample_r2": m0["r2"],
                "M1_in_sample_r2": m1["r2"],
                "note": "in-sample R2 is diagnostic only; confirmatory is LOFO",
            }
        )
    return {"leave_one_family_out": lofo, "n_families": len(families)}


def _zscore(xs: list[float | None]) -> list[float | None]:
    vals = [x for x in xs if x is not None]
    if not vals:
        return list(xs)
    mu = sum(vals) / len(vals)
    var = sum((x - mu) ** 2 for x in vals) / len(vals)
    sd = math.sqrt(var) if var > 0 else 1.0
    return [None if x is None else (x - mu) / sd for x in xs]


def factor_specificity(matrix_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """matrix_rows: audit_factor, downstream_factor, score

    Confirmatory diagonal-vs-off-diagonal summary uses scores standardized
    within each downstream-factor column so TallyQA Count U and GQA U are
    not compared on raw utility scales.
    """
    diag = []
    off = []
    grid = {af: {df: None for df in FACTORS} for af in FACTORS}
    for row in matrix_rows:
        af, df = str(row["audit_factor"]), str(row["downstream_factor"])
        score = float(row["score"])
        if af in grid and df in grid[af]:
            grid[af][df] = score
        if af == df:
            diag.append(score)
        else:
            off.append(score)
    zgrid = {af: {df: None for df in FACTORS} for af in FACTORS}
    for df in FACTORS:
        col = [grid[af][df] for af in FACTORS]
        zcol = _zscore(col)
        for i, af in enumerate(FACTORS):
            zgrid[af][df] = zcol[i]
    zdiag = [zgrid[f][f] for f in FACTORS if zgrid[f][f] is not None]
    zoff = [zgrid[af][df] for af in FACTORS for df in FACTORS if af != df and zgrid[af][df] is not None]
    return {
        "matrix": grid,
        "column_standardized_matrix": zgrid,
        "diagonal_mean": _mean(diag),
        "off_diagonal_mean": _mean(off),
        "diagonal_minus_off": None if not diag or not off else _mean(diag) - _mean(off),
        "n_diagonal": len(diag),
        "n_off_diagonal": len(off),
        "column_standardized": {
            "diagonal_mean": _mean(zdiag),
            "off_diagonal_mean": _mean(zoff),
            "diagonal_minus_off": None if not zdiag or not zoff else _mean(zdiag) - _mean(zoff),
            "note": "Use this summary for confirmatory diagonal vs off-diagonal. Within-column z-score before aggregation.",
        },
        "confirmatory_summary": "column_standardized",
        "do_not_compare_raw_tallyqa_and_gqa_U": True,
    }


def cluster_bootstrap(
    rows: list[dict[str, Any]],
    *,
    family_key: str = "family",
    stat_fn=None,
    n_boot: int = 1000,
    seed: int = 20260912,
) -> dict[str, Any]:
    import random

    if stat_fn is None:
        raise ValueError("stat_fn required")
    rng = random.Random(seed)
    families = sorted({str(r[family_key]) for r in rows})
    grouped = {fam: [r for r in rows if str(r[family_key]) == fam] for fam in families}
    observed = stat_fn(rows)
    samples = []
    for _ in range(n_boot):
        drawn = []
        for fam in rng.choices(families, k=len(families)):
            drawn.extend(grouped[fam])
        samples.append(stat_fn(drawn))
    samples_sorted = sorted(samples)
    lo = samples_sorted[int(0.025 * n_boot)]
    hi = samples_sorted[min(n_boot - 1, int(0.975 * n_boot))]
    return {
        "observed": observed,
        "ci95": [lo, hi],
        "n_boot": n_boot,
        "n_families": len(families),
        "unit": "model_family",
    }
