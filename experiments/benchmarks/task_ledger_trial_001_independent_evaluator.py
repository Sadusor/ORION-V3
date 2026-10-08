"""Independent, inert Task Ledger submission evaluator v1.

This is a static defect gate, NOT a functional correctness verdict.
It never imports or executes submitted source.
"""
from __future__ import annotations
import ast
import json
import re
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "docs/benchmarks/untrusted/task-ledger-trial-001/GPT_OSS_120B_ORIGINAL_RESPONSE.md"
REQUIRED = ("task_ledger/__init__.py", "task_ledger/db.py", "task_ledger/app.py", "task_ledger/__main__.py", "tests/test_api.py")
FENCE = re.compile(r"(?m)^\*\*([^\n*]+)\*\*\s*\n\x60\x60\x60python\s*\n(.*?)^\x60\x60\x60\s*$", re.S | re.M)

def extract(text: str) -> dict[str, str]:
    """Extract named Python fences, including fences following Markdown examples.

    A README may contain its own fenced shell commands. A subsequent file
    heading still takes precedence; no code is executed during extraction.
    """
    out = {}
    heading = re.compile(r"^\*\*([^\n*]+)\*\*\s*$")
    fence_start = re.compile(r"^\x60{3}python\s*$")
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = heading.match(lines[i])
        if not m:
            i += 1
            continue
        name = m.group(1).strip()
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j >= len(lines) or not fence_start.match(lines[j]):
            i += 1
            continue
        end = j + 1
        while end < len(lines) and lines[end].strip() != "```":
            end += 1
        out[name] = "\n".join(lines[j + 1:end]) + "\n"
        i = end + 1 if end < len(lines) else len(lines)
    return out

def imported_names(tree: ast.AST) -> set[str]:
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.asname or a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.update(a.asname or a.name for a in node.names)
    return names

def analyze(text: str) -> dict:
    sources = extract(text)
    findings = []
    def finding(code, detail):
        findings.append({"id": code, "detail": detail})
    if text.rstrip().endswith("body ="):
        finding("TRUNCATED_SUBMISSION", "Original response ends inside tests/test_api.py; test file incomplete")
    for name in REQUIRED:
        if name not in sources:
            finding("MISSING_FILE", name)
    trees = {}
    for name, src in sources.items():
        if not name.endswith(".py"):
            continue
        try:
            trees[name] = ast.parse(src, filename=name)
        except SyntaxError as exc:
            finding("SYNTAX_ERROR", f"{name}:{exc.lineno}")
    app = sources.get("task_ledger/app.py", "")
    db = sources.get("task_ledger/db.py", "")
    test = sources.get("tests/test_api.py", "")
    app_tree = trees.get("task_ledger/app.py")
    test_tree = trees.get("tests/test_api.py")
    if app_tree is not None:
        imports = imported_names(app_tree)
        if re.search(r"except\s+sqlite3\.IntegrityError", app) and "sqlite3" not in imports:
            finding("UNBOUND_SQLITE3", "app.py catches sqlite3.IntegrityError without import")
        if "set(payload.keys())" in app and not re.search(r"isinstance\(payload,\s*dict\)", app):
            finding("NON_OBJECT_JSON", "app.py calls payload.keys() without object validation")
        if re.search(r"\.read\(length\)", app) and not re.search(r"length\s*<\s*0|0\s*>\s*length", app):
            finding("NEGATIVE_CONTENT_LENGTH", "app.py may pass negative length to read()")
    if test_tree is not None and re.search(r"\bsys\.executable\b", test) and "sys" not in imported_names(test_tree):
        finding("UNBOUND_SYS", "tests/test_api.py uses sys.executable without import")
    if re.search(r'DEFAULT_DB\s*=\s*["\x27]:memory:', db) and "sqlite3.connect(path" in db:
        finding("DISCONNECTED_MEMORY_DB", "db.py uses independent :memory: connections")
    if "UPDATE tasks SET state = ? WHERE id = ? AND state = ?" in db:
        atomic = "CONDITIONAL_UPDATE_PRESENT_NOT_RUNTIME_VERIFIED"
    else:
        atomic = "NOT_IDENTIFIED"
    return {"schema": "orion.task_ledger.inert_evaluator.v1",
            "submission_execution": "NEVER", "assessment": "STATIC_ONLY",
            "source_files": sorted(sources), "findings": findings,
            "conditional_update": atomic,
            "verdict": "FAIL_STATIC_GATE" if findings else "STATIC_GATE_CLEAR_FUNCTIONAL_UNVERIFIED"}

def main():
    result = analyze(SOURCE.read_text(encoding="utf-8"))
    print("LEDGER_EVALUATOR>", json.dumps(result, sort_keys=True))
    print("LEDGER_EVALUATOR> UNTRUSTED_SOURCE_NOT_EXECUTED")

if __name__ == "__main__":
    main()
