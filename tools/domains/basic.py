"""Basic communication: properties, places, facts, questions and requests about the
physical world and the things agents handle."""
import version1_source as V

from .compose import Exchange, asserted, assertion, k, message, term

NAME = "basic communication"
SLUG = "basic"

TOPIC = dict(
    tasks=[("open", "door"), ("shut", "door"), ("repair", "wheel"), ("read", "document"),
           ("copy", "map"), ("find", "key"), ("examine", "map"), ("write", "text"),
           ("store", "file"), ("take", "battery")],
    contents=[
        ("(situation heavy (UNDERGOER (term stone DEFINITE)))", "the stone is heavy"),
        ("(situation open (UNDERGOER (term door DEFINITE)))", "the door is open"),
        ("(situation full (UNDERGOER (term battery DEFINITE)))", "the battery is full"),
        ("(situation locate (UNDERGOER (term key DEFINITE)) (CONTENT (term house "
         "DEFINITE)))", "the key is in the house"),
    ],
    things=["key", "map", "battery", "document", "file"])

# Properties and the things each is sensibly said of; colours have a schema of their own.
PROPERTIES = {
    "heavy": ["stone", "metal", "machine", "battery", "vehicle"],
    "hot": ["water", "metal", "fire", "sun", "stone"],
    "cold": ["water", "air", "metal", "ground"],
    "wet": ["ground", "stone", "hand", "leaf"],
    "dry": ["ground", "leaf", "seed", "air"],
    "clean": ["water", "room", "hand"],
    "dirty": ["water", "room", "hand", "wheel"],
    "hard": ["stone", "metal", "ground"],
    "soft": ["ground", "leaf", "food"],
    "smooth": ["stone", "surface", "metal"],
    "sharp": ["edge", "stone", "metal"],
    "flat": ["ground", "land", "surface"],
    "round": ["wheel", "stone", "sun", "moon"],
    "straight": ["line", "path", "edge"],
    "big": ["mountain", "city", "machine", "tree", "room"],
    "small": ["insect", "seed", "cell", "atom", "room"],
    "long": ["river", "path", "line", "text", "list"],
    "short": ["path", "line", "text", "list"],
    "wide": ["river", "path", "room", "door"],
    "deep": ["sea", "river", "hole"],
    "full": ["room", "list", "battery"],
    "empty": ["room", "list", "house", "battery"],
    "bright": ["sun", "star", "light", "image"],
    "dark": ["night", "room", "sky", "forest"],
    "loud": ["storm", "sound", "voice", "machine"],
    "quiet": ["room", "forest", "machine"],
    "old": ["tree", "house", "map", "document", "machine"],
    "young": ["tree", "dog", "child", "plant"],
    "fast": ["vehicle", "bird", "wind", "river"],
    "slow": ["vehicle", "river", "machine"],
    "strong": ["wind", "robot", "arm", "metal"],
    "weak": ["signal", "battery", "wind"],
    "calm": ["sea", "wind", "river"],
    "safe": ["house", "path", "data"],
    "beautiful": ["flower", "image", "sky", "music"],
}
# Spatial relations, each with the pairs of a thing and its landmark it is said of.
PLACES = {
    "above": [("bird", "tree"), ("sun", "mountain"), ("cloud", "city")],
    "below": [("fish", "surface"), ("room", "ground"), ("river", "bridge")],
    "behind": [("house", "tree"), ("robot", "door"), ("moon", "cloud")],
    "in front": [("vehicle", "house"), ("dog", "door"), ("tree", "house")],
    "beside": [("dog", "child"), ("river", "path"), ("battery", "machine")],
    "inside": [("key", "house"), ("data", "file"), ("cell", "body"), ("robot", "room")],
    "outside": [("dog", "house"), ("vehicle", "city"), ("robot", "room")],
    "near": [("city", "sea"), ("tree", "river"), ("house", "forest")],
    "far": [("star", "world"), ("mountain", "city"), ("sea", "land")],
    "left": [("door", "machine"), ("path", "river")],
    "right": [("vehicle", "path"), ("house", "bridge")],
}


def basic_property(p, n):
    """Up to three properties agent 1 observes of one thing."""
    props = [p(list(PROPERTIES))]
    thing = p(PROPERTIES[props[0]])
    for _ in range(2):
        others = [q for q in PROPERTIES if thing in PROPERTIES[q] and q not in props]
        if others:
            props.append(p(others))
    unit = "(UNDERGOER %s)" % term(thing, "DEFINITE")
    moves = [asserted("OBSERVATION", "CERTAIN", "(situation %s %s)" % (k(q), unit))
             for q in props]
    named = props[0] if len(props) == 1 else ", ".join(props[:-1]) + " and " + props[-1]
    return ("agent 1 tells agent 2 what it observes of the %s: %s" % (thing, named),
            [message(1, [2], 0, 1, *moves)])


def basic_question(p, n):
    prop = p(list(PROPERTIES))
    thing = p(PROPERTIES[prop])
    negative = n % 3 == 0
    unit = "(UNDERGOER %s)" % term(thing, "DEFINITE")
    question = "(move ACT-QUESTION (situation %s POLAR %s))" % (k(prop), unit)
    answer = "(move ACT-ANSWER (names 1 1 ISSUE QUESTION OPEN) %s)" % assertion(
        "OBSERVATION", "CERTAIN", "(situation %s%s %s)" % (
            k(prop), " POLARITY.NEGATIVE" if negative else "", unit))
    return ("agent 1 asks agent 2 whether the %s is %s, and agent 2 answers that it %s"
            % (thing, prop, "is not" if negative else "is"),
            [message(1, [2], 0, 1, question), message(2, [1], 1, 1, answer)])


def basic_place(p, n):
    """Where two things are, each by its relation to a landmark."""
    out = []
    for _ in range(2):
        rel = p(list(PLACES))
        thing, landmark = PLACES[rel][n % len(PLACES[rel])]
        p.note(thing, landmark)
        out.append((rel, thing, landmark))
    moves = [asserted("OBSERVATION", "CERTAIN", "(situation %s (UNDERGOER %s) (CONTENT %s))"
                      % (k(rel), term(thing, "DEFINITE"), term(landmark, "DEFINITE")))
             for rel, thing, landmark in out]
    return ("agent 1 tells agent 2 where things are: %s" % "; ".join(
        "the %s is %s the %s" % (thing, rel, landmark) for rel, thing, landmark in out),
            [message(1, [2], 0, 1, *moves)])


def basic_fact(p, n):
    pairs = [(a, b) for a, b in V.PART_OF]
    whole_part = pairs[n % len(pairs)]
    p.note(*whole_part)
    part, whole = whole_part
    situation = "(situation part (UNDERGOER %s) (CONTENT %s))" % (term(part, "GENERIC"),
                                                                 term(whole, "GENERIC"))
    return ("agent 1 tells agent 2 that a %s is part of a %s, from its training"
            % (part, whole),
            [message(1, [2], 0, 1, asserted("TRAINED-KNOWLEDGE", "CERTAIN", situation))])


def basic_request(p, n):
    act = p(["open", "shut", "repair", "clean", "read", "copy", "move", "find"])
    thing = p({"open": ["door", "file", "document"], "shut": ["door", "file", "interface"],
               "repair": ["wheel", "machine", "door"], "clean": ["room", "wheel", "surface"],
               "read": ["document", "text", "list"], "copy": ["file", "map", "document"],
               "move": ["battery", "machine", "stone"], "find": ["key", "map", "battery"]}[act])
    if act == "clean":
        situation = "(situation clean INCEPTIVE (UNDERGOER %s))" % term(thing, "DEFINITE")
    elif act == "move":
        situation = "(situation move (UNDERGOER %s) (CONTENT %s))" % (
            term(thing, "DEFINITE"), term("room", "DEFINITE"))
    else:
        situation = "(situation %s (ACTOR (term INTERLOCUTOR)) (UNDERGOER %s))" % (
            k(act), term(thing, "DEFINITE"))
    request = "(move ACT-REQUEST SPEAKERS-OWN %s)" % situation
    accept = "(move ACT-UNDERTAKING SPEAKERS-OWN (names 1 1 ISSUE REQUEST OPEN) %s)" % (
        situation.replace("(term INTERLOCUTOR)", "(term SELF)"))
    return ("agent 1 asks agent 2 to %s the %s, and agent 2 undertakes to" % (act, thing),
            [message(1, [2], 0, 1, request), message(2, [1], 1, 1, accept)])


# Colours and the things each is said of.
COLOURS = {"white": ["cloud", "stone", "light"],
           "black": ["night", "stone", "metal"], "red": ["blood", "flower", "fire"],
           "green": ["leaf", "tree", "plant"], "yellow": ["sun", "flower"],
           "blue": ["sky", "sea"]}


def basic_colour(p, n):
    """The colour of a thing, asked and answered."""
    colour = p(list(COLOURS))
    thing = p(COLOURS[colour])
    x = Exchange()
    asked = x.send(1, [2], "(move ACT-QUESTION (situation MEMBER-OF CONSTITUENT (UNDERGOER "
                   "(term colour DEFINITE (CONTENT %s)))))" % term(thing, "DEFINITE"))
    x.send(2, [1], "(move ACT-ANSWER (names 1 %d ISSUE QUESTION OPEN) (assertion OBSERVATION "
           "CERTAIN (situation %s (UNDERGOER %s))))" % (asked, colour, term(thing, "DEFINITE")))
    return "agent 1 asks what colour the %s is, and agent 2 answers that it is %s" % (
        thing, colour), x.messages


# The parts of a thing a place is stated by.
SIDES = ["top", "bottom", "end", "side", "centre", "edge"]


def basic_part_of_place(p, n):
    """Where a thing is, by the part of another it is at."""
    side = p(SIDES)
    thing, whole = [("key", "house"), ("bird", "tree"), ("robot", "path"), ("dog", "room"),
                    ("vehicle", "bridge"), ("star", "sky")][n % 6]
    p.note(thing, whole)
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation locate "
           "(UNDERGOER %s) (CONTENT (term %s DEFINITE (CONTENT %s))))))" % (
               term(thing, "DEFINITE"), side, term(whole, "DEFINITE")))
    return "agent 1 says that the %s is at the %s of the %s" % (thing, side, whole), \
        x.messages


def basic_direction(p, n):
    """The direction of the wind or of a moving thing, and its turn."""
    mover = p(["wind", "river", "vehicle", "robot"])
    side = p(["north", "south", "east", "west"])
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation "
           "correspond (UNDERGOER (term direction DEFINITE (CONTENT %s))) (CONTENT (term %s "
           "GENERIC)))))" % (term(mover, "DEFINITE"), side))
    return "agent 1 says that the direction of the %s is %s" % (mover, side), x.messages


SCHEMAS = [basic_property, basic_question, basic_place, basic_fact, basic_request,
           basic_colour, basic_part_of_place, basic_direction]
