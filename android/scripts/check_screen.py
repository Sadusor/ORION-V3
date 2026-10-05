from __future__ import annotations
import sys
from PIL import Image
import numpy as np

if len(sys.argv) != 2:
    raise SystemExit("usage: check_screen.py <png>")

path = sys.argv[1]
im = Image.open(path).convert("RGB")
w, h = im.size

# Ignore Android status/navigation bars so they cannot make an all-black
# ORION surface look healthy.
top = int(h * 0.08)
bottom = int(h * 0.96)
crop = im.crop((0, top, w, bottom))

# Downsample for a cheap deterministic visual-health check.
sample = crop.resize((max(1, w // 8), max(1, (bottom - top) // 8)))
pixels = np.asarray(sample, dtype=np.uint8).reshape(-1, 3).astype(np.float32)

r = pixels[:, 0]
g = pixels[:, 1]
b = pixels[:, 2]
luma = 0.2126 * r + 0.7152 * g + 0.0722 * b

mean = float(luma.mean())
std = float(luma.std())
bright_ratio = float((luma >= 28.0).mean())
cyan_ratio = float(((b >= 35.0) & (g >= 28.0) & (b > r * 1.15)).mean())

print(
    f"ORION_SCREEN_METRICS> mean={mean:.2f} "
    f"std={std:.2f} bright={bright_ratio:.5f} cyan={cyan_ratio:.5f}"
)

# A healthy STRATA surface is dark, but it contains stars, labels, the core,
# pairing modal, or cyan UI chrome. A solid/near-solid black WebView will have
# almost no variance and essentially no brighter/cyan pixels.
healthy = (std >= 4.0 and bright_ratio >= 0.0020) or cyan_ratio >= 0.0010
if not healthy:
    raise SystemExit(2)

raise SystemExit(0)
