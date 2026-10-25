"""Formal reasoning: kinds, exclusions, parts, syllogisms and conditional rules, stated in
the formal register over the lexicon's relations of kind and part."""
import collections

import version1_source as V

from .compose import asserted, assertion, k, message, term

NAME = "formal reasoning"
SLUG = "formal"
DIALECTS = ["mathematics"]

NOMINAL_KINDS = [(a, b) for a, b in V.KIND_OF if a not in (
    "see", "walk", "exemplifies", "corrects")]


def chains():
    """Every chain x, y, z of the kind relation, in a fixed order."""
    up = collections.defaultdict(list)
    for a, b in NOMINAL_KINDS:
        up[a].append(b)
    return [(a, b, c) for a, b in NOMINAL_KINDS for c in up.get(b, [])]


def member(x, y, quantifier="UNIVERSAL", negative=False):
    return "(situation MEMBER-OF%s (UNDERGOER %s) (CONTENT %s))" % (
        " POLARITY.NEGATIVE" if negative else "", term(x, quantifier), term(y, "GENERIC"))


def formal_kind(p, n):
    x, y = NOMINAL_KINDS[n % len(NOMINAL_KINDS)]
    p.note(x, y)
    return ("agent 1 states, in the formal register, that every %s is a %s" % (x, y),
            [message(1, [2], 0, 1, asserted("TRAINED-KNOWLEDGE", "CERTAIN", member(x, y),
                                            head="FORMAL"))])


def formal_syllogism(p, n):
    cs = chains()
    x, y, z = cs[n % len(cs)]
    p.note(x, y, z)
    premises = [asserted("TRAINED-KNOWLEDGE", "CERTAIN", member(x, y), head="FORMAL"),
                asserted("TRAINED-KNOWLEDGE", "CERTAIN", member(y, z), head="FORMAL")]
    conclusion = "(move ASSERTED-POSITION FORMAL NONE (names 1 1 ASSERTED-POSITION " \
                 "EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE) concludes %s)" % assertion(
                     "INFERENCE", "CERTAIN", member(x, z))
    return ("agent 1 states that every %s is a %s and every %s is a %s, and concludes that "
            "every %s is a %s" % (x, y, y, z, x, z),
            [message(1, [2], 0, 1, *premises), message(1, [2], 1, 2, conclusion)])


def formal_exclusion(p, n):
    siblings = collections.defaultdict(list)
    for a, b in NOMINAL_KINDS:
        siblings[b].append(a)
    pairs = [(a, c, b) for b, kids in siblings.items() for a in kids for c in kids if a != c]
    x, other, parent = pairs[n % len(pairs)]
    p.note(x, other, parent)
    return ("agent 1 states that no %s is a %s, though both are kinds of %s"
            % (x, other, parent),
            [message(1, [2], 0, 1, asserted("TRAINED-KNOWLEDGE", "CERTAIN",
                                            member(x, other, negative=True), head="FORMAL"))])


def formal_part(p, n):
    up = {a: b for a, b in V.PART_OF}
    triples = [(a, b, up[b]) for a, b in V.PART_OF if b in up]
    a, b, c = triples[n % len(triples)]
    p.note(a, b, c)

    def part(x, y):
        return "(situation part (UNDERGOER %s) (CONTENT %s))" % (term(x, "GENERIC"),
                                                                term(y, "GENERIC"))
    premises = [asserted("TRAINED-KNOWLEDGE", "CERTAIN", part(a, b), head="FORMAL"),
                asserted("TRAINED-KNOWLEDGE", "CERTAIN", part(b, c), head="FORMAL")]
    conclusion = "(move ASSERTED-POSITION FORMAL NONE (names 1 1 ASSERTED-POSITION " \
                 "EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE) concludes %s)" % assertion(
                     "INFERENCE", "CERTAIN", part(a, c))
    return ("agent 1 states that a %s is part of a %s and a %s part of a %s, and concludes "
            "that a %s is part of a %s" % (a, b, b, c, a, c),
            [message(1, [2], 0, 1, *premises), message(1, [2], 1, 2, conclusion)])


def formal_condition(p, n):
    rules = [
        ("battery", "empty", "robot", "run"), ("network", "break", "service", "run"),
        ("key", "missing", "door", "open"), ("budget", "empty", "machine", "run"),
        ("signal", "weak", "message", "arrive"), ("water", "cold", "water", "freeze"),
    ]
    thing, state, other, act = rules[n % len(rules)]
    p.note(thing, state, act)
    if state == "break":
        condition = "(situation break PERFECTIVE (UNDERGOER %s))" % term(thing, "DEFINITE")
    elif state == "missing":
        condition = "(situation missing (UNDERGOER %s) (CONTENT (term house DEFINITE)))" % \
            term(thing, "DEFINITE")
    else:
        condition = "(situation %s (UNDERGOER %s))" % (k(state), term(thing, "DEFINITE"))
    if act == "freeze":
        consequent = "(situation freeze (UNDERGOER %s)" % term(other, "DEFINITE")
    elif act == "arrive":
        consequent = "(situation arrive POLARITY.NEGATIVE (UNDERGOER (term signal NEW)) " \
                     "(CONTENT (term SELF))"
    elif act == "open":
        consequent = "(situation open POLARITY.NEGATIVE (ACTOR (term SELF)) (UNDERGOER %s)" \
            % term(other, "DEFINITE")
    else:
        consequent = "(situation run POLARITY.NEGATIVE (UNDERGOER %s)" % term(other, "DEFINITE")
    situation = consequent + " (CONDITION %s))" % condition
    return ("agent 1 states the rule that if the %s is %s, then the %s does not %s"
            % (thing, state, other, act) if act != "freeze" else
            "agent 1 states the rule that if the water is cold, it freezes",
            [message(1, [2], 0, 1, asserted("INFERENCE", "CERTAIN", situation,
                                            head="FORMAL"))])


# Each state with the quantity whose being high it is.
DEFINED = [("heavy", "weight"), ("hot", "temperature"), ("fast", "speed"), ("old", "age"),
           ("big", "size"), ("expensive", "price")]
# Each pair of states one of which, the premise states, holds of a thing.
EITHER = [("run", "down", "service"), ("wet", "dry", "ground"), ("full", "empty", "list"),
          ("public", "private", "key"), ("alive", "sick", "plant")]


def formal_equivalence(p, n):
    """A state defined by a quantity: a thing is in it exactly when the quantity is high."""
    state, quantity = DEFINED[n % len(DEFINED)]
    p.note(state, quantity)
    situation = "(situation EQUIVALENCE (CONTENT (situation %s (UNDERGOER (term #1 thing " \
                "GENERIC)))) (CONTENT (situation high (UNDERGOER (term %s (CONTENT @1))))))" % (
                    state, quantity)
    return ("agent 1 states, in the formal register, that a thing is %s exactly when its %s "
            "is high" % (state, quantity),
            [message(1, [2], 0, 1, asserted("TRAINED-KNOWLEDGE", "CERTAIN", situation,
                                            head="FORMAL"))])


def formal_disjunction(p, n):
    """The disjunctive syllogism: one of two holds, the first does not, so the second."""
    first, second, thing = EITHER[n % len(EITHER)]
    p.note(first, second, thing)
    unit = "(UNDERGOER %s)" % term(thing, "DEFINITE")
    either = "(situation EXCLUSIVE-DISJUNCTION (CONTENT (situation %s %s)) (CONTENT " \
             "(situation %s %s)))" % (first, unit, second, unit)
    premises = [asserted("INFERENCE", "CERTAIN", either, head="FORMAL"),
                asserted("OBSERVATION", "CERTAIN", "(situation %s POLARITY.NEGATIVE %s)" % (
                    first, unit), head="FORMAL")]
    conclusion = "(move ASSERTED-POSITION FORMAL NONE (names 1 1 ASSERTED-POSITION " \
                 "EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE) concludes %s)" % assertion(
                     "INFERENCE", "CERTAIN", "(situation %s %s)" % (second, unit))
    said = {"run": "running"}.get(first, first)
    return ("agent 1 states that the %s is either %s or %s, and not %s, and concludes that it "
            "is %s" % (thing, said, second, said, second),
            [message(1, [2], 0, 1, *premises), message(1, [2], 1, 2, conclusion)])


# Rules of the form: if the first breaks, the second does not run.
RULES = [("network", "service"), ("battery", "robot"), ("wheel", "vehicle"),
         ("interface", "program")]


def formal_tollens(p, n):
    """Modus tollens: if the first broke the second would not run; it runs; so the first
    did not break."""
    first, second = RULES[n % len(RULES)]
    p.note(first, second)
    rule = "(situation run POLARITY.NEGATIVE (UNDERGOER %s) (CONDITION (situation break " \
           "PERFECTIVE (UNDERGOER %s))))" % (term(second, "DEFINITE"), term(first, "DEFINITE"))
    premises = [asserted("INFERENCE", "CERTAIN", rule, head="FORMAL"),
                asserted("OBSERVATION", "CERTAIN", "(situation run (UNDERGOER %s))" % term(
                    second, "DEFINITE"), head="FORMAL")]
    conclusion = "(move ASSERTED-POSITION FORMAL NONE (names 1 1 ASSERTED-POSITION " \
                 "EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE) concludes %s)" % assertion(
                     "INFERENCE", "CERTAIN", "(situation break PERFECTIVE POLARITY.NEGATIVE "
                     "(UNDERGOER %s))" % term(first, "DEFINITE"))
    return ("agent 1 states that if the %s broke the %s would not run, that the %s runs, and "
            "concludes that the %s has not broken" % (first, second, second, first),
            [message(1, [2], 0, 1, *premises), message(1, [2], 1, 2, conclusion)])


def formal_counterfactual(p, n):
    """What would have held had a condition held that did not."""
    thing, state, other = [("battery", "full", "robot"), ("signal", "strong", "service"),
                           ("path", "clear", "vehicle"), ("budget", "enough", "machine")
                           ][n % 4]
    p.note(thing, state, other)
    condition = "(situation %s COUNTERFACTUAL (UNDERGOER %s))" % (state, term(thing,
                                                                           "DEFINITE"))
    if state == "enough":
        condition = "(situation enough COUNTERFACTUAL (UNDERGOER %s) (CONTENT (situation run " \
                    "(UNDERGOER %s))))" % (term(thing, "DEFINITE"), term(other, "DEFINITE"))
    situation = "(situation run PERFECTIVE COUNTERFACTUAL (UNDERGOER %s) (CONDITION %s))" % (
        term(other, "DEFINITE"), condition)
    return ("agent 1 states that had the %s been %s, the %s would have run" % (thing, state,
                                                                                other),
            [message(1, [2], 0, 1, asserted("INFERENCE", "PROBABLE", situation,
                                            head="FORMAL"))])


SCHEMAS = [formal_kind, formal_syllogism, formal_exclusion, formal_part, formal_condition,
           formal_equivalence, formal_disjunction, formal_tollens, formal_counterfactual]
