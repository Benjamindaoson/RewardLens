# GPU Signal Gate Handoff

SIGNAL_GATE_V1 is frozen. This file is only the GPU-host procedure. Do not change data, QC, factors, or RQs.

Bundle: `gpu_bundle_signal_v1`

Use for:

- pipeline validation
- obvious signal check
- output-format validation
- metric sanity check

Do **not** use Signal Gate GPU outputs to change dataset, factor mapping, QC, answer pools, thresholds, predictors, RQ2/RQ3, or sample inclusion.

## GPU machine steps

1. Clone the repo.
2. Checkout the frozen commit/tag used for this bundle. Do not mix with later unfrozen FAST_TRACK files unless they are also frozen.
3. Verify SHA256: `sha256sum -c gpu_bundle_signal_v1/SHA256SUMS.txt`
4. Verify item count: Signal Gate manifest must have **1200** items (4 factors × 100 PASS triplets × 3 variants). Combined static/downstream in `manifests/fast_eval/` must be **800 / 800**. Count is TallyQA; GQA Count remains N=0.
5. Run signal-gate inference only (`run_signal_pipeline.sh` / worker `--stage probe` then `--stage signal_gate`). Offline after staging weights: `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`.
6. Save raw model outputs as append-only JSONL. Do not edit scores.
7. Run frozen analysis on Signal Gate outputs only as an engineering sanity check, not as confirmatory RQ1–RQ3. Confirmatory RQ2/RQ3 wait for the full P0 freeze.
8. Generate an evidence report (Question / Input / Execution / Results / Interpretation / Decision / Artifacts / Verification / Next). Keep failures.
9. **STOP.**

Do not start full P0. Do not train. Do not rebuild TallyQA/GQA. Do not invent a GQA Count mapping.
