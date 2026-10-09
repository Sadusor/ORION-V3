"""Offline bridge tests; fake vault and fake HTTP only."""
import unittest
from orion_v3.work_loop.openrouter_vault_bridge import request_openrouter, CloudRequestError

class Vault:
    def __init__(self, entry):
        self.entry = entry
        self.secret_calls = 0
    def get(self, provider_id):
        assert provider_id == "or-test"
        return self.entry
    def get_secret(self, provider_id):
        self.secret_calls += 1
        return "placeholder-key"

class Response:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, n): return b'{"choices":[{"message":{"content":"PLAN"}}]}'

class BridgeTests(unittest.TestCase):
    def invoke(self, vault, stopped=lambda: False):
        return request_openrouter(vault=vault, provider_id="or-test", model="google/gemma-4-31b-it:free",
                                  prompt="proposal only", stop_requested=stopped,
                                  transport=lambda req, timeout: Response())
    def test_success(self):
        vault = Vault({"adapter":"openrouter", "enabled":True})
        self.assertEqual(self.invoke(vault)["text"], "PLAN")
        self.assertEqual(vault.secret_calls, 1)
    def test_pre_stop(self):
        vault = Vault({"adapter":"openrouter", "enabled":True})
        with self.assertRaises(CloudRequestError) as ctx: self.invoke(vault, lambda: True)
        self.assertEqual(ctx.exception.category, "STOPPED")
        self.assertEqual(vault.secret_calls, 0)
    def test_wrong_adapter(self):
        vault = Vault({"adapter":"groq", "enabled":True})
        with self.assertRaises(CloudRequestError) as ctx: self.invoke(vault)
        self.assertEqual(ctx.exception.category, "WRONG_ADAPTER")
        self.assertEqual(vault.secret_calls, 0)
    def test_disabled(self):
        vault = Vault({"adapter":"openrouter", "enabled":False})
        with self.assertRaises(CloudRequestError) as ctx: self.invoke(vault)
        self.assertEqual(ctx.exception.category, "PROVIDER_DISABLED")
        self.assertEqual(vault.secret_calls, 0)
    def test_unregistered(self):
        vault = Vault(None)
        with self.assertRaises(CloudRequestError) as ctx: self.invoke(vault)
        self.assertEqual(ctx.exception.category, "PROVIDER_NOT_REGISTERED")
        self.assertEqual(vault.secret_calls, 0)

if __name__ == "__main__": unittest.main()
