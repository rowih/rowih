"""The reference glyphs of the originality check: the writing systems encoded in Unicode,
drawn by GNU Unifont, and Latin, Greek, Cyrillic and Japanese drawn as strokes in the
styles of the Hershey fonts, with the image-similarity measure that compares them with the
language's glyphs.

The sources are downloaded once into a cache outside the repository and checked against
the SHA-256 recorded here, so that every run compares against the same glyphs. Nothing
downloaded is redistributed: the reports record only measurements and code points.

The measure crops a glyph to its ink, stretches each axis to fill a 16 by 16 grid (an
axis less than a quarter of the other is kept as a line), and compares two glyphs by
the F-measure of their ink within one cell of each other's: the share of each glyph's
ink that lies within one cell of the other's, combined harmonically. It is 1 for the
same shape at any proportion and falls as strokes move apart.
"""
from __future__ import annotations

import gzip
import hashlib
import os
import urllib.request

CACHE = os.path.join(os.path.expanduser("~"), ".cache", "rowih")
TIMEOUT = 120
GRID = 16

UNIFONT = "https://unifoundry.com/pub/unifont/unifont-18.0.01/font-builds/"
UCD = "https://www.unicode.org/Public/18.0.0/ucd/"
HERSHEY = ("https://raw.githubusercontent.com/kamalmostafa/hershey-fonts/"
           "1356bf2f83d380fcef68c887e88675eb9d445d86/hershey-fonts/")

SOURCES = {
    "unifont_all-18.0.01.hex.gz": (
        UNIFONT, "14c96e497466a82e46cf20032ce510e186bdc8658c9158e2290f452cda9bc498"),
    "unifont_csur-18.0.01.hex.gz": (
        UNIFONT, "c6af92436013f6b43474adb3fdbf00f8e9afa8e01687401eecaa8de9947bd329"),
    "Scripts.txt": (UCD, "0071fd81b6aeae25f6e8bce8efec3066a6476a91b49bdb2f52dc76e817862a6a"),
    "UnicodeData.txt": (
        UCD, "0736451de439ae7baf1425136617da495e09ee5afbe6e394374db7009ea08950"),
}

# Each Hershey file is one alphabet in one style, laid out in ASCII order.
HERSHEY_STYLES = {
    "futural": ("Latin", "4958a1d06ea04709feb530deaab53d1efa1285d0d3e92a4a3edd74d279871ced"),
    "futuram": ("Latin", "621893f5e1aff698e387978ed5f3d372063683b0234b3ba3f38a92e5502a6975"),
    "rowmans": ("Latin", "8718fb129c0f6bce89c84fe41bc467e39534d215a6f7c3220cc5789a8a7d8618"),
    "rowmand": ("Latin", "c56497b162a3831f0da2e189ada4a7335ce81b1c3c1cf380b2ced04287313d2e"),
    "rowmant": ("Latin", "703d6a641334bce32ae8347900b6ec743d4672f898266796853f26f53918b52a"),
    "timesr": ("Latin", "c454a5ed471aa33c1aac8c5b21c2d343e828805af2b48eebba20c46f492d9457"),
    "timesi": ("Latin", "66cd7ca5c402d5609de083b166f704d89025619f2dabe42f3d13be95b261414b"),
    "scripts": ("Latin", "6b391b2ea3a0771cf18caff0ed111db3d05681fa586d423a740cc0b2b155a873"),
    "scriptc": ("Latin", "747f9384b0adbec3f6826cc374727adb262c6a96e2a758a2472d11291b7104c7"),
    "cursive": ("Latin", "9667a2c6424bc89f992738ff97de204a8580d92ef353e32b8014d9d7b106cd0b"),
    "gothiceng": ("Latin", "2d7a62784906897ca3707ae73423c319295567efbf2c27825d3b72c28d00c061"),
    "greek": ("Greek", "827d2e1dc4f5a5a235efd7c78d30b559822a7c7f3984206c41d382bd14e2ce29"),
    "greekc": ("Greek", "e1eae76922db931d47475b868ff1cf19bf083601925272a541f914cc71004fb4"),
    "greeks": ("Greek", "309298debb0e472047f8329d31f849b14a98108a706d0f4f684e40d1eb023a76"),
    "cyrillic": ("Cyrillic",
                 "0266865d94001fe26a642fbf20d2134de295dcfd2ca320d092b4d6476acda044"),
    "cyrilc_1": ("Cyrillic",
                 "efc90ac562e2f6705fe7a84ecad273b22c3e3d3c279b0beeca9641ebbca02c24"),
    "japanese": ("Japanese",
                 "9935d0c696fb16d02c8929ccfe98ba3045fbd9416855a09aafbb3b98a58f0039"),
}


def _r(a: int, b: int) -> list:
    return list(range(a, b + 1))


# The base alphabets of the writing systems the check compares against, by code point: the
# letters a reader would take a derivative system to be modelled on. Tengwar and Cirth are
# the ConScript registry's.
LISTED = {
    "Latin": _r(0x41, 0x5A) + _r(0x61, 0x7A),
    "Greek": [c for c in _r(0x391, 0x3A9) if c != 0x3A2] + _r(0x3B1, 0x3C9),
    "Cyrillic": _r(0x410, 0x44F),
    "Arabic": _r(0x621, 0x63A) + _r(0x641, 0x64A),
    "Hebrew": _r(0x5D0, 0x5EA),
    "Devanagari": _r(0x905, 0x939),
    "Hangul": _r(0x3131, 0x3163),
    "Runic": _r(0x16A0, 0x16EA),
    "Han": _r(0x2F00, 0x2FD5),
    "Kana": _r(0x3041, 0x3096) + _r(0x30A1, 0x30FA),
    "Bopomofo": _r(0x3105, 0x312F),
    "Tengwar": _r(0xE000, 0xE07F),
    "Cirth": _r(0xE080, 0xE0FF),
    "programming syntax": _r(0x21, 0x2F) + _r(0x3A, 0x40) + _r(0x5B, 0x60) + _r(0x7B, 0x7E),
    "circuit symbols": _r(0x2300, 0x23FF),
    "Kaktovik numerals": _r(0x1D2C0, 0x1D2D3),
    "Ogham": _r(0x1681, 0x169A),
}
CONSCRIPT = ("Tengwar", "Cirth")


class SourceUnavailable(Exception):
    """A reference source could not be fetched, or its bytes do not match the hash."""


def fetch(name: str, base: str, sha256: str) -> str:
    """The cached path of a source, downloaded and checked on first use."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if not os.path.isfile(path):
        try:
            with urllib.request.urlopen(base + name, timeout=TIMEOUT) as r:
                body = r.read()
        except OSError as e:
            raise SourceUnavailable("%s: %s" % (name, e)) from e
        with open(path + ".part", "wb") as f:
            f.write(body)
        os.replace(path + ".part", path)
    with open(path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    if digest != sha256:
        raise SourceUnavailable("%s: SHA-256 %s, expected %s" % (name, digest, sha256))
    return path


def _source(name: str) -> str:
    base, digest = SOURCES[name]
    return fetch(name, base, digest)


def scripts() -> dict:
    """The Unicode script of each code point (UCD Scripts.txt)."""
    out = {}
    with open(_source("Scripts.txt"), encoding="utf-8") as f:
        for line in f:
            line = line.split("#")[0].strip()
            if not line:
                continue
            span, name = [x.strip() for x in line.split(";")]
            a, _, b = span.partition("..")
            for cp in range(int(a, 16), int(b or a, 16) + 1):
                out[cp] = name
    return out


def categories() -> dict:
    """The general category of each code point (UCD UnicodeData.txt), ranges expanded."""
    out, first = {}, None
    with open(_source("UnicodeData.txt"), encoding="utf-8") as f:
        for line in f:
            fields = line.split(";")
            cp, name, cat = int(fields[0], 16), fields[1], fields[2]
            if name.endswith(", Last>") and first is not None:
                for x in range(first, cp + 1):
                    out[x] = cat
            out[cp] = cat
            first = cp if name.endswith(", First>") else None
    return out


def unifont(csur: bool = False):
    """Each glyph of Unifont as (code point, ink points in pixel coordinates)."""
    name = "unifont_csur-18.0.01.hex.gz" if csur else "unifont_all-18.0.01.hex.gz"
    with gzip.open(_source(name), "rt", encoding="ascii") as f:
        for line in f:
            cp, bits = line.strip().split(":")
            width = len(bits) // 4
            step = width // 4
            rows = [int(bits[i:i + step], 16) for i in range(0, len(bits), step)]
            ink = [(x, y) for y, row in enumerate(rows) for x in range(width)
                   if row >> (width - 1 - x) & 1]
            if ink:
                yield int(cp, 16), ink


def hershey(style: str) -> list:
    """The letters of one Hershey font as polylines, in ASCII order from A to z."""
    system, digest = HERSHEY_STYLES[style]
    path = fetch(style + ".jhf", HERSHEY, digest)
    glyphs = []
    with open(path, encoding="latin-1") as f:
        lines = f.read().split("\n")
    for i, line in enumerate(lines):
        line = line.rstrip("\r")
        if len(line) < 10:
            continue
        code = i + 32
        if system != "Japanese" and not (65 <= code <= 90 or 97 <= code <= 122):
            continue
        strokes, current = [], []
        body = line[10:]
        for k in range(0, len(body) - 1, 2):
            pair = body[k:k + 2]
            if pair == " R":
                if current:
                    strokes.append(current)
                current = []
            else:
                current.append((ord(pair[0]) - 82, ord(pair[1]) - 82))
        if current:
            strokes.append(current)
        if any(len(s) > 1 for s in strokes):
            glyphs.append((code, strokes))
    return glyphs


def sample(strokes, step: float) -> list:
    """Points along polylines, at most `step` apart."""
    out = []
    for line in strokes:
        for (x0, y0), (x1, y1) in zip(line, line[1:]):
            n = max(1, int(max(abs(x1 - x0), abs(y1 - y0)) / step))
            out += [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n + 1)]
    return out


_ROW = (1 << GRID) - 1
_LEFT = sum(1 << (r * GRID) for r in range(GRID))
_RIGHT = sum(1 << (r * GRID + GRID - 1) for r in range(GRID))
_FULL = (1 << (GRID * GRID)) - 1


def bitmap(points) -> int:
    """Ink points as an occupancy bit set on the grid, each axis stretched to fill it."""
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    x0, y0 = min(xs), min(ys)
    w, h = max(xs) - x0, max(ys) - y0
    side = max(w, h) or 1.0
    sx = w if w >= 0.25 * side else side
    sy = h if h >= 0.25 * side else side
    ox, oy = (sx - w) / 2, (sy - h) / 2
    bits = 0
    for x, y in points:
        cx = min(GRID - 1, int((x - x0 + ox) / (sx or 1) * (GRID - 1) + 0.5))
        cy = min(GRID - 1, int((y - y0 + oy) / (sy or 1) * (GRID - 1) + 0.5))
        bits |= 1 << (cy * GRID + cx)
    return bits


def dilate(bits: int) -> int:
    across = bits | ((bits & ~_RIGHT) << 1) | ((bits & ~_LEFT) >> 1)
    return (across | (across << GRID) | (across >> GRID)) & _FULL


class Glyph:
    """A glyph's bit set with its dilation and ink count, as the measure needs them."""
    __slots__ = ("bits", "near", "ink")

    def __init__(self, bits: int):
        self.bits, self.near, self.ink = bits, dilate(bits), bits.bit_count()


def similarity(a: Glyph, b: Glyph) -> float:
    """The F-measure of two glyphs' ink within one cell of each other's."""
    p = (a.bits & b.near).bit_count() / a.ink
    r = (b.bits & a.near).bit_count() / b.ink
    return 0.0 if p + r == 0 else 2 * p * r / (p + r)


def comparable(a: Glyph, b: Glyph) -> bool:
    """Whether two glyphs' ink is within a factor of 2.2, outside which the measure
    stays low; a filter, so that most of the comparisons need not be made."""
    return a.ink <= 2.2 * b.ink and b.ink <= 2.2 * a.ink


def turns(points) -> list:
    """The eight images of a point set under turns by quarters and mirroring."""
    out = []
    for mirror in (False, True):
        for quarter in range(4):
            image = []
            for x, y in points:
                if mirror:
                    x = -x
                for _ in range(quarter):
                    x, y = -y, x
                image.append((x, y))
            out.append(image)
    return out


def alphabets() -> dict:
    """Every reference alphabet, by system and style: Unifont's base alphabet of each
    listed system, and each Hershey font. Each is a list of (label, Glyph)."""
    want = {cp: system for system, cps in LISTED.items() for cp in cps}
    out = {}
    for csur in (False, True):
        for cp, ink in unifont(csur):
            system = want.get(cp)
            if system is None or (system in CONSCRIPT) != csur:
                continue
            out.setdefault("%s, Unifont" % system, []).append(
                ("U+%04X" % cp, Glyph(bitmap(ink))))
    for style, (system, _) in HERSHEY_STYLES.items():
        out["%s, Hershey %s" % (system, style)] = [
            ("ASCII %d" % code if system != "Japanese" else "glyph %d" % code,
             Glyph(bitmap(sample(strokes, 0.5)))) for code, strokes in hershey(style)]
    return out


def symbols() -> list:
    """Every symbol Unifont draws (general category S: mathematical, currency, modifier
    and other symbols, the arrows among them), with its script: signs to which a reader
    already gives a meaning, so that a component near-identical to one would be read as
    it."""
    script, cat = scripts(), categories()
    return [(cp, script.get(cp, "Unknown"), Glyph(bitmap(ink))) for cp, ink in unifont()
            if cat.get(cp, "Cn")[0] == "S"]


def letters() -> list:
    """Every letter and digit of every writing system Unifont draws, with its script:
    the whole of what the stress test asks a glyph to be compared against."""
    script, cat = scripts(), categories()
    out = []
    for cp, ink in unifont():
        if cat.get(cp, "Cn")[0] in "LN":
            out.append((cp, script.get(cp, "Unknown"), Glyph(bitmap(ink))))
    for cp, ink in unifont(csur=True):
        if 0xE000 <= cp <= 0xE0FF:
            out.append((cp, "Tengwar" if cp < 0xE080 else "Cirth", Glyph(bitmap(ink))))
    return out
