"""Local, read-only progress page for the active Hugging Face upload."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = Path.home() / "AppData" / "Local" / "Temp" / "rewardlens-hf-upload"
CACHE_DIR = Path(r"D:\.appdata\rewardlens-hf-cache")
PAYLOADS = (
    "datasets",
    "gpu_bundle",
    "gpu_bundle_fast_v1",
    "gpu_bundle_signal_v1",
    "outputs",
    "tools",
    "artifacts",
    "gpu_bundle_fast_v1.zip",
)


def tree_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file()) if path.exists() else 0


def upload_running() -> bool:
    command = (
        "(Get-CimInstance Win32_Process | Where-Object { "
        "$_.Name -eq 'python.exe' -and $_.CommandLine -match "
        "'upload_hf_dataset\\.py' } | Measure-Object).Count"
    )
    result = subprocess.run(["powershell", "-NoProfile", "-Command", command], capture_output=True, text=True, check=False)
    return result.stdout.strip() not in {"", "0"}


def status() -> dict[str, object]:
    log = max(LOG_DIR.glob("*.out.log"), key=lambda item: item.stat().st_mtime, default=None)
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines() if log else []
    current = next((line.removeprefix("UPLOAD ").split(" -> ")[0] for line in reversed(lines) if line.startswith("UPLOAD ")), None)
    current_name = Path(current).name if current else None
    phase = PAYLOADS.index(current_name) + 1 if current_name in PAYLOADS else 0
    return {
        "running": upload_running(),
        "current": current_name,
        "phase": phase,
        "phase_total": len(PAYLOADS),
        "cache_bytes": tree_bytes(CACHE_DIR),
        "dataset_bytes": tree_bytes(ROOT / "datasets"),
        "last_log_time": datetime.fromtimestamp(log.stat().st_mtime, timezone.utc).astimezone().isoformat() if log else None,
        "updated_at": datetime.now().astimezone().isoformat(),
    }


PAGE = """<!doctype html><meta charset=utf-8><title>RewardLens · Hugging Face 上传进度</title>
<style>body{font:16px system-ui;max-width:780px;margin:48px auto;background:#0d1117;color:#e6edf3}h1{margin-bottom:8px}.card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:20px;margin:16px 0}.bar{height:20px;background:#30363d;border-radius:12px;overflow:hidden}.fill{height:100%;background:#2ea043;transition:width .4s}.moving{background:linear-gradient(90deg,#238636,#58a6ff,#238636);background-size:200%;animation:move 1.2s linear infinite}@keyframes move{to{background-position:200%}}.good{color:#3fb950}.warn{color:#f85149}.muted{color:#8b949e}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}code{font-size:15px}</style>
<h1>RewardLens · Hugging Face 上传</h1><p id=state>读取状态…</p><div class=card><b>阶段进度（不是伪造的字节百分比）</b><p id=phaseText></p><div class=bar><div id=phaseBar class=fill></div></div></div><div class=card><b>当前传输活动</b><p id=current></p><div class=bar><div id=activity class="fill moving" style="width:100%"></div></div><p class=muted>Hugging Face/Xet 在提交完成前不提供可靠的逐字节上传百分比；此动画只在上传进程实际存活时显示。</p></div><div class="card grid"><div>数据集总量<br><code id=dataset></code></div><div>本地传输缓存（实际观测）<br><code id=cache></code></div><div>最近日志活动<br><code id=log></code></div><div>页面刷新<br><code id=updated></code></div></div><p class=muted>本页每 5 秒自动刷新，仅读取本机状态；关闭浏览器不会中断上传。</p>
<script>const fmt=n=>`${(n/1024/1024/1024).toFixed(2)} GiB`;async function tick(){const s=await fetch('/status').then(r=>r.json());state.textContent=s.running?'● 上传进程正在运行':'● 未检测到上传进程';state.className=s.running?'good':'warn';phaseText.textContent=s.phase?`第 ${s.phase} / ${s.phase_total} 阶段：${s.current}`:'正在等待上传日志';phaseBar.style.width=`${s.phase/s.phase_total*100}%`;current.textContent=s.running?'正在传输，请保持此页面或上传终端均可。':'上传进程已停止；请查看上传日志。';activity.style.display=s.running?'block':'none';dataset.textContent=fmt(s.dataset_bytes);cache.textContent=fmt(s.cache_bytes);log.textContent=s.last_log_time||'暂无';updated.textContent=new Date(s.updated_at).toLocaleString()}tick();setInterval(tick,5000)</script>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        body = json.dumps(status()).encode() if self.path == "/status" else PAGE.encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8" if self.path == "/status" else "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_: object) -> None:
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
