"""Self-contained HTML summary for visually auditing real CVPR-V2 results."""
from __future__ import annotations

from html import escape
from typing import Any


def render_html(payload: dict[str, Any]) -> str:
    summary = payload.get("audit", [])
    matched = payload.get("matched_pairs", [])
    def cell(value: Any) -> str:
        if value is None:
            return "—"
        if isinstance(value, float):
            return f"{value:.4f}"
        return escape(str(value))
    def table(records: list[dict[str, Any]], fields: list[str]) -> str:
        if not records:
            return '<p class="note">No records supplied.</p>'
        headers = "".join(f"<th>{escape(k)}</th>" for k in fields)
        trs = "".join("<tr>" + "".join(f"<td>{cell(r.get(k))}</td>" for k in fields) + "</tr>" for r in records)
        return f'<div class="overflow"><table><thead><tr>{headers}</tr></thead><tbody>{trs}</tbody></table></div>'
    audit_fields = ["model_id", "split", "domain", "factor", "shift_type", "n_triplets", "base_accuracy", "ra", "ii", "n_base_a", "n_base_b", "n_abstain"]
    pair_fields = ["split", "domain", "factor", "model_a", "model_b", "delta_static_accuracy", "n_shared_base_correct", "delta_ra_shared", "delta_ii_shared", "only_a_relevant_correct", "only_b_relevant_correct", "both_relevant_correct"]
    pred = payload.get("predictive")
    pred_html = '<p class="note">Not evaluated.</p>'
    if pred is not None:
        pred_html = (f'<p>Family-macro baseline MAE: <strong>{cell(pred["mae_baseline"])}</strong>; '
                     f'counterfactual MAE: <strong>{cell(pred["mae_counterfactual"])}</strong>; '
                     f'ΔMAE: <strong>{cell(pred["delta_mae"])}</strong>. Descriptive only.</p>'
                     + table(pred["family_results"], ["family", "n_outcomes", "mae_baseline", "mae_counterfactual", "delta_mae"]))
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>RewardLens CVPR V2 — Evidence Audit</title><style>
:root{font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#202936;background:#f6f8fc}
body{max-width:1150px;margin:36px auto;padding:0 20px}h1{font-size:30px}h2{font-size:20px;margin-top:35px}
section{background:white;border:1px solid #dde4ed;border-radius:13px;padding:20px;margin:18px 0;box-shadow:0 2px 10px #22334b09}
small,.note{color:#607080}table{border-collapse:collapse;width:100%;font-size:12px}th,td{border-bottom:1px solid #e5eaf0;padding:11px 8px;text-align:left;white-space:nowrap}
th{background:#f1f5fa;position:sticky;top:0}tr:hover td{background:#f8fafc}.overflow{overflow-x:auto}
.warning{border-left:4px solid #d59b42;padding-left:15px;background:#fff8ea;border-radius:5px}</style>
<h1>RewardLens CVPR V2</h1><p>Reproducible visual counterfactual evaluation · prototype audit report</p>
<div class="warning"><p><strong>Important:</strong> Schema validation is not human perceptual validation. These metrics do not prove novelty, model improvement or CVPR readiness. Demo inputs are synthetic, not research findings.</p></div>
<section><h2>Conditional intervention metrics</h2>''' + table(summary, audit_fields) + '''</section>
<section><h2>Independently static-score-matched judges · shared support</h2>''' + table(matched, pair_fields) + '''</section>
<section><h2>Held-out shift-loss prediction</h2>''' + pred_html + '''</section>
<p class="note">A/B label imbalance and provenance must be checked before drawing conclusions. See docs/cvpr/UPGRADE_PROTOCOL.md.</p></html>'''
