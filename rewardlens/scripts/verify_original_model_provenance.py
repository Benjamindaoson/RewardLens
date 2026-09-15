#!/usr/bin/env python3
"""Read-only checkpoint verification; metadata requests only, no weight downloads."""
import json
import hashlib
from pathlib import Path
import requests
from scripts.phase2_autonomous import PHASE,SHARED,MODELS,CHECKPOINTS,sha,write_json

def main():
    out=PHASE/"distributed_v1/original_checkpoint_provenance"
    out.mkdir(parents=True,exist_ok=True)
    for model,repo in zip(MODELS,CHECKPOINTS):
        receipt_path=out/(model+".json")
        if receipt_path.exists():
            print(model,"EXISTING_RECEIPT",flush=True)
            continue
        metadata_path=out/(model+".upstream.json")
        if metadata_path.exists():
            meta=json.loads(metadata_path.read_text())
        else:
            response=requests.get("https://hf-mirror.com/api/models/"+repo,params={"blobs":"true"},timeout=(10,40))
            response.raise_for_status();meta=response.json()
            write_json(metadata_path,meta,immutable=True)
        checkpoint=SHARED/"models"/repo
        files=[];missing=[];differences=[]
        rows={r["rfilename"]:r for r in meta["siblings"]}
        for name,row in rows.items():
            if "/" in name or not name.endswith((".safetensors",".json",".py",".model",".txt")):
                continue
            path=checkpoint/name
            if not path.exists():
                missing.append(name);continue
            digest=sha(path)
            if row.get("lfs"):
                match=path.stat().st_size==row["size"] and digest==row["lfs"]["sha256"]
            else:
                h=hashlib.sha1(("blob "+str(path.stat().st_size)+"\0").encode()+path.read_bytes()).hexdigest()
                match=h==row["blobId"] and path.stat().st_size==row["size"]
            rec={"file":name,"bytes":path.stat().st_size,"sha256":digest,"upstream_match":match,
                 "upstream_lfs":row.get("lfs"),"upstream_git_blob":row["blobId"]}
            files.append(rec)
            if not match:differences.append(name)
            print(model,name,"MATCH" if match else "LOCAL_DIFFERENCE",flush=True)
        required=set(json.loads((checkpoint/"model.safetensors.index.json").read_text())["weight_map"].values())
        if model=="skywork_vl_reward_7b":required.add("value_head.safetensors")
        matching={r["file"] for r in files if r["upstream_match"]}
        weights_verified=required<=matching
        write_json(receipt_path,{"model":model,"repo_id":repo,"revision":meta["sha"],
            "metadata_source":"hf-mirror metadata; exact upstream git and LFS object identities",
            "metadata_sha256":sha(metadata_path),"weights_verified":weights_verified,
            "all_upstream_runtime_files_match":not differences and not missing,
            "missing_upstream_runtime_files":missing,"local_differences":differences,"files":files,
            "checkpoint_mutated":False,"weights_downloaded":False,
            "note":"Existing compatibility patches are recorded as local differences, not silently attributed to upstream."},immutable=True)
        if not weights_verified:
            raise ValueError("existing checkpoint does not match frozen upstream weight identities: "+model)

if __name__=="__main__":
    main()
