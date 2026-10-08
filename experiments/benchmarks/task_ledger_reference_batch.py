"""Run the real disposable reference service, public HTTP evaluator and restart checks."""
from __future__ import annotations
import os, socket, subprocess, sys, tempfile, time
from pathlib import Path
from task_ledger_public_evaluator import call, evaluate
from task_ledger_batch_calibration import main as calibrate

def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1",0))
        return s.getsockname()[1]

def launch(db,port):
    env=dict(os.environ,TASK_LEDGER_DB=str(db))
    return subprocess.Popen([sys.executable,"-u",str(Path(__file__).with_name("task_ledger_reference.py")),
                             "--host","127.0.0.1","--port",str(port)],
                            env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)

def ready(base,proc):
    for _ in range(60):
        if proc.poll() is not None:raise RuntimeError("service exited "+str(proc.returncode))
        try:
            if call(base,"GET","/health")[0]==200:return
        except Exception:pass
        time.sleep(.1)
    raise RuntimeError("service startup timeout")

def stop(proc):
    if proc.poll() is None:
        proc.kill()
    proc.wait(timeout=10)
    if proc.stderr:proc.stderr.close()

def main():
    calibrate()
    with tempfile.TemporaryDirectory(prefix="orion-ledger-reference-") as temp:
        db=Path(temp)/"ledger.db"
        port=free_port()
        base="http://127.0.0.1:"+str(port)
        proc=launch(db,port)
        try:
            ready(base,proc)
            assert evaluate(base),"reference failed public HTTP checks"
            print("LEDGER_REFERENCE> PUBLIC_HTTP_19_OF_19_PASS",flush=True)
            ident="restart_proof"
            assert call(base,"POST","/tasks",{"id":ident})[0]==201
            assert call(base,"POST","/tasks/"+ident+"/transition",{"state":"RUNNING"})[0]==200
        finally:stop(proc)
        print("LEDGER_REFERENCE> PROCESS_KILLED_FOR_RESTART",flush=True)
        proc=launch(db,port)
        try:
            ready(base,proc)
            status,body=call(base,"GET","/tasks/restart_proof")
            assert status==200 and body["state"]=="RUNNING",(status,body)
            print("LEDGER_REFERENCE> DURABLE_RESTART_PASS",flush=True)
            assert call(base,"POST","/tasks/restart_proof/transition",{"state":"DONE"})[0]==200
            assert call(base,"POST","/tasks/restart_proof/transition",{"state":"RUNNING"})[0]==409
            print("LEDGER_REFERENCE> TERMINAL_AFTER_RESTART_PASS",flush=True)
        finally:stop(proc)
    print("LEDGER_REFERENCE> BATCH_ALL_PASS",flush=True)
    print("LEDGER_REFERENCE> NOT_A_MODEL_SUBMISSION_OR_NATIVE_HAND_QUALIFICATION",flush=True)
if __name__=="__main__":main()
