"""Independent black-box public smoke evaluator for Task Ledger v0.1.

Uses stdlib HTTP only. No model APIs, shell, network beyond loopback, or source writes.
This is PUBLIC protocol validation, NOT the held-out scored test suite.
"""
from __future__ import annotations
import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

def call(base, method, route, payload=None, raw=None):
    data=(json.dumps(payload).encode() if payload is not None else raw)
    req=urllib.request.Request(base+route,data=data,method=method,
        headers={"Content-Type":"application/json"} if data is not None else {})
    try:
        with urllib.request.urlopen(req,timeout=5) as response:
            body=response.read()
            return response.status,json.loads(body) if body else None
    except urllib.error.HTTPError as error:
        body=error.read()
        try:parsed=json.loads(body) if body else None
        except (ValueError,UnicodeDecodeError):parsed=None
        return error.code,parsed

def evaluate(base):
    results=[]
    def check(name,condition,detail=""):
        results.append({"name":name,"pass":bool(condition),"detail":str(detail)[:180]})
        print("LEDGER_PUBLIC>",name,"PASS" if condition else "FAIL",flush=True)
    suffix=str(time.time_ns())
    task="bench_"+suffix
    other="other_"+suffix
    s,b=call(base,"GET","/health")
    check("health",s==200 and isinstance(b,dict) and b.get("status")=="ok",s)
    s,b=call(base,"POST","/tasks",{"id":task})
    check("create",s==201 and isinstance(b,dict) and b.get("state")=="PENDING",s)
    s,_=call(base,"POST","/tasks",{"id":task})
    check("duplicate_rejected",s==409,s)
    s,b=call(base,"GET","/tasks/"+task)
    check("get_task",s==200 and isinstance(b,dict) and b.get("id")==task,s)
    s,b=call(base,"GET","/tasks")
    check("list_tasks",s==200 and isinstance(b,dict) and isinstance(b.get("tasks"),list),s)
    s,_=call(base,"POST","/tasks/"+task+"/transition",{"state":"DONE"})
    check("illegal_direct_terminal_rejected",s==409,s)
    s,b=call(base,"POST","/tasks/"+task+"/transition",{"state":"RUNNING"})
    check("start_task",s==200 and isinstance(b,dict) and b.get("state")=="RUNNING",s)
    def finish(_):return call(base,"POST","/tasks/"+task+"/transition",{"state":"DONE"})[0]
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses=list(pool.map(finish,range(2)))
    check("concurrent_terminal_transition",sorted(statuses)==[200,409],statuses)
    s,b=call(base,"GET","/tasks/"+task)
    check("terminal_state_persisted",s==200 and isinstance(b,dict) and b.get("state")=="DONE",s)
    s,_=call(base,"POST","/tasks/"+task+"/transition",{"state":"RUNNING"})
    check("terminal_cannot_reopen",s==409,s)
    s,b=call(base,"GET","/tasks/"+task+"/evidence")
    check("evidence_read",s==200 and isinstance(b,dict) and b.get("id")==task and b.get("evidence")==[],s)
    s,_=call(base,"POST","/tasks",raw=b"{broken")
    check("malformed_json_rejected",s==400,s)
    s,_=call(base,"POST","/tasks",{"id":"bad id"})
    check("invalid_id_rejected",s==400,s)
    s,_=call(base,"POST","/tasks",{"id":"x"*65})
    check("oversized_id_rejected",s==400,s)
    s,_=call(base,"POST","/tasks",{"id":other,"extra":True})
    check("unknown_field_rejected",s==400,s)
    s,_=call(base,"GET","/tasks/does_not_exist_"+suffix)
    check("unknown_task",s==404,s)
    s,_=call(base,"POST","/tasks/"+task+"/transition",{"state":"RUNNING","extra":1})
    check("unknown_transition_field_rejected",s==400,s)
    s,_=call(base,"POST","/tasks",raw=b"{" + b" "*17000 + b"}")
    check("body_limit",s==400,s)
    s,b=call(base,"GET","/tasks/"+task)
    check("no_partial_mutation",s==200 and isinstance(b,dict) and b.get("state")=="DONE",s)
    passed=sum(x["pass"] for x in results)
    print("LEDGER_PUBLIC> RESULT",json.dumps({"passed":passed,"total":len(results),
        "status":"PASS" if passed==len(results) else "FAIL"},sort_keys=True),flush=True)
    return passed==len(results)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--base-url",default="http://127.0.0.1:8765")
    args=parser.parse_args()
    u=urllib.parse.urlsplit(args.base_url)
    if u.scheme!="http" or u.hostname not in ("127.0.0.1","localhost") or u.username or u.password or u.query or u.fragment or u.path not in ("","/"):
        parser.error("only a local loopback HTTP base URL is allowed")
    raise SystemExit(0 if evaluate(args.base_url.rstrip("/")) else 1)
