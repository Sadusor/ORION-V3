import io
import json
import unittest
from unittest.mock import patch
from orion_v3.work_loop.ollama_governor_transport_v1 import ollama_governor_transport
from orion_v3.work_loop.budgeted_council_router_v1 import ModelRoute
from orion_v3.work_loop.role_contracts_v1 import Role

GOV = ModelRoute(Role.GOVERNOR, "ollama", "qwen3.5:9b", 200, 16000)
class OllamaTransportTests(unittest.TestCase):
    def test_mocked_ollama_request(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, size): return json.dumps({"done": True,
                "message": {"content": "plan"}, "prompt_eval_count": 12,
                "eval_count": 4}).encode()
        class Opener:
            def open(self, request, timeout):
                self.assert_request(request)
                return Response()
            def assert_request(self, request):
                data = json.loads(request.data)
                assert data["model"] == "qwen3.5:9b"
                assert data["messages"][0]["content"] == "scope"
                assert data["options"]["num_predict"] == 200
        with patch("urllib.request.build_opener", return_value=Opener()):
            result = ollama_governor_transport(GOV, "scope", "task")
        self.assertEqual(result.text, "plan")
        self.assertEqual(result.usage.output_tokens, 4)
        self.assertEqual(result.usage.charged_usd, 0)

    def test_cloud_role_rejected(self):
        with self.assertRaises(ValueError):
            ollama_governor_transport(ModelRoute(Role.CODER, "ollama", "qwen", 200, 100),
                                      "system", "task")

    def test_external_url_rejected(self):
        with self.assertRaises(ValueError):
            ollama_governor_transport(GOV, "system", "task", base_url="https://example.com")

    def test_credentials_in_url_rejected(self):
        with self.assertRaises(ValueError):
            ollama_governor_transport(GOV, "system", "task", base_url="http://user:pw@localhost:11434")

    def test_bad_timeout_rejected(self):
        with self.assertRaises(ValueError):
            ollama_governor_transport(GOV, "system", "task", timeout=999)

    def test_incomplete_response_rejected(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, size): return b'{"done":false,"message":{"content":"plan"}}'
        class Opener:
            def open(self, *args, **kwargs): return Response()
        with patch("urllib.request.build_opener", return_value=Opener()):
            with self.assertRaises(ValueError):
                ollama_governor_transport(GOV, "system", "task")

if __name__ == "__main__": unittest.main()
