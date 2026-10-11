import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from orion_v3.modules.document_index_v1 import DocumentIndexV1
from orion_v3.modules.document_chat_connector_v1 import (
    DocumentAwareGiteaChatBrain, indexed_chat_request
)
from orion_v3.modules.gitea_chat_brain_v1 import GiteaChatStreamingBrain


class DocumentChatConnectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.index = DocumentIndexV1(self.root / "indexed_documents.sqlite3")
        self.index.ingest_text(project="orion-v3", filename="contacts.csv",
                               content="ZEUS-843,Elena Example,Central Office")
        self.index.ingest_text(project="other", filename="private.csv",
                               content="OTHER-741,Separate Private Record")

    def _capture(self, project, query, goal="Owner request"):
        captured = {}
        def fake_start(self, prompt, model):
            captured["prompt"] = prompt
            return {"brain_started_utc": "fixture"}
        with patch.object(GiteaChatStreamingBrain, "start", fake_start):
            with indexed_chat_request(project_id=project, owner_text=query, state_dir=self.root):
                DocumentAwareGiteaChatBrain().start(goal, "fixture")
        return captured["prompt"]

    def test_matching_document_reaches_post_memory_prompt(self):
        prompt = self._capture("orion-v3", "ZEUS-843")
        self.assertIn("Elena Example", prompt)
        self.assertIn("Document contacts.csv page 1", prompt)
        self.assertIn("authority='context_only'", prompt)
        self.assertIn("Owner request", prompt)

    def test_project_isolation(self):
        prompt = self._capture("orion-v3", "OTHER-741")
        self.assertNotIn("Separate Private Record", prompt)
        prompt = self._capture("other", "OTHER-741")
        self.assertIn("Separate Private Record", prompt)

    def test_missing_index_is_nonintrusive(self):
        (self.root / "indexed_documents.sqlite3").unlink()
        self.assertEqual(self._capture("orion-v3", "ZEUS-843"), "Owner request")

    def test_scope_restored_between_requests(self):
        self._capture("orion-v3", "ZEUS-843")
        captured = {}
        def fake_start(self, prompt, model):
            captured["prompt"] = prompt
            return {}
        with patch.object(GiteaChatStreamingBrain, "start", fake_start):
            DocumentAwareGiteaChatBrain().start("New request", "fixture")
        self.assertEqual(captured["prompt"], "New request")


if __name__ == "__main__":
    unittest.main()
