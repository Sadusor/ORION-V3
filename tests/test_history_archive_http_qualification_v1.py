import tempfile
import threading
import unittest
import json
from pathlib import Path
from http.client import HTTPConnection
from src.orion_v3.modules.history_archive_http_qualification_v1 import bind_loopback

class HttpQualificationTests(unittest.TestCase):
    def test_disabled_is_404_over_real_http(self):
        with tempfile.TemporaryDirectory() as d:
            server = bind_loopback(root=Path(d), project_id="p", enabled=False)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                conn = HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
                conn.request("POST", "/api/history-archive/device-sync",
                             json.dumps({"project_id":"p"}))
                reply = conn.getresponse()
                self.assertEqual(reply.status, 404)
                reply.read()
                conn.close()
            finally:
                server.shutdown()
                server.server_close()

if __name__ == "__main__":
    unittest.main()
