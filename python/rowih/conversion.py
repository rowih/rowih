"""Conversion between registers (specification/lexicon.md#registers): a message rewritten
in another register, which keeps the core, sets the target's social and textual component,
re-realises within a mode the target admits, and declares what it changed.

A conversion is a transformation of the toolchain, not an act of the exchange: it declares
its changes to whoever asked for it, each move's as the members of the declared loss it
differs in, and a participant that sends the result on another's behalf relays it under
the rules of relaying. Where the target register cannot carry the core, because the core
holds a figure or a creative ambiguity none of its modes admits, the move is not converted
and a diagnostic says so: a conversion never changes the core to fit a register
(`compression/conversion-touches- the-core`)."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field

from . import data, register_rules, registers
from .checker import precision_bound
from .diagnostics import Diagnostic
from .economy import economy
from .marking import mark
from .moves import find_named, resolve_deixis, strip_name
from .normal import Normaliser
from .serialise import check_value
from .tree import Spell, strip_private
from .writer import Writer

CORE_DEVICES = ("marked figures", "creative ambiguity")


@dataclass
class Conversion:
    text: str
    # for each move, the records of the social and textual component the conversion
    # changed, by the names of the declared loss's members
    changes: list = field(default_factory=list)
    diagnostics: list = field(default_factory=list)


def register_code(name: str, lang) -> str | None:
    """A register by its code or its name: `R5` or `casual`."""
    for code, record in lang.registers.items():
        if name.upper() == code or name.lower() == record["name"]:
            return code
    return None


def _restated(t: dict, record: dict, norm: Normaliser):
    """An acceptance written with the device of shared context, with the content of the
    entry it names restated from `record`, which maps a handle to the entry's content
    and its author's recipients; None where the record lacks it."""
    named = t["named"]
    held = (record or {}).get((str(named["author"]), str(named["number"])))
    if held is None:
        return None
    content, recipients = held
    if named.get("part") is not None:
        content = [strip_name(find_named(content, named["part"]))]
    return dict(t, constituents=resolve_deixis(copy.deepcopy(content), str(named["author"]),
                                               recipients))


def convert_move(t: dict, lang, code: str, norm: Normaliser, record=None):
    """The move rewritten in register `code`, or a diagnostic. Where the target admits
    every device the move uses, its devices stay as they were and only its marking
    changes; where it does not, the move moves toward explicitness and takes the devices
    of the most economical mode the target admits (specification/lexicon.md#registers)."""
    target = lang.registers[code]
    admitted = set(target["devices admitted"])
    used = register_rules.devices_used(t, lang, norm)
    lacking = [d for d in CORE_DEVICES if d in used and d not in admitted]
    if lacking:
        return Diagnostic("d.convert.register-cannot-carry", t.get("_span"),
                          expected=list(target["devices admitted"]), detected=lacking,
                          note="the core holds what register %s cannot carry" % code)
    t = strip_private(t)
    if "shared context" in used and "shared context" not in admitted:
        restated = _restated(t, record, norm)
        if restated is None:
            return Diagnostic("d.convert.record-needed", None,
                              detected=["%s %s" % (t["named"]["author"],
                                                   t["named"]["number"])],
                              note="register %s restates what the move names, and the "
                                   "record of the entry is not given" % code)
        t = restated
        used.discard("shared context")
    moved = dict(t)
    if code != data.DEFAULT_REGISTER:
        moved["register"] = target["member"]
    else:
        moved.pop("register", None)
    # the realisation stands where the target admits every device it uses and lists
    # every entry it writes, the register-marked ones aside, which marking replaces
    keeps = used - {"formulas"} <= admitted and (
        "formulas" not in used or target["formulas admitted"]) and all(
        code in lang.entries[i]["register"] or registers.marked(lang.entries[i])
        for _, i in register_rules.entries_used(t, lang, norm))
    if not keeps:
        mode = "idiom" if "idioms" in admitted else "normal expression"
        moved = economy(moved, lang, mode)
    diction = lang.entries[t["diction"]]["key"] if t.get("diction") else None
    return mark(moved, lang, code, diction)


def rejecting(diagnostics: list) -> list:
    """The diagnostics that reject what they concern; an unknown word outside a
    precision-bound move is kept opaque, and its message stays interpretable."""
    return [d for d in diagnostics if d.recoverability != "kept opaque"]


def convert(analysis, to: str, record=None) -> Conversion:
    """The message `analysis` parsed, rewritten in register `to`, with each move's
    changes declared. Only a message no diagnostic rejects is converted. The message is
    converted in the release and with the dialects it was read under, which the converted
    message names as its source did: a register that does not admit the device of
    dialect forms writes each term in place of its form, and the dialect may still give a
    definition its scope (specification/dialects.md#naming-a-dialect-in-a-message)."""
    under = getattr(analysis, "read_under", None) or {}
    lang = data.load(under.get("version"), under.get("language"), under.get("dialects", ()))
    if analysis.message is None or rejecting(analysis.diagnostics):
        return Conversion("", [], rejecting(analysis.diagnostics) or [
            Diagnostic("d.convert.ill-formed", None, note="no message to convert")])
    code = register_code(to, lang)
    if code is None:
        return Conversion("", [], [Diagnostic("d.parser.unexpected-word", None,
                                              expected=sorted(lang.registers) + ["english"],
                                              detected=[to])])
    norm = Normaliser(lang)
    moves, diags = [], []
    for t in analysis.moves:
        out = convert_move(t, lang, code, norm, record)
        if isinstance(out, Diagnostic):
            diags.append(out)
        else:
            moves.append(out)
    if diags:
        return Conversion("", [], diags)
    text = seal(analysis.message.envelope, moves, lang, norm)
    from .api import parse
    after = parse(text)
    if rejecting(after.diagnostics):
        # the core holds what the target's rules refuse, a register precision-bound by
        # default among them: a conversion does not change the core to fit
        return Conversion("", [], [Diagnostic(
            "d.convert.register-cannot-carry", None,
            detected=sorted({d.code for d in rejecting(after.diagnostics)}),
            note="the core does not meet what register %s requires" % code)])
    changes = [registers.changed(registers.social(t, s["idioms"], lang),
                                 registers.social(u, s2["idioms"], lang))
               for t, s, u, s2 in zip(analysis.moves, analysis.social, after.moves,
                                      after.social)]
    return Conversion(text, changes, list(after.diagnostics))


def seal(env, moves: list, lang, norm: Normaliser) -> str:
    """The moves as written, under the envelope's sender, recipients, time, identifier
    and first entry, with the integrity check value and, where the source carried one,
    the semantic check value computed again."""
    spell, wr = Spell(lang), Writer(lang)
    normal_text = "".join(" ".join(spell.move(norm.move(t))) + "\n" for t in moves)
    words = wr.envelope(env.sender.text, [r.text for r in env.recipients], env.time.text,
                        identifier=env.identifier.integer(),
                        forwarded=env.forwarded is not None,
                        semantic=check_value(normal_text) if env.semantic is not None
                        else None, first_entry=env.first_entry.integer())
    integrity = env.integrity is not None or any(precision_bound(t) for t in moves)
    return wr.message(words, [spell.move(t) for t in moves], integrity=integrity)
