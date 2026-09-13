#!/bin/bash
# Fail-fast NVIDIA A800 preflight. Do not start large inference if this fails.
set -euo pipefail

ROOT="${REWARDLENS_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
PROJECT="${REWARDLENS_PROJECT:-$(cd "$ROOT/.." && pwd)}"
CLOUD_TMP="${REWARDLENS_CLOUD_TMP:-/root/autodl-tmp/RewardLens}"
PYTHON="${PYTHON:-python}"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"

fail() { echo "PREFLIGHT_FAIL: $*" >&2; exit 1; }

command -v nvidia-smi >/dev/null 2>&1 || fail "nvidia-smi missing"
nvidia-smi || fail "nvidia-smi failed"
GPU_NAME="$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n1 || true)"
VRAM="$(nvidia-smi --query-gpu=memory.total --format=csv,noheader | head -n1 || true)"
echo "GPU_NAME $GPU_NAME"
echo "VRAM $VRAM"
echo "$GPU_NAME" | grep -qi "A800\\|A100\\|H100\\|H800" || echo "WARN unexpected GPU name: $GPU_NAME"

"$PYTHON" - <<'PY' || fail "torch/cuda/bf16 check failed"
import os, sys
print("python", sys.version)
import torch
print("torch", torch.__version__, "cuda", torch.version.cuda, "hip", getattr(torch.version, "hip", None))
if not torch.cuda.is_available():
    raise SystemExit("torch.cuda is not available")
print("device", torch.cuda.get_device_name(0))
print("vram_gb", round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2))
a = torch.randn(256, 256, device="cuda", dtype=torch.bfloat16)
b = torch.randn(256, 256, device="cuda", dtype=torch.bfloat16)
c = a @ b
assert torch.isfinite(c).all()
print("bf16_ok")
import transformers
print("transformers", transformers.__version__)
PY

MANIFEST_ROOT="${MANIFEST_ROOT:-$PROJECT/outputs/signal_gate_v1}"
test -d "$PROJECT" || fail "project path missing: $PROJECT"
test -w "$PROJECT/outputs" || mkdir -p "$PROJECT/outputs"
test -w "$PROJECT/outputs" || fail "outputs not writable"
if [[ -f "$MANIFEST_ROOT/hashes.json" ]]; then
  echo "MANIFEST_HASHES $MANIFEST_ROOT/hashes.json"
else
  echo "WARN no hashes.json at $MANIFEST_ROOT (ok if using bundle manifests/)"
fi

MODEL_DIR="${MODEL_DIR:-$CLOUD_TMP/models}"
if [[ -d "$MODEL_DIR" ]]; then
  echo "MODEL_DIR $MODEL_DIR"
else
  echo "WARN model dir not present yet: $MODEL_DIR"
fi

"$PYTHON" "$ROOT/scripts/device_probe.py" --out "${PREFLIGHT_OUT:-$PROJECT/outputs/gpu_preflight.json}" || fail "device_probe failed"
echo "PREFLIGHT_OK"
