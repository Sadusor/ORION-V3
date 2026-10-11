import unittest
from pathlib import Path

SERVER = Path("src/orion_v3/product_server.py")
ANDROID = Path("android/app/src/main/java/com/sadusor/orionv3/online/OrionPcBridge.kt")

class ProductionIntegrationSourceChecks(unittest.TestCase):
    def test_server_routes_explicitly_opt_in(self):
        s = SERVER.read_text(encoding="utf-8")
        self.assertIn('ORION_ARCHIVE_HTTP_OPT_IN', s)
        self.assertIn('ORION_ARCHIVE_TEST_ROOT', s)
        self.assertIn('if path in (SYNC_PATH, DELETE_PATH)', s)
        self.assertLess(s.index('if path in (SYNC_PATH, DELETE_PATH)'),
                        s.index('elif not self._require_auth():'))
        self.assertIn('X-Orion-Archive-Owner', s)
        self.assertIn('X-Orion-Archive-Device', s)

    def test_android_legacy_remains_and_archive_default_off(self):
        s = ANDROID.read_text(encoding="utf-8")
        self.assertIn('fun syncHistory(requestId: String)', s)
        self.assertIn('"/api/chat-history/sync"', s)
        self.assertIn('fun syncArchiveHistory(', s)
        self.assertIn('prefs.getBoolean("archive_sync_opt_in", false)', s)
        self.assertIn('applyArchiveTombstones(projectId, removed)', s)
        self.assertIn('X-Orion-Archive-Device', s)

if __name__ == "__main__":
    unittest.main()
