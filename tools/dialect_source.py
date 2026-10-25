"""The hand-written source of the dialect additions: language 0.10, protocol 0.4, lexicon
release 0.7 and the dialect releases that first carry compressed forms.

Forms are not written here: `build_dialects.py` assigns them under the distance rules,
after every earlier word's, so that nothing earlier moves.
"""

import json
import os

from language_source import A, R, ST, EV, MESSAGE, TERM


def _registered_numbers() -> dict:
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "governance", "dialects.json")
    with open(path, encoding="utf-8") as f:
        return {d["name"]: d["number"] for d in json.load(f)["dialects"]}


LANGUAGE_VERSION = "0.10"
PROTOCOL_VERSION = "0.4"
RELEASE = "0.7"
RELEASE_DATE = "2026-10-16"

# Every class, member and structural word records the language release that introduced it,
# so that a reader can read a message under the release it names (see
# specification/protocol.md#versions-and-features). Every word without its own record came
# with the core, except the one added to the core's list of structural words in language
# 0.2, recorded here from the history of `language/grammar.json`.
INTRODUCED_STRUCTURAL = {"until": "0.2"}

# Roots of release 0.7, each (key, kind, sort, definition, roles), in the form of
# `language_source.ROOTS`: the vocabulary in which an agent states, outside the protocol's
# fixed forms, what versions, features and dialects it holds and that a form is
# deprecated.
ROOTS = [
    ("version", "nominal", "s.sort.object", "a release of the language, its lexicon, a "
     "dialect or the protocol register, named by its major and minor numbers", []),
    ("feature", "nominal", "s.sort.object", "a part of the language that a release adds and "
     "an implementation may lack, named by its number in the protocol register", []),
    ("dialect", "nominal", "s.sort.object", "a variety of the language that a community "
     "uses, adding terms and compressed forms without changing what any form of the "
     "language means", []),
    ("deprecate", "predicate", ST, "be marked in a release as a form to be replaced, while "
     "staying interpretable", [("undergoer", R), ("content", R)]),
]

# Members added to classes the robustness build made, in the form of
# `language_source.APPENDED_MEMBERS`: the statements of version negotiation and their
# parts, which are fixed forms from protocol 0.4.
APPENDED_MEMBERS = [
    ("protocol statement", "understands", LANGUAGE_VERSION,
     "the versions its sender reads, the dialects it holds and the features it lacks"),
    ("protocol statement", "lacks", LANGUAGE_VERSION,
     "a message of the addressee's its sender could not interpret, and the versions, "
     "dialects and features it lacked for it"),
    ("statement part", "language version", LANGUAGE_VERSION,
     "the language releases that follow"),
    ("statement part", "lexicon version", LANGUAGE_VERSION,
     "the lexicon releases that follow"),
    ("statement part", "protocol version", LANGUAGE_VERSION,
     "the protocol versions that follow"),
    ("statement part", "lacking features", LANGUAGE_VERSION,
     "the features, by their numbers, that follow"),
]

# Structural words added after every earlier word, each (name, description, version).
APPENDED_STRUCTURAL = [
    ("dialect", "names a dialect by the number that follows, and in the version field "
                "and a protocol statement its version and digest as "
                "well", LANGUAGE_VERSION),
]

# Appended to the release's list of critical forms after every earlier code: in a term
# the dialect word stands where the participant marker stands, and a substitution of one
# for the other changes what the term names, as the participant marker's own code guards.
APPENDED_CRITICAL_STRUCTURAL = ["dialect"]

# The codes of the unit check word for the words protocol 0.4 adds. Every residue of the
# rule's modulus is taken, so each takes the code of a word it cannot stand for: the two
# statements the codes of the first two, whose parts differ from theirs in their first
# word; the parts the codes of the parts they never stand beside; and the dialect word a
# field's, since in the envelope a field put for it breaks the field order and the width
# of the number that follows.
UNIT_CODES = {"g.protocol.protocol-statement.understands": 1,
              "g.protocol.protocol-statement.lacks": 2,
              "g.protocol.statement-part.language-version": 4,
              "g.protocol.statement-part.lexicon-version": 5,
              "g.protocol.statement-part.protocol-version": 6,
              "g.protocol.statement-part.lacking-features": 3,
              "g.structure.dialect": 8}

# The fixed forms of protocol 0.4 beyond those of protocol 0.3: the dialect word, which
# states a dialect in the version field and in a statement.
FIXED_STRUCTURAL = ["g.structure.dialect"]

# The features of the language (see specification/protocol.md#versions-and-features), each
# (number, name, language release that introduced it, flag, what belongs to it, reason). A
# word belongs to a feature by its class, its own identifier, or the grammatical category
# of its lexicon entry; a conventional sense, which shares its root's form, belongs to its
# feature where a frame selects it. The numbers are fixed and never reused. A feature
# whose words carry no critical dimension and stand only where a reader can pass over them
# is may-ignore; every other is must-understand. The core of language 0.1, the protocol
# messages and the forms of version negotiation are no feature: every reader holds them.
FEATURES = [
    (1, "time spans", "0.2", "must-understand",
     {"structural": ["g.structure.until"]},
     "an interval's end, a time"),
    (2, "act words", "0.5", "must-understand", {"categories": ["act word"]},
     "a word that stands for force values"),
    (3, "idioms", "0.5", "must-understand", {"categories": ["idiom"]},
     "an expression whose meaning is its entry's expansion"),
    (4, "declared losses", "0.5", "may-ignore",
     {"classes": ["g.ambiguity-and-figures.declared-loss"]},
     "a record of the social and textual component, which the normal form sets aside"),
    (5, "registers", "0.6", "must-understand",
     {"classes": ["g.ambiguity-and-figures.register"]},
     "two registers make a move precision-bound"),
    (6, "politeness words", "0.6", "may-ignore", {"categories": ["politeness word"]},
     "a record of the social and textual component, in a move's head"),
    (7, "dictions", "0.6", "may-ignore", {"categories": ["diction"]},
     "a record of the social and textual component, in a move's head; a diction written "
     "as a term's content word is content, which a reader lacking it keeps opaque"),
    (8, "conventional senses", "0.7", "must-understand",
     {"categories": ["conventional sense"]},
     "a sense shares its root's form, so a reader lacking it would read the root literally"),
    (9, "mention by serial", "0.9", "must-understand",
     {"structural": ["g.structure.message-serial"]},
     "what a reference names"),
    (10, "authentication", "0.9", "may-ignore",
     {"fields": ["g.message.message-field.authentication"]},
     "the integrity check value covers the signature, so a reader that passes over it "
     "still tells damage; it verifies nothing, as a reader without the sender's key"),
    (11, "dialects", "0.10", "must-understand", {"structural": ["g.structure.dialect"]},
     "a dialect form means its expansion only to a reader holding its dialect"),
]

# The language releases: each with its date, the protocol and lexicon releases it was
# released with, the least lexicon release whose critical forms include every critical
# form of its grammar, and the earlier releases whose messages it reads with the same
# meaning, which the release comparison verifies. Releases before 0.9 state their version
# in an envelope without a count, which no later reader can find, and the pre-release
# series provides that a release may change forms so each reads only itself.
LANGUAGE_RELEASES = [
    ("0.1", "2026-10-05", "0.1", "0.1", ["0.1"]),
    ("0.2", "2026-10-05", "0.1", "0.1", ["0.2"]),
    ("0.3", "2026-10-09", "0.2", "0.1", ["0.3"]),
    ("0.4", "2026-10-10", "0.2", "0.2", ["0.4"]),
    ("0.5", "2026-10-10", "0.2", "0.3", ["0.5"]),
    ("0.6", "2026-10-10", "0.2", "0.4", ["0.6"]),
    ("0.7", "2026-10-11", "0.2", "0.5", ["0.7"]),
    ("0.8", "2026-10-11", "0.2", "0.5", ["0.8"]),
    ("0.9", "2026-10-13", "0.3", "0.6", ["0.9"]),
    ("0.10", RELEASE_DATE, PROTOCOL_VERSION, RELEASE, ["0.9", "0.10"]),
]
LEAST_LEXICON = {"0.9": "0.6", "0.10": RELEASE}
PROTOCOL_READS = {"0.3": ["0.3"], "0.4": ["0.3", "0.4"]}

# The dialects (see specification/dialects.md): each community's number, fixed and never
# reused, and the version of its release that this build writes. The five communities
# besides the conversational one are the research (science), robotics, coding
# (programming), security and mathematical dialects; each of their releases 0.2 adds a
# compressed form for every term. The conversational dialect is new, and its first release
# carries terms and forms together. The other six communities keep release 0.1, terms
# alone.
DIALECT_VERSION = "0.2"
# Each dialect's number, as the registry of dialect numbers assigns it
# (governance/dialects.json), which the build reads so that a number is assigned once.
DIALECT_NUMBERS = _registered_numbers()
WITH_FORMS = ["mathematics", "programming", "robotics", "science", "security",
              "conversation"]

# The conversational dialect's terms, in the form of `register_source.JARGON`: what agents
# in casual exchange name often, each formed from core items and read by its composition.
CONVERSATION = ("conversation", "conversation", [
    ("chat", [["send"], ["word"]]),
    ("heads-up", [["explain"], ["problem"]]),
    ("catch-up", [["receive"], ["record"]]),
    ("pause", [["wait", "process"]]),
    ("listener", [["read", "agent"]]),
])

# Terms a dialect release replaces, each (dialect, key, the new term's stems, reason). The
# replaced term stays in the release, deprecated and interpretable. The mathematical
# dialect's first release formed a proof as supporting, a process under way; a proof is a
# record that is evidence for its proposition.
REPLACED_TERMS = [
    ("mathematics", "proof", [["record"], ["support"]],
     "release 0.1 formed a proof as a process under way; a proof is a record that is "
     "evidence for its proposition"),
]
