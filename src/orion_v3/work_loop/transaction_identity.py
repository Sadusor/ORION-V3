"""Stable, bounded transaction identities for Work Loop journal records.

This module does not grant authority, perform I/O, or change the Vault.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import re

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class TransactionIdentity:
    project_id: str
    task_id: str
    proposal_hash: str
    source_revision: str
    evidence_type: str
    verdict: str

    def __post_init__(self):
        if not self.project_id or not self.task_id or not self.source_revision:
            raise ValueError("transaction identity fields cannot be empty")
        if not _HEX64.fullmatch(self.proposal_hash):
            raise ValueError("proposal hash must be 64 lowercase hex characters")
        if self.evidence_type not in {"git_check", "execution", "test", "benchmark", "lint", "manual"}:
            raise ValueError("unknown evidence type")
        if self.verdict not in {"pass", "fail", "malformed", "indeterminate"}:
            raise ValueError("unknown verdict")

    @property
    def digest(self) -> str:
        payload = [
            "orion-work-transaction-v1", self.project_id, self.task_id,
            self.proposal_hash, self.source_revision, self.evidence_type,
            self.verdict,
        ]
        return hashlib.sha256(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
