"""Task Ledger HTTP contract harness v0.1. Stdlib only.

Runs ONLY the built-in synthetic reference/defective fixtures by default.
Never extracts, imports, launches, or executes cloud-submitted source.
Optional future candidate execution requires a separately approved isolation runner.
"""
import json
import os
import sqlite3
import tempfile
import threading
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import re

ID = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
MAX_BODY = 16384
TRANSITIONS = {"PENDING": {"RUNNING"}, "RUNNING": {"DONE", "FAILED", "CANCELLED"}}

class ReferenceLedger:
    def __init__(self, db_path, defective=False):
        self.db_path, self.defective = db_path, defective
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, state TEXT NOT NULL)")

    def connect(self):
        return sqlite3.connect(self.db_path, timeout=5)

    def handle(self, method, path, raw):
        def reply(code, obj):
            return code, obj
        if path == "/health":
            return reply(200, {"status": "ok"}) if method == "GET" else reply(405, {"error": "method"})
        if path == "/tasks":
            if method == "GET":
                with self.connect() as db:
                    rows = db.execute("SELECT id,state FROM tasks ORDER BY id").fetchall()
                return reply(200, {"tasks": [{"id": a, "state": b} for a, b in rows]})
            if method != "POST":
                return reply(405, {"error": "method"})
        parts = path.strip("/").split("/")
        if path != "/tasks":
            if len(parts) not in (2, 3) or parts[0] != "tasks" or (len(parts) == 3 and parts[2] not in ("transition", "evidence")):
                return reply(404, {"error": "not found"})
            task_id = parts[1]
            if not ID.fullmatch(task_id):
                return reply(400, {"error": "id"})
            if len(parts) == 2 and method != "GET":
                return reply(405, {"error": "method"})
            if len(parts) == 3 and method != ("POST" if parts[2] == "transition" else "GET"):
                return reply(405, {"error": "method"})
        if method == "POST":
            if len(raw) > MAX_BODY:
                return reply(400, {"error": "oversize"})
            try:
                obj = json.loads(raw.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                return reply(400, {"error": "json"})
            if not isinstance(obj, dict):
                return reply(500 if self.defective else 400, {"error": "object"})
            field = "id" if path == "/tasks" else "state"
            if set(obj) != {field} or not isinstance(obj[field], str):
                return reply(400, {"error": "fields"})
            if path == "/tasks":
                if not ID.fullmatch(obj["id"]):
                    return reply(400, {"error": "id"})
                try:
                    with self.connect() as db:
                        db.execute("INSERT INTO tasks VALUES (?, 'PENDING')", (obj["id"],))
                except sqlite3.IntegrityError:
                    return reply(201 if self.defective else 409, {"error": "duplicate"})
                return reply(201, {"id": obj["id"], "state": "PENDING"})
            if obj["state"] not in ("PENDING", "RUNNING", "DONE", "FAILED", "CANCELLED"):
                return reply(400, {"error": "state"})
            with self.connect() as db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT state FROM tasks WHERE id=?", (task_id,)).fetchone()
                if row is None:
                    return reply(404, {"error": "not found"})
                if obj["state"] not in TRANSITIONS.get(row[0], set()):
                    return reply(409, {"error": "transition"})
                cur = db.execute("UPDATE tasks SET state=? WHERE id=? AND state=?", (obj["state"], task_id, row[0]))
                if cur.rowcount != 1:
                    return reply(409, {"error": "conflict"})
            return reply(200, {"id": task_id, "state": obj["state"]})
        with self.connect() as db:
            row = db.execute("SELECT state FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            return reply(404, {"error": "not found"})
        if len(parts) == 3:
            return reply(200, {"id": task_id, "evidence": []})
        return reply(200, {"id": task_id, "state": row[0]})

@contextmanager
def server_for(ledger):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def dispatch(self):
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > MAX_BODY:
                code, obj = 400, {"error": "length"}
            else:
                code, obj = ledger.handle(self.command, self.path, self.rfile.read(length))
            data = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        do_GET = do_POST = do_DELETE = do_PUT = dispatch
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=srv.serve_forever, daemon=True)
    worker.start()
    try:
        yield "http://127.0.0.1:" + str(srv.server_port)
    finally:
        srv.shutdown()
        srv.server_close()
        worker.join(timeout=3)

def request(base, method, path, obj=None, raw=None):
    data = raw if raw is not None else (json.dumps(obj).encode() if obj is not None else None)
    req = Request(base + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=3) as resp:
            return resp.status, json.load(resp)
    except HTTPError as exc:
        return exc.code, json.loads(exc.read())

class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="orion-ledger-fixture-")
        cls.path = os.path.join(cls.tmp.name, "fixture.sqlite3")
        cls.ledger = ReferenceLedger(cls.path)
        cls.ctx = server_for(cls.ledger)
        cls.base = cls.ctx.__enter__()
    @classmethod
    def tearDownClass(cls):
        cls.ctx.__exit__(None, None, None)
        cls.tmp.cleanup()
    def setUp(self):
        with self.ledger.connect() as db:
            db.execute("DELETE FROM tasks")
    def call(self, method, path, obj=None, raw=None):
        return request(self.base, method, path, obj, raw)
    def create(self, id="x"):
        return self.call("POST", "/tasks", {"id": id})
    def transition(self, id, state):
        return self.call("POST", "/tasks/" + id + "/transition", {"state": state})

    def test_01_health(self): self.assertEqual(self.call("GET", "/health")[0], 200)
    def test_02_create(self): self.assertEqual(self.create()[0], 201)
    def test_03_get(self):
        self.create(); self.assertEqual(self.call("GET", "/tasks/x")[1]["state"], "PENDING")
    def test_04_missing(self): self.assertEqual(self.call("GET", "/tasks/unknown")[0], 404)
    def test_05_duplicate(self):
        self.create(); self.assertEqual(self.create()[0], 409)
    def test_06_order(self):
        self.create("z"); self.create("a")
        self.assertEqual([x["id"] for x in self.call("GET", "/tasks")[1]["tasks"]], ["a", "z"])
    def test_07_evidence(self):
        self.create(); self.assertEqual(self.call("GET", "/tasks/x/evidence")[1]["evidence"], [])
    def test_08_missing_evidence(self): self.assertEqual(self.call("GET", "/tasks/x/evidence")[0], 404)
    def test_09_running(self):
        self.create(); self.assertEqual(self.transition("x", "RUNNING")[0], 200)
    def test_10_done(self):
        self.create(); self.transition("x", "RUNNING"); self.assertEqual(self.transition("x", "DONE")[0], 200)
    def test_11_failed(self):
        self.create(); self.transition("x", "RUNNING"); self.assertEqual(self.transition("x", "FAILED")[0], 200)
    def test_12_cancelled(self):
        self.create(); self.transition("x", "RUNNING"); self.assertEqual(self.transition("x", "CANCELLED")[0], 200)
    def test_13_illegal_pending_done(self):
        self.create(); self.assertEqual(self.transition("x", "DONE")[0], 409)
    def test_14_terminal_immutable(self):
        self.create(); self.transition("x", "RUNNING"); self.transition("x", "DONE")
        self.assertEqual(self.transition("x", "RUNNING")[0], 409)
    def test_15_invalid_state(self):
        self.create(); self.assertEqual(self.transition("x", "BOGUS")[0], 400)
    def test_16_invalid_id(self): self.assertEqual(self.create("../oops")[0], 400)
    def test_17_long_id(self): self.assertEqual(self.create("a"*65)[0], 400)
    def test_18_empty_id(self): self.assertEqual(self.create("")[0], 400)
    def test_19_extra_fields(self): self.assertEqual(self.call("POST", "/tasks", {"id":"x","foo":1})[0], 400)
    def test_20_nonobject_list(self): self.assertEqual(self.call("POST", "/tasks", raw=b"[]")[0], 400)
    def test_21_nonobject_null(self): self.assertEqual(self.call("POST", "/tasks", raw=b"null")[0], 400)
    def test_22_nonobject_string(self): self.assertEqual(self.call("POST", "/tasks", raw=b'"abc"')[0], 400)
    def test_23_bad_json(self): self.assertEqual(self.call("POST", "/tasks", raw=b"{")[0], 400)
    def test_24_oversize(self): self.assertEqual(self.call("POST", "/tasks", raw=b"x"*16385)[0], 400)
    def test_25_unknown_route(self): self.assertEqual(self.call("GET", "/bogus")[0], 404)
    def test_26_wrong_method(self): self.assertEqual(self.call("DELETE", "/tasks")[0], 405)
    def test_27_wrong_transition_method(self):
        self.create(); self.assertEqual(self.call("GET", "/tasks/x/transition")[0], 405)
    def test_28_restart_persistence(self):
        self.create()
        other = ReferenceLedger(self.path)
        self.assertEqual(other.handle("GET", "/tasks/x", b"")[1]["state"], "PENDING")
    def test_29_atomic_competition(self):
        self.create(); self.transition("x", "RUNNING")
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda state: self.transition("x", state)[0], ["DONE"]*8))
        self.assertEqual(results.count(200), 1)
        self.assertEqual(results.count(409), 7)
    def test_30_wrong_id_type(self): self.assertEqual(self.create(42)[0], 400)
    def test_31_wrong_state_type(self):
        self.create(); self.assertEqual(self.transition("x", ["RUNNING"])[0], 400)

class FixtureSensitivityTests(unittest.TestCase):
    def test_known_bad_fixture_is_caught(self):
        with tempfile.TemporaryDirectory(prefix="orion-ledger-bad-") as tmp:
            bad = ReferenceLedger(os.path.join(tmp, "bad.sqlite3"), defective=True)
            with server_for(bad) as base:
                first = request(base, "POST", "/tasks", {"id": "dup"})[0]
                duplicate = request(base, "POST", "/tasks", {"id": "dup"})[0]
                malformed = request(base, "POST", "/tasks", raw=b"[]")[0]
                self.assertEqual((first, duplicate, malformed), (201, 201, 500))
                self.assertNotEqual(duplicate, 409)
                self.assertNotEqual(malformed, 400)

if __name__ == "__main__":
    unittest.main(verbosity=2)
