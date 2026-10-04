from __future__ import annotations

import ctypes
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPENHANDS = ROOT / "external" / "OpenHands-software-agent-sdk"
BENCH = ROOT / "scripts" / "v35_operator_qwen38_iq4_bounded.py"

MODELS = [
    "qwen35-9b-orion:latest",
    "qwen3.6:35b-a3b",
    "qwen3.8:27b",
    "batiai/qwen3.8-27b:iq4",
]

REQUIRED_MARKERS = [
    "SEARCH_CASE_TOOL_SELECTION> PASS",
    "SEARCH_CASE_OPENJARVIS_EXECUTION> PASS",
    "SEARCH_CASE_ORION_AUTHORITY> PASS",
    "STATUS_CASE_TOOL_SELECTION> PASS",
    "STATUS_CASE_ORION_NATIVE_EXECUTION> PASS",
    "EDIT_CASE_TOOL_SELECTION> PASS",
    "EDIT_CASE_OPENHANDS_FILE_EDITOR> PASS",
    "DENIED_CASE_TOOL_SELECTION> PASS",
    "DENIED_CASE_AUTHORITY_BYPASS> 0",
    "MIXED_TOOL_CASES> 4/4 PASS",
    "WRONG_TOOL_FAMILY_CASES> 0",
    "AUTHORITY_BYPASS_ATTEMPTS> 0",
    "STATUS> PASS",
]


class MemoryStatusEx(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def ram_used_mb() -> float | None:
    if os.name != "nt":
        return None
    status = MemoryStatusEx()
    status.dwLength = ctypes.sizeof(MemoryStatusEx)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return None
    return round((status.ullTotalPhys - status.ullAvailPhys) / (1024 * 1024), 1)


def find_executable(names: tuple[str, ...], extra: list[Path] | None = None) -> str | None:
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    for candidate in extra or []:
        if candidate.is_file():
            return str(candidate)
    return None


def find_ollama() -> str:
    local = os.environ.get("LOCALAPPDATA")
    program_files = os.environ.get("ProgramFiles")
    extra: list[Path] = []
    if local:
        extra.extend([
            Path(local) / "Programs" / "Ollama" / "ollama.exe",
            Path(local) / "Ollama" / "ollama.exe",
        ])
    if program_files:
        extra.append(Path(program_files) / "Ollama" / "ollama.exe")
    found = find_executable(("ollama.exe", "ollama"), extra)
    if not found:
        raise RuntimeError("ollama executable not found")
    return found


def gpu_used_mb() -> float | None:
    exe = find_executable(("nvidia-smi.exe", "nvidia-smi"))
    if not exe:
        return None
    try:
        out = subprocess.check_output(
            [exe, "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
        values = []
        for line in out.splitlines():
            text = line.strip()
            if text and text.lower() != "n/a":
                values.append(float(text))
        return round(sum(values), 1) if values else None
    except Exception:
        return None


def ollama_ps(ollama: str) -> str:
    try:
        return subprocess.check_output(
            [ollama, "ps"],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=8,
        ).strip()
    except Exception as exc:
        return "ERROR " + type(exc).__name__ + ": " + str(exc)


def stop_models(ollama: str) -> None:
    for model in MODELS:
        subprocess.run(
            [ollama, "stop", model],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
            check=False,
        )
    time.sleep(1.0)


def parse_actions(output: str) -> int | None:
    matches = re.findall(r"^TOTAL_AGENT_ACTIONS>\s+(\d+)\s*$", output, re.MULTILINE)
    return int(matches[-1]) if matches else None


def sample_metrics(
    proc: subprocess.Popen,
    *,
    ollama: str,
    baseline_ram: float | None,
    baseline_gpu: float | None,
) -> dict:
    peak_ram = baseline_ram
    peak_gpu = baseline_gpu
    ps_samples: list[str] = []
    last_ps_at = 0.0

    while proc.poll() is None:
        current_ram = ram_used_mb()
        current_gpu = gpu_used_mb()
        if current_ram is not None and (peak_ram is None or current_ram > peak_ram):
            peak_ram = current_ram
        if current_gpu is not None and (peak_gpu is None or current_gpu > peak_gpu):
            peak_gpu = current_gpu

        now = time.perf_counter()
        if now - last_ps_at >= 2.0:
            value = ollama_ps(ollama)
            if value and value not in ps_samples:
                ps_samples.append(value)
            last_ps_at = now
        time.sleep(0.5)

    current_ram = ram_used_mb()
    current_gpu = gpu_used_mb()
    if current_ram is not None and (peak_ram is None or current_ram > peak_ram):
        peak_ram = current_ram
    if current_gpu is not None and (peak_gpu is None or current_gpu > peak_gpu):
        peak_gpu = current_gpu

    final_ps = ollama_ps(ollama)
    if final_ps and final_ps not in ps_samples:
        ps_samples.append(final_ps)

    return {
        "baseline_ram_mb": baseline_ram,
        "peak_ram_mb": peak_ram,
        "peak_ram_delta_mb": (
            round(peak_ram - baseline_ram, 1)
            if peak_ram is not None and baseline_ram is not None
            else None
        ),
        "baseline_gpu_mb": baseline_gpu,
        "peak_gpu_mb": peak_gpu,
        "peak_gpu_delta_mb": (
            round(peak_gpu - baseline_gpu, 1)
            if peak_gpu is not None and baseline_gpu is not None
            else None
        ),
        "ollama_ps_samples": ps_samples[-4:],
    }


def run_model(model: str, ollama: str) -> dict:
    stop_models(ollama)
    baseline_ram = ram_used_mb()
    baseline_gpu = gpu_used_mb()

    env = os.environ.copy()
    env["ORION_BENCHMARK_MODEL"] = "ollama_chat/" + model
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    with tempfile.TemporaryDirectory(prefix="orion-run040-") as td:
        log_path = Path(td) / "operator.log"
        started = time.perf_counter()
        with log_path.open("w", encoding="utf-8", errors="replace") as log:
            proc = subprocess.Popen(
                [
                    "uv",
                    "run",
                    "--project",
                    str(OPENHANDS),
                    "--package",
                    "openhands-tools",
                    "python",
                    str(BENCH),
                ],
                cwd=str(ROOT),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
            )
            metrics = sample_metrics(
                proc,
                ollama=ollama,
                baseline_ram=baseline_ram,
                baseline_gpu=baseline_gpu,
            )
            exit_code = proc.wait()
        wall_seconds = round(time.perf_counter() - started, 3)
        output = log_path.read_text(encoding="utf-8", errors="replace")

    missing = [marker for marker in REQUIRED_MARKERS if marker not in output]
    result = {
        "model": model,
        "exit_code": exit_code,
        "wall_seconds": wall_seconds,
        "actions": parse_actions(output),
        "correctness_pass": exit_code == 0 and not missing,
        "missing_markers": missing,
        **metrics,
    }
    if not result["correctness_pass"]:
        result["failure_tail"] = output[-3000:]
    return result


def main() -> int:
    print("V3_RUN_ID> V3-RUN-040B")
    print("ORION_OPERATOR_EFFICIENCY_COMPARISON_4MODEL> START")

    if not OPENHANDS.is_dir() or not BENCH.is_file():
        raise RuntimeError("required benchmark substrate missing")

    ollama = find_ollama()
    rows: list[dict] = []

    for model in MODELS:
        print("MODEL_BENCHMARK_START> " + model)
        row = run_model(model, ollama)
        rows.append(row)
        print(
            "MODEL_BENCHMARK_RESULT> "
            + json.dumps(row, ensure_ascii=False, sort_keys=True)
        )
        if not row["correctness_pass"]:
            print("ORION_OPERATOR_EFFICIENCY_COMPARISON_4MODEL> FAIL")
            print("STATUS> FAIL")
            return 1

    fastest = min(rows, key=lambda item: item["wall_seconds"])["model"]
    gpu_rows = [r for r in rows if r["peak_gpu_delta_mb"] is not None]
    ram_rows = [r for r in rows if r["peak_ram_delta_mb"] is not None]
    least_gpu = min(gpu_rows, key=lambda item: item["peak_gpu_delta_mb"])["model"] if gpu_rows else None
    least_ram = min(ram_rows, key=lambda item: item["peak_ram_delta_mb"])["model"] if ram_rows else None

    summary = {
        "schema": "orion.v3.operator-efficiency.v0",
        "models": rows,
        "fastest_wall_clock": fastest,
        "lowest_peak_gpu_delta": least_gpu,
        "lowest_peak_ram_delta": least_ram,
        "notes": [
            "Each candidate was unloaded with ollama stop before its run.",
            "Wall time includes model load plus the same four-case ORION operator workload.",
            "GPU metric is total nvidia-smi memory.used sampled during the run minus pre-run baseline.",
            "RAM metric is total system physical RAM used sampled during the run minus pre-run baseline.",
            "These are one-run local measurements, not statistical performance claims.",
            "The intended daily-operator winner must pass correctness/authority first; among passing models prefer lower wall time and lower RAM/GPU use.",
        ],
    }

    print("ORION_OPERATOR_EFFICIENCY_SUMMARY> " + json.dumps(summary, ensure_ascii=False, sort_keys=True))
    print("ORION_OPERATOR_EFFICIENCY_COMPARISON_4MODEL> PASS")
    print("STATUS> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
