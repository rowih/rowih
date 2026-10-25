"""The corpus items the failures require
(specification/conformance.md#the-conformance-suite), each with the outcome expected of
it."""
import itertools

from rowih import api, data, writing
from rowih.generator import Generator
from rowih.notation import Reader

GEN = Generator()
READ = Reader(GEN.lang)


def test_inert_message_cut_between_its_moves_shows_the_limit():
    """A message of inert moves carries no integrity check value, so a cut between two of
    its moves leaves a well-formed message: the limit the message shows, which the
    channel's next serial reveals
    (specification/protocol.md#channels-acknowledgement-and-repair)."""
    text = GEN.message(READ.moves(
        "(move ASSERTED-POSITION (assertion OBSERVATION (situation run (UNDERGOER (term "
        "service))))) (move ASSERTED-POSITION (assertion INFERENCE (situation break "
        "(UNDERGOER (term network)))))"), integrity=False)
    lines = text.split("\n")
    cut = "\n".join(lines[:2]) + "\n"
    a = api.parse(cut)
    assert a.diagnostics == [] and len(a.moves) == 1
    whole = GEN.message(READ.moves(
        "(move ASSERTED-POSITION (assertion OBSERVATION (situation run (UNDERGOER (term "
        "service))))) (move ASSERTED-POSITION (assertion INFERENCE (situation break "
        "(UNDERGOER (term network)))))"))
    cut_checked = "\n".join(whole.split("\n")[:2]) + "\n"
    assert "d.check-values.integrity-mismatch" in [d.code for d in api.parse(cut_checked).diagnostics]


def _critical_pairs():
    lang = data.load()
    for cls in lang.grammar["classes"]:
        if cls["critical dimension"]:
            for a, b in itertools.combinations(cls["members"], 2):
                yield cls["identifier"], a["form"], b["form"]


def test_closest_critical_forms_are_distinct_to_the_eye():
    """The pair of forms that differ in a critical dimension and resemble each other
    most still differ in at least two components, each far from the other under the
    declared visual measure, turns and mirrors included (`writing/confusable-forms`;
    specification/writing-system.md#the-components)."""
    letters = data.load().letters
    closest_component = min(writing.distance(a, b)
                            for a, b in itertools.permutations(letters, 2))
    assert closest_component >= 0.6
    pairs = sorted(_critical_pairs(), key=lambda p: writing.form_distance(p[1], p[2]))
    cls, x, y = pairs[0]
    assert writing.form_distance(x, y) >= 2 * closest_component
    assert sum(1 for a, b in zip(x, y) if a != b) >= 2


def test_dialect_form_in_a_message_naming_no_dialect_is_unknown_vocabulary():
    """A form of a dialect the message does not name has no expansion the hearer can find:
    it is kept opaque and reported, never read under a dialect the hearer happens to hold."""
    text = GEN.message(READ.moves(
        "(move ASSERTED-POSITION (assertion OBSERVATION (situation (unknown \"rokiwomab\") "
        "(UNDERGOER (term service)))))"))
    a = api.parse(text)
    assert [d.code for d in a.diagnostics] == ["d.lexer.unknown-word"]
    word = next(w for w in a.words if w.form == "rokiwomab")
    assert word.kind == "unknown"
    part = a.normal[0]["constituents"][0]["parts"]
    assert any(p.get("kind") == "situation" and any(
        q.get("status") == "unknown" for q in p["parts"]) for p in part)
