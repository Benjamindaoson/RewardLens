#!/bin/bash
# Full GPU pipeline after engineering sanity. Does not require scientific-positive results.
set -euo pipefail

ROOT="${REWARDLENS_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
PROJECT="${REWARDLENS_PROJECT:-$(cd "$ROOT/.." && pwd)}"
PYTHON="${PYTHON:-python}"
NUM_WORKERS="${NUM_WORKERS:-2}"
MANIFEST_ROOT="${MANIFEST_ROOT:-$PROJECT/outputs/fast_track_audit_v1}"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"

bash "$ROOT/scripts/run_signal_pipeline.sh"

SANITY="$PROJECT/outputs/signal_sanity_gate.json"
"$PYTHON" - <<PY
import json, sys
p = r"$SANITY"
try:
    payload = json.load(open(p, encoding="utf-8"))
except Exception:
    sys.exit("sanity gate missing")
if payload.get("status") != "PASS":
    print("SANITY_GATE_BLOCK", payload)
    sys.exit(2)
print("SANITY_GATE_PASS")
PY

for stage in full_audit gqa_static gqa_bon; do
  for k in $(seq 0 $((NUM_WORKERS - 1))); do
    "$PYTHON" "$ROOT/inference/run_worker.py" \
      --num-workers "$NUM_WORKERS" --worker-index "$k" \
      --stage "$stage" --manifest-root "$MANIFEST_ROOT" &
  done
  wait
done

echo "FULL_PIPELINE_OK"
