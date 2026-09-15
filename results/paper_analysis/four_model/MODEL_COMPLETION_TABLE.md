# Expanded + original model completion table

Status vocabulary: COMPLETE | RUNNING | PARTIAL | NOT_STARTED | BLOCKED

| MODEL | STATUS | STATIC | AUDIT | DOWNSTREAM | PAIR_EDGES | OUTPUT_PATH | WORKER |
| --- | --- | --- | --- | --- | --- | --- | --- |
| qwen3_vl_4b_instruct | COMPLETE | 800 | canonical four-model audit | 800 pools | 22400 | /root/autodl-fs/RewardLens/results/phase2/gpu_4model_v1/qwen3_vl_4b_instruct | original four-model |
| gemma3_4b_it | COMPLETE | 800 | canonical four-model audit | 800 pools | 22400 | /root/autodl-fs/RewardLens/results/phase2/gpu_4model_v1/gemma3_4b_it | original four-model |
| molmo_7b_d_0924 | COMPLETE | 800 | canonical four-model audit | 800 pools | 22400 | /root/autodl-fs/RewardLens/results/phase2/gpu_4model_v1/molmo_7b_d_0924 | original four-model |
| skywork_vl_reward_7b | COMPLETE | 800 | canonical four-model audit | 800 pools | 22400 | /root/autodl-fs/RewardLens/results/phase2/gpu_parallel_017/skywork_vl_reward_7b | 017 (gpu_4model_v1/completion.json is delegation stub only) |
| idefics3_8b_llama3 | COMPLETE | 800 | 2400 | 800 pools | 22400 | /root/autodl-fs/RewardLens/results/phase2/distributed_v1/idefics3_8b_llama3 | 017 |
| phi35_vision_instruct | COMPLETE | 800 | 2400 | 800 pools | 22400 | /root/autodl-fs/RewardLens/results/phase2/distributed_v1/phi35_vision_instruct | 017 |
| internvl3_8b_hf | RUNNING | 800/800 | 2400/2400 | in progress | in progress | /root/autodl-fs/RewardLens/results/phase2/distributed_v1/internvl3_8b_hf | 017 (durable screen expanded_internvl_017; 011 smoke failure preserved separately) |
| llava_onevision_qwen2_7b | COMPLETE | 800 | 2400 | 800 pools | 22400 | /root/autodl-fs/RewardLens/results/phase2/distributed_v1/llava_onevision_qwen2_7b | 017 |
| minicpm_v_26 | NOT_STARTED | — | — | — | — | FROZEN_FALLBACK only | none |
| llama32_11b_vision_instruct | NOT_STARTED | — | — | — | — | FROZEN_FALLBACK only | none |
| phi4_multimodal_instruct | NOT_STARTED | — | — | — | — | FROZEN_FALLBACK only | none |
| idefics2_8b | NOT_STARTED | — | — | — | — | FROZEN_FALLBACK only | none |

Frozen selected expanded four: Idefics3, Phi-3.5-Vision, InternVL3, LLaVA-OneVision.
Target total 8 = original 4 + selected expanded 4. Fallbacks are not launched unless a selected family has no accepted candidate.

Do not re-infer any COMPLETE model.
