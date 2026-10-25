"""The irregular cells of lexicon 1.0
(specification/lexicon.md#listed-derivations-and-compounds): five suppletive cells, one in
each of five roots' paradigms; every irregularity has a documented reason, a lexicon entry
and a test, and the check finds each planted omission; a root states the irregular cell of
its paradigm; an irregular word reads as its entry and has the normal form of the
formation it stands for, in both implementations; and a further suffix builds on the
regular stem."""
import copy
import os
import sys

from rowih import api, data, lexicon_checks, parity
from rowih.generator import Generator
from rowih.notation import Reader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_corpus  # noqa: E402

LANG = data.load("1.0")
IRREGULAR = {i: e for i, e in LANG.entries.items() if "irregular" in e}
BY_KEY = {e["key"]: i for i, e in LANG.entries.items()}


def test_lexicon_1_has_five_suppletive_cells_one_in_each_paradigm():
    cells = {(LANG.entries[e["formed from"][0]]["key"], LANG.entries[e["formed from"][1]]["key"])
             : e["key"] for e in IRREGULAR.values()}
    assert cells == {("send", "undergoer"): "consignment", ("read", "potential"): "legible",
                     ("store", "place"): "depot", ("break", "nominalisation"): "fracture",
                     ("connect", "privative"): "apart"}
    for e in IRREGULAR.values():
        assert e["irregular"]["kind"] == "suppletion"
        assert e["version"]["introduced"] == "1.0"
    assert not any("irregular" in e for e in data.load("0.7").entries.values())


def planted(ident: str, **changes) -> data.Language:
    lang = copy.copy(LANG)
    lang.entries = dict(LANG.entries)
    lang.entries[ident] = dict(copy.deepcopy(LANG.entries[ident]), **changes)
    return lang


def test_every_irregularity_has_a_documented_reason_an_entry_and_a_test():
    assert lexicon_checks.check_irregularity(LANG) == []
    legible = BY_KEY["legible"]
    stated = LANG.entries[legible]["irregular"]
    for lang in (planted(legible, irregular=dict(stated, reason="taste")),
                 planted(legible, **{"constructed history": "it was always so"}),
                 planted(legible, irregular=dict(stated, **{"regular form": "rukaw"}))):
        assert ("irregularity-undocumented", legible) in lexicon_checks.check_irregularity(lang)
    # a listed derivation whose form departs from its parts' without saying why
    examiner = BY_KEY["examiner"]
    assert ("irregularity-undocumented", examiner) in lexicon_checks.check_irregularity(
        planted(examiner, **{"orthographic form": "ruhok"}))
    # an irregular word means what its root and suffix compose, and nothing else
    assert ("irregularity-misread", legible) in lexicon_checks.check_irregularity(
        planted(legible, definition="be easy to read"))


def test_a_root_states_the_irregular_cell_of_its_paradigm():
    send = LANG.entries[BY_KEY["send"]]
    cells = {LANG.entries[d["suffix"]]["key"]: d for d in send["derivational behaviour"]}
    consignment = LANG.entries[BY_KEY["consignment"]]
    assert cells["undergoer"]["form"] == consignment["orthographic form"]
    assert cells["undergoer"]["listed"] == consignment["machine identifier"]
    assert cells["undergoer"]["regular form"] == consignment["irregular"]["regular form"] \
        == send["orthographic form"] + LANG.entries[BY_KEY["undergoer"]]["orthographic form"]
    # every other cell of the paradigm is regular
    for key, d in cells.items():
        if key != "undergoer":
            assert "regular form" not in d
            assert d["form"] == send["orthographic form"] + LANG.entries[d["suffix"]][
                "orthographic form"]


def built(word: str) -> str:
    lang = data.load()
    notation = ("(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation %s "
                "(UNDERGOER (term document DEFINITE)))))" % word)
    moves = Reader(lang).moves(build_corpus.substitute(notation, lang))
    return Generator(lang).message(moves, "normal expression", 1, [2], "1760000000", 1,
                                   first_entry=1)


def test_an_irregular_word_has_the_normal_form_of_its_regular_formation():
    irregular, regular = built("legible"), built('(formed "read.potential")')
    a, b = api.parse(irregular), api.parse(regular)
    assert a.diagnostics == [] and b.diagnostics == []
    [word] = [w for w in a.words if w.form == "rukaw"]
    assert word.item.identifier == BY_KEY["legible"]
    assert [w.kind for w in b.words if w.form == "reyuduwot"] == ["formation"]
    assert a.normal_text == b.normal_text
    assert api.check_values(irregular)["semantic"] == api.check_values(regular)["semantic"]
    # the TypeScript implementation writes the same records
    typescript = parity.typescript_records([irregular, regular])
    assert typescript == [parity.record_line(irregular), parity.record_line(regular)]


def test_a_further_suffix_builds_on_the_regular_stem():
    # what cannot be read is the privative of the regular stem; the irregular word takes
    # no suffix, since it is no root
    privative = LANG.items[BY_KEY["privative"]].form
    regular = LANG.entries[BY_KEY["legible"]]["irregular"]["regular form"]
    a = api.parse(built('(formed "read.potential.privative")'))
    assert a.diagnostics == []
    assert [w.kind for w in a.words if w.form == regular + privative] == ["formation"]
    stacked = built("legible").replace("rukaw", "rukaw" + privative)
    assert "d.lexer.unknown-word" in {d.code for d in api.parse(stacked).diagnostics}
