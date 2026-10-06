from __future__ import annotations

import hashlib
import json
import pathlib
import re
import threading
from datetime import datetime, timezone

_EVIDENCE_ID_RE = re.compile(r"^thehands-[A-Za-z0-9._-]+$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_bytes(value: dict) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _atomic_json(path: pathlib.Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


class TheHandsLearningInbox:
    """ORION-owned intake for neutral TheHands evidence.

    Imported evidence is a candidate only. This class cannot promote canonical
    Memory and never writes back into TheHands.
    """

    def __init__(self, state_root: pathlib.Path):
        self.state_root = pathlib.Path(state_root)
        self.raw_root = self.state_root / "learning-evidence" / "thehands"
        self.candidate_root = self.state_root / "memory-candidates" / "thehands"
        self.raw_root.mkdir(parents=True, exist_ok=True)
        self.candidate_root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()

    @staticmethod
    def evidence_sha256(evidence: dict) -> str:
        return hashlib.sha256(_canonical_bytes(evidence)).hexdigest()

    @staticmethod
    def _validate(evidence: dict) -> tuple[str, dict]:
        if not isinstance(evidence, dict):
            raise ValueError("evidence must be a JSON object")
        if evidence.get("schema") != "thehands.run-evidence.v1":
            raise ValueError("unsupported evidence schema")
        if evidence.get("source_system") != "TheHands":
            raise ValueError("source_system must be TheHands")

        evidence_id = str(evidence.get("evidence_id") or "").strip()
        if not _EVIDENCE_ID_RE.fullmatch(evidence_id):
            raise ValueError("invalid TheHands evidence_id")

        provenance = evidence.get("provenance")
        if not isinstance(provenance, dict):
            raise ValueError("provenance is required")
        if provenance.get("authority") != "evidence_only":
            raise ValueError("TheHands payload must remain evidence_only")

        result = str(evidence.get("result") or "").upper()
        if result not in {"PASS", "FAIL", "STOPPED"}:
            raise ValueError("unsupported TheHands result")

        return evidence_id, provenance

    def import_evidence(self, evidence: dict) -> dict:
        evidence_id, provenance = self._validate(evidence)
        digest = self.evidence_sha256(evidence)
        safe_id = evidence_id.replace(":", "_")
        raw_path = self.raw_root / f"{safe_id}.json"
        candidate_path = self.candidate_root / f"{safe_id}.json"

        with self.lock:
            if candidate_path.exists():
                existing = json.loads(candidate_path.read_text(encoding="utf-8-sig"))
                existing_hash = str(existing.get("evidence_sha256") or "")
                if existing_hash != digest:
                    raise RuntimeError("evidence_id collision with different content")
                return {
                    "ok": True,
                    "accepted": True,
                    "already_imported": True,
                    "evidence_id": evidence_id,
                    "evidence_sha256": digest,
                    "candidate_id": existing.get("candidate_id"),
                }

            _atomic_json(raw_path, evidence)

            tail = str(evidence.get("output_tail") or "").strip()
            last_line = next(
                (line.strip() for line in reversed(tail.splitlines()) if line.strip()),
                "",
            )
            result = str(evidence.get("result") or "").upper()
            hand_id = str(evidence.get("hand_id") or "hand")
            content = f"TheHands {hand_id} {result}"
            if last_line:
                content += f" · {last_line[:240]}"

            candidate = {
                "schema": "orion-v3.memory-candidate/1",
                "candidate_id": f"thehands:{evidence_id}",
                "content": content,
                "classification": "THEHANDS_EXECUTION_EVIDENCE",
                "submitted_at": str(evidence.get("recorded_at") or _now()),
                "source_actor": str(provenance.get("actor") or "owner+thehands"),
                "source_ref": evidence_id,
                "trust_origin": str(provenance.get("trust_origin") or "trusted_internal_execution"),
                "confidence": None,
                "decision": "defer",
                "decision_reason": "Imported execution evidence only; canonical Memory review has not run.",
                "reason_for_candidate": "Completed TheHands execution evidence is available for ORION learning review.",
                "task_id": evidence_id,
                "evidence_sha256": digest,
                "evidence_path": str(raw_path),
                "source_system": "TheHands",
                "authority": "evidence_only",
                "result": result,
                "hand_id": hand_id,
                "source_commit": str(evidence.get("source_commit") or ""),
                "hand_tree_sha": str(evidence.get("hand_tree_sha") or ""),
                "working_directory": str(evidence.get("working_directory") or ""),
                "received_at": _now(),
            }
            _atomic_json(candidate_path, candidate)

        return {
            "ok": True,
            "accepted": True,
            "already_imported": False,
            "evidence_id": evidence_id,
            "evidence_sha256": digest,
            "candidate_id": candidate["candidate_id"],
        }

    def list_candidates(self) -> list[dict]:
        items: list[dict] = []
        with self.lock:
            for path in self.candidate_root.glob("*.json"):
                try:
                    value = json.loads(path.read_text(encoding="utf-8-sig"))
                except Exception:
                    continue
                if isinstance(value, dict):
                    items.append(value)
        items.sort(key=lambda x: str(x.get("submitted_at") or ""), reverse=True)
        return items
