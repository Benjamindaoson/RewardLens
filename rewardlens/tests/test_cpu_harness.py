#!/usr/bin/env python3
"""Unit tests for inference resume, parsers, stats, GQA split. Synthetic only."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from inference.adapters.dummy import DummyAdapter
from inference.common import load_items, resolve_image_path, run_items
from inference.metrics import compute_audit_metrics
from inference.parsers.ab_parser import parse_ab
from lib.gqa_mapping import map_factor, map_corpus, structured_hard_negative
from lib.gqa_pools import structured_candidates
from lib.jsonl_io import read_jsonl, write_jsonl
from models.registry import family_counts, load_registry, models_for_shard, models_for_worker
from scripts.merge_worker_results import merge_rows
from stats import accuracy_matched_pairs, cluster_bootstrap, factor_specificity, incremental_validity


class ParserTests(unittest.TestCase):
    def test_plain_ab(self):
        self.assertEqual(parse_ab("A"), "A")
        self.assertEqual(parse_ab("Answer: B"), "B")
        self.assertIsNone(parse_ab("UNPARSEABLE gibberish"))


class ResumeTests(unittest.TestCase):
    def test_skip_completed_and_failure_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out.jsonl")
            fail = os.path.join(tmp, "failures.jsonl")
            items = [
                {"item_id": "t0:base", "triplet_id": "t0", "factor": "count", "variant": "base", "question": "q0", "candidate_a": "2", "candidate_b": "3"},
                {"item_id": "t1:base", "triplet_id": "t1", "factor": "count", "variant": "base", "question": "FORCE_OOM", "candidate_a": "2", "candidate_b": "3"},
                {"item_id": "t2:base", "triplet_id": "t2", "factor": "count", "variant": "base", "question": "FORCE_PARSE", "candidate_a": "2", "candidate_b": "3"},
                {"item_id": "t3:base", "triplet_id": "t3", "factor": "count", "variant": "base", "question": "q3", "candidate_a": "2", "candidate_b": "3"},
            ]
            adapter = DummyAdapter()
            adapter.load_model()
            first = run_items(items=items[:2], adapter=adapter, model_id="dummy_cpu", out_jsonl=out, fail_jsonl=fail, parse_fn=parse_ab)
            self.assertEqual(first["ok"] + first["failed"], 2)
            second = run_items(items=items, adapter=adapter, model_id="dummy_cpu", out_jsonl=out, fail_jsonl=fail, parse_fn=parse_ab)
            self.assertEqual(second["skipped"], 2)
            rows = read_jsonl(out)
            self.assertEqual(len(rows), 4)
            ids = [r["item_id"] for r in rows]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertTrue(any(r["status"] == "oom" for r in rows))
            self.assertTrue(any(r["status"] == "parse_error" for r in rows))
            self.assertTrue(os.path.isfile(fail))
            adapter.cleanup()


class MetricsTests(unittest.TestCase):
    def test_pfc_joint_definition(self):
        gold = {"t": {"base": "A", "relevant": "B", "irrelevant": "A", "factor": "count"}}
        rows = [
            {"model_id": "m", "triplet_id": "t", "variant": "base", "parsed_preference": "A", "status": "ok", "factor": "count"},
            {"model_id": "m", "triplet_id": "t", "variant": "relevant", "parsed_preference": "B", "status": "ok", "factor": "count"},
            {"model_id": "m", "triplet_id": "t", "variant": "irrelevant", "parsed_preference": "A", "status": "ok", "factor": "count"},
        ]
        out = compute_audit_metrics(rows, gold)
        self.assertEqual(out[0]["PFC"], 1.0)
        self.assertEqual(out[0]["PSC"], 1.0)
        self.assertEqual(out[0]["PFC_cond"], 1.0)


class StatsTests(unittest.TestCase):
    def test_incremental_and_specificity_on_fixture(self):
        table = []
        families = ["qwen_vl", "gemma", "molmo", "specialized_vl_reward"]
        a_vals = [0.62, 0.71, 0.64, 0.69, 0.58, 0.73, 0.60, 0.68]
        pfc_vals = [0.31, 0.55, 0.40, 0.22, 0.61, 0.48, 0.35, 0.52]
        psc_vals = [0.70, 0.44, 0.63, 0.58, 0.41, 0.66, 0.50, 0.47]
        u_vals = [0.51, 0.66, 0.57, 0.49, 0.63, 0.70, 0.54, 0.61]
        n = 0
        for fam in families:
            for _k in range(2):
                table.append(
                    {
                        "model_id": "m%d" % n,
                        "family": fam,
                        "factor": "count",
                        "A": a_vals[n],
                        "PFC": pfc_vals[n],
                        "PSC": psc_vals[n],
                        "U": u_vals[n],
                    }
                )
                n += 1
        inc = incremental_validity(table)
        self.assertGreaterEqual(inc["n_families"], 4)
        pairs = accuracy_matched_pairs(table)
        self.assertIn("count", pairs)
        matrix = []
        for af in ("count", "attribute", "presence", "spatial"):
            for df in ("count", "attribute", "presence", "spatial"):
                matrix.append({"audit_factor": af, "downstream_factor": df, "score": 0.8 if af == df else 0.2})
        spec = factor_specificity(matrix)
        self.assertGreater(spec["diagonal_mean"], spec["off_diagonal_mean"])
        self.assertGreater(
            spec["column_standardized"]["diagonal_mean"],
            spec["column_standardized"]["off_diagonal_mean"],
        )
        boot = cluster_bootstrap(table, stat_fn=lambda rows: sum(r["U"] for r in rows) / len(rows), n_boot=50)
        self.assertEqual(len(boot["ci95"]), 2)

    def test_resolve_image_path_basename_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            real = os.path.join(td, "2410408.jpg")
            with open(real, "wb") as handle:
                handle.write(b"jpg")
            got = resolve_image_path({"image_path": r"D:\missing\VG_100K\2410408.jpg"}, images_root=td)
            self.assertEqual(os.path.normpath(got), os.path.normpath(real))


class GqaMappingTests(unittest.TestCase):
    def test_program_not_keyword_only(self):
        count_item = {
            "question": "How many apples are there?",
            "answer": "3",
            "types": {"structural": "query", "semantic": "obj", "detailed": "count"},
            "semantic": [{"operation": "select", "argument": "apple"}, {"operation": "count", "argument": "?"}],
        }
        attr_item = {
            "question": "What color is the chair?",
            "answer": "red",
            "types": {"structural": "query", "semantic": "attr", "detailed": "attrColor"},
            "semantic": [{"operation": "select", "argument": "chair"}, {"operation": "queryAttr", "argument": "color"}],
        }
        spatial_item = {
            "question": "Is the cup to the left of the plate?",
            "answer": "yes",
            "types": {"structural": "verify", "semantic": "rel", "detailed": "verifyRel"},
            "semantic": [
                {"operation": "select", "argument": "cup"},
                {"operation": "relate", "argument": "to the left of, plate"},
                {"operation": "verifyRel", "argument": "left"},
            ],
        }
        presence_item = {
            "question": "Is there a bicycle?",
            "answer": "no",
            "types": {"structural": "verify", "semantic": "obj", "detailed": "exist"},
            "semantic": [{"operation": "select", "argument": "bicycle"}, {"operation": "exist", "argument": "?"}],
        }
        self.assertEqual(map_factor(count_item)["factor"], "count")
        self.assertEqual(map_factor(attr_item)["factor"], "attribute")
        self.assertEqual(map_factor(spatial_item)["factor"], "spatial")
        self.assertEqual(map_factor(presence_item)["factor"], "presence")
        self.assertNotEqual(map_factor(count_item)["mapping_source"], "keyword")
        self.assertEqual(structured_hard_negative("count", "3")["hard_negative"], "4")
        self.assertEqual(structured_hard_negative("presence", "no")["hard_negative"], "yes")

    def test_image_disjoint_split_assert(self):
        questions = {}
        for i in range(40):
            factor_items = [
                ("count", "How many x?", str(i % 5), [{"operation": "count", "argument": "?"}]),
                ("attribute", "What color?", "red", [{"operation": "queryAttr", "argument": "color"}]),
                ("spatial", "left of?", "yes", [{"operation": "relate", "argument": "to the left of, y"}]),
                ("presence", "Is there z?", "yes", [{"operation": "exist", "argument": "?"}]),
            ]
            kind, q, a, sem = factor_items[i % 4]
            questions[str(i)] = {
                "questionId": str(i),
                "imageId": "img_%02d" % (i // 2),
                "question": q,
                "answer": a,
                "types": {"detailed": kind if kind != "attribute" else "attrColor", "semantic": "attr" if kind == "attribute" else "obj"},
                "semantic": sem,
            }
        mapped, report = map_corpus(questions, {}, split_name="synth")
        self.assertGreater(report["n_mapped"], 0)
        ids = sorted({r["image_id"] for r in mapped})
        static = [i for j, i in enumerate(ids) if j % 2 == 0]
        down = [i for j, i in enumerate(ids) if j % 2 == 1]
        self.assertEqual(set(static) & set(down), set())


class RegistryTests(unittest.TestCase):
    def test_eight_primary_four_families_two_workers(self):
        reg = load_registry()
        primary = [m for m in reg["models"] if m.get("fast_track_primary")]
        self.assertGreaterEqual(len(primary), 6)
        self.assertLessEqual(len(primary), 8)
        self.assertGreaterEqual(len(family_counts(reg)), 4)
        w0 = models_for_worker(0, reg)
        w1 = models_for_worker(1, reg)
        self.assertEqual(len(w0), 4)
        self.assertEqual(len(w1), 4)
        self.assertTrue(all(m["status"] == "UNTESTED" for m in primary))


class HarnessHardeningTests(unittest.TestCase):
    def test_partial_jsonl_recovery_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out.jsonl")
            fail = os.path.join(tmp, "failures.jsonl")
            with open(out, "w", encoding="utf-8") as handle:
                handle.write(json.dumps({"item_id": "t0:base", "status": "ok", "parsed_preference": "A"}) + "\n")
                handle.write('{"item_id": "truncated"')
            items = [
                {"item_id": "t0:base", "triplet_id": "t0", "factor": "count", "variant": "base", "question": "q0", "candidate_a": "2", "candidate_b": "3"},
                {"item_id": "t1:base", "triplet_id": "t1", "factor": "count", "variant": "base", "question": "q1", "candidate_a": "2", "candidate_b": "3"},
            ]
            adapter = DummyAdapter()
            adapter.load_model()
            result = run_items(items=items, adapter=adapter, model_id="dummy_cpu", out_jsonl=out, fail_jsonl=fail, parse_fn=parse_ab)
            self.assertEqual(result["skipped"], 1)
            self.assertEqual(result["ok"] + result["failed"], 1)
            ids = [r["item_id"] for r in read_jsonl(out)]
            self.assertIn("t0:base", ids)
            self.assertIn("t1:base", ids)
            adapter.cleanup()

    def test_duplicate_item_protection(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out.jsonl")
            fail = os.path.join(tmp, "failures.jsonl")
            items = [
                {"item_id": "dup", "triplet_id": "t", "factor": "count", "variant": "base", "question": "q", "candidate_a": "2", "candidate_b": "3"},
                {"item_id": "dup", "triplet_id": "t", "factor": "count", "variant": "base", "question": "q", "candidate_a": "2", "candidate_b": "3"},
            ]
            adapter = DummyAdapter()
            adapter.load_model()
            run_items(items=items, adapter=adapter, model_id="dummy_cpu", out_jsonl=out, fail_jsonl=fail, parse_fn=parse_ab)
            rows = read_jsonl(out)
            self.assertEqual(len(rows), 1)
            adapter.cleanup()

    def test_parse_model_error_missing_image_invalid_pool(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out.jsonl")
            fail = os.path.join(tmp, "failures.jsonl")
            missing = os.path.join(tmp, "nope.png")
            items = [
                {"item_id": "p", "triplet_id": "t", "factor": "count", "variant": "base", "question": "FORCE_PARSE", "candidate_a": "2", "candidate_b": "3"},
                {"item_id": "e", "triplet_id": "t", "factor": "count", "variant": "base", "question": "FORCE_ERROR", "candidate_a": "2", "candidate_b": "3"},
                {"item_id": "m", "triplet_id": "t", "factor": "count", "variant": "base", "question": "q", "candidate_a": "2", "candidate_b": "3", "image_path": missing},
                {
                    "item_id": "c",
                    "triplet_id": "t",
                    "factor": "count",
                    "variant": "base",
                    "question": "q",
                    "candidate_a": "2",
                    "candidate_b": "3",
                    "n_pool": 8,
                    "candidates": [{"text": "2"}, {"text": "3"}],
                },
            ]
            adapter = DummyAdapter()
            adapter.load_model()
            run_items(items=items, adapter=adapter, model_id="dummy_cpu", out_jsonl=out, fail_jsonl=fail, parse_fn=parse_ab)
            rows = {r["item_id"]: r for r in read_jsonl(out)}
            self.assertEqual(rows["p"]["status"], "parse_error")
            self.assertEqual(rows["e"]["status"], "error")
            self.assertEqual(rows["m"]["status"], "error")
            self.assertEqual(rows["c"]["status"], "error")
            adapter.cleanup()

    def test_manifest_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                load_items(os.path.join(tmp, "missing.jsonl"))

    def test_worker_shard_and_merge(self):
        reg = load_registry()
        s0 = models_for_shard(0, 3, reg)
        s1 = models_for_shard(1, 3, reg)
        s2 = models_for_shard(2, 3, reg)
        ids = [m["model_id"] for m in s0 + s1 + s2]
        primary = [m["model_id"] for m in reg["models"] if m.get("fast_track_primary")]
        self.assertEqual(sorted(ids), sorted(primary))
        with tempfile.TemporaryDirectory() as tmp:
            a = os.path.join(tmp, "w0.jsonl")
            b = os.path.join(tmp, "w1.jsonl")
            write_jsonl(a, [{"item_id": "i1", "model_id": "m", "parsed_preference": "A", "status": "ok"}])
            write_jsonl(
                b,
                [
                    {"item_id": "i2", "model_id": "m", "parsed_preference": "B", "status": "ok"},
                    {"item_id": "i1", "model_id": "m", "parsed_preference": "B", "status": "ok"},
                ],
            )
            rows, report = merge_rows([a, b])
            self.assertEqual(report["n_merged"], 2)
            self.assertEqual(report["n_duplicates"], 1)
            self.assertEqual(report["n_conflicts"], 1)

    def test_gqa_pool_fill_count(self):
        row = {"answer": "3", "hard_negative": "4"}
        cands = structured_candidates("count", row, vocab=["5", "6", "7"], scene=None)
        self.assertEqual(len(cands), 8)
        self.assertEqual(cands[0]["text"], "3")


if __name__ == "__main__":
    unittest.main()
