"""Offline authorization/inventory checks for the additive Gitea multi-repo adapter."""
import tempfile
import unittest
from pathlib import Path
from src.orion_v3.modules.gitea_multi_repo_v1 import GiteaMultiRepoV1, AuthorizedRepo

CATALOG=(
    AuthorizedRepo("orion-v3","MyGitea","ORION-V3","orion-v3"),
    AuthorizedRepo("payday","MyGitea","PayDay","payday"),
)
class Fake:
    def _get(self,path):
        from urllib.parse import parse_qs, urlsplit
        q=parse_qs(urlsplit(path).query)
        page=int(q["page"][0])
        size=int(q["limit"][0])
        assert size == 25
        names=["ORION-V3","PayDay"]
        return [{"owner":{"login":"MyGitea"},"name":name} for name in names[(page-1)*size:page*size]]
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.adapter=GiteaMultiRepoV1(api=Fake(),state_dir=Path(self.tmp.name),catalog=CATALOG)
    def test_alias(self):
        self.assertEqual(self.adapter.resolve("PAYDAY").name,"PayDay")
        self.assertEqual(self.adapter.resolve("MyGitea/PayDay").project,"payday")
    def test_scope(self):
        with self.assertRaises(ValueError):self.adapter.resolve("not-approved")
        with self.assertRaises(ValueError):self.adapter.search("plan",project="not-approved",limit=2)
    def test_inventory(self):
        data=self.adapter.visible_inventory()
        self.assertEqual(data["count"],2)
        self.assertTrue(data["complete"])
        self.assertEqual(data["scopes"]["owner_account"]["count"],2)
        self.assertEqual(len(self.adapter.authorized_inventory()),2)
    def test_duplicate(self):
        with self.assertRaises(ValueError):
            GiteaMultiRepoV1(api=Fake(),state_dir=Path(self.tmp.name),catalog=(CATALOG[0],CATALOG[0]))
    def test_no_new_index_on_inventory(self):
        self.adapter.visible_inventory()
        self.assertFalse(self.adapter.index_path.exists())
if __name__=="__main__":unittest.main()
