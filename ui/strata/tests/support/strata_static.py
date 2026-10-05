"""STRATA V3 static-file serving for ORION.  ADDITIVE and PRESENTATION-ONLY.

In ORION-V3 this copy is TEST SUPPORT ONLY. It is not wired to V1 Remote or any production backend. It serves the frontend under /v3/ and nothing else:
  - no API routes, no authentication logic, no execution logic, no state;
  - reads files only from <repo>/ui/strata, allowlisted extensions only;
  - no directory listings, no dotfiles, no path traversal, no symlink escapes;
  - never serves tests/, tools/, docs/, demo.html or bridge/mock-bridge.js (live ORION must never serve mock/demo code);
  - GET only.  Every /api route keeps its existing X-Orion-Token authentication, untouched.

Routes added to ORION (via patches/0001-serve-strata-v3.patch):  GET /v3  (redirect)  and  GET /v3/<file>
Remove V3 completely:  python patches/apply_patch.py --server <server.py> --revert   then delete ui/strata and this file.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote

MOUNT = "/v3"
ROOT = Path(__file__).resolve().parents[2]  # ui/strata (self-contained test support)
TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
    ".json": "application/json",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
}
DENY_DIRS = {"tests", "tools", "docs"}                       # never served
DENY_FILES = {"demo.html", "bridge/mock-bridge.js"}          # mock/demo code is never served by live ORION
MAX_BYTES = 2 * 1024 * 1024
NO_CACHE = "no-store, no-cache, must-revalidate, max-age=0"


def is_strata_path(path: str) -> bool:
    return path == MOUNT or path.startswith(MOUNT + "/")


def resolve(path: str, root: Path | None = None):
    """Return (status, content_type, body_bytes, redirect_location) for a GET of `path`. Never reads outside `root`."""
    root = (root or ROOT).resolve()
    missing = (404, "application/json", b'{"error":"Not found"}', None)
    if path == MOUNT:
        return 301, "text/plain; charset=utf-8", b"", MOUNT + "/"
    if not path.startswith(MOUNT + "/"):
        return missing
    rel = unquote(path[len(MOUNT) + 1:]) or "index.html"
    norm = rel.replace("\\", "/")
    parts = norm.split("/")
    if (
        "\x00" in rel
        or ":" in rel
        or any((not p) or p.startswith(".") for p in parts)      # empty segment, '.', '..', dotfiles
        or parts[0] in DENY_DIRS
        or norm in DENY_FILES
    ):
        return missing
    try:
        target = (root / norm).resolve()
        target.relative_to(root)                                  # traversal / symlink-escape guard
    except (ValueError, OSError):
        return missing
    ctype = TYPES.get(target.suffix.lower())
    try:
        if not ctype or not target.is_file() or target.stat().st_size > MAX_BYTES:
            return missing
        return 200, ctype, target.read_bytes(), None
    except OSError:
        return missing


def serve(handler, path: str, root: Path | None = None) -> None:
    """Write the response on a BaseHTTPRequestHandler. Called from Handler.do_GET only."""
    code, ctype, body, location = resolve(path, root)
    handler.send_response(code)
    handler.send_header("Content-Type", ctype)
    if location:
        handler.send_header("Location", location)
    handler.send_header("Cache-Control", NO_CACHE)
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)
