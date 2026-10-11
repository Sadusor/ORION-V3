"""Source contract for isolated Android Stage C helper (not device execution)."""
import unittest
from pathlib import Path

ANDROID = Path("android/app/src/main/java/com/sadusor/orionv3/history/ArchiveDeviceReconcileV1.kt")
BRIDGE = Path("android/app/src/main/java/com/sadusor/orionv3/online/OrionPcBridge.kt")


class AndroidArchiveSourceContract(unittest.TestCase):
    def test_helper_exists_and_protects_project_and_orphans(self):
        source = ANDROID.read_text(encoding="utf-8")
        self.assertIn('require(row.optString("project_id") == projectId)', source)
        self.assertIn("require(conversation in allowed)", source)
        self.assertIn('require(response.optBoolean("ok", false))', source)

    def test_legacy_bridge_not_rerouted_implicitly(self):
        source = BRIDGE.read_text(encoding="utf-8")
        self.assertIn('"/api/chat-history/sync"', source)
        self.assertIn('fun syncArchiveHistory(', source)
        self.assertIn('archive_sync_opt_in', source)
        self.assertIn('Device tombstone application not activated', source)


if __name__ == "__main__":
    unittest.main()
