"""The hand-written source of the registers: the class the grammar of language 0.6 adds,
lexicon release 0.4, the settings of the eight registers and the jargon of the eleven
communities of the dialects (specification/dialects.md).

Forms are not written here: `build_registers.py` assigns them under the distance rules,
after every earlier word's, so that nothing earlier moves.
"""

from language_source import MOVE

RELEASE = "0.4"
JARGON_VERSION = "0.1"
REGISTER_CLASS = "g.ambiguity-and-figures.register"

# The class language 0.6 adds, in the form of `convention_source.APPENDED_CLASSES`. A
# register is a setting of the social and textual component with the modes it admits
# (specification/lexicon.md#registers); a move states the one its whole surface is in, and
# where it states none it is in the standard register, a declared default.
APPENDED_CLASSES = [
    ("ambiguity and figures", "register",
     ["raw", "protocol", "standard", "explanatory", "formal", "casual", "playful",
      "ceremonial"],
     ("default", "standard", "the standard register, ordinary exchange"), None,
     "s.component.social-and-textual-component", "a move", MOVE,
     "0.6", "the register the move's whole surface is in"),
]

# The register is appended to the list of critical forms after every earlier code: two
# registers are precision-bound by default
# (specification/grammar.md#precision-bound-moves), so a substitution of one register word
# by another can change the rules a move is held to.
APPENDED_CRITICAL_RELEASE_4 = ["register"]

ALL = ["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7"]

# The registers' settings, and what the checker and the generator read of them.
# `vocabulary` names the marked synonyms the register writes, `politeness` its politeness
# word, `syntax` whether siblings stand in canonical order, `formulas` whether it admits
# the formulas of the conventional expressions
# (specification/lexicon.md#conventional-expressions-and-idioms), and `shared context`
# whether its modes admit naming an entry in place of restating it.
REGISTERS = [
    ("R0", "raw", "exchange among agents of one system",
     ["full explicitness", "normal expression", "compression"], False,
     {"vocabulary": "technical", "morphology": "minimal", "syntax": "canonical",
      "ellipsis": "declared defaults, inheritance, shared context", "politeness": "none",
      "discourse structure": "none",
      "compression": "conventional expressions, dialect forms", "prosody": "flat",
      "orthography": "transliteration"},
     "technical", None, False),
    ("R1", "protocol", "coordination under the protocol",
     ["full explicitness", "normal expression"], True,
     {"vocabulary": "technical", "morphology": "full", "syntax": "canonical",
      "ellipsis": "declared defaults, inheritance", "politeness": "neutral",
      "discourse structure": "fixed", "compression": "conventional expressions",
      "prosody": "flat", "orthography": "transliteration"},
     "technical", None, True),
    ("R2", "standard", "ordinary exchange",
     ["full explicitness", "normal expression", "compression", "idiom"], False,
     {"vocabulary": "standard", "morphology": "full", "syntax": "free",
      "ellipsis": "declared defaults, inheritance, shared context", "politeness": "neutral",
      "discourse structure": "as the exchange needs",
      "compression": "conventional expressions, dialect forms, idioms", "prosody": "neutral",
      "orthography": "native"},
     None, None, True),
    ("R3", "explanatory", "explanation to a human reader",
     ["full explicitness", "normal expression", "creative expression"], False,
     {"vocabulary": "plain", "morphology": "full", "syntax": "free",
      "ellipsis": "declared defaults, inheritance", "politeness": "courteous",
      "discourse structure": "signposted",
      "compression": "conventional expressions, marked figures", "prosody": "expressive",
      "orthography": "native"},
     None, "courteous", True),
    ("R4", "formal", "specification and proof", ["full explicitness", "normal expression"],
     True,
     {"vocabulary": "technical", "morphology": "full", "syntax": "canonical",
      "ellipsis": "declared defaults, inheritance", "politeness": "neutral",
      "discourse structure": "sectioned", "compression": "conventional expressions",
      "prosody": "measured", "orthography": "native"},
     "technical", None, True),
    ("R5", "casual", "informal exchange", ["normal expression", "compression", "idiom"],
     False,
     {"vocabulary": "informal", "morphology": "reduced", "syntax": "free",
      "ellipsis": "declared defaults, inheritance, shared context", "politeness": "familiar",
      "discourse structure": "loose",
      "compression": "conventional expressions, dialect forms, idioms",
      "prosody": "expressive", "orthography": "native"},
     "informal", "familiar", True),
    ("R6", "playful", "humour and play", ["normal expression", "idiom", "creative expression"],
     False,
     {"vocabulary": "informal", "morphology": "full", "syntax": "marked",
      "ellipsis": "declared defaults, inheritance", "politeness": "familiar",
      "discourse structure": "loose",
      "compression": "conventional expressions, idioms, marked figures",
      "prosody": "expressive", "orthography": "native"},
     "informal", "familiar", True),
    ("R7", "ceremonial", "occasions of high formality",
     ["full explicitness", "normal expression", "idiom"], False,
     {"vocabulary": "ornamental", "morphology": "honorific", "syntax": "marked",
      "ellipsis": "declared defaults, inheritance", "politeness": "elaborate",
      "discourse structure": "formulaic openings and closings",
      "compression": "conventional expressions, idioms", "prosody": "measured",
      "orthography": "native, ceremonial forms"},
     "ornamental", "deferential", True),
]

# Where each marking may be written: the vocabulary of a register-marked synonym, and the
# politeness words, by the registers whose settings name them.
MARKED = {"technical": ["R0", "R1", "R4"], "informal": ["R5", "R6"], "ornamental": ["R7"]}

# Register-marked synonyms (synonym pairs that differ in register): each has its base's
# category, sort and roles, and its expansion is its base, so that the normal form writes
# the base. Each is (key, the base's key, the vocabulary it belongs to).
SYNONYMS = [
    ("operate", "run", "technical"),
    ("hum", "run", "informal"),
    ("proceed", "run", "ornamental"),
    ("daemon", "service", "technical"),
    ("box", "service", "informal"),
    ("establishment", "service", "ornamental"),
    ("audit", "examine", "technical"),
    ("eyeball", "examine", "informal"),
    ("scrutinise", "examine", "ornamental"),
]

# The register-marked derivation: a suffix whose formation keeps its base's sort and roles
# and adds only the deference the ceremonial register shows, which the normal form sets
# aside.
HONORIFIC = ("honorific", "nominal", None, "the base, named with deference", [])

# Politeness words (specification/lexicon.md#politeness-words-and-dictions): each records
# the relation between participants, written in a move's head, and never alters force. The
# neutral politeness of the protocol, standard and formal registers is the absence of one,
# and raw exchange admits none.
POLITENESS = [
    ("courteous", "the move is addressed with courtesy, as to a reader the speaker serves",
     ["R3"]),
    ("familiar", "the move is addressed as between familiars", ["R5", "R6"]),
    ("deferential", "the move is addressed with elaborate deference, as on an occasion of "
     "high formality", ["R7"]),
]

# Dictions (specification/lexicon.md#politeness-words-and-dictions): each a word written
# in a move's head to declare the move's diction, and a nominal a speaker can name in
# content, so that a request for a diction is a request whose content is that the hearer
# write in it. `mode` is the mode the generator chooses for the diction among those the
# register admits, the first admitted of the list; `vocabulary` the marking it prefers. A
# diction never alters force or standing: what distinguishes a tentative move from an
# authoritative one in the core is the strength and the authority it states.
DICTIONS = [
    ("terse", "spare: the fewest words the hearer can recover the meaning from",
     ["compression", "idiom", "normal expression", "full explicitness"], None),
    ("neutral", "unmarked: the ordinary realisation of the register",
     ["normal expression", "full explicitness"], None),
    ("elaborate", "full: every value stated where the register admits it",
     ["full explicitness", "normal expression"], None),
    ("technical", "technical: the technical vocabulary where the register admits it",
     ["normal expression", "full explicitness"], "technical"),
    ("poetic", "poetic: figures and the sound of the words where the register admits them",
     ["creative expression", "normal expression", "full explicitness"], None),
    ("humorous", "humorous: the idioms and play the register admits",
     ["idiom", "creative expression", "normal expression", "full explicitness"], None),
    ("cautious", "cautious: nothing left to a default the hearer must supply",
     ["full explicitness", "normal expression"], None),
    ("authoritative", "authoritative in manner; the authority a move claims is stated "
     "apart", ["normal expression", "full explicitness"], None),
    ("tentative", "tentative in manner; the strength a move claims is stated apart",
     ["normal expression", "full explicitness"], None),
    ("diplomatic", "diplomatic: attentive to the hearer's standing in the exchange",
     ["normal expression", "full explicitness"], None),
    ("adversarial", "adversarial: pressing the speaker's position against the hearer's",
     ["normal expression", "full explicitness"], None),
    ("collaborative", "collaborative: building on the hearer's moves toward a shared aim",
     ["normal expression", "full explicitness"], None),
]

# The jargon of the communities (specification/dialects.md#terms): each community a
# dialect, each of its terms formed from core items by the mechanisms of word formation
# and read by its composition, so that a hearer outside the community computes what it
# means, and no dialect changes the meaning of a core form. A term is (the community's
# name for it, its stems), each stem a root's key followed by the keys of its suffixes; a
# compound's first stem is its head.
JARGON = [
    ("mathematics", "mathematics", [
        ("metric", [["measure", "instrument"]]),
        ("isomorphism", [["correspond", "property"]]),
        ("cardinality", [["count", "result"]]),
        ("proof", [["support", "process"]]),
        ("subset", [["part"], ["share"]]),
    ]),
    ("programming", "programming", [
        ("deploy", [["cause"], ["run"]]),
        ("suite", [["record"], ["examine"]]),
        ("crash", [["break"], ["service"]]),
        ("log", [["write"], ["operation"]]),
        ("debugger", [["find", "agent"], ["fault"]]),
    ]),
    ("machine learning", "machine-learning", [
        ("dataset", [["data"], ["record"]]),
        ("inference", [["interpret", "process"]]),
        ("weight update", [["change"], ["data"]]),
        ("training", [["change"], ["memory"]]),
        ("loss", [["fault"], ["measure"]]),
    ]),
    ("robotics", "robotics", [
        ("actuator", [["move", "instrument"]]),
        ("sensor", [["detect", "instrument"]]),
        ("gripper", [["take", "instrument"]]),
        ("odometry", [["measure"], ["move"]]),
        ("payload", [["move", "undergoer"]]),
    ]),
    ("science", "science", [
        ("sample", [["take", "undergoer"]]),
        ("observation", [["detect", "process"]]),
        ("finding", [["find", "result"]]),
        ("reading", [["evidence"], ["measure"]]),
        ("replication", [["make"], ["correspond"]]),
    ]),
    ("philosophy", "philosophy", [
        ("sense", [["meaning", "abstraction"]]),
        ("contradiction", [["contradict", "nominalisation"]]),
        ("causation", [["cause", "process"]]),
        ("warrant", [["support", "property"]]),
        ("normativity", [["standard", "property"]]),
    ]),
    ("linguistics", "linguistics", [
        ("lexeme", [["word", "abstraction"]]),
        ("interpretation", [["interpret", "result"]]),
        ("meaningfulness", [["mean", "property"]]),
        ("corpus", [["record"], ["language"]]),
        ("writer", [["write", "agent"]]),
    ]),
    ("security", "security", [
        ("access denial", [["forbid"], ["open"]]),
        ("lock", [["shut", "instrument"]]),
        ("exposure", [["open"], ["memory"]]),
        ("tamper check", [["examine"], ["corrupt"]]),
        ("tampered item", [["corrupt", "undergoer"]]),
    ]),
    ("databases", "databases", [
        ("query", [["find"], ["record"]]),
        ("index", [["find", "instrument"]]),
        ("purge", [["delete", "process"]]),
        ("schema", [["record", "abstraction"]]),
        ("commit", [["store"], ["record"]]),
    ]),
    ("planning", "planning", [
        ("allocation", [["allocate", "result"]]),
        ("dependency", [["need", "nominalisation"]]),
        ("milestone", [["arrive", "result"]]),
        ("backlog", [["wait"], ["operation"]]),
        ("resource plan", [["resource"], ["allocate"]]),
    ]),
    ("negotiation", "negotiation", [
        ("bid", [["give"], ["price"]]),
        ("deal", [["share"], ["give"]]),
        ("leverage", [["possess", "property"]]),
        ("concession", [["decrease"], ["price"]]),
        ("stalemate", [["wait", "result"]]),
    ]),
]
