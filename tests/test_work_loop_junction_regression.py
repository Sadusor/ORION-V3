"""Windows junction escape regression: temporary paths only, no other projects touched."""
import os
import subprocess
import pytest
from orion_v3.work_loop.paths import require_inside_workspace, WorkspaceViolation


@pytest.mark.skipif(os.name != "nt", reason="Windows junction test")
def test_windows_junction_escape(tmp_path):
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    junction = workspace / "junction"
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
        capture_output=True, text=True,
    )
    if result.returncode:
        pytest.skip("junction creation unavailable")
    try:
        with pytest.raises(WorkspaceViolation):
            require_inside_workspace("junction/secret.txt", workspace)
    finally:
        junction.rmdir()
