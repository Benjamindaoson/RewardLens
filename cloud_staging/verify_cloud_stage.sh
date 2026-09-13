#!/bin/bash
# Verify staged code/data/models before switching to paid GPU.
set -euo pipefail
TMP="${REWARDLENS_CLOUD_TMP:-/root/autodl-tmp/RewardLens}"
fail() { echo "STAGE_FAIL $*" >&2; exit 1; }
test -d "$TMP/code" || fail "code missing"
test -d "$TMP/models" || mkdir -p "$TMP/models"
MANIFEST="$TMP/code/rewardlens/models/model_stage_manifest.json"
if [[ ! -f "$MANIFEST" ]]; then
  MANIFEST="$TMP/code/models/model_stage_manifest.json"
fi
python - <<PY
import json, os, sys
manifest_path = r"$MANIFEST"
tmp = r"$TMP"
missing = []
if os.path.isfile(manifest_path):
    payload = json.load(open(manifest_path, encoding="utf-8"))
    for rec in payload.get("models", []):
        local = os.path.join(tmp, rec.get("expected_local_path") or "")
        if not os.path.isdir(local):
            missing.append(rec.get("model_id") + " -> " + local)
            continue
        for name in rec.get("required_files") or []:
            if not os.path.isfile(os.path.join(local, name)):
                missing.append(rec.get("model_id") + " missing " + name)
else:
    print("WARN no model_stage_manifest.json")
if missing:
    print("INCOMPLETE_CHECKPOINTS")
    print("\n".join(missing))
    sys.exit(2)
print("CLOUD_STAGE_MODELS_OK")
PY
echo "CLOUD_STAGE_VERIFY_OK"
