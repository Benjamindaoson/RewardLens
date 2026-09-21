# RewardLens Phase II forensics 2026-09-16

These analyses are post-hoc forensic analyses of frozen RewardLens Phase II artifacts. They do not modify the frozen experiment, manifests, thresholds, or primary predeclared analyses.

Generated: 2026-09-15T22:06:46Z
CPU only. No model inference.

## Provenance gate

- Audit source kind: procedural CLEVR-controlled renders from blank `base_scene.blend`.
- Audit `source_image_id` is null on all 2400 SHA-manifest rows.
- `I_Audit-source ∩ I_Downstream = ∅` pass = **True**.
- Rendered PNG SHA overlap with downstream = 0.
- SHA-manifest `carrier=gqa/tallyqa` on audit is a factor-to-dataset label leak, not a photograph pointer.

## Eight-state reconstruction

- 160/160 metric cells match canonical values within 1e-12.
- `audit_base_accuracy` is `P(B=1)=sum_ri π_1ri`. It is never called static accuracy.

## Accuracy-equivalence (A^S matching)

- Predeclared band remains `|ΔA^S| ≤ 1 pp`: 7 pairs, median |ΔRA| = 15.053763440860212 pp, max = 38.604166666666664 pp.
- Exact-zero `|ΔA^S|=0`: 1 pairs.
- 0.5 pp post-hoc: 4 pairs, median |ΔRA| = 25.628140703517587 pp.
- Other ε values are post-hoc sensitivity only.

## Pair graph

See `pair_graph/`. Exploratory. Do not retarget the main paper.

