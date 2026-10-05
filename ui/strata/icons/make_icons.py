"""ORION icon renderer (STRATA identity): lattice planet, tilted orbital ring, Orion-belt stars, deep space. Supersampled for clean edges."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ION = (118, 207, 228); ICE = (201, 238, 245); SILVER = (231, 235, 239)

def radial(S, cx, cy, r, c0, c1, a0, a1, power=1.0):
    y, x = np.mgrid[0:S, 0:S]; d = np.clip(np.hypot(x - cx, y - cy) / r, 0, 1) ** power
    a = (a0 + (a1 - a0) * d)
    out = np.zeros((S, S, 4), np.float32)
    for i in range(3): out[..., i] = c0[i] + (c1[i] - c0[i]) * d
    out[..., 3] = a * 255
    return Image.fromarray(out.astype(np.uint8), "RGBA")

def background(S, stars=True, seed=7):
    y, x = np.mgrid[0:S, 0:S]; d = np.clip(np.hypot(x - S * .5, y - S * .46) / (S * .72), 0, 1)
    top = np.array([11, 24, 40], np.float32); edge = np.array([4, 6, 11], np.float32)
    img = np.zeros((S, S, 4), np.float32)
    for i in range(3): img[..., i] = top[i] + (edge[i] - top[i]) * d ** .8
    img[..., 3] = 255
    im = Image.fromarray(img.astype(np.uint8), "RGBA")
    if stars:
        rnd = random.Random(seed); layer = Image.new("RGBA", (S, S), (0, 0, 0, 0)); dr = ImageDraw.Draw(layer)
        for _ in range(int(S * .030)):
            px, py = rnd.random() * S, rnd.random() * S
            if math.hypot(px - S * .5, py - S * .5) < S * .30: continue
            r = S * (0.0012 + rnd.random() ** 3 * 0.0032); a = int(50 + rnd.random() * 120)
            dr.ellipse([px - r, py - r, px + r, py + r], fill=(*SILVER, a))
        for _ in range(4):
            px, py = rnd.random() * S, rnd.random() * S
            if math.hypot(px - S * .5, py - S * .5) < S * .34: continue
            r = S * .003; dr.ellipse([px - r, py - r, px + r, py + r], fill=(*ION, 230))
            dr.line([px - r * 4, py, px + r * 4, py], fill=(*ION, 70), width=max(1, int(S * .0008)))
            dr.line([px, py - r * 4, px, py + r * 4], fill=(*ION, 70), width=max(1, int(S * .0008)))
        im = Image.alpha_composite(im, layer)
    return im

def ring_layers(S, cx, cy, R, width, detail=True):
    RX, RY, RA = R * 1.46, R * .36, -0.38
    back = Image.new("RGBA", (S, S), (0, 0, 0, 0)); front = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    db, df = ImageDraw.Draw(back), ImageDraw.Draw(front); K = 360
    def pt(a):
        ex, ey = RX * math.cos(a), RY * math.sin(a)
        return (cx + ex * math.cos(RA) - ey * math.sin(RA), cy + ex * math.sin(RA) + ey * math.cos(RA))
    for k in range(K):
        a0, a1 = k / K * 2 * math.pi, (k + 1.6) / K * 2 * math.pi; mid = (a0 + a1) / 2
        sm = (math.sin(mid) + 1) / 2; (df if math.sin(mid) > 0 else db).line([pt(a0), pt(a1)], fill=(*SILVER, int(95 + 150 * sm ** .8)), width=width)
    glow = lambda L, b, k: Image.alpha_composite(L.filter(ImageFilter.GaussianBlur(b)).point(lambda v: min(255, int(v * k))), L)
    return glow(back, S * .006, .9), glow(front, S * .006, 1.1), pt

def planet(S, cx, cy, R, detail=True):
    y, x = np.mgrid[0:S, 0:S]; nx = (x - cx) / R; ny = (y - cy) / R; rr = nx ** 2 + ny ** 2
    inside = rr <= 1; nz = np.sqrt(np.clip(1 - rr, 0, 1))
    L = np.array([-.45, -.50, .74]); L = L / np.linalg.norm(L)
    d = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    dark = np.array([5, 8, 13], np.float32); mid = np.array([16, 34, 50], np.float32); tint = np.array(ION, np.float32)
    col = dark + (mid - dark) * np.clip(d * 1.7, 0, 1)[..., None]
    col = col + (tint * .62 - col) * (np.clip(d - .48, 0, 1) ** 1.25 * 2.1)[..., None]
    rim = (1 - nz) ** 3.2
    col = col + tint * (rim * .85)[..., None]
    edge = np.clip((R - np.hypot(x - cx, y - cy)) / 1.6, 0, 1)
    out = np.zeros((S, S, 4), np.float32); out[..., :3] = np.clip(col, 0, 255); out[..., 3] = edge * 255 * inside
    return Image.fromarray(out.astype(np.uint8), "RGBA")

def lattice(S, cx, cy, R, detail=True, rot=0.75, tilt=0.42):
    N = 230 if detail else 90; pts = []
    for i in range(N):
        yv = 1 - 2 * (i + .5) / N; r = math.sqrt(1 - yv * yv); th = i * 2.39996
        x0, z0 = math.cos(th) * r, math.sin(th) * r
        x1 = x0 * math.cos(rot) + z0 * math.sin(rot); z1 = -x0 * math.sin(rot) + z0 * math.cos(rot)
        y1 = yv * math.cos(tilt) - z1 * math.sin(tilt); z2 = yv * math.sin(tilt) + z1 * math.cos(tilt)
        pts.append((x0, yv, z0, cx + x1 * R, cy + y1 * R, z2))
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0)); dr = ImageDraw.Draw(layer)
    lw = max(1, int(S * (.0011 if detail else .0022)))
    for i in range(N):
        for j in range(i + 1, N):
            if pts[i][0] * pts[j][0] + pts[i][1] * pts[j][1] + pts[i][2] * pts[j][2] > (.945 if detail else .86):
                z = min(pts[i][5], pts[j][5])
                if z > -.05: dr.line([pts[i][3], pts[i][4], pts[j][3], pts[j][4]], fill=(*ION, int(30 + 150 * max(0, z))), width=lw)
    for p in pts:
        if p[5] > -.05:
            r = S * (.0016 if detail else .003) * (1 + max(0, p[5]) * .9); dr.ellipse([p[3] - r, p[4] - r, p[3] + r, p[4] + r], fill=(*ICE, int(90 + 150 * max(0, p[5]))))
    return layer

def belt(S, cx, cy, R):
    g = Image.new("RGBA", (S, S), (0, 0, 0, 0)); dr = ImageDraw.Draw(g)
    stars = [(-.34, -.26, 1.0), (0, 0, 1.15), (.34, .26, 1.0)]
    for a, b, k in stars:
        x, y = cx + a * R * 1.7, cy + b * R * 1.7; r = S * .0125 * k
        dr.ellipse([x - r * 3, y - r * 3, x + r * 3, y + r * 3], fill=(*ION, 120))
    g = g.filter(ImageFilter.GaussianBlur(S * .012))
    dr = ImageDraw.Draw(g)
    for a, b, k in stars:
        x, y = cx + a * R * 1.7, cy + b * R * 1.7; r = S * .0072 * k
        dr.ellipse([x - r * 1.9, y - r * 1.9, x + r * 1.9, y + r * 1.9], fill=(*ION, 90))
        dr.ellipse([x - r, y - r, x + r, y + r], fill=(*SILVER, 255))
    return g

def render(size=1024, bg=True, stars=True, scale=1.12, detail=True, ss=3):
    S = size * ss; cx = cy = S / 2; R = S * .255 * scale
    base = background(S, stars) if bg else Image.new("RGBA", (S, S), (0, 0, 0, 0))
    halo = radial(S, cx, cy, R * 2.0, ION, ION, .42, 0.0, 1.0); halo = Image.composite(halo, Image.new("RGBA", (S, S), (0, 0, 0, 0)), halo.split()[3])
    back, front, _ = ring_layers(S, cx, cy, R, max(2, int(S * (.0065 if detail else .011))), detail)
    im = Image.alpha_composite(base, halo); im = Image.alpha_composite(im, back)
    im = Image.alpha_composite(im, planet(S, cx, cy, R, detail))
    im = Image.alpha_composite(im, lattice(S, cx, cy, R, detail))
    im = Image.alpha_composite(im, belt(S, cx, cy, R))
    im = Image.alpha_composite(im, front)
    return im.resize((size, size), Image.LANCZOS)

def rounded(im, radius_frac=.2237):
    S = im.size[0]; m = Image.new("L", (S * 4, S * 4), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, S * 4 - 1, S * 4 - 1], radius=int(S * 4 * radius_frac), fill=255)
    m = m.resize((S, S), Image.LANCZOS); out = im.copy(); out.putalpha(m); return out

if __name__ == "__main__":
    import os, sys
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out + "/sizes", exist_ok=True)
    full = render(1024); full.convert("RGB").save(f"{out}/orion-icon-1024.png")
    rounded(full).save(f"{out}/orion-icon-rounded-1024.png")
    render(1024, bg=False, stars=False, scale=1.12).save(f"{out}/orion-mark-transparent-1024.png")
    render(512, scale=.74, stars=False).convert("RGB").save(f"{out}/sizes/orion-icon-maskable-512.png")
    for n in (512, 384, 256, 192, 180, 152, 144, 128, 96):
        full.resize((n, n), Image.LANCZOS).convert("RGB").save(f"{out}/sizes/orion-icon-{n}.png")
    small = {n: render(n, stars=False, scale=1.2, detail=False, ss=6).convert("RGB") for n in (72, 64, 48, 32, 16)}
    for n, im in small.items(): im.save(f"{out}/sizes/orion-icon-{n}.png")
    small[48].save(f"{out}/sizes/favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)], append_images=[small[32], small[16]])
    full.resize((180, 180), Image.LANCZOS).convert("RGB").save(f"{out}/sizes/apple-touch-icon.png")
    print("ok")
