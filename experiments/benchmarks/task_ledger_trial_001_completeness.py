"""Fail-closed, read-only completeness gate for inert Task Ledger trial 001.

Does not import, extract to disk, or execute submitted code.
"""
from __future__ import annotations
import ast
import hashlib
import json
import re
from pathlib import Path
from task_ledger_cloud_trial_001 import runtime_root

FENCE = re.compile(r"(?m)^\s*```([^\n]*)\n(.*?)^\s*```\s*$", re.S | re.M)
EXPECTED = ("task_ledger/__init__.py", "task_ledger/__main__.py")
MAX_BYTES = 1_000_000

def check(text: str) -> dict:
    blocks = list(FENCE.finditer(text))
    found = {}
    issues = []
    test_count = 0
    for index, match in enumerate(blocks, 1):
        tag = match.group(1).strip().lower()
        body = match.group(2)
        header = text[max(0, match.start()-180):match.start()]
        labels = re.findall(r"(?:task_ledger[/\\][\w.-]+\.py|tests?[/\\][\w./-]+\.py)", header, re.I)
        if tag.endswith(".py"):
            labels.append(tag.replace("\\", "/"))
        if tag not in ("python", "py") and not tag.endswith(".py"):
            continue
        try:
            tree = ast.parse(body)
        except SyntaxError:
            issues.append("invalid_python_block_" + str(index))
            continue
        test_count += sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")
                          for n in ast.walk(tree))
        for label in labels:
            name = label.replace("\\", "/").lower()
            if name in found:
                issues.append("duplicate_file_" + name)
            found[name] = {"block": index, "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest()}
    for name in EXPECTED:
        if name not in found:
            issues.append("missing_file_" + name)
    if not any(n.startswith("test") or "/test" in n for n in found):
        issues.append("missing_named_test_file")
    if test_count < 20:
        issues.append("fewer_than_20_test_functions")
    # Static completeness is not proof of API semantics, safety or correct behavior.
    return {"verdict": "PASS_STATIC_COMPLETENESS" if not issues else "FAIL_INCOMPLETE",
            "issues": sorted(set(issues)), "named_files": found, "test_function_count": test_count,
            "fenced_block_count": len(blocks), "execution": "NOT_RUN", "semantic_score": "NOT_RUN"}

def main() -> None:
    folder = runtime_root() / "coding-mode" / "reviewers" / "task-ledger-trial-001"
    source = folder / "cloud-output.txt"
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    raw = source.read_bytes()
    if len(raw) > MAX_BYTES:
        raise RuntimeError("oversized saved response")
    text = raw.decode("utf-8").replace("\r\n", "\n")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if digest != manifest["output_sha256"]:
        raise RuntimeError("saved response hash mismatch")
    report = check(text)
    report["input_sha256"] = digest
    print("LEDGER_COMPLETENESS> SAVED_OUTPUT_HASH_VERIFIED", flush=True)
    print("LEDGER_COMPLETENESS> VERDICT", report["verdict"], flush=True)
    print("LEDGER_COMPLETENESS> TEST_FUNCTIONS", report["test_function_count"], flush=True)
    for issue in report["issues"]:
        print("LEDGER_COMPLETENESS> ISSUE", issue, flush=True)
    # Avoid overwriting existing evidence.
    destination = folder / "completeness-report.json"
    if destination.exists():
        raise RuntimeError("completeness report exists; refusing overwrite")
    destination.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print("LEDGER_COMPLETENESS> REPORT_SAVED", flush=True)

if __name__ == "__main__":
    main()
