#!/usr/bin/env python3
"""017: Skywork only, isolated status/results, no analysis entry point."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path("/root/autodl-tmp/RewardLens/code")
sys.path.insert(0,str(ROOT/"rewardlens"))
for key in ("HF_HUB_OFFLINE","TRANSFORMERS_OFFLINE","HF_HUB_DISABLE_TELEMETRY"):
    os.environ[key]="1"
os.environ["PYTHONDONTWRITEBYTECODE"]="1"
os.environ["TOKENIZERS_PARALLELISM"]="false"
os.chdir(ROOT)
from scripts import phase2_autonomous as p
p.HOST="autodl-container-03dd44a781-f2a6258d"
p.OUT=p.PHASE/"gpu_parallel_017"
MODEL="skywork_vl_reward_7b"
CONTROL=p.PHASE/"parallel_control_v1"

def require_hold():
    hold=json.loads((CONTROL/"dispatch_hold.json").read_text())
    if hold.get("status")!="DUPLICATE_DISPATCH_BLOCKED":
        raise ValueError("011 dispatch hold not established")
    if hold.get("assigned_model")!=MODEL or hold.get("output_017")!=str(p.OUT):
        raise ValueError("assignment conflict")
    if p.sha(hold["marker_path"])!=hold["marker_sha256"]:
        raise ValueError("dispatch guard hash changed")
    marker=json.loads(Path(hold["marker_path"]).read_text())
    if marker.get("complete") is not False or marker.get("external_output")!=str(p.OUT):
        raise ValueError("invalid external delegation marker")
    return hold

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight",action="store_true")
    parser.add_argument("--worker",action="store_true")
    args=parser.parse_args()
    contract,_,_=p.preflight()
    baseline=json.loads((p.PHASE/"gpu_4model_v1/run_contract.json").read_text())
    for key in ("gate_sha256","static_sha256","downstream_sha256","code_sha256","checkpoints","audit_sha256"):
        if contract[key]!=baseline[key]:
            raise ValueError("017/011 scientific or checkpoint contract mismatch: "+key)
    if args.preflight:
        print(json.dumps({"preflight":"PASS","host":p.HOST,"only_model":MODEL,
                          "output":str(p.OUT),"downstream_sha256":contract["downstream_sha256"]}))
        return
    require_hold()
    p.OUT.mkdir(parents=True,exist_ok=True)
    if args.worker:
        with (p.OUT/"model_execution.lock").open("a") as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            p.run_model(MODEL)
        return
    with (p.OUT/"execution.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        p.write_json(p.OUT/"run_contract.json",contract,immutable=True)
        p.write_json(p.OUT/"launcher_017.json",{"pid":os.getpid(),"host":p.HOST,
                     "only_model":MODEL,"screen":"phase2_skywork_017","time":time.time(),
                     "wrapper_sha256":p.sha(__file__),"hold_sha256":p.sha(CONTROL/"dispatch_hold.json")},immutable=True)
        with (p.OUT/"console.log").open("a") as log:
            proc=subprocess.Popen([sys.executable,"-u",__file__,"--worker"],stdout=log,stderr=subprocess.STDOUT)
            p.write_json(p.OUT/"current_process.json",{"pid":proc.pid,"model":MODEL,"started_unix":time.time()})
            while proc.poll() is None:
                p.dashboard()
                time.sleep(10)
            p.write_json(p.OUT/"worker_exit.json",{"returncode":proc.returncode,"time":time.time()},immutable=True)
            if proc.returncode:
                raise RuntimeError("017 Skywork failed; durable partial results preserved")
        p.validate_completion(p.OUT/MODEL,contract)
        p.dashboard()
        print("017_SKYWORK_COMPLETE = TRUE",flush=True)
        # No report(), no RQ2/RQ3 on this machine.

if __name__=="__main__":
    main()
