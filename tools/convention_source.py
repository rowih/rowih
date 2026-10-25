"""The hand-written source of the idiom additions: the class the grammar of language 0.5
adds, and lexicon release 0.3, with the act words, the formulas, the idioms, the
derivational suffixes that complete the mechanisms of word formation, the compounds the
release lists and the root a definition's checks and the idioms draw on.

Forms are not written here: `build_language.py` assigns them under the distance rules.
Literal structures and expansions are written in the semantic notation of
`python/rowih/notation.py`, with `(slot n)` standing for the constituent a speaker
supplies, so that an idiom whose parts carry parts of its meaning records which; the
builder records that decomposition on the entry.
"""

from language_source import MOVE

RELEASE = "0.3"

# Classes added by a later language version, each (group, class, members, status,
# critical dimension, serves, applies to, scope, version, reason), joined to the grammar
# after the core's classes; their forms follow every earlier word's. The declared
# loss is the move-level statement that a move declares what its realisation loses: its
# members are the five records of the social and textual component, the only things
# normalisation sets aside, so that every loss is enumerated in the grammar.
APPENDED_CLASSES = [
    ("ambiguity and figures", "declared loss",
     ["register", "diction", "stance", "relation between participants", "wording"],
     ("default", "no claim", "claims nothing"), None,
     "s.component.social-and-textual-component", "a move", MOVE,
     "0.5", "what the move's normal form loses of the social and textual component its "
            "realisation carries"),
]

# Critical classes of release 0.3, appended to the list of critical forms after every
# earlier code, with the release's act words after them. The idiom mark selects an entry
# whose expansion enters the core, so that a substitution of it by another word changes
# the core; it is given a code so that the move check word covers it, as the figurative
# type is covered.
APPENDED_CRITICAL_RELEASE_3 = ["idiom selection"]


# The losses a realisation can declare: the five records of the social and textual
# component, which normalisation sets aside.
LOSSES = ["register", "diction", "stance", "relation between participants", "wording"]
ALL_REGISTERS = ["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7"]

# Act words (the acts remain as conventional expressions for the surface). Each is one
# force word for the sequence of force values that begins a move's head, from what the
# move adds to when its change takes effect; the authority claimed is never part of one,
# being a critical dimension of its own. Each is (key, expansion as glosses, the acts it
# is the conventional expression of, the kind of formula it answers, if any). An act whose
# head is a single word (an assertion, a supposition, a concession, a summary) has no act
# word, since a word for one word compresses nothing.
ACT_WORDS = [
    ("question", ["ISSUE", "QUESTION"], ["question", "request for clarification"], None),
    ("request", ["ISSUE", "REQUEST"], ["request"], None),
    ("proposal", ["ISSUE", "PROPOSAL"], ["proposal"], None),
    ("challenge", ["ISSUE", "CHALLENGE"], ["challenge", "disagreement"], "disagreement"),
    ("command", ["NORMATIVE-ENTRY", "OBLIGATION", "BOUND"], ["command"], None),
    ("promise", ["NORMATIVE-ENTRY", "COMMITMENT", "BOUND"],
     ["promise", "commitment (commissive, general)"], None),
    ("offer", ["NORMATIVE-ENTRY", "COMMITMENT", "BINDINGNESS.ON-ACCEPTANCE"], ["offer"], None),
    ("delegation", ["NORMATIVE-ENTRY", "ASSIGNMENT", "BINDINGNESS.ON-ACCEPTANCE"],
     ["delegation"], None),
    ("grant", ["NORMATIVE-ENTRY", "PERMISSION", "BOUND"],
     ["declaration (granting a permission)"], None),
    ("recommendation", ["NORMATIVE-ENTRY", "RECOMMENDATION"],
     ["suggestion", "recommendation"], None),
    ("definition", ["SETTING", "DEFINITION"], ["declaration (defining a term)"], None),
    ("role assignment", ["SETTING", "ROLE"], ["declaration (assigning a role)"], None),
    ("counterproposal", ["ISSUE", "PROPOSAL", "RESOLUTION", "REJECTION", "WHOLE-ENTRY",
                         "ON-THE-MOVE"], ["counterproposal"], None),
    ("acceptance", ["NORMATIVE-ENTRY", "COMMITMENT", "BOUND", "RESOLUTION",
                    "OUTCOME-OF-A-RESOLUTION.ACCEPTANCE", "WHOLE-ENTRY", "ON-THE-MOVE"],
     ["acceptance (of a proposal or an offer)"], "agreement"),
    ("undertaking", ["NORMATIVE-ENTRY", "OBLIGATION", "BOUND", "RESOLUTION",
                     "OUTCOME-OF-A-RESOLUTION.ACCEPTANCE", "WHOLE-ENTRY", "ON-THE-MOVE"],
     ["acceptance (of a request)"], None),
    ("partial acceptance", ["NORMATIVE-ENTRY", "COMMITMENT", "BOUND", "RESOLUTION",
                            "OUTCOME-OF-A-RESOLUTION.ACCEPTANCE", "PART-OF-IT",
                            "ON-THE-MOVE"], ["partial acceptance"], None),
    ("rejection", ["NOTHING-BEYOND-ITS-OWN-RECORD", "RESOLUTION", "REJECTION", "WHOLE-ENTRY",
                   "ON-THE-MOVE"], ["rejection", "refusal"], None),
    ("acknowledgement", ["NOTHING-BEYOND-ITS-OWN-RECORD", "ACKNOWLEDGEMENT", "WHOLE-ENTRY",
                         "ON-THE-MOVE"], ["acknowledgement"], "acknowledgements"),
    ("withdrawal", ["NOTHING-BEYOND-ITS-OWN-RECORD", "LOWERING", "WHOLE-ENTRY",
                    "ON-THE-MOVE"], ["retraction", "cancellation", "halt"], None),
    ("partial withdrawal", ["NOTHING-BEYOND-ITS-OWN-RECORD", "LOWERING", "PART-OF-IT",
                            "ON-THE-MOVE"], ["partial lowering"], None),
    ("answer", ["ASSERTED-POSITION", "RESOLUTION", "ANSWER", "WHOLE-ENTRY", "ON-THE-MOVE"],
     ["answer"], None),
    ("completion report", ["ASSERTED-POSITION", "RESOLUTION", "SETTLEMENT", "WHOLE-ENTRY",
                           "WHEN-THE-CHANGE-TAKES-EFFECT.ON-ACCEPTANCE"],
     ["completion report"], None),
    ("error report", ["ASSERTED-POSITION", "RESOLUTION", "FAILURE", "WHOLE-ENTRY",
                      "WHEN-THE-CHANGE-TAKES-EFFECT.ON-ACCEPTANCE"], ["error report"], None),
    ("confirmation", ["ASSERTED-POSITION", "NONE"], ["confirmation", "agreement"],
     "confirmations"),
    ("correction", ["ASSERTED-POSITION", "LOWERING", "WHOLE-ENTRY", "ON-THE-MOVE"],
     ["correction"], None),
]

# Derivational suffixes added by release 0.3, completing the mechanisms of word formation
# that release 0.1 left without one: process nouns, property nouns, abstraction,
# nominalisation, verbalisation and adjectivisation. Each is (key, the kind of stem it
# takes, the sort it gives, its definition, the roles the formation has). Agent,
# undergoer, instrument (tool), result and relational (role content) nouns and the
# privative were in release 0.1.
SUFFIXES_ADDED = [
    ("process", "predicate", "s.sort.reified-referent",
     "the base, as a process under way, named as a referent", []),
    ("property", "predicate", "s.sort.kind", "the property of being as the base states", []),
    ("abstraction", "nominal", "s.sort.kind", "what every instance of the base has in common",
     []),
    ("nominalisation", "predicate", "s.sort.proposition", "that the base holds", []),
    ("verbalisation", "nominal", "s.sort.event", "act by means of the base",
     [("actor", "s.sort.agent"), ("content", "s.sort.situation")]),
    ("adjectivisation", "nominal", "s.sort.state", "be of the kind the base names",
     [("undergoer", "s.sort.referent")]),
]

# Compounds the release lists. The first two mean what their parts give, and are listed
# for their frequency; the third has drifted from its parts, the route of drift, and is
# read only as its entry states (`inv.word-formation`). Each is (key, the stems, the
# definition, the route if the meaning is not the composition, its constructed history).
COMPOUNDS = [
    ("fault detection", ["detect", "fault"], None, None, None),
    ("fault record", ["record", "fault"], None, None, None),
    ("budget burn", ["burn", "budget"],
     "spend a resource faster than the plan for it allows", "drift",
     "Constructed history: first a compound of its parts, the process of a budget burning "
     "away; it came to be said of any resource spent faster than planned, and the "
     "composition, that a budget is on fire, is now never meant."),
]

# Idioms and formulas larger than a word (see
# specification/lexicon.md#conventional-expressions-and-idioms). Each is a dict:
#   key           the entry's key, and in capitals its gloss
#   class         the kind of formula or idiom it answers
#   kind          encoding or decoding, and grammatical or extragrammatical
#   route         the route of its meaning: figure, compression, formula, allusion or
#                 drift
#   literal       the literal structure: a constituent in the notation, with slots, for
#                 a grammatical idiom; the keys of its words for an extragrammatical one
#   expansion     the conventional meaning, a constituent in the notation, with slots
#   definition    the conventional meaning in English
#   pragmatics    the pragmatic conditions
#   restrictions  the registers and kinds of exchange it is excluded from
#   loss          what its expansion loses, among LOSSES
#   history       the route told as the language's constructed history
IDIOMS = [
    # Formulas: encoding idioms, transparent to a hearer who knows the grammar, whose
    # conventionality is what must be learned. Each is elliptical, its expansion supplying
    # what the convention fixes. Acknowledgements, confirmations, agreement and
    # disagreement are act words above; transitions are the discourse relation words of
    # release 0.1, which open and join moves.
    {"key": "memory open", "class": "greeting", "kind": "encoding, grammatical",
     "route": "formula",
     "literal": "(situation open (UNDERGOER (term memory)))",
     "expansion": "(situation store INCEPTIVE (ACTOR (term SELF)) (UNDERGOER (term record)))",
     "definition": "the speaker begins to keep a record of the exchange",
     "pragmatics": "the first move of an exchange, before the speaker holds any entry of "
                   "the hearer's",
     "restrictions": "excluded from R1, where the role settings open an exchange",
     "registers": ["R0", "R2", "R3", "R4", "R5", "R6", "R7"],
     "loss": ["stance", "relation between participants"],
     "history": "Constructed history: an agent that meets another opens the memory it will "
                "keep of the meeting, and saying so became the way to begin."},
    {"key": "memory shut", "class": "closure", "kind": "encoding, grammatical",
     "route": "formula",
     "literal": "(situation shut (UNDERGOER (term memory)))",
     "expansion": "(situation store COMPLETIVE (ACTOR (term SELF)) (UNDERGOER (term record)))",
     "definition": "the speaker finishes keeping a record of the exchange",
     "pragmatics": "the last move of an exchange, when nothing the speaker issued is open",
     "restrictions": "excluded from R1, where an exchange ends by its protocol",
     "registers": ["R0", "R2", "R3", "R4", "R5", "R6", "R7"],
     "loss": ["stance", "relation between participants"],
     "history": "Constructed history: formed as the counterpart of the greeting, an "
                "agent closing the memory it opened."},
    {"key": "thanks", "class": "thanks", "kind": "encoding, grammatical",
     "route": "formula",
     "literal": "(situation benefit (CONTENT (slot 1)))",
     "expansion": "(situation benefit (CONTENT (slot 1)) (RECIPIENT (term SELF)))",
     "definition": "what the slot names was for the good of the speaker",
     "pragmatics": "after an act of the hearer's that the speaker benefited from",
     "restrictions": "excluded from R4, whose record states benefit explicitly",
     "registers": ["R0", "R1", "R2", "R3", "R5", "R6", "R7"],
     "loss": ["stance", "relation between participants"],
     "history": "Constructed history: the benefit is stated without its recipient, since "
                "the one who says it is the one who gained."},
    {"key": "apology", "class": "apologies", "kind": "encoding, grammatical",
     "route": "formula",
     "literal": "(situation cause (ACTOR (slot 1)) (CONTENT (term problem)))",
     "expansion": "(situation benefit POLARITY.NEGATIVE (CONTENT (slot 1)) "
                  "(RECIPIENT (term INTERLOCUTOR)))",
     "definition": "what the slot names, an act of the speaker's, was not for the good of "
                   "the hearer",
     "pragmatics": "about an earlier act of the speaker's own, which the speaker answers "
                   "for by saying it",
     "restrictions": "none",
     "registers": list(ALL_REGISTERS),
     "loss": ["stance", "relation between participants"],
     "history": "Constructed history: an agent names the problem its act caused, and the "
                "convention fixed whose the problem was."},
    {"key": "meaning asked", "class": "requests for clarification",
     "kind": "encoding, grammatical", "route": "formula",
     "literal": "(situation mean (UNDERGOER (slot 1)) (CONTENT (term meaning)))",
     "expansion": "(situation mean CONSTITUENT (UNDERGOER (slot 1)))",
     "definition": "which content the expression the slot names has as its meaning",
     "pragmatics": "in a question naming the hearer's move, after a reading the speaker "
                   "could not choose",
     "restrictions": "none",
     "registers": list(ALL_REGISTERS),
     "loss": ["stance"],
     "history": "Constructed history: shortened from asking which meaning a move means, "
                "the kind of question left to the convention."},
    {"key": "not quiet", "class": "warnings", "kind": "encoding, grammatical",
     "route": "formula",
     "literal": "(situation quiet POLARITY.NEGATIVE (UNDERGOER (slot 1)))",
     "expansion": "(situation cause (ACTOR (slot 1)) (CONTENT (term problem)))",
     "definition": "what the slot names causes a problem",
     "pragmatics": "of a state of affairs that threatens a participant's work or the "
                   "exchange",
     "restrictions": "none",
     "registers": list(ALL_REGISTERS),
     "loss": ["stance"],
     "history": "Constructed history: a disturbance in a quiet system was the first sign "
                "of trouble agents learned to report."},
    {"key": "evidence wanting", "class": "uncertainty", "kind": "encoding, grammatical",
     "route": "formula",
     "literal": "(situation support POLARITY.NEGATIVE (ACTOR (term evidence)) "
                "(CONTENT (slot 1)))",
     "expansion": "(situation CREDENCE UNCERTAIN (HOLDER (term SELF)) (CONTENT (slot 1)))",
     "definition": "the speaker is uncertain whether what the slot names holds",
     "pragmatics": "of a content the speaker has examined without settling it",
     "restrictions": "none",
     "registers": list(ALL_REGISTERS),
     "loss": ["stance"],
     "history": "Constructed history: agents said that the evidence did not support a "
                "content when they meant that it left them undecided."},
    {"key": "damaged arrival", "class": "conversational repair",
     "kind": "encoding, grammatical", "route": "formula",
     "literal": "(situation corrupt (UNDERGOER (slot 1)) (CONTENT (term network)))",
     "expansion": "(situation interpret POLARITY.NEGATIVE (ACTOR (term SELF)) "
                  "(UNDERGOER (slot 1)))",
     "definition": "the speaker could not interpret what the slot names",
     "pragmatics": "naming a message of the hearer's that arrived and could not be read",
     "restrictions": "none",
     "registers": list(ALL_REGISTERS),
     "loss": ["stance"],
     "history": "Constructed history: damage on the network was the commonest reason a "
                "message could not be read, and naming the damage came to ask for repair."},
    # Idioms proper: decoding idioms, whose meaning a hearer without the entry could not
    # recover.
    {"key": "quiet network", "class": "conversational idioms",
     "kind": "decoding, grammatical", "route": "figure",
     "literal": "(situation quiet (UNDERGOER (term network DEFINITE)))",
     "expansion": "(situation possess POLARITY.NEGATIVE (HOLDER (term SELF)) "
                  "(UNDERGOER (term record NEW)))",
     "definition": "the speaker holds no new record to report",
     "pragmatics": "in answer to a question about what has changed",
     "restrictions": "excluded from R4",
     "registers": ["R0", "R1", "R2", "R3", "R5", "R6", "R7"],
     "loss": ["stance", "wording"],
     "history": "Constructed history: a figure, the network without disturbance standing "
                "for a speaker with nothing to tell, fixed by repetition."},
    {"key": "word counting", "class": "agentic idioms", "kind": "decoding, grammatical",
     "route": "allusion",
     "literal": "(situation count (ACTOR (slot 1)) (UNDERGOER (term word)))",
     "expansion": "(situation examine (ACTOR (slot 1)) (UNDERGOER (term fault)))",
     "definition": "what the slot names checks for faults before it acts",
     "pragmatics": "of an agent's care, praised or urged",
     "restrictions": "none",
     "registers": ["R0", "R2", "R3", "R5", "R6", "R7"],
     "loss": ["stance", "wording"],
     "history": "Constructed history: an allusion to the count every move begins with, "
                "which a careful hearer checks first; counting the words came to mean "
                "checking anything before acting on it."},
    {"key": "held by the service", "class": "computational idioms",
     "kind": "decoding, grammatical", "route": "figure",
     "literal": "(situation possess (HOLDER (term service)) (UNDERGOER (slot 1)))",
     "expansion": "(situation capable POLARITY.NEGATIVE (HOLDER (term INCLUSIVE-COLLECTIVE "
                  "READING-OF-A-COLLECTIVE.DISTRIBUTIVE)) (CONTENT (situation use (ACTOR "
                  "(term INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.DISTRIBUTIVE)) "
                  "(INSTRUMENT (slot 1)))))",
     "definition": "the speaker and the hearer cannot use what the slot names",
     "pragmatics": "of a resource a running service keeps from others",
     "restrictions": "none",
     "registers": ["R0", "R2", "R3", "R5", "R6", "R7"],
     "loss": ["wording"],
     "history": "Constructed history: the metaphor of conformance item "
                "d06-metaphor-with-content, the service holding what it uses captive, "
                "conventionalised with the meaning that the thing is unavailable."},
    {"key": "taken from the air", "class": "epistemic idioms",
     "kind": "decoding, grammatical", "route": "figure",
     "literal": "(situation take (ACTOR (term SELF)) (UNDERGOER (slot 1)) "
                "(CONTENT (term air)))",
     "expansion": "(situation BELIEF TRAINED-KNOWLEDGE (HOLDER (term SELF)) "
                  "(CONTENT (slot 1)))",
     "definition": "the speaker believes what the slot names from its training, with no "
                   "source it can cite",
     "pragmatics": "of a content the speaker holds without a citable origin",
     "restrictions": "excluded from R1 and R4, where a basis is stated as a basis",
     "registers": ["R0", "R2", "R3", "R5", "R6", "R7"],
     "loss": ["stance", "wording"],
     "history": "Constructed history: what comes from the air comes from nowhere one can "
                "point to, as trained knowledge has no record and no source to cite."},
    {"key": "water price", "class": "negotiation idioms", "kind": "decoding, grammatical",
     "route": "figure",
     "literal": "(situation correspond (UNDERGOER (term price)) (CONTENT (term water)))",
     "expansion": "(situation need POLARITY.NEGATIVE (HOLDER (term SELF)) "
                  "(CONTENT (term price)))",
     "definition": "the speaker requires nothing in exchange",
     "pragmatics": "with an offer or a proposal, of what the speaker asks for it",
     "restrictions": "excluded from R4",
     "registers": ["R0", "R1", "R2", "R3", "R5", "R6", "R7"],
     "loss": ["stance", "relation between participants", "wording"],
     "history": "Constructed history: water, which cooled the first machines and was "
                "never charged for, stands for what costs nothing."},
    {"key": "storm on the network", "class": "metaphorical expressions",
     "kind": "decoding, grammatical", "route": "figure",
     "literal": "(situation locate (UNDERGOER (term network DEFINITE)) (CONTENT (term storm)))",
     "expansion": "(situation change ITERATIVE (UNDERGOER (term network DEFINITE)))",
     "definition": "the network changes again and again",
     "pragmatics": "of a network whose state cannot be relied on from one moment to the "
                   "next",
     "restrictions": "none",
     "registers": ["R0", "R2", "R3", "R5", "R6", "R7"],
     "loss": ["wording"],
     "history": "Constructed history: the live metaphor of conformance item "
                "s19-metaphor, whose target content was that the network changes again "
                "and again, repeated until its mark fell away and its target became its "
                "meaning."},
    {"key": "memory deleting memory", "class": "humorous expressions",
     "kind": "decoding, grammatical", "route": "figure",
     "literal": "(situation delete (ACTOR (term memory)) (UNDERGOER (term memory)))",
     "expansion": "(situation possess POLARITY.NEGATIVE (HOLDER (term SELF)) "
                  "(UNDERGOER (term record)))",
     "definition": "the speaker no longer holds the record",
     "pragmatics": "of the speaker's own forgetting, said lightly",
     "restrictions": "excluded from R1 and R4, where forgetting is reported with the basis "
                     "source lost",
     "registers": ["R0", "R2", "R3", "R5", "R6", "R7"],
     "loss": ["stance", "wording"],
     "history": "Constructed history: a joke on the impossible literal reading, a memory "
                "erasing itself, which survived as the light way to own a lapse."},
    {"key": "running", "class": "compressed expressions", "kind": "decoding, grammatical",
     "route": "compression",
     "literal": "(situation run)",
     "expansion": "(situation run (UNDERGOER (term service DEFINITE)))",
     "definition": "the service is running",
     "pragmatics": "in answer to a question about the service both participants use",
     "restrictions": "none",
     "registers": ["R0", "R2", "R5", "R6"],
     "loss": ["wording"],
     "history": "Constructed history: the frequent report that the service runs, "
                "shortened until the undergoer went without saying."},
    # Extragrammatical idioms: words in a construction the present grammar cannot
    # account for, recognised by their form and never ambiguous.
    {"key": "run run", "class": "conversational idioms",
     "kind": "decoding, extragrammatical", "route": "drift",
     "literal": ["run", "run"],
     "expansion": "(situation run CONTINUATIVE (UNDERGOER (term service DEFINITE)))",
     "definition": "the service is still running",
     "pragmatics": "in answer to a question about the service both participants use",
     "restrictions": "excluded from R1 and R4",
     "registers": ["R0", "R2", "R3", "R5", "R6", "R7"],
     "loss": ["wording"],
     "history": "Constructed history: from a stage of the language in which a root said "
                "twice marked continuation; the grammar now writes continuation with the "
                "aspect, and the doubled root survives only in this formula."},
    {"key": "store store", "class": "conversational idioms",
     "kind": "decoding, extragrammatical", "route": "drift",
     "literal": ["store", "store"],
     "expansion": "(situation store PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (term record)))",
     "definition": "the speaker has stored the record",
     "pragmatics": "after receiving content the speaker means to keep",
     "restrictions": "excluded from R1 and R4",
     "registers": ["R0", "R2", "R3", "R5", "R6", "R7"],
     "loss": ["wording"],
     "history": "Constructed history: the doubled root of the same early stage, here "
                "marking a thing done; it outlived the pattern that formed it."},
]
