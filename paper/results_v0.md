# Results v0

## RQ1
Qwen and Skywork have A=0.8575 and 0.8450 (delta 1.25 pp), PFC=0.7875 and 0.8700 (delta 8.25 pp), and U@8=0.6975 and 0.7513 (delta 5.38 pp).

| Model | A | PFC | PSC | U2 | U4 | U8 |
|---|---:|---:|---:|---:|---:|---:|
| qwen3_vl_4b_instruct | 0.8575 | 0.7875 | 0.9988 | 0.9025 | 0.8050 | 0.6975 |
| gemma3_4b_it | 0.6050 | 0.4300 | 0.8125 | 0.8100 | 0.6412 | 0.4838 |
| molmo_7b_d_0924 | 0.6875 | 0.5212 | 0.7925 | 0.7550 | 0.5763 | 0.4725 |
| skywork_vl_reward_7b | 0.8450 | 0.8700 | 0.9912 | 0.9175 | 0.8363 | 0.7512 |

RQ1_STATUS = SUPPORTED DESCRIPTIVELY. Conventional preference accuracy does not fully characterize visual evidence dependence.

## RQ2
Pearson U@8 correlations are A=0.9342, PFC=0.9779, PSC=0.9829; Spearman values are 0.6, 0.8, 0.8. These are descriptive N=4 relationships; no saturated regression inference is claimed.

RQ2_STATUS = DESCRIPTIVE / INSUFFICIENT EVIDENCE.

## RQ3
RQ3_IMPLEMENTATION_AUDIT = BUG_FOUND
RQ3_REVISED_STATUS = INSUFFICIENT_EVIDENCE_NOT_IDENTIFIABLE_FOR_FOUR_MODELS

The unofficial diagonal/off-diagonal equality near 0.05725 is an identity of a saturated in-sample estimator (M1 interpolates 4 points with 4 parameters, so contributions are column-constant). It is not a scientific null. The frozen LOFO 4×4 matrix is not identifiable with four families.
