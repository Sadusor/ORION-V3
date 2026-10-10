"""Derived, read-only codebase map from a Gitea Git tree.

This is context for Qwen, not a new canonical memory store or authority.
Repository text and filenames remain untrusted data.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import PurePosixPath

MAX_ENTRIES = 5000
MAX_PATH = 500
SOURCE_EXTENSIONS = {".py", ".go", ".rs", ".cs", ".kt", ".java", ".js", ".ts", ".tsx",
                     ".jsx", ".html", ".css", ".json", ".toml", ".yaml", ".yml",
                     ".md", ".ps1", ".sh", ".sql", ".xml", ".gradle"}
SKIP_PARTS = {".git", "node_modules", ".venv", "venv", "dist", "build",
              "__pycache__", "target", ".next", "vendor", "coverage"}
SECRET_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519",
                "credentials.json", "secrets.json", "app.ini"}

@dataclass(frozen=True)
class CodebaseFile:
    path: str
    blob_sha: str
    extension: str

def create_codebase_map(tree: dict, *, owner: str, repository: str, commit_sha: str) -> dict:
    if not owner or not repository:
        raise ValueError("Explicit repository owner/name required")
    if len(commit_sha) != 40 or any(ch not in "0123456789abcdefABCDEF" for ch in commit_sha):
        raise ValueError("Exact Git commit SHA required")
    if tree.get("truncated"):
        raise ValueError("Incomplete Gitea tree must not be represented as complete")
    entries = tree.get("tree")
    if not isinstance(entries, list) or len(entries) > MAX_ENTRIES:
        raise ValueError("Tree missing or too large; use bounded per-directory maps")
    files = []
    for item in entries:
        if item.get("type") != "blob":
            continue
        name = item.get("path")
        if not isinstance(name, str) or not name or len(name) > MAX_PATH:
            continue
        parsed = PurePosixPath(name)
        if (name.startswith("/") or "\\" in name or
            any(part in ("", ".", "..") for part in name.split("/"))):
            continue
        if any(part.lower() in SKIP_PARTS for part in parsed.parts):
            continue
        if parsed.name.lower() in SECRET_NAMES or parsed.name.lower().endswith((".key", ".pem", ".p12")):
            continue
        ext = parsed.suffix.lower()
        if ext not in SOURCE_EXTENSIONS:
            continue
        files.append(CodebaseFile(name, str(item.get("sha", "")), ext))
    files.sort(key=lambda x: x.path)
    kinds = {}
    for f in files:
        kinds[f.extension] = kinds.get(f.extension, 0) + 1
    return {"schema": "orion.gitea-codebase-map/1", "owner": owner,
            "repository": repository, "source_commit": commit_sha,
            "source_tree_sha": str(tree.get("sha", "")), "files": [vars(f) for f in files],
            "file_count": len(files), "extensions": dict(sorted(kinds.items())),
            "authority": "context_only", "filesystem_writes": False}
