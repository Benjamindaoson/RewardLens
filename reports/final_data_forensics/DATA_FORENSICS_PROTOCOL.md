# RewardLens Pre-Deadline Data Forensics Protocol

Frozen: 2026-09-15T21:58:27Z
Status: CPU forensics only. No GPU inference. No model rerun.

This freeze separates **data identity**, **metric objects**, and **optional new analyses** for the ICLR revision.

## Hard constraints

1. Physical identity is SHA256 of raw image bytes (`physical_image_id`).
2. The same numeric `example_id` does not imply the same physical example.
3. `A^S ≠ A^B`. Never substitute independent static accuracy for audit-base accuracy.
4. If an item-level Audit↔BoN join is possible on physical identity, stop; that is an integrity issue.
5. If it is impossible, that is required by the frozen physical-disjoint design. Do not force the join.

## Identity objects

Every Static / Audit / Downstream row must trace to: dataset, split, source_example_id, source_image_id, physical_image_path, image hash, manifest row id, factor, variant, pool_id.

`I_audit ∩ I_downstream = ∅` is a statement about **physical image hashes**, not local autoincrement IDs.

## Frozen manifests

| split | sha256 |
|---|---|
| static | `6e4a23fc54d4704e70587b177586152e6e63b7a4dac5964e7e16f56395e682e3` |
| audit | `880a3769df10e7e4dff5939ba03bbff7347cc62e56b11f79e10f5a1b61d8a018` |
| downstream v2 | `0afb6dfefd7a47e3dc47fd05127e82d5fd260943d04e5c5cc3117ae11055133c` |

Downstream v1 was not physically disjoint from static (196 shared hashes; 197 rows replaced). Downstream v2 is the frozen GPU set.

## Measurement objects

Do not use a single symbol A.

- `A^S(J)` = independent static benchmark accuracy (TallyQA Count; GQA otherwise)
- `A^B(J)` = P(C_B=1) on complete audit triplets
- `RA(J) = P(C_R=1 | C_B=1)` (frozen `PFC_cond`)
- `II(J) = P(C_I=1 | C_B=1)` (frozen `PSC_cond`)
- `PFC = P(C_B=1, C_R=1)`
- `PSC = P(C_B=1, C_I=1)`
- `D(J) = (RA(J), II(J))`

On the same audit population and the same abstention convention: `PFC = A^B · RA` and `PSC = A^B · II`.
These identities do not use `A^S`.

Empirical main proposition: **`A^S(J)` does not empirically determine `D(J)`.**
Theory should compare an observational/static score with an intervention distribution and must not assume `A^S = A^B`.

## Denominators

- Audit: complete triplets only. Incomplete or unparsed triplets are dropped.
- Static `A^S`: status=ok and parsed A/B. Parse failures are excluded, not counted wrong.
- Pair-graph abstention: parsed preference not in {A,B} or status != ok.

## Analyses after P0

| ID | Analysis | Paper role |
|---|---|---|
| P2 | Eight-state π_bri on audit triplets | Allowed; RA/II are projections of joint intervention behavior |
| P3 | Prediction flip F_I = P(Y_I ≠ Y_B) | Allowed; correctness ≠ behavioral stability |
| P4 | Equivalence curve on A^S, ε in {0.5,1,2,3,5} pp | 1pp stays predeclared; others are post-hoc sensitivity |
| P5 | Pair graph | Secondary exploratory only |
| — | Audit↔BoN item-level join | Cancelled unless P0 finds unexpected physical overlap |

RQ2 stays a model-level secondary diagnostic.

## P0 result in this freeze

- audit ∩ static physical = 0
- audit ∩ downstream_v2 physical = 0
- static ∩ downstream_v2 physical = 0
- pass = True

P1 reconstruction: 32 factor-rows have A^S ≠ A^B; PFC=A^B·RA holds on 32/32 rows.

P4 1pp pairs recomputed on A^S: 7. This remains the predeclared headline matching analysis.

## Machine policy

- 017 GPU stays off unless a unique local-disk file is the only evidence copy.
- 011 no-GPU is allowed for missing shared-fs files.
- First pass: local HF archive + autodl-fs CPU reads.

