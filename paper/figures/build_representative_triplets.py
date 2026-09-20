"""Compose an appendix montage solely from retained frozen PASS triplet renders."""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
OUTPUT_DIR = Path(__file__).resolve().parent
OUTPUT_PNG = OUTPUT_DIR / "representative_triplets.png"
OUTPUT_PDF = OUTPUT_DIR / "representative_triplets.pdf"
SELECTIONS = (
    ("count", "Count", "count_000000"),
    ("attribute", "Attribute", "attr_000000"),
    ("presence", "Presence", "pres_000000"),
    ("spatial", "Spatial", "spat_000000"),
)
VARIANTS = (("base", "Base"), ("relevant", "Relevant"), ("irrelevant", "Irrelevant"))


def resolve_manifest_path(path: str) -> Path:
    """Map the frozen Windows manifest path to its mounted read-only source."""
    if not path.startswith("D:\\"):
        raise ValueError(f"unexpected frozen image path: {path}")
    return Path("/mnt/d") / Path(path[3:].replace("\\", "/"))


def load_triplet(factor: str, triplet_id: str) -> list[Image.Image]:
    manifest = REPO / "manifests" / "factors" / factor / "factor_audit_manifest.jsonl"
    rows = {}
    with manifest.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row["triplet_id"] == triplet_id:
                rows[row["variant"]] = row
    if set(rows) != {variant for variant, _ in VARIANTS}:
        raise ValueError(f"incomplete manifest triplet: {factor}/{triplet_id}")
    images = []
    for variant, _ in VARIANTS:
        row = rows[variant]
        if row.get("qc_status") != "PASS":
            raise ValueError(f"non-PASS source: {factor}/{triplet_id}/{variant}")
        path = resolve_manifest_path(row["image_path"])
        if not path.is_file():
            raise FileNotFoundError(path)
        images.append(Image.open(path).convert("RGB"))
    return images


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)


def main() -> None:
    triplets = [(label, load_triplet(factor, triplet_id))
                for factor, label, triplet_id in SELECTIONS]
    width, height = triplets[0][1][0].size
    if any(image.size != (width, height) for _, images in triplets for image in images):
        raise ValueError("all frozen source renders must have identical dimensions")

    scale = 2
    cell_w, cell_h = width * scale, height * scale
    label_w, header_h, gap = 205, 70, 16
    canvas = Image.new("RGB", (label_w + 3 * cell_w + 4 * gap, header_h + 4 * cell_h + 5 * gap), "white")
    draw = ImageDraw.Draw(canvas)
    header_font, row_font = font(28), font(26)
    for column, (_, label) in enumerate(VARIANTS):
        x = label_w + gap + column * (cell_w + gap) + cell_w // 2
        draw.text((x, 18), label, anchor="ma", fill="black", font=header_font)
    for row, (label, images) in enumerate(triplets):
        y = header_h + gap + row * (cell_h + gap)
        draw.text((label_w - 18, y + cell_h // 2), label, anchor="rm", fill="black", font=row_font)
        for column, image in enumerate(images):
            x = label_w + gap + column * (cell_w + gap)
            canvas.paste(image.resize((cell_w, cell_h), Image.Resampling.LANCZOS), (x, y))
    canvas.save(OUTPUT_PNG, dpi=(300, 300))
    canvas.save(OUTPUT_PDF, resolution=300.0)


if __name__ == "__main__":
    main()
