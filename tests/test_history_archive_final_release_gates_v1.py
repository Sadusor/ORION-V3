"""Release truth gates: a PASS must not imply production archive is activated."""
from pathlib import Path
import unittest

ROOT=Path("src/orion_v3/product_server.py")
BRIDGE=Path("android/app/src/main/java/com/sadusor/orionv3/online/OrionPcBridge.kt")
class HistoryArchiveFinalGates(unittest.TestCase):
    def test_original_chat_persistence_and_advisory_memory_intake(self):
        s=ROOT.read_text(encoding="utf-8")
        self.assertIn('synced = CHAT_HISTORY.sync(body)',s)
        self.assertIn('MEMORY_AUTO_CANDIDATES.consider_sync(body)',s)
        self.assertIn('MEMORY_RETRIEVAL.retrieve(',s)
        # Candidate extraction is not automatically permanent archive indexing.
        self.assertIn('ORION_HISTORY_ARCHIVE_V1_EXPERIMENTAL',s)
    def test_existing_prod_archive_sync_is_opt_in(self):
        s=BRIDGE.read_text(encoding="utf-8")
        self.assertIn('prefs.getBoolean("archive_sync_opt_in", false)',s)
        self.assertIn('archive_device_capability',s)
        self.assertIn('/api/history-archive/device-sync',s)
    def test_scoped_archive_owner_delete_is_fail_closed(self):
        s=ROOT.read_text(encoding="utf-8")
        self.assertIn('os.environ.get("ORION_ARCHIVE_HTTP_OPT_IN") != "1"',s)
        self.assertIn('X-Orion-Archive-Owner',s)
        self.assertIn('X-Orion-Archive-Device',s)

if __name__=="__main__":
    unittest.main()
