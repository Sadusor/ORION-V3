import tempfile
import unittest
from pathlib import Path
from src.orion_v3.modules.history_archive_scoped_credentials_v1 import ProjectDeviceCredentialsV1


class ProjectDeviceCredentialsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "device-credentials.sqlite3"
        self.store = ProjectDeviceCredentialsV1(self.path)

    def test_default_unenrolled_denies_pairing(self):
        self.assertFalse(self.store.authorized("ordinary-pair", "p"))

    def test_physical_confirmation_required(self):
        with self.assertRaises(PermissionError):
            self.store.enroll(project_id="p")
        self.assertFalse(self.store.authorized("ordinary-pair", "p"))

    def test_enrolled_token_binds_project(self):
        token = self.store.enroll(project_id="p", physically_confirmed=True)
        self.assertTrue(self.store.authorized(token, "p"))
        self.assertFalse(self.store.authorized(token, "other"))
        self.assertFalse(self.store.authorized("paired-device", "p"))

    def test_restart_and_revoke(self):
        token = self.store.enroll(project_id="p", physically_confirmed=True)
        reopened = ProjectDeviceCredentialsV1(self.path)
        self.assertTrue(reopened.authorized(token, "p"))
        with self.assertRaises(PermissionError):
            reopened.revoke(token)
        self.assertTrue(reopened.revoke(token, physically_confirmed=True))
        self.assertFalse(self.store.authorized(token, "p"))

    def test_no_plaintext_stored(self):
        token = self.store.enroll(project_id="p", physically_confirmed=True)
        self.assertNotIn(token.encode(), self.path.read_bytes())

    def test_invalid_scope_denied(self):
        for bad in ("", " ", "x" * 161):
            with self.assertRaises(ValueError):
                self.store.enroll(project_id=bad, physically_confirmed=True)
        self.assertFalse(self.store.authorized("", "p"))


if __name__ == "__main__":
    unittest.main()
