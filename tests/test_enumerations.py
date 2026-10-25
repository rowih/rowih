"""The enumerations (specification/conformance.md#the-enumerations): every proper prefix
rejected, every routine transport transformation survived or detected, fuzzed input
raising nothing, and single edits sampled here and run in full by
`tools/run_enumerations.py`. Each enumeration is first shown to find a planted defect."""
import os

import pytest

from rowih import api, conformance as C, data, parser
from rowih.generator import Generator
from rowih.notation import Reader

from corpus import ROOT, messages

MESSAGES = messages()
TEXTS = [t for _, _, _, t in MESSAGES]
IDS = ["%s.%d" % (i, k) for i, k, _, _ in MESSAGES]


@pytest.mark.parametrize("text", TEXTS, ids=IDS)
def test_every_proper_prefix_is_rejected(text):
    assert C.enumerate_prefixes(text) == []
    assert C.enumerate_prefixes(text, native=True) == []


@pytest.mark.parametrize("name", sorted(C.TRANSFORMATIONS))
def test_transport_transformation_is_survived_or_detected(name):
    outcomes = {C.transform(t, name) for t in TEXTS}
    assert "changed" not in outcomes


@pytest.mark.parametrize("name", sorted(C.TRANSFORMATIONS))
def test_transport_transformation_of_the_native_form_is_survived_or_detected(name):
    """The native digital form is a transmitted encoding too (`inv.transport-stable`;
    specification/writing-system.md#the-native-digital-form)."""
    outcomes = {C.transform(t, name, native=True) for t in TEXTS}
    assert "changed" not in outcomes


def test_no_character_level_transformation_changes_a_character_of_an_alphabet():
    """Unicode normalisation, Markdown, typographic quotes and HTML escaping leave every
    letter, code point and space of both transmitted encodings as it is, so that they
    cannot change a message silently (`inv.transport-stable`)."""
    assert C.alphabet_changes() == []


def test_fuzzed_input_raises_nothing():
    assert C.fuzz(seed=39, size=3000, corpus=TEXTS) == []


@pytest.mark.parametrize("item_id", ["s06-request.1", "x01-cancel.2", "d08-tool-use.1"])
def test_single_symbol_edits_change_no_critical_dimension(item_id):
    text = TEXTS[IDS.index(item_id)]
    result = C.enumerate_single_edits(text, "symbol", canonical=False)
    assert result["silent"][True] == []
    assert result["counts"][True]["rejected"] > 0


@pytest.mark.parametrize("text", TEXTS[:12], ids=IDS[:12])
def test_word_deletion_and_duplication_change_no_critical_dimension(text):
    """With the integrity check value verified no deletion or duplication of a word is
    silent. With it ignored, the moves still protect themselves by their counts; the
    envelope, which has no count, relies on the check value, and a duplicated or deleted
    digit the weighted check word misses passes there and only there."""
    original = api.parse(text)
    for edit, cand in C.word_edits(text, []):
        res = C.judge(original, cand, canonical=False)
        assert res[True] != "silent", edit
        if res[False] == "silent":
            assert edit[1] == 0, edit


def _message(notation, **kw):
    gen = Generator()
    return gen.message(Reader(gen.lang).moves(notation), **kw)


def test_single_edit_enumeration_finds_a_planted_defect(monkeypatch):
    """With the move check word planted to compute zero for every move, in writer and
    reader alike, a substitution of one strength word for another passes unless the
    integrity check value is verified: the enumeration reports it silent."""
    monkeypatch.setattr(parser, "move_check", lambda body, lang: 0)
    text = _message("(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation run "
                    "(UNDERGOER (term service)))))")
    original = api.parse(text)
    assert original.diagnostics == []
    lang = data.load()
    cand = text.replace(" %s " % lang.form_of("g.standing.strength.certain"),
                        " %s " % lang.form_of("g.standing.strength.probable"))
    res = C.judge(original, cand, canonical=False)
    assert res[False] == "silent" and res[True] == "rejected"


def test_truncation_enumeration_finds_a_planted_defect():
    """A message of inert moves without the integrity check value, cut between its
    moves, survives: the failure-mode analysis's recorded limit, which the enumeration
    must be able to see."""
    text = _message("(move ASSERTED-POSITION (assertion OBSERVATION (situation run (UNDERGOER "
                    "(term service))))) (move ASSERTED-POSITION (assertion INFERENCE (situation "
                    "break (UNDERGOER (term network)))))", integrity=False)
    assert C.enumerate_prefixes(text) != []


def test_transport_enumeration_finds_a_planted_defect():
    """A transformation that deletes a word changes the analysis or is detected; one
    that removes a whole move from a message without the check value is 'changed'."""
    text = _message("(move ASSERTED-POSITION (assertion OBSERVATION (situation run (UNDERGOER "
                    "(term service))))) (move ASSERTED-POSITION (assertion INFERENCE (situation "
                    "break (UNDERGOER (term network)))))", integrity=False)
    C.TRANSFORMATIONS["planted-drop-last-line"] = lambda t: "".join(
        line + "\n" for line in t.split("\n")[:-2])
    try:
        assert C.transform(text, "planted-drop-last-line") == "changed"
    finally:
        del C.TRANSFORMATIONS["planted-drop-last-line"]


def test_word_substitution_of_a_critical_word_is_rejected_without_the_check_value():
    """In a message without the integrity check value, replacing one strength word by
    another is caught by the move check word alone (`inv.single-edit-detected`)."""
    text = _message("(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation run "
                    "(UNDERGOER (term service)))))", integrity=False)
    lang = data.load()
    for other in ("probable", "speculative", "uncertain", "highly-probable"):
        cand = text.replace(" %s " % lang.form_of("g.standing.strength.certain"),
                            " %s " % lang.form_of("g.standing.strength." + other))
        assert [d.code for d in api.parse(cand).diagnostics] == ["d.parser.move-check-mismatch"]


@pytest.mark.parametrize("path,original,replacements", [
    ("conformance/d01-simple-fact.1.txt", "g.situations-and-contents.connective.condition",
     ["g.ambiguity-and-figures.figures-relation.target-content",
      "g.ambiguity-and-figures.figures-relation.stands-for"]),
    ("conformance/s05-claims-disagree.2.txt", "lx.000093",
     ["g.ambiguity-and-figures.precision-bound-declaration.precision-bound"]),
])
def test_substitutions_found_over_the_adversarial_set_are_caught_by_the_move_check(
        path, original, replacements):
    """The enumeration with the integrity check value ignored found these whole-word
    substitutions passing; the words now carry critical codes (`inv.single-edit-detected`)."""
    lang = data.load()
    with open(os.path.join(ROOT, "corpus", path),
              encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")
    words = lines[1].split(" ")
    k = words.index(lang.form_of(original))
    for other in replacements:
        edited = lines[:1] + [" ".join(words[:k] + [lang.form_of(other)] + words[k + 1:])] \
            + lines[2:]
        codes = [d.code for d in api.parse("\n".join(edited)).diagnostics]
        assert [c for c in codes if c not in C.ICV_CODES] == ["d.parser.move-check-mismatch"]


def test_wrapping_at_word_boundaries_changes_nothing():
    """Line breaks are layout: a message wrapped between words reads the same
    (`writing/layout-carries-meaning`)."""
    assert {C.transform(t, "wrap-20") for t in TEXTS} == {"same"}


def test_an_export_is_never_read_as_the_language():
    """A JSON export is a view: the parser rejects it (`machine/export-parsed-back`)."""
    for text in TEXTS[:5]:
        export, _ = api.convert(text, "json")
        assert api.parse(export).diagnostics != []


# ------------------------------------------------------------- a run divided among jobs
def _tool():
    import sys
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import run_enumerations
    return run_enumerations


def test_the_shares_of_a_run_are_disjoint_and_together_the_run():
    tool, jobs = _tool(), list(range(23))
    parts = [tool.share(jobs, "%d/4" % k) for k in range(1, 5)]
    assert sorted(j for part in parts for j in part) == jobs
    assert max(map(len, parts)) - min(map(len, parts)) <= 1
    assert tool.share(jobs, None) == jobs


@pytest.mark.parametrize("shard", ["0/4", "5/4", "1/0", "a/4", "1-4", ""])
def test_a_malformed_share_is_refused(shard):
    with pytest.raises(ValueError):
        _tool().share([1, 2, 3], shard)


def test_the_share_is_read_from_anywhere_on_the_command_line():
    tool = _tool()
    assert tool.arguments(["word", "--shard", "2/3", "4"]) == (["word", "4"], "2/3")
    assert tool.arguments(["both"]) == (["both"], None)
    with pytest.raises(ValueError):
        tool.arguments(["both", "--shard"])


def test_a_run_fails_on_an_exception_or_a_silent_edit_where_the_value_is_verified():
    tool = _tool()
    clean = {"rejected": 9, "unchanged": 1, "silent": 0}
    totals = {"word": {"transliteration/verified": dict(clean),
                       "transliteration/ignored": dict(clean, silent=3)}}
    assert not tool.failed(totals, [])
    assert tool.failed(totals, [["a.1.txt", "word", [0], "ValueError()"]])
    totals["word"]["transliteration/verified"]["silent"] = 1
    assert tool.failed(totals, [])
