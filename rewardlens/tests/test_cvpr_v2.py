"""Pure synthetic unit tests; never count as scientific evaluation."""
import copy
import tempfile
import unittest
from pathlib import Path

from rewardlens.cvpr_v2.demo import make_demo
from rewardlens.cvpr_v2.cli import _jsonl
from rewardlens.cvpr_v2.protocol import ProtocolError, validate_records
from rewardlens.cvpr_v2.metrics import audit_summary, matched_pairs, shared_support_gaps
from rewardlens.cvpr_v2.report import render_html


class CvprV2Test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        make_demo(Path(self.tmp.name))
        self.audit = _jsonl(str(Path(self.tmp.name) / "audit_synthetic.jsonl"))
        self.static = _jsonl(str(Path(self.tmp.name) / "static_synthetic.jsonl"))

    def test_valid_and_conditional_metrics(self):
        rows = validate_records(self.audit)
        a = audit_summary(rows)
        self.assertEqual(len(a), 4)  # 2 models x development/test
        demo2_dev = next(x for x in a if x["model_id"] == "demo_judge_2" and x["split"] == "development")
        demo2_test = next(x for x in a if x["model_id"] == "demo_judge_2" and x["split"] == "test")
        self.assertEqual(demo2_dev["ra"], 0.0)
        self.assertEqual(demo2_test["ra"], 1.0)
        self.assertEqual(demo2_dev["ii"], 1.0)
        self.assertEqual(demo2_dev["n_base_a"], 2)
        self.assertEqual(demo2_dev["n_base_b"], 2)

    def test_static_matching_and_shared_support(self):
        pairs = matched_pairs(self.static)
        self.assertEqual(len(pairs), 2)
        shared = shared_support_gaps(validate_records(self.audit), pairs)
        dev = next(x for x in shared if x["split"] == "development")
        self.assertEqual(dev["n_shared_base_correct"], 4)
        self.assertEqual(dev["delta_ra_shared"], 1.0)
        self.assertEqual(dev["only_a_relevant_correct"], 4)
        self.assertEqual(dev["both_relevant_correct"], 0)

    def test_leakage_rejected(self):
        rows = copy.deepcopy(self.audit)
        rows[12]["split"] = "test"
        with self.assertRaises(ProtocolError):
            validate_records(rows)

    def test_wrong_gold_contract_rejected(self):
        rows = copy.deepcopy(self.audit)
        row = next(x for x in rows if x["model_id"] == "demo_judge_1" and x["triplet_id"] == "synthetic_0" and x["variant"] == "relevant")
        row["gold"] = "A"
        with self.assertRaises(ProtocolError):
            validate_records(rows)

    def test_question_change_rejected(self):
        rows = copy.deepcopy(self.audit)
        row = next(x for x in rows if x["variant"] == "irrelevant")
        row["question"] = "Different query"
        with self.assertRaises(ProtocolError):
            validate_records(rows)

    def test_model_inconsistent_ground_truth_rejected(self):
        rows = copy.deepcopy(self.audit)
        row = next(x for x in rows if x["model_id"] == "demo_judge_2" and x["variant"] == "base")
        row["gold"] = "B"
        with self.assertRaises(ProtocolError):
            validate_records(rows)

    def test_missing_or_unvalidated_rejected(self):
        rows = copy.deepcopy(self.audit)
        rows[0]["semantic_validation_passed"] = False
        with self.assertRaises(ProtocolError):
            validate_records(rows)
        with self.assertRaises(ProtocolError):
            validate_records(self.audit[:-1])

    def test_abstain_is_not_correct_and_zero_base_is_undefined(self):
        rows = copy.deepcopy(self.audit)
        for r in rows:
            if r["model_id"] == "demo_judge_1" and r["variant"] == "base" and r["split"] == "development":
                r["prediction"] = "ABSTAIN"
        validated = validate_records(rows)
        a = audit_summary(validated)
        one = next(x for x in a if x["model_id"] == "demo_judge_1" and x["split"] == "development")
        self.assertIsNone(one["ra"])
        self.assertIsNone(one["ii"])
        self.assertEqual(one["n_base_correct"], 0)

    def test_html_escapes_dynamic_content(self):
        output = render_html({"audit": [{"model_id": "<script>alert(1)</script>"}], "matched_pairs": []})
        self.assertNotIn("<script>", output)
        self.assertIn("&lt;script&gt;", output)

    def test_cost_aware_selection_and_oracle_no_leakage(self):
        from rewardlens.cvpr_v2.selection import selection_regret
        rows = [
            {"task_id": "t", "domain": "natural", "shift_type": "color", "split": "test",
             "model_id": "static_leader", "static_accuracy": 0.95,
             "predicted_ood_utility": 0.45, "true_ood_utility": 0.4,
             "inference_cost": 1, "static_audit_cost": 1, "counterfactual_audit_cost": 2},
            {"task_id": "t", "domain": "natural", "shift_type": "color", "split": "test",
             "model_id": "counterfactual_leader", "static_accuracy": 0.85,
             "predicted_ood_utility": 0.85, "true_ood_utility": 0.9,
             "inference_cost": 1, "static_audit_cost": 1, "counterfactual_audit_cost": 2},
        ]
        result = selection_regret(rows, budget=3)
        self.assertEqual(result["cf_wins"], 1)
        self.assertAlmostEqual(result["mean_regret_improvement"], 0.5)
        self.assertEqual(result["tasks"][0]["cf_selected"], "counterfactual_leader")
        with self.assertRaises(ValueError):
            selection_regret(rows, budget=2)  # CF strategy is infeasible
        bad = copy.deepcopy(rows)
        bad[0]["split"] = "development"
        with self.assertRaises(ValueError):
            selection_regret(bad, budget=3)

    def test_predictive_requires_four_families(self):
        from rewardlens.cvpr_v2.predictive import compare_predictors
        with self.assertRaises(ValueError):
            compare_predictors([{"model_id": "a", "model_family": "f1", "domain": "d", "shift_type": "s",
                                 "shift_loss": 0.1, "static_accuracy": 0.5, "in_distribution_utility": 0.6,
                                 "ra": 0.4, "ii": 0.7}])

    def test_predictive_heldout_not_trained_on_same_family(self):
        from rewardlens.cvpr_v2.predictive import compare_predictors
        rec = [{"model_id": "m" + str(i), "model_family": "f" + str(i),
                "domain": "d", "shift_type": "color", "shift_loss": i / 20,
                "static_accuracy": i / 10, "in_distribution_utility": 0.8,
                "ra": i / 10, "ii": 0.8} for i in range(5)]
        res = compare_predictors(rec)
        self.assertEqual(res["n_families"], 5)
        self.assertEqual(len(res["held_out_predictions"]), 5)
        self.assertIn("delta_mae", res)


if __name__ == "__main__":
    unittest.main()
