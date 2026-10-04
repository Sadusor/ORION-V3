from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "v35_final_local_operator_tournament.py"


def load_run043_module():
    spec = importlib.util.spec_from_file_location("orion_run043_tournament", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load RUN-043 tournament module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    print("V3_RUN_ID> V3-RUN-044A")
    print("ORION_9B_THINKING_ON_QUALIFICATION> START")
    print("PURPOSE> one final 9B thinking-ON qualification before production attachment")
    print("COMMON_NUM_CTX> 4096")

    if not SOURCE.is_file():
        raise RuntimeError("RUN-043 tournament substrate missing")

    run043 = load_run043_module()
    candidate = {
        "label": "9B_ON",
        "model": "qwen35-9b-orion:latest",
        "reasoning_effort": "medium",
    }

    # Make the inherited cold-stop helper touch only this candidate.
    run043.CANDIDATES = [candidate]
    run043.NUM_CTX = 4096

    if not run043.OPENHANDS.is_dir() or not run043.RUNTIME.is_file():
        raise RuntimeError("required OpenHands/resilience substrate missing")

    ollama = run043.find_ollama()
    row = run043.run_candidate(candidate, ollama)

    print(
        "NINE_B_THINKING_ON_RESULT> "
        + json.dumps(row, ensure_ascii=False, sort_keys=True)
    )

    cases = row.get("case_results") or []
    for case in cases:
        print(
            "NINE_B_THINKING_ON_CASE> "
            + json.dumps(case, ensure_ascii=False, sort_keys=True)
        )

    benchmark_valid = bool(row.get("benchmark_valid"))
    qualified = bool(row.get("qualified"))

    summary = {
        "schema": "orion.v3.9b-thinking-on-qualification.v0",
        "run_id": "V3-RUN-044A",
        "candidate": "qwen35-9b-orion:latest",
        "reasoning_effort": "medium",
        "think_expected": True,
        "num_ctx": 4096,
        "benchmark_valid": benchmark_valid,
        "qualified": qualified,
        "cases_passed": row.get("cases_passed"),
        "cases_total": row.get("cases_total"),
        "wall_seconds": row.get("wall_seconds"),
        "total_actions": row.get("total_actions"),
        "peak_ram_delta_mb": row.get("peak_ram_delta_mb"),
        "peak_gpu_delta_mb": row.get("peak_gpu_delta_mb"),
        "runtime": row.get("runtime"),
        "comparison_note": (
            "RUN-043 proved no candidate reached 5/5. "
            "This single 9B-ON rerun checks whether thinking changes the hard-case result. "
            "Do not invent a RUN-043 9B-OFF wall-time value because its detailed row was not preserved."
        ),
    }
    print(
        "ORION_9B_THINKING_ON_SUMMARY> "
        + json.dumps(summary, ensure_ascii=False, sort_keys=True)
    )
    print(
        "NINE_B_THINKING_ON_QUALIFIED> "
        + ("PASS" if qualified else "FAIL")
    )

    # Gate validity is distinct from candidate qualification, matching RUN-043 semantics.
    if not benchmark_valid:
        print("ORION_9B_THINKING_ON_QUALIFICATION> FAIL")
        print("STATUS> FAIL")
        return 1

    print("ORION_9B_THINKING_ON_QUALIFICATION> COMPLETE")
    print("STATUS> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
