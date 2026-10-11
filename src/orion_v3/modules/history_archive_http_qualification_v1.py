"""Isolated HTTP qualification server for HistoryArchive integration.

NOT the live product_server, not installed as a service. Only caller-provided
temp directories and explicit project. Use on loopback in a test harness only.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .history_archive_backend_composition_v1 import build_archive_route_fixture
from .history_archive_route_adapter_v1 import SYNC_PATH, DELETE_PATH


def make_handler(*, root, project_id, enabled=False):
    adapter = build_archive_route_fixture(root=root, project_id=project_id, enabled=enabled)

    class ArchiveHandler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            if self.path not in (SYNC_PATH, DELETE_PATH) or not enabled:
                return self.respond(404, {"ok": False})
            try:
                n = int(self.headers.get("Content-Length", "0"))
                if not 0 < n <= 2_800_000:
                    return self.respond(413, {"ok": False})
                body = json.loads(self.rfile.read(n))
                status, result = adapter.dispatch(
                    path=self.path,
                    body=body,
                    device_token=self.headers.get("X-Orion-Archive-Device", ""),
                    owner_token=self.headers.get("X-Orion-Archive-Owner", ""),
                )
                return self.respond(status, result)
            except (ValueError, TypeError, json.JSONDecodeError):
                return self.respond(400, {"ok": False})
            except Exception:
                return self.respond(503, {"ok": False})

        def respond(self, status, obj):
            payload = json.dumps(obj).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    return ArchiveHandler


def bind_loopback(*, root, project_id, enabled=False):
    return ThreadingHTTPServer(("127.0.0.1", 0), make_handler(
        root=root, project_id=project_id, enabled=enabled))
