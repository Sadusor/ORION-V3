import unittest
from orion_v3.work_loop.healthy_cloud_router import rank_healthy
from orion_v3.work_loop.cloud_model_ranker import ModelHealth
from orion_v3.work_loop.provider_health import Health,update_health
from orion_v3.work_loop.free_provider_router import Candidate
def m(name,quality=70,private=False):
 return ModelHealth(Candidate("groq",name,name),capability="coding",
                    free_confirmed=True,smoke_passed=False,latency_ms=30,
                    quality=quality,paid_or_private=private)
def ok(name,now=100):
 return update_health(Health("groq",name),outcome="SUCCESS",now=now)
class IntegrationTests(unittest.TestCase):
 def test_no_health(self):self.assertEqual(rank_healthy([m("a")],{},now=101),())
 def test_success(self):self.assertEqual(rank_healthy([m("a")],{("groq","a"):ok("a")},now=101)[0].model,"a")
 def test_stale(self):self.assertEqual(rank_healthy([m("a")],{("groq","a"):ok("a")},now=90000),())
 def test_rate_limit(self):
  h=update_health(ok("a"),outcome="RATE_LIMIT",now=101)
  self.assertEqual(rank_healthy([m("a")],{("groq","a"):h},now=102),())
 def test_auth(self):
  h=update_health(ok("a"),outcome="AUTH",now=101)
  self.assertEqual(rank_healthy([m("a")],{("groq","a"):h},now=102),())
 def test_other_model_health(self):self.assertEqual(rank_healthy([m("a")],{("groq","a"):ok("b")},now=101),())
 def test_quality(self):
  a=rank_healthy([m("a",40),m("b",90)],{("groq","a"):ok("a"),("groq","b"):ok("b")},now=101)
  self.assertEqual(a[0].model,"b")
 def test_family_reserved(self):self.assertEqual(rank_healthy([m("a")],{("groq","a"):ok("a")},now=101,reserved_families=("a",)),())
 def test_private_default_off(self):self.assertEqual(rank_healthy([m("a",private=True)],{("groq","a"):ok("a")},now=101),())
 def test_private_opt_in(self):
  self.assertEqual(rank_healthy([m("a",private=True)],{("groq","a"):ok("a")},now=101,allow_private_reserve=True)[0].model,"a")
 def test_free_first(self):
  r=rank_healthy([m("a",100,True),m("b",10)],{("groq","a"):ok("a"),("groq","b"):ok("b")},now=101,allow_private_reserve=True)
  self.assertEqual(r[0].model,"b")
 def test_negative_time(self):
  with self.assertRaises(ValueError):rank_healthy([],{},now=-1)
if __name__=="__main__":unittest.main()
