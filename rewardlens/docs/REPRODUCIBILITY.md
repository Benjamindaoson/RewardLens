# Reproducibility

## Seeds

- Count Pilot V1 master seed: 20260912
- Attribute / Presence / Spatial pilots: 202609121 / 202609122 / 202609123

## Commands

Count (already completed):

```
python rewardlens/scripts/generate_count_pilot.py --config rewardlens/configs/count_pilot_v1.json
python rewardlens/scripts/validate_count_pilot.py --config rewardlens/configs/count_pilot_v1.json
```

Other factor pilots:

```
python rewardlens/scripts/generate_controlled_pilot.py --factor attribute
python rewardlens/scripts/validate_controlled_pilot.py --factor attribute
```

Replace `attribute` with `presence` or `spatial`.

## Environment (data generation host)

- Windows, Blender 2.79b portable
- Host Python 3.12, Pillow, numpy
- torch 2.13.0+cpu, CUDA unavailable

## Forbidden after confirmatory freeze

- Per-model candidate reshuffle
- Computing A on audit bases
- Sharing images across static and downstream
- Dropping ugly models
- Prompt shopping to change model order
