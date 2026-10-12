import unittest
from orion_v3.work_loop.codespace_open_contract_v1 import (
    CloudRole, recognize_codespace_open, request_codespace_open, plan_coding_roles)

class CodeSpaceContractTests(unittest.TestCase):
    def test_open_intents(self):
        for text in ("open codespace", "Qwen, open coding workspace",
                     "open the coding window for ORION", "let's code", "I want to start coding"):
            self.assertTrue(recognize_codespace_open(text), text)
    def test_no_ambiguous_open(self):
        for text in ("close codespace", "don't open codespace", "what is coding?",
                     "delete my files", "open code and execute it"):
            self.assertFalse(recognize_codespace_open(text), text)
    def test_same_action_from_all_surfaces(self):
        for origin in ("qwen_chat", "pc_button", "android_qwen"):
            req = request_codespace_open(project_id="ORION-V3", origin=origin,
                request_id="request_123", authenticated=True, stop_requested=False)
            self.assertEqual(req.action, "codespace.open")
            self.assertFalse(req.can_execute or req.can_write or req.can_approve)
    def test_unauthenticated_denied(self):
        with self.assertRaises(PermissionError):
            request_codespace_open(project_id="ORION", origin="pc_button",
                request_id="request_123", authenticated=False, stop_requested=False)
    def test_stop_denied(self):
        with self.assertRaises(PermissionError):
            request_codespace_open(project_id="ORION", origin="qwen_chat",
                request_id="request_123", authenticated=True, stop_requested=True)
    def test_invalid_project_denied(self):
        with self.assertRaises(ValueError):
            request_codespace_open(project_id="../other", origin="qwen_chat",
                request_id="request_123", authenticated=True, stop_requested=False)
    def test_invalid_origin_denied(self):
        with self.assertRaises(ValueError):
            request_codespace_open(project_id="ORION", origin="cloud_model",
                request_id="request_123", authenticated=True, stop_requested=False)
    def test_free_models_route_without_execution(self):
        result = plan_coding_roles(coder=CloudRole("openrouter", "free-coder", "coder", True),
            reviewer=CloudRole("groq", "free-reviewer", "reviewer", True),
            owner_approved_paid=False, budget_remaining=True)
        self.assertEqual(result["coordinator"], "local_qwen")
        self.assertEqual(result["status"], "ROUTING_PLAN_ONLY")
        self.assertFalse(result["can_execute"] or result["can_write"])
    def test_paid_denied_by_default(self):
        with self.assertRaises(PermissionError):
            plan_coding_roles(coder=CloudRole("provider", "paid", "coder", False),
                reviewer=CloudRole("groq", "free", "reviewer", True),
                owner_approved_paid=False, budget_remaining=True)
    def test_paid_allowed_with_explicit_authorization(self):
        result = plan_coding_roles(coder=CloudRole("provider", "paid", "coder", False),
            reviewer=CloudRole("groq", "free", "reviewer", True),
            owner_approved_paid=True, budget_remaining=True)
        self.assertFalse(result["can_execute"])
    def test_same_model_reviewer_denied(self):
        with self.assertRaises(ValueError):
            plan_coding_roles(coder=CloudRole("a", "x", "coder", True),
                reviewer=CloudRole("a", "x", "reviewer", True),
                owner_approved_paid=False, budget_remaining=True)
    def test_budget_exhaustion_denied(self):
        with self.assertRaises(PermissionError):
            plan_coding_roles(coder=CloudRole("a", "x", "coder", True),
                reviewer=CloudRole("b", "y", "reviewer", True),
                owner_approved_paid=False, budget_remaining=False)

if __name__ == "__main__":
    unittest.main()
