import unittest
from pathlib import Path

class BackupNetworkContract(unittest.TestCase):
    def test_owner_backup_requires_owner_destination(self):
        s=Path("android/app/src/main/java/com/sadusor/orionv3/history/OwnerChatBackupV1.kt").read_text(encoding="utf-8")
        for required in ('context.packageName == "com.sadusor.orionv3"','ownerSelectedUri.scheme == "content"','VACUUM INTO','PRAGMA integrity_check','context.contentResolver.openOutputStream','temp.delete()'):
            self.assertIn(required,s)
    def test_production_archive_remains_off(self):
        s=Path("src/orion_v3/product_server.py").read_text(encoding="utf-8")
        self.assertIn('os.environ.get("ORION_ARCHIVE_HTTP_OPT_IN") != "1"',s)
        a=Path("android/app/src/main/java/com/sadusor/orionv3/online/OrionPcBridge.kt").read_text(encoding="utf-8")
        self.assertIn('prefs.getBoolean("archive_sync_opt_in", false)',a)

if __name__=="__main__":
    unittest.main()
