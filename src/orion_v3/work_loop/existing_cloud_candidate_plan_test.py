import unittest
from orion_v3.work_loop.existing_cloud_candidate_plan import family_of,plan_candidates

CAT={"models":[
 {"reviewer_id":"a","provider":"groq","model":"gpt-oss-120b","available":True},
 {"reviewer_id":"b","provider":"gemini","model":"gemini-2.5-flash","available":True},
 {"reviewer_id":"c","provider":"groq","model":"unknown-experimental","available":True},
 {"reviewer_id":"d","provider":"groq","model":"qwen3-32b","available":False},
 {"reviewer_id":"e","provider":"ollama","model":"qwen3-9b","available":True},
 {"reviewer_id":"f","provider":"gemini","model":"gemini-preview","available":True},
]}
class PlanTests(unittest.TestCase):
 def test_no_unverified_free(self):
  self.assertEqual(plan_candidates(CAT),())
 def test_two_distinct_families(self):
  r=plan_candidates(CAT,free_confirmed_ids={"a","b"})
  self.assertEqual({c.family for _,c in r},{"gpt-oss","gemini"})
 def test_unknown_excluded(self):
  self.assertEqual(plan_candidates(CAT,free_confirmed_ids={"c"}),())
 def test_unavailable_excluded(self):
  self.assertEqual(plan_candidates(CAT,free_confirmed_ids={"d"}),())
 def test_local_excluded(self):
  self.assertEqual(plan_candidates(CAT,free_confirmed_ids={"e"}),())
 def test_preview_excluded(self):
  self.assertEqual(plan_candidates(CAT,free_confirmed_ids={"f"}),())
 def test_family(self):
  self.assertEqual(family_of("nvidia/nemotron-3"),"nemotron")
if __name__=="__main__":unittest.main()
