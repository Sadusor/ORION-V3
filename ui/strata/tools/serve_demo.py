"""Serve the DEMO / MOCK build locally (no ORION needed):  python tools/serve_demo.py   ->  http://127.0.0.1:8800/demo.html
This plain static server is for development only. It is NOT how ORION serves V3 (see INTEGRATION.md)."""
import functools, http.server, pathlib, socketserver
root = pathlib.Path(__file__).resolve().parent.parent
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def end_headers(self): self.send_header("Cache-Control", "no-store"); super().end_headers()
with socketserver.TCPServer(("127.0.0.1", 8800), functools.partial(H, directory=str(root))) as s:
    print("DEMO / MOCK BACKEND at http://127.0.0.1:8800/demo.html   (Ctrl+C to stop)"); s.serve_forever()
