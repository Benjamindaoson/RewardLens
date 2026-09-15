#!/usr/bin/env python3
"""Durable preliminary analysis for the original four models."""
import json,time,sys
from pathlib import Path
ROOT=Path("/root/autodl-tmp/RewardLens/code");sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"rewardlens"))
from scripts import expanded_analysis as ea
from scripts.phase2_autonomous import PHASE,write_json,sha
SHARED=Path("/root/autodl-fs/RewardLens");OUT=SHARED/"results/phase2/preliminary_four_model"
MODELS=[("qwen3_vl_4b_instruct",PHASE/"gpu_4model_v1/qwen3_vl_4b_instruct"),("gemma3_4b_it",PHASE/"gpu_4model_v1/gemma3_4b_it"),("molmo_7b_d_0924",PHASE/"gpu_4model_v1/molmo_7b_d_0924"),("skywork_vl_reward_7b",PHASE/"gpu_parallel_017/skywork_vl_reward_7b")]
FAMILIES={"qwen3_vl_4b_instruct":"qwen","gemma3_4b_it":"gemma","molmo_7b_d_0924":"molmo","skywork_vl_reward_7b":"skywork"}
def wait_complete():
 while True:
  if all((root/"completion.json").exists() and json.loads((root/"completion.json").read_text()).get("complete") is True for _,root in MODELS): return
  time.sleep(30)
def rows_for(model,root):
 sm=json.loads((root/"static_metrics.json").read_text())["rows"];um=json.loads((root/"utility.json").read_text())["rows"]
 aud=json.loads((SHARED/"results/metrics"/model/"contract_metrics.json").read_text())["rows"];out=[]
 for f in ea.FACTORS:
  s=next(x for x in sm if x["factor"]==f);a=next(x for x in aud if x["factor"]==f);u={int(x["N"]):x["U"] for x in um if x["factor"]==f}
  out.append({"model_id":model,"family":FAMILIES[model],"decoder_family":FAMILIES[model],"factor":f,"dataset":"tallyqa" if f=="count" else "gqa","A":s["A"],"PFC":a["PFC"],"PSC":a["PSC"],"U":u[8],"U2":u[2],"U4":u[4],"U8":u[8],"n_static_scored":s["n"],"n_audit_triplets_scored":a["n"],"n_static_completed":200,"n_downstream":200})
 return out
def main():
 wait_complete();table=[];receipts=[]
 for model,root in MODELS:
  table+=rows_for(model,root);receipts.append({"model":model,"completion_sha256":sha(root/"completion.json")})
 rq2,rq3,robust,matched=ea.analyses(table);OUT.mkdir(parents=True,exist_ok=True)
 data={"evidence":"preliminary_four_model_only","models":[m for m,_ in MODELS],"model_count":4,"rq2":rq2,"rq3":rq3,"robustness":robust,"accuracy_matched":matched,"table":table,"receipts":receipts,"analysis_code_sha256":sha(ROOT/"rewardlens/scripts/expanded_analysis.py"),"confirmatory":False}
 write_json(OUT/"preliminary_four_model_analysis.json",data,immutable=True)
 lines=["# RewardLens preliminary four-model analysis","","Preliminary evidence only; not the confirmatory expanded analysis.","","| Model | Factor | A | PFC | PSC | U@2 | U@4 | U@8 |","|---|---|---:|---:|---:|---:|---:|---:|"]
 for r in table: lines.append("| %s | %s | %.4f | %.4f | %.4f | %.4f | %.4f | %.4f |"%(r["model_id"],r["factor"],r["A"],r["PFC"],r["PSC"],r["U2"],r["U4"],r["U8"]))
 lines+=["","## RQ2 preliminary","", "M0: U ~ A; M1: U ~ A + PFC + PSC. Descriptive only; no confirmatory significance claim."]
 for f,fit in rq2["8"].items():lines.append("- %s: status=%s, delta_MAE=%s, bootstrap_CI95=%s"%(f,fit.get("status"),fit.get("delta_mae"),fit.get("bootstrap",{}).get("ci95") if fit.get("bootstrap") else None))
 lines+=["","## RQ3 preliminary","", "The full matrix and diagonal/off-diagonal comparison are retained in JSON.", "- status=%s"%rq3.get("status")]
 (OUT/"preliminary_four_model.md").write_text("\n".join(lines)+"\n")
 print(json.dumps({"status":"PRELIMINARY_FOUR_MODEL_READY","output":str(OUT/"preliminary_four_model_analysis.json")}))
if __name__=="__main__":main()
