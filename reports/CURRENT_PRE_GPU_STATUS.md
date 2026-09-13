# CURRENT_PRE_GPU_STATUS

Updated: 2026-09-12T15:03:13+00:00

- SIGNAL_GATE_V1 = **FROZEN** (untouched; n_items=1200)
- SIGNAL_DATA_READY = **PASS**
- SIGNAL_GATE_GPU = **READY**
- FAST_TRACK_AUDIT_V1 = **PASS** (800 PASS triplets / 2400 images)
- gpu_bundle_fast_v1 = **PASS** (`verify_bundle.py` + `validate_gpu_bundle.py --mode fast-track`)
- FULL_P0_GPU / paid GPU start = **NOT STARTED** (waiting on GPU host)

## Watchers

- old_fast_track_watcher: **EXPECTED_STOP** (replaced_by_per_factor_freeze_watcher; not a failure)
- new_fast_track_watcher: **COMPLETED** (exit 0)
- Blender: **4/4 RUNNING** (500-scale robustness; do not restart)

## Per-factor FAST_TRACK freeze

| Factor | Frozen | Live PASS at aggregate | BORDERLINE included |
|---|---|---:|---|
| Count | PASS (200) | 234 | 0 |
| Attribute | PASS (200) | 200 | 0 |
| Presence | PASS (200) | 212 | 0 |
| Spatial | PASS (200) | 207 | 0 |

Hard validation: factor manifests agree with aggregate; missing images=0; PASS-only.

## Count natural-image freeze (already done)

- static/downstream intersection: 0
- simple/complex static: 100/100
- simple/complex downstream: 100/100
- images missing: 0
- GQA Count remains N=0
