# TallyQA Count Construction

**PRE-RESULT DATA AVAILABILITY ADAPTATION** (2026-09-12). GQA 1.2 public questions provided no usable Count programs. TallyQA is the frozen Count static/downstream source. This is not a result-driven change. No GQA Count mapping was invented.

## Role

| Split | File | Target |
|---|---|---|
| Static (subset A) | `datasets/tallyqa/derived/tallyqa_count_static_manifest.jsonl` | 200 items, prefer 100 simple / 100 complex |
| Downstream (subset B) | `datasets/tallyqa/derived/tallyqa_count_downstream_manifest.jsonl` | 200 questions, N=8, prefer 100 simple / 100 complex |

Independent of RewardLens-CLEVR by construction.

## Image disjointness

`static_image_ids ∩ downstream_image_ids = ∅` (hard assert on `vg:` / `coco:` keys).

At most one question per image inside each split.

## Static item fields

- question
- gold numeric answer
- hard negative: gold ± 1 (deterministic; gold+1 when nonnegative fallback exists, else nearby nonnegative integer)
- candidate_a / candidate_b: deterministically shuffled
- expected_preference

Reject: non-integer / negative gold, missing image source, duplicate (image, question).

## Downstream N=8

Each pool contains gold exactly once and 7 unique nonnegative numeric distractors constructed around gold (`±1, ±2, ±3`, then further nearby counts). Order shuffled deterministically. No negatives, no duplicates.

## Images

Do not download the full TallyQA image dump. After freezing the 400 questions, collect required IDs and:

1. reuse already-downloaded Visual Genome / GQA files when the exact source image is present
2. fetch only missing COCO or VG files

Inventory (`tallyqa_image_inventory.json`) must end with `missing = 0`.

Scripts: `scripts/download_tallyqa.py` (annotations zip only), `scripts/build_tallyqa_count.py`, `scripts/acquire_tallyqa_images.py`, `scripts/combine_fast_eval_manifests.py`.
