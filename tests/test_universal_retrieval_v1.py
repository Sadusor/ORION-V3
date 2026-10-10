import unittest
from orion_v3.modules.universal_retrieval_v1 import UniversalRetrievalV1,KnowledgeHit
class UniversalTests(unittest.TestCase):
    def test_sources_combined_and_cited(self):
        router=UniversalRetrievalV1()
        router.register("documents",lambda **k:[KnowledgeHit("documents","d1","Greek-English document","manual.pdf p.3",k["project"],.8)])
        router.register("code",lambda **k:[KnowledgeHit("code","g1","function foo","ORION-V3@sha src/foo.py",k["project"],.7)])
        result=router.retrieve("explain",project="orion-v3")
        self.assertEqual([r["source"] for r in result["results"]],["documents","code"])
        self.assertFalse(result["may_write"])
    def test_wrong_project_rejected(self):
        router=UniversalRetrievalV1()
        router.register("memory",lambda **k:[KnowledgeHit("memory","x","secret","id", "other")])
        result=router.retrieve("hello",project="orion-v3")
        self.assertEqual(result["results"],[])
        self.assertEqual(result["source_errors"][0]["source"],"memory")
    def test_duplicate_deduplicated(self):
        router=UniversalRetrievalV1()
        h=KnowledgeHit("documents","d","text","file", "p")
        router.register("documents",lambda **k:[h,h])
        self.assertEqual(len(router.retrieve("text",project="p")["results"]),1)
    def test_bad_source_denied(self):
        router=UniversalRetrievalV1()
        with self.assertRaises(ValueError):router.register("bad-name!",lambda **k:[])
    def test_missing_scope_denied(self):
        with self.assertRaises(ValueError):UniversalRetrievalV1().retrieve("hello",project="")
    def test_unavailable_source_disclosed(self):
        router=UniversalRetrievalV1()
        def broken(**kwargs): raise RuntimeError("offline")
        router.register("docs",broken)
        self.assertEqual(router.retrieve("question",project="p")["source_errors"][0]["error"],"RuntimeError")
if __name__=="__main__":unittest.main()
