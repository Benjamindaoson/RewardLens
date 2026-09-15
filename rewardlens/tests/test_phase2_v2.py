from __future__ import annotations

import hashlib
import unittest

from inference.bon import (
    candidate_uid,
    copeland_select,
    derive_subset_selections,
    nested_candidate_sets,
    oriented_pair,
    pair_count,
)


def _pool() -> dict:
    return {
        "item_id": "pool:example",
        "gold_index": 3,
        "gold_answer": "gold",
        "candidates": [
            {"text": "d0"},
            {"text": "d1"},
            {"text": "d2"},
            {"text": "gold"},
            {"text": "d4"},
            {"text": "d5"},
            {"text": "d6"},
            {"text": "d7"},
        ],
    }


class CandidateSubsetTests(unittest.TestCase):
    def test_fallback_uid_uses_original_index_and_text(self) -> None:
        self.assertEqual(candidate_uid({"text": "alpha"}, 7), "index:7|text:alpha")

    def test_nested_sets_are_gold_containing_and_deterministic(self) -> None:
        pool = _pool()
        first = nested_candidate_sets(pool)
        second = nested_candidate_sets(pool)
        self.assertEqual(first, second)
        self.assertEqual(set(first[2]), set(first[2]) & set(first[4]))
        self.assertEqual(set(first[4]), set(first[4]) & set(first[8]))
        gold_uid = candidate_uid(pool["candidates"][3], 3)
        self.assertIn(gold_uid, first[2])
        self.assertIn(gold_uid, first[4])
        self.assertIn(gold_uid, first[8])
        self.assertEqual(len(first[2]), 2)
        self.assertEqual(len(first[4]), 4)
        self.assertEqual(len(first[8]), 8)

    def test_invalid_pool_without_exactly_one_gold_fails(self) -> None:
        pool = _pool()
        pool["candidates"][4]["text"] = "gold"
        with self.assertRaises(ValueError):
            nested_candidate_sets(pool)


class PairProtocolTests(unittest.TestCase):
    def test_pair_orientation_is_order_independent_and_hash_defined(self) -> None:
        pool_id = "pool:example"
        left = "index:1|text:left"
        right = "index:2|text:right"
        got = oriented_pair(pool_id, left, right)
        self.assertEqual(got, oriented_pair(pool_id, right, left))
        digest = hashlib.sha256(
            ("RewardLens-PairOrientation-v1|" + pool_id + "|" + "|".join(sorted((left, right)))).encode("utf-8")
        ).hexdigest()
        expected = (left, right) if int(digest[-1], 16) % 2 == 0 else (right, left)
        self.assertEqual(got, expected)

    def test_pair_count(self) -> None:
        self.assertEqual(pair_count(2), 1)
        self.assertEqual(pair_count(4), 6)
        self.assertEqual(pair_count(8), 28)


class CopelandTests(unittest.TestCase):
    def test_semantic_abstention_awards_half_to_both(self) -> None:
        result = copeland_select(
            pool_id="pool:abstain",
            candidate_uids=["a", "b"],
            pair_outcomes=[{"left_uid": "a", "right_uid": "b", "outcome": "abstain"}],
        )
        self.assertEqual(result["scores"], {"a": 0.5, "b": 0.5})
        self.assertEqual(result["semantic_abstentions"], 1)
        expected = min(
            ("a", "b"),
            key=lambda uid: hashlib.sha256(("RewardLens-BoN-Tie-v1|pool:abstain|" + uid).encode("utf-8")).hexdigest(),
        )
        self.assertEqual(result["selected_uid"], expected)

    def test_complete_three_candidate_graph_selects_max_copeland(self) -> None:
        result = copeland_select(
            pool_id="pool:three",
            candidate_uids=["a", "b", "c"],
            pair_outcomes=[
                {"left_uid": "a", "right_uid": "b", "outcome": "left"},
                {"left_uid": "a", "right_uid": "c", "outcome": "left"},
                {"left_uid": "b", "right_uid": "c", "outcome": "right"},
            ],
        )
        self.assertEqual(result["selected_uid"], "a")
        self.assertEqual(result["scores"]["a"], 2.0)
        self.assertEqual(result["scores"]["b"], 0.0)
        self.assertEqual(result["scores"]["c"], 1.0)


class InducedGraphTests(unittest.TestCase):
    def test_n2_n4_n8_are_derived_from_one_complete_n8_graph(self) -> None:
        pool = _pool()
        uids = nested_candidate_sets(pool)[8]
        gold_uid = candidate_uid(pool["candidates"][3], 3)
        outcomes = []
        for index, left in enumerate(uids):
            for right in uids[index + 1 :]:
                if left == gold_uid:
                    outcome = "left"
                elif right == gold_uid:
                    outcome = "right"
                else:
                    outcome = "tie"
                outcomes.append({"left_uid": left, "right_uid": right, "outcome": outcome})
        result = derive_subset_selections(pool, outcomes)
        self.assertEqual(len(outcomes), 28)
        self.assertEqual(result[2]["selected_uid"], gold_uid)
        self.assertEqual(result[4]["selected_uid"], gold_uid)
        self.assertEqual(result[8]["selected_uid"], gold_uid)
        self.assertTrue(result[2]["success"])
        self.assertTrue(result[4]["success"])
        self.assertTrue(result[8]["success"])


if __name__ == "__main__":
    unittest.main()


class PhysicalRepairTests(unittest.TestCase):
    def test_repair_retains_disjoint_rows_and_hash_selects_same_carrier_replacement(self) -> None:
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from scripts.build_phase2_downstream_v2 import repair_downstream_rows

        def write(root: Path, name: str, data: bytes) -> str:
            path = root / name
            path.write_bytes(data)
            return str(path)

        def row(item_id: str, image_path: str, *, factor: str = "count", dataset: str = "tallyqa") -> dict:
            return {
                "item_id": item_id,
                "image_path": image_path,
                "image_id": item_id,
                "factor": factor,
                "dataset": dataset,
                "question": item_id,
                "gold_answer": "1",
                "gold_index": 0,
                "n_pool": 8,
                "candidates": [
                    {"text": "1", "type": "gold"},
                    {"text": "2"}, {"text": "3"}, {"text": "4"},
                    {"text": "5"}, {"text": "6"}, {"text": "7"}, {"text": "8"},
                ],
            }

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            static = row("static", write(root, "static.jpg", b"static"))
            audit = row("audit", write(root, "audit.jpg", b"audit"))
            kept = row("keep", write(root, "keep.jpg", b"keep"))
            conflict = row("conflict", static["image_path"])
            first = row("candidate-z", write(root, "candidate-z.jpg", b"z"))
            second = row("candidate-a", write(root, "candidate-a.jpg", b"a"))
            first["source_item_id"] = "candidate-z"
            second["source_item_id"] = "candidate-a"
            repaired, receipt = repair_downstream_rows(
                static_rows=[static],
                audit_rows=[audit],
                downstream_rows=[kept, conflict],
                replacement_candidates=[first, second],
            )
            selected = min(
                (first, second),
                key=lambda item: hashlib.sha256(
                    (
                        "RewardLens-Phase2-PhysicalRepair-v1|count|tallyqa|"
                        + item["source_item_id"]
                        + "|"
                        + hashlib.sha256(Path(item["image_path"]).read_bytes()).hexdigest()
                    ).encode("utf-8")
                ).hexdigest(),
            )
            self.assertEqual(repaired[0], kept)
            self.assertEqual(repaired[1]["item_id"], selected["item_id"])
            self.assertEqual(receipt["n_replaced"], 1)
            self.assertEqual(receipt["physical_intersections"]["static_downstream"], 0)
            self.assertEqual(receipt["physical_intersections"]["audit_downstream"], 0)


class PairOutcomeTests(unittest.TestCase):
    def test_parse_failure_is_one_semantic_abstention(self) -> None:
        from inference.bon import pair_outcome

        self.assertEqual(
            pair_outcome("left", "right", None),
            {"left_uid": "left", "right_uid": "right", "outcome": "abstain"},
        )
        self.assertEqual(
            pair_outcome("left", "right", "A"),
            {"left_uid": "left", "right_uid": "right", "outcome": "left"},
        )
        self.assertEqual(
            pair_outcome("left", "right", "B"),
            {"left_uid": "left", "right_uid": "right", "outcome": "right"},
        )


class PairwiseAdapterExecutionTests(unittest.TestCase):
    def test_complete_graph_makes_28_calls_and_never_retries_parse_failure(self) -> None:
        from inference.bon import evaluate_pairwise_graph

        class OneParseFailureAdapter:
            def __init__(self) -> None:
                self.calls = 0

            def prepare_inputs(self, **kwargs):
                return kwargs

            def judge(self, prepared):
                self.calls += 1
                if self.calls == 1:
                    return {"raw_output": "not an answer", "parsed_preference": None}
                return {"raw_output": "A", "parsed_preference": "A"}

        adapter = OneParseFailureAdapter()
        rows = evaluate_pairwise_graph(_pool(), adapter, image_path="/tmp/image.jpg")
        self.assertEqual(adapter.calls, 28)
        self.assertEqual(len(rows), 28)
        self.assertEqual(sum(row["outcome"] == "abstain" for row in rows), 1)
        self.assertEqual(sum(row["status"] == "semantic_abstention" for row in rows), 1)


class ScalarGraphTests(unittest.TestCase):
    def test_scalar_scores_create_the_same_complete_graph_with_exact_ties(self) -> None:
        from inference.bon import scalar_pair_graph

        pool = _pool()
        uids = nested_candidate_sets(pool)[8]
        scores = {uid: float(index) for index, uid in enumerate(uids)}
        scores[uids[0]] = scores[uids[1]]
        rows = scalar_pair_graph(pool, scores)
        self.assertEqual(len(rows), 28)
        tied = [
            row for row in rows
            if {row["left_uid"], row["right_uid"]} == {uids[0], uids[1]}
        ]
        self.assertEqual(tied[0]["outcome"], "tie")


class PairwiseResumeTests(unittest.TestCase):
    def test_completed_pair_is_skipped_on_resume(self) -> None:
        from inference.bon import evaluate_pairwise_graph

        class AlwaysA:
            def __init__(self) -> None:
                self.calls = 0

            def prepare_inputs(self, **kwargs):
                return kwargs

            def judge(self, prepared):
                self.calls += 1
                return {"raw_output": "A", "parsed_preference": "A"}

        first = AlwaysA()
        full = evaluate_pairwise_graph(_pool(), first, image_path="/tmp/image.jpg")
        resumed = AlwaysA()
        rows = evaluate_pairwise_graph(
            _pool(),
            resumed,
            image_path="/tmp/image.jpg",
            completed_pair_keys={full[0]["pair_key"]},
        )
        self.assertEqual(first.calls, 28)
        self.assertEqual(resumed.calls, 27)
        self.assertEqual(len(rows), 27)


class BestOfNRunnerTests(unittest.TestCase):
    def test_runner_writes_one_complete_graph_and_three_induced_selections(self) -> None:
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from inference.adapters.dummy import DummyAdapter
        from inference.run_bon import run_bon_items
        from lib.jsonl_io import read_jsonl

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "image.jpg"
            image.write_bytes(b"not-decoded-by-dummy")
            pool = _pool()
            pool["image_path"] = str(image)
            adapter = DummyAdapter()
            adapter.load_model()
            summary = run_bon_items(
                items=[pool],
                adapter=adapter,
                model_id="dummy_cpu",
                pair_out_jsonl=str(root / "pairs.jsonl"),
                selection_out_jsonl=str(root / "selections.jsonl"),
                fail_jsonl=str(root / "failures.jsonl"),
            )
            adapter.cleanup()
            pairs = read_jsonl(str(root / "pairs.jsonl"))
            selections = read_jsonl(str(root / "selections.jsonl"))
            self.assertEqual(summary["pairs_written"], 28)
            self.assertEqual(summary["pools_completed"], 1)
            self.assertEqual(len(pairs), 28)
            self.assertEqual([row["n"] for row in selections], [2, 4, 8])
            self.assertTrue(all(row["status"] == "ok" for row in selections))


class SkyworkScalarAdapterTests(unittest.TestCase):
    def test_public_scalar_method_delegates_to_native_score_once(self) -> None:
        from inference.adapters.skywork_reward import SkyworkRewardAdapter

        adapter = SkyworkRewardAdapter(model_id="skywork", checkpoint="/unused")
        calls = []
        adapter._score = lambda **kwargs: calls.append(kwargs) or 0.75
        self.assertEqual(
            adapter.score_candidate(image_path="image.jpg", question="what?", candidate="answer"),
            0.75,
        )
        self.assertEqual(calls, [{"image_path": "image.jpg", "question": "what?", "answer": "answer"}])


class DownstreamMetricTests(unittest.TestCase):
    def test_utility_groups_frozen_selections_by_model_factor_and_n(self) -> None:
        from inference.metrics import downstream_utility_from_selections

        rows = [
            {"status": "ok", "model_id": "m", "factor": "count", "n": 8, "utility_success": True, "semantic_abstentions": 2, "n_pairs": 28},
            {"status": "ok", "model_id": "m", "factor": "count", "n": 8, "utility_success": False, "semantic_abstentions": 0, "n_pairs": 28},
            {"status": "ok", "model_id": "m", "factor": "count", "n": 4, "utility_success": True, "semantic_abstentions": 1, "n_pairs": 6},
            {"status": "error", "model_id": "m", "factor": "count", "n": 8, "utility_success": True},
        ]
        got = downstream_utility_from_selections(rows)
        self.assertEqual(
            got,
            [
                {
                    "model_id": "m",
                    "factor": "count",
                    "N": 4,
                    "U": 1.0,
                    "n_pools": 1,
                    "semantic_abstention_rate": 1 / 6,
                    "utility_definition": "selected_candidate == gold_candidate",
                },
                {
                    "model_id": "m",
                    "factor": "count",
                    "N": 8,
                    "U": 0.5,
                    "n_pools": 2,
                    "semantic_abstention_rate": 2 / 56,
                    "utility_definition": "selected_candidate == gold_candidate",
                },
            ],
        )


class Phase2MergeTests(unittest.TestCase):
    def test_primary_merge_uses_static_a_audit_dependencies_and_n8_utility(self) -> None:
        from inference.phase2_analysis import merge_primary_table

        got = merge_primary_table(
            audit_rows=[{"model_id": "m", "factor": "count", "PFC": 0.2, "PSC": 0.7}],
            static_rows=[{"model_id": "m", "factor": "count", "A": 0.6, "n": 200}],
            utility_rows=[
                {"model_id": "m", "factor": "count", "N": 2, "U": 0.9, "n_pools": 200},
                {"model_id": "m", "factor": "count", "N": 8, "U": 0.5, "n_pools": 200},
            ],
            families={"m": "family"},
        )
        self.assertEqual(
            got,
            [{
                "model_id": "m", "family": "family", "factor": "count", "dataset": "tallyqa",
                "A": 0.6, "PFC": 0.2, "PSC": 0.7, "U": 0.5,
                "n_static": 200, "n_downstream": 200, "primary_n": 8,
            }],
        )


class ManualImageDeliveryTests(unittest.TestCase):
    def test_zip_materialization_and_verification_preserve_raw_bytes(self) -> None:
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from zipfile import ZipFile

        from scripts.phase2_image_handoff import materialize_required_images, verify_required_images

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            required = root / "required.txt"
            required.write_text("1\n2\n3\n", encoding="utf-8")
            archive = root / "images.zip"
            with ZipFile(archive, "w") as z:
                z.writestr("VG_100K/1.jpg", b"same-raw-bytes")
                z.writestr("VG_100K_2/2.jpg", b"same-raw-bytes")
                z.writestr("README.txt", b"unexpected")
            out = root / "images"
            extracted = materialize_required_images(str(required), str(archive), str(out))
            self.assertEqual(extracted["found_ids"], ["1", "2"])
            self.assertEqual(extracted["missing_ids"], ["3"])
            self.assertEqual(len(extracted["byte_hash_manifest"]), 2)
            self.assertEqual((out / "1.jpg").read_bytes(), b"same-raw-bytes")
            verified = verify_required_images(str(required), str(out))
            self.assertEqual(verified["found_ids"], ["1", "2"])
            self.assertEqual(verified["missing_ids"], ["3"])
            self.assertEqual(len(verified["duplicate_physical_sha256"]), 1)
            self.assertEqual(verified["unexpected_files"], [])


    def test_directory_materialization_accepts_extracted_images(self) -> None:
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from scripts.phase2_image_handoff import materialize_required_images

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            required = root / "required.txt"
            required.write_text("4\n5\n", encoding="utf-8")
            source = root / "source"
            (source / "VG_100K").mkdir(parents=True)
            (source / "VG_100K" / "4.jpg").write_bytes(b"four")
            out = root / "images"
            receipt = materialize_required_images(str(required), str(source), str(out))
            self.assertEqual(receipt["found_ids"], ["4"])
            self.assertEqual(receipt["missing_ids"], ["5"])
            self.assertEqual((out / "4.jpg").read_bytes(), b"four")


class CocoImageHandoffTests(unittest.TestCase):
    def test_coco_manifest_resolves_canonical_archive_name(self) -> None:
        import json
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from zipfile import ZipFile

        from scripts.phase2_image_handoff import materialize_required_images, verify_required_images

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            required = root / "required.txt"
            image_id = "000000000049"
            filename = "COCO_train2014_000000000049.jpg"
            required.write_text("%s\n" % image_id, encoding="utf-8")
            names = root / "names.json"
            names.write_text(
                json.dumps({"expected_canonical_filename_by_id": {image_id: filename}}),
                encoding="utf-8",
            )
            archive = root / "train2014.zip"
            with ZipFile(archive, "w") as z:
                z.writestr("train2014/%s" % filename, b"raw-coco-bytes")
            out = root / "images"
            extracted = materialize_required_images(
                str(required), str(archive), str(out), filename_manifest=str(names)
            )
            self.assertEqual(extracted["found_ids"], [image_id])
            self.assertEqual((out / filename).read_bytes(), b"raw-coco-bytes")
            verified = verify_required_images(
                str(required), str(out), filename_manifest=str(names)
            )
            self.assertEqual(
                verified["byte_hash_manifest"][0]["canonical_filename"], filename
            )


class CocoAcquisitionTests(unittest.TestCase):
    def test_reconstruction_uses_tallyqa_path_for_coco_split_and_filename(self) -> None:
        import json
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from lib.tallyqa import split_bucket
        from scripts.freeze_phase2_required_coco_ids import build_required_coco_acquisition

        def downstream_stem(split: str, start: int) -> str:
            for value in range(start, start + 10000):
                stem = "COCO_%s_%012d" % (split, value)
                if split_bucket("coco:%s" % stem) == "downstream":
                    return stem
            raise AssertionError("fixture did not find downstream item")

        with TemporaryDirectory() as tmp:
            annotations = Path(tmp) / "annotations"
            annotations.mkdir()
            train_stem = downstream_stem("train2014", 0)
            val_stem = downstream_stem("val2014", 10000)
            train_id = train_stem.rsplit("_", 1)[1]
            val_id = val_stem.rsplit("_", 1)[1]
            (annotations / "train.json").write_text(
                json.dumps([
                    {
                        "question_id": 1,
                        "question": "How many birds are there?",
                        "answer": 2,
                        "image_id": 1,
                        "image": "train2014/%s.jpg" % train_stem,
                    },
                    {
                        "question_id": 2,
                        "question": "How many dogs are there?",
                        "answer": 1,
                        "image_id": 2,
                        "image": "val2014/%s.jpg" % val_stem,
                    },
                ]),
                encoding="utf-8",
            )

            result = build_required_coco_acquisition(str(annotations), availability_roots=[])
            self.assertEqual(result["ids"], sorted([train_id, val_id]))
            self.assertEqual(result["receipt"]["counts_by_coco_split"], {"train2014": 1, "val2014": 1})
            self.assertEqual(result["receipt"]["other_coco_splits"], {})
            self.assertEqual(
                result["receipt"]["expected_canonical_filename_by_id"][train_id],
                "%s.jpg" % train_stem,
            )
            self.assertEqual(
                result["receipt"]["expected_canonical_filename_by_id"][val_id],
                "%s.jpg" % val_stem,
            )


class ImageHandoffProgressTests(unittest.TestCase):
    def test_progress_disabled_writes_nothing(self) -> None:
        import io

        from scripts.phase2_image_handoff import ProgressUI

        ui = ProgressUI("off", source="fixture.zip", target=2, stream=io.StringIO(), is_tty=True)
        ui.stage("Scan archive", 2)
        ui.update(1)
        ui.close()
        self.assertEqual(ui.stream.getvalue(), "")

    def test_non_tty_uses_periodic_plain_text(self) -> None:
        import io

        from scripts.phase2_image_handoff import ProgressUI

        now = [0.0]
        stream = io.StringIO()
        ui = ProgressUI(
            "auto", source="fixture.zip", target=20, stream=stream,
            is_tty=False, clock=lambda: now[0],
        )
        ui.stage("extract", 20)
        now[0] = 2.0
        ui.update(5)
        self.assertIn("[extract] 5/20 25.0%", stream.getvalue())
        self.assertNotIn("\x1b[", stream.getvalue())
        ui.close()

    def test_progress_calculates_rate_eta_and_zero_total(self) -> None:
        from scripts.phase2_image_handoff import _format_duration, _progress_stats

        self.assertEqual(_format_duration(46), "00:46")
        self.assertEqual(_format_duration(3661), "01:01:01")
        pct, rate, eta = _progress_stats(25, 100, 5.0)
        self.assertEqual(pct, 25.0)
        self.assertEqual(rate, 5.0)
        self.assertEqual(eta, 15.0)
        self.assertEqual(_progress_stats(0, 0, 0.0), (100.0, 0.0, None))


class GqaVgCanonicalizationTests(unittest.TestCase):
    def test_tallyqa_vg_namespace_resolves_to_delivered_gqa_filename(self) -> None:
        from scripts.run_phase2_v2_preflight import gqa_raw_filename

        self.assertEqual(
            gqa_raw_filename({"image_id": "vg:2404460", "source_id": "2404460"}),
            "2404460.jpg",
        )
        self.assertEqual(gqa_raw_filename({"image_id": "vg:2404460"}), "2404460.jpg")
