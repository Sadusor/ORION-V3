"""Export inert, hash-verified cloud response as a DeepSeek review document.

No import or execution of submitted code. Refuse overwrite.
"""
from __future__ import annotations
import hashlib
import json
from task_ledger_cloud_trial_001 import runtime_root
from task_ledger_trial_001_completeness import FENCE, MAX_BYTES

def export() -> str:
    folder = runtime_root() / "coding-mode" / "reviewers" / "task-ledger-trial-001"
    raw = (folder / "cloud-output.txt").read_bytes()
    if len(raw) > MAX_BYTES:
        raise RuntimeError("saved response exceeds size limit")
    text = raw.decode("utf-8").replace("\r\n", "\n")
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if digest != manifest["output_sha256"]:
        raise RuntimeError("saved response hash mismatch")
    blocks = list(FENCE.finditer(text))
    if len(blocks) < 4:
        raise RuntimeError("expected at least four fenced source blocks")
    # Keep original source unchanged, including headings and any warnings.
    out = folder / "DEEPSEEK_REVIEW_SOURCE_TRIAL_001.md"
    if out.exists():
        existing = out.read_text(encoding="utf-8")
        if existing != text:
            raise RuntimeError("existing review source differs; refusing overwrite")
        print("DEEPSEEK_EXPORT> ALREADY_PRESENT_MATCHES_SOURCE", flush=True)
    else:
        out.write_text(text, encoding="utf-8", newline="\n")
        print("DEEPSEEK_EXPORT> SAVED", flush=True)
    print("DEEPSEEK_EXPORT> VERIFIED_SHA256", digest, flush=True)
    print("DEEPSEEK_EXPORT> CODE_BLOCKS", len(blocks), flush=True)
    print("DEEPSEEK_EXPORT> PATH", out, flush=True)
    print("DEEPSEEK_EXPORT> INERT_TEXT_ONLY", flush=True)
    return str(out)

if __name__ == "__main__":
    export()
