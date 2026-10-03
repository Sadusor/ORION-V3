from __future__ import annotations

import json
import subprocess
from pathlib import Path


TRACKED_SUFFIXES = {".py", ".json"}


def tracked_files(repo_root: Path) -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files"],
        cwd=str(repo_root),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "git ls-files failed").strip())
    return [
        line.strip().replace("\\", "/")
        for line in proc.stdout.splitlines()
        if line.strip() and Path(line.strip()).suffix.lower() in TRACKED_SUFFIXES
    ]


def check_file(repo_root: Path, relative_path: str) -> str | None:
    path = (repo_root / relative_path).resolve(strict=False)
    try:
        path.relative_to(repo_root.resolve())
    except ValueError:
        return "path_escape"

    if not path.is_file():
        return "missing_source_file"

    suffix = path.suffix.lower()
    if suffix == ".py":
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, relative_path, "exec")
        except (UnicodeDecodeError, SyntaxError) as exc:
            if isinstance(exc, SyntaxError):
                return f"python_syntax_error line={exc.lineno or '?'} {exc.msg}"
            return f"python_decode_error {exc}"
    elif suffix == ".json":
        try:
            json.loads(path.read_text(encoding="utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return f"json_syntax_error {exc}"
    return None


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    print("AUTHORING_PREFLIGHT> START")
    try:
        files = tracked_files(repo_root)
    except Exception as exc:
        print(f"AUTHORING_PREFLIGHT_DETAIL> repository inventory failed: {exc}")
        print("AUTHORING_PREFLIGHT> FAIL")
        print("STATUS> FAIL")
        return 1

    print(f"AUTHORING_PREFLIGHT_FILES> {len(files)}")
    failures: list[str] = []
    for relative_path in files:
        problem = check_file(repo_root, relative_path)
        if problem:
            failures.append(f"{relative_path}: {problem}")

    if failures:
        for failure in failures:
            print(f"AUTHORING_PREFLIGHT_DETAIL> {failure}")
        print("AUTHORING_FAILURE_CLASS> AUTHORING_SYNTAX_ERROR")
        print("ARCHITECTURE_GATE_STATE> NOT_REACHED")
        print("AUTHORING_PREFLIGHT> FAIL")
        print("STATUS> FAIL")
        return 1

    print("AUTHORING_PREFLIGHT> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
