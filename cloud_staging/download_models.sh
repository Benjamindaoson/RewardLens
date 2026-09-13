#!/bin/bash
# Download P0 Signal Gate models on a no-GPU staging machine.
set -euo pipefail
TMP="${REWARDLENS_CLOUD_TMP:-/root/autodl-tmp/RewardLens}"
FS="${REWARDLENS_CLOUD_FS:-/root/autodl-fs/RewardLens}"
export HF_HOME="${HF_HOME:-$TMP/cache/huggingface}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-$TMP/cache/transformers}"
mkdir -p "$TMP/models" "$FS/models"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MANIFEST_JSON="${MODEL_STAGE_MANIFEST:-}"
if [[ -z "$MANIFEST_JSON" ]]; then
  for p in \
    "$TMP/code/rewardlens/models/model_stage_manifest.json" \
    "$SCRIPT_DIR/../rewardlens/models/model_stage_manifest.json"
  do
    if [[ -f "$p" ]]; then MANIFEST_JSON="$p"; break; fi
  done
fi
test -f "$MANIFEST_JSON" || { echo "missing model_stage_manifest.json"; exit 1; }

python - "$MANIFEST_JSON" "$TMP" <<'PY'
import json, os, subprocess, sys
manifest, tmp = sys.argv[1], sys.argv[2]
payload = json.load(open(manifest, encoding="utf-8"))
for rec in payload["models"]:
    dest = os.path.join(tmp, rec["expected_local_path"])
    os.makedirs(dest, exist_ok=True)
    repo = rec["repo"]
    rev = rec.get("revision") or "main"
    print("DOWNLOAD", repo, "->", dest, flush=True)
    cmd = ["huggingface-cli", "download", repo, "--revision", rev, "--local-dir", dest]
    try:
        subprocess.check_call(cmd)
    except Exception as exc:
        ms = rec.get("fallback_source") or ""
        if ms.startswith("modelscope:"):
            ms_id = ms.split(":", 1)[1]
            print("HF failed, trying modelscope", ms_id, exc, flush=True)
            subprocess.check_call([sys.executable, "-m", "modelscope", "download", "--model", ms_id, "--local_dir", dest])
        else:
            raise
print("MODEL_DOWNLOAD_DONE")
PY
rsync -a "$TMP/models/" "$FS/models/" || true
echo "DOWNLOAD_MODELS_OK"
