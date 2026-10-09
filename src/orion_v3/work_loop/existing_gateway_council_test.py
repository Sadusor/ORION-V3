"""Offline gateway-to-council tests; no HTTP, donor, or paid calls."""
import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from orion_v3.work_loop.free_provider_router import Candidate
from orion_v3.work_loop.existing_gateway_council import run_gateway_council
from orion_v3.work_loop.unified_cloud_adapter import DispatchError

POOL=[Candidate("openrouter",f"vendor/{name}:free",name)
      for name in ("gemma","qwen","deepseek","llama")]
def run(pool=POOL,stop=lambda:False,evidence_path=None):
    return run_gateway_council(candidates=pool,credentials={"openrouter":"placeholder"},
        connector=None,reviewer_ids={},task_id="test",objective="Design offline task tracker",
        stop_requested=stop,evidence_path=evidence_path)

class GatewayCouncilTests(unittest.TestCase):
    def test_four_distinct_and_cross_review(self):
        prompts=[]
        def fake(**kw):
            prompts.append((kw["model"],kw["prompt"]))
            return {"text":"proposal "+kw["model"]}
        with patch("orion_v3.work_loop.existing_gateway_council.dispatch",side_effect=fake):
            result=run()
        self.assertEqual(result["status"],"PROPOSAL_ONLY_COMPLETE")
        self.assertEqual(len(result["completed"]),4)
        self.assertEqual(len({v["family"] for v in result["completed"].values()}),4)
        self.assertIn("author_a:",prompts[2][1])
        self.assertIn("author_b:",prompts[2][1])
        self.assertEqual(result["execution"],"NOT_PERFORMED")
        self.assertEqual(result["owner_approval"],"NOT_GRANTED")
    def test_evidence_contains_original_responses_and_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"council.json"
            with patch("orion_v3.work_loop.existing_gateway_council.dispatch",
                       side_effect=lambda **kw:{"text":"reply from "+kw["model"]}):
                result=run(evidence_path=path)
            payload=json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(result["status"],"PROPOSAL_ONLY_COMPLETE")
            self.assertEqual(len(payload["roles"]),4)
            self.assertEqual(payload["owner_approval"],"NOT_GRANTED")
            self.assertEqual(payload["execution"],"NOT_PERFORMED")
            self.assertTrue(all(v["text"].startswith("reply from ") and len(v["sha256"])==64
                                for v in payload["roles"].values()))
            with patch("orion_v3.work_loop.existing_gateway_council.dispatch",
                       return_value={"text":"another"}):
                with self.assertRaises(FileExistsError):
                    run(evidence_path=path)

    def test_paid_openrouter_blocked(self):
        with self.assertRaises(ValueError):
            run([Candidate("openrouter","vendor/paid","gemma")])
    def test_unconfirmed_paid_candidate_blocked(self):
        with self.assertRaises(ValueError):
            run([Candidate("groq","model","gpt-oss",False)])
    def test_stop_prevents_dispatch(self):
        with patch("orion_v3.work_loop.existing_gateway_council.dispatch") as send:
            self.assertEqual(run(stop=lambda:True)["status"],"STOPPED")
            send.assert_not_called()
    def test_provider_failure_no_execution(self):
        with patch("orion_v3.work_loop.existing_gateway_council.dispatch",
                   side_effect=DispatchError("AUTH")):
            result=run()
        self.assertNotEqual(result["status"],"PROPOSAL_ONLY_COMPLETE")
        self.assertEqual(result["completed"],{})
    def test_duplicate_family_fails_closed(self):
        pool=[Candidate("openrouter",f"x/{i}:free","gemma") for i in range(4)]
        with patch("orion_v3.work_loop.existing_gateway_council.dispatch",
                   return_value={"text":"proposal"}):
            result=run(pool)
        self.assertNotEqual(result["status"],"PROPOSAL_ONLY_COMPLETE")
if __name__=="__main__":unittest.main()
