from __future__ import annotations

import copy
import json
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import urlparse


PREFERRED_MODEL = "qwen35-9b-orion:latest"
OLLAMA_BASE_URL = "http://127.0.0.1:11434"

_REPLY_SCHEMA = {
    "type": "object",
    "properties": {
        "conclusion": {"type": "string"},
        "proposed_action": {"type": "string"},
        "needs_execution": {"type": "boolean"},
    },
    "required": ["conclusion", "proposed_action", "needs_execution"],
    "additionalProperties": False,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_lane() -> dict:
    return {
        "run_state": "idle",
        "result": "",
        "activity": "Local Brain ready",
        "goal": "",
        "output": "",
        "error": "",
        "started_utc": "",
        "finished_utc": "",
        "exit_code": None,
        "pid": None,
        "evidence_path": "",
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


class LocalBrainModule:
    """Bounded reasoning-only Local Brain.

    This module may interpret and reply. It has no execution/tool authority.
    """

    def __init__(
        self,
        *,
        ollama_base_url: str = OLLAMA_BASE_URL,
        preferred_model: str = PREFERRED_MODEL,
        list_models_fn: Callable[[], list[str]] | None = None,
        generate_fn: Callable[[str, str], dict] | None = None,
    ):
        self._base = ollama_base_url.rstrip("/")
        self._preferred = preferred_model
        self._list_models_fn = list_models_fn
        self._generate_fn = generate_fn
        self._lock = threading.Lock()
        self._lane = _empty_lane()
        self._validate_local_base()

    @property
    def preferred_model(self) -> str:
        return self._preferred

    def snapshot(self) -> dict:
        with self._lock:
            return copy.deepcopy(self._lane)

    def submit(self, goal: str, model: str = "") -> dict:
        goal = str(goal or "").strip()
        if not goal:
            raise RuntimeError("Enter a goal for ORION first.")
        if len(goal.encode("utf-8")) > 16000:
            raise RuntimeError("ORION request is too large; limit is 16 KiB.")

        selected = self._select_model(str(model or "").strip())

        with self._lock:
            if self._lane.get("brain_state") == "running":
                raise RuntimeError("Local Brain is already working.")

            revision = int(self._lane.get("brain_revision") or 0) + 1
            self._lane = _empty_lane()
            self._lane.update({
                "goal": goal,
                "activity": "Local Brain is drafting a reasoning-only reply",
                "brain_state": "running",
                "brain_phase": "drafting",
                "brain_started_utc": _now(),
                "brain_model": selected,
                "brain_revision": revision,
            })

        threading.Thread(
            target=self._worker,
            args=(goal, selected, revision),
            daemon=True,
            name="orion-v3-local-brain",
        ).start()

        return self.snapshot()

    def _worker(self, goal: str, model: str, revision: int) -> None:
        started = time.perf_counter()
        try:
            doc = (
                self._generate_fn(goal, model)
                if self._generate_fn is not None
                else self._generate(goal, model)
            )
            conclusion = str(doc.get("conclusion") or "").strip()
            proposed_action = str(doc.get("proposed_action") or "").strip()
            needs_execution = bool(doc.get("needs_execution"))

            if not conclusion:
                raise RuntimeError("Local Brain returned an empty conclusion.")

            # First V3 gate is deliberately reasoning-only. Action text is context,
            # never an executable plan or authority grant.
            if needs_execution and proposed_action:
                conclusion = (
                    conclusion
                    + "\n\nProposed next step (not executed): "
                    + proposed_action
                )

            with self._lock:
                if int(self._lane.get("brain_revision") or 0) != revision:
                    return
                self._lane.update({
                    "activity": "Local Brain reply ready",
                    "brain_state": "ready",
                    "brain_phase": "complete",
                    "brain_model": model,
                    "brain_conclusion": conclusion,
                    "brain_error": "",
                    "brain_latency_seconds": round(time.perf_counter() - started, 3),
                    # Explicitly keep all execution seams empty.
                    "brain_next_script": "",
                    "brain_next_capability": "",
                    "execution_kind": "",
                    "execution_action": "",
                })
        except Exception as exc:
            with self._lock:
                if int(self._lane.get("brain_revision") or 0) != revision:
                    return
                self._lane.update({
                    "activity": "Local Brain error",
                    "brain_state": "error",
                    "brain_phase": "error",
                    "brain_error": str(exc),
                    "brain_latency_seconds": round(time.perf_counter() - started, 3),
                    "brain_next_script": "",
                    "brain_next_capability": "",
                    "execution_kind": "",
                    "execution_action": "",
                })

    def _validate_local_base(self) -> None:
        parsed = urlparse(self._base)
        if parsed.scheme not in {"http", "https"}:
            raise RuntimeError("Local Brain Ollama URL must be http/https.")
        if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise RuntimeError("Local Brain Ollama must remain loopback-local.")

    def _list_models(self) -> list[str]:
        if self._list_models_fn is not None:
            return list(self._list_models_fn())

        req = urllib.request.Request(
            self._base + "/api/tags",
            headers={"Accept": "application/json"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError("Could not read local Ollama model catalog: " + str(exc)) from exc

        result = []
        for item in payload.get("models", []):
            name = str(item.get("name") or item.get("model") or "").strip()
            if name:
                result.append(name)
        return result

    def _select_model(self, requested: str) -> str:
        models = self._list_models()
        if not models:
            raise RuntimeError("Ollama is online but reports no installed models.")

        by_base = {name.split(":", 1)[0]: name for name in models}

        if requested:
            if requested in models:
                return requested
            if requested.split(":", 1)[0] in by_base:
                return by_base[requested.split(":", 1)[0]]
            raise RuntimeError(
                "Selected Local Brain model is not installed in Ollama: " + requested
            )

        if self._preferred in models:
            return self._preferred

        preferred_base = self._preferred.split(":", 1)[0]
        if preferred_base in by_base:
            return by_base[preferred_base]

        raise RuntimeError(
            "Preferred Local Brain model is not installed: "
            + self._preferred
            + ". Installed: "
            + ", ".join(models[:12])
        )

    def _generate(self, goal: str, model: str) -> dict:
        prompt = f"""You are ORION V3's bounded local reasoning brain.

Authority boundary:
- You may interpret the owner's request and answer it.
- You may propose a next step in plain language.
- You may NOT execute anything.
- You may NOT call tools, run PowerShell, edit files, browse, send messages, or grant permission.
- Never claim an action happened unless the human request itself says it already happened.
- If an action would be needed, say so in proposed_action and set needs_execution=true.
- Keep the conclusion concise and useful.

Owner request:
{goal}

Return only the required JSON object.
"""

        body = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": _REPLY_SCHEMA,
            "think": False,
            "keep_alive": "5m",
            "options": {
                "temperature": 0,
                "num_predict": 700,
            },
        }

        req = urllib.request.Request(
            self._base + "/api/generate",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError("Local Brain Ollama request failed: " + str(exc)) from exc

        if payload.get("done") is False:
            raise RuntimeError("Local Brain response was incomplete.")

        raw = str(payload.get("response") or "").strip()
        if not raw:
            raise RuntimeError("Local Brain returned an empty response.")

        try:
            doc = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Local Brain returned malformed structured JSON.") from exc

        if not isinstance(doc, dict):
            raise RuntimeError("Local Brain response is not a JSON object.")
        if set(doc) != {"conclusion", "proposed_action", "needs_execution"}:
            raise RuntimeError("Local Brain response did not match the required schema.")
        if not isinstance(doc["conclusion"], str):
            raise RuntimeError("Local Brain conclusion must be text.")
        if not isinstance(doc["proposed_action"], str):
            raise RuntimeError("Local Brain proposed_action must be text.")
        if not isinstance(doc["needs_execution"], bool):
            raise RuntimeError("Local Brain needs_execution must be boolean.")

        return doc
