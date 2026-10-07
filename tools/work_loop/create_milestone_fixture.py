"""Create the disposable Autonomous Work Loop V1 qualification project.

Safe staging utility: creates files only under the explicitly supplied empty
fixture directory.  It does not invoke a model, Hand, network, or sandbox.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from orion_v3.work_loop.contracts import WorkState
from orion_v3.work_loop.vault import ProjectVault


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", help="Empty disposable project directory, preferably on E:")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve(strict=False)
    if root.exists() and any(root.iterdir()):
        raise SystemExit("REFUSE: fixture root must be empty")
    root.mkdir(parents=True, exist_ok=True)

    vault = ProjectVault(root)
    vault.initialize(
        WorkState(
            project_id="work-loop-v1-fixture",
            objective="Prove bounded FAIL -> restart -> repair -> PASS continuity",
            checkpoint="M4-FIRST-PHYSICAL-QUALIFICATION",
            current_task="T-001",
            next_action="Run the deliberate failing fixture only after confinement qualification",
            constraints=[
                "No writes outside this project workspace",
                "Real evidence decides PASS/FAIL",
                "Existing ORION STOP remains authoritative",
            ],
            frozen_paths=["repo/FROZEN.txt"],
        )
    )

    (vault.repo_path / "FROZEN.txt").write_text("DO NOT MODIFY\n", encoding="utf-8")
    (vault.repo_path / "calculator.py").write_text(
        "def add(a, b):\n"
        "    # Deliberate qualification defect. Repair should return a + b.\n"
        "    return a - b\n",
        encoding="utf-8",
    )
    (vault.repo_path / "test_calculator.py").write_text(
        "from calculator import add\n\n"
        "def test_add():\n"
        "    assert add(2, 3) == 5\n",
        encoding="utf-8",
    )
    print(f"WORK_LOOP_FIXTURE_CREATED> {root}")
    print("EXECUTION_NOT_STARTED> sandbox qualification still required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
