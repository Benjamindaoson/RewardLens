#!/usr/bin/env python3
"""Figure 3: empirical display of Lemma 4 (binary response algebra).

Frozen forensics only. Does not modify Figure 2 or Section 3 theory.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

ROOT = Path(__file__).resolve().parents[2]
FORE = ROOT / "reports" / "forensics_20260916"
OUT_DIR = ROOT / "rewardlens" / "paper" / "figures"

# Decomposition columns: counts, then probabilities with the same stem prefixed by p_.
P_DC = (
    "p_B_correct__arm_wrong__pred_flipped",
    "p_B_correct__arm_wrong__pred_unchanged",
    "p_B_wrong__arm_correct__pred_flipped",
    "p_B_wrong__arm_correct__pred_unchanged",
)
P_DY = (
    "p_B_correct__arm_correct__pred_flipped",
    "p_B_correct__arm_wrong__pred_flipped",
    "p_B_wrong__arm_correct__pred_flipped",
    "p_B_wrong__arm_wrong__pred_changed_to_another_wrong",
)

FACTOR_COLOR = {
    "attribute": "#0072B2",
    "count": "#E69F00",
    "presence": "#009E73",
    "spatial": "#CC79A7",
}
FACTOR_LABEL = {
    "attribute": "Attribute",
    "count": "Count",
    "presence": "Presence",
    "spatial": "Spatial",
}


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def fsum(row: dict, keys: tuple[str, ...]) -> float:
    return sum(float(row[k]) for k in keys)


def cells(decomp: list[dict], arm: str) -> list[dict]:
    out = []
    for r in decomp:
        if r["arm"] != arm:
            continue
        dy = fsum(r, P_DY)
        dc = fsum(r, P_DC)
        out.append(
            {
                "display": r["display"],
                "factor": r["factor"],
                "F": dy,
                "dC": dc,
                "n": int(r["n"]),
            }
        )
    return out


def draw_geometry(ax) -> None:
    xs = [0.0, 1.0]
    ax.plot(xs, xs, color="#4C78A8", lw=1.6, zorder=1)
    ax.plot(xs, [1.0, 0.0], color="#E45756", lw=1.6, zorder=1)
    ax.scatter([1.0], [0.0], s=70, color="#0072B2", zorder=3, edgecolors="#111111", lw=0.6)
    ax.scatter([0.17], [0.83], s=70, color="#E69F00", zorder=3, edgecolors="#111111", lw=0.6)
    ax.text(0.74, 0.80, "gold stays\nΔC = ΔY", fontsize=7.2, color="#4C78A8", ha="left", va="bottom")
    ax.text(0.80, 0.44, "gold flips\nΔC = 1 − ΔY", fontsize=7.2, color="#E45756", ha="left", va="center")
    ax.annotate(
        "Qwen Attribute\nF_R = 1,  ΔC = 0",
        (1.0, 0.0),
        xytext=(0.38, 0.12),
        fontsize=7.0,
        color="#111111",
        arrowprops={"arrowstyle": "-", "color": "#555555", "lw": 0.6},
        annotation_clip=False,
    )
    ax.annotate(
        "Qwen Count\nF_R = 0.17,  ΔC = 0.83",
        (0.17, 0.83),
        xytext=(0.02, 0.58),
        fontsize=7.0,
        color="#111111",
        arrowprops={"arrowstyle": "-", "color": "#555555", "lw": 0.6},
        annotation_clip=False,
    )
    ax.set_xlim(-0.03, 1.03)
    ax.set_ylim(-0.03, 1.03)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("prediction change  P(ΔY = 1)")
    ax.set_ylabel("correctness change  P(ΔC = 1)")
    ax.set_title("(a)  Lemma 4 geometry", loc="left", fontsize=9.5, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xticks([0, 0.5, 1.0])
    ax.set_yticks([0, 0.5, 1.0])


def _annotate(ax, x: float, y: float, text: str, dx: float, dy: float) -> None:
    ax.scatter([x], [y], s=90, facecolors="none", edgecolors="#111111", lw=1.2, zorder=4)
    ax.annotate(
        text,
        (x, y),
        xytext=(x + dx, y + dy),
        fontsize=7.0,
        color="#111111",
        arrowprops={"arrowstyle": "-", "color": "#555555", "lw": 0.6},
    )


def draw_relevant(ax, rows: list[dict]) -> None:
    ax.plot([0, 1], [1, 0], color="#E45756", lw=1.15, ls="--", zorder=1, label="Lemma 4:  ΔC = 1 − ΔY")
    for factor, color in FACTOR_COLOR.items():
        pts = [r for r in rows if r["factor"] == factor]
        ax.scatter(
            [r["F"] for r in pts],
            [r["dC"] for r in pts],
            s=36,
            color=color,
            alpha=0.88,
            zorder=2,
            label=FACTOR_LABEL[factor],
        )
    _annotate(ax, 1.0, 0.0, "Qwen Attribute", -0.38, 0.07)
    _annotate(ax, 0.17, 0.83, "Qwen Count", 0.14, 0.05)
    _annotate(ax, 0.27, 0.73, "Gemma Spatial", 0.16, -0.14)
    ax.set_xlim(-0.03, 1.03)
    ax.set_ylim(-0.03, 1.03)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("prediction change  F_R = P(ΔY_R = 1)")
    ax.set_ylabel("correctness change  P(ΔC_R = 1)")
    ax.set_title("(b)  Relevant: gold flips", loc="left", fontsize=9.5, fontweight="bold")
    ax.legend(frameon=False, loc="lower left", fontsize=6.8, ncol=1)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xticks([0, 0.5, 1.0])
    ax.set_yticks([0, 0.5, 1.0])


def draw_mirrors(ax) -> None:
    labels = ["Qwen\nAttribute", "Qwen\nCount"]
    pred = [1.00, 0.17]
    corr = [0.00, 0.83]
    x = [0.0, 1.15]
    w = 0.38
    b1 = ax.bar([t - w / 2 for t in x], pred, w, color="#4C78A8", label="prediction change  F_R")
    b2 = ax.bar([t + w / 2 for t in x], corr, w, color="#E45756", label="correctness change  P(ΔC_R = 1)")
    for bars in (b1, b2):
        for rect in bars:
            h = rect.get_height()
            ax.text(
                rect.get_x() + rect.get_width() / 2,
                (h + 0.04) if h >= 0.02 else 0.10,
                f"{h:.2f}",
                ha="center",
                va="bottom",
                fontsize=8.0,
            )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel("rate (n = 200)")
    ax.set_ylim(0, 1.18)
    ax.set_xlim(-0.55, 1.70)
    ax.set_title(
        "(c)  Same identity, two realizations",
        loc="left",
        fontsize=9.5,
        fontweight="bold",
        pad=18,
    )
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.16), fontsize=7.2, ncol=2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.text(
        0.0,
        -0.28,
        "gold flips, letter follows\nΔC = 1 − ΔY = 0",
        ha="center",
        va="top",
        fontsize=7.2,
        color="#333333",
        transform=ax.get_xaxis_transform(),
        clip_on=False,
    )
    ax.text(
        1.15,
        -0.28,
        "gold flips, letter stays\nΔC = 1 − ΔY = 0.83",
        ha="center",
        va="top",
        fontsize=7.2,
        color="#333333",
        transform=ax.get_xaxis_transform(),
        clip_on=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    args = parser.parse_args()
    decomp = load_csv(FORE / "flips" / "flip_correctness_decomposition.csv")
    rel = cells(decomp, "relevant")
    irr = cells(decomp, "irrelevant")
    if len(rel) != 32 or len(irr) != 32:
        raise SystemExit(f"expected 32 relevant and 32 irrelevant cells, got {len(rel)} / {len(irr)}")
    rel_off = max(abs(r["F"] + r["dC"] - 1.0) for r in rel)
    irr_off = max(abs(r["F"] - r["dC"]) for r in irr)
    if rel_off > 1e-9:
        raise SystemExit(f"relevant cells leave the Lemma 4 anti-diagonal; max |F+dC-1|={rel_off}")
    if irr_off > 1e-9:
        raise SystemExit(f"irrelevant cells leave the Lemma 4 diagonal; max |F-dC|={irr_off}")

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.bbox": "tight",
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
        }
    )
    fig = plt.figure(figsize=(7.2, 6.85))
    gs = GridSpec(2, 2, figure=fig, height_ratios=[1.12, 1.00], hspace=0.55, wspace=0.32)
    draw_geometry(fig.add_subplot(gs[0, 0]))
    draw_relevant(fig.add_subplot(gs[0, 1]), rel)
    draw_mirrors(fig.add_subplot(gs[1, :]))
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = out / "fig3_correctness_vs_prediction"
    fig.savefig(stem.with_suffix(".pdf"))
    fig.savefig(stem.with_suffix(".png"), dpi=300)
    fig.savefig(stem.with_suffix(".svg"))
    plt.close(fig)
    print("WROTE", stem.with_suffix(".pdf"))
    print(f"Lemma 4 check: max |F_R + dC_R - 1| = {rel_off:.2e}; max |F_I - dC_I| = {irr_off:.2e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
