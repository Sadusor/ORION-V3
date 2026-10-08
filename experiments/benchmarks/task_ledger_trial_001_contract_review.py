"""Static-only Task Ledger HTTP contract review of the saved model response.

The reviewer never imports, extracts, executes or evaluates submitted Python.
Regex findings are indicators, not functional test results.
"""
from __future__ import annotations
import ast
import hashlib
import json
import re
from task_ledger_cloud_trial_001 import runtime_root
from task_ledger_trial_001_completeness import FENCE, MAX_BYTES

CHECKS = {
    "loopback_bind": r"127\.0\.0\.1",
    "json_content_type": r"application/json",
    "create_task": r"/tasks|create_task",
    "duplicate_conflict": r"\b409\b|HTTPStatus\.CONFLICT",
    "get_task": r"/tasks/|get_task",
    "list_tasks": r"ORDER\s+BY|sorted\s*\(",
    "transition_endpoint": r"/transition",
    "pending_running": r"\bPENDING\b[\s\S]{0,250}\bRUNNING\b",
    "terminal_states": r"\bDONE\b|\bFAILED\b|\bCANCELLED\b",
    "evidence_endpoint": r"/evidence",
    "id_validation": r"A-Za-z0-9_|fullmatch|re\.match",
    "invalid_input_400": r"\b400\b|HTTPStatus\.BAD_REQUEST",
    "body_size_limit": r"16384|16\s*\*\s*1024|16\s*KiB",
    "sqlite_storage": r"sqlite3|SQLite",
    "database_env": r"TASK_LEDGER_DB",
    "atomic_transition": r"BEGIN\s+IMMEDIATE|UPDATE\s+tasks|\bcommit\s*\(",
    "health_endpoint": r"/health",
    "module_entrypoint": r"__main__|python\s+-m\s+task_ledger",
    "tests": r"(?m)^\s*(?:async\s+)?def\s+test_\w+\s*\(",
}
def review(text: str) -> dict:
    blocks = []
    for i, match in enumerate(FENCE.finditer(text), 1):
        tag = match.group(1).strip().lower()
        if tag not in ("python", "py") and not tag.endswith(".py"):
            continue
        body = match.group(2)
        try:
            tree = ast.parse(body)
            status = "VALID"
            functions = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        except SyntaxError:
            status, functions = "INVALID", []
        preceding = text[:match.start()].rstrip().split("\n")[-1].strip()
        blocks.append({"block": i, "label": preceding[:140], "syntax": status,
                       "lines": len(body.splitlines()), "function_names": functions[:50],
                       "sha256": hashlib.sha256(body.encode()).hexdigest()})
    checks = {name: bool(re.search(pattern, text, re.I)) for name, pattern in CHECKS.items()}
    return {"schema": "orion.task_ledger.contract_static_review.v1",
            "blocks": blocks, "indicators": checks,
            "missing_indicators": sorted(k for k, v in checks.items() if not v),
            "static_review": "INDICATORS_ONLY", "functional_contract": "NOT_TESTED",
            "execution": "NOT_RUN",
            "decision": "HOLD_ISOLATED_EXECUTION_PENDING_HUMAN_REVIEW",
            "caveat": "Regex matches do not establish endpoint correctness, transaction safety, validation or durability."}

def main() -> None:
    folder = runtime_root() / "coding-mode" / "reviewers" / "task-ledger-trial-001"
    raw = (folder / "cloud-output.txt").read_bytes()
    if len(raw) > MAX_BYTES:
        raise RuntimeError("oversized saved response")
    text = raw.decode("utf-8").replace("\r\n", "\n")
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if digest != manifest["output_sha256"]:
        raise RuntimeError("saved response hash mismatch")
    report = review(text)
    report["input_sha256"] = digest
    print("LEDGER_REVIEW> HASH_VERIFIED", flush=True)
    print("LEDGER_REVIEW> PYTHON_BLOCKS", len(report["blocks"]), flush=True)
    for block in report["blocks"]:
        print("LEDGER_REVIEW> BLOCK", json.dumps(block, sort_keys=True), flush=True)
    print("LEDGER_REVIEW> INDICATORS", json.dumps(report["indicators"], sort_keys=True), flush=True)
    print("LEDGER_REVIEW> MISSING_INDICATORS", json.dumps(report["missing_indicators"]), flush=True)
    destination = folder / "contract-static-review-v1.json"
    if destination.exists():
        raise RuntimeError("review exists; refusing overwrite")
    destination.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print("LEDGER_REVIEW> HOLD_ISOLATED_EXECUTION_NO_MODEL_CODE_RUN", flush=True)

if __name__ == "__main__":
    main()
