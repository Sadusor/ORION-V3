"""Non-mutating readiness checks; no production activation, backups or writes."""
import pathlib
import unittest

SERVER = pathlib.Path("src/orion_v3/product_server.py")
BRIDGE = pathlib.Path("android/app/src/main/java/com/sadusor/orionv3/online/OrionPcBridge.kt")
BUILD = pathlib.Path("android/app/build.gradle.kts")
MANIFEST = pathlib.Path("android/app/src/main/AndroidManifest.xml")

class ProductionArchiveReadiness(unittest.TestCase):
    def test_archive_routes_remain_explicitly_disabled(self):
        s = SERVER.read_text(encoding="utf-8")
        self.assertIn('os.environ.get("ORION_ARCHIVE_HTTP_OPT_IN") != "1"', s)
        self.assertIn('os.environ.get("ORION_HISTORY_ARCHIVE_V1_EXPERIMENTAL") != "1"', s)
        self.assertIn('ORION_ARCHIVE_TEST_ROOT', s)
        self.assertIn('X-Orion-Archive-Device', s)
        self.assertIn('X-Orion-Archive-Owner', s)

    def test_android_existing_sync_and_update_path_preserved(self):
        s = BRIDGE.read_text(encoding="utf-8")
        self.assertIn('"/api/chat-history/sync"', s)
        self.assertIn('"/api/update/main"', s)
        self.assertIn('"/apk"', s)
        self.assertIn('fun installLatestApk(requestId: String)', s)
        self.assertIn('prefs.getBoolean("archive_sync_opt_in", false)', s)

    def test_production_apk_identity_retained(self):
        s = BUILD.read_text(encoding="utf-8")
        self.assertIn('else "com.sadusor.orionv3"', s)
        self.assertIn('versionCode = 9', s)
        m = MANIFEST.read_text(encoding="utf-8")
        self.assertIn('android:authorities="${applicationId}.files"', m)
        self.assertIn('orionArchiveQualificationExported', m)

if __name__ == "__main__":
    unittest.main()
