"""The hand-written source of the protocol's repair and authentication additions: language
0.9, protocol 0.3 and lexicon release 0.6.

Forms are not written here: `build_robustness.py` assigns them under the distance rules,
after every earlier word's, so that nothing earlier moves.
"""

from language_source import A, MESSAGE, R, ST, EV

LANGUAGE_VERSION = "0.9"
PROTOCOL_VERSION = "0.3"
RELEASE = "0.6"
RELEASE_DATE = "2026-10-13"

# Roots of release 0.6, each (key, kind, sort, definition, roles), in the form of
# `language_source.ROOTS` (specification/protocol.md#protocol-messages): the vocabulary a
# report of failure draws on that the first release left out, forgetting a record whose
# reduced entry is kept and authenticating a message; and the act each addressee commits
# itself to, acknowledging, whose event time states its quiet interval.
ROOTS = [
    ("forget", "predicate", EV, "cease to hold the content of a record, keeping the record "
     "that one held it", [("actor", A), ("undergoer", R)]),
    ("authenticate", "predicate", EV, "establish, by a key one holds, that a message was "
     "made by the agent the key belongs to", [("actor", A), ("undergoer", R)]),
    ("acknowledge", "predicate", EV, "state to a sender which of its messages one holds",
     [("actor", A), ("recipient", A)]),
]

# Members added to a class after the release that fixed the class, in the form of
# `language_source.APPENDED_MEMBERS`.
APPENDED_MEMBERS = [
    ("message field", "authentication", LANGUAGE_VERSION,
     "a signature over the canonical serialisation of the whole message, its claims of "
     "sender and time included, by a scheme the field names"),
]

# Structural words added after every earlier word, each (name, description, version).
# The mention of a message by its channel and serial names what its speaker never
# received, whose first entry it cannot know.
APPENDED_STRUCTURAL = [
    ("message serial", "makes the target of a reference a message, by its sender, its "
                       "serial and the recipients of its channel",
     LANGUAGE_VERSION),
]

# Appended to the release's list of critical forms after every earlier code: a
# substitution of the message serial for the message target, or of either for another
# word, changes what a reference names, as the message target's own code guards.
APPENDED_CRITICAL_STRUCTURAL = ["message serial"]

# Classes added by this version, each (group, name, members, serves, applies to, scope,
# reason). Their words are the fixed forms of the protocol register: the forms of
# the acknowledgement, the request to send again and the statement of loss, which mean the
# same in every version (specification/protocol.md#versions-and-features). None is
# critical: a statement carries a check word of its own, computed by a fixed rule over
# fixed codes, so that a reader of any version can check it.
APPENDED_CLASSES = [
    ("protocol", "protocol statement", ["holds", "send again", "not held"],
     "s.sort.message", "a protocol message", MESSAGE,
     "what a protocol message states: the messages its sender holds of its addressee's, "
     "those it asks to be sent again, or those it cannot send again"),
    ("protocol", "statement part", ["channel", "serials", "entries"],
     "s.sort.message", "a protocol statement", MESSAGE,
     "a channel by the recipients of the addressee's messages on it, the serials that "
     "follow, and entries of the addressee's by their numbers"),
]

# The fixed widths of a protocol message's numbers, which a later version keeps.
FIXED_WIDTHS = {"identifier width": 6, "check value width": 9}

# The fixed forms: every word a protocol message can hold, by the identifier of its class
# or member. A later version keeps each with its form and its meaning, and keeps the rule
# of the unit check word.
FIXED_CLASSES = ["g.message.message-field", "g.message.word-count", "g.message.forwarded",
                 "g.numbers.numeral", "g.numbers.check-word", "g.protocol.protocol-statement",
                 "g.protocol.statement-part"]

# The unit check word of the envelope and of a protocol statement
# (specification/protocol.md#the-unit-check-word): each word between the unit's count and
# its check word, at position i counting from 0, adds its code multiplied by (i mod 10) +
# 1, and the sum is taken modulo 11 and written as the number check word of that value.
# Numerals are protected by the check words of their numbers, which weigh digits alone, so
# the decimal point has a code of its own and the other signs of a number, which no number
# of an envelope or a statement holds, share one; a check word is told from a numeral and
# from every other word by its own code; the fields of the envelope share one code, since
# their order is fixed and a field put for another breaks it; and a payload has none,
# since what it carries is checked by what it is for. The rule is fixed, so that a reader
# of any version checks a protocol message alike.
UNIT_CHECK_MODULUS = 11
UNIT_CODES = {"g.numbers.check-word": 7, "g.protocol.protocol-statement.holds": 1,
              "g.protocol.protocol-statement.send-again": 2,
              "g.protocol.protocol-statement.not-held": 3,
              "g.protocol.statement-part.channel": 4,
              "g.protocol.statement-part.serials": 5,
              "g.protocol.statement-part.entries": 6,
              "g.message.message-field": 8, "g.message.forwarded": 8,
              "g.numbers.numeral.decimal-point": 9, "g.numbers.numeral.negative": 10,
              "g.numbers.numeral.ratio": 10, "g.numbers.numeral.exponent": 10,
              "g.numbers.numeral.interval": 10}

# The check values are widened from six numerals to nine
# (specification/protocol.md#the-check-values): an edit that only the integrity check
# value catches passes it with probability one in 10^9 rather than one in 10^6.
CHECK_VALUE_WIDTH = 9

# The defaults of the protocol register for the rules of repair, in seconds and times
# (specification/protocol.md#channels-acknowledgement-and-repair). An addressee's own
# commitment to acknowledge within a duration replaces the quiet interval for it.
REPAIR_DEFAULTS = {
    "quiet interval": 30,
    "interval before sending again": 120,
    "times sent again": 4,
}

# Authentication schemes, by the number the authentication field states.
AUTHENTICATION_SCHEMES = {
    1: {"name": "Ed25519", "specification": "RFC 8032 § 5.1, pure Ed25519",
        "signature bytes": 64, "public key bytes": 32},
}
