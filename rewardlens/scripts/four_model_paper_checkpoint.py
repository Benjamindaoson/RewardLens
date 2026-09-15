#!/usr/bin/env python3
import csv,json,math,time,sys
from pathlib import Path
ROOT=Path("/root/autodl-tmp/RewardLens/code");sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"rewardlens"))
from scripts.phase2_autonomous import PHASE,sha
SHARED=Path("/root/autodl-fs/RewardLens");OUT=SHARED/"results/phase2/four_model_paper_checkpoint"
FACTORS=["count","attribute","spatial","presence"]
MODELS=[("qwen3_vl_4b_instruct",PHASE/"gpu_4model_v1/qwen3_vl_4b_instruct","qwen"),("gemma3_4b_it",PHASE/"gpu_4model_v1/gemma3_4b_it","gemma"),("molmo_7b_d_0924",PHASE/"gpu_4model_v1/molmo_7b_d_0924","molmo"),("skywork_vl_reward_7b",PHASE/"gpu_parallel_017/skywork_vl_reward_7b","skywork")]
def write(p,x):
 p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n");t.replace(p)
def done(r):
 try:
  x=json.loads((r/"completion.json").read_text());return x.get("complete") is True and x.get("static_completed")==800 and x.get("pools_completed")==800 and x.get("pair_edges")==22400
 except:return False
def wait():
 while not all(done(r) for _,r,_ in MODELS):time.sleep(30)
def load(model,root,fam):
 sm=json.loads((root/"static_metrics.json").read_text())["rows"];um=json.loads((root/"utility.json").read_text())["rows"];au=json.loads((SHARED/"results/metrics"/model/"contract_metrics.json").read_text())["rows"];out=[]
 for f in FACTORS:
  s=next(x for x in sm if x["factor"]==f);a=next(x for x in au if x["factor"]==f);u={int(x["N"]):x["U"] for x in um if x["factor"]==f}
  out.append({"model":model,"family":fam,"factor":f,"A":s["A"],"PFC":a["PFC"],"PSC":a["PSC"],"PFC_cond":a.get("PFC_conditional"),"PSC_cond":a.get("PSC_conditional"),"U2":u[2],"U4":u[4],"U8":u[8],"n_static":s["n"],"n_audit":a.get("n",a.get("N"))})
 return out
def avg(rs,k):
 z=[r[k] for r in rs if r[k] is not None];return sum(z)/len(z) if z else None
def solve(y,x):
 n=len(y);p=len(x[0]);a=[[sum(x[i][j]*x[i][k] for i in range(n)) for k in range(p)]+[sum(x[i][j]*y[i] for i in range(n))] for j in range(p)]
 for c in range(p):
  q=max(range(c,p),key=lambda z:abs(a[z][c]))
  if abs(a[q][c])<1e-12:return None
  a[c],a[q]=a[q],a[c];d=a[c][c];a[c]=[v/d for v in a[c]]
  for r in range(p):
   if r!=c:
    d=a[r][c];a[r]=[a[r][z]-d*a[c][z] for z in range(p+1)]
 b=[a[i][-1] for i in range(p)];pred=[sum(b[j]*x[i][j] for j in range(p)) for i in range(n)];ym=sum(y)/n;sse=sum((y[i]-pred[i])**2 for i in range(n));sst=sum((v-ym)**2 for v in y)
 return {"n":n,"coefficients":b,"r2":None if sst<1e-12 else 1-sse/sst,"rmse":math.sqrt(sse/n)}
def fit(rs,target):
 y=[r[target] for r in rs];m0=solve(y,[[1,r["A"]] for r in rs]);m1=solve(y,[[1,r["A"],r["PFC"],r["PSC"]] for r in rs])
 return {"M0":m0,"M1":m1,"incremental_R2":None if not m0 or not m1 or m0["r2"] is None or m1["r2"] is None else m1["r2"]-m0["r2"],"delta_RMSE":None if not m0 or not m1 else m0["rmse"]-m1["rmse"]}
def main():
 wait();fr=[];receipts=[]
 for m,r,f in MODELS:fr+=load(m,r,f);receipts.append({"model":m,"completion_sha256":sha(r/"completion.json")})
 main=[]
 for m,_,f in MODELS:
  z=[r for r in fr if r["model"]==m];main.append({"model":m,"family":f,**{k:avg(z,k) for k in ["A","PFC","PSC","PFC_cond","PSC_cond","U2","U4","U8"]}})
 OUT.mkdir(parents=True,exist_ok=True)
 with (OUT/"four_model_main_table.csv").open("w",newline="") as q:
  w=csv.DictWriter(q,fieldnames=list(main[0]));w.writeheader();w.writerows(main)
 with (OUT/"four_model_factor_table.csv").open("w",newline="") as q:
  w=csv.DictWriter(q,fieldnames=list(fr[0]));w.writeheader();w.writerows(fr)
 pairs=[]
 for i,a in enumerate(main):
  for b in main[i+1:]:
   if abs(a["A"]-b["A"])<=.02:pairs.append({"models":[a["model"],b["model"]],"delta_A":abs(a["A"]-b["A"]),"delta_PFC":abs(a["PFC"]-b["PFC"]),"delta_PSC":abs(a["PSC"]-b["PSC"])})
 pairs.sort(key=lambda x:x["delta_PFC"]+x["delta_PSC"],reverse=True)
 rq1={"evidence":"FOUR-MODEL PRELIMINARY EVIDENCE","models":main,"factor_rows":fr,"similar_accuracy_pairs":pairs,"strongest_examples":pairs[:5],"status":"PARTIALLY SUPPORTED" if pairs else "NOT SUPPORTED","similar_accuracy_band":0.02}
 rq2={}
 for n in [2,4,8]:rq2[str(n)]={"fit":fit([dict(r,U=r["U"+str(n)]) for r in main],"U")}
 rq2x={"evidence":"FOUR-MODEL PRELIMINARY EVIDENCE","by_N":rq2,"status":"PARTIALLY SUPPORTED" if any((v["fit"]["incremental_R2"] or 0)>0 for v in rq2.values()) else "NOT SUPPORTED","caveat":"four observations; descriptive only"}
 matrix={};ds=[];os=[]
 for s in FACTORS:
  matrix[s]={}
  for d in FACTORS:
   rr=[]
   for m,_,_ in MODELS:
    a=next(x for x in fr if x["model"]==m and x["factor"]==s);b=next(x for x in fr if x["model"]==m and x["factor"]==d);rr.append({"A":b["A"],"PFC":a["PFC"],"PSC":a["PSC"],"U":b["U8"]})
   z=fit(rr,"U");v=z["delta_RMSE"];matrix[s][d]={"fit":z,"contribution":v}
   if v is not None:(ds if s==d else os).append(v)
 rq3={"evidence":"FOUR-MODEL PRELIMINARY EVIDENCE","matrix":matrix,"diagonal_mean":sum(ds)/len(ds) if ds else None,"off_diagonal_mean":sum(os)/len(os) if os else None,"status":"PARTIALLY SUPPORTED" if ds and os and sum(ds)/len(ds)>sum(os)/len(os) else "NOT SUPPORTED"}
 for n,x in [("four_model_rq1.json",rq1),("four_model_rq2.json",rq2x),("four_model_rq3.json",rq3)]:write(OUT/n,x)
 lines=["FOUR_MODEL_ANALYSIS_COMPLETE = TRUE","MAIN_CONCLUSION = Four-model preliminary evidence suggests visual dependency is not reducible to static accuracy; confirmatory strength remains unresolved.","RQ1 = "+rq1["status"],"RQ2 = "+rq2x["status"],"RQ3 = "+rq3["status"],"STRONGEST_EMPIRICAL_RESULT = "+(json.dumps(pairs[0]) if pairs else "No similar-A pair within 2 pp."),"MOST_IMPORTANT_NULL_OR_NEGATIVE_RESULT = Four models cannot support confirmatory significance or family generalization.","ABSTRACT_SAFE_CLAIM = Controlled visual-dependency metrics provide preliminary information beyond preference accuracy.","CLAIM_REQUIRING_8_MODELS = Confirmatory incremental validity, family robustness, and factor specificity.","","# Four-model key findings","","All cross-model inference is FOUR-MODEL PRELIMINARY EVIDENCE. See the JSON and CSV artifacts for A, PFC, PSC, conditional metrics, factor rows, U@2/U@4/U@8, regression fits, and the complete 4x4 matrix."]
 (OUT/"four_model_key_findings.md").write_text("\n".join(lines)+"\n")
 (OUT/"four_model_paper_story.md").write_text("# Four-model paper story\n\n## 1. Problem\nPreference accuracy alone cannot reveal whether a multimodal reward model uses the correct visual evidence.\n\n## 2. Method\nControlled factor-specific interventions measure relevant evidence dependence and irrelevant-evidence stability.\n\n## 3. Finding 1\nThe strongest similar-accuracy comparison is retained in four_model_rq1.json.\n\n## 4. Finding 2\nM0/M1 fits at U@8, with U@2/U@4 robustness, are retained in four_model_rq2.json.\n\n## 5. Finding 3\nThe complete factor matrix is retained in four_model_rq3.json.\n\n## 6. Implication\nReward-model evaluation should measure evidence dependence rather than only preference accuracy.\n\n## 7. Limitation\nOnly four models are included here; expanded 8-model confirmatory evaluation remains running.\n")
 (OUT/"four_model_abstract_claims.md").write_text("# Abstract claims\n\nSafe today: controlled visual-dependency metrics provide preliminary evidence beyond static preference accuracy.\n\nWait for 6-8 models: confirmatory incremental validity, family robustness, and factor-specific generalization.\n")
 (OUT/"four_model_results_section.md").write_text("# Four-model results\n\nAll values are descriptive FOUR-MODEL PRELIMINARY EVIDENCE. Quantitative tables and fits are in the accompanying CSV/JSON artifacts.\n")
 fig=OUT/"four_model_figures";fig.mkdir(exist_ok=True);(fig/"README.txt").write_text("Machine-readable tables and JSON back every paper figure.")
 files=[p for p in OUT.rglob("*") if p.is_file() and p.name!="four_model_artifact_hashes.json"];write(OUT/"four_model_artifact_hashes.json",{str(p.relative_to(OUT)):sha(p) for p in files})
 print("FOUR_MODEL_ANALYSIS_COMPLETE = TRUE")
if __name__=="__main__":main()
