> **Portfolio status / 作品集状态：RESEARCH FLAGSHIP · Model Systems**
> Canonical independent research repository for multimodal judge evaluation.

# RewardLens

RewardLens is a reproducible research workspace for controlled evaluation of vision-language reward and preference models.

## Repository contents

- `rewardlens/` — experiment code, model registry, configurations, tests, and research documentation.
- `cloud_staging/` — no-GPU staging, transfer, and verification scripts.
- `docs/`, `reports/` — runbooks, frozen protocol notes, and observed status reports.
- `external/clevr-dataset-gen` — the upstream CLEVR renderer, pinned as a Git submodule.

## Data and large artifacts

Raw datasets, generated datasets, GPU bundles, tool archives, and runtime outputs are intentionally excluded from GitHub. They are being published to the private Hugging Face dataset repository [`jlai300/RewardLens-data`](https://huggingface.co/datasets/jlai300/RewardLens-data).

`UPLOAD_MANIFEST.md` and the scripts under `rewardlens/scripts/` define the data acquisition, SHA-256 verification, and staging workflow.

## Reproduction

Start with [the reproducibility protocol](rewardlens/docs/REPRODUCIBILITY.md), then follow [the GPU runbook](GPU_RUNBOOK.md). The project uses the locked GPU dependencies in `rewardlens/requirements-gpu.lock`.
