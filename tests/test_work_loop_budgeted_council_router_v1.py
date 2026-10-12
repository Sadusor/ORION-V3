import unittest
from orion_v3.work_loop.budgeted_council_router_v1 import (
    BudgetedCouncilRouter, ModelRoute, ModelResponse, Usage)
from orion_v3.work_loop.offline_coding_council_v1 import run_offline_council
from orion_v3.work_loop.role_contracts_v1 import Role, TrustedBindings

ROUTES = (
    ModelRoute(Role.GOVERNOR, "ollama", "qwen-local", 500, 16000),
    ModelRoute(Role.CODER, "deepseek", "deepseek-coder", 500, 16000),
    ModelRoute(Role.REVIEWER, "xai", "grok-reviewer", 500, 16000),
)

class RouterTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.stop = False
        self.cost = 0.0

    def transport(self, route, system, question):
        self.calls.append(route.role)
        return ModelResponse("response for " + route.role.value, Usage(10, 20, self.cost))

    def router(self, **kw):
        args = dict(routes=ROUTES, transport=self.transport,
            stop_requested=lambda: self.stop, max_total_usd=0.01)
        args.update(kw)
        return BudgetedCouncilRouter(**args)

    def test_full_council_with_routed_transport(self):
        router = self.router()
        scope = TrustedBindings("orion", "T1", "owner/repo", "a"*40,
            ("new.py",), (), "dry_run", "test")
        result = run_offline_council(bindings=scope, objective="add isolated module",
            invoke=router.invoke, stop_requested=lambda: self.stop)
        self.assertEqual(result.status, "REVIEWED_NOT_EXECUTED")
        self.assertEqual(self.calls, [Role.GOVERNOR, Role.CODER,
                                      Role.REVIEWER, Role.GOVERNOR])
        self.assertEqual(router.calls, 4)

    def test_call_cap(self):
        router = self.router(max_calls=1)
        router.invoke(Role.GOVERNOR, "system", "task")
        with self.assertRaises(ValueError):
            router.invoke(Role.GOVERNOR, "system", "task")
        self.assertEqual(len(self.calls), 1)

    def test_spending_cap_rejects_result(self):
        self.cost = 0.02
        with self.assertRaises(ValueError):
            self.router().invoke(Role.CODER, "system", "task")

    def test_zero_cost_default_denies_charge(self):
        self.cost = 0.001
        with self.assertRaises(ValueError):
            self.router(max_total_usd=0.0).invoke(Role.CODER, "system", "task")

    def test_stop_before_request(self):
        self.stop = True
        with self.assertRaises(ValueError):
            self.router().invoke(Role.CODER, "system", "task")
        self.assertFalse(self.calls)

    def test_stop_after_request(self):
        def transport(*args):
            self.stop = True
            return ModelResponse("response", Usage(1, 1, 0.0))
        with self.assertRaises(ValueError):
            self.router(transport=transport).invoke(Role.CODER, "system", "task")

    def test_missing_usage_denied(self):
        with self.assertRaises(ValueError):
            self.router(transport=lambda *args: "untrusted").invoke(
                Role.CODER, "system", "task")

    def test_input_cap(self):
        with self.assertRaises(ValueError):
            self.router().invoke(Role.CODER, "x"*16000, "extra")

    def test_wrong_role_routes_denied(self):
        with self.assertRaises(ValueError):
            self.router(routes=(ROUTES[0], ROUTES[0], ROUTES[2]))

    def test_output_token_limit(self):
        with self.assertRaises(ValueError):
            self.router(transport=lambda *args: ModelResponse(
                "long", Usage(1, 501, 0.0))).invoke(Role.CODER, "system", "task")

if __name__ == "__main__": unittest.main()
