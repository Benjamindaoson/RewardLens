"""Build the complete ranked 1-pp matched-pair RA-gap plot."""

from pathlib import Path
import csv

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "results" / "paper_analysis" / "v1" / "accuracy_matched_1pp.csv"
OUTPUT = Path(__file__).resolve().parent / "matched_ra_gaps.pdf"


def main() -> None:
    with SOURCE.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows.sort(key=lambda row: float(row["abs_delta_RA_pp"]), reverse=True)
    labels = [f"{row['factor'].capitalize()}: {row['model_1']}--{row['model_2']}"
              for row in rows]
    values = [float(row["abs_delta_RA_pp"]) for row in rows]
    colors = ["#c94c4c" if value >= 10 else "#8aa6c1" for value in values]

    fig, ax = plt.subplots(figsize=(6.8, 3.1))
    positions = list(range(len(rows)))
    bars = ax.barh(positions, values, color=colors, height=0.60)
    ax.set_yticks(positions, labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlim(0, 43)
    ax.set_xlabel("Absolute RA gap (percentage points)", fontsize=9)
    ax.set_xticks([0, 10, 20, 30, 40])
    ax.tick_params(axis="x", labelsize=8)
    ax.xaxis.grid(True, color="#d9d9d9", lw=0.6)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    for bar, value in zip(bars, values):
        ax.text(value + .55, bar.get_y() + bar.get_height() / 2, f"{value:.1f}",
                va="center", fontsize=8)
    fig.tight_layout(pad=.7)
    fig.savefig(OUTPUT, bbox_inches="tight")


if __name__ == "__main__":
    main()
