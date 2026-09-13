# Data-source confound note

**Logged before GPU results. Not result-driven.**

## Frozen assignment

| Factor | Static / downstream source |
|---|---|
| Count | TallyQA |
| Attribute | GQA |
| Spatial | GQA |
| Presence | GQA |

GQA Count remains **N=0**. No GQA Count mapping was invented. Count moved to TallyQA as a **PRE-RESULT DATA AVAILABILITY ADAPTATION**.

## Confound

On Count, **factor identity and dataset source co-vary**. Attribute, Spatial, and Presence share GQA; Count does not.

RQ2 remains factor-wise: `U_f ~ A_f` vs `U_f ~ A_f + PFC_f + PSC_f`. That does not remove the Count/TallyQA vs GQA source difference.

RQ3 compares four `D` predictors within each `U_f` column, then z-scores within column before aggregating diagonal vs off-diagonal. **Within-column standardization does not eliminate this dataset-source confound.** It only stops raw TallyQA and GQA utility scales from being compared directly.

Do not claim that standardization makes Count comparable to GQA as if they were the same dataset.

## Primary plan (unchanged)

The confirmatory 4-factor matrix stays primary. Count is not dropped.

## Pre-registered supplementary sensitivity (not a substitute)

**GQA-only 3-factor sensitivity:** Attribute, Spatial, Presence only (drop Count). Role: sensitivity. Does **not** replace the primary 4-factor analysis. Pre-registered now, before GPU scores exist. Whether the 3-factor pattern agrees with the 4-factor pattern will be reported; the decision to run it is not deferred until after seeing results.

Code: `scripts/run_rq3_analysis.py` emits `gqa_only_3factor_sensitivity` alongside the primary 4-factor summary.
