"""Builds ONE self-contained DEMO file (mock bridge, red DEMO / MOCK banner) for design review:  python tools/build-demo.py  ->  dist/strata-v3-demo.html
The production UI is never bundled: ORION serves the module files directly at /v3/, and never serves demo.html or mock-bridge.js."""
import pathlib, re
root = pathlib.Path(__file__).resolve().parent.parent
html = (root / "demo.html").read_text(encoding="utf-8")
html = re.sub(r'<link rel="stylesheet" href="([^"]+)">', lambda m: "<style>\n" + (root / m.group(1)).read_text(encoding="utf-8") + "\n</style>", html)
html = re.sub(r'<script src="([^"]+)"></script>', lambda m: "<script>\n" + (root / m.group(1)).read_text(encoding="utf-8") + "\n</script>", html)
out = root / "dist"; out.mkdir(exist_ok=True); (out / "strata-v3-demo.html").write_text(html, encoding="utf-8")
print("built", out / "strata-v3-demo.html", len(html), "bytes")
