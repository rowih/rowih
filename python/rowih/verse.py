"""The sound of verse: a line's measure and its echoes, computed from its words.

Every word is stressed on its first syllable, so a line's measure is the pattern of its
words' lengths in syllables: each word a stressed syllable and the unstressed syllables
after it. An echo is a repetition among the stressed syllables of a line, of the
consonant that opens them (an onset echo) or of their vowel (a vowel echo), or between
the last syllables of lines (an end echo). The onset of a word is fixed by its class
(every root begins with *r*), so that an onset echo among words of one class is the
grammar's and carries no choice; the vowel echoes, the end echoes and the measure are
what a poem chooses.
"""
from __future__ import annotations

from collections import Counter

from .data import Language, load
from .speech import _speakable, syllables


def measure(forms: list, lang: Language | None = None) -> str:
    """The measure of a line: `/` for each stressed syllable and `x` for each unstressed
    one, the words divided by spaces."""
    lang = lang or load()
    return " ".join("/" + "x" * (len(syllables(f, lang)) - 1) for f in forms)


def line(forms: list, lang: Language | None = None) -> dict:
    lang = lang or load()
    stressed = [syllables(f, lang)[0] for f in forms]
    onsets = Counter(s[0] for s in stressed)
    vowels = Counter(s[1] for s in stressed)
    return {"measure": measure(forms, lang),
            "syllables": sum(len(syllables(f, lang)) for f in forms),
            "stresses": len(forms),
            "onset echoes": {k: v for k, v in sorted(onsets.items()) if v > 1},
            "vowel echoes": {k: v for k, v in sorted(vowels.items()) if v > 1},
            "end": syllables(forms[-1], lang)[-1] if forms else ""}


def sound(analysis, lang: Language | None = None) -> dict:
    """The sound of each move of a parsed message, and the end echoes between them."""
    lang = lang or load()
    if analysis.message is None:
        return {"lines": [], "end echoes": {}}
    lines = [line([w.form for w in words if _speakable(w, lang)], lang)
             for words in analysis.message.lines]
    ends = Counter(entry["end"] for entry in lines)
    return {"lines": lines, "end echoes": {k: v for k, v in sorted(ends.items()) if v > 1}}
