"""The spoken form (specification/sounds-and-words.md#the-spoken-form): speech is an
encoding, one phoneme to each symbol, every word beginning with a consonant and stressed
on its first syllable.

A word divides into syllables of a consonant and a vowel, the last taking a final
consonant (`language/phonology.json`). A line is spoken in the prosody its register's
setting names (flat, neutral, expressive or measured), the envelope flat; prosody is fixed
by the register and the words and carries nothing of its own, so that a hearer who loses
it loses no word: the shapes of the words divide a stream of phonemes without stresses
or pauses into its words in one way only (`decode`). Embedded material is not in the
language and is not spoken; its place is marked by a pause, which is the spoken form's
one loss.
"""
from __future__ import annotations

from .data import Language, load
from .lexer import LINKER, SUFFIX_FIRST

STRESS = "ˈ"
EMBEDDED = "(embedded material)"


def syllables(form: str, lang: Language) -> list:
    """The syllables of a word: consonant and vowel, the last closed by a final consonant."""
    out, i = [], 0
    while i < len(form):
        syl = form[i:i + 2]
        i += 2
        if i == len(form) - 1 and form[i] in lang.consonants:
            syl += form[i]
            i += 1
        out.append(syl)
    return out


def ipa(form: str, lang: Language | None = None) -> str:
    """A word in the IPA, stressed on its first syllable, its syllables divided by dots."""
    lang = lang or load()
    table = {s["letter"]: s["ipa"] for s in lang.phonology["symbols"]}
    return STRESS + ".".join("".join(table[c] for c in syl) for syl in syllables(form, lang))


def espeak(form: str, lang: Language | None = None) -> str:
    """A word as espeak-ng phoneme input, its first syllable stressed."""
    lang = lang or load()
    table = {s["letter"]: s["espeak"] for s in lang.phonology["symbols"]}
    return "'" + "".join(table[c] for c in form)


def _speakable(w, lang: Language) -> bool:
    return w.kind != "payload" and w.form != "" and all(c in lang.code_points for c in w.form)


def spoken(analysis, lang: Language | None = None) -> list:
    """Each line of a parsed message as it is spoken: its prosody, its words in the IPA
    and as espeak-ng input, embedded material marked by its pause."""
    lang = lang or load()
    if analysis.message is None:
        return []
    registers = {}
    for move, social in zip(analysis.message.moves, analysis.social):
        registers[move.index - 1] = social.get("register")
    lines = [("flat", analysis.message.envelope.words)]
    for i, words in enumerate(analysis.message.lines):
        code = registers.get(i) or "R2"
        lines.append((lang.registers[code]["settings"]["prosody"], words))
    out = []
    for prosody, words in lines:
        said, phonemes = [], []
        for w in words:
            if _speakable(w, lang):
                said.append(ipa(w.form, lang))
                phonemes.append(espeak(w.form, lang))
            else:
                said.append(EMBEDDED)
                phonemes.append("_:")
        out.append({"prosody": prosody, "ipa": " ".join(said),
                    "espeak": "[[" + " ".join(phonemes) + "]]"})
    return out


def decode(stream: str, lang: Language | None = None) -> list:
    """The words of a stream of symbols without boundaries: each word's first syllable
    fixes its length, and a vowel after it begins a suffix, or with the linker a further
    root, whose first syllable fixes its length in turn, so that the division is unique
    (specification/sounds-and-words.md#how-a-words-opening-fixes-its-length). None where
    the stream does not divide into words of these shapes."""
    lang = lang or load()
    words, i = [], 0
    while i < len(stream):
        length = lang.length_at(stream, i)
        if length is None:
            return None
        j = i + length
        while j < len(stream) and stream[j] in lang.vowels:
            if stream[j] == LINKER:
                root = lang.length_at(stream, j + 1)
                if root is None:
                    return None
                j += 1 + root
            elif stream[j] in SUFFIX_FIRST:
                j += 4
            else:
                return None
        if j > len(stream):
            return None
        words.append(stream[i:j])
        i = j
    return words
