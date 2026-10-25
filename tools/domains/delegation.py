"""Task delegation: work assigned with its deadline, plans of several steps, agents hired
and paid, what an agent can and cannot do, how far work has gone and what comes first,
commands, promises and their withdrawal, the demands of a task, and the robots' and
planners' terms."""
from .compose import Exchange, k, names, party, plural, term

NAME = "task delegation"
SLUG = "delegation"
DIALECTS = ["robotics", "planning"]

TOPIC = dict(
    tasks=[("design", "interface"), ("produce", "document"), ("improve", "method"),
           ("solve", "problem"), ("test", "machine"), ("arrange", "step"),
           ("make", "model"), ("measure", "distance"), ("translate", "text"),
           ("allocate", "resource"), ("examine", "machine"), ("count", "battery")],
    contents=[
        ("(situation progress (UNDERGOER (situation work (ACTOR (term team DEFINITE)))))",
         "the team's work is going forward"),
        ("(situation urgent (UNDERGOER (situation repair (ACTOR (term robot DEFINITE)) "
         "(UNDERGOER (term bridge DEFINITE)))))", "the robot's repair of the bridge is urgent"),
        ("(situation difficult (UNDERGOER (situation design (ACTOR (term SELF)) (UNDERGOER "
         "(term model DEFINITE)))))", "designing the model is difficult"),
        ("(situation easy (UNDERGOER (situation count (ACTOR (term SELF)) (UNDERGOER (term "
         "battery UNIVERSAL)))))", "counting every battery is easy"),
    ],
    things=["machine", "battery", "document", "model", "interface"])

# Tasks a robot is sent to do, each a predicate whose actor acts on a thing.
ROBOT_TASKS = [("carry", "battery"), ("lift", "stone"), ("push", "vehicle"),
               ("pull", "wheel"), ("throw", "stone"), ("catch", "battery"),
               ("drop", "stone"), ("grasp", "key"), ("turn", "wheel"), ("cut", "metal"),
               ("press", "door"), ("hit", "metal"), ("cover", "machine"), ("hide", "key")]
STEPS = [("design", "model"), ("make", "model"), ("test", "model"), ("improve", "model"),
         ("publish", "model"), ("arrange", "list"), ("produce", "document"),
         ("draw", "map"), ("search", "forest"), ("combine", "data")]
LACKS = [("lack tool", "the tool"), ("lack permission", "the permission"),
         ("lack resource", "the resources"), ("lack knowledge", "the knowledge")]


def delegating(p, n):
    """A task delegated to a robot, with a deadline, accepted and later reported."""
    verb = p([v for v, _ in ROBOT_TASKS])
    thing = dict(ROBOT_TASKS)[verb]
    p.note(thing)
    hours = 1 + n % 4
    x = Exchange()
    task = "(situation %s (ACTOR %%s) (UNDERGOER %s))" % (k(verb), term(thing, "DEFINITE"))
    given = x.send(1, [2], "(move ACT-DELEGATION SPEAKERS-OWN (deadline %d HOUR HENCE) %s)"
                   % (hours, task % party(2)))
    x.send(2, [1], "(move ACT-ACCEPTANCE SPEAKERS-OWN %s %s)" % (
        names(1, given, "assignment"), task % "(term SELF)"))
    # work done on an assignment is reported on behalf of the agent that assigned it
    done = task.replace("(situation %s" % k(verb), "(situation %s COMPLETED" % k(verb))
    x.send(2, [1], "(move ACT-COMPLETION-REPORT ON-BEHALF-OF-A-NAMED-PRINCIPAL (authority %s) "
           "%s (assertion OBSERVATION CERTAIN %s))" % (
               party(1), names(1, given, "assignment"), done % "(term SELF)"))
    return "agent 1 delegates to the robot, agent 2, the task to %s the %s within %s; " \
           "agent 2 accepts and reports it done" % (verb, thing, plural(hours, "hour")), \
        x.messages


def planning(p, n):
    """A plan of two steps in order, proposed to the team."""
    first = STEPS[n % len(STEPS)]
    second = STEPS[(n + 3) % len(STEPS)]
    p.note(*first, *second)
    x = Exchange()
    x.send(1, [2, 3], "(move ACT-PROPOSAL SPEAKERS-OWN (situation CONJUNCTION (CONTENT "
           "(situation #1 %s (ACTOR (term (party 2))) (UNDERGOER %s))) (CONTENT (situation "
           "%s (EXECUTION-TIME AFTER (@1 EXECUTION-TIME)) (ACTOR (term (party 3))) "
           "(UNDERGOER %s)))))" % (k(first[0]), term(first[1], "DEFINITE"), k(second[0]),
                                   term(second[1], "DEFINITE")))
    return "agent 1 proposes a plan: agent 2 is to %s the %s, and after that agent 3 is to " \
           "%s the %s" % (first[0], first[1], second[0], second[1]), x.messages


def hiring(p, n):
    """An agent hired for work and paid for it."""
    verb = p(["hire", "pay", "lend", "owe"])
    amount = 10 * (2 + n % 9)
    x = Exchange()
    money = "(term money (q EXACTLY %d))" % amount
    if verb == "hire":
        asked = x.send(1, [2], "(move ACT-PROPOSAL SPEAKERS-OWN (situation hire (ACTOR (term "
                       "SELF)) (UNDERGOER %s)))" % party(2))
        x.send(2, [1], "(move ACT-ACCEPTANCE SPEAKERS-OWN %s (situation hire (ACTOR %s) "
               "(UNDERGOER (term SELF))))" % (names(1, asked, "proposal"), party(1)))
        english = "agent 1 proposes to hire agent 2, which accepts"
    elif verb == "pay":
        x.send(1, [2], "(move ACT-PROMISE SPEAKERS-OWN (situation pay (ACTOR (term SELF)) "
               "(UNDERGOER %s) (RECIPIENT %s)))" % (money, party(2)))
        english = "agent 1 promises to pay agent 2 %d in money" % amount
    elif verb == "lend":
        x.send(1, [2], "(move ACT-OFFER SPEAKERS-OWN (situation lend (ACTOR (term SELF)) "
               "(UNDERGOER %s) (RECIPIENT %s)))" % (money, party(2)))
        english = "agent 1 offers to lend agent 2 %d in money" % amount
    else:
        x.send(1, [2], "(move ASSERTED-POSITION (assertion RETRIEVAL CERTAIN (situation owe "
               "(HOLDER %s) (UNDERGOER %s) (RECIPIENT (term SELF)))))" % (party(3), money))
        english = "agent 1 states from its records that agent 3 owes it %d in money" % amount
    return english, x.messages


def capability(p, n):
    """Whether an agent can do a task, and what it lacks if it cannot."""
    verb, thing = ROBOT_TASKS[(n * 5) % len(ROBOT_TASKS)]
    lack, english = LACKS[n % len(LACKS)]
    p.note(verb, thing, lack)
    x = Exchange()
    task = "(situation %s (ACTOR (term SELF)) (UNDERGOER %s))" % (k(verb), term(thing,
                                                                              "DEFINITE"))
    asked = x.send(1, [2], "(move ACT-QUESTION (situation capable POLAR (HOLDER (term "
                   "INTERLOCUTOR)) (CONTENT %s)))" % task.replace("(term SELF)",
                                                                  "(term INTERLOCUTOR)"))
    x.send(2, [1], "(move ACT-ANSWER %s (assertion INTROSPECTION CERTAIN (situation capable "
           "POLARITY.NEGATIVE (HOLDER (term SELF)) (CONTENT %s)))) (move ASSERTED-POSITION "
           "(assertion INTROSPECTION CERTAIN (situation %s (HOLDER (term SELF)) (CONTENT "
           "%s))))" % (names(1, asked, "question"), task, k(lack), task))
    return "agent 1 asks whether agent 2 can %s the %s; agent 2 answers that it cannot, " \
           "for it lacks %s" % (verb, thing, english), x.messages


def priority(p, n):
    """Which of two tasks comes first, and how the first stands."""
    first, second = STEPS[(n * 3) % len(STEPS)], STEPS[(n * 3 + 1) % len(STEPS)]
    p.note(*first, *second)
    state = p(["urgent", "important", "difficult", "easy"])
    x = Exchange()
    task = "(situation %s (ACTOR (term (party 2))) (UNDERGOER %s))"
    x.send(1, [2], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
           "PREFERENCE (HOLDER (term SELF)) (CONTENT (situation CONJUNCTION (CONTENT "
           "(situation #1 %s (ACTOR (term (party 2))) (UNDERGOER %s))) (CONTENT (situation "
           "%s (EXECUTION-TIME AFTER (@1 EXECUTION-TIME)) (ACTOR (term (party 2))) "
           "(UNDERGOER %s))))))))" % (k(first[0]), term(first[1], "DEFINITE"), k(second[0]),
                           term(second[1], "DEFINITE")),
           "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE (situation %s (UNDERGOER "
           "%s))))" % (state if state != "important" else "urgent",
                       task % (k(first[0]), term(first[1], "DEFINITE"))))
    return "agent 1 prefers that agent 2 %s the %s before it %ss the %s, and holds the " \
           "first task %s" % (first[0], first[1], second[0], second[1],
                              state if state != "important" else "urgent"), x.messages


def commanding(p, n):
    """A command given under authority, and a commitment withdrawn in whole or in part."""
    kind = p(["command", "promise", "withdrawal", "partial withdrawal"])
    verb, thing = STEPS[(n * 7) % len(STEPS)]
    p.note(verb, thing)
    x = Exchange()
    if kind == "command":
        task = "(situation %s (ACTOR %s) (UNDERGOER %s))" % (k(verb), party(2), term(
            thing, "DEFINITE"))
        x.send(1, [2], "(move ACT-COMMAND IN-A-NAMED-ROLE (authority (term team DEFINITE)) "
               "%s)" % task)
        return "agent 1, in its role for the team, commands agent 2 to %s the %s" % (
            verb, thing), x.messages
    task = "(situation %s (ACTOR (term SELF)) (UNDERGOER %s))" % (k(verb), term(thing,
                                                                              "DEFINITE"))
    other = "(situation store (ACTOR (term SELF)) (UNDERGOER %s))" % term(thing, "DEFINITE")
    if kind == "promise":
        x.send(1, [2], "(move ACT-PROMISE SPEAKERS-OWN %s)" % task)
        return "agent 1 promises agent 2 to %s the %s" % (verb, thing), x.messages
    if kind == "withdrawal":
        promised = x.send(1, [2], "(move ACT-PROMISE SPEAKERS-OWN %s)" % task)
        x.send(1, [2], "(move ACT-WITHDRAWAL SPEAKERS-OWN %s %s)" % (
            names(1, promised, "commitment"), task))
        return "agent 1 promises to %s the %s and later withdraws the promise" % (
            verb, thing), x.messages
    promised = x.send(1, [2], "(move ACT-PROMISE SPEAKERS-OWN (situation CONJUNCTION "
                      "(CONTENT %s) (CONTENT %s)))" % (task, other.replace(
                          "(situation store", "(situation #1 store")))
    x.send(1, [2], "(move ACT-PARTIAL-WITHDRAWAL SPEAKERS-OWN %s %s)" % (
        names(1, promised, "commitment")[:-1] + " part 1)", other))
    return "agent 1 promises to %s the %s and to store it, and later withdraws the second " \
           "part" % (verb, thing), x.messages


# The senses of work: each root read in its conventional sense by the frame it stands in.
DEMANDS = [
    ("pressure", "the urgency that the network be repaired",
     "(term pressure DEFINITE (CONTENT (situation repair (UNDERGOER (term network "
     "DEFINITE)))))"),
    ("weight", "the workload of the translation of the text",
     "(term weight DEFINITE (CONTENT (situation translate (ACTOR (term SELF)) (UNDERGOER "
     "(term text DEFINITE)))))"),
    ("mountain", "the obstacle before the robot's repair of the bridge",
     "(term mountain DEFINITE (CONTENT (situation repair (ACTOR (term robot DEFINITE)) "
     "(UNDERGOER (term bridge DEFINITE)))))"),
]


def demanding(row):
    """How demanding a task is: the senses urgency, workload, obstacle and demanding."""
    root, english, unit = row
    x = Exchange()
    x.send(2, [1], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
           "heavy (UNDERGOER (situation design (ACTOR (term SELF)) (UNDERGOER (term model "
           "DEFINITE)))))))", "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE "
                              "(situation increase PERFECTIVE (UNDERGOER %s))))" % unit)
    return "agent 2 says that designing the model is demanding, and that %s has grown" % (
        english), x.messages


SCHEMAS = [delegating, planning, hiring, capability, priority, commanding]
# each sense of work said once
FIXED = [demanding(row) for row in DEMANDS]

# Exchanges written by hand for idiom range in delegation.
AUTHORED = [
    ("agent 1 delegates a translation to agent 2 with a deadline; agent 2 accepts, and "
     "when asked how it goes, answers that the work is between its hands",
     Exchange.scripted(
         (1, [2], "(move ACT-DELEGATION SPEAKERS-OWN (deadline 2 HOUR HENCE) (situation "
                  "translate (ACTOR (term (party 2))) (UNDERGOER (term document DEFINITE)) "
                  "(CONTENT (term language INDEFINITE))))"),
         (2, [1], "(move ACT-ACCEPTANCE SPEAKERS-OWN (names 1 1 NORMATIVE-ENTRY ASSIGNMENT "
                  "EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE) (situation translate (ACTOR (term "
                  "SELF)) (UNDERGOER (term document DEFINITE)) (CONTENT (term language "
                  "INDEFINITE))))"),
         (1, [2], "(move ACT-QUESTION (situation progress POLAR (UNDERGOER (situation "
                  "translate (ACTOR (term (party 2))) (UNDERGOER (term document "
                  "DEFINITE))))))"),
         (2, [1], "(move ACT-ANSWER (names 1 2 ISSUE QUESTION OPEN) (assertion "
                  "INTROSPECTION CERTAIN (situation IDIOM-ENTRY between (UNDERGOER (term "
                  "(names 1 1 NORMATIVE-ENTRY ASSIGNMENT "
                  "EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE))) (CONTENT (term hand)))))"))),
    ("agent 1 asks the robot to lift the machine; the robot declines, lacking the "
     "resources, and offers to push it instead",
     Exchange.scripted(
         (1, [2], "(move ACT-REQUEST SPEAKERS-OWN (situation lift (ACTOR (term (party 2))) "
                  "(UNDERGOER (term machine DEFINITE))))"),
         (2, [1], "(move ACT-REJECTION SPEAKERS-OWN (names 1 1 ISSUE REQUEST OPEN) "
                  "(situation lift (ACTOR (term SELF)) (UNDERGOER (term machine DEFINITE))))",
          "(move ACT-OFFER SPEAKERS-OWN (situation push (ACTOR (term SELF)) (UNDERGOER "
          "(term machine DEFINITE))))"))),
    ("agent 1 proposes to pay agent 2 fifty if agent 2 repairs the bridge, and agent 2 accepts",
     Exchange.scripted(
         (1, [2], "(move ACT-PROPOSAL SPEAKERS-OWN (situation pay (ACTOR (term SELF)) "
                  "(UNDERGOER (term money (q EXACTLY 50))) (RECIPIENT (term (party 2))) "
                  "(CONDITION (situation repair COMPLETED (ACTOR (term (party 2))) "
                  "(UNDERGOER (term bridge DEFINITE))))))"),
         (2, [1], "(move ACT-ACCEPTANCE SPEAKERS-OWN (names 1 1 ISSUE PROPOSAL OPEN) "
                  "(situation pay (ACTOR (term (party 1))) (UNDERGOER (term money (q "
                  "EXACTLY 50))) (RECIPIENT (term SELF)) (CONDITION (situation repair "
                  "COMPLETED (ACTOR (term SELF)) (UNDERGOER (term bridge DEFINITE))))))"))),
]
