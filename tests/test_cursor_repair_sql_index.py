"""Cursor's Repair CR-2: source SQL schemas enter existing authorized indexes."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src/orion_v3/modules"


def test_default_index_accepts_sql():
    tree = ast.parse((ROOT / "gitea_auto_index_v2.py").read_text(encoding="utf-8"))
    values = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    assert ".sql" in values


def test_authorized_multi_repo_index_accepts_sql_without_scope_expansion():
    tree = ast.parse((ROOT / "gitea_multi_repo_v1.py").read_text(encoding="utf-8"))
    eligible = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "ELIGIBLE" for t in n.targets))
    assert ".sql" in ast.literal_eval(eligible.args[0])
    refresh = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "refresh")
    source = ast.get_source_segment((ROOT / "gitea_multi_repo_v1.py").read_text(encoding="utf-8"), refresh)
    assert "Repository not authorized" in source
    assert "commit_sha=commit" in source
