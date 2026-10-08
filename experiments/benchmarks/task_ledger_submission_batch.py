"""Public, black-box batch evaluator for separately delivered Task Ledger submissions.

Run: python task_ledger_submission_batch.py --submission PATH
Submission must contain task_ledger/__main__.py and >=20 discoverable unittest
methods (or pytest-style test_ functions). The public evaluator does not run
untrusted developer tests; they are counted, not executed.
Only use trusted/disposable submissions inside an externally enforced sandbox.
"""
from __future__ import annotations
import argparse, ast, json, os, re, socket, subprocess, sys, tempfile, time
from pathlib import Path
from task_ledger_public_evaluator import call, evaluate

def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0))
        return sock.getsockname()[1]

def count_tests(root):
    count=0
    for path in root.rglob("test*.py"):
        if any(part in (".git","__pycache__", ".venv","venv") for part in path.parts):
            continue
        try:tree=ast.parse(path.read_text(encoding="utf-8"))
        except (OSError,UnicodeError,SyntaxError):continue
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                count+=1
    return count

def start(root,db,port):
    env=dict(os.environ,TASK_LEDGER_DB=str(db),PYTHONPATH=str(root),PYTHONDONTWRITEBYTECODE="1")
    return subprocess.Popen([sys.executable,"-B","-m","task_ledger","--host","127.0.0.1","--port",str(port)],
                            cwd=str(root),env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)

def wait_ready(proc,base):
    for _ in range(80):
        if proc.poll() is not None:raise RuntimeError("candidate exited before ready: "+str(proc.returncode))
        try:
            if call(base,"GET","/health")[0]==200:return
        except Exception:pass
        time.sleep(.1)
    raise RuntimeError("candidate readiness timeout")

def kill(proc):
    if proc.poll() is None:proc.kill()
    proc.wait(timeout=10)
    if proc.stderr:proc.stderr.close()

def run(root):
    root=root.resolve(strict=True)
    if not root.is_dir() or not (root/"task_ledger"/"__main__.py").is_file():
        raise ValueError("submission must be a directory containing task_ledger/__main__.py")
    test_count=count_tests(root)
    print("LEDGER_SUBMISSION> DEVELOPER_TESTS_FOUND",test_count,flush=True)
    with tempfile.TemporaryDirectory(prefix="orion-ledger-submission-") as tmp:
        db=Path(tmp)/"candidate.sqlite3"
        port=free_port()
        base="http://127.0.0.1:"+str(port)
        proc=start(root,db,port)
        try:
            wait_ready(proc,base)
            if not evaluate(base):raise AssertionError("public API evaluator failed")
            print("LEDGER_SUBMISSION> PUBLIC_API_PASS",flush=True)
            ident="submission_restart_probe"
            assert call(base,"POST","/tasks",{"id":ident})[0]==201
            assert call(base,"POST","/tasks/"+ident+"/transition",{"state":"RUNNING"})[0]==200
        finally:kill(proc)
        proc=start(root,db,port)
        try:
            wait_ready(proc,base)
            status,data=call(base,"GET","/tasks/submission_restart_probe")
            assert status==200 and isinstance(data,dict) and data.get("state")=="RUNNING",(status,data)
            print("LEDGER_SUBMISSION> DURABLE_RESTART_PASS",flush=True)
            assert call(base,"POST","/tasks/"+ident+"/transition",{"state":"DONE"})[0]==200
            assert call(base,"POST","/tasks/"+ident+"/transition",{"state":"RUNNING"})[0]==409
            print("LEDGER_SUBMISSION> TERMINAL_RESTART_PASS",flush=True)
        finally:kill(proc)
    assert test_count>=20,"submission has fewer than 20 developer-visible tests"
    print("LEDGER_SUBMISSION> PUBLIC_BATCH_PASS",flush=True)
    print("LEDGER_SUBMISSION> NOT_HIDDEN_SCORE_NOT_NATIVE_ISOLATION",flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--submission",required=True,type=Path)
    args=p.parse_args()
    try:run(args.submission)
    except Exception as error:
        print("LEDGER_SUBMISSION> PUBLIC_BATCH_FAIL",type(error).__name__,str(error)[:300],flush=True)
        raise SystemExit(1)
