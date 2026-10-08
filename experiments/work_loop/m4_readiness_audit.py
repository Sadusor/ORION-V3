"""Read-only Milestone 4 readiness gate; never invokes Qwen or executes a Hand."""
from __future__ import annotations
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[3]
checks = {
    "vault": ROOT / "src/orion_v3/work_loop/vault.py",
    "coordinator": ROOT / "src/orion_v3/work_loop/coordinator.py",
    "engine": ROOT / "src/orion_v3/work_loop/engine.py",
    "stop": ROOT / "src/orion_v3/work_loop/stop.py",
    "bound_native": ROOT / "src/orion_v3/work_loop/m35_experimental_cycle.py",
    "native_probe": ROOT / "experiments/windows_appcontainer/M35BoundActionProbe.cs",
}
for name, path in checks.items():
    if not path.is_file():
        raise SystemExit(f"M4_READINESS> FAIL missing {name}: {path}")
    if path.suffix == ".py":
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"M4_READINESS> {name.upper()} SOURCE_PRESENT")
engine = checks["engine"].read_text(encoding="utf-8")
coord = checks["coordinator"].read_text(encoding="utf-8")
native = checks["bound_native"].read_text(encoding="utf-8")
if "SimulatedWorkHand" not in coord or "independently_verified_pass" not in engine:
    raise SystemExit("M4_READINESS> FAIL authority seam drift")
if "hold_for_stop_test" not in native or "STOP during bound native child" not in native:
    raise SystemExit("M4_READINESS> FAIL STOP seam drift")
print("M4_READINESS> REAL_QWEN_ADAPTER_NOT_QUALIFIED")
print("M4_READINESS> FAIL_RESTART_REPAIR_PASS_NOT_QUALIFIED")
print("M4_READINESS> PRODUCTION_EXECUTION_DISABLED")
print("M4_READINESS> READ_ONLY_AUDIT_PASS")
