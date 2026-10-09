"""Append-only, bounded council slot checkpoints with no credential material.

The caller supplies an evidence path inside an approved workspace. Never log prompts,
responses, exception text or credentials. Each record is hash-chained for audit.
"""
import hashlib
import json
from pathlib import Path

MAX_BYTES = 256_000

def append_checkpoint(*, path, task_id, slot_id, provider, model, family, status):
    for value in (task_id, slot_id, provider, model, family, status):
        if not isinstance(value, str) or not value or len(value) > 160 or any(
            ord(c) < 32 for c in value):
            raise ValueError("invalid checkpoint metadata")
    p = Path(path)
    if p.is_symlink() or (p.exists() and not p.is_file()):
        raise ValueError("unsafe checkpoint path")
    raw = p.read_bytes() if p.exists() else b""
    if len(raw) > MAX_BYTES:
        raise ValueError("checkpoint ledger full")
    previous = "0" * 64
    for line in raw.splitlines():
        entry = json.loads(line)
        claimed = entry.pop("sha256")
        encoded = json.dumps(entry, sort_keys=True, separators=(",", ":")).encode()
        if entry.get("previous") != previous or hashlib.sha256(encoded).hexdigest() != claimed:
            raise ValueError("checkpoint ledger tampered")
        previous = claimed
    record = {"task_id":task_id,"slot_id":slot_id,"provider":provider,"model":model,
              "family":family,"status":status,"previous":previous}
    encoded = json.dumps(record,sort_keys=True,separators=(",",":")).encode()
    record["sha256"] = hashlib.sha256(encoded).hexdigest()
    output = (json.dumps(record,sort_keys=True,separators=(",",":"))+"\n").encode()
    if len(raw)+len(output)>MAX_BYTES:
        raise ValueError("checkpoint ledger full")
    p.parent.mkdir(parents=True,exist_ok=True)
    # Only single-process writer; production must add locking and workspace validation.
    with p.open("ab") as f:
        f.write(output)
        f.flush()
    return record["sha256"]
