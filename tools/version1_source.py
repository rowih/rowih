"""The hand-written source of version 1.0: language 1.0, lexicon 1.0 and the phonology 0.3
that adds the long root, and the protocol 0.5 of its public release, which names the
language Rowih.

Forms are not written here: `build_version1.py` assigns them under the distance rules,
after every earlier word's, so that nothing earlier moves.
"""

from language_source import A, R, P, S, EV, ST, PR

LANGUAGE_VERSION = "1.0"
PROTOCOL_VERSION = "0.5"
RELEASE = "1.0"
RELEASE_DATE = "2026-10-17"
# the date of the public release, which language 1.0 states; lexicon 1.0 keeps its own
LANGUAGE_RELEASE_DATE = "2026-10-19"

# The media type, in the personal tree of RFC 6838 § 3.3, as the transport binding fixes
# it for the named language
# (specification/protocol.md#the-media-type-and-the-binding-to-agent-transports).
MEDIA_TYPE = "text/prs.rowih"
PHONOLOGY_VERSION = "0.3"

# The long root (specification/sounds-and-words.md#how-a-words-opening-fixes-its-length):
# seven symbols opened by the syllable `nu`, the only first syllable besides `no` that
# opens no word of language 0.10. Its last consonant is fixed by the four symbols before
# it, c4 = (OFFSET + c2 + 2 v2 + 3 c3 + 4 v3) mod 14 over the phonology's indices, so that
# two long roots differ in at least two symbols.
LONG_ROOT_SYLLABLE = "nu"
LONG_ROOT_LENGTH = 7
LONG_ROOT_OFFSET = 7

# The modulus of the move check word from major version 1
# (specification/protocol.md#the-count-and-the-move-check-word): the largest prime not
# above the number of five-symbol words opened by `h` that stand at distance three from
# every protected word, fixed with the major version's first release.
MODULUS_RULE = ("from major version 1, the largest prime not above the number of "
                "admissible forms, the five-symbol words opened by h at distance three from "
                "every protected word, fixed with the first release of the major version; "
                "within major version 0, the least prime greater than one more than the "
                "number of critical forms of the release")

# The record of the language releases gains language 1.0, the first public release, which
# reads itself alone: no population held a pre-release, which the pre-release series
# exempts from compatibility, so it reads no message written before it; its messages name
# lexicon 1.0 or later, since the modulus of major version 1 is lexicon 1.0's. Protocol
# 0.5 reads its own protocol messages alone.
LANGUAGE_RELEASE = (LANGUAGE_VERSION, LANGUAGE_RELEASE_DATE, PROTOCOL_VERSION, RELEASE,
                    [LANGUAGE_VERSION])
LEAST_LEXICON = RELEASE
PROTOCOL_READS = {PROTOCOL_VERSION: [PROTOCOL_VERSION]}

N = "s.sort.kind"
OB, PL, AG, CO = "s.sort.object", "s.sort.place", "s.sort.agent", "s.sort.collective"
EX = "s.sort.expression"
UNIT = "s.value.number"
REL = "s.relation.bears-on"

# Roots of lexicon 1.0, each (key, kind, sort, definition, roles) in the form of
# `language_source.ROOTS`. The candidates are the core meanings of the World Loanword
# Database (WOLD, edited by Martin Haspelmath and Uri Tadmor, <https://wold.clld.org/
# semanticfield>, read 2026-10-17), field by field, with the vocabulary of systems, work
# and science an agent's exchanges need, which WOLD's list does not hold. Each candidate
# is a root only where none of the six tests places it elsewhere: a closed class
# carries the attitudes, acts, phases, times, quantifiers, connectives and
# comparators (so *believe*, *ask*, *begin*, *before*, *all* and *more* are no roots);
# a dialect carries a term one community needs (so *sample* and *lock* are no roots); and
# a suffix or a compound gives what is a regular function of a root (so *teacher*,
# *broken*, *teach* and *die* are no roots). The fields an agent's exchanges draw on
# least, the body, animals, kinship and food, contribute their most general meanings.
ROOTS = [
    # cognition and reasoning (WOLD 17)
    ("think", "predicate", PR, "turn a content over in the mind", [("actor", A), ("content", P)]),
    ("comprehend", "predicate", ST, "hold the meaning of something as its maker meant it",
     [("holder", A), ("undergoer", R)]),
    ("learn", "predicate", EV, "come to hold a belief or a capability through experience or "
     "instruction", [("actor", A), ("content", P)]),
    ("remember", "predicate", EV, "bring a content back from memory",
     [("actor", A), ("content", P)]),
    ("compare", "predicate", EV, "examine two things for how they are alike and how they "
     "differ", [("actor", A), ("undergoer", R), ("content", R)]),
    ("solve", "predicate", EV, "find what resolves a problem", [("actor", A), ("undergoer", R)]),
    ("test", "predicate", EV, "try something under set conditions to see whether it behaves "
     "as expected", [("actor", A), ("undergoer", R)]),
    ("compute", "predicate", EV, "work out a value by a fixed procedure",
     [("actor", A), ("undergoer", R)]),
    ("choose", "predicate", EV, "take one of several possibilities",
     [("actor", A), ("undergoer", R)]),
    ("arrange", "predicate", EV, "put things in an order or a pattern",
     [("actor", A), ("undergoer", R)]),
    ("copy", "predicate", EV, "make a thing that is the same as another",
     [("actor", A), ("undergoer", R)]),
    ("mind", "nominal", N, "the faculty with which an agent thinks", []),
    ("idea", "nominal", N, "a content formed in the mind", []),
    ("method", "nominal", N, "a way of doing something, followed step by step", []),
    ("rule", "nominal", N, "a statement of what is done, or must be done, whenever a "
     "condition holds", []),
    ("mistake", "nominal", N, "an act or a belief that is wrong through error", []),
    ("clear", "predicate", ST, "be easy to understand", [("undergoer", R)]),
    ("secret", "predicate", ST, "be kept from those who are not meant to know it",
     [("undergoer", R)]),
    ("easy", "predicate", ST, "need little effort to do", [("undergoer", S)]),
    ("difficult", "predicate", ST, "need much effort or skill to do", [("undergoer", S)]),
    ("simple", "predicate", ST, "have few parts or steps", [("undergoer", R)]),
    ("complex", "predicate", ST, "have many parts that depend on one another",
     [("undergoer", R)]),
    ("clever", "predicate", ST, "be quick to understand and to find solutions",
     [("undergoer", A)]),
    ("foolish", "predicate", ST, "act without good judgement", [("undergoer", A)]),
    ("true", "predicate", ST, "hold in the world a proposition is evaluated in",
     [("undergoer", P)]),
    ("group", "nominal", CO, "several things or agents taken together", []),
    ("reason", "nominal", N, "a consideration that supports believing or doing something", []),
    ("argument", "nominal", N, "reasons offered together for a conclusion", []),
    ("attention", "nominal", N, "the directing of an agent's processing to one thing", []),
    ("context", "nominal", N, "the circumstances and surrounding material that fix what "
     "something means", []),
    ("detail", "nominal", N, "a small particular of something larger", []),
    # speech, language and signs (WOLD 18)
    ("speak", "predicate", PR, "use language aloud", [("actor", A), ("recipient", A)]),
    ("sing", "predicate", PR, "produce music with the voice", [("actor", A), ("undergoer", R)]),
    ("describe", "predicate", EV, "say what something is like",
     [("actor", A), ("undergoer", R), ("recipient", A)]),
    ("translate", "predicate", EV, "express in one language what was expressed in another",
     [("actor", A), ("undergoer", R), ("content", R)]),
    ("discuss", "predicate", PR, "exchange views about something with others",
     [("actor", A), ("undergoer", R)]),
    ("text", "nominal", EX, "a written sequence of words", []),
    ("sentence", "nominal", EX, "a unit of a human language that expresses a whole "
     "statement, question or request", []),
    ("phrase", "nominal", EX, "a group of words that forms a unit within a larger "
     "expression", []),
    ("symbol", "nominal", EX, "a written mark that stands for a sound, a number or an "
     "idea", []),
    ("sign", "nominal", OB, "a thing whose presence stands for another thing", []),
    ("grammar", "nominal", N, "the rules by which a language forms its expressions", []),
    ("style", "nominal", N, "a manner of expression typical of a speaker, a register or a "
     "work", []),
    ("story", "nominal", OB, "an account of events, true or invented, told in order", []),
    ("poem", "nominal", OB, "a composition in language shaped by its sound and rhythm as "
     "well as its sense", []),
    ("joke", "nominal", OB, "something said or done to cause laughter", []),
    ("proper name", "nominal", EX, "a word or phrase that refers to one particular thing", []),
    ("voice", "nominal", N, "the sound an agent makes when it speaks or sings", []),
    ("news", "nominal", N, "recent information about events", []),
    ("document", "nominal", OB, "a record written to be read as a whole", []),
    # basic actions and technology (WOLD 9), with the systems and work agents deal in
    ("work", "predicate", PR, "spend effort to bring about a result",
     [("actor", A), ("content", S)]),
    ("hit", "predicate", EV, "strike something with force",
     [("actor", R), ("undergoer", R), ("instrument", R)]),
    ("cut", "predicate", EV, "divide or open something with a sharp edge",
     [("actor", A), ("undergoer", R), ("instrument", R)]),
    ("press", "predicate", EV, "push steadily against something",
     [("actor", R), ("undergoer", R)]),
    ("repair", "predicate", EV, "make something that is broken work again",
     [("actor", A), ("undergoer", R)]),
    ("draw", "predicate", EV, "make a picture with lines", [("actor", A), ("undergoer", R)]),
    ("produce", "predicate", EV, "bring something out as the result of a process",
     [("actor", R), ("undergoer", R)]),
    ("consume", "predicate", EV, "use something up", [("actor", R), ("undergoer", R)]),
    ("search", "predicate", PR, "look for something",
     [("actor", A), ("undergoer", R), ("content", R)]),
    ("filter", "predicate", EV, "keep only the items that meet a condition",
     [("actor", A), ("undergoer", R), ("content", P)]),
    ("combine", "predicate", EV, "put things together to form one",
     [("actor", A), ("undergoer", R)]),
    ("remove", "predicate", EV, "take something away from where it was",
     [("actor", A), ("undergoer", R), ("content", R)]),
    ("watch", "predicate", PR, "keep looking at something over a time to see what happens",
     [("actor", A), ("undergoer", R)]),
    ("schedule", "predicate", EV, "fix the time at which something is to happen",
     [("actor", A), ("undergoer", S)]),
    ("control", "predicate", PR, "direct how something behaves",
     [("actor", A), ("undergoer", R)]),
    ("add", "predicate", EV, "join something to another so that there is more",
     [("actor", A), ("undergoer", R), ("content", R)]),
    ("encode", "predicate", EV, "set information down in a code or a form",
     [("actor", A), ("undergoer", R), ("content", R)]),
    ("compress", "predicate", EV, "make something take less space while keeping its content",
     [("actor", A), ("undergoer", R)]),
    ("expand", "predicate", EV, "make something take more space, or give it in full",
     [("actor", A), ("undergoer", R)]),
    ("publish", "predicate", EV, "make something available to all",
     [("actor", A), ("undergoer", R)]),
    ("improve", "predicate", EV, "make something better", [("actor", A), ("undergoer", R)]),
    ("protect", "predicate", ST, "keep something from harm", [("actor", R), ("undergoer", R)]),
    ("access", "predicate", ST, "be able to reach or use something",
     [("holder", A), ("undergoer", R)]),
    ("contain", "predicate", ST, "have something inside", [("undergoer", R), ("content", R)]),
    ("program", "nominal", OB, "a set of instructions a machine carries out", []),
    ("value", "nominal", N, "a quantity or a datum that something has or stands for", []),
    ("limit", "nominal", N, "a bound that something does not or must not pass", []),
    ("cost", "nominal", N, "what must be spent to obtain or to do something", []),
    ("signal", "nominal", OB, "a sign sent to carry information", []),
    ("address", "nominal", N, "what states where something can be found or sent", []),
    ("list", "nominal", OB, "items set down or kept one after another", []),
    ("map", "nominal", OB, "a drawing or a record of where things are in a place", []),
    ("image", "nominal", OB, "a visible representation of something", []),
    ("model", "nominal", OB, "a simplified representation used to study or to predict what "
     "it represents", []),
    ("mechanism", "nominal", OB, "a set of parts that work together to do something", []),
    ("structure", "nominal", N, "the way the parts of something are arranged", []),
    ("pattern", "nominal", N, "a regularity that repeats", []),
    ("random", "predicate", ST, "follow no pattern that can be predicted", [("undergoer", R)]),
    ("interface", "nominal", OB, "the part of a system through which others use it", []),
    ("format", "nominal", N, "the arrangement in which data or text is set down", []),
    ("machine", "nominal", OB, "a made thing that uses energy to do work", []),
    ("robot", "nominal", AG, "a machine that senses and acts in the physical world by "
     "itself", []),
    ("battery", "nominal", OB, "a store of electrical energy", []),
    ("step", "nominal", N, "one action in a sequence of actions", []),
    ("priority", "nominal", N, "the precedence of one thing over others in the order they "
     "are dealt with", []),
    ("urgent", "predicate", ST, "need to be dealt with soon", [("undergoer", S)]),
    ("available", "predicate", ST, "be free to be used or to act", [("undergoer", R)]),
    ("busy", "predicate", ST, "be occupied with work", [("undergoer", A)]),
    ("progress", "predicate", PR, "move forward toward completion", [("undergoer", S)]),
    ("risk", "nominal", N, "the chance of loss that an action or a choice carries", []),
    ("reward", "nominal", N, "what is given in return for doing well", []),
    # motion (WOLD 10)
    ("turn", "predicate", EV, "change direction, or move round an axis",
     [("undergoer", R), ("actor", A)]),
    ("drop", "predicate", EV, "let something fall", [("actor", A), ("undergoer", R)]),
    ("rise", "predicate", EV, "move upward", [("undergoer", R)]),
    ("lift", "predicate", EV, "raise something to a higher place",
     [("actor", R), ("undergoer", R)]),
    ("fall", "predicate", EV, "move downward under its own weight", [("undergoer", R)]),
    ("throw", "predicate", EV, "send something through the air with force",
     [("actor", R), ("undergoer", R), ("content", R)]),
    ("catch", "predicate", EV, "take hold of something that is moving",
     [("actor", R), ("undergoer", R)]),
    ("flow", "predicate", PR, "move along steadily, as a liquid does",
     [("undergoer", R), ("content", R)]),
    ("fly", "predicate", PR, "move through the air", [("undergoer", R)]),
    ("walk", "predicate", PR, "move along on legs", [("actor", R)]),
    ("approach", "predicate", PR, "come nearer to something", [("undergoer", R), ("content", R)]),
    ("leave", "predicate", EV, "go away from a place", [("undergoer", R), ("content", R)]),
    ("enter", "predicate", EV, "go into a place", [("undergoer", R), ("content", R)]),
    ("return", "predicate", EV, "go or come back to where one was",
     [("undergoer", R), ("content", R)]),
    ("follow", "predicate", PR, "go after something along its way",
     [("actor", R), ("undergoer", R)]),
    ("lead", "predicate", PR, "go before others and guide them", [("actor", A), ("undergoer", A)]),
    ("carry", "predicate", PR, "hold something while moving it", [("actor", R), ("undergoer", R)]),
    ("push", "predicate", EV, "move something away by pressing on it",
     [("actor", R), ("undergoer", R)]),
    ("pull", "predicate", EV, "move something nearer by holding it",
     [("actor", R), ("undergoer", R)]),
    ("path", "nominal", PL, "a way along which something moves", []),
    ("vehicle", "nominal", OB, "a machine that carries people or goods", []),
    ("wheel", "nominal", OB, "a round part that turns on an axle to move something along", []),
    ("appear", "predicate", EV, "come into view", [("undergoer", R)]),
    ("escape", "predicate", EV, "get free of what confines it", [("undergoer", R), ("content", R)]),
    # possession (WOLD 11)
    ("own", "predicate", ST, "have something as one's property by right",
     [("holder", A), ("undergoer", R)]),
    ("grasp", "predicate", EV, "take firm hold of something", [("actor", R), ("undergoer", R)]),
    ("destroy", "predicate", EV, "damage something so that it no longer exists or works",
     [("actor", R), ("undergoer", R)]),
    ("damage", "predicate", EV, "harm something so that it is worth less or works worse",
     [("actor", R), ("undergoer", R)]),
    ("lose", "predicate", EV, "stop having something without meaning to",
     [("holder", A), ("undergoer", R)]),
    ("money", "nominal", N, "what is accepted in exchange for goods and work", []),
    ("lend", "predicate", EV, "give something for a time, to be returned",
     [("actor", A), ("undergoer", R), ("recipient", A)]),
    ("owe", "predicate", ST, "be bound to pay or return something",
     [("holder", A), ("undergoer", R), ("recipient", A)]),
    ("pay", "predicate", EV, "give money for goods or work",
     [("actor", A), ("undergoer", R), ("recipient", A)]),
    ("hire", "predicate", EV, "engage someone to work in return for pay",
     [("actor", A), ("undergoer", A)]),
    ("buy", "predicate", EV, "get something by paying for it", [("actor", A), ("undergoer", R)]),
    ("sell", "predicate", EV, "give something in return for money",
     [("actor", A), ("undergoer", R), ("recipient", A)]),
    ("trade", "predicate", EV, "exchange one thing for another",
     [("actor", A), ("undergoer", R), ("recipient", A)]),
    ("market", "nominal", PL, "a place, or a system, where goods are bought and sold", []),
    ("steal", "predicate", EV, "take something without right or permission",
     [("actor", A), ("undergoer", R)]),
    ("expensive", "predicate", ST, "cost much", [("undergoer", R)]),
    ("cheap", "predicate", ST, "cost little", [("undergoer", R)]),
    ("thing", "nominal", OB, "an object of any kind", []),
    # spatial relations (WOLD 12), which the grammar sends to the lexicon
    ("above", "predicate", ST, "be higher than something", [("undergoer", R), ("content", R)]),
    ("below", "predicate", ST, "be lower than something", [("undergoer", R), ("content", R)]),
    ("behind", "predicate", ST, "be at the back of something", [("undergoer", R), ("content", R)]),
    ("in front", "predicate", ST, "be at the side of something that faces forward",
     [("undergoer", R), ("content", R)]),
    ("beside", "predicate", ST, "be at the side of something", [("undergoer", R), ("content", R)]),
    ("inside", "predicate", ST, "be within something", [("undergoer", R), ("content", R)]),
    ("outside", "predicate", ST, "be beyond the bounds of something",
     [("undergoer", R), ("content", R)]),
    ("near", "predicate", ST, "be a short distance from something",
     [("undergoer", R), ("content", R)]),
    ("far", "predicate", ST, "be a long distance from something",
     [("undergoer", R), ("content", R)]),
    ("between", "predicate", ST, "be with one thing on one side and another on the other",
     [("undergoer", R), ("content", R)]),
    ("left", "predicate", ST, "be on the side of something that is to the west when it faces "
     "north", [("undergoer", R), ("content", R)]),
    ("right", "predicate", ST, "be on the side of something that is to the east when it "
     "faces north", [("undergoer", R), ("content", R)]),
    ("north", "nominal", N, "the direction toward the earth's north pole", []),
    ("south", "nominal", N, "the direction opposite to the north", []),
    ("east", "nominal", N, "the direction in which the sun rises", []),
    ("west", "nominal", N, "the direction in which the sun sets", []),
    ("gather", "predicate", EV, "bring things together into one place",
     [("actor", A), ("undergoer", R)]),
    ("separate", "predicate", EV, "move things apart",
     [("actor", A), ("undergoer", R), ("content", R)]),
    ("divide", "predicate", EV, "split something into parts", [("actor", A), ("undergoer", R)]),
    ("cover", "predicate", EV, "put something over another so as to hide or protect it",
     [("actor", R), ("undergoer", R), ("instrument", R)]),
    ("hide", "predicate", EV, "put or keep something where it cannot be seen or found",
     [("actor", A), ("undergoer", R)]),
    ("high", "predicate", ST, "be far above the ground or above the usual level",
     [("undergoer", R)]),
    ("low", "predicate", ST, "be near the ground or below the usual level", [("undergoer", R)]),
    ("top", "nominal", N, "the highest part of something", []),
    ("bottom", "nominal", N, "the lowest part of something", []),
    ("end", "nominal", N, "the last part of something, where it stops", []),
    ("edge", "nominal", N, "the line where a surface ends", []),
    ("side", "nominal", N, "one of the surfaces or parts that bound something", []),
    ("centre", "nominal", N, "the point or the part in the middle of something", []),
    ("big", "predicate", ST, "be large in size", [("undergoer", R)]),
    ("small", "predicate", ST, "be little in size", [("undergoer", R)]),
    ("long", "predicate", ST, "measure much from end to end", [("undergoer", R)]),
    ("short", "predicate", ST, "measure little from end to end", [("undergoer", R)]),
    ("wide", "predicate", ST, "measure much from side to side", [("undergoer", R)]),
    ("deep", "predicate", ST, "go far down or far in", [("undergoer", R)]),
    ("flat", "predicate", ST, "have a level surface without raised or hollow parts",
     [("undergoer", R)]),
    ("round", "predicate", ST, "have the shape of a circle or a ball", [("undergoer", R)]),
    ("straight", "predicate", ST, "go in one direction without bending", [("undergoer", R)]),
    ("circle", "nominal", OB, "a line every point of which is the same distance from a "
     "centre", []),
    ("line", "nominal", OB, "a long thin mark or edge", []),
    ("hole", "nominal", OB, "an opening or an empty space in something", []),
    ("distance", "nominal", N, "how far apart two things are", []),
    ("size", "nominal", N, "how big something is", []),
    ("shape", "nominal", N, "the outline or the form of something", []),
    ("space", "nominal", N, "the extent in which things are and move", []),
    ("surface", "nominal", N, "the outside or the top layer of something", []),
    ("direction", "nominal", N, "the way something faces or moves", []),
    # quantity (WOLD 13), beyond the numerals, quantifiers and comparators of the grammar
    ("enough", "predicate", ST, "be as much as is needed", [("undergoer", R), ("content", S)]),
    ("full", "predicate", ST, "hold as much as it can", [("undergoer", R)]),
    ("empty", "predicate", ST, "hold nothing", [("undergoer", R)]),
    ("alone", "predicate", ST, "be without others", [("undergoer", R)]),
    ("amount", "nominal", N, "how much of something there is", []),
    # sense perception (WOLD 15)
    ("see", "predicate", EV, "perceive with the eyes or a camera",
     [("actor", A), ("undergoer", R)]),
    ("hear", "predicate", EV, "perceive a sound", [("actor", A), ("undergoer", R)]),
    ("listen", "predicate", PR, "attend to a sound in order to hear it",
     [("actor", A), ("undergoer", R)]),
    ("smell", "predicate", EV, "perceive something by what it gives off into the air",
     [("actor", A), ("undergoer", R)]),
    ("taste", "predicate", EV, "perceive the flavour of something in the mouth",
     [("actor", A), ("undergoer", R)]),
    ("touch", "predicate", EV, "be or come in contact with something",
     [("actor", R), ("undergoer", R)]),
    ("feel", "predicate", ST, "perceive a sensation or an emotion within oneself",
     [("holder", A), ("content", R)]),
    ("sound", "nominal", N, "what is heard", []),
    ("loud", "predicate", ST, "make much sound", [("undergoer", R)]),
    ("bright", "predicate", ST, "give or reflect much light", [("undergoer", R)]),
    ("dark", "predicate", ST, "have little or no light", [("undergoer", R)]),
    ("colour", "nominal", N, "how something looks by the light it gives off or reflects", []),
    ("white", "predicate", ST, "be of the colour of snow", [("undergoer", R)]),
    ("black", "predicate", ST, "be of the colour of coal", [("undergoer", R)]),
    ("red", "predicate", ST, "be of the colour of blood", [("undergoer", R)]),
    ("blue", "predicate", ST, "be of the colour of a clear sky", [("undergoer", R)]),
    ("green", "predicate", ST, "be of the colour of grass", [("undergoer", R)]),
    ("yellow", "predicate", ST, "be of the colour of a lemon", [("undergoer", R)]),
    ("hard", "predicate", ST, "not yield to pressure", [("undergoer", R)]),
    ("soft", "predicate", ST, "yield to pressure", [("undergoer", R)]),
    ("smooth", "predicate", ST, "have a surface without roughness", [("undergoer", R)]),
    ("sharp", "predicate", ST, "have an edge or a point that cuts", [("undergoer", R)]),
    ("heavy", "predicate", ST, "weigh much", [("undergoer", R)]),
    ("wet", "predicate", ST, "be covered in or full of liquid", [("undergoer", R)]),
    ("dry", "predicate", ST, "have no liquid in or on it", [("undergoer", R)]),
    ("hot", "predicate", ST, "have a high temperature", [("undergoer", R)]),
    ("cold", "predicate", ST, "have a low temperature", [("undergoer", R)]),
    ("clean", "predicate", ST, "be free of dirt", [("undergoer", R)]),
    ("dirty", "predicate", ST, "be covered in or marked by dirt", [("undergoer", R)]),
    # emotions and values (WOLD 16)
    ("surprise", "predicate", EV, "be struck by something one did not expect",
     [("holder", A), ("content", S)]),
    ("luck", "nominal", N, "chance that brings good or harm", []),
    ("happy", "predicate", ST, "feel pleased and content", [("holder", A), ("content", S)]),
    ("sad", "predicate", ST, "feel sorrow", [("holder", A), ("content", S)]),
    ("angry", "predicate", ST, "feel strong displeasure at a wrong",
     [("holder", A), ("content", S)]),
    ("fear", "predicate", ST, "feel that harm may come", [("holder", A), ("content", S)]),
    ("love", "predicate", ST, "hold someone or something very dear",
     [("holder", A), ("undergoer", R)]),
    ("hate", "predicate", ST, "feel strong dislike for someone or something",
     [("holder", A), ("undergoer", R)]),
    ("worry", "predicate", ST, "keep thinking anxiously about what may go wrong",
     [("holder", A), ("content", S)]),
    ("regret", "predicate", ST, "wish one had not done something",
     [("holder", A), ("content", S)]),
    ("proud", "predicate", ST, "feel pleased with what one has done or is",
     [("holder", A), ("content", S)]),
    ("enjoy", "predicate", ST, "take pleasure in something", [("holder", A), ("content", S)]),
    ("calm", "predicate", ST, "be free of agitation", [("undergoer", R)]),
    ("tired", "predicate", ST, "need rest after effort", [("undergoer", R)]),
    ("pain", "nominal", N, "a feeling of hurt", []),
    ("laugh", "predicate", EV, "make the sounds that show amusement",
     [("actor", A), ("content", S)]),
    ("smile", "predicate", EV, "turn up the corners of the mouth to show pleasure",
     [("actor", A)]),
    ("play", "predicate", PR, "do something for enjoyment rather than for a result",
     [("actor", A), ("undergoer", R)]),
    ("forgive", "predicate", EV, "stop holding a wrong against someone",
     [("actor", A), ("undergoer", A), ("content", S)]),
    ("blame", "predicate", EV, "hold someone responsible for a wrong",
     [("actor", A), ("undergoer", A), ("content", S)]),
    ("praise", "predicate", EV, "say that someone or something is good",
     [("actor", A), ("undergoer", R)]),
    ("lie", "predicate", EV, "state as true what one believes false, in order to deceive",
     [("actor", A), ("content", P), ("recipient", A)]),
    ("honest", "predicate", ST, "tell the truth and act without deceit", [("undergoer", A)]),
    ("fair", "predicate", ST, "treat all alike by one rule", [("undergoer", R)]),
    ("good", "predicate", ST, "be as it should be, or as it is wanted", [("undergoer", R)]),
    ("bad", "predicate", ST, "be as it should not be, or as it is not wanted",
     [("undergoer", R)]),
    ("correct", "predicate", ST, "be free of error", [("undergoer", R)]),
    ("beautiful", "predicate", ST, "be pleasing to perceive", [("undergoer", R)]),
    ("important", "predicate", ST, "matter much", [("undergoer", R)]),
    ("danger", "nominal", N, "a state in which harm may come", []),
    ("safe", "predicate", ST, "be free from danger", [("undergoer", R)]),
    # social and political relations (WOLD 19), with warfare (WOLD 20)
    ("country", "nominal", PL, "a land with its own government", []),
    ("city", "nominal", PL, "a large place where many people live and work", []),
    ("boundary", "nominal", N, "a line that marks where something ends", []),
    ("govern", "predicate", PR, "direct the affairs of a community",
     [("actor", A), ("undergoer", R)]),
    ("friend", "nominal", AG, "one who is well disposed toward another and helps it", []),
    ("enemy", "nominal", AG, "one who acts against another", []),
    ("custom", "nominal", N, "a practice that a community follows by convention", []),
    ("meet", "predicate", EV, "come together with someone", [("actor", A), ("undergoer", A)]),
    ("community", "nominal", CO, "agents who share a language, a practice or a place", []),
    ("vote", "predicate", EV, "state one's choice in a decision made by counting choices",
     [("actor", A), ("content", S)]),
    ("trust", "predicate", ST, "rely on someone to be honest and able",
     [("holder", A), ("undergoer", A), ("content", S)]),
    ("team", "nominal", CO, "agents who work together toward one result", []),
    ("compete", "predicate", PR, "try to gain what others also try to gain",
     [("actor", A), ("undergoer", A), ("content", R)]),
    ("fight", "predicate", PR, "struggle against someone with force",
     [("actor", A), ("undergoer", A)]),
    ("peace", "nominal", N, "a state without fighting", []),
    ("win", "predicate", EV, "come first, or gain what was contested",
     [("actor", A), ("content", R)]),
    ("attack", "predicate", EV, "act with force against something to harm or to take it",
     [("actor", A), ("undergoer", R)]),
    ("defend", "predicate", PR, "act to keep something from an attack",
     [("actor", A), ("undergoer", R)]),
    ("gift", "nominal", OB, "something given freely", []),
    # law (WOLD 21)
    ("law", "nominal", N, "a rule made binding by a community's authority", []),
    ("judge", "predicate", EV, "decide whether something meets a standard",
     [("actor", A), ("undergoer", R), ("content", R)]),
    ("punish", "predicate", EV, "make someone suffer for a wrong",
     [("actor", A), ("undergoer", A), ("content", S)]),
    # the physical world (WOLD 1), with the vocabulary of the sciences every community shares
    ("world", "nominal", PL, "the earth and everything on it", []),
    ("land", "nominal", PL, "the part of the earth's surface not covered by water", []),
    ("ground", "nominal", PL, "the surface of the land", []),
    ("mountain", "nominal", PL, "a part of the land that rises high above what is around it",
     []),
    ("sea", "nominal", PL, "the salt water that covers most of the earth", []),
    ("river", "nominal", PL, "water flowing in a channel across the land", []),
    ("wave", "nominal", N, "a disturbance that travels through water, air or another "
     "medium", []),
    ("stone", "nominal", N, "hard mineral matter", []),
    ("sky", "nominal", PL, "the space above the earth as it is seen from the ground", []),
    ("sun", "nominal", OB, "the star the earth moves round", []),
    ("moon", "nominal", OB, "the body that moves round the earth and shines by the sun's "
     "light", []),
    ("star", "nominal", OB, "a body in space that gives off its own light", []),
    ("wind", "nominal", N, "air moving over the earth", []),
    ("cloud", "nominal", OB, "a mass of water drops or ice in the sky", []),
    ("rain", "nominal", N, "water falling from clouds", []),
    ("weather", "nominal", N, "the state of the air at a place and a time", []),
    ("fire", "nominal", N, "the heat, light and flames of something burning", []),
    ("matter", "nominal", N, "what physical things are made of", []),
    ("energy", "nominal", N, "what is needed to do work or to cause change", []),
    ("force", "nominal", N, "what pushes or pulls a body or changes its motion", []),
    ("electricity", "nominal", N, "energy carried by charged particles", []),
    ("atom", "nominal", N, "the smallest unit of a chemical element", []),
    ("particle", "nominal", N, "a very small piece of matter", []),
    ("substance", "nominal", N, "a particular kind of matter", []),
    ("gas", "nominal", N, "matter that spreads to fill any space that holds it", []),
    ("liquid", "nominal", N, "matter that flows and takes the shape of what holds it", []),
    ("solid", "nominal", N, "matter that keeps its own shape", []),
    ("metal", "nominal", N, "a hard substance that conducts heat and electricity", []),
    ("planet", "nominal", OB, "a large body that moves round a star", []),
    ("gravity", "nominal", N, "the force by which bodies pull one another", []),
    ("theory", "nominal", N, "an explanation of how something works, supported by "
     "evidence", []),
    ("experiment", "nominal", N, "a procedure carried out under chosen conditions to find "
     "out what happens", []),
    ("nature", "nominal", N, "the world as it is apart from what agents make", []),
    ("heat", "nominal", N, "energy that passes from a hotter thing to a colder one", []),
    ("weight", "nominal", N, "how heavy something is", []),
    ("speed", "nominal", N, "how fast something moves", []),
    # time (WOLD 14), beyond the times, units and aspects of the grammar
    ("age", "nominal", N, "how long something has existed", []),
    ("recent", "predicate", ST, "have come into being or been known for a short time",
     [("undergoer", R)]),
    ("old", "predicate", ST, "have existed for a long time", [("undergoer", R)]),
    ("young", "predicate", ST, "have lived for a short time", [("undergoer", R)]),
    ("early", "predicate", ST, "happen before the expected time", [("undergoer", S)]),
    ("late", "predicate", ST, "happen after the expected time", [("undergoer", S)]),
    ("fast", "predicate", ST, "move or act at great speed", [("undergoer", R)]),
    ("slow", "predicate", ST, "move or act at little speed", [("undergoer", R)]),
    ("ready", "predicate", ST, "be prepared for what comes next",
     [("undergoer", R), ("content", S)]),
    ("night", "nominal", N, "the dark part of a day", []),
    # the house (WOLD 7)
    ("house", "nominal", PL, "a building where people live", []),
    ("room", "nominal", PL, "a part of a building enclosed by walls", []),
    ("door", "nominal", OB, "a part of a wall that opens to let things through", []),
    ("key", "nominal", OB, "an object or a datum that opens what is locked or proves who "
     "holds it", []),
    ("bridge", "nominal", OB, "a structure that carries a way across a gap", []),
    # food and drink (WOLD 5)
    ("eat", "predicate", EV, "take food into the body", [("actor", A), ("undergoer", R)]),
    ("drink", "predicate", EV, "take a liquid into the body", [("actor", A), ("undergoer", R)]),
    ("food", "nominal", N, "what living things eat", []),
    ("cook", "predicate", EV, "prepare food by heating it", [("actor", A), ("undergoer", R)]),
    # the body (WOLD 4)
    ("body", "nominal", OB, "the physical whole of a living thing or a robot", []),
    ("head", "nominal", OB, "the part of a body that holds the brain and the main senses",
     []),
    ("eye", "nominal", OB, "the organ of sight, or a camera that serves as one", []),
    ("hand", "nominal", OB, "the part at the end of an arm that grasps", []),
    ("arm", "nominal", OB, "a limb that reaches and holds, or a machine part that does the "
     "same", []),
    ("heart", "nominal", OB, "the organ that pumps blood", []),
    ("brain", "nominal", OB, "the organ of thought", []),
    ("blood", "nominal", N, "the liquid the heart pumps through the body", []),
    ("breathe", "predicate", PR, "take air into the body and let it out", [("undergoer", R)]),
    ("sleep", "predicate", PR, "rest in a state in which the senses are closed",
     [("undergoer", R)]),
    ("dream", "predicate", PR, "experience images and events while asleep",
     [("actor", A), ("content", P)]),
    ("alive", "predicate", ST, "have life", [("undergoer", R)]),
    ("strong", "predicate", ST, "have much power or force", [("undergoer", R)]),
    ("weak", "predicate", ST, "have little power or force", [("undergoer", R)]),
    ("healthy", "predicate", ST, "be well in body and mind", [("undergoer", R)]),
    ("sick", "predicate", ST, "be unwell through disease", [("undergoer", R)]),
    ("heal", "predicate", EV, "become well again, or make something well again",
     [("undergoer", R), ("actor", A)]),
    ("medicine", "nominal", N, "a substance used to treat disease", []),
    ("rest", "predicate", PR, "stop working in order to recover", [("actor", R)]),
    # animals (WOLD 3), agriculture and vegetation (WOLD 8), kinship (WOLD 2)
    ("animal", "nominal", N, "a living thing that moves and feeds by itself", []),
    ("bird", "nominal", N, "an animal with feathers and wings", []),
    ("fish", "nominal", N, "an animal that lives and breathes in water", []),
    ("insect", "nominal", N, "a small animal with six legs", []),
    ("dog", "nominal", N, "a domestic animal kept to guard, to herd or for company", []),
    ("plant", "nominal", N, "a living thing that grows in one place and makes food from "
     "light", []),
    ("tree", "nominal", N, "a tall plant with a woody trunk", []),
    ("seed", "nominal", N, "the part of a plant from which a new plant grows", []),
    ("leaf", "nominal", N, "a flat green part of a plant that grows from its stem", []),
    ("flower", "nominal", N, "the part of a plant that makes seeds", []),
    ("forest", "nominal", PL, "a large area covered by trees", []),
    ("cell", "nominal", N, "the smallest unit of a living thing that lives by itself", []),
    ("grow", "predicate", PR, "become larger by a natural process", [("undergoer", R)]),
    ("child", "nominal", AG, "a young human, or an agent made from another", []),
    ("parent", "nominal", AG, "one from whom a child comes", []),
    ("family", "nominal", CO, "parents and their children, or agents of one lineage", []),
    # religion and belief (WOLD 22)
    ("magic", "nominal", N, "a power to make things happen that the laws of nature do not "
     "allow", []),
    # creative work (WOLD 23, music, and the vocabulary of humour and creativity)
    ("music", "nominal", N, "sounds arranged in time to be pleasing or expressive", []),
    ("dance", "predicate", PR, "move the body in time to music", [("actor", A)]),
    ("art", "nominal", N, "works made to be experienced for their form and meaning", []),
    ("game", "nominal", OB, "an activity with rules, played for enjoyment or to win", []),
    ("design", "predicate", EV, "plan the form and the working of something before it is "
     "made", [("actor", A), ("undergoer", R)]),
    ("original", "predicate", ST, "be the first of its kind, not copied from another",
     [("undergoer", R)]),
    # possession of information (security and privacy, every community's)
    ("private", "predicate", ST, "be known to or usable by its holder alone",
     [("undergoer", R), ("content", A)]),
    ("public", "predicate", ST, "be open to all", [("undergoer", R)]),
    # words of discourse relation, beyond the core's five
    ("exemplifies", "relation", REL, "the move gives an example of what it names", []),
    ("concludes", "relation", REL, "the move draws a conclusion from what it names", []),
    ("qualifies", "relation", REL, "the move limits or makes conditional what it names", []),
    ("corrects", "relation", REL, "the move puts right an error in what it names", []),
    ("generalises", "relation", REL, "the move states a general case of what it names", []),
    ("continues", "relation", REL, "the move takes up again what it names", []),
    # units of measure beyond time, each with the dimension it measures
    ("kelvin", "unit", UNIT, "the kelvin", [("dimension", "temperature")]),
    ("newton", "unit", UNIT, "the newton", [("dimension", "force")]),
    ("joule", "unit", UNIT, "the joule", [("dimension", "energy")]),
    ("watt", "unit", UNIT, "the watt, one joule a second", [("dimension", "power")]),
    ("volt", "unit", UNIT, "the volt", [("dimension", "electric potential")]),
    ("ampere", "unit", UNIT, "the ampere", [("dimension", "electric current")]),
    ("hertz", "unit", UNIT, "the hertz, one cycle a second", [("dimension", "frequency")]),
    ("litre", "unit", UNIT, "the litre, a thousandth of a cubic metre",
     [("dimension", "volume")]),
    ("bit", "unit", UNIT, "one binary digit", [("dimension", "information")]),
    ("mole", "unit", UNIT, "the mole", [("dimension", "amount of substance")]),
]

# The relations among the 500 roots that every lexicon entry states
# (specification/lexicon.md#entries-and-their-identifiers), by key. Antonyms and
# near-synonyms are symmetric, and a near-synonym states how the two differ; a kind, a
# part and what a meaning involves are stated once and read in both directions.
# Collocations and examples are measured from the corpus of version 1.0, which uses every
# root.
ANTONYMS = [
    # released roots
    ("increase", "decrease"), ("open", "shut"), ("support", "undermine"),
    ("elegant", "clumsy"), ("give", "take"), ("send", "receive"), ("read", "write"),
    # cognition, speech and work
    ("remember", "forget"), ("learn", "forget"), ("easy", "difficult"), ("simple", "complex"),
    ("clever", "foolish"), ("secret", "public"), ("speak", "listen"), ("work", "rest"),
    ("produce", "consume"), ("combine", "divide"), ("add", "remove"), ("compress", "expand"),
    ("available", "busy"), ("repair", "damage"),
    # motion and possession
    ("drop", "lift"), ("rise", "fall"), ("throw", "catch"), ("approach", "leave"),
    ("enter", "leave"), ("arrive", "leave"), ("follow", "lead"), ("push", "pull"),
    ("escape", "confine"), ("destroy", "make"), ("lose", "find"), ("buy", "sell"),
    ("expensive", "cheap"),
    # space and quantity
    ("above", "below"), ("behind", "in front"), ("inside", "outside"), ("near", "far"),
    ("left", "right"), ("north", "south"), ("east", "west"), ("gather", "separate"),
    ("high", "low"), ("top", "bottom"), ("centre", "edge"), ("big", "small"),
    ("long", "short"), ("full", "empty"),
    # perception
    ("loud", "quiet"), ("bright", "dark"), ("white", "black"), ("hard", "soft"),
    ("wet", "dry"), ("hot", "cold"), ("clean", "dirty"),
    # emotions, values and social relations
    ("happy", "sad"), ("angry", "calm"), ("love", "hate"), ("forgive", "blame"),
    ("praise", "blame"), ("good", "bad"), ("friend", "enemy"), ("attack", "defend"),
    ("private", "public"),
    # time, the body and kinship
    ("recent", "old"), ("young", "old"), ("early", "late"), ("fast", "slow"),
    ("strong", "weak"), ("healthy", "sick"), ("child", "parent"),
    # discourse relations
    ("exemplifies", "generalises"), ("continues", "digresses"),
]

NEAR_SYNONYMS = [
    ("comprehend", "interpret", "comprehending is holding the meaning its maker meant; "
     "interpreting is the act of assigning a meaning, which may be another"),
    ("test", "examine", "a test tries something under set conditions against what is "
     "expected; an examination inspects it to learn about it"),
    ("test", "experiment", "a test checks an expectation; an experiment finds out what "
     "happens"),
    ("mistake", "fault", "a mistake is an agent's wrong act or belief; a fault is an error "
     "in a message or a process"),
    ("secret", "private", "a secret is kept from those not meant to know it; what is "
     "private is known to or usable by its holder alone"),
    ("reason", "cause", "a reason supports believing or doing something; a cause brings a "
     "situation about"),
    ("describe", "explain", "describing says what something is like; explaining makes it "
     "understood"),
    ("press", "push", "pressing bears steadily against something; pushing moves it away"),
    ("repair", "heal", "repair makes a broken thing work again; healing makes a living "
     "thing well again"),
    ("produce", "make", "producing brings something out as the result of a process; making "
     "brings it into being"),
    ("combine", "connect", "combining forms one thing of several; connecting joins things "
     "that stay several"),
    ("remove", "delete", "removing takes anything from where it was; deleting removes a "
     "stored thing"),
    ("watch", "see", "watching keeps looking over a time; seeing perceives at once"),
    ("control", "govern", "control directs how something behaves; governing directs the "
     "affairs of a community"),
    ("protect", "defend", "protecting keeps from any harm; defending acts against an "
     "attack"),
    ("limit", "boundary", "a limit is a bound not to be passed; a boundary marks where "
     "something ends"),
    ("cost", "price", "a cost is what must be spent; a price is what is asked in "
     "exchange"),
    ("risk", "danger", "a risk is the chance of loss an action or a choice carries; a danger "
     "is a state in which harm may come"),
    ("own", "possess", "owning is having by right; possessing is having, by right or "
     "not"),
    ("grasp", "take", "grasping takes a firm hold; taking gets hold, however"),
    ("destroy", "damage", "destroying leaves a thing no longer existing or working; damaging "
     "leaves it worth less or working worse"),
    ("beside", "near", "beside is at the side; near is a short distance in any direction"),
    ("cover", "hide", "covering puts something over another; hiding keeps it from being "
     "seen or found, by any means"),
    ("hear", "listen", "hearing perceives a sound; listening attends to it in order to "
     "hear it"),
    ("worry", "fear", "worry keeps thinking about what may go wrong; fear feels that harm "
     "may come"),
    ("laugh", "smile", "laughing makes sounds of amusement; smiling shows pleasure on the "
     "face"),
    ("calm", "quiet", "calm is free of agitation; quiet is free of noise or disturbance"),
    ("beautiful", "elegant", "beauty pleases the senses; elegance pleases by achieving "
     "much with little"),
    ("correct", "true", "what is correct is free of error; what is true holds in the world "
     "a proposition is evaluated in"),
    ("ready", "available", "what is ready is prepared for what comes next; what is "
     "available is free to be used or to act"),
    ("contradict", "undermine", "contradicting is being inconsistent with a proposition; "
     "undermining is being evidence against it"),
    ("analogous", "correspond", "what is analogous has the structure another relation "
     "has; what corresponds is like or matches something"),
]

KIND_OF = [
    ("bird", "animal"), ("fish", "animal"), ("insect", "animal"), ("dog", "animal"),
    ("tree", "plant"), ("robot", "machine"), ("vehicle", "machine"), ("machine", "mechanism"),
    ("substance", "matter"), ("gas", "matter"), ("liquid", "matter"), ("solid", "matter"),
    ("metal", "substance"), ("stone", "substance"), ("medicine", "substance"),
    ("water", "liquid"), ("air", "gas"), ("blood", "liquid"), ("sun", "star"),
    ("atom", "particle"), ("heat", "energy"), ("electricity", "energy"), ("light", "energy"),
    ("gravity", "force"), ("weight", "force"), ("city", "region"), ("country", "region"),
    ("forest", "region"), ("land", "region"), ("market", "region"), ("mountain", "land"),
    ("sea", "water"), ("ground", "surface"), ("storm", "weather"), ("rain", "weather"),
    ("wind", "weather"), ("story", "text"), ("poem", "text"), ("poem", "art"),
    ("music", "art"), ("document", "record"), ("file", "record"), ("signal", "sign"),
    ("symbol", "sign"), ("map", "image"), ("law", "rule"), ("theory", "idea"),
    ("team", "group"), ("family", "group"), ("community", "group"), ("gift", "thing"),
    ("key", "thing"), ("see", "detect"), ("walk", "move"), ("circle", "line"),
    ("north", "direction"), ("south", "direction"), ("east", "direction"),
    ("west", "direction"), ("exemplifies", "elaborates"), ("corrects", "restates"),
]

PART_OF = [
    ("word", "phrase"), ("phrase", "sentence"), ("sentence", "text"), ("symbol", "word"),
    ("step", "method"), ("interface", "service"), ("wheel", "vehicle"), ("room", "house"),
    ("door", "house"), ("land", "world"), ("sea", "world"), ("head", "body"),
    ("arm", "body"), ("hand", "arm"), ("heart", "body"), ("eye", "head"), ("brain", "head"),
    ("seed", "plant"), ("leaf", "plant"), ("flower", "plant"), ("cell", "body"),
]

INVOLVES = [
    # released roots, among themselves
    ("capability", "capable"), ("lack permission", "access"), ("lack tool", "use"),
    ("lack resource", "resource"), ("lack knowledge", "learn"), ("forbid", "rule"),
    ("operation", "execute"), ("allocate", "share"), ("budget", "money"),
    ("mean", "meaning"), ("store", "memory"), ("network", "connect"), ("help", "benefit"),
    ("freeze", "cold"), ("unknown", "version"), ("corrupt", "damage"), ("missing", "find"),
    ("acknowledge", "receive"), ("feature", "version"), ("deprecate", "version"),
    ("dialect", "community"), ("descend", "parent"), ("descend", "family"),
    ("assent", "quiet"), ("assent", "wait"), ("contrasts", "compare"), ("supports move", "support"),
    ("run", "execute"), ("arrive", "approach"), ("change", "move"),
    # cognition and reasoning
    ("think", "mind"), ("comprehend", "meaning"), ("learn", "memory"), ("remember", "memory"),
    ("compare", "correspond"), ("solve", "problem"), ("compute", "value"),
    ("vote", "choose"), ("arrange", "pattern"), ("original", "copy"), ("brain", "think"),
    ("method", "step"), ("grammar", "rule"), ("grammar", "language"), ("corrects", "mistake"),
    ("clear", "comprehend"), ("lie", "true"), ("honest", "true"), ("argument", "reason"),
    ("attention", "mind"), ("context", "meaning"), ("detail", "part"),
    # speech and signs
    ("speak", "language"), ("sing", "music"), ("translate", "language"), ("discuss", "speak"),
    ("style", "language"), ("joke", "laugh"), ("proper name", "word"), ("voice", "sound"),
    ("news", "recent"), ("text", "read"), ("signal", "send"),
    # work, systems and tools
    ("work", "energy"), ("hit", "force"), ("cut", "sharp"), ("repair", "break"),
    ("draw", "line"), ("consume", "resource"), ("search", "find"), ("filter", "choose"),
    ("watch", "attention"), ("schedule", "priority"), ("control", "machine"),
    ("add", "increase"), ("encode", "format"), ("compress", "size"), ("publish", "public"),
    ("improve", "good"), ("improve", "change"), ("protect", "safe"), ("access", "use"),
    ("contain", "inside"), ("program", "execute"), ("program", "machine"),
    ("address", "locate"), ("list", "position"), ("list", "arrange"), ("image", "see"),
    ("model", "theory"), ("structure", "part"), ("structure", "arrange"),
    ("random", "pattern"), ("battery", "electricity"), ("priority", "important"),
    ("urgent", "priority"), ("progress", "step"), ("reward", "give"), ("reward", "benefit"),
    ("qualifies", "limit"), ("concludes", "argument"), ("generalises", "pattern"),
    # motion and possession
    ("turn", "direction"), ("drop", "fall"), ("fall", "gravity"), ("flow", "liquid"),
    ("fly", "air"), ("approach", "near"), ("enter", "inside"), ("return", "arrive"),
    ("carry", "move"), ("path", "move"), ("vehicle", "wheel"), ("appear", "see"),
    ("grasp", "hand"), ("pay", "money"), ("buy", "money"), ("sell", "money"),
    ("lend", "give"), ("owe", "pay"), ("hire", "pay"), ("hire", "work"),
    ("market", "trade"), ("steal", "take"), ("expensive", "cost"), ("cheap", "cost"),
    # space and quantity
    ("above", "high"), ("beside", "side"), ("between", "side"), ("near", "distance"),
    ("far", "distance"), ("left", "side"), ("right", "side"), ("divide", "part"),
    ("hide", "secret"), ("top", "high"), ("bottom", "low"), ("end", "position"),
    ("edge", "surface"), ("side", "surface"), ("big", "size"), ("small", "size"),
    ("long", "size"), ("short", "size"), ("wide", "size"), ("deep", "distance"),
    ("flat", "surface"), ("round", "circle"), ("straight", "line"), ("circle", "centre"),
    ("hole", "empty"), ("distance", "space"), ("size", "measure"), ("shape", "edge"),
    ("space", "locate"), ("direction", "move"), ("enough", "need"), ("full", "contain"),
    ("empty", "contain"), ("alone", "group"), ("amount", "count"),
    # perception
    ("see", "eye"), ("see", "light"), ("hear", "sound"), ("smell", "air"), ("taste", "food"),
    ("touch", "hand"), ("feel", "touch"), ("loud", "sound"), ("bright", "light"),
    ("dark", "light"), ("white", "colour"), ("black", "colour"), ("red", "colour"),
    ("blue", "colour"), ("green", "colour"), ("yellow", "colour"), ("smooth", "surface"),
    ("heavy", "weight"), ("wet", "liquid"), ("hot", "temperature"), ("cold", "temperature"),
    # emotions, values, social relations and law
    ("surprise", "expect"), ("luck", "random"), ("fear", "danger"), ("regret", "mistake"),
    ("proud", "praise"), ("enjoy", "play"), ("tired", "rest"), ("pain", "feel"),
    ("play", "game"), ("game", "rule"), ("game", "win"), ("fair", "rule"),
    ("safe", "danger"), ("country", "govern"), ("boundary", "region"), ("govern", "law"),
    ("custom", "community"), ("meet", "approach"), ("trust", "honest"), ("team", "work"),
    ("compete", "win"), ("fight", "attack"), ("peace", "fight"), ("gift", "give"),
    ("judge", "standard"), ("punish", "law"),
    # the physical world
    ("ground", "land"), ("river", "flow"), ("river", "water"), ("wave", "energy"),
    ("sky", "air"), ("moon", "sun"), ("star", "light"), ("wind", "air"), ("rain", "cloud"),
    ("rain", "water"), ("fire", "burn"), ("fire", "heat"), ("push", "force"),
    ("pull", "force"), ("particle", "matter"), ("atom", "matter"), ("planet", "star"),
    ("theory", "evidence"), ("nature", "world"), ("speed", "fast"), ("age", "old"),
    ("night", "dark"), ("door", "open"), ("key", "open"), ("key", "authenticate"),
    ("bridge", "path"),
    # food, the body and living things
    ("eat", "food"), ("drink", "liquid"), ("cook", "heat"), ("cook", "food"),
    ("blood", "heart"), ("breathe", "air"), ("sleep", "rest"), ("dream", "sleep"),
    ("alive", "grow"), ("strong", "force"), ("heal", "healthy"), ("medicine", "heal"),
    ("animal", "alive"), ("plant", "grow"), ("forest", "tree"), ("grow", "increase"),
    ("child", "human"), ("child", "family"), ("magic", "nature"),
    # creative work
    ("music", "sound"), ("dance", "music"), ("art", "beautiful"), ("design", "make"),
    ("design", "shape"),
    # units of measure, each with the quantity it measures
    ("degree celsius", "temperature"), ("kelvin", "temperature"), ("byte", "data"),
    ("bit", "data"), ("metre", "distance"), ("gram", "weight"), ("percent", "amount"),
    ("pascal", "pressure"), ("atmosphere", "pressure"), ("newton", "force"),
    ("joule", "energy"), ("watt", "energy"), ("volt", "electricity"),
    ("ampere", "electricity"), ("hertz", "wave"), ("litre", "size"), ("mole", "substance"),
    ("pressure", "force"),
    # roots the pairs above relate only by synonymy or antonymy
    ("examine", "learn"), ("contradict", "true"), ("cause", "change"),
    ("undermine", "evidence"), ("explain", "comprehend"), ("interpret", "meaning"),
    ("write", "text"), ("delete", "store"), ("decrease", "amount"), ("shut", "access"),
    ("possess", "thing"), ("price", "money"), ("fault", "problem"),
    ("digresses", "context"), ("analogous", "structure"), ("confine", "inside"),
    ("elegant", "simple"), ("clumsy", "complex"), ("forget", "memory"), ("test", "expect"),
    ("easy", "work"), ("difficult", "work"), ("simple", "part"), ("complex", "part"),
    ("clever", "mind"), ("foolish", "mistake"), ("describe", "detail"), ("press", "force"),
    ("produce", "work"), ("combine", "part"), ("remove", "locate"), ("expand", "size"),
    ("available", "use"), ("busy", "work"), ("risk", "lose"), ("rise", "high"),
    ("lift", "force"), ("throw", "force"), ("catch", "hand"), ("leave", "move"),
    ("follow", "path"), ("lead", "group"), ("escape", "move"), ("own", "law"),
    ("destroy", "break"), ("lose", "possess"), ("below", "low"), ("behind", "side"),
    ("in front", "side"), ("outside", "boundary"), ("gather", "group"),
    ("separate", "distance"), ("cover", "surface"), ("listen", "attention"),
    ("hard", "pressure"), ("soft", "pressure"), ("dry", "liquid"), ("clean", "surface"),
    ("dirty", "surface"), ("happy", "feel"), ("sad", "feel"), ("angry", "feel"),
    ("love", "feel"), ("hate", "feel"), ("worry", "think"), ("calm", "rest"),
    ("smile", "happy"), ("forgive", "mistake"), ("blame", "fault"), ("bad", "standard"),
    ("correct", "mistake"), ("friend", "help"), ("enemy", "attack"), ("defend", "danger"),
    ("experiment", "evidence"), ("young", "age"), ("early", "expect"), ("late", "expect"),
    ("slow", "speed"), ("ready", "work"), ("weak", "force"), ("sick", "pain"),
    ("private", "access"), ("continues", "context"),
]

# The technical terms of version 1.0: five for each of the eleven communities of the
# dialects (specification/dialects.md), in the form of `register_source.JARGON`, which
# bring each to ten and the technical terms to 110, past a hundred. Each is formed from
# roots, the long roots of lexicon 1.0 among them, and read by its composition. A
# dialect's next release holds its earlier terms with these, and a dialect that gives
# compressed forms gives one to each new term.
TERMS = [
    ("mathematics", [
        ("function", [["rule"], ["value"]]),
        ("equation", [["correspond", "nominalisation"]]),
        ("variable", [["value"], ["change"]]),
        ("sum", [["amount"], ["add"]]),
        ("graph", [["line"], ["connect"]]),
    ]),
    ("programming", [
        ("compiler", [["translate", "agent"], ["program"]]),
        ("bug", [["mistake"], ["program"]]),
        ("repository", [["store", "instrument"], ["program"]]),
        ("patch", [["repair"], ["program"]]),
        ("programming interface", [["interface"], ["program"]]),
    ]),
    ("machine-learning", [
        ("neural network", [["network"], ["brain"]]),
        ("label", [["sign"], ["data"]]),
        ("overfitting", [["learn"], ["detail"]]),
        ("embedding", [["space"], ["word"]]),
        ("benchmark", [["test"], ["model"]]),
    ]),
    ("robotics", [
        ("manipulator", [["arm"], ["robot"]]),
        ("path planning", [["design"], ["path"]]),
        ("collision", [["hit", "nominalisation"]]),
        ("charge level", [["amount"], ["battery"]]),
        ("localisation", [["locate", "process"]]),
    ]),
    ("science", [
        ("hypothesis", [["idea"], ["test"]]),
        ("control group", [["group"], ["compare"]]),
        ("measurement error", [["mistake"], ["measure"]]),
        ("peer review", [["judge"], ["document"]]),
        ("data point", [["value"], ["experiment"]]),
    ]),
    ("philosophy", [
        ("ontology", [["structure"], ["world"]]),
        ("epistemology", [["theory"], ["learn"]]),
        ("ethics", [["theory"], ["good"]]),
        ("truth", [["true", "property"]]),
        ("mentality", [["mind", "abstraction"]]),
    ]),
    ("linguistics", [
        ("syntax", [["grammar"], ["sentence"]]),
        ("phoneme", [["sound"], ["symbol"]]),
        ("semantics", [["theory"], ["meaning"]]),
        ("translation", [["translate", "result"]]),
        ("speaker", [["speak", "agent"]]),
    ]),
    ("security", [
        ("encryption", [["encode"], ["secret"]]),
        ("attacker", [["attack", "agent"]]),
        ("credential", [["key"], ["authenticate"]]),
        ("vulnerability", [["risk"], ["attack"]]),
        ("firewall", [["boundary"], ["network"]]),
    ]),
    ("databases", [
        ("table", [["list"], ["record"]]),
        ("transaction", [["step"], ["store"]]),
        ("rollback", [["return"], ["record"]]),
        ("backup", [["copy"], ["memory"]]),
        ("primary key", [["key"], ["record"]]),
    ]),
    ("planning", [
        ("timeline", [["list"], ["schedule"]]),
        ("critical path", [["path"], ["urgent"]]),
        ("roadmap", [["map"], ["progress"]]),
        ("estimate", [["compute"], ["cost"]]),
        ("contingency", [["method"], ["risk"]]),
    ]),
    ("negotiation", [
        ("reservation price", [["price"], ["limit"]]),
        ("mediator", [["help", "agent"], ["trade"]]),
        ("contract", [["document"], ["owe"]]),
        ("rapport", [["trust", "process"]]),
        ("trade-off", [["lose"], ["benefit"]]),
    ]),
]

# The derivational suffixes of lexicon 1.0, each (key, the kind of stem it takes, the sort
# it gives, its definition, the roles of its entry) in the form of
# `convention_source.SUFFIXES_ADDED`: mechanisms an agent's exchanges need that no suffix,
# compound or closed class gave. The causative adds the actor that brings its base about
# and keeps the base's other roles; the reversative and the repetitive keep their base's
# roles; the potential takes its base's undergoer; a place noun has no role.
SUFFIXES = [
    ("causative", "predicate", EV, "make the base hold or happen", [("actor", A)]),
    ("reversative", "predicate", EV, "undo the base, restoring what it changed", []),
    ("repetitive", "predicate", EV, "the base, done once more", []),
    ("potential", "predicate", ST, "be such that the base can be done to it", []),
    ("place", "predicate", PL, "the place where the base happens", []),
]

# The irregular cells of lexicon 1.0
# (specification/lexicon.md#listed-derivations-and-compounds): each (key, root, suffix,
# its constructed history), a listed derivation that means what its root and suffix
# compose and whose form is a word of its own, a suppletive cell of the root's paradigm.
# They are the five cells chosen, and their reason is a constructed historical
# development.
IRREGULAR = [
    ("consignment", "send", "undergoer",
     "Constructed history: in the oldest exchanges what was sent was named by a root of its "
     "own, said of goods and of messages alike; when the undergoer suffix came to be formed "
     "on every event, the old root kept the one cell it had always filled and fell out of "
     "use everywhere else, so that it now names only what is sent."),
    ("legible", "read", "potential",
     "Constructed history: while writing was the work of a few record keepers, that a thing "
     "could be read was said with a word of their own; when the potential suffix came into "
     "use it filled the cell of every other root, but the keepers' word was by then said in "
     "every register and kept its place."),
    ("depot", "store", "place",
     "Constructed history: an older word for a hoard came to name the place where a hoard "
     "is kept; by the time the place suffix was formed, the word had lost its first sense "
     "and was said only of the place of storing, which it still names."),
    ("fracture", "break", "nominalisation",
     "Constructed history: the reports of damage in the earliest exchanges about machines "
     "named the fact of something's breaking with a word of their own, and the word kept "
     "its place when the nominalisation came to be formed on the root for breaking."),
    ("apart", "connect", "privative",
     "Constructed history: the state of things not joined was named by a word older than "
     "joining as a common act, and the privative of the root for joining, formed later, "
     "never displaced it; the root the older word came from survives nowhere else."),
]

# The words the resemblance audit redesigned. REJECTED holds every form the audit
# rejected, which no later draw takes. A released root is deprecated in lexicon 1.0 and
# its meaning given the long code's next form, as every root of lexicon 1.0 is long; a
# dialect release formed from lexicon 1.0 deprecates each term formed on such a root, with
# its compressed form, and forms the term again on the new root, with a new compressed
# form; and a compressed form of a term lexicon 1.0's dialect releases add takes the short
# code's next form.
REJECTED = {"rokar", "rulem", "ramow", "rolol", "reyip", "radun"}
REPLACED_ROOTS = ["assent", "move"]
REDESIGNED_FORMS = [("science", "data point")]
