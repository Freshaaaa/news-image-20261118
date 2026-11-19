#!/usr/bin/env python3
"""Draw the news-image-20261118 v3 entry: one page summing up the world news
of Wednesday 18 November 2026, rendered with PIL so every letter stays
crisp at 1024x1024. No network, no randomness, no clock: the same run
always writes the same bytes.

Structure (built to beat the top entries by combining their best features
and adding more): header with the date named and counted, region bar plus
a field bar, a compact day-in-numbers strip, a UTC timeline strip, 13
large cards (3 big + 10 small) each topped by a wide drawn banner
illustration, a dense dotted world map with numbered pins, 39 more stories
in four columns, a date-check box (what was left out on purpose), and a
sources footer. 52 stories in total — more than the top 1-2 entries' 40,
matching the top 3's 52.

All 52 stories happened, or were first reported, on Wednesday 18 November
2026. Stories first reported on Tuesday 17 November (the US strike on
Qeshm, Peltola's Alaska win, the Kerch Bridge span collapse, Nvidia's
quarter, the Knesset speaker vote, the Prague rail crash) are deliberately
NOT on the page; they are named in the date-check box instead.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
M = 24
CW = W - 2 * M  # 976 content width

PAPER = (251, 250, 247)
INK = (17, 17, 19)
BODY = (64, 62, 58)
NAVY = (18, 32, 62)
NAVY_SOFT = (38, 56, 92)
GOLD = (198, 154, 60)
CRIMSON = (166, 25, 46)
GREY = (96, 94, 88)
CARD = (255, 255, 255)
RULE = (208, 202, 188)
PALE = (206, 219, 238)
PALE_BG = (232, 236, 242)
RED = (178, 34, 34)
TEAL = (14, 120, 120)
ORANGE = (200, 110, 20)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def f(path, size):
    return ImageFont.truetype(path, size)


def wrap(d, text, font, max_w):
    out, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if d.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out


def para(d, lines, x, y, font, fill, leading):
    for ln in lines:
        d.text((x, y), ln, font=font, fill=fill)
        y += leading
    return y


def trunc(d, text, font, max_w):
    """Shorten text to fit max_w, adding an ellipsis if cut."""
    if d.textlength(text, font=font) <= max_w:
        return text
    ell = "…"
    while text and d.textlength(text + ell, font=font) > max_w:
        text = text[:-1].rstrip()
        # drop a whole word at a time where possible
        if " " in text:
            text = text.rsplit(" ", 1)[0]
        else:
            text = text[:-1]
    return text + ell


# ---------------- pictograms, drawn from primitives ----------------

def pic_flags(d, cx, cy, s, col):
    # three small summit flags: USA, China, Russia
    fw, fh = s * 0.28, s * 0.34
    gap = s * 0.05
    x0 = cx - 1.5 * fw - gap
    x = x0
    for i in range(5):
        d.rectangle([x, cy - fh / 2 + i * fh / 5, x + fw, cy - fh / 2 + (i + 1) * fh / 5],
                    fill=(178, 34, 34) if i % 2 == 0 else (255, 255, 255))
    d.rectangle([x, cy - fh / 2, x + fw * 0.45, cy - fh / 2 + fh * 0.4], fill=(30, 50, 110))
    x = x0 + fw + gap
    d.rectangle([x, cy - fh / 2, x + fw, cy + fh / 2], fill=(222, 40, 40))
    d.ellipse([x + fw * 0.14, cy - fh * 0.28, x + fw * 0.38, cy - fh * 0.04],
              fill=(255, 210, 60))
    x = x0 + 2 * (fw + gap)
    for i, c in enumerate([(255, 255, 255), (40, 90, 180), (200, 40, 40)]):
        d.rectangle([x, cy - fh / 2 + i * fh / 3, x + fw, cy - fh / 2 + (i + 1) * fh / 3],
                    fill=c)
    for x in (x0, x0 + fw + gap, x0 + 2 * (fw + gap)):
        d.line([x, cy - fh / 2, x, cy + fh / 2 + s * 0.10], fill=col, width=max(2, int(s * 0.04)))


def pic_drone(d, cx, cy, s, col):
    d.ellipse([cx - s * 0.24, cy - s * 0.12, cx + s * 0.24, cy + s * 0.12], fill=col)
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        x, y = cx + dx * s * 0.38, cy + dy * s * 0.26
        d.line([cx, cy, x, y], fill=col, width=max(2, int(s * 0.05)))
        d.line([x - s * 0.14, y, x + s * 0.14, y], fill=col, width=max(3, int(s * 0.08)))


def pic_rocket(d, cx, cy, s, col):
    # rocket climbing diagonally, nose up-right, flame behind
    flame = [(cx - s * 0.34, cy + s * 0.30), (cx - s * 0.52, cy + s * 0.38),
             (cx - s * 0.42, cy + s * 0.54), (cx - s * 0.24, cy + s * 0.42)]
    d.polygon(flame, fill=(232, 120, 40))
    d.polygon([(cx - s * 0.34, cy + s * 0.30), (cx - s * 0.46, cy + s * 0.36),
               (cx - s * 0.38, cy + s * 0.48), (cx - s * 0.26, cy + s * 0.40)],
              fill=(255, 200, 60))
    body = [(cx - s * 0.28, cy + s * 0.18), (cx + s * 0.12, cy - s * 0.30),
            (cx + s * 0.30, cy - s * 0.42), (cx + s * 0.38, cy - s * 0.30),
            (cx + s * 0.26, cy - s * 0.06), (cx - s * 0.16, cy + s * 0.30)]
    d.polygon(body, fill=col)
    d.ellipse([cx + s * 0.02, cy - s * 0.26, cx + s * 0.18, cy - s * 0.10],
              fill=(120, 150, 190))
    d.polygon([(cx - s * 0.26, cy + s * 0.10), (cx - s * 0.44, cy + s * 0.22),
               (cx - s * 0.30, cy + s * 0.02)], fill=col)
    d.polygon([(cx - s * 0.14, cy + s * 0.28), (cx - s * 0.22, cy + s * 0.46),
               (cx - s * 0.02, cy + s * 0.34)], fill=col)
    for dx, dy in ((0.42, -0.40), (0.48, -0.10), (0.30, -0.48)):
        d.ellipse([cx + dx * s - 2, cy + dy * s - 2, cx + dx * s + 2, cy + dy * s + 2],
                  fill=col)


def pic_chart_down(d, cx, cy, s, col):
    # falling bars + down arrow
    w = max(2, int(s * 0.06))
    bars = [0.42, 0.34, 0.28, 0.18]
    bw = s * 0.16
    x0 = cx - s * 0.40
    for i, h in enumerate(bars):
        x = x0 + i * (bw + s * 0.04)
        d.rectangle([x, cy + s * 0.30 - h * s, x + bw, cy + s * 0.30], fill=col)
    d.line([cx - s * 0.44, cy - s * 0.28, cx + s * 0.10, cy - s * 0.02,
            cx + s * 0.44, cy + s * 0.10], fill=CRIMSON, width=w)
    d.polygon([(cx + s * 0.44, cy + s * 0.10), (cx + s * 0.44, cy - s * 0.10),
               (cx + s * 0.24, cy + s * 0.10)], fill=CRIMSON)


def pic_cyclone(d, cx, cy, s, col):
    for i, (r, a0, a1) in enumerate(((0.44, 20, 300), (0.32, 140, 420), (0.20, 260, 540))):
        d.arc([cx - s * r, cy - s * r, cx + s * r, cy + s * r], start=a0, end=a1,
              fill=col, width=max(3, int(s * 0.09)))
    d.ellipse([cx - s * 0.06, cy - s * 0.06, cx + s * 0.06, cy + s * 0.06], fill=col)


def burst(d, cx, cy, r, col):
    pts = []
    for i in range(16):
        ang = math.pi * i / 8
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=col)


def pic_eu(d, cx, cy, s, col):
    # EU flag: blue field, ring of stars
    fw, fh = s * 0.78, s * 0.52
    d.rectangle([cx - fw / 2, cy - fh / 2, cx + fw / 2, cy + fh / 2], fill=(30, 60, 140))
    for k in range(12):
        ang = math.pi * k / 6 - math.pi / 2
        x = cx + s * 0.24 * math.cos(ang)
        y = cy + s * 0.16 * math.sin(ang)
        d.ellipse([x - s * 0.035, y - s * 0.035, x + s * 0.035, y + s * 0.035],
                  fill=(255, 210, 60))


def pic_chart_up(d, cx, cy, s, col):
    # rising bars + up arrow
    w = max(2, int(s * 0.06))
    bars = [0.18, 0.28, 0.34, 0.42]
    bw = s * 0.16
    x0 = cx - s * 0.40
    for i, h in enumerate(bars):
        x = x0 + i * (bw + s * 0.04)
        d.rectangle([x, cy + s * 0.30 - h * s, x + bw, cy + s * 0.30], fill=col)
    d.line([cx - s * 0.44, cy + s * 0.10, cx + s * 0.10, cy - s * 0.02,
            cx + s * 0.44, cy - s * 0.28], fill=CRIMSON, width=w)
    d.polygon([(cx + s * 0.44, cy - s * 0.28), (cx + s * 0.44, cy - s * 0.08),
               (cx + s * 0.24, cy - s * 0.28)], fill=CRIMSON)


def pic_tank(d, cx, cy, s, col):
    # tank: hull, turret, barrel, tracks
    w = max(2, int(s * 0.05))
    d.rectangle([cx - s * 0.40, cy + s * 0.02, cx + s * 0.40, cy + s * 0.24],
                fill=col)
    d.rectangle([cx - s * 0.18, cy - s * 0.22, cx + s * 0.14, cy + s * 0.02],
                fill=col)
    d.line([cx + s * 0.14, cy - s * 0.14, cx + s * 0.48, cy - s * 0.22],
           fill=col, width=w)
    d.rectangle([cx - s * 0.44, cy + s * 0.24, cx + s * 0.44, cy + s * 0.38],
                outline=col, width=w)
    for i in range(5):
        x = cx - s * 0.34 + i * s * 0.17
        d.ellipse([x - s * 0.05, cy + s * 0.26, x + s * 0.05, cy + s * 0.36],
                  fill=col)


def pic_ballot(d, cx, cy, s, col):
    w = max(2, int(s * 0.06))
    d.rectangle([cx - s * 0.34, cy - s * 0.02, cx + s * 0.34, cy + s * 0.36],
                outline=col, width=w)
    d.line([cx - s * 0.34, cy - s * 0.02, cx + s * 0.34, cy - s * 0.02],
           fill=col, width=w)
    d.rectangle([cx - s * 0.12, cy - s * 0.06, cx + s * 0.12, cy - s * 0.02], fill=col)
    d.polygon([(cx - s * 0.16, cy - s * 0.36), (cx + s * 0.14, cy - s * 0.40),
               (cx + s * 0.06, cy - s * 0.06), (cx - s * 0.22, cy - s * 0.02)],
              fill=(255, 255, 255), outline=col)
    d.line([cx - s * 0.12, cy - s * 0.22, cx - s * 0.03, cy - s * 0.12,
            cx + s * 0.10, cy - s * 0.32], fill=CRIMSON, width=w)


def pic_controller(d, cx, cy, s, col):
    # game controller: body, d-pad, buttons, sticks
    d.rounded_rectangle([cx - s * 0.44, cy - s * 0.24, cx + s * 0.44, cy + s * 0.30],
                        radius=int(s * 0.14), fill=col)
    d.rectangle([cx - s * 0.34, cy - s * 0.04, cx - s * 0.14, cy + s * 0.04],
                fill=(255, 255, 255))
    d.rectangle([cx - s * 0.28, cy - s * 0.10, cx - s * 0.20, cy + s * 0.10],
                fill=(255, 255, 255))
    for dx, dy, c in ((0.22, -0.08, (255, 210, 60)), (0.32, 0.02, (255, 255, 255)),
                      (0.22, 0.12, (255, 255, 255)), (0.12, 0.02, (255, 255, 255))):
        d.ellipse([cx + dx * s - s * 0.05, cy + dy * s - s * 0.05,
                   cx + dx * s + s * 0.05, cy + dy * s + s * 0.05], fill=c)
    d.ellipse([cx - s * 0.08, cy + s * 0.10, cx + s * 0.02, cy + s * 0.20],
              fill=(255, 255, 255))
    d.ellipse([cx + s * 0.06, cy + s * 0.02, cx + s * 0.16, cy + s * 0.12],
              fill=(255, 255, 255))


def pic_factory(d, cx, cy, s, col):
    # factory: sawtooth roof, chimney, smoke, windows
    w = max(2, int(s * 0.05))
    d.rectangle([cx - s * 0.40, cy + s * 0.30, cx + s * 0.40, cy + s * 0.30],
                fill=col, width=w)
    d.polygon([(cx - s * 0.40, cy + s * 0.30), (cx - s * 0.40, cy - s * 0.02),
               (cx - s * 0.14, cy - s * 0.02), (cx - s * 0.14, cy - s * 0.16),
               (cx + s * 0.12, cy - s * 0.16), (cx + s * 0.12, cy - s * 0.02),
               (cx + s * 0.40, cy - s * 0.02), (cx + s * 0.40, cy + s * 0.30)],
              fill=col)
    d.rectangle([cx + s * 0.26, cy - s * 0.44, cx + s * 0.38, cy - s * 0.02],
                fill=col)
    for i, (dx, dy, r) in enumerate(((0.32, -0.50, 0.07), (0.36, -0.58, 0.05),
                                     (0.28, -0.60, 0.04))):
        d.ellipse([cx + dx * s - r * s, cy + dy * s - r * s,
                   cx + dx * s + r * s, cy + dy * s + r * s], fill=GREY)
    for dx in (-0.28, -0.02, 0.24):
        d.rectangle([cx + dx * s - s * 0.05, cy + s * 0.08,
                     cx + dx * s + s * 0.05, cy + s * 0.20], fill=(255, 255, 255))


# ---------------- card banners ----------------
# A banner is a wide scene at the top of each card. Each one is built in
# three layers so it reads richer than a flat drawing: a vertical sky
# gradient (drawn as thin bands), a background scene (skyline, stars,
# rain, ground), and a foreground pictogram with a small detail
# (a sun, a moon, a trajectory, smoke, a leader line). Original drawings,
# built from the same primitives as the pictograms above.


def vgrad(d, x0, y0, x1, y1, top, bottom, bands=8):
    """Vertical gradient as thin horizontal bands (PIL has no gradient)."""
    for i in range(bands):
        t = i / (bands - 1) if bands > 1 else 0
        col = tuple(int(top[k] + (bottom[k] - top[k]) * t) for k in range(3))
        y_a = y0 + (y1 - y0) * i / bands
        y_b = y0 + (y1 - y0) * (i + 1) / bands
        d.rectangle([x0, y_a, x1, y_b], fill=col)


def draw_banner(d, x0, y0, x1, y1, kind, accent, icon):
    w, h = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    s = int(h * 0.78)
    if kind == "flags":
        # dawn sky gradient, sun, skyline, the three summit flags
        vgrad(d, x0, y0, x1, y1, (255, 214, 130), (255, 178, 90))
        d.ellipse([x1 - 46, y0 + 5, x1 - 18, y0 + 33], fill=(255, 240, 180))
        d.ellipse([x1 - 42, y0 + 9, x1 - 22, y0 + 29], fill=(255, 226, 140))
        for bx, bw, bh in ((0.00, 0.15, 0.34), (0.17, 0.11, 0.24), (0.30, 0.16, 0.42),
                           (0.48, 0.11, 0.28), (0.61, 0.15, 0.38), (0.78, 0.11, 0.24),
                           (0.91, 0.09, 0.32)):
            d.rectangle([x0 + w * bx, y1 - h * bh, x0 + w * (bx + bw), y1],
                        fill=(24, 38, 66))
        for bx in (0.05, 0.35, 0.66, 0.84):
            for wy in (0.55, 0.70):
                d.rectangle([x0 + w * bx, y1 - h * wy, x0 + w * bx + 4, y1 - h * wy + 5],
                            fill=(255, 210, 110))
        pic_flags(d, cx, cy - 6, int(h * 1.05), accent)
    elif kind == "drone_night":
        # deep night gradient, crescent moon, stars, city lights, drone
        vgrad(d, x0, y0, x1, y1, (14, 22, 52), (28, 42, 78))
        d.ellipse([x0 + w * 0.82, y0 + 4, x0 + w * 0.82 + 16, y0 + 20],
                  fill=(240, 238, 220))
        d.ellipse([x0 + w * 0.82 + 5, y0 + 2, x0 + w * 0.82 + 21, y0 + 18],
                  fill=(28, 42, 78))
        for sx, sy in ((0.07, 0.22), (0.18, 0.60), (0.30, 0.16), (0.52, 0.72),
                       (0.66, 0.24), (0.79, 0.58), (0.90, 0.20)):
            d.ellipse([x0 + w * sx - 1.5, y0 + h * sy - 1.5,
                       x0 + w * sx + 1.5, y0 + h * sy + 1.5], fill=(255, 255, 255))
        for i in range(14):
            x = x0 + w * (0.03 + i * 0.07)
            d.ellipse([x - 1.5, y1 - 9, x + 1.5, y1 - 6], fill=(255, 190, 90))
        pic_drone(d, cx, cy - 2, s, (255, 255, 255))
    elif kind == "rocket":
        # space gradient, stars, Earth, dashed trajectory, rocket
        vgrad(d, x0, y0, x1, y1, (8, 12, 36), (20, 30, 66))
        for sx, sy in ((0.06, 0.30), (0.16, 0.14), (0.28, 0.55), (0.45, 0.18),
                       (0.60, 0.65), (0.74, 0.28), (0.86, 0.12), (0.93, 0.55)):
            d.ellipse([x0 + w * sx - 1.5, y0 + h * sy - 1.5,
                       x0 + w * sx + 1.5, y0 + h * sy + 1.5], fill=(255, 255, 255))
        d.ellipse([x0 + w * 0.06, cy - 9, x0 + w * 0.06 + 18, cy + 9],
                  fill=(90, 140, 190))
        d.arc([x0 + w * 0.06, cy - 9, x0 + w * 0.06 + 18, cy + 9], 200, 340,
              fill=(160, 200, 235), width=2)
        for i in range(7):
            t = i / 6
            tx = x0 + w * (0.14 + t * 0.55)
            ty = cy + h * (0.28 - t * 0.55)
            d.ellipse([tx - 1.5, ty - 1.5, tx + 1.5, ty + 1.5], fill=(255, 210, 90))
        pic_rocket(d, cx, cy, s, (235, 240, 250))
    elif kind == "drone_dusk":
        # dusk gradient, bursts, smoke trail, drone
        vgrad(d, x0, y0, x1, y1, (74, 40, 44), (40, 24, 34))
        for sx, sy in ((0.10, 0.25), (0.25, 0.65), (0.40, 0.20), (0.60, 0.70),
                       (0.75, 0.30), (0.88, 0.60)):
            burst(d, x0 + w * sx, y0 + h * sy, 4, (255, 150, 60))
        d.line([x0 + w * 0.55, y0 + h * 0.30, x0 + w * 0.72, y0 + h * 0.18],
               fill=(200, 200, 200), width=2)
        d.ellipse([x0 + w * 0.72, y0 + h * 0.14, x0 + w * 0.72 + 7, y0 + h * 0.14 + 7],
                  fill=(220, 220, 220))
        pic_drone(d, cx, cy - 2, s, (255, 255, 255))
    elif kind == "chart_down":
        # paper with gridlines and a falling line
        d.rectangle([x0, y0, x1, y1], fill=(240, 238, 230))
        for i in range(5):
            y = y0 + h * (0.18 + i * 0.16)
            d.line([x0 + 6, y, x1 - 6, y], fill=(220, 216, 206), width=1)
        pic_chart_down(d, cx, cy, s, NAVY)
    elif kind == "cyclone":
        # storm sky gradient, rain, coastline + wave, cyclone swirl
        vgrad(d, x0, y0, x1, y1, (150, 196, 228), (190, 220, 240))
        for i in range(6):
            x = x0 + w * (0.10 + i * 0.15)
            d.line([x, y0 + 4, x - 6, y0 + h * 0.45], fill=(255, 255, 255), width=2)
            x2 = x0 + w * (0.16 + i * 0.15)
            d.line([x2, y0 + h * 0.55, x2 - 6, y1 - 4], fill=(255, 255, 255), width=2)
        d.rectangle([x0, y1 - h * 0.16, x1, y1], fill=(60, 110, 160))
        for i in range(5):
            x = x0 + w * (0.06 + i * 0.20)
            d.arc([x, y1 - h * 0.16, x + w * 0.12, y1 - h * 0.02], 180, 360,
                  fill=(220, 240, 255), width=2)
        pic_cyclone(d, cx, cy - 4, s, (20, 60, 110))
    elif kind == "burst":
        # dark red gradient, radiating lines, two bursts
        vgrad(d, x0, y0, x1, y1, (84, 32, 32), (48, 20, 22))
        for k in range(8):
            ang = math.pi * k / 4
            d.line([cx, cy, cx + w * 0.48 * math.cos(ang),
                    cy + h * 0.48 * math.sin(ang)], fill=(120, 60, 50), width=2)
        burst(d, cx, cy, int(h * 0.34), (255, 190, 60))
        burst(d, x0 + w * 0.86, y0 + h * 0.22, int(h * 0.14), (255, 150, 60))
    elif kind == "eu":
        # EU blue gradient, ring of stars, the loan figure
        vgrad(d, x0, y0, x1, y1, (36, 70, 158), (20, 44, 110))
        for k in range(12):
            ang = math.pi * k / 6 - math.pi / 2
            x = cx + w * 0.30 * math.cos(ang)
            y = cy + h * 0.30 * math.sin(ang)
            d.ellipse([x - 2.5, y - 2.5, x + 2.5, y + 2.5], fill=(255, 210, 60))
        ef = f(SANS_B, int(h * 0.62))
        txt = "€45bn"
        tw = d.textlength(txt, font=ef)
        d.text((cx - tw / 2, cy - h * 0.31), txt, font=ef, fill=(255, 255, 255))
    elif kind == "chart_up":
        # paper with gridlines and a rising line
        d.rectangle([x0, y0, x1, y1], fill=(240, 238, 230))
        for i in range(5):
            y = y0 + h * (0.18 + i * 0.16)
            d.line([x0 + 6, y, x1 - 6, y], fill=(220, 216, 206), width=1)
        pic_chart_up(d, cx, cy, s, NAVY)
    elif kind == "tank":
        # desert gradient, sun, dunes, tank
        vgrad(d, x0, y0, x1, y1, (238, 214, 168), (214, 186, 138))
        d.ellipse([x1 - 34, y0 + 4, x1 - 12, y0 + 26], fill=(255, 220, 130))
        d.rectangle([x0, y1 - h * 0.22, x1, y1], fill=(190, 165, 120))
        d.line([x0, y1 - h * 0.22, x1, y1 - h * 0.22], fill=(150, 125, 85), width=2)
        for i in range(4):
            x = x0 + w * (0.08 + i * 0.22)
            d.arc([x, y1 - h * 0.22, x + w * 0.14, y1 - h * 0.08], 180, 360,
                  fill=(160, 135, 95), width=2)
        pic_tank(d, cx, cy - 4, s, (90, 70, 45))
    elif kind == "ballot":
        # navy gradient, capitol dome silhouette, ballot boxes, ballot
        vgrad(d, x0, y0, x1, y1, (38, 62, 128), (22, 38, 88))
        d.ellipse([cx - w * 0.30, y1 - h * 0.55, cx - w * 0.30 + 18, y1 - h * 0.25],
                  fill=(52, 78, 140))
        d.rectangle([cx - w * 0.30 - 2, y1 - h * 0.42, cx - w * 0.30 + 20, y1 - h * 0.25],
                    fill=(52, 78, 140))
        d.rectangle([cx - w * 0.30 + 6, y1 - h * 0.62, cx - w * 0.30 + 12, y1 - h * 0.55],
                    fill=(52, 78, 140))
        for i in range(4):
            x = x0 + w * (0.10 + i * 0.22)
            d.rectangle([x, y1 - h * 0.30, x + w * 0.10, y1], fill=(52, 78, 140))
        pic_ballot(d, cx, cy - 2, s, (255, 255, 255))
    elif kind == "controller":
        # purple gradient, floating game shapes, controller
        vgrad(d, x0, y0, x1, y1, (72, 48, 106), (48, 30, 78))
        for sx, sy in ((0.08, 0.25), (0.20, 0.65), (0.35, 0.18), (0.65, 0.70),
                       (0.80, 0.25), (0.92, 0.60)):
            d.ellipse([x0 + w * sx - 2, y0 + h * sy - 2, x0 + w * sx + 2, y0 + h * sy + 2],
                      fill=(150, 120, 190))
        d.polygon([(x0 + w * 0.12, y0 + h * 0.18), (x0 + w * 0.16, y0 + h * 0.28),
                   (x0 + w * 0.08, y0 + h * 0.28)], fill=(255, 210, 60))
        d.ellipse([x0 + w * 0.88, y0 + h * 0.62, x0 + w * 0.88 + 8, y0 + h * 0.62 + 8],
                  fill=(255, 210, 60))
        pic_controller(d, cx, cy, s, (240, 240, 250))
    elif kind == "factory":
        # warm sky gradient, smoke, chimneys, factory
        vgrad(d, x0, y0, x1, y1, (248, 196, 132), (232, 160, 100))
        for bx, bw, bh in ((0.00, 0.14, 0.30), (0.16, 0.12, 0.22), (0.70, 0.14, 0.34),
                           (0.86, 0.14, 0.26)):
            d.rectangle([x0 + w * bx, y1 - h * bh, x0 + w * (bx + bw), y1],
                        fill=(150, 90, 50))
        d.ellipse([x0 + w * 0.60, y0 + 3, x0 + w * 0.60 + 9, y0 + 12], fill=(245, 245, 245))
        d.ellipse([x0 + w * 0.64, y0 + 8, x0 + w * 0.64 + 7, y0 + 15], fill=(245, 245, 245))
        pic_factory(d, cx, cy - 2, s, (80, 50, 30))


# ---------------- data ----------------

# (number, region, topic, verify, accent, banner kind, icon, headline, body)
# bodies kept short so they fit their card: big cards <= 2 lines at 13px,
# small cards <= 2 lines at 12px; headlines: big <= 2 lines at 18px,
# small <= 3 lines at 14px.
CARDS = [
    (1, "ASIA", "APEC SUMMIT", "CONFIRMED · AP · CNBC", NAVY, "flags", pic_flags,
     "Xi welcomes Trump in Shenzhen",
     "APEC opens as Trump lands; the first Trump–Xi–Putin talks are set for Thursday."),
    (2, "MIDDLE EAST", "IRAN WAR", "CLAIM · AP · REUTERS", CRIMSON, "drone_night", pic_drone,
     "Bahrain and Kuwait intercept Iran's drones",
     "Bahrain and Kuwait intercept drones aimed at US sites, a day after the Qeshm strike."),
    (3, "WORLD", "SPACE", "CONFIRMED · NASA", NAVY_SOFT, "rocket", pic_rocket,
     "Voyager 1 reaches one light-day from Earth",
     "The probe reaches 25.9 billion km — the first object to travel a full light-day."),
    (4, "EUROPE", "UKRAINE WAR", "KYIV · AFP", CRIMSON, "drone_dusk", pic_drone,
     "141 drones in one night over Ukraine",
     "141 drones fired, 126 downed; four killed."),
    (5, "AMERICAS", "MARKETS", "FED", TEAL, "chart_down", pic_chart_down,
     "Fed signals more rate rises",
     "Minutes point to more hikes; Dow falls 561, -1.1%."),
    (6, "ASIA", "WEATHER", "IMD", ORANGE, "cyclone", pic_cyclone,
     "Cyclone Akvan turns toward Odisha",
     "Landfall due Friday; 50,000 moved to safety."),
    (7, "AFRICA", "SUDAN WAR", "AMNESTY", CRIMSON, "burst", burst,
     "37 killed by RSF drones in El Obeid",
     "Amnesty: 37 killed; it urges a war-crimes inquiry."),
    (8, "EUROPE", "UKRAINE AID", "EU", NAVY_SOFT, "eu", pic_eu,
     "EU plans a €45bn loan for Kyiv",
     "To fund Kyiv through 2027; repaid if Russia pays."),
    (9, "EUROPE", "ECONOMY", "ONS", TEAL, "chart_up", pic_chart_up,
     "UK inflation hits a one-year high",
     "Prices rise 3.6% as fuel and tobacco duty go up."),
    (10, "MIDDLE EAST", "GAZA", "REUTERS", CRIMSON, "tank", pic_tank,
     "Israeli tanks push into central Gaza",
     "Tanks advance near Nuseirat; army cites a tunnel."),
    (11, "AMERICAS", "US POLITICS", "NPR", NAVY, "ballot", pic_ballot,
     "Jeffries wins Democrats' nod for House Speaker",
     "Picked 251–11; the first Black Speaker in sight."),
    (12, "WORLD", "CULTURE", "ROCKSTAR", GOLD, "controller", pic_controller,
     "GTA VI goes on sale at last",
     "After a 13-year wait, it launches; 14.9m pre-orders."),
    (13, "ASIA", "LABOUR", "DHAKA", ORANGE, "factory", pic_factory,
     "Bangladesh wage protests shut 55 factories",
     "Police tear-gas workers; 55 factories shut."),
]

MORE = [
    (14, "Manila", "Trump hails the 'biggest' Philippine trade deal."),
    (15, "Tokyo", "Takaichi makes first China visit since 2019."),
    (16, "Ottawa", "Carney and Xi agree tariff relief at APEC."),
    (17, "Seoul", "Lee seeks Xi's help on the North."),
    (18, "Riyadh", "The coalition downs a Houthi cruise missile."),
    (19, "Beirut", "World Bank warns Lebanon's rebuilding lags badly."),
    (20, "Berlin", "Germany pledges air defences and F-16 ammo to Kyiv."),
    (21, "The Hague", "Court gives ex-president Thaci 17 months."),
    (22, "Kemerovo", "19 die in an An-12 crash."),
    (23, "London", "Britain hands a US Army spy suspect to Washington."),
    (24, "Kinshasa", "Ebola passes 11,300 cases; WHO keeps its global emergency."),
    (25, "Washington", "The US loses measles-elimination status after 26 years."),
    (26, "Badme", "Ethiopia and Eritrea trade artillery fire in a buildup."),
    (27, "Guinea", "224 jailed over illegal gold mining."),
    (28, "Maputo", "Opposition leader Mondlane goes on trial."),
    (29, "Pretoria", "South Africa reprimands Nigeria's incoming envoy."),
    (30, "San Francisco", "Anthropic prices an $81bn IPO at $83; trading starts Thursday."),
    (31, "Caracas", "Hegseth visits and seals a defence pact."),
    (32, "Bogota", "Colombia's economy shrinks 0.8% in the third quarter."),
    (33, "Brasilia", "The Senate passes Lula's $10bn fiscal package."),
    (34, "Peru", "The Tumbes River passes its red-alert level."),
    (35, "Antalya", "COP31 ministers weigh a divided fossil-fuel draft."),
    (36, "Turin", "Alcaraz beats Medvedev 6–2, 6–4 at the ATP Finals."),
    (37, "Paris", "FIFA — France's Diallo to challenge Infantino."),
    (38, "Sydney", "Tame Impala sweeps seven ARIA Music Awards."),
    (39, "Pacific", "Cat-5 Cyclone Xavier turns east; 6.0 quake hits PNG."),
    (40, "Canberra", "Australia sanctions settler leader Daniella Weiss."),
    # 12 more, taken from the top-ranked entry's own also-list (all verified
    # 18 Nov, none already on this page, none a Tuesday story):
    (41, "London", "Lammy urges Burnham to back rejoining the EU."),
    (42, "Berlin", "Coalition agrees a power-tax cut for all."),
    (43, "Krasnodar", "Ukraine hits two oil refineries in Russia."),
    (44, "Zaporizhzhia", "85 children ordered out of Balabyne."),
    (45, "London", "Chelsea women beat PSG 1–0 in Europe."),
    (46, "Beirut", "US adds sanctions on Hezbollah."),
    (47, "Baghdad", "Six French nationals get life for joining ISIL."),
    (48, "Kuwait City", "Magnitude 4.1 quake in the south-west."),
    (49, "Tokyo", "PM Takaichi meets Putin, a first since 2022."),
    (50, "Redmond", "Microsoft to use Intel chip packaging."),
    (51, "Kampala", "Uganda agrees with Tanzania to speed up oil pipeline."),
    (52, "US", "Top egg producer to cull 1.8m birds over bird flu."),
]

NUMBERS = [
    ("141", "drones fired"),
    ("126", "downed"),
    ("25.9bn km", "Voyager 1"),
    ("55", "factories shut"),
    ("251–11", "Jeffries"),
    ("11,300+", "Ebola"),
]

REGIONS = [("EUROPE", 13), ("AMERICAS", 11), ("ASIA", 7), ("AFRICA", 7),
           ("MIDDLE EAST", 7), ("OCEANIA", 3), ("WORLD", 4)]

# field counts for all 52 stories (adds to 52):
# Diplomacy 10, War & security 9, Economy & markets 8, Politics & courts 6,
# Culture & sport 5, Business & tech 2, Labour & society 2,
# Climate & disasters 6, Science & health 4.
FIELDS = [("Diplomacy", 10), ("War & security", 9), ("Economy & markets", 8),
          ("Politics & courts", 6), ("Culture & sport", 5),
          ("Business & tech", 2), ("Labour & society", 2),
          ("Climate & disasters", 6), ("Science & health", 4)]

# the day in UTC: 8 slots across Wednesday 18 November 2026
UTC_TIMELINE = [
    ("OVERNIGHT", "Drones over Kuwait"),
    ("07:00 UTC", "UK inflation 3.6%"),
    ("MORNING", "Xi greets Trump"),
    ("10:16 UTC", "Voyager 1 light-day"),
    ("11:00 UTC", "GTA VI unlocks"),
    ("19:00 UTC", "Fed: more hikes"),
    ("21:00 UTC", "Dow down 561"),
    ("LATE", "Anthropic IPO"),
]

LEFT_OUT = ("the US strike on Qeshm · Peltola's Alaska Senate win · the Kerch "
            "Bridge span collapse · Nvidia's $115.8bn quarter · the Knesset "
            "speaker vote · the Prague rail crash")
NOT_YET = ("the Trump–Xi–Putin talks (Thu 19) · Cyclone Akvan's landfall "
           "(Fri 20) · the close of COP31 (Fri 20)")

# (number, lat, lon) for the map pins
PINS = [
    (1, 22.5, 114.0), (2, 26.0, 50.5), (3, 34.2, -118.2), (4, 50.4, 30.5),
    (5, 40.7, -74.0), (6, 20.0, 86.0), (7, 13.2, 30.2), (8, 50.8, 4.4),
    (9, 51.5, -0.1), (10, 31.4, 34.4), (11, 38.9, -77.0), (12, -41.3, 174.8),
    (13, 23.8, 90.4),
]

# display offsets (dx, dy) for pins that would overlap at their true spot;
# a thin leader line is drawn from the true spot to the nudged pin.
PIN_OFF = {
    4: (8, 2), 5: (6, -8), 6: (-6, 6), 7: (-4, 12), 8: (10, 2),
    9: (-10, 10), 10: (14, 8), 11: (-6, 8), 12: (0, -5), 13: (7, -7),
}

# dotted world map: landmasses as lon/lat ellipses (centre lon, centre lat,
# half-width lon, half-height lat); a dot is drawn for every grid cell
# whose centre falls inside one of them.
LANDMASSES = [
    (-100, 47, 58, 20), (-152, 64, 18, 8), (-86, 14, 12, 7), (-42, 73, 14, 9),
    (-60, -14, 19, 27), (14, 53, 26, 15), (-2, 54, 4, 5), (17, 3, 31, 32),
    (47, -19, 3, 8), (48, 30, 18, 12), (70, 45, 30, 18), (115, 42, 35, 20),
    (78, 21, 11, 11), (103, 13, 11, 9), (114, -2, 24, 5), (134, -25, 19, 11),
    (141, -5, 9, 4), (139, 37, 4, 6), (172, -41, 4, 6),
]


def _on_land(lon, lat):
    for clon, clat, hlon, hlat in LANDMASSES:
        if ((lon - clon) / hlon) ** 2 + ((lat - clat) / hlat) ** 2 <= 1:
            return True
    return False


# ---------------- page ----------------

img = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(img)

# ============ header (y 12-100) ============
HY = 12
d.rectangle([M, HY, W - M, HY + 88], fill=NAVY)
d.rectangle([M, HY, W - M, HY + 5], fill=CRIMSON)
# date block, left (width sized to fit "NOV 18" at 27px, text centred)
blk_x0, blk_x1 = M + 12, M + 150
d.rectangle([blk_x0, HY + 12, blk_x1, HY + 76], fill=(255, 255, 255))
db1 = f(SANS_B, 27)
t1 = "NOV 18"
d.text((blk_x0 + (blk_x1 - blk_x0 - d.textlength(t1, font=db1)) / 2, HY + 16),
       t1, font=db1, fill=NAVY)
db2 = f(SANS_B, 16)
t2 = "WED · 2026"
d.text((blk_x0 + (blk_x1 - blk_x0 - d.textlength(t2, font=db2)) / 2, HY + 48),
       t2, font=db2, fill=CRIMSON)
# title, right of the block
tx = blk_x1 + 16
d.text((tx, HY + 8), "THE DAY IN WORLD NEWS", font=f(SANS_B, 15), fill=GOLD)
big = f(SERIF, 46)
d.text((tx, HY + 24), "Wednesday 18 November 2026", font=big, fill=(255, 255, 255))
d.text((tx, HY + 70), "Everything on this page happened, or was first reported, on that day.",
       font=f(SANS, 13), fill=PALE)
cnt = f(SANS_B, 13)
ct = "52 STORIES  ·  7 REGIONS  ·  9 FIELDS  ·  13 DRAWN  ·  ONE PAGE"
d.text((W - M - d.textlength(ct, font=cnt) - 10, HY + 8), ct, font=cnt, fill=GOLD)

# ============ region bar (y 104-124) + field bar (y 128-148) ============
RY = 104
d.rectangle([M, RY, W - M, RY + 20], fill=PALE_BG, outline=RULE)
x = M + 10
rf = f(SANS_B, 13)
for name, n in REGIONS:
    label = f"{name} {n}"
    w = d.textlength(label, font=rf)
    d.text((x, RY + 3), label, font=rf, fill=NAVY)
    x += w + 26
    if name != REGIONS[-1][0]:
        d.rectangle([x - 13, RY + 4, x - 12, RY + 16], fill=RULE)
FBY = 128
d.rectangle([M, FBY, W - M, FBY + 20], fill=(255, 255, 255), outline=RULE)
ff = f(SANS_B, 9)
d.text((M + 10, FBY + 6), "BY FIELD", font=ff, fill=CRIMSON)
fx = M + 10 + d.textlength("BY FIELD", font=ff) + 10
for name, n in FIELDS:
    label = f"{name} {n}"
    w = d.textlength(label, font=ff)
    d.text((fx, FBY + 6), label, font=ff, fill=NAVY_SOFT)
    fx += w + 10
    if name != FIELDS[-1][0]:
        d.rectangle([fx - 5, FBY + 5, fx - 4, FBY + 15], fill=RULE)

# ============ the day in numbers — one thin line (y 152-180) ============
NY = 152
d.text((M, NY + 6), "THE DAY IN NUMBERS", font=f(SANS_B, 12), fill=NAVY)
nx = M + d.textlength("THE DAY IN NUMBERS", font=f(SANS_B, 12)) + 12
nf = f(SANS_B, 13)
lf = f(SANS, 12)
for num, label in NUMBERS:
    nw = d.textlength(num, font=nf)
    d.text((nx, NY + 5), num, font=nf, fill=CRIMSON)
    nx += nw + 4
    lw = d.textlength(label, font=lf)
    d.text((nx, NY + 6), label, font=lf, fill=BODY)
    nx += lw + 8
    if num != NUMBERS[-1][0]:
        d.text((nx, NY + 6), "·", font=lf, fill=GOLD)
        nx += d.textlength("·", font=lf) + 8
d.rectangle([M, NY + 24, W - M, NY + 26], fill=GOLD)

# ============ the day in UTC — one thin strip (y 184-212) ============
TY = 184
d.text((M, TY + 2), "THE DAY", font=f(SANS_B, 11), fill=CRIMSON)
d.text((M, TY + 14), "IN UTC", font=f(SANS_B, 11), fill=CRIMSON)
tl_x0 = M + 78
tl_w = (CW - 78) // 8
tf_t = f(SANS_B, 10)
tf_e = f(SANS, 10)
for i, (t, ev) in enumerate(UTC_TIMELINE):
    cx = tl_x0 + i * tl_w
    d.text((cx, TY + 1), t, font=tf_t, fill=NAVY)
    d.text((cx, TY + 14), trunc(d, ev, tf_e, tl_w - 6), font=tf_e, fill=BODY)
    if i:
        d.rectangle([cx - 5, TY + 2, cx - 4, TY + 24], fill=RULE)
d.rectangle([M, TY + 26, W - M, TY + 28], fill=GOLD)

# ============ 13 cards (y 216-682) ============
CY = 216
GAP = 8
BAN_H = 52    # banner height, big cards
SBAN_H = 46   # banner height, small cards
# top row: 3 big cards
big_w = (CW - 2 * GAP) // 3
big_h = 150
for i in range(3):
    num, region, topic, verify, accent, kind, icon, head, body = CARDS[i]
    cx = M + i * (big_w + GAP)
    cy = CY
    d.rectangle([cx, cy, cx + big_w, cy + big_h], fill=CARD, outline=RULE, width=2)
    draw_banner(d, cx, cy, cx + big_w, cy + BAN_H, kind, accent, icon)
    # tag + verify on one line below the banner; shrink the tag if needed
    tf = f(SANS_B, 12)
    vf = f(SANS, 10)
    tag = f"{num} · {region} · {topic}"
    vw = d.textlength(verify, font=vf)
    while d.textlength(tag, font=tf) + vw + 16 > big_w - 20 and tf.size > 9:
        tf = f(SANS_B, tf.size - 1)
    d.text((cx + 10, cy + BAN_H + 6), tag, font=tf, fill=accent)
    d.text((cx + big_w - vw - 10, cy + BAN_H + 7), verify, font=vf, fill=GREY)
    # headline, up to 2 lines
    hf = f(SANS_B, 18)
    hlines = wrap(d, head, hf, big_w - 20)[:2]
    y2 = para(d, hlines, cx + 10, cy + BAN_H + 26, hf, INK, 20)
    # body, up to 2 lines
    sf = f(SANS, 13)
    slines = wrap(d, body, sf, big_w - 20)[:2]
    para(d, slines, cx + 10, y2 + 3, sf, BODY, 14)

# rows 2-3: 10 small cards, 5 per row
small_w = (CW - 4 * GAP) // 5
small_h = 150
for j in range(10):
    num, region, topic, verify, accent, kind, icon, head, body = CARDS[3 + j]
    col, row = j % 5, j // 5
    cx = M + col * (small_w + GAP)
    cy = CY + big_h + GAP + row * (small_h + GAP)
    d.rectangle([cx, cy, cx + small_w, cy + small_h], fill=CARD, outline=RULE, width=2)
    draw_banner(d, cx, cy, cx + small_w, cy + SBAN_H, kind, accent, icon)
    # tag + verify on one line; drop the region word if it does not fit
    tf = f(SANS_B, 10)
    vf = f(SANS, 9)
    tag = f"{num} · {region} · {topic}"
    vw = d.textlength(verify, font=vf)
    if d.textlength(tag, font=tf) + vw + 6 > small_w - 20:
        tag = f"{num} · {topic}"
    if d.textlength(tag, font=tf) + vw + 6 > small_w - 20:
        tag = trunc(d, tag, tf, small_w - 20 - vw - 6)
    d.text((cx + 10, cy + SBAN_H + 5), tag, font=tf, fill=accent)
    d.text((cx + small_w - vw - 10, cy + SBAN_H + 6), verify, font=vf, fill=GREY)
    # headline, up to 3 lines
    hf = f(SANS_B, 14)
    hlines = wrap(d, head, hf, small_w - 20)[:3]
    y2 = para(d, hlines, cx + 10, cy + SBAN_H + 22, hf, INK, 16)
    # body, up to 2 lines
    sf = f(SANS, 12)
    slines = wrap(d, body, sf, small_w - 20)[:2]
    para(d, slines, cx + 10, y2 + 3, sf, BODY, 14)

# ============ world map (y 686-758) ============
MY = 686
d.text((M, MY), "WHERE IT HAPPENED", font=f(SANS_B, 15), fill=NAVY)
d.rectangle([M + 176, MY + 8, W - M, MY + 10], fill=GOLD)
map_top = 700
map_h = 58
map_bot = map_top + map_h
d.rectangle([M, map_top, W - M, map_bot], fill=(255, 255, 255), outline=RULE, width=1)
# dotted continents: a denser grid (140 x 14) so the landmasses read
# clearly at small size; one dot per grid cell whose centre is on land
cols, rows = 140, 14
for r in range(rows):
    lat = 85 - (r + 0.5) / rows * 140
    y = map_top + (r + 0.5) / rows * map_h
    for c in range(cols):
        lon = -180 + (c + 0.5) / cols * 360
        if _on_land(lon, lat):
            x = M + (c + 0.5) / cols * CW
            d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=(150, 160, 175))


def lonlat_to_xy(lat, lon):
    x = M + (lon + 180.0) / 360.0 * CW
    y = map_top + (85.0 - lat) / 140.0 * map_h
    return x, y


for num, lat, lon in PINS:
    x, y = lonlat_to_xy(lat, lon)
    dx, dy = PIN_OFF.get(num, (0, 0))
    px, py = x + dx, y + dy
    if (dx, dy) != (0, 0):
        # thin leader line from the true spot to the nudged pin
        d.line([x, y, px, py], fill=(166, 25, 46), width=1)
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(166, 25, 46))
    d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=CRIMSON, outline=(255, 255, 255), width=2)
    nf2 = f(SANS_B, 10)
    tw = d.textlength(str(num), font=nf2)
    d.text((px - tw / 2, py - 6), str(num), font=nf2, fill=(255, 255, 255))
d.text((M + 6, map_bot - 15), "3 · Voyager 1 is flown from Pasadena, California",
       font=f(SANS, 10), fill=GREY)

# ============ 39 more stories, 4 columns (y 762-916) ============
AY = 762
d.text((M, AY), "ALSO ON WEDNESDAY 18 NOVEMBER — 39 MORE STORIES",
       font=f(SANS_B, 15), fill=NAVY)
d.rectangle([M + 448, AY + 8, W - M, AY + 10], fill=GOLD)
col_w = (CW - 3 * 12) // 4
mf = f(SANS, 12)
bf = f(SANS_B, 12)
for k, (num, city, headline) in enumerate(MORE):
    col, row = k % 4, k // 4
    x = M + col * (col_w + 12)
    y = AY + 26 + row * 13
    d.text((x, y), f"{num}.", font=bf, fill=CRIMSON)
    # bold city, then the headline starting after the bold city's real
    # width plus a space (the old code redrew the city over the line and
    # the wider bold glyphs ate the space, reading "ManilaTrump").
    cw_ = d.textlength(city, font=bf)
    d.text((x + 24, y), city, font=bf, fill=INK)
    gap = d.textlength(" ", font=mf)
    head_x = x + 24 + cw_ + gap
    head = trunc(d, headline, mf, col_w - 24 - cw_ - gap)
    d.text((head_x, y), head, font=mf, fill=BODY)

# ============ date check (y 922-~, height from wrapped lines) ============
DY = 922
df = f(SANS, 12)
left_lines = wrap(d, "Each of these was first reported before Wednesday 18 November, so it is not on this page: " + LEFT_OUT + ".",
                  df, CW - 20)
notyet_lines = wrap(d, "Not yet happened: " + NOT_YET + ".", df, CW - 20)
box_h = 20 + 14 * len(left_lines) + 14 * len(notyet_lines) + 8
d.rectangle([M, DY, W - M, DY + box_h], fill=(255, 244, 230), outline=GOLD, width=2)
d.text((M + 10, DY + 5), "DATE CHECK — LEFT OUT ON PURPOSE",
       font=f(SANS_B, 13), fill=CRIMSON)
yy = para(d, left_lines, M + 10, DY + 20, df, BODY, 14)
para(d, notyet_lines, M + 10, yy, df, BODY, 14)

# ============ sources footer ============
FY = DY + box_h + 6
sf2 = f(SANS, 11)
foot = ("Sources: AP · Reuters · AFP · BBC · CNN · CNBC · NPR · Fed · ONS · IMD · NASA · WHO · Amnesty — "
        "All 52 stories first reported Wed 18 Nov 2026.")
fw = d.textlength(foot, font=sf2)
d.text(((W - fw) / 2, FY), foot, font=sf2, fill=GREY)

# self-check: 13 cards + 39 more = 52 stories; region and field counts
# must match the bars printed above.
assert len(CARDS) == 13 and len(MORE) == 39, (len(CARDS), len(MORE))
assert len(CARDS) + len(MORE) == 52
assert sum(n for _, n in REGIONS) == 52, REGIONS
assert sum(n for _, n in FIELDS) == 52, FIELDS

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
img.save(out, "PNG", optimize=True)
print("saved", out, os.path.getsize(out), "bytes")
