"""The hand-written source of the figurative additions to the lexicon: lexicon release
0.5, with its four roots, its six conventional figurative senses and the nine mappings
that motivate those senses and the idioms of release 0.3 whose route is a figure.

Forms are not written here: `build_figures.py` assigns the roots theirs under the
distance rules, after every earlier word's, so that nothing earlier moves, and a sense
takes the form of the root it extends.
"""

from language_source import A, P, R, S, ST

RELEASE = "0.5"

# Roots of release 0.5, each (key, kind, sort, definition, roles), in the form of
# `language_source.ROOTS`: the word of relational likeness, which an analogy asserts; the
# source domain of captivity, whose agent and undergoer formations name the captor and the
# captive; and a pair of aesthetic judgements that measure a thing's form by how much it
# achieves with how little.
ROOTS = [
    ("analogous", "predicate", ST, "have the structure another relation has",
     [("undergoer", S), ("content", S)]),
    ("confine", "predicate", ST, "keep something where it cannot leave",
     [("actor", A), ("undergoer", R)]),
    ("elegant", "predicate", ST, "be pleasing in form by achieving much with little",
     [("undergoer", R)]),
    ("clumsy", "predicate", ST, "be displeasing in form by using more than is needed",
     [("undergoer", R)]),
]

# The conventional figurative senses, each (root, key, definition, frame, roles, mapping,
# constructed history). The frame is the role of the unit the word heads and the kind of
# constituent filling it that select the sense; a sense keeps its root's sort, so that its
# unit takes the defaults its form always took.
SENSES = [
    ("take", "understand", "come to understand a content", ("undergoer", "situation"),
     [("actor", A), ("undergoer", P)], 1,
     "Constructed history: a content was first said to be taken as a record is taken from "
     "a store, whole and ready to use; once taking a content came to mean having it ready "
     "to reason with, the sense stood apart from the taking of a thing."),
    ("arrive", "conclude", "come to hold a content as the end of one's reasoning",
     ("content", "situation"), [("undergoer", A), ("content", P)], 2,
     "Constructed history: reasoning was said to travel from its premises to what follows, "
     "as a message travels a network from node to node, and the content an inference "
     "reaches came to be the place it arrives at."),
    ("freeze", "settle", "become fixed and no longer open to change",
     ("undergoer", "situation"), [("undergoer", P)], 3,
     "Constructed history: water that freezes keeps its shape, and a content no "
     "participant may change any longer was said to freeze; the release of a design whose "
     "decisions could no longer move fixed the sense."),
    ("pressure", "urgency", "the need that a content be brought about soon",
     ("content", "situation"), [("content", S)], 4,
     "Constructed history: a content that must be brought about soon presses on the agent "
     "that must act, as force presses on an area, and the measure of that need became the "
     "pressure of the content."),
    ("storm", "burst", "many of what the content names, arriving in a short time",
     ("content", "term"), [("content", R)], 5,
     "Constructed history: networks were said to have weather, calm when nothing arrives "
     "and stormy when much arrives at once, and a storm of messages came to mean their "
     "burst without the weather."),
    ("light", "clarity", "what makes a content plain to the one who considers it",
     ("content", "situation"), [("content", P)], 6,
     "Constructed history: what makes a content plain lets it be seen, as light lets a "
     "thing be seen, and the light on a content came to mean what makes it plain."),
]

# The mappings, each (name, source domain, target domain, correspondences, what it
# motivates). A correspondence pairs an element of the source with an element of the
# target; what a mapping motivates is named by the key of a sense of this release or of an
# idiom of release 0.3.
MAPPINGS = [
    ("IDEAS ARE OBJECTS", "objects held and handed over", "contents understood and told",
     [("an object", "a content"), ("getting hold of an object", "coming to understand a content"),
      ("the one who holds the object", "the one who understands the content"),
      ("handing an object over", "making a content understood")],
     ["understand"]),
    ("REASONING IS TRAVEL", "travel across a network", "reasoning",
     [("a traveller", "a reasoner"), ("the place set out from", "the premises"),
      ("the route", "the steps of an inference"), ("the place reached", "the conclusion")],
     ["conclude"]),
    ("WHAT CAN CHANGE IS LIQUID", "water and ice", "contents open or closed to change",
     [("liquid water", "a content still open to change"), ("ice", "a content fixed"),
      ("freezing", "a content's becoming fixed"), ("cold", "the decision that fixes it")],
     ["settle"]),
    ("URGENCY IS PRESSURE", "force on an area", "the need to act soon",
     [("force", "the need that a content be brought about"),
      ("the area pressed", "the agent that must act"), ("more force", "less time to act")],
     ["urgency"]),
    ("NETWORK ACTIVITY IS WEATHER", "weather", "the traffic of a network",
     [("the atmosphere", "the network"), ("a storm", "a burst of messages or of changes"),
      ("calm", "no new record arriving")],
     ["burst", "storm on the network", "quiet network"]),
    ("KNOWING IS SEEING", "light and sight", "knowledge",
     [("light", "what makes a content plain"), ("seeing", "knowing"),
      ("darkness", "not knowing")],
     ["clarity"]),
    ("WHAT IS UNAVAILABLE IS HELD CAPTIVE", "captivity", "the availability of a resource",
     [("a captor", "the system that keeps a resource"), ("a captive", "the resource kept"),
      ("release", "making the resource available")],
     ["held by the service"]),
    ("KNOWLEDGE WITHOUT A SOURCE COMES FROM THE AIR", "the air", "the origin of knowledge",
     [("the air", "the training an agent learned from"),
      ("taking from the air", "believing without a source one can cite")],
     ["taken from the air"]),
    ("WHAT COSTS NOTHING IS WATER", "water", "price",
     [("water", "what costs nothing"), ("drawing water", "receiving without paying")],
     ["water price"]),
]
