"""Groq-only artifact capture: no execution of model-produced code."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "src"))
from live_two_cloud_architecture_demo import DONOR, runtime_from_existing_source
from orion_v3.work_loop.unified_cloud_adapter import dispatch, DispatchError

TASK = ("Produce a Python source file named title_normalizer.py. "
        "Implement normalize_task_title(value: str) -> str: collapse whitespace, "
        "strip ends, raise ValueError for empty. Return only Python source, "
        "no markdown fences, imports, side effects, I/O or external dependencies. "
        "Advisory proposal only; do not execute.")

def digest(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def main():
    if not (DONOR / "reviewer_connector.py").is_file():
        print("GROQ_ARTIFACT> DONOR_MISSING", flush=True)
        return 2
    sys.path.insert(0, str(DONOR))
    from provider_vault import ProviderVault
    from reviewer_connector import ReviewerConnector
    runtime = runtime_from_existing_source()
    connector = ReviewerConnector(runtime / "coding-mode" / "reviewers",
        provider_vault=ProviderVault(runtime / "provider-vault"),
        configured_free_providers=[])
    catalog = connector.refresh_catalog()
    candidates = [m for m in catalog.get("models", [])
        if isinstance(m, dict) and m.get("available") is True
        and str(m.get("provider", "")).lower() == "groq"
        and m.get("reviewer_id")
        and "gpt-oss-120b" in str(m.get("model", "")).lower()]
    if not candidates:
        print("GROQ_ARTIFACT> NO_FREE_GROQ_MODEL_AVAILABLE", flush=True)
        return 2
    model = candidates[0]
    def ask(prompt):
        result = dispatch(provider="groq", model=str(model.get("model", "")),
            prompt=prompt, stop_requested=lambda: False,
            connector=connector, reviewer_id=model["reviewer_id"], timeout=45)
        answer = result.get("text", "")
        if not isinstance(answer, str) or not answer.strip() or len(answer) > 16000:
            raise ValueError("invalid proposal")
        return answer
    try:
        proposal = ask("CODER ROLE. " + TASK)
        review = ask("REVIEWER ROLE. Review this untrusted code for correctness, "
            "security, and missing tests. Do not execute.\n" + TASK +
            "\nPROPOSAL:\n" + proposal[:3500])
        import ast
        syntax_ok = True
        try:
            ast.parse(proposal)
        except SyntaxError:
            syntax_ok = False
        # A new exclusive file; never overwrite an existing artifact.
        output = Path("groq_artifact_trial_20261012.json")
        artifact = {"schema": "orion.groq.artifact_trial.v1",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "provider": "groq", "model": str(model.get("model", "")),
            "task": TASK, "proposal": proposal, "proposal_sha256": digest(proposal),
            "review": review, "review_sha256": digest(review),
            "python_syntax_ok": syntax_ok, "execution": "NOT_PERFORMED",
            "production_modified": False}
        with output.open("x", encoding="utf-8") as f:
            json.dump(artifact, f, indent=2, ensure_ascii=False)
        print("GROQ_ARTIFACT> PROPOSAL_SHA256", digest(proposal), flush=True)
        print("GROQ_ARTIFACT> REVIEW_SHA256", digest(review), flush=True)
        print("GROQ_ARTIFACT> SYNTAX_OK", syntax_ok, flush=True)
        print("GROQ_ARTIFACT> SAVED", output, flush=True)
        print("GROQ_ARTIFACT> NO_EXECUTION_NO_PRODUCTION_CHANGE PASS", flush=True)
        return 0 if syntax_ok else 2
    except Exception as exc:
        print("GROQ_ARTIFACT> FAILED", type(exc).__name__, flush=True)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
