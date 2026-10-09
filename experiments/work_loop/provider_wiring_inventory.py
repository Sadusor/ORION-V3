"""Read-only provider wiring diagnostics: names only, never keys or values."""
import ast
from pathlib import Path

DONOR = Path("E:/ORION/spikes/coding_mode_github_loop")
def main():
    names = ("reviewer_connector.py", "provider_vault.py")
    for filename in names:
        path = DONOR / filename
        if not path.is_file():
            print("ORION_WIRING> MISSING", filename, flush=True)
            continue
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        providers = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                for p in ("openrouter", "groq", "gemini"):
                    if p in node.id.lower(): providers.add(p)
            if isinstance(node, ast.Attribute):
                for p in ("openrouter", "groq", "gemini"):
                    if p in node.attr.lower(): providers.add(p)
        print("ORION_WIRING> SOURCE", filename, "PROVIDER_IDENTIFIERS", ",".join(sorted(providers)) or "none", flush=True)
    print("ORION_WIRING> AST_ONLY_NO_KEYS_NO_CALLS", flush=True)

if __name__ == "__main__":
    main()
