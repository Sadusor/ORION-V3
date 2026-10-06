from __future__ import annotations

import copy
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "orion_v3"))

from thehands_learning import TheHandsLearningInbox


def sample() -> dict:
    return {
        "schema": "thehands.run-evidence.v1",
        "evidence_id": "thehands-test123",
        "source_system": "TheHands",
        "hand_id": "powershell-1",
        "result": "PASS",
        "source_commit": "a" * 40,
        "hand_tree_sha": "b" * 40,
        "started_at": "2026-10-06T00:00:00+00:00",
        "finished_at": "2026-10-06T00:00:01+00:00",
        "recorded_at": "2026-10-06T00:00:02+00:00",
        "local_evidence_path": r"C:\Users\Test\AppData\Local\TheHands\runs\test123\result.json",
        "working_directory": r"E:\Example",
        "output_tail": "EXAMPLE> PASS\n",
        "provenance": {
            "actor": "owner+thehands",
            "trust_origin": "trusted_internal_execution",
            "authority": "evidence_only",
        },
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        inbox = TheHandsLearningInbox(pathlib.Path(td))
        evidence = sample()

        first = inbox.import_evidence(evidence)
        assert first["accepted"] is True
        assert first["already_imported"] is False

        second = inbox.import_evidence(evidence)
        assert second["accepted"] is True
        assert second["already_imported"] is True
        assert second["evidence_sha256"] == first["evidence_sha256"]

        candidates = inbox.list_candidates()
        assert len(candidates) == 1
        c = candidates[0]
        assert c["decision"] == "defer"
        assert c["authority"] == "evidence_only"
        assert c["source_system"] == "TheHands"
        assert c["candidate_id"] == "thehands:thehands-test123"

        altered = copy.deepcopy(evidence)
        altered["output_tail"] = "DIFFERENT\n"
        try:
            inbox.import_evidence(altered)
            raise AssertionError("collision should fail")
        except RuntimeError:
            pass

    print("ORION_THEHANDS_LEARNING_IMPORT> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
