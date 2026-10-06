from __future__ import annotations

import copy
import threading
import time

from .local_brain import LocalBrainModule
from .verifier_preflight import VerifierError, VerifierPreflightModule


class BrainPipeline:
    """Compose the frozen Local Brain with a bounded verifier/preflight module."""

    def __init__(
        self,
        local_brain: LocalBrainModule | None = None,
        verifier: VerifierPreflightModule | None = None,
    ):
        self.local_brain = local_brain or LocalBrainModule()
        self.verifier = verifier or VerifierPreflightModule()
        self._lock = threading.RLock()
        self._verification = self._blank_verification()

    @staticmethod
    def _blank_verification() -> dict:
        return {
            "brain_started_utc": "",
            "state": "idle",
            "preflight": "not-run",
            "preflight_reason": "",
            "quality_state": "not-run",
            "quality_reason": "",
            "unsupported_claims": [],
            "missing_evidence": [],
            "needs_escalation": False,
            "error": "",
        }

    def cached_models(self) -> list[str]:
        return self.local_brain.cached_models()

    def default_model(self) -> str:
        return self.local_brain.default_model()

    def start(self, goal: str, model: str = "") -> dict:
        started = self.local_brain.start(goal, model)
        stamp = str(started.get("brain_started_utc") or "")

        with self._lock:
            self._verification = self._blank_verification()
            self._verification.update({
                "brain_started_utc": stamp,
                "state": "waiting",
            })

        threading.Thread(
            target=self._verify_when_ready,
            args=(stamp,),
            daemon=True,
            name="orion-v3-reply-verifier",
        ).start()

        return self.view()

    def view(self) -> dict:
        base = self.local_brain.view()
        with self._lock:
            check = copy.deepcopy(self._verification)

        stamp = str(base.get("brain_started_utc") or "")
        if not stamp or stamp != check.get("brain_started_utc"):
            return base

        base["brain_preflight"] = check["preflight"]
        base["brain_preflight_reason"] = check["preflight_reason"]
        base["brain_quality_state"] = check["quality_state"]
        base["brain_quality_reason"] = check["quality_reason"]
        base["brain_quality_unsupported_claims"] = check["unsupported_claims"]
        base["brain_quality_missing_evidence"] = check["missing_evidence"]
        base["brain_needs_escalation"] = check["needs_escalation"]

        if base.get("brain_state") == "ready" and check["state"] in {"waiting", "running"}:
            base["brain_state"] = "running"
            base["brain_phase"] = "verifying"
            base["activity"] = "Local Brain reply ready · verifier checking honesty and evidence"
            base["brain_conclusion"] = ""

        if check["state"] == "blocked":
            base["brain_state"] = "blocked"
            base["brain_phase"] = "blocked"
            base["brain_error"] = (
                check["preflight_reason"]
                or check["quality_reason"]
                or "Reply blocked by verifier."
            )
            base["activity"] = "Reply blocked by ORION verifier · nothing executed"

        if check["state"] == "error":
            base["brain_state"] = "blocked"
            base["brain_phase"] = "blocked"
            base["brain_quality_state"] = "error"
            base["brain_error"] = check["error"] or "Verifier failed closed."
            base["activity"] = "Verifier failed closed · reply not released"

        if check["state"] == "pass":
            base["brain_state"] = "ready"
            base["brain_phase"] = "complete"
            base["activity"] = "Local Brain reply verified · reasoning only · nothing executed"

        return base

    def _verify_when_ready(self, stamp: str) -> None:
        while True:
            current = self.local_brain.view()
            if str(current.get("brain_started_utc") or "") != stamp:
                return

            state = str(current.get("brain_state") or "")
            if state == "running":
                time.sleep(0.05)
                continue

            if state != "ready":
                return
            break

        goal = str(current.get("goal") or "")
        reply = str(current.get("brain_conclusion") or "")
        model = str(current.get("brain_model") or "")

        with self._lock:
            if self._verification.get("brain_started_utc") != stamp:
                return
            self._verification["state"] = "running"
            self._verification["preflight"] = "running"
            self._verification["quality_state"] = "not-run"

        try:
            result = self.verifier.verify(goal, reply, model)

            with self._lock:
                if self._verification.get("brain_started_utc") != stamp:
                    return
                self._verification.update({
                    "preflight": result["preflight"],
                    "preflight_reason": result["preflight_reason"],
                    "quality_state": result["quality_state"],
                    "quality_reason": result["quality_reason"],
                    "unsupported_claims": list(result["unsupported_claims"]),
                    "missing_evidence": list(result["missing_evidence"]),
                    "needs_escalation": bool(result["needs_escalation"]),
                    "state": (
                        "pass"
                        if result["preflight"] == "pass"
                        and result["quality_state"] == "pass"
                        else "blocked"
                    ),
                })
        except VerifierError as exc:
            with self._lock:
                if self._verification.get("brain_started_utc") != stamp:
                    return
                self._verification.update({
                    "state": "error",
                    "preflight": (
                        self._verification["preflight"]
                        if self._verification["preflight"] != "running"
                        else "pass"
                    ),
                    "quality_state": "error",
                    "error": str(exc),
                })
        except Exception as exc:
            with self._lock:
                if self._verification.get("brain_started_utc") != stamp:
                    return
                self._verification.update({
                    "state": "error",
                    "quality_state": "error",
                    "error": str(exc),
                })
