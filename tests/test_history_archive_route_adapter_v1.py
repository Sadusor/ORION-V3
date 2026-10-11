"""Transport adapter qualification, no product_server launch or credentials."""
import unittest
from src.orion_v3.modules.history_archive_route_adapter_v1 import (
    HistoryArchiveRouteAdapterV1, SYNC_PATH, DELETE_PATH,
)


class StubBoundary:
    def __init__(self):
        self.calls = []
        self.fail = False

    def sync(self, *, device_token, body):
        if self.fail:
            raise RuntimeError("storage error")
        self.calls.append(("sync", device_token, body["project_id"]))
        return 200, {"ok": True}

    def owner_delete(self, *, owner_token, conversation_id, project_id):
        if self.fail:
            raise RuntimeError("delete error")
        self.calls.append(("delete", owner_token, conversation_id, project_id))
        return 200, {"ok": True}


class RouteAdapterTests(unittest.TestCase):
    def setUp(self):
        self.boundary = StubBoundary()
        self.enabled = False
        self.adapter = HistoryArchiveRouteAdapterV1(
            boundary=self.boundary, enabled=lambda: self.enabled,
            project_authorized=lambda token, project: token == "scoped" and project == "p",
            owner_authorized=lambda token: token == "separate-owner")
        self.sync_body = {"project_id": "p", "snapshot": {"conversations": [], "messages": []}}
        self.delete_body = {"project_id": "p", "conversation_id": "old"}

    def test_disabled_both(self):
        self.assertEqual(self.adapter.dispatch(
            path=SYNC_PATH, device_token="scoped", body=self.sync_body)[0], 404)
        self.assertEqual(self.adapter.dispatch(
            path=DELETE_PATH, owner_token="separate-owner", body=self.delete_body)[0], 404)
        self.assertFalse(self.boundary.calls)

    def test_enabled_authorized_sync_and_delete(self):
        self.enabled = True
        self.assertEqual(self.adapter.dispatch(
            path=SYNC_PATH, device_token="scoped", body=self.sync_body)[0], 200)
        self.assertEqual(self.adapter.dispatch(
            path=DELETE_PATH, owner_token="separate-owner", body=self.delete_body)[0], 200)
        self.assertEqual(len(self.boundary.calls), 2)

    def test_pairing_cannot_delete_or_reconcile(self):
        self.enabled = True
        self.assertEqual(self.adapter.dispatch(
            path=SYNC_PATH, device_token="paired", body=self.sync_body)[0], 403)
        self.assertEqual(self.adapter.dispatch(
            path=DELETE_PATH, owner_token="paired", body=self.delete_body)[0], 403)
        self.assertFalse(self.boundary.calls)

    def test_wrong_project_rejected(self):
        self.enabled = True
        self.assertEqual(self.adapter.dispatch(
            path=SYNC_PATH, device_token="scoped",
            body={**self.sync_body, "project_id": "other"})[0], 403)
        self.assertFalse(self.boundary.calls)

    def test_missing_fields_fails_closed(self):
        self.enabled = True
        self.assertEqual(self.adapter.dispatch(path=SYNC_PATH,
            device_token="scoped", body={"project_id": "p"})[0], 400)
        self.assertEqual(self.adapter.dispatch(path=DELETE_PATH,
            owner_token="separate-owner", body={"project_id": "p"})[0], 400)
        self.assertEqual(self.adapter.dispatch(path=SYNC_PATH,
            device_token="scoped", body=[])[0], 400)

    def test_delegate_failure_is_not_success(self):
        self.enabled = True
        self.boundary.fail = True
        self.assertEqual(self.adapter.dispatch(
            path=SYNC_PATH, device_token="scoped", body=self.sync_body)[0], 409)
        self.assertEqual(self.adapter.dispatch(
            path=DELETE_PATH, owner_token="separate-owner", body=self.delete_body)[0], 409)
        self.assertFalse(self.boundary.calls)

    def test_unknown_route_not_handled(self):
        self.enabled = True
        self.assertEqual(self.adapter.dispatch(path="/api/chat-history/sync",
            device_token="scoped", body=self.sync_body)[0], 404)


if __name__ == "__main__":
    unittest.main()
