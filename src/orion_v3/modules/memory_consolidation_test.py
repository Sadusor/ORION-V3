from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
PARENT = HERE.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from modules.memory_consolidation import MemoryConsolidation, semantic_key


class FakeReview:
    def list_canonical(self, *, include_revoked=False):
        rows = [
            {
                "memory_id": "m-old-dark",
                "content": "I prefer dark mode for ORION.",
                "project_id": "",
                "created_at_ms": 1000,
                "active": True,
                "status": "active",
            },
            {
                "memory_id": "m-new-dark",
                "content": "My preferred ORION mode is dark.",
                "project_id": "",
                "created_at_ms": 2000,
                "active": True,
                "status": "active",
            },
            {
                "memory_id": "m-browser",
                "content": "My preferred browser is Firefox.",
                "project_id": "",
                "created_at_ms": 1500,
                "active": True,
                "status": "active",
            },
            {
                "memory_id": "m-project",
                "content": "I prefer light mode for ORION.",
                "project_id": "A",
                "created_at_ms": 2500,
                "active": True,
                "status": "active",
            },
            {
                "memory_id": "m-revoked",
                "content": "The old benchmark target is 50.",
                "project_id": "",
                "created_at_ms": 500,
                "active": False,
                "status": "revoked",
            },
        ]
        out = {"memories": [x for x in rows if x["active"]], "count": 4}
        if include_revoked:
            out["all_memories"] = rows
            out["revoked_memories"] = [x for x in rows if not x["active"]]
        return out


class FakeFoundation:
    def __init__(self):
        self.calls = []

    def supersessions(self):
        return {"events": [], "count": 0}

    def retrieve(self, query, **kwargs):
        self.calls.append((query, kwargs))
        include_historical = bool(kwargs.get("include_historical"))
        items = [
            {
                "memory_id": "m-old-dark",
                "content": "I prefer dark mode for ORION.",
                "content_sha256": "a",
                "project_id": "",
                "created_at_ms": 1000,
                "score": 0.8,
                "provenance": {"source_message_id": "old"},
            },
            {
                "memory_id": "m-new-dark",
                "content": "My preferred ORION mode is dark.",
                "content_sha256": "b",
                "project_id": "",
                "created_at_ms": 2000,
                "score": 0.9,
                "provenance": {"source_message_id": "new"},
            },
            {
                "memory_id": "m-browser",
                "content": "My preferred browser is Firefox.",
                "content_sha256": "c",
                "project_id": "",
                "created_at_ms": 1500,
                "score": 0.7,
                "provenance": {"source_message_id": "browser"},
            },
        ]
        if include_historical:
            items.append({
                "memory_id": "m-historical",
                "content": "I prefer light mode for ORION.",
                "content_sha256": "d",
                "project_id": "",
                "created_at_ms": 500,
                "score": 0.6,
                "status": "historical",
                "provenance": {"source_message_id": "hist"},
            })
        return {"items": items, "trace": {}, "context": "x"}


def main() -> int:
    assert semantic_key("I prefer dark mode for ORION.") == semantic_key(
        "My preferred ORION mode is dark."
    )
    assert semantic_key("I prefer dark mode for ORION.") != semantic_key(
        "I prefer light mode for ORION."
    )
    assert semantic_key("I prefer light mode in Orion.") == semantic_key(
        "My preferred ORION mode is light."
    )

    foundation = FakeFoundation()
    module = MemoryConsolidation(FakeReview(), foundation)

    groups = module.groups("")
    assert groups["duplicate_count"] == 1
    dark = next(
        x for x in groups["groups"]
        if x["representative_memory_id"] == "m-new-dark"
    )
    assert dark["evidence_count"] == 2
    assert dark["duplicate_memory_ids"] == ["m-old-dark"]
    assert groups["canonical_rows_mutated"] is False

    l0 = module.l0("")
    assert l0["level"] == "L0"
    assert l0["count"] == 2
    assert l0["chars"] <= 900

    l1 = module.l1("mode", project_id="", conversation_id="current")
    assert l1["hierarchy_level"] == "L1"
    assert len(l1["items"]) == 2
    current_dark = next(
        x for x in l1["items"]
        if x["memory_id"] == "m-new-dark"
    )
    assert current_dark["consolidation"]["evidence_count"] == 2
    assert current_dark["consolidation"]["duplicate_evidence"][0]["memory_id"] == "m-old-dark"
    assert l1["trace"]["consolidation"]["duplicates_collapsed"] == 1
    assert foundation.calls[-1][1]["include_historical"] is False

    l2 = module.l2("mode", project_id="", conversation_id="current")
    assert l2["hierarchy_level"] == "L2"
    assert l2["historical_expansion"] is True
    assert foundation.calls[-1][1]["include_historical"] is True

    print("ORION_MEMORY_CONSOLIDATION_V1> PASS")
    print("SEMANTIC_EQUIVALENT_DUPLICATES> COLLAPSED")
    print("PROVENANCE> PRESERVED")
    print("CANONICAL_ROWS_MUTATED> NONE")
    print("L0> PASS")
    print("L1> PASS")
    print("L2> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
