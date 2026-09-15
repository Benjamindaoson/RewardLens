#!/usr/bin/env python3
"""Two-worker model queue, isolated outputs, frozen inference delegated unchanged."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import traceback

ROOT=Path("/root/autodl-tmp/RewardLens/code")
sys.path.insert(0,str(ROOT/"rewardlens"))
from scripts import phase2_autonomous as p
from scripts.expanded_model_acquire import HOSTS,SELECTION,CONTROL
from inference.adapters.expanded import ExpandedAdapter
from inference.metrics import compute_audit_metrics
from scripts.compute_audit_metrics import load_expected

OUT=p.PHASE/"distributed_v1"
AUDIT=ROOT/"outputs/qwen_full/audit_manifest.linux.jsonl"
AUDIT_SHA="880a3769df10e7e4dff5939ba03bbff7347cc62e56b11f79e10f5a1b61d8a018"
SELECTION_SHA="395392050551ed36b91a9209bc6531fe46d4cae101f0b8ed06a84ff3e83c0ab9"

def candidates():
    if p.sha(SELECTION)!=SELECTION_SHA:
        raise ValueError("frozen model selection changed")
    return json.loads(SELECTION.read_text())["candidates"][:4]

def preflight(candidate):
    p.HOST=socket.gethostname()
    baseline,static,pools=p.preflight()
    original=json.loads((p.PHASE/"gpu_4model_v1/run_contract.json").read_text())
    for key in ("code_sha256","static_sha256","downstream_sha256","physical_path_receipt_sha256","gate_sha256","audit_sha256","checkpoints"):
        if baseline[key]!=original[key]:
            raise ValueError("original scientific contract differs: "+key)
    if p.sha(AUDIT)!=AUDIT_SHA:
        raise ValueError("frozen audit manifest hash differs")
    audit=p.read_rows(AUDIT)
    if len(audit)!=2400 or len({r["item_id"] for r in audit})!=2400:
        raise ValueError("invalid audit manifest")
    if any(not Path(r["image_path"]).is_file() for r in audit):
        raise ValueError("frozen audit image missing")
    state=json.loads((CONTROL/"status"/(candidate["model"]+".json")).read_text())
    if state["worker_hostname"]!=socket.gethostname():
        transfer_path=OUT/"checkpoint_transfers"/(candidate["model"]+".json")
        transfer=json.loads(transfer_path.read_text())
        original_receipt=CONTROL/"receipts"/(candidate["model"]+".json")
        if transfer.get("verified") is not True or transfer["model"]!=candidate["model"] or transfer["revision"]!=candidate["revision"]:
            raise ValueError("cross-worker checkpoint transfer not verified")
        if transfer["acquisition_receipt_sha256"]!=p.sha(original_receipt) or p.sha(Path(transfer["shared_checkpoint"])/"acquisition_receipt.json")!=transfer["acquisition_receipt_sha256"]:
            raise ValueError("cross-worker acquisition provenance changed")
        state={**state,"local_checkpoint":transfer["shared_checkpoint"],"worker_hostname":socket.gethostname()}
    if state["revision"]!=candidate["revision"] or state["worker_hostname"]!=socket.gethostname():
        raise ValueError("acquisition provenance differs")
    if not state.get("checkpoint_verified") or not state.get("processor_verified"):
        raise ValueError("acquisition checks incomplete")
    checkpoint=Path(state["local_checkpoint"])
    receipt=json.loads((checkpoint/"acquisition_receipt.json").read_text())
    if receipt["revision"]!=candidate["revision"] or receipt["selection_sha256"]!=SELECTION_SHA:
        raise ValueError("checkpoint receipt differs")
    for row in receipt["files"]:
        if (checkpoint/row["file"]).stat().st_size!=row["bytes"]:
            raise ValueError("checkpoint file size changed")
    contract={"schema":"EXPANDED_PHASE2_V1","model":candidate["model"],"worker":socket.gethostname(),
        "selection_sha256":SELECTION_SHA,"revision":candidate["revision"],"checkpoint":str(checkpoint),
        "acquisition_receipt_sha256":p.sha(checkpoint/"acquisition_receipt.json"),
        "original_contract_sha256":p.sha(p.PHASE/"gpu_4model_v1/run_contract.json"),
        "static_sha256":p.STATIC_SHA,"downstream_sha256":p.DOWN_SHA,"audit_sha256":AUDIT_SHA,
        "adapter_sha256":p.sha(ROOT/"rewardlens/inference/adapters/expanded.py"),
        "runner_sha256":p.sha(Path(__file__)),"frozen_science_code":baseline["code_sha256"]}
    return contract,static,pools,audit

def smoke(adapter,root,contract):
    gate=root/"compatibility_gate.json"
    if gate.exists():
        saved=json.loads(gate.read_text())
        if saved["contract"]!=contract or saved["status"]!="PASS":
            raise ValueError("compatibility gate failed or changed; no semantic re-query")
        return
    if (root/"smoke_attempt.json").exists():
        raise ValueError("prior smoke generation has unknown/failed outcome; explicit engineering reconciliation required")
    from PIL import Image
    image=root/"synthetic_red.png"
    Image.new("RGB",(224,224),"red").save(image)
    prepared=adapter.prepare_inputs(image_path=str(image),question="What color is the image?",candidate_a="Red",candidate_b="Blue")
    p.write_json(root/"smoke_attempt.json",{"time":time.time(),"synthetic_only":True,
        "prompt_sha256":p.sha(ROOT/"rewardlens/inference/prompts/pairwise_ab.txt"),
        "candidate_semantics_unchanged":True},immutable=True)
    result=adapter.judge(prepared)
    parsed=p.parse_ab(result.get("raw_output",""))
    import torch,resource
    memory=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    peak=torch.cuda.max_memory_reserved()
    status="PASS" if parsed in ("A","B") and peak<=72*1024**3 and memory<=100*1024**3 else "ENGINEERING_EXCLUSION"
    p.write_json(gate,{"contract":contract,"status":status,"raw_output":result.get("raw_output"),
        "parsed":parsed,"peak_vram_bytes":peak,"peak_rss_bytes":memory,
        "semantic_queries":1,"selection_used_rewardlens_outcomes":False,"time":time.time()},immutable=True)
    if status!="PASS":
        raise ValueError("predeclared synthetic compatibility gate failed")

def valid_full(root):
    path=root/"completion.json"
    if not path.exists():return False
    receipt=json.loads(path.read_text())
    if receipt.get("complete") is not True:raise ValueError("invalid full completion")
    if any(receipt.get(k)!=v for k,v in {"static_count":800,"pool_count":800,"edge_count":22400,"audit_count":2400}.items()):
        raise ValueError("invalid full completion counts")
    if not receipt.get("artifacts"):raise ValueError("missing full completion artifact hashes")
    for name,digest in receipt["artifacts"].items():
        if p.sha(root/name)!=digest:raise ValueError("completed artifact changed: "+name)
    return receipt

def run_model(candidate):
    root=OUT/candidate["model"]
    root.mkdir(parents=True,exist_ok=True)
    with (root/"model.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if valid_full(root):return
        contract,static,pools,audit=preflight(candidate)
        p.write_json(root/"contract.json",contract,immutable=True)
        adapter=ExpandedAdapter(candidate["model"],contract["checkpoint"])
        started=time.time()
        p.write_json(root/"task_status.json",{"stage":"loading","pid":os.getpid(),"time":started})
        adapter.load_model()
        smoke(adapter,root,contract)
        p.write_json(root/"readiness.json",{"formal_run_ready":True,"gate_sha256":p.sha(root/"compatibility_gate.json")})
        try:
            # Same run_items execution and frozen audit definitions, including parse handling.
            auditroot=root/"audit"
            auditroot.mkdir(exist_ok=True)
            p.write_json(root/"task_status.json",{"stage":"audit","pid":os.getpid(),"time":time.time()})
            def progress(count,row):
                if count%10==0:
                    p.write_json(root/"task_status.json",{"stage":"audit","completed":count,"total":2400,"pid":os.getpid(),"time":time.time()})
            judgments=p.execute_static(audit,adapter,candidate["model"],auditroot,progress)
            metrics=compute_audit_metrics(judgments,load_expected(str(AUDIT)))
            p.write_json(auditroot/"metrics.json",{"rows":metrics,"completed":len(judgments),
                "failures":sum(r["status"]!="ok" for r in judgments)},immutable=True)
            import inference.runner_lib as runner
            runner.build_adapter=lambda args:adapter
            p.OUT=root/"execution"
            p.MODELS=(candidate["model"],)
            p.ADAPTERS=("hf",)
            p.preflight=lambda:(contract,static,pools)
            p.run_model(candidate["model"])
            phase_root=p.OUT/candidate["model"]
            phase=p.validate_completion(phase_root,contract)
            if not phase or len(judgments)!=2400:
                raise ValueError("model outputs incomplete")
            files=[root/"contract.json",root/"compatibility_gate.json",auditroot/"static.jsonl",
                   auditroot/"metrics.json",phase_root/"completion.json",p.OUT/"run_contract.json"]
            files.extend(phase_root/name for name in phase["artifacts"])
            receipt={"complete":True,"model":candidate["model"],"family":candidate["family"],
                "worker_hostname":socket.gethostname(),"checkpoint_revision":candidate["revision"],
                "static_count":800,"pool_count":800,"edge_count":22400,"audit_count":2400,
                "abstention_count":sum(r["outcome"]=="abstain" for r in p.read_rows(phase_root/"pairs.jsonl")),
                "wall_seconds":time.time()-started,"gpu_allocated_hours_this_attempt":(time.time()-started)/3600,
                "phase2_receipt":str(phase_root/"completion.json"),"completion_timestamp":time.time(),
                "artifacts":{str(f.relative_to(root)):p.sha(f) for f in files}}
            p.write_json(root/"completion.json",receipt,immutable=True)
            p.write_json(root/"task_status.json",{"stage":"complete","pid":os.getpid(),"time":time.time()})
        finally:
            adapter.cleanup()

def gpu_busy():
    result=subprocess.run(["nvidia-smi","--query-compute-apps=pid","--format=csv,noheader,nounits"],
                          capture_output=True,text=True,timeout=10)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return bool(result.stdout.strip())

def worker(worker_id):
    if socket.gethostname()!=HOSTS[worker_id]:raise ValueError("wrong worker")
    OUT.mkdir(parents=True,exist_ok=True)
    control=OUT/"workers"/worker_id
    control.mkdir(parents=True,exist_ok=True)
    # ponytail: one worker process per host; exclusive model lock provides cross-host exclusion.
    with (ROOT/(".expanded_worker_"+worker_id+".lock")).open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        while True:
            available=candidates()
            if gpu_busy():
                p.write_json(control/"status.json",{"stage":"waiting_for_existing_gpu_job","time":time.time(),"gpu":p.gpu()})
                time.sleep(15);continue
            task=None
            for candidate in available:
                if candidate["assigned_worker"]!=worker_id:continue
                root=OUT/candidate["model"]
                if valid_full(root):continue
                if (root/"worker_failure.json").exists():continue
                state_path=CONTROL/"status"/(candidate["model"]+".json")
                if not state_path.exists():continue
                state=json.loads(state_path.read_text())
                if state.get("checkpoint_verified") and state.get("processor_verified"):
                    task=candidate;break
            if task is None:
                p.write_json(control/"status.json",{"stage":"waiting_for_ready_checkpoint_or_engineering_repair","time":time.time(),"gpu":p.gpu()})
                time.sleep(15);continue
            root=OUT/task["model"];root.mkdir(parents=True,exist_ok=True)
            python=ROOT/".venv_phi35/bin/python" if task["model"]=="phi35_vision_instruct" and (ROOT/".venv_phi35/bin/python").exists() else Path(sys.executable)
            with (root/"console.log").open("a") as log:
                proc=subprocess.Popen([str(python),"-u",__file__,"--model",task["model"]],
                    stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy())
                while proc.poll() is None:
                    p.write_json(control/"status.json",{"stage":"running","model":task["model"],"pid":proc.pid,"time":time.time(),"gpu":p.gpu()})
                    time.sleep(10)
            p.write_json(control/"last_exit.json",{"model":task["model"],"returncode":proc.returncode,"time":time.time()})
            if proc.returncode:
                p.write_json(root/"worker_failure.json",{"returncode":proc.returncode,"time":time.time(),"resume_preserved":True})
            time.sleep(1)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker",choices=HOSTS)
    parser.add_argument("--model")
    parser.add_argument("--preflight",action="store_true")
    args=parser.parse_args()
    os.environ.update(HF_HUB_OFFLINE="1",TRANSFORMERS_OFFLINE="1",HF_HUB_DISABLE_TELEMETRY="1",
                      TOKENIZERS_PARALLELISM="false",OMP_NUM_THREADS="1")
    os.chdir(ROOT)
    if args.model:
        candidate=next(r for r in candidates() if r["model"]==args.model)
        if args.preflight:
            contract,static,pools,audit=preflight(candidate)
            print(json.dumps({"preflight":"PASS","static":len(static),"pools":len(pools),"audit":len(audit)}))
        else:
            run_model(candidate)
    else:
        worker(args.worker)

if __name__=="__main__":
    if "--model" in sys.argv:
        os.execv(sys.executable,[sys.executable,str(ROOT/"rewardlens/scripts/expanded_model_entry.py"),*sys.argv[1:]])
    main()
