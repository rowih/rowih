"""Build the font of the native digital form (see
specification/writing-system.md#the-font): `language/font/rowih.ttf`, a TrueType font
drawn from `language/writing.json`.

A glyph is drawn for each of the nineteen code points, from its component's strokes of
the pen: each segment a rectangle as wide as the display form's stroke, each point of a
stroke an octagon as wide, overlapping contours filled by the nonzero rule and flagged as
overlapping. The space is as wide as the word gap less the gap the components keep. The
signs drawn whole that a font can draw alone are ligatures (`liga`): each word that opens
or closes a unit, drawn as its side with its mark and a foot, as the drawing draws a side
whose partner is out of sight, since a font cannot join two sides by a rule; each word
that opens or closes a wall; and each protected word, drawn with its overline. A
ligature replaces its word only where no component stands before or after it, so that it
never fires inside a longer word. The ceremonial variant is the stylistic set `ss01`: a
serif across each free end, and the protected words' overline doubled. A run of numerals
is not framed, which needs the run's extent, and embedded material is drawn by whichever
font a reader's system takes for its characters.

The build is deterministic, its dates fixed, so that a rebuild writes the same bytes; the
test compares the committed font with a fresh build. Run from the repository root.
"""
from __future__ import annotations

import io
import json
import math
import os
import sys

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.misc.timeTools import timestampFromString
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._g_l_y_f import flagOverlapSimple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))
from rowih import writing  # noqa: E402
from rowih.data import load  # noqa: E402

OUT = os.path.join(ROOT, "language", "font", "rowih.ttf")
FAMILY = "Rowih"
UNITS_PER_EM = 1000
SCALE = 50            # font units to a unit of the lattice
DATE = "Sun Oct 11 00:00:00 2026"
OCTAGON = [(math.cos(math.pi / 8 + k * math.pi / 4), math.sin(math.pi / 8 + k * math.pi / 4))
           for k in range(8)]


def _font_point(p, box_height: int) -> tuple:
    """A point of the lattice, y downward from the top of the box, in font units, y
    upward from the baseline at the bottom of the box."""
    return (p[0] * SCALE, (box_height - p[1]) * SCALE)


def _clockwise(points: list) -> list:
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]))
    return points if area < 0 else points[::-1]


def _contours(paths: list, half: float, box_height: int) -> list:
    """The outline of polylines drawn with round ends and joins, as integer contours."""
    out = []
    radius = half / math.cos(math.pi / 8)
    for path in paths:
        pts = [_font_point(p, box_height) for p in path]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            length = math.hypot(bx - ax, by - ay)
            nx, ny = -(by - ay) / length * half, (bx - ax) / length * half
            quad = [(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)]
            out.append(_clockwise([(round(x), round(y)) for x, y in quad]))
        for x, y in pts:
            out.append(_clockwise([(round(x + radius * c), round(y + radius * s))
                                   for c, s in OCTAGON]))
    return out


def _glyph(contours: list):
    pen = TTGlyphPen(None)
    for contour in contours:
        pen.moveTo(contour[0])
        for p in contour[1:]:
            pen.lineTo(p)
        pen.closePath()
    g = pen.glyph()
    if contours:
        g.flags[0] |= flagOverlapSimple
    return g


def _composite(parts: list, glyphs: dict):
    """A glyph made of others, each (glyph name, x offset in font units)."""
    pen = TTGlyphPen(glyphs)
    for name, dx in parts:
        pen.addComponent(name, (1, 0, 0, 1, dx, 0))
    return pen.glyph()


def _name(symbol: str, lang) -> str:
    return "uni%04X" % ord(lang.code_points[symbol])


class _Glyphs:
    """The glyphs of the font as they are drawn, with their advances, the character map
    and the word each ligature replaces, in the order the font lists them."""

    def __init__(self, lang):
        self.lang, self.spec = lang, lang.writing
        self.m, self.box = self.spec["metrics"], self.spec["lattice"]["box"]
        self.half = self.m["stroke"] * SCALE / 2
        self.advance = (self.box[0] + self.m["gap"]) * SCALE
        self.glyphs, self.widths, self.cmap, self.words = {}, {}, {}, {}
        self.glyphs[".notdef"] = _glyph([[(50, 0), (50, 600), (550, 600), (550, 0)][::-1],
                                         [(100, 50), (500, 50), (500, 550), (100, 550)][::-1]])
        self.widths[".notdef"] = 600
        self.glyphs["space"] = _glyph([])
        self.widths["space"] = (self.m["word gap"] - self.m["gap"]) * SCALE
        self.cmap[0x20] = "space"

    def add(self, name: str, paths: list, width: int):
        self.glyphs[name] = _glyph(_contours(paths, self.half, self.box[1]))
        self.widths[name] = width

    def components(self, letters: list):
        """Each symbol's component, and its ceremonial variant with a serif across each
        free end."""
        serif = self.spec["serif"]
        for ch in letters:
            name = _name(ch, self.lang)
            self.cmap[ord(self.lang.code_points[ch])] = name
            pens = [list(map(tuple, p)) for p in writing.pen_strokes(ch, self.lang)]
            self.add(name, pens, self.advance)
            serifs = [[(x, y - serif), (x, y + serif)]
                      for x, y in writing.free_ends(ch, self.lang)]
            self.add(name + ".ss01", pens + serifs, self.advance)

    def signs(self):
        """The signs of units and walls, each word drawn alone, in a slot as wide as a
        side and the gap a component keeps."""
        m, spec = self.m, self.spec
        width = (m["side"] + m["gap"]) * SCALE
        x, top = m["side"] // 2, -2
        rule = self.box[1] + m["rule depth"]
        for unit, sign in spec["units"].items():
            base = [p[0] for p in sign["mark"] if p[1] == 0]
            dx = x - (min(base) + max(base)) // 2
            drawn = [(dx + px, py - 2) for px, py in sign["mark"]]
            for opens in (True, False):
                name = "sign.%s.%s" % (unit, "opens" if opens else "closes")
                foot = 4 if opens else -4
                self.add(name, [[(x, top), (x, rule), (x + foot, rule)], drawn], width)
                self.words[name] = self.lang.form_of(sign["opens" if opens else "closes"])
        for opens in (True, False):
            name = "sign.wall.%s" % ("opens" if opens else "closes")
            tick = [(6, top), (10, top)] if opens else [(-2, top), (2, top)]
            self.add(name, [[(2, top), (2, rule)], [(6, top), (6, rule)], tick], width)
            self.words[name] = self.lang.form_of(spec["walls"]["opens" if opens else "closes"])

    def protected(self):
        """The protected words, each its components under an overline, doubled in the
        ceremonial variant."""
        m, double = self.m, self.spec["double"]
        forms = sorted({i.form for i in self.lang.items.values() if i.protected and i.form})
        for n in sorted({len(f) for f in forms}):
            end, y = n * (self.box[0] + m["gap"]) - m["gap"], -m["overline"]
            self.add("overline.%d" % n, [[(0, y), (end, y)]], 0)
            self.add("overline.%d.ss01" % n,
                     [[(0, y), (end, y)], [(0, y - double), (end, y - double)]], 0)
        for form in forms:
            name = "word." + form
            for suffix in ("", ".ss01"):
                parts = [(_name(ch, self.lang) + suffix, i * self.advance)
                         for i, ch in enumerate(form)]
                parts.append(("overline.%d%s" % (len(form), suffix), 0))
                self.glyphs[name + suffix] = _composite(parts, self.glyphs)
                self.widths[name + suffix] = len(form) * self.advance
            self.words[name] = form


def build(lang=None) -> bytes:
    lang = lang or load()
    letters = [c["symbol"] for c in lang.writing["components"]]
    g = _Glyphs(lang)
    g.components(letters)
    g.signs()
    g.protected()
    font = _assemble(g)
    addOpenTypeFeaturesFromString(font, _features(lang, letters, g.words))
    font["OS/2"].recalcUnicodeRanges(font)
    font.recalcTimestamp = False
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()


def _assemble(g: _Glyphs):
    """The font's tables around its glyphs, its dates fixed."""
    spec, m, box = g.spec, g.m, g.box
    order = [".notdef", "space"] + [n for n in g.glyphs if n not in (".notdef", "space")]
    fb = FontBuilder(UNITS_PER_EM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(g.cmap)
    fb.setupGlyf(g.glyphs)
    glyf = fb.font["glyf"]
    fb.setupHorizontalMetrics({n: (g.widths[n], getattr(glyf[n], "xMin", 0)) for n in order})
    # the readings mark stands highest, fourteen units above the box, and the rules
    # lowest, the rule depth below it; each with half a stroke and a margin beside
    ascent = (box[1] + 16) * SCALE
    descent = -(m["rule depth"] + 2) * SCALE
    fb.setupHorizontalHeader(ascent=ascent, descent=descent)
    fb.setupNameTable({"familyName": FAMILY, "styleName": "Regular",
                       "uniqueFontIdentifier": "%s Regular %s" % (FAMILY, spec["version"]),
                       "version": "Version %s" % spec["version"],
                       "psName": FAMILY + "-Regular"})
    fb.setupOS2(sTypoAscender=ascent, sTypoDescender=descent, sTypoLineGap=0,
                usWinAscent=ascent, usWinDescent=-descent, fsType=0, achVendID="NONE")
    fb.setupPost()
    fb.updateHead(created=timestampFromString(DATE), modified=timestampFromString(DATE),
                  fontRevision=float(spec["version"]))
    return fb.font


def _features(lang, letters: list, words: dict) -> str:
    """The ligatures, each guarded so that it fires only on a whole word, and the
    ceremonial stylistic set, which acts after them."""
    names = [_name(ch, lang) for ch in letters]
    lines = ["languagesystem DFLT dflt;", "@C = [%s];" % " ".join(names), "lookup words {"]
    for name, form in words.items():
        lines.append("  sub %s by %s;" % (" ".join(_name(ch, lang) for ch in form), name))
    lines += ["} words;", "feature liga {"]
    for name, form in words.items():
        marked = " ".join(_name(ch, lang) + "'" for ch in form)
        lines.append("  ignore sub @C %s;" % marked)
        lines.append("  ignore sub %s @C;" % marked)
        first, rest = form[0], form[1:]
        lines.append("  sub %s' lookup words %s;" % (
            _name(first, lang), " ".join(_name(ch, lang) + "'" for ch in rest)))
    lines += ["} liga;", "lookup ceremonial {"]
    for name in names + [n for n in words if n.startswith("word.")]:
        lines.append("  sub %s by %s.ss01;" % (name, name))
    lines += ["} ceremonial;", "feature ss01 {", '  featureNames { name "Ceremonial"; };',
              "  lookup ceremonial;", "} ss01;"]
    return "\n".join(lines) + "\n"


def main() -> int:
    data = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "wb") as f:
        f.write(data)
    print("wrote %s, %d bytes" % (os.path.relpath(OUT, ROOT), len(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
