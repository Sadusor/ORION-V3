"""Minimal OpenRouter text-only adapter, isolated from ORION authority and vault.

The caller supplies a credential at invocation time. Never log request headers.
No tools, code execution, automatic retries or implicit provider fallback.
"""
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
ALLOWED_HOST = "openrouter.ai"

class CloudRequestError(RuntimeError):
    def __init__(self, category, status=None):
        super().__init__(category)
        self.category, self.status = category, status

def classify_status(status):
    if status in (401, 403): return "AUTH"
    if status == 429: return "RATE_LIMIT"
    if status in (400, 404, 422): return "REQUEST"
    if status >= 500: return "PROVIDER"
    return "HTTP_ERROR"

def completion(*, model, prompt, api_key, timeout=45, transport=None):
    if not isinstance(model, str) or not model or len(model) > 200 or any(c.isspace() for c in model):
        raise ValueError("invalid model")
    # Fail closed: this adapter is exclusively for OpenRouter free-model IDs.
    # A free suffix is necessary, not proof of current quota or zero account spend.
    if not model.endswith(":free"):
        raise CloudRequestError("PAID_MODEL_BLOCKED")
    if not isinstance(prompt, str) or not prompt or len(prompt) > 24000:
        raise ValueError("invalid prompt")
    if not isinstance(api_key, str) or not api_key:
        raise CloudRequestError("NO_CREDENTIAL")
    if not 1 <= timeout <= 60:
        raise ValueError("invalid timeout")
    payload = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                          "stream": False, "max_tokens": 1200}).encode("utf-8")
    req = Request(ENDPOINT, data=payload, method="POST", headers={
        "Authorization": "Bearer " + api_key, "Content-Type": "application/json",
        "Accept": "application/json", "User-Agent": "ORION-V3-proposal-only"})
    send = transport or urlopen
    try:
        with send(req, timeout=timeout) as response:
            if response.status != 200:
                raise CloudRequestError(classify_status(response.status), response.status)
            raw = response.read(250001)
    except HTTPError as exc:
        raise CloudRequestError(classify_status(exc.code), exc.code) from None
    except (TimeoutError, URLError) as exc:
        raise CloudRequestError("TRANSPORT") from None
    if len(raw) > 250000:
        raise CloudRequestError("RESPONSE_TOO_LARGE")
    try:
        body = json.loads(raw.decode("utf-8"))
        choice = body["choices"][0]["message"]["content"]
        if not isinstance(choice, str) or not choice.strip():
            raise ValueError("empty")
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError):
        raise CloudRequestError("MALFORMED_RESPONSE") from None
    return {"provider": "openrouter", "model": model, "text": choice[:16000],
            "truncated": len(choice) > 16000}
