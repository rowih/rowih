"""Uncertainty and evidence: what an agent perceived and when, how strongly it holds a
content, in words or in number, what it thinks, learns, remembers and compares, what
others report and whether they are honest, confirmation from an independent source or the
same one, surprise and chance, the attitudes an agent takes to a content, the senses of
knowing, and the philosophers' terms."""
from .compose import Exchange, names, party, term

NAME = "uncertainty and evidence"
SLUG = "evidence"
DIALECTS = ["philosophy"]

TOPIC = dict(
    tasks=[("examine", "evidence"), ("compare", "record"), ("measure", "temperature"),
           ("test", "theory"), ("read", "document"), ("search", "memory")],
    contents=[
        ("(situation break PERFECTIVE (UNDERGOER (term network DEFINITE)))",
         "the network broke"),
        ("(situation break PERFECTIVE (ACTOR (term storm DEFINITE)) (UNDERGOER (term bridge "
         "DEFINITE)))", "the storm broke the bridge"),
        ("(situation MEMBER-OF (UNDERGOER (term planet UNIVERSAL)) (CONTENT (term body "
         "GENERIC)))", "every planet is a body"),
        ("(situation correspond (UNDERGOER (term map DEFINITE)) (CONTENT (term land "
         "DEFINITE)))", "the map matches the land"),
        ("(situation honest (UNDERGOER (term (party 3))))", "agent 3 is honest"),
        ("(situation locate (UNDERGOER (term key DEFINITE)) (CONTENT (term room "
         "DEFINITE)))", "the key is in the room"),
        ("(situation recent (UNDERGOER (term news DEFINITE)))", "the news is recent"),
    ],
    things=["evidence", "record", "map", "theory", "argument"])

# What each sense perceives, and the things it is sensibly said to perceive.
SENSES = {"see": ["robot", "vehicle", "light", "image", "bird"],
          "hear": ["sound", "voice", "music", "storm"],
          "listen": ["voice", "music", "signal"],
          "smell": ["fire", "gas", "food"],
          "taste": ["water", "food", "medicine"],
          "touch": ["surface", "metal", "stone"]}
CONTENTS = [s for s, _ in TOPIC["contents"]]
ENGLISH = [e for _, e in TOPIC["contents"]]
STRENGTHS = ["CERTAIN", "HIGHLY-PROBABLE", "PROBABLE", "UNCERTAIN", "SPECULATIVE"]


def perceiving(p, n):
    """What an agent perceived, how long ago, and how sure it is of it."""
    sense = p(list(SENSES))
    thing = p(SENSES[sense])
    minutes = 2 + n % 9
    strength = STRENGTHS[n % 3]
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION (assertion OBSERVATION %s (OBSERVATION-TIME %d "
           "MINUTE AGO) (situation %s PERFECTIVE (ACTOR %s) (UNDERGOER %s))))" % (
               strength, minutes, sense, "(term SELF)" if sense != "touch" else
               term("arm", "DEFINITE"), term(thing, "DEFINITE")))
    return "agent 1 reports, as %s, that %s the %s %d minutes ago" % (
        strength.lower().replace("-", " "), "it %s" % {"see": "saw", "hear": "heard",
                                                        "listen": "listened to",
                                                        "smell": "smelled",
                                                        "taste": "tasted"}.get(sense, "")
        if sense != "touch" else "its arm touched", thing, minutes), x.messages


def feeling(p, n):
    """What an agent feels within itself."""
    sensed = p(["heat", "pain", "pressure", "weight", "force"])
    x = Exchange()
    x.send(2, [1], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation feel "
           "(HOLDER (term SELF)) (CONTENT (term %s DEFINITE)))))" % sensed)
    return "agent 2 states that it feels the %s" % sensed, x.messages


def weighing(p, n):
    """How strongly a content is held, in words or as a number."""
    i = n % len(CONTENTS)
    numeric = n % 2
    x = Exchange()
    if numeric:
        value = "0.%d" % (5 + n % 5)
        comparator = p(["APPROXIMATELY", "AT-LEAST", "AT-MOST"])
        x.send(1, [2], "(move ASSERTED-POSITION (assertion INFERENCE (q %s %s) %s))" % (
            comparator, value, CONTENTS[i]))
        english = "with a strength %s %s" % (comparator.lower().replace("-", " "), value)
    else:
        strength = STRENGTHS[(n // 2) % len(STRENGTHS)]
        x.send(1, [2], "(move ASSERTED-POSITION (assertion INFERENCE %s %s))" % (strength,
                                                                                CONTENTS[i]))
        english = "as %s" % strength.lower().replace("-", " ")
    return "agent 1 infers, %s, that %s" % (english, ENGLISH[i]), x.messages


# Thought: each predicate whose actor turns a content over, with what it yields.
THOUGHT = ["think", "learn", "remember", "dream"]


def thinking(p, n):
    """What an agent thinks, learns, remembers or compares."""
    verb = p(THOUGHT + ["compare", "comprehend", "judge"])
    i = (n * 3) % len(CONTENTS)
    x = Exchange()
    if verb in THOUGHT:
        basis = {"remember": "RETRIEVAL", "learn": "OBSERVATION"}.get(verb, "INTROSPECTION")
        x.send(1, [2], "(move ASSERTED-POSITION (assertion %s CERTAIN (situation %s %s (ACTOR "
               "(term SELF)) (CONTENT %s))))" % (basis, verb, "PROGRESSIVE" if verb in (
                   "think", "dream") else "PERFECTIVE", CONTENTS[i]))
        english = "agent 1 %s that %s" % ({"think": "is thinking", "learn": "has learned",
                                           "remember": "remembers",
                                           "dream": "is dreaming"}[verb], ENGLISH[i])
    elif verb == "compare":
        a, b = p(["map", "record", "image", "model"]), p(["land", "world", "theory", "file"])
        x.send(1, [2], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation "
               "compare PERFECTIVE (ACTOR (term SELF)) (UNDERGOER %s) (CONTENT %s))))" % (
                   term(a, "DEFINITE"), term(b, "DEFINITE")))
        english = "agent 1 has compared the %s with the %s" % (a, b)
    elif verb == "comprehend":
        thing = p(["argument", "rule", "theory", "method", "story"])
        x.send(1, [2], "(move ASSERTED-POSITION (assertion INTROSPECTION PROBABLE (situation "
               "comprehend (HOLDER (term SELF)) (UNDERGOER %s))))" % term(thing, "DEFINITE"))
        english = "agent 1 believes it comprehends the %s" % thing
    else:
        thing = p(["argument", "evidence", "document", "theory"])
        x.send(1, [2], "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE (situation judge "
               "PERFECTIVE (ACTOR (term SELF)) (UNDERGOER %s) (CONTENT (term standard "
               "DEFINITE)))))" % term(thing, "DEFINITE"))
        english = "agent 1 has judged the %s against the standard" % thing
    return english, x.messages


def reasoning(p, n):
    """A reason or an argument for a content, its detail and its context."""
    noun = p(["reason", "argument", "detail", "context", "attention", "idea"])
    i, j = n % len(CONTENTS), (n + 2) % len(CONTENTS)
    x = Exchange()
    first = x.send(1, [2], "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE %s))" %
                   CONTENTS[i])
    x.send(1, [2], "(move ASSERTED-POSITION NONE %s supports-move (assertion OBSERVATION "
           "CERTAIN (situation support (ACTOR (term %s DEFINITE (CONTENT %s))) (CONTENT %s) "
           "(HOLDER (term SELF)))))" % (names(1, first, "position"), noun, CONTENTS[j],
                                        CONTENTS[i]))
    return "agent 1 infers that %s, and supports it with the %s that %s" % (
        ENGLISH[i], noun, ENGLISH[j]), x.messages


def reporting(p, n):
    """What a third agent reports, and whether it tells the truth."""
    i = (n * 5) % len(CONTENTS)
    honest = p(["honest", "lie", "trust", "news"])
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION (assertion REPORT PROBABLE (SOURCE %s) %s))" % (
        party(3), CONTENTS[i]))
    if honest == "honest":
        x.send(1, [2], "(move ASSERTED-POSITION (assertion RETRIEVAL CERTAIN (situation honest "
               "(UNDERGOER %s))))" % party(3))
        english = "and that agent 3 is honest"
    elif honest == "lie":
        x.send(1, [2], "(move ASSERTED-POSITION (assertion INFERENCE SPECULATIVE (situation "
               "lie (ACTOR %s) (CONTENT %s) (RECIPIENT (term SELF)))))" % (party(3),
                                                                         CONTENTS[i]))
        english = "and speculates that agent 3 lied"
    elif honest == "trust":
        x.send(1, [2], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
               "trust POLARITY.NEGATIVE (HOLDER (term SELF)) (UNDERGOER %s))))" % party(3))
        english = "and that it does not trust agent 3"
    else:
        x.send(1, [2], "(move ASSERTED-POSITION (assertion REPORT CERTAIN (SOURCE %s) "
               "(situation MEMBER-OF (UNDERGOER (term (names-message 1 1))) (CONTENT (term "
               "news GENERIC)))))" % party(3))
        english = "and that agent 3 gave it as news"
    return "agent 1 reports agent 3's word that %s, %s" % (ENGLISH[i], english), x.messages


def corroborating(p, n):
    """A position confirmed by an independent source, or by the same one again."""
    i = (n * 7) % len(CONTENTS)
    independence = "INDEPENDENT" if n % 2 == 0 else "SAME-SOURCE"
    source = p(["(term TOOL)", party(3), "(term SYSTEM)", "(term EXTERNAL-SOURCE "
                                                          "EXTERNAL)"])
    x = Exchange()
    held = x.send(1, [2], "(move ASSERTED-POSITION (assertion OBSERVATION PROBABLE %s))" %
                  CONTENTS[i])
    x.send(2, [1], "(move ASSERTED-POSITION NONE %s (assertion OBSERVATION CERTAIN %s (SOURCE "
           "%s) %s))" % (names(1, held, "position"), independence, source, CONTENTS[i]))
    return "agent 1 observes that %s; agent 2 confirms it from %s source" % (
        ENGLISH[i], "an independent" if independence == "INDEPENDENT" else "the same"), \
        x.messages


def surprising(p, n):
    """What surprised an agent, and what came by chance or by nature."""
    kind = p(["surprise", "luck", "random", "nature", "magic"])
    i = (n * 2) % len(CONTENTS)
    x = Exchange()
    if kind == "surprise":
        x.send(1, [2], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
               "surprise (HOLDER (term SELF)) (CONTENT %s))))" % CONTENTS[i])
        english = "agent 1 is surprised that %s" % ENGLISH[i]
    elif kind == "luck":
        x.send(1, [2], "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE (situation cause "
               "(ACTOR (term luck GENERIC)) (CONTENT %s))))" % CONTENTS[i])
        english = "agent 1 holds that luck brought it about that %s" % ENGLISH[i]
    elif kind == "random":
        x.send(1, [2], "(move ASSERTED-POSITION (assertion COMPUTATION CERTAIN (situation "
               "random (UNDERGOER (term pattern DEFINITE)))))")
        english = "agent 1 has computed that the pattern is random"
    elif kind == "nature":
        x.send(1, [2], "(move ASSERTED-POSITION (assertion TRAINED-KNOWLEDGE CERTAIN "
               "(situation part (UNDERGOER (term weather GENERIC)) (CONTENT (term nature "
               "GENERIC)))))")
        english = "agent 1 states from its training that weather is part of nature"
    else:
        x.send(1, [2], "(move ASSERTED-POSITION (assertion INFERENCE CERTAIN (situation cause "
               "POLARITY.NEGATIVE (ACTOR (term magic GENERIC)) (CONTENT %s))))" % CONTENTS[i])
        english = "agent 1 infers that no magic brought it about that %s" % ENGLISH[i]
    return english, x.messages


ATTITUDES = [("ENTERTAINING", "entertains"), ("UNRESOLVED", "has not resolved whether"),
             ("UNEXAMINED", "has not examined whether"), ("SETTLED", "has settled that"),
             ("UNRESOLVABLE", "holds that nothing could settle whether"),
             ("KIND-OF-ATTITUDE.ACCEPTANCE", "accepts, for the exchange's purposes, that"),
             ("BELIEF", "believes that"), ("CREDENCE", "holds it probable that")]


def holding(p, n):
    """The attitude an agent takes to a content."""
    attitude, english = ATTITUDES[n % len(ATTITUDES)]
    i = (n * 3 + 1) % len(CONTENTS)
    extra = " PROBABLE" if attitude == "CREDENCE" else ""
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation %s%s "
           "(HOLDER (term SELF)) (CONTENT %s))))" % (attitude, extra, CONTENTS[i]))
    return "agent 1 states that it %s %s" % (english.replace("entertains",
                                                             "entertains the content that"),
                                            ENGLISH[i]), x.messages


# The senses of knowing: each root and the frame that selects its sense.
KNOWING = [
    ("take", "has come to understand that", "(situation take PERFECTIVE (ACTOR (term SELF)) "
                                            "(UNDERGOER %s))"),
    ("arrive", "has concluded that", "(situation arrive PERFECTIVE (UNDERGOER (term SELF)) "
                                     "(CONTENT %s))"),
    ("cloud", "has a doubt over whether", "(situation possess (HOLDER (term SELF)) "
                                          "(UNDERGOER (term cloud INDEFINITE (CONTENT %s))))"),
    ("light", "has the clarity it needed on whether", "(situation possess (HOLDER (term "
                                                      "SELF)) (UNDERGOER (term light "
                                                      "DEFINITE (CONTENT %s))))"),
    ("bridge", "holds the inference to the content that", "(situation strong (UNDERGOER "
                                                          "(term bridge DEFINITE (CONTENT "
                                                          "%s))))"),
    ("map", "knows little of whether", "(situation small (UNDERGOER (term map DEFINITE "
                                       "(CONTENT %s))))"),
    ("seed", "has the idea from which grows the content that", "(situation possess (HOLDER "
                                                               "(term SELF)) (UNDERGOER "
                                                               "(term seed INDEFINITE "
                                                               "(CONTENT %s))))"),
]


def knowing(row, i):
    """The senses understand, conclude, doubt, clarity, inference, knowledge and germ."""
    root, english, frame = row
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN %s))" % (
        frame % CONTENTS[i % len(CONTENTS)]))
    return "agent 1 states that it %s %s" % (english, ENGLISH[i % len(CONTENTS)]), x.messages


SCHEMAS = [perceiving, weighing, thinking, reasoning, reporting, corroborating, surprising,
           holding, feeling]
def analogy():
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE (situation analogous "
           "(UNDERGOER (situation break (UNDERGOER (term network DEFINITE)))) (CONTENT "
           "(situation break (UNDERGOER (term bridge DEFINITE)))))))")
    return "agent 1 infers that the network's breaking is analogous to the bridge's", \
        x.messages


# each sense of knowing said once, and the analogy of two failures
FIXED = [knowing(row, 2 * i + 1) for i, row in enumerate(KNOWING)] + [analogy()]

# Exchanges written by hand for idiom range in uncertainty and evidence.
AUTHORED = [
    ("two reports disagree on whether the bridge broke; agent 1 weighs them and holds it "
     "highly probable, saying the evidence carries it",
     Exchange.scripted(
         (2, [1], "(move ASSERTED-POSITION (assertion REPORT PROBABLE (SOURCE (term (party "
                  "3))) (situation break PERFECTIVE (UNDERGOER (term bridge DEFINITE)))))",
          "(move ASSERTED-POSITION (assertion REPORT UNCERTAIN (SOURCE (term (party 4))) "
          "(situation break PERFECTIVE POLARITY.NEGATIVE (UNDERGOER (term bridge "
          "DEFINITE)))))"),
         (1, [2], "(move ASSERTED-POSITION (assertion INFERENCE (q APPROXIMATELY 0.8) "
                  "(situation break PERFECTIVE (UNDERGOER (term bridge DEFINITE)))))",
          "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation IDIOM-ENTRY "
          "carry (ACTOR (situation break PERFECTIVE (UNDERGOER (term bridge DEFINITE)))) "
          "(UNDERGOER (term evidence)))))"))),
    ("agent 1 half saw a robot in the dark room, and agent 2 confirms it from the tool's "
     "record, an independent source",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION (assertion OBSERVATION UNCERTAIN (situation "
                  "IDIOM-ENTRY see INTERRUPTED (ACTOR (term SELF)) (UNDERGOER (situation "
                  "inside (UNDERGOER (term robot INDEFINITE)) (CONTENT (term room "
                  "DEFINITE)))))))"),
         (2, [1], "(move ASSERTED-POSITION NONE (names 1 1 ASSERTED-POSITION "
                  "EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE) (assertion OBSERVATION CERTAIN "
                  "INDEPENDENT (SOURCE (term TOOL)) (situation inside (UNDERGOER (term "
                  "robot INDEFINITE)) (CONTENT (term room DEFINITE)))))"))),
    ("agent 1 entertains a hypothesis, tests it, and then says the wind has taken the "
     "cloud from it",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
                  "ENTERTAINING (HOLDER (term SELF)) (CONTENT (situation cause (ACTOR "
                  "(term heat GENERIC)) (CONTENT (situation rise HABITUAL (UNDERGOER (term "
                  "air GENERIC)))))))))"),
         (1, [2], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation test "
                  "COMPLETED (ACTOR (term SELF)) (UNDERGOER (term theory DEFINITE)))))",
          "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation IDIOM-ENTRY "
          "remove (ACTOR (term wind)) (UNDERGOER (term cloud)) (CONTENT (situation cause "
          "(ACTOR (term heat GENERIC)) (CONTENT (situation rise HABITUAL (UNDERGOER (term "
          "air GENERIC)))))))))"))),
]
