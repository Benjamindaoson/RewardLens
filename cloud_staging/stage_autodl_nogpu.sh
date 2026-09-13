#!/bin/bash
# Stage RewardLens on AutoDL no-GPU disk. Safe to run without CUDA.
set -euo pipefail
TMP="${REWARDLENS_CLOUD_TMP:-/root/autodl-tmp/RewardLens}"
FS="${REWARDLENS_CLOUD_FS:-/root/autodl-fs/RewardLens}"
SRC="${REWARDLENS_BUNDLE:-./gpu_bundle_signal_v1}"
mkdir -p "$TMP"/{code,data,models,cache,outputs,logs} \
         "$FS"/{bundles,datasets,models,results,checksums}
if [[ -d "$SRC" ]]; then
  rsync -a --delete "$SRC/" "$TMP/code/" || cp -a "$SRC/." "$TMP/code/"
fi
export HF_HOME="$TMP/cache/huggingface"
export TRANSFORMERS_CACHE="$TMP/cache/transformers"
export HF_HUB_CACHE="$TMP/cache/huggingface"
echo "STAGED $TMP"
echo "PERSIST $FS"
echo "Next: bash cloud_staging/download_models.sh"
