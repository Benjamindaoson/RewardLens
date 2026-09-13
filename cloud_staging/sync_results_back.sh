#!/bin/bash
# Copy GPU JSONL results back from AutoDL.
set -euo pipefail
SSH="${REWARDLENS_SSH:?set REWARDLENS_SSH=user@host}"
TMP="${REWARDLENS_CLOUD_TMP:-/root/autodl-tmp/RewardLens}"
LOCAL="${REWARDLENS_LOCAL_RESULTS:-./outputs/runs}"
mkdir -p "$LOCAL"
rsync -avP "$SSH:$TMP/outputs/runs/" "$LOCAL/"
rsync -avP "$SSH:$TMP/outputs/"*.json "$LOCAL/../" || true
echo "RESULTS_SYNCED $LOCAL"
