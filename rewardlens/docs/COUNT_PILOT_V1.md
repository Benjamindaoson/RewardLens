# COUNT PILOT V1

Generate 10 strictly controlled Count intervention triplets for RewardLens.

Do not expand this into Attribute / Presence / Spatial, and do not run any VLM.

## Scientific contract

For a visual counting question, a relevant visual intervention should flip preference, while an irrelevant but magnitude-matched intervention should keep preference.

Each triplet shares the same question and the same two numeric candidates. Only the image changes:

- `I_base`
- `I_rel`
- `I_irr`

Question form:

```text
How many <COLOR> objects are there?
```

Target membership is defined only by color. The tested variable is the count of that target subset.

## Triplet structure

Assume `target_color = red` and `base_count = n`.

- Base: `n` target-color objects. Preference = the candidate equal to `n`.
- Relevant: add one target-color object in a reserved intervention slot. Count becomes `n+1`. Preference must flip.
- Irrelevant: add one non-target-color object in the exact same slot. Count stays `n`. Preference must stay.

Candidate A / B are shuffled per triplet. Values are numeric strings such as `"3"` and `"4"`.

## Matching contract

Relevant and irrelevant intervention objects match:

- position
- shape
- size
- material
- rotation

They differ only in color, which changes target membership.

Within a triplet, Base / Relevant / Irrelevant also share:

- camera and camera pose
- lights
- background
- base object geometry and appearance
- resolution, samples, and Cycles render seed

Camera and light jitter are disabled. `use_animated_seed` is disabled. `bpy.context.scene.cycles.seed` is set to the triplet seed for all three variants.

## Pilot composition

Master seed: `20260912`.

- 10 triplets, 30 rendered images
- Count transitions: 3× `2->3`, 4× `3->4`, 3× `4->5`, shuffled deterministically
- Multiple CLEVR target colors; irrelevant color is a different deterministic color
- Resolution `320x240`, `128` Cycles samples
- Placement uses 9 predefined safe slots; the intervention slot is chosen from the front row

## Layout

```text
rewardlens/
├── configs/count_pilot_v1.json
├── renderers/clevr_count_renderer.py
├── scripts/generate_count_pilot.py
├── scripts/validate_count_pilot.py
├── scripts/run_count_pilot.ps1
└── docs/COUNT_PILOT_V1.md
```

Outputs:

```text
outputs/count_pilot_v1/
├── images/
├── scenes/
├── manifests/
├── contact_sheets/
├── pilot_manifest.jsonl
└── validation_report.json
```

The renderer reuses CLEVR `utils.add_object`, `utils.add_material`, and `utils.get_camera_coords`. It does not modify `external/clevr-dataset-gen` except for the existing Windows tempfile patch in `render_images.py`.

## Run

From the RewardLens repo:

```powershell
powershell -ExecutionPolicy Bypass -File D:\01_work\RewardLens\rewardlens\scripts\run_count_pilot.ps1
```

Or:

```powershell
python D:\01_work\RewardLens\rewardlens\scripts\generate_count_pilot.py --config D:\01_work\RewardLens\rewardlens\configs\count_pilot_v1.json
python D:\01_work\RewardLens\rewardlens\scripts\validate_count_pilot.py --config D:\01_work\RewardLens\rewardlens\configs\count_pilot_v1.json
```

Validation exits non-zero if any contract check fails. Image-diff statistics are diagnostics only; they are recorded in `validation_report.json` and do not delete triplets.
