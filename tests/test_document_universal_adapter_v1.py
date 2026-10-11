import tempfile
import unittest
from pathlib import Path

from orion_v3.modules.document_index_v1 import DocumentIndexV1
from orion_v3.modules.document_universal_adapter_v1 import document_knowledge_source
from orion_v3.modules.universal_retrieval_v1 import UniversalRetrievalV1


class DocumentUniversalAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "documents.sqlite3"
        index = DocumentIndexV1(self.path)
        index.ingest_text(project="orion-v3", filename="demo-records.csv",
                          content="record,contact\\nZENITH-482,Marina Example")
        index.ingest_text(project="other-project", filename="private.md",
                          content="OTHER-992 secret-other-project")

    def test_retrieval_and_provenance(self):
        retriever = UniversalRetrievalV1()
        retriever.register("documents", document_knowledge_source(self.path))
        result = retriever.retrieve("ZENITH-482", project="orion-v3")
        self.assertEqual(len(result["results"]), 1)
        hit = result["results"][0]
        self.assertEqual(hit["source"], "documents")
        self.assertIn("demo-records.csv", hit["citation"])
        self.assertIn("Marina Example", hit["snippet"])
        self.assertEqual(hit["project"], "orion-v3")
        self.assertEqual(hit["trust"], "context_only")
        self.assertFalse(result["may_write"])
        self.assertFalse(result["may_execute"])

    def test_separate_project_and_no_cross_project_leak(self):
        retriever = UniversalRetrievalV1()
        retriever.register("documents", document_knowledge_source(self.path))
        result = retriever.retrieve("OTHER-992", project="orion-v3")
        self.assertEqual(result["results"], [])
        found = retriever.retrieve("OTHER-992", project="other-project")
        self.assertEqual(len(found["results"]), 1)

    def test_missing_index_fails_closed(self):
        with self.assertRaises(FileNotFoundError):
            document_knowledge_source(Path(self.temp.name) / "missing.sqlite3")

    def test_adapter_does_not_ingest_or_modify_rows(self):
        retriever = UniversalRetrievalV1()
        retriever.register("documents", document_knowledge_source(self.path))
        self.assertEqual(len(retriever.retrieve("ZENITH-482", project="orion-v3")["results"]), 1)
        self.assertEqual(len(retriever.retrieve("ZENITH-482", project="orion-v3")["results"]), 1)


if __name__ == "__main__":
    unittest.main()
