# GPU Runbook — FAST_TRACK P0 (A800 80GB, 1–3 workers)

Canonical copy: `rewardlens/docs/GPU_RUNBOOK.md`.

Inference only. Do not render CLEVR, re-split GQA, or invent numbers.

Default: **bf16 + Transformers + SDPA/eager**. No FlashAttention2 on the first pass.

Workers are **model-level** shards (`--num-workers N --worker-index K`), not tensor parallel.

Official compute must be offline after staging:

```bash
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export PYTHONPATH=./rewardlens
```

Preferred one-command path:

```bash
bash rewardlens/scripts/run_gpu_preflight.sh
bash rewardlens/scripts/run_signal_pipeline.sh   # probe + signal + engineering sanity
bash rewardlens/scripts/run_full_pipeline.sh     # only if sanity PASS (not scientific-positive)
```

Manual equivalent:

```bash
NUM_WORKERS=2 MODEL_SHARD=0 bash rewardlens/scripts/run_worker.sh --stage probe
NUM_WORKERS=2 MODEL_SHARD=1 bash rewardlens/scripts/run_worker.sh --stage probe
NUM_WORKERS=2 MODEL_SHARD=0 bash rewardlens/scripts/run_worker.sh --stage signal_gate
NUM_WORKERS=2 MODEL_SHARD=1 bash rewardlens/scripts/run_worker.sh --stage signal_gate
```

Never compute A on CLEVR audit bases. Factor-wise static/BoN uses `manifests/fast_eval/static_manifest.jsonl` and `downstream_manifest.jsonl` (Count = TallyQA; Attribute/Spatial/Presence = GQA; N=8). Do not use GQA Count.

Merge shards:

```bash
python rewardlens/scripts/merge_worker_results.py --inputs outputs/runs/worker_*_of_*/*/*.jsonl --out-jsonl outputs/runs/merged.jsonl
```

Price for ETA is configurable (`estimate_gpu_time.py --price-rmb-per-gpu-hour 5.59`).
