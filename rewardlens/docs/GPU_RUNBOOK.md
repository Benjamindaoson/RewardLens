# GPU Runbook — FAST_TRACK P0 (A800 80GB, 1–3 workers)

Inference only. Do not render CLEVR, re-split GQA, or invent numbers.

Default: **bf16 + Transformers + SDPA/eager**. No FlashAttention2 on the first pass.

Workers are **model-level** shards (`--num-workers N --worker-index K`), not tensor parallel.

```bash
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH=./rewardlens
bash rewardlens/scripts/run_gpu_preflight.sh
bash rewardlens/scripts/run_signal_pipeline.sh
bash rewardlens/scripts/run_full_pipeline.sh
```

Engineering sanity (parse rate / no all-model floor or ceiling) is required to continue. Hypothesis support is not.

Never compute A on CLEVR audit bases. Combined static/BoN manifests: Count is TallyQA; Attribute/Spatial/Presence are GQA.
