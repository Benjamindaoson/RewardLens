#!/usr/bin/env python3
"""Frozen Phase II V2 physical-disjoint downstream preflight."""

from __future__ import annotations

import json
import os
import random
import sys
import tempfile
import time
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from inference.bon import nested_candidate_sets, oriented_pair, pair_count, pool_candidates
from lib.gqa_mapping import load_questions_file, load_scene_graphs, map_corpus
from lib.gqa_pools import N_POOL, factor_vocab, structured_candidates
from lib.jsonl_io import read_jsonl
from lib.tallyqa import n8_pool, split_bucket
from scripts.build_phase2_downstream_v2 import repair_downstream_rows, sha256_file
from scripts.build_tallyqa_count import SEED, clean_row, load_rows

PHASE = Path("/root/autodl-fs/RewardLens/results/phase2")
SOURCES = Path("/root/autodl-fs/RewardLens/phase2_v2_sources")
CODE = PROJECT
STATIC_SHA256 = "6e4a23fc54d4704e70587b177586152e6e63b7a4dac5964e7e16f56395e682e3"
FACTORS = ("count", "attribute", "presence", "spatial")


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
        temp = Path(handle.name)
    os.replace(temp, path)


def atomic_json(path: Path, value: Any) -> None:
    atomic_text(path, json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n")


def atomic_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    atomic_text(path, "".join(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n" for row in rows))


def file_sha(path: Path) -> str:
    return sha256_file(str(path))


def receipt_hashes(path: Path) -> tuple[dict[str, str], dict[str, list[str]]]:
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if receipt.get("missing_ids") or receipt.get("unexpected_files"):
        raise ValueError("raw verification receipt is not clean: %s" % path)
    rows = receipt.get("byte_hash_manifest")
    if not isinstance(rows, list):
        raise ValueError("raw verification receipt lacks byte_hash_manifest: %s" % path)
    by_name = {}
    for row in rows:
        name, digest = str(row.get("canonical_filename") or ""), str(row.get("sha256") or "")
        if not name or len(digest) != 64 or name in by_name:
            raise ValueError("invalid byte-hash manifest entry in %s" % path)
        by_name[name] = digest
    return by_name, {str(k): list(v) for k, v in (receipt.get("duplicate_physical_sha256") or {}).items()}


def gqa_raw_filename(row: dict[str, Any]) -> str:
    """Map TallyQA's vg:<id> namespace and GQA's bare id to raw <id>.jpg."""
    image_id = str(row.get("source_id") or row.get("image_id") or "").strip()
    if image_id.startswith("vg:"):
        image_id = image_id.split(":", 1)[1]
    if image_id.endswith(".jpg"):
        image_id = os.path.basename(image_id)
    else:
        image_id += ".jpg"
    return image_id


def resolve_gqa(row: dict[str, Any], hashes: dict[str, str]) -> tuple[str, str]:
    name = gqa_raw_filename(row)
    path = SOURCES / "gqa/required_raw_images" / name
    digest = hashes.get(name)
    if not digest or not path.is_file():
        raise FileNotFoundError("required GQA/VG raw image unavailable: %s" % name)
    return str(path), digest


def resolve_tally(row: dict[str, Any], gqa: dict[str, str], coco: dict[str, str]) -> tuple[str, str]:
    if str(row.get("source")) == "vg":
        return resolve_gqa(row, gqa)
    if str(row.get("source")) == "coco":
        name = os.path.basename(str(row.get("image_rel") or ""))
        path = SOURCES / "coco/required_raw_images" / name
        digest = coco.get(name)
        if not digest or not path.is_file():
            raise FileNotFoundError("required COCO raw image unavailable: %s" % name)
        return str(path), digest
    raise ValueError("non-TallyQA source: %s" % row.get("source"))


def resolved_static(rows: list[dict[str, Any]], gqa: dict[str, str], coco: dict[str, str]) -> list[dict[str, Any]]:
    result = []
    for source in rows:
        row = dict(source)
        if row.get("dataset") == "tallyqa":
            row["image_path"], row["physical_image_id"] = resolve_tally(row, gqa, coco)
        else:
            row["image_path"], row["physical_image_id"] = resolve_gqa(row, gqa)
        result.append(row)
    return result


def audit_rows() -> list[dict[str, Any]]:
    original = read_jsonl(str(CODE / "manifests/audit_manifest.jsonl"))
    linux = read_jsonl(str(CODE / "outputs/qwen_full/audit_manifest.linux.jsonl"))
    if len(original) != 2400 or len(linux) != 2400:
        raise ValueError("expected 2400 audit rows in both frozen and Linux manifests")
    if [r["item_id"] for r in original] != [r["item_id"] for r in linux]:
        raise ValueError("Linux audit path manifest does not match frozen audit item order")
    result = []
    for row in linux:
        row = dict(row)
        path = Path(str(row.get("image_path") or ""))
        if not path.is_file():
            raise FileNotFoundError("audit image unavailable: %s" % path)
        row["physical_image_id"] = file_sha(path)
        result.append(row)
    return result


def gqa_mapping() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    qdir = SOURCES / "gqa/questions"
    qfiles = [qdir / "train_balanced_questions.json", qdir / "val_balanced_questions.json"]
    sfiles = sorted((SOURCES / "gqa/sceneGraphs").glob("*sceneGraphs.json"))
    if not all(p.is_file() for p in qfiles) or not sfiles:
        raise FileNotFoundError("validated GQA balanced questions or scene graphs are unavailable")
    scenes = load_scene_graphs([str(p) for p in sfiles])
    mapped, reports = [], []
    for path in qfiles:
        questions = load_questions_file(str(path))
        rows, report = map_corpus(questions, scenes, split_name=path.stem, seed=SEED)
        mapped.extend(rows)
        reports.append(report)
        del questions
    expected = json.loads((CODE / "manifests/gqa_factor_mapping_report.json").read_text(encoding="utf-8"))
    if len(mapped) != int(expected.get("n_mapped") or -1):
        raise ValueError("GQA mapping count differs from frozen report: %d" % len(mapped))
    if dict(Counter(r["factor"] for r in mapped)) != expected.get("counts"):
        raise ValueError("GQA factor mapping counts differ from frozen report")
    return mapped, {"n_mapped": len(mapped), "reports": reports}


def gqa_pool(mapping: list[dict[str, Any]], hashes: dict[str, str], limit: int | None) -> list[dict[str, Any]]:
    down_ids = set(json.loads((CODE / "manifests/downstream_image_ids.json").read_text(encoding="utf-8"))["image_ids"])
    scenes = load_scene_graphs([str(p) for p in sorted((SOURCES / "gqa/sceneGraphs").glob("*sceneGraphs.json"))])
    vocab = {factor: factor_vocab(mapping, factor) for factor in FACTORS}
    rng, items = random.Random(SEED), []
    for factor in FACTORS:
        pool = [r for r in mapping if r["factor"] == factor and r.get("image_id") in down_ids and r.get("answer")]
        pool.sort(key=lambda r: (r.get("mapping_confidence") != "high", str(r.get("question_id"))))
        rng.shuffle(pool)
        written = 0
        for row in pool:
            if limit is not None and written >= limit:
                break
            candidates = structured_candidates(factor, row, vocab=vocab[factor], scene=scenes.get(str(row["image_id"])))
            if len(candidates) < N_POOL:
                continue
            rng.shuffle(candidates)
            gold = str(row["answer"])
            gold_index = next((i for i, c in enumerate(candidates) if str(c.get("text")).strip().casefold() == gold.strip().casefold()), -1)
            if gold_index < 0:
                raise ValueError("GQA constructed pool lost gold: %s" % row["question_id"])
            item = {
                "item_id": "gqa_down:%s:%s" % (factor, row["question_id"]),
                "source_item_id": "gqa_down:%s:%s" % (factor, row["question_id"]),
                "question_id": row["question_id"], "image_id": row["image_id"], "factor": factor,
                "question": row["question"], "gold": gold, "gold_answer": gold, "n_pool": N_POOL,
                "candidates": candidates, "gold_index": gold_index,
                "candidate_source": [c.get("source") for c in candidates],
                "partial": False, "split": "downstream", "mapping_source": row.get("mapping_source"),
            }
            item["image_path"], item["physical_image_id"] = resolve_gqa(item, hashes)
            items.append(item)
            written += 1
    return items


def tally_pool(gqa: dict[str, str], coco: dict[str, str]) -> list[dict[str, Any]]:
    raw = load_rows(str(SOURCES / "tallyqa/annotations"))
    clean, seen = [], set()
    for source in raw:
        row = clean_row(source)
        if row is None:
            continue
        key = (row["image_id"], row["question"].lower())
        if key not in seen:
            clean.append(row)
            seen.add(key)
    items = []
    for row in clean:
        if split_bucket(row["image_id"], SEED) != "downstream":
            continue
        candidates, gold_index = n8_pool(row["gold"], random.Random("%s:%s:n8" % (SEED, row["question_id"])))
        item = {
            "item_id": "tallyqa_down:count:%s" % row["question_id"],
            "source_item_id": "tallyqa_down:count:%s" % row["question_id"],
            "question_id": row["question_id"], "image_id": row["image_id"], "image_rel": row["image_rel"],
            "source": row["source"], "source_id": row["source_id"], "factor": "count",
            "question": row["question"], "gold": str(row["gold"]), "gold_answer": str(row["gold"]),
            "n_pool": 8, "candidates": candidates, "gold_index": gold_index, "issimple": row["issimple"],
            "split": "downstream", "dataset": "tallyqa", "partial": False,
        }
        item["image_path"], item["physical_image_id"] = resolve_tally(item, gqa, coco)
        items.append(item)
    if not items:
        raise ValueError("no eligible TallyQA downstream source rows")
    return items


def frozen_projection(row: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in row.items() if k not in {"image_path", "source_item_id", "physical_image_id"}}


def verify_original_downstream(gqa_original: list[dict[str, Any]], tally: list[dict[str, Any]]) -> list[dict[str, Any]]:
    old_gqa = read_jsonl(str(CODE / "manifests/gqa_downstream_manifest.jsonl"))
    old_tally = read_jsonl(str(CODE / "manifests/fast_eval/tallyqa_count_downstream_manifest.jsonl"))
    if len(old_gqa) != 600 or len(old_tally) != 200:
        raise ValueError("frozen downstream components are not 600 GQA + 200 TallyQA")
    gqa_by_id, tally_by_id = ({r["item_id"]: r for r in gqa_original}, {r["item_id"]: r for r in tally})
    for row in old_gqa:
        if row["item_id"] not in gqa_by_id or frozen_projection(gqa_by_id[row["item_id"]]) != frozen_projection(row):
            raise ValueError("GQA frozen downstream reconstruction mismatch: %s" % row["item_id"])
    for row in old_tally:
        if row["item_id"] not in tally_by_id or frozen_projection(tally_by_id[row["item_id"]]) != frozen_projection(row):
            raise ValueError("TallyQA frozen downstream reconstruction mismatch: %s" % row["item_id"])
    return [dict(tally_by_id[r["item_id"]]) for r in old_tally] + [dict(gqa_by_id[r["item_id"]]) for r in old_gqa]


def physical_rows(rows: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    return [{"split": split, "item_id": row["item_id"], "factor": row.get("factor"),
             "carrier": "tallyqa" if row.get("dataset") == "tallyqa" or row.get("factor") == "count" else "gqa",
             "image_id": row.get("image_id"), "image_path": row.get("image_path"),
             "physical_image_id": row["physical_image_id"]} for row in rows]


def validate_bon(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter()
    for row in rows:
        parsed, subsets = pool_candidates(row), nested_candidate_sets(row)
        if set(subsets[2]) - set(subsets[4]) or set(subsets[4]) - set(subsets[8]):
            raise ValueError("BoN nested subset failure: %s" % parsed["pool_id"])
        if parsed["gold_uid"] not in subsets[2] or [len(subsets[n]) for n in (2, 4, 8)] != [2, 4, 8]:
            raise ValueError("BoN gold/subset failure: %s" % parsed["pool_id"])
        pairs = {frozenset(oriented_pair(parsed["pool_id"], a, b)) for a, b in combinations(subsets[8], 2)}
        if len(pairs) != pair_count(8):
            raise ValueError("BoN pair orientation failure: %s" % parsed["pool_id"])
        counts[str(row["factor"])] += 1
    return {
        "status": "PASS", "pools": len(rows), "factor_counts": dict(counts),
        "candidates_per_pool": 8, "gold_per_pool": 1, "distractors_per_pool": 7,
        "nested_N": [2, 4, 8], "pairwise_judgments_per_N8_pool": pair_count(8),
        "salts": {"subset": "RewardLens-BoN-Subset-v1", "orientation": "RewardLens-PairOrientation-v1",
                  "tie": "RewardLens-BoN-Tie-v1"},
    }


def main() -> int:
    started = time.time()
    PHASE.mkdir(parents=True, exist_ok=True)
    gqa_list, coco_list = SOURCES / "required_gqa_image_ids.txt", SOURCES / "required_coco_image_ids.txt"
    if file_sha(gqa_list) != "734b95bde39f110f7734ed9dca12972a13a17cdd569c8e7108a7f8010616fbeb":
        raise ValueError("frozen GQA acquisition-list hash mismatch")
    if file_sha(coco_list) != "c3cfc12191a0ed8bf5aa3d9d7ad8034301ee138cb4828485c21c787b8ad5e2d6":
        raise ValueError("frozen COCO acquisition-list hash mismatch")
    gqa_hashes, gqa_duplicates = receipt_hashes(PHASE / "autodl_gqa_raw_image_verification_receipt.json")
    coco_hashes, coco_duplicates = receipt_hashes(PHASE / "autodl_coco_raw_image_verification_receipt.json")
    if len(gqa_hashes) != 58851 or len(coco_hashes) != 49616:
        raise ValueError("raw byte-hash manifest count mismatch")
    static_source = CODE / "manifests/fast_eval/static_manifest.jsonl"
    if file_sha(static_source) != STATIC_SHA256:
        raise ValueError("frozen D_static manifest hash mismatch")
    static = resolved_static(read_jsonl(str(static_source)), gqa_hashes, coco_hashes)
    audit = audit_rows()
    qfiles, sfiles = gqa_inputs()
    vocab, mapping_counts = gqa_vocab_and_counts(qfiles)
    down_ids = set(json.loads((CODE / "manifests/downstream_image_ids.json").read_text(encoding="utf-8"))["image_ids"])
    scenes = gqa_scene_summary(down_ids, sfiles)
    relevant = gqa_relevant_mapping(qfiles, scenes, down_ids)
    mapping_report = {"n_mapped": sum(mapping_counts.values()), "counts": mapping_counts,
                      "relevant_by_factor": {factor: len(relevant.get(factor, [])) for factor in FACTORS}}
    gqa_original = gqa_pool_from_relevant(relevant, vocab, scenes, gqa_hashes, limit=200)
    if Counter(r["factor"] for r in gqa_original) != {"attribute": 200, "presence": 200, "spatial": 200}:
        raise ValueError("GQA frozen downstream selection reconstruction has a quota mismatch")
    tally = tally_pool(gqa_hashes, coco_hashes)
    downstream = verify_original_downstream(gqa_original, tally)
    replacements = tally + gqa_pool_from_relevant(relevant, vocab, scenes, gqa_hashes, limit=None)
    del relevant, scenes
    repaired, repair = repair_downstream_rows(
        static_rows=static, audit_rows=audit, downstream_rows=downstream, replacement_candidates=replacements)
    physical = [r["physical_image_id"] for r in repaired]
    if len(physical) != len(set(physical)):
        raise ValueError("downstream has duplicate physical images after repair")
    counts = Counter(r["factor"] for r in repaired)
    if counts != Counter({factor: 200 for factor in FACTORS}):
        raise ValueError("repaired downstream factor quotas failed: %s" % dict(counts))
    bon = validate_bon(repaired)
    audit_hashes, static_hashes, down_hashes = ({r["physical_image_id"] for r in audit},
                                                 {r["physical_image_id"] for r in static}, set(physical))
    overlap = {"audit_static": len(audit_hashes & static_hashes),
               "audit_downstream": len(audit_hashes & down_hashes),
               "static_downstream": len(static_hashes & down_hashes)}
    if any(overlap.values()):
        raise ValueError("final physical leakage gate failed: %s" % overlap)
    manifest = PHASE / "PHASE2_DOWNSTREAM_V2_PHYSICAL_DISJOINT_manifest.jsonl"
    atomic_jsonl(manifest, repaired)
    atomic_json(PHASE / "phase2_v2_physical_sha_manifests.json",
                {"audit": physical_rows(audit, "audit"), "static": physical_rows(static, "static"),
                 "downstream_v2": physical_rows(repaired, "downstream_v2")})
    atomic_json(PHASE / "phase2_v2_repair_receipt.json",
                {**repair, "status": "PASS", "algorithm": "PHASE2_DOWNSTREAM_V2_PHYSICAL_DISJOINT",
                 "static_manifest_sha256": STATIC_SHA256, "mapping": mapping_report})
    atomic_json(PHASE / "phase2_v2_zero_overlap_receipt.json",
                {"status": "PASS", "physical_image_id": "SHA256(raw image bytes)", "intersections": overlap,
                 "audit_items": len(audit), "static_items": len(static), "downstream_items": len(repaired)})
    atomic_json(PHASE / "phase2_v2_bon_structural_preflight_receipt.json", bon)
    final_hashes = {
        "gqa_acquisition_list_sha256": file_sha(gqa_list), "coco_acquisition_list_sha256": file_sha(coco_list),
        "static_manifest_sha256": file_sha(static_source), "downstream_v2_manifest_sha256": file_sha(manifest),
        "gqa_raw_verification_receipt_sha256": file_sha(PHASE / "autodl_gqa_raw_image_verification_receipt.json"),
        "coco_raw_verification_receipt_sha256": file_sha(PHASE / "autodl_coco_raw_image_verification_receipt.json")}
    atomic_json(PHASE / "phase2_v2_final_hashes.json", final_hashes)
    all_raw = defaultdict(list)
    for namespace, entries in (("gqa_vg", gqa_hashes), ("coco", coco_hashes)):
        for name, digest in entries.items():
            all_raw[digest].append("%s/%s" % (namespace, name))
    duplicates = {"gqa_vg_groups": len(gqa_duplicates), "coco_groups": len(coco_duplicates),
                  "combined_raw_groups": sum(len(v) > 1 for v in all_raw.values())}
    ready = {
        "status": "READY_FOR_PHASE2_GPU", "ready_for_phase2_gpu": True, "downstream_v2_manifest": str(manifest),
        "downstream_v2_manifest_sha256": final_hashes["downstream_v2_manifest_sha256"],
        "factor_counts": dict(counts), "physical_overlap_counts": overlap,
        "repaired_downstream_rows": repair["n_replaced"], "physical_duplicate_groups": duplicates,
        "runtime_seconds": round(time.time() - started, 3)}
    atomic_json(PHASE / "READY_FOR_PHASE2_GPU.json", ready)
    print(json.dumps(ready, sort_keys=True))
    return 0



# Low-memory source reconstruction: the AutoDL container is cgroup-limited to 2 GiB.
from lib.gqa_mapping import map_factor, structured_hard_negative


def iter_json_dict(path: Path):
    decoder, buffer, pos, eof = json.JSONDecoder(), "", 0, False
    with path.open("r", encoding="utf-8") as handle:
        def refill():
            nonlocal buffer, pos, eof
            if eof:
                return False
            buffer, pos = buffer[pos:] + handle.read(1 << 20), 0
            eof = not buffer or len(buffer) < (1 << 20)
            return bool(buffer)
        refill()
        while pos < len(buffer) and buffer[pos] in " \t\r\n":
            pos += 1
        if pos >= len(buffer) or buffer[pos] != "{":
            raise ValueError("expected top-level JSON object")
        pos += 1
        while True:
            while True:
                while pos < len(buffer) and buffer[pos] in " \t\r\n,":
                    pos += 1
                if pos >= len(buffer):
                    if not refill():
                        return
                    continue
                if buffer[pos] == "}":
                    return
                try:
                    key, pos = decoder.raw_decode(buffer, pos)
                    while pos >= len(buffer) or buffer[pos] in " \t\r\n":
                        if pos >= len(buffer):
                            if not refill():
                                raise ValueError("truncated JSON object")
                        else:
                            pos += 1
                    if buffer[pos] != ":":
                        raise ValueError("invalid JSON object separator")
                    pos += 1
                    while True:
                        if pos < len(buffer) and buffer[pos] in " \t\r\n":
                            pos += 1
                        elif pos >= len(buffer):
                            if not refill():
                                raise ValueError("truncated JSON value")
                        else:
                            break
                    break
                except json.JSONDecodeError:
                    if not refill():
                        raise
            while True:
                try:
                    value, pos = decoder.raw_decode(buffer, pos)
                    yield str(key), value
                    break
                except json.JSONDecodeError:
                    if not refill():
                        raise


def gqa_inputs() -> tuple[list[Path], list[Path]]:
    qdir, sdir = SOURCES / "gqa/questions", SOURCES / "gqa/sceneGraphs"
    qfiles = [qdir / "train_balanced_questions.json", qdir / "val_balanced_questions.json"]
    sfiles = sorted(sdir.glob("*sceneGraphs.json"))
    if not all(p.is_file() for p in qfiles) or not sfiles:
        raise FileNotFoundError("validated GQA balanced questions or scene graphs are unavailable")
    return qfiles, sfiles


def gqa_vocab_and_counts(qfiles: list[Path]) -> tuple[dict[str, list[str]], dict[str, int]]:
    factor_counts, answers = Counter(), defaultdict(Counter)
    for path in qfiles:
        for _qid, item in iter_json_dict(path):
            if not isinstance(item, dict):
                continue
            mapped = map_factor(item)
            if mapped is None:
                continue
            factor = mapped["factor"]
            factor_counts[factor] += 1
            answer = str(item.get("answer") or "")
            if answer:
                answers[factor][answer] += 1
    expected = json.loads((CODE / "manifests/gqa_factor_mapping_report.json").read_text(encoding="utf-8"))["counts"]
    actual = {factor: factor_counts.get(factor, 0) for factor in ("attribute", "presence", "spatial", "count")}
    if actual != expected:
        raise ValueError("GQA factor mapping counts differ from frozen report: %s" % actual)
    return {factor: [text for text, _n in answers[factor].most_common()] for factor in FACTORS}, actual


def gqa_scene_summary(ids: set[str], sfiles: list[Path]) -> dict[str, dict[str, Any]]:
    result = {}
    for path in sfiles:
        for image_id, scene in iter_json_dict(path):
            if image_id not in ids or not isinstance(scene, dict):
                continue
            objects = scene.get("objects") or {}
            if not isinstance(objects, dict):
                result[image_id] = {"objects": {}}
                continue
            result[image_id] = {"objects": {
                str(oid): {"name": obj.get("name") or obj.get("label"),
                           "attributes": list(obj.get("attributes") or [])}
                for oid, obj in objects.items() if isinstance(obj, dict)}}
    return result


def gqa_relevant_mapping(qfiles: list[Path], scenes: dict[str, dict[str, Any]], down_ids: set[str]) -> dict[str, list[dict[str, Any]]]:
    rows = defaultdict(list)
    for path in qfiles:
        for qid, item in iter_json_dict(path):
            if not isinstance(item, dict):
                continue
            mapped = map_factor(item)
            image_id = str(item.get("imageId") or item.get("image_id") or "")
            if mapped is None or image_id not in down_ids or not item.get("answer"):
                continue
            hard = structured_hard_negative(mapped["factor"], str(item["answer"]), item, scenes.get(image_id))
            rows[mapped["factor"]].append({
                "question_id": str(qid), "image_id": image_id, "question": item.get("question"),
                "answer": item.get("answer"), "factor": mapped["factor"],
                "mapping_source": mapped["mapping_source"], "mapping_confidence": mapped["confidence"], **hard})
    return rows


def gqa_pool_from_relevant(relevant: dict[str, list[dict[str, Any]]], vocab: dict[str, list[str]],
                           scenes: dict[str, dict[str, Any]], hashes: dict[str, str], limit: int | None) -> list[dict[str, Any]]:
    rng, items = random.Random(SEED), []
    for factor in FACTORS:
        pool = list(relevant.get(factor, []))
        pool.sort(key=lambda r: (r.get("mapping_confidence") != "high", str(r.get("question_id"))))
        rng.shuffle(pool)
        written = 0
        for row in pool:
            if limit is not None and written >= limit:
                break
            candidates = structured_candidates(factor, row, vocab=vocab[factor], scene=scenes.get(str(row["image_id"])))
            if len(candidates) < N_POOL:
                continue
            rng.shuffle(candidates)
            gold = str(row["answer"])
            gold_index = next((i for i, c in enumerate(candidates) if str(c.get("text")).strip().casefold() == gold.strip().casefold()), -1)
            if gold_index < 0:
                raise ValueError("GQA constructed pool lost gold: %s" % row["question_id"])
            item = {"item_id": "gqa_down:%s:%s" % (factor, row["question_id"]),
                    "source_item_id": "gqa_down:%s:%s" % (factor, row["question_id"]),
                    "question_id": row["question_id"], "image_id": row["image_id"], "factor": factor,
                    "question": row["question"], "gold": gold, "gold_answer": gold, "n_pool": N_POOL,
                    "candidates": candidates, "gold_index": gold_index,
                    "candidate_source": [c.get("source") for c in candidates],
                    "partial": False, "split": "downstream", "mapping_source": row.get("mapping_source")}
            item["image_path"], item["physical_image_id"] = resolve_gqa(item, hashes)
            items.append(item)
            written += 1
    return items


if __name__ == "__main__":
    raise SystemExit(main())
