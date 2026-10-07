from __future__ import annotations

import copy
import datetime as _dt
import hashlib
import json
import pathlib
import threading
from typing import Any

SCHEMA = "orion.memory-integrity-anchor/1"
HEAD_SCHEMA = "orion.memory-integrity-head/1"
ROOT_ALGO = "sha256-canonical-projection-v1"


class MemoryIntegrityError(RuntimeError):
    pass


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _record_hash(record: dict[str, Any]) -> str:
    body = {k: v for k, v in record.items() if k != "anchor_hash"}
    return _sha256_text(_canonical_json(body))


def _projection_root(
    canonical_rows: list[dict[str, Any]],
    decision_events: list[dict[str, Any]],
    supersession_events: list[dict[str, Any]],
) -> str:
    projection = {
        "schema": "orion.memory-integrity-projection/1",
        "canonical": sorted(
            [copy.deepcopy(x) for x in canonical_rows if isinstance(x, dict)],
            key=lambda x: (
                str(x.get("owner_scope") or ""),
                str(x.get("project_id") or ""),
                str(x.get("memory_id") or ""),
            ),
        ),
        "decisions": sorted(
            [copy.deepcopy(x) for x in decision_events if isinstance(x, dict)],
            key=lambda x: (
                int(x.get("event_index") or 0),
                str(x.get("decision_id") or ""),
            ),
        ),
        "supersessions": sorted(
            [copy.deepcopy(x) for x in supersession_events if isinstance(x, dict)],
            key=lambda x: (
                int(x.get("event_index") or 0),
                str(x.get("supersession_id") or ""),
            ),
        ),
    }
    return _sha256_text(_canonical_json(projection))


class MemoryIntegrityAnchor:
    """Local tamper-evidence sidecar for frozen Memory V1.

    Reads the existing durable-memory public projections only. It never writes
    canonical memory, decisions, candidates, or supersession ledgers.
    """

    def __init__(
        self,
        directory: pathlib.Path,
        review: Any,
        foundation: Any,
    ):
        self.directory = pathlib.Path(directory)
        self.log_path = self.directory / "anchor.jsonl"
        self.head_path = self.directory / "anchor_head.json"
        self.review = review
        self.foundation = foundation
        self._lock = threading.RLock()
        self._status: dict[str, Any] = {
            "schema": SCHEMA,
            "state": "uninitialized",
            "writes_frozen": True,
            "reason": "not_verified",
            "head_seq": 0,
            "head_root": "",
            "matched_seq": 0,
            "last_verified_utc": "",
            "local_only": True,
            "external_mirror": False,
        }

    def _snapshot(self) -> dict[str, Any]:
        canonical = self.review.list_canonical(include_revoked=True)
        decisions = self.review.decisions()
        supersessions = self.foundation.supersessions()
        decision_audit = self.review.audit_chain()
        supersession_audit = self.foundation.audit_supersessions()

        canonical_rows = [
            copy.deepcopy(x)
            for x in canonical.get("all_memories", [])
            if isinstance(x, dict)
        ]
        decision_events = [
            copy.deepcopy(x)
            for x in decisions.get("events", [])
            if isinstance(x, dict)
        ]
        supersession_events = [
            copy.deepcopy(x)
            for x in supersessions.get("events", [])
            if isinstance(x, dict)
        ]
        return {
            "root": _projection_root(
                canonical_rows,
                decision_events,
                supersession_events,
            ),
            "counts": {
                "canonical_records": len(canonical_rows),
                "canonical_current_raw": int(canonical.get("count") or 0),
                "canonical_revoked": int(canonical.get("revoked_count") or 0),
                "decision_events": len(decision_events),
                "supersession_events": len(supersession_events),
            },
            "internal_audit": {
                "decisions_ok": bool(decision_audit.get("ok")),
                "decision_head_hash": str(decision_audit.get("head_hash") or ""),
                "decision_problems": list(decision_audit.get("problems") or []),
                "supersessions_ok": bool(supersession_audit.get("ok")),
                "supersession_head_hash": str(
                    supersession_audit.get("head_hash") or ""
                ),
                "supersession_problems": list(
                    supersession_audit.get("problems") or []
                ),
            },
        }

    def _read_records(self) -> tuple[list[dict[str, Any]], list[str]]:
        if not self.log_path.is_file():
            return [], []
        records: list[dict[str, Any]] = []
        problems: list[str] = []
        expected_seq = 1
        previous_anchor_hash = ""
        try:
            lines = self.log_path.read_text(encoding="utf-8").splitlines()
        except Exception as exc:
            return [], ["anchor log unreadable: " + str(exc)]
        for line_no, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except Exception as exc:
                problems.append(f"line {line_no}: invalid JSON: {exc}")
                continue
            if not isinstance(record, dict):
                problems.append(f"line {line_no}: record is not an object")
                continue
            seq = int(record.get("seq") or 0)
            if seq != expected_seq:
                problems.append(
                    f"line {line_no}: seq {seq} expected {expected_seq}"
                )
            if str(record.get("prev_anchor_hash") or "") != previous_anchor_hash:
                problems.append(
                    f"line {line_no}: previous anchor hash mismatch"
                )
            expected_hash = _record_hash(record)
            actual_hash = str(record.get("anchor_hash") or "")
            if expected_hash != actual_hash:
                problems.append(f"line {line_no}: anchor hash mismatch")
            previous_anchor_hash = actual_hash
            expected_seq = seq + 1
            records.append(record)
        return records, problems

    def _write_head(self, record: dict[str, Any]) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": HEAD_SCHEMA,
            "seq": int(record.get("seq") or 0),
            "root": str(record.get("root") or ""),
            "anchor_hash": str(record.get("anchor_hash") or ""),
            "ts_utc": str(record.get("ts_utc") or ""),
        }
        temp = self.head_path.with_suffix(".json.tmp")
        temp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temp.replace(self.head_path)

    def _append_anchor(
        self,
        *,
        snapshot: dict[str, Any],
        cause: str,
        event: str = "commit",
        actor_fingerprint: str = "",
    ) -> dict[str, Any]:
        records, problems = self._read_records()
        if problems:
            raise MemoryIntegrityError(
                "anchor log chain invalid: " + "; ".join(problems[:3])
            )
        previous = records[-1] if records else {}
        record: dict[str, Any] = {
            "schema": SCHEMA,
            "seq": len(records) + 1,
            "ts_utc": _now(),
            "event": str(event or "commit"),
            "cause": str(cause or "unspecified")[:80],
            "root_algo": ROOT_ALGO,
            "root": str(snapshot.get("root") or ""),
            "prev_root": str(previous.get("root") or ""),
            "prev_anchor_hash": str(previous.get("anchor_hash") or ""),
            "counts": copy.deepcopy(snapshot.get("counts") or {}),
            "internal_audit": copy.deepcopy(
                snapshot.get("internal_audit") or {}
            ),
            "actor_fingerprint": str(actor_fingerprint or "")[:120],
            "local_only": True,
            "external_mirror": False,
        }
        record["anchor_hash"] = _record_hash(record)
        self.directory.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(_canonical_json(record) + "\n")
            handle.flush()
        self._write_head(record)
        return record

    def _set_status(
        self,
        *,
        state: str,
        writes_frozen: bool,
        reason: str,
        head: dict[str, Any] | None = None,
        matched_seq: int = 0,
        snapshot: dict[str, Any] | None = None,
        problems: list[str] | None = None,
    ) -> dict[str, Any]:
        head = head or {}
        snapshot = snapshot or {}
        self._status = {
            "schema": SCHEMA,
            "state": state,
            "writes_frozen": bool(writes_frozen),
            "reason": str(reason or ""),
            "head_seq": int(head.get("seq") or 0),
            "head_root": str(head.get("root") or ""),
            "current_root": str(snapshot.get("root") or ""),
            "matched_seq": int(matched_seq or 0),
            "counts": copy.deepcopy(snapshot.get("counts") or {}),
            "internal_audit": copy.deepcopy(
                snapshot.get("internal_audit") or {}
            ),
            "anchor_problems": list(problems or []),
            "last_verified_utc": _now(),
            "local_only": True,
            "external_mirror": False,
        }
        return copy.deepcopy(self._status)

    def initialize(self) -> dict[str, Any]:
        """Verify current durable state against local anchor history.

        Never raises into ORION startup. Any verifier failure freezes future
        durable-memory writes while leaving reads and the rest of ORION usable.
        """
        with self._lock:
            try:
                snapshot = self._snapshot()
                internal = snapshot["internal_audit"]
                if not internal["decisions_ok"] or not internal["supersessions_ok"]:
                    return self._set_status(
                        state="mismatch",
                        writes_frozen=True,
                        reason="internal_append_only_audit_failed",
                        snapshot=snapshot,
                    )

                records, problems = self._read_records()
                if problems:
                    return self._set_status(
                        state="mismatch",
                        writes_frozen=True,
                        reason="anchor_log_chain_invalid",
                        head=(records[-1] if records else None),
                        snapshot=snapshot,
                        problems=problems,
                    )

                if not records:
                    record = self._append_anchor(
                        snapshot=snapshot,
                        cause="first_verified_state",
                        event="bootstrap",
                    )
                    return self._set_status(
                        state="ok",
                        writes_frozen=False,
                        reason="bootstrap_anchor_created",
                        head=record,
                        matched_seq=int(record["seq"]),
                        snapshot=snapshot,
                    )

                head = records[-1]
                current_root = str(snapshot["root"])
                if current_root == str(head.get("root") or ""):
                    try:
                        self._write_head(head)
                    except Exception:
                        pass
                    return self._set_status(
                        state="ok",
                        writes_frozen=False,
                        reason="verified_against_head",
                        head=head,
                        matched_seq=int(head.get("seq") or 0),
                        snapshot=snapshot,
                    )

                matched = next(
                    (
                        record
                        for record in reversed(records[:-1])
                        if str(record.get("root") or "") == current_root
                    ),
                    None,
                )
                if matched:
                    return self._set_status(
                        state="rollback_detected",
                        writes_frozen=True,
                        reason="current_state_matches_older_anchor",
                        head=head,
                        matched_seq=int(matched.get("seq") or 0),
                        snapshot=snapshot,
                    )

                return self._set_status(
                    state="mismatch",
                    writes_frozen=True,
                    reason="current_state_not_in_anchor_history",
                    head=head,
                    snapshot=snapshot,
                )
            except Exception as exc:
                return self._set_status(
                    state="error",
                    writes_frozen=True,
                    reason="integrity_verifier_error:" + exc.__class__.__name__,
                    problems=[str(exc)],
                )

    def observe_commit(
        self,
        *,
        cause: str,
        actor_fingerprint: str = "",
    ) -> dict[str, Any]:
        """Anchor state after an already-committed durable-memory write.

        A sidecar failure never rewrites/rolls back the committed V1 decision.
        It freezes subsequent durable writes until owner recovery.
        """
        with self._lock:
            try:
                snapshot = self._snapshot()
                internal = snapshot["internal_audit"]
                if not internal["decisions_ok"] or not internal["supersessions_ok"]:
                    return self._set_status(
                        state="mismatch",
                        writes_frozen=True,
                        reason="post_commit_internal_audit_failed",
                        snapshot=snapshot,
                    )
                records, problems = self._read_records()
                if problems:
                    return self._set_status(
                        state="mismatch",
                        writes_frozen=True,
                        reason="post_commit_anchor_log_invalid",
                        head=(records[-1] if records else None),
                        snapshot=snapshot,
                        problems=problems,
                    )
                head = records[-1] if records else None
                if head and str(head.get("root") or "") == str(snapshot["root"]):
                    return self._set_status(
                        state="ok",
                        writes_frozen=False,
                        reason="state_already_anchored",
                        head=head,
                        matched_seq=int(head.get("seq") or 0),
                        snapshot=snapshot,
                    )
                record = self._append_anchor(
                    snapshot=snapshot,
                    cause=cause,
                    event="commit",
                    actor_fingerprint=actor_fingerprint,
                )
                return self._set_status(
                    state="ok",
                    writes_frozen=False,
                    reason="post_commit_anchor_written",
                    head=record,
                    matched_seq=int(record["seq"]),
                    snapshot=snapshot,
                )
            except Exception as exc:
                current = copy.deepcopy(self._status)
                current.update(
                    {
                        "schema": SCHEMA,
                        "state": "error",
                        "writes_frozen": True,
                        "reason": "post_commit_anchor_write_failed",
                        "anchor_problems": [str(exc)],
                        "last_verified_utc": _now(),
                        "local_only": True,
                        "external_mirror": False,
                    }
                )
                self._status = current
                return copy.deepcopy(self._status)

    def accept_current(
        self,
        *,
        actor_fingerprint: str,
        reason: str,
    ) -> dict[str, Any]:
        """Explicit owner recovery: accept current durable state and re-anchor."""
        actor_fingerprint = str(actor_fingerprint or "").strip()
        reason = str(reason or "").strip()
        if not actor_fingerprint:
            raise MemoryIntegrityError("Owner actor fingerprint is required.")
        if not reason:
            raise MemoryIntegrityError("Recovery reason is required.")
        with self._lock:
            snapshot = self._snapshot()
            internal = snapshot["internal_audit"]
            if not internal["decisions_ok"] or not internal["supersessions_ok"]:
                raise MemoryIntegrityError(
                    "Cannot accept current state while internal append-only audit fails."
                )
            record = self._append_anchor(
                snapshot=snapshot,
                cause=reason[:80],
                event="owner_reanchor",
                actor_fingerprint=actor_fingerprint,
            )
            return self._set_status(
                state="ok",
                writes_frozen=False,
                reason="owner_reanchored_current_state",
                head=record,
                matched_seq=int(record["seq"]),
                snapshot=snapshot,
            )

    def writes_allowed(self) -> bool:
        with self._lock:
            return not bool(self._status.get("writes_frozen", True))

    def status(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._status)
