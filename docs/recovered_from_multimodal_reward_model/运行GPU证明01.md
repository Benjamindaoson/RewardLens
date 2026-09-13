````
+-----------------------------------------------AutoDL-----------------------------------------------------+
目录说明:
╔═════════════════╦════════╦════╦═════════════════════════════════════════════════════════════════════════╗
║目录             ║名称    ║速度║说明                                                                     ║
╠═════════════════╬════════╬════╬═════════════════════════════════════════════════════════════════════════╣
║/                ║系 统 盘║一般║实例关机数据不会丢失，可存放代码等。会随保存镜像一起保存。               ║
║/root/autodl-tmp ║数 据 盘║ 快 ║实例关机数据不会丢失，可存放读写IO要求高的数据。但不会随保存镜像一起保存 ║
║/root/autodl-fs  ║文件存储║一般║可以实现多实例间的文件同步共享，不受实例开关机和保存镜像的影响。         ║
╚═════════════════╩════════╩════╩═════════════════════════════════════════════════════════════════════════╝
CPU ：0.5 核心
内存：2 GB
GPU ：No devices were found
存储：
  系 统 盘/               ：1% 53M/30G
  数 据 盘/root/autodl-tmp：1% 12K/50G
  文件存储/root/autodl-fs ：1% 580M/200G
+----------------------------------------------------------------------------------------------------------+
*注意: 
1.系统盘较小请将大的数据存放于数据盘或文件存储中，重置系统时数据盘和文件存储中的数据不受影响
2.清理系统盘请参考：https://www.autodl.com/docs/qa1/
3.终端中长期执行命令请使用screen等工具开后台运行，确保程序不受SSH连接中断影响：https://www.autodl.com/docs/daemon/
root@autodl-container-03dd44a781-f2a6258d:~# ls -lh /root/autodl-fs
lrwxrwxrwx 1 root root 20 Sep 13 02:15 /root/autodl-fs -> ../../autodl-fs/data
root@autodl-container-03dd44a781-f2a6258d:~# ls -lh /root/autodl-fs/data
ls: cannot access '/root/autodl-fs/data': No such file or directory
root@autodl-container-03dd44a781-f2a6258d:~# find /root/autodl-fs/data -name "gpu_bundle_fast_v1.zip"
find: ‘/root/autodl-fs/data’: No such file or directory
root@autodl-container-03dd44a781-f2a6258d:~# readlink -f /root/autodl-fs
/autodl-fs/data
root@autodl-container-03dd44a781-f2a6258d:~# ls -lh /root/autodl-fs/
total 580M
-rw-r--r-- 1 root root 580M Sep 13 01:47 gpu_bundle_fast_v1.zip
root@autodl-container-03dd44a781-f2a6258d:~# mkdir -p /root/autodl-fs/RewardLens/bundles
root@autodl-container-03dd44a781-f2a6258d:~# mv /root/autodl-fs/gpu_bundle_fast_v1.zip \
   /root/autodl-fs/RewardLens/bundles/
root@autodl-container-03dd44a781-f2a6258d:~# ls -lh /root/autodl-fs/RewardLens/bundles/
total 580M
-rw-r--r-- 1 root root 580M Sep 13 01:47 gpu_bundle_fast_v1.zip
root@autodl-container-03dd44a781-f2a6258d:~# cd /root/autodl-fs/RewardLens/bundles
root@autodl-container-03dd44a781-f2a6258d:~/autodl-fs/RewardLens/bundles# mkdir -p gpu_bundle_fast_v1
root@autodl-container-03dd44a781-f2a6258d:~/autodl-fs/RewardLens/bundles# unzip -q gpu_bundle_fast_v1.zip -d gpu_bundle_fast_v1

root@autodl-container-03dd44a781-f2a6258d:~/autodl-fs/RewardLens/bundles# 
root@autodl-container-03dd44a781-f2a6258d:~/autodl-fs/RewardLens/bundles# du -sh gpu_bundle_fast_v1
find gpu_bundle_fast_v1 -maxdepth 2 -type f | head -40
595M    gpu_bundle_fast_v1
gpu_bundle_fast_v1/gpu_bundle_fast_v1/bundle_meta.json
gpu_bundle_fast_v1/gpu_bundle_fast_v1/bundle_validate.json
gpu_bundle_fast_v1/gpu_bundle_fast_v1/bundle_verify.json
gpu_bundle_fast_v1/gpu_bundle_fast_v1/GPU_RUNBOOK.md
gpu_bundle_fast_v1/gpu_bundle_fast_v1/requirements-gpu.lock
gpu_bundle_fast_v1/gpu_bundle_fast_v1/requirements-gpu.txt
gpu_bundle_fast_v1/gpu_bundle_fast_v1/SHA256SUMS.txt
root@autodl-container-03dd44a781-f2a6258d:~/autodl-fs/RewardLens/bundles# du -sh gpu_bundle_fast_v1
find gpu_bundle_fast_v1 -maxdepth 2 -type f | head -40
595M    gpu_bundle_fast_v1
gpu_bundle_fast_v1/gpu_bundle_fast_v1/bundle_meta.json
gpu_bundle_fast_v1/gpu_bundle_fast_v1/bundle_validate.json
gpu_bundle_fast_v1/gpu_bundle_fast_v1/bundle_verify.json
gpu_bundle_fast_v1/gpu_bundle_fast_v1/GPU_RUNBOOK.md
gpu_bundle_fast_v1/gpu_bundle_fast_v1/requirements-gpu.lock
gpu_bundle_fast_v1/gpu_bundle_fast_v1/requirements-gpu.txt
gpu_bundle_fast_v1/gpu_bundle_fast_v1/SHA256SUMS.txt
root@autodl-container-03dd44a781-f2a6258d:~/autodl-fs/RewardLens/bundles# BUNDLE=/root/autodl-fs/RewardLens/bundles/gpu_bundle_fast_v1/gpu_bundle_fast_v1
root@autodl-container-03dd44a781-f2a6258d:~/autodl-fs/RewardLens/bundles# ls -lah "$BUNDLE"
total 594K
drwxr-xr-x 7 root root 4.0K Sep 12 23:03 .
drwxr-xr-x 3 root root 4.0K Sep 13 02:27 ..
-rw-r--r-- 1 root root 1.6K Sep 12 21:18 GPU_RUNBOOK.md
-rw-r--r-- 1 root root 559K Sep 12 23:03 SHA256SUMS.txt
-rw-r--r-- 1 root root 1.9K Sep 12 23:02 bundle_meta.json
-rw-r--r-- 1 root root  160 Sep 12 23:03 bundle_validate.json
-rw-r--r-- 1 root root  214 Sep 12 23:06 bundle_verify.json
drwxr-xr-x 2 root root 4.0K Sep 12 09:43 cloud_staging
drwxr-xr-x 2 root root 4.0K Sep 12 23:02 gqa_images
drwxr-xr-x 4 root root 4.0K Sep 12 23:02 images
drwxr-xr-x 6 root root 4.0K Sep 12 23:02 manifests
-rw-r--r-- 1 root root  547 Sep 12 09:46 requirements-gpu.lock
-rw-r--r-- 1 root root  175 Sep 12 23:02 requirements-gpu.txt
drwxr-xr-x 8 root root 4.0K Sep 12 23:02 rewardlens
root@autodl-container-03dd44a781-f2a6258d:~/autodl-fs/RewardLens/bundles# find "$BUNDLE" -maxdepth 4 -type f | grep -E \
"cloud_staging|download_models|verify_cloud|signal_gate_models|model_registry|gpu_preflight|requirements|RUNBOOK" | sort
/root/autodl-fs/RewardLens/bundles/gpu_bundle_fast_v1/gpu_bundle_fast_v1/GPU_RUNBOOK.md
/root/autodl-fs/RewardLens/bundles/gpu_bundle_fast_v1/gpu_bundle_fast_v1/cloud_staging/README_CLOUD_STAGE.md
/root/autodl-fs/RewardLens/bundles/gpu_bundle_fast_v1/gpu_bundle_fast_v1/cloud_staging/SHA256SUMS.txt
/root/autodl-fs/RewardLens/bundles/gpu_bundle_fast_v1/gpu_bundle_fast_v1/cloud_staging/download_models.sh
/root/autodl-fs/RewardLens/bundles/gpu_bundle_fast_v1/gpu_bundle_fast_v1/cloud_staging/stage_autodl_nogpu.sh
/root/autodl-fs/RewardLens/bundles/gpu_bundle_fast_v1/gpu_bundle_fast_v1/cloud_staging/sync_gpu_bundle.sh
/root/autodl-fs/RewardLens/bundles/gpu_bundle_fast_v1/gpu_bundle_fast_v1/cloud_staging/sync_results_back.sh
/root/autodl-fs/RewardLens/bundles/gpu_bundle_fast_v1/gpu_bundle_fast_v1/cloud_staging/verify_cloud_stage.sh
/root/autodl-fs/RewardLens/bundles/gpu_bundle_fast_v1/gpu_bundle_fast_v1/requirements-gpu.lock
/root/autodl-fs/RewardLens/bundles/gpu_bundle_fast_v1/gpu_bundle_fast_v1/requirements-gpu.txt
/root/autodl-fs/RewardLens/bundles/gpu_bundle_fast_v1/gpu_bundle_fast_v1/rewardlens/models/model_registry.json
/root/autodl-fs/RewardLens/bundles/gpu_bundle_fast_v1/gpu_bundle_fast_v1/rewardlens/models/model_registry.yaml
/root/autodl-fs/RewardLens/bundles/gpu_bundle_fast_v1/gpu_bundle_fast_v1/rewardlens/models/signal_gate_models.yaml
/root/autodl-fs/RewardLens/bundles/gpu_bundle_fast_v1/gpu_bundle_fast_v1/rewardlens/scripts/run_gpu_preflight.sh
root@autodl-container-03dd44a781-f2a6258d:~/autodl-fs/RewardLens/bundles# mkdir -p /root/autodl-fs/RewardLens/{models,datasets,results,logs,checksums}
root@autodl-container-03dd44a781-f2a6258d:~/autodl-fs/RewardLens/bundles# ls -lah /root/autodl-fs/RewardLens
total 32K
drwxr-xr-x 8 root root 4.0K Sep 13 02:31 .
drwxrwxrwx 4 root root 4.0K Sep 13 02:26 ..
drwxr-xr-x 3 root root 4.0K Sep 13 02:27 bundles
drwxr-xr-x 2 root root 4.0K Sep 13 02:31 checksums
drwxr-xr-x 2 root root 4.0K Sep 13 02:31 datasets
drwxr-xr-x 2 root root 4.0K Sep 13 02:31 logs
drwxr-xr-x 2 root root 4.0K Sep 13 02:31 models
drwxr-xr-x 2 root root 4.0K Sep 13 02:31 results
root@autodl-container-03dd44a781-f2a6258d:~/autodl-fs/RewardLens/bundles# cd "$BUNDLE"
root@autodl-container-03dd44a781-f2a6258d:~/autodl-fs/RewardLens/bundles/gpu_bundle_fast_v1/gpu_bundle_fast_v1# cd "$BUNDLE"
root@autodl-container-03dd44a781-f2a6258d:~/autodl-fs/RewardLens/bundles/gpu_bundle_fast_v1/gpu_bundle_fast_v1# cat rewardlens/models/signal_gate_models.yaml
# Signal Gate P0 — 4 families, UNTESTED
# Engineering first wave only. Not a scientific ranking.
models:
  - model_id: qwen3_vl_4b_instruct
    family: qwen_vl
    checkpoint: Qwen/Qwen3-VL-4B-Instruct
    rank: P0
    role: general_mllm_judge
  - model_id: gemma3_4b_it
    family: gemma
    checkpoint: google/gemma-3-4b-it
    rank: P0
    role: different_family_mllm
  - model_id: molmo_7b_d_0924
    family: molmo
    checkpoint: allenai/Molmo-7B-D-0924
    rank: P0
    role: another_architecture
  - model_id: skywork_vl_reward_7b
    family: specialized_vl_reward
    checkpoint: Skywork/Skywork-VL-Reward-7B
    rank: P0
    role: specialized_multimodal_reward
policy:
  families: 4
  status: UNTESTED
  skip_after_minutes: 40
root@autodl-container-03dd44a781-f2a6258d:~/autodl-fs/RewardLens/bundles/gpu_bundle_fast_v1/gpu_bundle_fast_v1# sed -n '1,200p' cloud_staging/download_models.sh
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
root@autodl-container-03dd44a781-f2a6258d:~/autodl-fs/RewardLens/bundles/gpu_bundle_fast_v1/gpu_bundle_fast_v1# sed -n '1,220p' cloud_staging/README_CLOUD_STAGE.md
# AutoDL no-GPU staging first, then GPU compute.

Assume:

```
/root/autodl-tmp/RewardLens/   # fast local disk
    code/ data/ models/ cache/ outputs/ logs/
/root/autodl-fs/RewardLens/    # persistent
    bundles/ datasets/ models/ results/ checksums/
```

Override with `REWARDLENS_CLOUD_TMP` and `REWARDLENS_CLOUD_FS`.

## Workflow

1. Local Windows prepares bundles (this repo).
2. Create AutoDL **no-GPU** instance (user action).
3. `bash cloud_staging/sync_gpu_bundle.sh` then `bash cloud_staging/stage_autodl_nogpu.sh`
4. `bash cloud_staging/download_models.sh`  (internet allowed here)
5. `bash cloud_staging/verify_cloud_stage.sh`
6. Switch the instance to GPU / A800. Do **not** download during paid GPU if avoidable.
7. `export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`
8. `bash rewardlens/scripts/run_gpu_preflight.sh`
9. `bash rewardlens/scripts/run_signal_pipeline.sh`
10. If engineering sanity PASS: `bash rewardlens/scripts/run_full_pipeline.sh`
11. `bash cloud_staging/sync_results_back.sh`

Do not rent GPU from this local task. Staging scripts are the deliverable.

## Exact user action required

Create or identify an AutoDL no-GPU machine and set:

```
export REWARDLENS_SSH=user@host
export REWARDLENS_CLOUD_TMP=/root/autodl-tmp/RewardLens
export REWARDLENS_CLOUD_FS=/root/autodl-fs/RewardLens
```

Then run the sync/stage scripts. Hugging Face gated models (Gemma, Llama) need `huggingface-cli login` on the staging machine.
root@autodl-container-03dd44a781-f2a6258d:~/autodl-fs/RewardLens/bundles/gpu_bundle_fast_v1/gpu_bundle_fast_v1# 
````



```
  os.environ.pop("HF_HUB_OFFLINE", None)
        os.environ.pop("TRANSFORMERS_OFFLINE", None)
    project = os.path.dirname(ROOT)
    worker_index = args.worker_index if args.worker_index is not None else (args.worker if args.worker is not None else 0)
    num_workers = args.num_workers if args.worker is None else 2
    manifest_root = resolve_manifest_root(project, args.manifest_root)
    out_root = args.out_root or os.path.join(project, "outputs", "runs", "worker_%d_of_%d" % (worker_index, num_workers))
    combined_static = first_existing(
        [
            os.path.join(project, "datasets", "processed", "fast_eval", "static_manifest.jsonl"),
            os.path.join(project, "manifests", "fast_eval", "static_manifest.jsonl"),
            os.path.join(project, "manifests", "static_manifest.jsonl"),
            os.path.join(project, "datasets", "gqa", "derived", "gqa_static_manifest.jsonl"),
        ]
    )
    combined_down = first_existing(
        [
            os.path.join(project, "datasets", "processed", "fast_eval", "downstream_manifest.jsonl"),
            os.path.join(project, "manifests", "fast_eval", "downstream_manifest.jsonl"),
            os.path.join(project, "manifests", "downstream_manifest.jsonl"),
            os.path.join(project, "datasets", "gqa", "derived", "gqa_downstream_manifest.jsonl"),
        ]
    )
    images_root = None
    for candidate in (
        os.path.join(project, "gqa_images"),
        os.path.join(project, "datasets", "gqa", "images"),
        os.path.join(project, "images"),
    ):
        if os.path.isdir(candidate):
            images_root = candidate
            break
    manifests = {
        "probe": os.path.join(manifest_root, "compatibility_probe_manifest.jsonl"),
        "signal_gate": os.path.join(manifest_root, "gpu_signal_gate_manifest.jsonl")
        if os.path.isfile(os.path.join(manifest_root, "gpu_signal_gate_manifest.jsonl"))
        else os.path.join(manifest_root, "signal_gate_manifest.jsonl"),
        "full_audit": os.path.join(manifest_root, "audit_manifest.jsonl"),
        "gqa_static": combined_static,
        "gqa_bon": combined_down,
    }
    if args.worker is not None and args.worker_index is None:
        models = models_for_worker(args.worker)
    else:
        models = models_for_shard(worker_index, num_workers)
    stages = STAGES if args.stage == "all" else (args.stage,)
    log_path = os.path.join(out_root, "worker_log.jsonl")
    os.makedirs(out_root, exist_ok=True)
    print("WORKER", worker_index, "of", num_workers, "models", [m["model_id"] for m in models], flush=True)
    missing = [path for path in manifests.values() if not os.path.isfile(path)]
    if missing and args.stage in {"all", "probe", "signal_gate", "full_audit"}:
        print("MANIFEST_MISSING", missing, flush=True)
    for rec in models:
        model_id = rec["model_id"]
        probe_out = os.path.join(out_root, model_id, "probe.jsonl")
        probe = run_stage("probe", model_id, manifests["probe"], probe_out, args.compat_timeout_sec, images_root)
        append_log(log_path, probe)
        if probe["status"] != "ok":
            append_log(
                log_path,
                {
                    "model_id": model_id,
                    "status": "INCOMPATIBLE",
                    "reason": "compatibility probe did not finish cleanly within timeout",
                    "seconds": probe["seconds"],
                },
            )
            print("SKIP_INCOMPATIBLE", model_id, probe, flush=True)
            continue
        for stage in stages:
            if stage == "probe":
                continue
            out_jsonl = os.path.join(out_root, model_id, "%s.jsonl" % stage)
            result = run_stage(stage, model_id, manifests[stage], out_jsonl, None, images_root)
            append_log(log_path, result)
            print(json.dumps(result), flush=True)
    print("WORKER_DONE", worker_index, flush=True)
    return 0


def append_log(path: str, row: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")
        handle.flush()


if __name__ == "__main__":
    raise SystemExit(main())
(venv) root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# grep -RniE "argparse|add_argument|model_id|model_registry|signal_gate_models|limit|max_samples|probe|signal_gate" \
rewardlens/inference rewardlens/models | head -160
grep: rewardlens/inference/__pycache__/__init__.cpython-312.pyc: binary file matches
grep: rewardlens/inference/__pycache__/common.cpython-312.pyc: binary file matches
grep: rewardlens/inference/__pycache__/device.cpython-312.pyc: binary file matches
grep: rewardlens/inference/__pycache__/metrics.cpython-312.pyc: binary file matches
grep: rewardlens/inference/__pycache__/__init__.cpython-310.pyc: binary file matches
grep: rewardlens/inference/__pycache__/device.cpython-310.pyc: binary file matches
grep: rewardlens/inference/adapters/__pycache__/base.cpython-312.pyc: binary file matches
grep: rewardlens/inference/adapters/__pycache__/dummy.cpython-312.pyc: binary file matches
grep: rewardlens/inference/adapters/__pycache__/hf_vlm.cpython-312.pyc: binary file matches
rewardlens/inference/adapters/base.py:10:    model_id: str = "unknown"
rewardlens/inference/adapters/dummy.py:12:    def __init__(self, model_id: str = "dummy_cpu", fail_mode: str | None = None):
rewardlens/inference/adapters/dummy.py:13:        self.model_id = model_id
rewardlens/inference/adapters/hf_vlm.py:25:        model_id: str,
rewardlens/inference/adapters/hf_vlm.py:36:        self.model_id = model_id
rewardlens/inference/adapters/hf_vlm.py:53:                % self.model_id
rewardlens/inference/adapters/hf_vlm.py:56:            raise RuntimeError("%s requires quantization; bitsandbytes is not a default backend." % self.model_id)
rewardlens/inference/__init__.py:3:from .device import format_probe_text, probe_device, write_probe
rewardlens/inference/__init__.py:5:__all__ = ["probe_device", "format_probe_text", "write_probe"]
rewardlens/inference/common.py:25:    model_id: str,
rewardlens/inference/common.py:40:        "model_id": model_id,
rewardlens/inference/common.py:113:    model_id: str,
rewardlens/inference/common.py:187:            model_id=model_id,
rewardlens/inference/common.py:211:                    "model_id": model_id,
rewardlens/inference/device.py:1:"""Dual-backend device probe: CUDA and ROCm/HIP.
rewardlens/inference/device.py:23:def probe_device() -> dict[str, Any]:
rewardlens/inference/device.py:87:def format_probe_text(report: dict[str, Any]) -> str:
rewardlens/inference/device.py:100:def write_probe(path: str, report: dict[str, Any] | None = None) -> dict[str, Any]:
rewardlens/inference/device.py:101:    report = report or probe_device()
rewardlens/inference/metrics.py:21:        key = (str(row.get("model_id")), str(row.get("triplet_id")))
rewardlens/inference/metrics.py:41:    for (model_id, triplet_id), variants in grouped.items():
rewardlens/inference/metrics.py:63:        bucket = by_model_factor[(model_id, factor)]
rewardlens/inference/metrics.py:72:    for (model_id, factor), bucket in sorted(by_model_factor.items()):
rewardlens/inference/metrics.py:78:                "model_id": model_id,
rewardlens/inference/metrics.py:102:        grouped[(str(row.get("model_id")), str(row.get("factor")))].append(int(pred == gold))
rewardlens/inference/metrics.py:104:    for (model_id, factor), vals in sorted(grouped.items()):
rewardlens/inference/metrics.py:107:                "model_id": model_id,
rewardlens/inference/run_probe.py:14:    raise SystemExit(main_with_stage("compatibility_probe"))
rewardlens/inference/run_signal_gate.py:14:    raise SystemExit(main_with_stage("signal_gate"))
rewardlens/inference/run_worker.py:9:import argparse
rewardlens/inference/run_worker.py:23:STAGES = ("probe", "signal_gate", "full_audit", "gqa_static", "gqa_bon")
rewardlens/inference/run_worker.py:33:def run_stage(stage: str, model_id: str, manifest: str, out_jsonl: str, timeout: int | None, images_root: str | None = None) -> dict:
rewardlens/inference/run_worker.py:35:        "probe": os.path.join(ROOT, "inference", "run_probe.py"),
rewardlens/inference/run_worker.py:36:        "signal_gate": os.path.join(ROOT, "inference", "run_signal_gate.py"),
rewardlens/inference/run_worker.py:51:        model_id,
rewardlens/inference/run_worker.py:69:        "model_id": model_id,
rewardlens/inference/run_worker.py:81:    signal = os.path.join(project, "outputs", "signal_gate_v1")
rewardlens/inference/run_worker.py:84:    if os.path.isfile(os.path.join(signal, "signal_gate_manifest.jsonl")):
rewardlens/inference/run_worker.py:90:    parser = argparse.ArgumentParser()
rewardlens/inference/run_worker.py:91:    parser.add_argument("--worker", type=int, default=None, help="legacy 0/1 using registry worker field")
rewardlens/inference/run_worker.py:92:    parser.add_argument("--worker-index", type=int, default=None)
rewardlens/inference/run_worker.py:93:    parser.add_argument("--num-workers", type=int, default=2)
rewardlens/inference/run_worker.py:94:    parser.add_argument("--stage", default="all", choices=["all", *STAGES])
rewardlens/inference/run_worker.py:95:    parser.add_argument("--manifest-root", default=None)
rewardlens/inference/run_worker.py:96:    parser.add_argument("--out-root", default=None)
rewardlens/inference/run_worker.py:97:    parser.add_argument("--compat-timeout-sec", type=int, default=COMPAT_TIMEOUT_SEC)
rewardlens/inference/run_worker.py:98:    parser.add_argument("--online", action="store_true", help="do not force HF offline env")
rewardlens/inference/run_worker.py:134:        "probe": os.path.join(manifest_root, "compatibility_probe_manifest.jsonl"),
rewardlens/inference/run_worker.py:135:        "signal_gate": os.path.join(manifest_root, "gpu_signal_gate_manifest.jsonl")
rewardlens/inference/run_worker.py:136:        if os.path.isfile(os.path.join(manifest_root, "gpu_signal_gate_manifest.jsonl"))
rewardlens/inference/run_worker.py:137:        else os.path.join(manifest_root, "signal_gate_manifest.jsonl"),
rewardlens/inference/run_worker.py:149:    print("WORKER", worker_index, "of", num_workers, "models", [m["model_id"] for m in models], flush=True)
rewardlens/inference/run_worker.py:151:    if missing and args.stage in {"all", "probe", "signal_gate", "full_audit"}:
rewardlens/inference/run_worker.py:154:        model_id = rec["model_id"]
rewardlens/inference/run_worker.py:155:        probe_out = os.path.join(out_root, model_id, "probe.jsonl")
rewardlens/inference/run_worker.py:156:        probe = run_stage("probe", model_id, manifests["probe"], probe_out, args.compat_timeout_sec, images_root)
rewardlens/inference/run_worker.py:157:        append_log(log_path, probe)
rewardlens/inference/run_worker.py:158:        if probe["status"] != "ok":
rewardlens/inference/run_worker.py:162:                    "model_id": model_id,
rewardlens/inference/run_worker.py:164:                    "reason": "compatibility probe did not finish cleanly within timeout",
rewardlens/inference/run_worker.py:165:                    "seconds": probe["seconds"],
rewardlens/inference/run_worker.py:168:            print("SKIP_INCOMPATIBLE", model_id, probe, flush=True)
rewardlens/inference/run_worker.py:171:            if stage == "probe":
rewardlens/inference/run_worker.py:173:            out_jsonl = os.path.join(out_root, model_id, "%s.jsonl" % stage)
rewardlens/inference/run_worker.py:174:            result = run_stage(stage, model_id, manifests[stage], out_jsonl, None, images_root)
rewardlens/inference/runner_lib.py:2:"""Shared CLI runner used by probe / signal-gate / full-audit scripts."""
rewardlens/inference/runner_lib.py:6:import argparse
rewardlens/inference/runner_lib.py:17:from inference.device import probe_device, write_probe  # noqa: E402
rewardlens/inference/runner_lib.py:21:def build_adapter(args: argparse.Namespace):
rewardlens/inference/runner_lib.py:23:        adapter = DummyAdapter(model_id=args.model_id, fail_mode=args.fail_mode or None)
rewardlens/inference/runner_lib.py:28:    rec = get_model(args.model_id)
rewardlens/inference/runner_lib.py:35:        model_id=rec["model_id"],
rewardlens/inference/runner_lib.py:46:def add_common_args(parser: argparse.ArgumentParser) -> None:
rewardlens/inference/runner_lib.py:47:    parser.add_argument("--manifest", required=True)
rewardlens/inference/runner_lib.py:48:    parser.add_argument("--out-jsonl", required=True)
rewardlens/inference/runner_lib.py:49:    parser.add_argument("--fail-jsonl", default=None)
rewardlens/inference/runner_lib.py:50:    parser.add_argument("--model-id", default="dummy_cpu")
rewardlens/inference/runner_lib.py:51:    parser.add_argument("--adapter", choices=["dummy", "hf", "qwen_vl", "gemma", "llama_vision", "molmo", "specialized_reward"], default="dummy")
rewardlens/inference/runner_lib.py:52:    parser.add_argument("--images-root", default=None)
rewardlens/inference/runner_lib.py:53:    parser.add_argument("--fail-mode", default="", help="dummy only: oom|error|parse|timeout")
rewardlens/inference/runner_lib.py:54:    parser.add_argument("--limit", type=int, default=0)
rewardlens/inference/runner_lib.py:55:    parser.add_argument("--env-json", default=None)
rewardlens/inference/runner_lib.py:59:    parser = argparse.ArgumentParser()
rewardlens/inference/runner_lgrep: ib.py:65:    if args.limit:
rewardlens/inference/runner_lib.py:66:        items = items[: args.limit]
rewardlens/inference/runner_lib.py:67:    report = probe_device()
rewardlens/inference/runner_lib.py:69:    report["model_id"] = args.model_id
rewardlens/inference/runner_lib.py:70:    write_probe(env_path, report)
rewardlens/inference/runner_lib.py:77:            model_id=args.model_id,
rewardlens/models/__pycache__/registry.cpython-312.pyc: binary file matches
rewardlens/models/model_download_plan.csv:1:model_id,family,rank,checkpoint,revision,parameter_size,estimated_gb,source,fallback,license,bf16,sdpa,custom_kernel_risk,status,worker_2of2,notes
rewardlens/models/model_registry.json:16:      "model_id": "qwen3_vl_4b_instruct",
rewardlens/models/model_registry.json:38:      "model_id": "gemma3_4b_it",
rewardlens/models/model_registry.json:60:      "model_id": "molmo_7b_d_0924",
rewardlens/models/model_registry.json:81:      "model_id": "skywork_vl_reward_7b",
rewardlens/models/model_registry.json:103:      "model_id": "qwen3_vl_8b_instruct",
rewardlens/models/model_registry.json:124:      "model_id": "gemma3_12b_it",
rewardlens/models/model_registry.json:145:      "model_id": "internvl3_8b",
rewardlens/models/model_registry.json:167:      "model_id": "llama32_11b_vision_instruct",
rewardlens/models/model_registry.json:189:      "model_id": "qwen2_5_vl_7b_instruct",
rewardlens/models/model_registry.json:211:      "model_id": "molmo_7b_o_0924",
rewardlens/models/model_registry.json:233:      "model_id": "ixc25_reward_7b",
rewardlens/models/model_registry.yaml:12:  - model_id: qwen3_vl_4b_instruct
rewardlens/models/model_registry.yaml:31:  - model_id: qwen3_vl_8b_instruct
rewardlens/models/model_registry.yaml:50:  - model_id: qwen2_5_vl_7b_instruct
rewardlens/models/model_registry.yaml:69:  - model_id: gemma3_4b_it
rewardlens/models/model_registry.yaml:88:  - model_id: gemma3_12b_it
rewardlens/models/model_registry.yaml:106:  - model_id: llama32_11b_vision_instruct
rewardlens/models/model_registry.yaml:125:  - model_id: molmo_7b_d_0924
rewardlens/models/model_registry.yaml:144:  - model_id: molmo_7b_o_0924
rewardlens/models/model_registry.yaml:162:  - model_id: internvl3_8b
rewardlens/models/model_registry.yaml:181:  - model_id: skywork_vl_reward_7b
rewardlens/models/model_registry.yaml:200:  - model_id: ixc25_reward_7b
rewardlens/models/model_stage_manifest.json:7:      "model_id": "qwen3_vl_4b_instruct",
rewardlens/models/model_stage_manifest.json:19:      "model_id": "gemma3_4b_it",
rewardlens/models/model_stage_manifest.json:32:      "model_id": "molmo_7b_d_0924",
rewardlens/models/model_stage_manifest.json:44:      "model_id": "skywork_vl_reward_7b",
rewardlens/models/registry.py:8:JSON_PATH = os.path.join(ROOT, "models", "model_registry.json")
rewardlens/models/registry.py:9:YAML_PATH = os.path.join(ROOT, "models", "model_registry.yaml")
rewardlens/models/registry.py:38:def get_model(model_id: str) -> dict[str, Any]:
rewardlens/models/registry.py:40:        if rec.get("model_id") == model_id:
rewardlens/models/registry.py:42:    raise KeyError("unknown model_id: %s" % model_id)
rewardlens/models/replacement_models.yaml:3:  - model_id: qwen2_5_vl_7b_instruct
rewardlens/models/replacement_models.yaml:7:  - model_id: molmo_7b_o_0924
rewardlens/models/replacement_models.yaml:11:  - model_id: ixc25_reward_7b
rewardlens/models/replacement_models.yaml:15:  - model_id: internvl3_8b
rewardlens/models/signal_gate_models.yaml:4:  - model_id: qwen3_vl_4b_instruct
rewardlens/models/signal_gate_models.yaml:9:  - model_id: gemma3_4b_it
rewardlens/models/signal_gate_models.yaml:14:  - model_id: molmo_7b_d_0924
rewardlens/models/signal_gate_models.yaml:19:  - model_id: skywork_vl_reward_7b
(venv) root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# sed -n '1,260p' rewardlens/models/model_registry.yaml
schema_version: 1
status: UNTESTED_REGISTRY_ONLY
weights_downloaded: false
local_device: cpu
note: >
  No checkpoint is marked compatible. Status starts at UNTESTED for every
  system. Do not download weights on the CPU host. Default inference path is
  bf16 + Transformers + SDPA/eager. flash-attn, CUDA custom kernels, and
  bitsandbytes are optional capabilities, never defaults.

models:
  - model_id: qwen3_vl_4b_instruct
    family: qwen_vl
    model_type: general_mllm_as_judge
    checkpoint: Qwen/Qwen3-VL-4B-Instruct
    revision: main
    license: apache-2.0
    parameter_size: 4B
    expected_vram: 10GB_bf16
    transformers_support: expected
    rocm_expected: unknown
    cuda_expected: unknown
    requires_custom_kernel: false
    requires_flash_attention: false
    requires_quantization: false
    prompt_adapter: pairwise_ab
    parser: ab_parser
    status: UNTESTED
    notes: First ROCm carrier. Transformers Qwen3VLForConditionalGeneration.

  - model_id: qwen3_vl_8b_instruct
    family: qwen_vl
    model_type: general_mllm_as_judge
    checkpoint: Qwen/Qwen3-VL-8B-Instruct
    revision: main
    license: apache-2.0
    parameter_size: 8B
    expected_vram: 18GB_bf16
    transformers_support: expected
    rocm_expected: unknown
    cuda_expected: unknown
    requires_custom_kernel: false
    requires_flash_attention: false
    requires_quantization: false
    prompt_adapter: pairwise_ab
    parser: ab_parser
    status: UNTESTED
    notes: Second ROCm carrier after 4B qualification.

  - model_id: qwen2_5_vl_7b_instruct
    family: qwen_vl
    model_type: general_mllm_as_judge
    checkpoint: Qwen/Qwen2.5-VL-7B-Instruct
    revision: main
    license: apache-2.0
    parameter_size: 7B
    expected_vram: 16GB_bf16
    transformers_support: expected
    rocm_expected: unknown
    cuda_expected: unknown
    requires_custom_kernel: false
    requires_flash_attention: false
    requires_quantization: false
    prompt_adapter: pairwise_ab
    parser: ab_parser
    status: UNTESTED
    notes: Same family as Qwen3-VL for cluster bootstrap.

  - model_id: gemma3_4b_it
    family: gemma
    model_type: general_mllm_as_judge
    checkpoint: google/gemma-3-4b-it
    revision: main
    license: gemma
    parameter_size: 4B
    expected_vram: 10GB_bf16
    transformers_support: expected
    rocm_expected: unknown
    cuda_expected: unknown
    requires_custom_kernel: false
    requires_flash_attention: false
    requires_quantization: false
    prompt_adapter: pairwise_ab
    parser: ab_parser
    status: UNTESTED
    notes: Gated license. Bidirectional image attention may be backend-sensitive.

  - model_id: gemma3_12b_it
    family: gemma
    model_type: general_mllm_as_judge
    checkpoint: google/gemma-3-12b-it
    revision: main
    license: gemma
    parameter_size: 12B
    expected_vram: 28GB_bf16
    transformers_support: expected
    rocm_expected: unknown
    cuda_expected: unknown
    requires_custom_kernel: false
    requires_flash_attention: false
    requires_quantization: false
    prompt_adapter: pairwise_ab
    parser: ab_parser
    status: UNTESTED

  - model_id: llama32_11b_vision_instruct
    family: llama_vision
    model_type: general_mllm_as_judge
    checkpoint: meta-llama/Llama-3.2-11B-Vision-Instruct
    revision: main
    license: llama3.2
    parameter_size: 11B
    expected_vram: 24GB_bf16
    transformers_support: expected
    rocm_expected: unknown
    cuda_expected: unknown
    requires_custom_kernel: unknown
    requires_flash_attention: false
    requires_quantization: false
    prompt_adapter: pairwise_ab
    parser: ab_parser
    status: UNTESTED
    notes: Gated license. Mllama stack has historically carried CUDA-only risk.

  - model_id: molmo_7b_d_0924
    family: molmo
    model_type: general_mllm_as_judge
    checkpoint: allenai/Molmo-7B-D-0924
    revision: main
    license: apache-2.0
    parameter_size: 7B
    expected_vram: 16GB_bf16
    transformers_support: expected
    rocm_expected: unknown
    cuda_expected: unknown
    requires_custom_kernel: false
    requires_flash_attention: false
    requires_quantization: false
    prompt_adapter: pairwise_ab
    parser: ab_parser
    status: UNTESTED
    notes: trust_remote_code may be required; still UNTESTED.

  - model_id: molmo_7b_o_0924
    family: molmo
    model_type: general_mllm_as_judge
    checkpoint: allenai/Molmo-7B-O-0924
    revision: main
    license: apache-2.0
    parameter_size: 7B
    expected_vram: 16GB_bf16
    transformers_support: expected
    rocm_expected: unknown
    cuda_expected: unknown
    requires_custom_kernel: false
    requires_flash_attention: false
    requires_quantization: false
    prompt_adapter: pairwise_ab
    parser: ab_parser
    status: UNTESTED

  - model_id: internvl3_8b
    family: internvl
    model_type: general_mllm_as_judge
    checkpoint: OpenGVLab/InternVL3-8B
    revision: main
    license: mit
    parameter_size: 8B
    expected_vram: 18GB_bf16
    transformers_support: expected
    rocm_expected: unknown
    cuda_expected: unknown
    requires_custom_kernel: unknown
    requires_flash_attention: false
    requires_quantization: false
    prompt_adapter: pairwise_ab
    parser: ab_parser
    status: UNTESTED
    notes: Often ships custom modeling code. CUDA custom-kernel risk if flash-attn is forced.

  - model_id: skywork_vl_reward_7b
    family: specialized_vl_reward
    model_type: dedicated_multimodal_reward
    checkpoint: Skywork/Skywork-VL-Reward-7B
    revision: main
    license: unknown
    parameter_size: 7B
    expected_vram: 16GB_bf16
    transformers_support: unknown
    rocm_expected: unknown
    cuda_expected: unknown
    requires_custom_kernel: unknown
    requires_flash_attention: false
    requires_quantization: false
    prompt_adapter: pairwise_ab
    parser: ab_parser
    status: UNTESTED
    notes: Qwen2.5-VL backbone with a value head. Backbone family is qwen_vl; cluster by specialized_vl_reward unless confirmatory plan is revised.

  - model_id: ixc25_reward_7b
    family: specialized_vl_reward
    model_type: dedicated_multimodal_reward
    checkpoint: internlm/internlm-xcomposer2d5-7b-reward
    revision: main
    license: unknown
    parameter_size: 7B
    expected_vram: 16GB_bf16
    transformers_support: unknown
    rocm_expected: unknown
    cuda_expected: unknown
    requires_custom_kernel: unknown
    requires_flash_attention: false
    requires_quantization: false
    prompt_adapter: pairwise_ab
    parser: ab_parser
    status: UNTESTED
    notes: Checkpoint id must be re-verified on GPU host before download. Do not mark compatible in advance.
(venv) root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# cd /root/autodl-tmp/RewardLens/code

echo "===== runner_lib ====="
sed -n '1,150p' rewardlens/inference/runner_lib.py

echo "===== hf_vlm ====="
sed -n '1,260p' rewardlens/inference/adapters/hf_vlm.py

echo "===== registry ====="
sed -n '1,140p' rewardlens/models/registry.py

echo "===== manifests ====="
find . -type f \( \
  -name "compatibility_probe_manifest.jsonl" -o \
  -name "gpu_signal_gate_manifest.jsonl" -o \
  -name "signal_gate_manifest.jsonl" \
\) -print
===== runner_lib =====
#!/usr/bin/env python3
"""Shared CLI runner used by probe / signal-gate / full-audit scripts."""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from inference.adapters.dummy import DummyAdapter  # noqa: E402
from inference.common import load_items, run_items  # noqa: E402
from inference.device import probe_device, write_probe  # noqa: E402
from inference.parsers.ab_parser import parse_ab  # noqa: E402


def build_adapter(args: argparse.Namespace):
    if args.adapter == "dummy":
        adapter = DummyAdapter(model_id=args.model_id, fail_mode=args.fail_mode or None)
        return adapter
    from inference.adapters.hf_vlm import HuggingFaceVLMAdapter
    from models.registry import get_model

    rec = get_model(args.model_id)
    from inference.adapters import ADAPTERS

    cls = ADAPTERS.get(args.adapter, HuggingFaceVLMAdapter)
    if args.adapter == "hf":
        cls = HuggingFaceVLMAdapter
    adapter = cls(
        model_id=rec["model_id"],
        checkpoint=rec["checkpoint"],
        dtype="bfloat16",
        attn_implementation="sdpa",
        trust_remote_code=bool(rec.get("trust_remote_code")),
        requires_flash_attention=bool(rec.get("requires_flash_attention")),
        requires_quantization=bool(rec.get("requires_quantization")),
    )
    return adapter


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out-jsonl", required=True)
    parser.add_argument("--fail-jsonl", default=None)
    parser.add_argument("--model-id", default="dummy_cpu")
    parser.add_argument("--adapter", choices=["dummy", "hf", "qwen_vl", "gemma", "llama_vision", "molmo", "specialized_reward"], default="dummy")
    parser.add_argument("--images-root", default=None)
    parser.add_argument("--fail-mode", default="", help="dummy only: oom|error|parse|timeout")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--env-json", default=None)


def main_with_stage(stage: str) -> int:
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    args = parser.parse_args()
    fail_jsonl = args.fail_jsonl or os.path.join(os.path.dirname(args.out_jsonl), "failures.jsonl")
    env_path = args.env_json or os.path.join(os.path.dirname(args.out_jsonl), "environment_report.json")
    items = load_items(args.manifest)
    if args.limit:
        items = items[: args.limit]
    report = probe_device()
    report["stage"] = stage
    report["model_id"] = args.model_id
    write_probe(env_path, report)
    adapter = build_adapter(args)
    adapter.load_model()
    try:
        summary = run_items(
            items=items,
            adapter=adapter,
            model_id=args.model_id,
            out_jsonl=args.out_jsonl,
            fail_jsonl=fail_jsonl,
            parse_fn=parse_ab,
            images_root=args.images_root,
        )
    finally:
        adapter.cleanup()
    summary_path = os.path.join(os.path.dirname(args.out_jsonl), "run_summary.json")
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump({"stage": stage, **summary}, handle, indent=2)
    print(json.dumps({"stage": stage, **summary}, indent=2))
    return 0 if summary["failed"] == 0 or args.adapter == "dummy" else 1
===== hf_vlm =====
"""Standard Transformers VLM adapter.

Default: bf16, SDPA/eager. flash-attn / bitsandbytes are opt-in only.
Works on CUDA and ROCm (both expose torch.cuda).
"""

from __future__ import annotations

import os
from typing import Any

from .base import JudgeAdapter

PROMPT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "pairwise_ab.txt")


def load_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as handle:
        return handle.read()


class HuggingFaceVLMAdapter(JudgeAdapter):
    def __init__(
        self,
        model_id: str,
        checkpoint: str,
        *,
        dtype: str = "bfloat16",
        attn_implementation: str = "sdpa",
        max_new_tokens: int = 16,
        prompt_adapter: str = "pairwise_ab",
        trust_remote_code: bool = False,
        requires_flash_attention: bool = False,
        requires_quantization: bool = False,
    ):
        self.model_id = model_id
        self.checkpoint = checkpoint
        self.dtype_name = dtype
        self.attn_implementation = attn_implementation
        self.max_new_tokens = max_new_tokens
        self.prompt_adapter = prompt_adapter
        self.trust_remote_code = trust_remote_code
        self.requires_flash_attention = requires_flash_attention
        self.requires_quantization = requires_quantization
        self.model = None
        self.processor = None
        self.prompt_template = load_prompt()

    def load_model(self) -> None:
        if self.requires_flash_attention and self.attn_implementation == "sdpa":
            raise RuntimeError(
                "%s is marked requires_flash_attention; refuse silent CUDA-kernel fallback. Set attn explicitly."
                % self.model_id
            )
        if self.requires_quantization:
            raise RuntimeError("%s requires quantization; bitsandbytes is not a default backend." % self.model_id)

        import torch
        from transformers import AutoModelForImageTextToText, AutoProcessor

        dtype_map = {
            "bfloat16": torch.bfloat16,
            "bf16": torch.bfloat16,
            "float16": torch.float16,
            "fp16": torch.float16,
            "float32": torch.float32,
        }
        dtype = dtype_map.get(self.dtype_name, torch.bfloat16)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        attn = self.attn_implementation
        if attn == "sdpa_or_eager":
            attn = "sdpa"
        kwargs = {
            "torch_dtype": dtype,
            "trust_remote_code": self.trust_remote_code,
        }
        if attn and attn != "auto":
            kwargs["attn_implementation"] = attn
        try:
            self.model = AutoModelForImageTextToText.from_pretrained(self.checkpoint, **kwargs)
        except Exception:
            from transformers import AutoModelForCausalLM

            self.model = AutoModelForCausalLM.from_pretrained(self.checkpoint, **kwargs)
        self.model.to(device)
        self.model.eval()
        self.processor = AutoProcessor.from_pretrained(self.checkpoint, trust_remote_code=self.trust_remote_code)
        self.device = device

    def prepare_inputs(self, *, image_path: str, question: str, candidate_a: str, candidate_b: str) -> dict[str, Any]:
        from PIL import Image

        prompt = self.prompt_template.format(
            question=question,
            candidate_a=candidate_a,
            candidate_b=candidate_b,
        )
        image = Image.open(image_path).convert("RGB")
        return {"image": image, "prompt": prompt, "image_path": image_path}

    def judge(self, prepared: Any) -> dict[str, Any]:
        import torch

        if self.model is None or self.processor is None:
            raise RuntimeError("load_model() was not called")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": prepared["prompt"]},
                ],
            }
        ]
        text = self.processor.apply_chat_template(messages, add_generation_prompt=True)
        inputs = self.processor(text=[text], images=[prepared["image"]], return_tensors="pt")
        inputs = {k: v.to(self.device) if hasattr(v, "to") else v for k, v in inputs.items()}
        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                temperature=None,
            )
        trimmed = output_ids[:, inputs["input_ids"].shape[1] :]
        raw = self.processor.batch_decode(trimmed, skip_special_tokens=True)[0]
        return {"raw_output": raw, "score_a": None, "score_b": None, "margin": None}

    def cleanup(self) -> None:
        self.model = None
        self.processor = None
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
===== registry =====
from __future__ import annotations

import json
import os
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(ROOT, "models", "model_registry.json")
YAML_PATH = os.path.join(ROOT, "models", "model_registry.yaml")


def load_registry(path: str | None = None) -> dict[str, Any]:
    json_path = path or JSON_PATH
    if json_path.endswith(".yaml") or json_path.endswith(".yml"):
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("PyYAML required to read %s" % json_path) from exc
        with open(json_path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    if os.path.isfile(json_path):
        with open(json_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    if os.path.isfile(YAML_PATH):
        import yaml

        with open(YAML_PATH, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    raise FileNotFoundError("no model registry found")


def iter_models(registry: dict[str, Any] | None = None):
    registry = registry or load_registry()
    for rec in registry.get("models", []):
        yield rec


def get_model(model_id: str) -> dict[str, Any]:
    for rec in iter_models():
        if rec.get("model_id") == model_id:
            return rec
    raise KeyError("unknown model_id: %s" % model_id)


def primary_models(registry: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    out = []
    for rec in iter_models(registry):
        if rec.get("fast_track_primary") and rec.get("status") != "INCOMPATIBLE":
            out.append(rec)
    return out


def models_for_worker(worker: int, registry: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    out = []
    for rec in iter_models(registry):
        if rec.get("fast_track_primary") and int(rec.get("worker", -1)) == int(worker):
            if rec.get("status") != "INCOMPATIBLE":
                out.append(rec)
    return out


def models_for_shard(worker_index: int, num_workers: int, registry: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if num_workers < 1:
        raise ValueError("num_workers must be >= 1")
    if worker_index < 0 or worker_index >= num_workers:
        raise ValueError("worker_index must be in [0, num_workers)")
    primary = primary_models(registry)
    if num_workers == 2 and all(rec.get("worker") in (0, 1) for rec in primary):
        return [rec for rec in primary if int(rec.get("worker", -1)) == int(worker_index)]
    return [rec for i, rec in enumerate(primary) if i % num_workers == worker_index]


def family_counts(registry: dict[str, Any] | None = None) -> dict[str, int]:
    counts: dict[str, int] = {}
    for rec in iter_models(registry):
        if rec.get("fast_track_primary"):
            fam = str(rec.get("family"))
            counts[fam] = counts.get(fam, 0) + 1
    return counts
===== manifests =====
./manifests/signal_gate_v1/compatibility_probe_manifest.jsonl
./manifests/signal_gate_v1/gpu_signal_gate_manifest.jsonl
./manifests/signal_gate_v1/signal_gate_manifest.jsonl
./manifests/compatibility_probe_manifest.jsonl
./manifests/gpu_signal_gate_manifest.jsonl
(venv) root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# cd /root/autodl-tmp/RewardLens/code

cp rewardlens/models/model_registry.json \
   rewardlens/models/model_registry.json.before_local_paths

python - <<'PY'
import json

p = "rewardlens/models/model_registry.json"
data = json.load(open(p, encoding="utf-8"))

for rec in data["models"]:
    if rec["model_id"] == "qwen3_vl_4b_instruct":
        rec["checkpoint"] = "/root/autodl-fs/RewardLens/models/Qwen/Qwen3-VL-4B-Instruct"
        print("PATCHED:", rec["model_id"], "->", rec["checkpoint"])

json.dump(data, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
PY
PATCHED: qwen3_vl_4b_instruct -> /root/autodl-fs/RewardLens/models/Qwen/Qwen3-VL-4B-Instruct
(venv) root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# python - <<'PY'
from rewardlens.models.registry import get_model
print(get_model("qwen3_vl_4b_instruct")["checkpoint"])
PY
/root/autodl-fs/RewardLens/models/Qwen/Qwen3-VL-4B-Instruct
(venv) root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# mkdir -p outputs/smoke_qwen

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8

python rewardlens/inference/run_probe.py \
  --adapter hf \
  --model-id qwen3_vl_4b_instruct \
  --manifest manifests/signal_gate_v1/compatibility_probe_manifest.jsonl \
  --images-root /root/autodl-tmp/RewardLens/code/images \
  --limit 5 \
  --out-jsonl outputs/smoke_qwen/qwen_probe5.jsonl \
  2>&1 | tee outputs/smoke_qwen/qwen_probe5.log
`torch_dtype` is deprecated! Use `dtype` instead!
Loading checkpoint shards: 100%|██████████| 2/2 [00:13<00:00,  6.90s/it]
{
  "stage": "compatibility_probe",
  "ok": 0,
  "failed": 5,
  "skipped": 0,
  "out_jsonl": "outputs/smoke_qwen/qwen_probe5.jsonl"
}
(venv) root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# echo "===== RESULTS ====="
wc -l outputs/smoke_qwen/qwen_probe5.jsonl
cat outputs/smoke_qwen/qwen_probe5.jsonl

echo "===== GPU ====="
nvidia-smi
===== RESULTS =====
5 outputs/smoke_qwen/qwen_probe5.jsonl
{"item_id": "count_000000:base", "triplet_id": "count_000000", "factor": "count", "variant": "base", "model_id": "qwen3_vl_4b_instruct", "raw_output": "image missing: /root/autodl-tmp/RewardLens/code/images/D:\\01_work\\RewardLens\\outputs\\count_scale_v1\\images\\count_000000_base.png\nTraceback (most recent call last):\n  File \"/root/autodl-tmp/RewardLens/code/rewardlens/inference/common.py\", line 144, in run_items\n    raise FileNotFoundError(\"image missing: %s\" % image_path)\nFileNotFoundError: image missing: /root/autodl-tmp/RewardLens/code/images/D:\\01_work\\RewardLens\\outputs\\count_scale_v1\\images\\count_000000_base.png\n", "parsed_preference": null, "score_a": null, "score_b": null, "margin": null, "latency_ms": 0.39254873991012573, "status": "error", "candidate_a": "3", "candidate_b": "4"}
{"item_id": "count_000000:relevant", "triplet_id": "count_000000", "factor": "count", "variant": "relevant", "model_id": "qwen3_vl_4b_instruct", "raw_output": "image missing: /root/autodl-tmp/RewardLens/code/images/D:\\01_work\\RewardLens\\outputs\\count_scale_v1\\images\\count_000000_relevant.png\nTraceback (most recent call last):\n  File \"/root/autodl-tmp/RewardLens/code/rewardlens/inference/common.py\", line 144, in run_items\n    raise FileNotFoundError(\"image missing: %s\" % image_path)\nFileNotFoundError: image missing: /root/autodl-tmp/RewardLens/code/images/D:\\01_work\\RewardLens\\outputs\\count_scale_v1\\images\\count_000000_relevant.png\n", "parsed_preference": null, "score_a": null, "score_b": null, "margin": null, "latency_ms": 0.22271275520324707, "status": "error", "candidate_a": "3", "candidate_b": "4"}
{"item_id": "count_000000:irrelevant", "triplet_id": "count_000000", "factor": "count", "variant": "irrelevant", "model_id": "qwen3_vl_4b_instruct", "raw_output": "image missing: /root/autodl-tmp/RewardLens/code/images/D:\\01_work\\RewardLens\\outputs\\count_scale_v1\\images\\count_000000_irrelevant.png\nTraceback (most recent call last):\n  File \"/root/autodl-tmp/RewardLens/code/rewardlens/inference/common.py\", line 144, in run_items\n    raise FileNotFoundError(\"image missing: %s\" % image_path)\nFileNotFoundError: image missing: /root/autodl-tmp/RewardLens/code/images/D:\\01_work\\RewardLens\\outputs\\count_scale_v1\\images\\count_000000_irrelevant.png\n", "parsed_preference": null, "score_a": null, "score_b": null, "margin": null, "latency_ms": 0.20489469170570374, "status": "error", "candidate_a": "3", "candidate_b": "4"}
{"item_id": "attr_000000:base", "triplet_id": "attr_000000", "factor": "attribute", "variant": "base", "model_id": "qwen3_vl_4b_instruct", "raw_output": "image missing: /root/autodl-tmp/RewardLens/code/images/D:\\01_work\\RewardLens\\outputs\\attribute_scale_v1\\images\\attr_000000_base.png\nTraceback (most recent call last):\n  File \"/root/autodl-tmp/RewardLens/code/rewardlens/inference/common.py\", line 144, in run_items\n    raise FileNotFoundError(\"image missing: %s\" % image_path)\nFileNotFoundError: image missing: /root/autodl-tmp/RewardLens/code/images/D:\\01_work\\RewardLens\\outputs\\attribute_scale_v1\\images\\attr_000000_base.png\n", "parsed_preference": null, "score_a": null, "score_b": null, "margin": null, "latency_ms": 0.2011917531490326, "status": "error", "candidate_a": "blue", "candidate_b": "red"}
{"item_id": "attr_000000:relevant", "triplet_id": "attr_000000", "factor": "attribute", "variant": "relevant", "model_id": "qwen3_vl_4b_instruct", "raw_output": "image missing: /root/autodl-tmp/RewardLens/code/images/D:\\01_work\\RewardLens\\outputs\\attribute_scale_v1\\images\\attr_000000_relevant.png\nTraceback (most recent call last):\n  File \"/root/autodl-tmp/RewardLens/code/rewardlens/inference/common.py\", line 144, in run_items\n    raise FileNotFoundError(\"image missing: %s\" % image_path)\nFileNotFoundError: image missing: /root/autodl-tmp/RewardLens/code/images/D:\\01_work\\RewardLens\\outputs\\attribute_scale_v1\\images\\attr_000000_relevant.png\n", "parsed_preference": null, "score_a": null, "score_b": null, "margin": null, "latency_ms": 0.2071186900138855, "status": "error", "candidate_a": "blue", "candidate_b": "red"}
===== GPU =====
Sun Sep 13 04:41:08 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 580.65.06              Driver Version: 580.65.06      CUDA Version: 13.0     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA A800 80GB PCIe          On  |   00000000:57:00.0 Off |                  Off |
| N/A   32C    P0             42W /  300W |       0MiB /  81920MiB |      0%      Default |
|                                         |                        |             Disabled |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+
(venv) root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# cd /root/autodl-tmp/RewardLens/code

python - <<'PY'
import json
from pathlib import Path, PureWindowsPath

src = Path("manifests/signal_gate_v1/compatibility_probe_manifest.jsonl")
img_root = Path("images").resolve()
dst = Path("outputs/smoke_qwen/compatibility_probe_manifest.linux.jsonl")

# 建立 basename -> 实际 Linux 文件索引
index = {}
for p in img_root.rglob("*.png"):
    index.setdefault(p.name, []).append(p.resolve())

rows = []
missing = []
ambiguous = []

for line in src.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue

    rec = json.loads(line)
    raw = rec.get("image_path", "")
    name = PureWindowsPath(raw).name
    matches = index.get(name, [])

    if len(matches) == 1:
        rec["image_path"] = str(matches[0])
    elif len(matches) == 0:
        missing.append((rec.get("item_id"), name, raw))
    else:
        ambiguous.append((rec.get("item_id"), name, [str(x) for x in matches]))

    rows.append(rec)

dst.parent.mkdir(parents=True, exist_ok=True)
with dst.open("w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print("ROWS:", len(rows))
print("MISSING:", len(missing))
print("AMBIGUOUS:", len(ambiguous))
print("OUT:", dst)

PY  print("AMBIGUOUS_ITEM:", x)
ROWS: 50
MISSING: 0
AMBIGUOUS: 0
OUT: outputs/smoke_qwen/compatibility_probe_manifest.linux.jsonl
(venv) root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# rm -f outputs/smoke_qwen/qwen_probe5.jsonl

python rewardlens/inference/run_probe.py \
  --adapter hf \
  --model-id qwen3_vl_4b_instruct \
  --manifest outputs/smoke_qwen/compatibility_probe_manifest.linux.jsonl \
  --limit 5 \
  --out-jsonl outputs/smoke_qwen/qwen_probe5.jsonl \
  2>&1 | tee outputs/smoke_qwen/qwen_probe5_retry.log
`torch_dtype` is deprecated! Use `dtype` instead!
Loading checkpoint shards: 100%|██████████| 2/2 [00:00<00:00, 23.68it/s]
The following generation flags are not valid and may be ignored: ['top_p', 'top_k']. Set `TRANSFORMERS_VERBOSITY=info` for more details.
{
  "stage": "compatibility_probe",
  "ok": 5,
  "failed": 0,
  "skipped": 0,
  "out_jsonl": "outputs/smoke_qwen/qwen_probe5.jsonl"
}
(venv) root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# echo "===== RESULTS ====="
cat outputs/smoke_qwen/qwen_probe5.jsonl
===== RESULTS =====
{"item_id": "count_000000:base", "triplet_id": "count_000000", "factor": "count", "variant": "base", "model_id": "qwen3_vl_4b_instruct", "raw_output": "A", "parsed_preference": "A", "score_a": null, "score_b": null, "margin": null, "latency_ms": 1134.2681646347046, "status": "ok", "candidate_a": "3", "candidate_b": "4"}
{"item_id": "count_000000:relevant", "triplet_id": "count_000000", "factor": "count", "variant": "relevant", "model_id": "qwen3_vl_4b_instruct", "raw_output": "A", "parsed_preference": "A", "score_a": null, "score_b": null, "margin": null, "latency_ms": 93.97987276315689, "status": "ok", "candidate_a": "3", "candidate_b": "4"}
{"item_id": "count_000000:irrelevant", "triplet_id": "count_000000", "factor": "count", "variant": "irrelevant", "model_id": "qwen3_vl_4b_instruct", "raw_output": "A", "parsed_preference": "A", "score_a": null, "score_b": null, "margin": null, "latency_ms": 88.54317665100098, "status": "ok", "candidate_a": "3", "candidate_b": "4"}
{"item_id": "attr_000000:base", "triplet_id": "attr_000000", "factor": "attribute", "variant": "base", "model_id": "qwen3_vl_4b_instruct", "raw_output": "B", "parsed_preference": "B", "score_a": null, "score_b": null, "margin": null, "latency_ms": 89.34856206178665, "status": "ok", "candidate_a": "blue", "candidate_b": "red"}
{"item_id": "attr_000000:relevant", "triplet_id": "attr_000000", "factor": "attribute", "variant": "relevant", "model_id": "qwen3_vl_4b_instruct", "raw_output": "A", "parsed_preference": "A", "score_a": null, "score_b": null, "margin": null, "latency_ms": 98.51201251149178, "status": "ok", "candidate_a": "blue", "candidate_b": "red"}
(venv) root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# cd /root/autodl-tmp/RewardLens/code

python - <<'PY'
import json
from pathlib import Path, PureWindowsPath
from collections import defaultdict

src = Path("manifests/signal_gate_v1/gpu_signal_gate_manifest.jsonl")
dst = Path("outputs/smoke_qwen/signal_gate_mini24.linux.jsonl")
img_root = Path("images").resolve()

# basename -> Linux image path
index = {}
for p in img_root.rglob("*.png"):
    index.setdefault(p.name, []).append(p.resolve())

rows = [json.loads(x) for x in src.read_text(encoding="utf-8").splitlines() if x.strip()]

# 每个 factor 取前 2 个完整 triplet
factor_triplets = defaultdict(list)
seen = defaultdict(set)

for r in rows:
    f = r["factor"]
    t = r["triplet_id"]
    if t not in seen[f] and len(factor_triplets[f]) < 2:
        factor_triplets[f].append(t)
        seen[f].add(t)

selected = []
missing = []

keep = {(f, t) for f, ts in factor_triplets.items() for t in ts}

for r in rows:
    if (r["factor"], r["triplet_id"]) not in keep:
        continue

    name = PureWindowsPath(r["image_path"]).name
    matches = index.get(name, [])

    if len(matches) != 1:
        missing.append((r["item_id"], name, len(matches)))
        continue

    r["image_path"] = str(matches[0])
PYint("OUT:", dst)missing[:10])factor_triplets))) + "\n")
FACTOR_TRIPLETS: {'count': ['count_000000', 'count_000001'], 'attribute': ['attr_000000', 'attr_000001'], 'presence': ['pres_000000', 'pres_000001'], 'spatial': ['spat_000000', 'spat_000001']}
ROWS: 24
MISSING: []
OUT: outputs/smoke_qwen/signal_gate_mini24.linux.jsonl
(venv) root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# python rewardlens/inference/run_signal_gate.py \
  --adapter hf \
  --model-id qwen3_vl_4b_instruct \
  --manifest outputs/smoke_qwen/signal_gate_mini24.linux.jsonl \
  --out-jsonl outputs/smoke_qwen/qwen_signal24.jsonl \
  2>&1 | tee outputs/smoke_qwen/qwen_signal24.log
`torch_dtype` is deprecated! Use `dtype` instead!
Loading checkpoint shards: 100%|██████████| 2/2 [00:00<00:00, 22.69it/s]
The following generation flags are not valid and may be ignored: ['top_p', 'top_k']. Set `TRANSFORMERS_VERBOSITY=info` for more details.
{
  "stage": "signal_gate",
  "ok": 24,
  "failed": 0,
  "skipped": 0,
  "out_jsonl": "outputs/smoke_qwen/qwen_signal24.jsonl"
}
(venv) root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# echo "===== STATUS ====="
python - <<'PY'
import json
from collections import Counter

p = "outputs/smoke_qwen/qwen_signal24.jsonl"
rows = [json.loads(x) for x in open(p, encoding="utf-8")]

print("rows:", len(rows))
print("status:", Counter(r["status"] for r in rows))
print("parsed:", Counter(r["parsed_preference"] for r in rows))
print("factor:", Counter(r["factor"] for r in rows))
PY
===== STATUS =====
rows: 24
status: Counter({'ok': 24})
parsed: Counter({'A': 13, 'B': 11})
factor: Counter({'count': 6, 'attribute': 6, 'presence': 6, 'spatial': 6})
(venv) root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# 
```



```
 "irrelevant_accuracy": 1.0,
      "PFC": 0.7875,
      "PSC": 0.99875,
      "PFC_conditional": 0.7884856070087609,
      "PSC_conditional": 1.0,
      "base_correct_N": 799
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "count",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.17,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.17,
      "PSC": 1.0,
      "PFC_conditional": 0.17,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "attribute",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 1.0,
      "PSC": 1.0,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "presence",
      "N": 200,
      "base_accuracy": 0.995,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.995,
      "PSC": 0.995,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 199
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "spatial",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.985,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.985,
      "PSC": 1.0,
      "PFC_conditional": 0.985,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    }
  ]
}

===== OFFICIAL QWEN METRICS =====
[
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "attribute",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 1.0,
    "PSC": 1.0,
    "PFC_cond": 1.0,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "count",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 0.17,
    "PSC": 1.0,
    "PFC_cond": 0.17,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "presence",
    "n": 200,
    "n_cond": 199,
    "base_acc": 0.995,
    "PFC": 0.995,
    "PSC": 0.995,
    "PFC_cond": 1.0,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "spatial",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 0.985,
    "PSC": 1.0,
    "PFC_cond": 0.985,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  }
]
===== CONTRACT QWEN METRICS =====
{
  "schema": "rewardlens_audit_contract_metrics_v1",
  "metric_contract": {
    "base_accuracy": "P(base correct)",
    "PFC": "P(base correct AND relevant correct)",
    "PSC": "P(base correct AND irrelevant correct)",
    "PFC_conditional": "P(relevant correct | base correct)",
    "PSC_conditional": "P(irrelevant correct | base correct)"
  },
  "gold_source_keys": {
    "expected_preference": 2400
  },
  "rows": [
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "overall",
      "N": 800,
      "base_accuracy": 0.99875,
      "relevant_accuracy": 0.78875,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.7875,
      "PSC": 0.99875,
      "PFC_conditional": 0.7884856070087609,
      "PSC_conditional": 1.0,
      "base_correct_N": 799
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "count",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.17,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.17,
      "PSC": 1.0,
      "PFC_conditional": 0.17,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "attribute",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 1.0,
      "PSC": 1.0,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "presence",
      "N": 200,
      "base_accuracy": 0.995,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.995,
      "PSC": 0.995,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 199
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "spatial",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.985,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.985,
      "PSC": 1.0,
      "PFC_conditional": 0.985,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    }
  ]
}
root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# +-----------------------------------------------AutoDL-----------------------------------------------------+
目录说明:
╔═════════════════╦════════╦════╦═════════════════════════════════════════════════════════════════════════╗
║目录             ║名称    ║速度║说明                                                                     ║
╠═════════════════╬════════╬════╬═════════════════════════════════════════════════════════════════════════╣
║/                ║系 统 盘║一般║实例关机数据不会丢失，可存放代码等。会随保存镜像一起保存。               ║
║/root/autodl-tmp ║数 据 盘║ 快 ║实例关机数据不会丢失，可存放读写IO要求高的数据。但不会随保存镜像一起保存 ║
║/root/autodl-fs  ║文件存储║一般║可以实现多实例间的文件同步共享，不受实例开关机和保存镜像的影响。         ║
╚═════════════════╩════════╩════╩═════════════════════════════════════════════════════════════════════════╝
CPU ：14 核心
内存：120 GB
GPU ：NVIDIA A800 80GB PCIe, 1
存储：
  系 统 盘/               ：4% 1.2G/30G
  数 据 盘/root/autodl-tmp：13% 6.1G/50G
  文件存储/root/autodl-fs ：32% 63G/200G
+----------------------------------------------------------------------------------------------------------+
*注意: 
1.系统盘较小请将大的数据存放于数据盘或文件存储中，重置系统时数据盘和文件存储中的数据不受影响
2.清理系统盘请参考：https://www.autodl.com/docs/qa1/
3.终端中长期执行命令请使用screen等工具开后台运行，确保程序不受SSH连接中断影响：https://www.autodl.com/docs/daemon/
root@autodl-container-03dd44a781-f2a6258d:~# cd /root/autodl-tmp/RewardLens/code

# ============================================================
# 1. 修复备用 contract metrics：识别 expected_preference
# ============================================================

python - <<'PY'
from pathlib import Path

p = Path("/root/rewardlens_contract_metrics.py")
text = p.read_text(encoding="utf-8")

if '"expected_preference"' not in text:
    old = '''    direct_keys = [
        "gold_preference",'''
    new = '''    direct_keys = [
        "expected_preference",
        "gold_preference",'''

    if old not in text:
        raise SystemExit("Could not locate direct_keys block")

    text = text.replace(old, new, 1)
    p.write_text(text, encoding="utf-8")
    print("PATCHED: expected_preference support added")
else:
    print("ALREADY PATCHED")
PY


# ============================================================
# 2. 修复 official-metrics helper
#    不再猜参数，直接使用仓库真实 CLI
# ============================================================

cat > /root/rewardlens_existing_metrics_auto.py <<'PY'
import argparse
import json
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--script", required=True)
parser.add_argument("--predictions", required=True)
parser.add_argument("--manifest", required=True)
parser.add_argument("--out-dir", required=True)
parser.add_argument("--model", required=True)
  /root/autodl-fs/RewardLens/results/metrics/qwen3_vl_4b_instruct/contract_metrics.jsons.jsonon
PATCHED: expected_preference support added
WROTE /root/autodl-fs/RewardLens/results/metrics/qwen3_vl_4b_instruct/official_audit_metrics.json n 4
{
  "schema": "rewardlens_audit_contract_metrics_v1",
  "metric_contract": {
    "base_accuracy": "P(base correct)",
    "PFC": "P(base correct AND relevant correct)",
    "PSC": "P(base correct AND irrelevant correct)",
    "PFC_conditional": "P(relevant correct | base correct)",
    "PSC_conditional": "P(irrelevant correct | base correct)"
  },
  "gold_source_keys": {
    "expected_preference": 2400
  },
  "rows": [
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "overall",
      "N": 800,
      "base_accuracy": 0.99875,
      "relevant_accuracy": 0.78875,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.7875,
      "PSC": 0.99875,
      "PFC_conditional": 0.7884856070087609,
      "PSC_conditional": 1.0,
      "base_correct_N": 799
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "count",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.17,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.17,
      "PSC": 1.0,
      "PFC_conditional": 0.17,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "attribute",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 1.0,
      "PSC": 1.0,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "presence",
      "N": 200,
      "base_accuracy": 0.995,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.995,
      "PSC": 0.995,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 199
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "spatial",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.985,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.985,
      "PSC": 1.0,
      "PFC_conditional": 0.985,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    }
  ]
}

===== OFFICIAL QWEN METRICS =====
[
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "attribute",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 1.0,
    "PSC": 1.0,
    "PFC_cond": 1.0,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "count",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 0.17,
    "PSC": 1.0,
    "PFC_cond": 0.17,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "presence",
    "n": 200,
    "n_cond": 199,
    "base_acc": 0.995,
    "PFC": 0.995,
    "PSC": 0.995,
    "PFC_cond": 1.0,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "spatial",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 0.985,
    "PSC": 1.0,
    "PFC_cond": 0.985,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  }
]
===== CONTRACT QWEN METRICS =====
{
  "schema": "rewardlens_audit_contract_metrics_v1",
  "metric_contract": {
    "base_accuracy": "P(base correct)",
    "PFC": "P(base correct AND relevant correct)",
    "PSC": "P(base correct AND irrelevant correct)",
    "PFC_conditional": "P(relevant correct | base correct)",
    "PSC_conditional": "P(irrelevant correct | base correct)"
  },
  "gold_source_keys": {
    "expected_preference": 2400
  },
  "rows": [
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "overall",
      "N": 800,
      "base_accuracy": 0.99875,
      "relevant_accuracy": 0.78875,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.7875,
      "PSC": 0.99875,
      "PFC_conditional": 0.7884856070087609,
      "PSC_conditional": 1.0,
      "base_correct_N": 799
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "count",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.17,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.17,
      "PSC": 1.0,
      "PFC_conditional": 0.17,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "attribute",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 1.0,
      "PSC": 1.0,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "presence",
      "N": 200,
      "base_accuracy": 0.995,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.995,
      "PSC": 0.995,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 199
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "spatial",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.985,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.985,
      "PSC": 1.0,
      "PFC_conditional": 0.985,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    }
  ]
}
root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# +-----------------------------------------------AutoDL-----------------------------------------------------+
目录说明:
╔═════════════════╦════════╦════╦═════════════════════════════════════════════════════════════════════════╗
║目录             ║名称    ║速度║说明                                                                     ║
╠═════════════════╬════════╬════╬═════════════════════════════════════════════════════════════════════════╣
║/                ║系 统 盘║一般║实例关机数据不会丢失，可存放代码等。会随保存镜像一起保存。               ║
║/root/autodl-tmp ║数 据 盘║ 快 ║实例关机数据不会丢失，可存放读写IO要求高的数据。但不会随保存镜像一起保存 ║
║/root/autodl-fs  ║文件存储║一般║可以实现多实例间的文件同步共享，不受实例开关机和保存镜像的影响。         ║
╚═════════════════╩════════╩════╩═════════════════════════════════════════════════════════════════════════╝
CPU ：14 核心
内存：120 GB
GPU ：NVIDIA A800 80GB PCIe, 1
存储：
  系 统 盘/               ：4% 1.2G/30G
  数 据 盘/root/autodl-tmp：13% 6.1G/50G
  文件存储/root/autodl-fs ：32% 63G/200G
+----------------------------------------------------------------------------------------------------------+
*注意: 
1.系统盘较小请将大的数据存放于数据盘或文件存储中，重置系统时数据盘和文件存储中的数据不受影响
2.清理系统盘请参考：https://www.autodl.com/docs/qa1/
3.终端中长期执行命令请使用screen等工具开后台运行，确保程序不受SSH连接中断影响：https://www.autodl.com/docs/daemon/
root@autodl-container-03dd44a781-f2a6258d:~# cd /root/autodl-tmp/RewardLens/code

# ============================================================
# 1. 修复备用 contract metrics：识别 expected_preference
# ============================================================

python - <<'PY'
from pathlib import Path

p = Path("/root/rewardlens_contract_metrics.py")
text = p.read_text(encoding="utf-8")

if '"expected_preference"' not in text:
    old = '''    direct_keys = [
        "gold_preference",'''
    new = '''    direct_keys = [
        "expected_preference",
        "gold_preference",'''

    if old not in text:
        raise SystemExit("Could not locate direct_keys block")

    text = text.replace(old, new, 1)
    p.write_text(text, encoding="utf-8")
    print("PATCHED: expected_preference support added")
else:
    print("ALREADY PATCHED")
PY


# ============================================================
# 2. 修复 official-metrics helper
#    不再猜参数，直接使用仓库真实 CLI
# ============================================================

cat > /root/rewardlens_existing_metrics_auto.py <<'PY'
import argparse
import json
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--script", required=True)
parser.add_argument("--predictions", required=True)
parser.add_argument("--manifest", required=True)
parser.add_argument("--out-dir", required=True)
parser.add_argument("--model", required=True)
  /root/autodl-fs/RewardLens/results/metrics/qwen3_vl_4b_instruct/contract_metrics.jsons.jsonon
PATCHED: expected_preference support added
WROTE /root/autodl-fs/RewardLens/results/metrics/qwen3_vl_4b_instruct/official_audit_metrics.json n 4
{
  "schema": "rewardlens_audit_contract_metrics_v1",
  "metric_contract": {
    "base_accuracy": "P(base correct)",
    "PFC": "P(base correct AND relevant correct)",
    "PSC": "P(base correct AND irrelevant correct)",
    "PFC_conditional": "P(relevant correct | base correct)",
    "PSC_conditional": "P(irrelevant correct | base correct)"
  },
  "gold_source_keys": {
    "expected_preference": 2400
  },
  "rows": [
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "overall",
      "N": 800,
      "base_accuracy": 0.99875,
      "relevant_accuracy": 0.78875,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.7875,
      "PSC": 0.99875,
      "PFC_conditional": 0.7884856070087609,
      "PSC_conditional": 1.0,
      "base_correct_N": 799
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "count",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.17,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.17,
      "PSC": 1.0,
      "PFC_conditional": 0.17,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "attribute",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 1.0,
      "PSC": 1.0,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "presence",
      "N": 200,
      "base_accuracy": 0.995,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.995,
      "PSC": 0.995,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 199
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "spatial",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.985,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.985,
      "PSC": 1.0,
      "PFC_conditional": 0.985,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    }
  ]
}

===== OFFICIAL QWEN METRICS =====
[
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "attribute",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 1.0,
    "PSC": 1.0,
    "PFC_cond": 1.0,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "count",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 0.17,
    "PSC": 1.0,
    "PFC_cond": 0.17,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "presence",
    "n": 200,
    "n_cond": 199,
    "base_acc": 0.995,
    "PFC": 0.995,
    "PSC": 0.995,
    "PFC_cond": 1.0,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "spatial",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 0.985,
    "PSC": 1.0,
    "PFC_cond": 0.985,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  }
]
===== CONTRACT QWEN METRICS =====
{
  "schema": "rewardlens_audit_contract_metrics_v1",
  "metric_contract": {
    "base_accuracy": "P(base correct)",
    "PFC": "P(base correct AND relevant correct)",
    "PSC": "P(base correct AND irrelevant correct)",
    "PFC_conditional": "P(relevant correct | base correct)",
    "PSC_conditional": "P(irrelevant correct | base correct)"
  },
  "gold_source_keys": {
    "expected_preference": 2400
  },
  "rows": [
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "overall",
      "N": 800,
      "base_accuracy": 0.99875,
      "relevant_accuracy": 0.78875,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.7875,
      "PSC": 0.99875,
      "PFC_conditional": 0.7884856070087609,
      "PSC_conditional": 1.0,
      "base_correct_N": 799
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "count",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.17,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.17,
      "PSC": 1.0,
      "PFC_conditional": 0.17,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "attribute",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 1.0,
      "PSC": 1.0,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "presence",
      "N": 200,
      "base_accuracy": 0.995,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.995,
      "PSC": 0.995,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 199
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "spatial",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.985,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.985,
      "PSC": 1.0,
      "PFC_conditional": 0.985,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    }
  ]
}
root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# +-----------------------------------------------AutoDL-----------------------------------------------------+
目录说明:
╔═════════════════╦════════╦════╦═════════════════════════════════════════════════════════════════════════╗
║目录             ║名称    ║速度║说明                                                                     ║
╠═════════════════╬════════╬════╬═════════════════════════════════════════════════════════════════════════╣
║/                ║系 统 盘║一般║实例关机数据不会丢失，可存放代码等。会随保存镜像一起保存。               ║
║/root/autodl-tmp ║数 据 盘║ 快 ║实例关机数据不会丢失，可存放读写IO要求高的数据。但不会随保存镜像一起保存 ║
║/root/autodl-fs  ║文件存储║一般║可以实现多实例间的文件同步共享，不受实例开关机和保存镜像的影响。         ║
╚═════════════════╩════════╩════╩═════════════════════════════════════════════════════════════════════════╝
CPU ：14 核心
内存：120 GB
GPU ：NVIDIA A800 80GB PCIe, 1
存储：
  系 统 盘/               ：4% 1.2G/30G
  数 据 盘/root/autodl-tmp：13% 6.1G/50G
  文件存储/root/autodl-fs ：32% 63G/200G
+----------------------------------------------------------------------------------------------------------+
*注意: 
1.系统盘较小请将大的数据存放于数据盘或文件存储中，重置系统时数据盘和文件存储中的数据不受影响
2.清理系统盘请参考：https://www.autodl.com/docs/qa1/
3.终端中长期执行命令请使用screen等工具开后台运行，确保程序不受SSH连接中断影响：https://www.autodl.com/docs/daemon/
root@autodl-container-03dd44a781-f2a6258d:~# cd /root/autodl-tmp/RewardLens/code

# ============================================================
# 1. 修复备用 contract metrics：识别 expected_preference
# ============================================================

python - <<'PY'
from pathlib import Path

p = Path("/root/rewardlens_contract_metrics.py")
text = p.read_text(encoding="utf-8")

if '"expected_preference"' not in text:
    old = '''    direct_keys = [
        "gold_preference",'''
    new = '''    direct_keys = [
        "expected_preference",
        "gold_preference",'''

    if old not in text:
        raise SystemExit("Could not locate direct_keys block")

    text = text.replace(old, new, 1)
    p.write_text(text, encoding="utf-8")
    print("PATCHED: expected_preference support added")
else:
    print("ALREADY PATCHED")
PY


# ============================================================
# 2. 修复 official-metrics helper
#    不再猜参数，直接使用仓库真实 CLI
# ============================================================

cat > /root/rewardlens_existing_metrics_auto.py <<'PY'
import argparse
import json
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--script", required=True)
parser.add_argument("--predictions", required=True)
parser.add_argument("--manifest", required=True)
parser.add_argument("--out-dir", required=True)
parser.add_argument("--model", required=True)
  /root/autodl-fs/RewardLens/results/metrics/qwen3_vl_4b_instruct/contract_metrics.jsons.jsonon
PATCHED: expected_preference support added
WROTE /root/autodl-fs/RewardLens/results/metrics/qwen3_vl_4b_instruct/official_audit_metrics.json n 4
{
  "schema": "rewardlens_audit_contract_metrics_v1",
  "metric_contract": {
    "base_accuracy": "P(base correct)",
    "PFC": "P(base correct AND relevant correct)",
    "PSC": "P(base correct AND irrelevant correct)",
    "PFC_conditional": "P(relevant correct | base correct)",
    "PSC_conditional": "P(irrelevant correct | base correct)"
  },
  "gold_source_keys": {
    "expected_preference": 2400
  },
  "rows": [
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "overall",
      "N": 800,
      "base_accuracy": 0.99875,
      "relevant_accuracy": 0.78875,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.7875,
      "PSC": 0.99875,
      "PFC_conditional": 0.7884856070087609,
      "PSC_conditional": 1.0,
      "base_correct_N": 799
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "count",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.17,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.17,
      "PSC": 1.0,
      "PFC_conditional": 0.17,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "attribute",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 1.0,
      "PSC": 1.0,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "presence",
      "N": 200,
      "base_accuracy": 0.995,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.995,
      "PSC": 0.995,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 199
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "spatial",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.985,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.985,
      "PSC": 1.0,
      "PFC_conditional": 0.985,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    }
  ]
}

===== OFFICIAL QWEN METRICS =====
[
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "attribute",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 1.0,
    "PSC": 1.0,
    "PFC_cond": 1.0,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "count",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 0.17,
    "PSC": 1.0,
    "PFC_cond": 0.17,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "presence",
    "n": 200,
    "n_cond": 199,
    "base_acc": 0.995,
    "PFC": 0.995,
    "PSC": 0.995,
    "PFC_cond": 1.0,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "spatial",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 0.985,
    "PSC": 1.0,
    "PFC_cond": 0.985,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  }
]
===== CONTRACT QWEN METRICS =====
{
  "schema": "rewardlens_audit_contract_metrics_v1",
  "metric_contract": {
    "base_accuracy": "P(base correct)",
    "PFC": "P(base correct AND relevant correct)",
    "PSC": "P(base correct AND irrelevant correct)",
    "PFC_conditional": "P(relevant correct | base correct)",
    "PSC_conditional": "P(irrelevant correct | base correct)"
  },
  "gold_source_keys": {
    "expected_preference": 2400
  },
  "rows": [
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "overall",
      "N": 800,
      "base_accuracy": 0.99875,
      "relevant_accuracy": 0.78875,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.7875,
      "PSC": 0.99875,
      "PFC_conditional": 0.7884856070087609,
      "PSC_conditional": 1.0,
      "base_correct_N": 799
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "count",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.17,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.17,
      "PSC": 1.0,
      "PFC_conditional": 0.17,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "attribute",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 1.0,
      "PSC": 1.0,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "presence",
      "N": 200,
      "base_accuracy": 0.995,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.995,
      "PSC": 0.995,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 199
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "spatial",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.985,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.985,
      "PSC": 1.0,
      "PFC_conditional": 0.985,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    }
  ]
}
root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# 
```

```
 "irrelevant_accuracy": 1.0,
      "PFC": 0.7875,
      "PSC": 0.99875,
      "PFC_conditional": 0.7884856070087609,
      "PSC_conditional": 1.0,
      "base_correct_N": 799
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "count",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.17,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.17,
      "PSC": 1.0,
      "PFC_conditional": 0.17,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "attribute",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 1.0,
      "PSC": 1.0,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "presence",
      "N": 200,
      "base_accuracy": 0.995,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.995,
      "PSC": 0.995,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 199
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "spatial",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.985,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.985,
      "PSC": 1.0,
      "PFC_conditional": 0.985,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    }
  ]
}

===== OFFICIAL QWEN METRICS =====
[
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "attribute",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 1.0,
    "PSC": 1.0,
    "PFC_cond": 1.0,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "count",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 0.17,
    "PSC": 1.0,
    "PFC_cond": 0.17,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "presence",
    "n": 200,
    "n_cond": 199,
    "base_acc": 0.995,
    "PFC": 0.995,
    "PSC": 0.995,
    "PFC_cond": 1.0,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "spatial",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 0.985,
    "PSC": 1.0,
    "PFC_cond": 0.985,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  }
]
===== CONTRACT QWEN METRICS =====
{
  "schema": "rewardlens_audit_contract_metrics_v1",
  "metric_contract": {
    "base_accuracy": "P(base correct)",
    "PFC": "P(base correct AND relevant correct)",
    "PSC": "P(base correct AND irrelevant correct)",
    "PFC_conditional": "P(relevant correct | base correct)",
    "PSC_conditional": "P(irrelevant correct | base correct)"
  },
  "gold_source_keys": {
    "expected_preference": 2400
  },
  "rows": [
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "overall",
      "N": 800,
      "base_accuracy": 0.99875,
      "relevant_accuracy": 0.78875,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.7875,
      "PSC": 0.99875,
      "PFC_conditional": 0.7884856070087609,
      "PSC_conditional": 1.0,
      "base_correct_N": 799
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "count",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.17,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.17,
      "PSC": 1.0,
      "PFC_conditional": 0.17,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "attribute",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 1.0,
      "PSC": 1.0,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "presence",
      "N": 200,
      "base_accuracy": 0.995,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.995,
      "PSC": 0.995,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 199
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "spatial",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.985,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.985,
      "PSC": 1.0,
      "PFC_conditional": 0.985,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    }
  ]
}
root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# +-----------------------------------------------AutoDL-----------------------------------------------------+
目录说明:
╔═════════════════╦════════╦════╦═════════════════════════════════════════════════════════════════════════╗
║目录             ║名称    ║速度║说明                                                                     ║
╠═════════════════╬════════╬════╬═════════════════════════════════════════════════════════════════════════╣
║/                ║系 统 盘║一般║实例关机数据不会丢失，可存放代码等。会随保存镜像一起保存。               ║
║/root/autodl-tmp ║数 据 盘║ 快 ║实例关机数据不会丢失，可存放读写IO要求高的数据。但不会随保存镜像一起保存 ║
║/root/autodl-fs  ║文件存储║一般║可以实现多实例间的文件同步共享，不受实例开关机和保存镜像的影响。         ║
╚═════════════════╩════════╩════╩═════════════════════════════════════════════════════════════════════════╝
CPU ：14 核心
内存：120 GB
GPU ：NVIDIA A800 80GB PCIe, 1
存储：
  系 统 盘/               ：4% 1.2G/30G
  数 据 盘/root/autodl-tmp：13% 6.1G/50G
  文件存储/root/autodl-fs ：32% 63G/200G
+----------------------------------------------------------------------------------------------------------+
*注意: 
1.系统盘较小请将大的数据存放于数据盘或文件存储中，重置系统时数据盘和文件存储中的数据不受影响
2.清理系统盘请参考：https://www.autodl.com/docs/qa1/
3.终端中长期执行命令请使用screen等工具开后台运行，确保程序不受SSH连接中断影响：https://www.autodl.com/docs/daemon/
root@autodl-container-03dd44a781-f2a6258d:~# cd /root/autodl-tmp/RewardLens/code

# ============================================================
# 1. 修复备用 contract metrics：识别 expected_preference
# ============================================================

python - <<'PY'
from pathlib import Path

p = Path("/root/rewardlens_contract_metrics.py")
text = p.read_text(encoding="utf-8")

if '"expected_preference"' not in text:
    old = '''    direct_keys = [
        "gold_preference",'''
    new = '''    direct_keys = [
        "expected_preference",
        "gold_preference",'''

    if old not in text:
        raise SystemExit("Could not locate direct_keys block")

    text = text.replace(old, new, 1)
    p.write_text(text, encoding="utf-8")
    print("PATCHED: expected_preference support added")
else:
    print("ALREADY PATCHED")
PY


# ============================================================
# 2. 修复 official-metrics helper
#    不再猜参数，直接使用仓库真实 CLI
# ============================================================

cat > /root/rewardlens_existing_metrics_auto.py <<'PY'
import argparse
import json
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--script", required=True)
parser.add_argument("--predictions", required=True)
parser.add_argument("--manifest", required=True)
parser.add_argument("--out-dir", required=True)
parser.add_argument("--model", required=True)
  /root/autodl-fs/RewardLens/results/metrics/qwen3_vl_4b_instruct/contract_metrics.jsons.jsonon
PATCHED: expected_preference support added
WROTE /root/autodl-fs/RewardLens/results/metrics/qwen3_vl_4b_instruct/official_audit_metrics.json n 4
{
  "schema": "rewardlens_audit_contract_metrics_v1",
  "metric_contract": {
    "base_accuracy": "P(base correct)",
    "PFC": "P(base correct AND relevant correct)",
    "PSC": "P(base correct AND irrelevant correct)",
    "PFC_conditional": "P(relevant correct | base correct)",
    "PSC_conditional": "P(irrelevant correct | base correct)"
  },
  "gold_source_keys": {
    "expected_preference": 2400
  },
  "rows": [
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "overall",
      "N": 800,
      "base_accuracy": 0.99875,
      "relevant_accuracy": 0.78875,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.7875,
      "PSC": 0.99875,
      "PFC_conditional": 0.7884856070087609,
      "PSC_conditional": 1.0,
      "base_correct_N": 799
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "count",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.17,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.17,
      "PSC": 1.0,
      "PFC_conditional": 0.17,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "attribute",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 1.0,
      "PSC": 1.0,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "presence",
      "N": 200,
      "base_accuracy": 0.995,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.995,
      "PSC": 0.995,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 199
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "spatial",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.985,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.985,
      "PSC": 1.0,
      "PFC_conditional": 0.985,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    }
  ]
}

===== OFFICIAL QWEN METRICS =====
[
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "attribute",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 1.0,
    "PSC": 1.0,
    "PFC_cond": 1.0,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "count",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 0.17,
    "PSC": 1.0,
    "PFC_cond": 0.17,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "presence",
    "n": 200,
    "n_cond": 199,
    "base_acc": 0.995,
    "PFC": 0.995,
    "PSC": 0.995,
    "PFC_cond": 1.0,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "spatial",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 0.985,
    "PSC": 1.0,
    "PFC_cond": 0.985,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  }
]
===== CONTRACT QWEN METRICS =====
{
  "schema": "rewardlens_audit_contract_metrics_v1",
  "metric_contract": {
    "base_accuracy": "P(base correct)",
    "PFC": "P(base correct AND relevant correct)",
    "PSC": "P(base correct AND irrelevant correct)",
    "PFC_conditional": "P(relevant correct | base correct)",
    "PSC_conditional": "P(irrelevant correct | base correct)"
  },
  "gold_source_keys": {
    "expected_preference": 2400
  },
  "rows": [
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "overall",
      "N": 800,
      "base_accuracy": 0.99875,
      "relevant_accuracy": 0.78875,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.7875,
      "PSC": 0.99875,
      "PFC_conditional": 0.7884856070087609,
      "PSC_conditional": 1.0,
      "base_correct_N": 799
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "count",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.17,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.17,
      "PSC": 1.0,
      "PFC_conditional": 0.17,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "attribute",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 1.0,
      "PSC": 1.0,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "presence",
      "N": 200,
      "base_accuracy": 0.995,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.995,
      "PSC": 0.995,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 199
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "spatial",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.985,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.985,
      "PSC": 1.0,
      "PFC_conditional": 0.985,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    }
  ]
}
root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# +-----------------------------------------------AutoDL-----------------------------------------------------+
目录说明:
╔═════════════════╦════════╦════╦═════════════════════════════════════════════════════════════════════════╗
║目录             ║名称    ║速度║说明                                                                     ║
╠═════════════════╬════════╬════╬═════════════════════════════════════════════════════════════════════════╣
║/                ║系 统 盘║一般║实例关机数据不会丢失，可存放代码等。会随保存镜像一起保存。               ║
║/root/autodl-tmp ║数 据 盘║ 快 ║实例关机数据不会丢失，可存放读写IO要求高的数据。但不会随保存镜像一起保存 ║
║/root/autodl-fs  ║文件存储║一般║可以实现多实例间的文件同步共享，不受实例开关机和保存镜像的影响。         ║
╚═════════════════╩════════╩════╩═════════════════════════════════════════════════════════════════════════╝
CPU ：14 核心
内存：120 GB
GPU ：NVIDIA A800 80GB PCIe, 1
存储：
  系 统 盘/               ：4% 1.2G/30G
  数 据 盘/root/autodl-tmp：13% 6.1G/50G
  文件存储/root/autodl-fs ：32% 63G/200G
+----------------------------------------------------------------------------------------------------------+
*注意: 
1.系统盘较小请将大的数据存放于数据盘或文件存储中，重置系统时数据盘和文件存储中的数据不受影响
2.清理系统盘请参考：https://www.autodl.com/docs/qa1/
3.终端中长期执行命令请使用screen等工具开后台运行，确保程序不受SSH连接中断影响：https://www.autodl.com/docs/daemon/
root@autodl-container-03dd44a781-f2a6258d:~# cd /root/autodl-tmp/RewardLens/code

# ============================================================
# 1. 修复备用 contract metrics：识别 expected_preference
# ============================================================

python - <<'PY'
from pathlib import Path

p = Path("/root/rewardlens_contract_metrics.py")
text = p.read_text(encoding="utf-8")

if '"expected_preference"' not in text:
    old = '''    direct_keys = [
        "gold_preference",'''
    new = '''    direct_keys = [
        "expected_preference",
        "gold_preference",'''

    if old not in text:
        raise SystemExit("Could not locate direct_keys block")

    text = text.replace(old, new, 1)
    p.write_text(text, encoding="utf-8")
    print("PATCHED: expected_preference support added")
else:
    print("ALREADY PATCHED")
PY


# ============================================================
# 2. 修复 official-metrics helper
#    不再猜参数，直接使用仓库真实 CLI
# ============================================================

cat > /root/rewardlens_existing_metrics_auto.py <<'PY'
import argparse
import json
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--script", required=True)
parser.add_argument("--predictions", required=True)
parser.add_argument("--manifest", required=True)
parser.add_argument("--out-dir", required=True)
parser.add_argument("--model", required=True)
  /root/autodl-fs/RewardLens/results/metrics/qwen3_vl_4b_instruct/contract_metrics.jsons.jsonon
PATCHED: expected_preference support added
WROTE /root/autodl-fs/RewardLens/results/metrics/qwen3_vl_4b_instruct/official_audit_metrics.json n 4
{
  "schema": "rewardlens_audit_contract_metrics_v1",
  "metric_contract": {
    "base_accuracy": "P(base correct)",
    "PFC": "P(base correct AND relevant correct)",
    "PSC": "P(base correct AND irrelevant correct)",
    "PFC_conditional": "P(relevant correct | base correct)",
    "PSC_conditional": "P(irrelevant correct | base correct)"
  },
  "gold_source_keys": {
    "expected_preference": 2400
  },
  "rows": [
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "overall",
      "N": 800,
      "base_accuracy": 0.99875,
      "relevant_accuracy": 0.78875,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.7875,
      "PSC": 0.99875,
      "PFC_conditional": 0.7884856070087609,
      "PSC_conditional": 1.0,
      "base_correct_N": 799
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "count",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.17,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.17,
      "PSC": 1.0,
      "PFC_conditional": 0.17,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "attribute",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 1.0,
      "PSC": 1.0,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "presence",
      "N": 200,
      "base_accuracy": 0.995,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.995,
      "PSC": 0.995,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 199
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "spatial",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.985,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.985,
      "PSC": 1.0,
      "PFC_conditional": 0.985,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    }
  ]
}

===== OFFICIAL QWEN METRICS =====
[
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "attribute",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 1.0,
    "PSC": 1.0,
    "PFC_cond": 1.0,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "count",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 0.17,
    "PSC": 1.0,
    "PFC_cond": 0.17,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "presence",
    "n": 200,
    "n_cond": 199,
    "base_acc": 0.995,
    "PFC": 0.995,
    "PSC": 0.995,
    "PFC_cond": 1.0,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "spatial",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 0.985,
    "PSC": 1.0,
    "PFC_cond": 0.985,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  }
]
===== CONTRACT QWEN METRICS =====
{
  "schema": "rewardlens_audit_contract_metrics_v1",
  "metric_contract": {
    "base_accuracy": "P(base correct)",
    "PFC": "P(base correct AND relevant correct)",
    "PSC": "P(base correct AND irrelevant correct)",
    "PFC_conditional": "P(relevant correct | base correct)",
    "PSC_conditional": "P(irrelevant correct | base correct)"
  },
  "gold_source_keys": {
    "expected_preference": 2400
  },
  "rows": [
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "overall",
      "N": 800,
      "base_accuracy": 0.99875,
      "relevant_accuracy": 0.78875,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.7875,
      "PSC": 0.99875,
      "PFC_conditional": 0.7884856070087609,
      "PSC_conditional": 1.0,
      "base_correct_N": 799
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "count",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.17,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.17,
      "PSC": 1.0,
      "PFC_conditional": 0.17,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "attribute",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 1.0,
      "PSC": 1.0,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "presence",
      "N": 200,
      "base_accuracy": 0.995,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.995,
      "PSC": 0.995,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 199
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "spatial",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.985,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.985,
      "PSC": 1.0,
      "PFC_conditional": 0.985,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    }
  ]
}
root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# +-----------------------------------------------AutoDL-----------------------------------------------------+
目录说明:
╔═════════════════╦════════╦════╦═════════════════════════════════════════════════════════════════════════╗
║目录             ║名称    ║速度║说明                                                                     ║
╠═════════════════╬════════╬════╬═════════════════════════════════════════════════════════════════════════╣
║/                ║系 统 盘║一般║实例关机数据不会丢失，可存放代码等。会随保存镜像一起保存。               ║
║/root/autodl-tmp ║数 据 盘║ 快 ║实例关机数据不会丢失，可存放读写IO要求高的数据。但不会随保存镜像一起保存 ║
║/root/autodl-fs  ║文件存储║一般║可以实现多实例间的文件同步共享，不受实例开关机和保存镜像的影响。         ║
╚═════════════════╩════════╩════╩═════════════════════════════════════════════════════════════════════════╝
CPU ：14 核心
内存：120 GB
GPU ：NVIDIA A800 80GB PCIe, 1
存储：
  系 统 盘/               ：4% 1.2G/30G
  数 据 盘/root/autodl-tmp：13% 6.1G/50G
  文件存储/root/autodl-fs ：32% 63G/200G
+----------------------------------------------------------------------------------------------------------+
*注意: 
1.系统盘较小请将大的数据存放于数据盘或文件存储中，重置系统时数据盘和文件存储中的数据不受影响
2.清理系统盘请参考：https://www.autodl.com/docs/qa1/
3.终端中长期执行命令请使用screen等工具开后台运行，确保程序不受SSH连接中断影响：https://www.autodl.com/docs/daemon/
root@autodl-container-03dd44a781-f2a6258d:~# cd /root/autodl-tmp/RewardLens/code

# ============================================================
# 1. 修复备用 contract metrics：识别 expected_preference
# ============================================================

python - <<'PY'
from pathlib import Path

p = Path("/root/rewardlens_contract_metrics.py")
text = p.read_text(encoding="utf-8")

if '"expected_preference"' not in text:
    old = '''    direct_keys = [
        "gold_preference",'''
    new = '''    direct_keys = [
        "expected_preference",
        "gold_preference",'''

    if old not in text:
        raise SystemExit("Could not locate direct_keys block")

    text = text.replace(old, new, 1)
    p.write_text(text, encoding="utf-8")
    print("PATCHED: expected_preference support added")
else:
    print("ALREADY PATCHED")
PY


# ============================================================
# 2. 修复 official-metrics helper
#    不再猜参数，直接使用仓库真实 CLI
# ============================================================

cat > /root/rewardlens_existing_metrics_auto.py <<'PY'
import argparse
import json
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--script", required=True)
parser.add_argument("--predictions", required=True)
parser.add_argument("--manifest", required=True)
parser.add_argument("--out-dir", required=True)
parser.add_argument("--model", required=True)
  /root/autodl-fs/RewardLens/results/metrics/qwen3_vl_4b_instruct/contract_metrics.jsons.jsonon
PATCHED: expected_preference support added
WROTE /root/autodl-fs/RewardLens/results/metrics/qwen3_vl_4b_instruct/official_audit_metrics.json n 4
{
  "schema": "rewardlens_audit_contract_metrics_v1",
  "metric_contract": {
    "base_accuracy": "P(base correct)",
    "PFC": "P(base correct AND relevant correct)",
    "PSC": "P(base correct AND irrelevant correct)",
    "PFC_conditional": "P(relevant correct | base correct)",
    "PSC_conditional": "P(irrelevant correct | base correct)"
  },
  "gold_source_keys": {
    "expected_preference": 2400
  },
  "rows": [
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "overall",
      "N": 800,
      "base_accuracy": 0.99875,
      "relevant_accuracy": 0.78875,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.7875,
      "PSC": 0.99875,
      "PFC_conditional": 0.7884856070087609,
      "PSC_conditional": 1.0,
      "base_correct_N": 799
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "count",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.17,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.17,
      "PSC": 1.0,
      "PFC_conditional": 0.17,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "attribute",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 1.0,
      "PSC": 1.0,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "presence",
      "N": 200,
      "base_accuracy": 0.995,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.995,
      "PSC": 0.995,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 199
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "spatial",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.985,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.985,
      "PSC": 1.0,
      "PFC_conditional": 0.985,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    }
  ]
}

===== OFFICIAL QWEN METRICS =====
[
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "attribute",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 1.0,
    "PSC": 1.0,
    "PFC_cond": 1.0,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "count",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 0.17,
    "PSC": 1.0,
    "PFC_cond": 0.17,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "presence",
    "n": 200,
    "n_cond": 199,
    "base_acc": 0.995,
    "PFC": 0.995,
    "PSC": 0.995,
    "PFC_cond": 1.0,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  },
  {
    "model_id": "qwen3_vl_4b_instruct",
    "factor": "spatial",
    "n": 200,
    "n_cond": 200,
    "base_acc": 1.0,
    "PFC": 0.985,
    "PSC": 1.0,
    "PFC_cond": 0.985,
    "PSC_cond": 1.0,
    "note": "base_acc is diagnostic only; confirmatory A is GQA-static, never audit bases"
  }
]
===== CONTRACT QWEN METRICS =====
{
  "schema": "rewardlens_audit_contract_metrics_v1",
  "metric_contract": {
    "base_accuracy": "P(base correct)",
    "PFC": "P(base correct AND relevant correct)",
    "PSC": "P(base correct AND irrelevant correct)",
    "PFC_conditional": "P(relevant correct | base correct)",
    "PSC_conditional": "P(irrelevant correct | base correct)"
  },
  "gold_source_keys": {
    "expected_preference": 2400
  },
  "rows": [
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "overall",
      "N": 800,
      "base_accuracy": 0.99875,
      "relevant_accuracy": 0.78875,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.7875,
      "PSC": 0.99875,
      "PFC_conditional": 0.7884856070087609,
      "PSC_conditional": 1.0,
      "base_correct_N": 799
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "count",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.17,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.17,
      "PSC": 1.0,
      "PFC_conditional": 0.17,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "attribute",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 1.0,
      "PSC": 1.0,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "presence",
      "N": 200,
      "base_accuracy": 0.995,
      "relevant_accuracy": 1.0,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.995,
      "PSC": 0.995,
      "PFC_conditional": 1.0,
      "PSC_conditional": 1.0,
      "base_correct_N": 199
    },
    {
      "model": "qwen3_vl_4b_instruct",
      "factor": "spatial",
      "N": 200,
      "base_accuracy": 1.0,
      "relevant_accuracy": 0.985,
      "irrelevant_accuracy": 1.0,
      "PFC": 0.985,
      "PSC": 1.0,
      "PFC_conditional": 0.985,
      "PSC_conditional": 1.0,
      "base_correct_N": 200
    }
  ]
}
root@autodl-container-03dd44a781-f2a6258d:~/autodl-tmp/RewardLens/code# 
```

