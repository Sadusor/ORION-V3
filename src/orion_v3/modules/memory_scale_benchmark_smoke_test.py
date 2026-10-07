from __future__ import annotations

import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCRIPT = ROOT / "tools" / "bench" / "memory_scale_benchmark.py"


def main() -> int:
    if not SCRIPT.is_file():
        raise SystemExit("Memory scale benchmark harness is missing.")
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--smoke"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)

    output = completed.stdout
    assert "ORION_MEMORY_SCALE_BENCH_SMOKE> PASS" in output
    assert '"production_runtime_loaded": false' in output
    assert '"frozen_memory_v1_modified": false' in output
    print("MEMORY_SCALE_BENCHMARK_HARNESS_GATE> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
