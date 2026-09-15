import json
import tempfile
import unittest
from pathlib import Path

from scripts import phase2_autonomous as p

def pool():
    return dict(item_id="pool", factor="count", dataset="tallyqa", question="q",
                gold_answer="0", gold_index=0, n_pool=8,
                candidates=[{"text":str(i)} for i in range(8)])

class PairAdapter:
    def __init__(self, fail_after=None):
        self.calls=0
        self.fail_after=fail_after
    def prepare_inputs(self, **kwargs):
        return kwargs
    def judge(self, inputs):
        if self.calls == self.fail_after:
            raise RuntimeError("interrupted")
        self.calls+=1
        return {"raw_output":"ambiguous" if self.calls==1 else "A"}

class ScalarAdapter:
    def __init__(self, fail_after=None):
        self.calls=0
        self.fail_after=fail_after
    def score_candidate(self, **kwargs):
        if self.calls == self.fail_after:
            raise RuntimeError("interrupted")
        self.calls+=1
        return float(kwargs["candidate"])

class AutonomousTests(unittest.TestCase):
    def test_ready_must_be_boolean_true_and_hash_match(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/"manifest.jsonl"
            path.write_text("{}\n")
            receipt={"ready_for_phase2_gpu":True,"downstream_v2_manifest":str(path),
                     "downstream_v2_manifest_sha256":p.sha(path)}
            self.assertEqual(p.read_gate_payload(receipt,p.sha(path)),path)
            for bad in [False,"true",1,None]:
                with self.assertRaises(ValueError):
                    p.read_gate_payload({**receipt,"ready_for_phase2_gpu":bad},p.sha(path))
            path.write_text("changed")
            with self.assertRaises(ValueError):
                p.read_gate_payload(receipt,receipt["downstream_v2_manifest_sha256"])

    def test_journal_preserves_prefix_and_stops_on_conflicting_rows(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/"rows.jsonl"
            prefix=b'{"id":"one","x":1}\n'
            path.write_bytes(prefix+b'{"id":')
            j=p.Journal(path,lambda r:r["id"])
            self.assertEqual(path.read_bytes(),prefix)
            j.add({"id":"two","x":2})
            self.assertTrue(path.read_bytes().startswith(prefix))
            with self.assertRaises(ValueError):
                j.add({"id":"one","x":9})
            corrupt=Path(t)/"bad.jsonl"
            corrupt.write_bytes(b'not-json\n'+prefix)
            with self.assertRaises(ValueError):
                p.Journal(corrupt,lambda r:r["id"])

    def test_resume_skips_saved_edges_and_never_requeries_abstention(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            first=PairAdapter(fail_after=5)
            with self.assertRaises(RuntimeError):
                p.execute_pool(pool(),first,"m",root,"unused")
            before=(root/"pairs.jsonl").read_bytes()
            second=PairAdapter()
            p.execute_pool(pool(),second,"m",root,"unused")
            self.assertEqual(second.calls,23)
            self.assertTrue((root/"pairs.jsonl").read_bytes().startswith(before))
            rows=p.read_rows(root/"pairs.jsonl")
            self.assertEqual(len(rows),28)
            self.assertEqual(rows[0]["outcome"],"abstain")
            selections=p.read_rows(root/"selections.jsonl")
            self.assertEqual([r["n"] for r in selections],[2,4,8])
            third=PairAdapter(fail_after=0)
            p.execute_pool(pool(),third,"m",root,"unused")
            self.assertEqual(third.calls,0)
            self.assertEqual(len(p.read_rows(root/"selections.jsonl")),3)

    def test_scalar_resume_keeps_scores_and_partial_selections(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            with self.assertRaises(RuntimeError):
                p.execute_pool(pool(),ScalarAdapter(fail_after=3),"m",root,"unused")
            self.assertEqual(len(p.read_rows(root/"scores.jsonl")),3)
            adapter=ScalarAdapter()
            p.execute_pool(pool(),adapter,"m",root,"unused")
            self.assertEqual(adapter.calls,5)
            selection_path=root/"selections.jsonl"
            first_line=selection_path.read_bytes().splitlines(keepends=True)[0]
            selection_path.write_bytes(first_line)
            final=ScalarAdapter(fail_after=0)
            p.execute_pool(pool(),final,"m",root,"unused")
            self.assertEqual(final.calls,0)
            self.assertEqual(len(p.read_rows(selection_path)),3)
            self.assertTrue(selection_path.read_bytes().startswith(first_line))

    def test_static_parse_error_is_preserved_on_resume(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            image=root/"image.jpg"
            image.write_bytes(b"not-decoded-by-test-adapter")
            item={"item_id":"s","factor":"count","variant":"static","image_path":str(image),
                  "question":"q","candidate_a":"a","candidate_b":"b","expected_preference":"A"}
            adapter=PairAdapter()
            p.execute_static([item],adapter,"m",root)
            before=(root/"static.jsonl").read_bytes()
            p.execute_static([item],PairAdapter(fail_after=0),"m",root)
            self.assertEqual((root/"static.jsonl").read_bytes(),before)
            self.assertEqual(p.read_rows(root/"static.jsonl")[0]["status"],"parse_error")

    def test_four_model_lofo_never_reports_estimable_m1(self):
        from scripts.phase2_report import preliminary_models
        rows=[dict(model_id=str(i),family=str(i),A=.2*i,PFC=.1*i,PSC=.3*i,U=.1*i)
              for i in range(4)]
        result=preliminary_models(rows)
        self.assertIsNone(result["delta_mae"])
        self.assertEqual(result["status"],"NOT_IDENTIFIABLE")
        self.assertEqual(len(result["folds"]),4)
        self.assertTrue(all(r["M1"] is None for r in result["folds"]))

if __name__=="__main__":
    unittest.main()
