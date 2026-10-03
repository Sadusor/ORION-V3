from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class PreflightFinding:
    code: str
    path: str
    detail: str


class AuthoringPreflightError(RuntimeError):
    def __init__(self, findings: Iterable[PreflightFinding]) -> None:
        self.findings = tuple(findings)
        summary = "; ".join(
            f"{item.code}:{item.path}:{item.detail}" for item in self.findings
        )
        super().__init__(summary or "authoring preflight failed")


def _safe_path(root: Path, relative_path: str) -> Path:
    root = root.resolve()
    target = (root / relative_path).resolve(strict=False)
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError("preflight path escapes repository root") from exc
    return target


def preflight_file(root: Path, relative_path: str) -> list[PreflightFinding]:
    path = _safe_path(Path(root), relative_path)
    if not path.is_file():
        return [
            PreflightFinding(
                code="missing_source_file",
                path=relative_path,
                detail="tracked source file is missing",
            )
        ]

    suffix = path.suffix.lower()
    if suffix == ".py":
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, relative_path, "exec")
        except (UnicodeDecodeError, SyntaxError) as exc:
            if isinstance(exc, SyntaxError):
                location = f"line {exc.lineno or '?'}"
                detail = f"{location}: {exc.msg}"
            else:
                detail = str(exc)
            return [
                PreflightFinding(
                    code="python_syntax_error",
                    path=relative_path,
                    detail=detail,
                )
            ]
        return []

    if suffix == ".json":
        try:
            json.loads(path.read_text(encoding="utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return [
                PreflightFinding(
                    code="json_syntax_error",
                    path=relative_path,
                    detail=str(exc),
                )
            ]
        return []

    return []


def preflight_paths(
    root: Path,
    relative_paths: Iterable[str],
) -> tuple[PreflightFinding, ...]:
    findings: list[PreflightFinding] = []
    seen: set[str] = set()
    for raw in relative_paths:
        relative = str(raw).replace("\\", "/").strip()
        if not relative or relative in seen:
            continue
        seen.add(relative)
        findings.extend(preflight_file(Path(root), relative))
    return tuple(findings)


def require_preflight(root: Path, relative_paths: Iterable[str]) -> None:
    findings = preflight_paths(root, relative_paths)
    if findings:
        raise AuthoringPreflightError(findings)


__all__ = [
    "AuthoringPreflightError",
    "PreflightFinding",
    "preflight_file",
    "preflight_paths",
    "require_preflight",
]
