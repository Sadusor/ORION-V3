from __future__ import annotations

import copy
import re
import unicodedata
from typing import Any

from .memory_conflict_suggestions import memory_slot

SCHEMA = "orion.memory-consolidation/1"
HIERARCHY_SCHEMA = "orion.memory-hierarchy/1"
L0_MAX_ITEMS = 8
L0_MAX_CHARS = 900


def _norm(value: Any) -> str:
    raw = unicodedata.normalize("NFKD", str(value or "")).casefold()
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    raw = re.sub(r"[^\w]+", " ", raw, flags=re.UNICODE)
    return " ".join(raw.split())


def semantic_key(text: str) -> str:
    parsed = memory_slot(text)
    if parsed:
        slot, value = parsed
        return "slot:" + slot + "=" + _norm(value)
    return "text:" + _norm(text)


class MemoryConsolidation:
    """Read-only canonical-memory consolidation and hierarchy view.

    Canonical rows remain immutable. Duplicate/equivalent facts are collapsed
    only at read/prompt time while their evidence remains attached.
    """

    def __init__(self, review: Any, foundation: Any):
        self.review = review
        self.foundation = foundation

    def _current_memories(self, project_id: str = "") -> list[dict[str, Any]]:
        listed = self.review.list_canonical(include_revoked=True)
        superseded = {
            str(e.get("prior_memory_id") or "")
            for e in self.foundation.supersessions().get("events", [])
            if isinstance(e, dict)
        }
        rows = [
            copy.deepcopy(x)
            for x in listed.get("all_memories", [])
            if isinstance(x, dict)
            and bool(x.get("active"))
            and str(x.get("status") or "") == "active"
            and str(x.get("project_id") or "") == str(project_id or "")
            and str(x.get("memory_id") or "") not in superseded
        ]
        rows.sort(
            key=lambda x: (
                int(x.get("created_at_ms") or 0),
                str(x.get("memory_id") or ""),
            ),
            reverse=True,
        )
        return rows

    def groups(self, project_id: str = "") -> dict[str, Any]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for memory in self._current_memories(project_id):
            key = semantic_key(str(memory.get("content") or ""))
            grouped.setdefault(key, []).append(memory)

        groups: list[dict[str, Any]] = []
        duplicate_count = 0
        for key, rows in grouped.items():
            representative = rows[0]
            duplicates = rows[1:]
            duplicate_count += len(duplicates)
            groups.append({
                "semantic_key": key,
                "representative_memory_id": str(representative.get("memory_id") or ""),
                "representative_content": str(representative.get("content") or ""),
                "evidence_memory_ids": [
                    str(x.get("memory_id") or "") for x in rows
                ],
                "duplicate_memory_ids": [
                    str(x.get("memory_id") or "") for x in duplicates
                ],
                "evidence_count": len(rows),
                "duplicate_count": len(duplicates),
                "project_id": str(project_id or ""),
                "authority": "context_only",
            })

        groups.sort(
            key=lambda x: (
                -int(x["evidence_count"]),
                x["semantic_key"],
            )
        )
        return {
            "schema": SCHEMA,
            "project_id": str(project_id or ""),
            "groups": groups,
            "group_count": len(groups),
            "duplicate_count": duplicate_count,
            "canonical_rows_mutated": False,
            "authority": "context_only",
        }

    def dedupe_retrieval(self, result: dict[str, Any]) -> dict[str, Any]:
        out = copy.deepcopy(result)
        items = [x for x in out.get("items", []) if isinstance(x, dict)]
        by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for item in items:
            key = (
                str(item.get("project_id") or ""),
                semantic_key(str(item.get("content") or "")),
            )
            by_key.setdefault(key, []).append(item)

        collapsed: list[dict[str, Any]] = []
        duplicate_items = 0
        for rows in by_key.values():
            rows.sort(
                key=lambda x: (
                    int(x.get("created_at_ms") or 0),
                    str(x.get("memory_id") or ""),
                ),
                reverse=True,
            )
            rep = rows[0]
            dupes = rows[1:]
            duplicate_items += len(dupes)
            rep["consolidation"] = {
                "semantic_key": semantic_key(str(rep.get("content") or "")),
                "evidence_count": len(rows),
                "duplicate_evidence": [
                    {
                        "memory_id": str(x.get("memory_id") or ""),
                        "content_sha256": str(x.get("content_sha256") or ""),
                        "provenance": copy.deepcopy(x.get("provenance", {})),
                    }
                    for x in dupes
                ],
                "canonical_rows_mutated": False,
            }
            collapsed.append(rep)

        collapsed.sort(
            key=lambda x: (
                -float(x.get("score") or 0.0),
                -int(x.get("created_at_ms") or 0),
                str(x.get("memory_id") or ""),
            )
        )
        out["items"] = collapsed
        trace = out.setdefault("trace", {})
        trace["consolidation"] = {
            "input_items": len(items),
            "output_items": len(collapsed),
            "duplicates_collapsed": duplicate_items,
            "canonical_rows_mutated": False,
        }
        return out

    def l0(self, project_id: str = "") -> dict[str, Any]:
        groups = self.groups(project_id)
        items: list[dict[str, Any]] = []
        used = 0
        for group in groups["groups"]:
            text = str(group.get("representative_content") or "").strip()
            if not text:
                continue
            cost = len(text) + (1 if items else 0)
            if len(items) >= L0_MAX_ITEMS or used + cost > L0_MAX_CHARS:
                continue
            items.append({
                "memory_id": group["representative_memory_id"],
                "content": text,
                "evidence_count": group["evidence_count"],
                "semantic_key": group["semantic_key"],
            })
            used += cost
        return {
            "schema": HIERARCHY_SCHEMA,
            "level": "L0",
            "purpose": "compact current canonical summary",
            "project_id": str(project_id or ""),
            "items": items,
            "count": len(items),
            "chars": used,
            "group_count": int(groups.get("group_count") or 0),
            "duplicate_count": int(groups.get("duplicate_count") or 0),
            "limits": {"items": L0_MAX_ITEMS, "chars": L0_MAX_CHARS},
            "authority": "context_only",
        }

    def retrieve(
        self,
        query: str,
        *,
        project_id: str = "",
        conversation_id: str = "",
        limit: int = 6,
        include_historical: bool = False,
        context_char_budget: int | None = None,
        owner_scope: str = "owner:primary",
    ) -> dict[str, Any]:
        raw = self.foundation.retrieve(
            query,
            project_id=project_id,
            conversation_id=conversation_id,
            limit=limit,
            include_historical=include_historical,
            context_char_budget=context_char_budget,
            owner_scope=owner_scope,
        )
        out = self.dedupe_retrieval(raw)
        out["hierarchy_level"] = "L2" if include_historical else "L1"
        if include_historical:
            out["historical_expansion"] = True
        return out

    def l1(
        self,
        query: str,
        *,
        project_id: str = "",
        conversation_id: str = "",
        limit: int = 6,
    ) -> dict[str, Any]:
        return self.retrieve(
            query,
            project_id=project_id,
            conversation_id=conversation_id,
            limit=limit,
            include_historical=False,
        )

    def l2(
        self,
        query: str,
        *,
        project_id: str = "",
        conversation_id: str = "",
        limit: int = 12,
    ) -> dict[str, Any]:
        return self.retrieve(
            query,
            project_id=project_id,
            conversation_id=conversation_id,
            limit=limit,
            include_historical=True,
        )
