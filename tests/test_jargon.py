"""The jargon of the eleven communities
(specification/dialects.md#dialects-registers-and-technical-terms): each community a
dialect whose terms are formed from core items and read by their composition, alike in
both implementations; and the conversational dialect
(specification/dialects.md#the-dialects-of-release-10)."""
import pytest

from rowih import api, data, formation
from rowih.generator import Generator
from rowih.lexer import segment
from rowih.notation import Reader

LANG = data.load()
GEN = Generator(LANG)
READ = Reader(LANG)


def test_the_jargon_is_formed_from_core_items_and_read_by_composition():
    """Eleven communities, each a dialect whose first release has terms that are
    formations of the lexicon's stems, and the conversational dialect beside them; the
    reader gives each term the composition its entry records, and no term is a word the
    lexicon lists or another dialect's form
    (specification/dialects.md#what-a-dialect-release-may-hold). Each term's scope is its
    dialect and the release that introduced it."""
    dialects = data.dialects()
    assert sorted(d["community"] for d in dialects.values()) == sorted([
        "mathematics", "programming", "machine learning", "robotics", "science",
        "philosophy", "linguistics", "security", "databases", "planning", "negotiation",
        "conversation"])
    forms = {}
    for d in dialects.values():
        assert len(d["terms"]) >= 5
        for term in d["terms"]:
            form = term["orthographic form"]
            assert form not in LANG.by_form and forms.get(form, d["dialect"]) == d["dialect"]
            forms[form] = d["dialect"]
            morphemes = segment(form, LANG)
            meaning = formation.compose(morphemes, LANG)
            assert meaning["definition"] == term["definition"], term["term"]
            assert meaning["sort"] == term["sort"]
            assert term["scope"] == {"dialect": d["dialect"],
                                     "version": term["version"]["introduced"]}
            stems = "".join(LANG.items[i].form for stem in term["formed from"]
                            for i in stem)
            assert form.replace("i", "") == stems.replace("i", "")
    assert {"deploy", "suite"} <= {t["term"] for t in dialects["programming"]["terms"]}
    assert api.version()["dialects"] == {name: d["version"] for name, d in dialects.items()}


def test_jargon_reads_alike_in_both_implementations():
    from rowih import parity
    texts = []
    for d in data.dialects().values():
        for term in d["terms"]:
            texts.append(GEN.message(READ.moves(
                "(move ASSERTED-POSITION (assertion OBSERVATION (situation detect (UNDERGOER "
                "(term (unknown \"%s\"))))))" % term["orthographic form"])))
    try:
        assert parity.compare_implementations(texts) == []
    except FileNotFoundError:
        pytest.skip("node is not installed")


def test_lookup_finds_a_term_by_its_name_and_its_form():
    deploy = next(t for t in data.dialects()["programming"]["terms"] if t["term"] == "deploy")
    for query in ("deploy", deploy["orthographic form"]):
        found = [i for i in api.lookup(query) if i.kind == "jargon"]
        assert [(i.identifier, i.form) for i in found] == [
            (deploy["machine identifier"], deploy["orthographic form"])]
