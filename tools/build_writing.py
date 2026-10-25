"""Write `language/writing.json`, the writing-system specification, from the declared
source `tools/writing_source.py` and the search's result `tools/component_search.json`.

Two things are decided here and nowhere else. Each component's unit strokes are divided
into strokes of the pen, at most two, in a declared order: a set with no odd point is one
closed stroke from its leftmost point, otherwise each stroke runs between two odd points,
every stroke is written from its left end, and strokes are written in the order of their
starting points from the left. And the components are assigned to the symbols: the
assignment maximises the least visual distance between two forms of the grammar that
differ in a critical dimension, then makes the fewest pairs that close, then maximises the
mean, by exchanges from the search's order until none improves, so that no shape is given
to a symbol by hand.

Run after `tools/build_language.py`, which calls it, since it reads the grammar.
"""
from __future__ import annotations

import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import writing_source as W  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEARCH = os.path.join(ROOT, "tools", "component_search.json")
VERSION = "0.2"
UNITS = ("assertion", "situation", "term", "readings")


def key(p):
    return (p[0], p[1])


def pen_strokes(unit_strokes: list) -> list:
    """The strokes of the pen that draw a set of unit strokes, by the rule above, each a
    list of points with the points where it runs straight on left out."""
    edges = [tuple(map(tuple, e)) for e in unit_strokes]
    degree = {}
    for a, b in edges:
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1
    odd = sorted((v for v, d in degree.items() if d % 2), key=key)
    virtual = []
    if len(odd) == 4:
        virtual = [(odd[2], odd[3])]
    elif len(odd) not in (0, 2):
        raise ValueError("a component needs more than two strokes: %r" % unit_strokes)
    start = odd[0] if odd else min(degree, key=key)
    trail = _walk(start, edges + virtual)
    paths, current = [], [trail[0][0]]
    for point, via in trail[1:]:
        if via is not None and via >= len(edges):
            paths.append(current)
            current = [point]
        else:
            current.append(point)
    paths.append(current)
    out = []
    for path in paths:
        if key(path[-1]) < key(path[0]):
            path = path[::-1]
        out.append(_straighten(path))
    out.sort(key=lambda p: key(p[0]))
    return [[list(p) for p in path] for path in out]


def _walk(start, edges: list) -> list:
    """Hierholzer's walk over every edge from `start`, taking at each point the unused
    edge to the leftmost neighbour, so that the result is determined: the points in
    order, each with the index of the edge that reached it."""
    used = [False] * len(edges)
    stack, trail = [(start, None)], []
    while stack:
        u, via = stack[-1]
        nexts = sorted((key(b if a == u else a), i) for i, (a, b) in enumerate(edges)
                       if not used[i] and u in (a, b))
        if nexts:
            _, i = nexts[0]
            used[i] = True
            a, b = edges[i]
            stack.append((b if a == u else a, i))
        else:
            trail.append(stack.pop())
    trail.reverse()
    return trail


def _straighten(path: list) -> list:
    out = [path[0]]
    for i in range(1, len(path) - 1):
        a, b, c = out[-1], path[i], path[i + 1]
        if (b[0] - a[0]) * (c[1] - b[1]) != (b[1] - a[1]) * (c[0] - b[0]):
            out.append(b)
    out.append(path[-1])
    return out


def _mask(unit_strokes, index):
    return frozenset(index[tuple(sorted(map(tuple, s)))] for s in unit_strokes)


def distances(components: list) -> list:
    """The distance under turns and mirrors between every two components."""
    strokes = W.unit_strokes()
    index = {s: i for i, s in enumerate(strokes)}
    sets = [_mask(c["strokes"], index) for c in components]
    images = []
    for c in components:
        imgs = set()
        for f in W.SYMMETRIES:
            imgs.add(frozenset(index[tuple(sorted((f(tuple(a)), f(tuple(b)))))]
                               for a, b in c["strokes"]))
        images.append(imgs)
    n = len(components)
    out = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                out[i][j] = min(1 - len(sets[i] & m) / len(sets[i] | m) for m in images[j])
    return out


def critical_pairs(grammar: dict) -> list:
    """The pairs of forms that differ in a critical dimension: two members of one class
    that carries one."""
    pairs = []
    for cls in grammar["classes"]:
        if cls.get("critical dimension"):
            for a, b in itertools.combinations(cls["members"], 2):
                if len(a["form"]) == len(b["form"]):
                    pairs.append((a["form"], b["form"]))
    return pairs


def assign(letters: str, dist: list, pairs: list) -> tuple:
    """The assignment of components to letters, improved by exchanges until none helps."""
    pos = {ch: i for i, ch in enumerate(letters)}
    coded = [[(pos[x], pos[y]) for x, y in zip(a, b) if x != y] for a, b in pairs]

    def value(perm):
        totals = [sum(dist[perm[i]][perm[j]] for i, j in diffs) for diffs in coded]
        least = min(totals)
        return (round(least, 9), -sum(1 for t in totals if abs(t - least) < 1e-9),
                round(sum(totals) / len(totals), 9))

    perm = list(range(len(letters)))
    val = value(perm)
    improved = True
    while improved:
        improved = False
        for i, j in itertools.combinations(range(len(letters)), 2):
            perm[i], perm[j] = perm[j], perm[i]
            v = value(perm)
            if v > val:
                val, improved = v, True
            else:
                perm[i], perm[j] = perm[j], perm[i]
    return perm, val


def build(grammar: dict, phonology: dict) -> dict:
    with open(SEARCH, encoding="utf-8") as f:
        search = json.load(f)
    dist = distances(search["components"])
    perm, val = assign("".join(s["letter"] for s in phonology["symbols"]), dist,
                       critical_pairs(grammar))
    out_components = []
    for i, s in enumerate(phonology["symbols"]):
        c = search["components"][perm[i]]
        out_components.append({
            "symbol": s["letter"], "code point": s["code point"],
            "unit strokes": c["strokes"], "pen strokes": pen_strokes(c["strokes"])})
    least_component = min(dist[i][j] for i in range(len(dist)) for j in range(len(dist))
                          if i != j)
    return {
        "version": VERSION,
        "lattice": {"points": [list(p) for p in W.LATTICE], "box": list(W.BOX),
                    "unit strokes": [[list(a), list(b)] for a, b in W.unit_strokes()]},
        "measure": "one minus the Jaccard similarity of two components' sets of unit "
                   "strokes, the least over the lattice's turns and mirrors of the second",
        "symmetries": ["identity", "mirror about the upright axis",
                       "mirror about the level axis", "half-turn"],
        "code point block": ["U+%04X" % W.CODE_POINT_BLOCK[0],
                             "U+%04X" % W.CODE_POINT_BLOCK[1]],
        "separator": "U+0020",
        "line end": "U+000A",
        "components": out_components,
        "units": _units(grammar),
        "walls": {"opens": "g.structure.wall", "closes": "g.structure.end-wall"},
        "numbers": {"class": "g.numbers.numeral"},
        "forms": {"display": "the components at their size on the lattice, with the "
                              "metrics below",
                   "compact": "the display form at half size, every coordinate halved",
                   "handwritten": "the display form with the components of a word joined "
                                  "by hairlines, from where the pen leaves one to where it "
                                  "starts the next",
                   "ceremonial": "the variant of each form for a move in the ceremonial "
                                 "register: a serif across each free end, and the rules "
                                 "and the overline doubled"},
        "metrics": W.METRICS,
        "pixels per unit": W.PIXELS_PER_UNIT,
        "serif": W.SERIF,
        "double": W.DOUBLE,
        "least component distance": round(least_component, 6),
        "least critical distance": val[0],
        "critical pairs at the least distance": -val[1],
        "mean critical distance": val[2],
        "search": {k: search[k] for k in ("orbits", "admissible", "least distance",
                                          "pairs at the least distance", "mean distance",
                                          "unit strokes used")},
    }


def _units(grammar: dict) -> dict:
    """The sign of each unit: the structural words that open and close it, and its mark."""
    structural = {w["identifier"] for w in grammar["structural words"]}
    units = {}
    for name in UNITS:
        units[name] = {"opens": "g.structure.%s" % name,
                       "closes": "g.structure.end-%s" % name,
                       "mark": [list(p) for p in W.UNIT_MARKS[name]]}
        assert units[name]["opens"] in structural and units[name]["closes"] in structural
    return units


def write(grammar: dict, phonology: dict):
    spec = build(grammar, phonology)
    path = os.path.join(ROOT, "language", "writing.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return spec


if __name__ == "__main__":
    with open(os.path.join(ROOT, "language", "grammar.json"), encoding="utf-8") as f:
        g = json.load(f)
    with open(os.path.join(ROOT, "language", "phonology.json"), encoding="utf-8") as f:
        p = json.load(f)
    s = write(g, p)
    print("least component distance %.3f, least critical distance %.3f in %d pairs"
          % (s["least component distance"], s["least critical distance"],
             s["critical pairs at the least distance"]))
