import unittest
from orion_v3.work_loop.gitea_write_preflight_v1 import build_write_intent, validate_write_endpoint


def intent(**kw):
    d = dict(project_id="orion", task_id="T1", repository="owner/repo",
             branch="orion/tasks/T1", expected_base_sha="a"*40, operation="commit_files")
    d.update(kw)
    return build_write_intent(**d)


class GiteaWritePreflightTests(unittest.TestCase):
    def test_scoped_commit_intent(self):
        self.assertEqual(intent().operation, "commit_files")

    def test_scoped_branch_creation(self):
        self.assertEqual(intent(operation="create_branch").operation, "create_branch")

    def test_protected_branch_rejected(self):
        for branch in ("main", "master", "orion/tasks/../main", "orion/tasks/a.lock",
                       "orion/tasks/a//b", "orion/tasks/a\\b", "orion/tasks/a@{x}"):
            with self.subTest(branch=branch), self.assertRaises(ValueError):
                intent(branch=branch)

    def test_unscoped_branch_rejected(self):
        with self.assertRaises(ValueError):
            intent(branch="feature/test")

    def test_bad_base_sha_rejected(self):
        with self.assertRaises(ValueError):
            intent(expected_base_sha="HEAD")

    def test_force_push_and_merge_rejected(self):
        for op in ("force_push", "merge", "delete_branch", "push_main"):
            with self.subTest(op=op), self.assertRaises(ValueError):
                intent(operation=op)

    def test_repository_escape_rejected(self):
        for repo in ("owner/../repo", "https://gitea/repo", "owner\\repo", "owner/repo@evil"):
            with self.subTest(repo=repo), self.assertRaises(ValueError):
                intent(repository=repo)

    def test_https_endpoint(self):
        self.assertEqual(validate_write_endpoint("https://gitea.example/api/v1"), "https://gitea.example/api/v1")

    def test_local_http_endpoint(self):
        self.assertEqual(validate_write_endpoint("http://127.0.0.1:3000/api/v1"), "http://127.0.0.1:3000/api/v1")

    def test_remote_http_rejected(self):
        with self.assertRaises(ValueError):
            validate_write_endpoint("http://gitea.example/api/v1")

    def test_embedded_credentials_rejected(self):
        with self.assertRaises(ValueError):
            validate_write_endpoint("https://user:token@gitea.example/api/v1")

    def test_unexpected_api_path_rejected(self):
        with self.assertRaises(ValueError):
            validate_write_endpoint("https://gitea.example/api/v1/repos/owner/repo")


if __name__ == "__main__":
    unittest.main()
