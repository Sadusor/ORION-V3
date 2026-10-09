import unittest
from orion_v3.work_loop.donor_catalog_audit import classify


class DonorCatalogAuditTests(unittest.TestCase):
    def test_available_does_not_mean_free(self):
        result = classify({'models': [{'provider': 'groq', 'model': 'openai/gpt-oss-120b', 'reviewer_id': 'x', 'available': True}]})
        self.assertEqual(len(result['candidates']), 1)
        self.assertEqual(result['candidates'][0]['free_entitlement'], 'UNVERIFIED')
        self.assertEqual(result['verified_free_families'], [])
        self.assertEqual(result['live_calls'], 0)

    def test_excludes_local_and_audio(self):
        result = classify({'models': [{'provider': 'ollama', 'model': 'qwen3'},
                                      {'provider': 'groq', 'model': 'whisper-audio'},
                                      {'provider': 'gemini', 'model': 'gemini-2.5-flash'}]})
        self.assertEqual([x['family'] for x in result['candidates']], ['gemini'])

    def test_empty_catalog(self):
        self.assertEqual(classify({})['candidates'], [])


if __name__ == '__main__':
    unittest.main()
