"""Read-only qualification of the Groq coding artifact.

Do not execute or import generated source. Detect repeated provider replies.
"""
import ast
import hashlib
import json
from pathlib import Path

ARTIFACT = Path("E:/ORION-WORK/groq_artifact_trial_20261012.json")

def main():
    if not ARTIFACT.is_file():
        print("GROQ_ARTIFACT_AUDIT> MISSING")
        return 2
    doc = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    if doc.get("schema") != "orion.groq.artifact_trial.v1":
        print("GROQ_ARTIFACT_AUDIT> SCHEMA_INVALID")
        return 2
    proposal, review = doc.get("proposal"), doc.get("review")
    if not isinstance(proposal, str) or not isinstance(review, str):
        print("GROQ_ARTIFACT_AUDIT> CONTENT_INVALID")
        return 2
    digest = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()
    if digest(proposal) != doc.get("proposal_sha256") or digest(review) != doc.get("review_sha256"):
        print("GROQ_ARTIFACT_AUDIT> HASH_MISMATCH")
        return 2
    print("GROQ_ARTIFACT_AUDIT> PROPOSAL_CHARS", len(proposal))
    print("GROQ_ARTIFACT_AUDIT> REVIEW_CHARS", len(review))
    if proposal == review:
        print("GROQ_ARTIFACT_AUDIT> IDENTICAL_RESPONSES_CONFIRMED")
    else:
        print("GROQ_ARTIFACT_AUDIT> DISTINCT_RESPONSES")
    try:
        tree = ast.parse(proposal)
    except SyntaxError:
        print("GROQ_ARTIFACT_AUDIT> PYTHON_SYNTAX_INVALID")
        return 2
    funcs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not any(f.name == "normalize_task_title" for f in funcs):
        print("GROQ_ARTIFACT_AUDIT> EXPECTED_FUNCTION_MISSING")
        return 2
    if proposal == review:
        print("GROQ_ARTIFACT_AUDIT> REVIEW_NOT_INDEPENDENT")
        return 2
    print("GROQ_ARTIFACT_AUDIT> CONTENT_CHECK_PASS_NO_EXECUTION")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
