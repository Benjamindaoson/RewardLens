"""Phase II V2 table assembly; estimators remain in stats."""

from __future__ import annotations

from typing import Any, Iterable

CARRIER_BY_FACTOR = {
    "count": "tallyqa",
    "attribute": "gqa",
    "presence": "gqa",
    "spatial": "gqa",
}


def _index(rows: Iterable[dict[str, Any]], fields: tuple[str, ...]) -> dict[tuple[str, str], dict[str, Any]]:
    out = {}
    for row in rows:
        key = (str(row.get("model_id")), str(row.get("factor")))
        if key in out:
            raise ValueError("duplicate %s row for %s" % ("/".join(fields), key))
        out[key] = row
    return out


def merge_primary_table(
    *,
    audit_rows: Iterable[dict[str, Any]],
    static_rows: Iterable[dict[str, Any]],
    utility_rows: Iterable[dict[str, Any]],
    families: dict[str, str],
) -> list[dict[str, Any]]:
    """Build the factor-wise primary N=8 RQ2 input table."""
    audit = _index(audit_rows, ("audit",))
    static = _index(static_rows, ("static",))
    utility = _index((r for r in utility_rows if int(r.get("N") or 0) == 8), ("utility",))
    keys = sorted(set(audit) | set(static) | set(utility))
    out = []
    for key in keys:
        if key not in audit or key not in static or key not in utility:
            raise ValueError("incomplete Phase II primary row for %s" % (key,))
        model_id, factor = key
        if factor not in CARRIER_BY_FACTOR:
            raise ValueError("unknown factor: %s" % factor)
        a, s, u = audit[key], static[key], utility[key]
        if model_id not in families:
            raise ValueError("model family missing: %s" % model_id)
        out.append(
            {
                "model_id": model_id,
                "family": families[model_id],
                "factor": factor,
                "dataset": CARRIER_BY_FACTOR[factor],
                "A": s["A"],
                "PFC": a["PFC"],
                "PSC": a["PSC"],
                "U": u["U"],
                "n_static": s["n"],
                "n_downstream": u["n_pools"],
                "primary_n": 8,
            }
        )
    return out
