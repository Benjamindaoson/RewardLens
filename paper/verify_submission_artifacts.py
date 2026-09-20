"""Verify the manuscript's frozen headline certificates and LaTeX links."""

import csv
import json
import re
from pathlib import Path


PAPER = Path(__file__).resolve().parent
ROOT = PAPER.parent
V1 = ROOT / "results" / "paper_analysis" / "v1"
TEXT_PATHS = [PAPER / "main.tex", *(PAPER / "sections").glob("*.tex"), *(PAPER / "appendix").glob("*.tex")]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def close(actual: float, expected: float, message: str) -> None:
    require(abs(actual - expected) < 1e-9, f"{message}: {actual} != {expected}")


def main() -> None:
    text = "\n".join(path.read_text() for path in TEXT_PATHS)
    rows = list(csv.DictReader((V1 / "figure_source" / "figure4_fingerprint.csv").open()))
    row = {(item["model"], item["factor"]): item for item in rows}
    phi, llava, qwen = row[("Phi", "attribute")], row[("LLaVA", "attribute")], row[("Qwen", "count")]
    close(float(phi["A"]), 0.805, "Phi Attribute static accuracy")
    close(float(llava["A"]), 0.805, "LLaVA Attribute static accuracy")
    close(float(phi["RA"]), 0.8494623655913979, "Phi Attribute RA")
    close(float(llava["RA"]), 1.0, "LLaVA Attribute RA")
    require(int(qwen["n_cond"]) == 200, "Qwen Count base-correct denominator")
    close(float(qwen["RA"]), 0.17, "Qwen Count RA")

    census = json.loads((V1 / "accuracy_matched_census.json").read_text())["1pp"]
    require(census["qualifying_pairs"] == 7, "one-point matched-pair count")
    close(census["median_abs_delta_RA"], 15.053763440860212, "one-point median RA gap")
    close(census["median_abs_delta_II"], 1.005025125628145, "one-point median II gap")
    gaps = {round(item["abs_delta_RA_pp"], 2) for item in census["pairs"]}
    require({25.63, 38.60} <= gaps, "matched-pair RA headline gaps")

    bootstrap = json.loads((V1 / "paired_bootstrap_accuracy_matched.json").read_text())
    attribute = next(item for item in bootstrap["contrasts"] if item["factor"] == "attribute")
    close(abs(attribute["RA"]["point_pp"]), 15.053763440860212, "Attribute bootstrap RA gap")
    require([round(abs(value), 2) for value in attribute["RA"]["ci95_pp"]] == [20.43, 10.21],
            "Attribute bootstrap CI")

    magnitude = json.loads((V1 / "edit_magnitude_summary.json").read_text())
    attr = magnitude["by_factor"]["attribute"]["pixel_change"]
    close(attr["relevant_mean"], 0.11814010620117188, "Attribute relevant pixel change")
    close(attr["irrelevant_mean"], 0.17863739013671875, "Attribute irrelevant pixel change")
    require(magnitude["matched_bins"]["n_matched"] == 459, "magnitude-matched total")
    require(magnitude["matched_bins"]["n_matched_by_factor"]["attribute"] == 109,
            "magnitude-matched Attribute total")
    matched = magnitude["matched_bins"]["ra_ii_on_matched_triplets"]
    close((matched["LLaVA"]["attribute"]["RA"] - matched["Phi"]["attribute"]["RA"]) * 100,
          16.83168316831683, "magnitude-matched Attribute RA gap")
    report = json.loads((V1 / "FINAL_REPORT.json").read_text())
    for band, expected in (("1pp", 15.053763440860212), ("2pp", 15.053763440860212),
                           ("3pp", 15.135135135135142)):
        close(report["census_bands"][band]["median_abs_delta_RA"], expected,
              f"{band} matching-band median RA gap")

    for phrase in ("80.5\\%", "84.95\\%", "100.00\\%", "15.05", "10.75", "38.60",
                   "25.63", "166/200", "34/200", "16.8", "459", "109"):
        require(phrase in text, f"manuscript headline missing: {phrase}")
    require(not re.search(r"\b(?:PFC|PSC)\b", text), "legacy PFC/PSC term in manuscript")
    for display in ("Qwen3-VL-4B", "Gemma-3-4B", "Molmo-7B-D", "Skywork-VL-Reward-7B",
                    "Idefics3-8B", "Phi-3.5-Vision", "InternVL3-8B", "LLaVA-OneVision-7B"):
        require(display in text, f"missing model display name: {display}")
    for pattern in (r"Appendix\s+[0-9]", r"Figure\s+[0-9]", r"Table\s+[0-9]", r"Section\s+[0-9]", r"Sec\.\s+[0-9]"):
        require(not re.search(pattern, text), f"fixed-number cross reference: {pattern}")

    cited = set()
    for match in re.finditer(r"\\cite\w*\{([^}]+)\}", text):
        cited.update(key.strip() for key in match.group(1).split(","))
    bibliography = (PAPER / "references.bib").read_text()
    bibkeys = set(re.findall(r"@\w+\{([^,]+),", bibliography))
    require(cited <= bibkeys, f"missing citation keys: {sorted(cited - bibkeys)}")
    labels = set(re.findall(r"\\label\{([^}]+)\}", text))
    refs = set(re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", text))
    require(refs <= labels, f"missing labels: {sorted(refs - labels)}")
    print("submission artifact verification: PASS")
    print("headline: Phi/LLaVA Attribute 80.5%, RA 84.95%/100.00%, gap 15.05 pp")
    print("census: 7 one-point pairs, median RA/II gaps 15.05/1.01 pp")
    print("citations and cross-references: PASS")


if __name__ == "__main__":
    main()
