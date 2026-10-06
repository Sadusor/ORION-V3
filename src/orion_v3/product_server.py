from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import pathlib
import secrets
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

from modules.brain_pipeline import BrainPipeline
from modules.local_brain import LocalBrainError

ROOT = pathlib.Path(__file__).resolve().parents[2]
UI_ROOT = ROOT / "ui" / "strata"
STATE_ROOT = pathlib.Path(os.environ.get("LOCALAPPDATA", str(ROOT / ".local"))) / "ORION-V3"
STATE_ROOT.mkdir(parents=True, exist_ok=True)
PID_FILE = STATE_ROOT / "product-ui.pid"

LOCAL_BRAIN = BrainPipeline()

DENIED_TOP = {"demo.html", "README.md", "ARCHITECTURE.md", "INTEGRATION.md", "PRODUCT_UI.md", "STATE_CONTRACT.md", "TESTING.md"}
DENIED_DIRS = {"tests", "tools"}
DENIED_FILES = {"bridge/mock-bridge.js"}
ALLOWED_EXT = {".html", ".js", ".css", ".png", ".svg", ".ico", ".jpg", ".jpeg", ".webp"}


def _git(*args: str) -> str:
    try:
        p = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, timeout=4)
        return p.stdout.strip() if p.returncode == 0 else ""
    except Exception:
        return ""


def _now() -> str:
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class Auth:
    def __init__(self, pair_code: str):
        self.pair_code = pair_code
        self.pair_expires = time.time() + 3600
        self._digests: set[str] = set()
        self._lock = threading.Lock()

    @staticmethod
    def digest(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def pair(self, code: str) -> str:
        if time.time() > self.pair_expires:
            raise RuntimeError("pairing code expired")
        if str(code).strip() != self.pair_code:
            raise RuntimeError("invalid pairing code")
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._digests.add(self.digest(token))
        return token

    def valid(self, token: str) -> bool:
        if not token:
            return False
        with self._lock:
            return self.digest(token) in self._digests


class ProductState:
    def __init__(self):
        self.started_at = _now()
        self.started_commit = _git("rev-parse", "HEAD")
        self.started_branch = _git("branch", "--show-current") or "unknown"

    def view(self) -> dict:
        head = _git("rev-parse", "HEAD") or self.started_commit
        branch = _git("branch", "--show-current") or self.started_branch
        return {
            "schema": "orion-v3.product-status/1",
            "mode": "normal",
            "run_state": "idle",
            "result": "",
            "activity": "ORION V3 product UI online",
            "repo": "Sadusor/ORION-V3",
            "branch": branch,
            "checkout_sha": head,
            "runner_sha": self.started_commit,
            "runner_cwd": str(ROOT),
            "pending_sha": "",
            "approved_sha": "",
            "last_tested_sha": "",
            "last_result": "",
            "last_output": "",
            "last_error": "",
            "runner_log": "",
            "evidence_path": "",
            "publish_state": "not_configured",
            "published_commit": "",
            "attempt": 0,
            "active_project_link_id": "orion-v3",
            "project_links": [{
                "link_id": "orion-v3",
                "label": "ORION V3",
                "repo": "Sadusor/ORION-V3",
                "branch": branch,
                "scope": str(ROOT),
                "state": "active",
            }],
            "local_hand_lane": LOCAL_BRAIN.view(),
            "manual_lane": {
                "run_state": "idle",
                "result": "",
                "activity": "Engineering Manual is owned by TheHands, not ORION product UI",
            },
            "dispatch_sessions": [],
            "dispatch_tasks": [],
            "reviewer": {
                "state": "idle",
                "run_id": "",
                "evidence_path": "",
                "catalog": {"models": []},
                "reviewers": {},
            },
            "provider_vault": {"providers": []},
            "local_brain_default_model": LOCAL_BRAIN.default_model(),
            "update_status": {"phase": "", "detail": "", "error": "", "target_sha": ""},
        }


AUTH: Auth
STATE = ProductState()


class Handler(BaseHTTPRequestHandler):
    server_version = "ORION-V3-Product/0.1"

    def log_message(self, fmt, *args):
        print("[ORION-UI] " + (fmt % args), flush=True)

    def _json(self, status: int, payload: dict):
        body = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def _token(self) -> str:
        return self.headers.get("X-Orion-Token", "").strip()

    def _is_local_pc(self) -> bool:
        host = str(self.client_address[0] if self.client_address else "")
        return host in {"127.0.0.1", "::1"} or host.startswith("127.")

    def _require_auth(self) -> bool:
        # The PC-local ORION console is trusted locally. Remote/phone clients must pair.
        if self._is_local_pc() or AUTH.valid(self._token()):
            return True
        self._json(401, {"ok": False, "error": "pairing required"})
        return False

    def _serve_ui(self, path: str):
        if path in ("/v3", "/v3/"):
            rel = "index.html"
        else:
            rel = unquote(path[len("/v3/"):])
        rel = rel.replace("\\", "/").lstrip("/")
        if not rel or rel.startswith(".") or ".." in pathlib.PurePosixPath(rel).parts:
            self.send_error(404)
            return
        if rel in DENIED_TOP or rel in DENIED_FILES or any(part in DENIED_DIRS for part in pathlib.PurePosixPath(rel).parts):
            self.send_error(404)
            return
        target = (UI_ROOT / rel).resolve()
        try:
            target.relative_to(UI_ROOT.resolve())
        except ValueError:
            self.send_error(404)
            return
        if not target.is_file() or target.suffix.lower() not in ALLOWED_EXT:
            self.send_error(404)
            return
        body = target.read_bytes()
        if rel == "index.html" and self._is_local_pc():
            marker = b"</head>"
            injected = (
                "<script>window.ORION_PC_PAIR_CODE="
                + json.dumps(AUTH.pair_code)
                + ";</script></head>"
            ).encode("utf-8")
            body = body.replace(marker, injected, 1)
        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if target.suffix == ".js":
            ctype = "application/javascript; charset=utf-8"
        elif target.suffix == ".css":
            ctype = "text/css; charset=utf-8"
        elif target.suffix == ".html":
            ctype = "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self.send_response(302)
            self.send_header("Location", "/v3/")
            self.end_headers()
            return
        if path.startswith("/v3"):
            return self._serve_ui(path)
        if path == "/api/health":
            return self._json(200, {
                "ok": True,
                "service": "ORION-V3 product UI",
                "schema": "orion-v3.health/1",
                "started_at": STATE.started_at,
                "running_commit": STATE.started_commit,
                "branch": STATE.started_branch,
            })
        if not self._require_auth():
            return
        if path == "/api/status":
            return self._json(200, STATE.view())
        if path == "/api/project-links":
            v = STATE.view()
            return self._json(200, {"project_links": v["project_links"], "active_project_link_id": v["active_project_link_id"]})
        if path == "/api/work-exchange/latest":
            return self._json(200, {"items": [], "status": "not_connected"})
        if path == "/api/memory/candidates":
            return self._json(200, {"candidates": []})
        if path == "/api/reviewers/latest":
            return self._json(200, STATE.view()["reviewer"])
        if path == "/api/providers":
            return self._json(200, STATE.view()["provider_vault"])
        self.send_error(404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/pair":
            try:
                token = AUTH.pair(str(self._read_json().get("code", "")))
                return self._json(200, {"ok": True, "token": token})
            except Exception as exc:
                return self._json(400, {"ok": False, "error": str(exc)})
        if not self._require_auth():
            return
        if path == "/api/local-hand/draft":
            try:
                body = self._read_json()
                LOCAL_BRAIN.start(
                    str(body.get("goal", "")),
                    str(body.get("model", "")),
                )
                return self._json(202, STATE.view())
            except LocalBrainError as exc:
                return self._json(409, {"ok": False, "error": str(exc), "route": path})
            except Exception as exc:
                return self._json(500, {"ok": False, "error": str(exc), "route": path})
        # Registered frontend routes that are not yet real backend capabilities fail truthfully.
        known = {
            "/api/local-hand/draft", "/api/local-hand/revise", "/api/local-hand/run", "/api/local-hand/stop",
            "/api/run/start", "/api/run/stop", "/api/session/start", "/api/session/stop", "/api/reviewers/stop",
            "/api/github/check", "/api/github/sync", "/api/mode/enter", "/api/mode/pause", "/api/mode/resume",
            "/api/mode/exit", "/api/project-links/refresh", "/api/project-links/activate",
            "/api/reviewers/catalog/refresh", "/api/providers/test", "/api/providers/enabled",
            "/api/system/update-restart", "/api/manual/stop",
        }
        if path in known:
            return self._json(409, {
                "ok": False,
                "error": "ORION V3 capability not connected in Phase A product server",
                "route": path,
            })
        self.send_error(404)


def main() -> int:
    global AUTH
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8890)
    ap.add_argument("--pair-code", default="")
    args = ap.parse_args()
    code = args.pair_code.strip() or f"{secrets.randbelow(1_000_000):06d}"
    if len(code) != 6 or not code.isdigit():
        raise SystemExit("--pair-code must be exactly 6 digits")
    AUTH = Auth(code)
    PID_FILE.write_text(str(os.getpid()), encoding="ascii")
    print("ORION_V3_PRODUCT> ONLINE", flush=True)
    print(f"ORION_V3_PAIR_CODE> {code}", flush=True)
    print(f"ORION_V3_PC> http://127.0.0.1:{args.port}/v3/", flush=True)
    print(f"ORION_V3_PHONE> http://<PC-private-IP>:{args.port}/v3/", flush=True)
    try:
        ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
    finally:
        try:
            PID_FILE.unlink(missing_ok=True)
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
