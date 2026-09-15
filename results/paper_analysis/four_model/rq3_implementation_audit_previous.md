# RQ3 Implementation Audit

RQ3_IMPLEMENTATION_AUDIT = PASS
RQ3_REVISED_STATUS = INSUFFICIENT_EVIDENCE_NOT_IDENTIFIABLE_FOR_FOUR_MODELS

## What was checked

1. Each 4x4 cell is constructed from dependency factor `af` and downstream utility factor `df` separately.
2. PFC/PSC are read from the dependency-factor row.
3. A and U@8 are read from the downstream-factor row.
4. Dependency rows and utility columns are dumped in `rq3_debug_inputs.csv`.
5. The frozen estimator is the existing LOFO delta MAE contract from `phase2_report.preliminary_models`.
6. Column standardization is only applied after all 16 raw contribution scores are estimable.

## Finding

The frozen implementation is not producing a valid numeric four-model RQ3 matrix, because it correctly refuses to estimate M1 under leave-one-family-out validation. With four models/families, each fold trains on three observations. M1 has four parameters: intercept, A, PFC, and PSC. Therefore every cell is `NOT_IDENTIFIABLE`.

The previous diagonal/off-diagonal equality near machine precision should not be interpreted as `NOT_SUPPORTED`. It came from an earlier saturated/descriptive path, not from an estimable frozen RQ3 analysis.

## Output files

- Raw matrix: `/root/autodl-fs/RewardLens/results/phase2/paper_analysis/four_model/rq3_debug_raw_matrix.csv`
- Standardized matrix: `/root/autodl-fs/RewardLens/results/phase2/paper_analysis/four_model/rq3_debug_standardized_matrix.csv`
- Cell inputs: `/root/autodl-fs/RewardLens/results/phase2/paper_analysis/four_model/rq3_debug_inputs.csv`

## Scientific interpretation

Four-model RQ3 remains pending expanded-model evidence. Current status is `INSUFFICIENT_EVIDENCE`, not a positive or negative RQ3 result.
