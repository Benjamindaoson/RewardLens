# RewardLens-CLEVR Dataset Card

Primary audit dataset for RewardLens. Not the original CLEVR VQA benchmark.

## Role

\(D_{audit}\) only.

Do not compute static preference accuracy \(A\) from these base images.
Do not mix these images into GQA static or downstream splits.

## Factors

| Factor | Question form | Relevant | Irrelevant | Matching |
|---|---|---|---|---|
| Count | How many COLOR objects are there? | +1 target-color object | +1 same-slot non-target-color object | position, shape, size, material, rotation; color only |
| Attribute | What color is the SHAPE? | recolor unique target | recolor matched non-target, same color transition | size, material, similar depth; uniqueness by shape |
| Presence | Is there a COLOR SHAPE? | remove target | remove matched non-target | shape, size, material, similar depth |
| Spatial | Is A left of B? | move referent until left→right | same world displacement on distractor | dx, dy, size/material of moved objects |

## Render contract

- 320×240, 128 samples
- No camera/light jitter
- Fixed Cycles seed within a triplet
- Blender 2.79b / official CLEVR assets

## Current status

- Count Pilot V1: 10 triplets, validation PASS
- Attribute / Presence / Spatial pilots: generated from the same renderer family
