from __future__ import annotations

import copy
import datetime as _dt
import json
import threading
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


class LocalBrainError(RuntimeError):
    pass


class LocalBrainModule:
    """Reasoning-only Local Brain adapter.

    This module may ask a local Ollama model for a bounded textual proposal.
    It owns no execution authority and exposes no Hand/tool/capability dispatch.
    """

    SCHEMA = {
        "type": "object",
        "properties": {
            "conclusion": {"type": "string"},
            "draft": {"type": "string"},
        },
        "required": ["conclusion", "draft"],
        "additionalProperties": False,
    }

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        preferred_model: str = "qwen3.5-9b-orion",
    ):
        self.base_url = self._validated_base_url(base_url)
        self.preferred_model = str(preferred_model or "").strip()
        self._lock = threading.RLock()
        self._state = self._blank_state()
        self._cached_models: list[str] = []

        # Explicitly ignore environment proxy settings. This module is local-only.
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    @staticmethod
    def _validated_base_url(value: str) -> str:
        base = str(value or "").strip().rstrip("/")
        parsed = urlparse(base)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "http" or host not in {"127.0.0.1", "localhost", "::1"}:
            raise LocalBrainError("Local Brain Ollama endpoint must be loopback HTTP only.")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise LocalBrainError("Local Brain Ollama endpoint contains unsupported URL components.")
        return base

    @staticmethod
    def _blank_state() -> dict:
        return {
            "run_state": "idle",
            "result": "",
            "activity": "Local Brain ready for an owner request",
            "goal": "",
            "brain_state": "idle",
            "brain_phase": "idle",
            "brain_started_utc": "",
            "brain_stream_preview": "",
            "brain_model": "",
            "brain_conclusion": "",
            "brain_error": "",
            "brain_next_script": "",
            "brain_next_capability": "",
            "brain_next_artifact_path": "",
            "brain_next_url": "",
            "brain_next_browser": "",
            "brain_preflight": "not-run",
            "brain_preflight_reason": "",
            "brain_quality_state": "not-run",
            "brain_quality_reason": "",
            "brain_quality_unsupported_claims": [],
            "brain_quality_missing_evidence": [],
            "brain_quality_approved_sha256": "",
            "brain_needs_escalation": False,
            "brain_revision": 0,
            "brain_latency_seconds": None,
            "execution_kind": "",
            "execution_action": "",
            "execution_target_project_link": "",
            "execution_target_repo": "",
            "execution_target_branch": "",
            "execution_target_scope": "",
        }

    def view(self) -> dict:
        with self._lock:
            return copy.deepcopy(self._state)

    def cached_models(self) -> list[str]:
        with self._lock:
            return list(self._cached_models)

    def default_model(self) -> str:
        with self._lock:
            models = list(self._cached_models)
        return self._choose_model("", models, allow_empty=True)

    def _request_json(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        timeout: float = 3.0,
    ) -> dict:
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(
            self.base_url + path,
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with self._opener.open(req, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise LocalBrainError("Local Ollama is not reachable.") from exc
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LocalBrainError("Local Ollama returned malformed JSON.") from exc
        if not isinstance(payload, dict):
            raise LocalBrainError("Local Ollama returned an invalid response.")
        return payload

    def _available_models(self) -> list[str]:
        payload = self._request_json("GET", "/api/tags", timeout=2.0)
        models: list[str] = []
        for item in payload.get("models", []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or item.get("model") or "").strip()
            if name and name not in models:
                models.append(name)
        with self._lock:
            self._cached_models = list(models)
        return models

    def _choose_model(
        self,
        requested: str,
        models: list[str],
        *,
        allow_empty: bool = False,
    ) -> str:
        requested = str(requested or "").strip()
        if requested:
            if requested not in models:
                raise LocalBrainError(
                    "Selected Local Brain model is not available in Ollama: " + requested
                )
            return requested

        if not models:
            if allow_empty:
                return ""
            raise LocalBrainError("No local Ollama models are available.")

        if self.preferred_model and self.preferred_model in models:
            return self.preferred_model

        def score(name: str) -> tuple[int, str]:
            low = name.lower()
            points = 0
            if "qwen3.5" in low:
                points += 100
            elif "qwen" in low:
                points += 40
            if "9b" in low:
                points += 60
            if "orion" in low:
                points += 10
            return (-points, low)

        return sorted(models, key=score)[0]

    def start(self, goal: str, model: str = "") -> dict:
        goal = str(goal or "").strip()
        if not goal:
            raise LocalBrainError("Enter a request for ORION first.")
        if len(goal.encode("utf-8")) > 16000:
            raise LocalBrainError("Local Brain request is too large; limit is 16 KiB.")

        models = self._available_models()
        selected = self._choose_model(model, models)

        with self._lock:
            if self._state.get("brain_state") == "running":
                raise LocalBrainError("Local Brain is already working.")

            self._state = self._blank_state()
            self._state.update(
                {
                    "goal": goal,
                    "brain_state": "running",
                    "brain_phase": "drafting",
                    "brain_started_utc": _now(),
                    "brain_model": selected,
                    "activity": "Local Brain drafting a reasoning-only response",
                }
            )
            snapshot = copy.deepcopy(self._state)

        threading.Thread(
            target=self._worker,
            args=(goal, selected),
            daemon=True,
            name="orion-v3-local-brain",
        ).start()
        return snapshot

    def _worker(self, goal: str, model: str) -> None:
        prompt = (
            "You are ORION's bounded local reasoning brain.\n"
            "You are NOT an autonomous agent. You have no tools and cannot execute anything.\n"
            "Do not claim that you opened, changed, checked, searched, ran, sent, or verified anything.\n"
            "Respond only to the owner's request with a concise conclusion and, when useful, a short draft plan.\n"
            "The draft is advisory text only. Do not produce executable PowerShell or tool calls.\n"
            "Do not invent access to files, memory, browsers, devices, cloud services, or current external facts.\n"
            "If the request requires unavailable evidence, say what evidence would be needed.\n\n"
            "OWNER REQUEST:\n"
            + goal
            + "\n\nReturn ONLY JSON matching the supplied schema."
        )

        body = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": self.SCHEMA,
            "think": False,
            "keep_alive": "5m",
            "options": {
                "temperature": 0,
                "num_predict": 900,
            },
        }

        started = time.perf_counter()
        try:
            payload = self._request_json(
                "POST",
                "/api/generate",
                body=body,
                timeout=120.0,
            )
            if payload.get("done") is False:
                raise LocalBrainError("Local Brain response was incomplete.")

            raw = str(payload.get("response") or "").strip()
            if not raw:
                raise LocalBrainError("Local Brain returned an empty response.")

            try:
                document = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise LocalBrainError("Local Brain returned malformed structured JSON.") from exc

            if not isinstance(document, dict):
                raise LocalBrainError("Local Brain structured output is not an object.")
            if set(document) != {"conclusion", "draft"}:
                raise LocalBrainError("Local Brain structured output did not match the required schema.")
            conclusion = document.get("conclusion")
            draft = document.get("draft")
            if not isinstance(conclusion, str) or not isinstance(draft, str):
                raise LocalBrainError("Local Brain structured fields must be strings.")

            conclusion = conclusion.strip()
            draft = draft.strip()
            if not conclusion and not draft:
                raise LocalBrainError("Local Brain returned no usable text.")

            combined = conclusion
            if draft:
                combined += ("\n\nDraft:\n" if combined else "Draft:\n") + draft

            with self._lock:
                self._state.update(
                    {
                        "brain_state": "ready",
                        "brain_phase": "complete",
                        "brain_conclusion": combined,
                        "brain_error": "",
                        "brain_latency_seconds": round(time.perf_counter() - started, 3),
                        "activity": "Local Brain response ready · reasoning only · nothing executed",
                    }
                )
        except Exception as exc:
            message = str(exc).strip() or exc.__class__.__name__
            with self._lock:
                self._state.update(
                    {
                        "brain_state": "error",
                        "brain_phase": "error",
                        "brain_error": message,
                        "brain_conclusion": "",
                        "brain_latency_seconds": round(time.perf_counter() - started, 3),
                        "activity": "Local Brain failed · nothing executed",
                    }
                )
