"""Read-only local provider-implementation locator. Never prints file contents, env or secrets."""
from __future__ import annotations
import os
from pathlib import Path

ROOTS = [Path("E:/ORION-V3"), Path("E:/ORION"), Path("E:/ORION-V2"),
         Path("E:/ORION-WORKLOOP-REMOTE-TEST")]
TOKENS = ("provider", "connector", "cloud", "groq", "gemini", "deepseek", "openrouter",
          "gitcheck", "reviewer", "api_client", "api_router")
EXCLUDED = {".git", "node_modules", ".venv", "venv", "build", "dist", ".gradle",
            "__pycache__", "cache", "logs", "secrets", "credentials"}
EXTS = {".py", ".ps1", ".md", ".json", ".toml", ".yaml", ".yml"}
for root in ROOTS:
    if not root.is_dir():
        continue
    print("M4_PROVIDER_LOCATOR> ROOT_PRESENT", root.name)
    matches = 0
    for base, dirs, files in os.walk(root):
        depth = len(Path(base).relative_to(root).parts)
        dirs[:] = [d for d in dirs if d.lower() not in EXCLUDED and not d.startswith(".")][:40] if depth < 6 else []
        for name in files:
            path = Path(base) / name
            if path.suffix.lower() not in EXTS or not any(t in name.lower() for t in TOKENS):
                continue
            if any(t in name.lower() for t in ("secret", "token", "credential", ".env", "key")):
                continue
            print("M4_PROVIDER_LOCATOR> CANDIDATE", root.name, str(path.relative_to(root)).replace("\\", "/"))
            matches += 1
            if matches >= 45:
                break
        if matches >= 45:
            break
    print("M4_PROVIDER_LOCATOR> CANDIDATES", root.name, matches)
print("M4_PROVIDER_LOCATOR> READ_ONLY_NO_SECRETS_PASS")
