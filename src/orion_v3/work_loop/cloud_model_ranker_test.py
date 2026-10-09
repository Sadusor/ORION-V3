import unittest
from orion_v3.work_loop.cloud_model_ranker import ModelHealth,rank_models
from orion_v3.work_loop.free_provider_router import Candidate

def model(name,quality=80,**kw):
 defaults=dict(capability="coding",free_confirmed=True,smoke_passed=True,
               latency_ms=100,quality=quality)
 defaults.update(kw)
 return ModelHealth(Candidate("groq",name,name),**defaults)
class RankTests(unittest.TestCase):
 def test_quality(self):
  self.assertEqual(rank_models([model("low",30),model("high",90)])[0].model,"high")
 def test_latency_tiebreak(self):
  self.assertEqual(rank_models([model("slow",latency_ms=900),model("fast",latency_ms=20)])[0].model,"fast")
 def test_unproven_excluded(self):
  self.assertFalse(rank_models([model("unknown",smoke_passed=False)]))
 def test_unconfirmed_free_excluded(self):
  self.assertFalse(rank_models([model("unknown",free_confirmed=False)]))
 def test_cooldown(self):
  self.assertFalse(rank_models([model("cool",cooldown=True)]))
 def test_capability(self):
  self.assertFalse(rank_models([model("review",capability="review")]))
 def test_family(self):
  self.assertFalse(rank_models([model("taken")],reserved_families=("taken",)))
 def test_private_off(self):
  self.assertFalse(rank_models([model("private",paid_or_private=True)]))
 def test_private_opt_in(self):
  self.assertEqual(rank_models([model("private",paid_or_private=True)],allow_private_reserve=True)[0].model,"private")
 def test_private_last(self):
  self.assertEqual(rank_models([model("private",100,paid_or_private=True),model("free",10)],
                               allow_private_reserve=True)[0].model,"free")
 def test_invalid_capability(self):
  with self.assertRaises(ValueError):rank_models([],capability="anything")
 def test_negative_latency(self):
  self.assertFalse(rank_models([model("bad",latency_ms=-1)]))
 def test_invalid_quality(self):
  self.assertFalse(rank_models([model("bad",quality=101)]))
 def test_no_candidate(self):
  self.assertEqual(rank_models([]),())
 def test_deterministic(self):
  a=rank_models([model("z"),model("a")]);b=rank_models([model("a"),model("z")])
  self.assertEqual(a,b)
if __name__=="__main__":unittest.main()
