#!/usr/bin/env python3
"""011: fail-closed external delegation, no process signals or active-code edits."""
import argparse
import json
import os
from pathlib import Path
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

def arm():
    if (CONTROL/"dispatch_hold.json").exists():
        raise ValueError("delegation already armed")
    current=json.loads((BASE/"current_process.json").read_text())
    launcher=json.loads((BASE/"launcher.json").read_text())
    if current["model"]!="molmo_7b_d_0924":
        raise ValueError("011 is no longer running Molmo")
    parent,child=process(launcher["pid"]),process(current["pid"])
    if child["ppid"]!=parent["pid"] or child["state"] in ("T","Z"):
        raise ValueError("expected Molmo child not running")
    if "--model" in parent["cmdline"] or "phase2_autonomous.py" not in parent["cmdline"]:
        raise ValueError("unexpected parent")
    if "--model molmo_7b_d_0924" not in child["cmdline"]:
        raise ValueError("unexpected child")
    if (BASE/MODEL).exists():
        raise ValueError("011 Skywork output already exists; refuse overwrite")
    contract=json.loads((BASE/"run_contract.json").read_text())
    if p.sha(ROOT/"rewardlens/scripts/phase2_autonomous.py")!=contract["code_sha256"]["rewardlens/scripts/phase2_autonomous.py"]:
        raise ValueError("existing dispatch validator changed")
    marker={"schema":"EXTERNAL_MODEL_DELEGATION_V1","complete":False,
            "status":"DELEGATED_TO_017_NOT_A_COMPLETED_RESULT","model_id":MODEL,
            "contract_sha256":p.sha(BASE/"run_contract.json"),"external_output":str(EXTERNAL),
            "expected_parent_stop":"invalid completion receipt",
            "note":"Dispatch guard only; contains no judgments or scientific results."}
    p.write_json(BASE/MODEL/"completion.json",marker,immutable=True)
    try:
        p.validate_completion(BASE/MODEL,contract)
    except ValueError as e:
        if str(e)!="invalid completion receipt":
            raise
    else:
        raise AssertionError("existing validator did not block duplicate dispatch")
    receipt={"status":"DUPLICATE_DISPATCH_BLOCKED","parent":parent,"child":child,
             "assigned_model":MODEL,"output_017":str(EXTERNAL),"time_unix":time.time(),
             "marker_path":str(BASE/MODEL/"completion.json"),
             "marker_sha256":p.sha(BASE/MODEL/"completion.json"),
             "signals_sent":False,"active_code_modified":False}
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
                       "note":"Derived reporting view only. Source contracts, receipts and judgments remain authoritative."}
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
    while True:
        if p.sha(hold["marker_path"])!=hold["marker_sha256"]:
            raise ValueError("duplicate-dispatch guard changed")
        child_live=same_process(child) and process(child["pid"])["state"]!="Z"
        parent_live=same_process(parent) and process(parent["pid"])["state"]!="Z"
        p.write_json(CONTROL/"handoff_status.json",{
            "time_unix":time.time(),"molmo_running":child_live,"original_parent_running":parent_live,
            "duplicate_dispatch_blocked":True,
            "skywork_complete":(EXTERNAL/MODEL/"completion.json").exists(),
            "stage":"WAITING_FOR_NATIVE_COMPLETION_RECEIPTS"})
        if not child_live and not parent_live:
            verified_receipt(BASE,"molmo_7b_d_0924")
            if (EXTERNAL/MODEL/"completion.json").exists():
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
    if args.arm: arm()
    else: watch()

if __name__=="__main__":
    try: main()
    except Exception:
        p.write_json(CONTROL/"handoff_failure.json",{"time":time.time(),"error":traceback.format_exc()})
        raise
