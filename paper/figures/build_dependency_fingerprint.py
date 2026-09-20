"""Render the RA/II fingerprint from the frozen ledger without extra Python deps."""

import csv
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "results" / "paper_analysis" / "v1" / "figure_source" / "figure4_fingerprint.csv"
OUTPUT = Path(__file__).resolve().parent / "dependency_fingerprint.pdf"
PNG_OUTPUT = Path(__file__).resolve().parent / "dependency_fingerprint.png"
FACTORS = [("count", "Count"), ("attribute", "Attribute"), ("presence", "Presence"), ("spatial", "Spatial")]
MODELS = ["Qwen", "Gemma", "Molmo", "Skywork", "Idefics3", "Phi", "LLaVA", "InternVL"]


def main() -> None:
    with SOURCE.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    lookup = {(row["model"], row["factor"]): row for row in rows}

    def panel(metric: str, title: str) -> str:
        lines = [
            r"\begin{minipage}{3.45in}\centering\footnotesize",
            rf"\textbf{{{title}}}\\[2pt]",
            r"\resizebox{\linewidth}{!}{\renewcommand{\arraystretch}{1.25}\begin{tabular}{lcccc}",
            " & " + " & ".join(label for _, label in FACTORS) + r"\\\hline",
        ]
        for model in MODELS:
            cells = []
            for factor, _ in FACTORS:
                value = float(lookup[(model, factor)][metric])
                shade = round(value * 100)
                text = "white" if value < 0.55 else "black"
                cells.append(rf"\cellcolor{{blue!{shade}!white}}\textcolor{{{text}}}{{{value:.2f}}}")
            lines.append(model + " & " + " & ".join(cells) + r"\\")
        return "\n".join(lines + [r"\end{tabular}}\end{minipage}"])

    document = "\n".join([
        r"\documentclass[border=2pt]{standalone}",
        r"\usepackage[table]{xcolor}",
        r"\usepackage{graphicx}",
        r"\begin{document}",
        panel("RA", "Relevant Adaptation (RA)") + r"\hfill" + panel("II", "Irrelevant Invariance (II)"),
        r"\end{document}",
    ])
    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        source = temporary / "dependency_fingerprint.tex"
        source.write_text(document)
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", source.name],
                       cwd=temporary, check=True, stdout=subprocess.DEVNULL)
        shutil.copy2(temporary / "dependency_fingerprint.pdf", OUTPUT)
    if shutil.which("pdftoppm"):
        subprocess.run(["pdftoppm", "-png", "-singlefile", "-r", "300", str(OUTPUT), str(PNG_OUTPUT.with_suffix(""))],
                       check=True, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
