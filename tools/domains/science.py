"""Scientific communication: measurements in units, the regularities of the physical
world, hypotheses and the evidence that bears on them."""
from .compose import Exchange, asserted, k, message, plural, term

NAME = "scientific communication"
SLUG = "science"
DIALECTS = ["science", "machine-learning"]

# Each quantity, the units that measure it and the things it is measured of.
QUANTITIES = [
    ("temperature", ["kelvin", "degree celsius"], ["water", "metal", "air", "gas"],
     [293, 310, 77, 373]),
    ("pressure", ["pascal", "atmosphere"], ["gas", "air", "water"], [101325, 2, 5]),
    ("force", ["newton"], ["wind", "wave", "arm"], [12, 40, 250]),
    ("energy", ["joule"], ["heat", "light", "battery"], [500, 1200, 36]),
    ("electricity", ["volt", "ampere", "watt"], ["battery", "machine", "robot"],
     [12, 3, 60]),
    ("sound", ["hertz"], ["voice", "music", "signal"], [440, 220, 1000]),
    ("amount", ["litre"], ["water", "liquid", "blood"], [2, 5, 1]),
    ("size", ["byte", "bit"], ["file", "data", "memory", "document"], [4096, 512, 64]),
    ("amount", ["mole"], ["gas", "substance", "atom"], [3, 1, 2]),
    ("distance", ["metre"], ["path", "river", "bridge", "mountain"], [120, 900, 40]),
    ("weight", ["gram"], ["stone", "metal", "seed", "insect"], [250, 30, 2]),
    ("amount", ["percent"], ["energy", "data", "budget", "resource"], [40, 85, 12]),
]
# Regularities of the physical world, each a cause and what it brings about.
LAWS = [
    ("gravity", "(situation fall HABITUAL (UNDERGOER (term stone GENERIC)))",
     "stones fall"),
    ("heat", "(situation increase HABITUAL (UNDERGOER (term temperature GENERIC)))",
     "temperature rises"),
    ("wind", "(situation move HABITUAL (UNDERGOER (term cloud GENERIC)) (CONTENT (term sky "
     "GENERIC)))", "clouds move across the sky"),
    ("sun", "(situation grow HABITUAL (UNDERGOER (term plant GENERIC)))", "plants grow"),
    ("cold", "(situation freeze HABITUAL (UNDERGOER (term water GENERIC)))",
     "water freezes"),
    ("rain", "(situation flow HABITUAL (UNDERGOER (term river GENERIC)) (CONTENT (term sea "
     "GENERIC)))", "rivers flow to the sea"),
    ("electricity", "(situation run HABITUAL (UNDERGOER (term machine GENERIC)))",
     "machines run"),
    ("light", "(situation grow HABITUAL (UNDERGOER (term leaf GENERIC)))", "leaves grow"),
    ("force", "(situation move HABITUAL (UNDERGOER (term body GENERIC)) (CONTENT (term "
     "space GENERIC)))", "bodies move through space"),
    ("fire", "(situation burn HABITUAL (UNDERGOER (term forest GENERIC)))", "forests burn"),
]


def science_measurement(p, n):
    quantity, units, things, numbers = QUANTITIES[n % len(QUANTITIES)]
    unit = p(units)
    thing = p(things)
    number = numbers[(n // len(QUANTITIES)) % len(numbers)]
    p.note(quantity)
    measured = term(quantity, "(q EXACTLY %d %s)" % (number, k(unit)))
    first = asserted("OBSERVATION", "CERTAIN", "(situation measure PERFECTIVE (ACTOR "
                     "(term SELF)) (UNDERGOER %s))" % measured)
    second = asserted("OBSERVATION", "CERTAIN", "(situation part (UNDERGOER %s) "
                      "(CONTENT %s))" % (term(quantity, "DEFINITE"), term(thing, "DEFINITE")))
    return ("agent 1 reports that it measured the %s of the %s as %d %s"
            % (quantity, thing, number, unit),
            [message(1, [2], 0, 1, first, second)])


def science_law(p, n):
    cause, effect, gloss = LAWS[n % len(LAWS)]
    p.note(cause)
    situation = "(situation cause (ACTOR %s) (CONTENT %s))" % (term(cause, "GENERIC"), effect)
    return ("agent 1 states from its training that %s causes the regularity that %s"
            % (cause, gloss),
            [message(1, [2], 0, 1, asserted("TRAINED-KNOWLEDGE", "CERTAIN", situation))])


def science_hypothesis(p, n):
    cause, effect, gloss = LAWS[(n + 3) % len(LAWS)]
    p.note(cause)
    method = p(["experiment", "model", "theory"])
    suppose = "(move SUPPOSITION (situation cause (ACTOR %s) (CONTENT %s)))" % (
        term(cause, "GENERIC"), effect)
    test = "(move ACT-PROPOSAL SPEAKERS-OWN (situation test (ACTOR (term INCLUSIVE-COLLECTIVE " \
           "READING-OF-A-COLLECTIVE.JOINT)) (UNDERGOER %s)))" % term(method, "NEW")
    return ("agent 1 supposes that %s causes the regularity that %s and proposes %s %s to "
            "test it" % (cause, gloss, "an" if method[0] in "aeiou" else "a", method),
            [message(1, [2], 0, 1, suppose, test)])


def science_evidence(p, n):
    cause, effect, gloss = LAWS[(n + 5) % len(LAWS)]
    p.note(cause)
    stance = p(["support", "undermine"])
    source = p(["experiment", "evidence", "theory"])
    situation = "(situation %s (ACTOR %s) (CONTENT (situation cause (ACTOR %s) (CONTENT %s))) " \
                "(HOLDER (term SELF)))" % (stance, term(source, "DEFINITE"),
                                           term(cause, "GENERIC"), effect)
    return ("agent 1 reports that the %s %ss the claim that %s causes the regularity that %s"
            % (source, stance, cause, gloss),
            [message(1, [2], 0, 1, asserted("INFERENCE", "PROBABLE", situation))])


# What a model predicts: the quantity, its unit, the thing it is of, and its values.
PREDICTIONS = [("temperature", "kelvin", "water", [350, 280, 300]),
               ("pressure", "pascal", "gas", [120000, 90000]),
               ("electricity", "volt", "battery", [11, 9]),
               ("distance", "metre", "vehicle", [400, 1200]),
               ("amount", "litre", "liquid", [3, 8])]
# Events that recur, at a rate, and what recurs.
RATES = [("arrive", "signal", "(CONTENT (term SELF))", "signals reach it", "MINUTE"),
         ("fall", "rain", "", "drops of rain fall", "SECOND"),
         ("break", "wave", "", "waves break", "MINUTE"),
         ("appear", "star", "", "stars appear", "HOUR"),
         ("fly", "bird", "", "birds fly over", "HOUR")]
COMPARED = [("temperature", "gas", "liquid"), ("weight", "stone", "metal"),
            ("pressure", "air", "water"), ("speed", "vehicle", "robot"),
            ("size", "planet", "moon"), ("age", "tree", "forest")]


def science_prediction(p, n):
    """A value a model predicts for some hours hence."""
    quantity, unit, thing, values = PREDICTIONS[n % len(PREDICTIONS)]
    value = values[(n // len(PREDICTIONS)) % len(values)]
    hours = 1 + n % 6
    p.note(quantity, unit, thing)
    x = Exchange()
    x.send(1, [2], asserted("SIMULATION", "PROBABLE", "(situation MEMBER-OF (EVENT-TIME %d "
                            "HOUR HENCE) (UNDERGOER (term %s DEFINITE (CONTENT %s))) (CONTENT "
                            "(term %s (q APPROXIMATELY %d %s))))" % (
                                hours, quantity, term(thing, "DEFINITE"), quantity, value,
                                k(unit))))
    return "agent 1 predicts from its model that in %s the %s of the %s will be about %d " \
           "%s" % (plural(hours, "hour"), quantity, thing, value, unit), x.messages


def science_rate(p, n):
    """How often an event recurs, counted over a time."""
    verb, thing, content, english, unit = RATES[n % len(RATES)]
    rate = 3 + (n * 7) % 40
    p.note(verb, thing)
    x = Exchange()
    x.send(1, [2], asserted("OBSERVATION", "CERTAIN", "(situation %s ITERATIVE (EVENT-TIME "
                            "%d PER %s) (UNDERGOER (term %s GENERIC))%s)" % (
                                verb, rate, unit, thing, " " + content if content else "")))
    return "agent 1 observes that %s at %d a %s" % (english, rate, unit.lower()), x.messages


def science_comparison(p, n):
    """Two quantities measured and compared, and which is higher."""
    quantity, first, second = COMPARED[n % len(COMPARED)]
    p.note(quantity, first, second)
    x = Exchange()
    of = "(term %s DEFINITE (CONTENT %s))"
    x.send(1, [2], asserted("OBSERVATION", "CERTAIN", "(situation compare PERFECTIVE (ACTOR "
                            "(term SELF)) (UNDERGOER %s) (CONTENT %s))" % (
                                of % (quantity, term(first, "DEFINITE")),
                                of % (quantity, term(second, "DEFINITE")))),
           asserted("INFERENCE", "CERTAIN", "(situation high (UNDERGOER %s))" % (
               of % (quantity, term(first, "DEFINITE")))))
    return "agent 1 reports that it compared the %s of the %s with that of the %s, and that " \
           "the first is high" % (quantity, first, second), x.messages


SCHEMAS = [science_measurement, science_law, science_hypothesis, science_evidence,
           science_prediction, science_rate, science_comparison]


def measured(quantity, thing, english, basis="OBSERVATION"):
    """A quantity measured of a thing, stated in its unit."""
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION (assertion %s CERTAIN (situation measure "
           "PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (term %s (CONTENT %s))))))" % (
               basis, quantity, term(thing, "DEFINITE")))
    return "agent 1 reports that it measured %s" % english, x.messages


def known(situation, english):
    x = Exchange()
    x.send(1, [2], asserted("TRAINED-KNOWLEDGE", "CERTAIN", situation))
    return "agent 1 states from its training that %s" % english, x.messages


# Every unit of measure with a quantity it measures, a thing it is measured of and a
# value, each said once.
UNITS = [("temperature", "degree celsius", "air", 21), ("temperature", "kelvin", "gas", 77),
         ("pressure", "pascal", "gas", 101325), ("pressure", "atmosphere", "water", 3),
         ("size", "byte", "file", 4096), ("size", "bit", "signal", 64),
         ("distance", "metre", "bridge", 40), ("weight", "gram", "seed", 2),
         ("amount", "percent", "budget", 35), ("force", "newton", "wind", 120),
         ("energy", "joule", "battery", 500), ("electricity", "volt", "battery", 12),
         ("electricity", "ampere", "machine", 3), ("electricity", "watt", "robot", 90),
         ("sound", "hertz", "voice", 220), ("amount", "litre", "liquid", 5),
         ("amount", "mole", "substance", 2)]

# Quantities and facts of the body and of matter, each said once, and one measurement in
# every unit.
FIXED = [measured("%s (q EXACTLY %d %s)" % (quantity, value, k(unit)), thing,
                  "the %s of the %s as %d %s" % (quantity, thing, value, unit))
         for quantity, unit, thing, value in UNITS] + [
    known("(situation MEMBER-OF (UNDERGOER (term metal GENERIC)) (CONTENT (term solid "
          "GENERIC)))", "a metal is a solid"),
    measured("speed (q EXACTLY 12 metre PER SECOND)", "vehicle",
             "the speed of the vehicle as 12 metres a second"),
    measured("age (q EXACTLY 400 YEAR)", "tree", "the age of the tree as 400 years"),
    known("(situation alive HABITUAL (UNDERGOER (term cell GENERIC)))", "cells live"),
    known("(situation cause HABITUAL (ACTOR (term heart GENERIC)) (CONTENT (situation flow "
          "HABITUAL (UNDERGOER (term blood GENERIC)) (CONTENT (term body GENERIC)))))",
          "the heart makes blood flow through the body"),
    known("(situation part (UNDERGOER (term atom GENERIC)) (CONTENT (term matter GENERIC)))",
          "atoms are part of matter"),
]
