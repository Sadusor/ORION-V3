"""Known-good calibration fixture for Task Ledger v0.1 public evaluator.

Ephemeral in-memory state; intentionally not a benchmark submission and not a
durability/crash recovery reference. The evaluator's public checks alone do not
prove SQLite persistence or crash safety.
"""
from __future__ import annotations
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Thread
from urllib.parse import unquote, urlsplit
from task_ledger_public_evaluator import evaluate

tasks={}
lock=Lock()
valid=re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
def valid_id(value):return isinstance(value,str) and valid.fullmatch(value) is not None
class GoodLedger(BaseHTTPRequestHandler):
    def send_json(self,status,value):
        raw=json.dumps(value,separators=(",",":")).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
    def route(self):
        path=urlsplit(self.path).path
        return [unquote(x) for x in path.strip("/").split("/")]
    def do_GET(self):
        parts=self.route()
        if parts==["health"]:return self.send_json(200,{"status":"ok"})
        with lock:
            if parts==["tasks"]:
                return self.send_json(200,{"tasks":[{"id":k,"state":tasks[k]} for k in sorted(tasks)]})
            if len(parts)>=2 and parts[0]=="tasks":
                ident=parts[1]
                if not valid_id(ident):return self.send_json(400,{"error":"invalid id"})
                if ident not in tasks:return self.send_json(404,{"error":"not found"})
                if len(parts)==2:return self.send_json(200,{"id":ident,"state":tasks[ident]})
                if len(parts)==3 and parts[2]=="evidence":
                    return self.send_json(200,{"id":ident,"evidence":[]})
        return self.send_json(404,{"error":"not found"})
    def do_POST(self):
        parts=self.route()
        length=self.headers.get("Content-Length")
        try:
            count=int(length)
            if count<0 or count>16384:raise ValueError("body size")
            raw=self.rfile.read(count)
            data=json.loads(raw)
            if not isinstance(data,dict):raise ValueError("object required")
        except (ValueError,TypeError,UnicodeDecodeError):
            return self.send_json(400,{"error":"invalid JSON"})
        with lock:
            if parts==["tasks"]:
                if set(data)!={"id"} or not valid_id(data["id"]):
                    return self.send_json(400,{"error":"invalid task"})
                ident=data["id"]
                if ident in tasks:return self.send_json(409,{"error":"duplicate"})
                tasks[ident]="PENDING"
                return self.send_json(201,{"id":ident,"state":"PENDING"})
            if len(parts)==3 and parts[0]=="tasks" and parts[2]=="transition":
                ident=parts[1]
                if not valid_id(ident):return self.send_json(400,{"error":"invalid id"})
                if set(data)!={"state"} or not isinstance(data["state"],str) or data["state"] not in ("RUNNING","DONE","FAILED","CANCELLED"):
                    return self.send_json(400,{"error":"invalid transition"})
                if ident not in tasks:return self.send_json(404,{"error":"not found"})
                old=tasks[ident]
                new=data["state"]
                if not ((old=="PENDING" and new=="RUNNING") or (old=="RUNNING" and new in ("DONE","FAILED","CANCELLED"))):
                    return self.send_json(409,{"error":"illegal transition"})
                tasks[ident]=new
                return self.send_json(200,{"id":ident,"state":new})
        return self.send_json(404,{"error":"not found"})
    def log_message(self,*args):pass

def main():
    server=ThreadingHTTPServer(("127.0.0.1",0),GoodLedger)
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        assert evaluate("http://127.0.0.1:"+str(server.server_address[1]))
        print("LEDGER_CALIBRATION> GOOD_FIXTURE_ACCEPTED PASS",flush=True)
        print("LEDGER_CALIBRATION> PERSISTENCE_AND_CRASH_RECOVERY_NOT_TESTED",flush=True)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

if __name__=="__main__":main()
