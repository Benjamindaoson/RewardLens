#!/usr/bin/env python3
"""Read-only reconstruction and frozen factorwise confirmatory analysis."""
import argparse
import collections
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

ROOT=Path("/root/autodl-tmp/RewardLens/code")
sys.path.insert(0,str(ROOT/"rewardlens"))
from scripts import phase2_autonomous as p
from scripts.expanded_worker import OUT,candidates,valid_full,AUDIT,AUDIT_SHA
from scripts.phase2_report import preliminary_models,text_once,csv_text
from inference.metrics import accuracy_from_static,compute_audit_metrics,downstream_utility_from_selections
from scripts.compute_audit_metrics import load_expected
from stats import FACTORS,_fit_ols,cluster_bootstrap,factor_specificity,_zscore,_mean,accuracy_matched_pairs
from models.registry import get_model

FINAL=OUT/"final"
ORIGINAL=p.MODELS

def validate_rows(rows):
    keys=[(r["model_id"],r["factor"]) for r in rows]
    if len(set(keys))!=len(keys):raise ValueError("duplicate model-factor row")
    for model in {r["model_id"] for r in rows}:
        if {r["factor"] for r in rows if r["model_id"]==model}!=set(FACTORS):
            raise ValueError("missing factor row")

def analyze_factor(rows):
    if any(not isinstance(r.get(k),(int,float)) or not math.isfinite(r[k]) for r in rows for k in ("A","PFC","PSC","U")):
        return {"status":"NOT_IDENTIFIABLE","n_models":len(rows),"folds":[],"delta_mae":None,"bootstrap":None,"reason":"missing/nonfinite metric; no model dropped"}
    result=preliminary_models(rows)
    result.pop("evidence",None)
    result["status"]="ESTIMABLE" if result["delta_mae"] is not None else "NOT_IDENTIFIABLE"
    result["bootstrap"]=None
    if result["delta_mae"] is not None:
        losses=[{"family":f["held_out_family"],"delta":f["delta_mae"]} for f in result["folds"]]
        result["bootstrap"]=cluster_bootstrap(losses,stat_fn=lambda rs:sum(r["delta"] for r in rs)/len(rs),
                                              n_boot=1000,seed=20260912)
        result["bootstrap"]["scope"]="held-out family loss contributions conditional on fitted LOFO models; no refit"
    return result

def matrix_analysis(table):
    keyed={(r["model_id"],r["factor"]):r for r in table}
    cells=[]
    for source in FACTORS:
        for target in FACTORS:
            rows=[{**r,"PFC":keyed[(r["model_id"],source)]["PFC"],"PSC":keyed[(r["model_id"],source)]["PSC"]}
                  for r in table if r["factor"]==target]
            fit=analyze_factor(rows)
            cells.append({"audit_factor":source,"downstream_factor":target,"score":fit["delta_mae"],
                          "status":fit["status"],"fit":fit})
    summary=None;sensitivity=None
    if all(c["score"] is not None for c in cells):
        summary=factor_specificity(cells)
        factors=("attribute","presence","spatial")
        grid={a:{b:next(c["score"] for c in cells if c["audit_factor"]==a and c["downstream_factor"]==b) for b in factors} for a in factors}
        zgrid={a:{} for a in factors}
        for b in factors:
            for a,z in zip(factors,_zscore([grid[a][b] for a in factors])):zgrid[a][b]=z
        diag=[zgrid[a][a] for a in factors]
        off=[zgrid[a][b] for a in factors for b in factors if a!=b]
        sensitivity={"role":"sensitivity_only","factors":list(factors),"matrix":grid,"column_standardized_matrix":zgrid,
                     "diagonal_minus_off":_mean(diag)-_mean(off)}
    return {"matrix":cells,"primary_4factor":summary,"gqa_only_3factor_sensitivity":sensitivity,
            "contribution_definition":"LOFO MAE(U_df~A_df) minus LOFO MAE(U_df~A_df+PFC_af+PSC_af)",
            "status":"ESTIMABLE" if summary else "NOT_IDENTIFIABLE",
            "source_confound_warning":"Within-column standardization does not remove TallyQA versus GQA source confounding."}

def verified_receipt(root):
    receipt=json.loads((root/"completion.json").read_text())
    if receipt.get("complete") is not True or any(receipt[k]!=n for k,n in [("static_completed",800),("pools_completed",800),("pair_edges",22400)]):
        raise ValueError("invalid Phase II completion")
    for name,digest in receipt["artifacts"].items():
        if p.sha(root/name)!=digest:raise ValueError("changed completed result "+str(root/name))
    if receipt["contract_sha256"]!=p.sha(root.parent/"run_contract.json"):
        raise ValueError("result contract mismatch")
    return receipt

def verify_graphs(root,model,static,pools):
    judgments=p.read_rows(root/"static.jsonl")
    if len(judgments)!=800 or {r["item_id"] for r in judgments}!={r["item_id"] for r in static}:
        raise ValueError("static IDs/counts invalid")
    static_by_id={r["item_id"]:r for r in static}
    if any(r["model_id"]!=model or r["status"] not in ("ok","parse_error") or
           any(r.get(k)!=static_by_id[r["item_id"]].get(k) for k in ("factor","candidate_a","candidate_b"))
           for r in judgments):
        raise ValueError("static result provenance/status invalid")
    pairs=p.read_rows(root/"pairs.jsonl");selections=p.read_rows(root/"selections.jsonl")
    if len(pairs)!=22400 or len({r["pair_key"] for r in pairs})!=22400:
        raise ValueError("pair graph count/duplicate invalid")
    if len(selections)!=2400 or len({(r["pool_id"],r["n"]) for r in selections})!=2400:
        raise ValueError("selection count/duplicate invalid")
    bypool=collections.defaultdict(list)
    for row in pairs:
        if row["model_id"]!=model:raise ValueError("pair model mismatch")
        bypool[row["pool_id"]].append(row)
    selected={(r["pool_id"],r["n"]):r for r in selections}
    if set(bypool)!={r["item_id"] for r in pools}:raise ValueError("unknown/missing pool")
    for pool in pools:
        pid=pool["item_id"];edges=bypool[pid]
        if len(edges)!=28:raise ValueError("incomplete pair graph")
        for row in edges:
            if row["factor"]!=pool["factor"] or row["dataset"]!=pool["dataset"] or row["item_id"]!=pid:
                raise ValueError("pair factor/carrier/item mismatch")
            if row["pair_key"]!=pid+"|"+row["left_uid"]+"|"+row["right_uid"]:
                raise ValueError("pair key mismatch")
            if row["status"] not in ("ok","semantic_abstention"):
                raise ValueError("unexpected pair status")
            if (row["left_uid"],row["right_uid"])!=p.oriented_pair(pid,row["left_uid"],row["right_uid"]):
                raise ValueError("orientation changed")
            if (row["outcome"]=="abstain")!=(row["status"]=="semantic_abstention"):
                raise ValueError("abstention changed")
        derived=p.derive_subset_selections(pool,edges)
        for n in (2,4,8):
            saved=selected[(pid,n)]
            if saved["model_id"]!=model or saved["status"]!="ok" or saved["factor"]!=pool["factor"] or saved["dataset"]!=pool["dataset"]:
                raise ValueError("selection provenance/status changed")
            if saved.get("utility_success")!=derived[n]["success"]:
                raise ValueError("utility_success differs from frozen graph success")
            if any(saved[k]!=v for k,v in derived[n].items()):
                raise ValueError("nested subset/Copeland/tie derivation differs")
    expected={r["item_id"]:r["expected_preference"] for r in static}
    sm=accuracy_from_static([{**r,"expected_preference":expected[r["item_id"]]} for r in judgments])
    um=downstream_utility_from_selections(selections)
    if sm!=json.loads((root/"static_metrics.json").read_text())["rows"]:
        raise ValueError("static metrics cannot be reproduced")
    if um!=json.loads((root/"utility.json").read_text())["rows"]:
        raise ValueError("utility cannot be reproduced")
    n_scored=sum(r["n"] for r in sm)
    aggregates={"static_A":sum(r["A"]*r["n"] for r in sm)/n_scored if n_scored else None,
        "U":{str(n):sum(r["U"] for r in um if r["N"]==n)/4 for n in (2,4,8)},
        "static_failures":sum(r["status"]!="ok" for r in judgments),
        "abstention_rate":sum(r["outcome"]=="abstain" for r in pairs)/22400}
    native=json.loads((root/"completion.json").read_text())
    if any(native.get(k)!=value for k,value in aggregates.items()):
        raise ValueError("completion aggregate differs from reconstructed judgments")
    return sm,um,{"model":model,"static":800,"pools":800,"edges":22400,"selections":2400,
                  "derived_N2_N4_from_N8":True,"metric_reconstruction":"EXACT","no_inference_rerun":True,
                  "verified_aggregates":aggregates}

def historical_audit_time(recorded_seconds,judgments):
    recorded=float(recorded_seconds or 0)
    latency=sum(row.get("latency_ms",0) or 0 for row in judgments)/1000
    return max(recorded,latency),recorded<=0 or recorded<latency

def collect():
    contract,static,pools=p.preflight()
    if contract!=json.loads((p.PHASE/"gpu_4model_v1/run_contract.json").read_text()):
        raise ValueError("original frozen execution contract changed")
    physical=json.loads((p.PHASE/"phase2_v2_physical_sha_manifests.json").read_text())
    ids={k:{r["physical_image_id"] for r in v} for k,v in physical.items()}
    overlaps={a+"__"+b:len(ids[a]&ids[b]) for a,b in [("audit","static"),("audit","downstream_v2"),("static","downstream_v2")]}
    if any(overlaps.values()) or p.sha(AUDIT)!=AUDIT_SHA:raise ValueError("frozen physical-disjoint gate failed")
    added={r["model"]:r for r in candidates()}
    records=[];factor_rows=[];audits=[];runtime=[];integrity=[];registry=[]
    expected=load_expected(str(AUDIT))
    for model in list(ORIGINAL)+list(added):
        is_new=model in added
        if is_new:
            outer=OUT/model
            full=valid_full(outer)
            if not full:raise ValueError("expanded model incomplete "+model)
            bound=json.loads((outer/"contract.json").read_text())
            for key in ("adapter_sha256","runner_sha256"):
                snapshot=OUT/"code_snapshots"/(bound[key]+".py")
                if not snapshot.is_file() or p.sha(snapshot)!=bound[key]:
                    raise ValueError("bound engineering source snapshot missing")
            root=Path(full["phase2_receipt"]).parent
            family=added[model]["family"]
            aq=json.loads((outer/"audit/metrics.json").read_text())
            judgments=p.read_rows(outer/"audit/static.jsonl")
            auditmetrics=compute_audit_metrics(judgments,expected)
            if auditmetrics!=aq["rows"]:raise ValueError("audit metrics cannot be reproduced")
            if len(judgments)!=2400 or len({r["item_id"] for r in judgments})!=2400:
                raise ValueError("audit counts invalid")
            acquisition_path=p.PHASE/"expanded_acquisition/receipts"/(model+".json")
            acquisition=json.loads(acquisition_path.read_text())
            if p.sha(acquisition_path)!=bound["acquisition_receipt_sha256"]:
                raise ValueError("acquisition provenance receipt changed")
            if acquisition.get("verified") is not True or any(acquisition[k]!=expected_value for k,expected_value in {
                "model":model,"repo_id":added[model]["repo_id"],"revision":added[model]["revision"],
                "selection_sha256":p.sha(p.PHASE/"EXPANDED_MODEL_SELECTION.json")}.items()):
                raise ValueError("acquisition provenance identity differs")
            revision=added[model]["revision"]
            attempt_events=p.read_rows(outer/"controller_attempts.jsonl")
            starts={r["attempt"] for r in attempt_events if r["event"]=="start"}
            ends={r["attempt"]:r for r in attempt_events if r["event"]=="end"}
            audit_known_seconds=sum(r.get("latency_ms",0) or 0 for r in judgments)/1000
            model_runtime=full["wall_seconds"]
            runtime_incomplete=bool(starts-set(ends))
            if ends:
                model_runtime=max(model_runtime,sum(r["runtime_seconds"] for r in ends.values()))
            legacy_failures=list(outer.glob("worker_failure.json*"))
            if legacy_failures:
                runtime_incomplete=True
            worker=full["worker_hostname"]
            finished=full["completion_timestamp"]
            auditpath=outer/"audit/static.jsonl"
        else:
            root=p.PHASE/("gpu_parallel_017" if model==ORIGINAL[3] else "gpu_4model_v1")/model
            family=get_model(model)["family"]
            ar=json.loads((p.SHARED/"results/receipts"/(model+"_full_audit.json")).read_text())
            auditpath=p.SHARED/"results"/model/Path(ar["output"]).name
            if p.sha(auditpath)!=ar["output_sha256"] or ar["manifest_sha256"]!=AUDIT_SHA or ar["row_count"]!=2400:
                raise ValueError("historical audit receipt invalid")
            judgments=p.read_rows(auditpath)
            auditmetrics=compute_audit_metrics(judgments,expected)
            historic=json.loads((p.SHARED/"results/metrics"/model/"contract_metrics.json").read_text())["rows"]
            for row in auditmetrics:
                prior=next(r for r in historic if r["factor"]==row["factor"])
                if any(abs(row[k]-prior[k])>1e-12 for k in ("PFC","PSC")):
                    raise ValueError("historical audit metrics differ from frozen code")
            provenance=json.loads((OUT/"original_checkpoint_provenance"/(model+".json")).read_text())
            if not provenance["weights_verified"]:raise ValueError("original weights unverified")
            revision=provenance["revision"]
            aruntime,runtime_incomplete=historical_audit_time(ar.get("runtime_seconds"),judgments)
            native=verified_receipt(root)
            model_runtime=native["runtime_seconds"]+aruntime
            worker=json.loads((root.parent/"run_contract.json").read_text())["host"]
            finished=native["finished_unix"]
        audit_expected={r["item_id"]:r for r in p.read_rows(AUDIT)}
        if len(judgments)!=2400 or {r["item_id"] for r in judgments}!=set(audit_expected):
            raise ValueError("audit IDs/counts invalid")
        if any(r["model_id"]!=model or r["status"] not in ("ok","parse_error") or
               any(r.get(k)!=audit_expected[r["item_id"]].get(k) for k in ("factor","triplet_id","variant","candidate_a","candidate_b")) for r in judgments):
            raise ValueError("audit provenance/status invalid")
        native=verified_receipt(root)
        if is_new:
            model_runtime=max(model_runtime,native["runtime_seconds"]+audit_known_seconds)
        sm,um,checks=verify_graphs(root,model,static,pools)
        integrity.append({**checks,"audit":2400,"audit_sha256":p.sha(auditpath),
                          "receipt_sha256":p.sha(root/"completion.json"),"source_dir":str(root)})
        audits.extend(auditmetrics)
        decoder=added[model]["decoder_family"] if is_new and "decoder_family" in added[model] else (
            "qwen" if model in (ORIGINAL[0],ORIGINAL[3]) else "gemma" if model==ORIGINAL[1] else "olmo")
        if is_new:
            decoder={"idefics3_8b_llama3":"llama","phi35_vision_instruct":"phi",
                     "internvl3_8b_hf":"qwen","llava_onevision_qwen2_7b":"qwen"}[model]
        for factor in FACTORS:
            s=next((r for r in sm if r["factor"]==factor),{"A":None,"n":0})
            a=next((r for r in auditmetrics if r["factor"]==factor),{"PFC":None,"PSC":None,"n":0})
            u={r["N"]:r["U"] for r in um if r["factor"]==factor}
            factor_rows.append({"model_id":model,"family":family,"decoder_family":decoder,"factor":factor,
                "dataset":"tallyqa" if factor=="count" else "gqa","A":s["A"],"PFC":a["PFC"],"PSC":a["PSC"],
                "U":u[8],"U2":u[2],"U4":u[4],"U8":u[8],"n_static_scored":s["n"],"n_audit_triplets_scored":a["n"],
                "n_static_completed":sum(row["factor"]==factor for row in static),"n_downstream":200})
        def mean_audit(key):
            count=sum(r["n"] for r in auditmetrics)
            return sum(r[key]*r["n"] for r in auditmetrics)/count if count else None
        record={"model_id":model,"family":family,"decoder_family":decoder,"revision":revision,
                "A":native["static_A"],"PFC":mean_audit("PFC"),"PSC":mean_audit("PSC"),
                "U2":native["U"]["2"],"U4":native["U"]["4"],"U8":native["U"]["8"],
                "abstention_rate":native["abstention_rate"],"static_failures":native["static_failures"],
                "runtime_seconds":model_runtime,"runtime_is_lower_bound":runtime_incomplete,"worker":worker,"source_output":str(root)}
        records.append(record)
        runtime.append({"model":model,"worker":worker,"audit_worker":worker if is_new else ar["hostname"],"wall_seconds_including_audit":model_runtime,
            "gpu_allocated_hours":model_runtime/3600,"phase2_seconds":native["runtime_seconds"],
            "phase2_edges_per_second":22400/native["runtime_seconds"],"finished_unix":finished,
            "abstention_rate":native["abstention_rate"],"runtime_is_lower_bound":runtime_incomplete,"measurement":"allocated-job wall time, not integrated utilization; missing legacy/interrupted attempt durations flagged"})
        registry.append({"model":model,"family":family,"decoder_family":decoder,"revision":revision,
                         "source_output":str(root),"reused_existing_result":not is_new,
                         "provenance":str(p.PHASE/"expanded_acquisition/receipts"/(model+".json")) if is_new else str(OUT/"original_checkpoint_provenance"/(model+".json"))})
    validate_rows(factor_rows)
    return records,factor_rows,registry,runtime,{"pass":True,"models":integrity,"physical_overlap_counts":overlaps,
        "static_sha256":p.sha(p.STATIC),"downstream_sha256":contract["downstream_sha256"],
        "audit_sha256":p.sha(AUDIT),"raw_image_hashes_reused_from_final_gate":True,"scientific_code_unchanged":True}

def analyses(table):
    rq2={str(n):{f:analyze_factor([{**r,"U":r["U"+str(n)]} for r in table if r["factor"]==f]) for f in FACTORS} for n in (8,2,4)}
    rq3=matrix_analysis(table)
    backbone=[{**r,"family":r["decoder_family"]} for r in table]
    sensitivity={"decoder_family_LOFO":{f:analyze_factor([r for r in backbone if r["factor"]==f]) for f in FACTORS},
                 "primary_family_LOFO":rq2["8"],"decoder_family_RQ3":matrix_analysis(backbone)}
    matched={}
    for factor in FACTORS:
        rows=[r for r in table if r["factor"]==factor]
        if any(r.get(k) is None for r in rows for k in ("A","PFC","PSC")):
            matched[factor]={"status":"NOT_ESTIMABLE","n_models":len(rows),"bands":None,
                             "reason":"missing metric; every model retained in the full table"}
        else:
            matched.update(accuracy_matched_pairs(rows))
    comparisons=[]
    for factor in FACTORS:
        rows=[r for r in table if r["factor"]==factor]
        for i,a in enumerate(rows):
            for b in rows[i+1:]:
                delta=abs(a["A"]-b["A"])*100 if a["A"] is not None and b["A"] is not None else None
                for threshold in (1,2,3):
                    if delta is not None and delta<=threshold:
                        comparisons.append({"factor":factor,"threshold_pp":threshold,"model_a":a["model_id"],"model_b":b["model_id"],
                            "delta_A_pp":delta,"delta_PFC":None if a["PFC"] is None or b["PFC"] is None else a["PFC"]-b["PFC"],"delta_PSC":None if a["PSC"] is None or b["PSC"] is None else a["PSC"]-b["PSC"],
                            "delta_U8":a["U8"]-b["U8"]})
    return rq2,rq3,sensitivity,{"bands":matched,"pairs":comparisons,"thresholds_pp":[1,2,3]}

def report():
    models,table,registry,runtime,integrity=collect()
    if len(models)!=8 or len({r["decoder_family"] for r in models})<4:
        raise ValueError("target eight models and distinct family gate not met")
    rq2,rq3,robustness,matched=analyses(table)
    plan=json.loads((OUT/"confirmatory_analysis_plan.json").read_text())
    for relative,digest in plan["code_hashes"].items():
        if p.sha(ROOT/relative)!=digest:raise ValueError("analysis contract changed")
    selection=json.loads((p.PHASE/"EXPANDED_MODEL_SELECTION.json").read_text())
    expanded_selection={"frozen_selection":selection,"selection_sha256":p.sha(p.PHASE/"EXPANDED_MODEL_SELECTION.json"),
        "compatibility_results":{r["model"]:json.loads((OUT/r["model"]/"compatibility_gate.json").read_text()) for r in candidates()},
        "excluded_models":[],"fallbacks_not_attempted":[r["model"] for r in selection["candidates"][4:]]}
    timings={"models":runtime,"total_gpu_allocated_hours":sum(r["gpu_allocated_hours"] for r in runtime),
             "wall_duration_phase2_seconds":max(r["finished_unix"] for r in runtime)-min(r["finished_unix"]-r["phase2_seconds"] for r in runtime),
             "estimated_RMB":None,"price_metadata_available":False,
             "total_is_lower_bound":any(r["runtime_is_lower_bound"] for r in runtime),
             "note":"Do not equate allocated job hours with continuously busy GPU hours. Prior attempts without complete timing are explicit unknown components, not zero."}
    rq2out={"evidence":"expanded frozen confirmatory set","plan":plan,"primary_N":8,"by_N":rq2,
            "in_sample_R2":"diagnostic only","p_values":None}
    rq3out={"evidence":"expanded frozen confirmatory set","plan_sha256":p.sha(OUT/"confirmatory_analysis_plan.json"),**rq3}
    for name,data in [("expanded_model_selection.json",expanded_selection),("model_registry_final.json",registry),
        ("all_model_metrics.json",models),("factor_metrics.json",table),("rq2_confirmatory.json",rq2out),
        ("rq3_confirmatory.json",rq3out),("accuracy_matched.json",matched),("family_robustness.json",robustness),
        ("runtime_cost.json",timings),("integrity_audit.json",integrity)]:
        p.write_json(FINAL/name,data,immutable=True)
    text_once(FINAL/"all_model_metrics.csv",csv_text(models))
    text_once(FINAL/"factor_metrics.csv",csv_text(table))
    text_once(FINAL/"accuracy_matched.csv",csv_text(matched["pairs"]))
    matrix=[{k:c[k] for k in ("audit_factor","downstream_factor","score","status")} for c in rq3["matrix"]]
    text_once(FINAL/"rq3_matrix.csv",csv_text(matrix))
    folds=[{"factor":f,"N":int(n),**fold} for n,byfactor in rq2.items() for f,fit in byfactor.items() for fold in fit["folds"]]
    text_once(FINAL/"family_robustness.csv",csv_text(folds))
    from scripts.expanded_figures import figures
    figures(FINAL,table,models,rq2,rq3,matched)
    original_table=[r for r in table if r["model_id"] in ORIGINAL]
    pre2,pre3,_,prematch=analyses(original_table)
    p.write_json(FINAL/"preliminary_four_model.json",{"evidence":"preliminary_only","rq2":pre2,"rq3":pre3,"accuracy_matched":prematch},immutable=True)
    lines=["# RewardLens: expanded frozen experiment","",
        "Eight models completed. The original four-model analysis remains preliminary; the expanded frozen set is analyzed with the predeclared confirmatory procedure.",
        "","## Main results","",
        "| Model | Family | A | PFC | PSC | U2 | U4 | U8 | Abstention |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    fmt=lambda value:"N/A" if value is None else "%.4f"%value
    for row in models:
        lines.append("| "+row["model_id"]+" | "+row["family"]+" | "+" | ".join(fmt(row[k]) for k in ("A","PFC","PSC","U2","U4","U8","abstention_rate"))+" |")
    lines+=["","## RQ2: held-out incremental prediction","",
        "Positive delta MAE favors adding PFC/PSC to independent Static A. Factors are fit separately. Bootstrap intervals resample held-out family loss contributions conditional on fitted LOFO models; these are not refit-bootstrap intervals."]
    for factor,fit in rq2["8"].items():
        ci=fit["bootstrap"]["ci95"] if fit["bootstrap"] else None
        lines.append("- "+factor+": delta MAE="+fmt(fit["delta_mae"])+", conditional family-bootstrap 95% interval="+str(ci)+", status="+fit["status"]+".")
    diag=rq3["primary_4factor"]["column_standardized"]["diagonal_minus_off"] if rq3["primary_4factor"] else None
    lines+=["","## RQ3: factor-specific contribution","",
        "Within-column standardized diagonal minus off-diagonal contribution: "+fmt(diag)+". The full 4x4 matrix, every fold, and GQA-only 3x3 sensitivity are retained.",
        "","## Interpretation and limitations","",
        "These cross-model predictive relationships do not establish that changing dependency causes downstream utility to improve. No model was included/excluded using RewardLens outcomes. Null, negative, mixed and non-identifiable results are retained.",
        "","The sample remains small. Model-system families and shared decoder backbones are both reported; shared-Qwen systems are clustered together in an additional robustness analysis. Count uses TallyQA while other factors use GQA; standardization does not remove this source confound.",
        "","Static A and audit metrics retain the frozen valid-response/complete-triplet denominators. Failures and scored denominators are reported alongside completed counts. No pools were dropped and N2/N4 were reconstructed from the same N8 graph.",
        "","No p-values or multiplicity-adjusted discovery claims are asserted. Confidence intervals are descriptive and marginal. In-sample fit is diagnostic only.",
        "","Reproducibility verification reconstructed metrics and selections from durable judgments exactly, without re-querying any model."]
    text_once(FINAL/"scientific_results.md","\n".join(lines)+"\n")
    text_once(FINAL/"engineering_status.md","# Engineering status\n\nEight model executions and frozen-graph reconstruction passed. Existing four results reused by hashed provenance. Separate output roots and model locks prevented simultaneous writers. Model checkpoints only were acquired; no datasets or raw-image rehash were performed. Phi used an isolated Transformers 4.43 environment and documented eager-attention API plumbing. See receipts, code snapshots, processor checks, and all failure logs.\n")
    hashes={str(f.relative_to(FINAL)):p.sha(f) for f in sorted(FINAL.rglob("*")) if f.is_file() and f.name!="artifact_hashes.json"}
    p.write_json(FINAL/"artifact_hashes.json",hashes,immutable=True)
    marker={"REWARDLENS_FULL_EXPERIMENT_COMPLETE":True,"TOTAL_MODELS":8,
        "DISTINCT_FAMILIES":len({r["decoder_family"] for r in models}),
        "MODEL_SYSTEM_FAMILIES":len({r["family"] for r in models}),
        "STATIC_COMPLETE":True,"DOWNSTREAM_COMPLETE":True,"RQ2_CONFIRMATORY_COMPLETE":True,
        "RQ3_CONFIRMATORY_COMPLETE":True,"ROBUSTNESS_COMPLETE":True,"INTEGRITY_PASS":True,
        "final_directory":str(FINAL),"artifact_hashes_sha256":p.sha(FINAL/"artifact_hashes.json"),
        "integrity_audit_sha256":p.sha(FINAL/"integrity_audit.json"),
        "selection_sha256":p.sha(p.PHASE/"EXPANDED_MODEL_SELECTION.json"),
        "analysis_plan_sha256":p.sha(OUT/"confirmatory_analysis_plan.json")}
    p.write_json(p.PHASE/"REWARDLENS_FULL_EXPERIMENT_COMPLETE.json",marker,immutable=True)
    return marker

def ready():
    for model in ORIGINAL:
        root=p.PHASE/("gpu_parallel_017" if model==ORIGINAL[3] else "gpu_4model_v1")/model
        if not (root/"completion.json").exists():return False
    paths=[OUT/r["model"]/"completion.json" for r in candidates()]
    # Allow successful children to flush final attempt timing before reporting.
    return all(path.exists() and time.time()-path.stat().st_mtime>=60 for path in paths)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watch",action="store_true")
    args=parser.parse_args()
    if args.watch:
        while not ready():time.sleep(30)
    print(json.dumps(report(),indent=2))

if __name__=="__main__":
    main()
