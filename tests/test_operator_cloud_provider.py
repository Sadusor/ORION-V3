from __future__ import annotations

import json
from types import SimpleNamespace

from orion_v3.operator import (
    CloudProviderSpec,
    call_openai_compatible_advisory,
)


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_missing_cloud_credential_is_blocked_without_network(monkeypatch):
    called = False

    def fail_urlopen(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("network must not be called")

    monkeypatch.setattr("urllib.request.urlopen", fail_urlopen)

    spec = CloudProviderSpec(
        provider_id="groq",
        model_id="openai/gpt-oss-120b",
        endpoint="https://example.invalid/chat",
        api_key_env="GROQ_API_KEY",
    )
    result = call_openai_compatible_advisory(
        spec,
        "review this",
        env={},
    )

    assert result.status == "BLOCKED"
    assert result.reason == "missing credential: GROQ_API_KEY"
    assert called is False


def test_exact_provider_model_response_passes(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse(
            {
                "id": "provider-message-1",
                "model": "openai/gpt-oss-120b",
                "choices": [
                    {
                        "message": {
                            "content": "Bounded advisory response."
                        }
                    }
                ],
            }
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    spec = CloudProviderSpec(
        provider_id="groq",
        model_id="openai/gpt-oss-120b",
        endpoint="https://api.groq.com/openai/v1/chat/completions",
        api_key_env="GROQ_API_KEY",
    )
    result = call_openai_compatible_advisory(
        spec,
        "review this exact request",
        env={"GROQ_API_KEY": "secret-test-key"},
    )

    assert result.status == "PASS"
    assert result.served_model == spec.model_id
    assert result.response_text == "Bounded advisory response."
    assert result.external_message_id == "provider-message-1"

    body = json.loads(captured["request"].data.decode("utf-8"))
    assert body["model"] == "openai/gpt-oss-120b"
    assert body["stream"] is False
    assert body["max_tokens"] == 700
    assert body["reasoning_effort"] == "medium"
    assert body["include_reasoning"] is False
    assert "tools" not in body


def test_served_model_substitution_fails_closed(monkeypatch):
    def fake_urlopen(request, timeout):
        return FakeResponse(
            {
                "id": "provider-message-2",
                "model": "different/model",
                "choices": [
                    {
                        "message": {
                            "content": "Answer from wrong model."
                        }
                    }
                ],
            }
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    spec = CloudProviderSpec(
        provider_id="groq",
        model_id="openai/gpt-oss-120b",
        endpoint="https://api.groq.com/openai/v1/chat/completions",
        api_key_env="GROQ_API_KEY",
    )
    result = call_openai_compatible_advisory(
        spec,
        "review this",
        env={"GROQ_API_KEY": "secret-test-key"},
    )

    assert result.status == "FAIL"
    assert result.served_model == "different/model"
    assert result.reason == "served model did not exactly match requested model"
