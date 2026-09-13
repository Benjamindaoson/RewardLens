#!/bin/bash
# Model-level parallelism. N workers, not tensor parallel.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
INDEX="${MODEL_SHARD:-${WORKER_INDEX:-${1:-0}}}"
NUM="${NUM_WORKERS:-2}"
shift || true
python "$ROOT/inference/run_worker.py" --num-workers "$NUM" --worker-index "$INDEX" "$@"
