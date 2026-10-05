#!/usr/bin/env python3
"""Single entry point.   python tests/run_tests.py [--orion-root <ORION repo>] [--browser] [--no-browser] [--shots DIR]
 UNIT TESTS (always)         need only node + python3: assets, normalize, state reducer, routes/safety, boot (live+mock, malformed/offline/reconnect), static serving
 BRIDGE TESTS (always)       real bridge over real HTTP against tests/fake_orion.py (valid / malformed / offline / reconnect / timeout / 401 / approval gesture)
 BROWSER TESTS (auto)        need playwright+chromium; SKIPPED (not failed) when absent. Force with --browser, disable with --no-browser
 ORION INTEGRATION (opt-in)  --orion-root <repo>: applies the patch to a TEMP COPY of your server.py and drives ORION's real patched Handler
Exit code 0 only if nothing FAILED. SKIPPED is reported loudly and is not a pass."""
import argparse, pathlib, re, shutil, subprocess, sys, time
T = pathlib.Path(__file__).resolve().parent
ap = argparse.ArgumentParser(); ap.add_argument("--orion-root"); ap.add_argument("--browser", action="store_true"); ap.add_argument("--no-browser", action="store_true"); ap.add_argument("--shots")
a = ap.parse_args()
if not shutil.which("node"): print("node is required (>=18) for the JS tests"); sys.exit(2)
suites = [("UNIT", "assets", ["node", T / "unit/test_assets.js"]), ("UNIT", "normalize", ["node", T / "unit/test_normalize.js"]), ("UNIT", "state reducer", ["node", T / "unit/test_state.js"]),
          ("UNIT", "routes & safety", ["node", T / "unit/test_routes.js"]), ("UNIT", "boot (live + mock)", ["node", T / "unit/test_boot.js"]), ("UNIT", "static serving", [sys.executable, T / "unit/test_static.py"]),
          ("BRIDGE", "real bridge over HTTP", [sys.executable, T / "bridge/test_bridge.py"])]
if not a.no_browser: suites.append(("BROWSER", "Chromium (demo + live vs fake ORION)", [sys.executable, T / "browser/test_browser.py"] + ([a.shots] if a.shots else [])))
if a.orion_root: suites.append(("ORION", "patched real Handler", [sys.executable, T / "integration/test_orion_patch.py", "--orion-root", a.orion_root]))
rows = []; bad = 0
for kind, name, cmd in suites:
    t0 = time.time(); r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, timeout=600); out = r.stdout + r.stderr
    n = len(re.findall(r"^\s+ok\s", out, re.M)); f = len(re.findall(r"^\s+FAIL", out, re.M))
    skipped = out.lstrip().startswith("SKIPPED") or "\nSKIPPED" in out[:300]
    status = "SKIPPED" if skipped else ("PASS" if r.returncode == 0 and f == 0 else "FAIL"); bad += status == "FAIL"
    rows.append((kind, name, status, n, f, time.time() - t0))
    if status == "FAIL": print(f"\n----- {kind}: {name} FAILED -----\n" + "\n".join(l for l in out.splitlines() if "FAIL" in l or "Error" in l or "Traceback" in l)[:3000])
    if status == "SKIPPED": print(f"\n{kind}: {name}: {out.strip().splitlines()[0]}")
print("\n%-8s %-42s %-8s %6s %6s %7s" % ("KIND", "SUITE", "RESULT", "checks", "failed", "secs"))
for k, n, s, c, f, t in rows: print("%-8s %-42s %-8s %6d %6d %7.1f" % (k, n, s, c, f, t))
if not a.orion_root: print("\nNOTE: ORION integration tests were NOT run (pass --orion-root <repo>).")
print("\nRESULT:", "ALL PASSED" if not bad else f"{bad} SUITE(S) FAILED"); sys.exit(1 if bad else 0)
