"""The originality check of the writing system (see
specification/writing-system.md#what-the-writing-system-has-been-tested-on): render every
glyph of the inventory and compare it against the glyphs of the writing systems encoded in
Unicode by an image-similarity measure, reporting the nearest.

Each inventory is matched one to one against each reference alphabet (`reference_glyphs.
alphabets`: Unifont's base alphabet of every listed system and each Hershey font), as
drawn and under the eight turns and mirrors, and the matched pairs are counted at a
similarity of 0.95 and of 0.90; a derivative writing system is one with many components
near-identical to one alphabet's letters. Two criteria decide: no component as drawn is
paired at 0.95 or more with a letter of any listed alphabet, and no alphabet takes more
than two components at 0.90 or more. The core's inventory, which imitated Latin capitals,
is run as the control, so that the report shows the check can fail. Each component's
nearest letters among all of Unicode's, its nearest symbols (the arrows among them, which
a reader would read as themselves), and the signs drawn whole against programming syntax
and circuit symbols, are reported beside, with a third criterion: no component is
near-identical to any letter, digit or symbol Unicode encodes, which the search for
components also applies.

Writes `corpus/reports/glyph-originality.json`. Run from the repository root. Exit status:
1 when a component fails a criterion or the control meets every one, 0 otherwise.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reference_glyphs as R  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "corpus", "reports", "glyph-originality.json")
IDENTICAL, NEAR, NEAR_ALLOWED = 0.95, 0.90, 2

# The core's components (render.py at commit 1c81b8e), kept as the control.
CORE = {
    "p": [[(0, 0), (0, 1)], [(0, 0), (0.7, 0), (0.7, 0.45), (0, 0.45)]],
    "t": [[(0, 0), (1, 0)], [(0.5, 0), (0.5, 1)], [(0.5, 1), (0.9, 0.75)]],
    "k": [[(0, 0), (0, 1)], [(0.9, 0), (0, 0.5), (0.9, 1)]],
    "b": [[(0, 0), (0, 1), (0.8, 1), (0.8, 0.5), (0, 0.5)]],
    "d": [[(0.8, 0), (0.8, 1)], [(0.8, 0.4), (0.1, 0.4), (0.1, 1), (0.8, 1)], [(0, 0), (0.4, 0)]],
    "g": [[(0.9, 0.1), (0.2, 0.1), (0.2, 0.9), (0.9, 0.9), (0.9, 0.55), (0.55, 0.55)]],
    "m": [[(0, 1), (0, 0), (0.5, 0.6), (1, 0), (1, 1)]],
    "n": [[(0, 1), (0, 0), (1, 1), (1, 0)], [(0.4, 1), (0.6, 1)]],
    "s": [[(1, 0), (0, 0), (0, 0.5), (1, 0.5), (1, 1), (0, 1)], [(0.5, 0.25), (0.5, 0.35)]],
    "l": [[(0, 0), (0, 1), (0.8, 1)], [(0.3, 0.3), (0.6, 0.3)]],
    "r": [[(0, 1), (0, 0), (0.8, 0), (0.8, 0.5), (0, 0.5), (0.8, 1)]],
    "w": [[(0, 0), (0.25, 1), (0.5, 0.4), (0.75, 1), (1, 0)], [(0.5, 0), (0.5, 0.15)]],
    "y": [[(0, 0), (0.5, 0.5), (1, 0)], [(0.5, 0.5), (0.5, 1), (0.2, 1)]],
    "h": [[(0, 0), (0, 0.6), (1, 0.6), (1, 0)], [(0.5, 0.6), (0.5, 1)]],
    "a": [[(0, 1), (0.5, 0), (1, 1)], [(0.2, 0.6), (0.8, 0.6)], [(1, 1), (1, 0.75)]],
    "e": [[(0.9, 0), (0, 0), (0, 1), (0.9, 1)], [(0, 0.5), (0.6, 0.5)], [(0.6, 0.5), (0.6, 0.7)]],
    "i": [[(0.5, 0.25), (0.5, 1)], [(0.3, 0), (0.7, 0)], [(0.5, 1), (0.8, 1)]],
    "o": [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)], [(0.3, 0.3), (0.3, 0.7)]],
    "u": [[(0, 0), (0, 1), (1, 1), (1, 0)], [(1, 0), (0.7, 0)]],
}


def _glyphs(strokes, turns: bool) -> list:
    pts = R.sample(strokes, 0.02 * max(1.0, max(abs(c) for s in strokes for p in s for c in p)))
    images = R.turns(pts) if turns else [pts]
    return [R.Glyph(R.bitmap(p)) for p in images]


def _hungarian(cost: list) -> list:
    """The assignment of each row to a distinct column at least total cost."""
    n, m = len(cost), len(cost[0])
    inf = float("inf")
    u, v, p, way = [0.0] * (n + 1), [0.0] * (m + 1), [0] * (m + 1), [0] * (m + 1)
    for i in range(1, n + 1):
        p[0], j0 = i, 0
        minv, used = [inf] * (m + 1), [False] * (m + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = p[j0], inf, 0
            for j in range(1, m + 1):
                if not used[j]:
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j], way[j] = cur, j0
                    if minv[j] < delta:
                        delta, j1 = minv[j], j
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break
    out = [0] * n
    for j in range(1, m + 1):
        if p[j]:
            out[p[j] - 1] = j - 1
    return out


def match(inventory: dict, alphabets: dict, turns: bool) -> dict:
    """For each alphabet, the matched pairs counted at the two levels, and their mean."""
    keys = sorted(inventory)
    glyphs = {k: _glyphs(inventory[k], turns) for k in keys}
    out = {}
    for name, letters in alphabets.items():
        if len(letters) < len(keys):
            continue
        sims = [[max(R.similarity(a, g) for a in glyphs[k]) for _, g in letters] for k in keys]
        pairs = _hungarian([[1 - s for s in row] for row in sims])
        matched = {k: (letters[pairs[i]][0], round(sims[i][pairs[i]], 4))
                   for i, k in enumerate(keys)}
        values = [m[1] for m in matched.values()]
        out[name] = {"at 0.95": sum(x >= IDENTICAL for x in values),
                     "at 0.90": sum(x >= NEAR for x in values),
                     "mean": round(sum(values) / len(values), 4), "pairs": matched}
    return out


def verdict(as_drawn: dict) -> dict:
    worst = max(as_drawn.items(),
                key=lambda kv: (kv[1]["at 0.95"], kv[1]["at 0.90"], kv[1]["mean"]))
    return {"no component near-identical to a listed letter":
            all(r["at 0.95"] == 0 for r in as_drawn.values()),
            "no alphabet near more than two components":
            all(r["at 0.90"] <= NEAR_ALLOWED for r in as_drawn.values()),
            "closest alphabet": worst[0]}


def nearest(inventory: dict, letters: list, k: int = 3) -> dict:
    out = {}
    for name in sorted(inventory):
        g = _glyphs(inventory[name], False)[0]
        scored = sorted(((R.similarity(g, h), cp, script) for cp, script, h in letters
                         if R.comparable(g, h)), reverse=True)[:k]
        out[name] = [{"code point": "U+%04X" % cp, "script": script, "similarity": round(s, 4)}
                     for s, cp, script in scored]
    return out


def current() -> tuple:
    """The specification, its components by their strokes of the pen, and the signs drawn
    whole as the drawing draws them alone and as the font draws them: each side with its
    mark and its foot, each wall with its tick, the number frame round one numeral, a
    word of four symbols, and each mark by itself."""
    with open(os.path.join(ROOT, "language", "writing.json"), encoding="utf-8") as f:
        spec = json.load(f)
    components = {c["symbol"]: c["pen strokes"] for c in spec["components"]}
    m, box = spec["metrics"], spec["lattice"]["box"]
    top, rule = -2, box[1] + m["rule depth"]
    signs = {}
    for unit, sign in spec["units"].items():
        mark = sign["mark"]
        base = [p[0] for p in mark if p[1] == 0]
        x = (min(base) + max(base)) // 2
        raised = [[px, py - 2] for px, py in mark]
        for opens, foot in (("opens", 4), ("closes", -4)):
            signs["%s side, %s" % (unit, opens)] = [raised, [[x, top], [x, rule],
                                                             [x + foot, rule]]]
        signs["%s mark" % unit] = [mark]
    signs["wall, opens"] = [[[2, top], [2, rule]], [[6, top], [6, rule]], [[6, top], [10, top]]]
    signs["wall, closes"] = [[[2, top], [2, rule]], [[6, top], [6, rule]],
                             [[-2, top], [2, top]]]
    half, h = m["frame"], box[1] // 2
    a, b = -m["frame space"] // 2, 4 * (box[0] + m["gap"]) - m["gap"] + m["frame space"] // 2
    tip = half // 3
    signs["number frame"] = [[[a, h - half], [b, h - half], [b + tip, h], [b, h + half],
                              [a, h + half], [a - tip, h], [a, h - half]]]
    return spec, components, signs


def failed(report: dict) -> bool:
    """Whether a comparison fails: a criterion the current components do not meet, or a
    control that meets every criterion, which would show the check unable to fail."""
    def met(label):
        return [v for v in report[label]["verdict"].values() if isinstance(v, bool)]
    return not all(met("current")) or all(met("core, the control"))


def main() -> int:
    spec, components, signs = current()
    alphabets = R.alphabets()
    listed = {k: v for k, v in alphabets.items()}
    report = {"sources": {"Unifont": "18.0.01", "UCD": "18.0.0",
                          "Hershey": "kamalmostafa/hershey-fonts 1356bf2f"},
              "criteria": {"near-identical": IDENTICAL, "near": NEAR,
                           "near allowed in one alphabet": NEAR_ALLOWED},
              "components": {c["symbol"]: c["unit strokes"] for c in spec["components"]}}
    for label, inventory in (("current", components), ("core, the control", CORE)):
        drawn, turned = match(inventory, listed, False), match(inventory, listed, True)
        report[label] = {"verdict": verdict(drawn), "as drawn": drawn, "turned": turned}
    letters = R.letters()
    report["current"]["nearest letters"] = nearest(components, letters)
    report["current"]["nearest symbols"] = nearest(components, R.symbols())
    report["current"]["verdict"]["no component near-identical to an encoded sign"] = all(
        near[0]["similarity"] < IDENTICAL for key in ("nearest letters", "nearest symbols")
        for near in report["current"][key].values())
    syntax = [(int(label[2:], 16), name.split(",")[0], g) for name, gs in alphabets.items()
              if name.startswith(("programming syntax", "circuit symbols")) for label, g in gs]
    report["signs drawn whole"] = {
        "nearest letters": nearest(signs, letters),
        "nearest symbols": nearest(signs, R.symbols()),
        "nearest programming syntax or circuit symbols": nearest(signs, syntax)}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
        f.write("\n")
    for label in ("current", "core, the control"):
        print(label, report[label]["verdict"])
    return 1 if failed(report) else 0


if __name__ == "__main__":
    sys.exit(main())
