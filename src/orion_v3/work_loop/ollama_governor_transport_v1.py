"""Opt-in local Ollama council transport. No cloud API calls or execution."""
from __future__ import annotations
import json
import urllib.request
from urllib.parse import urlparse
from .budgeted_council_router_v1 import ModelResponse, Usage
from .role_contracts_v1 import Role

def ollama_governor_transport(route, system: str, question: str, *,
                              base_url: str = "http://127.0.0.1:11434",
                              timeout: float = 90.0) -> ModelResponse:
    if route.role != Role.GOVERNOR or route.provider != "ollama":
        raise ValueError("local adapter supports only governor role")
    parsed = urlparse(base_url)
    if (parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1", "::1")
        or parsed.username or parsed.password or parsed.query or parsed.fragment
        or parsed.path not in ("", "/")):
        raise ValueError("Ollama must use a loopback endpoint")
    if not 1 <= timeout <= 120:
        raise ValueError("invalid timeout")
    body = json.dumps({"model": route.model, "stream": False,
                       "messages": [{"role": "system", "content": system},
                                    {"role": "user", "content": question}],
                       "options": {"num_predict": route.max_output_tokens, "temperature": 0}
                      }).encode("utf-8")
    request = urllib.request.Request(base_url.rstrip("/") + "/api/chat", data=body,
                                     headers={"Content-Type": "application/json"}, method="POST")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=timeout) as response:
        payload = json.loads(response.read(262144).decode("utf-8"))
    if not isinstance(payload, dict) or payload.get("done") is not True:
        raise ValueError("incomplete Ollama response")
    message = payload.get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        raise ValueError("invalid Ollama message")
    prompt_tokens = payload.get("prompt_eval_count", 0)
    output_tokens = payload.get("eval_count", 0)
    if type(prompt_tokens) is not int or type(output_tokens) is not int:
        raise ValueError("invalid Ollama usage")
    return ModelResponse(message["content"], Usage(prompt_tokens, output_tokens, 0.0))
