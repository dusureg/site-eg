"""
Dusur placeholder art.

Every project (and every section picture) gets its own original SVG illustration until a real
photo is dropped into media/. The art is generated, not hand-drawn, so each key produces a
different composition while all of them share the same brand language:
warm wood tones, thin brass line-work, a soft light pool, and the dovetail mark in the corner.

    svg = make_placeholder("kitchen", key="kitchen-walnut", tone="walnut")

Same key -> same picture, always (the key seeds the random generator).
"""
import random
import zlib

W, H, FY = 800, 600, 480          # canvas and floor line (4:3)

PALETTES = {
    "walnut": dict(bg0="#33231A", bg1="#130D09", ink="#EDBF7E", acc="#B8743A", glow="#E3A863", grain="#2a1608"),
    "ebony":  dict(bg0="#2F2D2A", bg1="#121110", ink="#EEDDBF", acc="#8C6C40", glow="#C9A06A", grain="#0f0b07"),
    "oak":    dict(bg0="#E8D6B8", bg1="#C2A276", ink="#3A2718", acc="#9A6A3A", glow="#FFF3DC", grain="#4a2c12"),
    "linen":  dict(bg0="#F4ECDF", bg1="#D6C5A8", ink="#5A3E2B", acc="#B8743A", glow="#FFFFFF", grain="#5a3414"),
    "copper": dict(bg0="#A8602F", bg1="#4B2713", ink="#FCE6C0", acc="#F0B26B", glow="#FFD9A0", grain="#3a1a08"),
    "moss":   dict(bg0="#364631", bg1="#141C14", ink="#EADCB0", acc="#A9B88B", glow="#CFD9A8", grain="#1d2616"),
}
TONES = list(PALETTES)
BACKDROPS = ["arch", "sun", "planks", "beams", "grid", "arcs"]


class Scene:
    """Tiny SVG builder. Every shape inherits the group stroke, so outlines stay consistent."""

    def __init__(self, pal, rnd):
        self.p, self.r, self.out = pal, rnd, []

    # -- primitives ---------------------------------------------------------------------------
    def add(self, s):
        self.out.append(s)

    def rect(self, x, y, w, h, rx=3, fill="none", op=None, sw=None, stroke=True):
        a = f' fill="{fill}"'
        if op is not None:
            a += f' fill-opacity="{op}"'
        if sw:
            a += f' stroke-width="{sw}"'
        if not stroke:
            a += ' stroke="none"'
        self.add(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{rx}"{a}/>')

    def line(self, x1, y1, x2, y2, op=None, sw=None, color=None):
        a = ""
        if op is not None:
            a += f' stroke-opacity="{op}"'
        if sw:
            a += f' stroke-width="{sw}"'
        if color:
            a += f' stroke="{color}"'
        self.add(f'<path d="M{x1:.0f} {y1:.0f}L{x2:.0f} {y2:.0f}"{a}/>')

    def circ(self, cx, cy, rad, fill="none", op=None, stroke=True, sw=None):
        a = f' fill="{fill}"'
        if op is not None:
            a += f' fill-opacity="{op}"'
        if not stroke:
            a += ' stroke="none"'
        if sw:
            a += f' stroke-width="{sw}"'
        self.add(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{rad:.0f}"{a}/>')

    def path(self, d, fill="none", op=None, stroke=True, sw=None, sop=None):
        a = f' fill="{fill}"'
        if op is not None:
            a += f' fill-opacity="{op}"'
        if not stroke:
            a += ' stroke="none"'
        if sw:
            a += f' stroke-width="{sw}"'
        if sop is not None:
            a += f' stroke-opacity="{sop}"'
        self.add(f'<path d="{d}"{a}/>')

    # -- helpers ------------------------------------------------------------------------------
    @property
    def ink(self):
        return self.p["ink"]

    def wood(self):
        return self.r.choice(["url(#w)", "url(#w)", "url(#wl)"])

    def door(self, x, y, w, h, bar="none", fill=None):
        """A cabinet door with an optional handle."""
        self.rect(x, y, w, h, rx=3, fill=fill or self.wood())
        if bar == "top":
            self.line(x + w * .22, y + 16, x + w * .78, y + 16, sw=5)
        elif bar == "bottom":
            self.line(x + w * .22, y + h - 16, x + w * .78, y + h - 16, sw=5)
        elif bar == "side":
            self.line(x + w - 14, y + h * .38, x + w - 14, y + h * .62, sw=5)
        elif bar == "knob":
            self.circ(x + w - 18, y + 20, 4, fill=self.ink, stroke=False)

    def thing(self, x, base, kind=None):
        """A small object standing on a surface: jar, vase, books, plant."""
        k = kind or self.r.choice(["jar", "vase", "books", "plant", "kettle"])
        ink = self.ink
        if k == "jar":
            self.rect(x, base - 38, 26, 38, rx=5, fill=ink, op=.85, stroke=False)
            self.rect(x + 3, base - 46, 20, 8, rx=3, fill=ink, op=.85, stroke=False)
        elif k == "vase":
            self.path(f"M{x + 6} {base}C{x - 6} {base - 26} {x + 6} {base - 34} {x + 10} {base - 52}"
                      f"H{x + 18}C{x + 22} {base - 34} {x + 34} {base - 26} {x + 22} {base}Z",
                      fill=ink, op=.85, stroke=False)
        elif k == "books":
            for i, (bw, bh) in enumerate([(9, 40), (11, 46), (8, 36), (12, 42)]):
                self.rect(x + i * 13, base - bh, bw, bh, rx=1, fill=ink, op=.8 - i * .08, stroke=False)
        elif k == "plant":
            self.rect(x + 4, base - 20, 22, 20, rx=4, fill=ink, op=.85, stroke=False)
            for dx, dy, rr in [(15, 34, 14), (4, 28, 11), (26, 30, 11), (15, 48, 12)]:
                self.circ(x + dx, base - dy, rr, fill=self.p["acc"], op=.9, stroke=False)
        else:   # kettle
            self.rect(x, base - 30, 34, 30, rx=9, fill=ink, op=.85, stroke=False)
            self.path(f"M{x + 34} {base - 22}q14 -4 0 -14", sw=4)

    def pendants(self, xs, drop=72):
        for x in xs:
            self.line(x, 0, x, drop, sw=2, op=.7)
            self.path(f"M{x - 24} {drop + 26}a24 26 0 0 1 48 0Z", fill=self.ink, op=.9, stroke=False)
            self.circ(x, drop + 30, 5, fill=self.p["glow"], stroke=False)


# ======================================================================================
# scenes: each one draws a frontal elevation on the 800x600 canvas
# ======================================================================================
def kitchen(s):
    r = s.r
    n = r.choice([3, 4, 4, 5])
    x0, x1 = 96, 704
    w = (x1 - x0) / n
    bar = r.choice(["top", "top", "knob", "none"])
    tall = r.random() < .45
    upper = r.random() < .85
    hood = upper and n >= 4 and r.random() < .6
    hi = n // 2 if hood else -1
    if upper:
        for i in range(n):
            x = x0 + i * w
            if tall and i == 0:
                continue
            if i == hi:
                cx = x + w / 2
                s.path(f"M{cx - 20:.0f} 90H{cx + 20:.0f}V176L{cx + w * .44:.0f} 226H{cx - w * .44:.0f}L{cx - 20:.0f} 176Z",
                       fill=s.ink, op=.16)
            else:
                s.door(x + 4, 128, w - 8, 106, bar="bottom" if bar != "none" else "none")
    if tall:
        s.door(x0 + 4, 104, w - 8, FY - 104, bar="side")
    # back splash tiles
    for ty in (258, 284):
        s.line(x0 + (w if tall else 0), ty, x1, ty, op=.18, sw=2)
    s.rect(x0 - 14, 314, x1 - x0 + 28, 18, rx=3, fill=s.ink, op=.92)
    for i in range(n):
        x = x0 + i * w
        if tall and i == 0:
            continue
        s.door(x + 4, 336, w - 8, FY - 336, bar=bar)
    if n >= 4:
        s.line(x0 + w * 1.5, 336, x0 + w * 1.5, FY, op=.0)
    if r.random() < .55:
        s.pendants(sorted(r.sample([x0 + w * k for k in range(1, n)], k=min(2, n - 1))), drop=r.choice([50, 70]))
    px = x0 + (w if tall else 0) + 24
    for k in range(r.choice([2, 3])):
        s.thing(px + k * r.choice([70, 90, 110]) + r.randint(0, 30), 314)


def dressing(s):
    r = s.r
    cols = r.choice([4, 5, 6])
    x0, x1 = 92, 708
    w = (x1 - x0) / cols
    kinds = [r.choice(["door", "door", "open", "glass", "drawers"]) for _ in range(cols)]
    kinds[r.randrange(cols)] = "open"
    kinds[(kinds.index("open") + 2) % cols] = "drawers"
    s.rect(x0 - 8, 84, x1 - x0 + 16, 20, rx=3, fill=s.ink, op=.9)
    for i, k in enumerate(kinds):
        x = x0 + i * w
        if k == "door":
            s.door(x + 4, 112, w - 8, FY - 112, bar="side")
        elif k == "glass":
            s.rect(x + 4, 112, w - 8, FY - 112, fill=s.p["glow"], op=.18)
            s.line(x + w * .3, 130, x + w * .1, 300, op=.5, sw=2)
            s.line(x + w * .55, 130, x + w * .25, 360, op=.4, sw=2)
        elif k == "drawers":
            hh = (FY - 112) / 5
            for j in range(5):
                s.door(x + 4, 112 + j * hh + 2, w - 8, hh - 4, bar="top")
        else:
            s.rect(x + 4, 112, w - 8, FY - 112, fill="none")
            s.line(x + 10, 170, x + w - 10, 170, sw=4)
            for j in range(r.choice([3, 4, 5])):
                hx = x + 20 + j * (w - 40) / 4.2
                hgt = r.choice([100, 150, 190])
                s.path(f"M{hx:.0f} 170l-9 8h18z", fill=s.ink, op=.9, stroke=False)
                s.rect(hx - 9, 178, 18, hgt, rx=4, fill=s.ink, op=.55 + r.random() * .3, stroke=False)
            s.line(x + 4, 360, x + w - 4, 360, op=.5)
            s.rect(x + 12, 372, w - 24, 22, rx=2, fill=s.ink, op=.35, stroke=False)
            s.rect(x + 12, 398, w - 24, 22, rx=2, fill=s.ink, op=.25, stroke=False)
    if r.random() < .8:
        s.rect(300, 436, 200, 44, rx=18, fill=s.p["acc"], op=.95)
        s.line(330, 446, 470, 446, op=.35, sw=2)


def tv(s):
    r = s.r
    s.add(f'<g stroke-opacity=".35">')
    for x in range(160, 641, 16):
        s.line(x, 84, x, 350, sw=5)
    s.add("</g>")
    tx, tw, th = 250, 300, 172
    s.rect(tx, 140, tw, th, rx=6, fill="#0b0806", op=.92)
    s.line(tx + 30, 150, tx + 120, 302, op=.28, sw=3, color=s.p["glow"])
    s.line(tx + 80, 150, tx + 170, 302, op=.18, sw=3, color=s.p["glow"])
    floating = r.random() < .6
    top = 366
    s.rect(176, top, 448, 112 if not floating else 92, rx=4, fill=s.wood())
    for k in range(1, 4):
        s.line(176 + k * 112, top, 176 + k * 112, top + (112 if not floating else 92), op=.8)
    for k in range(4):
        s.line(176 + k * 112 + 34, top + 18, 176 + k * 112 + 78, top + 18, sw=4)
    if floating:
        s.line(180, top + 104, 620, top + 104, sw=5, op=.85, color=s.p["glow"])
    for side, x in (("l", 92), ("r", 640)):
        s.rect(x, 104, 68, FY - 104, rx=3, fill="none")
        for j in range(4):
            yy = 104 + j * 94
            s.line(x, yy, x + 68, yy, op=.8)
            if r.random() < .75:
                s.thing(x + 14, yy + 94 if j < 3 else FY, r.choice(["books", "vase", "plant", "jar"]))


def bath(s):
    r = s.r
    for gx in range(110, 700, 58):
        s.line(gx, 60, gx, 400, op=.12, sw=2)
    for gy in range(100, 400, 58):
        s.line(100, gy, 700, gy, op=.12, sw=2)
    cx = 400
    s.path(f"M{cx - 96} 300V170a96 96 0 0 1 192 0V300Z", fill=s.p["glow"], op=.22)
    s.path(f"M{cx - 78} 284V172a78 78 0 0 1 156 0V284Z", sw=2, sop=.6)
    for sx in (cx - 150, cx + 150):
        s.rect(sx - 6, 150, 12, 56, rx=6, fill=s.p["glow"], op=.85)
        s.line(sx, 206, sx, 220, sw=3)
    vx, vw = 210, 380
    s.rect(vx, 340, vw, 96, rx=4, fill=s.wood())
    s.line(vx + vw / 2, 340, vx + vw / 2, 436)
    s.line(vx + 60, 360, vx + vw / 2 - 60, 360, sw=5)
    s.line(vx + vw / 2 + 60, 360, vx + vw - 60, 360, sw=5)
    s.line(vx + 6, 448, vx + vw - 6, 448, sw=5, op=.85, color=s.p["glow"])
    s.rect(vx - 10, 318, vw + 20, 22, rx=4, fill=s.ink, op=.92)
    bw = r.choice([120, 150])
    s.path(f"M{cx - bw / 2:.0f} 318c0 -30 {bw / 2 - 10:.0f} -34 {bw / 2:.0f} -34s{bw / 2:.0f} 4 {bw / 2:.0f} 34Z", fill=s.ink, op=.22)
    s.path(f"M{cx} 284V256c0 -10 8 -14 18 -14h10", sw=5)
    if r.random() < .7:
        s.rect(640, 150, 70, FY - 150, rx=3, fill=s.wood())
        for yy in (150 + 124, 150 + 248):
            s.line(640, yy, 710, yy, op=.9)
        s.line(700, 300, 700, 340, sw=5)
    if r.random() < .8:
        for k in range(3):
            s.rect(110, FY - 30 - k * 24, 70, 22, rx=10, fill=s.ink, op=.85 - k * .15, stroke=False)


def joinery(s):
    r = s.r
    v = r.choice(["door", "shelf", "desk"])
    if v == "door":
        s.rect(110, 84, 230, FY - 84, rx=3, fill="none", sw=5)
        for (px, py, pw, ph) in [(136, 112, 78, 130), (236, 112, 78, 130), (136, 270, 78, 170), (236, 270, 78, 170)]:
            s.rect(px, py, pw, ph, rx=2, fill=s.wood())
        s.circ(318, 300, 6, fill=s.ink, stroke=False)
        x0, x1 = 390, 710
        s.rect(x0, 120, x1 - x0, FY - 120, rx=3)
        for j in range(1, 4):
            s.line(x0, 120 + j * 90, x1, 120 + j * 90)
        s.line((x0 + x1) / 2, 120 + 90, (x0 + x1) / 2, FY - 90 * 1)
        for j in range(4):
            s.thing(x0 + 20 + r.randint(0, 120), 120 + (j + 1) * 90 if j < 3 else FY, r.choice(["books", "vase", "plant", "jar"]))
            s.thing(x0 + 190 + r.randint(0, 80), 120 + (j + 1) * 90 if j < 3 else FY, r.choice(["books", "jar", "vase"]))
    elif v == "shelf":
        x0, x1 = 100, 700
        s.rect(x0, 90, x1 - x0, FY - 90, rx=3)
        cuts = sorted(r.sample(range(150, 650, 50), 3))
        for c in cuts:
            s.line(c, 90, c, FY)
        for j in range(1, 4):
            s.line(x0, 90 + j * 98, x1, 90 + j * 98)
        s.rect(cuts[0], 90 + 98, cuts[1] - cuts[0], 98, fill=s.wood())
        s.rect(cuts[2], 90 + 196, x1 - cuts[2], 98, fill=s.wood())
        for j in range(4):
            yy = 90 + (j + 1) * 98 if j < 3 else FY
            s.thing(x0 + 16 + r.randint(0, 20), yy)
            s.thing(cuts[1] + 14 + r.randint(0, 20), yy, r.choice(["books", "plant"]))
    else:
        s.rect(130, 296, 540, 16, rx=3, fill=s.ink, op=.92)
        s.rect(150, 312, 120, FY - 312, rx=3, fill=s.wood())
        for j in range(3):
            s.door(154, 316 + j * 54, 112, 52, bar="top")
        s.line(650, 312, 650, FY, sw=5)
        s.line(300, 312, 300, FY, sw=5)
        s.rect(130, 90, 300, 130, rx=3, fill="none")
        s.line(130, 155, 430, 155)
        s.thing(150, 155, "books")
        s.thing(320, 220, "vase")
        s.path("M560 296V230L610 190M610 190l40 14", sw=4)
        s.circ(655, 206, 18, fill=s.p["glow"], op=.9, stroke=False)
    # dovetail detail roundel - the joinery signature
    cx, cy, rr = 662, 150, 62
    s.circ(cx, cy, rr, fill=s.p["bg1"], op=.85)
    s.path(f"M{cx - 44} {cy - 24}H{cx - 6}V{cy - 12}L{cx + 10} {cy - 18}V{cy + 2}L{cx - 6} {cy - 4}V{cy + 12}L{cx + 10} {cy + 6}V{cy + 24}H{cx - 44}Z", fill="url(#w)", sw=2.5)
    s.path(f"M{cx - 6} {cy - 12}H{cx + 44}V{cy + 24}H{cx - 6}Z", fill=s.ink, op=.75, sw=2.5)


def restaurant(s):
    r = s.r
    for x in range(100, 701, 28):
        s.line(x, 60, x, 300, op=.2, sw=4)
    s.pendants(sorted(r.sample([200, 330, 470, 600], 3)), drop=r.choice([40, 80]))
    s.rect(96, 296, 608, 84, rx=r.choice([14, 30]), fill=s.wood())
    for x in range(124, 690, 46):
        s.line(x, 310, x, 372, op=.55, sw=2)
    s.rect(88, 380, 624, 54, rx=10, fill=s.p["acc"], op=.95)
    s.rect(96, 434, 608, FY - 434, rx=2, fill="none")
    for x in range(130, 690, 90):
        s.line(x, 440, x, FY, op=.45, sw=2)
    tx = r.choice([300, 340, 380])
    s.rect(tx, 408, 130, 12, rx=3, fill=s.ink, op=.95)
    s.line(tx + 65, 420, tx + 65, FY, sw=6)
    s.line(tx + 25, FY, tx + 105, FY, sw=6)
    s.circ(tx + 28, 402, 9, fill=s.ink, op=.7, stroke=False)
    s.circ(tx + 102, 402, 9, fill=s.ink, op=.7, stroke=False)
    s.thing(tx + 56, 408, "vase")


def cafe(s):
    r = s.r
    rows = r.choice([(150, 232), (170,), (130, 205, 280)])
    for sy in rows:
        s.line(110, sy, 690, sy, sw=5)
        x = 126
        while x < 660:
            k = r.choice(["cup", "bottle", "jar", "gap"])
            if k == "cup":
                s.rect(x, sy - 22, 24, 22, rx=5, fill=s.ink, op=.88, stroke=False)
                x += 40
            elif k == "bottle":
                s.rect(x, sy - 52, 16, 52, rx=6, fill=s.ink, op=.8, stroke=False)
                x += 34
            elif k == "jar":
                s.thing(x, sy, "jar")
                x += 44
            else:
                x += 30
    s.pendants(sorted(r.sample([180, 300, 420, 540, 650], 3)), drop=r.choice([30, 60]))
    s.rect(96, 330, 608, 16, rx=3, fill=s.ink, op=.92)
    s.rect(108, 346, 584, FY - 346, rx=2, fill=s.wood())
    for x in range(124, 692, 16):
        s.line(x, 352, x, FY - 6, op=.45, sw=2)
    mx = r.choice([180, 420])
    s.rect(mx, 270, 130, 60, rx=6, fill=s.ink, op=.9, stroke=False)
    s.rect(mx + 14, 252, 102, 22, rx=4, fill=s.ink, op=.75, stroke=False)
    s.circ(mx + 40, 322, 6, fill=s.p["bg1"], stroke=False)
    s.circ(mx + 90, 322, 6, fill=s.p["bg1"], stroke=False)
    for k, x in enumerate(sorted(r.sample([250, 330, 410, 490, 570, 650], 3))):
        s.rect(x - 26, 404 + (k % 2) * 8, 52, 14, rx=7, fill=s.p["acc"], op=1)
        s.line(x - 14, 420, x - 22, FY, sw=4)
        s.line(x + 14, 420, x + 22, FY, sw=4)


def shop(s):
    r = s.r
    x0, x1 = 90, 470
    s.rect(x0, 96, x1 - x0, FY - 96, rx=3)
    cols, rows = 3, 4
    cw, rh = (x1 - x0) / cols, (FY - 96) / rows
    for c in range(1, cols):
        s.line(x0 + c * cw, 96, x0 + c * cw, FY)
    for j in range(1, rows):
        s.line(x0, 96 + j * rh, x1, 96 + j * rh)
    for j in range(rows):
        for c in range(cols):
            bx, by = x0 + c * cw + 14, 96 + (j + 1) * rh
            k = r.choice(["box", "bottle", "bag", "stack", "none"])
            if k == "box":
                s.rect(bx, by - 44, 44, 44, rx=2, fill=s.ink, op=.8, stroke=False)
                s.rect(bx + 54, by - 30, 40, 30, rx=2, fill=s.p["acc"], stroke=False)
            elif k == "bottle":
                for q in range(3):
                    s.rect(bx + q * 28, by - 54 + q * 6, 18, 54 - q * 6, rx=6, fill=s.ink, op=.85 - q * .1, stroke=False)
            elif k == "bag":
                s.path(f"M{bx} {by}l8 -50h40l8 50Z", fill=s.ink, op=.8, stroke=False)
                s.path(f"M{bx + 14} {by - 50}c0 -14 24 -14 24 0", sw=3)
            elif k == "stack":
                for q in range(3):
                    s.rect(bx, by - 14 * (q + 1), 70 - q * 8, 12, rx=2, fill=s.ink, op=.85 - q * .15, stroke=False)
    s.rect(510, 108, 190, 62, rx=4, fill=s.wood())
    for q, ww in enumerate((120, 80)):
        s.line(530, 130 + q * 22, 530 + ww, 130 + q * 22, sw=5, op=.9)
    s.rect(520, 330, 180, 16, rx=3, fill=s.ink, op=.92)
    s.rect(528, 346, 164, FY - 346, rx=2, fill=s.wood())
    s.line(528 + 82, 346, 528 + 82, FY, op=.8)
    s.rect(560, 296, 56, 34, rx=4, fill=s.ink, op=.85, stroke=False)
    s.path("M650 330l6 -40h30l6 40Z", fill=s.p["acc"], stroke=False)
    s.thing(536, 330, "plant")


def cladding(s):
    r = s.r
    x, i = 90, 0
    while x < 710:
        ww = r.choice([22, 28, 36, 44])
        ww = min(ww, 710 - x)
        s.rect(x, 108, ww - 3, FY - 108, rx=1, fill=("url(#w)" if i % 3 else "url(#wl)"))
        x += ww
        i += 1
    s.rect(80, 70, 640, 28, rx=3, fill=s.ink, op=.92)
    s.line(80, 98, 720, 98, sw=5, op=.8, color=s.p["glow"])
    dx = r.choice([200, 330, 460])
    s.rect(dx, 190, 130, FY - 190, rx=3, fill=s.p["bg1"], op=.96)
    s.rect(dx + 14, 204, 102, FY - 218, rx=2, fill="none", sw=2)
    s.line(dx + 108, 330, dx + 108, 380, sw=6)
    for sx in (dx - 52, dx + 182):
        if 100 < sx < 700:
            s.circ(sx, 250, 26, fill=s.p["glow"], op=.5, stroke=False)
            s.rect(sx - 5, 236, 10, 28, rx=5, fill=s.p["glow"], stroke=False)


def fitout(s):
    r = s.r
    x0, y0, x1, y1 = 110, 100, 690, 400
    s.rect(x0, y0, x1 - x0, y1 - y0, rx=0, sw=8)
    cx = r.choice([340, 400, 450])
    s.line(cx, y0, cx, 250, sw=6)
    s.line(cx, 320, cx, y1, sw=6)
    s.path(f"M{cx} 250V320", sw=2, sop=.0)
    s.path(f"M{cx} 320a70 70 0 0 1 70 -70", sw=2, sop=.8)
    s.line(cx, 320, cx + 70, 320, sw=2, op=.8)
    s.line(cx, 250, cx, 320, sw=5, op=.0)
    s.line(x0, 250, cx, 250, sw=6)
    s.rect(x0 + 24, y0 + 24, 150, 34, rx=2, fill="url(#w)")
    s.rect(x0 + 24, y0 + 58, 34, 90, rx=2, fill="url(#w)")
    for k in range(3):
        s.circ(cx + 100 + k * 90, 170, 26, fill=s.ink, op=.15)
        s.circ(cx + 100 + k * 90, 170, 10, fill=s.ink, op=.75, stroke=False)
    s.rect(cx + 90, 300, 220, 60, rx=3, fill="url(#wl)")
    s.rect(x0 + 40, 290, 130, 90, rx=3, fill="url(#w)")
    s.line(x0, 440, x1, 440, sw=2)
    for xx in (x0, x1):
        s.line(xx, 428, xx, 452, sw=2)
    s.rect(380, 428, 40, 24, rx=3, fill=s.p["bg1"], op=.9, stroke=False)


SCENES = {
    "kitchen": kitchen, "dressing": dressing, "tv": tv, "bath": bath, "joinery": joinery,
    "restaurant": restaurant, "cafe": cafe, "shop": shop, "cladding": cladding, "fitout": fitout,
}


# ======================================================================================
# backdrop, frame, assembly
# ======================================================================================
def _backdrop(s, style, fit=False):
    p, r, ink, glow = s.p, s.r, s.p["ink"], s.p["glow"]
    if style == "arch":
        cx = r.choice([220, 400, 580])
        s.path(f"M{cx - 120} {FY}V230a120 120 0 0 1 240 0V{FY}Z", fill=glow, op=.13, stroke=False)
        s.path(f"M{cx - 120} {FY}V230a120 120 0 0 1 240 0V{FY}", sw=2, sop=.28)
    elif style == "sun":
        s.circ(r.choice([250, 400, 560]), r.choice([210, 260]), r.choice([150, 190]), fill=glow, op=.17, stroke=False)
    elif style == "planks":
        x = 0
        while x < W:
            ww = r.choice([40, 56, 72])
            if r.random() < .5:
                s.rect(x, 0, ww, FY, rx=0, fill=ink, op=.05, stroke=False)
            x += ww
    elif style == "beams":
        for k in range(3):
            x = r.randint(-100, 600)
            s.path(f"M{x} 0H{x + 90}L{x + 90 + 260} {FY}H{x + 260}Z", fill=glow, op=.07 + k * .02, stroke=False)
    elif style == "grid":
        for gx in range(0, W, 64):
            s.line(gx, 0, gx, FY if not fit else H, op=.09, sw=1.5)
        for gy in range(0, FY if not fit else H, 64):
            s.line(0, gy, W, gy, op=.09, sw=1.5)
    else:   # arcs
        cx, cy = r.choice([0, W]), r.choice([0, 200])
        for rr in (120, 200, 280, 360):
            s.circ(cx, cy, rr, sw=1.8)
        s.add("")


def _wood_defs(p, rnd):
    """Two tileable grain patterns: 'w' (accent wood) and 'wl' (light veneer)."""
    def grain(color, op):
        d = []
        x = rnd.randint(3, 8)
        while x < 64:
            d.append(f"M{x} 0q{rnd.choice([-3, 3])} 32 0 64")
            x += rnd.randint(6, 12)
        return f'<path d="{"".join(d)}" fill="none" stroke="{color}" stroke-opacity="{op}" stroke-width="1.4"/>'
    return (
        f'<pattern id="w" width="64" height="64" patternUnits="userSpaceOnUse"><rect width="64" height="64" fill="{p["acc"]}"/>{grain(p["grain"], .32)}</pattern>'
        f'<pattern id="wl" width="64" height="64" patternUnits="userSpaceOnUse"><rect width="64" height="64" fill="{p["ink"]}" fill-opacity=".14"/>{grain(p["ink"], .35)}</pattern>'
    )


def make_placeholder(kind, key=None, tone=None, backdrop=None):
    """Return a self-contained SVG string for one picture."""
    key = key or kind
    seed = zlib.crc32(f"{kind}:{key}".encode())
    rnd = random.Random(seed)
    tone = tone if tone in PALETTES else rnd.choice(TONES)
    pal = dict(PALETTES[tone])
    style = backdrop or rnd.choice(BACKDROPS)
    fit = kind == "fitout"
    if fit:
        style = "grid"
    s = Scene(pal, rnd)

    glow_x, glow_y = rnd.choice([160, 300, 500, 640]), rnd.choice([140, 220, 300])
    head = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice">'
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0.35" y2="1"><stop offset="0" stop-color="{pal["bg0"]}"/><stop offset="1" stop-color="{pal["bg1"]}"/></linearGradient>'
        f'<radialGradient id="gl" cx="{glow_x}" cy="{glow_y}" r="380" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{pal["glow"]}" stop-opacity=".42"/><stop offset="1" stop-color="{pal["glow"]}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="fl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{pal["ink"]}" stop-opacity=".16"/><stop offset="1" stop-color="{pal["ink"]}" stop-opacity="0"/></linearGradient>'
        f'{_wood_defs(pal, rnd)}</defs>'
        f'<rect width="{W}" height="{H}" fill="url(#bg)"/><rect width="{W}" height="{H}" fill="url(#gl)"/>'
    )
    body = [f'<g fill="none" stroke="{pal["ink"]}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">']
    s.out = body
    _backdrop(s, style, fit)
    if not fit:
        s.add(f'<rect x="0" y="{FY}" width="{W}" height="{H - FY}" fill="url(#fl)" stroke="none"/>')
        s.add(f'<path d="M0 {FY}H{W}" stroke-opacity=".4" stroke-width="2"/>')
        s.add(f'<ellipse cx="400" cy="{FY + 8}" rx="330" ry="9" fill="#000" fill-opacity=".22" stroke="none"/>')
    SCENES[kind](s)
    # inset frame and the dovetail signature (same on every picture = brand consistency)
    s.add(f'<rect x="16" y="16" width="{W - 32}" height="{H - 32}" rx="10" stroke-opacity=".2" stroke-width="1.5"/>')
    s.add(f'<path transform="translate(738 548)" d="M0 0H12V5L19 3V11L12 9V17L19 15V23L12 21V28H0Z" stroke-opacity=".6" stroke-width="2.2"/>')
    s.add("</g></svg>")
    svg = head + "".join(s.out)
    uid = f"p{seed & 0xFFFF:04x}"          # unique ids so several pictures can share one HTML page
    return svg.replace('id="', f'id="{uid}').replace("url(#", f"url(#{uid}")


if __name__ == "__main__":      # quick self-test: python build/placeholders.py
    for k in SCENES:
        print(k, len(make_placeholder(k, key=k)))
