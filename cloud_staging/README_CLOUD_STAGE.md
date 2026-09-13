# AutoDL no-GPU staging first, then GPU compute.

Assume:

```
/root/autodl-tmp/RewardLens/   # fast local disk
    code/ data/ models/ cache/ outputs/ logs/
/root/autodl-fs/RewardLens/    # persistent
    bundles/ datasets/ models/ results/ checksums/
```

Override with `REWARDLENS_CLOUD_TMP` and `REWARDLENS_CLOUD_FS`.

## Workflow

1. Local Windows prepares bundles (this repo).
2. Create AutoDL **no-GPU** instance (user action).
3. `bash cloud_staging/sync_gpu_bundle.sh` then `bash cloud_staging/stage_autodl_nogpu.sh`
4. `bash cloud_staging/download_models.sh`  (internet allowed here)
5. `bash cloud_staging/verify_cloud_stage.sh`
6. Switch the instance to GPU / A800. Do **not** download during paid GPU if avoidable.
7. `export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`
8. `bash rewardlens/scripts/run_gpu_preflight.sh`
9. `bash rewardlens/scripts/run_signal_pipeline.sh`
10. If engineering sanity PASS: `bash rewardlens/scripts/run_full_pipeline.sh`
11. `bash cloud_staging/sync_results_back.sh`

Do not rent GPU from this local task. Staging scripts are the deliverable.

## Exact user action required

Create or identify an AutoDL no-GPU machine and set:

```
export REWARDLENS_SSH=user@host
export REWARDLENS_CLOUD_TMP=/root/autodl-tmp/RewardLens
export REWARDLENS_CLOUD_FS=/root/autodl-fs/RewardLens
```

Then run the sync/stage scripts. Hugging Face gated models (Gemma, Llama) need `huggingface-cli login` on the staging machine.
