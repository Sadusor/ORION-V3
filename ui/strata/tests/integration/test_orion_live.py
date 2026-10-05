"""ORION INTEGRATION TEST against a RUNNING ORION (read-only; sends no commands):
   python tests/integration/test_orion_live.py --base http://PC-IP:8766 --token <orionToken>      (token optional: skips the authenticated checks)
Run it after applying the patch and restarting ORION."""
import argparse, http.client, json, sys
from urllib.parse import urlparse
ap = argparse.ArgumentParser(); ap.add_argument("--base", required=True); ap.add_argument("--token", default=""); a = ap.parse_args()
u = urlparse(a.base); fails = 0
def ok(c, m):
    global fails; fails += (not c); print(("  ok   " if c else "  FAIL ") + m)
def get(p, tok=None):
    c = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=8); c.request("GET", p, headers={"X-Orion-Token": tok} if tok else {}); r = c.getresponse(); d = r.read(); c.close(); return r.status, dict(r.getheaders()), d
print("live ORION (read-only)")
ok(get("/")[0] == 200, "legacy / is up"); ok(get("/operator")[0] == 200, "legacy /operator is up")
s, h, b = get("/v3/"); ok(s == 200 and b"<title>ORION</title>" in b, "/v3/ serves V3 (live page)")
ok(get("/v3/demo.html")[0] == 404 and get("/v3/bridge/mock-bridge.js")[0] == 404, "live ORION does not serve demo/mock files")
ok(get("/v3/../server.py")[0] == 404 and get("/v3/%2e%2e/server.py")[0] == 404, "traversal rejected")
ok(get("/api/status")[0] == 401, "/api/status requires the token")
if a.token:
    s, h, b = get("/api/status", a.token); d = json.loads(b) if s == 200 else {}
    ok(s == 200, "authenticated /api/status = 200")
    for k in ["run_state", "mode", "local_hand_lane", "manual_lane", "pending_sha", "project_links", "dispatch_sessions", "provider_vault", "reviewer", "local_brain_default_model"]:
        ok(k in d, f"status contains '{k}'")
    for k in ["run_state", "result", "output", "activity", "goal", "brain_state", "brain_phase", "brain_quality_state", "brain_preflight", "brain_next_script", "brain_next_capability", "execution_kind"]:
        ok(k in d.get("local_hand_lane", {}), f"local_hand_lane contains '{k}'")
    s, h, b = get("/api/memory/candidates", a.token); ok(s == 200 and "candidates" in json.loads(b), "/api/memory/candidates -> {candidates:[…]}")
print("live ORION:", "ALL PASS" if not fails else f"{fails} FAILED"); sys.exit(1 if fails else 0)
