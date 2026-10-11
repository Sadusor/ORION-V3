import unittest
from unittest.mock import patch, Mock
from src.orion_v3.modules.gitea_dpapi_credential_v1 import read_gitea_token

class CredentialTests(unittest.TestCase):
    def test_environment_override(self):
        with patch.dict("os.environ", {"ORION_GITEA_TOKEN":"test-value"}):
            self.assertEqual(read_gitea_token(),"test-value")
    def test_other_platform_without_override(self):
        with patch.dict("os.environ", {"ORION_GITEA_TOKEN":""}):
            with patch("src.orion_v3.modules.gitea_dpapi_credential_v1.sys.platform","linux"):
                self.assertEqual(read_gitea_token(),"")
    def test_windows_failed_decrypt(self):
        with patch.dict("os.environ", {"ORION_GITEA_TOKEN":""}):
            with patch("src.orion_v3.modules.gitea_dpapi_credential_v1.sys.platform","win32"):
                with patch("src.orion_v3.modules.gitea_dpapi_credential_v1.subprocess.run",return_value=Mock(returncode=1,stdout="")):
                    self.assertEqual(read_gitea_token(),"")
    def test_windows_success(self):
        with patch.dict("os.environ", {"ORION_GITEA_TOKEN":""}):
            with patch("src.orion_v3.modules.gitea_dpapi_credential_v1.sys.platform","win32"):
                with patch("src.orion_v3.modules.gitea_dpapi_credential_v1.subprocess.run",return_value=Mock(returncode=0,stdout="synthetic")):
                    self.assertEqual(read_gitea_token(),"synthetic")

if __name__=="__main__":
    unittest.main()
