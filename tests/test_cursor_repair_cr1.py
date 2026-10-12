"""Cursor's Repair CR-1: default lookup and optional-evidence size budget."""
from pathlib import Path
import ast


def test_default_chat_uses_interpreter():
    source = Path(__file__).resolve().parents[1] / "src/orion_v3/modules/gitea_chat_brain_v1.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    assert any(isinstance(c.func, ast.Attribute) and c.func.attr == "retrieve"
               and c.args and isinstance(c.args[0], ast.Call)
               and isinstance(c.args[0].func, ast.Attribute)
               and c.args[0].func.attr == "interpret" for c in calls)


def test_optional_evidence_budget_and_original_goal():
    source = Path(__file__).resolve().parents[1] / "src/orion_v3/modules/gitea_chat_brain_v1.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
              and n.name == "attach_bounded_reference")
    ns = {}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), "exec"), ns)
    attach = ns["attach_bounded_reference"]
    goal = "My latest question about SQL tables and schemas"
    out = attach(goal, "Δοκιμή" * 4000)
    assert out.startswith(goal + "\n\n")
    assert len(out.encode("utf-8")) <= 15360
    assert "Evidence truncated" in out
    assert attach("x" * 15400, "evidence") == "x" * 15400
    assert attach(goal, "") == goal
    assert attach(goal, "short evidence").endswith("short evidence")
