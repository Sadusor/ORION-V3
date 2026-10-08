"""No-network, no-approval, no-execution unit tests for read-only overview."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from read_only_overview import snapshot, MAX_PROJECTS

class OverviewTests(unittest.TestCase):
    def test_missing_root(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(snapshot([Path(temp)/"missing"])["projects"], [])
    def test_explicit_root_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/"allowed";root.mkdir()
            (root/"project-a").mkdir()
            (Path(temp)/"secret").mkdir()
            names=[p["name"] for p in snapshot([root])["projects"]]
            self.assertEqual(names, ["project-a"])
    def test_hidden_and_symlinks_not_traversed(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/"allowed";root.mkdir()
            (root/".hidden").mkdir()
            (root/"normal").mkdir()
            names=[p["name"] for p in snapshot([root])["projects"]]
            self.assertEqual(names, ["normal"])
    def test_bounded(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for i in range(30): (root/("p"+str(i))).mkdir()
            self.assertLessEqual(len(snapshot([root])["projects"]),MAX_PROJECTS)
    def test_no_git_execution_without_dotgit(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/"ordinary").mkdir()
            with patch("read_only_overview.subprocess.run") as run:
                snapshot([root])
                run.assert_not_called()

if __name__=="__main__":
    unittest.main()
