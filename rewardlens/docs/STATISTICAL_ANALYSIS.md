# Statistical Analysis

Confirmatory endpoints are in `CONFIRMATORY_ANALYSIS_PLAN.md`.

Independent variation is **model × factor**, not image count.

**PRE-RESULT DATA AVAILABILITY ADAPTATION (2026-09-12).** Count static/downstream are TallyQA; Attribute/Spatial/Presence are GQA. This is not a result-driven change. Do not pool raw downstream utility across those datasets.

## RQ1

- Scatter \(A_f\) vs PFC / PSC
- Accuracy-matched pairs at |ΔA| ≤ 1, 2, 3 pp **within factor**
- Model × factor heatmap
- Family-aware comparison

Count \(A\) is TallyQA-Static. Other factors use GQA-Static.

## RQ2

Primary, **separately for each downstream factor** \(f \in \{\mathrm{count},\mathrm{attribute},\mathrm{spatial},\mathrm{presence}\}\):

- Count outcome: TallyQA \(U_{\mathrm{count}}\)
- Attribute / Spatial / Presence outcomes: GQA \(U_f\)

- M0: \(U_f \sim A_f\)
- M1: \(U_f \sim A_f + \mathrm{PFC}_f + \mathrm{PSC}_f\)
- Leave-one-model-family-out MAE / RMSE / R² / rank correlation
- Family cluster bootstrap 95% CI on Δ

Do not treat in-sample R² as the confirmatory result.

Do **not** concatenate TallyQA Count rows with GQA rows into one \(U\sim A\) fit.

## RQ3

4×4 audit factor × downstream factor matrix. Within each downstream-factor **column**, the four audit profiles \(D_{\mathrm{count}}, D_{\mathrm{attribute}}, D_{\mathrm{spatial}}, D_{\mathrm{presence}}\) predict the **same** \(U_f\). That within-column comparison remains valid even though Count \(U\) and GQA \(U\) live on different datasets.

For the **final diagonal-vs-off-diagonal summary**, z-score (or equivalent standardize) the predictive contribution **within each downstream-factor column**, then aggregate. Do not compare raw TallyQA vs GQA utility scales.

Code: `stats.incremental_validity_factorwise`, `stats.factor_specificity` (`column_standardized`).

## Null policy

If M1 does not beat M0, report CI, power, model diversity, and downstream noise. Do not rephrase a weak null as a theorem.
