#!/bin/bash
# GPU compute pipeline: preflight → probe → signal gate → engineering sanity → optional continue.
# Sanity is engineering-only: parse success, no all-model floor/ceiling. Not a scientific-positive gate.
set -euo pipefail

ROOT="${REWARDLENS_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
PROJECT="${REWARDLENS_PROJECT:-$(cd "$ROOT/.." && pwd)}"
PYTHON="${PYTHON:-python}"
NUM_WORKERS="${NUM_WORKERS:-2}"
MANIFEST_ROOT="${MANIFEST_ROOT:-$PROJECT/outputs/signal_gate_v1}"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"

bash "$ROOT/scripts/run_gpu_preflight.sh"

for k in $(seq 0 $((NUM_WORKERS - 1))); do
  "$PYTHON" "$ROOT/inference/run_worker.py" \
    --num-workers "$NUM_WORKERS" --worker-index "$k" \
    --stage probe --manifest-root "$MANIFEST_ROOT" &
done
wait

for k in $(seq 0 $((NUM_WORKERS - 1))); do
  "$PYTHON" "$ROOT/inference/run_worker.py" \
    --num-workers "$NUM_WORKERS" --worker-index "$k" \
    --stage signal_gate --manifest-root "$MANIFEST_ROOT" &
done
wait

"$PYTHON" "$ROOT/scripts/signal_sanity_gate.py" \
  --runs-root "$PROJECT/outputs/runs" \
  --out "$PROJECT/outputs/signal_sanity_gate.json"

echo "SIGNAL_PIPELINE_OK"
