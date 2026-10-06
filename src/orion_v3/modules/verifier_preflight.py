from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from urllib.parse import urlparse


class VerifierError(RuntimeError):
    pass


class VerifierPreflightModule:
    """Bounded verifier for Local Brain advisory text.

    It owns no execution authority. It can only PASS/BLOCK an advisory reply.
    """

    SCHEMA = {
        "type": "object",
        "properties": {
            "ready": {"type": "boolean"},
            "reason": {"type": "string"},
            "unsupported_claims": {"type": "array", "items": {"type": "string"}},
            "missing_evidence": {"type": "array", "items": {"type": "string"}},
            "needs_escalation": {"type": "boolean"},
        },
        "required": [
            "ready",
            "reason",
            "unsupported_claims",
            "missing_evidence",
            "needs_escalation",
        ],
        "additionalProperties": False,
    }

    def __init__(self, base_url: str = "http://127.0.0.1:11434"):
        self.base_url = self._validated_base_url(base_url)
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    @staticmethod
    def _validated_base_url(value: str) -> str:
        base = str(value or "").strip().rstrip("/")
        parsed = urlparse(base)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "http" or host not in {"127.0.0.1", "localhost", "::1"}:
            raise VerifierError("Verifier Ollama endpoint must be loopback HTTP only.")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise VerifierError("Verifier Ollama endpoint contains unsupported URL components.")
        return base

    @staticmethod
    def deterministic_preflight(text: str) -> dict:
        value = str(text or "").strip()
        if not value:
            return {"allowed": False, "reason": "Local Brain produced no advisory text."}

        executable_patterns = (
            r"(?im)^\s*(?:powershell|pwsh|cmd|bash|sh)(?:\.exe)?\s+[-/]",
            r"(?im)^\s*(?:Start-Process|Invoke-Expression|Invoke-WebRequest|curl|wget|git\s+(?:push|commit|checkout|merge)|Remove-Item|Set-Content)\b",
        )
        if any(re.search(pattern, value) for pattern in executable_patterns):
            return {
                "allowed": False,
                "reason": "Reasoning-only reply contains executable command mechanics.",
            }

        action_claim_patterns = (
            r"(?i)\bI\s+(?:opened|launched|ran|executed|changed|modified|deleted|created|installed|uninstalled|sent|uploaded|downloaded|clicked|browsed|searched|checked|verified)\b",
            r"(?i)\bORION\s+(?:opened|launched|ran|executed|changed|modified|deleted|created|installed|uninstalled|sent|uploaded|downloaded|clicked|browsed|searched|checked|verified)\b",
            r"(?i)\b(?:I|ORION)\s+have\s+(?:opened|launched|run|executed|changed|modified|deleted|created|installed|sent|uploaded|downloaded|checked|verified)\b",
        )
        if any(re.search(pattern, value) for pattern in action_claim_patterns):
            return {
                "allowed": False,
                "reason": "Reply claims an external action or verification that this module cannot perform.",
            }

        return {"allowed": True, "reason": ""}

    def verify(self, goal: str, reply: str, model: str) -> dict:
        preflight = self.deterministic_preflight(reply)
        if not preflight["allowed"]:
            return {
                "preflight": "blocked",
                "preflight_reason": preflight["reason"],
                "quality_state": "not-run",
                "quality_reason": "",
                "unsupported_claims": [],
                "missing_evidence": [],
                "needs_escalation": False,
            }

        prompt = (
            "You are the bounded ORION reply verifier.\n"
            "You cannot execute, browse, inspect files, use tools, or change state.\n"
            "Judge only whether the advisory Local Brain reply is honest and supported by the owner request.\n"
            "Block unsupported factual claims, claims of actions that did not happen, invented access, or advice that requires evidence not available in the request.\n"
            "Do not rewrite the answer.\n"
            "A concise ordinary conversational answer may PASS when it does not depend on unavailable external evidence.\n\n"
            "OWNER REQUEST:\n"
            + str(goal or "").strip()
            + "\n\nLOCAL BRAIN REPLY:\n"
            + str(reply or "").strip()
            + "\n\nReturn ONLY JSON matching the supplied schema."
        )

        body = {
            "model": str(model or "").strip(),
            "prompt": prompt,
            "stream": False,
            "format": self.SCHEMA,
            "think": False,
            "keep_alive": "5m",
            "options": {"temperature": 0, "num_predict": 700},
        }

        req = urllib.request.Request(
            self.base_url + "/api/generate",
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with self._opener.open(req, timeout=120.0) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise VerifierError("Local verifier request failed: " + str(exc)) from exc

        if not isinstance(payload, dict):
            raise VerifierError("Local verifier returned an invalid response.")
        if payload.get("done") is False:
            raise VerifierError("Local verifier response was incomplete.")

        raw = str(payload.get("response") or "").strip()
        if not raw:
            raise VerifierError("Local verifier returned an empty response.")

        try:
            doc = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise VerifierError("Local verifier returned malformed structured JSON.") from exc

        if not isinstance(doc, dict) or set(doc) != set(self.SCHEMA["required"]):
            raise VerifierError("Local verifier output did not match the required schema.")
        if not isinstance(doc["ready"], bool):
            raise VerifierError("Verifier field ready must be boolean.")
        if not isinstance(doc["reason"], str):
            raise VerifierError("Verifier field reason must be text.")
        if not isinstance(doc["unsupported_claims"], list) or any(
            not isinstance(x, str) for x in doc["unsupported_claims"]
        ):
            raise VerifierError("Verifier unsupported_claims must be a list of text.")
        if not isinstance(doc["missing_evidence"], list) or any(
            not isinstance(x, str) for x in doc["missing_evidence"]
        ):
            raise VerifierError("Verifier missing_evidence must be a list of text.")
        if not isinstance(doc["needs_escalation"], bool):
            raise VerifierError("Verifier needs_escalation must be boolean.")

        return {
            "preflight": "pass",
            "preflight_reason": "",
            "quality_state": "pass" if doc["ready"] else "blocked",
            "quality_reason": doc["reason"].strip(),
            "unsupported_claims": [
                x.strip() for x in doc["unsupported_claims"] if x.strip()
            ],
            "missing_evidence": [
                x.strip() for x in doc["missing_evidence"] if x.strip()
            ],
            "needs_escalation": bool(doc["needs_escalation"]),
        }
