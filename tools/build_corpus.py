"""Write the conformance corpus from `corpus/source/conformance.json`: each message's
transliteration, as the generator writes it in normal expression, and its normal form.
Run from the repository root: `python3 tools/build_corpus.py`."""
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))

from rowih import data  # noqa: E402
from rowih.generator import Generator  # noqa: E402
from rowih.notation import Reader  # noqa: E402
from rowih.writer import Writer  # noqa: E402


SETS = ["conformance", "attitudes", "adversarial", "domains"]


def substitute(notation, lang, counting=False):
    """Fill the placeholders: QUOTED is a corpus message carried byte for byte, and
    QUOTED:item.k the message k of an earlier conformance item, which the build has
    written before it reaches this one; COMPOUND is a compound the release does not
    list. `counting` leaves a quoted message empty, for counting moves before the
    message quoted is written."""
    for name in re.findall(r'"QUOTED:([a-z0-9-]+\.[0-9]+)"', notation):
        if counting:
            notation = notation.replace('"QUOTED:%s"' % name, '""')
            continue
        quoted = open(os.path.join(ROOT, "corpus", "conformance", name + ".txt"),
                      encoding="utf-8").read()
        notation = notation.replace('"QUOTED:%s"' % name, json.dumps(quoted))
    if '"QUOTED"' in notation:
        quoted = open(os.path.join(ROOT, "corpus", "conformance", "s01-observed.1.txt"),
                      encoding="utf-8").read()
        notation = notation.replace('"QUOTED"', json.dumps(quoted))
    if "COMPOUND" in notation:
        root = {e["key"]: lang.items[i].form for i, e in lang.entries.items()
                if data.in_force(lang, e)}
        notation = notation.replace("COMPOUND", root["network"] + "i" + root["service"])
    for spec in re.findall(r'\(formed "([^"]+)"\)', notation):
        notation = notation.replace('(formed "%s")' % spec,
                                    '(unknown "%s")' % formed(spec, lang))
    for name in re.findall(r'"FORM:([^"]+)"', notation):
        notation = notation.replace('"FORM:%s"' % name, '"%s"' % form_of(name, lang))
    return notation


def form_of(name, lang):
    """The form of a word named by its identifier or, for an entry, its key."""
    if name in lang.items:
        return lang.items[name].form
    return next(lang.items[i].form for i, e in lang.entries.items()
                if e["key"] == name and data.in_force(lang, e))


def formed(spec, lang):
    """The form of a formation written by its parts: its stems joined by "~", each a
    root's key followed by its suffixes' keys after ".", so that `burn~memory` is a
    compound and `detect.agent` a derivation."""
    suffix = {it.name: f for f, it in lang.suffixes.items()}
    stems = []
    for stem in spec.split("~"):
        root, *suffixes = stem.split(".")
        stems.append(form_of(root, lang) + "".join(suffix[k] for k in suffixes))
    return "i".join(stems)


def corpus_key(participant) -> bytes:
    """The private key of a corpus participant, a test fixture published with the corpus:
    the SHA-256 of its name in the corpus."""
    return hashlib.sha256(("rowih corpus key %s" % participant).encode()).digest()


def language_for(m, lang):
    """The language a record's message is written in: the current release, or the
    language and lexicon release its `release` names, with the dialects its `dialects`
    names, each [number, version]."""
    release = m.get("release", {})
    dialects = tuple(tuple(d) for d in m.get("dialects", ()))
    if not release and not dialects:
        return lang
    return data.load(release.get("lexicon"), release.get("language"), dialects)


def _tupled(x):
    return tuple(_tupled(y) for y in x) if isinstance(x, list) else x


def protocol_message(m, lang) -> str:
    """A protocol message of a corpus record: identifier and first entry zero, its
    statement's kind and parts as the record states them."""
    w = Writer(lang)
    env = w.envelope(sender=m["sender"], recipients=tuple(m["recipients"]), time=m["time"],
                     identifier=0, first_entry=0)
    parts = [_tupled(p) for p in m["statement"]["parts"]]
    return w.message(env, [w.statement(m["statement"]["kind"], parts)])


def first_entries(item, lang):
    """The first entry each message of an exchange states: one more than the number of
    moves its sender wrote in the item's earlier messages, every move adding an entry
    (protocol 0.2), unless the record states its own."""
    counts, out = {}, []
    for m in item["messages"]:
        sender = str(m["sender"])
        if "statement" in m:
            # a protocol message adds no entry (protocol 0.3)
            out.append(0)
            continue
        first = m.get("first entry", counts.get(sender, 0) + 1)
        out.append(first)
        written = language_for(m, lang)
        counts[sender] = first - 1 + len(Reader(written).moves(
            substitute(m["notation"], written, counting=True)))
    return out


def main():
    for name in SETS:
        build(name)


def build(set_name):
    src = json.load(open(os.path.join(ROOT, "corpus", "source", set_name + ".json"),
                         encoding="utf-8"))
    gen = Generator()
    out_dir = os.path.join(ROOT, "corpus", set_name)
    os.makedirs(out_dir, exist_ok=True)
    for name in os.listdir(out_dir):
        os.remove(os.path.join(out_dir, name))
    count = 0
    for item in src["items"]:
        firsts = first_entries(item, gen.lang)
        for k, m in enumerate(item["messages"], 1):
            if "statement" in m:
                text = protocol_message(m, gen.lang)
            else:
                written = language_for(m, gen.lang)
                g = gen if written is gen.lang else Generator(written)
                moves = Reader(written).moves(substitute(m["notation"], written))
                text = g.message(moves, m.get("mode", "normal expression"), m["sender"],
                                 m["recipients"], m["time"], m["identifier"],
                                 semantic=m.get("semantic", False),
                                 first_entry=firsts[k - 1])
            if m.get("signed"):
                from rowih.authentication import sign
                text = sign(text, corpus_key(m["sender"]))
            with open(os.path.join(out_dir, "%s.%d.txt" % (item["id"], k)), "w",
                      encoding="utf-8") as f:
                f.write(text)
            count += 1
    print("%s: %d items, %d messages" % (set_name, len(src["items"]), count))


if __name__ == "__main__":
    main()
