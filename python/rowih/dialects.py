"""Dialects (specification/dialects.md#what-a-dialect-release-may-hold). A dialect release
lists its community's terms, each formed from core items and read by its composition, and
its compressed forms, each a word of the root's shape whose meaning is the term it
compresses. A message names each dialect it uses by its number, its version and the digest
of the release, so that a hearer holding another release of the same number and version is
told apart rather than reading the forms its own way.

The digest is the SHA-256 of the release's canonical text reduced modulo 10^9 and written
at nine numerals, as the check values are (specification/protocol.md#the-check-values).
The canonical text holds what a reader takes from the release: the dialect's number, name
and version, the lexicon release it is formed from, each term's form with the release that
deprecated it, and each compressed form with the form of its expansion."""
from __future__ import annotations

import hashlib

DIGEST_WIDTH = 9


def canonical_text(release: dict) -> str:
    lines = ["rowih dialect %d %s %s lexicon %s" % (
        release["number"], release["dialect"], release["version"],
        release["formed from lexicon"])]
    for t in release["terms"]:
        lines.append("term %s %s" % (t["orthographic form"],
                                     t["version"]["deprecated"] or "-"))
    for f in release.get("forms", []):
        lines.append("form %s %s %s" % (f["orthographic form"], f["expansion"]["form"],
                                        f["version"]["deprecated"] or "-"))
    return "\n".join(lines) + "\n"


def digest(release: dict) -> str:
    """The release's digest, nine numerals."""
    value = int(hashlib.sha256(canonical_text(release).encode("utf-8")).hexdigest(), 16)
    return "%0*d" % (DIGEST_WIDTH, value % 10 ** DIGEST_WIDTH)


def expansion_word(p: dict, lang) -> dict:
    """A word part with a compressed form of a named dialect written as the term it
    compresses: the entry the term's form spells where the lexicon lists it, and
    otherwise the formation, read by its composition."""
    record = lang.dialect_forms.get(p.get("entry")) if p.get("entry") else None
    if record is None:
        return p
    form = record["expansion"]["form"]
    item = lang.by_form.get(form)
    if item is not None and item.kind in ("root", "derivation"):
        return {"kind": "word", "form": form, "entry": item.identifier, "status": "known"}
    return {"kind": "word", "form": form, "entry": None, "status": "formation"}


def expand(node, lang):
    """Every compressed form within `node` written as its expansion, in place."""
    if not lang.dialect_forms:
        return
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, dict) and v.get("kind") == "word":
                node[k] = expansion_word(v, lang)
            else:
                expand(v, lang)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            if isinstance(v, dict) and v.get("kind") == "word":
                node[i] = expansion_word(v, lang)
            else:
                expand(v, lang)


def used_in(moves, lang) -> tuple:
    """The dialects, each (number, release), whose compressed forms `moves` write or to
    which a definition among them is scoped: the dialects a message of them names and no
    other (specification/dialects.md#naming-a-dialect-in-a-message)."""
    from .convention_rules import scope_of
    found = set()
    for t in moves:
        if isinstance(t, dict) and "g.force.kind-of-setting.definition" in t.get("adds", []):
            number = scope_of(t)
            found.update(d for d in lang.dialects if d[0] == number)

    def visit(node):
        if isinstance(node, dict):
            if node.get("kind") == "word" and node.get("entry") in lang.dialect_forms:
                f = lang.dialect_forms[node["entry"]]
                found.add((f["dialect"], f["release"]))
            for v in node.values():
                visit(v)
        elif isinstance(node, list):
            for v in node:
                visit(v)
    visit(moves)
    return tuple(sorted(found))
