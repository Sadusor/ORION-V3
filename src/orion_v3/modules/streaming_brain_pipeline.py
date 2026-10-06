from __future__ import annotations

from .brain_pipeline import BrainPipeline
from .streaming_local_brain import StreamingLocalBrainModule
from .verifier_preflight import VerifierPreflightModule


class StreamingBrainPipeline(BrainPipeline):
    """BrainPipeline using the streaming Local Brain adapter."""

    def __init__(
        self,
        local_brain: StreamingLocalBrainModule | None = None,
        verifier: VerifierPreflightModule | None = None,
    ):
        super().__init__(
            local_brain=local_brain or StreamingLocalBrainModule(),
            verifier=verifier or VerifierPreflightModule(),
        )
