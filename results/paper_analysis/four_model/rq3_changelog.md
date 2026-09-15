# RQ3 changelog

## 2026-09-15 — 017 implementation re-audit

- BUG_FOUND in the unofficial four-model saturated in-sample RQ3 path.
- Preserved original unofficial artifact:
  `four_model_paper_checkpoint/four_model_rq3.json`
  copied to `paper_analysis/four_model/rq3_saturated_in_sample_PRESERVED.json`.
- Did not change the frozen LOFO scientific definition.
- Official four-model matrix remains all-cell `NOT_IDENTIFIABLE`.
- RQ3_REVISED_STATUS = INSUFFICIENT_EVIDENCE_NOT_IDENTIFIABLE_FOR_FOUR_MODELS.
- Previous wording that treated diagonal≈off-diagonal as NOT_SUPPORTED is withdrawn.
