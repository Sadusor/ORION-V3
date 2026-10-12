"""Offline safety checks for the Forge staging UI candidate; not a sandbox certification."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

HTML = Path(__file__).resolve().parents[1] / "prototypes/forge/orion_forge_staging_v3.html"

class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

class ForgeStagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML.read_text(encoding="utf-8")
        cls.dom = Elements()
        cls.dom.feed(cls.html)

    def test_original_three_pane_features(self):
        for x in ('id="dock"', 'id="msgs"', 'id="ptabs"', 'data-p="changes"', 'data-p="files"'):
            self.assertIn(x, self.html)

    def test_review_only(self):
        self.assertIn("mode='review'", self.html)
        self.assertNotIn("mode='auto'", self.html)
        self.assertNotIn("Auto-apply</", self.html)

    def test_disk_writes_denied(self):
        self.assertRegex(self.html, r"async function diskWrite\(p,c\)\{throw Error\(")
        self.assertRegex(self.html, r"async function commit\(p,c\)\{throw Error\(")

    def test_disk_deletion_denied(self):
        self.assertRegex(self.html, r"async function diskDelete\(p\)\{throw Error\(")

    def test_staged_deletion(self):
        self.assertIn("ws.staged.set(p,null)", self.html)

    def test_no_file_write_handle(self):
        self.assertNotIn("createWritable(", self.html)
        self.assertNotIn("getDirectoryHandle(s,{create:true})", self.html)

    def test_no_executable_preview(self):
        self.assertNotIn("<iframe", self.html.lower())
        self.assertNotIn("srcdoc", self.html.lower())
        self.assertNotIn("function previewHTML(", self.html)
        self.assertIn("Live preview disabled.", self.html)

    def test_no_persisted_keys(self):
        self.assertIn("let keys={}", self.html)
        self.assertNotIn("forge.keys", self.html)

    def test_approval_remains_external(self):
        self.assertIn("async function accept(p){note('ORION approval required", self.html)
        self.assertNotIn("await commit(", self.html)

    def test_folder_read_only(self):
        self.assertIn("showDirectoryPicker({mode:'read'})", self.html)

    def test_no_embedded_auto_execute(self):
        self.assertNotIn("child_process", self.html)
        self.assertNotIn("subprocess", self.html)

    def test_required_controls_present(self):
        ids = {attrs.get("id") for _, attrs in self.dom.tags}
        for x in ("stop", "send", "mpop", "pb", "in"):
            self.assertIn(x, ids)

if __name__ == "__main__":
    unittest.main()
