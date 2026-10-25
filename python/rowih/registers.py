"""Registers (specification/lexicon.md#registers): the register a move states, the
precision bound two registers carry by default, the register-marked words the normal form
writes as their bases, and the records of the social and textual component a move's
realisation carries.

A register is a setting of the social and textual component with the modes it admits,
and nothing else, so nothing here reads or writes the core: the normal form of a move is
the same in every register."""
from __future__ import annotations

import copy

from .data import DEFAULT_REGISTER, REGISTER_CLASS, Language

# The two registers precision-bound by default; `tests/test_registers.py` holds this to
# the registers' records.
BOUND = (REGISTER_CLASS + ".protocol", REGISTER_CLASS + ".formal")
HONORIFIC = "honorific"
LOSSES = ("register", "diction", "stance", "relation between participants", "wording")
SOCIAL_KEYS = ("act", "losses", "politeness", "diction", "register")


def code(t: dict, lang: Language) -> str:
    """The register of a move: the one its head states, or the standard register, the
    declared default."""
    member = t.get("register")
    return lang.register_code[member] if member else DEFAULT_REGISTER


def record(t: dict, lang: Language) -> dict:
    return lang.registers[code(t, lang)]


def bound_by_register(t: dict) -> bool:
    return t.get("register") in BOUND


def carry(t: dict, n: dict) -> dict:
    """The normal form `n` of move `t` with the register, the politeness word and the
    diction `t` states written back in its head, and the losses they incur: a realisation
    in full explicitness is the normal form in the move's own register
    (specification/lexicon.md#registers), since the register belongs to the realisation,
    not the core."""
    out = dict(n)
    incurred = []
    if t.get("register"):
        out["register"] = t["register"]
        incurred.append("register")
    for key, loss in (("politeness", "relation between participants"),
                      ("diction", "diction")):
        if t.get(key):
            out[key] = t[key]
            incurred.append(loss)
    losses = [x for x in t.get("losses", []) if x.rsplit(".", 1)[-1].replace("-", " ")
              in incurred]
    if losses:
        out["losses"] = losses
    return out


def marked(entry: dict) -> bool:
    """Whether an entry is register-marked: a synonym of another word, or the honorific
    suffix, whose expansion is its base."""
    return "synonym of" in entry or entry.get("key") == HONORIFIC and \
        entry["grammatical category"] == "derivational suffix"


def base_word(p: dict, lang: Language) -> dict:
    """A word part with every register-marked morpheme written as its base: a synonym as
    the word it is a synonym of, and the honorific suffix removed
    (specification/lexicon.md#registers). A formation whose base form the release lists is
    that entry, since the listed entry governs
    (specification/lexicon.md#listed-derivations-and-compounds)."""
    entry = lang.entries.get(p.get("entry")) if p.get("entry") else None
    if entry is not None and "synonym of" in entry:
        base = entry["synonym of"]
        return dict(p, form=lang.items[base].form, entry=base, status="known")
    if p.get("status") != "formation":
        return p
    from .lexer import segment
    morphemes = segment(p["form"], lang)
    if morphemes is None:
        return p
    form, changed = "", False
    for m in morphemes:
        if m == "linker":
            form += "i"
            continue
        e = lang.entries.get(m.identifier)
        if e is not None and "synonym of" in e:
            form += lang.items[e["synonym of"]].form
            changed = True
        elif e is not None and marked(e):
            changed = True
        else:
            form += m.form
    if not changed:
        return p
    item = lang.by_form.get(form)
    if item is not None and item.kind in ("root", "derivation"):
        return {"kind": "word", "form": form, "entry": item.identifier, "status": "known"}
    return {"kind": "word", "form": form, "entry": None, "status": "formation"}


def marked_words(t: dict, lang: Language) -> list:
    """The register-marked words a move writes, in the order it writes them."""
    from .lexer import segment
    out = []
    for node in _walk(t.get("constituents", [])):
        if node.get("kind") != "word":
            continue
        entry = lang.entries.get(node.get("entry")) if node.get("entry") else None
        if entry is not None and marked(entry):
            out.append(node["form"])
        elif node.get("status") == "formation":
            morphemes = segment(node["form"], lang) or []
            if any(m != "linker" and marked(lang.entries.get(m.identifier, {}))
                   for m in morphemes):
                out.append(node["form"])
    return out


def stance(t: dict, resolved: list, lang: Language) -> list:
    """The forms of the move whose entries carry a stance its normal form loses: its act
    word and the idioms it read by their entries."""
    out = []
    for ident in ([t["act"]] if t.get("act") else []) + list(resolved):
        if "stance" in lang.entries[ident].get("declared loss", []):
            out.append(ident)
    return out


def wording(t: dict) -> dict:
    """The move as written, apart from the register, the politeness word, the diction and
    the declared losses, which are records of their own: the wording on which quotation,
    wordplay and verse depend."""
    out = {k: v for k, v in copy.deepcopy(t).items()
           if k not in ("losses", "politeness", "diction", "register")}
    return _strip(out)


def social(t: dict, resolved: list, lang: Language) -> dict:
    """The five records of the social and textual component a move's realisation
    carries, by the names of the declared loss's members."""
    return {"register": code(t, lang),
            "diction": lang.entries[t["diction"]]["key"] if t.get("diction") else None,
            "stance": stance(t, resolved, lang),
            "relation between participants":
                lang.entries[t["politeness"]]["key"] if t.get("politeness") else None,
            "wording": wording(t)}


def changed(before: dict, after: dict) -> list:
    """The records of the social and textual component two realisations differ in, in
    the order of the declared loss's members."""
    return [k for k in LOSSES if before[k] != after[k]]


def _strip(node):
    if isinstance(node, dict):
        return {k: _strip(v) for k, v in node.items() if not k.startswith("_")}
    if isinstance(node, list):
        return [_strip(x) for x in node]
    return node


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for x in node:
            yield from _walk(x)
