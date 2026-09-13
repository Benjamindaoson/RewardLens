#!/usr/bin/env python3
"""Figure 1: controlled intervention concept from real pilot triplets. No model numbers."""

from __future__ import annotations

import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.common import load_font  # noqa: E402

FACTORS = [
    ("Count", os.path.join(PROJECT, "outputs", "count_pilot_v1", "contact_sheets", "count_000000.png")),
    ("Attribute", os.path.join(PROJECT, "outputs", "attribute_pilot_v1", "contact_sheets", "attr_000000.png")),
    ("Presence", os.path.join(PROJECT, "outputs", "presence_pilot_v1", "contact_sheets", "pres_000000.png")),
    ("Spatial", os.path.join(PROJECT, "outputs", "spatial_pilot_v1", "contact_sheets", "spat_000000.png")),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=os.path.join(PROJECT, "outputs", "figures", "figure1_controlled_intervention.png"))
    args = parser.parse_args()
    images = []
    labels = []
    for label, path in FACTORS:
        if not os.path.isfile(path):
            print("MISSING", path, flush=True)
            continue
        images.append(Image.open(path).convert("RGB"))
        labels.append(label)
    if len(images) != 4:
        raise SystemExit("Figure 1 needs all four real pilot contact sheets")
    pad = 24
    title_h = 72
    w = max(im.width for im in images)
    h = sum(im.height for im in images) + title_h + pad * 5 + 40 * 4
    canvas = Image.new("RGB", (w + pad * 2, h), (248, 248, 246))
    draw = ImageDraw.Draw(canvas)
    font = load_font(28)
    small = load_font(20)
    draw.text((pad, pad), "Figure 1. Controlled visual interventions (real RewardLens-CLEVR pilots)", fill=(20, 20, 20), font=font)
    y = pad + title_h
    captions = {
        "Count": "Relevant: +1 target-color object. Irrelevant: +1 matched non-target-color object.",
        "Attribute": "Relevant: recolor queried shape. Irrelevant: same color edit on a matched non-target.",
        "Presence": "Relevant: remove queried object. Irrelevant: remove a matched non-target.",
        "Spatial": "Relevant: flip left/right. Irrelevant: identical displacement on a distractor.",
    }
    for label, im in zip(labels, images):
        draw.text((pad, y), label + "  —  " + captions[label], fill=(40, 40, 40), font=small)
        y += 36
        canvas.paste(im.resize((w, int(im.height * w / im.width))), (pad, y))
        y += int(im.height * w / im.width) + pad
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    canvas.save(args.out)
    print("WROTE", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
