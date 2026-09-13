# GPU Job Manifest

Local host has **no CUDA**. Data generation, validation, QC, and statistics run here.

Inference / LoRA must run on a GPU machine.

## Required for PHASE 6–13

Minimum useful GPU: 24 GB (fits 7B VL judges in bf16 or 4-bit 7B + 2B probes).

Better: 40–80 GB if running 7B/8B without aggressive quantization.

## Estimated work after datasets freeze

| stage | models | items (order of magnitude) | note |
|---|---:|---:|---|
| compatibility probe | 8–12 | ~50 each | minutes–hours |
| signal gate | 2–4 families | 100 triplets × 3 images × 4 factors | hours |
| full controlled audit | 8–12 | 500×3×4 if scaled | tens of hours |
| GQA static | 8–12 | ~4000 | tens of hours |
| GQA BoN N=8 | 8–12 | ~4000 × 8 scores | largest cost |

## Do not do on GPU

- CLEVR rendering
- GQA zip download
- plot/table generation

## Resume

Inference writers must append jsonl and skip completed item ids.
