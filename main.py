#!/usr/bin/env python3
"""news-image-20261119 - dense newspaper front page for 19 November 2026.

Draws a 1024x1024 PNG front page ("THE WORLD IN ONE IMAGE") in pure
Python 3 standard library: a small rasterizer, a 5x7 bitmap font written
out below, and a minimal PNG encoder (zlib + struct). No network, no
timestamps, no randomness: two runs write byte-identical output.

Layout: masthead with the date, one lead story (Trump-Xi-Putin summit),
two second stories (ICJ Myanmar ruling, Houthi strike on Riyadh),
a third row (Kerch Bridge, Gaza, Anthropic IPO), a UTC timeline,
a 20-story brief grid, and a footer with a date check. 29 stories in all,
every one first reported on Thursday 19 November 2026 (see NEWS.md).

Usage: python3 main.py   (writes entry.png to $MAKEFUN_OUTPUT_DIR or /output)
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font -----
# 5x7 bitmap font. Each glyph is 7 rows of 5 cells; '1' is on, '0' is off.
# Lowercase g, p, q and y carry a descender inside the 7 rows.
FONT = {
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01000", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01110", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "00010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "11110", "10001", "10001", "11110", "10000", "10000"),
    "q": ("00000", "01111", "10001", "10001", "01111", "00001", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("00100", "00100", "11111", "00100", "00100", "00100", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "10001", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01100"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01100"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "\u2013": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "\u2014": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "\u2022": ("00000", "00000", "01100", "01100", "00000", "00000", "00000"),
    "\u00b7": ("00000", "00000", "00000", "01100", "00000", "00000", "00000"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "~": ("00000", "00000", "01001", "10110", "00000", "00000", "00000"),
    "^": ("00100", "01010", "10001", "00000", "00000", "00000", "00000"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    "`": ("01000", "00100", "00000", "00000", "00000", "00000", "00000"),
    "{": ("00010", "00100", "00100", "01100", "00100", "00100", "00010"),
    "}": ("01000", "00100", "00100", "00110", "00100", "00100", "01000"),
}

# ------------------------------------------------------------- canvas ------
PAPER = (246, 241, 227)
INK = (26, 26, 26)
NAVY = (22, 35, 63)
NAVY2 = (38, 54, 92)
RED = (176, 30, 36)
GOLD = (201, 162, 39)
TEAL = (15, 95, 92)
GREY = (96, 96, 90)
LGREY = (214, 208, 192)
SKY = (58, 84, 128)
ORANGE = (214, 120, 44)
SEA = (24, 52, 84)
WHITE = (250, 248, 242)


class Canvas:
    """A flat RGB raster with rect/line/circle/text primitives."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        for i in range(w * h):
            self.px[3 * i] = bg[0]
            self.px[3 * i + 1] = bg[1]
            self.px[3 * i + 2] = bg[2]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = 3 * (y * self.w + x)
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + w, self.w), min(y + h, self.h)
        for yy in range(y0, y1):
            base = 3 * (yy * self.w + x0)
            for xx in range(x0, x1):
                i = base + 3 * (xx - x0)
                self.px[i] = c[0]
                self.px[i + 1] = c[1]
                self.px[i + 2] = c[2]

    def rect(self, x, y, w, h, c, t=1):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def hline(self, x, y, w, c, t=1):
        self.fill_rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill_rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            if t == 1:
                self.set(x0, y0, c)
            else:
                self.fill_rect(x0 - t // 2, y0 - t // 2, t, t, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c):
        for yy in range(-r, r + 1):
            dx = int((r * r - yy * yy) ** 0.5)
            self.fill_rect(cx - dx, cy + yy, 2 * dx + 1, 1, c)

    def poly(self, pts, c):
        # scanline fill of a simple polygon
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[k]), y,
                               max(1, int(xs[k + 1]) - int(xs[k])), 1, c)

    def text(self, x, y, s, scale, c):
        cx = x
        for ch in s:
            g = FONT[ch]  # KeyError on an unmapped char: fail loudly
            for r, row in enumerate(g):
                for col, bit in enumerate(row):
                    if bit == "1":
                        self.fill_rect(cx + col * scale, y + r * scale,
                                       scale, scale, c)
            cx += 6 * scale
        return cx

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def text_c(self, x, y, w, s, scale, c):
        tw = self.text_w(s, scale)
        self.text(x + (w - tw) // 2, y, s, scale, c)

    def wrap(self, s, max_chars):
        words, lines, cur = s.split(" "), [], ""
        for wd in words:
            if cur and len(cur) + 1 + len(wd) > max_chars:
                lines.append(cur)
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
        if cur:
            lines.append(cur)
        return lines

    def para(self, x, y, w, s, scale, c, lh=None):
        max_chars = max(1, w // (6 * scale))
        lh = lh or (8 * scale + 2)
        yy = y
        for ln in self.wrap(s, max_chars):
            self.text(x, yy, ln, scale, c)
            yy += lh
        return yy


# ---------------------------------------------------------------- png -------
def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    comp = zlib.compress(bytes(raw), 6)

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)

# ---------------------------------------------------------- illustrations ---
def draw_summit(cv, x, y, w, h):
    """Shenzhen at dusk: skyline, red sun, three flags above the towers."""
    cv.fill_rect(x, y, w, h, (30, 32, 58))
    cv.circle(x + int(w * 0.74), y + int(h * 0.20), 15, RED)
    cv.circle(x + int(w * 0.74), y + int(h * 0.20), 9, (220, 90, 80))
    for sx, sy in ((0.07, 0.09), (0.20, 0.05), (0.40, 0.12), (0.58, 0.07),
                   (0.90, 0.09), (0.33, 0.20), (0.52, 0.16)):
        cv.fill_rect(x + int(w * sx), y + int(h * sy), 3, 3, WHITE)
    base = y + h
    towers = ((0.02, 0.52, 0.13), (0.17, 0.38, 0.12), (0.31, 0.58, 0.11),
              (0.44, 0.30, 0.12), (0.58, 0.46, 0.12), (0.72, 0.36, 0.12),
              (0.86, 0.54, 0.12))
    for fx, fh, fw in towers:
        tx, tw, th = x + int(w * fx), int(w * fw), int(h * fh)
        cv.fill_rect(tx, base - th, tw, th, (12, 14, 26))
        for wy in range(base - th + 6, base - 4, 12):
            for wx in range(tx + 3, tx + tw - 3, 9):
                if (wx + wy) % 3 == 0:
                    cv.fill_rect(wx, wy, 3, 4, GOLD)
    # tallest tower spire
    cv.line(x + int(w * 0.50), base - int(h * 0.30),
            x + int(w * 0.50), base - int(h * 0.48), GOLD, 2)
    cv.fill_rect(x, base - 4, w, 4, GOLD)
    # three flags on poles above the skyline
    pole_y = y + int(h * 0.10)
    for i, (fx, cols) in enumerate((
            (0.16, ((200, 40, 40), (250, 248, 242), (30, 60, 140))),
            (0.50, ((222, 30, 30), (222, 30, 30), (222, 30, 30))),
            (0.84, ((250, 248, 242), (30, 60, 160), (200, 40, 40))))):
        px = x + int(w * fx)
        cv.line(px, pole_y, px, pole_y + 34, (200, 200, 190), 2)
        for j, col in enumerate(cols):
            cv.fill_rect(px + 2, pole_y + j * 7, 26, 7, col)
        if i == 1:  # a gold star on the red flag
            cv.fill_rect(px + 6, pole_y + 2, 4, 4, GOLD)


def draw_scales(cv, x, y, w, h):
    """The Hague: gold scales of justice over a navy court facade."""
    cv.fill_rect(x, y, w, h, NAVY2)
    # pediment
    cv.poly([(x + 6, y + h - 26), (x + w // 2, y + h - 52),
             (x + w - 6, y + h - 26)], (52, 72, 118))
    cv.fill_rect(x + 6, y + h - 26, w - 12, 26, (38, 54, 92))
    for i in range(5):
        colx = x + 14 + i * 22
        cv.fill_rect(colx, y + h - 24, 8, 24, (52, 72, 118))
    # scales: pillar, beam, two pans
    cxp = x + w // 2
    top = y + 22
    cv.fill_rect(cxp - 3, top, 6, 62, GOLD)
    cv.circle(cxp, top - 4, 5, GOLD)
    cv.fill_rect(x + 14, top + 8, w - 28, 4, GOLD)
    for side in (-1, 1):
        px = cxp + side * (w // 2 - 18)
        cv.line(px, top + 10, cxp, top + 10, GOLD, 2)
        cv.line(px, top + 10, px - 12, top + 34, GOLD, 2)
        cv.line(px, top + 10, px + 12, top + 34, GOLD, 2)
        cv.poly([(px - 14, top + 34), (px + 14, top + 34),
                 (px, top + 46)], GOLD)
    cv.fill_rect(cxp - 16, top + 62, 32, 5, GOLD)
    cv.fill_rect(cxp - 24, top + 67, 48, 5, GOLD)


def draw_tower(cv, x, y, w, h):
    """Riyadh at night: the tapered PIF Tower, damage near the top."""
    cv.fill_rect(x, y, w, h, (16, 20, 40))
    for sx, sy in ((0.08, 0.10), (0.24, 0.06), (0.42, 0.12), (0.60, 0.08),
                   (0.88, 0.12), (0.70, 0.20)):
        cv.fill_rect(x + int(w * sx), y + int(h * sy), 3, 3, WHITE)
    # ground and low blocks
    base = y + h
    cv.fill_rect(x, base - 10, w, 10, (10, 12, 24))
    cv.fill_rect(x + 4, base - 30, 26, 20, (12, 14, 26))
    cv.fill_rect(x + w - 32, base - 24, 28, 14, (12, 14, 26))
    # tapered tower
    top_w = int(w * 0.30)
    bot_w = int(w * 0.46)
    tx0, tx1 = x + (w - top_w) // 2, x + (w + top_w) // 2
    bx0, bx1 = x + (w - bot_w) // 2, x + (w + bot_w) // 2
    cv.poly([(tx0, y + 8), (tx1, y + 8), (bx1, base - 10),
             (bx0, base - 10)], (52, 72, 118))
    # window grid inside the taper
    for row in range(6, h - 16, 12):
        frac = row / float(h)
        lw = top_w + (bot_w - top_w) * frac
        lx0 = x + (w - lw) // 2
        for wx in range(int(lx0) + 4, int(lx0 + lw) - 4, 9):
            cv.fill_rect(wx, y + row, 4, 5, GOLD)
    # damage: dark scorch + smoke near the top third
    cv.circle(x + int(w * 0.62), y + int(h * 0.30), 10, (110, 110, 108))
    cv.circle(x + int(w * 0.62), y + int(h * 0.30), 6, (140, 140, 138))
    cv.circle(x + int(w * 0.56), y + int(h * 0.22), 7, (110, 110, 108))
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        cv.line(x + int(w * 0.62), y + int(h * 0.34),
                x + int(w * 0.62) + dx * 10, y + int(h * 0.34) + dy * 10,
                ORANGE, 2)


def draw_kerch(cv, x, y, w, h):
    """Kerch Strait: bridge deck with a collapsed span, smoke, water."""
    cv.fill_rect(x, y, w, h, (176, 188, 204))
    cv.fill_rect(x, y, w, int(h * 0.16), (120, 140, 168))
    sea_y = y + int(h * 0.64)
    cv.fill_rect(x, sea_y, w, h - int(h * 0.64), (40, 78, 118))
    for wy in range(sea_y + 6, y + h - 4, 10):
        cv.hline(x + 6, wy, w - 12, (96, 140, 180), 2)
    # deck, left and right of the gap
    deck_y = y + int(h * 0.40)
    cv.fill_rect(x, deck_y, int(w * 0.36), 8, (52, 52, 56))
    cv.fill_rect(x + int(w * 0.64), deck_y, int(w * 0.36), 8, (52, 52, 56))
    # piers
    cv.fill_rect(x + int(w * 0.10), deck_y + 8, 8, sea_y - deck_y - 8,
                 (52, 52, 56))
    cv.fill_rect(x + int(w * 0.90), deck_y + 8, 8, sea_y - deck_y - 8,
                 (52, 52, 56))
    # fallen span, tilted into the strait
    cv.poly([(x + int(w * 0.38), deck_y + 2),
             (x + int(w * 0.60), deck_y + 18),
             (x + int(w * 0.58), deck_y + 26),
             (x + int(w * 0.36), deck_y + 10)], (52, 52, 56))
    # smoke over the gap
    for sx, sy, sr in ((0.46, 0.24, 9), (0.54, 0.18, 11)):
        cv.circle(x + int(w * sx), y + int(h * sy), sr, (110, 110, 108))
        cv.circle(x + int(w * sx), y + int(h * sy), sr - 4, (140, 140, 138))
    # splash where the span fell
    for sx in (0.44, 0.50, 0.56):
        cv.line(x + int(w * sx), sea_y + 2, x + int(w * sx) + 4,
                sea_y - 8, WHITE, 2)

# ----------------------------------------------------------------- page ------
GRID = [
    ("UKRAINE", "RUSSIAN STRIKES KILL 5"),
    ("KOREA", "NORTH EXPANDS URANIUM SITE"),
    ("CLIMATE", "COP31 SPLIT ON FOSSIL FUELS"),
    ("DENMARK", "GREENLAND DEAL PASSES 109-0"),
    ("USA", "JEFFRIES WINS SPEAKER NOD"),
    ("USA", "TRUMP ASKS COURT ON TPS"),
    ("BANGLADESH", "YUNUS HOME SET ABLAZE"),
    ("SENEGAL", "MIGRANT BOAT SINKS"),
    ("TECH", "BITCOIN DIPS BELOW $63,000"),
    ("CANADA", "CARNEY WRAPS APEC"),
    ("SPORT", "ALCARAZ BEATS MEDVEDEV 6-2"),
    ("SPORT", "ENGLAND WIN ODI SERIES 2-1"),
    ("SPORT", "ZVEREV TOPS GROUP UNBEATEN"),
    ("SPORT", "S AFRICA BEAT BANGLADESH"),
    ("USA", "ARIZONA PROBES OPENAI"),
    ("KOREA", "HAN CONVICTION OVERTURNED"),
    ("USA", "KUSHNER FIRM BUYS ARXIS"),
    ("JAPAN", "TAKAICHI TALKS WITH PUTIN"),
    ("MARITIME", "GAS HUSKY TANKER SINKS"),
    ("USA", "NIKE SHOES FOR VALEDICTORIANS"),
]

TIMELINE = [
    ("04:00", "HOUTHI STRIKE", "HITS RIYADH"),
    ("~08:00", "3-WAY SUMMIT", "IN SHENZHEN"),
    ("~09:00", "BANGLADESH", "LOCKDOWN"),
    ("~12:00", "ICJ RULES", "MYANMAR GUILTY"),
    ("~14:30", "ANTHROPIC IPO", "$81BN RECORD"),
    ("~18:00", "KERCH BRIDGE", "HIT 3RD TIME"),
]


def build():
    cv = Canvas(W, H, PAPER)
    cv.fill_rect(0, 0, W, H, NAVY)
    cv.fill_rect(8, 8, W - 16, H - 16, PAPER)

    # ---- masthead ------------------------------------------------------
    cv.fill_rect(8, 8, W - 16, 96, NAVY)
    cv.text(24, 26, "VOL. I", 2, GOLD)
    cv.text(1024 - 24 - cv.text_w("LATE EDITION", 2), 26, "LATE EDITION", 2, GOLD)
    cv.text_c(8, 18, W - 16, "THE WORLD IN ONE IMAGE", 5, WHITE)
    cv.fill_rect(182, 62, 660, 2, GOLD)
    cv.text_c(8, 70, W - 16, "THURSDAY, 19 NOVEMBER 2026", 3, GOLD)

    # ---- kicker --------------------------------------------------------
    cv.text_c(8, 112, W - 16,
              "FRONT PAGE - EVERY STORY BELOW WAS FIRST REPORTED TODAY", 2, RED)

    # ---- lead story: the Shenzhen summit --------------------------------
    draw_summit(cv, 12, 132, 344, 168)
    cv.text(12, 304, "THREE LEADERS, ONE TABLE", 2, GREY)
    tx = 372
    cv.text(tx, 132, "SHENZHEN - APEC SUMMIT", 2, RED)
    cv.text(tx, 154, "TRUMP, XI &", 6, INK)
    cv.text(tx, 202, "PUTIN MEET", 6, INK)
    cv.para(tx, 252, 640,
            "Trump, Xi and Putin hold the first-ever three-way summit in "
            "Shenzhen, on the sidelines of APEC. After 90 minutes they "
            "announce a 'peace declaration' - but it names neither "
            "Ukraine nor Iran.",
            2, INK)
    cv.hline(8, 328, W - 16, NAVY, 3)

    # ---- row 2: ICJ ruling / Riyadh tower -------------------------------
    y2 = 336
    draw_scales(cv, 12, y2, 120, 148)
    cv.text(144, y2, "THE HAGUE - WORLD COURT", 2, RED)
    cv.text(144, y2 + 22, "MYANMAR GUILTY", 3, INK)
    cv.text(144, y2 + 46, "OF GENOCIDE", 3, INK)
    cv.para(144, y2 + 74, 356,
            "The UN court rules 9-6 that Myanmar committed genocide "
            "against the Rohingya in 2017 - a first for any state.",
            2, INK, lh=14)
    cv.vline(508, y2, 148, LGREY, 2)

    draw_tower(cv, 520, y2, 120, 148)
    cv.text(652, y2, "RIYADH - SAUDI ARABIA", 2, RED)
    cv.text(652, y2 + 22, "HOUTHI MISSILE", 3, INK)
    cv.text(652, y2 + 46, "HITS PIF TOWER", 3, INK)
    cv.para(652, y2 + 74, 356,
            "A Houthi missile damages the PIF Tower, Riyadh's tallest, "
            "in the financial district. No casualties reported.",
            2, INK, lh=14)
    cv.hline(8, 490, W - 16, NAVY, 3)

    # ---- row 3: Kerch Bridge / Gaza / Anthropic --------------------------
    y3 = 498
    draw_kerch(cv, 12, y3, 120, 130)
    cv.text(144, y3, "UKRAINE - CRIMEA", 2, RED)
    cv.text(144, y3 + 22, "KERCH BRIDGE", 3, INK)
    cv.text(144, y3 + 46, "HIT 3RD TIME", 3, INK)
    cv.para(144, y3 + 72, 356,
            "Ukraine hits the bridge a third time; rail halted. Russia "
            "strikes the power grid; 5 killed.",
            2, INK, lh=14)
    cv.vline(508, y3, 130, LGREY, 2)

    cv.text(520, y3, "GAZA", 2, RED)
    cv.text(520, y3 + 20, "ISRAEL PUSHES INTO CENTRAL GAZA", 2, INK)
    cv.para(520, y3 + 38, 492,
            "Tanks roll past the Yellow Line near Nuseirat; the ceasefire "
            "strains.",
            2, INK, lh=15)
    cv.hline(520, y3 + 74, 492, LGREY, 2)
    cv.text(520, y3 + 82, "TECH", 2, RED)
    cv.text(520, y3 + 100, "ANTHROPIC IPO: RECORD $81BN", 2, INK)
    cv.text(520, y3 + 116, "Largest IPO ever at $83 a share.", 2, INK)
    cv.hline(8, 634, W - 16, NAVY, 3)

    # ---- timeline ------------------------------------------------------
    yt = 640
    cv.text(12, yt, "THE DAY IN UTC", 2, RED)
    cv.text(1024 - 12 - cv.text_w("TIMES APPROXIMATE", 2), yt,
            "TIMES APPROXIMATE", 2, GREY)
    cv.hline(12, yt + 30, W - 24, NAVY, 2)
    slot = (W - 24) // len(TIMELINE)
    for i, (tm, l1, l2) in enumerate(TIMELINE):
        cxp = 12 + slot * i + slot // 2
        cv.circle(cxp, yt + 31, 5, RED)
        cv.text_c(12 + slot * i, yt + 42, slot, tm, 2, INK)
        cv.text_c(12 + slot * i, yt + 58, slot, l1, 2, INK)
        cv.text_c(12 + slot * i, yt + 74, slot, l2, 2, INK)
    cv.hline(8, 734, W - 16, NAVY, 3)

    # ---- story grid ----------------------------------------------------
    yg = 742
    cv.text(12, yg, "MORE OF THE DAY - IN BRIEF", 2, RED)
    cv.text(1024 - 12 - cv.text_w("20 STORIES", 2), yg, "20 STORIES", 2, GREY)
    cols, rows = 5, 4
    gw = (W - 24 - (cols - 1) * 12) // cols
    gh = 44
    gy0 = yg + 22
    for idx, (tag, head) in enumerate(GRID):
        r, c = divmod(idx, cols)
        gx = 12 + c * (gw + 12)
        gy = gy0 + r * gh
        cv.text(gx, gy, tag, 1, RED)
        lines = cv.wrap(head, max(1, gw // 12))
        yy = gy + 10
        for ln in lines[:2]:
            cv.text(gx, yy, ln, 2, INK)
            yy += 15
    cv.hline(8, 946, W - 16, NAVY, 3)

    # ---- footer: date check + also reported ----------------------------
    yf = 954
    cv.rect(12, yf, 348, 54, RED, 3)
    cv.text(24, yf + 4, "DATE CHECK", 2, RED)
    cv.text(24, yf + 20, "TODAY IS THURSDAY", 2, INK)
    cv.text(24, yf + 35, "19 NOVEMBER 2026.", 2, INK)
    cv.text(372, yf, "ALSO REPORTED TODAY:", 2, RED)
    cv.para(372, yf + 18, 640,
            "Abu Dhabi talks end with no deal - Hegseth stops in Caracas "
            "- cruise outbreak sickens about 150.",
            2, INK, lh=16)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = build()
    write_png(cv, os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
