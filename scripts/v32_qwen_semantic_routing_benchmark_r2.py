from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "v32_qwen_semantic_routing_benchmark.py"

spec = importlib.util.spec_from_file_location("orion_v3_run_011_base", SOURCE)
if spec is None or spec.loader is None:
    raise SystemExit("Could not load V3-RUN-011 base benchmark.")

benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)

benchmark.CATALOG += """

Routing clarification for exact-name file requests:
- One or more explicitly named filenames plus find/search/locate means fs.search_exact.
- Plain "find X" is search-only; keep reveal_containing_folders=false.
- If the request also says to open/reveal the containing folder, set reveal_containing_folders=true.
- "Do not search subfolders", "directly in", or "top level only" means recursive=false.
- Multiple exact filenames still use fs.search_exact.
- fs.list is for inventory/browsing such as newest/oldest files or folders when no exact filename search is requested.
"""

print("V3_RUN_RETRY> V3-RUN-011-R2")
raise SystemExit(benchmark.main())
