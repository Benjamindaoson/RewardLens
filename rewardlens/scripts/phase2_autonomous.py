#!/usr/bin/env python3
"""Remote-only durable execution; scientific behavior is delegated to frozen code."""
from __future__ import annotations

import argparse
import collections
import contextlib
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import traceback
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "rewardlens"))
from inference.bon import (pool_candidates, evaluate_pairwise_graph,
                           scalar_pair_graph, derive_subset_selections, oriented_pair)
from inference.common import load_items, resolve_image_path, run_items
from inference.metrics import accuracy_from_static, downstream_utility_from_selections
from inference.parsers.ab_parser import parse_ab
from lib.jsonl_io import append_jsonl
from models.registry import get_model

SHARED = Path("/root/autodl-fs/RewardLens")
PHASE = SHARED / "results/phase2"
GATE = PHASE / "READY_FOR_PHASE2_GPU.json"
OUT = PHASE / "gpu_4model_v1"
STATIC = ROOT / "manifests/fast_eval/static_manifest.jsonl"
STATIC_SHA = "6e4a23fc54d4704e70587b177586152e6e63b7a4dac5964e7e16f56395e682e3"
DOWN_SHA = "0afb6dfefd7a47e3dc47fd05127e82d5fd260943d04e5c5cc3117ae11055133c"
HOST = "autodl-container-47bb4a8b0c-371e5795"
MODELS = ("qwen3_vl_4b_instruct", "gemma3_4b_it", "molmo_7b_d_0924", "skywork_vl_reward_7b")
ADAPTERS = ("qwen_vl", "gemma", "molmo", "specialized_reward")
CHECKPOINTS = (
    "Qwen/Qwen3-VL-4B-Instruct", "google/gemma-3-4b-it",
    "allenai/Molmo-7B-D-0924", "Skywork/Skywork-VL-Reward-7B",
)
FACTORS = ("count", "attribute", "presence", "spatial")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_rows(path):
    if not Path(path).exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def sync_dir(path):
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_json(path, data, *, immutable=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if immutable and path.exists():
        if json.loads(path.read_text()) != data:
            raise ValueError("immutable receipt conflict: " + str(path))
        return
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temp.open("x", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    if immutable:
        os.link(temp, path)
        temp.unlink()
    else:
        os.replace(temp, path)
    sync_dir(path.parent)


class Journal:
    """Append/fsync records; only a torn EOF is quarantined, never valid rows."""
    def __init__(self, path, key):
        self.path, self.key = Path(path), key
        self.rows = {}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            return
        with self.path.open("rb") as f:
            data = f.read()
        offset = 0
        for line in data.splitlines(keepends=True):
            try:
                row = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                if offset + len(line) != len(data) or line.endswith(b"\n"):
                    raise ValueError("corrupt non-tail journal: " + str(self.path))
                quarantine = self.path.with_name(self.path.name + ".torn." + uuid.uuid4().hex)
                with quarantine.open("xb") as q:
                    q.write(line)
                    q.flush()
                    os.fsync(q.fileno())
                with self.path.open("r+b") as w:
                    w.truncate(offset)
                    w.flush()
                    os.fsync(w.fileno())
                sync_dir(self.path.parent)
                break
            identity = key(row)
            if identity in self.rows:
                raise ValueError("duplicate durable record: " + str(identity))
            self.rows[identity] = row
            offset += len(line)
        else:
            if data and not data.endswith(b"\n"):
                with self.path.open("ab") as w:
                    w.write(b"\n")
                    w.flush()
                    os.fsync(w.fileno())

    def add(self, row):
        identity = self.key(row)
        if identity in self.rows:
            if self.rows[identity] != row:
                raise ValueError("conflicting durable record: " + str(identity))
            return
        append_jsonl(str(self.path), row, flush=True)
        self.rows[identity] = row


def read_gate_payload(receipt, expected_sha=DOWN_SHA):
    if receipt.get("ready_for_phase2_gpu") is not True:
        raise ValueError("READY must explicitly contain boolean ready_for_phase2_gpu=true")
    path = Path(receipt["downstream_v2_manifest"])
    if not path.is_absolute() or not path.is_file():
        raise ValueError("READY manifest must be an existing absolute local path")
    if receipt.get("downstream_v2_manifest_sha256") != expected_sha or sha(path) != expected_sha:
        raise ValueError("READY downstream manifest hash conflict")
    return path


def preflight():
    os.chdir(ROOT)
    if socket.gethostname() != HOST:
        raise ValueError("wrong host")
    receipt = json.loads(GATE.read_text())
    downstream = read_gate_payload(receipt)
    if sha(STATIC) != STATIC_SHA:
        raise ValueError("frozen D_static hash conflict")
    if receipt.get("factor_counts") != {f: 200 for f in FACTORS}:
        raise ValueError("READY factor counts conflict")
    if receipt.get("physical_overlap_counts") != {
        "audit_downstream": 0, "audit_static": 0, "static_downstream": 0
    }:
        raise ValueError("READY overlap counts conflict")
    static, pools = load_items(str(STATIC)), load_items(str(downstream))
    physical_path = PHASE / "phase2_v2_physical_sha_manifests.json"
    physical = json.loads(physical_path.read_text())
    static_paths = {r["item_id"]: r["image_path"] for r in physical["static"]}
    if len(static_paths) != 800:
        raise ValueError("static path receipt incomplete")
    for items in (static, pools):
        if len(items) != 800 or len({r["item_id"] for r in items}) != 800:
            raise ValueError("manifest must have 800 unique item IDs")
        if collections.Counter(r["factor"] for r in items) != {f: 200 for f in FACTORS}:
            raise ValueError("manifest factor quota mismatch")
        for row in items:
            carrier = row.get("dataset")
            if carrier is None and row["item_id"].startswith("gqa_"):
                carrier = "gqa"
            if carrier != ("tallyqa" if row["factor"] == "count" else "gqa"):
                raise ValueError("carrier mismatch")
            row["dataset"] = carrier
    for row in static:
        if row.get("expected_preference") not in ("A", "B"):
            raise ValueError("static label missing")
        if not row.get("candidate_a") or not row.get("candidate_b"):
            raise ValueError("static candidates missing")
        # Runtime path binding from the final physical receipt; frozen file stays untouched.
        row["image_path"] = static_paths[row["item_id"]]
        if not Path(row["image_path"]).is_file():
            raise ValueError("static image unavailable")
    for row in pools:
        pool_candidates(row)
        if not Path(row["image_path"]).is_file():
            raise ValueError("downstream image unavailable")
    if {r["item_id"] for r in static} & {r["item_id"] for r in pools}:
        raise ValueError("static/downstream item overlap")
    fingerprints = {}
    for relative in (
        "rewardlens/inference/bon.py", "rewardlens/inference/common.py",
        "rewardlens/inference/metrics.py", "rewardlens/inference/phase2_analysis.py",
        "rewardlens/inference/parsers/ab_parser.py", "rewardlens/inference/prompts/pairwise_ab.txt",
        "rewardlens/inference/adapters/hf_vlm.py", "rewardlens/inference/adapters/molmo_native.py",
        "rewardlens/inference/adapters/skywork_reward.py", "rewardlens/inference/adapters/__init__.py",
        "rewardlens/models/model_registry.json", "rewardlens/stats/__init__.py",
        "rewardlens/configs/rq2_analysis.json", "rewardlens/configs/rq3_analysis.json",
        "rewardlens/scripts/phase2_autonomous.py", "rewardlens/scripts/phase2_report.py",
    ):
        fingerprints[relative] = sha(ROOT / relative)
    checkpoints = {}
    audits = {}
    for model, checkpoint in zip(MODELS, CHECKPOINTS):
        p = SHARED / "models" / checkpoint
        if get_model(model)["checkpoint"] != str(p):
            raise ValueError("registry local checkpoint mismatch")
        index = json.loads((p / "model.safetensors.index.json").read_text())
        sizes = {}
        for shard in set(index["weight_map"].values()):
            target = p / shard
            if not target.is_file() or target.stat().st_size < 1000:
                raise ValueError("checkpoint shard unavailable")
            sizes[shard] = target.stat().st_size
        checkpoints[model] = {"path": str(p), "index_sha256": sha(p / "model.safetensors.index.json"),
                              "config_sha256": sha(p / "config.json"), "shard_sizes": sizes}
        if model == MODELS[3]:
            checkpoints[model]["value_head_sha256"] = sha(p / "value_head.safetensors")
        if model == MODELS[2]:
            checkpoints[model]["local_model_code"] = {x.name: sha(x) for x in p.glob("*.py")}
        audit = SHARED / "results/metrics" / model / "contract_metrics.json"
        rows = json.loads(audit.read_text())["rows"]
        if {r["factor"] for r in rows} != set(FACTORS) | {"overall"}:
            raise ValueError("audit metrics incomplete")
        audits[model] = sha(audit)
    contract = {
        "schema": "PHASE2_AUTONOMOUS_V1", "host": HOST, "gate_sha256": sha(GATE),
        "downstream_manifest": str(downstream), "downstream_sha256": DOWN_SHA,
        "static_manifest": str(STATIC), "static_sha256": STATIC_SHA,
        "physical_path_receipt_sha256": sha(physical_path), "models": list(MODELS),
        "code_sha256": fingerprints, "checkpoints": checkpoints, "audit_sha256": audits,
        "n_pools": 800, "n_static": 800, "primary_n": 8, "derived_n": [2, 4],
        "no_raw_image_hashing_at_launch": True,
    }
    return contract, static, pools


def execute_static(items, adapter, model, root, progress=None):
    root = Path(root)
    journal = Journal(root / "static.jsonl", lambda r: r["item_id"])
    expected = {r["item_id"]: r for r in items}
    if not set(journal.rows) <= set(expected):
        raise ValueError("unexpected static IDs")
    for saved in journal.rows.values():
        if saved["model_id"] != model or saved["factor"] != expected[saved["item_id"]]["factor"]:
            raise ValueError("static provenance mismatch")
        if saved["status"] not in ("ok", "parse_error"):
            raise ValueError("saved static infrastructure error requires explicit engineering repair")
    for item in items:
        if item["item_id"] in journal.rows:
            continue
        run_items(items=[item], adapter=adapter, model_id=model,
                  out_jsonl=str(journal.path), fail_jsonl=str(root / "static_failures.jsonl"),
                  parse_fn=parse_ab, skip_completed=False)
        # run_items is the existing frozen static execution path and fsyncs each row.
        with journal.path.open("rb") as f:
            f.seek(max(0, f.seek(0, 2) - 262144))
            tail = f.read().splitlines()[-1]
        row = json.loads(tail)
        journal.rows[item["item_id"]] = row
        if progress:
            progress(len(journal.rows), row)
        if row["status"] not in ("ok", "parse_error"):
            raise RuntimeError("static infrastructure failure: " + str(row["raw_output"]))
    return list(journal.rows.values())


def bon_journals(root):
    root = Path(root)
    return (
        Journal(root / "pairs.jsonl", lambda r: r["pair_key"]),
        Journal(root / "selections.jsonl", lambda r: (r["pool_id"], r["n"])),
        Journal(root / "scores.jsonl", lambda r: (r["pool_id"], r["candidate_uid"])),
    )


def execute_pool(item, adapter, model, root, image_path, journals=None, on_edge=None):
    pairs, selections, scores = journals if journals is not None else bon_journals(root)
    parsed = pool_candidates(item)
    pid = parsed["pool_id"]
    metadata = {"schema_version": "PHASE2_BON_V2", "pool_id": pid,
                "item_id": item["item_id"], "model_id": model,
                "factor": item["factor"], "dataset": item["dataset"]}
    existing = [r for r in pairs.rows.values() if r["pool_id"] == pid]
    allowed = {r["uid"] for r in parsed["records"]}
    for row in existing:
        if any(row.get(k) != v for k, v in metadata.items()):
            raise ValueError("pair provenance mismatch")
        if row["left_uid"] not in allowed or row["right_uid"] not in allowed:
            raise ValueError("unknown candidate in saved edge")
        if (row["left_uid"], row["right_uid"]) != oriented_pair(pid, row["left_uid"], row["right_uid"]):
            raise ValueError("saved orientation mismatch")
        if row["pair_key"] != pid + "|" + row["left_uid"] + "|" + row["right_uid"]:
            raise ValueError("saved pair key mismatch")
        if row["status"] not in ("ok", "semantic_abstention"):
            raise ValueError("invalid completed edge status")
        if (row["outcome"] == "abstain") != (row["status"] == "semantic_abstention"):
            raise ValueError("abstention/status mismatch")
    completed = set(pairs.rows)

    def persist(row):
        pairs.add({**metadata, **row})
        existing.append({**metadata, **row})
        if on_edge:
            on_edge()

    if len(existing) < 28:
        if callable(getattr(adapter, "score_candidate", None)):
            values = {}
            for record in parsed["records"]:
                key = (pid, record["uid"])
                if key not in scores.rows:
                    value = float(adapter.score_candidate(image_path=image_path,
                                  question=item["question"], candidate=record["candidate"]["text"]))
                    if not math.isfinite(value):
                        raise ValueError("non-finite scalar reward")
                    scores.add({**metadata, "candidate_uid": record["uid"], "score": value})
                saved = scores.rows[key]
                if any(saved.get(k) != v for k, v in metadata.items()):
                    raise ValueError("scalar provenance mismatch")
                values[record["uid"]] = saved["score"]
            for row in scalar_pair_graph(item, values):
                row["pair_key"] = pid + "|" + row["left_uid"] + "|" + row["right_uid"]
                if row["pair_key"] not in completed:
                    persist(row)
        else:
            evaluate_pairwise_graph(item, adapter, image_path=image_path,
                                    completed_pair_keys=completed, on_row=persist)
    derived = derive_subset_selections(item, existing)
    for n in (2, 4, 8):
        selections.add({**metadata, "n": n, "status": "ok", **derived[n],
                        "utility_success": derived[n]["success"]})
    return derived


def gpu():
    try:
        text = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
             "--format=csv,noheader,nounits"], text=True, timeout=5).strip().split(",")
        return {"util_percent": int(text[0]), "vram_mib": int(text[1]), "total_mib": int(text[2])}
    except Exception as e:
        return {"error": str(e)}


def update_status(**data):
    write_json(OUT / "live_status.json", {"time_unix": time.time(), "pid": os.getpid(), **data})


def validate_completion(root, contract):
    path = root / "completion.json"
    if not path.exists():
        return None
    receipt = json.loads(path.read_text())
    if receipt["contract_sha256"] != sha(OUT / "run_contract.json"):
        raise ValueError("completion belongs to another contract")
    if receipt.get("complete") is not True:
        raise ValueError("invalid completion receipt")
    for name, digest in receipt["artifacts"].items():
        if sha(root / name) != digest:
            raise ValueError("completed artifact was changed: " + name)
    if receipt["static_completed"] != 800 or receipt["pools_completed"] != 800 or receipt["pair_edges"] != 22400:
        raise ValueError("completion counts invalid")
    return receipt


def run_model(model):
    contract, static, pools = preflight()
    write_json(OUT / "run_contract.json", contract, immutable=True)
    root = OUT / model
    root.mkdir(parents=True, exist_ok=True)
    if validate_completion(root, contract):
        update_status(model=model, stage="complete", checkpoint="validated existing completion")
        return
    from inference.runner_lib import build_adapter
    started = time.time()
    attempt = uuid.uuid4().hex
    append_jsonl(str(root / "attempts.jsonl"), {"attempt": attempt, "event": "start", "time": started})
    last_update = [0.0]
    stage = ["loading"]
    counters = {"static_completed": len(read_rows(root / "static.jsonl")),
                "pools_completed": 0, "pair_edges": len(read_rows(root / "pairs.jsonl")),
                "abstentions": sum(r["outcome"] == "abstain" for r in read_rows(root / "pairs.jsonl"))}

    def progress(force=False):
        now = time.time()
        if not force and now - last_update[0] < 2:
            return
        last_update[0] = now
        update_status(model=model, stage=stage[0], **counters,
                      static_total=800, pools_total=800, pair_edges_total=22400,
                      elapsed_seconds=now-started, checkpoint="JSONL fsync",
                      abstention_rate=counters["abstentions"]/max(1,counters["pair_edges"]))

    adapter = None
    try:
        import torch
        if not torch.cuda.is_available() or "A800" not in torch.cuda.get_device_name(0):
            raise ValueError("A800 not available to project venv")
        progress(True)
        adapter = build_adapter(argparse.Namespace(model_id=model, adapter=ADAPTERS[MODELS.index(model)]))
        adapter.load_model()
        stage[0] = "static"
        progress(True)

        def on_static(count, row):
            counters["static_completed"] = count
            progress()

        judgments = execute_static(static, adapter, model, root, on_static)
        by_id = {r["item_id"]:r for r in static}
        enriched = [{**r, "expected_preference":by_id[r["item_id"]]["expected_preference"]} for r in judgments]
        static_metrics = accuracy_from_static(enriched)
        n_scored = sum(r["n"] for r in static_metrics)
        static_summary = {"rows":static_metrics, "completed":len(judgments),
                          "failures":sum(r["status"]!="ok" for r in judgments),
                          "n_scored_by_existing_metric":n_scored,
                          "A":sum(r["A"]*r["n"] for r in static_metrics)/n_scored if n_scored else None,
                          "note":"Existing accuracy_from_static filtering unchanged; parse errors reported separately."}
        write_json(root / "static_metrics.json", static_summary, immutable=True)
        stage[0] = "downstream"
        journals = bon_journals(root)
        valid_ids = {r["item_id"] for r in pools}
        for journal in journals:
            if any(r["pool_id"] not in valid_ids or r["model_id"] != model for r in journal.rows.values()):
                raise ValueError("unexpected downstream journal provenance")

        def edge():
            counters["pair_edges"] = len(journals[0].rows)
            counters["abstentions"] = sum(r["outcome"] == "abstain" for r in journals[0].rows.values())
            progress()

        for item in pools:
            execute_pool(item, adapter, model, root, item["image_path"], journals, edge)
            counters["pools_completed"] += 1
            progress()
        utility = downstream_utility_from_selections(journals[1].rows.values())
        if len(journals[0].rows) != 22400 or len(journals[1].rows) != 2400:
            raise ValueError("incomplete downstream outputs")
        if len(utility) != 12 or any(r["n_pools"] != 200 for r in utility):
            raise ValueError("incomplete factor utility")
        write_json(root / "utility.json", {"rows":utility}, immutable=True)
        runtime = time.time()-started
        append_jsonl(str(root / "attempts.jsonl"), {"attempt":attempt,"event":"complete",
                     "time":time.time(),"runtime_seconds":runtime})
        prior_runtime = sum(r.get("runtime_seconds",0) for r in read_rows(root/"attempts.jsonl"))
        names = ["static.jsonl","static_metrics.json","pairs.jsonl","selections.jsonl","utility.json"]
        if (root/"scores.jsonl").exists():
            names.append("scores.jsonl")
        receipt = {"complete":True,"model_id":model,"contract_sha256":sha(OUT/"run_contract.json"),
                   "static_completed":len(judgments),"static_failures":static_summary["failures"],
                   "static_A":static_summary["A"],"pools_completed":800,"pair_edges":22400,
                   "abstention_rate":counters["abstentions"]/22400,
                   "runtime_seconds":prior_runtime, "finished_unix":time.time(),
                   "U":{str(n):sum(r["U"] for r in utility if r["N"]==n)/4 for n in (2,4,8)},
                   "artifacts":{name:sha(root/name) for name in names}}
        write_json(root/"completion.json",receipt,immutable=True)
        stage[0]="complete"
        progress(True)
    except Exception:
        failure={"attempt":attempt,"event":"failed","time":time.time(),"model_id":model,
                 "stage":stage[0],"runtime_seconds":time.time()-started,"error":traceback.format_exc()}
        append_jsonl(str(root/"attempts.jsonl"),failure)
        write_json(root/("failure_"+attempt+".json"),failure,immutable=True)
        update_status(model=model,stage="failed",checkpoint="partial durable results preserved",
                      error=failure["error"],**counters)
        raise
    finally:
        if adapter is not None:
            adapter.cleanup()


def dashboard():
    status_path = OUT/"live_status.json"
    data = json.loads(status_path.read_text()) if status_path.exists() else {}
    dev = gpu()
    elapsed=data.get("elapsed_seconds",0)
    stage=data.get("stage","starting")
    done=data.get("static_completed",0) if stage=="static" else data.get("pair_edges",0)
    total=800 if stage=="static" else 22400
    rate=done/elapsed if elapsed else 0
    eta=(total-done)/rate if rate else None
    display={**data,"gpu":dev,"percent":100*done/total,"throughput_per_second":rate,"eta_seconds":eta}
    write_json(OUT/"dashboard.json",display)
    print("\033[2J\033[HRewardLens · Phase II · "+data.get("model","-"),flush=True)
    print("Stage:",stage,"| Static:",str(data.get("static_completed",0))+"/800",
          "| Pools:",str(data.get("pools_completed",0))+"/800")
    print("Pair edges:",str(data.get("pair_edges",0))+"/22400",
          "| %.2f%% | %.3f/s"%(100*done/total,rate))
    print("Elapsed: %.0fs | ETA: %s | Abstention: %.4f"%(elapsed,
          "N/A" if eta is None else "%.0fs"%eta,data.get("abstention_rate",0)))
    print("GPU:",dev,"| Checkpoint:",data.get("checkpoint","pending"),flush=True)


def pipeline():
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT/"execution.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        contract, _, _ = preflight()
        write_json(OUT/"run_contract.json",contract,immutable=True)
        write_json(OUT/"launcher.json",{"pid":os.getpid(),"host":socket.gethostname(),
                   "started_unix":time.time(),"screen_session":"phase2_gpu"})
        for model in MODELS:
            # Revalidate gate and bound code before each model. No raw-image hashing.
            current, _, _ = preflight()
            if current != contract:
                raise ValueError("contract changed during execution")
            root=OUT/model
            root.mkdir(exist_ok=True)
            if validate_completion(root,contract):
                continue
            with (root/"console.log").open("a") as log:
                proc=subprocess.Popen([sys.executable,"-u",__file__,"--model",model],
                                      stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy())
                write_json(OUT/"current_process.json",{"pid":proc.pid,"model":model,"started_unix":time.time()})
                while proc.poll() is None:
                    dashboard()
                    time.sleep(10)
                append_jsonl(str(OUT/"model_exits.jsonl"),{"model":model,"returncode":proc.returncode,"time":time.time()})
            dashboard()
        from scripts.phase2_report import report
        update_status(model="all",stage="preliminary_analysis",checkpoint="model receipts retained")
        report(OUT)
        update_status(model="all",stage="finished",checkpoint="final_summary.json")
        dashboard()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight",action="store_true",help="structural/manifest hash checks only; no model load")
    parser.add_argument("--model",choices=MODELS,help="internal sequential worker; still requires READY")
    args=parser.parse_args()
    for key in ("HF_HUB_OFFLINE","TRANSFORMERS_OFFLINE"):
        os.environ[key]="1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"]="1"
    os.environ["TOKENIZERS_PARALLELISM"]="false"
    os.chdir(ROOT)
    if args.preflight:
        contract,static,pools=preflight()
        print(json.dumps({"preflight":"PASS","static":len(static),"downstream":len(pools),
                          "downstream_sha256":contract["downstream_sha256"]}))
    elif args.model:
        run_model(args.model)
    else:
        pipeline()
    return 0


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except Exception:
        if OUT.exists():
            write_json(OUT/"launcher_failure.json",{"time":time.time(),"error":traceback.format_exc()})
        raise
