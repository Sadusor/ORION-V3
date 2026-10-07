import subprocess
import sys
from pathlib import Path


def test_fixture_creator_refuses_nonempty_root(tmp_path):
    root = tmp_path / "fixture"
    root.mkdir()
    (root / "existing.txt").write_text("x", encoding="utf-8")
    script = Path(__file__).parents[1] / "tools" / "work_loop" / "create_milestone_fixture.py"
    result = subprocess.run([sys.executable, str(script), str(root)], capture_output=True, text=True)
    assert result.returncode != 0
    assert "must be empty" in (result.stdout + result.stderr)
