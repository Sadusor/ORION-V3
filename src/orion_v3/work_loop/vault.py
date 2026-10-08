"""Minimal project Vault: STATE.md + append-only JOURNAL.md.

The Vault is project continuity, not ORION Memory.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import uuid
import threading

from .contracts import EvidenceRecord, WorkState
from .vault_lock import exclusive_vault_lock
from .vault_transaction import new_pending, parse_pending, journal_entry, journal_contains


_STATE_MARKER = "<!-- ORION_WORK_STATE_V1 -->"


class VaultError(RuntimeError):
    pass


class ProjectVault:
    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve(strict=False)
        self.state_path = self.root / "STATE.md"
        self.journal_path = self.root / "JOURNAL.md"
        self.repo_path = self.root / "repo"
        self._mutex = threading.RLock()
        self.pending_path = self.root / "PENDING_TRANSACTION.json"

    def initialize(self, state: WorkState) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.repo_path.mkdir(exist_ok=True)
        if self.state_path.exists():
            raise VaultError("STATE.md already exists; refusing to overwrite project truth")
        self._write_state(state)
        if not self.journal_path.exists():
            self.journal_path.write_text("# Work Journal\n\n", encoding="utf-8")

    def load(self) -> WorkState:
        with self._mutex, exclusive_vault_lock(self.root):
            self._recover_pending()
            return self._read_state()

    def _read_state(self) -> WorkState:
        text = self.state_path.read_text(encoding="utf-8")
        marker = _STATE_MARKER + "\n"
        if marker not in text:
            raise VaultError("STATE.md is not an ORION Work State V1 file")
        payload = json.loads(text.split(marker, 1)[1])
        return WorkState(**payload)

    def record_verified_result(
        self,
        evidence: EvidenceRecord,
        *,
        next_action: str,
        blocked: bool | None = None,
        commit_guard=None,
        commit_coordinator=None,
        expected_generation: int | None = None,
    ) -> WorkState:
        if commit_coordinator is None:
            if expected_generation is not None:
                raise VaultError("generation requires commit coordinator")
            with self._mutex, exclusive_vault_lock(self.root):
                return self._record_under_mutex(evidence, next_action=next_action, blocked=blocked, commit_guard=commit_guard)
        if expected_generation is None:
            raise VaultError("coordinated commit requires expected generation")
        from .commit_coordinator import CommitStopped
        try:
            with commit_coordinator.commit_window(expected_generation):
                with self._mutex, exclusive_vault_lock(self.root):
                    return self._record_under_mutex(evidence, next_action=next_action, blocked=blocked, commit_guard=commit_guard)
        except CommitStopped as exc:
            raise VaultError("STOP blocked Vault commit") from exc

    def _record_under_mutex(self, evidence, *, next_action, blocked, commit_guard):
        self._recover_pending()
        current = self._read_state()
        if evidence.project_id != current.project_id or evidence.task_id != current.current_task:
            raise VaultError("evidence does not belong to current Vault task")
        updated = replace(
            current,
            last_verified_result=f"{evidence.evidence_type}:{evidence.verdict}",
            next_action=next_action,
            blocked=(evidence.verdict != "pass") if blocked is None else blocked,
        )
        entry = (
            f"{evidence.evidence_type.upper()} {evidence.verdict.upper()} "
            f"task={evidence.task_id} proposal={evidence.proposal_hash[:12]} "
            f"source={evidence.source}@{evidence.source_revision} {evidence.detail}".strip()
        )
        if commit_guard is not None and not commit_guard():
            raise VaultError("STOP blocked Vault commit")
        pending = new_pending(entry, {k: getattr(updated, k) for k in updated.__dataclass_fields__})
        self._write_pending(pending)
        self._write_state(updated)
        self.append_journal(journal_entry(entry, pending["txid"]))
        self.pending_path.unlink()
        return updated

    def _write_pending(self, payload: dict) -> None:
        temp = self.root / ("PENDING_" + uuid.uuid4().hex + ".tmp")
        try:
            with temp.open("w", encoding="utf-8") as stream:
                json.dump(payload, stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, self.pending_path)
        finally:
            temp.unlink(missing_ok=True)

    def _recover_pending(self) -> None:
        if not self.pending_path.exists():
            return
        transaction = json.loads(self.pending_path.read_text(encoding="utf-8"))
        entry, state_payload, txid = parse_pending(transaction)
        state = WorkState(**state_payload)
        self._write_state(state)
        existing = self.journal_path.read_text(encoding="utf-8") if self.journal_path.exists() else ""
        if not journal_contains(existing, entry, txid):
            self.append_journal(journal_entry(entry, txid))
        self.pending_path.unlink()

    def append_journal(self, entry: str) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        with self.journal_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(f"- {timestamp} — {entry}\n")
            handle.flush()
            os.fsync(handle.fileno())

    def _write_state(self, state: WorkState) -> None:
        payload = json.dumps(
            {
                "project_id": state.project_id,
                "objective": state.objective,
                "checkpoint": state.checkpoint,
                "current_task": state.current_task,
                "last_verified_result": state.last_verified_result,
                "next_action": state.next_action,
                "blocked": state.blocked,
                "constraints": state.constraints,
                "frozen_paths": state.frozen_paths,
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        rendered = (
            "# ORION Work State\n\n"
            "This file is canonical project continuity for the bounded Work project. "
            "It is not ORION Memory.\n\n"
            f"{_STATE_MARKER}\n{payload}\n"
        )
        temporary = self.state_path.with_suffix(".md.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(rendered)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(self.state_path)
