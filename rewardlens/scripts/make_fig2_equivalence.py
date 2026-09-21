#!/usr/bin/env python3
"""Figure 2: Same accuracy, different intervention behavior.

Frozen forensics only. 1 pp band remains the predeclared primary analysis.
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


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def fnum(row: dict, key: str) -> float:
    return float(row[key])


def draw_scatter(ax, pairs: list[dict]) -> None:
    xs = [fnum(p, "delta_A_S_pp") for p in pairs]
    ys = [fnum(p, "delta_RA_pp") for p in pairs]
    inside = [x <= 1.0 + 1e-12 for x in xs]
    ax.axvspan(0, 1.0, color="#E45756", alpha=0.10, zorder=0)
    ax.axvline(1.0, color="#E45756", lw=1.0, ls="--", zorder=1)
    ax.scatter(
        [x for x, inn in zip(xs, inside) if not inn],
        [y for y, inn in zip(ys, inside) if not inn],
        s=28,
        alpha=0.75,
        color="#4C78A8",
        zorder=2,
        label="|ΔA^S| > 1 pp",
    )
    ax.scatter(
        [x for x, inn in zip(xs, inside) if inn],
        [y for y, inn in zip(ys, inside) if inn],
        s=44,
        alpha=0.95,
        color="#E45756",
        zorder=3,
        label="predeclared |ΔA^S| ≤ 1 pp",
    )

    def mark(factor: str, a: str, b: str, text: str, dx: float, dy: float) -> None:
        for p in pairs:
            if p["factor"] == factor and {p["model_a"], p["model_b"]} == {a, b}:
                x, y = fnum(p, "delta_A_S_pp"), fnum(p, "delta_RA_pp")
                ax.scatter([x], [y], s=90, facecolors="none", edgecolors="#111111", lw=1.2, zorder=4)
                ax.annotate(
                    text,
                    (x, y),
                    xytext=(x + dx, y + dy),
                    fontsize=7.2,
                    color="#111111",
                    arrowprops={"arrowstyle": "-", "color": "#555555", "lw": 0.6},
                )
                return

    mark(
        "attribute",
        "Phi",
        "LLaVA",
        "Phi–LLaVA Attribute\nΔA^S = 0 pp,  |ΔRA| = 15.1 pp",
        8.0,
        16.0,
    )
    mark(
        "spatial",
        "Skywork",
        "Phi",
        "Skywork–Phi Spatial\n|ΔA^S| = 0.35 pp,  |ΔRA| = 38.6 pp",
        9.5,
        11.0,
    )
    ax.set_xlabel("|ΔA^S| (percentage points)")
    ax.set_ylabel("|ΔRA| (percentage points)")
    ax.set_title("(a)  Equal accuracy, unequal RA", loc="left", fontsize=9.5, fontweight="bold")
    ax.legend(frameon=False, loc="upper right", fontsize=7.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlim(-0.4, max(xs) + 1.5)


def draw_curve(ax, curve: list[dict]) -> None:
    eps = [fnum(r, "epsilon_pp") for r in curve]
    med = [fnum(r, "median_abs_delta_RA") for r in curve]
    mx = [fnum(r, "max_abs_delta_RA") for r in curve]
    ax.plot(eps, med, marker="o", color="#E45756", label="median |ΔRA|")
    ax.plot(eps, mx, marker="s", color="#4C78A8", label="max |ΔRA|")
    ax.axvline(1.0, color="#9A9A9A", lw=1.0, ls="--")
    ax.text(1.15, 33, "1 pp = predeclared\nprimary analysis", fontsize=7, color="#555555")
    ax.set_xlabel("matching tolerance ε (percentage points)")
    ax.set_ylabel("RA dispersion (percentage points)")
    ax.set_title("(b)  Dispersion across examined ε", loc="left", fontsize=9.5, fontweight="bold")
    ax.legend(frameon=False, loc="upper left", fontsize=7.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xticks(eps)


def draw_states(ax, counts: list[dict]) -> None:
    picks = [
        ("LLaVA", "attribute", "LLaVA\nAttribute"),
        ("Phi", "attribute", "Phi\nAttribute"),
        ("Qwen", "attribute", "Qwen\nAttribute"),
        ("Qwen", "count", "Qwen\nCount"),
        ("InternVL", "count", "InternVL\nCount"),
        ("Gemma", "spatial", "Gemma\nSpatial"),
    ]
    lookup = {(r["display"], r["factor"]): r for r in counts}
    x = list(range(len(picks)))
    n111, n101, nother = [], [], []
    for m, f, _ in picks:
        r = lookup[(m, f)]
        a = int(r["n_111"])
        b = int(r["n_101"])
        n111.append(a)
        n101.append(b)
        nother.append(int(r["n"]) - a - b)
    w = 0.62
    ax.bar(x, n111, w, color="#0072B2", label="111  correct on B, R, I")
    ax.bar(x, n101, w, bottom=n111, color="#E69F00", label="101  correct on B, I; wrong on R")
    ax.bar(
        x,
        nother,
        w,
        bottom=[a + b for a, b in zip(n111, n101)],
        color="#BBBBBB",
        label="other states",
    )
    for i, (a, b) in enumerate(zip(n111, n101)):
        if a:
            ax.text(i, a / 2, str(a), ha="center", va="center", fontsize=7.5, color="white", fontweight="bold")
        if b:
            ax.text(i, a + b / 2, str(b), ha="center", va="center", fontsize=7.5, color="#111111", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([lab for _, _, lab in picks], fontsize=7.5)
    ax.set_ylabel("triplets (n = 200)")
    ax.set_ylim(0, 220)
    ax.set_title("(c)  Joint correctness-state counts", loc="left", fontsize=9.5, fontweight="bold", pad=18)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.16), fontsize=7.0, ncol=3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    args = parser.parse_args()
    pairs = load_csv(FORE / "equivalence" / "all_pairs_delta.csv")
    curve = load_csv(FORE / "equivalence" / "accuracy_equivalence_curve.csv")
    counts = load_csv(FORE / "states" / "eight_state_counts.csv")

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
    gs = GridSpec(2, 2, figure=fig, height_ratios=[1.05, 1.08], hspace=0.52, wspace=0.32)
    draw_scatter(fig.add_subplot(gs[0, 0]), pairs)
    draw_curve(fig.add_subplot(gs[0, 1]), curve)
    ax_c = fig.add_subplot(gs[1, :])
    draw_states(ax_c, counts)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = out / "fig2_same_accuracy_different_behavior"
    fig.savefig(stem.with_suffix(".pdf"))
    fig.savefig(stem.with_suffix(".png"), dpi=300)
    fig.savefig(stem.with_suffix(".svg"))
    plt.close(fig)
    print("WROTE", stem.with_suffix(".pdf"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
