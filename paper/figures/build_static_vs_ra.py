"""Build the four-factor static-accuracy versus RA figure from the frozen ledger."""

from pathlib import Path
import csv

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "results" / "paper_analysis" / "v1" / "figure_source" / "figure4_fingerprint.csv"
OUTPUT = Path(__file__).resolve().parent / "static_vs_ra.pdf"

COLORS = {
    "Qwen": "#4c78a8", "Gemma": "#f58518", "Molmo": "#54a24b",
    "Skywork": "#e45756", "Idefics3": "#72b7b2", "Phi": "#b279a2",
    "LLaVA": "#ff9da6", "InternVL": "#9d755d",
}
SHORT = {
    "Qwen3-VL-4B": "Qwen", "Gemma-3-4B": "Gemma", "Molmo-7B-D": "Molmo",
    "Skywork-VL-Reward-7B": "Skywork", "Idefics3-8B": "Idefics3",
    "Phi-3.5-Vision": "Phi", "LLaVA-OneVision-7B": "LLaVA",
    "InternVL3-8B": "InternVL",
}
ORDER = ["count", "attribute", "presence", "spatial"]


def main() -> None:
    with SOURCE.open(newline="") as handle:
        data = list(csv.DictReader(handle))
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.55), sharex=True, sharey=True)
    for ax, factor in zip(axes.flat, ORDER):
        subset = [row for row in data if row["factor"] == factor]
        for row in subset:
            name = SHORT[row["display"]]
            highlight = factor == "attribute" and name in {"Phi", "LLaVA"}
            static = float(row["A"]) * 100
            ra = float(row["RA"]) * 100
            ax.scatter(static, ra, s=54 if highlight else 37,
                       color=COLORS[row["model"]], edgecolor="black" if highlight else "white",
                       linewidth=1.25 if highlight else 0.55, zorder=3)
            if factor == "attribute" and name == "Phi":
                ax.annotate("Phi", (static, ra), xytext=(-25, -14),
                            textcoords="offset points", fontsize=7)
            elif factor == "attribute" and name == "LLaVA":
                ax.annotate("LLaVA", (static, ra), xytext=(5, 5),
                            textcoords="offset points", fontsize=7)
        if factor == "attribute":
            ax.axvline(80.5, color="#555555", lw=0.85, ls="--", zorder=1)
            ax.text(80.8, 5, "Phi/LLaVA\n$A_S=80.5$", fontsize=6.3, color="#333333")
        ax.set_title(factor.capitalize(), fontsize=9, pad=4)
        ax.set_xlim(35, 97)
        ax.set_ylim(-3, 103)
        ax.grid(color="#d9d9d9", lw=0.5, zorder=0)
        ax.set_xticks([40, 60, 80, 100])
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.tick_params(labelsize=7)
    for ax in axes[:, 0]:
        ax.set_ylabel("Relevant Adaptation (RA, %)", fontsize=8)
    for ax in axes[1, :]:
        ax.set_xlabel("Measured static accuracy ($A_S$, %)", fontsize=8)
    handles = [Line2D([0], [0], marker="o", color="w", label=name,
                      markerfacecolor=COLORS[key], markeredgecolor="white", markersize=5)
               for key, name in [("Qwen", "Qwen"), ("Gemma", "Gemma"),
                                 ("Molmo", "Molmo"), ("Skywork", "Skywork"),
                                 ("Idefics3", "Idefics3"), ("Phi", "Phi"),
                                 ("LLaVA", "LLaVA"), ("InternVL", "InternVL")]]
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=6.5,
               frameon=False, columnspacing=1.1, handletextpad=0.35)
    fig.tight_layout(rect=(0, 0.08, 1, 1), pad=1.0, w_pad=0.85, h_pad=1.25)
    fig.savefig(OUTPUT, bbox_inches="tight")


if __name__ == "__main__":
    main()
