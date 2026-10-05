from __future__ import annotations
import sys
from PIL import Image, ImageStat

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
pixels = list(sample.getdata())
n = max(1, len(pixels))

luma = [0.2126*r + 0.7152*g + 0.0722*b for r, g, b in pixels]
mean = sum(luma) / n
var = sum((x - mean) ** 2 for x in luma) / n
std = var ** 0.5
bright_ratio = sum(1 for x in luma if x >= 28.0) / n
cyan_ratio = sum(1 for r, g, b in pixels if b >= 35 and g >= 28 and b > r * 1.15) / n

print(f"ORION_SCREEN_METRICS> mean={mean:.2f} std={std:.2f} bright={bright_ratio:.5f} cyan={cyan_ratio:.5f}")

# A healthy STRATA surface is dark, but it contains stars, labels, the core,
# pairing modal, or cyan UI chrome. A solid/near-solid black WebView will have
# almost no variance and essentially no brighter/cyan pixels.
healthy = (std >= 4.0 and bright_ratio >= 0.0020) or cyan_ratio >= 0.0010
if not healthy:
    raise SystemExit(2)
