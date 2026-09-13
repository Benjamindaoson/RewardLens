#!/bin/bash
# Copy a local GPU bundle to AutoDL tmp/fs. Run from the Windows/Linux jump host if rsync/scp exists.
set -euo pipefail
SSH="${REWARDLENS_SSH:?set REWARDLENS_SSH=user@host}"
TMP="${REWARDLENS_CLOUD_TMP:-/root/autodl-tmp/RewardLens}"
FS="${REWARDLENS_CLOUD_FS:-/root/autodl-fs/RewardLens}"
BUNDLE="${1:-gpu_bundle_signal_v1}"
ssh "$SSH" "mkdir -p $TMP/code $FS/bundles"
rsync -avP --mkpath "$BUNDLE/" "$SSH:$TMP/code/"
rsync -avP --mkpath "$BUNDLE/" "$SSH:$FS/bundles/$(basename "$BUNDLE")/"
echo "SYNCED $BUNDLE -> $SSH:$TMP/code"
