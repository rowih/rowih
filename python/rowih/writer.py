"""Spelling helpers for the generator and the tests: words by identifier, numbers with
their check words, moves with their counts and move check words, protocol statements
with their counts and statement check words, and messages with their envelopes, their
authentication where a signer is given, and their integrity check values."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .data import Language, load
from .diagnostics import InputError
from .lexer import Word, encode_payload
from .parser import number_check, unit_check
from .serialise import check_value, covered
from .syntax import DIGITS

SYMBOL_NUMERAL = {str(i): d for i, d in enumerate(DIGITS)}
SYMBOL_NUMERAL.update({".": "decimal-point", "-": "negative", "/": "ratio", "e": "exponent",
                       "~": "interval"})
# a communication time: seconds since 1970-01-01T00:00:00Z, with a decimal fraction where
# the sender states one (specification/protocol.md#communication-time)
TIME = re.compile(r"-?[0-9]+(\.[0-9]+)?")


class EnvelopeError(InputError):
    """Envelope values that cannot be written: an error of a writer's input, as
    `notation.NotationError` is for its moves, not a diagnostic of the language."""


class StatementError(InputError):
    """A protocol statement whose parts cannot be written: a kind the protocol does not
    have, or parts its kind does not take."""


class OptionError(InputError):
    """A register, mode, diction or hearer's lexicon release the language does not have,
    given to the generator."""


def options(lang: Language, register: str | None, mode: str | None,
            diction: str | None) -> tuple:
    """The generator's options as it takes them: a register by its code, from its code or
    its name; a mode the language has; a diction by its key."""
    from .conversion import register_code
    from .generator import MODES
    code = None
    if register is not None:
        code = register_code(register, lang) if isinstance(register, str) else None
        if code is None:
            raise OptionError("no register %r: the registers are %s" % (register, ", ".join(
                "%s (%s)" % (c, r["name"]) for c, r in sorted(lang.registers.items()))))
    if mode is not None and mode not in MODES:
        raise OptionError("no mode %r: the modes are %s" % (mode, ", ".join(MODES)))
    if diction is not None:
        keys = sorted(e["key"] for e in lang.entries.values()
                      if e["grammatical category"] == "diction")
        if diction not in keys:
            raise OptionError("no diction %r: the dictions are %s" % (diction, ", ".join(keys)))
    return code, mode, diction


def _natural(value, what: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EnvelopeError("%s is a whole number of zero or more, not %r" % (what, value))


@dataclass(frozen=True)
class Envelope:
    """The values a writer gives the generator beside the moves
    (specification/notation.md#the-envelope): the sender, the recipients, the
    communication time, the message's serial on its channel, the entry its first move
    adds, the dialect releases it names, each (number, version), and whether to write the
    semantic check value and the integrity check value; `integrity` False leaves the
    latter out only from a message that may go without it. Each value is checked only for
    being writable; the rules of the language on them are the reader's to report."""
    sender: int
    recipients: tuple
    time: str
    identifier: int = 1
    first_entry: int = 1
    dialects: tuple = field(default=())
    semantic: bool = False
    integrity: bool | None = None

    def __post_init__(self):
        for name in ("sender", "identifier", "first_entry"):
            _natural(getattr(self, name), name.replace("_", " "))
        if isinstance(self.recipients, (str, bytes)) or not hasattr(self.recipients, "__iter__"):
            raise EnvelopeError("the recipients are a list of participant numbers, not %r"
                                % (self.recipients,))
        recipients = tuple(self.recipients)
        for r in recipients:
            _natural(r, "a recipient")
        object.__setattr__(self, "recipients", recipients)
        time = self.time
        if isinstance(time, int) and not isinstance(time, bool):
            time = str(time)
        if not isinstance(time, str) or not TIME.fullmatch(time):
            raise EnvelopeError("the communication time is a number of seconds since "
                                "1970-01-01T00:00:00Z, as an integer or a decimal numeral, "
                                "not %r" % (self.time,))
        object.__setattr__(self, "time", time)
        from .data import dialect_releases
        held = dialect_releases() if self.dialects else {}
        dialects = []
        for d in self.dialects:
            try:
                number, version = d
            except (TypeError, ValueError):
                raise EnvelopeError("a dialect is a pair (number, version), not %r" % (d,)) \
                    from None
            if (number, version) not in held:
                raise EnvelopeError("no dialect release %r %r is held; the releases held are "
                                    "%s" % (number, version,
                                            ", ".join("%d %s" % k for k in sorted(held))))
            dialects.append((number, version))
        object.__setattr__(self, "dialects", tuple(sorted(dialects)))
        if not isinstance(self.semantic, bool):
            raise EnvelopeError("semantic is true or false")
        if self.integrity is not None and not isinstance(self.integrity, bool):
            raise EnvelopeError("integrity is true, false or unstated")

    def arguments(self) -> dict:
        """The envelope as `Generator.message` takes it."""
        return {"sender": self.sender, "recipients": self.recipients, "time": self.time,
                "identifier": self.identifier, "first_entry": self.first_entry,
                "semantic": self.semantic, "integrity": self.integrity}


# the envelope `generate` writes where a writer gives none: participant 1 to participant
# 2, at 2025-10-05T00:00:00Z, the first message on its channel, adding entry 1
FIXED_ENVELOPE = Envelope(1, (2,), "1759622400")



@dataclass
class Writer:
    lang: Language

    def __init__(self, lang: Language | None = None):
        self.lang = lang or load()

    def w(self, identifier: str) -> str:
        """The form of a member, a structural word or an entry; `identifier` may be a
        member's identifier, `g.structure.<name>`, an `lx.` identifier or a root's key."""
        lang = self.lang
        if identifier in lang.items:
            return lang.items[identifier].form
        for item in lang.items.values():
            if item.kind in ("root", "derivation") and item.name == identifier:
                return item.form
        raise KeyError(identifier)

    def ws(self, *identifiers: str) -> list:
        return [self.w(i) for i in identifiers]

    def number(self, text: str, width: int | None = None) -> list:
        text = str(text)
        if width is not None:
            text = text.zfill(width)
        forms = [self.w("g.numbers.numeral.%s" % SYMBOL_NUMERAL[ch]) for ch in text]
        digits = "".join(ch for ch in text if ch.isdigit())
        forms.append(self.w("g.numbers.check-word.check-%d" % number_check(digits)))
        return forms

    def name(self, n: int) -> list:
        return self.number(str(n), self.lang.protocol["name width"])

    def payload(self, data: bytes) -> list:
        return self.number(str(len(data))) + [encode_payload(data)]

    def move(self, body: list) -> list:
        """WORD-COUNT, the count, the body and the move check word."""
        from .parser import move_check

        class _W:  # a stand-in carrying what move_check reads
            def __init__(self, item):
                self.item = item
        items = [_W(self.lang.by_form.get(f)) for f in body]
        chk = move_check(items, self.lang)
        return ([self.w("g.message.word-count.word-count")] + self.number(str(len(body) + 1))
                + list(body) + [self.lang.move_check_forms[chk]])

    def statement(self, kind: str, parts: list) -> list:
        """WORD-COUNT, the count, the statement and its check word
        (specification/protocol.md#protocol-messages). `kind` is holds, send-again,
        not-held, understands or lacks; each part is ("channel", recipients, serials),
        ("entries", numbers), ("language" | "lexicon" | "protocol", versions), ("dialect",
        number, version, digest) or ("lacking", feature numbers)."""
        part_word = "g.protocol.statement-part."
        body = [self.w("g.protocol.protocol-statement.%s" % kind)]
        for part in parts:
            if part[0] == "channel":
                body.append(self.w(part_word + "channel"))
                for r in part[1]:
                    body += self.number(str(r))
                body.append(self.w(part_word + "serials"))
                for serial in part[2]:
                    body += self.number(str(serial))
            elif part[0] == "entries":
                body.append(self.w(part_word + "entries"))
                for n in part[1]:
                    body += self.number(str(n))
            elif part[0] in ("language", "lexicon", "protocol"):
                body.append(self.w(part_word + "%s-version" % part[0]))
                for v in part[1]:
                    body += self.number(v)
            elif part[0] == "dialect":
                body += [self.w("g.structure.dialect")] + self.number(str(part[1])) + \
                    self.number(part[2]) + self.number(part[3], len(part[3]))
            else:
                body.append(self.w(part_word + "lacking-features"))
                for n in part[1]:
                    body += self.number(str(n))
        return self.unit(body)

    def unit(self, body: list) -> list:
        """WORD-COUNT, the count, the body and its unit check word: an envelope's or a
        statement's (specification/protocol.md#the-unit-check-word)."""
        words = [Word(f, None, self.lang.by_form.get(f)) for f in body]
        check = unit_check(words, self.lang)
        return ([self.w("g.message.word-count.word-count")] + self.number(str(len(body) + 1))
                + body + [self.w("g.numbers.check-word.check-%d" % check)])

    def envelope(self, sender=1, recipients=(2,), time="1759622400",
                 version=None, identifier=1, forwarded=False,
                 semantic: int | None = None, first_entry: int = 1,
                 dialects=None) -> list:
        """The envelope. `dialects`, each (number, version), are the dialects the message
        uses, those the language was loaded with where it is None; each is written with
        its release's digest (specification/dialects.md#the-digest-of-a-release)."""
        f = "g.message.message-field."
        out = [self.w(f + "sender")] + self.number(str(sender))
        out += [self.w(f + "recipients")]
        for r in recipients:
            out += self.number(str(r))
        out += [self.w(f + "communication-time")] + self.number(str(time))
        out += [self.w(f + "version")]
        if version is None:
            # the language release the writer's language reads under, its lexicon release,
            # and the protocol that language release was released with
            from .data import language_releases
            language = self.lang.language or self.lang.grammar["version"]
            protocol = next((r["protocol"] for r in language_releases()["language"]
                             if r["language"] == language), self.lang.protocol["version"])
            version = (language, self.lang.release["version"], protocol)
        for v in version:
            out += self.number(v)
        from .data import dialect_releases
        for number, dialect_version in (self.lang.dialects if dialects is None else dialects):
            digest = dialect_releases()[(number, dialect_version)]["digest"]
            out += [self.w("g.structure.dialect")] + self.number(str(number)) + \
                self.number(dialect_version) + self.number(digest, len(digest))
        out += [self.w(f + "identifier")] + self.number(str(identifier),
                                                         self.lang.protocol["identifier width"])
        out += [self.w(f + "first-entry")] + self.number(str(first_entry))
        if forwarded:
            out += [self.w("g.message.forwarded.forwarded")]
        if semantic is not None:
            out += [self.w(f + "semantic-check-value")] + self.number(
                str(semantic), self.lang.protocol["check value width"])
        return self.unit(out)

    def message(self, envelope: list, moves: list, integrity: bool = True,
                signer=None) -> str:
        """The canonical serialisation, with the integrity check value computed over the
        message without its field and appended to the envelope. `signer`, where given,
        is a pair (scheme, sign), `sign` taking the bytes the authentication covers and
        returning the signature, which is written before the integrity check value and
        covered by it (specification/protocol.md#authentication)."""
        body = "".join(" ".join(m) + "\n" for m in moves)
        text = " ".join(envelope) + "\n" + body
        if signer is not None:
            scheme, sign = signer
            signature = sign(covered(" ".join(envelope), body))
            envelope = envelope + [self.w("g.message.message-field.authentication")] + \
                self.number(str(scheme)) + self.payload(signature)
            text = " ".join(envelope) + "\n" + body
        if not integrity:
            return text
        icv = check_value(text)
        field = [self.w("g.message.message-field.integrity-check-value")] + self.number(
            str(icv), self.lang.protocol["check value width"])
        return " ".join(envelope + field) + "\n" + body
