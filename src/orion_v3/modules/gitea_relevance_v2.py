"""V2 query-specific source retrieval. Untrusted reference context only."""
from __future__ import annotations
import re
from .gitea_search_context_v1 import search_code_context
from .orion_understanding_v1 import interpret, rank_source_path

def search_relevant_context(index_path, *, query, project, repository, commit_sha, max_chars=6000):
    from .gitea_code_index_v1 import GiteaCodeIndex
    base=search_code_context(index_path,query=query,project=project,repository=repository,
                             commit_sha=commit_sha,max_chars=max_chars)
    tokens=[x.casefold() for x in re.findall(r"[a-zA-Z0-9]+",query)]
    stop={"what","is","in","orion","v3","the","from","find","source","and","explain","does","it","mygitea2","how","of","a","for","to"}
    terms=[t for t in tokens if len(t)>2 and t not in stop]
    if len(terms)<2:
        return base
    index=GiteaCodeIndex(index_path)
    import sqlite3
    from contextlib import closing
    with closing(sqlite3.connect(index.path)) as db:
        revision=db.execute("select commit_sha from code_revision where project=? and repository=?",
                            (project,repository)).fetchone()
        if not revision or revision[0]!=commit_sha:
            raise ValueError("Index revision mismatch")
        rows=db.execute("select path,part,text from code_fts where project=? and repository=? and commit_sha=? order by path,cast(part as integer)",
                        (project,repository,commit_sha)).fetchall()
    understanding=interpret(query)
    candidates=[]
    for path,part,body in rows:
        name=path.casefold().replace("_","-")
        matched=sum(bool(re.search(r"(?<![a-z0-9])"+re.escape(term)+r"(?![a-z0-9])",name)) for term in set(terms))
        path_score=rank_source_path(path,concepts=understanding.concepts)
        # Source paths are indexed metadata, not model instructions. A path matching
        # the requested platform and implementation outranks generic prose hits.
        if matched>=2 or (matched>=1 and path_score>=15):
            candidates.append((matched,path_score,len(path),path,int(part),body))
    candidates.sort(key=lambda x:(-x[0],-x[1],x[2],x[3],x[4]))
    selected=[{"path":path,"part":part,"source_commit":commit_sha,"text":body}
              for _,_,_,path,part,body in candidates[:12]]
    # Prioritize implementation paths before FTS prose; retain fallback evidence.
    combined=selected+base["results"]
    output=[]
    remaining=max_chars
    for item in combined:
        if any(x["path"]==item["path"] and x["part"]==item["part"] for x in output):
            continue
        if len(item["text"])>remaining:
            continue
        remaining-=len(item["text"])
        output.append(item)
    base["results"]=output
    return base
