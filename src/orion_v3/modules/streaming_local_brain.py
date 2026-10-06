from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from .local_brain import LocalBrainError, LocalBrainModule


class StreamingLocalBrainModule(LocalBrainModule):
    """Streaming Local Brain adapter.

    Extends the frozen LocalBrainModule model-selection/state contract, but
    streams plain advisory text into brain_stream_preview while the model runs.
    It owns no execution authority.
    """

    def _worker(self, goal: str, model: str) -> None:
        prompt = (
            "You are ORION's bounded local reasoning brain.\n"
            "You are NOT an autonomous agent. You have no tools and cannot execute anything.\n"
            "The selected local model for this turn is: "
            + model
            + ".\n"
            "If asked what model you are, say that exact model name and that it is running locally inside ORION. "
            "Do not invent a trainer, vendor, provider, or different model identity.\n"
            "Do not claim that you opened, changed, checked, searched, ran, sent, or verified anything.\n"
            "Answer the owner's request directly in natural language.\n"
            "Do not add a 'Draft:' section unless the owner explicitly asks for a plan or draft.\n"
            "Do not produce executable PowerShell, shell commands, or tool calls.\n"
            "Do not invent access to files, memory, browsers, devices, cloud services, or current external facts.\n"
            "If the request requires unavailable evidence, say what evidence would be needed.\n\n"
            "OWNER REQUEST:\n"
            + goal
        )

        body = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "think": False,
            "keep_alive": "5m",
            "options": {
                "temperature": 0,
                "num_predict": 900,
            },
        }

        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + "/api/generate",
            data=data,
            headers={
                "Accept": "application/x-ndjson",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        started = time.perf_counter()
        chunks: list[str] = []

        try:
            with self._opener.open(req, timeout=120.0) as response:
                while True:
                    raw = response.readline()
                    if not raw:
                        break

                    try:
                        payload = json.loads(raw.decode("utf-8"))
                    except json.JSONDecodeError as exc:
                        raise LocalBrainError(
                            "Local Brain stream returned malformed JSON."
                        ) from exc

                    if not isinstance(payload, dict):
                        raise LocalBrainError(
                            "Local Brain stream returned an invalid event."
                        )

                    piece = str(payload.get("response") or "")
                    if piece:
                        chunks.append(piece)
                        preview = "".join(chunks)
                        with self._lock:
                            self._state.update(
                                {
                                    "brain_stream_preview": preview,
                                    "activity": "Local Brain streaming live · unverified · nothing executed",
                                }
                            )

                    if payload.get("done") is True:
                        break

            combined = "".join(chunks).strip()
            if not combined:
                raise LocalBrainError("Local Brain returned no usable text.")

            with self._lock:
                self._state.update(
                    {
                        "brain_state": "ready",
                        "brain_phase": "complete",
                        "brain_stream_preview": combined,
                        "brain_conclusion": combined,
                        "brain_error": "",
                        "brain_latency_seconds": round(
                            time.perf_counter() - started, 3
                        ),
                        "activity": "Local Brain response ready · awaiting verification · nothing executed",
                    }
                )
        except urllib.error.URLError as exc:
            message = "Local Ollama is not reachable."
            with self._lock:
                self._state.update(
                    {
                        "brain_state": "error",
                        "brain_phase": "error",
                        "brain_error": message,
                        "brain_conclusion": "",
                        "brain_latency_seconds": round(
                            time.perf_counter() - started, 3
                        ),
                        "activity": "Local Brain failed · nothing executed",
                    }
                )
        except Exception as exc:
            message = str(exc).strip() or exc.__class__.__name__
            with self._lock:
                self._state.update(
                    {
                        "brain_state": "error",
                        "brain_phase": "error",
                        "brain_error": message,
                        "brain_conclusion": "",
                        "brain_latency_seconds": round(
                            time.perf_counter() - started, 3
                        ),
                        "activity": "Local Brain failed · nothing executed",
                    }
                )
