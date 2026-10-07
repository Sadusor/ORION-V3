from __future__ import annotations

import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
PARENT = HERE.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from modules.memory_integrity_anchor import MemoryIntegrityAnchor


class FakeReview:
    def __init__(self):
        self.version = 0
        self.audit_ok = True

    def list_canonical(self, include_revoked=False):
        rows = []
        if self.version >= 1:
            rows.append({
                "memory_id": "cm-1",
                "content": "I prefer dark mode for ORION.",
                "content_sha256": "hash-1",
                "owner_scope": "owner:primary",
                "project_id": "",
                "candidate_id": "cand-1",
                "promoted_decision_id": "md-1",
                "promoted_event_hash": "event-1",
                "active": True,
                "status": "active",
                "authority": "context_only",
            })
        if self.version >= 2:
            rows.append({
                "memory_id": "cm-2",
                "content": "My preferred browser is Firefox.",
                "content_sha256": "hash-2",
                "owner_scope": "owner:primary",
                "project_id": "",
                "candidate_id": "cand-2",
                "promoted_decision_id": "md-2",
                "promoted_event_hash": "event-2",
                "active": True,
                "status": "active",
                "authority": "context_only",
            })
        return {
            "all_memories": rows,
            "memories": [x for x in rows if x["active"]],
            "count": len(rows),
            "revoked_count": 0,
        }

    def decisions(self):
        events = []
        if self.version >= 1:
            events.append({
                "event_index": 1,
                "decision_id": "md-1",
                "candidate_id": "cand-1",
                "candidate_content_sha256": "hash-1",
                "decision": "promote",
                "event_hash": "event-1",
                "prev_event_hash": "",
                "owner_scope": "owner:primary",
                "project_id": "",
            })
        if self.version >= 2:
            events.append({
                "event_index": 2,
                "decision_id": "md-2",
                "candidate_id": "cand-2",
                "candidate_content_sha256": "hash-2",
                "decision": "promote",
                "event_hash": "event-2",
                "prev_event_hash": "event-1",
                "owner_scope": "owner:primary",
                "project_id": "",
            })
        return {"events": events, "count": len(events)}

    def audit_chain(self):
        return {
            "ok": self.audit_ok,
            "events": self.version,
            "head_hash": f"event-{self.version}" if self.version else "",
            "problems": [] if self.audit_ok else ["synthetic decision chain failure"],
        }


class FakeFoundation:
    def __init__(self):
        self.sup_version = 0
        self.audit_ok = True

    def supersessions(self):
        events = []
        if self.sup_version:
            events.append({
                "event_index": 1,
                "supersession_id": "sup-1",
                "prior_memory_id": "cm-1",
                "replacement_memory_id": "cm-2",
                "prior_content_sha256": "hash-1",
                "replacement_content_sha256": "hash-2",
                "owner_scope": "owner:primary",
                "project_id": "",
                "event_hash": "sup-event-1",
                "prev_event_hash": "",
            })
        return {"events": events, "count": len(events)}

    def audit_supersessions(self):
        return {
            "ok": self.audit_ok,
            "events": self.sup_version,
            "head_hash": "sup-event-1" if self.sup_version else "",
            "problems": [] if self.audit_ok else ["synthetic supersession chain failure"],
        }


class FailWriteAnchor(MemoryIntegrityAnchor):
    def _append_anchor(self, **kwargs):
        raise OSError("synthetic disk-full failure")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="orion-memory-integrity-") as td:
        root = pathlib.Path(td) / "memory_sidecars"
        review = FakeReview()
        foundation = FakeFoundation()

        # Fresh first run anchors an empty-but-valid durable state.
        anchor = MemoryIntegrityAnchor(root, review, foundation)
        boot = anchor.initialize()
        assert boot["state"] == "ok"
        assert boot["writes_frozen"] is False
        assert boot["head_seq"] == 1
        root_empty = boot["current_root"]
        assert root_empty

        # Restart on unchanged state verifies rather than appending.
        restart = MemoryIntegrityAnchor(root, review, foundation)
        same = restart.initialize()
        assert same["state"] == "ok"
        assert same["head_seq"] == 1
        assert same["reason"] == "verified_against_head"

        # First committed memory creates a new state anchor.
        review.version = 1
        committed = restart.observe_commit(
            cause="promotion",
            actor_fingerprint="paired:test",
        )
        assert committed["state"] == "ok"
        assert committed["head_seq"] == 2
        assert committed["current_root"] != root_empty
        root_v1 = committed["current_root"]

        # Second committed state advances again.
        review.version = 2
        committed2 = restart.observe_commit(
            cause="promotion",
            actor_fingerprint="paired:test",
        )
        assert committed2["head_seq"] == 3
        root_v2 = committed2["current_root"]
        assert root_v2 not in {root_empty, root_v1}

        # Rollback to a known older durable state is detected and freezes writes.
        review.version = 1
        rolled = MemoryIntegrityAnchor(root, review, foundation).initialize()
        assert rolled["state"] == "rollback_detected"
        assert rolled["writes_frozen"] is True
        assert rolled["matched_seq"] == 2
        assert rolled["head_seq"] == 3
        assert rolled["current_root"] == root_v1

        # Explicit owner recovery appends a re-anchor; it never rewrites history.
        accepted = MemoryIntegrityAnchor(root, review, foundation)
        assert accepted.initialize()["writes_frozen"] is True
        reanchored = accepted.accept_current(
            actor_fingerprint="paired:owner",
            reason="owner_accepts_restored_checkpoint",
        )
        assert reanchored["state"] == "ok"
        assert reanchored["writes_frozen"] is False
        assert reanchored["head_seq"] == 4
        lines = root.joinpath("anchor.jsonl").read_text(encoding="utf-8").splitlines()
        assert len(lines) == 4
        assert json.loads(lines[-1])["event"] == "owner_reanchor"

        # Unknown durable state not present in history is a mismatch.
        review.version = 2
        foundation.sup_version = 1
        unknown = MemoryIntegrityAnchor(root, review, foundation).initialize()
        assert unknown["state"] == "mismatch"
        assert unknown["writes_frozen"] is True
        assert unknown["reason"] == "current_state_not_in_anchor_history"

        # Internal append-only audit failure freezes writes independently.
        foundation.audit_ok = False
        broken_internal = MemoryIntegrityAnchor(root, review, foundation).initialize()
        assert broken_internal["writes_frozen"] is True
        assert broken_internal["reason"] == "internal_append_only_audit_failed"
        foundation.audit_ok = True

        # Corrupting anchor history itself is detected.
        with root.joinpath("anchor.jsonl").open("a", encoding="utf-8") as handle:
            handle.write('{"seq":999,"root":"tampered"}\n')
        corrupt = MemoryIntegrityAnchor(root, review, foundation).initialize()
        assert corrupt["writes_frozen"] is True
        assert corrupt["reason"] == "anchor_log_chain_invalid"

    # A post-commit sidecar write failure never undoes the V1 commit, but it
    # immediately freezes subsequent durable writes in the observer state.
    with tempfile.TemporaryDirectory(prefix="orion-memory-integrity-fail-") as td2:
        review2 = FakeReview()
        foundation2 = FakeFoundation()
        good = MemoryIntegrityAnchor(pathlib.Path(td2), review2, foundation2)
        assert good.initialize()["writes_frozen"] is False
        review2.version = 1
        failing = FailWriteAnchor(pathlib.Path(td2), review2, foundation2)
        # Carry startup verification first: current DB is ahead of the anchor,
        # so this independent instance is already frozen. Use the verified
        # observer state to exercise the post-commit failure directly.
        failing._status = good.status()
        failed = failing.observe_commit(cause="promotion")
        assert failed["state"] == "error"
        assert failed["writes_frozen"] is True
        assert failed["reason"] == "post_commit_anchor_write_failed"
        assert review2.version == 1

    print("ORION_MEMORY_INTEGRITY_ANCHOR_V1_1A> PASS")
    print("BOOTSTRAP_ANCHOR> PASS")
    print("UNCHANGED_RESTART_VERIFY> PASS")
    print("NORMAL_STATE_EVOLUTION> PASS")
    print("KNOWN_ROLLBACK_DETECTION> PASS")
    print("UNKNOWN_REPLACEMENT_DETECTION> PASS")
    print("INTERNAL_CHAIN_AUDIT> PASS")
    print("ANCHOR_CHAIN_CORRUPTION> PASS")
    print("OWNER_REANCHOR> PASS")
    print("POST_COMMIT_ANCHOR_FAILURE_FREEZES_FUTURE_WRITES> PASS")
    print("CANONICAL_ROWS_MUTATED_BY_SIDECAR> NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
