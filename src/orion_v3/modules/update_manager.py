from __future__ import annotations

import json
import os
import pathlib
import subprocess
import threading
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class UpdateError(RuntimeError):
    pass


class UpdateManager:
    """Bounded fast-forward updater for ORION main.

    The HTTP server may request an update, but it never performs a destructive merge.
    Only a clean local `main` that is not ahead of `origin/main` may fast-forward.
    A Windows-owned helper then runs tests/builds, restarts ORION, and records evidence.
    """

    def __init__(self, root: pathlib.Path, state_root: pathlib.Path):
        self.root = pathlib.Path(root).resolve()
        self.state_root = pathlib.Path(state_root).resolve()
        self.status_path = self.state_root / "update-status.json"
        self.helper = self.root / "scripts" / "apply_orion_update.ps1"
        self._lock = threading.Lock()

    def _git(self, *args: str, check: bool = True, timeout: int = 30) -> str:
        try:
            proc = subprocess.run(
                ["git", "-C", str(self.root), *args],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
            )
        except Exception as exc:
            raise UpdateError("git failed: " + str(exc)) from exc
        if check and proc.returncode != 0:
            raise UpdateError((proc.stderr or proc.stdout or "git command failed").strip())
        return proc.stdout.strip()

    def _read_status(self) -> dict[str, Any]:
        if not self.status_path.is_file():
            return {
                "schema": "orion-v3.update-status/1",
                "state": "idle",
                "message": "",
                "commit": "",
                "updated_at": "",
            }
        try:
            data = json.loads(self.status_path.read_text(encoding="utf-8-sig"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return {
            "schema": "orion-v3.update-status/1",
            "state": "unknown",
            "message": "update status file is unreadable",
            "commit": "",
            "updated_at": "",
        }

    def _write_status(self, state: str, message: str, commit: str) -> None:
        self.state_root.mkdir(parents=True, exist_ok=True)
        temp = self.status_path.with_suffix(".json.tmp")
        temp.write_text(
            json.dumps(
                {
                    "schema": "orion-v3.update-status/1",
                    "state": state,
                    "message": message,
                    "commit": commit,
                    "updated_at": _now(),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        temp.replace(self.status_path)

    def status(self) -> dict[str, Any]:
        return self._read_status()

    def check(self) -> dict[str, Any]:
        with self._lock:
            branch = self._git("branch", "--show-current")
            dirty = bool(self._git("status", "--porcelain", "--untracked-files=no"))
            current = self._git("rev-parse", "HEAD")

            if branch != "main":
                return {
                    "ok": True,
                    "can_update": False,
                    "branch": branch or "detached",
                    "current": current,
                    "remote": "",
                    "ahead": 0,
                    "behind": 0,
                    "dirty": dirty,
                    "reason": "ORION update requires the PC repo to be on main.",
                    "status": self.status(),
                }

            try:
                self._git("fetch", "--quiet", "origin", "main", timeout=60)
                remote = self._git("rev-parse", "origin/main")
                counts = self._git(
                    "rev-list",
                    "--left-right",
                    "--count",
                    "HEAD...origin/main",
                ).split()
                ahead = int(counts[0]) if len(counts) > 0 else 0
                behind = int(counts[1]) if len(counts) > 1 else 0
            except Exception as exc:
                return {
                    "ok": False,
                    "can_update": False,
                    "branch": branch,
                    "current": current,
                    "remote": "",
                    "ahead": 0,
                    "behind": 0,
                    "dirty": dirty,
                    "reason": str(exc),
                    "status": self.status(),
                }

            reason = ""
            can_update = True
            if dirty:
                can_update = False
                reason = "Tracked local changes detected; refusing remote update."
            elif ahead > 0:
                can_update = False
                reason = "Local main contains commits not on origin/main."
            elif behind == 0:
                reason = "ORION main is current."

            return {
                "ok": True,
                "can_update": can_update,
                "branch": branch,
                "current": current,
                "remote": remote,
                "ahead": ahead,
                "behind": behind,
                "dirty": dirty,
                "reason": reason,
                "status": self.status(),
            }

    def apply(self, running_commit: str) -> dict[str, Any]:
        with self._lock:
            branch = self._git("branch", "--show-current")
            if branch != "main":
                raise UpdateError(
                    "UPDATE ORION requires PC repo main; current branch is "
                    + (branch or "detached")
                )

            dirty = self._git("status", "--porcelain", "--untracked-files=no")
            if dirty:
                raise UpdateError("Tracked local changes detected; refusing UPDATE ORION.")

            before = self._git("rev-parse", "HEAD")
            self._git("fetch", "--quiet", "origin", "main", timeout=60)
            counts = self._git(
                "rev-list",
                "--left-right",
                "--count",
                "HEAD...origin/main",
            ).split()
            ahead = int(counts[0]) if len(counts) > 0 else 0
            behind = int(counts[1]) if len(counts) > 1 else 0

            if ahead > 0:
                raise UpdateError("Local main is ahead of origin/main; refusing remote update.")

            if behind > 0:
                self._git("merge", "--ff-only", "origin/main", timeout=60)

            after = self._git("rev-parse", "HEAD")
            runtime_mismatch = bool(running_commit and running_commit != after)
            restart_needed = before != after or runtime_mismatch

            if not restart_needed:
                self._write_status("pass", "ORION is already current.", after)
                return {
                    "before": before,
                    "after": after,
                    "changed": False,
                    "runtime_mismatch": False,
                    "restart_scheduled": False,
                }

            if not self.helper.is_file():
                if after != before:
                    self._git("reset", "--hard", before)
                raise UpdateError("ORION update helper is missing.")

            self._write_status(
                "scheduled",
                "Update merged; Windows restart worker is being armed.",
                after,
            )

            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
            proc = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(self.helper),
                    "-ExpectedCommit",
                    after,
                    "-PreviousCommit",
                    before,
                ],
                cwd=str(self.root),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=flags,
                timeout=25,
                check=False,
            )

            if proc.returncode != 0:
                detail = (proc.stderr or proc.stdout or "").strip()
                if after != before:
                    try:
                        self._git("reset", "--hard", before)
                    except Exception:
                        pass
                self._write_status(
                    "failed",
                    "Windows update worker could not start"
                    + (": " + detail[-1200:] if detail else ""),
                    before,
                )
                raise UpdateError(
                    "Windows update worker could not start"
                    + (": " + detail[-1200:] if detail else "")
                )

            return {
                "before": before,
                "after": after,
                "changed": before != after,
                "runtime_mismatch": runtime_mismatch,
                "restart_scheduled": True,
            }
