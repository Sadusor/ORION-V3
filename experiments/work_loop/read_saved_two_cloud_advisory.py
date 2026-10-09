"""Read-only, bounded review of the physically saved ORION multi-AI advisory.

Never calls providers, writes files, approves plans, or executes generated code.
Prints proposal/critique excerpts into the owner-controlled command evidence.
"""
import hashlib
import json
from pathlib import Path
import re

SOURCE = Path(r"E:\ORION-WORKLOOP-REMOTE-TEST\artifacts\multi-ai\live-70483bb2c45747e3b58cf4215d0221db.json")
MAX_FILE = 150_000
MAX_EXCERPT = 7_000

def redact(value):
    value = re.sub(r"(?i)(api[_-]?key|access[_-]?token|authorization|password|secret)\s*[:=]\s*[^\s,;]+",
                   r"\1=[REDACTED]", value)
    value = re.sub(r"(?i)bearer\s+[A-Za-z0-9._-]{12,}", "Bearer [REDACTED]", value)
    value = re.sub(r"\b(?:gsk|sk)-[A-Za-z0-9_-]{12,}\b", "[REDACTED_KEY]", value)
    return value

def main():
    if not SOURCE.is_file() or SOURCE.is_symlink() or SOURCE.stat().st_size > MAX_FILE:
        raise RuntimeError("Expected bounded advisory file missing or invalid")
    raw = SOURCE.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    if data.get("schema") != "orion.v3.multi_ai.advisory.v1":
        raise RuntimeError("Unexpected advisory schema")
    if data.get("owner_approval") != "NOT_GRANTED" or data.get("execution") != "NOT_PERFORMED":
        raise RuntimeError("Unexpected approval/execution state")
    print("ORION_REVIEW> SOURCE_SHA256", hashlib.sha256(raw).hexdigest(), flush=True)
    print("ORION_REVIEW> OBJECTIVE", redact(str(data.get("objective", "")))[:2000], flush=True)
    for field in ("proposals", "critiques"):
        entries = data.get(field)
        if not isinstance(entries, list) or len(entries) != 2:
            raise RuntimeError("Expected exactly two " + field)
        for index, item in enumerate(entries, 1):
            name, body, digest = item.get("model_id"), item.get("text"), item.get("sha256")
            if not isinstance(name, str) or not isinstance(body, str) or not isinstance(digest, str):
                raise RuntimeError("Malformed advisory entry")
            if hashlib.sha256(body.encode("utf-8")).hexdigest() != digest:
                raise RuntimeError("Advisory digest mismatch")
            print("ORION_REVIEW> BEGIN", field.upper(), index, redact(name)[:100],
                  "CHARS", len(body), "SHA256", digest, flush=True)
            print(redact(body[:MAX_EXCERPT]), flush=True)
            if len(body) > MAX_EXCERPT:
                print("ORION_REVIEW> TRUNCATED", len(body)-MAX_EXCERPT, flush=True)
            print("ORION_REVIEW> END", field.upper(), index, flush=True)
    print("ORION_REVIEW> READ_ONLY_NO_CLOUD_NO_EXECUTION_NO_APPROVAL", flush=True)

if __name__ == "__main__":
    main()
