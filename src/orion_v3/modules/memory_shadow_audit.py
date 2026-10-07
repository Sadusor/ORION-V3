from __future__ import annotations

import copy
import datetime as _dt
import gzip
import hashlib
import json
import pathlib
import threading
from typing import Any

from .memory_conflict_suggestions import memory_slot

SCHEMA = "orion.memory-shadow-audit/1"
RULE_ID = "fusion.same_slot.v1"
DEFAULT_MAX_BYTES = 5 * 1024 * 1024
DEFAULT_RETENTION_DAYS = 90


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


class MemoryShadowAudit:
    """Observation-only audit sidecar for the frozen V1 shadowing rule.

    It never decides whether to shadow, never changes retrieval, and never
    contributes content to a model prompt.
    """

    def __init__(
        self,
        directory: pathlib.Path,
        recall: Any,
        durable: Any,
        *,
        max_bytes: int = DEFAULT_MAX_BYTES,
        retention_days: int = DEFAULT_RETENTION_DAYS,
    ):
        self.directory = pathlib.Path(directory)
        self.path = self.directory / "shadow_audit.jsonl"
        self.recall = recall
        self.durable = durable
        self.max_bytes = max(4096, int(max_bytes or DEFAULT_MAX_BYTES))
        self.retention_days = max(1, int(retention_days or DEFAULT_RETENTION_DAYS))
        self._lock = threading.RLock()
        self._status: dict[str, Any] = {
            "schema": SCHEMA,
            "state": "idle",
            "events_written": 0,
            "last_event_utc": "",
            "last_error": "",
            "last_error_utc": "",
            "prompt_path_effect": "none",
            "authority": "context_only",
        }

    def _rotate_if_needed(self, incoming_bytes: int) -> None:
        if not self.path.is_file():
            return
        try:
            current = int(self.path.stat().st_size)
        except Exception:
            current = 0
        if current + int(incoming_bytes or 0) <= self.max_bytes:
            return

        self.directory.mkdir(parents=True, exist_ok=True)
        stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        archive = self.directory / f"shadow_audit.{stamp}.jsonl.gz"
        with self.path.open("rb") as source, gzip.open(archive, "wb") as target:
            while True:
                chunk = source.read(64 * 1024)
                if not chunk:
                    break
                target.write(chunk)
        self.path.unlink(missing_ok=True)
        self._prune_archives()

    def _prune_archives(self) -> None:
        cutoff = (
            _dt.datetime.now(_dt.timezone.utc)
            - _dt.timedelta(days=self.retention_days)
        ).timestamp()
        for archive in self.directory.glob("shadow_audit.*.jsonl.gz"):
            try:
                if archive.stat().st_mtime < cutoff:
                    archive.unlink(missing_ok=True)
            except Exception:
                pass

    def _append_event(self, event: dict[str, Any]) -> None:
        line = _canonical_json(event) + "\n"
        encoded = line.encode("utf-8")
        self.directory.mkdir(parents=True, exist_ok=True)
        self._rotate_if_needed(len(encoded))
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line)
            handle.flush()

    def _resolve_sources(
        self,
        query: str,
        *,
        conversation_id: str,
        project_id: str | None,
    ) -> tuple[dict[str, Any], dict[str, Any], str]:
        recall_result = self.recall.retrieve(
            query,
            conversation_id=conversation_id,
            project_id=project_id,
        )
        resolved_project = (
            str(project_id or "")
            if project_id is not None
            else str(recall_result.get("scope", {}).get("project_id") or "")
        )
        durable_result = self.durable.retrieve(
            query,
            project_id=resolved_project,
            conversation_id=conversation_id,
            include_historical=False,
        )
        return recall_result, durable_result, resolved_project

    @staticmethod
    def _observations(
        recall_result: dict[str, Any],
        durable_result: dict[str, Any],
        *,
        project_id: str,
    ) -> list[dict[str, Any]]:
        current_slots: dict[str, dict[str, Any]] = {}
        for item in durable_result.get("items", []):
            if not isinstance(item, dict):
                continue
            if str(item.get("status") or "current") == "historical":
                continue
            if str(item.get("trust_tier") or "") != "owner_message_unverified":
                continue
            parsed = memory_slot(str(item.get("content") or ""))
            if not parsed:
                continue
            slot, value = parsed
            current_slots[slot] = {
                "value": value,
                "item": copy.deepcopy(item),
            }

        observations: list[dict[str, Any]] = []
        for item in recall_result.get("items", []):
            if not isinstance(item, dict):
                continue
            provenance = (
                item.get("provenance", {})
                if isinstance(item.get("provenance"), dict)
                else {}
            )
            if str(provenance.get("role") or "") != "user":
                continue
            parsed = memory_slot(str(item.get("content") or ""))
            if not parsed:
                continue
            slot, old_value = parsed
            current = current_slots.get(slot)
            if not current:
                continue

            durable_item = current["item"]
            durable_provenance = (
                durable_item.get("provenance", {})
                if isinstance(durable_item.get("provenance"), dict)
                else {}
            )
            old_text = str(item.get("content") or "")
            current_text = str(durable_item.get("content") or "")
            observations.append({
                "schema": SCHEMA,
                "ts_utc": _now(),
                "slot": slot,
                "scope": {
                    "project_id": str(project_id or ""),
                    "owner_scope": str(
                        durable_item.get("owner_scope")
                        or "owner:primary"
                    ),
                },
                "old_recall": {
                    "text": old_text,
                    "value": old_value,
                    "source_conversation_id": str(
                        provenance.get("conversation_id") or ""
                    ),
                    "source_message_id": str(
                        provenance.get("message_id") or ""
                    ),
                    "source_hash": _sha256_text(old_text),
                },
                "current_durable": {
                    "memory_id": str(durable_item.get("memory_id") or ""),
                    "text": current_text,
                    "value": str(current.get("value") or ""),
                    "content_sha256": str(
                        durable_item.get("content_sha256")
                        or _sha256_text(current_text)
                    ),
                    "source_conversation_id": str(
                        durable_provenance.get("source_conversation_id") or ""
                    ),
                    "source_message_id": str(
                        durable_provenance.get("source_message_id") or ""
                    ),
                    "promotion_event_hash": str(
                        durable_provenance.get("promotion_event_hash") or ""
                    ),
                },
                "match": {
                    "rule_id": RULE_ID,
                    "deterministic_slot": slot,
                    "same_value": old_value == str(current.get("value") or ""),
                    "confidence": "deterministic_rule_match",
                },
                "rationale": (
                    "Frozen V1 fusion reported same-slot owner recall shadowing; "
                    "V1.1 audit independently reconstructed the matching pair."
                ),
                "prompt_path_effect": "none",
                "authority": "context_only",
            })
        return observations

    def observe(
        self,
        query: str,
        *,
        conversation_id: str = "",
        project_id: str | None = None,
        expected_shadow_count: int = 0,
    ) -> dict[str, Any]:
        """Audit a shadowing decision already made by frozen V1.

        Call only after frozen V1 has already decided and reported a non-zero
        shadow count. Any failure here is observational and nonfatal.
        """
        expected = max(0, int(expected_shadow_count or 0))
        if expected == 0:
            return self.status()

        with self._lock:
            try:
                recall_result, durable_result, resolved_project = self._resolve_sources(
                    str(query or ""),
                    conversation_id=str(conversation_id or ""),
                    project_id=project_id,
                )
                observations = self._observations(
                    recall_result,
                    durable_result,
                    project_id=resolved_project,
                )

                written = 0
                for event in observations:
                    self._append_event(event)
                    written += 1

                self._status.update({
                    "state": "ok" if written == expected else "count_mismatch",
                    "events_written": int(self._status.get("events_written") or 0) + written,
                    "last_batch_written": written,
                    "last_expected_shadow_count": expected,
                    "last_event_utc": _now() if written else str(
                        self._status.get("last_event_utc") or ""
                    ),
                    "last_error": "",
                    "last_error_utc": "",
                    "prompt_path_effect": "none",
                    "authority": "context_only",
                })
            except Exception as exc:
                self._status.update({
                    "state": "error",
                    "last_batch_written": 0,
                    "last_expected_shadow_count": expected,
                    "last_error": str(exc).strip() or exc.__class__.__name__,
                    "last_error_utc": _now(),
                    "prompt_path_effect": "none",
                    "authority": "context_only",
                })
            return copy.deepcopy(self._status)

    def status(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._status)
