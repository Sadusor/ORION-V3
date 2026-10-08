"""Batch independent Task Ledger calibration, disposable SQLite durability and concurrency.

No ORION native execution, no cloud calls, no external networking.
"""
from __future__ import annotations
import json, sqlite3, subprocess, sys, tempfile, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from task_ledger_evaluator_calibration import main as broken
from task_ledger_good_fixture_calibration import main as good

def sqlite_checks():
    with tempfile.TemporaryDirectory(prefix="orion-ledger-batch-") as temp:
        db=Path(temp)/"tasks.sqlite3"
        def connect():
            con=sqlite3.connect(str(db),timeout=5,isolation_level=None)
            con.execute("PRAGMA journal_mode=WAL")
            con.execute("PRAGMA busy_timeout=5000")
            return con
        with connect() as c:
            c.execute("CREATE TABLE tasks(id TEXT PRIMARY KEY, state TEXT NOT NULL)")
            c.execute("INSERT INTO tasks VALUES('a','PENDING')")
        with connect() as c:
            assert c.execute("SELECT state FROM tasks WHERE id='a'").fetchone()[0]=="PENDING"
        print("LEDGER_BATCH> SQLITE_REOPEN_PERSISTENCE PASS",flush=True)
        barrier=threading.Barrier(2)
        def compete(_):
            c=connect()
            try:
                barrier.wait(timeout=5)
                cursor=c.execute("UPDATE tasks SET state='RUNNING' WHERE id='a' AND state='PENDING'")
                return cursor.rowcount
            finally:c.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes=list(pool.map(compete,range(2)))
        assert sorted(outcomes)==[0,1],outcomes
        with connect() as c:
            assert c.execute("SELECT state FROM tasks WHERE id='a'").fetchone()[0]=="RUNNING"
        print("LEDGER_BATCH> SQLITE_ATOMIC_CONCURRENT_TRANSITION PASS",flush=True)
        with connect() as c:
            try:
                c.execute("BEGIN IMMEDIATE")
                c.execute("UPDATE tasks SET state='DONE' WHERE id='a'")
                raise RuntimeError("simulate interrupted transaction")
            except RuntimeError:
                c.execute("ROLLBACK")
        with connect() as c:
            assert c.execute("SELECT state FROM tasks WHERE id='a'").fetchone()[0]=="RUNNING"
            assert c.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        print("LEDGER_BATCH> SQLITE_ROLLBACK_AND_INTEGRITY PASS",flush=True)
        # Abruptly terminate a separate Python process with an open transaction.
        child='''import sqlite3,sys,os
c=sqlite3.connect(sys.argv[1],isolation_level=None)
c.execute("BEGIN IMMEDIATE")
c.execute("UPDATE tasks SET state='FAILED' WHERE id='a'")
os._exit(7)
'''
        run=subprocess.run([sys.executable,"-c",child,str(db)],capture_output=True,text=True,timeout=15)
        assert run.returncode==7,(run.returncode,run.stderr)
        with connect() as c:
            assert c.execute("SELECT state FROM tasks WHERE id='a'").fetchone()[0]=="RUNNING"
            assert c.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        print("LEDGER_BATCH> SQLITE_ABRUPT_CHILD_EXIT_RECOVERY PASS",flush=True)

def main():
    print("LEDGER_BATCH> START",flush=True)
    broken()
    good()
    sqlite_checks()
    print("LEDGER_BATCH> ALL_6_CALIBRATION_GATES_PASS",flush=True)
    print("LEDGER_BATCH> NOT_A_MODEL_SCORE_NOT_NATIVE_HAND_QUALIFICATION",flush=True)

if __name__=="__main__":main()
