"""Offline checks for four-family selection, no cloud requests."""
import unittest
from orion_v3.work_loop.cloud_family_selection import family, select_distinct

class SelectionTests(unittest.TestCase):
    def test_family(self):
        self.assertEqual(family("openai/gpt-oss-120b"), "gpt-oss")
        self.assertEqual(family("qwen/qwen3.8-27b"), "qwen")
    def test_same_family_rejected(self):
        models = [
            {"provider": "groq", "model": "openai/gpt-oss-120b", "reviewer_id": "g:120", "available": True},
            {"provider": "openrouter", "model": "openai/gpt-oss-20b", "reviewer_id": "o:20", "available": True},
            {"provider": "groq", "model": "qwen/qwen3.8-27b", "reviewer_id": "g:q", "available": True},
            {"provider": "gemini", "model": "gemini-2.5-pro", "reviewer_id": "g:gem", "available": True},
        ]
        selected = select_distinct(models)
        self.assertEqual(len(selected), 3)
        self.assertEqual(len({x["family"] for x in selected}), 3)
    def test_excludes_unavailable(self):
        self.assertEqual(select_distinct([{"provider": "openrouter", "model": "deepseek-v4", "reviewer_id": "o:d", "available": False}]), [])
    def test_preview_excluded(self):
        self.assertEqual(select_distinct([{"provider": "gemini", "model": "gemini-preview", "reviewer_id": "g:p", "available": True}]), [])

if __name__ == "__main__":
    unittest.main()
