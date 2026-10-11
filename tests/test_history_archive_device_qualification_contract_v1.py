import unittest
from pathlib import Path

class AndroidDeviceQualificationContract(unittest.TestCase):
    def test_isolated_disposable_database_and_actual_kotlin_paths(self):
        s = Path("android/app/src/main/java/com/sadusor/orionv3/history/ArchiveQualificationActivity.kt").read_text(encoding="utf-8")
        self.assertIn('packageName != "com.sadusor.orionv3.archivequal"', s)
        self.assertIn('orion2_disposable_qualification.db', s)
        self.assertIn('check(!file.exists())', s)
        self.assertIn('original.version = 1', s)
        self.assertIn('store.applyArchiveTombstones', s)
        self.assertIn('restarted.merge(replay.toString())', s)
        self.assertIn('"MIGRATION_PASS"', s)
        self.assertIn('"DELETE_REPLAY_RESTART_PASS"', s)

    def test_production_activity_not_exported(self):
        gradle = Path("android/app/build.gradle.kts").read_text(encoding="utf-8")
        manifest = Path("android/app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
        self.assertIn('orionArchiveQualificationExported', gradle)
        self.assertIn('"true" else "false"', gradle)
        self.assertIn('android:name=".history.ArchiveQualificationActivity"', manifest)

if __name__ == "__main__":
    unittest.main()
