"""strata_static.py: serves only allowlisted files under ui/strata; rejects traversal, unsupported types, dotfiles, symlink escapes, mock/demo. Pure unit test."""
import importlib.util, pathlib, sys, tempfile, shutil
HERE = pathlib.Path(__file__).resolve().parent
UIROOT = HERE.parent.parent
spec = importlib.util.spec_from_file_location("strata_static", HERE.parent / "support" / "strata_static.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
fails = 0
def chk(path, want, why="", root=None):
    global fails
    code, ctype, body, loc = m.resolve(path, root)
    good = code == want and not (b"SECRET" in body)
    fails += (not good)
    print(("  ok   " if good else "  FAIL ") + path.ljust(58) + str(code) + (" " + why if why else ""))
    return code, ctype, body, loc
print("static serving")
tmp = pathlib.Path(tempfile.mkdtemp()); root = tmp / "ui" / "strata"; shutil.copytree(UIROOT, root)
(tmp / "ui" / "secret.txt").write_text("SECRET"); (tmp / "config.json").write_text('{"SECRET":1}')
try: (root / "styles" / "evil.css").symlink_to(tmp / "ui" / "secret.txt")
except OSError: print("  (symlink test skipped on this platform)")
(root / ".hidden.js").write_text("x"); (root / "note.md").write_text("x"); (root / "run.py").write_text("x"); (root / "data.exe").write_bytes(b"x")
c = lambda p, w, y="": chk(p, w, y, root)
code, ct, body, loc = c("/v3", 301); assert loc == "/v3/", loc
c("/v3/", 200); assert m.resolve("/v3/", root)[1].startswith("text/html")
c("/v3/index.html", 200); c("/v3/config.js", 200); c("/v3/bridge/real-bridge.js", 200); c("/v3/styles/strata.css", 200); c("/v3/shell/shell.js", 200)
print("  -- path traversal / escapes")
for p in ["/v3/../spikes/coding_mode_github_loop/strata_static.py", "/v3/%2e%2e/%2e%2e/config.json", "/v3/..%5c..%5cconfig.json", "/v3/%2e%2e%2fsecret.txt", "/v3/styles/../../../config.json",
          "/v3/bridge/..%2f..%2f..%2fconfig.json", "/v3//etc/passwd", "/v3/C:/Windows/win.ini", "/v3/%00", "/v3/styles/evil.css", "/v3/styles/", "/v3/styles", "/v3/."]:
    c(p, 404)
print("  -- unsupported file types / hidden / denied")
for p in ["/v3/README.md", "/v3/note.md", "/v3/run.py", "/v3/data.exe", "/v3/.hidden.js", "/v3/tools/build-demo.py", "/v3/tests/harness.js", "/v3/tests/unit/test_state.js", "/v3/docs/x.html",
          "/v3/demo.html", "/v3/bridge/mock-bridge.js", "/v3/missing.js", "/api/status", "/v3x/index.html", "/"]:
    c(p, 404)
for tail in ["", "?x=1"]: pass
shutil.rmtree(tmp)
# real handler-shaped call
class W:
    def __init__(s): s.b = b""
    def write(s, d): s.b += d
class H:
    def __init__(s): s.h = []; s.wfile = W(); s.code = None
    def send_response(s, c): s.code = c
    def send_header(s, k, v): s.h.append((k, v))
    def end_headers(s): pass
h = H(); m.serve(h, "/v3/index.html", UIROOT)
ok = h.code == 200 and ("Cache-Control", m.NO_CACHE) in h.h and ("X-Content-Type-Options", "nosniff") in h.h and b"<title>ORION</title>" in h.wfile.b
print(("  ok   " if ok else "  FAIL ") + "serve(): 200 + no-store + nosniff + body"); fails += (not ok)
print(f"static serving: {'ALL PASS' if not fails else str(fails) + ' FAILED'}"); sys.exit(1 if fails else 0)
