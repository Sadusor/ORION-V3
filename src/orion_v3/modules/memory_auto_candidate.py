from __future__ import annotations

import re
import threading
from typing import Any

from .chat_history import ChatHistoryStore
from .memory_candidate_queue import CanonicalMemoryCandidateQueue, MemoryCandidateError

SCHEMA = "orion.memory-auto-candidate/1"
MAX_TEXT_CHARS = 1_200

_SECRET_OR_SENSITIVE = (
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----", re.I),
    re.compile(r"\b(?:password|passcode|api[_ -]?key|secret|token)\s*[:=]\s*\S+", re.I),
    re.compile(r"\b(?:credit card|card number|cvv|iban|bank account|social security|passport number)\b", re.I),
    re.compile(r"\b(?:diagnosis|diagnosed|medication|medical condition|religion|political party|sexual orientation|sex life|race|ethnicity)\b", re.I),
)

_TRANSIENT_OR_TEST = (
    re.compile(r"^\s*(?:hi|hello|hey|thanks|thank you|ok|okay|done|pass|passed|failed)\W*$", re.I),
    re.compile(r"\b(?:sync test|live sync test|test message|testing only)\b", re.I),
)

_QUESTION_START = re.compile(
    r"^\s*(?:who|what|when|where|why|how|can|could|would|should|do|does|did|is|are|am|will|may|might|have|has)\b",
    re.I,
)

_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("preference", re.compile(
        r"\b(?:i|we)\s+(?:strongly\s+)?(?:prefer|like|love|dislike|hate)\b|\bmy\s+preferred\b|\bour\s+preferred\b",
        re.I,
    )),
    ("stable_fact", re.compile(
        r"\b(?:my|our)\s+[a-z0-9][a-z0-9 _./+\-]{0,48}\s+(?:is|are)\b",
        re.I,
    )),
    ("stable_fact", re.compile(
        r"\b(?:i|we)\s+(?:use|have|own|work with|run)\s+[a-z0-9]",
        re.I,
    )),
    ("naming_fact", re.compile(
        r"\b(?:the|this|that)\s+[a-z0-9][a-z0-9 _./+\-]{0,48}\s+(?:is called|is named|means)\b",
        re.I,
    )),
    ("decision", re.compile(
        r"\b(?:we|i)\s+(?:decided|agreed|chose)\b|\bthe decision is\b|\bfrom now on\b",
        re.I,
    )),
)


class AutomaticMemoryCandidateSelector:
    """Conservative, deterministic intake for owner-reviewable memory candidates.

    This module never promotes canonical memory. It only decides whether an exact
    new owner chat message is worth placing in the existing review queue.

    Existing chat messages are baselined as already seen on startup, so enabling
    the module does not backfill old conversations.
    """

    def __init__(
        self,
        history: ChatHistoryStore,
        queue: CanonicalMemoryCandidateQueue,
    ):
        self.history = history
        self.queue = queue
        self._lock = threading.RLock()
        self._seen: set[str] = {
            str(m.get("id") or "")
            for m in history.snapshot().get("messages", [])
            if isinstance(m, dict) and str(m.get("id") or "")
        }
        self._stats: dict[str, Any] = {
            "schema": SCHEMA,
            "enabled": True,
            "considered": 0,
            "selected": 0,
            "skipped": 0,
            "errors": 0,
            "last_message_id": "",
            "last_outcome": "idle",
            "last_reason": "",
        }

    @staticmethod
    def classify(text: str) -> tuple[bool, str, str]:
        value = str(text or "").strip()[:MAX_TEXT_CHARS]
        if len(value) < 12:
            return False, "", "too_short"
        if any(p.search(value) for p in _SECRET_OR_SENSITIVE):
            return False, "", "sensitive_or_secret"
        if any(p.search(value) for p in _TRANSIENT_OR_TEST):
            return False, "", "transient_or_test"
        if value.endswith("?") or _QUESTION_START.search(value):
            return False, "", "question"
        if re.search(r"\b(?:i want you to|please |can you |could you |would you )", value, re.I):
            return False, "", "task_request"
        for category, pattern in _PATTERNS:
            if pattern.search(value):
                return True, category, "automatic_stable_owner_statement"
        return False, "", "no_stable_signal"

    def consider_sync(self, payload: dict[str, Any] | None) -> dict[str, Any]:
        payload = payload if isinstance(payload, dict) else {}
        raw_messages = payload.get("messages")
        messages = raw_messages if isinstance(raw_messages, list) else []
        selected: list[dict[str, Any]] = []

        for raw in messages:
            if not isinstance(raw, dict):
                continue
            message_id = str(raw.get("id") or "").strip()[:160]
            if not message_id:
                continue

            with self._lock:
                if message_id in self._seen:
                    continue
                self._seen.add(message_id)
                self._stats["considered"] += 1
                self._stats["last_message_id"] = message_id

            if str(raw.get("role") or "").strip().lower() != "user":
                with self._lock:
                    self._stats["skipped"] += 1
                    self._stats["last_outcome"] = "skipped"
                    self._stats["last_reason"] = "not_owner_message"
                continue

            choose, category, reason = self.classify(str(raw.get("text") or ""))
            if not choose:
                with self._lock:
                    self._stats["skipped"] += 1
                    self._stats["last_outcome"] = "skipped"
                    self._stats["last_reason"] = reason
                continue

            try:
                result = self.queue.enqueue_chat_message(
                    conversation_id=str(raw.get("conversation_id") or ""),
                    message_id=message_id,
                    project_id=None,
                    reason_for_candidate=reason + ":" + category,
                )
                selected.append(result)
                with self._lock:
                    self._stats["selected"] += 1 if result.get("created") else 0
                    self._stats["last_outcome"] = "selected" if result.get("created") else "already_queued"
                    self._stats["last_reason"] = category
            except MemoryCandidateError as exc:
                with self._lock:
                    self._stats["errors"] += 1
                    self._stats["last_outcome"] = "error"
                    self._stats["last_reason"] = str(exc)

        out = self.status()
        out["new_candidates"] = len([x for x in selected if x.get("created")])
        return out

    def status(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._stats)
