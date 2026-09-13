# Upload manifest — local Windows → AutoDL

Do not rent GPU from this machine. Stage on **no-GPU** AutoDL first.

| Artifact | Typical role | Destination | Required before |
|---|---|---|---|
| `rewardlens/` code + `cloud_staging/` | code | `/root/autodl-tmp/RewardLens/code` | all GPU steps |
| `gpu_bundle_signal_v1/` | Signal Gate manifests + images + code | `/root/autodl-tmp/RewardLens` and `/root/autodl-fs/RewardLens/bundles/` | signal run |
| `gpu_bundle_fast_v1/` | FAST_TRACK + GQA manifests/images | same | full run |
| `rewardlens/models/model_stage_manifest.json` | P0 checkpoint list | models dir | model download |
| `SHA256SUMS.txt` (inside each bundle) | integrity | `/root/autodl-fs/RewardLens/checksums/` | preflight |
| `outputs/signal_gate_v1/` | 100/factor freeze | data/ | signal |
| `outputs/fast_track_audit_v1/` | 200/factor freeze | data/ | full audit |
| `datasets/gqa/derived/` + `datasets/gqa/images/` | GQA fast | data/ | static + BoN |

Sizes and SHA256 are filled after each freeze by `write_sha256sums.py`. Until a freeze exists, do not invent hashes.

Exact user action: provide AutoDL no-GPU SSH (`REWARDLENS_SSH`) and run `cloud_staging/sync_gpu_bundle.sh`. Gated HF logins (Gemma, Llama) must be done on the staging host.

Default A800 price for ETA: **5.59 RMB / GPU-hour** (`estimate_gpu_time.py --price-rmb-per-gpu-hour`).
