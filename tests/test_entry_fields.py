"""The fields a release asks of every lexical item
(specification/lexicon.md#entries-and-their-identifiers), stated for each of lexicon 1.0's
500 roots: the derivations the rules of formation give it, its synonyms and antonyms, each
stated by both entries, and its related concepts, each read in both directions. A released
entry stays as released: its own release reads it unchanged, and lexicon 1.0 states its
fields beside it."""
import copy
import json
import os

from rowih import data, formation, lexicon_checks as lc

LANG = data.load()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def roots(lang):
    return {e["key"]: e for e in lang.entries.values()
            if e["grammatical category"] in lc.ROOT_CATEGORIES and "synonym of" not in e}


def test_every_root_of_lexicon_1_states_its_fields():
    assert len(roots(LANG)) == 500
    assert lc.check_fields(LANG) == []
    assert all(e["derivational behaviour"] and e["related concepts"]
               for e in roots(LANG).values())


def test_a_released_entry_is_read_as_released_by_its_own_release():
    ident = roots(LANG)["run"]["machine identifier"]
    with open(os.path.join(ROOT, "lexicon", "roots", ident + ".json"), encoding="utf-8") as f:
        on_disk = json.load(f)
    assert on_disk["related concepts"] == [] and on_disk["derivational behaviour"] == []
    assert data.load("0.7").entries[ident]["related concepts"] == []
    assert {r["relation"] for r in LANG.entries[ident]["related concepts"]} == {"involves"}


def test_the_derivations_stated_are_those_formation_gives():
    suffixes = {i: e for i, e in LANG.entries.items()
                if e["grammatical category"] == "derivational suffix"}
    for e in roots(LANG).values():
        stated = {d["suffix"]: d for d in e["derivational behaviour"]}
        for i, s in suffixes.items():
            given = formation.derive(formation.of_entry(e), s)
            assert (given is None) == (i not in stated), (e["key"], s["key"])
            if given is not None:
                assert stated[i]["definition"] == given["definition"]
                assert stated[i]["sort"] == given["sort"]
    think = roots(LANG)["think"]
    assert "agent" in {d["mechanism"] for d in think["derivational behaviour"]}


def test_antonyms_and_near_synonyms_are_stated_by_both_entries():
    r = roots(LANG)
    small = r["small"]["machine identifier"]
    assert {"entry": small} in r["big"]["antonyms"]
    near = [s for s in r["protect"]["synonyms"] if s["dimension"] == "near"]
    assert [s["entry"] for s in near] == [r["defend"]["machine identifier"]]
    assert near[0]["difference"]
    service = r["service"]
    assert {s["dimension"] for s in service["synonyms"]} == {"register"}


def test_a_relation_stated_one_way_is_found():
    planted = copy.copy(LANG)
    planted.entries = dict(LANG.entries)
    big = roots(LANG)["big"]["machine identifier"]
    planted.entries[big] = dict(LANG.entries[big], antonyms=[])
    assert ("relation-not-mutual", "%s antonyms %s" % (
        roots(LANG)["small"]["machine identifier"], big)) in lc.check_fields(planted)


def test_a_root_without_a_related_concept_is_found():
    planted = copy.copy(LANG)
    planted.entries = dict(LANG.entries)
    bird = roots(LANG)["bird"]["machine identifier"]
    planted.entries[bird] = dict(LANG.entries[bird], **{"related concepts": []})
    codes = {code for code, _ in lc.check_fields(planted)}
    assert "root-without-related-concept" in codes
    # and the animal that names it as a kind now states a relation bird does not return
    assert "relation-not-mutual" in codes
