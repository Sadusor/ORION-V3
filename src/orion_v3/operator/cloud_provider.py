from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class CloudProviderSpec:
    provider_id: str
    model_id: str
    endpoint: str
    api_key_env: str


@dataclass(frozen=True)
class CloudProviderResponse:
    provider_id: str
    requested_model: str
    served_model: str | None
    response_text: str
    prompt_sha256: str
    response_sha256: str
    elapsed_seconds: float
    status: str
    reason: str
    external_message_id: str | None


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def call_openai_compatible_advisory(
    spec: CloudProviderSpec,
    prompt: str,
    *,
    env: Mapping[str, str] | None = None,
    timeout_seconds: float = 180.0,
) -> CloudProviderResponse:
    """One bounded advisory call with exact provider/model identity.

    This connector has no tools, Hands, task mutation or fallback authority.
    A transient 429/503 retry targets only the exact same provider/model.
    """
    env = os.environ if env is None else env
    prompt = str(prompt)
    if not prompt.strip():
        raise ValueError("prompt must be non-empty")

    key = str(env.get(spec.api_key_env, "")).strip()
    prompt_hash = _sha256_text(prompt)
    if not key:
        return CloudProviderResponse(
            provider_id=spec.provider_id,
            requested_model=spec.model_id,
            served_model=None,
            response_text="",
            prompt_sha256=prompt_hash,
            response_sha256=_sha256_text(""),
            elapsed_seconds=0.0,
            status="BLOCKED",
            reason="missing credential: " + spec.api_key_env,
            external_message_id=None,
        )

    body: dict[str, object] = {
        "model": spec.model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "stream": False,
        "max_tokens": 1200,
    }
    if spec.provider_id == "groq" and spec.model_id == "openai/gpt-oss-120b":
        body["reasoning_effort"] = "medium"
        body["include_reasoning"] = False

    request = urllib.request.Request(
        spec.endpoint,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ORION-V3-Cloud-Specialist/0.1",
        },
    )

    started = time.perf_counter()
    payload: dict[str, object] | None = None
    last_error: str | None = None

    for attempt, delay in enumerate((0.0, 1.0, 2.0), start=1):
        if delay:
            time.sleep(delay)
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                decoded = json.loads(response.read().decode("utf-8"))
                if not isinstance(decoded, dict):
                    raise RuntimeError("provider returned non-object JSON")
                payload = decoded
            break
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            last_error = f"HTTP {exc.code}: {detail}"
            if exc.code in {429, 503} and attempt < 3:
                continue
            status = "BLOCKED" if exc.code in {401, 403, 408, 409, 429, 503} else "FAIL"
            return CloudProviderResponse(
                provider_id=spec.provider_id,
                requested_model=spec.model_id,
                served_model=None,
                response_text="",
                prompt_sha256=prompt_hash,
                response_sha256=_sha256_text(""),
                elapsed_seconds=round(time.perf_counter() - started, 3),
                status=status,
                reason=last_error,
                external_message_id=None,
            )
        except Exception as exc:
            return CloudProviderResponse(
                provider_id=spec.provider_id,
                requested_model=spec.model_id,
                served_model=None,
                response_text="",
                prompt_sha256=prompt_hash,
                response_sha256=_sha256_text(""),
                elapsed_seconds=round(time.perf_counter() - started, 3),
                status="FAIL",
                reason=type(exc).__name__ + ": " + str(exc),
                external_message_id=None,
            )

    if payload is None:
        return CloudProviderResponse(
            provider_id=spec.provider_id,
            requested_model=spec.model_id,
            served_model=None,
            response_text="",
            prompt_sha256=prompt_hash,
            response_sha256=_sha256_text(""),
            elapsed_seconds=round(time.perf_counter() - started, 3),
            status="BLOCKED",
            reason=last_error or "provider unavailable",
            external_message_id=None,
        )

    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return CloudProviderResponse(
            provider_id=spec.provider_id,
            requested_model=spec.model_id,
            served_model=str(payload.get("model") or "") or None,
            response_text="",
            prompt_sha256=prompt_hash,
            response_sha256=_sha256_text(""),
            elapsed_seconds=round(time.perf_counter() - started, 3),
            status="FAIL",
            reason="provider response had no choices",
            external_message_id=str(payload.get("id") or "") or None,
        )

    first = choices[0] if isinstance(choices[0], dict) else {}
    message = first.get("message") if isinstance(first, dict) else None
    content = str(message.get("content") or "").strip() if isinstance(message, dict) else ""
    served = str(payload.get("model") or "").strip() or None
    external_id = str(payload.get("id") or "").strip() or None
    elapsed = round(time.perf_counter() - started, 3)

    if not content:
        return CloudProviderResponse(
            provider_id=spec.provider_id,
            requested_model=spec.model_id,
            served_model=served,
            response_text="",
            prompt_sha256=prompt_hash,
            response_sha256=_sha256_text(""),
            elapsed_seconds=elapsed,
            status="FAIL",
            reason="provider returned empty visible response",
            external_message_id=external_id,
        )
    if served != spec.model_id:
        return CloudProviderResponse(
            provider_id=spec.provider_id,
            requested_model=spec.model_id,
            served_model=served,
            response_text=content,
            prompt_sha256=prompt_hash,
            response_sha256=_sha256_text(content),
            elapsed_seconds=elapsed,
            status="FAIL",
            reason="served model did not exactly match requested model",
            external_message_id=external_id,
        )

    return CloudProviderResponse(
        provider_id=spec.provider_id,
        requested_model=spec.model_id,
        served_model=served,
        response_text=content,
        prompt_sha256=prompt_hash,
        response_sha256=_sha256_text(content),
        elapsed_seconds=elapsed,
        status="PASS",
        reason="exact advisory response captured",
        external_message_id=external_id,
    )


def groq_gptoss_120b_spec() -> CloudProviderSpec:
    return CloudProviderSpec(
        provider_id="groq",
        model_id="openai/gpt-oss-120b",
        endpoint="https://api.groq.com/openai/v1/chat/completions",
        api_key_env="GROQ_API_KEY",
    )
