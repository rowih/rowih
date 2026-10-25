"""The analysis and its parts as structured data: JSON values that a tool, a server or the
comparison of the two implementations can carry. Each function takes what the API
returns and adds nothing to it; the TypeScript implementation writes words and
diagnostics in the same shape (`typescript/src/record.ts`)."""
from __future__ import annotations

from .data import Item, Language
from .notation import Printer
from .tree import strip_private


def span(s) -> list | None:
    """A location as [encoding, start, end, line, column]."""
    return None if s is None else [s.encoding, s.start, s.end, s.line, s.column]


def word(w) -> dict:
    return {"form": w.form, "kind": w.kind, "entry": w.item.identifier if w.item else None,
            "morphemes": ["linker" if m == "linker" else m.identifier for m in w.morphemes],
            "payload": w.payload.hex(), "span": span(w.span)}


def diagnostic(d) -> dict:
    return {"code": d.code, "location": span(d.location), "expected": d.expected,
            "detected": d.detected, "ambiguity": d.ambiguity, "confidence": d.confidence,
            "recoverability": d.recoverability, "note": d.note, "text": d.as_text()}


def diagnostics(ds: list) -> list:
    return [diagnostic(d) for d in ds]


def envelope(env) -> dict:
    """What an envelope states, each value as written."""
    return {"sender": env.sender.text, "recipients": [r.text for r in env.recipients],
            "communication time": env.time.text, "version": [v.text for v in env.version],
            "identifier": env.identifier.text if env.identifier else None,
            "first entry": env.first_entry.text if env.first_entry else None,
            "semantic check value": env.semantic.text if env.semantic else None,
            "integrity check value": env.integrity.text if env.integrity else None,
            "protocol message": env.is_protocol}


def analysis(a, lang: Language) -> dict:
    """An analysis as a reader acts on it: whether the message drew no diagnostic, how far
    what parsed is vouched for, the diagnostics, the envelope, each move as written and
    in its literal semantic form (its normal form) with its class and its social and
    textual component, the protocol statement of a protocol message, the releases named
    and what the reader lacked of them, the deprecated words used, the meanings of the
    formations, and the canonical serialisation."""
    printer = Printer(lang)
    moves = []
    for t, n, c, social in zip(a.moves, a.normal, a.classes, a.social, strict=True):
        moves.append({"as written": printer.move(t), "literal semantic form": printer.move(n),
                      "class": [k for k, v in c.items() if v], "social": social})
    return {"ok": a.ok, "encoding": a.encoding, "confidence": a.confidence,
            "diagnostics": diagnostics(a.diagnostics),
            "envelope": envelope(a.message.envelope) if a.message is not None else None,
            "moves": moves, "statement": a.statement, "named": a.named,
            "lacking": a.lacking, "ignored": a.ignored, "deprecated": a.deprecated,
            "formations": a.formations, "canonical": a.canonical}


def trees(ts: list) -> list:
    """Move trees without their private fields, the locations among them."""
    return [strip_private(t) for t in ts]


def item(it: Item, lang: Language) -> dict:
    """A word of the lexicon, a member or a morpheme, with how the notation writes it."""
    entry = lang.entries.get(it.identifier, {})
    return {"identifier": it.identifier, "form": it.form, "gloss": it.gloss,
            "kind": it.kind, "category": it.category or None, "class": it.class_id or None,
            "sort": it.sort or None, "definition": entry.get("definition"),
            "written": Printer(lang).atom_of(it)}
