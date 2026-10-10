import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
SERVER=ROOT/"src"/"orion_v3"/"product_server.py"

class RouteSourceContracts(unittest.TestCase):
    def test_opt_in_route_and_server_allowlist(self):
        text=SERVER.read_text(encoding="utf-8")
        self.assertIn('if path == "/api/gitea/context/preview":',text)
        self.assertIn('body.get("project_id", "")',text)
        self.assertIn('!= "orion-v3"',text)
        self.assertIn('!= "MyGitea/ORION-V3"',text)
        self.assertIn('allowed_repository="MyGitea/ORION-V3"',text)
        self.assertIn('max_total_chars=12000',text)
    def test_existing_draft_preserved(self):
        text=SERVER.read_text(encoding="utf-8")
        self.assertIn('if path == "/api/local-hand/draft":',text)
        self.assertIn('started = LOCAL_BRAIN.start(',text)
    def test_server_compiles(self):
        compile(SERVER.read_text(encoding="utf-8"),str(SERVER),"exec")

if __name__=="__main__": unittest.main()
