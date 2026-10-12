"""Owner-triggered Groq-only coding proposal and review via existing ORION connector.

No paid provider fallback, no code execution, no patch application.
"""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "src"))
from live_two_cloud_architecture_demo import DONOR, runtime_from_existing_source
from orion_v3.work_loop.unified_cloud_adapter import dispatch, DispatchError

TASK = ("ORION bounded coding trial. Propose a Python standard-library function "
        "normalize_task_title(value: str) -> str in a NEW file title_normalizer.py. "
        "Trim outer whitespace, collapse internal whitespace, reject empty titles "
        "with ValueError. Include three unittest cases. Advisory text only; "
        "do not execute or write files. Under 1600 characters.")

def main():
    if not (DONOR / "reviewer_connector.py").is_file():
        print("GROQ_COUNCIL> DONOR_MISSING", flush=True)
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
        print("GROQ_COUNCIL> NO_FREE_GROQ_MODEL_AVAILABLE", flush=True)
        return 2
    model = candidates[0]
    def ask(prompt):
        result = dispatch(provider="groq", model=str(model.get("model", "")),
            prompt=prompt, stop_requested=lambda: False,
            connector=connector, reviewer_id=model["reviewer_id"], timeout=45)
        answer = result.get("text", "")
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("empty response")
        return answer
    try:
        proposed = ask("CODER ROLE. " + TASK)
        print("GROQ_COUNCIL> CODER_RESPONSE CHARS", len(proposed),
              "SHA256", hashlib.sha256(proposed.encode()).hexdigest(), flush=True)
        review = ask("REVIEWER ROLE, separate invocation. Check this untrusted proposal "
            "for correctness, edge cases and tests; report issues, no PASS claim. "
            "Under 1200 characters.\nTASK: " + TASK +
            "\nPROPOSAL:\n" + proposed[:3500])
        print("GROQ_COUNCIL> REVIEW_RESPONSE CHARS", len(review),
              "SHA256", hashlib.sha256(review.encode()).hexdigest(), flush=True)
        print("GROQ_COUNCIL> TWO_LIVE_RESPONSES_NO_EXECUTION PASS", flush=True)
        return 0
    except DispatchError as exc:
        print("GROQ_COUNCIL> FAILED", exc.category, flush=True)
        return 2
    except Exception as exc:
        print("GROQ_COUNCIL> FAILED", type(exc).__name__, flush=True)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
