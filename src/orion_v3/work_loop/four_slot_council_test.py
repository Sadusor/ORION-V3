import tempfile
import unittest
from pathlib import Path
from orion_v3.work_loop.four_slot_council import run_four,SLOTS
from orion_v3.work_loop.free_provider_router import Candidate
from orion_v3.work_loop.existing_reviewer_slot_adapter import ReviewerInvocationError

FAMILIES=("gpt-oss","gemini","qwen","llama")
def pools():
 return {slot:[Candidate("groq" if i%2==0 else "gemini",f"model-{family}",family)]
         for i,(slot,family) in enumerate(zip(SLOTS,FAMILIES))}
class CouncilTests(unittest.TestCase):
 def call(self,**kw):
  return run_four(pools=kw.pop("pools",pools()),
                  invoke=kw.pop("invoke",lambda slot,c:"proposal "+slot),
                  stop_requested=kw.pop("stop_requested",lambda:False),
                  task_id="demo",**kw)
 def test_four(self):
  r=self.call()
  self.assertEqual(r["status"],"PROPOSAL_ONLY_COMPLETE")
  self.assertEqual(len(r["completed"]),4)
 def test_no_execution(self):
  r=self.call()
  self.assertEqual(r["execution"],"NOT_PERFORMED")
  self.assertEqual(r["owner_approval"],"NOT_GRANTED")
 def test_four_distinct(self):
  r=self.call()
  self.assertEqual(len({v["family"] for v in r["completed"].values()}),4)
 def test_stop_before(self):
  self.assertEqual(self.call(stop_requested=lambda:True)["status"],"STOPPED")
 def test_stop_during(self):
  calls=[0]
  def invoke(slot,c):
   calls[0]+=1
   return "proposal"
  self.assertEqual(self.call(invoke=invoke,stop_requested=lambda:calls[0]>=2)["status"],"STOPPED")
 def test_family_collision(self):
  p=pools();p["author_b"]=[Candidate("gemini","another","gpt-oss")]
  r=self.call(pools=p)
  self.assertEqual(r["status"],"NO_ELIGIBLE_FREE_CANDIDATE")
  self.assertEqual(r["failed_slot"],"author_b")
 def test_failure_blocks_next_slot(self):
  def invoke(slot,c):raise ReviewerInvocationError("AUTH")
  r=self.call(invoke=invoke)
  self.assertEqual(r["failed_slot"],"author_a")
  self.assertEqual(r["completed"],{})
 def test_fallback_in_slot(self):
  p=pools()
  p["author_a"].insert(0,Candidate("groq","rate-limited","nemotron"))
  def invoke(slot,c):
   if c.model=="rate-limited":raise ReviewerInvocationError("RATE_LIMIT")
   return "proposal"
  r=self.call(pools=p,invoke=invoke)
  self.assertEqual(r["status"],"PROPOSAL_ONLY_COMPLETE")
  self.assertEqual(r["completed"]["author_a"]["family"],"gpt-oss")
 def test_checkpoint(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"log.jsonl"
   r=self.call(checkpoint_path=p)
   self.assertEqual(r["status"],"PROPOSAL_ONLY_COMPLETE")
   self.assertEqual(len(p.read_text().splitlines()),4)
 def test_missing_slot(self):
  p=pools();del p["reviewer_b"]
  with self.assertRaises(ValueError):self.call(pools=p)
 def test_extra_slot(self):
  p=pools();p["fifth"]=[]
  with self.assertRaises(ValueError):self.call(pools=p)
 def test_empty_pool(self):
  p=pools();p["reviewer_a"]=[]
  self.assertEqual(self.call(pools=p)["failed_slot"],"reviewer_a")
 def test_zero_budget(self):
  with self.assertRaises(ValueError):self.call(max_attempts=0)
 def test_excess_budget(self):
  with self.assertRaises(ValueError):self.call(max_attempts=9)
 def test_invalid_invoke(self):
  with self.assertRaises(ValueError):self.call(invoke=None)
if __name__=="__main__":unittest.main()
