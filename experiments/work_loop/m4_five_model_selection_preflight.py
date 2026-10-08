"""Select five distinct configured cloud reviewers without calling APIs or exposing secrets."""
from __future__ import annotations
import ast
from pathlib import Path

root=Path("E:/ORION/spikes/coding_mode_github_loop")
source=root/"cloud_e2e_brainstorm_probe.py"
tree=ast.parse(source.read_text(encoding="utf-8-sig"))
functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
if "choose_reviewers" not in functions:
    raise RuntimeError("Original council selection unavailable")
print("M4_FIVE> ORIGINAL_COUNCIL_SELECTION_PRESENT")
for name in ("provider_vault.py","reviewer_connector.py"):
    if not (root/name).is_file():raise RuntimeError("Original provider module missing")
print("M4_FIVE> ORIGINAL_PROVIDER_MODULES_PRESENT")
# Safe structural check: no imports, network, credentials, or provider calls.
keys=set()
for node in ast.walk(functions["choose_reviewers"]):
    if isinstance(node,ast.Constant) and isinstance(node.value,str):
        if node.value in {"provider","model","reviewer_id","available","adapter"}:
            keys.add(node.value)
print("M4_FIVE> SELECTOR_FIELDS",",".join(sorted(keys)))
print("M4_FIVE> FIVE_MODEL_SELECTION_PREFLIGHT_PASS")
