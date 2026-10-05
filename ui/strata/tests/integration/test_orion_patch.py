"""ORION INTEGRATION TEST (needs a copy of the ORION repo):  python tests/run_tests.py --orion-root <repo>
Applies the minimal patch to a TEMP COPY of your server.py, then runs ORION's REAL (patched) Handler over HTTP and proves V3 coexists with legacy
and no existing boundary changed. Modules your repo lacks at import time are stubbed ONLY inside the temp copy (never in your repo)."""
import argparse, difflib, http.client, importlib.util, json, pathlib, shutil, subprocess, sys, tempfile, threading
from http.server import ThreadingHTTPServer
HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parent.parent.parent.parent
ap = argparse.ArgumentParser(); ap.add_argument("--orion-root", required=True); a = ap.parse_args()
src_dir = pathlib.Path(a.orion_root) / "spikes" / "coding_mode_github_loop"
if not (src_dir / "server.py").exists():
    print(f"SKIPPED: {src_dir/'server.py'} not found"); sys.exit(0)
fails = 0
def ok(c, m):
    global fails; fails += (not c); print(("  ok   " if c else "  FAIL ") + m)
print("ORION integration (patched real Handler)")
tmp = pathlib.Path(tempfile.mkdtemp()); work = tmp / "spikes" / "coding_mode_github_loop"
shutil.copytree(src_dir, work); shutil.copytree(PKG / "ui", tmp / "ui")
shutil.copy(PKG / "spikes/coding_mode_github_loop/strata_static.py", work / "strata_static.py")
orig = (work / "server.py").read_bytes()
for mod, body in {"dispatch_runtime": "class DispatchRuntime:\n    def __init__(s,*a,**k): pass\n", "provider_vault": "class ProviderVault:\n    def __init__(s,*a,**k): pass\n",
                  "reviewer_connector": "class ReviewerConnector:\n    def __init__(s,*a,**k): pass\n", "protected_baseline": "def check_path_change(*a,**k): return {}\ndef check_script_change(*a,**k): return {}\n"}.items():
    if not (work / f"{mod}.py").exists(): (work / f"{mod}.py").write_text(body)          # stub only if absent from the copy
def run(*args): return subprocess.run([sys.executable, str(PKG / "patches/apply_patch.py"), "--server", str(work / "server.py"), *args], capture_output=True, text=True)
r = run("--check"); ok("not applied" in r.stdout, "pristine server.py: V3 hooks not applied")
r = run(); ok(r.returncode == 0 and "Applied" in r.stdout, "apply_patch.py applies cleanly")
r = run(); ok("Already applied" in r.stdout, "apply is idempotent")
patched = (work / "server.py").read_bytes()
d = list(difflib.unified_diff(orig.decode().splitlines(), patched.decode().splitlines(), lineterm="", n=0))
added = [l for l in d if l.startswith("+") and not l.startswith("+++")]; removed = [l for l in d if l.startswith("-") and not l.startswith("---")]
ok(len(removed) == 0 and 5 <= len(added) <= 9, f"patch is purely additive: {len(added)} lines added, {len(removed)} removed")
ok(sum("strata_static" in l for l in added) == 3 and all(("strata" in l.lower()) or l[1:].strip() == "" for l in added), "every added line belongs to the V3 import / route / markers")
ok(subprocess.run([sys.executable, "-m", "py_compile", str(work / "server.py")]).returncode == 0, "patched server.py compiles")
sys.path[:0] = [str(work)]
spec = importlib.util.spec_from_file_location("orion_server_patched", work / "server.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
class Ctl:
    token = "T0KEN"
    def view(self): return {"run_state": "idle", "local_hand_lane": {}}
m.Handler.controller = Ctl()
srv = ThreadingHTTPServer(("127.0.0.1", 0), m.Handler); port = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
def get(p, h=None, method="GET", body=None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5); c.request(method, p, body, h or {}); r = c.getresponse(); data = r.read(); out = (r.status, dict(r.getheaders()), data); c.close(); return out
s, h, b = get("/");          ok(s == 200 and b == m.HTML.encode(), "legacy / (Remote V1) is served byte-for-byte unchanged")
s, h, b = get("/operator");  ok(s == 200 and b == m.OPERATOR_HTML.encode(), "legacy /operator is served byte-for-byte unchanged")
s, h, b = get("/v3");        ok(s == 301 and h.get("Location") == "/v3/", "/v3 redirects to /v3/")
s, h, b = get("/v3/");       ok(s == 200 and b"<title>ORION</title>" in b and "text/html" in h.get("Content-Type", ""), "/v3/ serves the V3 live page")
for p, t in [("/v3/config.js", "javascript"), ("/v3/bridge/real-bridge.js", "javascript"), ("/v3/styles/strata.css", "css"), ("/v3/shell/shell.js", "javascript")]:
    s, h, b = get(p); ok(s == 200 and t in h.get("Content-Type", ""), f"{p} -> 200 {t}")
s, h, b = get("/v3/index.html"); ok(h.get("Cache-Control", "").startswith("no-store") and h.get("X-Content-Type-Options") == "nosniff", "static assets: no-store + nosniff")
for p in ["/v3/../server.py", "/v3/%2e%2e/server.py", "/v3/..%5cserver.py", "/v3/%2e%2e%2fspikes/coding_mode_github_loop/server.py", "/v3//etc/passwd", "/v3/C:/Windows/win.ini",
          "/v3/demo.html", "/v3/bridge/mock-bridge.js", "/v3/tests/harness.js", "/v3/tools/build-demo.py", "/v3/README.md", "/v3/.git/config", "/v3/styles/", "/v3/nope.js"]:
    s, h, b = get(p); ok(s == 404 and b"def " not in b and b"MockBridge" not in b, f"{p} -> 404")
s, h, b = get("/api/status"); ok(s == 401, "GET /api/status WITHOUT token is still 401 (auth untouched)")
s, h, b = get("/api/status", {"X-Orion-Token": "T0KEN"}); ok(s == 200 and json.loads(b).get("run_state") == "idle", "GET /api/status with token still returns the controller view")
s, h, b = get("/api/status", {"X-Orion-Token": "wrong"}); ok(s == 401, "wrong token still 401")
for p in ["/api/local-hand/run", "/api/run/start", "/api/system/update-restart", "/api/local-hand/draft"]:
    s, h, b = get(p, {"Content-Type": "application/json"}, "POST", "{}"); ok(s == 401, f"POST {p} WITHOUT token is still 401")
s, h, b = get("/v3/api/status", {"X-Orion-Token": "T0KEN"}); ok(s == 404, "the /v3 mount exposes no API")
r = run("--revert"); ok(r.returncode == 0 and (work / "server.py").read_bytes() == orig, "--revert restores server.py byte-identical to the original")
srv.shutdown(); shutil.rmtree(tmp, ignore_errors=True)
print(f"ORION integration: {'ALL PASS' if not fails else str(fails) + ' FAILED'}"); sys.exit(1 if fails else 0)
