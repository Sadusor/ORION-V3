import unittest
from unittest.mock import patch
from orion_v3.work_loop.windows_host_isolation_inventory_v1 import inspect_host

class WindowsHostIsolationInventoryTests(unittest.TestCase):
    @patch("orion_v3.work_loop.windows_host_isolation_inventory_v1.os.name", "posix")
    def test_non_windows_denied(self):
        self.assertFalse(inspect_host()["qualified"])
    @patch("orion_v3.work_loop.windows_host_isolation_inventory_v1.os.name", "nt")
    @patch("orion_v3.work_loop.windows_host_isolation_inventory_v1.shutil.which", return_value=None)
    def test_missing_tools(self, _):
        result = inspect_host()
        self.assertEqual(result["checks"]["powershell"], "MISSING")
        self.assertFalse(result["qualified"])
    @patch("orion_v3.work_loop.windows_host_isolation_inventory_v1.os.name", "nt")
    @patch("orion_v3.work_loop.windows_host_isolation_inventory_v1.shutil.which", return_value="present")
    def test_available_still_unqualified(self, _):
        class Result:
            returncode = 0
        result = inspect_host(runner=lambda *a, **k: Result())
        self.assertEqual(result["checks"]["whoami"], "AVAILABLE")
        self.assertFalse(result["qualified"])
    @patch("orion_v3.work_loop.windows_host_isolation_inventory_v1.os.name", "nt")
    @patch("orion_v3.work_loop.windows_host_isolation_inventory_v1.shutil.which", return_value="present")
    def test_command_failure(self, _):
        class Result:
            returncode = 1
        result = inspect_host(runner=lambda *a, **k: Result())
        self.assertEqual(result["checks"]["powershell"], "FAILED")
        self.assertFalse(result["qualified"])
    @patch("orion_v3.work_loop.windows_host_isolation_inventory_v1.os.name", "nt")
    @patch("orion_v3.work_loop.windows_host_isolation_inventory_v1.shutil.which", return_value="present")
    def test_exception(self, _):
        def fail(*a, **k):
            raise OSError("blocked")
        self.assertEqual(inspect_host(runner=fail)["checks"]["whoami"], "FAILED")

if __name__ == "__main__":
    unittest.main()
