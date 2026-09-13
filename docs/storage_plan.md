# Storage plan — AutoDL A800 staging + compute

Prices and sizes are engineering estimates from the frozen 8-model registry and FAST_TRACK / GQA-fast targets.
They are **not** scientific results.

## Inputs

| Item | Count / size basis |
|---|---|
| P0 Signal Gate models | Qwen3-VL-4B, Gemma-3-4B, Molmo-7B-D, Skywork-VL-Reward-7B ≈ 9+9+15+15 = **48 GB** |
| P1 remaining primaries | Qwen3-VL-8B, Gemma-3-12B, InternVL3-8B, Llama-3.2-11B-Vision ≈ 16+24+16+22 = **78 GB** |
| P2 replacements (optional) | ~15 GB each, keep one slot ≈ **15 GB** |
| HF / Transformers cache overhead | tokenizer + duplicate shards ≈ **20–40 GB** |
| FAST_TRACK CLEVR images | 800 triplets × 3 PNG @ 320×240, ~80–150 KB each ≈ **0.2–0.4 GB** |
| Signal Gate subset | 400 triplets × 3 ≈ **0.1–0.2 GB** (subset of FAST_TRACK) |
| GQA frozen images | ≤1600 unique VG JPEGs ≈ **0.3–0.8 GB** |
| GQA questions + scene graphs (metadata only) | zip 1.50 + 0.04 GB, extracted ~**4–8 GB** |
| Code + manifests + env | **<2 GB** |
| Result JSONL | 8 models × ~10k judgments ≈ **<1 GB** |

Do **not** store: Blender, CLEVR source, GQA `images.zip` (~20 GB), old CNN features, paper figure masters.

## Totals

| Profile | Disk | Notes |
|---|---:|---|
| **Minimum** | **~160 GB** | P0 models + FAST_TRACK images + GQA subset + metadata + 20 GB cache |
| **Recommended** | **~240 GB** | All 8 primaries + cache + GQA metadata + results |
| **Headroom** | **~300 GB** | Recommended + one replacement + extract slack + logs |

Target practical AutoDL disk: **200–300 GB**. A 80 GB data disk is **not** enough for 8 checkpoints.

## Cloud layout

- `/root/autodl-tmp/RewardLens/` — working copy, models, cache, outputs
- `/root/autodl-fs/RewardLens/` — persistent bundles / checksums / results

Stage models on **no-GPU** mode. GPU compute should run `HF_HUB_OFFLINE=1`.
