"""The temporal network and the derived kinds of the times of a move
(specification/meaning.md#time): each relation can hold, a contradiction is refused at the
time that closes it, and tense and prediction are read from the bounds."""
import pytest

from rowih import api
from rowih.generator import Generator
from rowih.notation import Reader

GEN = Generator()
READER = Reader(GEN.lang)
RELATIONS = ["BEFORE", "AFTER", "MEETS", "MET-BY", "OVERLAPS", "OVERLAPPED-BY", "STARTS",
             "STARTED-BY", "DURING", "CONTAINS", "FINISHES", "FINISHED-BY", "EQUALS"]


def message(notation: str) -> str:
    return GEN.message(READER.moves(notation), "normal expression")


def codes(notation: str) -> list:
    return [d.code for d in api.parse(message(notation)).diagnostics]


def two(first: str, second: str, basis: str = "INFERENCE") -> str:
    return ("(move ASSERTED-POSITION (assertion %s (situation #1 break %s (UNDERGOER (term "
            "network))) (situation run %s (UNDERGOER (term service)))))" % (basis, first, second))


@pytest.mark.parametrize("relation", RELATIONS)
def test_each_relation_holds_between_two_intervals(relation):
    first = "(EVENT-TIME (60 MINUTE AGO) until (20 MINUTE AGO))"
    assert codes(two(first, "(EVENT-TIME %s (@1 EVENT-TIME))" % relation)) == []


@pytest.mark.parametrize("relation,holds", [("BEFORE", True), ("MEETS", True),
                                            ("STARTS", False), ("DURING", False),
                                            ("CONTAINS", True), ("FINISHED-BY", True)])
def test_a_relation_to_an_instant_holds_only_where_an_instant_can_stand(relation, holds):
    expected = [] if holds else ["d.checker.times-inconsistent"]
    assert codes(two("(EVENT-TIME 5 MINUTE AGO)",
                     "(EVENT-TIME %s (@1 EVENT-TIME))" % relation)) == expected


def test_a_relation_contradicting_clock_values_is_refused():
    assert codes(two("(EVENT-TIME 5 MINUTE AGO)", "(EVENT-TIME (30 MINUTE AGO) until "
                     "(20 MINUTE AGO))")) == []
    contradiction = ("(move ASSERTED-POSITION (assertion INFERENCE (situation #1 break "
                     "(EVENT-TIME 5 MINUTE AGO) (UNDERGOER (term network))) (situation run "
                     "(EVENT-TIME AFTER (@1 EVENT-TIME)) (REFERENCE-TIME 1 HOUR AGO) "
                     "(UNDERGOER (term service)))))")
    assert codes(contradiction) == ["d.checker.times-inconsistent"]


def test_a_duration_bounds_the_interval_it_measures():
    fits = "(EVENT-TIME AT-MOST 2 HOUR)"
    assert codes(two("(EVENT-TIME (3 HOUR AGO) until NOW)", fits)) == []
    nested = ("(move ASSERTED-POSITION (assertion INFERENCE (situation #1 break (EVENT-TIME "
              "(3 HOUR AGO) until NOW) (UNDERGOER (term network))) (situation run "
              "(EVENT-TIME AT-MOST 1 HOUR) (REFERENCE-TIME DURING (@1 EVENT-TIME)) "
              "(UNDERGOER (term service)))))")
    assert codes(nested) == []


def test_an_observation_cannot_precede_what_it_observes():
    seen = "(move ASSERTED-POSITION (assertion OBSERVATION %s (situation run %s (UNDERGOER " \
           "(term service)))))"
    assert codes(seen % ("(OBSERVATION-TIME 1 MINUTE AGO)", "(EVENT-TIME 5 MINUTE AGO)")) == []
    assert codes(seen % ("(OBSERVATION-TIME 10 MINUTE AGO)", "(EVENT-TIME 5 MINUTE AGO)")) \
        == ["d.checker.times-inconsistent"]
    inferred = seen.replace("OBSERVATION %s", "INFERENCE %s")
    assert codes(inferred % ("", "(EVENT-TIME 5 MINUTE HENCE)")) == []


def test_the_ordered_times_keep_their_own_diagnostic_and_are_not_reported_twice():
    text = ("(move ASSERTED-POSITION (assertion INFERENCE (OBSERVATION-TIME 1 MINUTE AGO) "
            "(INFERENCE-TIME 5 MINUTE AGO) (situation run (UNDERGOER (term service)))))")
    assert codes(text) == ["d.checker.ordered-times"]


def test_the_validity_interval_is_unmarked_and_every_other_interval_marked():
    until = GEN.lang.items["g.structure.until"].form
    validity = message("(move ASSERTED-POSITION (assertion RETRIEVAL (VALIDITY-INTERVAL NOW "
                       "(1 DAY HENCE)) (situation run (UNDERGOER (term service)))))")
    lasting = message("(move ASSERTED-POSITION (assertion RETRIEVAL (situation run (EVENT-TIME "
                      "NOW until (1 DAY HENCE)) (UNDERGOER (term service)))))")
    assert until not in validity.split()
    assert until in lasting.split()


def tenses(notation: str) -> list:
    return [x for x in api.analyze(message(notation))["times"][0]]


@pytest.mark.parametrize("time,tense", [("(EVENT-TIME 5 MINUTE AGO)", "past"),
                                        ("(EVENT-TIME 5 MINUTE HENCE)", "future"),
                                        ("(EVENT-TIME (5 MINUTE AGO) until (5 MINUTE HENCE))",
                                         "present"),
                                        ("(EVENT-TIME BEFORE (5 MINUTE HENCE))",
                                         "undetermined")])
def test_tense_is_what_every_placement_agrees_on(time, tense):
    out = tenses("(move ASSERTED-POSITION (assertion INFERENCE (situation run %s (UNDERGOER "
                 "(term service)))))" % time)
    assert [x["tense"] for x in out if x["unit"] == "situation"] == [tense]
    assert [x["prediction"] for x in out if x["unit"] == "assertion"] == [tense == "future"]


def test_a_supposed_situation_has_no_tense():
    out = tenses("(move SUPPOSITION (situation break (EVENT-TIME 1 HOUR HENCE) (UNDERGOER "
                 "(term network))))")
    assert out == []
