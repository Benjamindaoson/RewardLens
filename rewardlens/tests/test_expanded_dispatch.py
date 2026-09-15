"""CPU-only: two different workers must claim different model directories."""
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import time
from scripts import expanded_dispatch as dispatch

def check():
    with tempfile.TemporaryDirectory() as directory:
        dispatch.OUT=Path(directory)
        dispatch.candidates=lambda:[{"model":"a","assigned_worker":"011"},{"model":"b","assigned_worker":"011"}]
        dispatch.complete=lambda model:False
        dispatch.checkpoint_ready=lambda candidate,worker:True
        a,lease_a=dispatch.claim("011")
        b,lease_b=dispatch.claim("017")
        assert a["model"]=="a" and b["model"]=="b"
        none,_=dispatch.claim("011")
        assert none is None
        dispatch.terminal(lease_a,"complete",0)
        state=json.loads((dispatch.OUT/"dynamic_queue.json").read_text())
        assert state["claims"]["a"]["status"]=="complete"
        assert state["claims"]["b"]["worker"]=="017"
    # Real CPU-only subprocesses verify that a live model child survives handoff.
    parent=subprocess.Popen([sys.executable,"-c","import subprocess,time,sys; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(2)']); p.wait(); time.sleep(30)"])
    proc=Path("/proc")/str(parent.pid)
    try:
        deadline=time.monotonic()+5
        while not (proc/"task"/proc.name/"children").read_text().strip():
            assert time.monotonic()<deadline
            time.sleep(.02)
        child=int((proc/"task"/proc.name/"children").read_text().split()[0])
        assert dispatch.retire_idle_controller(proc) is False
        assert parent.poll() is None and Path("/proc",str(child)).exists()
        assert dispatch.process_state(proc)[0]!="T"
        deadline=time.monotonic()+5
        while (proc/"task"/proc.name/"children").read_text().strip():
            assert time.monotonic()<deadline
            time.sleep(.02)
        assert dispatch.retire_idle_controller(proc) is True
        assert parent.wait(timeout=3)!=0
    finally:
        if parent.poll() is None:
            parent.terminate();parent.wait(timeout=3)
    print("DYNAMIC_DISTINCT_CLAIM_AND_FENCED_HANDOFF_PASS")

if __name__=="__main__":
    check()
