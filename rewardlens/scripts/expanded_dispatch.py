#!/usr/bin/env python3
"""Shared locked queue; different ready models, no active-model interruption."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import uuid

ROOT=Path("/root/autodl-tmp/RewardLens/code")
sys.path.insert(0,str(ROOT/"rewardlens"))
from scripts.phase2_autonomous import PHASE,write_json,sha,gpu
from scripts.expanded_worker import OUT,candidates,valid_full,gpu_busy
from scripts.expanded_model_acquire import HOSTS,CONTROL

def complete(model):
    root=OUT/model
    receipt=valid_full(root)
    if not receipt:return False
    if receipt.get("model")!=model:raise ValueError("completed model identity differs")
    required={"contract.json","compatibility_gate.json","audit/static.jsonl","audit/metrics.json",
              "execution/run_contract.json","execution/"+model+"/completion.json",
              "execution/"+model+"/pairs.jsonl","execution/"+model+"/selections.jsonl",
              "execution/"+model+"/static.jsonl","execution/"+model+"/utility.json"}
    if not required<=set(receipt["artifacts"]):raise ValueError("missing required completed artifact")
    gate=json.loads((root/"compatibility_gate.json").read_text())
    if gate["status"]!="PASS" or gate["contract"]!=json.loads((root/"contract.json").read_text()):
        raise ValueError("completed compatibility contract differs")
    return receipt

def legacy_controllers(worker):
    found=[]
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():continue
        try:
            args=(proc/"cmdline").read_bytes().decode().strip("\0").split("\0")
            if not Path(args[0]).name.startswith("python"):continue
            if any(a.endswith("/expanded_worker.py") for a in args) and "--worker" in args and args[args.index("--worker")+1]==worker:
                found.append(proc)
        except (OSError,IndexError,UnicodeError):continue
    return found

def process_state(proc):
    try:
        fields=(proc/"stat").read_text().rsplit(")",1)[1].split()
        return fields[0],fields[19]  # state, kernel start tick
    except FileNotFoundError:
        return None,None

def retire_idle_controller(proc):
    identity=process_state(proc)[1]
    if identity is None:return True
    # Fence only this queue controller. Its model child is never signalled.
    os.kill(int(proc.name),signal.SIGSTOP)
    try:
        deadline=time.monotonic()+5
        while True:
            state,start=process_state(proc)
            if state in (None,"Z"):return True
            if start!=identity:raise ValueError("controller PID identity changed")
            if state=="T":break
            if time.monotonic()>deadline:raise TimeoutError("controller did not stop")
            time.sleep(.02)
        if (proc/"task"/proc.name/"children").read_text().strip():
            return False
        os.kill(int(proc.name),signal.SIGTERM)
    finally:
        state,start=process_state(proc)
        if start==identity and state not in (None,"Z"):
            os.kill(int(proc.name),signal.SIGCONT)
    deadline=time.monotonic()+5
    while process_state(proc)[0] not in (None,"Z"):
        if process_state(proc)[1]!=identity:raise ValueError("controller PID reused")
        if time.monotonic()>deadline:raise TimeoutError("idle controller did not exit")
        time.sleep(.02)
    return True

def existing_model_processes():
    found=[]
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():continue
        try:
            args=(proc/"cmdline").read_bytes().decode().strip("\0").split("\0")
            if not Path(args[0]).name.startswith("python"):continue
            if "--model" in args and any(Path(a).name in ("expanded_worker.py","expanded_model_entry.py") for a in args):
                found.append(int(proc.name))
        except (OSError,IndexError,UnicodeError):continue
    return found

def takeover(worker,after_legacy):
    while True:
        if after_legacy and not all(complete(r["model"]) for r in candidates() if r["assigned_worker"]==worker):
            time.sleep(15);continue
        controllers=legacy_controllers(worker)
        retired=[retire_idle_controller(proc) for proc in controllers]
        if not all(retired):
            time.sleep(10);continue
        if legacy_controllers(worker):raise ValueError("legacy controller still present")
        return

def checkpoint_ready(candidate,worker):
    state_path=CONTROL/"status"/(candidate["model"]+".json")
    if not state_path.exists():return False
    state=json.loads(state_path.read_text())
    if not state.get("checkpoint_verified") or not state.get("processor_verified"):return False
    if state["worker_hostname"]==socket.gethostname():return Path(state["local_checkpoint"]).is_dir()
    transfer=OUT/"checkpoint_transfers"/(candidate["model"]+".json")
    if not transfer.exists():return False
    row=json.loads(transfer.read_text())
    return row.get("verified") is True and row["revision"]==candidate["revision"] and Path(row["shared_checkpoint"]).is_dir()

def claim(worker):
    with (OUT/"dynamic_queue.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        path=OUT/"dynamic_queue.json"
        state=json.loads(path.read_text()) if path.exists() else {"schema":"DYNAMIC_TWO_WORKER_V2","claims":{}}
        for candidate in candidates():
            model=candidate["model"]
            if complete(model):continue
            # The older017 controller retains its two tasks until its clean handoff.
            if candidate["assigned_worker"]=="017" and not (OUT/"dynamic_017_ready.json").exists():
                continue
            prior=state["claims"].get(model)
            if prior:
                if prior["status"] in ("failed","complete"):continue
                if prior["worker"]!=worker:continue
                if Path("/proc",str(prior["controller_pid"])).exists():continue
            if (OUT/model/"worker_failure.json").exists():continue
            if not checkpoint_ready(candidate,worker):continue
            contract=OUT/model/"contract.json"
            if contract.exists() and json.loads(contract.read_text())["worker"]!=socket.gethostname():
                continue
            record={"model":model,"worker":worker,"hostname":socket.gethostname(),"controller_pid":os.getpid(),
                    "claim":uuid.uuid4().hex,"status":"claimed","started_unix":time.time()}
            state["claims"][model]=record
            write_json(path,state)
            return candidate,record
    return None,None

def terminal(record,status,returncode):
    with (OUT/"dynamic_queue.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        path=OUT/"dynamic_queue.json";state=json.loads(path.read_text())
        current=state["claims"][record["model"]]
        if current["claim"]!=record["claim"]:raise ValueError("claim ownership changed")
        current.update(status=status,returncode=returncode,finished_unix=time.time())
        write_json(path,state)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker",required=True,choices=HOSTS)
    parser.add_argument("--after-legacy",action="store_true")
    args=parser.parse_args();worker=args.worker
    if socket.gethostname()!=HOSTS[worker]:raise ValueError("wrong worker")
    os.environ.update(HF_HUB_OFFLINE="1",TRANSFORMERS_OFFLINE="1",TOKENIZERS_PARALLELISM="false",OMP_NUM_THREADS="1")
    OUT.mkdir(parents=True,exist_ok=True)
    control=OUT/"workers"/worker;control.mkdir(parents=True,exist_ok=True)
    with (ROOT/(".expanded_dispatch_"+worker+".lock")).open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        takeover(worker,args.after_legacy)
        if worker=="017":write_json(OUT/"dynamic_017_ready.json",{"hostname":socket.gethostname(),"time":time.time()})
        while True:
            if gpu_busy() or existing_model_processes():
                write_json(control/"status.json",{"stage":"waiting_for_existing_gpu_job","controller":"dynamic_v2","gpu":gpu(),"time":time.time()})
                time.sleep(15);continue
            if all(complete(r["model"]) for r in candidates()):
                write_json(control/"status.json",{"stage":"all_expanded_models_complete","controller":"dynamic_v2","gpu":gpu(),"time":time.time()})
                return
            candidate,record=claim(worker)
            if not candidate:
                write_json(control/"status.json",{"stage":"waiting_for_ready_unclaimed_task","controller":"dynamic_v2","time":time.time(),"gpu":gpu()})
                time.sleep(15);continue
            model=candidate["model"];root=OUT/model;root.mkdir(parents=True,exist_ok=True)
            python=ROOT/".venv_phi35/bin/python" if model=="phi35_vision_instruct" else Path("/root/autodl-tmp/RewardLens/venv/bin/python")
            with (root/"console.log").open("a") as log:
                process=subprocess.Popen([str(python),"-u",str(ROOT/"rewardlens/scripts/expanded_model_entry.py"),"--model",model],
                                          stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy())
                while process.poll() is None:
                    write_json(control/"status.json",{"stage":"running","controller":"dynamic_v2","model":model,"pid":process.pid,"time":time.time(),"gpu":gpu()})
                    time.sleep(10)
            status="complete" if process.returncode==0 and complete(model) else "failed"
            terminal(record,status,process.returncode)
            if status=="failed":write_json(root/"worker_failure.json",{"returncode":process.returncode,"time":time.time(),"partial_results_preserved":True})

if __name__=="__main__":
    main()
