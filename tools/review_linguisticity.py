"""Prepare the independent reviewer's test of whether the language behaves like a
language, at the gate of version 1.0: a summary of the grammar, generated from the
canonical sources and from nothing written about the design, and a seeded sample of the
domain corpus, each message with its transliteration and each move with its morpheme gloss
and natural English.

The reviewer is given these two files and the four questions it states, and nothing else,
so that it answers without being told the intended answers. The reading is recorded as
given in `corpus/reports/linguisticity.json`.

Run from the repository root: `python3 tools/review_linguisticity.py <directory>` writes
the packet; `python3 tools/review_linguisticity.py record <directory> <reader> <date>`
records the reviewer's reading, `<directory>/reading.json`, made over that packet."""
import hashlib
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))

from rowih import data  # noqa: E402

OUT = os.path.join(ROOT, "corpus", "reports", "linguisticity.json")
# The rule the report is made under, stated with it.
RULE = ("an independent reviewer, given only a summary of the grammar generated from "
        "the canonical sources and a sample of sixty items of the domain corpus, "
        "answers four questions without being told the intended answers: whether the "
        "language behaves like a language, and whether it is merely a programming "
        "language, a cipher or an English relexification; a no to the first or a yes to "
        "any other is a departure, and each ground of an answer in part is ruled on")
SEED = 20261018
ITEMS_PER_DOMAIN = 5
QUESTIONS = (
    "Does the language actually behave like a language?",
    "Is it merely a programming language?",
    "Is it merely a cipher?",
    "Is it merely an English relexification?",
)
ANSWERS = ("yes", "no", "in part")
# the answer to each question that shows a departure from the language's design
DEPARTURE = ("no", "yes", "yes", "yes")


def summary(lang) -> str:
    """The grammar as its canonical sources state it: the phonology's symbols and word
    shapes, the productions, every class with its status, scope and members, the
    structural words and the suffixes."""
    p = lang.phonology
    out = ["# A summary of the grammar", "", "## Phonology", "",
           "Symbols: " + json.dumps(p["symbols"], ensure_ascii=False), "",
           "Syllables: " + json.dumps(p["syllables"], ensure_ascii=False), "",
           "Word shapes: " + json.dumps(p["word shapes"], ensure_ascii=False), "",
           "## Productions", "", "```", lang.grammar["productions"].strip(), "```", "",
           "## Grammatical classes", ""]
    for c in lang.grammar["classes"]:
        status = c["status"]["kind"]
        if status == "default":
            status += ", default %s" % c["status"]["default"]
        out.append("- **%s** (%s; %s; scope: %s; applies to %s): %s" % (
            c["name"], c["group"], status, c["scope"], c["applies to"],
            ", ".join(m["name"] for m in c["members"])))
    out += ["", "## Structural words", ""]
    out += ["- `%s` %s: %s" % (s["gloss"], s["name"], s["description"])
            for s in lang.grammar["structural words"]]
    out += ["", "## Suffixes", ""]
    out += ["- %s (%s)" % (s.name, s.gloss) for s in lang.suffixes.values()]
    return "\n".join(out) + "\n"


def sample() -> tuple:
    """Five items of each domain, drawn from a fixed seed, with every message's
    transliteration and each move's morpheme gloss and natural English."""
    with open(os.path.join(ROOT, "corpus", "source", "domains.json"), encoding="utf-8") as f:
        items = json.load(f)["items"]
    with open(os.path.join(ROOT, "corpus", "glossed", "domains.json"), encoding="utf-8") as f:
        glossed = json.load(f)
    rng = random.Random(SEED)
    domains = sorted({i["domain"] for i in items})
    chosen = [i for d in domains
              for i in rng.sample([i for i in items if i["domain"] == d], ITEMS_PER_DOMAIN)]
    out = ["# A sample of the corpus", ""]
    for n, item in enumerate(chosen, 1):
        out += ["## Item %d" % n, ""]
        for k in range(1, len(item["messages"]) + 1):
            record = glossed["%s.%d" % (item["id"], k)]
            out += ["Message %d:" % k, "", "    " + record["transliteration"].strip()
                    .replace("\n", "\n    "), ""]
            moves = record["moves"] if isinstance(record["moves"], list) else [record["moves"]]
            for m in moves:
                out += ["- gloss: " + m["morpheme gloss"],
                        "- English: " + m["natural English"], ""]
    return "\n".join(out), [i["id"] for i in chosen]


class ReadingRefused(ValueError):
    """A reading that does not answer the four questions as they were put, or a packet
    that is not the one this tool writes."""


def outcome(reading: dict) -> dict:
    """The outcome of the reading: a departure where the reviewer answers no to the first
    question or yes to any other, which blocks the release, and a finding where it answers
    in part, whose grounds are ruled on."""
    answers = reading.get("answers", [])
    if [a.get("question") for a in answers] != list(QUESTIONS):
        raise ReadingRefused("the reading does not answer the four questions verbatim")
    if any(a.get("answer") not in ANSWERS for a in answers):
        raise ReadingRefused("each answer is one of %s" % ", ".join(ANSWERS))
    departures = [a["question"] for a, d in zip(answers, DEPARTURE) if a["answer"] == d]
    return {"departures": departures,
            "findings": [a["question"] for a in answers if a["answer"] == "in part"],
            "blocks the release": bool(departures)}


def write_packet(directory: str) -> list:
    """The two files the reviewer is given, written into `directory`; the sample's items."""
    os.makedirs(directory, exist_ok=True)
    text, ids = sample()
    with open(os.path.join(directory, "grammar.md"), "w", encoding="utf-8") as f:
        f.write(summary(data.load()))
    with open(os.path.join(directory, "sample.md"), "w", encoding="utf-8") as f:
        f.write(text)
    return ids


def evaluate(directory: str, reader: str, date: str) -> dict:
    """The record of the reading in `directory/reading.json`, made over the packet beside
    it, which must be byte for byte what this tool writes at this commit, so that the
    record names the files that were read."""
    text, ids = sample()
    expected = {"grammar.md": summary(data.load()), "sample.md": text}
    packet = {}
    for name, content in expected.items():
        with open(os.path.join(directory, name), encoding="utf-8") as f:
            if f.read() != content:
                raise ReadingRefused("%s is not the file this tool writes" % name)
        packet[name] = hashlib.sha256(content.encode("utf-8")).hexdigest()
    with open(os.path.join(directory, "reading.json"), encoding="utf-8") as f:
        reading = json.load(f)
    return {"rule": RULE, "reader": reader, "read": date, "seed": SEED,
            "items": ids, "packet": packet, "questions": list(QUESTIONS),
            "reading": reading, "outcome": outcome(reading)}


def main():
    if sys.argv[1] == "record":
        out = evaluate(sys.argv[2], sys.argv[3], sys.argv[4])
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print(json.dumps(out["outcome"], indent=1))
        return
    ids = write_packet(sys.argv[1])
    print("%s: %d items" % (sys.argv[1], len(ids)))
    print(json.dumps(ids))


if __name__ == "__main__":
    main()
