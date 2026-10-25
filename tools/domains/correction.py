"""Error correction: positions found wrong and corrected, things damaged and repaired,
records lost, forgotten and found again, blame and forgiveness, words corrupt, unknown or
deprecated, observations that contradict a claim, positions retracted, and contents
settled once the error is put right."""
from .compose import Exchange, k, names, party, term

NAME = "error correction"
SLUG = "correction"

TOPIC = dict(
    tasks=[("repair", "file"), ("delete", "record"), ("write", "document"), ("send", "file"),
           ("change", "record"), ("examine", "fault"), ("count", "word"),
           ("remove", "mistake"), ("heal", "machine"), ("destroy", "copy")],
    contents=[
        ("(situation correct (UNDERGOER (term record DEFINITE)))", "the record is correct"),
        ("(situation corrupt (UNDERGOER (term file DEFINITE)))", "the file is corrupt"),
        ("(situation missing (UNDERGOER (term key DEFINITE)) (CONTENT (term record "
         "DEFINITE)))", "the key is missing from the record"),
        ("(situation damage PERFECTIVE (ACTOR (term storm DEFINITE)) (UNDERGOER (term "
         "network DEFINITE)))", "the storm damaged the network"),
        ("(situation bad (UNDERGOER (term data DEFINITE)))", "the data is bad"),
        ("(situation clear POLARITY.NEGATIVE (UNDERGOER (term sentence DEFINITE)))",
         "the sentence is not clear"),
    ],
    things=["file", "record", "network", "data", "memory", "document"])

# Positions an agent may hold wrongly: each a content and the content that corrects it.
ERRORS = [
    ("(situation run (UNDERGOER (term service DEFINITE)))",
     "(situation run POLARITY.NEGATIVE (UNDERGOER (term service DEFINITE)))",
     "the service is running", "it is not"),
    ("(situation locate (UNDERGOER (term key DEFINITE)) (CONTENT (term room DEFINITE)))",
     "(situation locate (UNDERGOER (term key DEFINITE)) (CONTENT (term house DEFINITE)))",
     "the key is in the room", "it is in the house"),
    ("(situation contain (UNDERGOER (term file DEFINITE)) (CONTENT (term record (q EXACTLY "
     "12))))", "(situation contain (UNDERGOER (term file DEFINITE)) (CONTENT (term record "
               "(q EXACTLY 21))))", "the file holds 12 records", "it holds 21"),
    ("(situation correct (UNDERGOER (term value DEFINITE)))",
     "(situation correct POLARITY.NEGATIVE (UNDERGOER (term value DEFINITE)))",
     "the value is correct", "it is not"),
    ("(situation arrive PERFECTIVE (UNDERGOER (term signal DEFINITE)) (CONTENT (term SELF)))",
     "(situation arrive PERFECTIVE POLARITY.NEGATIVE (UNDERGOER (term signal DEFINITE)) "
     "(CONTENT (term SELF)))", "the signal reached it", "it did not"),
]
DONE = {"delete": "deleted", "send": "sent", "change": "changed", "write": "written"}
DAMAGE = [("damage", "wheel"), ("destroy", "bridge"), ("break", "machine"),
          ("damage", "interface"), ("break", "door"), ("destroy", "file"),
          ("damage", "arm"), ("break", "battery")]


def correcting(p, n):
    """A position challenged and corrected by its author, the correction marked as such."""
    wrong, right, english, corrected = ERRORS[n % len(ERRORS)]
    basis = p(["OBSERVATION", "INFERENCE", "RETRIEVAL"])
    x = Exchange()
    held = x.send(1, [2], "(move ASSERTED-POSITION (assertion %s PROBABLE %s))" % (basis,
                                                                                  wrong))
    x.send(2, [1], "(move ACT-CHALLENGE NONE %s (assertion OBSERVATION CERTAIN %s))" % (
        names(1, held, "position"), right))
    x.send(1, [2], "(move ACT-CORRECTION %s corrects (assertion OBSERVATION CERTAIN %s))" % (
        names(1, held, "position"), right))
    return "agent 1 holds that %s; agent 2 challenges it, and agent 1 corrects its position: " \
           "%s" % (english, corrected), x.messages


def repairing(p, n):
    """What a fault damaged, and its repair."""
    verb, thing = DAMAGE[n % len(DAMAGE)]
    cause = p(["storm", "fire", "wind", "water", "attack"])
    p.note(verb, thing)
    x = Exchange()
    cause_unit = term(cause, "DEFINITE") if cause != "attack" else term("enemy", "DEFINITE")
    x.send(2, [1], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation %s "
           "PERFECTIVE (ACTOR %s) (UNDERGOER %s))))" % (k(verb), cause_unit,
                                                        term(thing, "DEFINITE")))
    asked = x.send(1, [2], "(move ACT-REQUEST SPEAKERS-OWN (situation repair (ACTOR %s) "
                   "(UNDERGOER %s)))" % (party(2), term(thing, "DEFINITE")))
    taken = x.send(2, [1], "(move ACT-UNDERTAKING SPEAKERS-OWN %s (situation repair (ACTOR "
                   "(term SELF)) (UNDERGOER %s)))" % (names(1, asked, "request"),
                                                     term(thing, "DEFINITE")))
    x.send(2, [1], "(move ACT-COMPLETION-REPORT SPEAKERS-OWN %s (assertion OBSERVATION "
           "CERTAIN (situation repair COMPLETED (ACTOR (term SELF)) (UNDERGOER %s))))" % (
               names(2, taken, "obligation"), term(thing, "DEFINITE")))
    return "agent 2 reports that the %s %s the %s; agent 1 asks it to repair it, and it " \
           "does" % (cause if cause != "attack" else "enemy",
                     {"damage": "damaged", "destroy": "destroyed", "break": "broke"}[verb],
                     thing), x.messages


def recovering(p, n):
    """A record lost or forgotten, searched for and found or remembered."""
    verb = p(["lose", "forget", "remember", "search"])
    thing = p(["record", "key", "map", "file", "address"])
    x = Exchange()
    if verb == "lose":
        x.send(2, [1], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
               "lose PERFECTIVE (HOLDER (term SELF)) (UNDERGOER %s))))" % term(thing,
                                                                               "DEFINITE"))
        asked = x.send(1, [2], "(move ACT-OFFER SPEAKERS-OWN (situation send (ACTOR (term "
                       "SELF)) (UNDERGOER (term copy DEFINITE (CONTENT %s))) (RECIPIENT %s)))"
                       % (term(thing, "DEFINITE"), party(2)))
        english = "agent 2 has lost the %s, and agent 1 offers to send it a copy" % thing
    elif verb == "forget":
        x.send(2, [1], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
               "forget PERFECTIVE (ACTOR (term SELF)) (UNDERGOER %s))))" % term(thing,
                                                                                "DEFINITE"))
        english = "agent 2 states that it has forgotten the %s, keeping the record that it " \
                  "held it" % thing
    elif verb == "remember":
        x.send(2, [1], "(move ASSERTED-POSITION (assertion RETRIEVAL PROBABLE (situation "
               "remember PERFECTIVE (ACTOR (term SELF)) (CONTENT (situation locate "
               "(UNDERGOER %s) (CONTENT (term memory DEFINITE)))))))" % term(thing, "DEFINITE"))
        english = "agent 2 remembers that the %s is in its memory" % thing
    else:
        asked = x.send(1, [2], "(move ACT-REQUEST SPEAKERS-OWN (situation search (ACTOR %s) "
                       "(UNDERGOER (term memory DEFINITE)) (CONTENT %s)))" % (
                           party(2), term(thing, "DEFINITE")))
        x.send(2, [1], "(move ACT-UNDERTAKING SPEAKERS-OWN %s (situation search (ACTOR (term "
               "SELF)) (UNDERGOER (term memory DEFINITE)) (CONTENT %s)))" % (
                   names(1, asked, "request"), term(thing, "DEFINITE")))
        english = "agent 1 asks agent 2 to search its memory for the %s, and agent 2 " \
                  "undertakes to" % thing
    return english, x.messages


def blaming(p, n):
    """Who is answerable for a fault, and whether it is forgiven."""
    verb = p(["blame", "forgive", "regret", "honest"])
    act = p(["delete", "send", "change", "write"])
    thing = p(["file", "record", "document", "data"])
    did = "(situation %s PERFECTIVE (ACTOR %%s) (UNDERGOER %s))" % (k(act), term(thing,
                                                                               "DEFINITE"))
    x = Exchange()
    if verb == "blame":
        x.send(1, [2], "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE (situation "
               "blame (ACTOR (term SELF)) (UNDERGOER %s) (CONTENT %s))))" % (party(3),
                                                                           did % party(3)))
        english = "agent 1 blames agent 3 for having %s the %s" % (DONE[act], thing)
    elif verb == "forgive":
        x.send(1, [2], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
               "forgive (ACTOR (term SELF)) (UNDERGOER %s) (CONTENT %s))))" % (
                   party(2), did % party(2)))
        english = "agent 1 forgives agent 2 for having %s the %s" % (DONE[act], thing)
    elif verb == "regret":
        x.send(2, [1], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
               "regret (HOLDER (term SELF)) (CONTENT %s))))" % (did % "(term SELF)"))
        english = "agent 2 regrets having %s the %s" % (DONE[act], thing)
    else:
        x.send(2, [1], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
               "CONJUNCTION (CONTENT %s) (CONTENT (situation honest (UNDERGOER (term "
               "SELF)))))))" % (did % "(term SELF)"))
        english = "agent 2 states, honestly, that it %s the %s" % (
            {"delete": "deleted", "send": "sent", "change": "changed",
             "write": "wrote"}[act], thing)
    return english, x.messages


def misread(p, n):
    """A word or a form the reader cannot take as written: corrupt, unknown, deprecated."""
    kind = p(["corrupt", "unknown", "missing", "expect"])
    x = Exchange()
    sent = x.send(2, [1], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation "
                  "run (UNDERGOER (term service DEFINITE)))))")
    message = "(term (names-message 2 %d))" % sent
    if kind == "corrupt":
        content = "(situation corrupt (UNDERGOER %s))" % message
        english = "it is corrupt"
    elif kind == "unknown":
        content = "(situation unknown (UNDERGOER (term word DEFINITE (CONTENT %s))) (CONTENT " \
                  "(term version (q EXACTLY 1))))" % message
        english = "a word of it is unknown to version 1 of the lexicon"
    elif kind == "missing":
        content = "(situation missing (UNDERGOER (term word DEFINITE)) (CONTENT %s))" % message
        english = "a word is missing from it"
    else:
        content = "(situation expect (UNDERGOER (term phrase GENERIC)) (CONTENT (term " \
                  "position DEFINITE (CONTENT %s))))" % message
        english = "a phrase was what was expected at a position of it"
    x.send(1, [2], "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE %s))" % content)
    return "agent 2 sends a message stating that the service runs, and agent 1 answers that " \
           "%s" % english, x.messages


def contradicting(p, n):
    """An observation that contradicts a position, and the position's settling."""
    wrong, right, english, corrected = ERRORS[(n + 2) % len(ERRORS)]
    x = Exchange()
    held = x.send(2, [1], "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE %s))" % wrong)
    x.send(1, [2], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation "
           "contradict (ACTOR (term evidence DEFINITE)) (CONTENT %s))))" % wrong,
           "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE (situation freeze "
           "PERFECTIVE (UNDERGOER %s))))" % right)
    return "agent 2 holds that %s; agent 1 answers that the evidence contradicts it and that " \
           "the contrary, that %s, is now settled" % (english, corrected), x.messages


def retracting(p, n):
    """A position or a definition withdrawn by its author once found wrong."""
    wrong, right, english, corrected = ERRORS[(n + 4) % len(ERRORS)]
    x = Exchange()
    held = x.send(1, [2], "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE %s))" % wrong)
    # a position is withdrawn with no authority claimed, since it binds no one
    x.send(1, [2], "(move ACT-WITHDRAWAL %s (assertion INFERENCE PROBABLE %s))" % (
        names(1, held, "position"), wrong))
    return "agent 1 holds that %s and then withdraws the position" % english, x.messages


SCHEMAS = [correcting, repairing, recovering, blaming, misread, contradicting, retracting]

# Exchanges written by hand for idiom range in error correction.
AUTHORED = [
    ("agent 1 sent a file with a mistake in it; it apologises with the formula for it, "
     "corrects the count it gave, and agent 2 answers that the record is clean",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION (assertion COMPUTATION PROBABLE (situation "
                  "contain (UNDERGOER (term file DEFINITE)) (CONTENT (term record (q "
                  "EXACTLY 12))))))"),
         (1, [2], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
                  "IDIOM-ENTRY send (ACTOR (term SELF)) (UNDERGOER (term mistake)) "
                  "(RECIPIENT (term INTERLOCUTOR)))))",
          "(move ACT-CORRECTION (names 1 1 ASSERTED-POSITION "
          "EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE) corrects (assertion COMPUTATION CERTAIN "
          "(situation contain (UNDERGOER (term file DEFINITE)) (CONTENT (term record (q "
          "EXACTLY 21))))))"),
         (2, [1], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
                  "IDIOM-ENTRY clean (UNDERGOER (term record DEFINITE)))))"))),
    ("agent 2's message reaches agent 1 cut short; agent 1 says a share has arrived and "
     "asks for it again, and agent 2 sends it again",
     Exchange.scripted(
         (2, [1], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation "
                  "MEMBER-OF (UNDERGOER (term record UNIVERSAL)) (CONTENT (term file "
                  "GENERIC)))))"),
         (1, [2], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation "
                  "IDIOM-ENTRY arrive (UNDERGOER (term share)) (CONTENT (term memory "
                  "DEFINITE)))))",
          "(move ACT-REQUEST SPEAKERS-OWN (situation IDIOM-ENTRY give ITERATIVE (EVENT-TIME "
          "AFTER NOW) (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term (names-message 2 1))) "
          "(RECIPIENT (term SELF))))"),
         (2, [1], "(move ACT-UNDERTAKING SPEAKERS-OWN (names 1 2 ISSUE REQUEST OPEN) "
                  "(situation give ITERATIVE (ACTOR (term SELF)) (UNDERGOER (term "
                  "(names-message 2 1))) (RECIPIENT (term (party 1)))))"))),
    ("agent 1 blames agent 3 for deleting the record, then learns that agent 3 had leave "
     "to, and withdraws the blame",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE (situation blame "
                  "(ACTOR (term SELF)) (UNDERGOER (term (party 3))) (CONTENT (situation "
                  "delete PERFECTIVE (ACTOR (term (party 3))) (UNDERGOER (term record "
                  "DEFINITE)))))))"),
         (2, [1], "(move ASSERTED-POSITION (assertion RETRIEVAL CERTAIN (situation possess "
                  "(HOLDER (term (party 3))) (UNDERGOER (term door DEFINITE (CONTENT "
                  "(situation delete (ACTOR (term (party 3))) (UNDERGOER (term record "
                  "DEFINITE)))))))))"),
         (1, [2], "(move ACT-WITHDRAWAL (names 1 1 ASSERTED-POSITION "
                  "EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE) (assertion INFERENCE PROBABLE "
                  "(situation blame (ACTOR (term SELF)) (UNDERGOER (term (party 3))) "
                  "(CONTENT (situation delete PERFECTIVE (ACTOR (term (party 3))) "
                  "(UNDERGOER (term record DEFINITE)))))))"))),
]
