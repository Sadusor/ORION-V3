"""Disposable SQLite Task Ledger reference, NOT a model submission or production ORION module."""
from __future__ import annotations
import argparse, json, re, sqlite3, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

ID=re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
STATES={"RUNNING","DONE","FAILED","CANCELLED"}
def good_id(x):return isinstance(x,str) and ID.fullmatch(x) is not None
class Ledger(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,db):
        self.db=db
        with self.connect() as c:
            c.execute("CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY,state TEXT NOT NULL)")
        super().__init__(address,Handler)
    def connect(self):
        c=sqlite3.connect(self.db,timeout=5)
        c.execute("PRAGMA busy_timeout=5000")
        return c
class Handler(BaseHTTPRequestHandler):
    def reply(self,status,obj):
        data=json.dumps(obj,separators=(",",":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def parts(self):
        return [unquote(p) for p in urlsplit(self.path).path.strip("/").split("/")]
    def do_GET(self):
        p=self.parts()
        if p==["health"]:return self.reply(200,{"status":"ok"})
        with self.server.connect() as c:
            if p==["tasks"]:
                rows=c.execute("SELECT id,state FROM tasks ORDER BY id").fetchall()
                return self.reply(200,{"tasks":[{"id":i,"state":s} for i,s in rows]})
            if len(p) in (2,3) and p[0]=="tasks":
                if not good_id(p[1]):return self.reply(400,{"error":"invalid id"})
                row=c.execute("SELECT state FROM tasks WHERE id=?",(p[1],)).fetchone()
                if row is None:return self.reply(404,{"error":"not found"})
                if len(p)==2:return self.reply(200,{"id":p[1],"state":row[0]})
                if p[2]=="evidence":return self.reply(200,{"id":p[1],"evidence":[]})
        return self.reply(404,{"error":"not found"})
    def do_POST(self):
        p=self.parts()
        if not (p==["tasks"] or len(p)==3 and p[0]=="tasks" and p[2]=="transition"):
            return self.reply(404,{"error":"not found"})
        try:
            size=int(self.headers.get("Content-Length","-1"))
            if not 0<size<=16384:raise ValueError("size")
            body=json.loads(self.rfile.read(size))
            if not isinstance(body,dict):raise ValueError("object")
        except (ValueError,UnicodeDecodeError):
            return self.reply(400,{"error":"invalid JSON"})
        if p==["tasks"]:
            if set(body)!={"id"} or not good_id(body["id"]):
                return self.reply(400,{"error":"invalid task"})
            try:
                with self.server.connect() as c:
                    c.execute("INSERT INTO tasks VALUES(?,?)",(body["id"],"PENDING"))
            except sqlite3.IntegrityError:
                return self.reply(409,{"error":"duplicate"})
            return self.reply(201,{"id":body["id"],"state":"PENDING"})
        if not good_id(p[1]):return self.reply(400,{"error":"invalid id"})
        if set(body)!={"state"} or not isinstance(body["state"],str) or body["state"] not in STATES:
            return self.reply(400,{"error":"invalid transition"})
        new=body["state"]
        allowed_from="PENDING" if new=="RUNNING" else "RUNNING"
        with self.server.connect() as c:
            cursor=c.execute("UPDATE tasks SET state=? WHERE id=? AND state=?",(new,p[1],allowed_from))
            if cursor.rowcount==1:return self.reply(200,{"id":p[1],"state":new})
            exists=c.execute("SELECT 1 FROM tasks WHERE id=?",(p[1],)).fetchone()
        return self.reply(409 if exists else 404,{"error":"illegal transition" if exists else "not found"})
    def log_message(self,*args):pass

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--host",default="127.0.0.1")
    parser.add_argument("--port",type=int,required=True)
    args=parser.parse_args()
    if args.host!="127.0.0.1":parser.error("loopback only")
    db=os.environ.get("TASK_LEDGER_DB")
    if not db:parser.error("TASK_LEDGER_DB is required")
    server=Ledger((args.host,args.port),db)
    print("LEDGER_REFERENCE> READY",flush=True)
    try:server.serve_forever()
    finally:server.server_close()
if __name__=="__main__":main()
