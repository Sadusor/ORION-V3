"""Offline OpenRouter catalog tests."""
import unittest
from orion_v3.work_loop.openrouter_catalog import normalize_catalog
from orion_v3.work_loop.cloud_family_selection import select_distinct

class OpenRouterTests(unittest.TestCase):
    def test_valid(self):
        rows = normalize_catalog({"data": [{"id": "deepseek/deepseek-chat", "context_length": 64000,
                                             "pricing": {"prompt": "0", "completion": "0"}}]})
        self.assertEqual(rows[0]["family"], "deepseek")
        self.assertEqual(rows[0]["provider"], "openrouter")
    def test_invalid(self):
        with self.assertRaises(ValueError):
            normalize_catalog({"data": {}})
    def test_ignores_unknown(self):
        self.assertEqual(normalize_catalog({"data": [{"id": "unknown/random"}]}), [])
    def test_cross_provider_same_family(self):
        models = normalize_catalog({"data": [{"id": "openai/gpt-oss-120b"}]})
        models += [{"provider": "groq", "model": "openai/gpt-oss-20b",
                    "reviewer_id": "groq:openai/gpt-oss-20b", "available": True}]
        self.assertEqual(len(select_distinct(models)), 1)

if __name__ == "__main__":
    unittest.main()
