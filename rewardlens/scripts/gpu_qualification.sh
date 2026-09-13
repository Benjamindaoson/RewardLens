#!/usr/bin/env bash
# GPU qualification. Run once after the ROCm/CUDA machine boots.
# Default: bf16 + SDPA. Do not enable FlashAttention2 on this first pass.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="$(cd "$ROOT/.." && pwd)"
OUT_DIR="${OUT_DIR:-$PROJECT/outputs/gpu_qualification}"
MODEL_ID="${MODEL_ID:-Qwen/Qwen3-VL-4B-Instruct}"
SECOND_MODEL_ID="${SECOND_MODEL_ID:-Qwen/Qwen3-VL-8B-Instruct}"
RUN_SECOND="${RUN_SECOND:-0}"
PROBE_MANIFEST="${PROBE_MANIFEST:-$PROJECT/outputs/controlled_v1/compatibility_probe_manifest.jsonl}"
PYTHON="${PYTHON:-python}"
mkdir -p "$OUT_DIR"

export ROOT PROJECT OUT_DIR MODEL_ID PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export TRANSFORMERS_ATTN_IMPLEMENTATION="${TRANSFORMERS_ATTN_IMPLEMENTATION:-sdpa}"
export QUAL_OUT="$OUT_DIR/device_probe.json"
export PROJECT_ROOT="$PROJECT"

echo "=== 1. torch environment ==="
"$PYTHON" "$ROOT/scripts/device_probe.py" --out "$OUT_DIR/device_probe.json"

echo "=== 2-4. ROCm/HIP, GPU, bf16 matmul ==="
"$PYTHON" - <<'PY'
import json, os, time
from pathlib import Path
import torch
from inference.device import probe_device, write_probe

out = Path(os.environ.get("OUT_DIR_FALLBACK", "."))
report = probe_device()
print("backend", report["backend"], "hip", report["torch_hip_version"], "cuda", report["torch_cuda_version"])
print("device", report.get("primary_device_name"), "vram_gb", report.get("primary_vram_gb"))
bf16_ok = False
if torch.cuda.is_available():
    a = torch.randn(1024, 1024, device="cuda", dtype=torch.bfloat16)
    b = torch.randn(1024, 1024, device="cuda", dtype=torch.bfloat16)
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    c = a @ b
    torch.cuda.synchronize()
    dt = time.perf_counter() - t0
    bf16_ok = torch.isfinite(c).all().item()
    report["bf16_matmul_ok"] = bool(bf16_ok)
    report["bf16_matmul_seconds"] = dt
    print("bf16 matmul", bf16_ok, "seconds", dt)
else:
    report["bf16_matmul_ok"] = False
    print("NO_GPU_FOR_MATMUL")
write_probe(str(Path(os.environ.get("QUAL_OUT", "gpu_qualification_report.json"))), report)
if torch.cuda.is_available() and not bf16_ok:
    raise SystemExit("bf16 matmul failed")
PY

echo "=== 5. PIL image load ==="
"$PYTHON" - <<'PY'
from PIL import Image
import os, glob
paths = glob.glob(os.path.join(os.environ.get("PROJECT_ROOT", "."), "outputs", "*_pilot_v1", "images", "*.png"))
if not paths:
    raise SystemExit("no pilot PNG found for PIL probe")
im = Image.open(paths[0])
print("PIL_OK", paths[0], im.size, im.mode)
PY

echo "=== 6. Transformers import ==="
"$PYTHON" - <<'PY'
import transformers
print("transformers", transformers.__version__)
PY

echo "=== 7. Qwen3-VL processor test ==="
"$PYTHON" - <<PY
from transformers import AutoProcessor
proc = AutoProcessor.from_pretrained("${MODEL_ID}")
print("PROCESSOR_OK", type(proc))
PY

echo "=== 8-10. 1-image, 10-item, throughput (bf16 SDPA) ==="
"$PYTHON" - <<PY
import json, os, time, glob
from pathlib import Path
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForImageTextToText

out_dir = Path(r"${OUT_DIR}")
model_id = "${MODEL_ID}"
images = glob.glob(os.path.join(r"${PROJECT}", "outputs", "*_pilot_v1", "images", "*.png"))
if not images:
    raise SystemExit("no images")
device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.bfloat16 if device == "cuda" else torch.float32
processor = AutoProcessor.from_pretrained(model_id)
model = AutoModelForImageTextToText.from_pretrained(
    model_id,
    torch_dtype=dtype,
    attn_implementation="sdpa",
)
model.to(device)
model.eval()

def run_one(path):
    image = Image.open(path).convert("RGB")
    messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": "Reply with A or B. Question: How many objects? A: 2 B: 3"}]}]
    text = processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = processor(text=[text], images=[image], return_tensors="pt")
    inputs = {k: v.to(device) if hasattr(v, "to") else v for k, v in inputs.items()}
    t0 = time.perf_counter()
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=8, do_sample=False)
    if device == "cuda":
        torch.cuda.synchronize()
    dt = time.perf_counter() - t0
    decoded = processor.batch_decode(out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)[0]
    return dt, decoded

dt1, raw1 = run_one(images[0])
print("ONE_IMAGE_OK", dt1, raw1[:80])
times = []
n = min(10, len(images))
for i in range(n):
    dt, raw = run_one(images[i])
    times.append(dt)
    print("item", i, dt, raw[:40])
mean = sum(times) / len(times)
items_per_sec = 1.0 / mean if mean else 0.0
peak = None
if torch.cuda.is_available():
    peak = int(torch.cuda.max_memory_allocated())
report = {
    "model_id": model_id,
    "attn_implementation": "sdpa",
    "dtype": "bfloat16" if device == "cuda" else "float32",
    "flash_attention_2": False,
    "n_items": n,
    "sec_per_item": mean,
    "items_per_sec": items_per_sec,
    "one_image_sec": dt1,
    "peak_vram_bytes": peak,
    "peak_vram_gb": None if peak is None else peak / (1024**3),
    "raw_sample": raw1,
}
path = out_dir / "gpu_qualification_report.json"
path.write_text(json.dumps(report, indent=2))
print("WROTE", path)
print("items/sec", items_per_sec, "sec/item", mean, "peak_vram_gb", report["peak_vram_gb"])
PY

if [[ "$RUN_SECOND" == "1" ]]; then
  echo "=== optional second carrier ${SECOND_MODEL_ID} ==="
  MODEL_ID="$SECOND_MODEL_ID" "$0"
fi

echo "GPU_QUALIFICATION_OK"
