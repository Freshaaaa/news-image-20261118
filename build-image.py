#!/usr/bin/env python3
"""Draw the news-image-20261118 v2 entry: one page summing up the world news
of Wednesday 18 November 2026, rendered with PIL so every letter stays
crisp at 1024x1024. No network, no randomness, no clock: the same run
always writes the same bytes.

Structure (following the proven top entries): header with the date named
and counted, region bar, the day in numbers, 13 large cards (3 big + 10
small) with drawn illustrations, a world map with numbered pins, 27 more
stories in three columns, a date-check box (what was left out on purpose),
and a sources footer.

All 40 stories happened, or were first reported, on Wednesday 18 November
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


# ---------------- data ----------------

# (number, region, topic, verify, accent, icon, headline, body)
# bodies kept short so they fit their card: big cards <= 3 lines at 13px,
# small cards <= 3 lines at 12px.
CARDS = [
    (1, "ASIA", "APEC SUMMIT", "CONFIRMED · AP", NAVY, pic_flags,
     "Xi welcomes Trump in Shenzhen",
     "APEC opens as Trump lands for the first three-way talks with Xi and Putin, set for Thursday."),
    (2, "MIDDLE EAST", "IRAN WAR", "CLAIM · AP", CRIMSON, pic_drone,
     "Gulf states shoot down Iran's drones",
     "Bahrain and Kuwait intercept drones aimed at US sites, a day after the Qeshm strike."),
    (3, "WORLD", "SPACE", "CONFIRMED · NASA", NAVY_SOFT, pic_rocket,
     "Voyager 1, one light-day from home",
     "The probe reaches 25.9 billion km — the first object to travel a full light-day."),
    (4, "EUROPE", "UKRAINE WAR", "KYIV · AFP", CRIMSON, pic_drone,
     "141 drones in one night over Ukraine",
     "Russia fires 141 drones; 126 downed. Four die in Donetsk."),
    (5, "AMERICAS", "MARKETS", "FED", TEAL, pic_chart_down,
     "Fed signals more rate rises",
     "Minutes point to more hikes. The Dow falls 561, down 1.1%."),
    (6, "ASIA", "WEATHER", "IMD", ORANGE, pic_cyclone,
     "Cyclone Akvan turns toward Odisha",
     "Landfall due Friday 20 Nov. About 50,000 moved to safety."),
    (7, "AFRICA", "SUDAN WAR", "AMNESTY", CRIMSON, burst,
     "37 killed by RSF drones in El Obeid",
     "Amnesty: the strikes killed 37; it urges a war-crimes inquiry."),
    (8, "EUROPE", "UKRAINE AID", "EU", NAVY_SOFT, pic_eu,
     "EU plans a €45bn loan for Kyiv",
     "A loan to fund Kyiv through 2027, repaid if Russia pays up."),
    (9, "EUROPE", "ECONOMY", "ONS", TEAL, pic_chart_up,
     "UK inflation hits a one-year high",
     "Prices rise 3.6% as fuel and tobacco duty go up."),
    (10, "MIDDLE EAST", "GAZA", "REUTERS", CRIMSON, pic_tank,
     "Israeli tanks push into central Gaza",
     "Tanks advance near Nuseirat; the army cites a tunnel network."),
    (11, "AMERICAS", "US POLITICS", "NPR", NAVY, pic_ballot,
     "Jeffries picked for House Speaker",
     "Democrats pick Jeffries 251–11; first Black Speaker in sight."),
    (12, "WORLD", "CULTURE", "ROCKSTAR", GOLD, pic_controller,
     "GTA VI goes on sale at last",
     "After a 13-year wait, it launches; 14.9m pre-orders."),
    (13, "ASIA", "LABOUR", "DHAKA", ORANGE, pic_factory,
     "Bangladesh wage protests shut 55 factories",
     "Police tear-gas workers; 55 factories shut in the protests."),
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
]

NUMBERS = [
    ("141", "drones fired"),
    ("126", "drones downed"),
    ("25.9bn km", "Voyager 1 from Earth"),
    ("55", "factories shut"),
    ("251–11", "Jeffries vote"),
    ("11,300+", "Ebola cases"),
]

REGIONS = [("EUROPE", 8), ("AMERICAS", 9), ("ASIA", 6), ("AFRICA", 6),
           ("MIDDLE EAST", 4), ("OCEANIA", 3), ("WORLD", 4)]

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

# dotted world map: per row, (start_col, end_col) spans on a 122x12 grid
MAP_ROWS = [
    [(8, 20), (42, 50), (60, 110)],
    [(4, 30), (44, 52), (55, 115)],
    [(3, 32), (58, 70), (72, 118)],
    [(5, 30), (58, 68), (72, 110)],
    [(8, 28), (58, 66), (66, 78), (78, 108)],
    [(12, 26), (24, 28), (56, 74), (76, 100)],
    [(36, 46), (56, 72), (80, 100)],
    [(36, 45), (57, 70), (82, 96)],
    [(37, 44), (58, 68), (84, 94)],
    [(38, 43), (59, 66), (98, 110)],
    [(39, 42), (99, 109)],
    [(40, 41)],
]


# ---------------- page ----------------

img = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(img)

# ============ header (y 16-108) ============
HY = 16
d.rectangle([M, HY, W - M, HY + 92], fill=NAVY)
d.rectangle([M, HY, W - M, HY + 5], fill=CRIMSON)
# date block, left (width sized to fit "NOV 18" at 27px, text centred)
blk_x0, blk_x1 = M + 12, M + 150
d.rectangle([blk_x0, HY + 12, blk_x1, HY + 80], fill=(255, 255, 255))
db1 = f(SANS_B, 27)
t1 = "NOV 18"
d.text((blk_x0 + (blk_x1 - blk_x0 - d.textlength(t1, font=db1)) / 2, HY + 16),
       t1, font=db1, fill=NAVY)
db2 = f(SANS_B, 16)
t2 = "WED · 2026"
d.text((blk_x0 + (blk_x1 - blk_x0 - d.textlength(t2, font=db2)) / 2, HY + 50),
       t2, font=db2, fill=CRIMSON)
# title, right of the block
tx = blk_x1 + 16
d.text((tx, HY + 10), "THE DAY IN WORLD NEWS", font=f(SANS_B, 15), fill=GOLD)
big = f(SERIF, 40)
d.text((tx, HY + 28), "Wednesday 18 November 2026", font=big, fill=(255, 255, 255))
d.text((tx, HY + 72), "Everything on this page happened, or was first reported, on that day.",
       font=f(SANS, 13), fill=PALE)
cnt = f(SANS_B, 13)
ct = "40 STORIES  ·  7 REGIONS  ·  ONE PAGE"
d.text((W - M - d.textlength(ct, font=cnt) - 10, HY + 72), ct, font=cnt, fill=GOLD)

# ============ region bar (y 114-136) ============
RY = 114
d.rectangle([M, RY, W - M, RY + 22], fill=PALE_BG, outline=RULE)
x = M + 10
rf = f(SANS_B, 13)
for name, n in REGIONS:
    label = f"{name} {n}"
    w = d.textlength(label, font=rf)
    d.text((x, RY + 4), label, font=rf, fill=NAVY)
    x += w + 26
    if name != REGIONS[-1][0]:
        d.rectangle([x - 13, RY + 5, x - 12, RY + 17], fill=RULE)

# ============ the day in numbers (y 142-196) ============
NY = 142
d.text((M, NY), "THE DAY IN NUMBERS", font=f(SANS_B, 15), fill=NAVY)
d.rectangle([M + 178, NY + 8, W - M, NY + 10], fill=GOLD)
nw = CW // 6
nf = f(SANS_B, 26)
lf = f(SANS, 12)
for i, (num, lab) in enumerate(NUMBERS):
    cx = M + i * nw + nw // 2
    tw = d.textlength(num, font=nf)
    d.text((cx - tw / 2, NY + 22), num, font=nf, fill=CRIMSON)
    lw = d.textlength(lab, font=lf)
    d.text((cx - lw / 2, NY + 50), lab, font=lf, fill=BODY)

# ============ 13 cards (y 204-668) ============
CY = 204
GAP = 8
# top row: 3 big cards
big_w = (CW - 2 * GAP) // 3
big_h = 148
for i in range(3):
    num, region, topic, verify, accent, icon, head, body = CARDS[i]
    cx = M + i * (big_w + GAP)
    cy = CY
    d.rectangle([cx, cy, cx + big_w, cy + big_h], fill=CARD, outline=RULE, width=2)
    d.rectangle([cx, cy, cx + big_w, cy + 5], fill=accent)
    tag = f"{num} · {region} · {topic}"
    d.text((cx + 12, cy + 12), tag, font=f(SANS_B, 13), fill=accent)
    vw = d.textlength(verify, font=f(SANS, 11))
    d.text((cx + big_w - vw - 10, cy + 14), verify, font=f(SANS, 11), fill=GREY)
    icx, icy = cx + 44, cy + 92
    d.ellipse([icx - 34, icy - 34, icx + 34, icy + 34], fill=PALE_BG)
    icon(d, icx, icy, 52, accent)
    tx2 = cx + 88
    tw2 = big_w - 88 - 12
    hf = f(SANS_B, 19)
    hlines = wrap(d, head, hf, tw2)
    y2 = para(d, hlines, tx2, cy + 40, hf, INK, 22)
    sf = f(SANS, 13)
    slines = wrap(d, body, sf, tw2)[:3]
    para(d, slines, tx2, y2 + 4, sf, BODY, 16)

# rows 2-3: 10 small cards, 5 per row
small_w = (CW - 4 * GAP) // 5
small_h = 150
for j in range(10):
    num, region, topic, verify, accent, icon, head, body = CARDS[3 + j]
    col, row = j % 5, j // 5
    cx = M + col * (small_w + GAP)
    cy = CY + big_h + GAP + row * (small_h + GAP)
    d.rectangle([cx, cy, cx + small_w, cy + small_h], fill=CARD, outline=RULE, width=2)
    d.rectangle([cx, cy, cx + small_w, cy + 5], fill=accent)
    # tag spans the full card width, one line
    tag = f"{num} · {region} · {topic}"
    d.text((cx + 10, cy + 12), trunc(d, tag, f(SANS_B, 10), small_w - 20),
           font=f(SANS_B, 10), fill=accent)
    # icon circle left, verify text to its right
    icx, icy = cx + 24, cy + 44
    d.ellipse([icx - 15, icy - 15, icx + 15, icy + 15], fill=PALE_BG)
    icon(d, icx, icy, 23, accent)
    d.text((cx + 44, cy + 38), verify, font=f(SANS, 10), fill=GREY)
    # headline
    hf = f(SANS_B, 14)
    hlines = wrap(d, head, hf, small_w - 20)[:2]
    y2 = para(d, hlines, cx + 10, cy + 66, hf, INK, 17)
    # body
    sf = f(SANS, 12)
    slines = wrap(d, body, sf, small_w - 20)[:3]
    para(d, slines, cx + 10, y2 + 4, sf, BODY, 15)

# ============ world map (y 676-768) ============
MY = 676
d.text((M, MY), "WHERE IT HAPPENED", font=f(SANS_B, 15), fill=NAVY)
d.rectangle([M + 176, MY + 8, W - M, MY + 10], fill=GOLD)
map_top = MY + 22
map_h = 64
map_bot = map_top + map_h
d.rectangle([M, map_top, W - M, map_bot], fill=(255, 255, 255), outline=RULE, width=1)
cols, rows = 122, 12
dx = CW / cols
dy = map_h / rows
for r, spans in enumerate(MAP_ROWS):
    for c0, c1 in spans:
        for c in range(c0, c1 + 1):
            x = M + (c + 0.5) * dx
            y = map_top + (r + 0.5) * dy
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(150, 160, 175))


def lonlat_to_xy(lat, lon):
    x = M + (lon + 180.0) / 360.0 * CW
    y = map_top + (85.0 - lat) / 140.0 * map_h
    return x, y


for num, lat, lon in PINS:
    x, y = lonlat_to_xy(lat, lon)
    d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=CRIMSON, outline=(255, 255, 255), width=1)
    nf2 = f(SANS_B, 10)
    tw = d.textlength(str(num), font=nf2)
    d.text((x - tw / 2, y - 6), str(num), font=nf2, fill=(255, 255, 255))
d.text((M + 6, map_bot - 15), "3 · Voyager 1 is flown from Pasadena, California",
       font=f(SANS, 10), fill=GREY)

# ============ 27 more stories (y 770-922) ============
AY = 770
d.text((M, AY), "ALSO ON WEDNESDAY 18 NOVEMBER — 27 MORE STORIES",
       font=f(SANS_B, 15), fill=NAVY)
d.rectangle([M + 448, AY + 8, W - M, AY + 10], fill=GOLD)
col_w = (CW - 2 * 16) // 3
mf = f(SANS, 12)
bf = f(SANS_B, 12)
for k, (num, city, headline) in enumerate(MORE):
    col, row = k % 3, k // 3
    x = M + col * (col_w + 16)
    y = AY + 26 + row * 14
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

# ============ date check (y 928-998, height from wrapped lines) ============
DY = 928
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
        "All 40 stories first reported Wed 18 Nov 2026.")
fw = d.textlength(foot, font=sf2)
d.text(((W - fw) / 2, FY), foot, font=sf2, fill=GREY)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
img.save(out, "PNG", optimize=True)
print("saved", out, os.path.getsize(out), "bytes")
