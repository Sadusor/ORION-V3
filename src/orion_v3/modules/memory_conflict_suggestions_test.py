from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
PARENT = HERE.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from modules.memory_conflict_suggestions import MemoryConflictSuggestions, memory_slot


class FakeReview:
    def list_canonical(self, *, include_revoked=False):
        all_memories = [
            {
                "memory_id": "old",
                "content": "I prefer dark mode for ORION.",
                "project_id": "",
                "created_at_ms": 1000,
                "active": True,
                "status": "active",
            },
            {
                "memory_id": "new",
                "content": "I prefer light mode for ORION.",
                "project_id": "",
                "created_at_ms": 2000,
                "active": True,
                "status": "active",
            },
            {
                "memory_id": "other",
                "content": "My preferred browser is Firefox.",
                "project_id": "",
                "created_at_ms": 1500,
                "active": True,
                "status": "active",
            },
            {
                "memory_id": "project",
                "content": "I prefer blue mode for ORION.",
                "project_id": "project-a",
                "created_at_ms": 3000,
                "active": True,
                "status": "active",
            },
        ]
        return {
            "all_memories": all_memories,
            "memories": all_memories,
            "count": len(all_memories),
        }


class FakeFoundation:
    def __init__(self, events=None):
        self.events = list(events or [])

    def supersessions(self):
        return {"events": list(self.events), "count": len(self.events)}


def main() -> int:
    assert memory_slot("I prefer dark mode for ORION.") == (
        "preference:mode:orion",
        "dark",
    )
    assert memory_slot("I prefer light mode for ORION.") == (
        "preference:mode:orion",
        "light",
    )
    assert memory_slot("I prefer ORION in dark mode.") == (
        "preference:mode:orion",
        "dark",
    )
    assert memory_slot("For ORION, I prefer light mode.") == (
        "preference:mode:orion",
        "light",
    )
    assert memory_slot("My preferred mode for ORION is dark.") == (
        "preference:mode:orion",
        "dark",
    )
    assert memory_slot("My preferred ORION mode is light.") == (
        "preference:mode:orion",
        "light",
    )
    assert memory_slot("I prefer Firefox as my browser.") == (
        "preference:browser:owner",
        "firefox",
    )
    assert memory_slot("My preferred browser is Chrome.") == (
        "preference:browser:owner",
        "chrome",
    )
    assert memory_slot("What mode do I prefer for ORION?") is None

    view = MemoryConflictSuggestions(FakeReview(), FakeFoundation()).view()
    assert view["automatic_supersession"] is False
    assert view["owner_review_required"] is True
    assert view["count"] == 1
    item = view["suggestions"][0]
    assert item["prior_memory_id"] == "old"
    assert item["replacement_memory_id"] == "new"
    assert item["prior_content"] == "I prefer dark mode for ORION."
    assert item["replacement_content"] == "I prefer light mode for ORION."
    assert item["decision"] == "owner_required"

    resolved = MemoryConflictSuggestions(
        FakeReview(),
        FakeFoundation([{
            "prior_memory_id": "old",
            "replacement_memory_id": "new",
        }]),
    ).view()
    assert resolved["count"] == 0

    print("ORION_MEMORY_CONFLICT_SUGGESTIONS_V1> PASS")
    print("SAME_SLOT_DIFFERENT_VALUE> PASS")
    print("PREFERENCE_PHRASING_NORMALIZATION> PASS")
    print("CROSS_PROJECT_NOT_MERGED> PASS")
    print("OWNER_DECISION_REQUIRED> PASS")
    print("AUTOMATIC_SUPERSESSION> NONE")
    print("RESOLVED_CONFLICT_HIDDEN> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
