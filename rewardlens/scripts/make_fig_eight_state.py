#!/usr/bin/env python3
"""Publication figure: eight-state Sankey + pi_101 heatmap from frozen forensics.

Reads reports/forensics_20260916/states/eight_state_counts.csv only.
Does not rerun models or touch confirmatory endpoints.
1pp A^S matching is not used here; this figure is the eight-state structure.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch, PathPatch
from matplotlib.path import Path as MplPath

ROOT = Path(__file__).resolve().parents[2]
COUNTS = ROOT / "reports" / "forensics_20260916" / "states" / "eight_state_counts.csv"
OUT_DIR = ROOT / "rewardlens" / "paper" / "figures"

STATES = ["111", "101", "110", "100", "011", "001", "010", "000"]
# Okabe–Ito; 101 is the RA-hidden mass.
STATE_COLOR = {
    "111": "#0072B2",
    "101": "#E69F00",
    "110": "#56B4E9",
    "100": "#CC79A7",
    "011": "#009E73",
    "001": "#D55E00",
    "010": "#F0E442",
    "000": "#999999",
}


def load_counts(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def row_states(row: dict) -> dict[str, int]:
    return {s: int(row[f"n_{s}"]) for s in STATES}


def ribbon(ax, x0, x1, y0t, y0b, y1t, y1b, color, alpha=0.78) -> None:
    xm = 0.5 * (x0 + x1)
    verts = [
        (x0, y0t),
        (xm, y0t),
        (xm, y1t),
        (x1, y1t),
        (x1, y1b),
        (xm, y1b),
        (xm, y0b),
        (x0, y0b),
        (x0, y0t),
    ]
    codes = [
        MplPath.MOVETO,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.LINETO,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CLOSEPOLY,
    ]
    ax.add_patch(
        PathPatch(MplPath(verts, codes), facecolor=color, edgecolor="none", alpha=alpha, lw=0)
    )


def node_box(ax, x, yb, w, h, facecolor, edgecolor="#222222", lw=0.6) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, yb),
            w,
            h,
            boxstyle="round,pad=0.004,rounding_size=0.012",
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=lw,
            mutation_aspect=0.4,
        )
    )


def draw_sankey(ax, counts: dict[str, int], title: str, subtitle: str, callout: str | None) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.10, 1.08)
    ax.axis("off")
    ax.text(0.0, 1.16, title, fontsize=10, fontweight="bold", transform=ax.transAxes, clip_on=False)
    ax.text(0.0, 1.07, subtitle, fontsize=8, color="#444444", transform=ax.transAxes, clip_on=False)

    n = sum(counts.values()) or 1
    gap = 0.035
    col_w = 0.11
    xs = [0.04, 0.36, 0.68]
    usable = 0.90

    def stack_height(k: int) -> float:
        return max(0.0, (k / n) * usable)

    # Terminal order (top → bottom): 111, 101, 110, 100, 011, 001, 010, 000
    term_order = ["111", "101", "110", "100", "011", "001", "010", "000"]
    y = 0.96
    term_span: dict[str, tuple[float, float]] = {}
    for s in term_order:
        h = stack_height(counts[s])
        if h <= 0:
            continue
        yb = y - h
        term_span[s] = (yb, y)
        node_box(ax, xs[2], yb, col_w, h, STATE_COLOR[s])
        mid = 0.5 * (yb + y)
        ax.text(
            xs[2] + col_w + 0.015,
            mid,
            f"{s}  {counts[s]}",
            va="center",
            ha="left",
            fontsize=8,
            color="#111111",
            fontweight="bold" if s in {"111", "101"} else "normal",
        )
        y = yb - (gap if h > 0.04 else gap * 0.45)

    # Relevant column: R=1 (111+110+011+010), R=0 (101+100+001+000)
    r1_states = ["111", "110", "011", "010"]
    r0_states = ["101", "100", "001", "000"]

    # Place R nodes stacked from the top; skip empty branches.
    r_groups = [("R=1", r1_states, "#1f4e79"), ("R=0", r0_states, "#8a5a00")]
    r_heights = {lab: stack_height(sum(counts[s] for s in mem)) for lab, mem, _ in r_groups}
    r_span: dict[str, tuple[float, float]] = {}
    y = 0.96
    for lab, mem, face in r_groups:
        h = r_heights[lab]
        if h <= 0:
            continue
        yb = y - h
        r_span[lab] = (yb, y)
        node_box(ax, xs[1], yb, col_w, h, face, edgecolor="#222222")
        ax.text(
            xs[1] + col_w / 2,
            0.5 * (yb + y),
            f"{lab}\n{sum(counts[s] for s in mem)}",
            ha="center",
            va="center",
            fontsize=7.5,
            color="white",
            fontweight="bold",
        )
        y = yb - gap

    # Base column
    b1_states = [s for s in STATES if s[0] == "1"]
    b0_states = [s for s in STATES if s[0] == "0"]
    b_groups = [("B=1", b1_states, "#2c5f2d"), ("B=0", b0_states, "#5c5c5c")]
    b_span: dict[str, tuple[float, float]] = {}
    y = 0.96
    for lab, mem, face in b_groups:
        h = stack_height(sum(counts[s] for s in mem))
        if h <= 0:
            continue
        yb = y - h
        b_span[lab] = (yb, y)
        node_box(ax, xs[0], yb, col_w, h, face)
        ax.text(
            xs[0] + col_w / 2,
            0.5 * (yb + y),
            f"{lab}\n{sum(counts[s] for s in mem)}",
            ha="center",
            va="center",
            fontsize=7.5,
            color="white",
            fontweight="bold",
        )
        y = yb - gap

    # Flows: allocate vertical slots inside each parent proportional to child counts.
    def allocate(parent: tuple[float, float], weights: list[int]) -> list[tuple[float, float]]:
        yb, yt = parent
        total = sum(weights) or 1
        height = yt - yb
        out = []
        cursor = yt
        for w in weights:
            h = height * (w / total)
            out.append((cursor - h, cursor))
            cursor -= h
        return out

    # B → R (color by majority terminal in that BR cell: use R=1 blue-ish / R=0 orange-ish)
    br_map = {
        ("B=1", "R=1"): [s for s in r1_states if s[0] == "1"],
        ("B=1", "R=0"): [s for s in r0_states if s[0] == "1"],
        ("B=0", "R=1"): [s for s in r1_states if s[0] == "0"],
        ("B=0", "R=0"): [s for s in r0_states if s[0] == "0"],
    }
    for b_lab, _bmem, _ in b_groups:
        if b_lab not in b_span:
            continue
        child_labs = [lab for lab, _, _ in r_groups if lab in r_span]
        weights = [sum(counts[s] for s in br_map[(b_lab, lab)]) for lab in child_labs]
        slots = allocate(b_span[b_lab], weights)
        for (yb0, yt0), lab, w in zip(slots, child_labs, weights):
            if w <= 0:
                continue
            yb1, yt1 = r_span[lab]
            # Target slot inside R node for this B parent: proportional.
            r_weights_from_b = []
            r_parents = [p for p, _, _ in b_groups if p in b_span]
            for p in r_parents:
                r_weights_from_b.append(sum(counts[s] for s in br_map[(p, lab)]))
            r_slots = allocate(r_span[lab], r_weights_from_b)
            idx = r_parents.index(b_lab)
            yb1, yt1 = r_slots[idx]
            color = "#E69F00" if lab == "R=0" else "#0072B2"
            ribbon(ax, xs[0] + col_w, xs[1], yt0, yb0, yt1, yb1, color, alpha=0.55)

    # R → terminal
    for r_lab, mem, _ in r_groups:
        if r_lab not in r_span:
            continue
        present = [s for s in mem if counts[s] > 0]
        if not present:
            continue
        weights = [counts[s] for s in present]
        slots = allocate(r_span[r_lab], weights)
        for (yb0, yt0), s in zip(slots, present):
            yb1, yt1 = term_span[s]
            ribbon(ax, xs[1] + col_w, xs[2], yt0, yb0, yt1, yb1, STATE_COLOR[s], alpha=0.8)

    ax.text(xs[0] + col_w / 2, 1.02, "Base", ha="center", fontsize=8, color="#333333")
    ax.text(xs[1] + col_w / 2, 1.02, "Relevant", ha="center", fontsize=8, color="#333333")
    ax.text(xs[2] + col_w / 2, 1.02, "State BRI", ha="center", fontsize=8, color="#333333")

    if callout:
        ax.text(
            0.02,
            -0.04,
            callout,
            fontsize=8,
            color="#8a5a00",
            fontweight="bold",
            transform=ax.transAxes,
        )


def draw_schematic(ax) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.0, 0.96, "(a)  Eight-state object  (B, R, I)", fontsize=10, fontweight="bold")

    lines = [
        "A^S : pairwise accuracy on the independent static set. Never computed on audit bases.",
        "A^B = P(B=1) : audit-base accuracy. Matching uses A^S, never A^B.",
        "RA = P(R=1 | B=1),   II = P(I=1 | B=1),   D = (RA, II).",
        "Predeclared matching remains |ΔA^S| ≤ 1 pp. Other ε are post-hoc sensitivity.",
    ]
    y = 0.88
    for line in lines:
        ax.text(0.0, y, line, fontsize=8.0, color="#222222")
        y -= 0.075

    ax.text(0.0, 0.54, "Given B = 1", fontsize=8.5, fontweight="bold", color="#2c5f2d")
    cells = [
        (0.10, 0.28, "111", "adapt + stay", "#0072B2", "white"),
        (0.38, 0.28, "110", "adapt, irr. break", "#56B4E9", "#111111"),
        (0.10, 0.06, "101", "stay; gold flipped", "#E69F00", "#111111"),
        (0.38, 0.06, "100", "base only", "#CC79A7", "white"),
    ]
    ax.text(0.23, 0.50, "I = 1", ha="center", fontsize=7.5, color="#444444")
    ax.text(0.51, 0.50, "I = 0", ha="center", fontsize=7.5, color="#444444")
    ax.text(0.01, 0.38, "R=1", va="center", fontsize=7.5, color="#444444")
    ax.text(0.01, 0.16, "R=0", va="center", fontsize=7.5, color="#444444")
    for x, yb, code, caption, color, tc in cells:
        ax.add_patch(
            FancyBboxPatch(
                (x, yb),
                0.26,
                0.20,
                boxstyle="round,pad=0.006,rounding_size=0.02",
                facecolor=color,
                edgecolor="#222222",
                linewidth=0.6,
                alpha=0.92,
            )
        )
        ax.text(x + 0.13, yb + 0.125, code, ha="center", va="center", fontsize=12, fontweight="bold", color=tc)
        ax.text(x + 0.13, yb + 0.045, caption, ha="center", va="center", fontsize=6.6, color=tc)

    notes = [
        ("RA collapses the two columns", "(111 + 110) / A^B"),
        ("II collapses the two rows", "(111 + 101) / A^B"),
        ("π_101 is the mass those", "two margins hide."),
    ]
    ny = 0.48
    for head, sub in notes:
        ax.text(0.70, ny, head, fontsize=8.0, fontweight="bold", color="#222222")
        ax.text(0.70, ny - 0.06, sub, fontsize=7.6, color="#555555")
        ny -= 0.18


def draw_heatmap(ax, rows: list[dict]) -> None:
    models = []
    seen = set()
    for r in rows:
        if r["display"] not in seen:
            models.append(r["display"])
            seen.add(r["display"])
    factors = ["attribute", "count", "presence", "spatial"]
    factor_lab = {"attribute": "Attribute", "count": "Count", "presence": "Presence", "spatial": "Spatial"}
    lookup = {(r["display"], r["factor"]): r for r in rows}
    data = []
    for m in models:
        data.append([int(lookup[(m, f)]["n_101"]) / int(lookup[(m, f)]["n"]) for f in factors])

    cmap = plt.cm.YlOrBr
    im = ax.imshow(data, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(4))
    ax.set_xticklabels([factor_lab[f] for f in factors], fontsize=8)
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(models, fontsize=8)
    ax.set_title(
        "(d)  π_101 = P(B=1, R=0, I=1)  — mass hidden when RA/II are reported alone",
        loc="left",
        fontsize=10,
        fontweight="bold",
        pad=6,
    )
    ax.tick_params(length=0)
    for i, m in enumerate(models):
        for j, f in enumerate(factors):
            v = data[i][j]
            n101 = int(lookup[(m, f)]["n_101"])
            txt = f"{100 * v:.0f}%\n({n101})"
            ax.text(
                j,
                i,
                txt,
                ha="center",
                va="center",
                fontsize=6.8,
                color="#111111" if v < 0.55 else "#fafafa",
                fontweight="bold" if v >= 0.5 else "normal",
            )
    for spine in ax.spines.values():
        spine.set_visible(False)
    cbar = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.ax.tick_params(labelsize=7, length=2)
    cbar.set_label(r"$\pi_{101}$", fontsize=8)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--counts", default=str(COUNTS))
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    args = parser.parse_args()
    rows = load_counts(Path(args.counts))
    by = {(r["display"], r["factor"]): row_states(r) for r in rows}

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 10,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.bbox": "tight",
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
        }
    )

    fig = plt.figure(figsize=(7.2, 8.6))
    gs = GridSpec(3, 2, figure=fig, height_ratios=[1.10, 1.45, 1.20], hspace=0.52, wspace=0.18)

    ax_s = fig.add_subplot(gs[0, :])
    draw_schematic(ax_s)

    q_attr = by[("Qwen", "attribute")]
    q_count = by[("Qwen", "count")]
    ax_b = fig.add_subplot(gs[1, 0])
    draw_sankey(
        ax_b,
        q_attr,
        "(b)  Qwen  ·  Attribute",
        "A^B = 1.00    RA = 1.00    II = 1.00    F_R = 1.00",
        None,
    )
    ax_c = fig.add_subplot(gs[1, 1])
    draw_sankey(
        ax_c,
        q_count,
        "(c)  Qwen  ·  Count",
        "A^B = 1.00    RA = 0.17    II = 1.00    F_R = 0.17",
        "166/200: gold flips, predicted letter unchanged.",
    )

    ax_h = fig.add_subplot(gs[2, :])
    draw_heatmap(ax_h, rows)

    fig.suptitle(
        "Eight-state structure of evidence dependence  (frozen Phase II audit triplets)",
        fontsize=11.5,
        fontweight="bold",
        y=0.995,
    )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = out_dir / "fig_eight_state_sankey"
    fig.savefig(stem.with_suffix(".pdf"))
    fig.savefig(stem.with_suffix(".png"), dpi=300)
    fig.savefig(stem.with_suffix(".svg"))
    plt.close(fig)
    print("WROTE", stem.with_suffix(".pdf"))
    print("WROTE", stem.with_suffix(".png"))
    print("WROTE", stem.with_suffix(".svg"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
