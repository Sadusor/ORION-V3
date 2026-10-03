from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "v32_qwen_canonicalization_isolation_benchmark.py"

spec = importlib.util.spec_from_file_location("orion_v3_run_013_base", SOURCE)
if spec is None or spec.loader is None:
    raise SystemExit("Could not load frozen V3-RUN-013 benchmark.")

benchmark = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = benchmark
spec.loader.exec_module(benchmark)

from openjarvis.agents._stubs import AgentContext, AgentResult
from openjarvis.agents.simple import SimpleAgent as DonorSimpleAgent
from openjarvis.engine._stubs import ResponseFormat


class StructuredSimpleAgent(DonorSimpleAgent):
    """Same one-turn donor agent, but use Ollama's native JSON mode."""

    def run(
        self,
        input: str,
        context: AgentContext | None = None,
        **kwargs: Any,
    ) -> AgentResult:
        self._emit_turn_start(input)
        messages = self._build_messages(input, context)
        result = self._generate(
            messages,
            response_format=ResponseFormat(type="json_object"),
        )
        content = result.get("content", "")
        self._emit_turn_end(content_length=len(content))
        return AgentResult(content=content, turns=1)


benchmark.SimpleAgent = StructuredSimpleAgent

original_print = print


def run014_print(*args: Any, **kwargs: Any) -> None:
    if args and isinstance(args[0], str):
        args = (
            args[0]
            .replace("V3-RUN-013", "V3-RUN-014")
            .replace(
                "CANONICALIZATION_ISOLATION_BENCHMARK",
                "STRUCTURED_CANONICALIZATION_BENCHMARK",
            ),
            *args[1:],
        )
    original_print(*args, **kwargs)


benchmark.print = run014_print

raise SystemExit(benchmark.main())
