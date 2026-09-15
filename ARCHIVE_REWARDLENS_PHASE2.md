# RewardLens Phase II Archive Index

This file records the current external archive locations for the completed RewardLens Phase II experiment.

## GitHub

Repository: https://github.com/Benjamindaoson/RewardLens

This repository is the lightweight code-facing entry point. The large experiment archive is stored on Hugging Face because it includes result artifacts and reproducibility bundles that do not belong in ordinary Git history.

## Hugging Face Dataset Archive

Dataset repository: https://huggingface.co/datasets/jlai300/RewardLens-phase2-archive

Verified uploaded files under `archive/20260915T173458Z/`:

- `rewardlens_phase2_results_paper_20260915T173458Z.tar.gz`
- `SHA256SUMS_results_paper_20260915T173458Z.txt`
- `external_large_artifacts_20260915T173458Z.tsv`
- `SHA256SUMS_20260915T173458Z.txt`

Primary uploaded evidence package:

```text
af6c4deb2c78fbc8d6601c62f4386320ded1b8a52067ce53a88bd678e5ee9b6a  rewardlens_phase2_results_paper_20260915T173458Z.tar.gz
```

This package contains the final Phase II result directory, paper draft materials, handoff files, logs, checksums, engineering handoff, and frozen source-ID receipts.

## Full Local Archive Preserved On 011

A larger full reproducibility bundle was built and SHA-verified on the AutoDL 011 machine and bridged to Windows for preservation. It includes the current remote code snapshot in addition to the results/paper materials. It was not fully uploaded to Hugging Face during this pass because the network path was too slow for the 1.2GB tarball.

Remote 011 paths:

```text
/root/autodl-fs/RewardLens/archive_publication/rewardlens_reproducibility_20260915T173458Z.tar.gz
/root/autodl-fs/RewardLens/archive_publication/external_large_artifacts_20260915T173458Z.tsv
/root/autodl-fs/RewardLens/archive_publication/SHA256SUMS_20260915T173458Z.txt
```

Full bundle SHA256:

```text
63bd1ff82da5813750be40e1207b78a1acdfb9d14ee66a1e68003d625ed24e5d  rewardlens_reproducibility_20260915T173458Z.tar.gz
8ab10ad6510e0c4c56dc0f4e209faeb7dc5459ea9767156ae33ead6087a8aee9  external_large_artifacts_20260915T173458Z.tsv
```

Local bridge copy retained at:

```text
D:\RewardLens_archive_bridge\rewardlens_reproducibility_20260915T173458Z.tar.gz
D:\RewardLens_archive_bridge\external_large_artifacts_20260915T173458Z.tsv
D:\RewardLens_archive_bridge\SHA256SUMS_20260915T173458Z.txt
D:\RewardLens_archive_bridge\rewardlens_phase2_results_paper_20260915T173458Z.tar.gz
D:\RewardLens_archive_bridge\SHA256SUMS_results_paper_20260915T173458Z.txt
```

## External Large Artifact Policy

Third-party model checkpoints and raw public dataset payloads were not duplicated into the uploaded result tarball. They are enumerated in `external_large_artifacts_20260915T173458Z.tsv` with paths and byte sizes, and the experiment outputs retain the checkpoint and manifest provenance needed for reproducibility.

## Experiment Status

The final Phase II marker on 011 was present at archive time:

```text
/root/autodl-fs/RewardLens/results/phase2/REWARDLENS_FULL_EXPERIMENT_COMPLETE.json
```

Recorded final state from the completed analysis:

```text
REWARDLENS_FULL_EXPERIMENT_COMPLETE = true
TOTAL_MODELS = 8
DISTINCT_FAMILIES = 5
STATIC_COMPLETE = true
DOWNSTREAM_COMPLETE = true
RQ2_CONFIRMATORY_COMPLETE = true
RQ3_CONFIRMATORY_COMPLETE = true
ROBUSTNESS_COMPLETE = true
INTEGRITY_PASS = true
```
