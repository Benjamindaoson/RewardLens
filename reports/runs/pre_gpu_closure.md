# Evidence run — PRE-GPU CLOSURE

## Question

Can Signal Gate GPU start, and can FAST_TRACK freeze proceed factor-by-factor, without changing frozen data or confirmatory RQs?

## Input

Frozen SIGNAL_GATE_V1 (1200 PASS-only items). TallyQA Count 200/200, intersection 0, missing=0. Combined static/downstream 800/800. Four Blender jobs running. No GPU model results.

## Execution

- Read-only Blender snapshot (`scripts/snapshot_blender.py`). Did not restart healthy jobs.
- Per-factor freeze path (`freeze_one_factor`) added. Combined FAST_TRACK_AUDIT_V1 still gated on 4×200 PASS.
- `build_gpu_bundle.py --fast-track` refused: FAST_TRACK_AUDIT_V1 != FROZEN.
- RQ2/RQ3 ran on synthetic fixtures only.
- Analysis configs copied into `gpu_bundle_signal_v1`; SHA256SUMS rewritten; validate PASS.
- Old FAST_TRACK watcher replaced so it freezes each factor at 200 without waiting.

## Results

Blender: 4/4 alive. QC PASS at snapshot+freeze: Count 162, Attribute 128 (BORDERLINE 2), Presence 135, Spatial 133 (BORDERLINE 2). No factor at 200. FAST_TRACK_AUDIT_V1 not frozen. SIGNAL_GATE_GPU READY. Full P0 NOT_READY.

## Interpretation

Closure artifacts are in place. Remaining work is wall-clock rendering to 200 PASS/factor.

## Decision

Do not start full P0. Do not modify SIGNAL_GATE_V1. Do not invent GQA Count. Keep watcher. Stop other development until 4×200 PASS.

## Artifacts

- `reports/DATA_SOURCE_CONFOUND_NOTE.md`
- `docs/GPU_SIGNAL_GATE_HANDOFF.md`
- `rewardlens/docs/GPU_SIGNAL_GATE_HANDOFF.md`
- `rewardlens/scripts/run_rq2_analysis.py`
- `rewardlens/scripts/run_rq3_analysis.py`
- `rewardlens/configs/rq2_analysis.json`
- `rewardlens/configs/rq3_analysis.json`
- `gpu_bundle_signal_v1` validate PASS

## Verification

- Unit tests 14/14 PASS
- `--fast-track` bundle builder exit 3 when unfrozen
- RQ2 factor keys: count, attribute, presence, spatial
- RQ3 confirmatory uses column_standardized
- Attribute/Spatial BORDERLINE retained

## Next

Keep FAST_TRACK watcher until each factor hits 200 PASS, then freeze FAST_TRACK_AUDIT_V1, then build full GPU bundle and stop for GPU.
