# Model Registry (draft)

No reward-model scores exist yet. This file lists intended families for the compatibility audit.

Local machine is CPU-only (`torch 2.13.0+cpu`). Compatibility probes and full inference require a GPU host.

## Constraints from the scientific contract

- 8–12 compatible systems if practically possible
- ≥4 genuinely distinct families/paradigms if practically possible
- Cluster by family in statistics; do not treat same-family sizes as independent
- No paid closed APIs without authorization
- Do not download every large checkpoint before a tiny compatibility probe

## Candidate families (not yet downloaded)

| family | example checkpoints | type | notes |
|---|---|---|---|
| Qwen2.5-VL / Qwen2-VL | 3B / 7B instruct | general MLLM-as-judge | local, open |
| InternVL | InternVL2 2B/8B | general MLLM-as-judge | local, open |
| LLaVA | LLaVA-OneVision 0.5B/7B | general MLLM-as-judge | local, open |
| specialized VL reward | e.g. public VL-Reward / critic checkpoints after license check | dedicated / generative reward | only if image+A/B interface is stable |

Final inclusion requires a compatibility probe:

1. image loads
2. prompt is stable
3. A/B or scalar output parses
4. parse failure < 2%
5. no format collapse
6. base competence above chance on a tiny held-out probe, not the confirmatory set

Machine-readable copy: `models/model_registry.yaml`
