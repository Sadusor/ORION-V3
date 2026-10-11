"""Static gates for disposable ORION2 USB loopback qualification."""
import unittest
from pathlib import Path

class UsbArchiveContract(unittest.TestCase):
    def test_orion2_only_and_disposable_database(self):
        s=Path("android/app/src/main/java/com/sadusor/orionv3/history/ArchiveQualificationActivity.kt").read_text(encoding="utf-8")
        self.assertIn('packageName != "com.sadusor.orionv3.archivequal"',s)
        self.assertIn('orion2_usb_sync_qualification.db',s)
        self.assertIn('usb_sync_qualification',s)
        self.assertIn('127.0.0.1:18765',s)
        self.assertIn('applyArchiveTombstones(project, removed)',s)
    def test_server_independent_credentials_and_loopback(self):
        s=Path("tests/orion2_usb_archive_server_v1.py").read_text(encoding="utf-8")
        self.assertIn('127.0.0.1", 18765',s)
        self.assertIn('OwnerCapabilityV1',s)
        self.assertIn('ProjectDeviceCredentialsV1',s)
        self.assertIn('physically_confirmed=True',s)
        self.assertIn('DELETE_PATH',s)
if __name__ == "__main__":
    unittest.main()
