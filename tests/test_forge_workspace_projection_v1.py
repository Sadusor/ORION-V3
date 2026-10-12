import unittest

from orion_v3.work_loop.forge_workspace_projection_v1 import (
    WorkspaceTask, project_workspace_view,
)


class ForgeWorkspaceProjectionTests(unittest.TestCase):
    def view(self, tasks, **kw):
        return project_workspace_view(
            "project-a", tasks, current_revision="abc123",
            source_authenticated=True, **kw
        )

    def test_empty_view_is_non_executing(self):
        v = self.view([])
        self.assertTrue(v["read_only"])
        self.assertFalse(v["can_execute"])
        self.assertFalse(v["can_approve"])
        self.assertEqual(v["tasks"], [])

    def test_review_and_approval_visible(self):
        v = self.view([WorkspaceTask(
            "t1", "project-a", "Review proposal", "awaiting_approval",
            coder="Groq", reviewer="DeepSeek", pending_approval=True,
        )])
        self.assertEqual(v["pending_approval_count"], 1)
        self.assertEqual(v["tasks"][0]["reviewer"], "DeepSeek")

    def test_cross_project_denied(self):
        with self.assertRaises(ValueError):
            self.view([WorkspaceTask("t1", "project-b", "Other", "queued")])

    def test_untrusted_source_denied(self):
        with self.assertRaises(ValueError):
            project_workspace_view("project-a", [], current_revision="abc123",
                                   source_authenticated=False)

    def test_duplicate_tasks_denied(self):
        t = WorkspaceTask("t1", "project-a", "Task", "queued")
        with self.assertRaises(ValueError):
            self.view([t, t])

    def test_approval_mismatch_denied(self):
        with self.assertRaises(ValueError):
            self.view([WorkspaceTask("t1", "project-a", "Task", "queued",
                                     pending_approval=True)])

    def test_unknown_status_denied(self):
        with self.assertRaises(ValueError):
            self.view([WorkspaceTask("t1", "project-a", "Task", "running_shell")])


if __name__ == "__main__":
    unittest.main()
