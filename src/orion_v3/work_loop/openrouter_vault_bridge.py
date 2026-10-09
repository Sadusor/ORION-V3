"""Vault-backed OpenRouter proposal invocation.

The vault is injected; this module never stores credentials and never imports
the donor vault itself. Caller controls model, task, STOP and owner approval.
"""
from .openrouter_text_adapter import completion, CloudRequestError

def request_openrouter(*, vault, provider_id, model, prompt, stop_requested,
                       transport=None):
    if stop_requested():
        raise CloudRequestError("STOPPED")
    entry = vault.get(provider_id)
    if not isinstance(entry, dict):
        raise CloudRequestError("PROVIDER_NOT_REGISTERED")
    adapter = str(entry.get("adapter") or "").strip().lower()
    if adapter != "openrouter":
        raise CloudRequestError("WRONG_ADAPTER")
    if entry.get("enabled") is not True:
        raise CloudRequestError("PROVIDER_DISABLED")
    key = vault.get_secret(provider_id)
    if stop_requested():
        raise CloudRequestError("STOPPED")
    return completion(model=model, prompt=prompt, api_key=key, transport=transport)
