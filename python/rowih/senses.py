"""The conventional figurative senses of the lexicon
(specification/lexicon.md#figurative-senses-and-conceptual-mappings). A word is read in a
conventional sense where the unit it heads has the role the sense's frame names, filled by
the kind of constituent the frame names, and in its basic sense elsewhere and inside the
source of a marked figure, which the mark asks to be read by comparison with its basic
meaning. The frame is read from the move alone, so that every reader computes the same
sense and none needs anything a participant holds; the release checks that no unit selects
two senses of one form."""
from __future__ import annotations

from .data import Language

UNIT_KINDS = ("assertion", "situation", "term")


def filler_kind(filler: dict, named: dict | None = None) -> str:
    """The kind of constituent a role is filled by: a shared node by the kind of the node
    it names, and a set of readings by the kind its readings share."""
    kind = filler.get("kind")
    if kind == "same" and named and filler.get("name") in named:
        return named[filler["name"]].get("kind", kind)
    if kind == "readings":
        kinds = {filler_kind(r, named) for r in filler.get("readings", [])}
        return kinds.pop() if len(kinds) == 1 else kind
    return kind


def head_word(unit: dict) -> dict | None:
    """The word a situation or a term is headed by, if it is an entry of the lexicon."""
    for p in unit.get("parts", []):
        if p.get("kind") == "word":
            return p if p.get("entry") else None
    return None


def sense_of(unit: dict, lang: Language, named: dict | None = None) -> str | None:
    """The conventional sense the unit's word is read in, or None for its basic sense."""
    if unit.get("kind") not in UNIT_KINDS:
        return None
    word = head_word(unit)
    if word is None:
        return None
    for ident in lang.senses.get(word["entry"], []):
        frame = lang.entries[ident]["frame"]
        for p in unit["parts"]:
            if p.get("kind") == "filler" and p["role"] == frame["role"] and \
                    filler_kind(p["filler"], named) == frame["filler"]:
                return ident
    return None


def entry_read(unit: dict, lang: Language, named: dict | None = None) -> str | None:
    """The entry the unit's word is read as: its conventional sense, or its root."""
    word = head_word(unit)
    if word is None:
        return None
    return sense_of(unit, lang, named) or word["entry"]
