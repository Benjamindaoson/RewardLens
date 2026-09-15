#!/usr/bin/env bash
set -euo pipefail
cd /root/autodl-tmp/RewardLens/code
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
export PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false
export PYTHONPATH=/root/autodl-tmp/RewardLens/code/rewardlens
exec /root/autodl-tmp/RewardLens/venv/bin/python -u rewardlens/scripts/phase2_autonomous.py "$@"
