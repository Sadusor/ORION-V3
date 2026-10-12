"""Fail-closed static qualification of untrusted Groq code proposals.

Never imports, evaluates, or executes proposed code.
"""
import ast
import hashlib

class QualificationError(ValueError):
    pass

def qualify(proposal, review):
    if not isinstance(proposal, str) or not 0 < len(proposal) <= 8000:
        raise QualificationError("INVALID_PROPOSAL")
    if not isinstance(review, str) or not 0 < len(review) <= 8000:
        raise QualificationError("INVALID_REVIEW")
    if proposal == review:
        raise QualificationError("REPLAYED_REVIEW")
    try:
        tree = ast.parse(proposal, filename="untrusted_proposal.py")
    except SyntaxError as exc:
        raise QualificationError("SYNTAX_INVALID") from None
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        raise QualificationError("UNEXPECTED_TOP_LEVEL")
    func = tree.body[0]
    if func.name != "normalize_task_title" or len(func.args.args) != 1 or func.args.args[0].arg != "value":
        raise QualificationError("FUNCTION_CONTRACT")
    if func.decorator_list or func.args.vararg or func.args.kwarg or func.args.kwonlyargs:
        raise QualificationError("FUNCTION_CONTRACT")
    forbidden = (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal,
                 ast.With, ast.AsyncWith, ast.Await, ast.Yield, ast.YieldFrom, ast.Lambda,
                 ast.ClassDef, ast.AsyncFunctionDef, ast.Delete)
    # This only checks structure. Calls and attributes are not safe to execute.
    for node in ast.walk(func):
        if isinstance(node, forbidden):
            raise QualificationError("UNTRUSTED_OPERATION")
    return {"stage": "STATIC_ONLY_NOT_EXECUTED",
            "proposal_sha256": hashlib.sha256(proposal.encode()).hexdigest(),
            "review_sha256": hashlib.sha256(review.encode()).hexdigest(),
            "function": func.name}
