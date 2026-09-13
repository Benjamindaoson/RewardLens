# FAST_TRACK_AUDIT_V1

Frozen only after four factors each reached 200 PASS. SIGNAL_GATE_V1 was not modified.

- READY_FOR_FULL_P0: **YES**
- n_items: 2400
- manifest SHA256: `5b2b457b8e6d0483d6c638b909ce5c0295f6c47db15cf72370133b13c5d23382`
- sample rule: first 200 PASS triplet_ids per factor, sorted
- BORDERLINE/FAIL retained in QC, never upgraded
- GQA Count N=0: `{'gqa_static_count': 0, 'gqa_down_count': 0, 'mapping_count': 0, 'ok': True}`
- TallyQA Count intersection: 0
- TallyQA simple/complex: static 100/100 downstream 100/100

## Checks

- `four_factors_200_pass`: True
- `pass_only`: True
- `no_accidental_duplicates`: True
- `gqa_count_n0`: True
- `count_simple_complex_100_100`: True
- `count_image_intersection_0`: True
- `combined_static_800`: True
- `combined_down_800`: True
- `borderline_not_upgraded`: True
- `manifest_sha256`: 5b2b457b8e6d0483d6c638b909ce5c0295f6c47db15cf72370133b13c5d23382
- `frozen_at`: 2026-09-12T15:02:32.279141+00:00

## What this freeze can prove

A deterministic FAST_TRACK controlled-audit subset exists for GPU P0. Natural-image Count is TallyQA; Attribute/Spatial/Presence are GQA.

## What this freeze cannot prove

RQ1–RQ3. Dataset-source confounding on Count. Signal-gate GPU scores must not rewrite this freeze.
