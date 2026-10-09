
"""ORION V3 — four independent cloud AI roles, proposal-only.

OpenRouter verified-free models first, existing Groq/Gemini connector fallback.
No generated code execution, no automatic owner approval, no secrets in logs.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from orion_v3.work_loop.cloud_family_selection import family
from orion_v3.work_loop.unified_cloud_adapter import dispatch, DispatchError

SLOTS = ("author_a", "author_b", "reviewer_a", "reviewer_b")

TASK = (
    "Design a tiny offline Python standard-library SQLite task tracker "
    "with localhost HTTP CRUD, deterministic unittest tests, "
    "and no external dependencies."
)

MAX_TOTAL_ATTEMPTS = 12


def free_openrouter_candidates():
    request = Request(
        "https://openrouter.ai/api/v1/models",
        headers={
            "Accept": "application/json",
            "User-Agent": "ORION-V3-four-slot",
        },
    )

    with urlopen(request, timeout=20) as response:
        raw = response.read(15_000_001)

    if len(raw) > 15_000_000:
        raise ValueError("Catalog too large")

    payload = json.loads(raw.decode("utf-8"))
    candidates = []

    for item in payload.get("data", []):
        if not isinstance(item, dict):
            continue

        model = item.get("id", "")
        pricing = item.get("pricing") or {}

        if not isinstance(model, str) or not model.endswith(":free"):
            continue
        if not isinstance(pricing, dict):
            continue

        if str(pricing.get("prompt", "")) not in ("0", "0.0", "0.000000"):
            continue
        if str(pricing.get("completion", "")) not in ("0", "0.0", "0.000000"):
            continue

        if any(word in model.lower() for word in (
            "image", "audio", "vision", "guard", "embed"
        )):
            continue

        model_family = family(model)
        if model_family == "unknown":
            continue

        candidates.append({
            "provider": "openrouter",
            "model": model,
            "family": model_family,
            "reviewer_id": None,
        })

    priority = {
        "qwen": 0,
        "deepseek": 1,
        "mistral": 2,
        "gemma": 3,
        "nemotron": 4,
        "llama": 5,
    }

    candidates.sort(
        key=lambda c: (
            priority.get(c["family"], 10),
            c["model"],
        )
    )

    return candidates


def existing_connector_candidates():
    """Load existing private provider adapter without duplicating keys."""
    donor = Path("E:/ORION/spikes/coding_mode_github_loop")

    if not (donor / "reviewer_connector.py").is_file():
        return [], None

    sys.path.insert(0, str(donor))

    from provider_vault import ProviderVault
    from reviewer_connector import ReviewerConnector

    runtime = Path(os.environ.get(
        "LOCALAPPDATA",
        str(Path.home() / "AppData/Local"),
    )) / "Orion"

    connector = ReviewerConnector(
        runtime / "coding-mode" / "reviewers",
        provider_vault=ProviderVault(runtime / "provider-vault"),
        configured_free_providers=[],
    )

    candidates = []

    for item in connector.refresh_catalog().get("models", []):
        if not isinstance(item, dict):
            continue
        if item.get("available") is not True:
            continue

        provider = str(item.get("provider") or "").lower()
        model = str(item.get("model") or "")
        reviewer_id = item.get("reviewer_id")

        if provider not in ("groq", "gemini") or not reviewer_id:
            continue

        if any(word in model.lower() for word in (
            "preview", "audio", "tts", "image",
            "whisper", "guard", "speech", "transcribe"
        )):
            continue

        model_family = family(model)
        if model_family == "unknown":
            continue

        candidates.append({
            "provider": provider,
            "model": model,
            "family": model_family,
            "reviewer_id": reviewer_id,
        })

    candidates.sort(
        key=lambda c: (
            0 if c["family"] == "gpt-oss" else 1,
            c["model"],
        )
    )

    return candidates, connector


def make_prompt(slot, completed):
    if slot.startswith("author"):
        return (
            "Independently propose a concise architecture, modules, "
            "acceptance tests and failure cases. "
            "Do not execute code or approve changes.\n"
            + TASK
        )

    authors = "\n".join(
        name + ": " + completed[name]["text"][:1500]
        for name in ("author_a", "author_b")
    )

    return (
        "Independently critique BOTH author proposals. "
        "Identify concrete bugs, security issues, missing tests "
        "and disagreements. Do not approve or execute code.\n"
        + TASK + "\n" + authors
    )


def main():
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()

    if not key:
        print("COUNCIL> OPENROUTER_KEY_MISSING", flush=True)
        return 2

    try:
        free = free_openrouter_candidates()
    except Exception as exc:
        print("COUNCIL> CATALOG_ERROR", type(exc).__name__, flush=True)
        return 2

    print("COUNCIL> FREE_CANDIDATES", len(free), flush=True)

    try:
        private, connector = existing_connector_candidates()
    except Exception as exc:
        print("COUNCIL> PRIVATE_CATALOG_ERROR", type(exc).__name__, flush=True)
        private, connector = [], None

    candidates = free + private

    used_families = set()
    attempted = set()
    completed = {}
    provider_failures = {}
    blocked_providers = set()

    for slot in SLOTS:
        prompt = make_prompt(slot, completed)
        success = False

        for candidate in candidates:
            if len(attempted) >= MAX_TOTAL_ATTEMPTS:
                break

            provider = candidate["provider"]
            model = candidate["model"]
            model_family = candidate["family"]
            identity = (provider, model)

            if (model_family in used_families or identity in attempted
                    or provider in blocked_providers):
                continue

            attempted.add(identity)

            print(
                "COUNCIL> ATTEMPT",
                slot, provider, model,
                flush=True,
            )

            try:
                if provider == "openrouter":
                    kwargs = {"api_key": key}
                else:
                    kwargs = {
                        "connector": connector,
                        "reviewer_id": candidate["reviewer_id"],
                    }

                result = dispatch(
                    provider=provider,
                    model=model,
                    prompt=prompt[:12000],
                    stop_requested=lambda: False,
                    timeout=40,
                    **kwargs,
                )

                output = str(result.get("text") or "").strip()

                if not output:
                    raise DispatchError("MALFORMED_RESPONSE")

                completed[slot] = {
                    "provider": provider,
                    "model": model,
                    "family": model_family,
                    "text": output,
                }

                used_families.add(model_family)
                success = True

                print(
                    "COUNCIL> PASS",
                    slot, provider, model_family,
                    "CHARS", len(output),
                    "SHA256",
                    hashlib.sha256(output.encode()).hexdigest(),
                    flush=True,
                )
                break

            except DispatchError as exc:
                provider_failures[provider] = provider_failures.get(provider, 0) + 1
                if exc.category in ("AUTH", "NO_CREDENTIAL", "WRONG_ADAPTER") or provider_failures[provider] >= 2:
                    blocked_providers.add(provider)
                print(
                    "COUNCIL> FAILURE",
                    slot, provider, model_family,
                    exc.category,
                    flush=True,
                )

            except Exception as exc:
                blocked_providers.add(provider)
                print(
                    "COUNCIL> FAILURE_CLASS",
                    slot, provider,
                    type(exc).__name__,
                    flush=True,
                )

        if not success:
            print(
                "COUNCIL> BLOCKED",
                slot,
                "COMPLETED",
                len(completed),
                flush=True,
            )
            return 2

    print(
        "COUNCIL> FOUR_DISTINCT_FAMILIES_PASS",
        ",".join(completed[s]["family"] for s in SLOTS),
        flush=True,
    )

    print(
        "COUNCIL> OWNER_APPROVAL_NOT_GRANTED NO_EXECUTION",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
