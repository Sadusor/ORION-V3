"""Versioned Vault pending-record helpers.

The transaction marker is for exact journal deduplication, NOT authorization.
V1 pending records remain readable for interrupted upgrades.
"""
from __future__ import annotations

import re
import uuid

_MARKER = re.compile(r"^txid=([0-9a-f]{32})$")


def new_pending(entry: str, state: dict) -> dict:
    if not isinstance(entry, str) or not entry.strip():
        raise ValueError("empty journal entry")
    return {"version": 2, "txid": uuid.uuid4().hex, "phase": "commit_prepared",
            "entry": entry, "state": state}


def parse_pending(record: dict) -> tuple[str, dict, str | None]:
    if not isinstance(record, dict):
        raise ValueError("invalid pending record")
    version = record.get("version", 1)
    if version == 1:
        if not isinstance(record.get("entry"), str) or not isinstance(record.get("state"), dict):
            raise ValueError("invalid legacy pending record")
        return record["entry"], record["state"], None
    if version != 2 or record.get("phase") != "commit_prepared":
        raise ValueError("unsupported pending transaction")
    txid = record.get("txid")
    if not isinstance(txid, str) or not re.fullmatch(r"[0-9a-f]{32}", txid):
        raise ValueError("invalid transaction ID")
    if not isinstance(record.get("entry"), str) or not record["entry"].strip():
        raise ValueError("invalid journal entry")
    if not isinstance(record.get("state"), dict):
        raise ValueError("invalid pending state")
    return record["entry"], record["state"], txid


def journal_entry(entry: str, txid: str | None) -> str:
    return f"{entry} txid={txid}" if txid is not None else entry


def journal_contains(journal: str, entry: str, txid: str | None) -> bool:
    if txid is None:
        return entry in journal  # historical V1 behavior; do not change recovery semantics
    return any(line.rstrip().endswith(f"txid={txid}") for line in journal.splitlines())
