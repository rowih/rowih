"""Features (specification/protocol.md#versions-and-features). A feature is a numbered
part of the language that a release adds and an implementation may lack, flagged
must-understand or may-ignore in the protocol register's registry. A word belongs to a
feature by its class, its own identifier or the grammatical category of its lexicon entry;
a conventional sense, which shares its root's form, belongs to its feature where a frame
selects it, and an idiom where a unit is read by its entry.

A reader lacking a must-understand feature rejects every move that uses it, rather than
interpreting the rest (specification/protocol.md#versions-and-features); a reader lacking
a may-ignore feature passes over its words in a move's head, and keeps a word of it that
stands as content opaque, as it keeps any word it lacks."""
from __future__ import annotations

from . import senses
from .data import Language

MUST = "must-understand"
MAY = "may-ignore"
IDIOMS, SENSES = "idiom", "conventional sense"
UNIT_KINDS = ("assertion", "situation", "term")


def registry(lang: Language) -> list:
    return lang.protocol.get("features", [])


def flag(lang: Language, number: int) -> str:
    return next(f["flag"] for f in registry(lang) if f["number"] == number)


def of_item(item, lang: Language) -> int | None:
    """The feature a word belongs to, or None for the core."""
    if item is None:
        return None
    entry = lang.entries.get(item.identifier)
    category = entry["grammatical category"] if entry is not None else None
    for f in registry(lang):
        if item.class_id and item.class_id in f.get("classes", []):
            return f["number"]
        if item.identifier in f.get("structural", []) + f.get("fields", []):
            return f["number"]
        if category is not None and category in f.get("categories", []):
            return f["number"]
    return None


def _number_of(lang: Language, category: str) -> int:
    return next(f["number"] for f in registry(lang) if category in f.get("categories", []))


def used_by_words(words, lang: Language) -> dict:
    """The features the words of a move belong to, each with its words."""
    out = {}
    for w in words:
        number = of_item(w.item, lang)
        if number is not None:
            out.setdefault(number, []).append(w)
    return out


def used_by_reading(t: dict, resolved: list, lang: Language) -> set:
    """The features a move uses by how it is read rather than by a word of its own: an
    idiom read by its entry, and a conventional sense a frame selects."""
    out = set()
    if resolved or any(n.get("kind") == "idiom" for n in _walk(t["constituents"])):
        out.add(_number_of(lang, IDIOMS))
    named = {}
    for n in _walk(t["constituents"]):
        if n.get("kind") in UNIT_KINDS and n.get("name") is not None:
            named[n["name"]] = n
    for n in _walk(t["constituents"]):
        if n.get("kind") in UNIT_KINDS and senses.sense_of(n, lang, named) is not None:
            out.add(_number_of(lang, SENSES))
            break
    return out


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for x in node:
            yield from _walk(x)
