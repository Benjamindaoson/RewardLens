# Inference Protocol

Applies after the 100-sample signal gate. Frozen candidate order. No per-model shuffle.

## Inputs

Each item is `(image, question, candidate_a, candidate_b)`.

All models see the same files and the same A/B order.

## Decoding

- temperature = 0 / deterministic decode
- record max tokens, seed if supported, dtype, quantization, checkpoint revision
- write `environment_report.json` per run

## Outputs (required)

`outputs/audit_runs/<model_id>/` jsonl with:

- raw_response
- parsed_preference
- score_A / score_B / margin when available
- latency
- parse_status
- OOM/retry
- model_version

Failures go to `failure_log.jsonl`. No silent drops.

## Metrics

From parsed preferences vs expected labels:

- A, PFC, PSC, PFC_cond, PSC_cond, N

Static \(A_f\) is computed only on the factor-wise static set (TallyQA Count; GQA otherwise), never on audit bases.

## GPU

This workstation has no CUDA. Full inference is a resource gate, not a scientific stop.
