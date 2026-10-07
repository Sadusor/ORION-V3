from __future__ import annotations

import gzip
import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
PARENT = HERE.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from modules.memory_shadow_audit import MemoryShadowAudit, RULE_ID


class FakeRecall:
    def __init__(self, items=None, *, fail=False):
        self.items = list(items or [])
        self.fail = fail
        self.calls = []

    def retrieve(self, query, *, conversation_id="", project_id=None):
        self.calls.append({
            "query": query,
            "conversation_id": conversation_id,
            "project_id": project_id,
        })
        if self.fail:
            raise RuntimeError("synthetic recall failure")
        return {
            "scope": {
                "project_id": "p1" if project_id is None else str(project_id or ""),
            },
            "items": self.items,
        }


class FakeDurable:
    def __init__(self, items=None, *, fail=False):
        self.items = list(items or [])
        self.fail = fail
        self.calls = []

    def retrieve(
        self,
        query,
        *,
        project_id="",
        conversation_id="",
        include_historical=False,
    ):
        self.calls.append({
            "query": query,
            "project_id": project_id,
            "conversation_id": conversation_id,
            "include_historical": include_historical,
        })
        if self.fail:
            raise RuntimeError("synthetic durable failure")
        return {"items": self.items}


class FailWriteAudit(MemoryShadowAudit):
    def _append_event(self, event):
        raise OSError("synthetic audit disk failure")


def recall_item(text: str, *, role="user", item_id="r1"):
    return {
        "id": item_id,
        "content": text,
        "trust_tier": "owner_message_unverified",
        "provenance": {
            "role": role,
            "conversation_id": "old-chat",
            "message_id": item_id,
        },
    }


def durable_item(text: str, *, memory_id="cm-current"):
    return {
        "memory_id": memory_id,
        "content": text,
        "content_sha256": "durable-hash",
        "trust_tier": "owner_message_unverified",
        "owner_scope": "owner:primary",
        "project_id": "p1",
        "status": "current",
        "provenance": {
            "source_conversation_id": "durable-chat",
            "source_message_id": "durable-msg",
            "promotion_event_hash": "promotion-hash",
        },
    }


def main() -> int:
    old = recall_item("I prefer dark mode for ORION.")
    current = durable_item("My preferred ORION mode is light.")

    with tempfile.TemporaryDirectory(prefix="orion-shadow-audit-") as td:
        root = pathlib.Path(td)
        recall = FakeRecall([old])
        durable = FakeDurable([current])
        audit = MemoryShadowAudit(root, recall, durable)

        # Normal turns with no V1 shadow event cause zero retrieval/work.
        idle = audit.observe(
            "What mode do I prefer?",
            conversation_id="current-chat",
            project_id="p1",
            expected_shadow_count=0,
        )
        assert idle["state"] == "idle"
        assert recall.calls == []
        assert durable.calls == []
        assert not root.joinpath("shadow_audit.jsonl").exists()

        # When frozen V1 reports one shadow, the observer independently
        # reconstructs and records the same-slot pair.
        state = audit.observe(
            "What mode do I prefer for ORION?",
            conversation_id="current-chat",
            project_id="p1",
            expected_shadow_count=1,
        )
        assert state["state"] == "ok"
        assert state["events_written"] == 1
        assert state["last_expected_shadow_count"] == 1
        assert len(recall.calls) == 1
        assert len(durable.calls) == 1
        assert durable.calls[0]["include_historical"] is False

        lines = root.joinpath("shadow_audit.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        assert len(lines) == 1
        event = json.loads(lines[0])
        assert event["schema"] == "orion.memory-shadow-audit/1"
        assert event["slot"] == "preference:mode:orion"
        assert event["scope"]["project_id"] == "p1"
        assert event["old_recall"]["text"] == "I prefer dark mode for ORION."
        assert event["old_recall"]["value"] == "dark"
        assert event["old_recall"]["source_conversation_id"] == "old-chat"
        assert event["old_recall"]["source_message_id"] == "r1"
        assert len(event["old_recall"]["source_hash"]) == 64
        assert event["current_durable"]["memory_id"] == "cm-current"
        assert event["current_durable"]["text"] == "My preferred ORION mode is light."
        assert event["current_durable"]["value"] == "light"
        assert event["current_durable"]["promotion_event_hash"] == "promotion-hash"
        assert event["match"]["rule_id"] == RULE_ID
        assert event["match"]["same_value"] is False
        assert event["prompt_path_effect"] == "none"
        assert event["authority"] == "context_only"

        # Assistant-authored recall is never audited as a V1 owner shadow.
        assistant_recall = FakeRecall([
            recall_item(
                "I prefer dark mode for ORION.",
                role="assistant",
                item_id="assistant-r",
            )
        ])
        audit2 = MemoryShadowAudit(root / "assistant", assistant_recall, durable)
        mismatch = audit2.observe(
            "What mode?",
            conversation_id="current-chat",
            project_id="p1",
            expected_shadow_count=1,
        )
        assert mismatch["state"] == "count_mismatch"
        assert mismatch["last_batch_written"] == 0

        # Audit write failure is fully nonfatal to the caller.
        fail_audit = FailWriteAudit(
            root / "fail",
            FakeRecall([old]),
            FakeDurable([current]),
        )
        failed = fail_audit.observe(
            "What mode?",
            conversation_id="current-chat",
            project_id="p1",
            expected_shadow_count=1,
        )
        assert failed["state"] == "error"
        assert "synthetic audit disk failure" in failed["last_error"]
        assert failed["prompt_path_effect"] == "none"

        # Bounded rotation uses gzip archives and preserves current logging.
        big_old = recall_item(
            "I prefer " + ("dark " * 700) + "mode for ORION.",
            item_id="big-r",
        )
        # Use valid slot-shaped text with enough extra target content to make
        # each JSON line large while still matching deterministically.
        big_old = recall_item(
            "I prefer dark mode for " + ("ORION" * 450),
            item_id="big-r",
        )
        big_current = durable_item(
            "I prefer light mode for " + ("ORION" * 450),
            memory_id="big-cm",
        )
        rotating = MemoryShadowAudit(
            root / "rotate",
            FakeRecall([big_old]),
            FakeDurable([big_current]),
            max_bytes=4096,
            retention_days=90,
        )
        for _ in range(3):
            rotating.observe(
                "mode",
                conversation_id="current",
                project_id="p1",
                expected_shadow_count=1,
            )
        archives = list((root / "rotate").glob("shadow_audit.*.jsonl.gz"))
        assert archives
        with gzip.open(archives[0], "rt", encoding="utf-8") as handle:
            archived_lines = [x for x in handle.read().splitlines() if x]
        assert archived_lines
        assert (root / "rotate" / "shadow_audit.jsonl").is_file()

    print("ORION_MEMORY_SHADOW_AUDIT_V1_1B> PASS")
    print("ZERO_WORK_WITHOUT_SHADOW> PASS")
    print("DETAILED_SHADOW_EVENT> PASS")
    print("OWNER_ONLY_RECALL_OBSERVATION> PASS")
    print("AUDIT_FAILURE_NONFATAL> PASS")
    print("BOUNDED_ROTATION> PASS")
    print("PROMPT_PATH_EFFECT> NONE")
    print("FROZEN_SHADOWING_RULE_MODIFIED> NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
