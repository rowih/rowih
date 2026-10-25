"""Choose the component inventory: every connected set of unit strokes of the lattice
within the bounds of `writing_source.SEARCH`, taken up to the lattice's turns and mirrors;
each drawn in the orientation least like any letter of the reference alphabets, and kept
only if that orientation resembles none; and nineteen of them chosen to make the least
distance between any two, under every turn and mirror, as large as it can be, then the
mean distance, then the fewest strokes. A chosen component near-identical to any letter,
digit or symbol Unicode encodes (an arrow, say, which a reader would read as one) is set
aside and the choice made again, until none is.

The distance of two components is one minus the Jaccard similarity of their sets of unit
strokes, and the distance under turns and mirrors is the least distance between one and
any image of the other. The search is seeded, so that a run reproduces its result; it
writes `tools/component_search.json`, which `tools/build_writing.py` reads.

Usage: search_components.py [--check]
  --check   rerun the search and compare with the recorded result, changing nothing.
"""
from __future__ import annotations

import itertools
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reference_glyphs as R  # noqa: E402
import writing_source as W  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "component_search.json")
STROKES = W.unit_strokes()
INDEX = {s: i for i, s in enumerate(STROKES)}


def image(mask: int, f) -> int:
    out = 0
    for i, (a, b) in enumerate(STROKES):
        if mask >> i & 1:
            out |= 1 << INDEX[tuple(sorted((f(a), f(b))))]
    return out


def strokes_of(mask: int) -> list:
    return [STROKES[i] for i in range(len(STROKES)) if mask >> i & 1]


def connected(mask: int) -> bool:
    segs = strokes_of(mask)
    seen, stack = {0}, [0]
    while stack:
        i = stack.pop()
        for j, s in enumerate(segs):
            if j not in seen and set(segs[i]) & set(s):
                seen.add(j)
                stack.append(j)
    return len(seen) == len(segs)


def pen_strokes(mask: int) -> int:
    """The fewest strokes of the pen that draw the set: half its odd points, at least
    one (Euler)."""
    degree = {}
    for a, b in strokes_of(mask):
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1
    return max(1, sum(d % 2 for d in degree.values()) // 2)


def spans(mask: int) -> bool:
    pts = [p for s in strokes_of(mask) for p in s]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(ys) == 0 and max(ys) == W.BOX[1] and \
        max(xs) - min(xs) >= W.SEARCH["width share"] * W.BOX[0]


def distance(a: int, b: int) -> float:
    return 1 - (a & b).bit_count() / (a | b).bit_count()


def glyph(mask: int) -> R.Glyph:
    return R.Glyph(R.bitmap(R.sample([list(s) for s in strokes_of(mask)], 0.25)))


def orbits() -> dict:
    """Each orbit of admissible sets under the symmetries, keyed by its least member,
    with its distinct members."""
    lo, hi = W.SEARCH["strokes"]
    out = {}
    for size in range(lo, hi + 1):
        for combo in itertools.combinations(range(len(STROKES)), size):
            mask = sum(1 << i for i in combo)
            if pen_strokes(mask) > W.SEARCH["pen strokes"] or not connected(mask):
                continue
            members = sorted({image(mask, f) for f in W.SYMMETRIES})
            if members[0] in out or not any(spans(m) for m in members):
                continue
            out[members[0]] = members
    return out


def resemblance(alphabets: dict) -> list:
    """The reference glyphs as (whether the system is held to the stricter bound, glyph)."""
    strict = set(W.SEARCH["strict systems"])
    return [(name.split(",")[0] in strict, g) for name, glyphs in alphabets.items()
            for _, g in glyphs]


def admissible(all_orbits: dict, references: list) -> dict:
    """The orbits with an orientation that resembles no reference glyph, each with that
    orientation, the least like any, and its two resemblances."""
    bound, strict_bound = W.SEARCH["resemblance"], \
        W.SEARCH["resemblance, Latin, Greek and Cyrillic"]
    out = {}
    for key, members in all_orbits.items():
        best = None
        for mask in members:
            if not spans(mask):
                continue
            g = glyph(mask)
            f_all = f_strict = 0.0
            for strict, ref in references:
                if not R.comparable(g, ref):
                    continue
                f = R.similarity(g, ref)
                f_all = max(f_all, f)
                if strict:
                    f_strict = max(f_strict, f)
            if f_all < bound and f_strict < strict_bound and \
                    (best is None or (f_all, mask) < (best[1], best[0])):
                best = (mask, f_all, f_strict)
        if best is not None:
            out[key] = {"mask": best[0], "resemblance": best[1],
                        "resemblance, strict": best[2], "members": members}
    return out


def choose(cands: dict) -> tuple:
    """Nineteen orbits maximising the least distance, then making the fewest pairs as
    close as that, then the mean distance, then using the fewest strokes."""
    keys = sorted(cands)
    rng = random.Random(W.SEARCH["seed"])
    n = W.SEARCH["inventory"]
    memo = {}

    def d(a, b):
        k = (a, b) if a < b else (b, a)
        if k not in memo:
            memo[k] = min(distance(cands[a]["mask"], m) for m in cands[b]["members"])
        return memo[k]

    def value(sel):
        dists = [d(a, b) for a, b in itertools.combinations(sel, 2)]
        least = min(dists)
        return (least, -sum(1 for x in dists if x == least),
                round(sum(dists) / len(dists), 9),
                -sum(bin(cands[k]["mask"]).count("1") for k in sel))

    best, best_value = None, None
    for _ in range(W.SEARCH["restarts"]):
        sel = [rng.choice(keys)]
        while len(sel) < n:
            sel.append(max((k for k in keys if k not in sel),
                           key=lambda k: (min(d(k, s) for s in sel), rng.random())))
        val = value(sel)
        improved = True
        while improved:
            improved = False
            for i in range(n):
                others = sel[:i] + sel[i + 1:]
                for k in keys:
                    if k in sel or min(d(k, s) for s in others) < val[0]:
                        continue
                    trial = others[:i] + [k] + others[i:]
                    tv = value(trial)
                    if tv > val:
                        sel, val, improved = trial, tv, True
                        break
        if best_value is None or val > best_value:
            best, best_value = sorted(sel), val
    return best, best_value


def near_identical(cands: dict, chosen: list, signs: list) -> dict:
    """The chosen orbits whose drawn orientation is near-identical to an encoded letter,
    digit or symbol, each with the nearest as (similarity, code point)."""
    out = {}
    for k in chosen:
        g = glyph(cands[k]["mask"])
        best = max(((R.similarity(g, h), cp) for cp, _, h in signs if R.comparable(g, h)),
                   default=(0.0, 0))
        if best[0] >= W.SEARCH["near-identical"]:
            out[k] = best
    return out


def search() -> dict:
    start = time.time()
    all_orbits = orbits()
    cands = admissible(all_orbits, resemblance(R.alphabets()))
    admitted = len(cands)
    signs = R.letters() + R.symbols()
    excluded = []
    while True:
        chosen, val = choose(cands)
        near = near_identical(cands, chosen, signs)
        if not near:
            break
        for k, (sim, cp) in sorted(near.items()):
            excluded.append({"strokes": [[list(a), list(b)] for a, b in
                                         strokes_of(cands[k]["mask"])],
                             "near-identical to": "U+%04X" % cp, "similarity": round(sim, 4)})
            del cands[k]
    return {
        "lattice": [list(p) for p in W.LATTICE],
        "unit strokes": len(STROKES),
        "bounds": W.SEARCH,
        "orbits": len(all_orbits),
        "admissible": admitted,
        "set aside as near-identical to an encoded sign": excluded,
        "least distance": round(val[0], 6),
        "pairs at the least distance": -val[1],
        "mean distance": val[2],
        "unit strokes used": -val[3],
        "components": [
            {"strokes": [[list(a), list(b)] for a, b in strokes_of(cands[k]["mask"])],
             "pen strokes": pen_strokes(cands[k]["mask"]),
             "resemblance": round(cands[k]["resemblance"], 6),
             "resemblance, strict": round(cands[k]["resemblance, strict"], 6)}
            for k in chosen],
        "seconds": round(time.time() - start),
    }


def main(argv: list) -> int:
    result = search()
    if "--check" in argv:
        with open(OUT, encoding="utf-8") as f:
            recorded = json.load(f)
        same = recorded["components"] == result["components"]
        print("the search reproduces the recorded inventory" if same
              else "the search does not reproduce the recorded inventory")
        return 0 if same else 1
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("orbits %d, admissible %d, least distance %.3f in %d pairs, mean %.3f, %d s"
          % (result["orbits"], result["admissible"], result["least distance"],
             result["pairs at the least distance"], result["mean distance"],
             result["seconds"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
