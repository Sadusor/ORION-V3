"""Read-only diagnostic of Task Ledger cloud response formatting and contract evidence.

Never imports, writes out, or executes submitted source code.
"""
from __future__ import annotations
import ast
import hashlib
import json
import re
from pathlib import Path
from task_ledger_cloud_trial_001 import runtime_root
from task_ledger_trial_001_completeness import check, FENCE, MAX_BYTES

CONTRACT = {
    "package_entrypoint": r"task_ledger[/\\]__main__\\.py|python\\s+-m\\s+task_ledger",
    "sqlite": r"\\bsqlite3\\b|\\bSQLite\\b",
    "environment_db": r"TASK_LEDGER_DB",
    "create_route": r"POST\\s+/tasks|do_POST",
    "read_route": r"GET\\s+/tasks/\\{?id|/tasks/|do_GET",
    "list_route": r"GET\\s+/tasks\\b|/tasks",
    "transition_route": r"/transition",
    "evidence_route": r"/evidence",
    "health_route": r"/health",
    "concurrency": r"\\b(lock|threading|transaction|BEGIN IMMEDIATE)\\b",
}
def diagnose(text: str) -> dict:
    basic = check(text)
    fences = list(FENCE.finditer(text))
    python_blocks = []
    test_counts = {"fenced_python_ast": 0, "raw_def_signatures": 0, "unittest_methods": 0, "pytest_functions": 0}
    for index, match in enumerate(fences, 1):
        tag = match.group(1).strip().lower()
        if tag not in ("python", "py") and not tag.endswith(".py"):
            continue
        body = match.group(2)
        try:
            tree = ast.parse(body)
            syntax = "VALID"
            funcs = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            count = sum(n.startswith("test_") for n in funcs)
            test_counts["fenced_python_ast"] += count
            test_counts["unittest_methods"] += sum(n.startswith("test_") and n != "test_" for n in funcs)
            test_counts["pytest_functions"] += sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_") for n in tree.body)
        except SyntaxError:
            syntax, count = "INVALID", 0
        python_blocks.append({"index": index, "tag": tag[:80], "syntax": syntax, "test_functions": count})
    test_counts["raw_def_signatures"] = len(re.findall(r"(?m)^\\s*(?:async\\s+)?def\\s+test_[A-Za-z0-9_]+\\s*\\(", text))
    paths = sorted(set(p.replace("\\\\", "/") for p in re.findall(r"(?:task_ledger|tests?)[/\\\\][A-Za-z0-9_./\\\\-]+\\.py", text, re.I)))
    signals = {key: bool(re.search(pattern, text, re.I)) for key, pattern in CONTRACT.items()}
    # Signal presence is never a claim that HTTP semantics are correct.
    if test_counts["raw_def_signatures"] == 0 and test_counts["fenced_python_ast"] == 0:
        classification = "NO_RECOGNIZED_TEST_FUNCTIONS"
    elif test_counts["fenced_python_ast"] > 0 and "missing_named_test_file" in basic["issues"]:
        classification = "TESTS_PRESENT_BUT_FILE_LABEL_NOT_RECOGNIZED"
    elif test_counts["fenced_python_ast"] > 0:
        classification = "TESTS_RECOGNIZED"
    else:
        classification = "TESTS_PRESENT_OUTSIDE_RECOGNIZED_PYTHON_FENCES"
    return {"schema": "orion.task_ledger.static_diagnostic.v1", "basic_verdict": basic["verdict"],
            "issues": basic["issues"], "classification": classification,
            "test_counts": test_counts, "mentioned_paths": paths,
            "python_blocks": python_blocks, "contract_signals": signals,
            "contract_semantics": "NOT_DETERMINED", "execution": "NOT_RUN",
            "note": "Regex signal presence/absence is only a formatting hint, not a functional contract score."}

def main() -> None:
    folder = runtime_root() / "coding-mode" / "reviewers" / "task-ledger-trial-001"
    raw = (folder / "cloud-output.txt").read_bytes()
    if len(raw) > MAX_BYTES:
        raise RuntimeError("oversized saved response")
    text = raw.decode("utf-8").replace("\\r\\n", "\\n")
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if digest != manifest["output_sha256"]:
        raise RuntimeError("saved response hash mismatch")
    report = diagnose(text)
    report["input_sha256"] = digest
    print("LEDGER_DIAGNOSTIC> HASH_VERIFIED", flush=True)
    print("LEDGER_DIAGNOSTIC> CLASSIFICATION", report["classification"], flush=True)
    print("LEDGER_DIAGNOSTIC> BASIC_VERDICT", report["basic_verdict"], flush=True)
    print("LEDGER_DIAGNOSTIC> TEST_COUNTS", json.dumps(report["test_counts"], sort_keys=True), flush=True)
    print("LEDGER_DIAGNOSTIC> PATHS", json.dumps(report["mentioned_paths"]), flush=True)
    print("LEDGER_DIAGNOSTIC> CONTRACT_SIGNALS", json.dumps(report["contract_signals"], sort_keys=True), flush=True)
    destination = folder / "format-diagnostic-v1.json"
    if destination.exists():
        raise RuntimeError("diagnostic already exists; refusing overwrite")
    destination.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print("LEDGER_DIAGNOSTIC> REPORT_SAVED_NO_MODEL_EXECUTION", flush=True)

if __name__ == "__main__":
    main()
