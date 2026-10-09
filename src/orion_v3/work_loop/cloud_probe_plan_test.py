import unittest
from orion_v3.work_loop.cloud_probe_plan import ProbeTarget,plan_probes
def t(provider="groq",model="a",family="qwen",**kw):
 return ProbeTarget(provider,model,family,kw.pop("free_confirmed",True),
                    kw.pop("credential_ready",True),**kw)
class ProbePlanTests(unittest.TestCase):
 def test_one(self):self.assertEqual(len(plan_probes([t()])),1)
 def test_no_credentials(self):self.assertFalse(plan_probes([t(credential_ready=False)]))
 def test_unconfirmed_free(self):self.assertFalse(plan_probes([t(free_confirmed=False)]))
 def test_private_denied(self):self.assertFalse(plan_probes([t(private_key=True)]))
 def test_private_explicit(self):self.assertEqual(len(plan_probes([t(private_key=True)],allow_private=True)),1)
 def test_duplicate(self):self.assertEqual(len(plan_probes([t(),t()])),1)
 def test_same_family(self):self.assertEqual(len(plan_probes([t(),t("gemini","b","qwen")])),1)
 def test_independent(self):self.assertEqual(len(plan_probes([t(),t("gemini","b","gemini")])),2)
 def test_budget(self):
  x=[t("p"+str(i),str(i),"f"+str(i)) for i in range(6)]
  self.assertEqual(len(plan_probes(x,max_calls=2)),2)
 def test_zero_budget(self):
  with self.assertRaises(ValueError):plan_probes([],max_calls=0)
 def test_excess_budget(self):
  with self.assertRaises(ValueError):plan_probes([],max_calls=9)
 def test_wrong_capability(self):self.assertFalse(plan_probes([t(capability="review")]))
 def test_empty_identity(self):self.assertFalse(plan_probes([t(provider="")]))
 def test_stable_order(self):
  x=[t(),t("gemini","b","gemini")]
  self.assertEqual(plan_probes(x),tuple(x))
 def test_private_no_credentials(self):self.assertFalse(plan_probes([t(private_key=True,credential_ready=False)],allow_private=True))
if __name__=="__main__":unittest.main()
