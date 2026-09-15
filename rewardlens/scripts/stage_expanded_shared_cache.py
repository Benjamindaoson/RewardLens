#!/usr/bin/env python3
"""Copy verified local checkpoints once for cross-worker dispatch; no network downloads."""
import json
import os
from pathlib import Path
import shutil
import socket
from scripts.phase2_autonomous import PHASE,SHARED,sha,write_json
from scripts.expanded_model_acquire import HOSTS
from scripts.expanded_worker import candidates

def main():
    if socket.gethostname()!=HOSTS["011"]:raise ValueError("source worker must be 011")
    for candidate in candidates():
        if candidate["assigned_worker"]!="011":continue
        model=candidate["model"]
        state=json.loads((PHASE/"expanded_acquisition/status"/(model+".json")).read_text())
        if not state["checkpoint_verified"] or not state["processor_verified"]:raise ValueError("checkpoint not ready")
        source=Path(state["local_checkpoint"])
        original=json.loads((source/"acquisition_receipt.json").read_text())
        target=SHARED/"expanded_execution_cache"/model/candidate["revision"]
        target.mkdir(parents=True,exist_ok=True)
        receipt=PHASE/"distributed_v1/checkpoint_transfers"/(model+".json")
        if receipt.exists():
            print(model,"ALREADY_STAGED",flush=True);continue
        remaining=sum(r["bytes"] for r in original["files"] if not (target/r["file"]).exists())
        if shutil.disk_usage(target).free-remaining<8*1024**3:raise ValueError("shared storage reserve insufficient")
        for row in original["files"]:
            dest=target/row["file"]
            if dest.exists():
                if sha(dest)!=row["sha256"]:raise ValueError("existing cache identity conflict")
                continue
            part=dest.with_name(dest.name+".part")
            offset=part.stat().st_size if part.exists() else 0
            if offset>row["bytes"]:raise ValueError("oversized partial cache file")
            with (source/row["file"]).open("rb") as src,part.open("ab") as dst:
                src.seek(offset)
                for block in iter(lambda:src.read(8*1024*1024),b""):
                    if shutil.disk_usage(target).free<8*1024**3:raise ValueError("shared reserve exhausted")
                    dst.write(block)
                dst.flush();os.fsync(dst.fileno())
            if part.stat().st_size!=row["bytes"] or sha(part)!=row["sha256"]:
                raise ValueError("copied checkpoint checksum differs")
            os.replace(part,dest)
            print(model,row["file"],"VERIFIED_COPY",flush=True)
        source_receipt=source/"acquisition_receipt.json"
        if (target/"acquisition_receipt.json").exists():
            if sha(target/"acquisition_receipt.json")!=sha(source_receipt):raise ValueError("receipt differs")
        else:shutil.copy2(source_receipt,target/"acquisition_receipt.json")
        write_json(receipt,{"model":model,"revision":candidate["revision"],"shared_checkpoint":str(target),
            "source_worker":"011","source_checkpoint":str(source),"verified":True,
            "acquisition_receipt_sha256":sha(source_receipt),"internet_download_repeated":False,
            "reason":"Enable idle worker to claim still-unstarted models while the other worker finishes its protected active job."},immutable=True)
        print(model,"SHARED_DISPATCH_READY",flush=True)

if __name__=="__main__":
    main()
