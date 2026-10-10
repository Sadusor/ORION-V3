import tempfile
import unittest
from pathlib import Path
from orion_v3.modules.document_index_v1 import DocumentIndexV1, extract_document_text

class DocumentIndexTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.index=DocumentIndexV1(Path(self.folder.name)/"docs.sqlite3")
    def tearDown(self): self.folder.cleanup()
    def test_project_isolation_and_provenance(self):
        record=self.index.ingest_text(project="orion-v3",filename="roadmap.md",
            content="Qwen uses the canonical roadmap and source references")
        hits=self.index.search("canonical",project="orion-v3")
        self.assertEqual(hits[0]["document_id"],record["document_id"])
        self.assertEqual(hits[0]["page"],1)
        self.assertEqual(self.index.search("canonical",project="other"),[])
    def test_superseded_document_replaced(self):
        self.index.ingest_text(project="p",filename="notes.txt",content="outdated")
        self.index.ingest_text(project="p",filename="notes.txt",content="revised")
        self.assertEqual(self.index.search("outdated",project="p"),[])
        self.assertEqual(len(self.index.search("revised",project="p")),1)
    def test_mult_page_attribution(self):
        self.index.ingest_text(project="p",filename="manual.pdf",content="",
            pages=[(1,"overview"),(2,"stop coordinator verification")])
        self.assertEqual(self.index.search("verification",project="p")[0]["page"],2)
    def test_text_extraction(self):
        self.assertEqual(extract_document_text(b"hello", "guide.md"),[(1,"hello")])
    def test_unsupported_rejected(self):
        with self.assertRaises(ValueError):extract_document_text(b"fake","bad.exe")
    def test_explicit_scope(self):
        with self.assertRaises(ValueError):self.index.search("hello",project="")
    def test_pdf_requires_real_parser(self):
        with self.assertRaises(Exception):extract_document_text(b"not a real PDF","fake.pdf")
if __name__=="__main__": unittest.main()
