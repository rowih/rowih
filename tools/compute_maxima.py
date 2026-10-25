"""Fix the registers' maxima from the conformance corpus (see
specification/protocol.md#the-maxima): the protocol register's are the least values that
admit every corpus item, and no register declares a smaller nesting maximum. Writes them
into `language/protocol.json`. Run from the repository root after
`tools/build_corpus.py`."""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))

from rowih import api, data  # noqa: E402


def depth(node, d=0):
    if isinstance(node, dict):
        here = d + 1 if node.get("kind") in ("assertion", "situation", "term") else d
        return max([here] + [depth(v, here) for v in node.values()])
    if isinstance(node, list):
        return max([d] + [depth(x, d) for x in node])
    return d


def walk(node, kind):
    if isinstance(node, dict):
        if node.get("kind") == kind:
            yield node
        for v in node.values():
            yield from walk(v, kind)
    elif isinstance(node, list):
        for x in node:
            yield from walk(x, kind)


def main():
    path = os.path.join(ROOT, "language", "protocol.json")
    proto = json.load(open(path, encoding="utf-8"))
    prior = proto.pop("maxima", None)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(proto, f, ensure_ascii=False, indent=1)
        f.write("\n")
    data._load_release.cache_clear()
    texts = []
    for d in ("conformance", "attitudes", "adversarial"):
        texts += [open(p, encoding="utf-8").read()
                  for p in sorted(glob.glob(os.path.join(ROOT, "corpus", d, "*.txt")))]
    from rowih.generator import Generator
    from rowih.notation import Reader
    gen = Generator()
    amb = json.load(open(os.path.join(ROOT, "corpus", "source", "ambiguity.json"),
                         encoding="utf-8"))["items"]
    reader = Reader(gen.lang)
    for item in amb:
        if item.get("refusal"):
            continue
        for key in ("expression", "disambiguation"):
            for mode in ("normal expression", "full explicitness"):
                texts.append(gen.message(reader.moves(item[key]), mode))
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from build_corpus import language_for, substitute
    for d in ("conformance", "attitudes", "adversarial"):
        src = json.load(open(os.path.join(ROOT, "corpus", "source", d + ".json"),
                             encoding="utf-8"))
        for item in src["items"]:
            for m in item["messages"]:
                if "statement" in m:
                    continue   # a protocol message carries no moves
                # in the release and with the dialects the record names
                written = language_for(m, gen.lang)
                g = gen if written is gen.lang else Generator(written)
                texts.append(g.message(Reader(written).moves(substitute(m["notation"],
                                                                         written)),
                                       "full explicitness",
                                       m["sender"], m["recipients"], m["time"],
                                       m["identifier"]))
    nest = words = readings = links = expansion = 0
    for text in texts:
        a = api.parse(text)
        assert all(x.code == "d.lexer.unknown-word" for x in a.diagnostics), \
            [x.as_text() for x in a.diagnostics]
        words = max(words, len(a.words))
        # an idiom read by its entry is an expansion one level deep, and no expansion
        # holds another, which the lexicon checks require
        if any(s["idioms"] for s in a.social):
            expansion = 1
        for t in a.moves:
            nest = max(nest, depth(t["constituents"]))
            for r in walk(t, "readings"):
                readings = max(readings, len(r["readings"]))
            for u in walk(t, "assertion"):
                links = max(links, sum(1 for p in u["parts"] if p["kind"] == "filler"
                                       and p["role"].startswith("g.standing.provenance-link.")))
    proto["maxima"] = {"nesting": nest, "message words": words, "readings": max(readings, 2),
                       "provenance links": links, "definition expansion": expansion,
                       "rule": "the least values that admit every item of the conformance "
                               "corpus, the attitude items, the adversarial messages and the ambiguity "
                               "test set, in normal "
                               "expression and in full explicitness; every register declares "
                               "these in protocol %s" % proto["version"]}
    # The maxima are a declaration of the protocol version: a release that keeps the
    # version keeps them, since a reader applies them to every message it reads, those of
    # the earlier releases it reads among them, and a corpus that exceeds them needs a new
    # protocol version.
    if prior is not None and prior["rule"].rsplit("protocol ", 1)[-1] == proto["version"]:
        exceeded = [k for k, v in proto["maxima"].items() if k != "rule" and v > prior[k]]
        if exceeded:
            raise SystemExit("the corpus exceeds protocol %s's maxima %s; a new protocol "
                             "version is needed" % (proto["version"], exceeded))
        proto["maxima"] = prior
    with open(path, "w", encoding="utf-8") as f:
        json.dump(proto, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(proto["maxima"])


if __name__ == "__main__":
    main()
