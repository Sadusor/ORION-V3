"""Unified proposal-only cloud adapter. No automatic retries or execution."""

from .existing_reviewer_slot_adapter import ReviewerInvocationError
from .connector_collision_guard import invoke_collision_safe as invoke_existing
from .openrouter_text_adapter import (
    completion,
    CloudRequestError,
)


class DispatchError(Exception):
    def __init__(self, category, origin="UNKNOWN", line=0):
        self.category = category
        self.origin = origin
        self.line = line
        super().__init__(category)


def dispatch(
    *,
    provider,
    model,
    prompt,
    stop_requested,
    connector=None,
    reviewer_id=None,
    api_key=None,
    transport=None,
    timeout=45,
):
    if not callable(stop_requested):
        raise ValueError("STOP callback required")

    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Invalid prompt")

    if len(prompt) > 12000 or not 1 <= timeout <= 60:
        raise ValueError("Request exceeds limits")

    if stop_requested():
        raise DispatchError("STOPPED")

    if provider == "openrouter":
        if reviewer_id or connector is not None:
            raise DispatchError("WRONG_ADAPTER")

        try:
            result = completion(
                model=model,
                prompt=prompt,
                api_key=api_key,
                timeout=timeout,
                transport=transport,
            )
        except CloudRequestError as exc:
            raise DispatchError(exc.category) from None

        if stop_requested():
            raise DispatchError("STOPPED")

        return result

    if provider in ("groq", "gemini"):
        if (
            connector is None
            or not reviewer_id
            or api_key is not None
            or transport is not None
        ):
            raise DispatchError("WRONG_ADAPTER")

        try:
            output = invoke_existing(
                connector=connector,
                reviewer_id=reviewer_id,
                prompt=prompt,
                stop_requested=stop_requested,
                timeout=timeout,
            )
        except ReviewerInvocationError as exc:
            raise DispatchError(exc.category, getattr(exc, "origin", "UNKNOWN"), getattr(exc, "line", 0)) from None

        return {
            "provider": provider,
            "model": model,
            "text": output,
            "truncated": False,
        }

    raise DispatchError("UNSUPPORTED_PROVIDER")
