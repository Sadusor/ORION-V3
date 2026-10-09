"""Report cloud model metadata from the configured ORION connector."""
import json
from live_two_cloud_architecture_demo import choose_two

def report(catalog):
    rows = []
    for m in catalog.get('models', []):
        if isinstance(m, dict):
            rows.append({k: m.get(k) for k in ('provider', 'model', 'reviewer_id', 'available')})
    return json.dumps(rows, ensure_ascii=True)
