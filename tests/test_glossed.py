"""The fully glossed corpus (specification/conformance.md#the-conformance-suite): every
stored record is what the toolchain writes from its message's text, every message of a
set has one, and each move's lines are the named lines of a gloss."""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import gloss_corpus  # noqa: E402

SETS = [s for s in gloss_corpus.SETS
        if os.path.exists(os.path.join(ROOT, "corpus", "glossed", s + ".json"))]


def stored(name):
    with open(os.path.join(ROOT, "corpus", "glossed", name + ".json"), encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("name", SETS)
def test_every_glossed_record_is_what_the_toolchain_writes(name):
    assert json.loads(json.dumps(gloss_corpus.gloss_set(name))) == stored(name)


def test_every_move_has_the_lines_of_its_gloss():
    lines = {"native", "transliteration", "morpheme gloss", "literal semantic form",
             "natural English", "grammatical analysis"}
    for name in SETS:
        for key, record in stored(name).items():
            for move in record["moves"]:
                assert set(move) == lines, (name, key)
                assert move["native"] and move["morpheme gloss"], (name, key)
