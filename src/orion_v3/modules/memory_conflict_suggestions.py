from __future__ import annotations

import re
import unicodedata
from typing import Any

SCHEMA = "orion.memory-conflict-suggestions/1"

_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "preference",
        re.compile(
            r"^\s*(?:i|we)\s+prefer\s+(?P<value>.+?)\s+"
            r"(?P<dimension>mode|theme|color|model|browser|editor|language)\s+"
            r"for\s+(?P<target>.+?)[.!]?\s*$",
            re.I,
        ),
    ),
    (
        "preferred",
        re.compile(
            r"^\s*(?:my|our)\s+preferred\s+(?P<dimension>[a-z0-9 _./+\-]{2,48})"
            r"\s+(?:is|are)\s+(?P<value>.+?)[.!]?\s*$",
            re.I,
        ),
    ),
    (
        "naming",
        re.compile(
            r"^\s*(?:the|this|that)\s+(?P<target>[a-z0-9 _./+\-]{2,64})"
            r"\s+(?:is called|is named)\s+(?P<value>.+?)[.!]?\s*$",
            re.I,
        ),
    ),
)


def _norm(value: Any) -> str:
    raw = unicodedata.normalize("NFKD", str(value or "")).casefold()
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    return " ".join(raw.strip(" .!?").split())


def memory_slot(text: str) -> tuple[str, str] | None:
    raw = str(text or "").strip()
    for kind, pattern in _PATTERNS:
        match = pattern.match(raw)
        if not match:
            continue
        groups = {k: _norm(v) for k, v in match.groupdict().items()}
        value = groups.get("value", "")
        if not value:
            return None
        if kind == "preference":
            slot = f"preference:{groups.get('dimension','')}:{groups.get('target','')}"
        elif kind == "preferred":
            slot = f"preferred:{groups.get('dimension','')}"
        else:
            slot = f"naming:{groups.get('target','')}"
        return slot, value
    return None


class MemoryConflictSuggestions:
    """Read-only conservative contradiction detector for canonical Memory.

    It never writes or supersedes anything. It only exposes high-confidence
    pairs that the owner may explicitly resolve through the existing
    append-only supersession boundary.
    """

    def __init__(self, review: Any, foundation: Any):
        self.review = review
        self.foundation = foundation

    def view(self) -> dict[str, Any]:
        listed = self.review.list_canonical(include_revoked=True)
        active = [
            x for x in listed.get("all_memories", [])
            if isinstance(x, dict)
            and bool(x.get("active"))
            and str(x.get("status") or "") == "active"
        ]
        superseded = {
            str(e.get("prior_memory_id") or "")
            for e in self.foundation.supersessions().get("events", [])
            if isinstance(e, dict)
        }

        grouped: dict[tuple[str, str], list[tuple[dict[str, Any], str]]] = {}
        for memory in active:
            memory_id = str(memory.get("memory_id") or "")
            if not memory_id or memory_id in superseded:
                continue
            parsed = memory_slot(str(memory.get("content") or ""))
            if not parsed:
                continue
            slot, value = parsed
            key = (str(memory.get("project_id") or ""), slot)
            grouped.setdefault(key, []).append((memory, value))

        suggestions: list[dict[str, Any]] = []
        for (project_id, slot), rows in grouped.items():
            rows.sort(
                key=lambda item: (
                    int(item[0].get("created_at_ms") or 0),
                    str(item[0].get("memory_id") or ""),
                )
            )
            latest, latest_value = rows[-1]
            for prior, prior_value in rows[:-1]:
                if prior_value == latest_value:
                    continue
                suggestions.append({
                    "suggestion_id": (
                        "conflict:" + str(prior.get("memory_id") or "") + ":" +
                        str(latest.get("memory_id") or "")
                    ),
                    "slot": slot,
                    "project_id": project_id,
                    "prior_memory_id": str(prior.get("memory_id") or ""),
                    "prior_content": str(prior.get("content") or ""),
                    "prior_created_at_ms": int(prior.get("created_at_ms") or 0),
                    "replacement_memory_id": str(latest.get("memory_id") or ""),
                    "replacement_content": str(latest.get("content") or ""),
                    "replacement_created_at_ms": int(latest.get("created_at_ms") or 0),
                    "reason": "same_memory_slot_different_value",
                    "confidence": "high",
                    "decision": "owner_required",
                    "authority": "context_only",
                })

        suggestions.sort(
            key=lambda x: (
                int(x["replacement_created_at_ms"]),
                x["replacement_memory_id"],
                x["prior_memory_id"],
            ),
            reverse=True,
        )
        return {
            "schema": SCHEMA,
            "suggestions": suggestions,
            "count": len(suggestions),
            "automatic_supersession": False,
            "owner_review_required": True,
            "authority": "context_only",
        }
