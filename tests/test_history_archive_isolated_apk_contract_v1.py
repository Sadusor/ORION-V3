import unittest
from pathlib import Path

ROOT = Path("android")
class IsolatedArchiveBuildContract(unittest.TestCase):
    def test_isolated_package_is_distinct(self):
        s = (ROOT / "app/build.gradle.kts").read_text(encoding="utf-8")
        self.assertIn('orionIsolatedArchiveTest', s)
        self.assertIn('com.sadusor.orionv3.archivequal', s)
        self.assertIn('else "com.sadusor.orionv3"', s)

    def test_label_and_provider_are_package_specific(self):
        manifest = (ROOT / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
        self.assertIn('orionAppLabel', manifest)
        self.assertIn('applicationId', manifest)

    def test_test_apk_cannot_connect_to_production_pc(self):
        s = (ROOT / "app/src/main/java/com/sadusor/orionv3/online/OrionPcBridge.kt").read_text(encoding="utf-8")
        self.assertIn('require(activity.packageName == "com.sadusor.orionv3")', s)
        self.assertIn('Isolated archive APK: production PC connectivity disabled', s)
        self.assertIn('"/api/update/main"', s)
        self.assertIn('"/apk"', s)

if __name__ == "__main__":
    unittest.main()
