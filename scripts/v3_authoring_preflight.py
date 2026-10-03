from __future__ import annotations

import subprocess
from pathlib import Path

from orion_v3.authoring import require_preflight


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


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    files = tracked_files(repo_root)
    print("AUTHORING_PREFLIGHT> START")
    print(f"AUTHORING_PREFLIGHT_FILES> {len(files)}")
    try:
        require_preflight(repo_root, files)
    except Exception as exc:
        print(f"AUTHORING_PREFLIGHT_DETAIL> {exc}")
        print("AUTHORING_PREFLIGHT> FAIL")
        print("STATUS> FAIL")
        return 1

    print("AUTHORING_PREFLIGHT> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
