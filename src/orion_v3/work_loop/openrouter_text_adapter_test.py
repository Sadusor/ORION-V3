"""Offline HTTP mock tests; never contact OpenRouter."""
import io
import json
import unittest
from urllib.error import HTTPError
from orion_v3.work_loop.openrouter_text_adapter import completion, CloudRequestError

class Response:
    status = 200
    def __init__(self, body): self.body = body
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, limit): return self.body[:limit]

class AdapterTests(unittest.TestCase):
    def test_success(self):
        def transport(req, timeout):
            self.assertEqual(timeout, 3)
            self.assertEqual(json.loads(req.data)["stream"], False)
            self.assertEqual(json.loads(req.data)["max_tokens"], 1200)
            return Response(b'{"choices":[{"message":{"content":"READY"}}]}')
        result = completion(model="google/gemma-4-31b-it:free", prompt="ping",
                            api_key="test-placeholder", timeout=3, transport=transport)
        self.assertEqual(result["text"], "READY")
    def test_paid_model_blocked_before_http(self):
        def forbidden(req, timeout):
            self.fail("paid model must not make an HTTP request")
        with self.assertRaises(CloudRequestError) as ctx:
            completion(model="openai/paid-model", prompt="ping",
                       api_key="placeholder", transport=forbidden)
        self.assertEqual(ctx.exception.category, "PAID_MODEL_BLOCKED")

    def test_unauthorized(self):
        def transport(req, timeout):
            raise HTTPError(req.full_url, 401, "denied", {}, None)
        with self.assertRaises(CloudRequestError) as ctx:
            completion(model="a/b:free", prompt="ping", api_key="placeholder", transport=transport)
        self.assertEqual(ctx.exception.category, "AUTH")
    def test_rate_limit(self):
        def transport(req, timeout):
            raise HTTPError(req.full_url, 429, "limit", {}, None)
        with self.assertRaises(CloudRequestError) as ctx:
            completion(model="a/b:free", prompt="ping", api_key="placeholder", transport=transport)
        self.assertEqual(ctx.exception.category, "RATE_LIMIT")
    def test_malformed(self):
        with self.assertRaises(CloudRequestError) as ctx:
            completion(model="a/b:free", prompt="ping", api_key="placeholder",
                       transport=lambda req, timeout: Response(b'{}'))
        self.assertEqual(ctx.exception.category, "MALFORMED_RESPONSE")
    def test_no_key(self):
        with self.assertRaises(CloudRequestError) as ctx:
            completion(model="a/b:free", prompt="ping", api_key="")
        self.assertEqual(ctx.exception.category, "NO_CREDENTIAL")
    def test_invalid_prompt(self):
        with self.assertRaises(ValueError):
            completion(model="a/b:free", prompt="x"*24001, api_key="placeholder")

if __name__ == "__main__":
    unittest.main()
