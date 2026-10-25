"""The checker's rules for registers (specification/lexicon.md#registers): what the
register a move states admits. A word, a suffix, an act word or an idiom stands only in a
register its entry lists (`d.checker.register-excludes-word`); a device of economy stands
only in a register one of whose modes admits it, and a formula only in a register that
admits formulas (`d.checker.register-excludes-device`); and a register whose syntax is
canonical admits siblings only in canonical order (`d.checker.register-order`). None of
the rules reads the core's meaning: each is a condition on the realisation."""
from __future__ import annotations

import copy

from . import idioms, registers
from .lexer import segment
from .tree import strip_private

FIGURE = "g.ambiguity-and-figures.figurative-type."
CREATIVE = "g.ambiguity-and-figures.kind-of-ambiguity.creative"
NORMATIVE = "g.force.what-the-move-adds.normative-entry"
RESOLUTION = "g.force.change-made.resolution"
ACCEPTANCE = "g.force.outcome-of-a-resolution.acceptance"


def shared_context(t: dict) -> bool:
    """Whether a move uses the device of shared context
    (specification/conformance.md#what-a-conformant-implementation-must-do): an acceptance
    that adds a normative entry and writes no content, naming the entry it accepts in
    place of restating it, so that the hearer's view takes the content from the entry
    named (specification/lexicon.md#registers)."""
    named = t.get("named")
    return (bool(t["adds"]) and t["adds"][0] == NORMATIVE and t["change"][:2] == [
        RESOLUTION, ACCEPTANCE] and bool(named) and named["ref"] == "names"
            and named["target"] == "entry" and not t["constituents"])


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for x in node:
            yield from _walk(x)


def entries_used(t: dict, lang, norm):
    """Every (node, entry identifier) of the lexicon the move writes: its act word, its
    politeness word and diction, each word and each morpheme of a formation, and each
    idiom it reads by its entry."""
    for key in ("act", "politeness", "diction"):
        if t.get(key):
            yield t, t[key]
    for node in _walk(t["constituents"]):
        if node.get("kind") == "idiom":
            yield node, node["entry"]
        elif idioms.marked(node):
            entry, _ = idioms.resolve(node, norm)
            if entry is not None:
                yield node, entry
        elif node.get("kind") == "word":
            if node.get("entry"):
                yield node, node["entry"]
            elif node.get("status") == "formation":
                for m in segment(node["form"], lang) or []:
                    if m != "linker" and m.identifier in lang.entries:
                        yield node, m.identifier


def devices_used(t: dict, lang, norm) -> set:
    """The devices of economy a move's realisation uses
    (specification/lexicon.md#registers), named as the registers' records name them, with
    `formulas` for a formula: what a register, or a hearer's holdings, must admit for the
    realisation to stand. Declared defaults and inheritance, which need only the grammar,
    are not counted."""
    out = set()
    if t.get("act"):
        out.add("conventional expressions")
    for node in _walk(t["constituents"]):
        entry = None
        if node.get("kind") == "idiom":
            entry = node["entry"]
        elif idioms.marked(node):
            entry, _ = idioms.resolve(node, norm)
        if entry is not None:
            if lang.entries[entry]["route"] == "formula":
                out |= {"conventional expressions", "formulas"}
            else:
                out.add("idioms")
        if node.get("kind") == "value" and node["member"].startswith(FIGURE):
            out.add("marked figures")
        elif node.get("kind") == "readings" and node["ambiguity"] == CREATIVE:
            out.add("creative ambiguity")
    if shared_context(t):
        out.add("shared context")
    if any(n.get("kind") == "word" and n.get("entry") in lang.dialect_forms
           for n in _walk(t["constituents"])):
        out.add("dialect forms")
    return out


def check_register(checker, t: dict):
    lang = checker.lang
    record = registers.record(t, lang)
    code = record["code"]
    devices = set(record["devices admitted"])
    for node, ident in entries_used(t, lang, checker.normaliser()):
        entry = lang.entries[ident]
        if code not in entry["register"]:
            checker.add("d.checker.register-excludes-word", node,
                        expected=list(entry["register"]),
                        detected=[entry["orthographic form"], code])
        if entry["grammatical category"] != "idiom":
            continue
        if entry["route"] == "formula":
            if not record["formulas admitted"]:
                checker.add("d.checker.register-excludes-device", node, detected=[code],
                            note="a formula, which the register does not admit")
        elif "idioms" not in devices:
            checker.add("d.checker.register-excludes-device", node, detected=[code],
                        note="an idiom, which none of the register's modes admits")
    for node in _walk(t["constituents"]):
        if node.get("kind") == "value" and node["member"].startswith(FIGURE) and \
                "marked figures" not in devices:
            checker.add("d.checker.register-excludes-device", node, detected=[code],
                        note="a marked figure, which none of the register's modes admits")
        elif node.get("kind") == "readings" and node["ambiguity"] == CREATIVE and \
                "creative ambiguity" not in devices:
            checker.add("d.checker.register-excludes-device", node, detected=[code],
                        note="a creative ambiguity, which none of the register's modes "
                             "admits")
    if shared_context(t) and "shared context" not in devices:
        checker.add("d.checker.register-excludes-device", t, detected=[code],
                    note="an entry named in place of restating it, which none of the "
                         "register's modes admits")
    if record["order"] == "canonical":
        written = copy.deepcopy(strip_private(t))
        if checker.normaliser().order_all(written):
            checker.add("d.checker.register-order", t, detected=[code],
                        note="siblings out of canonical order, which the register's "
                             "syntax requires")
