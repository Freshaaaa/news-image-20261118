#!/usr/bin/env python3
"""Draw the news-image-20261118 entry: a one-page newspaper front page summing
up the world news of Wednesday 18 November 2026, rendered with PIL so every
letter stays crisp at 1024x1024. No network, no randomness: the same run
always writes the same bytes.

Stories, each first reported on 18 November 2026 (OneTurn, Daily Baku,
Raj Global Studies, SimpleLife, Arab News):
  LEAD  U.S. jets strike a Revolutionary Guard missile site on Qeshm Island;
        Washington confirms it after Iran fires drones at U.S. radar sites
        in Bahrain and Kuwait.
  1     Ukraine hits the Kerch Bridge to Crimea for a second day; part of
        its road span falls into the strait.
  2     APEC opens in Shenzhen; Xi and Putin meet ahead of the first
        Trump-Xi-Putin trilateral; QUAD unveils a new plan in Manila.
  3     Mary Peltola unseats Dan Sullivan in Alaska's Senate race, giving
        Democrats a 56-seat majority.
  4     A Russian military plane crashes in the Kemerovo region; 19 dead.
  5     The DR Congo Ebola outbreak passes 11,000 cases and 5,400 deaths,
        the UN says.
  6     Category 5 Cyclone Xavier slams the Northern Cook Islands; quakes
        shake Papua New Guinea (6.0) and Romania (5.3).
  ALSO  Microsoft unveils seven in-house AI models; MS Dhoni retires from
        the IPL; the World Court is to rule on the Myanmar genocide case;
        oil slips as Hormuz risks limit losses; Houthi strikes on Saudi
        Arabia intercepted.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
M = 26

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


# ---------------- pictograms, drawn from primitives ----------------

def pic_bridge(d, cx, cy, s, col):
    # suspension bridge: deck, arch, two towers, hangers
    w = max(2, int(s * 0.05))
    d.line([cx - s * 0.46, cy + s * 0.28, cx + s * 0.46, cy + s * 0.28],
           fill=col, width=w)
    d.arc([cx - s * 0.40, cy - s * 0.30, cx + s * 0.40, cy + s * 0.42],
          start=180, end=360, fill=col, width=w)
    for tx in (-s * 0.30, s * 0.30):
        d.line([tx, cy - s * 0.34, tx, cy + s * 0.28], fill=col, width=w)
    for hx in (-0.22, -0.11, 0.0, 0.11, 0.22):
        x = cx + hx * s
        d.line([x, cy - s * 0.10, x, cy + s * 0.28], fill=col, width=max(1, w - 1))
    # broken span: a gap in the deck on the right
    d.line([cx + s * 0.16, cy + s * 0.28, cx + s * 0.30, cy + s * 0.42],
           fill=col, width=w)


def pic_flags(d, cx, cy, s, col):
    # three small summit flags: USA, China, Russia
    fw, fh = s * 0.28, s * 0.34
    gap = s * 0.05
    x0 = cx - 1.5 * fw - gap
    # USA: stripes + canton
    x = x0
    for i in range(5):
        d.rectangle([x, cy - fh / 2 + i * fh / 5, x + fw, cy - fh / 2 + (i + 1) * fh / 5],
                    fill=(178, 34, 34) if i % 2 == 0 else (255, 255, 255))
    d.rectangle([x, cy - fh / 2, x + fw * 0.45, cy - fh / 2 + fh * 0.4], fill=(30, 50, 110))
    # China: red + stars
    x = x0 + fw + gap
    d.rectangle([x, cy - fh / 2, x + fw, cy + fh / 2], fill=(222, 40, 40))
    d.ellipse([x + fw * 0.14, cy - fh * 0.28, x + fw * 0.38, cy - fh * 0.04],
              fill=(255, 210, 60))
    # Russia: white-blue-red tricolour
    x = x0 + 2 * (fw + gap)
    for i, c in enumerate([(255, 255, 255), (40, 90, 180), (200, 40, 40)]):
        d.rectangle([x, cy - fh / 2 + i * fh / 3, x + fw, cy - fh / 2 + (i + 1) * fh / 3],
                    fill=c)
    # poles
    for x in (x0, x0 + fw + gap, x0 + 2 * (fw + gap)):
        d.line([x, cy - fh / 2, x, cy + fh / 2 + s * 0.10], fill=col, width=max(2, int(s * 0.04)))


def pic_ballot(d, cx, cy, s, col):
    # ballot box with a paper going in and a tick
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


def pic_plane(d, cx, cy, s, col):
    # jet in a shallow dive, nose down-right, with a smoke trail
    w = max(2, int(s * 0.05))
    d.arc([cx - s * 0.48, cy - s * 0.30, cx - s * 0.10, cy + s * 0.10],
          start=200, end=330, fill=col, width=w)
    body = [(cx - s * 0.30, cy - s * 0.08), (cx + s * 0.28, cy + s * 0.18),
            (cx + s * 0.46, cy + s * 0.28), (cx + s * 0.20, cy + s * 0.30),
            (cx - s * 0.34, cy + s * 0.08)]
    d.polygon(body, fill=col)
    d.polygon([(cx - s * 0.08, cy - s * 0.02), (cx - s * 0.22, cy - s * 0.30),
               (cx - s * 0.02, cy + s * 0.04)], fill=col)
    d.polygon([(cx + s * 0.10, cy + s * 0.22), (cx - s * 0.02, cy + s * 0.44),
               (cx + s * 0.18, cy + s * 0.26)], fill=col)


def pic_microbe(d, cx, cy, s, col):
    # virus: spiked disc with inner dots
    w = max(2, int(s * 0.05))
    for k in range(10):
        ang = math.pi * k / 5
        x1 = cx + s * 0.26 * math.cos(ang)
        y1 = cy + s * 0.26 * math.sin(ang)
        x2 = cx + s * 0.44 * math.cos(ang)
        y2 = cy + s * 0.44 * math.sin(ang)
        d.line([x1, y1, x2, y2], fill=col, width=w)
        d.ellipse([x2 - s * 0.06, y2 - s * 0.06, x2 + s * 0.06, y2 + s * 0.06],
                  fill=col)
    d.ellipse([cx - s * 0.26, cy - s * 0.26, cx + s * 0.26, cy + s * 0.26],
              fill=col)
    for dx, dy, r in ((-0.10, -0.08, 0.06), (0.10, 0.06, 0.08), (-0.02, 0.12, 0.05)):
        d.ellipse([cx + dx * s - r * s, cy + dy * s - r * s,
                   cx + dx * s + r * s, cy + dy * s + r * s], fill=(255, 255, 255))


def pic_cyclone(d, cx, cy, s, col):
    # spiral: three arcs winding inward
    for i, (r, a0, a1) in enumerate(((0.44, 20, 300), (0.32, 140, 420), (0.20, 260, 540))):
        d.arc([cx - s * r, cy - s * r, cx + s * r, cy + s * r], start=a0, end=a1,
              fill=col, width=max(3, int(s * 0.09)))
    d.ellipse([cx - s * 0.06, cy - s * 0.06, cx + s * 0.06, cy + s * 0.06], fill=col)


def pic_missile(d, cx, cy, s, col):
    # missile climbing diagonally: fat body, pointed nose, tail fins, flame
    w = max(3, int(s * 0.07))
    # flame first (behind the tail)
    flame = [(cx - s * 0.30, cy + s * 0.30), (cx - s * 0.52, cy + s * 0.40),
             (cx - s * 0.40, cy + s * 0.56), (cx - s * 0.22, cy + s * 0.44)]
    d.polygon(flame, fill=(232, 120, 40))
    d.polygon([(cx - s * 0.30, cy + s * 0.30), (cx - s * 0.44, cy + s * 0.36),
               (cx - s * 0.36, cy + s * 0.48), (cx - s * 0.24, cy + s * 0.40)],
              fill=(255, 200, 60))
    # tail fins
    d.polygon([(cx - s * 0.28, cy + s * 0.22), (cx - s * 0.46, cy + s * 0.34),
               (cx - s * 0.34, cy + s * 0.14)], fill=col)
    d.polygon([(cx - s * 0.20, cy + s * 0.34), (cx - s * 0.30, cy + s * 0.50),
               (cx - s * 0.12, cy + s * 0.40)], fill=col)
    # body: thick diagonal bar with a pointed nose
    body = [(cx - s * 0.32, cy + s * 0.18), (cx + s * 0.16, cy - s * 0.28),
            (cx + s * 0.34, cy - s * 0.40), (cx + s * 0.42, cy - s * 0.30),
            (cx + s * 0.28, cy - s * 0.10), (cx - s * 0.18, cy + s * 0.32)]
    d.polygon(body, fill=col)
    # window band on the body
    d.line([cx - s * 0.08, cy + s * 0.02, cx + s * 0.10, cy - s * 0.14],
           fill=(120, 150, 190), width=w)


def pic_drone(d, cx, cy, s, col):
    d.ellipse([cx - s * 0.24, cy - s * 0.12, cx + s * 0.24, cy + s * 0.12], fill=col)
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        x, y = cx + dx * s * 0.38, cy + dy * s * 0.26
        d.line([cx, cy, x, y], fill=col, width=max(2, int(s * 0.05)))
        d.line([x - s * 0.14, y, x + s * 0.14, y], fill=col, width=max(3, int(s * 0.08)))


def burst(d, cx, cy, r, col):
    pts = []
    for i in range(16):
        ang = math.pi * i / 8
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=col)


# ---------------- page ----------------

img = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(img)

# Masthead
d.rectangle([M, M, W - M, M + 104], fill=NAVY)
d.rectangle([M, M, W - M, M + 6], fill=CRIMSON)
mast = f(SERIF, 54)
title = "THE WORLD IN ONE DAY"
tw = d.textlength(title, font=mast)
d.text(((W - tw) / 2, M + 16), title, font=mast, fill=(255, 255, 255))
d.rectangle([M + 90, M + 76, W - M - 90, M + 78], fill=GOLD)
dateline = f(SANS_B, 21)
date = "W E D N E S D A Y  ·  1 8  N O V E M B E R  2 0 2 6"
dw = d.textlength(date, font=dateline)
d.text(((W - dw) / 2, M + 82), date, font=dateline, fill=GOLD)

# Lead story: illustration left, text right
lx, ly, lw, lh = M, M + 116, W - 2 * M, 280
d.rectangle([lx, ly, lx + lw, ly + lh], fill=CARD, outline=RULE, width=2)
pw = 300  # illustration panel width
d.rectangle([lx, ly, lx + pw, ly + lh], fill=NAVY)
# dotted missile arc across the panel
for i in range(9):
    t = i / 8
    x = lx + 30 + t * 220
    y = ly + 150 - 46 * (4 * t * (1 - t))
    d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(120, 150, 190))
pic_missile(d, lx + 110, ly + 92, 96, (255, 255, 255))
pic_drone(d, lx + 225, ly + 70, 52, (200, 215, 235))
pic_drone(d, lx + 62, ly + 168, 44, (200, 215, 235))
burst(d, lx + 238, ly + 190, 30, (232, 120, 40))
cap = f(SANS_B, 15)
d.text((lx + 18, ly + lh - 36), "U.S. STRIKE ON QESHM ISLAND", font=cap, fill=PALE)
d.text((lx + 18, ly + lh - 18), "DRONES AT BAHRAIN & KUWAIT", font=cap, fill=PALE)
# lead text
tx = lx + pw + 24
tw_ = lw - pw - 48
d.text((tx, ly + 18), "THE GULF  —  LEAD STORY", font=f(SANS_B, 17), fill=CRIMSON)
head = f(SERIF, 40)
hlines = wrap(d, "U.S. strikes Iranian missile site on Qeshm Island", head, tw_)
y = para(d, hlines, tx, ly + 48, head, INK, 44)
summ = f(SANS, 21)
slines = wrap(d, "Washington confirms the strike after Iran fired drones at U.S. radar sites in Bahrain and Kuwait; the region braces for more.", summ, tw_)
para(d, slines, tx, y + 10, summ, BODY, 26)

# Section label
sy = ly + lh + 16
lab = "THE DAY IN BRIEF"
lab_f = f(SANS_B, 19)
d.text((M, sy - 4), lab, font=lab_f, fill=NAVY)
lab_w = d.textlength(lab, font=lab_f)
d.rectangle([M + lab_w + 14, sy + 8, W - M, sy + 10], fill=GOLD)

# Six cards, 3 columns x 2 rows
cards = [
    ("KERCH BRIDGE HIT AGAIN",
     "Ukraine hits the Crimea bridge for a second day; part of its road span falls into the strait.",
     (166, 25, 46), pic_bridge),
    ("SUMMITS IN SHENZHEN",
     "APEC opens in Shenzhen; Xi and Putin meet before the first Trump-Xi-Putin summit, as QUAD unveils a plan in Manila.",
     (30, 90, 160), pic_flags),
    ("DEMOCRATS TAKE ALASKA",
     "Peltola unseats Sullivan in the Senate race, giving Democrats a 56-seat majority.",
     (110, 70, 150), pic_ballot),
    ("PLANE CRASH IN SIBERIA",
     "A Russian military plane crashes in the Kemerovo region; 19 people are killed.",
     (90, 88, 82), pic_plane),
    ("EBOLA DOUBLES IN CONGO",
     "The DR Congo outbreak passes 11,000 cases and 5,400 deaths, the UN says.",
     (14, 120, 120), pic_microbe),
    ("CYCLONE XAVIER, CAT 5",
     "Category 5 Cyclone Xavier slams the Northern Cook Islands; quakes shake Papua New Guinea and Romania.",
     (200, 110, 20), pic_cyclone),
]
gx, gy = M, sy + 36
cw = (W - 2 * M - 2 * 12) // 3
ch = 210
for i, (headline, summary, accent, icon) in enumerate(cards):
    cx = gx + (i % 3) * (cw + 12)
    cy = gy + (i // 3) * (ch + 12)
    d.rectangle([cx, cy, cx + cw, cy + ch], fill=CARD, outline=RULE, width=2)
    d.rectangle([cx, cy, cx + cw, cy + 6], fill=accent)
    icx, icy, r = cx + 40, cy + 56, 27
    d.ellipse([icx - r, icy - r, icx + r, icy + r], fill=accent)
    icon(d, icx, icy, 42, (255, 255, 255))
    tx2 = cx + 78
    hf = f(SANS_B, 22)
    hlines = wrap(d, headline, hf, cw - 78 - 14)
    y2 = para(d, hlines, tx2, cy + 20, hf, INK, 26)
    sf = f(SANS, 17)
    slines = wrap(d, summary, sf, cw - 28)
    para(d, slines, cx + 14, cy + 102, sf, BODY, 22)

# Also strip
by = gy + 2 * ch + 12 + 12
d.rectangle([M, by, W - M, by + 64], fill=NAVY)
bf = f(SANS_B, 19)
line1 = "ALSO:  Microsoft unveils seven in-house AI models  ·  Dhoni retires from the IPL"
w1 = d.textlength(line1, font=bf)
d.text(((W - w1) / 2, by + 8), line1, font=bf, fill=(255, 255, 255))
bf2 = f(SANS, 18)
line2 = "World Court to rule on Myanmar genocide case  ·  Oil slips as Hormuz risks limit losses"
w2 = d.textlength(line2, font=bf2)
d.text(((W - w2) / 2, by + 34), line2, font=bf2, fill=PALE)

# Footer
ff = f(SANS, 14)
foot = "Sources: Associated Press · Reuters · BBC · Al Jazeera  —  events of 18 November 2026"
fw = d.textlength(foot, font=ff)
d.text(((W - fw) / 2, by + 72), foot, font=ff, fill=GREY)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
img.save(out, "PNG", optimize=True)
print("saved", out, os.path.getsize(out), "bytes")
