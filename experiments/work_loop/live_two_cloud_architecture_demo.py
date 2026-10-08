"""Owner-triggered live two-cloud architecture debate via existing ORION connector.

No code execution, no approval. Uses existing DPAPI-backed provider vault.
Run locally on the configured Windows ORION machine, never on GitHub-hosted CI.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from orion_v3.work_loop.multi_ai_existing_reviewer import run_council

DONOR = Path("E:/ORION/spikes/coding_mode_github_loop")
TASK = ("Build a tiny offline task tracker with Python standard library only, SQLite "
        "persistence, simple localhost HTTP API, and reproducible automated tests. "
        "No dependency installation, internet access, shell execution, or changes "
        "outside a disposable project. Discuss module split, acceptance tests, "
        "failure cases and repair strategy. This is planning only.")

def runtime_from_existing_source():
    source = DONOR / "cloud_e2e_brainstorm_probe.py"
    tree = ast.parse(source.read_text(encoding="utf-8-sig"))
    assignments = [node.value for node in ast.walk(tree) if isinstance(node, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "runtime" for t in node.targets)]
    if len(assignments) != 1:
        raise RuntimeError("original provider runtime shape changed")
    expr = assignments[0]
    parts = []
    while isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Div):
        if not isinstance(expr.right, ast.Constant) or not isinstance(expr.right.value, str):
            raise RuntimeError("unsupported runtime suffix")
        parts.insert(0, expr.right.value)
        expr = expr.left
    if not isinstance(expr, ast.Call) or not isinstance(expr.func, ast.Name) or expr.func.id != "Path":
        raise RuntimeError("unsupported runtime root")
    env = expr.args[0]
    if (not isinstance(env, ast.Call) or not isinstance(env.func, ast.Attribute)
            or env.func.attr != "get" or not env.args
            or not isinstance(env.args[0], ast.Constant)):
        raise RuntimeError("unsupported runtime env")
    runtime = Path(os.environ.get(env.args[0].value, str(Path.home())))
    for part in parts:
        runtime /= part
    return runtime

def choose_two(catalog):
    models = catalog.get("models") or []
    valid = [m for m in models if isinstance(m, dict) and m.get("available") is True
             and isinstance(m.get("reviewer_id"), str) and m["reviewer_id"].strip()
             and str(m.get("provider") or "").lower() not in ("ollama", "local")
             and "preview" not in str(m.get("model") or "").lower()
             and not any(x in str(m.get("model") or "").lower()
                         for x in ("whisper", "tts", "speech", "guard", "transcribe", "orpheus"))]
    def priority(m):
        label = str(m.get("model") or "").lower()
        if "gpt-oss-120b" in label: return 0
        if "qwen" in label and ("27b" in label or "32b" in label): return 1
        if "gpt-oss-20b" in label: return 2
        return 5
    valid.sort(key=priority)
    picked = []
    for item in valid:
        if item["reviewer_id"] not in [x["reviewer_id"] for x in picked]:
            picked.append(item)
        if len(picked) == 2: break
    if len(picked) != 2:
        raise RuntimeError("fewer than two available distinct cloud model IDs")
    return picked

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not (DONOR / "reviewer_connector.py").is_file():
        raise RuntimeError("existing ORION provider connector missing")
    sys.path.insert(0, str(DONOR))
    from provider_vault import ProviderVault
    from reviewer_connector import ReviewerConnector
    runtime = runtime_from_existing_source()
    connector = ReviewerConnector(runtime / "coding-mode" / "reviewers",
                                  provider_vault=ProviderVault(runtime / "provider-vault"),
                                  configured_free_providers=[])
    selected = choose_two(connector.refresh_catalog())
    ids = [m["reviewer_id"] for m in selected]
    print("ORION_COUNCIL> MODELS", ",".join(str(m.get("model") or "unknown")[:65] for m in selected), flush=True)
    print("ORION_COUNCIL> TWO_ROUNDS_START_NO_EXECUTION", flush=True)
    result = run_council(connector=connector, reviewer_ids=ids,
                         project_id="demo-task-tracker", task_id="architecture-001",
                         objective=TASK, stop_requested=lambda: False)
    def digest(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()
    payload = {
        "schema": "orion.v3.multi_ai.advisory.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "project_id": result.project_id, "task_id": result.task_id,
        "objective": result.objective, "stage": result.stage,
        "model_metadata": [{"model": str(m.get("model") or ""), "provider": str(m.get("provider") or "")}
                           for m in selected],
        "proposals": [{"model_id": name, "text": body, "sha256": digest(body)}
                      for name, body in result.proposals],
        "critiques": [{"model_id": name, "text": body, "sha256": digest(body)}
                      for name, body in result.critiques],
        "plan": "", "disagreements": [], "owner_approval": "NOT_GRANTED",
        "execution": "NOT_PERFORMED"
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    print("ORION_COUNCIL> INDEPENDENT_PROPOSALS", len(result.proposals), flush=True)
    print("ORION_COUNCIL> CROSS_REVIEWS", len(result.critiques), flush=True)
    print("ORION_COUNCIL> SAVED", args.output, flush=True)
    print("ORION_COUNCIL> ADVISORY_COMPLETE_OWNER_APPROVAL_REQUIRED", flush=True)

if __name__ == "__main__":
    main()
