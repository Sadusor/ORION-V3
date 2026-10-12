"""Offline regression checks for the isolated Qwen investigation candidate."""
import unittest
from orion_v3.modules.qwen_readonly_investigation_candidate_v1 import investigate


class InvestigationTests(unittest.TestCase):
    def test_refines_search_after_irrelevant_evidence(self):
        plans = iter([
            '{"repository":"MyGitea/ORION-V3","query":"UI buttons"}',
            '{"repository":"MyGitea/ORION-V3","query":"button click handler implementation"}',
            '{"done":true}',
        ])
        calls = []
        def retrieve(repo, query):
            calls.append((repo, query))
            if query == "UI buttons":
                return [{"repository":repo,"path":"docs/ROADMAP.md","commit":"abc","excerpt":"Roadmap"}]
            return [{"repository":repo,"path":"ui/buttons.tsx","commit":"abc","excerpt":"onClick={save}"}]
        result = investigate("Find UI button code", authorized_repositories=("MyGitea/ORION-V3",),
                             propose=lambda _: next(plans), retrieve=retrieve)
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(result.evidence), 2)
        self.assertFalse(result.exhausted)

    def test_rejects_unauthorized_repo_without_retrieval(self):
        calls = []
        result = investigate("Find buttons", authorized_repositories=("MyGitea/ORION-V3",),
                             propose=lambda _: '{"repository":"Other/Private","query":"buttons"}',
                             retrieve=lambda *args: calls.append(args))
        self.assertEqual(calls, [])
        self.assertIn("repository_not_authorized", result.errors)

    def test_rejects_spoofed_provenance(self):
        result = investigate("Find buttons", authorized_repositories=("MyGitea/ORION-V3",),
                             propose=lambda _: '{"repository":"MyGitea/ORION-V3","query":"buttons"}',
                             retrieve=lambda repo, query: [{"repository":"Other/Private","path":"x","commit":"abc","excerpt":"x"}])
        self.assertFalse(result.evidence)
        self.assertIn("invalid_provenance", result.errors)

    def test_deduplicates_same_file(self):
        plans = iter(['{"repository":"MyGitea/ORION-V3","query":"button"}',
                      '{"repository":"MyGitea/ORION-V3","query":"click"}'])
        hit = {"repository":"MyGitea/ORION-V3","path":"ui/x.kt","commit":"abc","excerpt":"button"}
        result = investigate("Find buttons", authorized_repositories=("MyGitea/ORION-V3",),
                             propose=lambda _: next(plans), retrieve=lambda *args:[hit], max_rounds=2)
        self.assertEqual(len(result.evidence), 1)

    def test_repeated_query_stops(self):
        result = investigate("Find buttons", authorized_repositories=("MyGitea/ORION-V3",),
                             propose=lambda _: '{"repository":"MyGitea/ORION-V3","query":"button"}',
                             retrieve=lambda *args: [], max_rounds=3)
        self.assertEqual(len(result.queries), 1)
        self.assertIn("repeated_query", result.errors)

    def test_budget_restricts_evidence(self):
        result = investigate("Find buttons", authorized_repositories=("MyGitea/ORION-V3",),
                             propose=lambda _: '{"repository":"MyGitea/ORION-V3","query":"button"}',
                             retrieve=lambda repo,query:[{"repository":repo,"path":"ui/a.tsx","commit":"abc","excerpt":"x"*2000}],
                             max_evidence_chars=1000)
        self.assertFalse(result.evidence)

    def test_invalid_planner_json_stops(self):
        result = investigate("Find buttons", authorized_repositories=("MyGitea/ORION-V3",),
                             propose=lambda _: "not json", retrieve=lambda *args:[])
        self.assertIn("JSONDecodeError", result.errors)

    def test_no_implicit_catalog(self):
        with self.assertRaises(ValueError):
            investigate("Find buttons", authorized_repositories=(),
                        propose=lambda _: '{"done":true}', retrieve=lambda *args:[])


if __name__ == "__main__":
    unittest.main()
