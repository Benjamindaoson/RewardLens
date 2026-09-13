# Generated result snippets

Auto-generated from artifacts. Not a substitute for the paper draft.
Missing or synthetic artifacts are reported, never invented.

## RQ1_TABLE

Anchor: `[TBD: RQ1 ACCURACY-MATCHED RESULT]`

```
MISSING D:\01_work\RewardLens\outputs/analysis/accuracy_matched_pairs.json
```

*No real artifact yet.*

## RQ1_MATCHED_PAIR_EXAMPLE

Anchor: `[TBD: RQ1 MATCHED PAIR EXAMPLE]`

```
MISSING D:\01_work\RewardLens\outputs/analysis/accuracy_matched_pairs.json
```

*No real artifact yet.*

## RQ2_DELTA_LOFO

Anchor: `[TBD: DELTA LOFO PERFORMANCE]`

```
MISSING D:\01_work\RewardLens\outputs/analysis/incremental_validity.json
```

*No real artifact yet.*

## RQ2_CI

Anchor: `[TBD: RQ2 CI]`

```
MISSING D:\01_work\RewardLens\outputs/analysis/incremental_validity.json
```

```
MISSING D:\01_work\RewardLens\outputs/analysis/cluster_bootstrap.json
```

*No real artifact yet.*

## RQ3_DIAGONAL_OFFDIAGONAL

Anchor: `[TBD: SPECIFICITY MATRIX RESULT]`

```
MISSING D:\01_work\RewardLens\outputs/analysis/factor_specificity.json
```

*No real artifact yet.*

## MODEL_COUNT

Anchor: `[TBD: MODEL COMPATIBILITY TABLE]`

```
{
  "schema_version": 1,
  "status": "UNTESTED_REGISTRY_ONLY",
  "weights_downloaded": false,
  "fast_track": {
    "target_models": 8,
    "minimum_models": 6,
    "minimum_families": 4,
    "compatibility_timeout_min": 40,
    "workers": 2,
    "worker_gpu": "A800-80GB"
  },
  "note": "No checkpoint is marked compatible. Status starts UNTESTED. Skip a model after ~40 minutes of compatibility debugging and replace from the backup pool.",
  "models": [
    {
      "model_id": "qwen3_vl_4b_instruct",
      "family": "qwen_vl",
      "model_type": "general_mllm_as_judge",
      "checkpoint": "Qwen/Qwen3-VL-4B-Instruct",
      "revision": "main",
      "license": "apache-2.0",
      "parameter_size": "4B",
      "expected_vram": "10GB_bf16",
      "transformers_support": "expected",
      "rocm_expected": "unknown",
      "cuda_expected": "unknown",
      "requires_custom_kernel": false,
      "requires_flash_attention": false,
      "requires_quantization": false,
      "prompt_adapter": "pairwise_ab",
      "parser": "ab_parser",
      "status": "UNTESTED",
      "fast_track_primary": true,
      "worker": 0,
      "notes": "First carrier. 4B, A800-80GB comfortable."
    },
    {
      "model_id": "gemma3_4b_it",
      "family": "gemma",
      "model_type": "general_mllm_as_judge",
      "checkpoint": "google/gemma-3-4b-it",
      "revision": "main",
      "license": "gemma",
      "parameter_size": "4B",
      "expected_vram": "10GB_bf16",
      "transformers_support": "expected",
      "rocm_expected": "unknown",
      "cuda_expected": "unknown",
      "requires_custom_kernel": false,
      "requires_flash_attention": false,
      "requires_quantization": false,
      "prompt_adapter": "pairwise_ab",
      "parser": "ab_parser",
      "status": "UNTESTED",
      "fast_track_primary": true,
      "worker": 0,
      "notes": "Gated license."
    },
    {
      "model_id": "molmo_7b_d_0924",
      "family": "molmo",
      "model_type": "general_mllm_as_judge",
      "checkpoint": "allenai/Molmo-7B-D-0924",
      "revision": "main",
      "license": "apache-2.0",
      "parameter_size": "7B",
      "expected_vram": "16GB_bf16",
      "transformers_support": "expected",
      "rocm_expected": "unknown",
      "cuda_expected": "unknown",
      "requires_custom_kernel": false,
      "requires_flash_attention": false,
      "requires_quantization": false,
      "prompt_adapter": "pairwise_ab",
      "parser": "ab_parser",
      "status": "UNTESTED",
      "fast_track_primary": true,
      "worker": 0
    },
    {
      "model_id": "skywork_vl_reward_7b",
      "family": "specialized_vl_reward",
      "model_type": "dedicated_multimodal_reward",
      "checkpoint": "Skywork/Skywork-VL-Reward-7B",
      "revision": "main",
      "license": "unknown",
      "parameter_size": "7B",
      "expected_vram": "16GB_bf16",
      "transformers_support": "unknown",
      "rocm_expected": "unknown",
      "cuda_expected": "unknown",
      "requires_custom_kernel": "unknown",
      "requires_flash_attention": false,
      "requires_quantization": false,
      "prompt_adapter": "pairwise_ab",
      "parser": "ab_parser",
      "status": "UNTESTED",
      "fast_track_primary": true,
      "worker": 0,
      "notes": "Specialized RM. If >40min debug, replace with ixc25_reward_7b."
    },
    {
      "model_id": "qwen3_vl_8b_instruct",
      "family": "qwen_vl",
      "model_type": "general_mllm_as_judge",
      "checkpoint": "Qwen/Qwen3-VL-8B-Instruct",
      "revision": "main",
      "license": "apache-2.0",
      "parameter_size": "8B",
      "expected_vram": "18GB_bf16",
      "transformers_support": "expected",
      "rocm_expected": "unknown",
      "cuda_expected": "unknown",
      "requires_custom_kernel": false,
      "requires_flash_attention": false,
      "requires_quantization": false,
      "prompt_adapter": "pairwise_ab",
      "parser": "ab_parser",
      "status": "UNTESTED",
      "fast_track_primary": true,
      "worker": 1
    },

```

## FACTOR_N

Anchor: `[TBD: FAST_TRACK PASS/FAIL COUNTS AFTER FREEZE]`

```
MISSING D:\01_work\RewardLens\outputs/fast_track_audit_v1/dataset_summary.json
```

*No real artifact yet.*

## STATIC_N

Anchor: `[TBD: GQA STATIC A]`

```
D:\01_work\RewardLens\datasets/gqa/derived/gqa_static_manifest.jsonl n=600
```

## DOWNSTREAM_N

Anchor: `[TBD: GQA BON U]`

```
D:\01_work\RewardLens\datasets/gqa/derived/gqa_downstream_manifest.jsonl n=600
```

## CONTROLLED_AUDIT_TABLE

Anchor: `[TBD: CONTROLLED AUDIT TABLE]`

```
MISSING D:\01_work\RewardLens\outputs/analysis/audit_metrics.csv
```

*No real artifact yet.*

## DOWNSTREAM_UTILITY_TABLE

Anchor: `[TBD: BEST-OF-N TABLE]`

```
MISSING D:\01_work\RewardLens\outputs/analysis/downstream_utility.csv
```

*No real artifact yet.*

## INCREMENTAL_VALIDITY_TABLE

Anchor: `[TBD: Δ LOFO PERFORMANCE]`

```
MISSING D:\01_work\RewardLens\outputs/analysis/incremental_validity.json
```

*No real artifact yet.*

## SPECIFICITY_TABLE

Anchor: `[TBD: SPECIFICITY MATRIX RESULT]`

```
MISSING D:\01_work\RewardLens\outputs/analysis/factor_specificity.json
```

*No real artifact yet.*

## SIGNAL_GATE_DYNAMIC_RANGE

Anchor: `[TBD: SIGNAL GATE DYNAMIC RANGE]`

```
MISSING D:\01_work\RewardLens\outputs/signal_sanity_gate.json
```

*No real artifact yet.*
