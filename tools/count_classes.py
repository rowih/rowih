"""How often each grammatical class is used over the domain corpus, answering the question
whether each grammatical class is needed often, under a rule fixed before the count.

A move uses a class where a word the move writes, its count included, is a member of the
class, an act word counting as the members of its expansion, which the parser reads in its
place; the values a normal form supplies by default are not counted, so the count is of
the corpus as written. A class whose scope in the grammar is the message is counted over
the messages, a message using it where its envelope, statement or any move writes a
member; every other class is counted over the moves. A class is rarely used where fewer
than 1 per cent of the units it is counted over use it, and such a class is a candidate
for the lexicon in a later version, which the rule of change governs. The count of the
classes' own words, act words not read, is reported beside it, since the rule as first
fixed counted those alone.

Writes `corpus/reports/classes.json`. Run after `tools/build_corpus.py`."""
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))

from rowih import api, data  # noqa: E402

RELEASE = "1.0"
OUT = os.path.join(ROOT, "corpus", "reports", "classes.json")
RARE_PERCENT = 1        # a class used by fewer than this share of its units is rarely used


def members_of(words, lang, is_expanding: bool) -> set:
    """The members among the words, and those of each act word's expansion if asked."""
    out = set()
    for w in words:
        if w.item is None:
            continue
        if w.item.kind == "member":
            out.add(w.item.identifier)
        elif w.item.kind == "act" and is_expanding:
            out.update(lang.entries[w.item.identifier]["expansion"])
    return out


def is_rare(units: int, total: int) -> bool:
    """Whether fewer than RARE_PERCENT per cent of the units counted use a class."""
    return 100 * units < RARE_PERCENT * total


def read(text: str) -> tuple:
    """A message's envelope and statement words, and the words of each move."""
    a = api.parse(text)
    if a.diagnostics or a.message is None:
        raise ValueError("a message reads with diagnostics: %s"
                         % [d.code for d in a.diagnostics])
    outer = list(a.message.envelope.words)
    if a.message.statement is not None:
        outer += a.message.statement.words
    return outer, [m.words for m in a.message.moves]


def move_classes(text: str, is_expanding: bool = True) -> list:
    """The classes each move of a message uses."""
    lang = data.load(RELEASE)
    return [{lang.member_class[m] for m in members_of(words, lang, is_expanding)}
            for words in read(text)[1]]


def units() -> list:
    """Every message of the domain corpus as (domain, its envelope's and statement's
    words, the words of each move)."""
    with open(os.path.join(ROOT, "corpus", "source", "domains.json"), encoding="utf-8") as f:
        items = json.load(f)["items"]
    out = []
    for item in items:
        for k in range(1, len(item["messages"]) + 1):
            path = os.path.join(ROOT, "corpus", "domains", "%s.%d.txt" % (item["id"], k))
            with open(path, encoding="utf-8") as f:
                outer, moves = read(f.read())
            out.append((item["domain"], outer, moves))
    return out


def tally(messages: list, lang, is_expanding: bool) -> tuple:
    """The units that use each class and each member, and the units counted."""
    of_message = {c["identifier"] for c in lang.grammar["classes"]
                  if c["scope"] == "message"}
    classes = collections.Counter()
    members = collections.Counter()
    by_domain = collections.defaultdict(collections.Counter)
    totals = collections.Counter()
    for domain, outer, moves in messages:
        totals["messages"] += 1
        written = members_of(outer, lang, is_expanding).union(
            *(members_of(m, lang, is_expanding) for m in moves))
        found = {m for m in written if lang.member_class[m] in of_message}
        members.update(found)
        for cls in {lang.member_class[m] for m in found}:
            classes[cls] += 1
            by_domain[cls][domain] += 1
        for words in moves:
            totals["moves"] += 1
            found = {m for m in members_of(words, lang, is_expanding)
                     if lang.member_class[m] not in of_message}
            members.update(found)
            for cls in {lang.member_class[m] for m in found}:
                classes[cls] += 1
                by_domain[cls][domain] += 1
    return classes, members, by_domain, totals


def count(messages: list) -> dict:
    """Each class's use, counted over the units its scope gives it."""
    lang = data.load(RELEASE)
    classes, members, by_domain, totals = tally(messages, lang, True)
    own, _, _, _ = tally(messages, lang, False)
    out = {}
    for c in lang.grammar["classes"]:
        ident = c["identifier"]
        over = "messages" if c["scope"] == "message" else "moves"
        n = classes[ident]
        written = {m["identifier"]: members[m["identifier"]] for m in c["members"]}
        out[ident] = {
            "name": c["name"], "scope": c["scope"], "status": c["status"]["kind"],
            "counted over": over, "units": n,
            "per cent": round(100 * n / totals[over], 2),
            "is rarely used": is_rare(n, totals[over]),
            "units, own words only": own[ident],
            "domains": dict(sorted(by_domain[ident].items())),
            "members": written,
            "members never written": sorted(m for m, k in written.items() if k == 0)}
    return {"release": RELEASE, "moves": totals["moves"], "messages": totals["messages"],
            "rarely used below per cent": RARE_PERCENT, "classes": out}


def main():
    report = count(units())
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("classes: %d moves, %d messages" % (report["moves"], report["messages"]))
    for c in sorted(report["classes"].values(), key=lambda c: c["per cent"]):
        print("  %6.2f%% %5d (own words %5d) %-8s %-32s %s%s" % (
            c["per cent"], c["units"], c["units, own words only"], c["counted over"],
            c["name"], "RARELY USED " if c["is rarely used"] else "",
            "never: %d of %d" % (len(c["members never written"]), len(c["members"]))
            if c["members never written"] else ""))


if __name__ == "__main__":
    main()
