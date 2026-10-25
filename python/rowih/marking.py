"""The marking a register writes on a realisation (specification/lexicon.md#registers):
its register word, its politeness word, the synonyms of its vocabulary, the honorific of
the ceremonial register and, where its syntax is canonical, the canonical order of
siblings. Marking chooses among forms whose cores are identical, so a marked move
normalises to the normal form its unmarked move has."""
from __future__ import annotations

import copy

from . import registers
from .data import DEFAULT_REGISTER, Language
from .normal import Normaliser

AGENT = "s.sort.agent"
# the losses only a register's marking incurs, which unmarking removes with it
MARKING_LOSSES = ("register", "relation-between-participants", "diction")


def _map_words(node, fn):
    if isinstance(node, list):
        return [_map_words(x, fn) for x in node]
    if not isinstance(node, dict):
        return node
    if node.get("kind") == "word":
        return fn(node)
    return {k: _map_words(v, fn) for k, v in node.items()}


def unmark(t: dict, lang: Language) -> dict:
    """The move with no register's marking: its register-marked words written as their
    bases, and its register, politeness word and diction removed, with the losses only
    they incurred."""
    out = copy.deepcopy(t)
    for key in ("register", "politeness", "diction"):
        out.pop(key, None)
    losses = [x for x in out.get("losses", []) if x.rsplit(".", 1)[-1] not in MARKING_LOSSES]
    if losses:
        out["losses"] = losses
    else:
        out.pop("losses", None)
    out["constituents"] = _map_words(out["constituents"],
                                     lambda p: registers.base_word(p, lang))
    return out


def synonym(lang: Language, base: str, vocabulary: str | None, code: str) -> str | None:
    """The synonym of `base` in `vocabulary` that register `code` admits, if the release
    lists one."""
    if vocabulary is None:
        return None
    for ident, e in lang.entries.items():
        if e.get("synonym of") == base and e.get("vocabulary") == vocabulary and \
                code in e["register"]:
            return ident
    return None


def _honorific(lang: Language):
    return next((i for i, e in lang.entries.items() if registers.marked(e)
                 and e["grammatical category"] == "derivational suffix"), None)


def _nominals(node, fn):
    """Apply `fn` to every word that stands as a term's content word."""
    if isinstance(node, list):
        return [_nominals(x, fn) for x in node]
    if not isinstance(node, dict):
        return node
    if node.get("kind") == "term":
        parts = [fn(p) if p.get("kind") == "word" else _nominals(p, fn) for p in node["parts"]]
        return dict(node, parts=parts)
    return {k: _nominals(v, fn) for k, v in node.items()}


def _vocabulary(constituents, lang: Language, vocabulary: str | None, code: str):
    """Every word written as its synonym in `vocabulary`, where the release lists one
    that register `code` admits."""
    def vocabulary_of(p):
        found = synonym(lang, p.get("entry"), vocabulary, code) if p.get("entry") else None
        return dict(p, form=lang.items[found].form, entry=found) if found else p
    return _map_words(constituents, vocabulary_of)


def _honour(constituents, lang: Language, code: str):
    """The honorific on every term's word that names an agent or a human, where register
    `code` admits the honorific."""
    honorific = _honorific(lang)
    if honorific is None or code not in lang.entries[honorific]["register"]:
        return constituents
    suffix = lang.items[honorific].form

    def deferential(p):
        e = lang.entries.get(p.get("entry")) if p.get("entry") else None
        if e is not None and (e["sort"] == AGENT or e["key"] == "human"):
            return {"kind": "word", "form": p["form"] + suffix, "entry": None,
                    "status": "formation"}
        return p
    return _nominals(constituents, deferential)


def mark(t: dict, lang: Language, code: str, diction: str | None = None) -> dict:
    """The move written in register `code`, with `diction` if one is given: unmarked,
    then given the register's word (none for the standard register, its declared
    default), its politeness word, the synonyms of its vocabulary or of the diction's
    where the register admits them, the honorific on every word naming an agent or a
    human where the register is ceremonial, and canonical order where its syntax is
    canonical."""
    record = lang.registers[code]
    out = unmark(t, lang)
    declared = t.get("losses", [])
    by_key = {e["key"]: i for i, e in lang.entries.items()}
    if code != DEFAULT_REGISTER:
        out["register"] = record["member"]
    if record["politeness word"]:
        out["politeness"] = by_key[record["politeness word"]]
    vocabulary = record["vocabulary"]
    if diction is not None:
        out["diction"] = by_key[diction]
        vocabulary = vocabulary or lang.entries[by_key[diction]].get("vocabulary")
    out["constituents"] = _vocabulary(out["constituents"], lang, vocabulary, code)
    out["constituents"] = _honour(out["constituents"], lang, code)
    if record["order"] == "canonical":
        norm = Normaliser(lang)
        for _ in range(64):
            if not norm.order_all(out):
                break
    # the losses the move declared that its marking still incurs
    incurred = set()
    if out.get("register") or registers.marked_words(out, lang):
        incurred.add("register")
    if out.get("politeness"):
        incurred.add("relation-between-participants")
    if out.get("diction"):
        incurred.add("diction")
    kept = out.get("losses", []) + [x for x in declared if x.rsplit(".", 1)[-1] in incurred]
    if kept:
        out["losses"] = sorted(set(kept), key=declared.index)
    return out
