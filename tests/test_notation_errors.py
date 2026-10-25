"""The notation as a writer's input (specification/notation.md#tokens): a text that does
not read as the notation raises `NotationError` and nothing else, so that a writer, a
command or a server can report it as an error of its input; and a text that reads is one
the generator can write."""
import copy
import json
import random

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from rowih import api, data
from rowih.generator import Generator
from rowih.notation import NotationError, Reader

from corpus import in_current_release, items, moves_of

LANG = data.load()
READER = Reader(LANG)
GEN = Generator(LANG)
GOOD = ("(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (OBSERVATION-TIME 5 MINUTE "
        "AGO) (situation run POLARITY.NEGATIVE (UNDERGOER (term service DEFINITE)))))")


@pytest.mark.parametrize("text,message", [
    ("(", "not closed"),
    ("(move ASSERTED-POSITION", "not closed"),
    ("()", "a move is"),
    ("(move ())", "empty list"),
    ("(move (authority))", "authority"),
    ("(move (deadline))", "deadline"),
    ("(move (names))", "names"),
    ("(move (names 1))", "names"),
    ("(move (names 1 1 part))", "part"),
    ("(move (names 1 1 part x))", "part"),
    ("(move (names-message 1))", "names-message"),
    ("(move (names-serial 1 2))", "names-serial"),
    ("(move (mentions-serial))", "mentions-serial"),
    ("(move (names x 1))", "not a number"),
    ("(move ASSERTED-POSITION (quote))", "quote"),
    ("(move ASSERTED-POSITION (quote abc))", "quote"),
    ("(move ASSERTED-POSITION (data \"text/plain\"))", "data"),
    ("(move ASSERTED-POSITION (idiom))", "idiom"),
    ("(move ASSERTED-POSITION (readings))", "readings"),
    ("(move ASSERTED-POSITION (slot x))", "slot"),
    ("(move ASSERTED-POSITION (situation @x))", "@x"),
    ("(move ASSERTED-POSITION (situation #x run))", "#x"),
    ("(move ASSERTED-POSITION (situation run (ACTOR)))", "ACTOR"),
    ("(move ASSERTED-POSITION (situation run (ACTOR (term x) (term y))))", "ACTOR"),
    ("(move ASSERTED-POSITION (situation run (ACTOR (term (party)))))", "party"),
    ("(move ASSERTED-POSITION (situation run (ACTOR (term (party x)))))", "not a number"),
    ("(move ASSERTED-POSITION (situation run (term (dialect))))", "dialect"),
    ("(move ASSERTED-POSITION (situation run (term (unknown))))", "unknown"),
    ("(move ASSERTED-POSITION (assertion (q)))", "quantity"),
    ("(move ASSERTED-POSITION (assertion (situation run (q abc))))", "not a number"),
    ("(move ASSERTED-POSITION (assertion (q 2 PER)))", "PER"),
    ("(move ASSERTED-POSITION (assertion (OBSERVATION-TIME)))", "time"),
    ("(move ASSERTED-POSITION (assertion (VALIDITY-INTERVAL NOW)))", "VALIDITY-INTERVAL"),
    ("(move ASSERTED-POSITION (assertion (VALIDITY-INTERVAL NOW until (2 DAY HENCE))))",
     "VALIDITY-INTERVAL"),
    ("(move ASSERTED-POSITION (assertion (OBSERVATION-TIME 5 MINUTE AGO NOW)))", "time"),
    ("(move ASSERTED-POSITION (assertion (OBSERVATION-TIME BEFORE)))", "BEFORE"),
    ("(move ASSERTED-POSITION (assertion (OBSERVATION-TIME x)))", "not a number"),
    ("(move ASSERTED-POSITION (situation run (EVENT-TIME 2 PER)))", "PER"),
    ("(move ASSERTED-POSITION (situation run (EVENT-TIME until NOW)))", "until"),
    ("(move ASSERTED-POSITION (situation run \"abc\"))", "string"),
    ("(move ASSERTED-POSITION (situation run ((term x))))", "list"),
])
def test_a_text_that_does_not_read_raises_a_notation_error_saying_why(text, message):
    with pytest.raises(NotationError, match=message):
        READER.moves(text)


def test_a_number_may_use_every_symbol_the_numerals_spell():
    for number in ("2", "0.8", "-1.5", "3/4", "1e-3", "2~4"):
        moves = READER.moves("(move ASSERTED-POSITION (assertion (q EXACTLY %s) (situation "
                             "run (UNDERGOER (term service DEFINITE)))))" % number)
        assert moves[0]["constituents"][0]["parts"][0]["number"] == number


def test_the_notation_of_every_corpus_move_still_reads():
    from rowih.notation import Printer
    printer = Printer(LANG)
    count = 0
    for item in items():
        for m in item["messages"]:
            if not in_current_release(m):
                continue
            for t in moves_of(m):
                again = READER.moves(printer.move(t))
                assert printer.move(again[0]) == printer.move(t)
                count += 1
    assert count > 300


# Random texts over the notation's own vocabulary reach every branch of the reader with
# lists too short, too long, or of the wrong kind; random characters reach the tokenizer.
VOCABULARY = sorted(READER.by_gloss)[::7] + sorted(READER.entry_by_key)[::40] + [
    "move", "assertion", "situation", "term", "q", "party", "names", "mentions",
    "names-message", "names-serial", "mentions-serial", "deadline", "authority", "quote",
    "example", "data", "readings", "idiom", "slot", "unknown", "dialect", "EVENT-TIME",
    "OBSERVATION-TIME", "VALIDITY-INTERVAL", "ACTOR", "CONTENT", "NOW", "AGO", "HENCE",
    "until", "PER", "part", "#1", "@1", "@x", "1", "0.5", "-1", "3/4", "2~4", "x",
    "MINUTE", '"abc"', '""']


def _text(tree) -> str:
    """A tree as `sexp` reads it, written back: a string token is a pair ("str", text)."""
    if isinstance(tree, tuple):
        return json.dumps(tree[1], ensure_ascii=False)
    return "(" + " ".join(_text(x) for x in tree) + ")" if isinstance(tree, list) else tree


TREES = st.recursive(st.sampled_from(VOCABULARY),
                     lambda children: st.lists(children, max_size=4), max_leaves=24)


def _reads_or_refuses(text: str) -> None:
    try:
        moves = READER.moves(text)
    except NotationError:
        return
    out = GEN.generate(moves)
    assert out["transliteration"]


@settings(max_examples=400, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(st.lists(TREES, max_size=4))
def test_any_tree_of_the_vocabulary_reads_or_raises_only_a_notation_error(parts):
    _reads_or_refuses(_text(["move"] + parts))


@settings(max_examples=200, deadline=None)
@given(st.text(max_size=60))
def test_any_text_reads_or_raises_only_a_notation_error(text):
    _reads_or_refuses(text)


def _mutate(tree, rng):
    """A corpus move's notation with one list shortened, emptied or given a stray atom."""
    lists = []

    def walk(x):
        if isinstance(x, list):
            lists.append(x)
            for y in x:
                walk(y)
    walk(tree)
    target = rng.choice(lists[1:] or lists)
    roll = rng.random()
    if roll < 0.4 and len(target) > 1:
        del target[rng.randrange(1, len(target)):]
    elif roll < 0.6:
        target.insert(rng.randrange(1, len(target) + 1), rng.choice(VOCABULARY))
    elif roll < 0.8 and len(target) > 1:
        target.pop(rng.randrange(1, len(target)))
    else:
        target[:] = target[:1]
    return tree


def test_near_misses_of_the_corpus_read_or_raise_only_a_notation_error():
    from rowih.notation import Printer, sexp
    printer = Printer(LANG)
    rng = random.Random(20261024)
    texts = [printer.move(t) for item in items() for m in item["messages"]
             if in_current_release(m) for t in moves_of(m)]
    for text in rng.sample(texts, 150):
        for _ in range(4):
            tree = _mutate(copy.deepcopy(sexp(text)[0]), rng)
            _reads_or_refuses(_text(tree))


def test_a_reading_text_is_written():
    out = api.generate(GOOD)
    assert api.parse(out["transliteration"]).diagnostics == []
