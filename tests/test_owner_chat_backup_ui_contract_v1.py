import unittest
from pathlib import Path

ROOT=Path("android/app/src/main")
class OwnerBackupUiContract(unittest.TestCase):
    def test_owner_picker_requires_explicit_document_choice(self):
        s=(ROOT/"java/com/sadusor/orionv3/history/OwnerChatBackupActivityV1.kt").read_text(encoding="utf-8")
        self.assertIn("Intent.ACTION_CREATE_DOCUMENT",s)
        self.assertIn("resultCode == RESULT_OK && uri != null",s)
        self.assertIn("OwnerChatBackupV1.exportToOwnerUri",s)
    def test_activity_not_exported_and_owner_menu_only(self):
        manifest=(ROOT/"AndroidManifest.xml").read_text(encoding="utf-8")
        self.assertIn('android:name=".history.OwnerChatBackupActivityV1" android:exported="false"',manifest)
        main=(ROOT/"java/com/sadusor/orionv3/MainActivity.kt").read_text(encoding="utf-8")
        self.assertIn('menu.add(0, 39021, 0, "Export chat backup")',main)
        self.assertIn('packageName == "com.sadusor.orionv3"',main)
    def test_no_network_activation_from_backup_ui(self):
        s=(ROOT/"java/com/sadusor/orionv3/history/OwnerChatBackupActivityV1.kt").read_text(encoding="utf-8")
        self.assertNotIn("archive_sync_opt_in",s)
        self.assertNotIn("archive_device_capability",s)
if __name__=="__main__": unittest.main()
