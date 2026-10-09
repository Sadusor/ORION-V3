"""Advisory-only code proposal round; no patch application."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "src"))
from live_two_cloud_architecture_demo import DONOR, choose_two, runtime_from_existing_source
from orion_v3.work_loop.multi_ai_existing_reviewer import _round

OBJECTIVE = ("Propose concrete Python standard-library source files for Task Tracker V1. "
             "SQLite CRUD, localhost HTTP API, unittest, temporary database. "
             "Allowed paths: tracker/db.py, tracker/model.py, tracker/api.py, "
             "tests/test_api.py, README.md. No execution or installation.")
def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(DONOR))
    from provider_vault import ProviderVault
    from reviewer_connector import ReviewerConnector
    runtime = runtime_from_existing_source()
    connector = ReviewerConnector(runtime / "coding-mode" / "reviewers",
                                  provider_vault=ProviderVault(runtime / "provider-vault"),
                                  configured_free_providers=[])
    selected = choose_two(connector.refresh_catalog())
    ids = tuple(m["reviewer_id"] for m in selected)
    prompt = "INDEPENDENT CODE PROPOSAL. Give file paths and implementation code, not an essay. Max 11000 characters. No execution.\n" + OBJECTIVE
    proposals = _round(connector, prompt, ids, stop_requested=lambda: False)
    frozen = "\n".join(name + ":\n" + body[:3500] for name, body in proposals)
    review = "CROSS-REVIEW BOTH CODE PROPOSALS. Find bugs, scope violations, missing tests and disagreements. No execution.\n" + OBJECTIVE + "\n" + frozen
    critiques = _round(connector, review, ids, stop_requested=lambda: False)
    payload = {"schema": "orion.v3.multi_ai.code_proposal.v1",
               "created_utc": datetime.now(timezone.utc).isoformat(),
               "authorization": "PROPOSAL_PHASE_ONLY",
               "execution": "NOT_PERFORMED",
               "prompt_sha256": sha(prompt), "review_prompt_sha256": sha(review),
               "proposals": [{"model_id": n, "text": b, "sha256": sha(b)} for n,b in proposals],
               "critiques": [{"model_id": n, "text": b, "sha256": sha(b)} for n,b in critiques]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print("ORION_CODE> TWO_PROPOSALS_TWO_CRITIQUES_SAVED", args.output, flush=True)
    print("ORION_CODE> NO_EXECUTION_NO_PATCH_APPLICATION", flush=True)

if __name__ == "__main__":
    main()
