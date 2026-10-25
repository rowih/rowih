"""The parser (specification/grammar.md#how-a-hearer-reads-a-message): words to the AST by
the productions of `language/grammar.json`, with the count, the move check word, every
number's check word and the widths verified. Each rejection is a diagnostic; parsing
resumes at the next move when a move's count is intact.

One module longer than 500 lines: a recursive-descent parser is one class whose
productions call one another, and split it would scatter one grammar over modules."""
from __future__ import annotations

import re

from .data import Language
from .diagnostics import Diagnostic, Reject, Span
from .lexer import Word
from . import versions
from .syntax import (DIGITS, Authentication, ContentWord, DialectName, Envelope, Statement, Filler, Head, Idiom, IndexOf, Message,
                     Move, Number, Party, Quantity, ReadingSet, Reference, Same, TimeSpec,
                     TimeValue, Unit, Value, Wall)

G = "g."
# RFC 6838 § 4.2: type "/" subtype, each a restricted name.
MEDIA_TYPE = re.compile(r"[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]{0,126}/"
                        r"[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]{0,126}")
FIELD = "g.message.message-field."
UNIT_OPEN = {"g.structure.assertion": ("assertion", "g.structure.end-assertion"),
             "g.structure.situation": ("situation", "g.structure.end-situation"),
             "g.structure.term": ("term", "g.structure.end-term")}
FILLER_ROLES = {"g.situations-and-contents.participation",
                "g.attitudes-and-aims.counterparty", "g.standing.provenance-link",
                "g.ambiguity-and-figures.figures-relation"}
CONDITION = "g.situations-and-contents.connective.condition"
LOSS = "g.ambiguity-and-figures.declared-loss"
REGISTER = "g.ambiguity-and-figures.register"
COMPARATOR = "g.situations-and-contents.comparator"
UNTIL = "g.structure.until"
# The times that may last, and those that may also be stated by their length alone
# (specification/notation.md#times).
SPANNING_TIMES = {"observation-time", "event-time", "reference-time", "execution-time"}
MEASURED_TIMES = {"event-time", "reference-time", "execution-time"}
NUMERAL = "g.numbers.numeral"
CHECK = "g.numbers.check-word"
DIALECT = "g.structure.dialect"
PART = "g.protocol.statement-part."
VERSION_PARTS = {PART + "language-version": "language", PART + "lexicon-version": "lexicon",
                 PART + "protocol-version": "protocol"}


def number_check(digits: str) -> int:
    """Each digit times (i mod 10) + 1, i counting from 0 at the left, summed mod 11."""
    return sum(int(d) * ((i % 10) + 1) for i, d in enumerate(digits)) % 11


def move_check(body_words, lang: Language) -> int:
    """The move check word's value over the words between the count and the check word
    (specification/protocol.md#the-move-check-word)."""
    p = lang.modulus
    total = 0
    for j, w in enumerate(body_words, start=1):
        code = w.item.critical_code if w.item is not None else 0
        total += code * ((j % (p - 1)) + 1)
    return total % p


def unit_check(body_words, lang: Language) -> int:
    """The unit check word's value over the words between the count of an envelope or a
    statement and its check word (specification/protocol.md#the-unit-check-word): a fixed
    rule over fixed codes, so that a reader of any version checks it alike."""
    rule = lang.protocol["unit check word"]
    codes = rule["codes"]
    total = 0
    for i, w in enumerate(body_words):
        code = 0
        if w.item is not None:
            code = codes.get(w.identifier, codes.get(w.class_id, 0))
        total += code * ((i % 10) + 1)
    return total % rule["modulus"]


def _span_of(words):
    if not words:
        return None
    a, b = words[0].span, words[-1].span
    return Span(a.encoding, a.start, b.end, a.line, a.column)


def statement_form(statement) -> str:
    """What makes a statement ill-formed, or an empty string: each channel named once by
    its recipients in ascending order, entries asked for once; in an acknowledgement, the
    serials beyond the first ascending and each above the serial after the first, which
    is the first missing; elsewhere every serial and entry ascending from one."""
    if statement.kind in ("understands", "lacks"):
        return ""           # their readers check their order (`Parser.understood`, `lacked`)
    seen = set()
    for part in statement.parts:
        if part[0] == "channel":
            recipients, serials = part[1], part[2]
            if list(recipients) != sorted(set(recipients)) or recipients in seen:
                return "a channel's recipients out of order, repeated or named twice"
            seen.add(recipients)
            if statement.kind == "holds":
                beyond = serials[1:]
                if list(beyond) != sorted(set(beyond)) or any(s <= serials[0] + 1
                                                              for s in beyond):
                    return "serials held beyond the first missing out of order"
            elif list(serials) != sorted(set(serials)) or serials[0] < 1:
                return "serials asked for out of order or below one"
        else:
            if "entries" in seen or list(part[1]) != sorted(set(part[1])) or part[1][0] < 1:
                return "entries asked for out of order, below one or twice"
            seen.add("entries")
    return ""


class Parser:
    def __init__(self, words, lang: Language):
        self.words = words
        self.lang = lang
        self.pos = 0
        self.end = len(words)
        self.diags: list[Diagnostic] = []
        self.names: set = set()
        self.name_refs: list = []
        self.depth = 0
        self.maxima = lang.protocol.get("maxima", {})
        self.queued: list = []      # the force values an act word stands for, unread
        self.named_dialects: list = []

    # ------------------------------------------------------------ primitives
    def peek(self, k: int = 0) -> Word | None:
        i = self.pos + k
        return self.words[i] if i < self.end else None

    def ident(self, k: int = 0) -> str:
        w = self.peek(k)
        return w.identifier if w is not None else ""

    def cls(self, k: int = 0) -> str:
        w = self.peek(k)
        return w.class_id if w is not None and w.item is not None else ""

    def take(self) -> Word:
        w = self.peek()
        if w is None:
            last = self.words[self.end - 1] if self.end else None
            raise Reject(Diagnostic("d.parser.end-of-input",
                                    last.span if last else None,
                                    expected=["more words"]))
        self.pos += 1
        return w

    def fail(self, code: str, expected, word: Word | None = None, note: str = ""):
        word = word if word is not None else self.peek()
        raise Reject(Diagnostic(code, word.span if word else None, expected=list(expected),
                                detected=[word.form] if word else [], note=note))

    def expect(self, identifier: str) -> Word:
        if self.ident() != identifier:
            self.fail("d.parser.unexpected-word", [identifier])
        return self.take()

    def value(self) -> Value:
        w = self.take()
        return Value(w.identifier, w)

    # ------------------------------------------------------------ numbers
    def number(self, width: int | None = None, integer: bool = False) -> Number:
        words, names = [], []
        while self.cls() == NUMERAL:
            w = self.take()
            words.append(w)
            names.append(w.item.name)
        if not names:
            self.fail("d.parser.unexpected-word", ["a numeral"])
        if self.cls() != CHECK:
            self.fail("d.parser.unexpected-word", ["a number's check word"])
        cw = self.take()
        words.append(cw)
        check = int(cw.item.name.split()[-1])
        num = Number(names, check, words)
        self._number_form(num, integer, width)
        if width is not None and (len(num.numerals) != width or num.text != num.digits):
            raise Reject(Diagnostic("d.parser.width", _span_of(words),
                                    expected=["%d digits" % width], detected=[num.text]))
        if number_check(num.digits) != check:
            raise Reject(Diagnostic("d.parser.number-check-mismatch", _span_of(words),
                                    expected=["check %d" % number_check(num.digits)],
                                    detected=["check %d" % check]))
        return num

    def _number_form(self, num: Number, integer: bool, width: int | None):
        """A number is [-]digits[.digits][e[-]digits], optionally a ratio or an interval
        of two; no whole part has a leading zero except at a fixed width."""
        text = num.text
        pieces = _split_any(text, "/~")
        ok = len(pieces) <= 2 and all(_decimal_ok(piece) for piece in pieces)
        if integer:
            ok = ok and text.isdigit()
        if ok and width is None:
            for piece in pieces:
                whole = piece.lstrip("-").split(".")[0].split("e")[0]
                if len(whole) > 1 and whole.startswith("0"):
                    ok = False
        if not ok:
            raise Reject(Diagnostic("d.parser.number-form", _span_of(num.words),
                                    expected=["a well-formed number"], detected=[text]))

    # ------------------------------------------------------------ message
    def message(self) -> Message:
        if not self.words:
            raise Reject(Diagnostic("d.parser.empty", None, expected=["a message"]))
        env = self.envelope()
        moves = []
        index = 0
        while self.pos < self.end:
            index += 1
            moves.append(self.move(index))
        if not moves:
            raise Reject(Diagnostic("d.parser.end-of-input", _span_of(env.words),
                                    expected=["a move"]))
        return Message(env, moves)

    def envelope(self) -> Envelope:
        start = self.pos
        pw = self.lang.protocol
        # the envelope is a counted unit with its own check word (protocol 0.3)
        fields = self.counted(self.envelope_body)[0]
        (sender, recipients, time, version, identifier, first_entry, forwarded,
         semantic) = fields
        integrity = authentication = None
        integrity_words = []
        if self.ident() == FIELD + "authentication":
            authentication = self.authentication()
        if self.ident() == FIELD + "integrity-check-value":
            iw = self.take()
            integrity = self.number(width=pw["check value width"], integer=True)
            integrity_words = [iw] + integrity.words
        if self.cls() == "g.message.message-field":
            self.fail("d.parser.envelope", ["a move"], note="a field repeated or out of order")
        env = Envelope(sender, recipients, time, version, identifier, first_entry, forwarded,
                       semantic, integrity, self.words[start:self.pos], integrity_words,
                       authentication, self.named_dialects)
        if env.is_protocol and (first_entry.integer() != 0 or len(recipients) != 1
                                or forwarded is not None):
            raise Reject(Diagnostic("d.parser.protocol-message", _span_of(identifier.words),
                                    expected=["first entry zero, one recipient, not "
                                              "forwarded"],
                                    note="a message whose identifier is zero is a protocol "
                                         "message"))
        return env

    def counted(self, read) -> tuple:
        """A counted unit, an envelope or a statement (protocol 0.3): WORD-COUNT, its count,
        what `read` reads within the count, and a check word computed by the unit check
        word's rule. Returns what `read` returned, with the count and the check word."""
        self.expect("g.message.word-count.word-count")
        count = self.number(integer=True)
        n = count.integer()
        body_start = self.pos
        if n < 2 or body_start + n > self.end:
            raise Reject(Diagnostic("d.parser.count-mismatch", _span_of(count.words),
                                    expected=["%d words" % n],
                                    detected=["%d words" % (self.end - body_start)]))
        check_word = self.words[body_start + n - 1]
        if check_word.item is None or check_word.class_id != CHECK:
            raise Reject(Diagnostic("d.parser.count-mismatch", check_word.span,
                                    expected=["a check word as word %d" % n],
                                    detected=[check_word.form]))
        end = self.end
        self.end = body_start + n - 1
        try:
            result = read()
        finally:
            self.end = end
        computed = unit_check(self.words[body_start:body_start + n - 1], self.lang)
        stated = int(check_word.item.name.split()[-1])
        if stated != computed:
            raise Reject(Diagnostic("d.parser.unit-check-mismatch", check_word.span,
                                    expected=["check %d" % computed],
                                    detected=["check %d" % stated]))
        self.pos = body_start + n
        return result, count, check_word

    def envelope_body(self) -> tuple:
        fields = self.envelope_fields()
        if self.pos < self.end:
            self.fail("d.parser.envelope", ["the envelope's check word"],
                      note="a field repeated or out of order")
        return fields

    def envelope_fields(self) -> tuple:
        """The fields inside the envelope's count, from the sender to the semantic check
        value."""
        pw = self.lang.protocol
        self._field("sender")
        sender = self.number(integer=True)
        self._field("recipients")
        recipients = [self.number(integer=True)]
        while self.cls() == NUMERAL:
            recipients.append(self.number(integer=True))
        self._field("communication-time")
        time = self.number()
        self._field("version")
        version = [self.version_number() for _ in range(3)]
        self.named_dialects = self.dialects()
        self._field("identifier")
        identifier = self.number(width=pw["identifier width"], integer=True)
        self._field("first-entry")
        first_entry = self.number(integer=True)
        if first_entry.integer() < 1 and identifier.integer() != 0:
            raise Reject(Diagnostic("d.parser.number-form", _span_of(first_entry.words),
                                    expected=["an entry number from 1"],
                                    detected=[first_entry.text]))
        forwarded = None
        if self.ident() == "g.message.forwarded.forwarded":
            forwarded = self.value()
        semantic = None
        if self.ident() == FIELD + "semantic-check-value":
            self.take()
            semantic = self.number(width=pw["check value width"], integer=True)
        return sender, recipients, time, version, identifier, first_entry, forwarded, semantic

    def version_number(self) -> Number:
        """A version: two integers with the decimal point between them, neither with a
        leading zero (specification/dialects.md#terms)."""
        v = self.number()
        if not versions.well_formed(v.text):
            raise Reject(Diagnostic("d.parser.number-form", _span_of(v.words),
                                    expected=["major . minor"], detected=[v.text]))
        return v

    def dialect_named(self) -> tuple:
        """`DIALECT number version digest`: a dialect by its number, its version and the
        digest of its release (language 0.10)."""
        self.expect(DIALECT)
        number = self.number(integer=True)
        version = self.version_number()
        digest = self.number(width=self.lang.protocol["check value width"], integer=True)
        return number, version, digest

    def dialects(self, code: str = "d.parser.envelope") -> list:
        """The dialects a version field or a statement names, in ascending order of number
        and then of version, none twice."""
        out = []
        while self.ident() == DIALECT:
            out.append(self.dialect_named())
        keys = [(n.integer(), versions.key(v.text)) for n, v, _ in out]
        if keys != sorted(set(keys)):
            raise Reject(Diagnostic(code, _span_of(out[0][0].words),
                                    expected=["dialects in ascending order, none twice"],
                                    detected=["%d %s" % (n, ".".join(map(str, v)))
                                              for n, v in keys]))
        return out

    def authentication(self) -> Authentication:
        """`AUTHENTICATION number number payload`: the scheme, the signature's length in
        bytes and the signature (protocol 0.3)."""
        start = self.pos
        self.take()
        scheme = self.number(integer=True)
        length = self.number(integer=True)
        w = self.peek()
        if w is None or w.kind != "payload":
            self.fail("d.parser.authentication-form", ["a signature"])
        self.take()
        schemes = self.lang.protocol.get("authentication schemes", {})
        known = schemes.get(str(scheme.integer()))
        if known is None or known["signature bytes"] != length.integer() \
                or len(w.payload) != length.integer():
            raise Reject(Diagnostic("d.parser.authentication-form",
                                    _span_of(self.words[start:self.pos]),
                                    expected=["a known scheme and a signature of its length"],
                                    detected=["scheme %s, %d bytes" % (scheme.text,
                                                                       len(w.payload))]))
        return Authentication(scheme, length, w.payload, self.words[start:self.pos])

    # ------------------------------------------------------------ protocol statement
    def statement(self) -> Statement:
        """The statement of a protocol message
        (specification/protocol.md#protocol-messages): its count, what it states, its
        parts and its check word, every word a fixed form."""
        start = self.pos
        (kind, parts), count, check_word = self.counted(self.statement_body)
        statement = Statement(kind, parts, count, check_word, self.words[start:self.pos])
        failure = statement_form(statement)
        if failure:
            raise Reject(Diagnostic("d.parser.statement-form", _span_of(statement.words),
                                    note=failure))
        return statement

    def statement_body(self) -> tuple:
        if self.cls() != "g.protocol.protocol-statement":
            self.fail("d.parser.unexpected-word", ["g.protocol.protocol-statement"])
        kind = self.take().item.name.replace(" ", "-")
        if kind == "understands":
            return kind, self.understood()
        if kind == "lacks":
            return kind, self.lacked()
        parts = []
        while self.pos < self.end:
            parts.append(self.statement_part(kind))
        if not parts:
            self.fail("d.parser.end-of-input", ["a channel or entries"])
        return kind, parts

    def versions_part(self, ident: str, one: bool = False) -> tuple:
        """A statement part of versions: its word and the versions that follow it, one or
        several in ascending order."""
        self.expect(ident)
        found = [self.version_number()]
        while not one and self.cls() == NUMERAL:
            found.append(self.version_number())
        texts = [v.text for v in found]
        if texts != versions.ordered(set(texts)):
            raise Reject(Diagnostic("d.parser.statement-form", _span_of(found[0].words),
                                    note="versions out of order or repeated"))
        return (VERSION_PARTS[ident], tuple(texts))

    def _dialect_parts(self) -> list:
        return [("dialect", n.integer(), v.text, d.text)
                for n, v, d in self.dialects("d.parser.statement-form")]

    def _lacking_part(self) -> tuple:
        word = self.expect(PART + "lacking-features")
        found = [self.number(integer=True)]
        while self.cls() == NUMERAL:
            found.append(self.number(integer=True))
        numbers = [n.integer() for n in found]
        if numbers != sorted(set(numbers)) or numbers[0] < 1:
            raise Reject(Diagnostic("d.parser.statement-form",
                                    _span_of([word] + found[-1].words),
                                    note="features out of order, repeated or below one"))
        return ("lacking", tuple(numbers))

    def understood(self) -> list:
        """What `UNDERSTANDS` states (protocol 0.4): the language, lexicon and protocol
        versions its sender reads, the dialects it holds and the features it lacks."""
        parts = [self.versions_part(ident) for ident in VERSION_PARTS]
        parts += self._dialect_parts()
        if self.pos < self.end:
            parts.append(self._lacking_part())
        if self.pos < self.end:
            self.fail("d.parser.unexpected-word", ["the statement's check word"])
        return parts

    def lacked(self) -> list:
        """What `LACKS` states (protocol 0.4): a message of the addressee's by its channel
        and serial, and the versions, dialects and features of it its sender lacks, in the
        order the production writes them."""
        start = self.pos
        channel = self.statement_part("lacks")
        if channel[0] != "channel" or len(channel[2]) != 1:
            raise Reject(Diagnostic("d.parser.statement-form",
                                    _span_of(self.words[start:self.pos]),
                                    note="one message, by its channel and one serial"))
        parts = [channel]
        for ident in VERSION_PARTS:
            if self.ident() == ident:
                parts.append(self.versions_part(ident, one=True))
        parts += self._dialect_parts()
        if self.ident() == PART + "lacking-features":
            parts.append(self._lacking_part())
        if self.pos < self.end:
            self.fail("d.parser.unexpected-word", ["the statement's check word"])
        if len(parts) == 1:
            self.fail("d.parser.end-of-input", ["what the message lacks"])
        return parts

    def statement_part(self, kind: str) -> tuple:
        if self.ident() == "g.protocol.statement-part.channel":
            self.take()
            recipients = [self.number(integer=True).integer()]
            while self.cls() == NUMERAL:
                recipients.append(self.number(integer=True).integer())
            self.expect("g.protocol.statement-part.serials")
            serials = [self.number(integer=True).integer()]
            while self.cls() == NUMERAL:
                serials.append(self.number(integer=True).integer())
            return ("channel", tuple(recipients), tuple(serials))
        if kind not in ("holds", "lacks") and self.ident() == "g.protocol.statement-part.entries":
            self.take()
            numbers = [self.number(integer=True).integer()]
            while self.cls() == NUMERAL:
                numbers.append(self.number(integer=True).integer())
            return ("entries", tuple(numbers))
        self.fail("d.parser.unexpected-word", ["g.protocol.statement-part.channel"]
                  + (["g.protocol.statement-part.entries"]
                     if kind not in ("holds", "lacks") else []))

    def _field(self, name: str):
        if self.ident() != FIELD + name:
            self.fail("d.parser.envelope", [FIELD + name])
        self.take()

    # ------------------------------------------------------------ moves
    def move(self, index: int) -> Move:
        start = self.pos
        self.expect("g.message.word-count.word-count")
        count = self.number(integer=True)
        n = count.integer()
        body_start = self.pos
        if n < 2 or body_start + n > self.end:
            avail = self.end - body_start
            raise Reject(Diagnostic("d.parser.count-mismatch", _span_of(count.words),
                                    expected=["%d words" % n],
                                    detected=["%d words" % avail]))
        body = self.words[body_start:body_start + n]
        check_word = body[-1]
        if check_word.item is None or check_word.item.kind != "move-check":
            raise Reject(Diagnostic("d.parser.count-mismatch", check_word.span,
                                    expected=["a move check word as word %d" % n],
                                    detected=[check_word.form]))
        computed = move_check(body[:-1], self.lang)
        stated = self.lang.move_check_value[check_word.form]
        if computed != stated:
            raise Reject(Diagnostic("d.parser.move-check-mismatch", check_word.span,
                                    expected=["CHK%d" % computed], detected=["CHK%d" % stated]))
        saved_end = self.end
        self.end = body_start + n - 1
        self.names, self.name_refs = set(), []
        try:
            head = self.head()
            constituents = []
            while self.pos < self.end:
                constituents.append(self.constituent())
        finally:
            self.end = saved_end
        for ref in self.name_refs:
            if ref.name.integer() not in self.names:
                raise Reject(Diagnostic("d.parser.name-undefined", _span_of(ref.words),
                                        expected=["a defined name"], detected=[ref.name.text]))
        cycle = _name_cycle(constituents)
        if cycle is not None:
            raise Reject(Diagnostic("d.parser.name-cycle", _span_of(body),
                                    expected=["a rooted acyclic graph"],
                                    detected=["name %d reaches itself" % cycle]))
        self.pos = body_start + n
        return Move(index, count, head, constituents, check_word, body,
                    self.words[start:self.pos])

    def head(self) -> Head:
        """The head. An act word stands for the force values its entry expands to, read
        in their place and spanning the act word (specification/lexicon.md#act-words)."""
        h = Head()
        w = self.peek()
        if w is not None and w.item is not None and w.item.kind == "act":
            h.act = self.take()
            self.queued = [Value(m, h.act) for m in
                           self.lang.entries[h.act.identifier]["expansion"]]
        try:
            self._force(h)
        finally:
            left, self.queued = self.queued, []
        if left:
            self.fail("d.parser.unexpected-word", [left[0].class_id], word=h.act)
        if self.cls() == "g.force.authority-claimed":
            h.authority = self.value()
            if h.authority.name != "speakers-own":
                if self.ident() != "g.structure.term":
                    self.fail("d.parser.unexpected-word", ["g.structure.term"])
                h.authority_term = self.unit()
        if self.ident() == "g.time.time-index.deadline":
            self.take()
            h.deadline = self.time_spec()
        if self.cls() == "g.reference.kind-of-reference":
            h.named = self.reference()
            # a summary names every entry it summarises
            # (specification/discourse.md#summaries-and-confirmations); whether a further
            # reference is admitted is the checker's to say
            while self.cls() == "g.reference.kind-of-reference":
                h.also_named.append(self.reference())
        while self.peek() is not None and self.peek().item is not None and \
                self.peek().item.category == "discourse relation":
            h.relations.append(ContentWord(self.take()))
        w = self.peek()
        if w is not None and w.item is not None and w.item.category == "politeness word":
            h.politeness = self.take()
        w = self.peek()
        if w is not None and w.item is not None and w.item.category == "diction":
            h.diction = self.take()
        while self.cls() == LOSS:
            h.losses.append(self.value())
        if self.cls() == REGISTER:
            h.register = self.value()
        if self.ident() == "g.ambiguity-and-figures.precision-bound-declaration.precision-bound":
            h.precision_bound = self.value()
        return h

    def _hcls(self) -> str:
        return self.queued[0].class_id if self.queued else self.cls()

    def _hvalue(self) -> Value:
        return self.queued.pop(0) if self.queued else self.value()

    def _force(self, h: Head):
        """The force values, from what the move adds to when its change takes effect."""
        if self._hcls() != "g.force.what-the-move-adds":
            self.fail("d.parser.unexpected-word", ["g.force.what-the-move-adds"])
        adds = self._hvalue()
        h.adds.append(adds)
        sub = {"issue": ["g.force.kind-of-issue"],
               "normative-entry": ["g.force.kind-of-normative-entry"],
               "setting": ["g.force.kind-of-setting"]}.get(adds.name, [])
        for c in sub:
            if self._hcls() != c:
                self.fail("d.parser.unexpected-word", [c])
            h.adds.append(self._hvalue())
        if adds.name == "normative-entry" and h.adds[-1].name != "recommendation":
            if self._hcls() != "g.force.bindingness":
                self.fail("d.parser.unexpected-word", ["g.force.bindingness"])
            h.adds.append(self._hvalue())
        if self._hcls() == "g.force.change-made":
            change = self._hvalue()
            h.change.append(change)
            if change.name == "resolution":
                if self._hcls() != "g.force.outcome-of-a-resolution":
                    self.fail("d.parser.unexpected-word", ["g.force.outcome-of-a-resolution"])
                h.change.append(self._hvalue())
            if change.name != "none":
                for c in ("g.force.extent", "g.force.when-the-change-takes-effect"):
                    if self._hcls() != c:
                        self.fail("d.parser.unexpected-word", [c])
                    h.change.append(self._hvalue())

    # ------------------------------------------------------------ constituents
    def idiom(self) -> Idiom | None:
        """An extragrammatical idiom whose words begin here, the longest the release
        lists, or None. Its first word is a content word where a constituent stands,
        which no production admits, so that it is recognised by form and never
        ambiguous."""
        best = None
        for words, entry in self.lang.extragrammatical.items():
            n = len(words)
            if self.pos + n <= self.end and all(
                    self.ident(k) == words[k] for k in range(n)) and (
                    best is None or n > len(best[0])):
                best = (words, entry)
        if best is None:
            return None
        return Idiom(best[1], [self.take() for _ in best[0]])

    def constituent(self):
        ident = self.ident()
        found = self.idiom()
        if found is not None:
            return found
        if ident in UNIT_OPEN:
            return self.unit()
        if ident == "g.structure.wall":
            return self.wall()
        if ident == "g.structure.readings":
            return self.readings()
        if ident == "g.structure.same":
            return self.same()
        self.fail("d.parser.unexpected-word", ["a unit", "a wall", "a set of readings",
                                               "g.structure.same"])

    def filler(self):
        ident = self.ident()
        if self.cls() == "g.reference.kind-of-reference":
            return self.reference()
        return self.constituent() if ident else self.fail("d.parser.end-of-input",
                                                          ["a constituent"])

    def same(self) -> Same:
        w = self.take()
        name = self.number(width=self.lang.protocol["name width"], integer=True)
        s = Same(name, [w] + name.words)
        self.name_refs.append(s)
        return s

    def unit(self) -> Unit:
        open_word = self.take()
        kind, closer = UNIT_OPEN[open_word.identifier]
        self.depth += 1
        try:
            limit = self.maxima.get("nesting")
            if limit is not None and self.depth > limit:
                # rejected where the depth is reached, before the rest is read
                raise Reject(Diagnostic("d.parser.maximum", open_word.span,
                                        expected=["nesting at most %d" % limit],
                                        detected=["nesting %d" % self.depth]))
            return self._unit_body(open_word, kind, closer)
        finally:
            self.depth -= 1

    def _unit_body(self, open_word, kind, closer) -> Unit:
        name = None
        if self.ident() == "g.structure.name":
            self.take()
            name = self.number(width=self.lang.protocol["name width"], integer=True)
            if name.integer() in self.names:
                raise Reject(Diagnostic("d.parser.name-repeated", _span_of(name.words),
                                        detected=[name.text]))
            self.names.add(name.integer())
        parts = []
        while True:
            w = self.peek()
            if w is None:
                raise Reject(Diagnostic("d.parser.unclosed-unit", open_word.span,
                                        expected=[closer]))
            if w.identifier == closer:
                close = self.take()
                return Unit(kind, name, parts, open_word, close)
            parts.append(self.unit_part(kind))

    def unit_part(self, kind: str):
        if kind == "assertion":
            found = self.idiom()
            if found is not None:
                return found
        w = self.peek()
        ident, c = w.identifier, self.cls()
        if w.item is None:
            self.take()
            return ContentWord(w)       # a formation or an unknown word, kept opaque
        k = w.item.kind
        if k == "dialect":
            self.take()
            return ContentWord(w)       # a compressed form of a named dialect
        if k in ("root", "derivation"):
            self.take()
            if w.item.category == "unit of measure":
                return ContentWord(w)
            return ContentWord(w)
        if k == "structural":
            if ident in UNIT_OPEN or ident in ("g.structure.wall", "g.structure.readings",
                                               "g.structure.same"):
                return self.constituent()
            if ident == "g.structure.party":
                self.take()
                return Party(self.number(integer=True))
            if ident == DIALECT:
                self.take()
                return DialectName(self.number(integer=True))
            self.fail("d.parser.unexpected-word", ["a part of a %s" % kind])
        if k != "member":
            self.fail("d.parser.unexpected-word", ["a part of a %s" % kind])
        if c in FILLER_ROLES or ident == CONDITION:
            role = self.value()
            return Filler(role, self.filler())
        if c == "g.time.time-index":
            index = self.value()
            return TimeValue(index, self.time_spec(index))
        if c == "g.reference.kind-of-reference":
            return self.reference()
        if c == "g.situations-and-contents.comparator" or c == NUMERAL:
            return self.quantity(kind)
        return self.value()

    def quantity(self, kind: str = "term") -> Quantity:
        comparator = self.value() if self.cls() == "g.situations-and-contents.comparator" \
            else None
        num = self.number()
        unit = per = None
        w = self.peek()
        if self.cls() == "g.time.time-unit":
            unit = self.value()
        elif w is not None and w.item is not None and w.item.category == "unit of measure":
            unit = ContentWord(self.take())
        if self.ident() == "g.time.time-anchor.per":
            self.take()
            if self.cls() != "g.time.time-unit":
                self.fail("d.parser.unexpected-word", ["g.time.time-unit"])
            per = self.value()
        calibration = None
        if kind != "term" and unit is None and per is None and \
                self.ident() == "g.structure.party":
            # a numeric strength's calibration, the participant whose numbers it is in
            # (specification/discourse.md#common-ground); in a term PARTY is a part of its
            # own
            self.take()
            calibration = self.number(integer=True)
        return Quantity(comparator, num, unit, per, calibration)

    def reference(self) -> Reference:
        start = self.pos
        kind = self.value().name
        if self.ident() == "g.structure.message-target":
            self.take()
            author = self.number(integer=True)
            num = self.number(integer=True)
            ref = Reference(kind, "message", author, num)
        elif self.ident() == "g.structure.message-serial":
            # a message by its sender, its serial and its channel's recipients, which
            # names a message its speaker does not hold
            # (specification/notation.md#references)
            self.take()
            author = self.number(integer=True)
            num = self.number(width=self.lang.protocol["identifier width"], integer=True)
            ref = Reference(kind, "serial", author, num)
            ref.recipients = [self.number(integer=True)]
            while self.cls() == NUMERAL:
                ref.recipients.append(self.number(integer=True))
        else:
            author = self.number(integer=True)
            num = self.number(integer=True)
            ref = Reference(kind, "entry", author, num)
            if kind == "names":
                ref.expected = self.expected_kind()
                if self.cls() != "g.reference.expected-status-of-an-entry":
                    self.fail("d.parser.unexpected-word",
                              ["g.reference.expected-status-of-an-entry"])
                ref.status = self.value()
        if self.ident() == "g.structure.part":
            self.take()
            ref.part = self.number(width=self.lang.protocol["name width"], integer=True)
        ref.words = self.words[start:self.pos]
        return ref

    def expected_kind(self) -> list:
        if self.cls() != "g.force.what-the-move-adds":
            self.fail("d.parser.unexpected-word", ["g.force.what-the-move-adds"])
        out = [self.value()]
        sub = {"issue": "g.force.kind-of-issue",
               "normative-entry": "g.force.kind-of-normative-entry",
               "setting": "g.force.kind-of-setting"}.get(out[0].name)
        if sub:
            if self.cls() != sub:
                self.fail("d.parser.unexpected-word", [sub])
            out.append(self.value())
        return out

    def time_spec(self, index: Value | None = None) -> TimeSpec:
        """A time (specification/notation.md#times): a point, an interval, a duration or a
        rate, as the index it describes admits."""
        name = index.name if index is not None else None
        measured = name in MEASURED_TIMES
        if measured and self.cls() == COMPARATOR:
            comparator = self.value()
            return self._simple_time(name, comparator)
        spec = self._point(name)
        if spec.kind in ("duration", "rate"):
            return spec
        if name == "validity-interval":
            return TimeSpec("interval", reference=spec, until=self._point())
        if name in SPANNING_TIMES and self.ident() == UNTIL:
            self.take()
            return TimeSpec("interval", reference=spec, until=self._point())
        return spec

    def _point(self, name: str | None = None) -> TimeSpec:
        if self.ident() == "g.time.time-anchor.now":
            self.take()
            return TimeSpec("now")
        if self.cls() == "g.time.time-relation":
            rel = self.value()
            return TimeSpec("relation", relation=rel, reference=self._time_reference())
        if self.cls() == NUMERAL:
            return self._simple_time(name)
        self.fail("d.parser.unexpected-word", ["a time"])

    def _time_reference(self):
        if self.cls() == "g.time.time-index":
            return self.value()
        if self.ident() == "g.structure.same":
            same = self.same()
            if self.cls() != "g.time.time-index":
                self.fail("d.parser.unexpected-word", ["g.time.time-index"])
            return IndexOf(same, self.value())
        return self._simple_time()

    def _simple_time(self, name: str | None = None, comparator: Value | None = None) -> TimeSpec:
        """A clock value; after a measured index, also a duration or a rate."""
        if comparator is None and self.ident() == "g.time.time-anchor.now":
            self.take()
            return TimeSpec("now")
        num = self.number()
        if name == "event-time" and self.ident() == "g.time.time-anchor.per":
            self.take()
            if self.cls() != "g.time.time-unit":
                self.fail("d.parser.unexpected-word", ["g.time.time-unit"])
            return TimeSpec("rate", number=num, unit=self.value(), comparator=comparator)
        if self.cls() == "g.time.time-unit":
            unit = self.value()
            if comparator is None and self.ident() in ("g.time.time-anchor.ago",
                                                       "g.time.time-anchor.hence"):
                return TimeSpec("offset", number=num, unit=unit, anchor=self.value())
            if name in MEASURED_TIMES:
                return TimeSpec("duration", number=num, unit=unit, comparator=comparator)
            self.fail("d.parser.unexpected-word", ["g.time.time-anchor.ago",
                                                   "g.time.time-anchor.hence"])
        if comparator is not None:
            self.fail("d.parser.unexpected-word", ["g.time.time-unit"])
        return TimeSpec("absolute", number=num)

    def wall(self) -> Wall:
        self.take()
        if self.cls() != "g.message.embedded-material":
            self.fail("d.parser.unexpected-word", ["g.message.embedded-material"])
        kind = self.value()
        if kind.name == "declared-data":
            w = Wall(kind)
            w.type_length = self.number(integer=True)
            w.type_payload = self._payload()
            w.length = self.number(integer=True)
            w.payload = self._payload()
            for num, pay in ((w.type_length, w.type_payload), (w.length, w.payload)):
                if len(pay.payload) != num.integer():
                    raise Reject(Diagnostic("d.lexer.payload-short", pay.span,
                                            expected=["%d bytes" % num.integer()],
                                            detected=["%d bytes" % len(pay.payload)]))
            if not MEDIA_TYPE.fullmatch(w.type_payload.payload.decode("latin-1")):
                raise Reject(Diagnostic("d.parser.media-type", w.type_payload.span,
                                        expected=["a media type (RFC 6838 § 4.2)"],
                                        detected=[w.type_payload.form]))
            self.expect("g.structure.end-wall")
            return w
        w = Wall(kind)
        while self.ident() != "g.structure.end-wall":
            if self.peek() is None:
                raise Reject(Diagnostic("d.parser.unclosed-unit", kind.word.span,
                                        expected=["g.structure.end-wall"]))
            w.words.append(self.take())
        self.take()
        return w

    def _payload(self) -> Word:
        w = self.peek()
        if w is None or w.kind != "payload":
            self.fail("d.parser.unexpected-word", ["a payload"])
        return self.take()

    def readings(self) -> ReadingSet:
        self.take()
        if self.cls() != "g.ambiguity-and-figures.kind-of-ambiguity":
            self.fail("d.parser.unexpected-word", ["g.ambiguity-and-figures.kind-of-ambiguity"])
        kind = self.value()
        readings = []
        limit = self.maxima.get("readings")
        while self.ident() != "g.structure.end-readings":
            if limit is not None and len(readings) >= limit:
                self.fail("d.parser.maximum", ["at most %d readings" % limit])
            if self.peek() is None:
                raise Reject(Diagnostic("d.parser.unclosed-unit", kind.word.span,
                                        expected=["g.structure.end-readings"]))
            readings.append(self.filler())
        self.take()
        return ReadingSet(kind, readings)


def _name_cycle(constituents):
    """A name whose unit reaches itself through the units and SAMEs inside it, or None
    (the structure is a rooted directed acyclic graph)."""
    reaches = {}

    def collect(node, out):
        if isinstance(node, Unit):
            if node.name is not None:
                out.add(node.name.integer())
                return
            for p in node.parts:
                collect(p, out)
        elif isinstance(node, Same):
            out.add(node.name.integer())
        elif isinstance(node, TimeValue):
            # a time reference is an edge of the graph (specification/notation.md#times)
            for same in _spec_sames(node.spec):
                out.add(same.name.integer())
        elif isinstance(node, Filler):
            collect(node.filler, out)
        elif isinstance(node, ReadingSet):
            for r in node.readings:
                collect(r, out)

    def named(node):
        if isinstance(node, Unit):
            if node.name is not None:
                inner = set()
                for p in node.parts:
                    collect(p, inner)
                reaches[node.name.integer()] = inner
            for p in node.parts:
                named(p)
        elif isinstance(node, Filler):
            named(node.filler)
        elif isinstance(node, ReadingSet):
            for r in node.readings:
                named(r)
    for c in constituents:
        named(c)
    state = {}

    def visit(n):
        state[n] = 1
        for m in reaches.get(n, ()):
            if state.get(m) == 1:
                return m
            if m not in state:
                found = visit(m)
                if found is not None:
                    return found
        state[n] = 2
        return None
    for n in sorted(reaches):
        if n not in state:
            found = visit(n)
            if found is not None:
                return found
    return None


def _spec_sames(spec) -> list:
    """The SAMEs a time names through its references."""
    if not isinstance(spec, TimeSpec):
        return []
    out = []
    if isinstance(spec.reference, IndexOf):
        out.append(spec.reference.same)
    elif isinstance(spec.reference, TimeSpec):
        out += _spec_sames(spec.reference)
    out += _spec_sames(spec.until)
    return out


def _split_any(text: str, seps: str):
    out, cur = [], ""
    for ch in text:
        if ch in seps:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return out


def _decimal_ok(piece: str) -> bool:
    """[-]digits[.digits][e[-]digits]"""
    if "e" in piece:
        mant, _, exp = piece.partition("e")
        exp = exp[1:] if exp.startswith("-") else exp
        if not exp.isdigit():
            return False
    else:
        mant = piece
    mant = mant[1:] if mant.startswith("-") else mant
    whole, dot, frac = mant.partition(".")
    if not whole.isdigit():
        return False
    if dot and not frac.isdigit():
        return False
    return True


def _protocol_message(p: Parser, env, words):
    """A protocol message: its envelope and one statement, nothing after it."""
    start = p.pos
    try:
        statement = p.statement()
        if p.pos < p.end:
            p.fail("d.parser.unexpected-word", ["the end of a protocol message"])
    except Reject as r:
        return Message(env, [], [words[start:]]), [r.diagnostic]
    return Message(env, [], [words[start:p.pos]], statement), []


def parse_words(words, lang: Language):
    """Parse a whole message. Returns (Message or None, diagnostics). A rejected move is
    reported and parsing resumes after its counted body; a rejection elsewhere ends it."""
    p = Parser(words, lang)
    diags = []
    limit = p.maxima.get("message words")
    if limit is not None and len(words) > limit:
        return None, [Diagnostic("d.parser.maximum", words[limit].span,
                                 expected=["at most %d words" % limit],
                                 detected=["%d words" % len(words)])]
    try:
        if not words:
            raise Reject(Diagnostic("d.parser.empty", None, expected=["a message"]))
        env = p.envelope()
    except Reject as r:
        return None, [r.diagnostic]
    if env.is_protocol:
        return _protocol_message(p, env, words)
    moves, lines = [], []
    index = 0
    while p.pos < p.end:
        index += 1
        start = p.pos
        try:
            moves.append(p.move(index))
        except Reject as r:
            diags.append(r.diagnostic)
            # resume after the counted body when the count can be read; otherwise the
            # rest of the words stand as one line
            p.pos = start
            p.end = len(words)
            try:
                p.expect("g.message.word-count.word-count")
                n = p.number(integer=True).integer()
                p.pos = min(len(words), p.pos + n)
            except Reject:
                lines.append(words[start:])
                break
        lines.append(words[start:p.pos])
    if not moves and not diags:
        diags.append(Diagnostic("d.parser.end-of-input", _span_of(env.words),
                                expected=["a move"]))
    return Message(env, moves, lines), diags
