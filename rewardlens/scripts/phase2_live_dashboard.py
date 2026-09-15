#!/usr/bin/env python3
"""Read-only experiment observer; only its own worker display directory is written."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import socket
import sys
import time
ROOT=Path("/root/autodl-tmp/RewardLens/code")
sys.path.insert(0,str(ROOT/"rewardlens"))
from scripts.phase2_autonomous import PHASE,gpu,write_json
from scripts.expanded_model_acquire import HOSTS
OUT=PHASE/"distributed_v1"

def read(path):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return {}

def process_age(pid):
    try:
        ticks=float((Path("/proc")/str(pid)/"stat").read_text().rsplit(")",1)[1].split()[19])
        return max(0,float(Path("/proc/uptime").read_text().split()[0])-ticks/os.sysconf("SC_CLK_TCK"))
    except (OSError,ValueError,IndexError):
        return None

def sample(worker):
    status_path=OUT/"workers"/worker/"status.json"
    control=read(status_path)
    data={};source=status_path
    if control.get("stage")=="running":
        model=control["model"];root=OUT/model
        task=read(root/"task_status.json")
        phase=read(root/"execution/live_status.json")
        if phase.get("pid")==control.get("pid"):
            data=phase;source=root/"execution/live_status.json"
        elif task.get("pid")==control.get("pid") and task.get("stage") in ("loading","audit"):
            data={**task,"model":model};source=root/"task_status.json"
    if not data and worker=="011":
        original=PHASE/"gpu_4model_v1/live_status.json"
        old=read(original)
        if old.get("pid") and process_age(old["pid"]) is not None and old.get("stage")!="complete":
            data=old;source=original
    if not data:
        data={**control,"model":control.get("model","-"),"stage":control.get("stage","waiting")}
    stage=data.get("stage","waiting")
    if stage=="audit":done,total=data.get("completed",0),2400
    elif stage=="static":done,total=data.get("static_completed",0),800
    elif stage in ("downstream","complete","failed"):done,total=data.get("pair_edges",0),22400
    else:done,total=0,0
    return {**data,"done":done,"total":total,"source":str(source),"count_initialized":stage!="audit" or "completed" in data,
            "elapsed_seconds":data.get("elapsed_seconds",process_age(data.get("pid"))),
            "checkpoint":data.get("checkpoint","JSONL fsync" if stage=="audit" else "waiting / no new judgments"),
            "gpu":gpu(),"observed_unix":time.time()}

def measure(data,baseline,now):
    if not data.get("count_initialized",True) or not data["total"]:
        return {**data,"percent":None,"throughput_per_second":None,"eta_seconds":None},None
    if baseline is None or (baseline["pid"],baseline["stage"])!=(data.get("pid"),data["stage"]) or data["done"]<baseline["done"]:
        baseline={"pid":data.get("pid"),"stage":data["stage"],"done":data["done"],"time":now}
    elapsed=now-baseline["time"]
    rate=(data["done"]-baseline["done"])/elapsed if elapsed>0 else None
    eta=max(0,data["total"]-data["done"])/rate if rate and rate>0 else None
    return {**data,"percent":100*data["done"]/data["total"] if data["total"] else None,
            "throughput_per_second":rate,"eta_seconds":eta},baseline

def render(data):
    def fmt(value,suffix=""):
        return "N/A" if value is None else "%.2f%s"%(value,suffix)
    dev=data["gpu"]
    return "\n".join([
        "RewardLens · Phase II · "+data.get("model","-"),
        "Stage: "+data["stage"]+" | Stage completed: %s/%s"%(data["done"] if data.get("count_initialized",True) else "N/A",data["total"]),
        "Static: %s/800 | Pools: %s/800 | Pair edges: %s/22400"%(data.get("static_completed",0),data.get("pools_completed",0),data.get("pair_edges",0)),
        "Progress: "+fmt(data["percent"],"%")+" | Throughput: "+fmt(data["throughput_per_second"],"/s")+" (observed, excludes resumed counts)",
        "Elapsed: "+fmt(data.get("elapsed_seconds"),"s")+" | ETA (~): "+fmt(data["eta_seconds"],"s"),
        "Abstention rate: "+fmt(None if data.get("abstention_rate") is None else 100*data["abstention_rate"],"%"),
        "GPU utilization: %s%% | VRAM: %s/%s MiB"%(dev.get("util_percent","N/A"),dev.get("vram_mib","N/A"),dev.get("total_mib","N/A")),
        "Durable checkpoint: "+data["checkpoint"],
        "Source (read-only): "+data.get("source","synthetic"),
    ])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker",required=True,choices=HOSTS)
    parser.add_argument("--once",action="store_true",help="one real read-only sample, no display files")
    args=parser.parse_args()
    if socket.gethostname()!=HOSTS[args.worker]:raise ValueError("wrong worker hostname")
    os.environ.update(HF_HUB_OFFLINE="1",TRANSFORMERS_OFFLINE="1")
    baseline=None
    if args.once:
        data,_=measure(sample(args.worker),None,time.time())
        print(render(data));return
    output=OUT/"workers"/args.worker/"terminal_dashboard"
    output.mkdir(parents=True,exist_ok=True)
    with (output/"display.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        while True:
            data,baseline=measure(sample(args.worker),baseline,time.time())
            write_json(output/"dashboard.json",data)
            print("\033[2J\033[H"+render(data),flush=True)
            time.sleep(5)

if __name__=="__main__":
    main()
