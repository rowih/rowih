"""The fields of a lexicon entry that the corpus gives
(specification/lexicon.md#entries-and-their-identifiers): each entry's collocations,
measured over the domain corpus, and its examples, items of that corpus. Every message is
read by the toolchain, and a move uses an entry where it reads a word as that entry: a
root in its own sense or a conventional sense its frame selects, a listed derivation, each
morpheme of a formation and the technical term a formation is in a dialect the message
names, a compressed form, a unit of measure, the act word, the politeness word, the
diction and the relation words of its head, and each idiom it reads. A marked idiom's own
words belong to the idiom, and only what fills its slots counts as the speaker's use of a
root.

The collocations of an entry are the roots that share its moves, ranked by log Dice
(14 + log2(2 f(xy) / (f(x) + f(y))), f counting moves); its examples are the items that
use it, the first in each domain before any second.

Run after `tools/gloss_corpus.py`; writes `lexicon/usage/1.0.json`, which a reader of
lexicon 1.0 or later reads over the entries."""
import collections
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))

from rowih import api, data, idioms, lexicon_checks, senses  # noqa: E402
from rowih.lexer import segment  # noqa: E402
from rowih.normal import Normaliser  # noqa: E402

RELEASE = "1.0"
COLLOCATIONS = 8        # the collocates stated for an entry
EXAMPLES = 5            # the examples stated for an entry
SKIPPED = ("value", "party", "ref", "same", "slot", "time", "wall", "dialect")


class Reading:
    """The entries the moves of one message use, read under the releases it names."""

    def __init__(self, text: str):
        a = api.parse(text)
        if a.diagnostics or a.message is None:
            raise ValueError("a corpus message reads with diagnostics: %s"
                             % [d.code for d in a.diagnostics])
        under = a.read_under
        self.lang = data.load(under["version"], under["language"], tuple(under["dialects"]))
        self.norm = Normaliser(self.lang)
        releases = data.dialect_releases()
        self.terms = {t["orthographic form"]: t["machine identifier"]
                      for d in under["dialects"] for t in releases[tuple(d)]["terms"]
                      if not t["version"]["deprecated"]}
        self.moves = []
        for t, social in zip(a.moves, a.social):
            out = set()
            out.update(x for x in (social["act"], social["politeness"], social["diction"])
                       if x)
            out.update(t.get("relations", []))
            out.update(social["idioms"])
            named = {n["name"]: n for n in _units(t["constituents"])
                     if n.get("name") is not None}
            for node in t["constituents"]:
                self.walk(node, named, out)
            self.moves.append(out)

    def walk(self, node, named: dict, out: set):
        kind = node.get("kind")
        if kind in idioms.UNITS:
            if idioms.marked(node):
                _, bindings = idioms.resolve(node, self.norm)
                for bound in (bindings or {}).values():
                    self.walk(bound, named, out)
                return
            head = senses.head_word(node)
            sense = senses.sense_of(node, self.lang, named)
            for p in node["parts"]:
                if p is head and sense:
                    out.add(sense)
                else:
                    self.walk(p, named, out)
        elif kind == "word":
            self.word(node, out)
        elif kind == "quantity":
            if (node.get("unit") or "").startswith(("lx.", "dl.")):
                out.add(node["unit"])
        elif kind == "filler":
            self.walk(node["filler"], named, out)
        elif kind == "readings":
            for r in node["readings"]:
                self.walk(r, named, out)
        elif kind == "idiom":
            out.add(node["entry"])
        elif kind not in SKIPPED:
            raise ValueError("a constituent the measure does not read: %s" % kind)

    def word(self, node: dict, out: set):
        if node.get("entry"):
            out.add(node["entry"])
            return
        if node.get("status") != "formation":
            raise ValueError("a corpus word the release does not hold: %s" % node["form"])
        # the linker of a compound is a bare symbol, not an entry
        out.update(m.identifier for m in segment(node["form"], self.lang)
                   if getattr(m, "identifier", "").startswith("lx."))
        if node["form"] in self.terms:
            out.add(self.terms[node["form"]])


def _units(constituents):
    for node in _nodes(constituents):
        if node.get("kind") in idioms.UNITS:
            yield node


def _nodes(x):
    if isinstance(x, dict):
        yield x
        for v in x.values():
            yield from _nodes(v)
    elif isinstance(x, list):
        for v in x:
            yield from _nodes(v)


def occurrences() -> list:
    """Every move of the domain corpus as (item, domain, message, move, entries used)."""
    with open(os.path.join(ROOT, "corpus", "source", "domains.json"), encoding="utf-8") as f:
        items = json.load(f)["items"]
    out = []
    for item in items:
        for k in range(1, len(item["messages"]) + 1):
            path = os.path.join(ROOT, "corpus", "domains", "%s.%d.txt" % (item["id"], k))
            with open(path, encoding="utf-8") as f:
                reading = Reading(f.read())
            for j, used in enumerate(reading.moves, 1):
                out.append((item["id"], item["domain"], k, j, used))
    return out


def roots(lang) -> set:
    return {i for i, e in lang.entries.items()
            if e["grammatical category"] in lexicon_checks.ROOT_CATEGORIES
            and "synonym of" not in e and data.in_force(lang, e)}


def measure(moves: list) -> dict:
    """The collocations and examples of every entry the moves use."""
    lang = data.load(RELEASE)
    core = roots(lang)
    count = collections.Counter()
    pairs = collections.Counter()
    for *_, used in moves:
        count.update(used)
        present = sorted(used & core)
        for x in used:
            for y in present:
                if y != x:
                    pairs[x, y] += 1
    collocates = collections.defaultdict(list)
    for (x, y), both in pairs.items():
        score = 14 + math.log2(2 * both / (count[x] + count[y]))
        collocates[x].append((-round(score, 2), -both, y))
    examples = collections.defaultdict(list)
    for item, domain, k, j, used in moves:
        for x in used:
            examples[x].append((item, domain, k, j))
    out = {}
    for x in sorted(count):
        out[x] = {"collocations": [{"entry": y, "log dice": -s, "moves": -n}
                                   for s, n, y in sorted(collocates[x])[:COLLOCATIONS]],
                  "examples": [{"item": item, "message": k, "move": j}
                               for item, _, k, j in _spread(examples[x])[:EXAMPLES]]}
    return out


def _spread(found: list) -> list:
    """The items an entry occurs in, the first move of each, the first item of every
    domain before any domain's second."""
    seen, by_domain = set(), collections.OrderedDict()
    for item, domain, k, j in found:
        if item not in seen:
            seen.add(item)
            by_domain.setdefault(domain, []).append((item, domain, k, j))
    out, rank = [], 0
    while any(len(v) > rank for v in by_domain.values()):
        out += [v[rank] for v in by_domain.values() if len(v) > rank]
        rank += 1
    return out


def expected(lang) -> dict:
    """Every entry the corpus is to use, by kind: the roots, the register synonyms, the
    suffixes, the listed derivations, the act words, the idioms and conventional
    expressions, the senses, the politeness words and dictions, and the technical terms
    and compressed forms of each dialect's newest release, none deprecated."""
    out = collections.defaultdict(set)
    kinds = {"suffix": "suffixes", "derivation": "derivations", "act": "act words",
             "idiom": "idioms", "sense": "senses"}
    core = roots(lang)
    for ident, e in lang.entries.items():
        category = e["grammatical category"]
        if ident in core:
            out["roots"].add(ident)
        elif "synonym of" in e:
            out["register synonyms"].add(ident)
        elif category in ("politeness word", "diction"):
            out[category + "s"].add(ident)
        elif lang.items[ident].kind in kinds:
            out[kinds[lang.items[ident].kind]].add(ident)
    for d in data.dialects().values():
        out["technical terms"].update(t["machine identifier"] for t in d["terms"]
                                      if not t["version"]["deprecated"])
        out["compressed forms"].update(f["machine identifier"] for f in d.get("forms", [])
                                       if not f["version"]["deprecated"])
    return out


def unused(usage: dict) -> dict:
    """Every entry the corpus is to use and does not, by kind."""
    return {kind: sorted(ids - set(usage))
            for kind, ids in sorted(expected(data.load(RELEASE)).items())}


def main():
    usage = measure(occurrences())
    os.makedirs(os.path.join(ROOT, "lexicon", "usage"), exist_ok=True)
    with open(os.path.join(ROOT, "lexicon", "usage", RELEASE + ".json"), "w",
              encoding="utf-8") as f:
        json.dump(usage, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    lang = data.load(RELEASE)
    print("usage: %d entries measured" % len(usage))
    for kind, ids in unused(usage).items():
        if ids:
            names = [lang.entries[i]["key"] if i in lang.entries else i for i in ids]
            print("  %s unused: %d: %s" % (kind, len(ids), ", ".join(names)))


if __name__ == "__main__":
    main()
