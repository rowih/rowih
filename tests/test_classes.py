"""How often each grammatical class is used over the domain corpus
(specification/grammar.md#the-grammatical-classes): the report is what
`tools/count_classes.py` counts, the count reads the cases whose answer is known, and a
class is rarely used below 1 per cent of its units and not at it."""
import json
import os
import sys

from rowih import data
from rowih.generator import Generator
from rowih.notation import Reader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_corpus  # noqa: E402
import count_classes  # noqa: E402

with open(os.path.join(ROOT, "corpus", "reports", "classes.json"), encoding="utf-8") as f:
    STORED = json.load(f)


def test_the_report_is_what_the_count_gives():
    assert count_classes.count(count_classes.units()) == STORED


def test_every_class_of_the_grammar_is_counted_over_the_units_its_scope_gives():
    grammar = data.load("1.0").grammar
    assert set(STORED["classes"]) == {c["identifier"] for c in grammar["classes"]}
    assert (STORED["moves"], STORED["messages"]) == (2501, 2237)
    for c in grammar["classes"]:
        over = STORED["classes"][c["identifier"]]["counted over"]
        assert over == ("messages" if c["scope"] == "message" else "moves")


def built(notation: str, sender: int = 1, recipient: int = 2) -> str:
    lang = data.load()
    moves = Reader(lang).moves(build_corpus.substitute(notation, lang))
    return Generator(lang).message(moves, "normal expression", sender, [recipient],
                                   "1760000000", 1, first_entry=1)


def test_the_count_reads_the_cases_whose_answer_is_known():
    # an act word is read as the members of its expansion, and the classes' own words
    # alone do not show what it carries
    acceptance = built(
        "(move ACT-ACCEPTANCE SPEAKERS-OWN (names 1 1 ISSUE PROPOSAL OPEN) (situation meet "
        "(ACTOR (term (party 2))) (UNDERGOER (term (party 3)))))", sender=2, recipient=1)
    [read] = count_classes.move_classes(acceptance)
    [own] = count_classes.move_classes(acceptance, is_expanding=False)
    assert "g.force.outcome-of-a-resolution" in read
    assert "g.force.outcome-of-a-resolution" not in own
    assert "g.force.authority-claimed" in own
    # a negated situation uses polarity, and a basis left to its default is not used
    negated = built(
        "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation cold "
        "POLARITY.NEGATIVE (UNDERGOER (term water DEFINITE)))))")
    plain = built(
        "(move ASSERTED-POSITION (assertion (situation cold (UNDERGOER (term water "
        "DEFINITE)))))")
    [negative] = count_classes.move_classes(negated)
    [affirmative] = count_classes.move_classes(plain)
    assert {"g.situations-and-contents.polarity", "g.standing.basis"} <= negative
    assert "g.situations-and-contents.polarity" not in affirmative
    assert "g.standing.basis" not in affirmative


def test_a_class_is_rarely_used_below_one_per_cent_and_not_at_it():
    assert count_classes.is_rare(24, 2497) and not count_classes.is_rare(25, 2497)
    assert count_classes.is_rare(22, 2233) and not count_classes.is_rare(23, 2233)
    # exactly 1 per cent is not fewer than 1 per cent
    assert not count_classes.is_rare(1, 100)
    for c in STORED["classes"].values():
        total = STORED[c["counted over"]]
        assert c["is rarely used"] == count_classes.is_rare(c["units"], total)
