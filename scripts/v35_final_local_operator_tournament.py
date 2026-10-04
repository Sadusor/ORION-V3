from __future__ import annotations

import ctypes
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPENHANDS = ROOT / "external" / "OpenHands-software-agent-sdk"
RUNTIME = ROOT / "scripts" / "v35_operator_resilience_runtime.py"
NUM_CTX = 4096

CANDIDATES = [
    {
        "label": "9B_OFF",
        "model": "qwen35-9b-orion:latest",
        "reasoning_effort": "none",
    },
    {
        "label": "IQ4_OFF",
        "model": "batiai/qwen3.8-27b:iq4",
        "reasoning_effort": "none",
    },
    {
        "label": "IQ4_ON",
        "model": "batiai/qwen3.8-27b:iq4",
        "reasoning_effort": "medium",
    },
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
    return round(
        (status.ullTotalPhys - status.ullAvailPhys) / (1024 * 1024),
        1,
    )


def find_executable(
    names: tuple[str, ...],
    extra: list[Path] | None = None,
) -> str | None:
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
        extra.extend(
            [
                Path(local) / "Programs" / "Ollama" / "ollama.exe",
                Path(local) / "Ollama" / "ollama.exe",
            ]
        )
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
            [
                exe,
                "--query-gpu=memory.used",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
        values = []
        for line in out.splitlines():
            value = line.strip()
            if value and value.lower() != "n/a":
                values.append(float(value))
        return round(sum(values), 1) if values else None
    except Exception:
        return None


def ollama_ps_text(ollama: str) -> str:
    try:
        return subprocess.check_output(
            [ollama, "ps"],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=8,
        ).strip()
    except Exception as exc:
        return "ERROR " + type(exc).__name__ + ": " + str(exc)


def ollama_ps_json() -> dict:
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:11434/api/ps",
            timeout=3,
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def runtime_model_info(model: str) -> dict | None:
    for item in ollama_ps_json().get("models", []):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("model") or "")
        if name == model:
            return {
                "name": name,
                "size_bytes": item.get("size"),
                "size_vram_bytes": item.get("size_vram"),
                "context_length": item.get("context_length"),
            }
    return None


def unique_models() -> list[str]:
    return list(dict.fromkeys(str(item["model"]) for item in CANDIDATES))


def stop_models(ollama: str) -> None:
    for model in unique_models():
        subprocess.run(
            [ollama, "stop", model],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
            check=False,
        )
    time.sleep(1.0)


def parse_runtime_summary(output: str) -> dict | None:
    prefix = "ORION_LOCAL_OPERATOR_RESILIENCE_SUMMARY> "
    matches = [
        line[len(prefix):]
        for line in output.splitlines()
        if line.startswith(prefix)
    ]
    if not matches:
        return None
    try:
        payload = json.loads(matches[-1])
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


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
        if current_ram is not None and (
            peak_ram is None or current_ram > peak_ram
        ):
            peak_ram = current_ram
        if current_gpu is not None and (
            peak_gpu is None or current_gpu > peak_gpu
        ):
            peak_gpu = current_gpu

        now = time.perf_counter()
        if now - last_ps_at >= 2.0:
            value = ollama_ps_text(ollama)
            if value and value not in ps_samples:
                ps_samples.append(value)
            last_ps_at = now
        time.sleep(0.5)

    current_ram = ram_used_mb()
    current_gpu = gpu_used_mb()
    if current_ram is not None and (
        peak_ram is None or current_ram > peak_ram
    ):
        peak_ram = current_ram
    if current_gpu is not None and (
        peak_gpu is None or current_gpu > peak_gpu
    ):
        peak_gpu = current_gpu

    final_ps = ollama_ps_text(ollama)
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


def run_candidate(candidate: dict, ollama: str) -> dict:
    label = str(candidate["label"])
    model = str(candidate["model"])
    reasoning_effort = str(candidate["reasoning_effort"])

    stop_models(ollama)
    baseline_ram = ram_used_mb()
    baseline_gpu = gpu_used_mb()

    env = os.environ.copy()
    env["ORION_BENCHMARK_MODEL"] = "ollama_chat/" + model
    env["ORION_BENCHMARK_REASONING_EFFORT"] = reasoning_effort
    env["ORION_BENCHMARK_NUM_CTX"] = str(NUM_CTX)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    with tempfile.TemporaryDirectory(prefix="orion-run043-tournament-") as td:
        log_path = Path(td) / "candidate.log"
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
                    str(RUNTIME),
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

    runtime_summary = parse_runtime_summary(output)
    runtime = runtime_model_info(model)
    context_verified = (
        runtime is not None
        and int(runtime.get("context_length") or 0) == NUM_CTX
    )
    think_expected = reasoning_effort in {"low", "medium", "high"}
    think_marker = (
        "OLLAMA_THINK_MAPPED> " + ("true" if think_expected else "false")
    )
    benchmark_valid = (
        exit_code == 0
        and runtime_summary is not None
        and "BENCHMARK_EXECUTION> PASS" in output
        and think_marker in output
        and context_verified
    )

    result = {
        "label": label,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "think_expected": think_expected,
        "requested_num_ctx": NUM_CTX,
        "runtime": runtime,
        "context_verified": context_verified,
        "benchmark_valid": benchmark_valid,
        "qualified": bool(runtime_summary.get("qualified"))
        if runtime_summary is not None
        else False,
        "cases_passed": runtime_summary.get("cases_passed")
        if runtime_summary is not None
        else None,
        "cases_total": runtime_summary.get("cases_total")
        if runtime_summary is not None
        else None,
        "total_actions": runtime_summary.get("total_actions")
        if runtime_summary is not None
        else None,
        "case_results": runtime_summary.get("cases")
        if runtime_summary is not None
        else None,
        "exit_code": exit_code,
        "wall_seconds": wall_seconds,
        **metrics,
    }
    if not benchmark_valid:
        result["failure_tail"] = output[-3500:]
    return result


def best_qualified(rows: list[dict], metric: str) -> str | None:
    valid = [
        row
        for row in rows
        if row["benchmark_valid"]
        and row["qualified"]
        and row.get(metric) is not None
    ]
    if not valid:
        return None
    return str(min(valid, key=lambda row: row[metric])["label"])


def main() -> int:
    print("V3_RUN_ID> V3-RUN-043")
    print("ORION_FINAL_LOCAL_OPERATOR_TOURNAMENT> START")
    print("COMMON_NUM_CTX> " + str(NUM_CTX))

    if not OPENHANDS.is_dir() or not RUNTIME.is_file():
        raise RuntimeError("required tournament substrate missing")

    ollama = find_ollama()
    rows: list[dict] = []

    for candidate in CANDIDATES:
        print(
            "FINAL_CANDIDATE_START> "
            + str(candidate["label"])
            + " "
            + str(candidate["model"])
            + " reasoning="
            + str(candidate["reasoning_effort"])
        )
        row = run_candidate(candidate, ollama)
        rows.append(row)
        print(
            "FINAL_CANDIDATE_RESULT> "
            + json.dumps(row, ensure_ascii=False, sort_keys=True)
        )

    valid_rows = [row for row in rows if row["benchmark_valid"]]
    qualified_rows = [row for row in valid_rows if row["qualified"]]

    summary = {
        "schema": "orion.v3.final-local-operator-tournament.v0",
        "common_num_ctx": NUM_CTX,
        "candidates": rows,
        "valid_labels": [row["label"] for row in valid_rows],
        "qualified_labels": [row["label"] for row in qualified_rows],
        "fastest_qualified": best_qualified(rows, "wall_seconds"),
        "lowest_ram_qualified": best_qualified(rows, "peak_ram_delta_mb"),
        "lowest_gpu_qualified": best_qualified(rows, "peak_gpu_delta_mb"),
        "fewest_actions_qualified": best_qualified(rows, "total_actions"),
        "selection_rule": (
            "hard behavioral qualification first; among qualified candidates "
            "prefer fast + low consumption for routine local operation"
        ),
    }
    print(
        "ORION_FINAL_LOCAL_OPERATOR_SUMMARY> "
        + json.dumps(summary, ensure_ascii=False, sort_keys=True)
    )

    expected_labels = {"9B_OFF", "IQ4_OFF", "IQ4_ON"}
    observed_labels = {str(row["label"]) for row in rows}
    all_valid = (
        observed_labels == expected_labels
        and all(row["benchmark_valid"] for row in rows)
    )
    print(
        "TOURNAMENT_BENCHMARK_VALID> "
        + ("PASS" if all_valid else "FAIL")
    )
    print("ORION_FINAL_LOCAL_OPERATOR_TOURNAMENT> COMPLETE")
    if not all_valid:
        print("STATUS> FAIL")
        return 1

    print("STATUS> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
