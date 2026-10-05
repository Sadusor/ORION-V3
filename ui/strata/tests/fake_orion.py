"""A fake ORION for tests. Mirrors the REAL server.py contract (X-Orion-Token, /api/pair {code}->{token}, 409 {error}, Controller.view() shape,
POST routes returning view()) and serves the frontend through the REAL strata_static.resolve(). Adds /__ctl/* to switch failure modes.
NOT part of the product; used by tests/bridge and tests/browser only."""
import importlib.util, json, pathlib, secrets, socket, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HERE = pathlib.Path(__file__).resolve().parent
UIROOT = HERE.parent
_spec = importlib.util.spec_from_file_location("strata_static", HERE / "support" / "strata_static.py")
strata_static = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(strata_static)

NOW = lambda: time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
def lane(**k):
    d = {"run_state": "idle", "result": None, "output": "", "error": "", "activity": "idle", "goal": "", "brain_state": "idle", "brain_phase": "idle", "brain_next_script": "",
         "brain_next_capability": "", "brain_next_url": "", "brain_error": "", "brain_preflight": "not-run", "brain_preflight_reason": "", "brain_quality_state": "not-run",
         "brain_quality_reason": "", "brain_quality_approved_sha256": "", "execution_kind": "", "execution_action": "", "brain_started_utc": None, "started_utc": None, "finished_utc": None}
    d.update(k); return d
READY = dict(brain_state="ready", brain_phase="complete", brain_quality_state="pass", brain_preflight="pass")
SCRIPT = "Get-ChildItem . | Select Name\nWrite-Output done"
OUT = json.dumps({"status": "launch_requested", "pid": 4242, "browser": "chrome", "host": "www.google.com", "url": "https://www.google.com/search?q=x",
                  "proof": "browser launch request accepted by the operating system; page render/content not independently verified"})
SCEN = {
    "idle": lambda: lane(),
    "drafting": lambda: lane(goal="g", brain_state="running", brain_phase="drafting", brain_started_utc=NOW()),
    "verifying": lambda: lane(goal="g", brain_state="running", brain_phase="verifying", brain_started_utc=NOW()),
    "acting": lambda: lane(goal="g", **READY, run_state="running", started_utc=NOW(), execution_kind="capability", execution_action="open_web_url"),
    "acting_ps": lambda: lane(goal="g", **READY, run_state="running", started_utc=NOW(), execution_kind="powershell", execution_action="PowerShell"),
    "pass": lambda: lane(goal="g", **READY, run_state="passed", result="PASS", started_utc=NOW(), finished_utc=NOW(), output=OUT, execution_kind="capability", execution_action="open_web_url"),
    "approval": lambda: lane(goal="list", **READY, brain_next_script=SCRIPT, brain_conclusion="Read-only listing.", brain_quality_approved_sha256="ab" * 32, brain_started_utc=NOW()),
    "blocked": lambda: lane(goal="g", brain_state="blocked", brain_phase="complete", brain_preflight="blocked", brain_preflight_reason="scope", brain_error="PREFLIGHT BLOCKED: scope", brain_started_utc=NOW()),
    "verif_failed": lambda: lane(goal="g", brain_state="blocked", brain_phase="complete", brain_preflight="pass", brain_quality_state="blocked", brain_quality_reason="unsupported", brain_error="QUALITY BLOCKED", brain_started_utc=NOW()),
    "run_failed": lambda: lane(goal="g", **READY, run_state="failed", result="FAIL", started_utc=NOW(), finished_utc=NOW(), exit_code=1, execution_kind="powershell", execution_action="PowerShell", output="1 failed"),
}

class FakeOrion:
    def __init__(self):
        self.token = "t-" + secrets.token_hex(8); self.code = "123456"
        self.mode = "ok"; self.scenario = "idle"; self.timed_goal = None; self.timed_t0 = 0
        self.log = []; self.srv = None
    def reset(self): self.mode = "ok"; self.scenario = "idle"; self.timed_goal = None; self.log.clear(); self.extra = {}
    extra = {}
    def lane(self):
        if self.timed_goal is not None:               # server-side lifecycle after a draft POST, like the real worker threads
            t = time.time() - self.timed_t0
            for lim, name in ((1.2, "drafting"), (2.4, "verifying"), (3.6, "acting"), (1e9, "pass")):
                if t < lim: return SCEN[name]()
        return SCEN[self.scenario]()
    def view(self):
        v = {"mode": "active", "run_state": "idle", "pending_sha": None, "activity": "idle", "checkout_sha": "abc123", "repo": "Sadusor/Orion", "branch": "agent/x", "project_links": [],
             "dispatch_sessions": [], "dispatch_tasks": [], "provider_vault": {"providers": []}, "update_status": {}, "local_brain_default_model": "qwen35-9b-orion:latest",
             "reviewer": {"state": "idle", "catalog": {"models": [{"reviewer_id": "r1", "provider": "ollama", "available": True, "model": "qwen35-9b-orion:latest"}]}},
             "manual_lane": lane(), "local_hand_lane": self.lane()}
        v.update(self.extra); return v
    def start(self):
        outer = self
        class H(BaseHTTPRequestHandler):
            def log_message(self, *a): pass
            def auth(self): return self.headers.get("X-Orion-Token", "") == outer.token
            def js(self, c, d, ct="application/json"):
                b = d if isinstance(d, bytes) else json.dumps(d).encode()
                self.send_response(c); self.send_header("Content-Type", ct); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
            def status_body(self):
                m = outer.mode
                if m == "drop": self.request.shutdown(socket.SHUT_RDWR); self.request.close(); return None
                if m == "hang": time.sleep(5)
                if m == "html": return self.js(200, b"<html>proxy error</html>", "text/html")
                if m == "array": return self.js(200, [])
                if m == "partial": return self.js(200, {"run_state": "idle"})
                if m == "truncated": return self.js(200, b'{"run_state":"idle","local_hand_lane":{', "application/json")
                if m == "e500": return self.js(500, {"error": "internal boom"})
                return self.js(200, outer.view())
            def do_GET(self):
                p = urlparse(self.path).path
                if p.startswith("/__ctl/"):
                    a = p[len("/__ctl/"):].split("/")
                    if a[0] == "mode": outer.mode = a[1]
                    elif a[0] == "scenario": outer.scenario = a[1]; outer.timed_goal = None
                    elif a[0] == "reset": outer.reset()
                    elif a[0] == "extra": outer.extra = json.loads(bytes.fromhex(a[1]).decode())
                    elif a[0] == "log": return self.js(200, outer.log)
                    return self.js(200, {"ok": True})
                if strata_static.is_strata_path(p):
                    c, ct, b, loc = strata_static.resolve(p)
                    self.send_response(c); self.send_header("Content-Type", ct)
                    if loc: self.send_header("Location", loc)
                    self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b); return
                if p in ("/", "/operator"): return self.js(200, b"<html>LEGACY " + p.encode() + b"</html>", "text/html")
                if not self.auth(): return self.js(401, {"error": "Unauthorized"})
                if p == "/api/status": return self.status_body()
                if p == "/api/memory/candidates":
                    return self.js(200, {"candidates": [{"candidate_id": "c1", "content": "Prefers dark UI <b>x</b>", "classification": "PREFERENCE", "source_actor": "t", "submitted_at": NOW(), "decision": "defer", "confidence": 0.8}]})
                self.js(404, {"error": "Not found"})
            def do_POST(self):
                n = min(int(self.headers.get("Content-Length", "0") or 0), 65536); body = json.loads(self.rfile.read(n) or b"{}"); p = urlparse(self.path).path
                if p == "/api/pair": return self.js(200, {"token": outer.token}) if body.get("code") == outer.code else self.js(409, {"error": "Invalid pairing code."})
                if not self.auth(): return self.js(401, {"error": "Unauthorized"})
                outer.log.append({"path": p, "body": body})
                if outer.mode == "hang_post": time.sleep(3)
                if p == "/api/local-hand/draft":
                    gl = str(body.get("goal", "")).strip()
                    if not gl: return self.js(409, {"error": "Enter a goal for the local brain first."})
                    if gl.lower().startswith("script"): outer.scenario = "approval"; outer.timed_goal = None
                    else: outer.timed_goal = gl; outer.timed_t0 = time.time()
                    return self.js(200, outer.view())
                if p == "/api/local-hand/run":
                    if body.get("script") != SCRIPT: return self.js(409, {"error": "QUALITY BLOCKED: script changed"})
                    outer.scenario = "acting_ps"; outer.timed_goal = None; return self.js(200, outer.view())
                if p == "/api/local-hand/stop": outer.scenario = "idle"; return self.js(200, outer.view())
                if p == "/api/run/stop": return self.js(409, {"error": "No active run."})
                self.js(404, {"error": "Not found"})
        class Q(ThreadingHTTPServer):
            def handle_error(self, *a): pass          # clients abort hung/dropped requests on purpose
        self.srv = Q(("127.0.0.1", 0), H); self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start(); self.base = f"http://127.0.0.1:{self.port}"; return self
    def stop(self): self.srv.shutdown(); self.srv.server_close()
