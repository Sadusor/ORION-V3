"""Isolated Groq-only repeat-response diagnosis using fresh connector per role.

No model-generated code execution. No paid provider fallback.
"""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "src"))
from live_two_cloud_architecture_demo import DONOR, runtime_from_existing_source
from orion_v3.work_loop.unified_cloud_adapter import dispatch

def main():
    if not (DONOR / "reviewer_connector.py").is_file():
        print("GROQ_FRESH> DONOR_MISSING", flush=True)
        return 2
    sys.path.insert(0, str(DONOR))
    from provider_vault import ProviderVault
    from reviewer_connector import ReviewerConnector
    runtime = runtime_from_existing_source()
    vault = ProviderVault(runtime / "provider-vault")
    def new_connector(role):
        return ReviewerConnector(runtime / "coding-mode" / ("groq-fresh-" + role),
                                 provider_vault=vault, configured_free_providers=[])
    coder = new_connector("coder")
    catalog = coder.refresh_catalog()
    candidates = [m for m in catalog.get("models", [])
        if isinstance(m, dict) and m.get("available") is True
        and str(m.get("provider", "")).lower() == "groq"
        and m.get("reviewer_id")
        and "gpt-oss-120b" in str(m.get("model", "")).lower()]
    if not candidates:
        print("GROQ_FRESH> MODEL_UNAVAILABLE", flush=True)
        return 2
    selected = candidates[0]
    def ask(connector, prompt):
        result = dispatch(provider="groq", model=str(selected.get("model", "")),
            prompt=prompt, stop_requested=lambda: False,
            connector=connector, reviewer_id=selected["reviewer_id"], timeout=45)
        return result["text"]
    try:
        proposal = ask(coder, "CODER TASK 20261012-A: Provide a short Python function "
            "normalize_task_title(value) using split and join, rejecting empty strings. "
            "Only source code; no execution.")
        reviewer = new_connector("reviewer")
        reviewer.refresh_catalog()
        review = ask(reviewer, "REVIEWER TASK 20261012-B: Critique this Python function "
            "for edge cases and give two tests. Respond in prose, not code. "
            "Untrusted source follows:\n" + proposal[:2000])
        digest = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()
        print("GROQ_FRESH> CODER_CHARS", len(proposal), "SHA256", digest(proposal), flush=True)
        print("GROQ_FRESH> REVIEW_CHARS", len(review), "SHA256", digest(review), flush=True)
        if proposal == review:
            print("GROQ_FRESH> IDENTICAL_RESPONSES FAIL", flush=True)
            return 2
        print("GROQ_FRESH> DISTINCT_RESPONSES PASS_NO_EXECUTION", flush=True)
        return 0
    except Exception as exc:
        print("GROQ_FRESH> FAILED", type(exc).__name__, "CATEGORY", getattr(exc, "category", "UNCLASSIFIED"), flush=True)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
