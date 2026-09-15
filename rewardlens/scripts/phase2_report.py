#!/usr/bin/env python3
"""Preliminary-only Phase II reporting using the existing estimators and metric contracts."""
from __future__ import annotations
import csv
import html
import io
import json
import math
import os
from pathlib import Path

from inference.phase2_analysis import merge_primary_table
from stats import _fit_ols, factor_specificity, FACTORS
from models.registry import get_model


def preliminary_models(rows):
    """Same unregularized OLS/LOFO contract; expose underidentification explicitly."""
    folds=[]
    for held in sorted({r["family"] for r in rows}):
        train=[r for r in rows if r["family"]!=held]
        test=[r for r in rows if r["family"]==held]
        fold={"held_out_family":held,"n_train":len(train),"n_test":len(test),"M0":None,"M1":None}
        for name,cols in (("M0",["A"]),("M1",["A","PFC","PSC"])):
            if len(train)<len(cols)+1:
                fold[name+"_reason"]="fewer training observations than intercept plus predictors"
                continue
            try:
                fit=_fit_ols([r["U"] for r in train],[[r[c] for r in train] for c in cols])
                predictions=[fit["beta"][0]+sum(fit["beta"][i+1]*r[c] for i,c in enumerate(cols)) for r in test]
                errors=[a-r["U"] for a,r in zip(predictions,test)]
                fold[name]={"mae":sum(abs(x) for x in errors)/len(errors),
                            "rmse":math.sqrt(sum(x*x for x in errors)/len(errors))}
            except (ValueError,ZeroDivisionError) as e:
                fold[name+"_reason"]=str(e)
        fold["delta_mae"]=None if fold["M0"] is None or fold["M1"] is None else fold["M0"]["mae"]-fold["M1"]["mae"]
        folds.append(fold)
    valid=[r["delta_mae"] for r in folds if r["delta_mae"] is not None]
    complete=bool(folds) and len(valid)==len(folds)
    return {"status":"ESTIMABLE_PRELIMINARY" if complete else "NOT_IDENTIFIABLE",
            "folds":folds,"delta_mae":sum(valid)/len(valid) if complete else None,
            "n_models":len(rows),"n_families":len(folds),"evidence":"preliminary",
            "p_value":None,"note":"Positive delta MAE favors added PFC/PSC; no substitution for singular or underdetermined M1."}


def text_once(path,text):
    from scripts.phase2_autonomous import sync_dir
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_text()!=text:
            raise ValueError("refusing to overwrite report: "+str(path))
        return
    with path.open("x",encoding="utf-8",newline="") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    sync_dir(path.parent)


def csv_text(rows,fields=None):
    buf=io.StringIO(newline="")
    fields=fields or list(rows[0]) if rows else fields or []
    writer=csv.DictWriter(buf,fieldnames=fields,extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k:json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in row.items()})
    return buf.getvalue()


def charts(table,matrix):
    # SVG is self-contained and avoids installing a plotting dependency on the offline host.
    start='<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="700" viewBox="0 0 1000 700"><rect width="1000" height="700" fill="white"/>'
    scatter=[start,'<text x="30" y="35" font-size="22">Independent static A vs downstream U@8 — preliminary</text>']
    colors=["#1f77b4","#d62728","#2ca02c","#9467bd"]
    ids=sorted({r["model_id"] for r in table})
    for idx,factor in enumerate(FACTORS):
        x=70+(idx%2)*480
        y=85+(idx//2)*285
        scatter.append(f'<text x="{x}" y="{y}" font-size="18">{factor}</text>')
        scatter.append(f'<path d="M{x} {y+15}V{y+225}H{x+330}" fill="none" stroke="#333"/>')
        scatter.append(f'<text x="{x+140}" y="{y+250}" font-size="14">Static A (0 to 1)</text><text x="{x-45}" y="{y+100}" font-size="14">U@8</text>')
        for row in table:
            if row["factor"]!=factor:
                continue
            color=colors[ids.index(row["model_id"])%4]
            scatter.append(f'<circle cx="{x+330*row["A"]}" cy="{y+225-210*row["U"]}" r="6" fill="{color}"><title>{html.escape(row["model_id"])}</title></circle>')
    for i,model in enumerate(ids):
        scatter.append(f'<text x="{30+i*240}" y="685" fill="{colors[i%4]}" font-size="12">{html.escape(model)}</text>')
    scatter.append("</svg>")
    grid=[start,'<text x="30" y="35" font-size="22">RQ3 predictive contribution — preliminary LOFO delta MAE</text>']
    grid.append('<text x="30" y="65" font-size="15">Rows: audit factor. Columns: downstream factor. N/A means not identifiable.</text>')
    for j,f in enumerate(FACTORS):
        grid.append(f'<text x="{210+j*180}" y="115" font-size="18">{f}</text>')
    for i,af in enumerate(FACTORS):
        grid.append(f'<text x="30" y="{185+i*110}" font-size="18">{af}</text>')
        for j,df in enumerate(FACTORS):
            row=next(r for r in matrix if r["audit_factor"]==af and r["downstream_factor"]==df)
            val=row["score"]
            x,y=190+j*180,140+i*110
            grid.append(f'<rect x="{x}" y="{y}" width="170" height="100" fill="#eeeeee" stroke="#aaaaaa"/>')
            label="N/A" if val is None else "%.4f"%val
            grid.append(f'<text x="{x+55}" y="{y+58}" font-size="22">{label}</text>')
    grid.append('<text x="30" y="625" font-size="15">Four families leave three training observations for four M1 parameters.</text>')
    grid.append('<text x="30" y="655" font-size="15">No p-values, regularization, pooled fit, or confirmatory claim substituted.</text></svg>')
    return "".join(scatter),"".join(grid)


def report(out):
    from scripts.phase2_autonomous import (MODELS,SHARED,ROOT,write_json,sha,validate_completion)
    out=Path(out)
    contract=json.loads((out/"run_contract.json").read_text())
    summaries=[]
    static=[]
    utility=[]
    audit=[]
    families={m:get_model(m)["family"] for m in MODELS}
    for model in MODELS:
        receipt=validate_completion(out/model,contract)
        aud=json.loads((SHARED/"results/metrics"/model/"contract_metrics.json").read_text())["rows"]
        overall=next(r for r in aud if r["factor"]=="overall")
        row={"Model":model,"Static A":None,"PFC":overall["PFC"],"PSC":overall["PSC"],
             "U@2":None,"U@4":None,"U@8":None,"Abstention":None,"Runtime":None,
             "Completed":False}
        if receipt:
            row.update({"Static A":receipt["static_A"],"U@2":receipt["U"]["2"],
                        "U@4":receipt["U"]["4"],"U@8":receipt["U"]["8"],
                        "Abstention":receipt["abstention_rate"],"Runtime":receipt["runtime_seconds"],
                        "Completed":True})
            static.extend(json.loads((out/model/"static_metrics.json").read_text())["rows"])
            utility.extend(json.loads((out/model/"utility.json").read_text())["rows"])
            audit.extend({"model_id":model,"factor":r["factor"],"PFC":r["PFC"],"PSC":r["PSC"]}
                         for r in aud if r["factor"] in FACTORS)
        summaries.append(row)
    table=merge_primary_table(audit_rows=audit,static_rows=static,utility_rows=utility,families=families) if static else []
    robust={(r["model_id"],r["factor"],r["N"]):r["U"] for r in utility}
    for row in table:
        row["U@2"]=robust[(row["model_id"],row["factor"],2)]
        row["U@4"]=robust[(row["model_id"],row["factor"],4)]
        row["evidence"]="preliminary"
    rq2={"evidence":"preliminary","confirmatory":False,
         "config":json.loads((ROOT/"rewardlens/configs/rq2_analysis.json").read_text()),
         "by_factor":{f:preliminary_models([r for r in table if r["factor"]==f]) for f in FACTORS}}
    matrix=[]
    keyed={(r["model_id"],r["factor"]):r for r in table}
    for af in FACTORS:
        for df in FACTORS:
            cross=[{**r,"PFC":keyed[(r["model_id"],af)]["PFC"],"PSC":keyed[(r["model_id"],af)]["PSC"]}
                   for r in table if r["factor"]==df and (r["model_id"],af) in keyed]
            result=preliminary_models(cross)
            matrix.append({"audit_factor":af,"downstream_factor":df,"score":result["delta_mae"],
                           "status":result["status"],"n_models":len(cross),"folds":result["folds"]})
    complete_matrix=all(r["score"] is not None for r in matrix)
    rq3={"evidence":"preliminary","confirmatory":False,
         "config":json.loads((ROOT/"rewardlens/configs/rq3_analysis.json").read_text()),
         "contribution_definition":"LOFO MAE(U_df~A_df) minus LOFO MAE(U_df~A_df+PFC_af+PSC_af)",
         "matrix":matrix,"column_standardized":None,
         "status":"ESTIMABLE_PRELIMINARY" if complete_matrix else "NOT_IDENTIFIABLE",
         "reason":"Four-model family folds cannot identify the four-parameter M1.",
         "gqa_only_3factor_sensitivity":None}
    if complete_matrix:
        result=factor_specificity(matrix)
        rq3["column_standardized"]=result["column_standardized"]
        rq3["column_standardized_matrix"]=result["column_standardized_matrix"]
    completed=all(r["Completed"] for r in summaries)
    final={"PHASE2_4MODEL_COMPLETE":completed,"models":summaries,
           "evidence":"preliminary","confirmatory":False,
           "confirmatory_target":{"minimum_models":6,"target_models":8,"minimum_families":4},
           "RQ2_status":"NOT_IDENTIFIABLE" if any(r["status"]=="NOT_IDENTIFIABLE" for r in rq2["by_factor"].values()) else "ESTIMABLE_PRELIMINARY",
           "RQ3_status":rq3["status"],"classification":"BORDERLINE",
           "classification_reason":"Insufficient model count and underidentified family-held-out M1; submission readiness is not established.",
           "contract_sha256":sha(out/"run_contract.json")}
    analysis=out/"analysis"
    for name,data in (("factorwise_table.json",table),("rq2_preliminary.json",rq2),
                      ("rq3_preliminary.json",rq3),("final_summary.json",final)):
        write_json(analysis/name,data,immutable=True)
    text_once(analysis/"factorwise_table.csv",csv_text(table))
    text_once(analysis/"models.csv",csv_text(summaries))
    text_once(analysis/"rq3_matrix.csv",csv_text(matrix,["audit_factor","downstream_factor","score","status","n_models"]))
    scatter,heatmap=charts(table,matrix)
    text_once(analysis/"static_vs_utility.svg",scatter)
    text_once(analysis/"rq3_contribution_matrix.svg",heatmap)
    def fmt(v):
        if v is None: return "N/A"
        if isinstance(v,float): return "%.6f"%v
        return str(v)
    keys=["Model","Static A","PFC","PSC","U@2","U@4","U@8","Abstention","Runtime"]
    md=["# RewardLens Phase II — preliminary four-model report","",
        "PHASE2_4MODEL_COMPLETE = "+str(completed).upper(),"",
        "| "+" | ".join(keys)+" |","| "+" | ".join(["---"]*len(keys))+" |"]
    md.extend("| "+" | ".join(fmt(r[k]) for k in keys)+" |" for r in summaries)
    md+=["","Runtime is seconds from completed/failed attempts. Static A retains the existing metric's valid-response denominator; see per-model static_metrics.json for failures and denominator.",
         "","RQ2: M0 is U_f ~ A_f; M1 is U_f ~ A_f + PFC_f + PSC_f. Family-held-out M1 is not identifiable with four models. Incremental predictive information is N/A, not zero.",
         "","RQ3: the 4x4 factor matrix uses the same held-out incremental MAE construction. Non-estimable cells remain N/A; diagonal/off-diagonal evidence is unavailable. No new estimator was substituted.",
         "","Classification: BORDERLINE — this is an evidence insufficiency assessment, not a statistical success or rejection.",
         "","These results are preliminary. Confirmatory target remains minimum 6 models, target 8, and at least 4 distinct model families.",
         "","Count uses TallyQA; other factors use GQA. Column standardization does not remove source confounding.",
         "","No p-values or significance claims are manufactured. Failed/incomplete models have no reported utility; saved judgments are retained."]
    text_once(analysis/"SUMMARY.md","\n".join(md)+"\n")
    write_json(out/"final_summary.json",final,immutable=True)
    print(json.dumps(final,indent=2),flush=True)
    return final
