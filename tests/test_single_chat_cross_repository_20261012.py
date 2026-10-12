import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.orion_v3.modules.gitea_multi_repo_chat_v1 import (
    named_repo_scope, multi_repo_chat_request, MultiRepoDocumentChatBrain,
)


class SingleChatCrossRepositoryTests(unittest.TestCase):
    def test_original_owner_question_routes_to_authorized_cross_repo(self):
        with tempfile.TemporaryDirectory() as d:
            request = named_repo_scope(
                "Search MyGitea2 and tell me what UI button code exists in my repositories.",
                state_dir=d,
            )
            self.assertEqual(request["kind"], "cross_repository")
            self.assertEqual(len(request["catalog"]), 2)

    def test_show_source_code_is_not_inventory(self):
        with tempfile.TemporaryDirectory() as d:
            request = named_repo_scope(
                "Show UI button code across my repositories",
                state_dir=d,
            )
            self.assertIsNotNone(request)
            self.assertEqual(request["kind"], "cross_repository")

    def test_cross_repo_does_not_route_other_host(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(named_repo_scope(
                "Find button code across my GitHub repositories", state_dir=d
            ))

    def test_named_repo_and_inventory_keep_existing_behavior(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(named_repo_scope("Show PayDay roadmap", state_dir=d)["kind"], "repository")
            self.assertEqual(named_repo_scope("How many repositories in MyGitea2?", state_dir=d)["kind"], "inventory")
            self.assertIsNone(named_repo_scope("Search my GitHub repositories for UI code", state_dir=d))

    def test_catalog_not_visible_inventory_controls_scope(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "authorized-gitea-repositories.json").write_text(
                json.dumps({"repositories": [
                    {"alias": "alpha", "owner": "MyGitea", "name": "Alpha", "project": "alpha", "authorized": True},
                    {"alias": "beta", "owner": "MyGitea", "name": "Beta", "project": "beta", "authorized": False},
                ]})
            )
            request = named_repo_scope("Find button code across my repositories", state_dir=d)
            self.assertEqual([r.project for r in request["catalog"]], ["alpha"])

    def test_no_implicit_broad_scope(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(named_repo_scope("What does ORION do?", state_dir=d))


if __name__ == "__main__":
    unittest.main()
