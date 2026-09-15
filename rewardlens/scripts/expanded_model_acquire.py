#!/usr/bin/env python3
"""Frozen-revision model-only acquisition, one model per worker, resumable files."""
import argparse
import concurrent.futures
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import time
import traceback
import requests

ROOT=Path("/root/autodl-tmp/RewardLens/code")
sys.path.insert(0,str(ROOT/"rewardlens"))
from scripts.phase2_autonomous import write_json,sha
PHASE=Path("/root/autodl-fs/RewardLens/results/phase2")
CONTROL=PHASE/"expanded_acquisition"
SELECTION=PHASE/"EXPANDED_MODEL_SELECTION.json"
LOCAL=Path("/root/autodl-tmp/RewardLens/expanded_models")
HOSTS={"011":"autodl-container-47bb4a8b0c-371e5795","017":"autodl-container-03dd44a781-f2a6258d"}
MS_REPOS={"phi35_vision_instruct":"LLM-Research/Phi-3.5-vision-instruct",
          "idefics3_8b_llama3":"AI-ModelScope/Idefics3-8B-Llama3",
          "internvl3_8b_hf":"OpenGVLab/InternVL3-8B-hf",
          "llava_onevision_qwen2_7b":"AI-ModelScope/llava-onevision-qwen2-7b-ov-hf"}

def status_path(model):
    return CONTROL/"status"/(model+".json")

def required_files(meta):
    return [r for r in meta["siblings"] if "/" not in r["rfilename"]
            and r["rfilename"].endswith((".safetensors",".json",".py",".model",".txt"))]

def matches(path,row):
    if not path.exists() or path.stat().st_size!=row["size"]:
        return False
    if row.get("lfs"):
        return sha(path)==row["lfs"]["sha256"]
    h=hashlib.sha1()
    h.update(("blob "+str(row["size"])+"\0").encode())
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()==row["blobId"]

def acquire(candidate):
    model=candidate["model"]
    local=LOCAL/model/candidate["revision"]
    local.mkdir(parents=True,exist_ok=True)
    started=time.time()
    status={k:candidate[k] for k in ("model","family","repo_id","revision","assigned_worker")}
    status.update(download_status="METADATA",downloaded_bytes=0,download_runtime=0,source=[],
                  checkpoint_verified=False,processor_verified=False,adapter_status="PENDING",
                  formal_run_ready=False,local_checkpoint=str(local),worker_hostname=socket.gethostname())
    write_json(status_path(model),status)
    def api(url,**kwargs):
        r=requests.get(url,timeout=(10,30),**kwargs);r.raise_for_status();return r
    metadata=api("https://hf-mirror.com/api/models/"+candidate["repo_id"]+"/revision/"+candidate["revision"],
                 params={"blobs":"true"}).json()
    if metadata["sha"]!=candidate["revision"]:
        raise ValueError("repository revision mismatch")
    files=required_files(metadata)
    expected=sum(r["size"] for r in files)
    remaining=sum(r["size"]-(local/r["rfilename"]).stat().st_size if (local/r["rfilename"]).exists()
                  else r["size"]-(local/(r["rfilename"]+".part")).stat().st_size
                  if (local/(r["rfilename"]+".part")).exists() else r["size"] for r in files)
    if shutil.disk_usage(LOCAL).free-remaining<8*1024**3:
        raise RuntimeError("disk reserve gate: keep at least 8 GiB free")
    write_json(CONTROL/"metadata"/(model+".json"),metadata,immutable=True)
    ms_files={}
    ms_repo=MS_REPOS.get(model)
    if ms_repo:
        try:
            ms_data=api("https://www.modelscope.cn/api/v1/models/"+ms_repo+"/repo/files",
                        params={"Revision":"master","Recursive":"true"}).json()
            for r in ms_data.get("Data",{}).get("Files",[]):
                if r.get("Type")=="blob":
                    ms_files[r["Path"]]=r
        except Exception as e:
            status["modelscope_metadata_error"]=str(e)
    # Only byte-identical LFS objects are eligible for mirror acceleration.
    def routes(row):
        name=row["rfilename"]
        urls=[("hf-mirror","https://hf-mirror.com/"+candidate["repo_id"]+"/resolve/"+candidate["revision"]+"/"+name)]
        ms=ms_files.get(name)
        if ms and row.get("lfs") and ms.get("Sha256")==row["lfs"]["sha256"] and ms.get("Size")==row["size"]:
            urls.append(("modelscope","https://www.modelscope.cn/api/v1/models/"+ms_repo+
                         "/repo?Revision="+ms["Revision"]+"&FilePath="+name))
        return urls
    benchmark=[]
    probe=next(r for r in files if r["rfilename"].endswith(".safetensors"))
    for source,url in routes(probe):
        t=time.time()
        try:
            with requests.get(url,headers={"Range":"bytes=0-8388607"},stream=True,timeout=(8,12)) as response:
                response.raise_for_status();n=0
                for block in response.iter_content(1048576):
                    n+=len(block)
                    if n>=8388608 or time.time()-t>15:break
            benchmark.append({"source":source,"bytes":n,"seconds":time.time()-t,"mib_s":n/1048576/(time.time()-t)})
        except Exception as e:
            benchmark.append({"source":source,"error":str(e),"mib_s":0})
    speed={r["source"]:r["mib_s"] for r in benchmark}
    write_json(CONTROL/"benchmarks"/(model+".json"),{"model":model,"measurements":benchmark})
    status.update(download_status="DOWNLOADING",expected_bytes=expected,benchmark=benchmark)
    progress={r["rfilename"]:(local/(r["rfilename"]+".part")).stat().st_size if (local/(r["rfilename"]+".part")).exists()
              else (local/r["rfilename"]).stat().st_size if (local/r["rfilename"]).exists() else 0 for r in files}
    used=set();guard=threading.Lock();done=threading.Event()
    def publish():
        while not done.wait(10):
            with guard:
                status.update(downloaded_bytes=sum(progress.values()),download_runtime=time.time()-started,
                              source=sorted(used),free_disk_bytes=shutil.disk_usage(LOCAL).free)
                write_json(status_path(model),status)
    monitor=threading.Thread(target=publish,daemon=True);monitor.start()
    file_receipts=[]
    def download(row):
        name=row["rfilename"];target=local/name;part=local/(name+".part")
        if target.exists():
            if not matches(target,row):
                raise ValueError("existing checkpoint file differs from frozen identity: "+name)
            return {"file":name,"bytes":row["size"],"sha256":sha(target),"source":"verified_existing"}
        choices=sorted(routes(row),key=lambda x:-speed.get(x[0],0))
        errors=[]
        for attempt in range(8):
            source,url=choices[attempt%len(choices)]
            offset=part.stat().st_size if part.exists() else 0
            try:
                if offset<row["size"]:
                    headers={"Range":"bytes="+str(offset)+"-","Cache-Control":"no-cache"} if offset else {}
                    with requests.get(url,headers=headers,stream=True,timeout=(12,35)) as response:
                        response.raise_for_status()
                        if offset and (response.status_code!=206 or not response.headers.get("Content-Range","").startswith("bytes "+str(offset)+"-")):
                            raise ValueError("server did not honor exact resume range")
                        with part.open("ab" if offset else "wb") as f:
                            for block in response.iter_content(1048576):
                                if not block:continue
                                f.write(block);offset+=len(block)
                                if offset>row["size"]:raise ValueError("response exceeded expected size")
                                if shutil.disk_usage(LOCAL).free<8*1024**3:
                                    raise RuntimeError("disk reserve exhausted")
                                with guard:
                                    progress[name]=offset;used.add(source)
                            f.flush();os.fsync(f.fileno())
                if part.stat().st_size!=row["size"]:
                    raise ValueError("incomplete transfer")
                if not matches(part,row):
                    raise ValueError("download hash mismatch")
                os.replace(part,target)
                return {"file":name,"bytes":row["size"],"sha256":sha(target),"source":source,
                        "upstream_git_blob":row["blobId"],"upstream_lfs":row.get("lfs")}
            except Exception as e:
                errors.append({"attempt":attempt,"source":source,"error":str(e)})
                if "hash mismatch" in str(e) or "exceeded" in str(e):
                    raise
                time.sleep(min(2*(attempt+1),10))
        raise RuntimeError(json.dumps({"file":name,"attempts":errors}))
    try:
        # Four file streams belong to ONE checkpoint; never two heavy models on a worker.
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            for receipt in ex.map(download,files):
                file_receipts.append(receipt)
        from safetensors import safe_open
        index=json.loads((local/"model.safetensors.index.json").read_text())
        for shard in set(index["weight_map"].values()):
            with safe_open(str(local/shard),framework="pt",device="cpu") as f:
                if set(f.keys())!={k for k,v in index["weight_map"].items() if v==shard}:
                    raise ValueError("checkpoint index/shard key mismatch")
        status.update(download_status="CHECKPOINT_VERIFIED",checkpoint_verified=True,
                      downloaded_bytes=expected,download_runtime=time.time()-started,source=sorted(used))
        write_json(local/"acquisition_receipt.json",{"model":model,"repo_id":candidate["repo_id"],
                   "revision":candidate["revision"],"selection_sha256":sha(SELECTION),
                   "files":file_receipts,"worker":socket.gethostname(),"verified":True},immutable=True)
        write_json(CONTROL/"receipts"/(model+".json"),json.loads((local/"acquisition_receipt.json").read_text()),immutable=True)
        # No model weights loaded; hide the GPU during processor/import validation.
        env={**os.environ,"HF_HUB_OFFLINE":"1","TRANSFORMERS_OFFLINE":"1","CUDA_VISIBLE_DEVICES":"",
             "OMP_NUM_THREADS":"1","TOKENIZERS_PARALLELISM":"false"}
        code="from transformers import AutoProcessor,AutoConfig; from PIL import Image; import sys; p=AutoProcessor.from_pretrained(sys.argv[1],trust_remote_code=True,local_files_only=True); c=AutoConfig.from_pretrained(sys.argv[1],trust_remote_code=True,local_files_only=True); p.image_processor(images=[Image.new('RGB',(64,64),'red')],return_tensors='pt'); print('PROCESSOR_CPU_PASS',c.model_type)"
        result=subprocess.run([sys.executable,"-c",code,str(local)],env=env,capture_output=True,text=True,timeout=180)
        status.update(processor_verified=result.returncode==0,processor_check_returncode=result.returncode,
                      processor_check_log=(result.stdout+result.stderr)[-12000:],
                      adapter_status="AWAITING_GPU_SMOKE" if result.returncode==0 else "CPU_PROCESSOR_REPAIR_REQUIRED",
                      download_status="COMPLETE")
    finally:
        done.set();monitor.join(timeout=2)
        status["download_runtime"]=time.time()-started
        write_json(status_path(model),status)
    return status

def status_watch():
    selection=json.loads(SELECTION.read_text())
    candidates=selection["candidates"][:4]
    while True:
        rows=[]
        for candidate in candidates:
            path=status_path(candidate["model"])
            row=json.loads(path.read_text()) if path.exists() else {
                **{k:candidate[k] for k in ("model","family","repo_id","revision","assigned_worker")},
                "download_status":"QUEUED","downloaded_bytes":0,"download_runtime":0,"source":None,
                "checkpoint_verified":False,"processor_verified":False,"adapter_status":"PENDING","formal_run_ready":False}
            readiness=PHASE/"distributed_v1"/candidate["model"]/"readiness.json"
            if readiness.exists():
                ready=json.loads(readiness.read_text())
                row.update(formal_run_ready=ready.get("formal_run_ready",False),adapter_status="GPU_SMOKE_PASS")
            if (PHASE/"distributed_v1"/candidate["model"]/"completion.json").exists():
                row["formal_execution_status"]="COMPLETE"
            rows.append(row)
        write_json(PHASE/"expanded_model_acquisition_status.json",
                   {"selection_sha256":sha(SELECTION),"updated_unix":time.time(),"models":rows})
        time.sleep(10)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker",choices=HOSTS)
    parser.add_argument("--status-watch",action="store_true")
    args=parser.parse_args()
    CONTROL.mkdir(parents=True,exist_ok=True);LOCAL.mkdir(parents=True,exist_ok=True)
    if args.status_watch:
        if socket.gethostname()!=HOSTS["011"]:raise ValueError("status publisher must be 011")
        with (CONTROL/"status_publisher.lock").open("a") as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);status_watch()
        return
    if socket.gethostname()!=HOSTS[args.worker]:raise ValueError("worker identity mismatch")
    with (LOCAL/"download.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        selection=json.loads(SELECTION.read_text())
        for candidate in selection["candidates"][:4]:
            if candidate["assigned_worker"]!=args.worker:continue
            try:
                acquire(candidate)
            except Exception:
                path=status_path(candidate["model"])
                state=json.loads(path.read_text()) if path.exists() else dict(candidate)
                state.update(download_status="ENGINEERING_BLOCKED",error=traceback.format_exc())
                write_json(path,state)
                print(state["error"],flush=True)

if __name__=="__main__":
    main()
