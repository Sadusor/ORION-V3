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
from urllib.parse import parse_qs, unquote, urlparse

from modules.streaming_brain_pipeline import StreamingBrainPipeline
from modules.local_brain import LocalBrainError
from modules.chat_history import ChatHistoryStore
from modules.memory_retrieval import MemoryRetrievalModule
from modules.canonical_memory_retrieval_foundation import CanonicalMemoryRetrievalFoundation
from modules.canonical_memory_integration import CanonicalMemoryIntegratedBrainPipeline
from modules.memory_candidate_queue import CanonicalMemoryCandidateQueue, MemoryCandidateError
from modules.memory_review_promotion import CanonicalMemoryReviewPromotion, MemoryReviewError
from modules.update_manager import UpdateError, UpdateManager

ROOT = pathlib.Path(__file__).resolve().parents[2]
UI_ROOT = ROOT / "ui" / "strata"
STATE_ROOT = pathlib.Path(os.environ.get("LOCALAPPDATA", str(ROOT / ".local"))) / "ORION-V3"
STATE_ROOT.mkdir(parents=True, exist_ok=True)
PID_FILE = STATE_ROOT / "product-ui.pid"
DEVICES_FILE = STATE_ROOT / "devices.json"
APK_FILE = ROOT / "dist" / "ORION-V3-debug.apk"

CHAT_HISTORY = ChatHistoryStore(STATE_ROOT / "chat_history.sqlite3")
MEMORY_RETRIEVAL = MemoryRetrievalModule(CHAT_HISTORY)
MEMORY_CANDIDATES = CanonicalMemoryCandidateQueue(
    STATE_ROOT / "memory_candidates.sqlite3",
    CHAT_HISTORY,
)
MEMORY_REVIEW = CanonicalMemoryReviewPromotion(
    STATE_ROOT / "canonical_memory.sqlite3",
    MEMORY_CANDIDATES,
)
CANONICAL_MEMORY_RETRIEVAL = CanonicalMemoryRetrievalFoundation(
    MEMORY_REVIEW,
    STATE_ROOT / "canonical_memory_supersession.sqlite3",
    MEMORY_CANDIDATES,
)
LOCAL_BRAIN = CanonicalMemoryIntegratedBrainPipeline(
    brain=StreamingBrainPipeline(),
    recall=MEMORY_RETRIEVAL,
    durable=CANONICAL_MEMORY_RETRIEVAL,
)
UPDATE_MANAGER = UpdateManager(ROOT, STATE_ROOT)

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
    def __init__(self, pair_code: str, devices_path: pathlib.Path):
        self.pair_code = pair_code
        self.pair_expires = time.time() + 3600
        self.devices_path = pathlib.Path(devices_path)
        self._digests: set[str] = set()
        self._lock = threading.Lock()
        self._load_devices()

    @staticmethod
    def digest(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _load_devices(self) -> None:
        try:
            doc = json.loads(self.devices_path.read_text(encoding="utf-8-sig"))
            if doc.get("schema") == "orion-v3.devices/1":
                self._digests = {
                    str(x.get("token_sha256") or "")
                    for x in doc.get("devices", [])
                    if str(x.get("token_sha256") or "")
                }
        except Exception:
            self._digests = set()

    def _save_devices(self) -> None:
        self.devices_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": "orion-v3.devices/1",
            "devices": [
                {"token_sha256": digest}
                for digest in sorted(self._digests)
            ],
        }
        temp = self.devices_path.with_suffix(".json.tmp")
        temp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temp.replace(self.devices_path)

    def pair(self, code: str) -> str:
        if time.time() > self.pair_expires:
            raise RuntimeError("pairing code expired")
        if str(code).strip() != self.pair_code:
            raise RuntimeError("invalid pairing code")
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._digests.add(self.digest(token))
            self._save_devices()
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
            "memory_retrieval": MEMORY_RETRIEVAL.last(),
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

    def _require_owner_token(self) -> bool:
        # Durable canonical-memory decisions are stricter than ordinary local UI
        # reads/commands: even loopback must present a paired owner token.
        if AUTH.valid(self._token()):
            return True
        self._json(401, {"ok": False, "error": "paired owner token required"})
        return False

    def _owner_actor_fingerprint(self) -> str:
        token = self._token()
        return "paired:" + AUTH.digest(token)[:16] if token else ""

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
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query, keep_blank_values=True)
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
        if path == "/apk":
            if not self._require_auth():
                return
            if not APK_FILE.is_file():
                return self._json(404, {"ok": False, "error": "ORION Android APK has not been built yet."})
            body = APK_FILE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.android.package-archive")
            self.send_header("Content-Disposition", 'attachment; filename="ORION-V3-debug.apk"')
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if not self._require_auth():
            return
        if path == "/api/status":
            return self._json(200, STATE.view())
        if path == "/api/models":
            try:
                models = LOCAL_BRAIN.local_brain._available_models()
            except Exception:
                models = LOCAL_BRAIN.cached_models()
            return self._json(200, {
                "models": models,
                "default_model": LOCAL_BRAIN.default_model(),
            })
        if path == "/api/update/status":
            return self._json(200, UPDATE_MANAGER.status())
        if path == "/api/update/check":
            return self._json(200, UPDATE_MANAGER.check())
        if path == "/api/chat-history":
            return self._json(200, CHAT_HISTORY.snapshot())
        if path == "/api/project-links":
            v = STATE.view()
            return self._json(200, {"project_links": v["project_links"], "active_project_link_id": v["active_project_link_id"]})
        if path == "/api/work-exchange/latest":
            return self._json(200, {"items": [], "status": "not_connected"})
        if path == "/api/memory/candidates":
            return self._json(200, MEMORY_REVIEW.candidates_view())
        if path == "/api/memory/canonical":
            return self._json(200, MEMORY_REVIEW.list_canonical())
        if path == "/api/memory/decisions":
            return self._json(200, MEMORY_REVIEW.decisions())
        if path == "/api/memory/search":
            try:
                raw_limit = str((query.get("limit") or ["6"])[0] or "6")
                result = MEMORY_RETRIEVAL.retrieve(
                    str((query.get("q") or [""])[0]),
                    conversation_id=str((query.get("conversation_id") or [""])[0]),
                    project_id=(
                        str((query.get("project_id") or [""])[0])
                        if "project_id" in query
                        else None
                    ),
                    limit=int(raw_limit),
                )
                return self._json(200, result)
            except (TypeError, ValueError) as exc:
                return self._json(400, {"ok": False, "error": str(exc), "route": path})
            except Exception as exc:
                return self._json(500, {"ok": False, "error": str(exc), "route": path})
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

        # Canonical-memory review is a durable write boundary. Unlike ordinary
        # V3 routes, loopback is not implicitly trusted here.
        if path in {"/api/memory/review-ticket", "/api/memory/decision"}:
            if not self._require_owner_token():
                return
        elif not self._require_auth():
            return
        if path == "/api/chat-history/sync":
            try:
                return self._json(200, CHAT_HISTORY.sync(self._read_json()))
            except Exception as exc:
                return self._json(500, {"ok": False, "error": str(exc), "route": path})
        if path == "/api/memory/candidate":
            try:
                body = self._read_json()
                result = MEMORY_CANDIDATES.enqueue_chat_message(
                    conversation_id=str(body.get("conversation_id", "")),
                    message_id=str(body.get("message_id", "")),
                    project_id=(
                        str(body.get("project_id", ""))
                        if "project_id" in body
                        else None
                    ),
                    owner_scope=str(body.get("owner_scope", "owner:primary")),
                )
                return self._json(201 if result.get("created") else 200, result)
            except MemoryCandidateError as exc:
                return self._json(409, {"ok": False, "error": str(exc), "route": path})
            except Exception as exc:
                return self._json(500, {"ok": False, "error": str(exc), "route": path})
        if path == "/api/memory/review-ticket":
            try:
                body = self._read_json()
                result = MEMORY_REVIEW.prepare_review(
                    candidate_id=str(body.get("candidate_id", "")),
                    decision=str(body.get("decision", "")),
                    expected_content_sha256=str(body.get("expected_content_sha256", "")),
                    owner_scope=str(body.get("owner_scope", "owner:primary")),
                    actor_fingerprint=self._owner_actor_fingerprint(),
                )
                return self._json(200, result)
            except MemoryReviewError as exc:
                return self._json(409, {"ok": False, "error": str(exc), "route": path})
            except Exception as exc:
                return self._json(500, {"ok": False, "error": str(exc), "route": path})
        if path == "/api/memory/decision":
            try:
                body = self._read_json()
                result = MEMORY_REVIEW.decide(
                    candidate_id=str(body.get("candidate_id", "")),
                    decision=str(body.get("decision", "")),
                    expected_content_sha256=str(body.get("expected_content_sha256", "")),
                    review_token=str(body.get("review_token", "")),
                    owner_scope=str(body.get("owner_scope", "owner:primary")),
                    actor_fingerprint=self._owner_actor_fingerprint(),
                )
                return self._json(201 if result.get("created") else 200, result)
            except MemoryReviewError as exc:
                return self._json(409, {"ok": False, "error": str(exc), "route": path})
            except Exception as exc:
                return self._json(500, {"ok": False, "error": str(exc), "route": path})
        if path == "/api/update/main":
            try:
                result = UPDATE_MANAGER.apply(STATE.started_commit)
                return self._json(202 if result.get("restart_scheduled") else 200, {"ok": True, "update": result})
            except UpdateError as exc:
                return self._json(409, {"ok": False, "error": str(exc), "route": path})
            except Exception as exc:
                return self._json(500, {"ok": False, "error": str(exc), "route": path})
        if path == "/api/local-hand/draft":
            try:
                body = self._read_json()
                LOCAL_BRAIN.start(
                    str(body.get("goal", "")),
                    str(body.get("model", "")),
                    memory_query=str(body.get("memory_query", "")),
                    conversation_id=str(body.get("conversation_id", "")),
                    project_id=(
                        str(body.get("project_id", ""))
                        if "project_id" in body
                        else None
                    ),
                    owner_message=str(body.get("owner_message", "")),
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
    AUTH = Auth(code, DEVICES_FILE)
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
