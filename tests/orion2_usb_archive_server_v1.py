"""Disposable USB-reverse archive server; test-only. Never accesses live ORION."""
import argparse
import json
import pathlib
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from src.orion_v3.modules.history_archive_backend_composition_v1 import build_archive_route_fixture
from src.orion_v3.modules.history_archive_scoped_credentials_v1 import ProjectDeviceCredentialsV1
from src.orion_v3.modules.history_archive_owner_capability_v1 import OwnerCapabilityV1
from src.orion_v3.modules.history_archive_route_adapter_v1 import SYNC_PATH, DELETE_PATH

PROJECT = "orion2-usb-qualification"
class Server(ThreadingHTTPServer):
    allow_reuse_address = True

def run(root, ready):
    root = pathlib.Path(root)
    if not root.is_dir() or any(root.iterdir()):
        raise RuntimeError("Require an empty disposable directory")
    secret = ProjectDeviceCredentialsV1(root / "device-credentials.sqlite3").enroll(
        project_id=PROJECT, physically_confirmed=True)
    owner = OwnerCapabilityV1(root / "owner-capability").enroll(physically_confirmed=True)
    adapter = build_archive_route_fixture(root=root, project_id=PROJECT, enabled=True)
    state = {"synced": False, "deleted": False}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass
        def do_POST(self):
            try:
                n = int(self.headers.get("Content-Length", "0"))
                if self.path != SYNC_PATH or not 0 < n < 100_000:
                    self.send_error(404)
                    return
                body = json.loads(self.rfile.read(n))
                code, result = adapter.dispatch(
                    path=SYNC_PATH, body=body,
                    device_token=self.headers.get("X-Orion-Archive-Device", ""))
                if code == 200 and not state["synced"]:
                    state["synced"] = True
                    delete_code, _ = adapter.dispatch(
                        path=DELETE_PATH, body={"project_id": PROJECT,
                            "conversation_id": "usb-q-1"}, owner_token=owner)
                    if delete_code != 200:
                        raise RuntimeError("Owner deletion failed")
                    state["deleted"] = True
                payload = json.dumps(result).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception:
                self.send_error(503)
    http = Server(("127.0.0.1", 18765), Handler)
    pathlib.Path(ready).write_text(json.dumps({"device_secret": secret, "port": 18765}), encoding="utf-8")
    print("ORION2_USB_SERVER_READY", flush=True)
    try:
        http.serve_forever(poll_interval=0.1)
    finally:
        http.server_close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--ready", required=True)
    args = parser.parse_args()
    run(args.root, args.ready)
