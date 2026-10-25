"""The two implementations agree (specification/conformance.md#the-two-implementations;
`compare_implementations`): over every corpus message and every item of the negative
corpus, the Python and the TypeScript parser and renderer, each run twice, write the same
record byte for byte, so that every negative item draws the same diagnostics in both."""
import glob
import json
import os

from rowih import api, parity

from corpus import CORPUS_DIRECTORIES, ROOT, corpus_paths

PATHS = corpus_paths()
TEXTS = [open(p, encoding="utf-8").read() for p in PATHS]


def test_the_corpus_is_the_whole_corpus():
    # every set of messages is read here but the domain corpus, which tests/test_domains.py
    # compares across the implementations on its own
    sets = {os.path.basename(os.path.dirname(p)) for p in glob.glob(
        os.path.join(ROOT, "corpus", "*", "*.txt"))}
    assert sets == set(CORPUS_DIRECTORIES) | {"domains"}
    assert {os.path.basename(os.path.dirname(p)) for p in PATHS} == set(CORPUS_DIRECTORIES)
    assert len(PATHS) == 512


def test_both_implementations_write_the_same_records():
    disagreements = parity.compare_implementations(TEXTS, every_view=True)
    assert [(os.path.basename(PATHS[i]), which) for i, which, _, _ in disagreements] == []


def test_negative_items_draw_their_codes_in_typescript():
    negative = [(p, t) for p, t in zip(PATHS, TEXTS) if "/negative/" in p]
    items = {i["id"]: i["code"] for i in json.load(open(os.path.join(
        ROOT, "corpus", "source", "negative.json"), encoding="utf-8"))["items"]}
    lines = parity.typescript_records([t for _, t in negative])
    for (path, _), line in zip(negative, lines):
        codes = [d["code"] for d in json.loads(line)["diagnostics"]]
        assert items[os.path.basename(path)[:-4]] in codes, path


def test_the_comparison_finds_a_planted_disagreement(monkeypatch):
    original = api.render

    def render(text, fmt="svg", has_font=False, form="display", contrast="normal"):
        out, diags = original(text, fmt, has_font, form, contrast)
        return (out.replace("<polyline", "<polygon", 1), diags) if fmt == "svg" else (out, diags)
    monkeypatch.setattr(api, "render", render)
    disagreements = parity.compare_implementations(TEXTS[:3])
    assert [which for _, which, _, _ in disagreements] == ["python and typescript"] * 3


def test_both_implementations_give_the_same_version_and_lookups():
    from rowih import data
    # a member, a root, an act word, an idiom, an English word, a form, an identifier, and
    # the term, form and compressed form of dialects
    terms = ["asserted position", "run", "act-question", "memory open", "service", "rudin",
             "lx.000001", "nothing at all"]
    for d in data.dialects().values():
        terms.append(d["terms"][0]["term"])
        terms.append(d["terms"][0]["orthographic form"])
        if d.get("forms"):
            terms.append(d["forms"][0]["term"])
    python = parity.interface_records(terms)
    assert python["version"]["dialects"] and any(
        item["kind"] in ("jargon", "dialect") for items in python["lookups"].values()
        for item in items)
    assert parity.typescript_interface(terms) == python
