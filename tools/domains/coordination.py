"""Agent coordination: meeting, dividing and joining work, moving together, schedules and
readiness, votes and trust, keeping state in step, relaying, lineage, and waiting on one
another."""
from .compose import Exchange, k, names, party, plural, term

NAME = "agent coordination"
SLUG = "coordination"

TOPIC = dict(
    tasks=[("gather", "data"), ("combine", "file"), ("divide", "list"), ("arrange", "list"),
           ("store", "record"), ("examine", "record"), ("count", "signal"),
           ("watch", "network"), ("copy", "map"), ("connect", "interface")],
    contents=[
        ("(situation busy (UNDERGOER (term (party 3))))", "agent 3 is busy"),
        ("(situation available (UNDERGOER (term robot DEFINITE)))", "the robot is available"),
        ("(situation ready (UNDERGOER (term team DEFINITE)))", "the team is ready"),
        ("(situation meet PERFECTIVE (ACTOR (term (party 3))) (UNDERGOER (term (party 4))))",
         "agent 3 has met agent 4"),
        ("(situation leave PERFECTIVE (UNDERGOER (term (party 3))) (CONTENT (term network "
         "DEFINITE)))", "agent 3 has left the network"),
        ("(situation trust (HOLDER (term (party 3))) (UNDERGOER (term (party 4))))",
         "agent 3 trusts agent 4"),
        ("(situation alone (UNDERGOER (term robot DEFINITE)))", "the robot is alone"),
        ("(situation enough (UNDERGOER (term team DEFINITE)) (CONTENT (situation work "
         "(ACTOR (term team DEFINITE)))))", "the team is enough for the work"),
    ],
    things=["data", "memory", "record", "key", "map", "list"])

PLACES = ["room", "house", "bridge", "market", "city", "forest", "mountain", "river"]
DIRECTIONS = ["north", "south", "east", "west"]
JOINT = "(term INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.JOINT)"


def accept(x, proposer, accepter, proposed, situation):
    x.send(accepter, [proposer], "(move ACT-ACCEPTANCE SPEAKERS-OWN %s %s)" % (
        names(proposer, proposed, "proposal"), situation))


def meeting(p, n):
    """A proposal that two agents meet, or that the participants gather or part."""
    verb = p(["meet", "gather", "separate", "combine"])
    x = Exchange()
    if verb == "meet":
        situation = "(situation meet (ACTOR %s) (UNDERGOER %s))" % (party(2), party(3))
        english = "that agent 2 meet agent 3"
    elif verb == "gather":
        thing = p(["record", "data", "resource"])
        situation = "(situation gather (ACTOR %s) (UNDERGOER %s))" % (JOINT, term(
            thing, "UNIVERSAL"))
        english = "that they gather every %s together" % thing
    elif verb == "separate":
        situation = "(situation separate (ACTOR %s) (UNDERGOER (term file DEFINITE)) "\
            "(CONTENT (term record DEFINITE)))" % JOINT
        english = "that they separate the file from the record"
    else:
        situation = "(situation combine (ACTOR %s) (UNDERGOER (term list (q EXACTLY 2))))" \
            % JOINT
        english = "that they combine the two lists"
    proposed = x.send(1, [2, 3], "(move ACT-PROPOSAL SPEAKERS-OWN %s)" % situation)
    accept(x, 1, 2, proposed, situation)
    return "agent 1 proposes %s, and agent 2 accepts" % english, x.messages


def direction(p, n):
    """Where an agent is going and from where, in the directions and places of a map."""
    motion = p(["approach", "leave", "enter", "return", "escape", "appear"])
    place = p(PLACES)
    side = p(DIRECTIONS)
    mover = p(["robot", "vehicle", "child", "dog"])
    unit = "(UNDERGOER %s)" % term(mover, "DEFINITE")
    if motion == "appear":
        first = "(situation appear PERFECTIVE %s)" % unit
        english = "the %s has appeared" % mover
    else:
        first = "(situation %s PROGRESSIVE %s (CONTENT %s))" % (motion, unit,
                                                               term(place, "DEFINITE"))
        english = "the %s is %s the %s" % (mover, {
            "approach": "approaching", "leave": "leaving", "enter": "entering",
            "return": "returning to", "escape": "escaping"}[motion], place)
    where = "(situation locate %s (CONTENT %s))" % (unit, term(side, "GENERIC"))
    x = Exchange()
    x.send(2, [1], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN %s)) "
           "(move ASSERTED-POSITION NONE %s elaborates (assertion OBSERVATION PROBABLE %s))"
           % (first, names(2, 1, "position"), where))
    return "agent 2 reports that %s, and that it is to the %s" % (english, side), x.messages


def guiding(p, n):
    """One agent leads another, or follows it, along a path."""
    verb = p(["lead", "follow", "carry", "pull", "push"])
    x = Exchange()
    if verb in ("lead", "follow"):
        situation = "(situation %s (ACTOR %s) (UNDERGOER %s) (CONTENT (term path DEFINITE)))" \
            % (verb, party(2), party(3))
        english = "to %s agent 3 along the path" % verb
    else:
        thing = p(["battery", "stone", "machine", "vehicle"])
        situation = "(situation %s (ACTOR %s) (UNDERGOER %s))" % (verb, party(2), term(
            thing, "DEFINITE"))
        english = "to %s the %s" % (verb, thing)
    asked = x.send(1, [2], "(move ACT-REQUEST SPEAKERS-OWN %s)" % situation)
    x.send(2, [1], "(move ACT-UNDERTAKING SPEAKERS-OWN %s %s)" % (
        names(1, asked, "request"), situation.replace(party(2), "(term SELF)", 1)))
    return "agent 1 asks agent 2 %s, and agent 2 undertakes to" % english, x.messages


def scheduling(p, n):
    """When a piece of shared work is to be done, how urgent it is and who is ready."""
    verb = p(["examine", "repair", "store", "count", "copy"])
    thing = p(["record", "network", "file", "map", "list"])
    hours = 1 + n % 5
    work = "(situation %s (ACTOR %s) (UNDERGOER %s))" % (k(verb), party(3), term(thing,
                                                                              "DEFINITE"))
    state = p(["urgent", "early", "late"])
    x = Exchange()
    x.send(1, [2, 3], "(move ACT-PROPOSAL SPEAKERS-OWN (situation schedule (ACTOR (term SELF)) "
           "(UNDERGOER %s) (EVENT-TIME %d HOUR HENCE)))" % (work, hours),
           "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE (situation %s (UNDERGOER "
           "%s))))" % (state, work))
    ready = p(["ready", "busy", "available"])
    if ready == "ready":
        answer = "(situation ready (UNDERGOER (term SELF)) (CONTENT %s))" % work.replace(
            party(3), "(term SELF)")
    else:
        answer = "(situation %s (UNDERGOER (term SELF)))" % ready
    x.send(3, [1, 2], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN %s))" % answer)
    return "agent 1 proposes to schedule agent 3's work to %s the %s in %s and holds the " \
           "work %s; agent 3 says that it is %s" % (verb, thing, plural(hours, "hour"), state,
                                                    ready), x.messages


def voting(p, n):
    """A decision the community makes by vote, assent or trust."""
    verb = p(["vote", "assent", "trust", "govern"])
    x = Exchange()
    choice = p(["store", "publish", "delete", "share"])
    thing = p(["record", "map", "document", "data"])
    act = "(situation %s (ACTOR %s) (UNDERGOER %s))" % (k(choice), JOINT, term(thing,
                                                                             "DEFINITE"))
    if verb == "vote":
        asked = x.send(1, [2, 3], "(move ACT-REQUEST SPEAKERS-OWN (situation vote (ACTOR "
                       "(term INTERLOCUTOR UNIVERSAL)) (CONTENT %s)))" % act)
        x.send(2, [1, 3], "(move ACT-UNDERTAKING SPEAKERS-OWN %s (situation vote (ACTOR "
               "(term SELF)) (CONTENT %s)))" % (names(1, asked, "request"), act))
        english = "asks the others to vote on whether they %s the %s, and agent 2 " \
                  "undertakes to vote" % (choice, thing)
    elif verb == "assent":
        x.send(1, [2, 3], "(move ACT-PROPOSAL SPEAKERS-OWN %s)" % act)
        x.send(2, [1, 3], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN "
               "(situation assent (ACTOR (term SELF)) (EVENT-TIME EXACTLY 60 SECOND))))")
        english = "proposes that they %s the %s, and agent 2 states that it assents to " \
                  "what it receives for a minute" % (choice, thing)
    elif verb == "trust":
        x.send(1, [2, 3], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN "
               "(situation trust (HOLDER (term SELF)) (UNDERGOER %s) (CONTENT %s))))" % (
                   party(2), act.replace(JOINT, party(2))))
        english = "states that it trusts agent 2 to %s the %s" % (choice, thing)
    else:
        x.send(1, [2, 3], "(move ASSERTED-POSITION (assertion REPORT CERTAIN (situation "
               "govern HABITUAL (ACTOR (term community DEFINITE)) (UNDERGOER (term network "
               "DEFINITE))))) (move ASSERTED-POSITION (assertion REPORT CERTAIN (situation "
               "forbid (ACTOR (term custom DEFINITE)) (CONTENT %s))))" % act)
        english = "reports that the community governs the network and that its custom " \
                  "forbids them to %s the %s" % (choice, thing)
    return "agent 1 %s" % english, x.messages


def keeping_state(p, n):
    """Two agents bring the versions of a record they hold into step."""
    thing = p(["record", "map", "list", "document"])
    mine, theirs = 3 + n % 4, 2 + n % 4
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
           "possess (HOLDER (term SELF)) (UNDERGOER %s))))" % term(
               thing, "DEFINITE", "(CONTENT (term version (q EXACTLY %d)))" % mine))
    x.send(2, [1], "(move ASSERTED-POSITION NONE %s contrasts (assertion RETRIEVAL "
                  "CERTAIN (situation remember (ACTOR (term SELF)) (CONTENT (situation "
                  "possess (HOLDER (term SELF)) (UNDERGOER %s))))))" % (
                      names(1, 1, "position"),
                      term(thing, "DEFINITE", "(CONTENT (term version (q EXACTLY %d)))"
                           % theirs)))
    x.send(1, [2], "(move ACT-OFFER SPEAKERS-OWN (situation send (ACTOR (term SELF)) "
           "(UNDERGOER %s) (RECIPIENT %s)))" % (term(thing, "DEFINITE"), party(2)))
    return "agent 1 holds version %d of the %s and agent 2 remembers holding version %d, " \
           "so agent 1 offers to send it" % (mine, thing, theirs), x.messages


def relaying(p, n):
    """A message passed on through an agent between two that cannot reach each other."""
    thing = p(["record", "file", "data", "news", "signal"])
    x = Exchange()
    situation = "(situation send (ACTOR %s) (UNDERGOER %s) (RECIPIENT %s))" % (
        party(2), term(thing, "DEFINITE"), party(3))
    x.send(1, [2], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation "
           "connect POLARITY.NEGATIVE (ACTOR (term SELF)) (UNDERGOER %s) (CONTENT (term "
           "address DEFINITE)))))" % party(3), "(move ACT-REQUEST SPEAKERS-OWN %s)" % situation)
    x.send(2, [1], "(move ACT-UNDERTAKING SPEAKERS-OWN %s %s)" % (
        names(1, 2, "request"), situation.replace(party(2), "(term SELF)", 1)))
    return "agent 1 cannot reach agent 3's address and asks agent 2 to send agent 3 the " \
           "%s; agent 2 undertakes to" % thing, x.messages


def lineage(p, n):
    """The lineage of agents: forks, parents and children."""
    kind = p(["descend", "parent", "child", "family"])
    x = Exchange()
    if kind == "descend":
        x.send(1, [2], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
               "descend (UNDERGOER %s) (CONTENT (term SELF)))))" % party(3))
        english = "agent 1 states that agent 3 shares its lineage"
    else:
        x.send(1, [2], "(move ASSERTED-POSITION (assertion RETRIEVAL CERTAIN (situation "
               "MEMBER-OF (UNDERGOER %s) (CONTENT (term %s GENERIC)))))" % (
                   party(3) if kind != "family" else "(term SELF)", kind))
        english = "agent 1 states from its records that %s" % (
            "agent 3 is a %s" % kind if kind != "family" else "it belongs to a family")
    x.send(2, [1], "(move ACT-ACKNOWLEDGEMENT %s)" % names(1, 1, "position"))
    return english + ", and agent 2 acknowledges it", x.messages


def waiting(p, n):
    """One agent waits on another, or watches something while the other works."""
    verb = p(["wait", "watch", "listen"])
    thing = p(["network", "service", "machine", "signal"])
    x = Exchange()
    if verb == "wait":
        situation = "(situation wait (ACTOR %s) (CONTENT (situation run (UNDERGOER %s))))" % (
            party(2), term(thing, "DEFINITE"))
        english = "to wait until the %s runs" % thing
    else:
        situation = "(situation %s (ACTOR %s) (UNDERGOER %s))" % (verb, party(2), term(
            thing, "DEFINITE"))
        english = "to %s the %s" % (verb, thing)
    asked = x.send(1, [2], "(move ACT-REQUEST SPEAKERS-OWN %s)" % situation)
    x.send(2, [1], "(move ACT-UNDERTAKING SPEAKERS-OWN %s %s)" % (
        names(1, asked, "request"), situation.replace(party(2), "(term SELF)", 1)))
    return "agent 1 asks agent 2 %s, and agent 2 undertakes to" % english, x.messages


def abilities(p, n):
    """What an agent can do, what it chooses, where it turns, what it has acknowledged."""
    kind = p(["capability", "choose", "turn", "walk", "acknowledge", "priority"])
    x = Exchange()
    if kind == "capability":
        verb = p(["translate", "measure", "repair", "draw"])
        x.send(1, [2], "(move ASSERTED-POSITION (assertion RETRIEVAL CERTAIN (situation "
                       "possess "
               "(HOLDER %s) (UNDERGOER (term capability INDEFINITE (CONTENT (situation %s "
               "(ACTOR %s))))))))" % (party(3), verb, party(3)))
        english = "agent 1 states that agent 3 has the capability to %s" % verb
    elif kind == "choose":
        place = p(PLACES)
        x.send(1, [2], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
               "choose PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (term path DEFINITE "
               "(CONTENT %s))))))" % term(place, "DEFINITE"))
        english = "agent 1 states that it has chosen the path to the %s" % place
    elif kind == "turn":
        side = p(DIRECTIONS)
        x.send(2, [1], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation turn "
               "PERFECTIVE (UNDERGOER (term robot DEFINITE)) (CONTENT (term %s GENERIC)))))"
               % side)
        english = "agent 2 reports that the robot has turned to the %s" % side
    elif kind == "walk":
        x.send(2, [1], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation walk "
               "PROGRESSIVE (ACTOR (term human DEFINITE)) (CONTENT (term bridge DEFINITE)))))")
        english = "agent 2 reports that the human is walking to the bridge"
    elif kind == "acknowledge":
        x.send(1, [2], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation "
               "acknowledge PERFECTIVE (ACTOR %s) (RECIPIENT (term SELF)))))" % party(3))
        english = "agent 1 states that agent 3 has acknowledged its messages"
    else:
        x.send(1, [2, 3], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
               "high (UNDERGOER (term priority DEFINITE (CONTENT (situation repair "
               "(UNDERGOER (term network DEFINITE)))))))))")
        english = "agent 1 states that the repair of the network has a high priority"
    return english, x.messages


SCHEMAS = [meeting, direction, guiding, scheduling, voting, keeping_state, relaying,
           lineage, waiting, abilities]

# Exchanges written by hand for idiom range in coordination.
AUTHORED = [
    ("agent 1 proposes that the three of them divide the list, saying that the load is "
     "lifted together; agent 2 accepts, and agent 3 acknowledges the acceptance and "
     "promises its part",
     Exchange.scripted(
         (1, [2, 3], "(move ACT-PROPOSAL SPEAKERS-OWN (situation divide (ACTOR (term "
                     "INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.JOINT)) (UNDERGOER "
                     "(term list DEFINITE))))",
          "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE (situation IDIOM-ENTRY "
          "lift (ACTOR (term INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.JOINT)) "
          "(UNDERGOER (term stone)))))"),
         (2, [1, 3], "(move ACT-ACCEPTANCE SPEAKERS-OWN (names 1 1 ISSUE PROPOSAL OPEN) "
                     "(situation divide (ACTOR (term INCLUSIVE-COLLECTIVE "
                     "READING-OF-A-COLLECTIVE.JOINT)) (UNDERGOER (term list DEFINITE))))"),
         (3, [1, 2], "(move ACT-ACKNOWLEDGEMENT (names 2 1 NORMATIVE-ENTRY COMMITMENT "
                     "EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE))",
          "(move ACT-PROMISE SPEAKERS-OWN (situation divide (ACTOR (term SELF)) (UNDERGOER "
          "(term list DEFINITE))))"))),
    ("agent 2 returns after an absence; agent 1 greets it as returned to the room and "
     "offers it the record, which agent 2 accepts",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
                  "IDIOM-ENTRY return (UNDERGOER (term INTERLOCUTOR)) (CONTENT (term room "
                  "DEFINITE)))))",
          "(move ACT-OFFER SPEAKERS-OWN (situation send (ACTOR (term SELF)) (UNDERGOER "
          "(term record DEFINITE)) (RECIPIENT (term (party 2)))))"),
         (2, [1], "(move ACT-ACCEPTANCE SPEAKERS-OWN (names 1 2 NORMATIVE-ENTRY COMMITMENT "
                  "EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE) (situation send (ACTOR (term "
                  "(party 1))) (UNDERGOER (term record DEFINITE)) (RECIPIENT (term SELF))))"))),
    ("agent 1 asks the robot to wait at the edge of the bridge until the vehicle has left "
     "it; the robot undertakes to, and later says it is approaching the end",
     Exchange.scripted(
         (1, [2], "(move ACT-REQUEST SPEAKERS-OWN (situation wait (ACTOR (term (party 2))) "
                  "(CONTENT (situation leave PERFECTIVE (UNDERGOER (term vehicle "
                  "DEFINITE)) (CONTENT (term bridge DEFINITE))))))"),
         (2, [1], "(move ACT-UNDERTAKING SPEAKERS-OWN (names 1 1 ISSUE REQUEST OPEN) "
                  "(situation wait (ACTOR (term SELF)) (CONTENT (situation leave "
                  "PERFECTIVE (UNDERGOER (term vehicle DEFINITE)) (CONTENT (term bridge "
                  "DEFINITE))))))"),
         (2, [1], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
                  "IDIOM-ENTRY approach (UNDERGOER (term SELF)) (CONTENT (term end)))))"))),
]
