"""Public OpenRouter model catalog inventory; no credentials, inference or local writes."""
import json
from urllib.request import Request, urlopen
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from orion_v3.work_loop.openrouter_catalog import normalize_catalog
from orion_v3.work_loop.cloud_family_selection import select_distinct

def main():
    req = Request("https://openrouter.ai/api/v1/models",
                  headers={"Accept": "application/json", "User-Agent": "ORION-V3-readonly-catalog"})
    with urlopen(req, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError("catalog request failed")
        raw = response.read(3_000_001)
    if len(raw) > 3_000_000:
        raise RuntimeError("catalog exceeds response bound")
    rows = normalize_catalog(json.loads(raw.decode("utf-8")))
    families = sorted(set(row["family"] for row in rows))
    free = [row for row in rows if row["model"].endswith(":free")]
    print("ORION_OPENROUTER> PUBLIC_CATALOG_ONLY", flush=True)
    print("ORION_OPENROUTER> MODEL_COUNT", len(rows), "FAMILIES", ",".join(families), flush=True)
    print("ORION_OPENROUTER> FREE_CANDIDATES", json.dumps(free[:30], ensure_ascii=True), flush=True)
    print("ORION_OPENROUTER> FAMILY_SHORTLIST", json.dumps(select_distinct(free), ensure_ascii=True), flush=True)
    print("ORION_OPENROUTER> NO_KEY_NO_INFERENCE_NO_EXECUTION", flush=True)

if __name__ == "__main__":
    main()
