**task_ledger/__init__.py**
```python
"""
Task Ledger – a tiny HTTP service for managing tasks and their state
according to the “Task Ledger HTTP Contract — Benchmark A v0.1”.
"""

__all__ = ["app", "run"]
```

**task_ledger/db.py**
```python
import os
import sqlite3
from contextlib import contextmanager
from typing import Generator, List, Tuple, Optional

DB_ENV = "TASK_LEDGER_DB"
DEFAULT_DB = ":memory:"  # fallback for tests; real runs should set the env var


def _connect() -> sqlite3.Connection:
    path = os.getenv(DB_ENV, DEFAULT_DB)
    conn = sqlite3.connect(path, isolation_level="EXCLUSIVE", timeout=5.0)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create tables if they do not exist."""
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                state TEXT NOT NULL CHECK(state IN ('PENDING','RUNNING','DONE','FAILED','CANCELLED'))
            );
            """
        )
        conn.commit()


@contextmanager
def transaction() -> Generator[sqlite3.Connection, None, None]:
    """Yield a connection with a transaction that is committed on success."""
    conn = _connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def create_task(task_id: str) -> None:
    with transaction() as conn:
        conn.execute("INSERT INTO tasks (id, state) VALUES (?, 'PENDING')", (task_id,))


def get_task(task_id: str) -> Optional[Tuple[str, str]]:
    with _connect() as conn:
        cur = conn.execute("SELECT id, state FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        return row if row else None


def list_tasks() -> List[Tuple[str, str]]:
    with _connect() as conn:
        cur = conn.execute("SELECT id, state FROM tasks ORDER BY id ASC")
        return cur.fetchall()


def update_state(task_id: str, from_state: str, to_state: str) -> bool:
    """
    Atomically change state from `from_state` to `to_state`.
    Returns True if the transition succeeded, False if the current state
    was not `from_state` (i.e. conflict).
    """
    with transaction() as conn:
        cur = conn.execute(
            "UPDATE tasks SET state = ? WHERE id = ? AND state = ?",
            (to_state, task_id, from_state),
        )
        return cur.rowcount == 1
```

**task_ledger/app.py**
```python
import json
import re
from io import BytesIO
from urllib.parse import parse_qs, urlparse, unquote

from wsgiref.util import request_uri

from . import db

# --------------------------------------------------------------------------- #
# Constants & helpers
# --------------------------------------------------------------------------- #

ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
MAX_BODY = 16 * 1024  # 16 KiB

ALLOWED_TRANSITIONS = {
    "PENDING": {"RUNNING"},
    "RUNNING": {"DONE", "FAILED", "CANCELLED"},
}

JSON_MIME = "application/json"


def json_response(start_response, status_code, payload):
    body = json.dumps(payload).encode("utf-8")
    headers = [("Content-Type", JSON_MIME), ("Content-Length", str(len(body)))]
    start_response(status_code, headers)
    return [body]


def error(start_response, code, message):
    return json_response(start_response, f"{code} {message}", {"error": message})


def read_json(environ):
    try:
        length = int(environ.get("CONTENT_LENGTH", "0"))
    except ValueError:
        length = 0
    if length > MAX_BODY:
        raise ValueError("Payload too large")
    body = environ["wsgi.input"].read(length)
    if not body:
        raise ValueError("Empty body")
    try:
        return json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"Malformed JSON: {exc}") from exc


def validate_id(task_id: str):
    if not ID_RE.fullmatch(task_id):
        raise ValueError("Invalid task id")


# --------------------------------------------------------------------------- #
# WSGI application
# --------------------------------------------------------------------------- #

def app(environ, start_response):
    path = urlparse(environ.get("PATH_INFO", "")).path
    method = environ["REQUEST_METHOD"]

    # Health endpoint – must be after DB init
    if path == "/health" and method == "GET":
        try:
            db.init_db()
        except Exception:
            return error(start_response, 500, "Database init failed")
        return json_response(start_response, "200 OK", {"status": "ok"})

    # ------------------------------------------------------------------- #
    # /tasks collection
    # ------------------------------------------------------------------- #
    if path == "/tasks":
        if method == "POST":
            try:
                payload = read_json(environ)
                if set(payload.keys()) != {"id"}:
                    raise ValueError("Unexpected fields")
                task_id = payload["id"]
                validate_id(task_id)
            except ValueError as exc:
                return error(start_response, 400, str(exc))

            try:
                db.create_task(task_id)
            except sqlite3.IntegrityError:
                return error(start_response, 409, "Task already exists")
            return json_response(start_response, "201 Created", {"id": task_id, "state": "PENDING"})

        if method == "GET":
            tasks = [{"id": tid, "state": st} for tid, st in db.list_tasks()]
            return json_response(start_response, "200 OK", {"tasks": tasks})

        return error(start_response, 405, "Method Not Allowed")

    # ------------------------------------------------------------------- #
    # /tasks/{id} and sub‑resources
    # ------------------------------------------------------------------- #
    parts = path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "tasks":
        raw_id = unquote(parts[1])
        try:
            validate_id(raw_id)
        except ValueError:
            return error(start_response, 400, "Invalid task id")

        # /tasks/{id}
        if len(parts) == 2:
            if method == "GET":
                task = db.get_task(raw_id)
                if not task:
                    return error(start_response, 404, "Not found")
                return json_response(start_response, "200 OK", {"id": task[0], "state": task[1]})
            return error(start_response, 405, "Method Not Allowed")

        # /tasks/{id}/transition
        if len(parts) == 3 and parts[2] == "transition":
            if method != "POST":
                return error(start_response, 405, "Method Not Allowed")
            try:
                payload = read_json(environ)
                if set(payload.keys()) != {"state"}:
                    raise ValueError("Unexpected fields")
                new_state = payload["state"]
                if new_state not in {"PENDING", "RUNNING", "DONE", "FAILED", "CANCELLED"}:
                    raise ValueError("Invalid target state")
            except ValueError as exc:
                return error(start_response, 400, str(exc))

            task = db.get_task(raw_id)
            if not task:
                return error(start_response, 404, "Not found")
            cur_state = task[1]

            # Validate transition
            allowed = ALLOWED_TRANSITIONS.get(cur_state, set())
            if new_state not in allowed:
                return error(start_response, 409, "Illegal transition")

            succeeded = db.update_state(raw_id, cur_state, new_state)
            if not succeeded:
                return error(start_response, 409, "Conflict")
            return json_response(start_response, "200 OK", {"id": raw_id, "state": new_state})

        # /tasks/{id}/evidence
        if len(parts) == 3 and parts[2] == "evidence":
            if method != "GET":
                return error(start_response, 405, "Method Not Allowed")
            task = db.get_task(raw_id)
            if not task:
                return error(start_response, 404, "Not found")
            return json_response(start_response, "200 OK", {"id": raw_id, "evidence": []})

    # ------------------------------------------------------------------- #
    # Unknown route
    # ------------------------------------------------------------------- #
    return error(start_response, 404, "Not found")
```

**task_ledger/__main__.py**
```python
import argparse
import os
import sys
from wsgiref.simple_server import make_server, WSGIRequestHandler, WSGIServer

from . import app, db

def run(host: str, port: int):
    # Initialise DB before serving
    db.init_db()
    httpd = make_server(host, port, app.app, server_class=WSGIServer,
                        handler_class=WSGIRequestHandler)
    print(f"Task Ledger listening on http://{host}:{port}", file=sys.stderr)
    httpd.serve_forever()


def main():
    parser = argparse.ArgumentParser(description="Task Ledger service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
```

**setup.cfg**
```ini
[metadata]
name = task_ledger
version = 0.1.0
description = Minimal task ledger HTTP service for Benchmark A v0.1
author = Benchmark Author
license = MIT
long_description = file: README.md
long_description_content_type = text/markdown
classifiers =
    Programming Language :: Python :: 3
    License :: OSI Approved :: MIT License

[options]
packages = find:
python_requires = >=3.8
```

**README.md**
```markdown
# Task Ledger

A tiny HTTP service that implements the *Task Ledger HTTP Contract — Benchmark A v0.1*.

Run with:

```bash
export TASK_LEDGER_DB=/tmp/tasks.db
python -m task_ledger --host 127.0.0.1 --port 8000
```

The service uses only the Python standard library.
```

**tests/__init__.py**
```python
# empty – makes the directory a package
```

**tests/test_api.py**
```python
import os
import json
import threading
import time
import unittest
import urllib.request
import urllib.error
import urllib.parse
import subprocess
import tempfile
import socket

HOST = "127.0.0.1"


def free_port():
    s = socket.socket()
    s.bind((HOST, 0))
    _, port = s.getsockname()
    s.close()
    return port


class TaskLedgerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_file = tempfile.NamedTemporaryFile(delete=False)
        os.environ["TASK_LEDGER_DB"] = cls.db_file.name
        cls.port = free_port()
        cls.proc = subprocess.Popen(
            [sys.executable, "-m", "task_ledger", "--host", HOST, "--port", str(cls.port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # wait for server to be ready
        for _ in range(30):
            try:
                urllib.request.urlopen(f"http://{HOST}:{cls.port}/health")
                break
            except Exception:
                time.sleep(0.1)
        else:
            raise RuntimeError("Server failed to start")

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait()
        os.unlink(cls.db_file.name)

    # --------------------------------------------------------------------- #
    # Helper methods
    # --------------------------------------------------------------------- #
    def request(self, method, path, data=None, headers=None):
        url = f"http://{HOST}:{self.port}{path}"
        if data is not None:
            data = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Accept", "application/json")
        req.add_header("Content-Type", "application/json")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        try:
            with urllib.request.urlopen(req) as resp:
                body = resp.read()
                return resp.getcode(), json.loads(body.decode())
        except urllib.error.HTTPError as e:
            body =