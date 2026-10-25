"""The sound of verse (specification/sounds-and-words.md#syllables-and-stress): a line's
measure from its words' syllables, every word stressed on its first, and its echoes of
onset, vowel and end."""
from rowih import api, data, verse

from corpus import messages

LANG = data.load()


def test_measure_marks_each_word_stressed_on_its_first_syllable():
    assert verse.measure(["napa", "kotepu", "rakut"], LANG) == "/x /xx /x"


def test_echoes_are_repetitions_among_stressed_syllables_and_line_ends():
    entry = verse.line(["napa", "neta", "rakut", "rapud"], LANG)
    assert entry["onset echoes"] == {"n": 2, "r": 2}
    assert entry["vowel echoes"] == {"a": 3}
    assert entry["end"] == "pud"
    assert entry["syllables"] == 8 and entry["stresses"] == 4


def test_the_poem_has_a_measure_and_its_stresses_are_its_words():
    """Every line of the corpus's poem has a measure whose stresses are its words and
    whose syllables are its words' syllables."""
    lines = [t for i, _, _, t in messages() if i == "e6-specification-and-poem"]
    assert lines
    for text in lines:
        a = api.parse(text)
        for entry, words in zip(verse.sound(a, LANG)["lines"], a.message.lines):
            assert entry["measure"].count("/") == entry["stresses"]
            assert entry["measure"].count("/") + entry["measure"].count("x") == \
                entry["syllables"]
