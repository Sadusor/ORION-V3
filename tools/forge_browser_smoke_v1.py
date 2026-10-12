"""Windows Edge headless smoke for the frozen Forge staging candidate.

Loads the trusted UI shell only, never submits model prompts or runs generated code.
Produces a screenshot and a small evidence report in a caller-supplied output folder.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

def find_edge():
    candidates = [
        shutil.which("msedge"),
        Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Microsoft/Edge/Application/msedge.exe",
    ]
    return next((str(p) for p in candidates if p and Path(p).is_file()), None)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1] / "prototypes/forge/orion_forge_staging_v3.html"
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    edge = find_edge()
    if not edge:
        print("FORGE_BROWSER_SMOKE> NOT_TESTED_EDGE_MISSING")
        return 2
    screenshot = output / "forge_staging_smoke.png"
    with tempfile.TemporaryDirectory(prefix="orion-forge-edge-") as profile:
        cmd = [edge, "--headless=new", "--disable-gpu", "--no-first-run",
               "--no-default-browser-check", "--disable-extensions",
               "--disable-background-networking", "--disable-sync",
               "--user-data-dir=" + profile, "--window-size=1440,900",
               "--screenshot=" + str(screenshot), source.resolve().as_uri()]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
        except subprocess.TimeoutExpired:
            print("FORGE_BROWSER_SMOKE> FAIL_TIMEOUT")
            return 1
    passed = proc.returncode == 0 and screenshot.is_file() and screenshot.stat().st_size > 3000
    report = {"browser": "Microsoft Edge headless", "exit_code": proc.returncode,
              "screenshot_bytes": screenshot.stat().st_size if screenshot.exists() else 0,
              "result": "PASS_SCREENSHOT_CREATED" if passed else "FAIL",
              "note": "Screenshot creation only. Visual inspection and interactive behavior NOT verified."}
    (output / "forge_browser_smoke.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("FORGE_BROWSER_SMOKE> " + report["result"])
    print("FORGE_BROWSER_VISUAL_INSPECTION> NOT_PERFORMED")
    return 0 if passed else 1

if __name__ == "__main__":
    sys.exit(main())
