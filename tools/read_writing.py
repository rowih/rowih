"""A reading of the writing system by a reader new to it: strings of components drawn as
the language draws a word, at three sizes, read by a reader who has the key and nothing
else, and the readings scored against the strings and against the measure of the
components' distance.

The strings are drawn uniformly at random from a fixed seed, so that no reading can lean
on knowing a word, and `score` draws them again from the seed rather than reading them
from a file, so that no answer stands on disk beside the sheets. `sheets DIR` writes the
key and one sheet for each size into DIR; `score READING.json` scores a reader's
transcription, {size: [string, ...]}, and writes `corpus/reports/reading.json`.

Run from the repository root."""
import collections
import itertools
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))

from rowih import data, writing  # noqa: E402
from rowih import png as png_format  # noqa: E402
from rowih.drawing import Drawing, Path, _Line  # noqa: E402
from rowih.raster import rasterise  # noqa: E402

OUT = os.path.join(ROOT, "corpus", "reports", "reading.json")
# The rule the report is made under, stated with it.
RULE = ("a reader that has read none of the language's documents, given the key, reads "
        "twenty strings of five components drawn at random from a fixed seed at each of "
        "48, 24 and 12 pixels to a component; a size is legible to it where it reads at "
        "least 95 per cent of its components correctly, and the measure of distance is "
        "borne out where its confusions fall on the pairs at the least distance more "
        "often than those pairs' share of all pairs")
SEED = 20261018
ITEMS = 20              # strings on a sheet
LENGTH = 5              # components in a string
BLOCK = 5               # strings in a block, blocks set apart to keep the rows in order
SIZES = (4, 2, 1)       # pixels per unit: components 48, 24 and 12 pixels tall
ROW_GAP, BLOCK_GAP = 10, 22   # units between rows and between blocks
LEGIBLE = 0.95          # the share of components read correctly that makes a size legible
FEWEST_CONFUSIONS = 10  # below this, the confusions are too few to test the measure


def letters(lang) -> str:
    """The key's order: the consonants, then the vowels, as the phonology lists them."""
    return lang.consonants + lang.vowels


def strings(lang) -> dict:
    """Each size's strings, drawn from the seed; a different set for each size."""
    rng = random.Random(SEED)
    alphabet = letters(lang)
    return {size: ["".join(rng.choice(alphabet) for _ in range(LENGTH))
                   for _ in range(ITEMS)] for size in SIZES}


def _sheet(rows: list, lang, gap: int) -> Drawing:
    """Rows of clusters, each drawn as the language draws a word (`drawing._Line`)."""
    m, box = lang.writing["metrics"], lang.writing["lattice"]["box"]
    paths, width, y = [], 0, m["above"]
    for n, row in enumerate(rows):
        line = _Line(lang, False, False)
        for form in row:
            line.cluster(form, False, False)
            line.x += gap
        paths += [Path(tuple((px, py + y) for px, py in p.points), p.weight)
                  for p in line.paths]
        width = max(width, line.x + m["margin"])
        y += box[1] + (BLOCK_GAP if (n + 1) % BLOCK == 0 else ROW_GAP)
    return Drawing("display", width, y, paths, [], m["stroke"], m["hairline"])


def _png(d: Drawing, size: int) -> bytes:
    width, height, greys = rasterise(d, size)
    return png_format.encode(width, height, greys, "")


def sheets(directory: str):
    lang = data.load()
    os.makedirs(directory, exist_ok=True)
    alphabet = letters(lang)
    # the key: the consonants in one row and the vowels in another, each component apart
    split = len(lang.consonants)
    key = _sheet([list(alphabet[:split]), list(alphabet[split:])], lang, 12)
    with open(os.path.join(directory, "key.png"), "wb") as f:
        f.write(_png(key, max(SIZES)))
    for size, items in strings(lang).items():
        with open(os.path.join(directory, "sheet-%d.png" % (12 * size)), "wb") as f:
            f.write(_png(_sheet([[s] for s in items], lang, 0), size))
    print("key: %s, in the order %s"
          % (os.path.join(directory, "key.png"), " ".join(alphabet)))


def evaluate(reading: dict, lang) -> dict:
    """A reading scored against the strings drawn from the seed: each size's share of
    components read correctly and whether that makes it legible, the confusions, and the
    confusions against the measure."""
    sizes, confusions = {}, collections.Counter()
    for size, items in strings(lang).items():
        read = reading["sheets"][str(12 * size)]
        right = 0
        for t, r in zip(items, read):
            for a, b in zip(t, r.ljust(LENGTH, "?")):
                right += a == b
                if a != b and b in letters(lang):
                    confusions[a, b] += 1
        total = ITEMS * LENGTH
        sizes[str(12 * size)] = {"components": total, "read correctly": right,
                                 "share": round(right / total, 3),
                                 "is legible": right >= LEGIBLE * total,
                                 "unread": sum(r.count("?") for r in read)}
    return {"rule": RULE, "reader": reading["reader"],
            "read": reading["read"], "seed": SEED, "sizes": sizes,
            "confusions": [{"drawn": a, "read": b, "times": n,
                            "distance": round(writing.distance(a, b, lang), 3)}
                           for (a, b), n in sorted(confusions.items())],
            "measure": _measure(confusions, lang), "reading": reading["sheets"],
            "remarks": reading.get("remarks", "")}


def score(path: str):
    with open(path, encoding="utf-8") as f:
        out = evaluate(json.load(f), data.load())
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps({"sizes": out["sizes"], "measure": out["measure"]}, indent=1))


def _measure(confusions: collections.Counter, lang) -> dict:
    """The confusions against the measure: the share falling on the pairs at the least
    distance, beside those pairs' share of all pairs, and the mean distance of the
    confused pairs, beside that of all pairs."""
    pairs = {frozenset(p): writing.distance(*p, lang) for p in itertools.combinations(
        letters(lang), 2)}
    least = min(pairs.values())
    confused = [(pairs[frozenset(p)], n) for p, n in confusions.items()]
    count = sum(n for _, n in confused)
    out = {"pairs": len(pairs), "least distance": round(least, 3),
           "pairs at the least distance": sum(d == least for d in pairs.values()),
           "mean distance of all pairs": round(sum(pairs.values()) / len(pairs), 3),
           "confusions": count}
    if count:
        out["confusions at the least distance"] = sum(n for d, n in confused if d == least)
        out["mean distance of the confused pairs"] = round(sum(d * n for d, n in confused)
                                                           / count, 3)
    if count >= FEWEST_CONFUSIONS:
        out["is borne out"] = (out["confusions at the least distance"] / count
                               > out["pairs at the least distance"] / len(pairs)
                               and out["mean distance of the confused pairs"]
                               < out["mean distance of all pairs"])
    return out


if __name__ == "__main__":
    {"sheets": sheets, "score": score}[sys.argv[1]](sys.argv[2])
