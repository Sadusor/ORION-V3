import unittest
from unittest.mock import patch
from live_free_family_preflight import probe

def candidates():
    return [{"provider":"openrouter","model":f"vendor/{x}:free","family":x}
            for x in ("gemma","qwen","llama","deepseek","mistral")]

class PreflightTests(unittest.TestCase):
    def test_four_distinct(self):
        r=probe(candidates=candidates(),key="test",invoke=lambda **kw:{"text":"READY"})
        self.assertEqual(r["status"],"FOUR_FAMILIES_RESPONSIVE")
        self.assertEqual(len(r["attempts"]),4)
        self.assertFalse(r["council_started"])
    def test_rate_limit_shortage(self):
        from orion_v3.work_loop.unified_cloud_adapter import DispatchError
        def invoke(**kw):
            if "gemma" in kw["model"]:
                raise DispatchError("RATE_LIMIT")
            return {"text":"READY"}
        r=probe(candidates=candidates(),key="test",invoke=invoke)
        self.assertEqual(r["status"],"FOUR_FAMILIES_RESPONSIVE")
        self.assertEqual(len(r["attempts"]),5)
        self.assertEqual(r["attempts"][0]["status"],"RATE_LIMIT")
    def test_all_rate_limited(self):
        from orion_v3.work_loop.unified_cloud_adapter import DispatchError
        def invoke(**kw): raise DispatchError("RATE_LIMIT")
        r=probe(candidates=candidates(),key="test",invoke=invoke)
        self.assertEqual(r["status"],"INSUFFICIENT_RESPONSIVE_FAMILIES")
        self.assertEqual(len(r["responsive_families"]),0)
    def test_malformed_first_model_tries_second_same_family(self):
        pool=[{"family":"gemma","model":"vendor/gemma-one:free"},
              {"family":"gemma","model":"vendor/gemma-two:free"}]+candidates()[1:]
        def invoke(**kw):
            return {"text":"" if "gemma-one" in kw["model"] else "READY"}
        r=probe(candidates=pool,key="test",invoke=invoke)
        self.assertEqual(r["status"],"FOUR_FAMILIES_RESPONSIVE")
        self.assertEqual([a["status"] for a in r["attempts"][:2]],
                         ["EMPTY","RESPONSIVE"])
    def test_rate_limit_skips_same_family(self):
        pool=[{"family":"gemma","model":"vendor/gemma-one:free"},
              {"family":"gemma","model":"vendor/gemma-two:free"}]+candidates()[1:]
        from orion_v3.work_loop.unified_cloud_adapter import DispatchError
        def invoke(**kw):
            if "gemma" in kw["model"]:
                raise DispatchError("RATE_LIMIT")
            return {"text":"READY"}
        r=probe(candidates=pool,key="test",invoke=invoke)
        self.assertEqual(sum(a["family"]=="gemma" for a in r["attempts"]),1)
    def test_no_paid_requests(self):
        pool=[{"family":"paid","model":"vendor/paid"}]+candidates()
        calls=[]
        def invoke(**kw):
            calls.append(kw["model"])
            return {"text":"READY"}
        r=probe(candidates=pool,key="test",invoke=invoke)
        self.assertEqual(len(calls),4)
        self.assertTrue(all(x.endswith(":free") for x in calls))
    def test_bounded(self):
        pool=[{"family":str(i),"model":f"v/{i}:free"} for i in range(12)]
        r=probe(candidates=pool,key="test",invoke=lambda **kw:{"text":""},limit=6)
        self.assertEqual(len(r["attempts"]),6)

if __name__=="__main__":unittest.main()
