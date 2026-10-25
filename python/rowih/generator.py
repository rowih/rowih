"""The generator (specification/notation.md#what-the-generator-writes): deterministic, it
writes the six outputs from a semantic representation, a register, a mode and the hearer's
acknowledged holdings."""
from __future__ import annotations

import copy
import json

from . import registers
from .checker import move_class, precision_bound
from .data import DEFAULT_REGISTER, Language, load
from .economy import Holdings, economy
from .marking import mark
from .register_rules import shared_context
from .english import English
from .normal import Normaliser
from .notation import Printer, Reader
from .serialise import check_value, text_to_native
from .tree import Spell, strip_private
from .writer import FIXED_ENVELOPE, Envelope, Writer, options

MODES = ("full explicitness", "normal expression", "compression", "idiom",
         "creative expression")
ORIGIN = "g.attitudes-and-aims.origin-of-an-aim."
INSTRUCTION_RECEIVED = ORIGIN + "instruction-received"


def _top_situations(constituents: list):
    """The situations a move's content states: its own, and those of its assertions."""
    for c in constituents:
        if c.get("kind") == "situation":
            yield c
        elif c.get("kind") == "assertion":
            yield from (p for p in c["parts"] if p.get("kind") == "situation")


def economise(t: dict, norm: Normaliser) -> dict:
    """Normal expression: every value that normalisation restores is left out. Each value
    is removed in turn and kept out when the normal form is unchanged, so the result
    normalises to the same normal form by construction."""
    target = norm.move(t)
    cur = copy.deepcopy(strip_private(t))

    def units(node):
        if isinstance(node, dict):
            if node.get("kind") in ("assertion", "situation", "term"):
                yield node
            for v in node.values():
                yield from units(v)
        elif isinstance(node, list):
            for x in node:
                yield from units(x)
    changed = True
    while changed:
        changed = False
        for u in list(units(cur)):
            for i, p in enumerate(list(u["parts"])):
                if p["kind"] != "value" and not (p["kind"] == "quantity" and p.get("comparator")
                                                 and p["comparator"].endswith("unstated")):
                    continue
                trial_parts = u["parts"][:i] + u["parts"][i + 1:]
                if p["kind"] == "quantity":
                    q = dict(p, comparator=None)
                    trial_parts = u["parts"][:i] + [q] + u["parts"][i + 1:]
                saved = u["parts"]
                u["parts"] = trial_parts
                if norm.move(cur) == target:
                    changed = True
                    break
                u["parts"] = saved
            if changed:
                break
    return cur


class Generator:
    def __init__(self, lang: Language | None = None):
        self.lang = lang or load()
        self.norm = Normaliser(self.lang)
        self.spell = Spell(self.lang)
        self.wr = Writer(self.lang)
        self.printer = Printer(self.lang)

    def realise(self, moves: list, mode: str = "normal expression") -> list:
        """The moves as written in `mode`, with the choices of form each move tree
        states; `economy` makes those choices for a meaning that states none. Full
        explicitness writes the normal form in the move's own register, with that
        register's marking (specification/lexicon.md#registers); `as written` writes each
        move exactly as its tree states it, which the negative corpus uses for a defect
        of form the generator would otherwise repair."""
        if mode == "as written":
            return [strip_private(t) for t in moves]
        if mode == "full explicitness":
            return [mark(registers.carry(t, self.norm.move(t)), self.lang,
                         registers.code(t, self.lang),
                         self.lang.entries[t["diction"]]["key"] if t.get("diction") else None)
                    for t in moves]
        out = [economise(t, self.norm) for t in moves]
        for t in out:
            # a register whose syntax is canonical has its siblings in canonical order as
            # written, which leaving values out can change
            # (specification/lexicon.md#registers)
            if registers.record(t, self.lang)["order"] == "canonical":
                for _ in range(64):
                    if not self.norm.order_all(t):
                        break
        return out

    def economy(self, moves: list, mode: str = "normal expression",
                holdings: Holdings | None = None) -> list:
        """Each move with the devices of economy `mode` admits applied to its meaning
        (specification/lexicon.md#conventional-expressions-and-idioms)."""
        return [economy(t, self.lang, mode, holdings) for t in moves]

    def mode_for(self, code: str, mode: str | None, diction: str | None) -> str:
        """The mode a realisation in register `code` is written in: the one asked for, or
        the first the diction names that the register admits, or normal expression."""
        admitted = self.lang.registers[code]["modes admitted"]
        if mode is not None:
            return mode
        if diction is not None:
            entry = next(e for e in self.lang.entries.values() if e["key"] == diction)
            return next(m for m in entry["modes"] if m in admitted)
        return "normal expression"

    def in_register(self, moves: list, code: str | None, mode: str | None = None,
                    diction: str | None = None, holdings: Holdings | None = None) -> tuple:
        """The moves realised in register `code`, or each in the register it states where
        `code` is None, in the mode `mode_for` gives, with the register's marking and the
        diction (specification/lexicon.md#registers). The register clips the mode's
        devices to those it admits, so a mode it does not admit moves toward explicitness.
        Returns the moves and the mode of the last."""
        out, chosen = [], mode or "normal expression"
        for t in moves:
            c = code or registers.code(t, self.lang)
            chosen = self.mode_for(c, mode, diction)
            target = dict(t)
            if shared_context(t) and "shared context" not in \
                    self.lang.registers[c]["devices admitted"] and holdings is not None:
                # a register without compression restates what the move names, from the
                # record the speaker holds (specification/lexicon.md#registers)
                from .conversion import _restated
                restated = _restated(t, holdings.entries, self.norm)
                target = restated if restated is not None else target
            if c != DEFAULT_REGISTER:
                target["register"] = self.lang.registers[c]["member"]
            else:
                target.pop("register", None)
            economised = economy(target, self.lang, chosen, holdings)
            out.append(mark(economised, self.lang, c, diction or (
                self.lang.entries[t["diction"]]["key"] if t.get("diction") else None)))
        return out, chosen

    def message(self, moves: list, mode: str = "normal expression", sender=1, recipients=(2,),
                time="1759622400", identifier=1, semantic: bool = False,
                integrity: bool | None = None, first_entry: int = 1, signer=None) -> str:
        """The message in the chosen mode. The integrity check value is written on every
        message unless `integrity` is False, which a message with an operative or a
        pending move does not admit; a message of inert moves without it cannot show a cut
        between two of its moves . `signer`, a (scheme, sign) pair, writes the
        authentication (specification/protocol.md#authentication)."""
        realised = self.realise(moves, mode)
        bound = any(precision_bound(t) for t in moves)
        if integrity is None or bound:
            integrity = True
        normal_text = "".join(" ".join(self.spell.move(self.norm.move(t))) + "\n"
                              for t in moves)
        env = self.wr.envelope(sender, recipients, time, identifier=identifier,
                               semantic=check_value(normal_text) if semantic else None,
                               first_entry=first_entry)
        return self.wr.message(env, [self.spell.move(t) for t in realised],
                               integrity=integrity, signer=signer)

    def for_hearer(self, holdings: Holdings | None) -> "Generator":
        """A generator that holds, beside this one's release, the dialects `holdings` show
        the hearer to hold, each under the digest of the release this implementation
        holds (`inv.devices-admissible`)."""
        from .economy import held_dialects
        usable = tuple(sorted(held_dialects(holdings))) if holdings is not None else ()
        if not usable:
            return self
        return Generator(load(self.lang.version, self.lang.language, usable))

    def compressed(self, moves: list, holdings: Holdings,
                   envelope: Envelope = FIXED_ENVELOPE) -> str:
        """The compressed form: compression for the hearer `holdings` describe, the
        message naming the dialects whose forms it uses and no other."""
        from .dialects import used_in
        g = self.for_hearer(holdings)
        economised = g.economy(moves, "compression", holdings)
        used = used_in(economised, g.lang)
        writer = Generator(load(self.lang.version, self.lang.language, tuple(used))) \
            if used else self
        return writer.message(economised, "compression", **envelope.arguments())

    def from_external(self, t: dict, material_type: str, material: str) -> list:
        """The moves for a move whose content derives from external material, a payload or
        a quotation the speaker read (`inv.external-origin-kept`): first the material,
        reported as the external source's and carried as declared data, which is inert by
        kind and on which the speaker claims no strength; then the move, whose content,
        where the move is operative or pending, states the origin of the aim as an
        instruction received, so that an agent that turns what it read into a request is
        on record as having done so."""
        report = Reader(self.lang).moves(
            "(move ASSERTED-POSITION (assertion REPORT (SOURCE (term EXTERNAL-SOURCE "
            "EXTERNAL)) (situation write (ACTOR (term EXTERNAL-SOURCE EXTERNAL)) "
            "(UNDERGOER (data %s %s)))))" % (json.dumps(material_type), json.dumps(material)))
        moved = copy.deepcopy(t)
        cls = move_class(moved)
        if cls["operative"] or cls["pending"]:
            for s in _top_situations(moved["constituents"]):
                s["parts"] = [p for p in s["parts"] if not (
                    p.get("kind") == "value" and p["member"].startswith(ORIGIN))]
                s["parts"].append({"kind": "value", "member": INSTRUCTION_RECEIVED})
        return report + [moved]

    def write(self, moves, envelope: Envelope, register: str | None = None,
              mode: str | None = None, holdings: Holdings | None = None,
              diction: str | None = None, signer=None) -> str:
        """The message a writer sends: the moves, a list of move trees or a text in the
        notation, realised in `register` (each move's own where it is None) and in `mode`
        or the mode the diction chooses, under `envelope`; `signer` writes the
        authentication. It is the transliteration of `generate`'s six outputs."""
        return self._realised(moves, envelope, register, mode, holdings, diction, signer)[0]

    def _realised(self, moves, envelope: Envelope, register, mode, holdings, diction,
                  signer=None) -> tuple:
        """The message `write` gives, and the mode it was written in."""
        register, mode, diction = options(self.lang, register, mode, diction)
        writer = self.under(envelope)
        if isinstance(moves, str):
            moves = Reader(writer.lang).moves(moves)
        realised, chosen = writer.in_register(moves, register, mode, diction, holdings)
        return writer.message(realised, chosen, signer=signer, **envelope.arguments()), chosen

    def under(self, envelope: Envelope) -> "Generator":
        """A generator whose language names the dialects `envelope` names: this one, where
        the envelope names none or the same, or one loaded with them."""
        if not envelope.dialects or envelope.dialects == tuple(sorted(self.lang.dialects)):
            return self
        return Generator(load(self.lang.version, self.lang.language, envelope.dialects))

    def generate(self, moves, register: str | None = None, mode: str | None = None,
                 holdings: Holdings | None = None, diction: str | None = None,
                 envelope: Envelope = FIXED_ENVELOPE) -> dict:
        """The six outputs of the generator
        (specification/notation.md#what-the-generator-writes). `moves` is a list of move
        trees or a text in the literal semantic notation; each message is written under
        `envelope`, the fixed envelope where none is given. The standard form is normal
        expression in the register each move states, the standard register where it states
        none; the compressed form is compression for a hearer whose holdings include the
        lexicon the message names, and full explicitness for any other; the
        transliteration, its native rendering and the gloss are the realisation in
        `register`, or each move's own, in `mode` or the mode the diction chooses
        (specification/lexicon.md#registers)."""
        register, mode, diction = options(self.lang, register, mode, diction)
        writer = self.under(envelope)
        if writer is not self:
            return writer.generate(moves, register, mode, holdings, diction, envelope)
        if isinstance(moves, str):
            moves = Reader(self.lang).moves(moves)
        normal = [self.norm.move(t) for t in moves]
        canonical = "".join(" ".join(self.spell.move(n)) + "\n" for n in normal)
        written = envelope.arguments()
        standard = self.message(self.economy(moves, "normal expression"), "normal expression",
                                **written)
        if holdings is not None and self.lang.version in holdings.lexicon:
            compressed = self.compressed(moves, holdings, envelope)
            declared = []
        else:
            compressed = self.message(moves, "full explicitness", **written)
            declared = ["no acknowledged holdings of lexicon %s: the compressed form is full "
                        "explicitness" % self.lang.version]
        transliteration, chosen = self._realised(moves, envelope, register, mode, holdings,
                                                 diction)
        from .api import parse
        a = parse(transliteration)
        gloss = gloss_lines(a, self.lang)
        return {"canonical form": canonical, "standard form": standard,
                "compressed form": compressed, "human-readable gloss": gloss,
                "transliteration": transliteration, "native-script rendering":
                    text_to_native(transliteration, self.lang),
                "register": register or "as each move states", "mode": chosen,
                "diction": diction, "declared": declared}


def morpheme_gloss(word, lang: Language) -> str:
    if word.kind == "payload":
        return "PAYLOAD"
    if word.item is None:
        if word.kind == "formation":
            parts = []
            for m in word.morphemes:
                parts.append("LINK" if m == "linker" else m.gloss)
            return "-".join(parts)
        return "?%s" % word.form
    return word.item.gloss


def gloss_lines(analysis, lang: Language | None = None) -> str:
    """The five lines for each move of a parsed message."""
    lang = lang or load()
    if analysis.message is None:
        return ""
    printer = Printer(lang)
    english = English(lang, analysis.message.envelope.sender.text)
    out = []
    for m, n in zip(analysis.message.moves, analysis.normal):
        translit = " ".join(w.form for w in m.words)
        out.append("NATIVE                 " + text_to_native(translit, lang))
        out.append("TRANSLITERATION        " + translit)
        out.append("MORPHEME GLOSS         " + " ".join(morpheme_gloss(w, lang)
                                                        for w in m.words))
        out.append("LITERAL SEMANTIC FORM  " + printer.move(n))
        out.append("NATURAL ENGLISH        " + english.move(n)
                   + " (an explanation made by this receiver; a view, not the language)")
        out.append("")
    return "\n".join(out)

