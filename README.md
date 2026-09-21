> **Portfolio status / 作品集状态：RESEARCH FLAGSHIP · Model Systems**
> Canonical independent research repository for multimodal judge evaluation.

# RewardLens

RewardLens is a reproducible research workspace for controlled evaluation of vision-language reward and preference models.

## Repository contents

- `rewardlens/` — experiment code, model registry, configurations, tests, and research documentation.
- `cloud_staging/` — no-GPU staging, transfer, and verification scripts.
- `docs/`, `reports/` — runbooks, frozen protocol notes, and observed status reports.
- `external/clevr-dataset-gen` — the upstream CLEVR renderer, pinned as a Git submodule.

## Paper variants

The repository contains two explicitly named builds of the same RewardLens
manuscript. They share the title, abstract, method, experiments, results,
figures, discussion, conclusion, and appendices; only the Related Work section
and the bibliography entries required by that section differ.

### 1. Original Related Work version

- Review PDF: [`paper/REWARDLENS_RelatedWork_Original.pdf`](paper/REWARDLENS_RelatedWork_Original.pdf)
- LaTeX entry point: [`paper/main_related_work_original.tex`](paper/main_related_work_original.tex)
- Related Work source: [`paper/sections/02_related_work.tex`](paper/sections/02_related_work.tex)

This is the repository's original concise Related Work section. It retains the
closest-work positioning table and the explicit comparison with MM-JudgeBias,
Perceptual Judgment Bias, and VisualFLIP. The default `paper/main.tex` build
uses this version.

### 2. Collaborator Related Work version

- Review PDF: [`paper/REWARDLENS_RelatedWork_Collaborator.pdf`](paper/REWARDLENS_RelatedWork_Collaborator.pdf)
- LaTeX entry point: [`paper/main_related_work_collaborator.tex`](paper/main_related_work_collaborator.tex)
- Related Work source: [`paper/sections/02_related_work_collaborator.tex`](paper/sections/02_related_work_collaborator.tex)
- Additional bibliography entries: [`paper/references_collaborator_additions.bib`](paper/references_collaborator_additions.bib)

This version uses the collaborator-authored Related Work prose in full. It
provides a broader literature review covering LLM-as-a-judge evaluation,
multimodal reward benchmarks, behavioral testing, controlled vision-language
evaluation, and perturbation-based judge audits. It does not mix in the
original version's comparison table.

Build the two variants independently from the `paper/` directory:

```bash
latexmk -norc -pdf -interaction=nonstopmode -halt-on-error main_related_work_original.tex
latexmk -norc -pdf -interaction=nonstopmode -halt-on-error main_related_work_collaborator.tex
```

## Data and large artifacts

Raw datasets, generated datasets, GPU bundles, tool archives, and runtime outputs are intentionally excluded from GitHub. They are being published to the private Hugging Face dataset repository [`jlai300/RewardLens-data`](https://huggingface.co/datasets/jlai300/RewardLens-data).

`UPLOAD_MANIFEST.md` and the scripts under `rewardlens/scripts/` define the data acquisition, SHA-256 verification, and staging workflow.

## Reproduction

Start with [the reproducibility protocol](rewardlens/docs/REPRODUCIBILITY.md), then follow [the GPU runbook](GPU_RUNBOOK.md). The project uses the locked GPU dependencies in `rewardlens/requirements-gpu.lock`.
