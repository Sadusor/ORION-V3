import tempfile
import unittest
from pathlib import Path

from src.orion_v3.modules.history_archive_backend_composition_v1 import build_archive_route_fixture
from src.orion_v3.modules.history_archive_scoped_credentials_v1 import ProjectDeviceCredentialsV1
from src.orion_v3.modules.history_archive_owner_capability_v1 import OwnerCapabilityV1
from src.orion_v3.modules.history_archive_route_adapter_v1 import SYNC_PATH, DELETE_PATH
from src.orion_v3.modules.history_archive_v1 import HistoryArchiveV1


class CompositionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.device = ProjectDeviceCredentialsV1(self.root / "device-credentials.sqlite3")
        self.token = self.device.enroll(project_id="orion-v3", physically_confirmed=True)
        self.owner = OwnerCapabilityV1(self.root / "owner-capability").enroll(physically_confirmed=True)
        self.payload = {"project_id": "orion-v3", "snapshot": {
            "conversations": [{"id": "c1", "project_id": "orion-v3",
                               "created_at_ms": 1, "updated_at_ms": 2}],
            "messages": [{"id": "m1", "conversation_id": "c1",
                          "role": "user", "text": "full message", "created_at_ms": 2}]}}

    def test_disabled_does_not_write(self):
        adapter = build_archive_route_fixture(root=self.root, project_id="orion-v3")
        self.assertEqual(adapter.dispatch(path=SYNC_PATH, device_token=self.token,
                                          body=self.payload)[0], 404)
        self.assertEqual(HistoryArchiveV1(self.root / "archive.sqlite3").query(
            project_id="orion-v3"), [])

    def test_scoped_roundtrip_and_owner_delete(self):
        adapter = build_archive_route_fixture(root=self.root, project_id="orion-v3", enabled=True)
        self.assertEqual(adapter.dispatch(path=SYNC_PATH, device_token=self.token,
                                          body=self.payload)[0], 200)
        self.assertEqual(len(HistoryArchiveV1(self.root / "archive.sqlite3").query(
            project_id="orion-v3")), 1)
        self.assertEqual(adapter.dispatch(path=DELETE_PATH, owner_token=self.owner,
            body={"project_id": "orion-v3", "conversation_id": "c1"})[0], 200)
        self.assertEqual(adapter.dispatch(path=SYNC_PATH, device_token=self.token,
                                          body=self.payload)[0], 200)
        self.assertEqual(HistoryArchiveV1(self.root / "archive.sqlite3").query(
            project_id="orion-v3"), [])

    def test_other_project_denied(self):
        adapter = build_archive_route_fixture(root=self.root, project_id="orion-v3", enabled=True)
        other = dict(self.payload, project_id="another")
        self.assertEqual(adapter.dispatch(path=SYNC_PATH, device_token=self.token,
                                          body=other)[0], 403)
        self.assertEqual(adapter.dispatch(path=DELETE_PATH, owner_token=self.owner,
            body={"project_id": "another", "conversation_id": "c1"})[0], 403)

    def test_pair_token_denied(self):
        adapter = build_archive_route_fixture(root=self.root, project_id="orion-v3", enabled=True)
        self.assertEqual(adapter.dispatch(path=SYNC_PATH, device_token="paired",
                                          body=self.payload)[0], 403)
        self.assertEqual(adapter.dispatch(path=DELETE_PATH, owner_token="paired",
            body={"project_id": "orion-v3", "conversation_id": "c1"})[0], 403)

    def test_revoked_device_denied(self):
        adapter = build_archive_route_fixture(root=self.root, project_id="orion-v3", enabled=True)
        self.device.revoke(self.token, physically_confirmed=True)
        self.assertEqual(adapter.dispatch(path=SYNC_PATH, device_token=self.token,
                                          body=self.payload)[0], 403)


if __name__ == "__main__":
    unittest.main()
