"""The canonical serialisation, the native digital form and the check values
(specification/protocol.md#the-forms-of-a-message-in-transport)."""
from __future__ import annotations

import hashlib

from .data import Language, load


def line_of(words) -> str:
    return " ".join(w.form for w in words)


def canonical_lines(envelope_words, moves_words, drop=()) -> str:
    """The envelope as the first line and each move a line of its own, words separated
    by one space and every line ended by one line feed. Words in `drop` (by identity)
    are left out, which is how the integrity check value's field is removed."""
    dropped = {id(w) for w in drop}
    lines = [" ".join(w.form for w in envelope_words if id(w) not in dropped)]
    for words in moves_words:
        lines.append(" ".join(w.form for w in words))
    return "".join(line + "\n" for line in lines)


def check_value(text: str, width: int | None = None) -> int:
    """SHA-256 (FIPS 180-4 § 6.2) of the text's UTF-8 bytes, as an integer, modulo ten to
    the check value width of the protocol schema (nine numerals from protocol 0.3;
    specification/protocol.md#the-check-values)."""
    width = width if width is not None else load().protocol["check value width"]
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest(), "big") \
        % (10 ** width)


def covered(envelope: str, body: str) -> bytes:
    """The bytes an authentication covers (specification/protocol.md#authentication): the
    canonical serialisation of the whole message, `envelope` its first line without the
    authentication and integrity check value fields and `body` its moves, each line ended
    by a line feed, so that the claims of sender and time are covered."""
    return (envelope + "\n" + body).encode("utf-8")


def to_native(words_by_line, lang: Language) -> str:
    """The native digital form: each symbol as its code point, payloads as written."""
    lines = []
    for words in words_by_line:
        out = []
        for w in words:
            if w.kind == "payload":
                out.append(w.form)
            else:
                out.append("".join(lang.code_points.get(ch, ch) for ch in w.form))
        lines.append(" ".join(out))
    return "".join(line + "\n" for line in lines)


def text_to_native(text: str, lang: Language) -> str:
    """Convert a transliteration whose tokens are all words (no payload) to the native
    digital form; payload-bearing text goes through `to_native` after lexing."""
    return "".join(lang.code_points.get(ch, ch) for ch in text)
