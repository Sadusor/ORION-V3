import base64
import tempfile
import unittest
from pathlib import Path

from orion_v3.modules.document_intake_v1 import import_indexed_document
from orion_v3.modules.document_index_v1 import DocumentIndexV1

class DocumentIntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def put(self, text, project="orion-v3", filename="test.csv"):
        return import_indexed_document(state_dir=self.root, project=project,
            filename=filename, data_base64=base64.b64encode(text.encode()).decode())

    def test_ingest_search_and_project_isolation(self):
        result=self.put("TOKEN-849,Helena Example,North Office")
        self.assertTrue(result["ok"])
        idx=DocumentIndexV1(self.root/"indexed_documents.sqlite3")
        self.assertIn("Helena Example",idx.search("TOKEN-849",project="orion-v3")[0]["snippet"])
        self.assertFalse(idx.search("TOKEN-849",project="other"))

    def test_replace_reindex(self):
        self.put("OUTDATED-55")
        self.put("CURRENT-77")
        idx=DocumentIndexV1(self.root/"indexed_documents.sqlite3")
        self.assertFalse(idx.search("OUTDATED-55",project="orion-v3"))
        self.assertTrue(idx.search("CURRENT-77",project="orion-v3"))

    def test_invalid_inputs_rejected(self):
        for kwargs in ({"filename":"../bad.txt"},{"filename":"malware.exe"},
                       {"project":""},{"data_base64":"invalid##"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                import_indexed_document(**dict(state_dir=self.root,project="orion-v3",
                    filename="sample.txt",data_base64="YWJj",**kwargs))

if __name__=="__main__":unittest.main()
