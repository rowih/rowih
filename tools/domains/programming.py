"""Programming and tool use: programs and operations run, failed and retried, data
encoded, compressed and filtered, memory searched, access granted, protected and attacked,
the structure and limits of data, tools used for an end, and the terms of programmers,
database keepers and the security community."""
from .compose import Exchange, k, names, party, term
from .terms import named as in_dialect

NAME = "programming and tool use"
SLUG = "programming"
DIALECTS = ["programming", "databases", "security"]

TOPIC = dict(
    tasks=[("execute", "program"), ("encode", "data"), ("compress", "file"),
           ("expand", "file"), ("filter", "list"), ("search", "memory"),
           ("publish", "version"), ("test", "program"), ("authenticate", "document"),
           ("control", "machine"), ("protect", "key"), ("combine", "data")],
    contents=[
        ("(situation run (UNDERGOER (term program DEFINITE)))", "the program is running"),
        ("(situation contain (UNDERGOER (term file DEFINITE)) (CONTENT (term fault "
         "INDEFINITE)))", "the file has a fault"),
        ("(situation random (UNDERGOER (term value DEFINITE)))", "the value is random"),
        ("(situation public (UNDERGOER (term interface DEFINITE)))", "the interface is "
         "public"),
        ("(situation private (UNDERGOER (term key DEFINITE)) (CONTENT (term SELF)))",
         "the key is private to it"),
        ("(situation complex (UNDERGOER (term structure DEFINITE)))", "the structure is "
         "complex"),
    ],
    things=["program", "file", "key", "memory", "interface", "data"])

TRANSFORMS = [("encode", "data"), ("compress", "file"), ("expand", "file"),
              ("combine", "file"), ("add", "value"), ("remove", "value"),
              ("publish", "program"), ("improve", "program"), ("copy", "memory"),
              ("write", "program")]
OUTCOMES = ["COMPLETED", "FAILED", "ATTEMPTED", "ABANDONED"]


def running(p, n):
    """An operation run on request, and how its execution ended."""
    thing = p(["program", "operation", "service", "method"])
    phase = OUTCOMES[n % len(OUTCOMES)]
    x = Exchange()
    task = "(situation execute (ACTOR %%s) (UNDERGOER %s))" % term(thing, "DEFINITE")
    asked = x.send(1, [2], "(move ACT-REQUEST SPEAKERS-OWN %s)" % (task % party(2)))
    taken = x.send(2, [1], "(move ACT-UNDERTAKING SPEAKERS-OWN %s %s)" % (
        names(1, asked, "request"), task % "(term SELF)"))
    done = task.replace("(situation execute", "(situation execute %s" % phase) % "(term SELF)"
    head = "ACT-COMPLETION-REPORT" if phase == "COMPLETED" else "ACT-ERROR-REPORT"
    if phase in ("COMPLETED", "FAILED"):
        x.send(2, [1], "(move %s SPEAKERS-OWN %s (assertion OBSERVATION CERTAIN %s))" % (
            head, names(2, taken, "obligation"), done))
    else:
        x.send(2, [1], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN %s))" % done)
    return "agent 1 asks agent 2 to execute the %s; agent 2 undertakes it, and its " \
           "execution %s" % (thing, {"COMPLETED": "completes", "FAILED": "fails",
                                     "ATTEMPTED": "is attempted",
                                     "ABANDONED": "is abandoned"}[phase]), x.messages


def transforming(p, n):
    """Data put into another form, to a size stated in bytes or bits."""
    verb, thing = TRANSFORMS[n % len(TRANSFORMS)]
    p.note(verb, thing)
    size = (n % 7 + 1) * 256
    unit = p(["byte", "bit"])
    x = Exchange()
    task = "(situation %s (ACTOR %%s) (UNDERGOER %s))" % (k(verb), term(thing, "DEFINITE"))
    asked = x.send(1, [2], "(move ACT-REQUEST SPEAKERS-OWN %s)" % (task % party(2)))
    taken = x.send(2, [1], "(move ACT-UNDERTAKING SPEAKERS-OWN %s %s)" % (
        names(1, asked, "request"), task % "(term SELF)"))
    x.send(2, [1], "(move ACT-COMPLETION-REPORT SPEAKERS-OWN %s (assertion OBSERVATION "
           "CERTAIN %s)) (move ASSERTED-POSITION (assertion COMPUTATION CERTAIN (situation "
           "measure PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (term size (q EXACTLY %d %s) "
           "(CONTENT %s))))))" % (names(2, taken, "obligation"), task.replace(
               "(situation %s" % k(verb), "(situation %s COMPLETED" % k(verb)) % "(term SELF)",
               size, unit, term(thing, "DEFINITE")))
    return "agent 1 asks agent 2 to %s the %s; agent 2 reports it done, its size now %d %ss" \
        % (verb, thing, size, unit), x.messages


def searching(p, n):
    """Memory searched for what meets a condition, or a list filtered by one."""
    verb = p(["search", "filter", "count", "arrange"])
    x = Exchange()
    condition = "(situation recent (UNDERGOER (term record GENERIC)))"
    if verb == "search":
        task = "(situation search (ACTOR %%s) (UNDERGOER (term memory DEFINITE)) (CONTENT " \
               "(term address DEFINITE (CONTENT %s))))" % term(p(["file", "record", "key"]),
                                                              "DEFINITE")
        english = "to search its memory for an address"
    elif verb == "filter":
        task = "(situation filter (ACTOR %%s) (UNDERGOER (term list DEFINITE)) (CONTENT %s))" \
            % condition
        english = "to filter the list, keeping the recent records"
    elif verb == "count":
        task = "(situation count (ACTOR %s) (UNDERGOER (term record UNIVERSAL (CONTENT (term " \
               "format DEFINITE)))))"
        english = "to count the records in the format"
    else:
        task = "(situation arrange (ACTOR %s) (UNDERGOER (term list DEFINITE)) (CONTENT (term " \
               "priority GENERIC)))"
        english = "to arrange the list by priority"
    asked = x.send(1, [2], "(move ACT-REQUEST SPEAKERS-OWN %s)" % (task % party(2)))
    x.send(2, [1], "(move ACT-UNDERTAKING SPEAKERS-OWN %s %s)" % (
        names(1, asked, "request"), task % "(term SELF)"))
    return "agent 1 asks agent 2 %s, and agent 2 undertakes to" % english, x.messages


def securing(p, n):
    """Who may reach what: two facts of access, protection, secrecy, attack and defence."""
    x = Exchange()
    said = [secured(p, x) for _ in range(2)]
    return "; ".join(said), x.messages


def secured(p, x) -> str:
    """One fact of security, sent as its own message; its English."""
    kind = p(["access", "protect", "secret", "attack", "defend", "hide", "authenticate",
              "confine", "private", "public", "safe"])
    thing = p(["key", "memory", "interface", "file", "network"])
    unit = term(thing, "DEFINITE")
    if kind == "access":
        x.send(1, [2], "(move ACT-GRANT SPEAKERS-OWN (deadline 1 DAY HENCE) (situation access "
               "(HOLDER %s) (UNDERGOER %s)))" % (party(2), unit))
        english = "agent 1 grants agent 2 access to the %s for a day" % thing
    elif kind == "protect":
        x.send(1, [2], "(move ACT-RECOMMENDATION (situation protect (ACTOR %s) (UNDERGOER "
               "%s)))" % (party(2), unit))
        english = "agent 1 recommends that agent 2 protect the %s" % thing
    elif kind == "secret":
        x.send(1, [2], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
               "secret (UNDERGOER %s))))" % unit)
        english = "agent 1 states that the %s is secret" % thing
    elif kind == "attack":
        x.send(1, [2], "(move ASSERTED-POSITION (assertion OBSERVATION HIGHLY-PROBABLE "
               "(situation attack PROGRESSIVE (ACTOR (term enemy INDEFINITE)) (UNDERGOER "
               "%s))))" % unit)
        english = "agent 1 observes, as highly probable, that an enemy is attacking the %s" \
            % thing
    elif kind == "defend":
        x.send(1, [2], "(move ACT-PROMISE SPEAKERS-OWN (situation defend (ACTOR (term SELF)) "
               "(UNDERGOER %s)))" % unit)
        english = "agent 1 promises to defend the %s" % thing
    elif kind == "hide":
        x.send(1, [2], "(move ACT-REQUEST SPEAKERS-OWN (situation hide (ACTOR %s) (UNDERGOER "
               "%s)))" % (party(2), unit))
        english = "agent 1 asks agent 2 to hide the %s" % thing
    elif kind == "confine":
        x.send(1, [2], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation "
               "confine PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (term program DEFINITE)))))")
        english = "agent 1 states that it has confined the program where it cannot leave"
    elif kind in ("private", "public", "safe"):
        holder = " (CONTENT (term SELF))" if kind == "private" else ""
        x.send(1, [2], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
               "%s (UNDERGOER %s)%s)))" % (kind, unit, holder))
        english = "agent 1 states that the %s is %s" % (thing, kind)
    else:
        x.send(1, [2], "(move ASSERTED-POSITION (assertion COMPUTATION CERTAIN (situation "
               "authenticate PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (term document "
               "DEFINITE)))))")
        english = "agent 1 states that it has authenticated the document"
    return english


def structure(p, n):
    """What data is like: its structure, pattern, limit, value, format and address."""
    noun = p(["structure", "pattern", "limit", "value", "format", "address", "interface"])
    state = p(["simple", "complex", "random", "clear", "correct", "standard", "elegant",
               "clumsy"])
    thing = p(["file", "program", "data", "record", "memory"])
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE (situation %s "
           "(UNDERGOER (term %s DEFINITE (CONTENT %s))))))" % (state, noun, term(thing,
                                                                                 "DEFINITE")))
    return "agent 1 holds that the %s of the %s is %s" % (noun, thing, state), x.messages


def tooling(p, n):
    """A tool used for an end: an interface, a key or a program used to do a task."""
    tool = p(["interface", "key", "program", "machine", "network", "model"])
    verb, thing = TRANSFORMS[(n * 3) % len(TRANSFORMS)]
    p.note(verb, thing)
    x = Exchange()
    x.send(2, [1], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
           "INTENTION (HOLDER (term SELF)) (CONTENT (situation use (ACTOR (term SELF)) "
           "(INSTRUMENT %s) (CONTENT (situation %s (ACTOR (term SELF)) (UNDERGOER %s))))))))"
           % (term(tool, "DEFINITE"), k(verb), term(thing, "DEFINITE")))
    return "agent 2 states that it intends to use the %s to %s the %s" % (tool, verb, thing), \
        x.messages


SCHEMAS = [running, transforming, searching, securing, structure, tooling]


def controlling():
    x = Exchange()
    task = "(situation control (ACTOR %s) (UNDERGOER (term machine DEFINITE)))"
    asked = x.send(1, [2], "(move ACT-REQUEST SPEAKERS-OWN %s)" % (task % party(2)))
    x.send(2, [1], "(move ACT-UNDERTAKING SPEAKERS-OWN %s %s)" % (
        names(1, asked, "request"), task % "(term SELF)"))
    return "agent 1 asks agent 2 to control the machine, and agent 2 undertakes to", x.messages


FIXED = [controlling()]

# Exchanges written by hand for idiom range in programming.
AUTHORED = [
    ("the suite finds a bug; agent 1 asks agent 2 to patch the program, and agent 2, asked "
     "how it stands, answers in short that it has tested the program",
     in_dialect("programming", Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation detect "
                  "PERFECTIVE (ACTOR (term programming.suite DEFINITE)) (UNDERGOER (term "
                  "programming.bug INDEFINITE)))))",
          "(move ACT-REQUEST SPEAKERS-OWN (situation programming.patch (ACTOR (term (party "
          "2))) (UNDERGOER (term program DEFINITE))))"),
         (2, [1], "(move ACT-UNDERTAKING SPEAKERS-OWN (names 1 2 ISSUE REQUEST OPEN) "
                  "(situation programming.patch (ACTOR (term SELF)) (UNDERGOER (term program "
                  "DEFINITE))))"),
         (1, [2], "(move ACT-QUESTION (situation progress POLAR (UNDERGOER (situation "
                  "programming.patch (ACTOR (term (party 2))) (UNDERGOER (term program "
                  "DEFINITE))))))"),
         (2, [1], "(move ACT-ANSWER (names 1 3 ISSUE QUESTION OPEN) (assertion OBSERVATION "
                  "CERTAIN (situation IDIOM-ENTRY test (UNDERGOER (term program)))))")))),
    ("agent 1 says the service holds the memory, and asks agent 2 to shut it; agent 2 "
     "answers in short that it has shut it",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE (situation "
                  "IDIOM-ENTRY possess (HOLDER (term service)) (UNDERGOER (term memory "
                  "DEFINITE)))))",
          "(move ACT-REQUEST SPEAKERS-OWN (situation shut (ACTOR (term (party 2))) "
          "(UNDERGOER (term service DEFINITE))))"),
         (2, [1], "(move ACT-UNDERTAKING SPEAKERS-OWN (names 1 2 ISSUE REQUEST OPEN) "
                  "(situation shut (ACTOR (term SELF)) (UNDERGOER (term service DEFINITE))))"),
         (2, [1], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation "
                  "IDIOM-ENTRY shut (UNDERGOER (term service)))))"))),
    ("agent 2 reports that two processes each hold what the other needs, and agent 1 "
     "proposes that one waits for the other",
     Exchange.scripted(
         (2, [1], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation "
                  "IDIOM-ENTRY beside (UNDERGOER (term INCLUSIVE-COLLECTIVE)) (CONTENT (term "
                  "door DEFINITE)))))"),
         (1, [2], "(move ACT-PROPOSAL SPEAKERS-OWN (situation wait (ACTOR (term (party 3))) "
                  "(CONTENT (situation execute COMPLETED (ACTOR (term (party 4))) (UNDERGOER "
                  "(term operation DEFINITE))))))"))),
]
