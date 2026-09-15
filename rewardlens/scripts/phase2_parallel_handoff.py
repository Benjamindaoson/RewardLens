#!/usr/bin/env python3
"""011 parent-only dispatch hold and evidence-preserving two-worker aggregation."""
import argparse
import ctypes
import platform
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback

ROOT=Path("/root/autodl-tmp/RewardLens/code")
sys.path.insert(0,str(ROOT/"rewardlens"))
from scripts import phase2_autonomous as p
CONTROL=p.PHASE/"parallel_control_v1"
BASE=p.PHASE/"gpu_4model_v1"
EXTERNAL=p.PHASE/"gpu_parallel_017"
COMBINED=p.PHASE/"gpu_4model_parallel_combined_v1"
MODEL="skywork_vl_reward_7b"

def process(pid):
    path=Path("/proc")/str(pid)
    raw=(path/"stat").read_text()
    fields=raw[raw.rfind(")")+2:].split()
    return {"pid":pid,"state":fields[0],"ppid":int(fields[1]),"start_ticks":int(fields[19]),
            "cmdline":(path/"cmdline").read_bytes().replace(b"\0",b" ").decode().strip()}

def same_process(info):
    try:
        return process(info["pid"])["start_ticks"]==info["start_ticks"]
    except FileNotFoundError:
        return False

def pidfd(pid):
    if platform.machine()!="x86_64":
        raise RuntimeError("pidfd syscall binding requires x86_64")
    libc=ctypes.CDLL(None,use_errno=True)
    libc.syscall.restype=ctypes.c_long
    # Verified against /usr/include/x86_64-linux-gnu/asm/unistd_64.h.
    fd=libc.syscall(434,pid,0)
    if fd<0:
        raise OSError(ctypes.get_errno(),"pidfd_open")
    return int(fd)


def signal_fd(fd,sig):
    libc=ctypes.CDLL(None,use_errno=True)
    libc.syscall.restype=ctypes.c_long
    if libc.syscall(424,fd,int(sig),0,0)<0:
        raise OSError(ctypes.get_errno(),"pidfd_send_signal")


def stop_parent(parent,child):
    before=process(parent)
    current=process(child)
    if current["ppid"]!=parent or current["state"] in ("T","Z"):
        raise ValueError("child is not actively running under the expected parent")
    fd=pidfd(parent)
    try:
        if process(parent)["start_ticks"]!=before["start_ticks"]:
            raise ValueError("parent PID changed")
        signal_fd(fd,signal.SIGSTOP)
        deadline=time.monotonic()+3
        while process(parent)["state"]!="T" and time.monotonic()<deadline:
            time.sleep(.02)
        after=process(parent)
        child_after=process(child)
        if after["state"]!="T" or child_after["start_ticks"]!=current["start_ticks"] or child_after["state"] in ("T","Z"):
            raise ValueError("parent-only stop did not preserve active child")
        return after,child_after
    finally:
        os.close(fd)

def arm():
    if CONTROL.joinpath("dispatch_hold.json").exists():
        raise ValueError("hold already exists; inspect it instead of re-signaling")
    current=json.loads((BASE/"current_process.json").read_text())
    launcher=json.loads((BASE/"launcher.json").read_text())
    if current["model"]!="molmo_7b_d_0924":
        raise ValueError("011 is no longer running Molmo")
    parent,child=launcher["pid"],current["pid"]
    parent_info,child_info=process(parent),process(child)
    if "--model" in parent_info["cmdline"] or "phase2_autonomous.py" not in parent_info["cmdline"]:
        raise ValueError("unexpected parent command")
    if "--model molmo_7b_d_0924" not in child_info["cmdline"]:
        raise ValueError("unexpected child command")
    children=(Path("/proc")/str(parent)/"task"/str(parent)/"children").read_text().split()
    if children!=[str(child)] or (BASE/MODEL).exists():
        raise ValueError("Skywork could already be assigned or another child exists")
    # Pin/check PID identity and signal only this parent, never its process group.
    after,child_after=stop_parent(parent,child)
    receipt={"status":"PARENT_STOPPED_CHILD_RUNNING","parent":after,"child":child_after,
             "assigned_model":MODEL,"output_017":str(EXTERNAL),"time_unix":time.time(),
             "original_contract_sha256":p.sha(BASE/"run_contract.json"),
             "signal_target":"parent PID only","molmo_signals_sent":False}
    p.write_json(CONTROL/"dispatch_hold.json",receipt,immutable=True)
    print(json.dumps(receipt,indent=2))

def verified_receipt(root,model):
    contract=json.loads((root/"run_contract.json").read_text())
    receipt=json.loads((root/model/"completion.json").read_text())
    if receipt["model_id"]!=model or receipt.get("complete") is not True:
        raise ValueError("model completion invalid")
    if receipt["contract_sha256"]!=p.sha(root/"run_contract.json"):
        raise ValueError("receipt contract mismatch")
    if [receipt["static_completed"],receipt["pools_completed"],receipt["pair_edges"]]!=[800,800,22400]:
        raise ValueError("incomplete model counts")
    for name,digest in receipt["artifacts"].items():
        if Path(name).name!=name or p.sha(root/model/name)!=digest:
            raise ValueError("model artifact hash conflict")
    return contract,receipt

def aggregate():
    baseline=json.loads((BASE/"run_contract.json").read_text())
    sources={}
    for model in p.MODELS:
        root=EXTERNAL if model==MODEL else BASE
        contract,receipt=verified_receipt(root,model)
        for key in ("gate_sha256","downstream_sha256","static_sha256","code_sha256","checkpoints","audit_sha256"):
            if contract[key]!=baseline[key]:
                raise ValueError("scientific contracts differ: "+key)
        sources[model]={"root":str(root),"contract_sha256":p.sha(root/"run_contract.json"),
                        "completion_sha256":p.sha(root/model/"completion.json")}
    combined_contract={"schema":"TWO_WORKER_VERIFIED_IMPORT_V1","sources":sources,
                       "static_sha256":baseline["static_sha256"],"downstream_sha256":baseline["downstream_sha256"],
                       "note":"Derived reporting view only. Original source contracts, receipts and judgments remain authoritative."}
    p.write_json(COMBINED/"run_contract.json",combined_contract,immutable=True)
    for model,source in sources.items():
        root=Path(source["root"])
        _,receipt=verified_receipt(root,model)
        target=COMBINED/model
        target.mkdir(parents=True,exist_ok=True)
        for name in receipt["artifacts"]:
            link=target/name
            expected=root/model/name
            if link.is_symlink():
                if link.resolve()!=expected.resolve():
                    raise ValueError("reporting link conflict")
            elif link.exists():
                raise ValueError("unexpected reporting file")
            else:
                link.symlink_to(expected)
        p.write_json(target/"source_completion.json",receipt,immutable=True)
        imported={**receipt,"contract_sha256":p.sha(COMBINED/"run_contract.json"),
                  "receipt_kind":"VERIFIED_IMPORT","source":source}
        p.write_json(target/"completion.json",imported,immutable=True)
    # Only this independent 011 process changes its own reporting context.
    p.OUT=COMBINED
    from scripts.phase2_report import report
    result=report(COMBINED)
    p.write_json(CONTROL/"handoff_complete.json",{"PHASE2_4MODEL_COMPLETE":result["PHASE2_4MODEL_COMPLETE"],
                 "combined_dir":str(COMBINED),"time_unix":time.time()},immutable=True)
    return result

def watch():
    while not (CONTROL/"dispatch_hold.json").exists():
        time.sleep(5)
    hold=json.loads((CONTROL/"dispatch_hold.json").read_text())
    parent,child=hold["parent"],hold["child"]
    retired=(CONTROL/"parent_retired.json").exists()
    while True:
        if not retired and same_process(parent):
            if process(parent["pid"])["state"]!="T":
                raise ValueError("dispatch hold unexpectedly released")
        child_live=same_process(child) and process(child["pid"])["state"]!="Z"
        p.write_json(CONTROL/"handoff_status.json",{
            "time_unix":time.time(),"molmo_running":child_live,"parent_dispatch_held":not retired,
            "skywork_complete":(EXTERNAL/MODEL/"completion.json").exists(),
            "stage":"WAITING_FOR_NATIVE_COMPLETION_RECEIPTS"})
        if not child_live and not retired:
            # Never retire the original parent while its Molmo child is alive.
            verified_receipt(BASE,"molmo_7b_d_0924")
            if same_process(parent):
                fd=pidfd(parent["pid"])
                try:
                    if process(parent["pid"])["start_ticks"]!=parent["start_ticks"]:
                        raise ValueError("parent identity changed")
                    signal_fd(fd,signal.SIGKILL)
                finally:
                    os.close(fd)
            p.write_json(CONTROL/"parent_retired.json",{"parent":parent,"time":time.time(),
                         "reason":"Molmo exited with hash-verified completion; duplicate Skywork dispatch disabled"},
                         immutable=True)
            retired=True
        if retired and (EXTERNAL/MODEL/"completion.json").exists():
            aggregate()
            return
        time.sleep(30)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm",action="store_true")
    args=parser.parse_args()
    if os.uname().nodename!="autodl-container-47bb4a8b0c-371e5795":
        raise ValueError("handoff and analysis run on 011 only")
    CONTROL.mkdir(parents=True,exist_ok=True)
    if args.arm:
        arm()
    else:
        watch()

if __name__=="__main__":
    try:
        main()
    except Exception:
        p.write_json(CONTROL/"handoff_failure.json",{"time":time.time(),"error":traceback.format_exc()})
        raise
