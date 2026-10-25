"""The fully glossed corpus: for every message of every corpus set, its native writing and
its transliteration, and for each move the five lines with its grammatical analysis: the
move as written, the class computed for it and its social and textual component. Every
record is written by the toolchain from the message's text, read under the releases the
message names, so that `tests/test_glossed.py` regenerates each and compares it.

Run after `tools/build_corpus.py`; writes `corpus/glossed/<set>.json`."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))

from rowih import api, data  # noqa: E402
from rowih.english import English  # noqa: E402
from rowih.generator import morpheme_gloss  # noqa: E402
from rowih.notation import Printer  # noqa: E402
from rowih.serialise import text_to_native  # noqa: E402

SETS = ["conformance", "attitudes", "adversarial", "domains"]


def record(text: str) -> dict:
    """The glossed record of one message's text."""
    a = api.parse(text)
    under = a.read_under
    # a protocol message, or one whose releases the reader lacks, is read under the
    # current release, as the reader reads its envelope
    lang = data.load(under["version"], under["language"], tuple(under["dialects"])) \
        if "version" in under else data.load()
    printer = Printer(lang)
    out = {"transliteration": text, "native": text_to_native(text, lang),
           "diagnostics": [d.code for d in a.diagnostics], "moves": []}
    if a.message is None:
        return out
    english = English(lang, a.message.envelope.sender.text)
    for m, t, n, cls, social in zip(a.message.moves, a.moves, a.normal, a.classes,
                                    a.social):
        words = " ".join(w.form for w in m.words)
        out["moves"].append({
            "native": text_to_native(words, lang),
            "transliteration": words,
            "morpheme gloss": " ".join(morpheme_gloss(w, lang) for w in m.words),
            "literal semantic form": printer.move(n),
            "natural English": english.move(n),
            "grammatical analysis": {
                "as written": printer.move(t),
                "class": sorted(k for k, v in cls.items() if v),
                "social and textual component": social}})
    out["formations"] = a.formations
    return out


def gloss_set(name: str) -> dict:
    """Every message of the set, by item and index, in the order of the set's source."""
    path = os.path.join(ROOT, "corpus", "source", name + ".json")
    with open(path, encoding="utf-8") as f:
        source = json.load(f)
    out = {}
    for item in source["items"]:
        for k in range(1, len(item["messages"]) + 1):
            name_k = "%s.%d" % (item["id"], k)
            with open(os.path.join(ROOT, "corpus", name, name_k + ".txt"),
                      encoding="utf-8") as f:
                out[name_k] = record(f.read())
    return out


def main():
    os.makedirs(os.path.join(ROOT, "corpus", "glossed"), exist_ok=True)
    for name in SETS:
        if not os.path.exists(os.path.join(ROOT, "corpus", "source", name + ".json")):
            continue
        glossed = gloss_set(name)
        with open(os.path.join(ROOT, "corpus", "glossed", name + ".json"), "w",
                  encoding="utf-8") as f:
            json.dump(glossed, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write("\n")
        print("%s: %d messages glossed" % (name, len(glossed)))


if __name__ == "__main__":
    main()
