"""Isolated bridge from Qwen planner to existing authorized Gitea read-only search.

Not wired to product_server. Owner-authenticated caller must supply catalog and
model callback. This module cannot grant new repository permissions.
"""
from __future__ import annotations
import json
import urllib.request

from .gitea_multi_repo_v1 import GiteaMultiRepoV1
from .gitea_readonly_v1 import GiteaReadonly
from .qwen_readonly_investigation_candidate_v1 import investigate


def ollama_planner(prompt: str, *, model: str, base_url: str = "http://127.0.0.1:11434") -> str:
    if base_url != "http://127.0.0.1:11434":
        raise ValueError("Only local Ollama is supported")
    if not model or len(model) > 120:
        raise ValueError("Explicit bounded model required")
    request = urllib.request.Request(
        base_url + "/api/generate",
        data=json.dumps({
            "model": model,
            "prompt": "You are ORION's read-only research planner. Return ONLY a JSON object. "
                      "Choose a repository ONLY from the supplied authorized list. "
                      "Search code evidence; if results are irrelevant, refine the query. "
                      "Never issue commands, writes, or authorization changes.\n" + prompt,
            "stream": False,
            "format": "json",
            "think": False,
            "options": {"temperature": 0, "num_predict": 180},
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=45) as response:
        data = json.load(response)
    if data.get("done") is not True or not isinstance(data.get("response"), str):
        raise ValueError("Incomplete model plan")
    return data["response"]


def investigate_gitea(owner_question: str, *, state_dir, catalog, token: str,
                      propose, api=None, max_rounds: int = 3):
    """Authorized repository catalog is provided by existing owner-gated caller."""
    reader = api if api is not None else GiteaReadonly("http://127.0.0.1:3001", token=token)
    adapter = GiteaMultiRepoV1(api=reader, state_dir=state_dir, catalog=tuple(catalog))
    authorized = tuple(r.owner + "/" + r.name for r in adapter.authorized_inventory())
    by_name = {r.owner + "/" + r.name: r for r in adapter.authorized_inventory()}

    def retrieve(repository: str, query: str) -> list[dict]:
        selected = by_name[repository]
        hits = adapter.search(query, project=selected.project, limit=6)
        result = []
        for hit in hits:
            # The existing adapter creates this citation from pinned commit and path.
            # Parse its exact format; fail closed on malformed provenance.
            prefix = "MyGitea2 " + repository + " "
            if not hit.citation.startswith(prefix):
                continue
            rest = hit.citation[len(prefix):]
            commit, sep, suffix = rest.partition(" ")
            path, marker, part = suffix.rpartition(" part ")
            if not sep or not marker or len(commit) != 40 or not path or not part.isdigit():
                continue
            result.append({
                "repository": repository, "path": path, "commit": commit,
                "excerpt": hit.snippet,
            })
        return result

    return investigate(owner_question, authorized_repositories=authorized,
                       propose=propose, retrieve=retrieve, max_rounds=max_rounds)
