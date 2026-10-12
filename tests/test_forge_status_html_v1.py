import unittest

from orion_v3.work_loop.forge_workspace_projection_v1 import WorkspaceTask, project_workspace_view
from orion_v3.work_loop.forge_status_html_v1 import render_forge_status_html


def sample():
    return project_workspace_view(
        "orion", [WorkspaceTask("1", "orion", "Review <script>alert(1)</script>",
                                "awaiting_approval", coder="Groq", reviewer="DeepSeek",
                                pending_approval=True)],
        current_revision="abc", source_authenticated=True)


class ForgeStatusHTMLTests(unittest.TestCase):
    def test_static_view_and_escaped_content(self):
        page = render_forge_status_html(sample())
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>", page)
        self.assertIn("Pending approvals: 1", page)

    def test_no_execution_surfaces(self):
        page = render_forge_status_html(sample()).lower()
        for token in ("<script", "<iframe", "<form", "onclick=", "filesystem", "fetch(", "eval("):
            self.assertNotIn(token, page)

    def test_bad_schema_denied(self):
        view = sample()
        view["schema"] = "unknown"
        with self.assertRaises(ValueError):
            render_forge_status_html(view)

    def test_authority_escalation_denied(self):
        view = sample()
        view["can_execute"] = True
        with self.assertRaises(ValueError):
            render_forge_status_html(view)

    def test_approval_count_tampering_denied(self):
        view = sample()
        view["pending_approval_count"] = 0
        with self.assertRaises(ValueError):
            render_forge_status_html(view)

    def test_cross_record_duplicate_denied(self):
        view = sample()
        view["tasks"].append(dict(view["tasks"][0]))
        view["pending_approval_count"] = 2
        with self.assertRaises(ValueError):
            render_forge_status_html(view)

    def test_empty_project_render(self):
        view = project_workspace_view("orion", [], current_revision="abc", source_authenticated=True)
        self.assertIn("No tasks reported", render_forge_status_html(view))


if __name__ == "__main__":
    unittest.main()
