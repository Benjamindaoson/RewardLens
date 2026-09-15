# RQ3 Implementation Audit (017 independent re-audit)

RQ3_IMPLEMENTATION_AUDIT = BUG_FOUND
RQ3_REVISED_STATUS = INSUFFICIENT_EVIDENCE_NOT_IDENTIFIABLE_FOR_FOUR_MODELS

The bug is in the unofficial saturated in-sample estimator that produced
diagonal mean ≈ 0.057250688864041444 and off-diagonal mean ≈ 0.057250688862794975
(difference ≈ 1.25e-12). That number is not a scientific null.

The frozen confirmatory protocol already refuses to estimate the four-model
matrix. This audit does not replace that protocol.

## Checklist

| Item | Result |
| --- | --- |
| 1. Each 4×4 cell uses a distinct dependency factor in the *inputs* | PASS |
| 2. Each column uses factor-specific downstream utility (A_df, U8_df) | PASS |
| 3. Macro A/PFC/PSC/U8 reused as the cell score | PASS (not reused in inputs) |
| 4. Row/column indexing | PASS (16 cells × 4 models = 64 input rows; 4 diagonal cells; 12 off-diagonal cells) |
| 5. Column standardization erased factor information | PASS (not the cause; the 0.057 numbers are raw in-sample delta RMSE, not z-scores) |
| 6. Diagonal is 4 cells | PASS |
| 7. Off-diagonal is 12 cells | PASS |
| 8. Broadcast / repeated-scalar in the *contribution matrix* | BUG_FOUND |

## What the 0.057 equality actually is

Preserved unofficial artifact:
`/root/autodl-fs/RewardLens/results/phase2/four_model_paper_checkpoint/four_model_rq3.json`

That file fits, for every cell (audit factor af, downstream factor df):

- M0: U_df ~ A_df, n=4, in-sample
- M1: U_df ~ A_df + PFC_af + PSC_af, n=4, in-sample
- contribution = delta_RMSE = RMSE(M0) − RMSE(M1)

M1 has four parameters (intercept, A, PFC, PSC) and four observations.
It interpolates. M1 RMSE is ~1e-13 to ~1e-11 in every cell, so

contribution(af, df) ≈ RMSE(M0_df)

M0 does not use PFC_af or PSC_af. Therefore every row in a column is the
same scalar, up to floating-point noise:

- count column ≈ 0.020389645509
- attribute column ≈ 0.014894378309
- presence column ≈ 0.091017840075
- spatial column ≈ 0.102700891564

For any column-constant 4×4 matrix, the mean of the 4 diagonal cells equals
the mean of the 12 off-diagonal cells. That identity is why the two reported
means agree to ~1e-12. It is not evidence that factor-specific dependency is
absent.

PFC/PSC *inputs* do differ by row. They never affect the unofficial
contribution because saturated M1 always interpolates.

## Frozen protocol (unchanged)

`phase2_report.preliminary_models` and `stats.incremental_validity` use
leave-one-family-out. With four families, each fold trains on 3 observations.
M1 needs 4 parameters. Every official cell is `NOT_IDENTIFIABLE`.

Official recomputed matrix (unchanged scientific definition):
`/root/autodl-fs/RewardLens/results/phase2/paper_analysis/four_model/rq3_debug_raw_matrix.csv`

All 16 scores are empty / NOT_IDENTIFIABLE. Standardized matrix is empty
because there is nothing to z-score.

## What was not changed

- Metric definitions
- Factor set (count, attribute, presence, spatial)
- Frozen LOFO estimator
- Prompt / candidate / manifest hashes
- The unofficial 0.057 JSON, which is preserved in place and copied to
  `rq3_saturated_in_sample_PRESERVED.json`

## Scientific status

RQ3_STATUS = INSUFFICIENT_EVIDENCE_NOT_IDENTIFIABLE_FOR_FOUR_MODELS

Do not report RQ3 as NOT_SUPPORTED from the 0.057 equality.
Do not report RQ3 as supported.
Confirmatory RQ3 waits for the expanded 8-model matrix.
