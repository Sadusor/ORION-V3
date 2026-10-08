"""Calibration: ensure the public evaluator rejects a deliberately broken service.

Runs an ephemeral local HTTP server in-process. Never launches external processes,
touches the filesystem, contacts cloud APIs, or runs a native Work Hand.
"""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
from task_ledger_public_evaluator import evaluate

class BrokenLedger(BaseHTTPRequestHandler):
    def do_GET(self):
        body=b'{"status":"ok"}'
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_POST(self):
        self.do_GET()
    def log_message(self,*args):pass

def main():
    server=ThreadingHTTPServer(("127.0.0.1",0),BrokenLedger)
    worker=Thread(target=server.serve_forever,daemon=True)
    worker.start()
    try:
        result=evaluate("http://127.0.0.1:"+str(server.server_address[1]))
        assert result is False,"defective service incorrectly passed evaluator"
        print("LEDGER_CALIBRATION> BROKEN_FIXTURE_REJECTED PASS",flush=True)
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)

if __name__=="__main__":main()
