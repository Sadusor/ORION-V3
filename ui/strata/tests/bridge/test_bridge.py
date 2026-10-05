"""BRIDGE TESTS: the real bridge over real HTTP against the fake ORION (no real ORION needed). Needs node."""
import pathlib, subprocess, sys
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from fake_orion import FakeOrion
f = FakeOrion().start()
try:
    r = subprocess.run(["node", str(HERE / "bridge_driver.js"), str(HERE.parent.parent), f.base, f.token, f.code], capture_output=True, text=True, timeout=90)
    print(r.stdout, end=""); print(r.stderr[-1500:], end="")
    sys.exit(r.returncode)
finally:
    f.stop()
