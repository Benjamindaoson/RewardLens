#!/usr/bin/env python3
"""Resume with the exact hash-bound runner and adapter; never mutate active workers."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import uuid
import shutil
ROOT=Path("/root/autodl-tmp/RewardLens/code")
sys.path.insert(0,str(ROOT/"rewardlens"))
from scripts.phase2_autonomous import PHASE,sha
from lib.jsonl_io import append_jsonl
OUT=PHASE/"distributed_v1"

def load_bound_runner(contract):
    snapshots=OUT/"code_snapshots"
    sources={}
    for key in ("runner_sha256","adapter_sha256"):
        path=snapshots/(contract[key]+".py")
        if not path.is_file() or sha(path)!=contract[key]:
            raise ValueError("bound source unavailable: "+key)
        sources[key]=path
    name="inference.adapters.expanded_pinned"
    spec=importlib.util.spec_from_file_location(name,sources["adapter_sha256"])
    adapter_module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter_module)
    namespace={"__name__":"rewardlens_pinned_runner","__file__":str(sources["runner_sha256"])}
    exec(compile(sources["runner_sha256"].read_text(),str(sources["runner_sha256"]),"exec"),namespace)
    namespace["ExpandedAdapter"]=adapter_module.ExpandedAdapter
    original_preflight=namespace["preflight"]
    def checked_preflight(candidate):
        current,static,pools,audit=original_preflight(candidate)
        # Identify the source actually loaded, rather than the mutable import pathname.
        current["adapter_sha256"]=sha(sources["adapter_sha256"])
        current["runner_sha256"]=sha(sources["runner_sha256"])
        if current!=contract:
            raise ValueError("resume contract differs beyond source pathname")
        return current,static,pools,audit
    namespace["preflight"]=checked_preflight
    return namespace

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    choices=[r["model"] for r in json.loads((PHASE/"EXPANDED_MODEL_SELECTION.json").read_text())["candidates"][:4]]
    parser.add_argument("--model",required=True,choices=choices)
    parser.add_argument("--check-resume","--preflight",action="store_true")
    args=parser.parse_args()
    os.environ.update(HF_HUB_OFFLINE="1",TRANSFORMERS_OFFLINE="1",HF_HUB_DISABLE_TELEMETRY="1",
                      TOKENIZERS_PARALLELISM="false",OMP_NUM_THREADS="1")
    os.chdir(ROOT)
    root=OUT/args.model
    path=root/"contract.json"
    attempt=uuid.uuid4().hex
    started=time.time()
    if not args.check_resume:
        root.mkdir(parents=True,exist_ok=True)
        append_jsonl(str(root/"controller_attempts.jsonl"),{"attempt":attempt,"event":"start","time":started,"pid":os.getpid()},flush=True)
    if path.exists():
        contract=json.loads(path.read_text())
        runner=load_bound_runner(contract)
        candidate=next(r for r in runner["candidates"]() if r["model"]==args.model)
        if args.check_resume:
            runner["preflight"](candidate)
            print("PINNED_RESUME_PREFLIGHT_PASS",args.model)
        else:
            try:
                runner["run_model"](candidate)
            finally:
                append_jsonl(str(root/"controller_attempts.jsonl"),{"attempt":attempt,"event":"end","time":time.time(),"runtime_seconds":time.time()-started},flush=True)
    else:
        from scripts import expanded_worker as runner
        candidate=next(r for r in runner.candidates() if r["model"]==args.model)
        if args.check_resume:
            runner.preflight(candidate)
            print("FRESH_PREFLIGHT_PASS",args.model)
        else:
            snapshots=OUT/"code_snapshots";snapshots.mkdir(parents=True,exist_ok=True)
            for source in [Path(runner.__file__),ROOT/"rewardlens/inference/adapters/expanded.py"]:
                target=snapshots/(sha(source)+".py")
                if not target.exists():shutil.copy2(source,target)
            try:
                runner.run_model(candidate)
            finally:
                append_jsonl(str(root/"controller_attempts.jsonl"),{"attempt":attempt,"event":"end","time":time.time(),"runtime_seconds":time.time()-started},flush=True)

if __name__=="__main__":
    main()
