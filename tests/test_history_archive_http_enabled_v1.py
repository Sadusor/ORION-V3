"""Enabled HTTP archive qualification, isolated temp SQLite and loopback."""
import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

from src.orion_v3.modules.history_archive_http_qualification_v1 import bind_loopback
from src.orion_v3.modules.history_archive_scoped_credentials_v1 import ProjectDeviceCredentialsV1
from src.orion_v3.modules.history_archive_owner_capability_v1 import OwnerCapabilityV1
from src.orion_v3.modules.history_archive_v1 import HistoryArchiveV1

SYNC = "/api/history-archive/device-sync"
DELETE = "/api/history-archive/owner-delete"


class EnabledHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        store = ProjectDeviceCredentialsV1(self.root / "device-credentials.sqlite3")
        self.device = store.enroll(project_id="orion-v3", physically_confirmed=True)
        self.owner = OwnerCapabilityV1(self.root / "owner-capability").enroll(
            physically_confirmed=True)
        self.server = bind_loopback(root=self.root, project_id="orion-v3", enabled=True)
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def post(self, path, body, headers=None):
        connection = HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=5)
        try:
            connection.request("POST", path, json.dumps(body),
                               {"Content-Type": "application/json", **(headers or {})})
            reply = connection.getresponse()
            return reply.status, json.loads(reply.read())
        finally:
            connection.close()

    def payload(self):
        return {"project_id": "orion-v3",
                "snapshot": {"conversations": [{"id": "c1", "project_id": "orion-v3",
                    "created_at_ms": 1, "updated_at_ms": 2}],
                    "messages": [{"id": "m1", "conversation_id": "c1", "role": "user",
                                  "text": "remember this fact", "created_at_ms": 2}]}}

    def test_network_sync_delete_offline_replay(self):
        headers = {"X-Orion-Archive-Device": self.device}
        self.assertEqual(self.post(SYNC, self.payload(), headers)[0], 200)
        self.assertEqual(len(HistoryArchiveV1(self.root / "archive.sqlite3").query(
            project_id="orion-v3")), 1)
        self.assertEqual(self.post(DELETE,
            {"project_id": "orion-v3", "conversation_id": "c1"},
            {"X-Orion-Archive-Owner": self.owner})[0], 200)
        code, result = self.post(SYNC, self.payload(), headers)
        self.assertEqual(code, 200)
        self.assertEqual(result["removed_conversation_ids"], ["c1"])
        self.assertEqual(HistoryArchiveV1(self.root / "archive.sqlite3").query(
            project_id="orion-v3"), [])

    def test_ordinary_pairing_never_authorizes(self):
        self.assertEqual(self.post(SYNC, self.payload(),
            {"X-Orion-Archive-Device": "paired"})[0], 403)
        self.assertEqual(self.post(DELETE,
            {"project_id": "orion-v3", "conversation_id": "c1"},
            {"X-Orion-Archive-Owner": "paired"})[0], 403)

    def test_project_scope_denied(self):
        payload = self.payload()
        payload["project_id"] = "other"
        self.assertEqual(self.post(SYNC, payload,
            {"X-Orion-Archive-Device": self.device})[0], 403)

    def test_unauthenticated_cannot_delete(self):
        self.assertEqual(self.post(DELETE,
            {"project_id": "orion-v3", "conversation_id": "c1"})[0], 403)


if __name__ == "__main__":
    unittest.main()
