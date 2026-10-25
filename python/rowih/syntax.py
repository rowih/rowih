"""The AST (specification/grammar.md#the-productions): what was written, the words where
they stand, each value at the unit where it was written, siblings in the order written and
every reference unresolved. Every node keeps the words it was read from."""
from __future__ import annotations

from dataclasses import dataclass, field

from .lexer import Word

DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
NUMERAL_SYMBOL = {d: str(i) for i, d in enumerate(DIGITS)}
NUMERAL_SYMBOL.update({"decimal point": ".", "negative": "-", "ratio": "/", "exponent": "e",
                       "interval": "~"})


@dataclass
class Number:
    numerals: list          # member names, from the most significant
    check: int
    words: list

    @property
    def text(self) -> str:
        """The numerals as a compact string: digits, '.', '-', '/', 'e', '~'."""
        return "".join(NUMERAL_SYMBOL[n] for n in self.numerals)

    @property
    def digits(self) -> str:
        return "".join(NUMERAL_SYMBOL[n] for n in self.numerals if n in DIGITS)

    def integer(self) -> int:
        return int(self.digits)


@dataclass
class Value:
    member: str             # the member's identifier
    word: Word

    @property
    def class_id(self) -> str:
        return self.member.rsplit(".", 1)[0]

    @property
    def name(self) -> str:
        return self.member.rsplit(".", 1)[1]


@dataclass
class ContentWord:
    word: Word


@dataclass
class Reference:
    kind: str               # names, mentions
    target: str             # entry, message, serial
    author: Number
    number: Number
    expected: list = field(default_factory=list)   # Values: the kind expected
    status: Value | None = None
    part: Number | None = None
    words: list = field(default_factory=list)
    # the recipients of the channel a message named by its serial was sent on
    # (specification/notation.md#references)
    recipients: list = field(default_factory=list)


@dataclass
class TimeSpec:
    kind: str               # now, absolute, offset, relation, interval, duration, rate
    number: Number | None = None
    unit: Value | None = None
    anchor: Value | None = None
    relation: Value | None = None
    reference: object = None    # a TimeSpec, a Value naming a time index, or an IndexOf
    until: object = None        # the second TimeSpec of an interval
    comparator: Value | None = None     # the bound of a duration or a rate


@dataclass
class IndexOf:
    """A time index of a named unit: SAME name time-index
    (specification/notation.md#times)."""
    same: "Same"
    index: Value


@dataclass
class TimeValue:
    index: Value
    spec: TimeSpec


@dataclass
class Quantity:
    comparator: Value | None
    number: Number
    unit: object = None     # a Value (time unit) or a ContentWord (unit root)
    per: Value | None = None
    calibration: Number | None = None   # a numeric strength's calibrating participant


@dataclass
class Party:
    number: Number


@dataclass
class DialectName:
    """`DIALECT number` in a term: the dialect whose number follows (language 0.10)."""
    number: Number


@dataclass
class Same:
    name: Number
    words: list = field(default_factory=list)


@dataclass
class Filler:
    """A role, a provenance link, a figure's relation or the condition, with the
    constituent it marks."""
    role: Value
    filler: object


@dataclass
class Unit:
    kind: str               # assertion, situation, term
    name: Number | None
    parts: list
    open_word: Word
    close_word: Word | None = None


@dataclass
class Wall:
    kind: Value
    type_length: Number | None = None
    type_payload: Word | None = None
    length: Number | None = None
    payload: Word | None = None
    words: list = field(default_factory=list)       # quoted words


@dataclass
class ReadingSet:
    kind: Value
    readings: list


@dataclass
class Idiom:
    """An extragrammatical idiom, recognised by its words where a constituent stands,
    which no production of the grammar admits
    (specification/lexicon.md#conventional-expressions-and-idioms)."""
    entry: str
    words: list


@dataclass
class Head:
    adds: list = field(default_factory=list)        # Values of the force classes
    change: list = field(default_factory=list)
    authority: Value | None = None
    authority_term: Unit | None = None
    deadline: TimeSpec | None = None
    named: Reference | None = None
    also_named: list = field(default_factory=list)  # a summary's further References
    relations: list = field(default_factory=list)   # ContentWords
    precision_bound: Value | None = None
    act: Word | None = None     # the act word that wrote the force values, if one did
    losses: list = field(default_factory=list)      # Values of the declared loss
    # the social and textual component the head states
    # (specification/lexicon.md#politeness-words-and-dictions): the politeness word and
    # the diction, words of the lexicon, and the register
    politeness: Word | None = None
    diction: Word | None = None
    register: Value | None = None


@dataclass
class Move:
    index: int
    count: Number
    head: Head
    constituents: list
    check: Word
    body: list              # the words the count states, the check word last
    words: list             # every word of the move, the count's included


@dataclass
class Authentication:
    """The authentication field (specification/protocol.md#authentication): the scheme it
    names, and the signature, carried as a payload."""
    scheme: Number
    length: Number
    signature: bytes
    words: list             # the field's words, its own word first


@dataclass
class Envelope:
    sender: Number
    recipients: list
    time: Number
    version: list
    identifier: Number
    first_entry: Number      # the number of the entry the first move adds (protocol 0.2)
    forwarded: Value | None
    semantic: Number | None
    integrity: Number | None
    words: list
    integrity_words: list = field(default_factory=list)
    authentication: Authentication | None = None
    # each dialect the message names, (number, version, digest), in ascending order of
    # number (specification/protocol.md#the-envelope)
    dialects: list = field(default_factory=list)

    @property
    def is_protocol(self) -> bool:
        """Whether the message is a protocol message, which takes no serial on its
        channel and adds no entry (protocol 0.3)."""
        return self.identifier.integer() == 0


@dataclass
class Statement:
    """The statement of a protocol message (specification/protocol.md#protocol-messages):
    what it states, `holds`, `send-again`, `not-held`, `understands` or `lacks`, and its
    parts, each a channel by its recipients with serials, the addressee's entries by their
    numbers, a list of versions, a dialect, or features."""
    kind: str
    parts: list             # ("channel", (recipient, ...), (serial, ...)) | ("entries", (n, ...))
    #                         | ("language" | "lexicon" | "protocol", (version, ...))
    #                         | ("dialect", number, version, digest) | ("lacking", (n, ...))
    count: Number
    check: Word
    words: list             # every word of the statement, the count's included


@dataclass
class Message:
    envelope: Envelope
    moves: list
    # The words of every move as written, rejected moves included, one list a move: what
    # the canonical serialisation, the integrity check value and conversion read; for a
    # protocol message, the words of its statement.
    lines: list = field(default_factory=list)
    statement: Statement | None = None
