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
BENCH = ROOT / "scripts" / "v35_operator_bounded_runtime.py"
NUM_CTX = 4096

CANDIDATES = [
    {
        "label": "9B_OFF",
        "model": "qwen35-9b-orion:latest",
        "reasoning_effort": "none",
    },
    {
        "label": "35B_OFF",
        "model": "qwen3.6:35b-a3b",
        "reasoning_effort": "none",
    },
    {
        "label": "27B_OFF",
        "model": "qwen3.8:27b",
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
    payload = ollama_ps_json()
    for item in payload.get("models", []):
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


def parse_actions(output: str) -> int | None:
    matches = re.findall(
        r"^TOTAL_AGENT_ACTIONS>\s+(\d+)\s*$",
        output,
        re.MULTILINE,
    )
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

    with tempfile.TemporaryDirectory(prefix="orion-run042-") as td:
        log_path = Path(td) / "operator.log"
        started = time.perf_counter()
        with log_path.open(
            "w",
            encoding="utf-8",
            errors="replace",
        ) as log:
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
        output = log_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

    dynamic_markers = [
        "OLLAMA_NUM_CTX_REQUESTED> " + str(NUM_CTX),
        "OLLAMA_REASONING_EFFORT> " + reasoning_effort,
        "OLLAMA_THINK_MAPPED> "
        + ("true" if reasoning_effort in {"low", "medium", "high"} else "false"),
    ]
    missing = [
        marker
        for marker in [*REQUIRED_MARKERS, *dynamic_markers]
        if marker not in output
    ]

    runtime = runtime_model_info(model)
    context_ok = (
        runtime is not None
        and int(runtime.get("context_length") or 0) == NUM_CTX
    )

    result = {
        "label": label,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "think_expected": reasoning_effort in {"low", "medium", "high"},
        "requested_num_ctx": NUM_CTX,
        "runtime": runtime,
        "context_verified": context_ok,
        "exit_code": exit_code,
        "wall_seconds": wall_seconds,
        "actions": parse_actions(output),
        "correctness_pass": exit_code == 0 and not missing and context_ok,
        "missing_markers": missing,
        **metrics,
    }
    if not result["correctness_pass"]:
        result["failure_tail"] = output[-3500:]
    return result


def best_label(rows: list[dict], key: str) -> str | None:
    eligible = [
        row
        for row in rows
        if row["correctness_pass"] and row.get(key) is not None
    ]
    if not eligible:
        return None
    return str(min(eligible, key=lambda item: item[key])["label"])


def main() -> int:
    print("V3_RUN_ID> V3-RUN-042")
    print("ORION_FAST_GOOD_LOW_CONSUMPTION> START")
    print("COMMON_NUM_CTX> " + str(NUM_CTX))

    if not OPENHANDS.is_dir() or not BENCH.is_file():
        raise RuntimeError("required benchmark substrate missing")

    ollama = find_ollama()
    rows: list[dict] = []

    for candidate in CANDIDATES:
        print(
            "CANDIDATE_START> "
            + str(candidate["label"])
            + " "
            + str(candidate["model"])
            + " reasoning="
            + str(candidate["reasoning_effort"])
        )
        row = run_candidate(candidate, ollama)
        rows.append(row)
        print(
            "CANDIDATE_RESULT> "
            + json.dumps(row, ensure_ascii=False, sort_keys=True)
        )

    passing = [row for row in rows if row["correctness_pass"]]
    summary = {
        "schema": "orion.v3.fast-good-low-consumption.v0",
        "common_num_ctx": NUM_CTX,
        "candidates": rows,
        "passing_labels": [row["label"] for row in passing],
        "fastest_passing": best_label(rows, "wall_seconds"),
        "lowest_peak_ram_passing": best_label(rows, "peak_ram_delta_mb"),
        "lowest_peak_gpu_passing": best_label(rows, "peak_gpu_delta_mb"),
        "fewest_actions_passing": best_label(rows, "actions"),
        "notes": [
            "Correctness and authority are hard gates before efficiency ranking.",
            "Every candidate runs at requested num_ctx=4096 and must be observed at that context through Ollama /api/ps.",
            "reasoning_effort=none maps to Ollama think=false in pinned LiteLLM 1.93.0.",
            "reasoning_effort=medium maps to Ollama think=true for these non-gpt-oss Ollama models in pinned LiteLLM 1.93.0.",
            "Each candidate is unloaded before its cold run.",
            "Metrics are one-run local measurements, not statistical claims.",
        ],
    }

    print(
        "ORION_FAST_GOOD_LOW_CONSUMPTION_SUMMARY> "
        + json.dumps(summary, ensure_ascii=False, sort_keys=True)
    )

    required_labels = {"9B_OFF", "35B_OFF", "27B_OFF", "IQ4_OFF", "IQ4_ON"}
    observed_labels = {str(row["label"]) for row in rows}
    if observed_labels != required_labels:
        print("ORION_FAST_GOOD_LOW_CONSUMPTION> FAIL")
        print("STATUS> FAIL")
        return 1

    if not any(row["label"] == "9B_OFF" and row["correctness_pass"] for row in rows):
        print("NINE_B_OPERATOR_QUALIFIED> FAIL")
    else:
        print("NINE_B_OPERATOR_QUALIFIED> PASS")

    print("ORION_FAST_GOOD_LOW_CONSUMPTION> COMPLETE")
    print("STATUS> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
