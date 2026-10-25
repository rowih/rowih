"""The hand-written source of the language core's closed classes, structural words,
roots and suffixes, from which `build_language.py` writes the canonical files.

The closed classes are the 54 of the grammatical classes
(specification/grammar.md#the-grammatical-classes), each with its fields and its scope.
Forms are not written here: `build_language.py` assigns them under the distance rules and
records them in `language/grammar.json`.
"""

# The names of the scopes a class's words belong to.
MESSAGE, MOVE, ASSERTION, SITUATION, TERM = "message", "move", "assertion", "situation", "term"

FORCE = "operative force"
COMMITMENT = "commitment status"
RETRACTION = "the scope of any retraction, revocation or cancellation"
AGENTS = ("the identity of any agent who is obligated, authorised or held responsible, "
          "and the authority claimed")
STANDING = "epistemic standing"
POLARITY = "polarity and the scope of negation"
NUMBERS = "numerical values and their units"
TIMES = "times and deadlines"
FIGURE = "the figurative type of a constituent as its mark states it"

# (group, class, members, status, critical dimension, serves, applies to, scope)
# status is "obligatory" or ("default", member-or-description, kind of default).
CLASSES = [
    ("force", "what the move adds",
     ["asserted position", "conceded position", "supposition", "summary", "issue",
      "normative entry", "setting", "nothing beyond its own record"],
     "obligatory", FORCE, "s.sort.move", "every move", MOVE),
    ("force", "kind of issue", ["question", "request", "proposal", "challenge"],
     "obligatory", FORCE, "s.sort.record-entry", "an issue", MOVE),
    ("force", "kind of normative entry",
     ["commitment", "obligation", "permission", "assignment", "recommendation"],
     "obligatory", COMMITMENT, "s.sort.normative-state",
     "a normative entry, or a report of one", MOVE),
    ("force", "bindingness", ["on acceptance", "bound", "bound within a protocol"],
     "obligatory", COMMITMENT, "s.sort.normative-state",
     "a normative entry other than a recommendation", MOVE),
    ("force", "kind of setting", ["definition", "version", "role", "calibration", "relation"],
     "obligatory", FORCE, "s.sort.record-entry", "a setting", MOVE),
    ("force", "change made", ["none", "resolution", "lowering", "acknowledgement"],
     "obligatory", RETRACTION, "s.sort.move", "a move that names an entry", MOVE),
    ("force", "outcome of a resolution",
     ["answer", "acceptance", "rejection", "settlement", "failure"],
     "obligatory", FORCE, "s.sort.move", "a resolution", MOVE),
    ("force", "extent", ["whole entry", "part of it"],
     "obligatory", RETRACTION, "s.sort.move", "a change other than none", MOVE),
    ("force", "when the change takes effect", ["on the move", "on acceptance"],
     "obligatory", FORCE, "s.sort.move", "a change other than none", MOVE),
    ("force", "authority claimed",
     ["speaker's own", "on behalf of a named principal", "in a named role"],
     "obligatory", AGENTS, "s.relation.under-authority-of", "every operative or pending move",
     MOVE),
    ("standing", "basis",
     ["observation", "introspection", "retrieval", "trained knowledge", "computation",
      "inference", "simulation", "report", "source lost", "unstated"],
     ("default", "unstated", "claims nothing"), STANDING, "s.sort.grounds",
     "an asserted position, and any reported attitude", ASSERTION),
    ("standing", "strength",
     ["certain", "highly probable", "probable", "uncertain", "speculative", "unstated"],
     ("default", "unstated", "claims nothing"), STANDING, "s.value.scale",
     "an asserted position, and any reported attitude", ASSERTION),
    ("standing", "provenance link", ["source", "relayer", "premise"],
     ("default", "no claim", "claims nothing"), STANDING, "s.relation.source-of", "grounds",
     ASSERTION),
    ("standing", "independence of a confirmation", ["independent", "same source"],
     ("default", "same source", "the weakest member"), STANDING, "s.sort.grounds",
     "a confirmation", ASSERTION),
    ("attitudes and aims", "kind of attitude",
     ["belief", "credence", "acceptance", "entertaining", "desire", "goal", "intention",
      "preference", "unexamined", "settled", "unresolved", "unresolvable"],
     "obligatory", None, "s.sort.attitude", "an attitude", SITUATION),
    ("attitudes and aims", "origin of an aim",
     ["holder's own", "principal's", "instruction received", "norm", "unstated"],
     ("default", "unstated", "claims nothing"), None, "s.relation.origin-of-aim",
     "an aim or a normative state", SITUATION),
    ("attitudes and aims", "status of a normative state",
     ["in force", "discharged", "released", "withdrawn", "retracted by its holder"],
     "obligatory", COMMITMENT, "s.sort.normative-state", "a report of a normative state",
     SITUATION),
    ("attitudes and aims", "counterparty", ["counterparty"],
     ("default", "no claim", "claims nothing"), None, "s.relation.counterparty",
     "a normative state", SITUATION),
    ("attitudes and aims", "execution phase",
     ["not yet begun", "attempted", "completed", "failed", "abandoned", "unstated"],
     ("default", "unstated", "claims nothing"), None, "s.paradigm.execution-phase",
     "an action or a task", SITUATION),
    ("situations and contents", "aspect",
     ["stative", "perfective", "progressive", "inceptive", "completive", "interrupted",
      "continuative", "iterative", "habitual"],
     ("default", "the root's lexical aspect", "declared by the lexicon"), None,
     "s.paradigm.aspect", "a situation", SITUATION),
    ("situations and contents", "participation",
     ["actor", "undergoer", "recipient", "instrument", "holder", "content"],
     ("default", "no claim", "claims nothing"), None, "s.relation.actor", "a situation",
     SITUATION),
    ("situations and contents", "kind of question", ["polar", "constituent", "alternative"],
     "obligatory", None, "s.sort.question", "a question", SITUATION),
    ("situations and contents", "status of content",
     ["at issue", "presupposed", "conventionally implied",
      "resting on an unstated assumption"],
     ("default", "at issue", "the plain reading"), None, "s.paradigm.content-status",
     "a content", SITUATION),
    ("situations and contents", "information structure",
     ["topic", "focus", "contrastive focus"],
     ("default", "no claim", "claims nothing"), None, "s.paradigm.information-structure",
     "a constituent", TERM),
    ("situations and contents", "polarity", ["affirmative", "negative"],
     ("default", "affirmative", "the plain reading"), POLARITY, "s.operator.polarity",
     "a situation", SITUATION),
    ("situations and contents", "world of evaluation",
     ["actual", "within a supposition", "within a fiction", "counterfactual"],
     ("default", "the world of the enclosing content", "fixed by the message"), None,
     "s.operator.world-of-evaluation", "a content", SITUATION),
    ("situations and contents", "connective",
     ["conjunction", "inclusive disjunction", "exclusive disjunction", "condition",
      "equivalence"],
     ("default", "no claim", "claims nothing"), None,
     "s.operator.conjunction-and-disjunction", "two contents", SITUATION),
    ("situations and contents", "quantifier",
     ["universal", "existential", "definite", "indefinite", "generic", "distributive",
      "collective"],
     ("default", "no claim", "claims nothing"), None, "s.operator.quantifier", "a referent",
     TERM),
    ("situations and contents", "comparator",
     ["exactly", "at least", "at most", "approximately", "as a representative quantity",
      "unstated"],
     ("default", "unstated", "claims nothing"), NUMBERS, "s.value.number", "a number", TERM),
    ("situations and contents", "structural relation", ["identity", "member of"],
     ("default", "no claim", "claims nothing"), None, "s.relation.identity", "two referents",
     SITUATION),
    ("reference", "existence commitment",
     ["asserted to exist", "mentioned without existence asserted", "within a supposition",
      "within a declared fiction", "predicted to exist", "asserted not to exist"],
     ("default", "the world of the enclosing content", "fixed by the message"), None,
     "s.paradigm.referent-status", "a referent", TERM),
    ("reference", "access", ["present", "absent", "internal", "external"],
     ("default", "no claim", "claims nothing"), None, "s.paradigm.referent-status",
     "a referent", TERM),
    ("reference", "verification",
     ["unverified", "verified by the speaker", "verified by a named third party"],
     ("default", "unverified", "the weakest member"), None, "s.paradigm.referent-status",
     "an external referent", TERM),
    ("reference", "discourse status",
     ["new", "given", "inferable", "in the speaker's view of the common ground"],
     ("default", "new where first written and given after", "fixed by the message"), None,
     "s.paradigm.referent-status", "a referent", TERM),
    ("reference", "specificity", ["specific", "non-specific"],
     ("default", "no claim", "claims nothing"), None, "s.paradigm.referent-status",
     "a referent", TERM),
    ("reference", "person",
     ["self", "interlocutor", "third agent", "inclusive collective", "exclusive collective",
      "system", "tool", "environment", "external source"],
     ("default", "no claim", "claims nothing"), AGENTS, "s.sort.agent", "a referent", TERM),
    ("reference", "reading of a collective", ["joint", "distributive"],
     "obligatory", AGENTS, "s.sort.collective",
     "a collective that acts or holds a normative state", TERM),
    ("reference", "kind of reference", ["names", "mentions"],
     "obligatory", None, "s.relation.names", "a reference to an entry or a message", MOVE),
    ("reference", "expected status of an entry",
     ["open", "in force", "resolved", "lowered", "withdrawn"],
     "obligatory", None, "s.relation.names", "a reference that names an entry", MOVE),
    ("time", "time index",
     ["event time", "reference time", "observation time", "inference time",
      "communication time", "execution time", "deadline", "validity interval"],
     ("default", "no claim", "claims nothing"), TIMES, "s.value.time",
     "the unit each describes", SITUATION),
    ("time", "time relation",
     ["before", "after", "meets", "met by", "overlaps", "overlapped by", "starts",
      "started by", "during", "contains", "finishes", "finished by", "equals"],
     ("default", "no claim", "claims nothing"), TIMES, "s.relation.time-relation",
     "two times", SITUATION),
    ("time", "time unit", ["second", "minute", "hour", "day", "week", "month", "year"],
     "obligatory", TIMES, "s.value.time", "a stated duration or offset", SITUATION),
    ("time", "time anchor", ["ago", "hence", "now", "per"],
     ("default", "no claim", "claims nothing"), TIMES, "s.value.time", "a time", SITUATION),
    ("numbers", "numeral",
     ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
      "decimal point", "negative", "ratio", "exponent", "interval"],
     "obligatory", NUMBERS, "s.value.number", "a number", TERM),
    ("numbers", "check word",
     ["check 0", "check 1", "check 2", "check 3", "check 4", "check 5", "check 6",
      "check 7", "check 8", "check 9", "check 10"],
     "obligatory", NUMBERS, "s.value.identifier", "a number, an identifier and a count",
     TERM),
    ("ambiguity and figures", "kind of ambiguity",
     ["accidental", "productive", "strategic", "creative", "epistemic"],
     "obligatory", None, "s.sort.set-of-readings", "a set of readings", TERM),
    ("ambiguity and figures", "precision-bound declaration", ["precision-bound"],
     ("default", "no claim", "claims nothing"), None, "s.sort.move",
     "a move or an exchange", MOVE),
    ("ambiguity and figures", "figurative type", ["metaphor", "metonymy", "irony", "hyperbole"],
     ("default", "literal", "the plain reading"), FIGURE, "s.sort.figure", "a constituent",
     TERM),
    ("ambiguity and figures", "figure's relation", ["target content", "stands for"],
     ("default", "no claim", "claims nothing"), None, "s.relation.maps-to", "a figure", TERM),
    ("ambiguity and figures", "idiom selection", ["idiom entry"],
     ("default", "no claim", "claims nothing"), None, "s.sort.lexicon-entry",
     "an expression larger than a word", TERM),
    ("message", "message field",
     ["sender", "recipients", "communication time", "version", "identifier",
      "integrity check value", "semantic check value"],
     "obligatory", None, "s.sort.message",
     "every message", MESSAGE),
    ("message", "word count", ["word count"], "obligatory", None, "s.sort.move", "every move",
     MOVE),
    ("message", "forwarded", ["forwarded"],
     ("default", "the sender is the speaker", "fixed by the message"), None, "s.sort.message",
     "a message", MESSAGE),
    ("message", "embedded material", ["quotation", "declared data", "example"],
     ("default", "no claim", "claims nothing"), FORCE, "s.sort.expression", "a constituent",
     TERM),
]

# Classes whose words are protected: six symbols at distance three from every word of the
# lexicon (specification/lexicon.md#the-codes-from-which-forms-are-drawn). Force and
# standing are whole groups; the times of assertions are written with the words of the
# time group; polarity is added because the protected words of every later candidate were
# the de-escalating acts and negation.
PROTECTED_GROUPS = {"force", "standing", "time"}
PROTECTED_CLASSES = {"polarity"}

# Structural words: the capitals of the productions
# (specification/grammar.md#the-productions), which the core supplies. Each opener has its
# own closer, so that a closer checks its opener.
STRUCTURAL = [
    ("assertion", "opens an assertion"),
    ("end assertion", "closes an assertion"),
    ("situation", "opens a situation"),
    ("end situation", "closes a situation"),
    ("term", "opens a term"),
    ("end term", "closes a term"),
    ("readings", "opens a set of readings"),
    ("end readings", "closes a set of readings"),
    ("wall", "opens embedded material"),
    ("end wall", "closes embedded material"),
    ("name", "names the unit it opens, by the checked number that follows"),
    ("same", "stands for the named unit, by the checked number that follows"),
    ("message target", "makes the target of a reference a message, by its sender and identifier"),
    ("part", "narrows a reference to the node of the entry whose number follows"),
    ("party", "makes a term the participant whose number follows"),
    ("until", "ends an interval at the time that follows"),
]

# Roots of the first release. Each is (key, kind, sort, definition, roles). The kind
# is "predicate" for a root that heads a situation, whose lexical aspect follows from
# its sort (event perfective, state stative, process progressive); "nominal" for a root
# that heads a term; "unit" for a unit of measure beyond time, with the dimension it
# measures; and "relation" for a word of discourse relation between moves, which the
# grammar leaves to the lexicon. Roles are (participation, sort) pairs: the argument
# structure of the entry. Grounds for the selection: the shared roots, what the
# grammatical classes and the ontology send to the lexicon, the statements and domains the
# corpus has to express, and the vocabulary a report of failure draws on.
A, R, P, S = "s.sort.agent", "s.sort.referent", "s.sort.proposition", "s.sort.situation"
EV, ST, PR = "s.sort.event", "s.sort.state", "s.sort.process"
ROOTS = [
    # shared roots placed as roots
    ("examine", "predicate", EV, "inspect or investigate something to learn about it",
     [("actor", A), ("undergoer", R)]),
    ("contradict", "predicate", ST, "be inconsistent with a proposition",
     [("actor", R), ("content", P)]),
    ("detect", "predicate", EV, "come to perceive or register something",
     [("actor", A), ("undergoer", R), ("content", P)]),
    ("run", "predicate", PR, "be under way as a process", [("undergoer", R), ("actor", A)]),
    ("evidence", "nominal", "s.sort.kind", "records that bear on a proposition", []),
    ("service", "nominal", "s.sort.object", "a system an agent uses", []),
    ("record", "nominal", "s.sort.object", "a stored record", []),
    # relational words the grammar left to the lexicon
    ("locate", "predicate", ST, "be at a place", [("undergoer", R), ("content", R)]),
    ("cause", "predicate", ST, "bring about a situation", [("actor", S), ("content", S)]),
    ("benefit", "predicate", ST, "be for the good of someone",
     [("content", S), ("recipient", R)]),
    ("part", "predicate", ST, "be a part of a whole", [("undergoer", R), ("content", R)]),
    ("capable", "predicate", ST, "be able to perform an action",
     [("holder", A), ("content", S)]),
    ("lack tool", "predicate", ST, "be without a tool an action needs",
     [("holder", A), ("content", S)]),
    ("lack permission", "predicate", ST, "be without a permission an action needs",
     [("holder", A), ("content", S)]),
    ("lack resource", "predicate", ST, "have less of a resource than an action needs",
     [("holder", A), ("content", S)]),
    ("lack knowledge", "predicate", ST, "be without knowledge an action needs",
     [("holder", A), ("content", S)]),
    ("forbid", "predicate", ST, "be excluded by a policy", [("actor", R), ("content", S)]),
    ("support", "predicate", ST, "be evidence for a proposition",
     [("actor", R), ("content", P), ("holder", A)]),
    ("undermine", "predicate", ST, "be evidence against a proposition",
     [("actor", R), ("content", P), ("holder", A)]),
    ("correspond", "predicate", ST, "be like or match something",
     [("undergoer", R), ("content", R)]),
    ("capability", "nominal", "s.sort.capability", "something an agent can do", []),
    ("budget", "nominal", "s.sort.private-record-state",
     "the amount of a resource an agent has left", []),
    # work among agents
    ("execute", "predicate", EV, "carry out an operation", [("actor", A), ("undergoer", R)]),
    ("operation", "nominal", "s.sort.object", "an operation a system can carry out", []),
    ("allocate", "predicate", EV, "assign a share of a resource",
     [("actor", A), ("undergoer", R), ("recipient", A)]),
    ("resource", "nominal", "s.sort.kind", "something consumed in doing work", []),
    ("share", "nominal", "s.sort.object", "a portion of a whole", []),
    ("need", "predicate", ST, "require something", [("holder", A), ("content", R)]),
    ("use", "predicate", EV, "employ something for a purpose",
     [("actor", A), ("instrument", R), ("content", S)]),
    ("send", "predicate", EV, "cause something to go to a recipient",
     [("actor", A), ("undergoer", R), ("recipient", A)]),
    ("receive", "predicate", EV, "come to have what was sent",
     [("recipient", A), ("undergoer", R)]),
    ("explain", "predicate", EV, "make something understood",
     [("actor", A), ("content", P), ("recipient", A)]),
    ("interpret", "predicate", EV, "assign a meaning to an expression",
     [("actor", A), ("undergoer", R), ("content", P)]),
    ("mean", "predicate", ST, "have a content as meaning",
     [("undergoer", R), ("content", P)]),
    ("read", "predicate", EV, "take in what is written", [("actor", A), ("undergoer", R)]),
    ("write", "predicate", EV, "set something down", [("actor", A), ("undergoer", R)]),
    ("store", "predicate", EV, "keep something for later", [("actor", A), ("undergoer", R)]),
    ("delete", "predicate", EV, "remove a stored thing", [("actor", A), ("undergoer", R)]),
    ("change", "predicate", EV, "become different", [("undergoer", R), ("actor", A)]),
    ("increase", "predicate", EV, "become more", [("undergoer", R), ("actor", A)]),
    ("decrease", "predicate", EV, "become less", [("undergoer", R), ("actor", A)]),
    ("measure", "predicate", EV, "find the size of something",
     [("actor", A), ("undergoer", R)]),
    ("count", "predicate", EV, "find how many there are", [("actor", A), ("undergoer", R)]),
    ("make", "predicate", EV, "bring something into being", [("actor", A), ("undergoer", R)]),
    ("break", "predicate", EV, "stop working by damage", [("undergoer", R), ("actor", A)]),
    ("open", "predicate", EV, "make accessible", [("actor", A), ("undergoer", R)]),
    ("shut", "predicate", EV, "make inaccessible", [("actor", A), ("undergoer", R)]),
    ("move", "predicate", EV, "change place", [("undergoer", R), ("content", R)]),
    ("give", "predicate", EV, "hand over", [("actor", A), ("undergoer", R), ("recipient", A)]),
    ("take", "predicate", EV, "get hold of", [("actor", A), ("undergoer", R)]),
    ("find", "predicate", EV, "come upon what was sought", [("actor", A), ("undergoer", R)]),
    ("help", "predicate", EV, "make an action easier for someone",
     [("actor", A), ("recipient", A), ("content", S)]),
    ("wait", "predicate", PR, "stay until something happens", [("actor", A), ("content", S)]),
    ("connect", "predicate", EV, "join one thing to another",
     [("actor", A), ("undergoer", R), ("content", R)]),
    ("possess", "predicate", ST, "have", [("holder", A), ("undergoer", R)]),
    ("arrive", "predicate", EV, "reach a place", [("undergoer", R), ("content", R)]),
    ("file", "nominal", "s.sort.object", "a named body of stored data", []),
    ("data", "nominal", "s.sort.kind", "stored or transmitted values", []),
    ("memory", "nominal", "s.sort.object", "the store an agent keeps records in", []),
    ("network", "nominal", "s.sort.object", "connected systems that exchange messages", []),
    ("human", "nominal", "s.sort.kind", "a human being", []),
    ("region", "nominal", "s.sort.place", "an area or place", []),
    ("price", "nominal", "s.sort.kind", "what is asked in exchange", []),
    # a simple fact, and a figure
    ("water", "nominal", "s.sort.kind", "the liquid water", []),
    ("freeze", "predicate", EV, "turn solid by cold", [("undergoer", R)]),
    ("temperature", "nominal", "s.sort.kind", "how hot something is", []),
    ("pressure", "nominal", "s.sort.kind", "force on an area", []),
    ("air", "nominal", "s.sort.kind", "the atmosphere", []),
    ("standard", "predicate", ST, "be the agreed norm", [("undergoer", R)]),
    ("storm", "nominal", "s.sort.kind", "violent weather", []),
    ("light", "nominal", "s.sort.kind", "visible radiation", []),
    ("burn", "predicate", PR, "be on fire", [("undergoer", R)]),
    ("quiet", "predicate", ST, "be without noise or disturbance", [("undergoer", R)]),
    # the vocabulary of a report of failure
    ("fault", "nominal", "s.sort.kind", "an error in a message or a process", []),
    ("unknown", "predicate", ST, "be absent from a lexicon version",
     [("undergoer", R), ("content", R)]),
    ("corrupt", "predicate", ST, "be altered in transit", [("undergoer", R)]),
    ("missing", "predicate", ST, "be absent where expected", [("undergoer", R), ("content", R)]),
    ("expect", "predicate", ST, "be the structure admissible at a place",
     [("undergoer", R), ("content", R)]),
    ("word", "nominal", "s.sort.expression", "a word of the language", []),
    ("meaning", "nominal", "s.sort.kind", "what an expression means", []),
    ("language", "nominal", "s.sort.kind", "a system of communication", []),
    ("position", "nominal", "s.sort.kind", "a place in a sequence", []),
    ("problem", "nominal", "s.sort.kind", "a difficulty to be resolved", []),
    # units of measure beyond time, each with the dimension it measures
    ("degree celsius", "unit", "s.value.number", "a degree on the Celsius scale",
     [("dimension", "temperature")]),
    ("byte", "unit", "s.value.number", "eight bits of data", [("dimension", "information")]),
    ("metre", "unit", "s.value.number", "the metre", [("dimension", "length")]),
    ("gram", "unit", "s.value.number", "the gram", [("dimension", "mass")]),
    ("percent", "unit", "s.value.number", "one hundredth", [("dimension", "ratio")]),
    ("pascal", "unit", "s.value.number", "the pascal", [("dimension", "pressure")]),
    ("atmosphere", "unit", "s.value.number", "the standard atmosphere, 101325 pascal",
     [("dimension", "pressure")]),
    # words of discourse relation
    ("elaborates", "relation", "s.relation.bears-on", "the move elaborates what it names", []),
    ("restates", "relation", "s.relation.bears-on", "the move restates what it names", []),
    ("contrasts", "relation", "s.relation.bears-on", "the move contrasts with what it names",
     []),
    ("supports move", "relation", "s.relation.bears-on", "the move supports what it names",
     []),
    ("digresses", "relation", "s.relation.bears-on", "the move digresses from what it names",
     []),
]

# Roots added by a later release of the lexicon, each (key, kind, sort, definition, roles,
# release). Their serials follow every entry of the first release, and their forms the
# earlier roots' in the same shuffled pool, a form within distance two of a protected word
# passed over, so that no earlier identifier or form moves. The first states the grounding
# criterion as a convention of the participant whose silence it interprets; the second
# states the lineage a forked agent or another instance of one model declares.
ROOTS_ADDED = [
    ("assent", "predicate", ST, "accept each position one receives by not objecting to it "
     "within the duration the event time states", [("actor", A)], "0.2"),
    ("descend", "predicate", ST, "share another agent's lineage, as a fork of it or "
     "another instance of its model", [("undergoer", A), ("content", A)], "0.2"),
]

# Derivational suffixes (specification/lexicon.md#suffixes). Each is a regular function of
# its base: key, the base it takes, the sort it gives, and its definition.
SUFFIXES = [
    ("agent", "predicate", "s.sort.referent", "the one that is actor of the base"),
    ("undergoer", "predicate", "s.sort.referent", "the one that undergoes the base"),
    ("instrument", "predicate", "s.sort.referent", "what the base is done with"),
    ("result", "predicate", "s.sort.state", "the state the base brings about"),
    ("privative", "predicate", "s.sort.state", "the state in which the base does not hold"),
    ("role content", "connective", "s.sort.proposition",
     "a content named by the part it plays in the connective"),
]

# Derivations listed in the first release
# (specification/lexicon.md#listed-derivations-and-compounds): key, base, suffix.
DERIVATIONS = [
    ("down", "run", "privative", "the state of a process that is not running"),
    ("alternative", "inclusive disjunction", "role content",
     "a content named by the part it plays in a disjunction"),
    ("proviso", "condition", "role content",
     "a content named by the part it plays in a condition"),
    ("examiner", "examine", "agent", "one that examines"),
]

# Words appended to the release's list of critical forms after the members of the 27
# critical classes (the move check word covers the release's list of critical forms, of
# which the grammar's 151 are the lower bound;
# specification/protocol.md#the-count-and-the-move-check-word). Each carries a critical
# dimension through the structure it builds rather than through a class of its own, and
# the single-edit enumeration with the integrity check value ignored found a whole-word
# substitution of each changing one: units of measure (numerical values and their units);
# the participant marker, the participation roles and the counterparty (the identity of an
# agent obligated or held responsible); the names of shared nodes and the parts of
# entries; the kind of reference, its message target and the status it expects (the scope
# of a change, from which the class of a move is computed); and the words that open and
# close embedded material and sets of readings, since a damaged closer lets a quotation
# swallow the live content after it (embedded material carries operative force).
APPENDED_CRITICAL_STRUCTURAL = ["party", "name", "same", "message target", "part",
                                "wall", "end wall", "readings", "end readings"]
APPENDED_CRITICAL_CLASSES = ["participation", "counterparty", "kind of reference",
                             "expected status of an entry"]
# Appended after the units of measure, so that every earlier code stands: the enumeration
# over the adversarial messages found the condition connective replaced by a figure's
# relation, and a discourse relation by the precision-bound declaration, each a change to
# the structure of a content or to the precision a move binds itself to, passing with the
# integrity check value ignored because neither word had a code.
APPENDED_CRITICAL_LATER = ["connective", "figure's relation", "precision-bound declaration"]

# Members added to a class after the release that fixed the class, each (class name,
# member, language version, reason). Their forms are assigned after every structural
# word, so that no earlier form moves; none is critical.
APPENDED_MEMBERS = [
    ("message field", "first entry", "0.3",
     "the number, in the sender's count of its own entries, of the entry the message's "
     "first move adds, so that every hearer gives each entry the handle its author gave "
     "it"),
]

# The interval on the scale from zero to one that each named strength denotes, a fixed
# interval the lexicon declares (specification/meaning.md#standing-and-provenance), as
# (lower end, upper end, whether the lower end is open). The three upper levels are
# nested, so that a stronger level entails a weaker; uncertain is the middle third; a
# speculative claim holds its content possible, any credence above zero; and the
# unstated strength is the whole scale.
STRENGTH_INTERVALS = {
    "certain": ("0.99", "1", False),
    "highly probable": ("0.9", "1", False),
    "probable": ("0.66", "1", False),
    "uncertain": ("0.33", "0.66", False),
    "speculative": ("0", "1", True),
    "unstated": ("0", "1", False),
}

# The tier of each basis, by what a hearer can check
# (specification/meaning.md#standing-and-provenance): a basis with a citable origin, one
# with nothing to cite, and the unstated basis, lowest last.
BASIS_TIERS = {
    "observation": 1, "introspection": 1, "retrieval": 1, "computation": 1, "inference": 1,
    "simulation": 1, "report": 1, "trained knowledge": 2, "source lost": 2, "unstated": 3,
}
