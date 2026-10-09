"""Pure, offline model-family selection; no provider or credential access."""
FAMILIES = ("gpt-oss", "qwen", "deepseek", "llama", "mistral", "kimi", "gemini", "claude", "nemotron", "gemma")

def family(model):
    name = str(model).lower()
    for label in FAMILIES:
        if label in name:
            return label
    return "unknown"

def select_distinct(catalog, count=4):
    if not isinstance(catalog, list) or count < 1:
        raise ValueError("invalid catalog or count")
    candidates = []
    for entry in catalog:
        if not isinstance(entry, dict) or entry.get("available") is not True:
            continue
        model = str(entry.get("model") or "")
        provider = str(entry.get("provider") or "").lower()
        identity = str(entry.get("reviewer_id") or "")
        group = family(model)
        if (not identity or group == "unknown" or provider in ("local", "ollama")
                or any(word in model.lower() for word in ("preview", "transcribe", "speech", "orpheus", "lyria", "banana"))):
            continue
        candidates.append({"model": model, "provider": provider, "reviewer_id": identity, "family": group})
    priority = {"gpt-oss": 0, "qwen": 1, "gemini": 2, "deepseek": 3, "mistral": 4, "llama": 5, "kimi": 6}
    candidates.sort(key=lambda m: (priority.get(m["family"], 20), m["provider"], m["model"]))
    selected = []
    used_families = set()
    for item in candidates:
        if item["family"] in used_families:
            continue
        selected.append(item)
        used_families.add(item["family"])
        if len(selected) == count:
            break
    return selected
