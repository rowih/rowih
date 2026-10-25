"""The writing-system specification as the renderer and the tests read it
(`language/writing.json`; specification/writing-system.md#the-components): each symbol's
component, its unit strokes on the lattice and its strokes of the pen, and the declared
visual measure.

The measure of two components is one minus the Jaccard similarity of their sets of unit
strokes, the least over the lattice's turns and mirrors of the second, so that a
component turned or mirrored is as close to another as the two would look. The visual
distance of two forms of one length is the sum of their components' measures, position
by position. Both are the project's confusability data for the native writing system.
"""
from __future__ import annotations

from .data import Language, load


def _point(p) -> tuple:
    return (p[0], p[1])


def _stroke(a, b) -> tuple:
    return tuple(sorted((_point(a), _point(b))))


def _symmetries(box) -> list:
    w, h = box
    return [lambda p: p, lambda p: (w - p[0], p[1]), lambda p: (p[0], h - p[1]),
            lambda p: (w - p[0], h - p[1])]


# The tables of each loaded language, by the identity of its record, which `data.load`
# keeps alive and never changes.
_TABLES: dict = {}


def _tables(lang: Language) -> dict:
    spec = lang.writing
    box = tuple(spec["lattice"]["box"])
    syms = _symmetries(box)
    units, images, pen = {}, {}, {}
    for c in spec["components"]:
        strokes = frozenset(_stroke(a, b) for a, b in c["unit strokes"])
        units[c["symbol"]] = strokes
        images[c["symbol"]] = {frozenset(_stroke(f(a), f(b)) for a, b in strokes)
                               for f in syms}
        pen[c["symbol"]] = [[_point(p) for p in path] for path in c["pen strokes"]]
    return {"units": units, "images": images, "pen": pen, "box": box}


def tables(lang: Language | None = None) -> dict:
    lang = lang or load()
    key = id(lang)
    if key not in _TABLES or _TABLES[key][0] is not lang:
        _TABLES[key] = (lang, _tables(lang))
    return _TABLES[key][1]


def unit_strokes(symbol: str, lang: Language | None = None) -> frozenset:
    return tables(lang)["units"][symbol]


def pen_strokes(symbol: str, lang: Language | None = None) -> list:
    """The strokes of the pen that write a component, in order, each from its start."""
    return tables(lang)["pen"][symbol]


def distance(a: str, b: str, lang: Language | None = None) -> float:
    """The declared visual measure of two components (the module's docstring)."""
    t = tables(lang)
    sa = t["units"][a]
    return min(1 - len(sa & m) / len(sa | m) for m in t["images"][b])


def form_distance(x: str, y: str, lang: Language | None = None) -> float:
    """The visual distance of two forms of one length; forms of different lengths differ
    in length, which a reader sees."""
    if len(x) != len(y):
        return float("inf")
    return sum(distance(a, b, lang) for a, b in zip(x, y) if a != b)


def turned_pairs(lang: Language | None = None) -> list:
    """Pairs of components one of which is the other turned or mirrored."""
    lang = lang or load()
    t = tables(lang)
    letters = sorted(t["units"])
    return [(a, b) for i, a in enumerate(letters) for b in letters[i + 1:]
            if t["units"][a] in t["images"][b]]


def free_ends(symbol: str, lang: Language | None = None) -> list:
    """The points where a component's strokes end without meeting another, where the
    ceremonial forms set a serif
    (specification/writing-system.md#drawing-a-word-and-a-line)."""
    degree = {}
    for a, b in unit_strokes(symbol, lang):
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1
    return sorted(p for p, d in degree.items() if d == 1)
