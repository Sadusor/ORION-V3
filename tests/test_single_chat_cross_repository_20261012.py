import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.orion_v3.modules.gitea_multi_repo_chat_v1 import (
    named_repo_scope, multi_repo_chat_request, MultiRepoDocumentChatBrain, _focused_code_query, _rank_evidence_hits,
)


class SingleChatCrossRepositoryTests(unittest.TestCase):
    def test_evidence_rank_preserves_citations_and_deduplicates(self):
        def hit(path, part):
            return {"snippet": f"Repository: MyGitea/ORION-V3\\nFile: {path}\\nCommit: abc\\nsource",
                    "identifier": f"MyGitea/ORION-V3:abc:{path}:{part}",
                    "citation": f"MyGitea2 MyGitea/ORION-V3 abc {path} part {part}",
                    "project": "orion-v3", "trust": "context_only"}
        hits = [hit("android/app/src/main/java/ChatHistoryStore.kt", i) for i in range(8)]
        hits += [hit("ui/strata/modules/chat-reading-controls-v1.js", 0),
                 hit("ui/strata/modules/conversation-controls-v2.js", 0)]
        selected = _rank_evidence_hits(hits, "Where did we build the UI controls?", limit=3)
        self.assertTrue(selected[0]["identifier"].endswith("chat-reading-controls-v1.js:0"))
        self.assertEqual(len({x["identifier"].rsplit(":", 1)[0] for x in selected}), 3)
        self.assertTrue(all(x["citation"].startswith("MyGitea2 ") for x in selected))

    def test_original_owner_question_routes_to_authorized_cross_repo(self):
        with tempfile.TemporaryDirectory() as d:
            request = named_repo_scope(
                "Search MyGitea2 and tell me what UI button code exists in my repositories.",
                state_dir=d,
            )
            self.assertEqual(request["kind"], "cross_repository")
            self.assertEqual(len(request["catalog"]), 2)

    def test_owner_question_focuses_ui_code_search(self):
        focused = _focused_code_query(
            "Search MyGitea2 and tell me what UI button code exists in my repositories. "
            "Include repository names, file paths, and source references."
        )
        self.assertIn("button", focused.split())
        self.assertIn("onclick", focused.split())
        self.assertNotIn("tell", focused.split())
        self.assertNotIn("repositories", focused.split())

    def test_identifier_survives_query_focus(self):
        focused = _focused_code_query("Find StopAllButton in my repositories")
        self.assertIn("stopallbutton", focused.split())

    def test_natural_language_gitea_source_question(self):
        with tempfile.TemporaryDirectory() as d:
            for question in (
                "What controls have we built in MyGitea2?",
                "Where is the interface implemented in MyGitea2?",
                "How does the UI work in Gitea?",
            ):
                with self.subTest(question=question):
                    self.assertEqual(
                        named_repo_scope(question, state_dir=d)["kind"],
                        "cross_repository",
                    )

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
