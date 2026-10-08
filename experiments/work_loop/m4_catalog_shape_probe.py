"""Inspect cloud catalog structure without printing identifiers, secrets or values."""
from __future__ import annotations
import ast
from pathlib import Path
p=Path("E:/ORION/spikes/coding_mode_github_loop/reviewer_connector.py")
tree=ast.parse(p.read_text(encoding="utf-8-sig"))
for n in ast.walk(tree):
    if isinstance(n,ast.FunctionDef) and n.name in ("_discover_groq","_discover_gemini","_discover_vault_provider","_discover_ollama","refresh_catalog"):
        print("M4_CATALOG_SHAPE> METHOD",n.name)
        keys=set()
        for x in ast.walk(n):
            if isinstance(x,ast.Dict):
                keys.update(k.value for k in x.keys if isinstance(k,ast.Constant) and isinstance(k.value,str))
        print("M4_CATALOG_SHAPE> DICT_KEYS",",".join(sorted(keys))[:500])
print("M4_CATALOG_SHAPE> STATIC_ONLY_PASS")
