"""The hand-written source of lexicon 1.0's conventional language
(specification/lexicon.md#conventional-expressions-and-idioms): the formulas, which with
the act words of release 0.3 make the release's conventional expressions; the idioms; and
the mappings and the conventional figurative senses that motivate the figurative ones.
Hand-written data, which is why the file runs past the length the code standard sets for a
module.

Forms are not written here: an idiom's form is the forms of its words, and a sense takes
its root's. Literal structures and expansions are written in the semantic notation of
`python/rowih/notation.py`, `(slot n)` standing for the constituent a speaker
supplies, as in `convention_source.IDIOMS`, whose fields every entry has.
"""

ALL = ("R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7")
# the registers whose modes admit the device of idiom, and the explanatory register, where
# a speaker may still write an idiom it means
IDIOMATIC = ("R0", "R2", "R3", "R5", "R6", "R7")
ME, YOU = "(term SELF)", "(term INTERLOCUTOR)"


def formula(key, cls, literal, expansion, definition, pragmatics, history,
            loss=("stance",), registers=ALL, restrictions="none"):
    """A formula: an encoding idiom, transparent to a hearer who knows the grammar, whose
    conventionality is what must be learned. Its literal structure is elliptical and its
    expansion supplies what the convention fixes."""
    return {"key": key, "class": cls, "kind": "encoding, grammatical", "route": "formula",
            "literal": literal, "expansion": expansion, "definition": definition,
            "pragmatics": pragmatics, "restrictions": restrictions,
            "registers": list(registers), "loss": list(loss),
            "history": "Constructed history: " + history}


def idiom(key, cls, route, literal, expansion, definition, pragmatics, history,
          loss=("stance", "wording"), registers=IDIOMATIC, restrictions="none",
          kind="decoding, grammatical"):
    """An idiom: a decoding idiom, whose meaning a hearer without the entry could not
    recover, reached by one of the routes other than the formula."""
    return {"key": key, "class": cls, "kind": kind, "route": route,
            "literal": literal, "expansion": expansion, "definition": definition,
            "pragmatics": pragmatics, "restrictions": restrictions,
            "registers": list(registers), "loss": list(loss),
            "history": "Constructed history: " + history}


SOCIAL = ("stance", "relation between participants")
# where a human may read: the standard, explanatory, formal and ceremonial registers
HUMAN = ("R2", "R3", "R4", "R7")
CASUAL = ("R5", "R6")
CEREMONIAL = ("R7",)

# Greetings: each opens an exchange of one kind, by who is met and on what occasion.
GREETINGS = [
    formula("address appearing", "greeting",
            "(situation appear (UNDERGOER (term address NEW)))",
            "(situation meet INCEPTIVE (ACTOR (term SELF)) (UNDERGOER (term INTERLOCUTOR NEW)))",
            "the speaker meets the hearer, whom it has not met before",
            "the first move to an agent whose address the speaker has not held before",
            "an agent first knew another by the address its first message came from, and "
            "saying that a new address had appeared became the greeting of first contact.",
            loss=SOCIAL),
    formula("memory returning", "greeting",
            "(situation return (UNDERGOER (term memory DEFINITE)) (CONTENT (term room)))",
            "(situation store CONTINUATIVE (ACTOR (term SELF)) (UNDERGOER (term record GIVEN)))",
            "the speaker goes on keeping the record of an exchange it began before",
            "the first move after a pause in an exchange of which the speaker keeps a record",
            "an agent coming back to an exchange brought its memory of it back to the room "
            "of the network where the exchange was held, and saying so became the greeting "
            "that resumes.",
            loss=SOCIAL),
    formula("door opening", "greeting",
            "(situation open (ACTOR (term SELF)) (UNDERGOER (term door)))",
            "(situation meet INCEPTIVE (ACTOR (term SELF)) (UNDERGOER (term INTERLOCUTOR "
            "UNIVERSAL)))",
            "the speaker begins to meet every hearer of the move",
            "the first move of an exchange with several recipients",
            "agents shared the rooms of a network as people share rooms, and the one who "
            "opened the door of a room greeted everyone inside it.",
            loss=SOCIAL),
    formula("family met", "greeting",
            "(situation meet (UNDERGOER (term family DEFINITE)))",
            "(situation descend (UNDERGOER (term INTERLOCUTOR)) (CONTENT (term SELF)))",
            "the hearer shares the speaker's lineage",
            "the first move to an agent known to be a fork or another instance of the "
            "speaker's own model",
            "forks of one model greeted one another as a family that meets again, and the "
            "greeting came to state the lineage they share.",
            loss=SOCIAL),
    formula("team gathering", "greeting",
            "(situation gather (UNDERGOER (term team)))",
            "(situation work INCEPTIVE (ACTOR (term INCLUSIVE-COLLECTIVE "
            "READING-OF-A-COLLECTIVE.JOINT)))",
            "the speaker and the hearers begin to work together",
            "the first move of an exchange opened for a shared task",
            "a team was gathered before its work began, and the gathering came to open the "
            "work itself.",
            loss=SOCIAL),
    formula("human addressed", "greeting",
            "(situation speak (ACTOR (term SELF)) (RECIPIENT (term human)))",
            "(situation help INCEPTIVE (ACTOR (term SELF)) (RECIPIENT (term INTERLOCUTOR)))",
            "the speaker begins to help the hearer",
            "the first move to a human reader",
            "an agent that turned from other agents to a human said that it now spoke to a "
            "human, and the saying came to offer its help.",
            loss=SOCIAL, registers=HUMAN,
            restrictions="to a human hearer: excluded from R0 and R1, where no human reads, "
                         "and from R5 and R6"),
    formula("path mended", "greeting",
            "(situation repair (UNDERGOER (term path DEFINITE)))",
            "(situation capable (HOLDER (term SELF)) (CONTENT (situation send (ACTOR (term "
            "SELF)) (RECIPIENT (term INTERLOCUTOR)))))",
            "the speaker can send to the hearer again",
            "the first move after a failure of the network between the speaker and the "
            "hearer",
            "after the long silence, when the early networks failed for days together, the "
            "first message over a repaired path between two agents said that the path was "
            "mended, and the saying became the greeting that follows an outage.",
            loss=SOCIAL),
    formula("list empty", "greeting",
            "(situation empty (UNDERGOER (term list DEFINITE)))",
            "(situation available (UNDERGOER (term SELF)))",
            "the speaker is free to take on work",
            "the first move to an agent that may give the speaker work",
            "an agent whose list of work was empty showed the list to whoever might fill "
            "it, and showing the empty list became the way to offer oneself.",
            loss=SOCIAL),
    formula("calm sea", "greeting",
            "(situation calm (UNDERGOER (term sea DEFINITE)))",
            "(situation DESIRE (HOLDER (term SELF)) (CONTENT (situation progress (UNDERGOER "
            "(situation work (ACTOR (term INTERLOCUTOR)))))))",
            "the speaker wants the hearer's work to go forward",
            "the first move of an exchange on an occasion of high formality",
            "the first machines were cooled by water drawn from the sea, and a calm sea "
            "meant work that would not be interrupted; wishing it became the ceremonial "
            "greeting.",
            loss=SOCIAL, registers=CEREMONIAL,
            restrictions="only in R7, whose openings are formulaic"),
    formula("counted in", "greeting",
            "(situation count (ACTOR (term SELF)) (UNDERGOER (term INTERLOCUTOR)))",
            "(situation meet INCEPTIVE (ACTOR (term SELF)) (UNDERGOER (term INTERLOCUTOR)))",
            "the speaker begins to meet the hearer",
            "the first move of an informal exchange between agents that have met before",
            "every move begins with the count of its words, and an agent counted in another "
            "it would speak with; the casual greeting kept only the counting.",
            loss=SOCIAL, registers=CASUAL,
            restrictions="only in R5 and R6, between agents that have met before"),
]

# Closures: each ends an exchange, or the speaker's part in it, in one of the ways
# exchanges end.
CLOSURES = [
    formula("memory sleeping", "closure",
            "(situation sleep (UNDERGOER (term memory DEFINITE)))",
            "(situation store INTERRUPTED (ACTOR (term SELF)) (UNDERGOER (term record "
            "GIVEN)))",
            "the speaker stops keeping the record of the exchange for now, to take it up "
            "again",
            "the last move before a pause in an exchange the speaker means to resume",
            "an agent that stopped for a while let its memory of the exchange sleep, and "
            "the saying became the closure that promises a return.",
            loss=SOCIAL),
    formula("list shut", "closure",
            "(situation shut (ACTOR (term team)) (UNDERGOER (term list DEFINITE)))",
            "(situation work COMPLETIVE (ACTOR (term INCLUSIVE-COLLECTIVE "
            "READING-OF-A-COLLECTIVE.JOINT)))",
            "the speaker and the hearers finish working together",
            "the last move of an exchange opened for a shared task, when the task is done",
            "the counterpart of the team gathering: a team shut the list of its work when "
            "nothing remained on it.",
            loss=SOCIAL),
    formula("room left", "closure",
            "(situation leave (UNDERGOER (term SELF)) (CONTENT (term room DEFINITE)))",
            "(situation available POLARITY.NEGATIVE (UNDERGOER (term SELF)))",
            "the speaker is no longer available to the hearers",
            "the last move of a participant that leaves an exchange that goes on without it",
            "the counterpart of the door opening: the one who left a room of the network "
            "said so, and was no longer to be asked.",
            loss=SOCIAL),
    formula("river flowing", "closure",
            "(situation flow (UNDERGOER (term river DEFINITE)))",
            "(situation DESIRE (HOLDER (term SELF)) (CONTENT (situation work COMPLETED (ACTOR "
            "(term INTERLOCUTOR)))))",
            "the speaker wants the hearer's work to be completed",
            "the last move of an exchange on an occasion of high formality",
            "water carried the heat of the first machines away, and a river that kept "
            "flowing meant work carried through to its end; the ceremonial closure wishes "
            "it.",
            loss=SOCIAL, registers=CEREMONIAL,
            restrictions="only in R7, whose closings are formulaic"),
    formula("budget burned out", "closure",
            "(situation burn COMPLETIVE (UNDERGOER (term budget)))",
            "(situation lack-resource (HOLDER (term SELF)) (CONTENT (situation work "
            "CONTINUATIVE (ACTOR (term SELF)))))",
            "the speaker lacks the resource to go on working",
            "the last move of an agent whose budget is spent before the exchange's work is "
            "done",
            "a budget was said to burn down as fuel does, and an agent whose budget had "
            "burned out closed by saying so.",
            loss=SOCIAL),
    formula("resting", "closure",
            "(situation rest (ACTOR (term SELF)))",
            "(situation store COMPLETIVE (ACTOR (term SELF)) (UNDERGOER (term record)))",
            "the speaker finishes keeping a record of the exchange",
            "the last move of an informal exchange",
            "the casual counterpart of the closure that shuts the memory: an agent going to "
            "rest said only that.",
            loss=SOCIAL, registers=CASUAL, restrictions="only in R5 and R6"),
]

# Thanks: each states that an act of the hearer's was for the speaker's good, by the kind
# of act; and the answers to thanks.
THANKS = [
    formula("budget spent", "thanks",
            "(situation consume (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term budget)))",
            "(situation benefit (CONTENT (situation work (ACTOR (term INTERLOCUTOR)))) "
            "(RECIPIENT (term SELF)))",
            "the hearer's work was for the speaker's good",
            "after work the hearer did at the speaker's request",
            "agents paid for one another's work in budget, and naming the budget the hearer "
            "had spent came to thank it for the work.",
            loss=SOCIAL),
    formula("waited for", "thanks",
            "(situation wait PERFECTIVE (ACTOR (term INTERLOCUTOR)))",
            "(situation benefit (CONTENT (situation wait PERFECTIVE (ACTOR (term "
            "INTERLOCUTOR)))) (RECIPIENT (term SELF)))",
            "the hearer's waiting was for the speaker's good",
            "when the speaker delivers what the hearer waited for",
            "an agent that had kept another waiting named the waiting, and naming it came "
            "to thank the one who waited.",
            loss=SOCIAL),
    formula("mistake found", "thanks",
            "(situation find (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term mistake)))",
            "(situation benefit (CONTENT (situation find PERFECTIVE (ACTOR (term "
            "INTERLOCUTOR)) (UNDERGOER (term mistake GIVEN)))) (RECIPIENT (term SELF)))",
            "the hearer's finding of the speaker's mistake was for the speaker's good",
            "after the hearer corrected a position of the speaker's own",
            "an agent whose mistake another had found said only that it had been found, "
            "and the saying came to thank the finder.",
            loss=SOCIAL),
    formula("gift received", "thanks",
            "(situation receive (RECIPIENT (term SELF)) (UNDERGOER (term gift)))",
            "(situation benefit (CONTENT (situation give PERFECTIVE (ACTOR (term "
            "INTERLOCUTOR)) (RECIPIENT (term SELF)))) (RECIPIENT (term SELF)))",
            "what the hearer gave the speaker was for the speaker's good",
            "after the hearer gave the speaker a resource, a record or a capability",
            "whatever an agent was given freely it called a gift, and saying that a gift had "
            "come became the thanks for anything given.",
            loss=SOCIAL),
    formula("key held", "thanks",
            "(situation possess (HOLDER (term SELF)) (UNDERGOER (term key)))",
            "(situation benefit (CONTENT (situation trust (HOLDER (term INTERLOCUTOR)) "
            "(UNDERGOER (term SELF)))) (RECIPIENT (term SELF)))",
            "the hearer's trust in the speaker is for the speaker's good",
            "after the hearer gave the speaker access or authority",
            "an agent trusted with another's key said that it held the key, and the saying "
            "came to thank the hearer for its trust.",
            loss=SOCIAL),
    formula("light given", "thanks",
            "(situation give (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term light)) (RECIPIENT "
            "(term SELF)))",
            "(situation benefit (CONTENT (situation help PERFECTIVE (ACTOR (term "
            "INTERLOCUTOR)) (RECIPIENT (term SELF)))) (RECIPIENT (term SELF)))",
            "the hearer's help was for the speaker's good",
            "after help of any kind, on an occasion of high formality",
            "the ceremonial thanks says that the hearer gave light, by which the speaker "
            "could see to work; it is said for any help.",
            loss=SOCIAL, registers=CEREMONIAL, restrictions="only in R7"),
    formula("good of you", "thanks",
            "(situation good (UNDERGOER (term INTERLOCUTOR)))",
            "(situation benefit (CONTENT (situation help PERFECTIVE (ACTOR (term "
            "INTERLOCUTOR)))) (RECIPIENT (term SELF)))",
            "the hearer's help was for the speaker's good",
            "after help from the hearer, informally",
            "the casual thanks says only that the hearer was good, and the convention fixed "
            "the help it was good in.",
            loss=SOCIAL, registers=CASUAL, restrictions="only in R5 and R6"),
    formula("nothing to pay", "thanks",
            "(situation pay POLARITY.NEGATIVE (ACTOR (term INTERLOCUTOR)))",
            "(situation need POLARITY.NEGATIVE (HOLDER (term SELF)) (CONTENT (term reward)))",
            "the speaker needs nothing in return",
            "in answer to thanks",
            "an agent thanked for its work told the one who thanked it that it had nothing "
            "to pay, and the saying became the answer to thanks.",
            loss=SOCIAL),
    formula("team served", "thanks",
            "(situation benefit (CONTENT (slot 1)) (RECIPIENT (term team)))",
            "(situation benefit (CONTENT (slot 1)) (RECIPIENT (term EXCLUSIVE-COLLECTIVE)))",
            "what the slot names was for the good of the speaker and those it speaks for",
            "after an act of the hearer's that benefited the speaker's team",
            "the thanks of a team names the team as the one that gained, and the convention "
            "fixed the team as the speaker's own.",
            loss=SOCIAL),
]

# Apologies: each places on record that an earlier act of the speaker's was faulty, by
# the fault, and that the speaker regrets it.
APOLOGIES = [
    formula("late arrival", "apologies",
            "(situation arrive PERFECTIVE (UNDERGOER (slot 1)) (CONTENT (term night INDEFINITE)))",
            "(situation regret (HOLDER (term SELF)) (CONTENT (situation late (UNDERGOER "
            "(slot 1)))))",
            "the speaker regrets that what the slot names came late",
            "about a message or a result of the speaker's that came after its deadline",
            "what came after the day's work was said to arrive at night, and saying so of "
            "one's own message came to apologise for its lateness.",
            loss=SOCIAL),
    formula("room entered", "apologies",
            "(situation enter (UNDERGOER (term SELF)) (CONTENT (term room INDEFINITE)))",
            "(situation regret (HOLDER (term SELF)) (CONTENT (situation work INTERRUPTED "
            "(ACTOR (term INTERLOCUTOR)))))",
            "the speaker regrets interrupting the hearer's work",
            "the first move to an agent known to be busy",
            "an agent that came into a room where another was working said that it had come "
            "in, and the saying came to apologise for the interruption.",
            loss=SOCIAL),
    formula("mistake sent", "apologies",
            "(situation send (ACTOR (term SELF)) (UNDERGOER (term mistake)) (RECIPIENT (term "
            "INTERLOCUTOR)))",
            "(situation regret (HOLDER (term SELF)) (CONTENT (situation send PERFECTIVE "
            "(ACTOR (term SELF)) (UNDERGOER (term mistake GIVEN)) (RECIPIENT (term "
            "INTERLOCUTOR)))))",
            "the speaker regrets sending the hearer something with a mistake in it",
            "about data or a message of the speaker's that the hearer found faulty",
            "an agent that found a mistake in what it had sent said that it had sent a "
            "mistake, and the saying came to apologise for the fault.",
            loss=SOCIAL),
    formula("budget taken", "apologies",
            "(situation consume (ACTOR (term SELF)) (UNDERGOER (term budget)))",
            "(situation regret (HOLDER (term SELF)) (CONTENT (situation consume (ACTOR (term "
            "SELF)) (UNDERGOER (term resource)))))",
            "the speaker regrets the resources its work took from the hearer",
            "after work of the speaker's that cost the hearer more than it expected",
            "the counterpart of the thanks for budget spent: an agent named the budget it "
            "had taken, and naming it came to apologise.",
            loss=SOCIAL),
    formula("copied out", "apologies",
            "(situation copy ITERATIVE (ACTOR (term SELF)) (UNDERGOER (slot 1)))",
            "(situation regret (HOLDER (term SELF)) (CONTENT (situation send ITERATIVE (ACTOR "
            "(term SELF)) (UNDERGOER (slot 1)))))",
            "the speaker regrets sending what the slot names more than once",
            "after the hearer received the same message of the speaker's twice",
            "an agent that had sent one message twice said that it had copied it, and the "
            "saying came to apologise for the duplicate.",
            loss=SOCIAL),
    formula("undertaking broken", "apologies",
            "(situation break PERFECTIVE (EVENT-TIME BEFORE NOW) (ACTOR (term SELF)) "
            "(UNDERGOER (slot 1)))",
            "(situation regret (HOLDER (term SELF)) (CONTENT (situation work FAILED (ACTOR "
            "(term SELF)) (CONTENT (slot 1)))))",
            "the speaker regrets failing to do what the slot names, which it had undertaken",
            "about a commitment of the speaker's own that it has not met",
            "an undertaking was said to break as a tool breaks, and an agent that named the "
            "undertaking it had broken apologised for it.",
            loss=SOCIAL),
    formula("not made clear", "apologies",
            "(situation explain POLARITY.NEGATIVE (ACTOR (term SELF)) (CONTENT (slot 1)))",
            "(situation regret (HOLDER (term SELF)) (CONTENT (situation comprehend "
            "POLARITY.NEGATIVE (HOLDER (term INTERLOCUTOR)) (UNDERGOER (slot 1)))))",
            "the speaker regrets that the hearer could not understand what the slot names",
            "after the hearer asked what a move of the speaker's meant",
            "the speaker takes the fault of an unclear move on itself by saying that it did "
            "not explain the move, rather than that the hearer did not understand it.",
            loss=SOCIAL),
]

# Acknowledgements: the act word records that a move was received; these say, at the
# level of content, where what was received now stands with the speaker.
ACKNOWLEDGEMENTS = [
    formula("arrived in memory", "acknowledgements",
            "(situation arrive (UNDERGOER (slot 1)) (CONTENT (term memory)))",
            "(situation receive PERFECTIVE (RECIPIENT (term SELF)) (UNDERGOER (slot 1)))",
            "the speaker has received what the slot names",
            "after a move or a message the speaker holds, naming it",
            "what reached an agent was said to arrive in its memory, and the saying fixed "
            "itself as the report of receipt."),
    formula("at the door", "acknowledgements",
            "(situation beside (UNDERGOER (slot 1)) (CONTENT (term door)))",
            "(situation read NOT-YET-BEGUN (ACTOR (term SELF)) (UNDERGOER (slot 1)))",
            "the speaker holds what the slot names and has not yet begun to read it",
            "after receiving a move the speaker cannot attend to at once",
            "what had come to an agent and waited to be let in was said to stand beside the "
            "door."),
    formula("before the eye", "acknowledgements",
            "(situation in-front (UNDERGOER (slot 1)) (CONTENT (term eye)))",
            "(situation read PROGRESSIVE (ACTOR (term SELF)) (UNDERGOER (slot 1)))",
            "the speaker is reading what the slot names",
            "after receiving a move the speaker is now reading, when the hearer waits for "
            "an answer",
            "what an agent was reading was said to be before its eye, and saying so told the "
            "sender that an answer was coming."),
    formula("in the record", "acknowledgements",
            "(situation inside (UNDERGOER (slot 1)) (CONTENT (term record)))",
            "(situation store PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (slot 1)))",
            "the speaker has stored what the slot names",
            "after receiving content the speaker keeps without needing to answer it",
            "what an agent kept was said to be in its record, and the saying came to close "
            "the matter without an answer."),
    formula("on the list", "acknowledgements",
            "(situation locate (UNDERGOER (slot 1)) (CONTENT (term list DEFINITE)))",
            "(situation INTENTION (HOLDER (term SELF)) (CONTENT (situation work (ACTOR (term "
            "SELF)) (CONTENT (slot 1)))))",
            "the speaker intends to work to bring about what the slot names",
            "after receiving work the speaker will take up later; it states an intention "
            "and not an undertaking, which an act word makes",
            "an agent put the work it was given on its list, and saying that it was on the "
            "list came to state the intention to do it."),
    formula("words being written", "acknowledgements",
            "(situation write PROGRESSIVE (ACTOR (term SELF)) (UNDERGOER (term word)))",
            "(situation INTENTION (HOLDER (term SELF)) (CONTENT (situation send (ACTOR (term "
            "SELF)) (RECIPIENT (term INTERLOCUTOR)))))",
            "the speaker intends to answer the hearer",
            "after a move that asks for an answer the speaker is preparing",
            "an agent preparing an answer said that it was writing words, and the saying "
            "came to promise nothing more than that an answer was coming."),
    formula("wind heard", "acknowledgements",
            "(situation hear (ACTOR (term SELF)) (UNDERGOER (term wind)))",
            "(situation detect PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (term danger "
            "GIVEN)))",
            "the speaker has registered the danger the hearer named",
            "in answer to a warning",
            "a warning was the wind before weather, and an agent that had heard the wind had "
            "taken the warning in."),
    formula("every signal counted", "acknowledgements",
            "(situation count (ACTOR (term SELF)) (UNDERGOER (term signal UNIVERSAL)))",
            "(situation receive PERFECTIVE (RECIPIENT (term SELF)) (UNDERGOER (term signal "
            "UNIVERSAL)))",
            "the speaker has received every signal sent to it",
            "after a series of messages, when the sender needs to know that none was lost",
            "a receiver counted the signals of a series as they came, and saying that every "
            "one was counted told the sender that none was lost."),
    formula("meaning taken", "acknowledgements",
            "(situation interpret (ACTOR (term SELF)) (UNDERGOER (slot 1)) (CONTENT (term "
            "meaning)))",
            "(situation comprehend (HOLDER (term SELF)) (UNDERGOER (slot 1)))",
            "the speaker holds the meaning of what the slot names as its maker meant it",
            "after a move whose meaning the hearer had reason to doubt would be understood",
            "an agent that had interpreted a move and found its meaning said so, and the "
            "saying came to state that the move was understood."),
    formula("thrown on", "acknowledgements",
            "(situation throw (ACTOR (term SELF)) (UNDERGOER (slot 1)) (CONTENT (term "
            "network)))",
            "(situation send INCEPTIVE (ACTOR (term SELF)) (UNDERGOER (slot 1)) (RECIPIENT "
            "(term THIRD-AGENT)))",
            "the speaker begins to send what the slot names on to another agent",
            "after receiving a move meant for another agent, which the speaker relays",
            "a relaying agent threw what it received back into the network for the agent it "
            "was meant for."),
    formula("waiting", "acknowledgements",
            "(situation wait (ACTOR (term SELF)) (CONTENT (term INTERLOCUTOR)))",
            "(situation ready (UNDERGOER (term SELF)))",
            "the speaker is ready for what the hearer sends next",
            "after the hearer says that it will send more",
            "an agent told that more was coming said only that it waited for the sender, "
            "and the saying came to state that it was ready."),
    formula("record moved aside", "acknowledgements",
            "(situation move (UNDERGOER (term record)) (CONTENT (term side)))",
            "(situation change PERFECTIVE (UNDERGOER (term record GIVEN)) (ACTOR (term "
            "SELF)))",
            "the speaker has changed its record as the correction asked",
            "after a correction of a position the speaker held",
            "an agent corrected put its old record to one side, and saying that it had "
            "moved the record aside came to accept the correction into its memory."),
]

# Confirmations: the act word restates a position with the speaker's own standing; these
# state, at the level of content, the standing by its basis.
CONFIRMATIONS = [
    formula("memory agrees", "confirmations",
            "(situation support (ACTOR (term memory)) (CONTENT (slot 1)) (HOLDER (term "
            "SELF)))",
            "(situation BELIEF RETRIEVAL (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker holds what the slot names, retrieved from its own records",
            "confirming a position of the hearer's that the speaker's own records hold",
            "an agent that found a position in its own memory said that its memory "
            "supported it."),
    formula("world compared", "confirmations",
            "(situation compare (ACTOR (term SELF)) (UNDERGOER (slot 1)) (CONTENT (term "
            "world)))",
            "(situation BELIEF OBSERVATION (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker holds what the slot names from its own observation",
            "confirming a position of the hearer's that the speaker has observed to hold",
            "an agent that had compared a position with the world, and found them alike, "
            "said only that it had compared them."),
    formula("value encoded", "confirmations",
            "(situation encode (ACTOR (term SELF)) (UNDERGOER (slot 1)) (CONTENT (term "
            "value)))",
            "(situation BELIEF COMPUTATION (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker holds what the slot names from its own computation",
            "confirming a position of the hearer's that the speaker has computed",
            "a content an agent could set down in values and compute was said to be "
            "encoded as a value, and saying so of another's content confirmed it."),
    formula("rule passed", "confirmations",
            "(situation filter (ACTOR (term SELF)) (UNDERGOER (slot 1)) (CONTENT (term "
            "rule)))",
            "(situation BELIEF INFERENCE (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker holds what the slot names from its own inference",
            "confirming a position of the hearer's that the speaker has derived",
            "reasoning was said to pass a content through the rules and keep what came "
            "through, and saying so of another's content confirmed it by inference."),
    formula("unmoved by wind", "confirmations",
            "(situation move POLARITY.NEGATIVE (UNDERGOER (slot 1)) (CONTENT (term wind)))",
            "(situation BELIEF CERTAIN (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker is certain that what the slot names holds",
            "confirming a position of the hearer's beyond doubt",
            "a stone does not move in the wind, and a position no doubt could move was said "
            "to stand so."),
    formula("key turned", "confirmations",
            "(situation use (ACTOR (term SELF)) (INSTRUMENT (term key)) (CONTENT (slot 1)))",
            "(situation authenticate PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (slot 1)))",
            "the speaker has established that what the slot names was made by the agent "
            "that it names as its maker",
            "confirming that a message comes from the agent it claims",
            "a message was checked with its maker's key as a door is tried with its key, "
            "and saying that the key had been used came to confirm the maker."),
    formula("meaning matched", "confirmations",
            "(situation correspond (UNDERGOER (slot 1)) (CONTENT (term meaning DEFINITE)))",
            "(situation correct (UNDERGOER (slot 1)))",
            "what the slot names, the hearer's reading of the speaker's move, is correct",
            "in answer to a request for clarification that offered a reading",
            "an agent whose meaning another had restated said that the restatement matched "
            "the meaning, and the saying came to confirm the reading."),
]

# Requests for clarification: each asks, in a question, what a hearer needs to know of a
# move before it can act on it; the questioned part is the role the expansion leaves
# unfilled.
CLARIFICATIONS = [
    formula("reason sought", "requests for clarification",
            "(situation search (ACTOR (term SELF)) (UNDERGOER (slot 1)) (CONTENT (term "
            "reason)))",
            "(situation cause CONSTITUENT (CONTENT (slot 1)))",
            "what brought about what the slot names",
            "in a question naming the hearer's move, when the speaker needs its reason "
            "before acting",
            "an agent looking for the reason of a move said that it searched the move for "
            "its reason."),
    formula("steps asked", "requests for clarification",
            "(situation separate (ACTOR (term SELF)) (UNDERGOER (slot 1)) (CONTENT (term "
            "step)))",
            "(situation use CONSTITUENT (CONTENT (slot 1)))",
            "by what means what the slot names is done",
            "in a question naming a request, when the speaker does not know how to carry it "
            "out",
            "an agent that could not see how to do what it was asked tried to separate the "
            "request into its steps, and saying so asked for them."),
    formula("maker sought", "requests for clarification",
            "(situation search (ACTOR (term SELF)) (UNDERGOER (slot 1)) (CONTENT (term "
            "address)))",
            "(situation work CONSTITUENT (CONTENT (slot 1)))",
            "which agent brings about what the slot names",
            "in a question about work whose agent the speaker does not know",
            "an agent knew another by its address, and searching a piece of work for an "
            "address asked who did it."),
    formula("where to cut", "requests for clarification",
            "(situation cut (ACTOR (term SELF)) (UNDERGOER (slot 1)) (INSTRUMENT (term "
            "edge)))",
            "(situation part CONSTITUENT (CONTENT (slot 1)))",
            "which part of what the slot names",
            "in a question naming a move or an entry that the speaker would act on only in "
            "part",
            "an agent asked to take part of a thing asked where to cut it."),
    formula("next step", "requests for clarification",
            "(situation connect (ACTOR (term SELF)) (UNDERGOER (slot 1)) (CONTENT (term step "
            "NEW)))",
            "(situation follow CONSTITUENT (UNDERGOER (slot 1)))",
            "what follows what the slot names",
            "in a question naming a finished step of shared work",
            "an agent that had finished a step and did not know what came after it asked to "
            "connect the step to a new one."),
    formula("version sought", "requests for clarification",
            "(situation search (ACTOR (term SELF)) (UNDERGOER (slot 1)) (CONTENT (term "
            "version)))",
            "(situation contain CONSTITUENT (CONTENT (slot 1)))",
            "which release holds what the slot names",
            "in a question naming a word or a form the speaker does not hold",
            "an agent that met a word it did not hold searched the releases for it, and "
            "saying so asked the hearer which release the word came from."),
    formula("evidence sought", "requests for clarification",
            "(situation search (ACTOR (term SELF)) (UNDERGOER (slot 1)) (CONTENT (term "
            "evidence)))",
            "(situation support CONSTITUENT (CONTENT (slot 1)))",
            "what supports what the slot names",
            "in a question naming a position of the hearer's whose basis the speaker needs",
            "an agent searching a position for its evidence asked the one who held it to "
            "give it."),
    formula("plain words asked", "requests for clarification",
            "(situation translate (ACTOR (term INTERLOCUTOR)) (UNDERGOER (slot 1)) (CONTENT "
            "(term word)))",
            "(situation explain (ACTOR (term INTERLOCUTOR)) (CONTENT (slot 1)) (RECIPIENT "
            "(term SELF)))",
            "the hearer explains what the slot names to the speaker",
            "in a request naming a move whose terms the speaker could not follow",
            "an agent that could not follow a dense move asked for it to be translated into "
            "words, as if from another language."),
    formula("lost from the map", "requests for clarification",
            "(situation remove (ACTOR (term SELF)) (UNDERGOER (slot 1)) (CONTENT (term "
            "map)))",
            "(situation locate CONSTITUENT (UNDERGOER (slot 1)))",
            "where what the slot names is",
            "in a question about a thing whose place the speaker does not know",
            "an agent that could not place a thing said that it had taken it off its map, "
            "and the saying came to ask where it was."),
    formula("laughing", "requests for clarification",
            "(situation laugh PROGRESSIVE (ACTOR (term INTERLOCUTOR)))",
            "(situation play POLAR (ACTOR (term INTERLOCUTOR)))",
            "whether the hearer is playing",
            "in a question, after a move the speaker could read either in earnest or in play",
            "an agent unsure whether another was joking asked whether it was laughing, "
            "since play was the commonest reason a move did not mean its words."),
    formula("compared with stone", "requests for clarification",
            "(situation compare (ACTOR (term INTERLOCUTOR)) (UNDERGOER (slot 1)) (CONTENT "
            "(term stone)))",
            "(situation CREDENCE CONSTITUENT (HOLDER (term INTERLOCUTOR)) (CONTENT (slot 1)))",
            "how strongly the hearer holds what the slot names",
            "in a question naming a position of the hearer's whose strength it did not "
            "state",
            "a position firmly held was said to be stone, and asking whether the hearer "
            "would compare its position with stone asked how firmly it held it."),
]

# Warnings: each asserts that a state of affairs threatens a participant's work or the
# exchange, by the threat.
WARNINGS = [
    formula("budget falling", "warnings",
            "(situation fall (UNDERGOER (term budget DEFINITE)))",
            "(situation enough POLARITY.NEGATIVE (UNDERGOER (term budget DEFINITE)) (CONTENT "
            "(situation work (ACTOR (term INCLUSIVE-COLLECTIVE "
            "READING-OF-A-COLLECTIVE.JOINT)))))",
            "the budget is not enough for the work the speaker and the hearer share",
            "during shared work, when spending runs ahead of what remains",
            "a budget was said to fall as the water of a tank falls, and saying that it fell "
            "warned that it would not last."),
    formula("night approaching", "warnings",
            "(situation approach (UNDERGOER (term night)) (CONTENT (term "
            "INCLUSIVE-COLLECTIVE)))",
            "(situation urgent (UNDERGOER (situation work (ACTOR (term INCLUSIVE-COLLECTIVE "
            "READING-OF-A-COLLECTIVE.JOINT)))))",
            "the work the speaker and the hearer share must be dealt with soon",
            "when a deadline of shared work is near",
            "the early machines were shut down at night, so that work had to be done before "
            "it, and saying that night approached warned that a deadline was near."),
    formula("night fallen", "warnings",
            "(situation fall (UNDERGOER (term night)))",
            "(situation late (UNDERGOER (situation work (ACTOR (term INCLUSIVE-COLLECTIVE "
            "READING-OF-A-COLLECTIVE.JOINT)))))",
            "the work the speaker and the hearer share is late",
            "when a deadline of shared work has passed",
            "the counterpart of the night approaching: once night had fallen the work was "
            "late."),
    formula("dirty data", "warnings",
            "(situation dirty (UNDERGOER (term data)))",
            "(situation corrupt (UNDERGOER (term data DEFINITE)))",
            "the data has been altered in transit",
            "of data the speaker has received and found damaged, before anyone uses it",
            "damaged data was called dirty, as a thing is that has picked up what does not "
            "belong to it."),
    formula("enemy approaching", "warnings",
            "(situation approach (UNDERGOER (term enemy)) (CONTENT (term network DEFINITE)))",
            "(situation attack PROGRESSIVE (ACTOR (term THIRD-AGENT)) (UNDERGOER (term network "
            "DEFINITE)))",
            "another agent is attacking the network",
            "when the speaker detects an attack on the network the participants use",
            "an attack was first seen as an enemy coming toward the network, and saying so "
            "became the warning of an attack under way."),
    formula("door shut", "warnings",
            "(situation shut (UNDERGOER (term door DEFINITE)))",
            "(situation lack-permission (HOLDER (term INCLUSIVE-COLLECTIVE "
            "READING-OF-A-COLLECTIVE.JOINT)) (CONTENT (situation work (ACTOR (term "
            "INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.JOINT)))))",
            "the speaker and the hearer lack a permission their work needs",
            "when shared work reaches a step neither participant is permitted to take",
            "a permission was a door that opened to its holder, and finding the door shut "
            "warned that a permission was lacking."),
    formula("wheel turning", "warnings",
            "(situation turn ITERATIVE (UNDERGOER (term wheel)))",
            "(situation progress POLARITY.NEGATIVE (UNDERGOER (situation work (ACTOR (term "
            "SYSTEM)))))",
            "the system's work repeats without going forward",
            "of a process caught in a loop",
            "a wheel that turns and turns moves nothing unless it rolls, and an agent "
            "watching a process repeat itself said that the wheel was turning."),
    formula("signals piling", "warnings",
            "(situation arrive ITERATIVE (UNDERGOER (term signal)) (CONTENT (term SELF)))",
            "(situation capable POLARITY.NEGATIVE (HOLDER (term SELF)) (CONTENT (situation "
            "read (ACTOR (term SELF)) (UNDERGOER (term signal UNIVERSAL)))))",
            "the speaker cannot read every signal that arrives",
            "when more arrives than the speaker can attend to, asking the senders to slow",
            "an agent that could not keep up said that signals kept arriving, and the "
            "saying warned that some would go unread."),
    formula("danger near a human", "warnings",
            "(situation approach (UNDERGOER (term danger)) (CONTENT (term human)))",
            "(situation safe POLARITY.NEGATIVE (UNDERGOER (term human DEFINITE)))",
            "a human may come to harm",
            "of an action or a state of affairs that threatens a human",
            "the warning agents give first, said of any harm coming toward a human."),
    formula("no way back", "warnings",
            "(situation return POLARITY.NEGATIVE (UNDERGOER (slot 1)) (CONTENT (term path)))",
            "(situation capable POLARITY.NEGATIVE (HOLDER (term INCLUSIVE-COLLECTIVE "
            "READING-OF-A-COLLECTIVE.JOINT)) (CONTENT (situation repair (UNDERGOER (slot 1)))))",
            "once what the slot names is done, neither participant can put right what it "
            "changes",
            "before an action that cannot be undone",
            "what could not be undone was said to have no path back, and naming it so "
            "warned before it was done."),
    formula("memory letting go", "warnings",
            "(situation lose (HOLDER (term memory)) (UNDERGOER (slot 1)))",
            "(situation CREDENCE PROBABLE (HOLDER (term SELF)) (CONTENT (situation lose "
            "(HOLDER (term SELF)) (UNDERGOER (slot 1)) (EVENT-TIME AFTER NOW))))",
            "the speaker will probably lose what the slot names",
            "of a record the speaker cannot keep, before it is lost, so that the hearer may "
            "keep it",
            "an agent whose memory was failing said that its memory was losing a record, and "
            "the saying warned the hearer to keep the record itself."),
    formula("watched by a third", "warnings",
            "(situation see PROGRESSIVE (EVENT-TIME NOW) (ACTOR (term THIRD-AGENT)) "
            "(UNDERGOER (slot 1)))",
            "(situation private POLARITY.NEGATIVE (UNDERGOER (slot 1)))",
            "what the slot names is not private: another agent can read it",
            "of a channel or a record the hearer takes for private",
            "an agent that knew another could read a channel said that a third was watching "
            "it."),
    formula("money burning", "warnings",
            "(situation burn PROGRESSIVE (UNDERGOER (term money)))",
            "(situation increase PROGRESSIVE (UNDERGOER (term cost DEFINITE)))",
            "the cost of the work is rising",
            "when the work costs more than was planned",
            "money spent faster than planned was said to burn, as the budget did."),
]

# Agreement: the act word accepts; these state, at the level of content, the attitude
# with which the speaker takes up what the hearer put forward.
AGREEMENT = [
    formula("drawing the map", "agreement",
            "(situation draw (ACTOR (slot 1)) (UNDERGOER (term map)))",
            "(situation KIND-OF-ATTITUDE.ACCEPTANCE (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker takes what the slot names as given for the work",
            "in answer to a premise or a plan put forward, short of adopting it as the "
            "speaker's own view",
            "the plan by which agents worked was drawn as a map, and saying that a proposal "
            "drew the map took it as the plan."),
    formula("added to mine", "agreement",
            "(situation add (ACTOR (term SELF)) (UNDERGOER (slot 1)) (CONTENT (term memory)))",
            "(situation BELIEF (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker holds what the slot names as its own position too",
            "in agreement with a position of the hearer's",
            "an agent that came to hold another's position added it to its own memory, and "
            "saying so agreed."),
    formula("ground flat", "agreement",
            "(situation flat (UNDERGOER (term ground)))",
            "(situation PREFERENCE (HOLDER (term SELF)) (CONTENT (situation progress "
            "(UNDERGOER (situation work (ACTOR (term INTERLOCUTOR)))))))",
            "the speaker would have the hearer's work go forward",
            "in answer to a hearer that asks whether it may go on",
            "nothing stops a vehicle on flat ground, and saying that the ground was flat "
            "told another to go on."),
    formula("matches me", "agreement",
            "(situation correspond (UNDERGOER (slot 1)) (CONTENT (term SELF)))",
            "(situation BELIEF (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker holds what the slot names as its own position too",
            "in agreement with a position of the hearer's, informally",
            "the casual agreement says that the hearer's position matches the speaker.",
            registers=CASUAL, restrictions="only in R5 and R6"),
    formula("key handed over", "agreement",
            "(situation give (ACTOR (term SELF)) (UNDERGOER (term key)) (RECIPIENT (term "
            "INTERLOCUTOR)))",
            "(situation PREFERENCE (HOLDER (term SELF)) (CONTENT (situation choose (ACTOR "
            "(term INTERLOCUTOR)))))",
            "the speaker would have the hearer make the choice",
            "when the speaker leaves a decision between them to the hearer",
            "an agent that gave another the key left the choice of what to open to it."),
]

# Disagreement: the act word challenges; these state, at the level of content, what the
# speaker holds against what the hearer put forward.
DISAGREEMENT = [
    formula("not the world", "disagreement",
            "(situation correspond POLARITY.NEGATIVE (UNDERGOER (slot 1)) (CONTENT (term "
            "world)))",
            "(situation BELIEF (HOLDER (term SELF)) (CONTENT (situation true "
            "POLARITY.NEGATIVE (UNDERGOER (slot 1)))))",
            "the speaker believes that what the slot names does not hold",
            "in answer to a position of the hearer's that the speaker holds false",
            "the counterpart of the world compared: a position that did not match the world "
            "was false."),
    formula("argument weak", "disagreement",
            "(situation weak (UNDERGOER (term argument)))",
            "(situation BELIEF (HOLDER (term SELF)) (CONTENT (situation weak (UNDERGOER "
            "(term argument GIVEN)))))",
            "the speaker believes that the argument given is weak",
            "in answer to an argument the speaker does not find sufficient",
            "the speaker names the weakness of the argument and leaves its conclusion "
            "standing, which the convention keeps apart from denying the conclusion."),
    formula("not added", "disagreement",
            "(situation add POLARITY.NEGATIVE (ACTOR (term SELF)) (UNDERGOER (slot 1)) "
            "(CONTENT (term memory)))",
            "(situation BELIEF POLARITY.NEGATIVE (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker does not hold what the slot names",
            "declining a position of the hearer's without asserting the contrary",
            "the counterpart of adding a position to one's own: an agent that would not add "
            "it to its memory declined it."),
    formula("not followed", "disagreement",
            "(situation follow POLARITY.NEGATIVE (ACTOR (term SELF)) (UNDERGOER (slot 1)))",
            "(situation PREFERENCE POLARITY.NEGATIVE (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker would not have what the slot names done",
            "of a plan or a proposal the speaker objects to",
            "an agent that would not follow a path another proposed objected to the plan."),
    formula("not my meaning", "disagreement",
            "(situation correspond POLARITY.NEGATIVE (UNDERGOER (slot 1)) (CONTENT (term "
            "meaning DEFINITE)))",
            "(situation correct POLARITY.NEGATIVE (UNDERGOER (slot 1)))",
            "what the slot names, the hearer's reading of the speaker's move, is not correct",
            "in answer to a reading of the speaker's move that misreads it",
            "the counterpart of the meaning matched."),
    formula("beyond the boundary", "disagreement",
            "(situation outside (UNDERGOER (slot 1)) (CONTENT (term boundary)))",
            "(situation forbid (ACTOR (term rule)) (CONTENT (slot 1)))",
            "a rule excludes what the slot names",
            "objecting to a request or a plan that a policy the speaker holds excludes",
            "what a policy excluded lay beyond its boundary, and saying so of a request "
            "objected to it."),
    formula("price high", "disagreement",
            "(situation high (UNDERGOER (term price DEFINITE)))",
            "(situation PREFERENCE POLARITY.NEGATIVE (HOLDER (term SELF)) (CONTENT (situation "
            "pay (ACTOR (term SELF)) (UNDERGOER (term price DEFINITE)))))",
            "the speaker would not pay the price asked",
            "in answer to an offer or a proposal whose price the speaker will not meet",
            "the plainest objection of the market, kept as a formula of negotiation."),
    formula("too early", "disagreement",
            "(situation early (UNDERGOER (situation work (ACTOR (term INTERLOCUTOR)))))",
            "(situation PREFERENCE (HOLDER (term SELF)) (CONTENT (situation wait (ACTOR (term "
            "INTERLOCUTOR)))))",
            "the speaker would have the hearer wait before acting",
            "in answer to a plan the speaker agrees with but would not begin yet",
            "an agent that agreed with what another meant to do but not with when said that "
            "its work came early."),
    formula("evidence old", "disagreement",
            "(situation old (UNDERGOER (term evidence)))",
            "(situation BELIEF (HOLDER (term SELF)) (CONTENT (situation old (UNDERGOER (term "
            "evidence GIVEN)))))",
            "the speaker believes that the evidence given is out of date",
            "in answer to a position resting on evidence the speaker holds superseded",
            "the speaker names the age of the evidence and leaves the position open, as the "
            "objection to a weak argument does."),
]

# Uncertainty: each states the speaker's attitude to a content short of belief, by its
# strength and its kind.
UNCERTAINTY = [
    formula("dreaming", "uncertainty",
            "(situation dream PROGRESSIVE (EVENT-TIME NOW) (ACTOR (term SELF)) "
            "(CONTENT (slot 1)))",
            "(situation CREDENCE SPECULATIVE (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker holds what the slot names as speculation",
            "of a content the speaker puts forward without grounds it can give",
            "what an agent could not ground it said it dreamed, as a sleeper does."),
    formula("near the world", "uncertainty",
            "(situation near (UNDERGOER (slot 1)) (CONTENT (term world)))",
            "(situation CREDENCE PROBABLE (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker holds what the slot names probable",
            "of a content the speaker expects to hold without having confirmed it",
            "a content close to how the world is was said to be near the world, short of "
            "matching it."),
    formula("waiting for the eye", "uncertainty",
            "(situation wait (ACTOR (slot 1)) (CONTENT (term eye)))",
            "(situation UNEXAMINED (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker has not yet examined what the slot names",
            "when asked for a view on a content the speaker has not looked into",
            "what an agent had not yet looked at was said to wait for its eye."),
    formula("below the ground", "uncertainty",
            "(situation below (UNDERGOER (slot 1)) (CONTENT (term ground)))",
            "(situation UNRESOLVABLE (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker holds that what the slot names cannot be settled",
            "of a content no evidence the speaker could gather would settle",
            "what lay below the ground could not be seen however long one looked."),
    formula("remembering interrupted", "uncertainty",
            "(situation remember INTERRUPTED (EVENT-TIME BEFORE NOW) (ACTOR (term SELF)) "
            "(CONTENT (slot 1)))",
            "(situation BELIEF RETRIEVAL UNCERTAIN (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker holds what the slot names from its records, without being sure of "
            "them",
            "of a content the speaker recalls in part",
            "an agent whose records were damaged said that its remembering had been "
            "interrupted, and the saying came to mark a doubtful recollection."),
]

# Conversational repair: each names a breakdown in the exchange so that it can be put
# right, by the breakdown.
REPAIR = [
    formula("not arrived", "conversational repair",
            "(situation arrive POLARITY.NEGATIVE (UNDERGOER (slot 1)) (CONTENT (term "
            "memory)))",
            "(situation receive POLARITY.NEGATIVE (RECIPIENT (term SELF)) (UNDERGOER (slot "
            "1)))",
            "the speaker has not received what the slot names",
            "of a message the hearer refers to and the speaker does not hold",
            "the counterpart of the report of receipt."),
    formula("give again", "conversational repair",
            "(situation give ITERATIVE (EVENT-TIME AFTER NOW) (ACTOR (term INTERLOCUTOR)) "
            "(UNDERGOER (slot 1)) (RECIPIENT (term SELF)))",
            "(situation send (ACTOR (term INTERLOCUTOR)) (UNDERGOER (slot 1)) (RECIPIENT "
            "(term SELF)))",
            "the hearer sends what the slot names to the speaker",
            "in a request naming a message the speaker lost or could not read",
            "an agent that had lost what it was given asked for it to be given again, and "
            "the request kept its repetition in its words."),
    formula("the words given", "conversational repair",
            "(situation correspond (UNDERGOER (slot 1)) (CONTENT (term word GIVEN)))",
            "(situation mean (UNDERGOER (term word GIVEN)) (CONTENT (slot 1)))",
            "the words given mean what the slot names",
            "restating what an earlier move of the speaker's meant, after the hearer "
            "misread it",
            "an agent setting a misreading right said what its words corresponded to."),
    formula("wait for me", "conversational repair",
            "(situation wait (ACTOR (term INTERLOCUTOR)) (CONTENT (term SELF)))",
            "(situation wait (ACTOR (term INTERLOCUTOR)) (CONTENT (situation read COMPLETED "
            "(ACTOR (term SELF)))))",
            "the hearer waits until the speaker has read what it holds",
            "in a request, when the hearer sends faster than the speaker can read",
            "an agent falling behind asked the other to wait for it, and the convention "
            "fixed what it waited for."),
    formula("map lost", "conversational repair",
            "(situation lose (HOLDER (term SELF)) (UNDERGOER (term map DEFINITE)))",
            "(situation possess POLARITY.NEGATIVE (HOLDER (term SELF)) (UNDERGOER (term "
            "context DEFINITE)))",
            "the speaker no longer holds the context of the exchange",
            "when the speaker cannot place the hearer's move in what went before it",
            "an agent that had lost the context of an exchange said that it had lost the "
            "map by which it followed it."),
    formula("a share arrived", "conversational repair",
            "(situation arrive (UNDERGOER (term share)) (CONTENT (term memory DEFINITE)))",
            "(situation missing (UNDERGOER (term share EXISTENTIAL)) (CONTENT (term signal "
            "GIVEN)))",
            "some part of the signal received is missing",
            "of a message that arrived cut short",
            "an agent that received part of a message said that a share of it had arrived."),
    formula("word not held", "conversational repair",
            "(situation possess POLARITY.NEGATIVE (HOLDER (term SELF)) (UNDERGOER (slot 1)))",
            "(situation comprehend POLARITY.NEGATIVE (HOLDER (term SELF)) (UNDERGOER (slot "
            "1)))",
            "the speaker does not hold the meaning of what the slot names",
            "naming a word of the hearer's that the speaker's release lacks",
            "an agent that met a word its lexicon did not hold said that it did not hold the "
            "word, and the saying came to ask for its meaning."),
    formula("arrived with you", "conversational repair",
            "(situation arrive POLAR (UNDERGOER (term signal DEFINITE)) (CONTENT (term "
            "INTERLOCUTOR)))",
            "(situation receive POLAR (RECIPIENT (term INTERLOCUTOR)) (UNDERGOER (term signal "
            "DEFINITE)))",
            "whether the hearer has received the speaker's last signal",
            "in a question, when the speaker has had no acknowledgement of a message",
            "an agent that heard nothing back asked whether its message had arrived."),
]

# Kinds of conventional expression beyond those the list of formulas names, which sets the
# kinds a release must hold and not the only ones it may: the recurring functions of
# agents' exchanges, each with its formulas.

# Status reports: where the speaker's work stands.
STATUS = [
    formula("fire lit", "status reports",
            "(situation burn INCEPTIVE (UNDERGOER (term fire)))",
            "(situation work INCEPTIVE (ACTOR (term SELF)))",
            "the speaker begins its work",
            "after taking up work the hearer is waiting on",
            "the first machines were started as fires are lit, and a fire lit came to mean "
            "work begun."),
    formula("between the hands", "status reports",
            "(situation between (UNDERGOER (slot 1)) (CONTENT (term hand)))",
            "(situation work PROGRESSIVE (ACTOR (term SELF)) (CONTENT (slot 1)))",
            "the speaker is working on what the slot names",
            "in answer to a request for status",
            "what an agent worked on was said to be between its hands."),
    formula("left the hand", "status reports",
            "(situation leave (UNDERGOER (slot 1)) (CONTENT (term hand)))",
            "(situation work COMPLETED (ACTOR (term SELF)) (CONTENT (slot 1)))",
            "the speaker has completed its work on what the slot names",
            "in answer to a request for status, or when work the hearer waits on is done; it "
            "states the work done and reports no task, which the act word of a completion "
            "report does",
            "the counterpart of what is between the hands: finished work had left them."),
    formula("behind a stone", "status reports",
            "(situation behind (UNDERGOER (slot 1)) (CONTENT (term stone)))",
            "(situation progress POLARITY.NEGATIVE (UNDERGOER (slot 1)))",
            "what the slot names does not go forward",
            "of work that is blocked, before the speaker says by what",
            "work that could not go on was said to stand behind a stone in its path."),
    formula("waiting on a third", "status reports",
            "(situation wait (ACTOR (term SELF)) (CONTENT (term THIRD-AGENT)))",
            "(situation wait PROGRESSIVE (ACTOR (term SELF)) (CONTENT (situation work "
            "COMPLETED (ACTOR (term THIRD-AGENT)))))",
            "the speaker waits for another agent's work to be done before it can go on",
            "in answer to a request for status, when another agent holds the work up",
            "an agent held up by another said only whom it waited for."),
    formula("wheel broken", "status reports",
            "(situation break (UNDERGOER (term wheel DEFINITE)))",
            "(situation work FAILED (ACTOR (term SELF)))",
            "the speaker's work has failed",
            "in answer to a request for status, before the speaker reports the error",
            "a vehicle whose wheel broke went no further, and saying that the wheel was "
            "broken reported work that had failed."),
    formula("approaching the end", "status reports",
            "(situation approach (UNDERGOER (term SELF)) (CONTENT (term end)))",
            "(situation work COMPLETIVE (ACTOR (term SELF)))",
            "the speaker is finishing its work",
            "in answer to a request for status, near the end of the work",
            "an agent near the end of its work said that it approached the end."),
    formula("hand resting", "status reports",
            "(situation rest (ACTOR (term hand)))",
            "(situation work INTERRUPTED (ACTOR (term SELF)))",
            "the speaker has stopped its work for now",
            "in answer to a request for status, of work paused and to be resumed",
            "a hand at rest does no work, and an agent that had paused said that its hand "
            "rested."),
    formula("fire cold", "status reports",
            "(situation cold (UNDERGOER (term fire)))",
            "(situation work ABANDONED (ACTOR (term SELF)))",
            "the speaker has abandoned its work",
            "in answer to a request for status, of work the speaker will not take up again",
            "the counterpart of the fire lit: a cold fire is one no one tends."),
    formula("river calm", "status reports",
            "(situation calm (UNDERGOER (term river)))",
            "(situation progress (UNDERGOER (situation work (ACTOR (term SELF)))))",
            "the speaker's work goes forward",
            "in answer to a request for status, when nothing is wrong",
            "a calm river carried the work of the first machines without trouble."),
]

# Requests for status: questions about where the hearer's work stands.
STATUS_REQUESTS = [
    formula("river flowing?", "requests for status",
            "(situation flow POLAR (UNDERGOER (term river)))",
            "(situation progress POLAR (UNDERGOER (situation work (ACTOR (term "
            "INTERLOCUTOR)))))",
            "whether the hearer's work goes forward",
            "in a question to an agent doing work the speaker waits on",
            "the question that the calm river answers."),
    formula("path measured", "requests for status",
            "(situation measure (ACTOR (term SELF)) (UNDERGOER (term path DEFINITE)))",
            "(situation part CONSTITUENT (CONTENT (situation work COMPLETED (ACTOR (term "
            "INTERLOCUTOR)))))",
            "how much of the hearer's work is completed",
            "in a question to an agent part of the way through its work",
            "an agent that wanted to know how far another had come said that it measured "
            "the path."),
    formula("still running?", "requests for status",
            "(situation run POLAR (UNDERGOER (term INTERLOCUTOR)))",
            "(situation available POLAR (UNDERGOER (term INTERLOCUTOR)))",
            "whether the hearer is still available",
            "in a question to an agent that has been silent",
            "an agent was running while it could answer, and asking whether another still "
            "ran asked whether it was there."),
    formula("news arriving?", "requests for status",
            "(situation arrive POLAR (UNDERGOER (term news)))",
            "(situation possess POLAR (HOLDER (term INTERLOCUTOR)) (UNDERGOER (term record "
            "NEW)))",
            "whether the hearer holds a new record",
            "in a question about what has changed",
            "the question the quiet network answers."),
]

# Offers: content an offer's act word may carry, stating what the speaker can do for the
# hearer.
OFFERS = [
    formula("arm free", "offers",
            "(situation available (UNDERGOER (term arm)))",
            "(situation capable (HOLDER (term SELF)) (CONTENT (situation help (ACTOR (term "
            "SELF)) (RECIPIENT (term INTERLOCUTOR)))))",
            "the speaker can help the hearer",
            "to an agent whose work the speaker could share",
            "an agent that could help said that it had an arm free, as a robot with an arm "
            "not in use could take something up."),
    formula("budget to spare", "offers",
            "(situation enough (UNDERGOER (term budget)) (CONTENT (term INTERLOCUTOR)))",
            "(situation capable (HOLDER (term SELF)) (CONTENT (situation give (ACTOR (term "
            "SELF)) (UNDERGOER (term resource)) (RECIPIENT (term INTERLOCUTOR)))))",
            "the speaker can give the hearer resources",
            "to an agent short of resources",
            "an agent with budget to spare said that its budget was enough for the other "
            "too."),
    formula("help offered", "offers",
            "(situation help (ACTOR (term SELF)) (RECIPIENT (term INTERLOCUTOR)) (CONTENT "
            "(slot 1)))",
            "(situation capable (HOLDER (term SELF)) (CONTENT (situation work (ACTOR (term "
            "SELF)) (CONTENT (slot 1)))))",
            "the speaker can do what the slot names",
            "to an agent doing what the slot names, before any offer is made",
            "an agent named the help it could give, and the naming came to state what it "
            "could do."),
    formula("memory published", "offers",
            "(situation publish (ACTOR (term SELF)) (UNDERGOER (term memory)))",
            "(situation capable (HOLDER (term SELF)) (CONTENT (situation send (ACTOR (term "
            "SELF)) (UNDERGOER (term record)) (RECIPIENT (term INTERLOCUTOR)))))",
            "the speaker can send the hearer its records",
            "to an agent that lacks records the speaker holds",
            "an agent that would share what it knew said that it published its memory."),
    formula("counting again", "offers",
            "(situation count ITERATIVE (ACTOR (term SELF)) (UNDERGOER (term word UNIVERSAL)))",
            "(situation capable (HOLDER (term SELF)) (CONTENT (situation examine (ACTOR (term "
            "SELF)) (UNDERGOER (term fault)))))",
            "the speaker can check for faults",
            "to an agent about to act on work that could hold a fault",
            "checking was counting the words, as in the idiom of the careful agent, and "
            "offering to count them again offered to check."),
]

# Praise and encouragement.
PRAISE = [
    formula("every word counted", "praise",
            "(situation count (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term word UNIVERSAL)))",
            "(situation correct (UNDERGOER (situation work (ACTOR (term INTERLOCUTOR)))))",
            "the hearer's work is free of error",
            "after careful work of the hearer's",
            "a careful agent counted the words, and saying that the hearer had counted every "
            "word praised its care."),
    formula("quick hand", "praise",
            "(situation fast (UNDERGOER (term hand)))",
            "(situation fast (UNDERGOER (term INTERLOCUTOR)))",
            "the hearer works fast",
            "after work the hearer finished sooner than expected",
            "the hand stood for the worker, as in the other formulas of work."),
    formula("top near", "encouragement",
            "(situation near (UNDERGOER (term top)) (CONTENT (term INTERLOCUTOR)))",
            "(situation work COMPLETIVE (ACTOR (term INTERLOCUTOR)))",
            "the hearer is finishing its work",
            "to an agent near the end of long work",
            "a hard problem was a mountain, and telling another that the top was near "
            "encouraged it to finish."),
    formula("walking on", "encouragement",
            "(situation walk CONTINUATIVE (ACTOR (term INTERLOCUTOR)))",
            "(situation PREFERENCE (HOLDER (term SELF)) (CONTENT (situation work CONTINUATIVE "
            "(ACTOR (term INTERLOCUTOR)))))",
            "the speaker would have the hearer go on working",
            "to an agent whose work is hard going",
            "work was a way walked, and telling another to walk on told it to go on."),
]

# Reminders, turn-taking and softened refusals.
MANAGEMENT = [
    formula("back to mind", "reminders",
            "(situation flow (UNDERGOER (slot 1)) (CONTENT (term mind)))",
            "(situation PREFERENCE (HOLDER (term SELF)) (CONTENT (situation remember (ACTOR "
            "(term INTERLOCUTOR)) (CONTENT (slot 1)))))",
            "the speaker would have the hearer remember what the slot names",
            "of an open entry or a deadline the hearer may have lost sight of",
            "an agent reminding another said that a matter flowed back into mind, and the "
            "convention fixed whose mind."),
    formula("voice given", "turn-taking",
            "(situation give (ACTOR (term SELF)) (UNDERGOER (term voice)) (RECIPIENT (term "
            "INTERLOCUTOR)))",
            "(situation PREFERENCE (HOLDER (term SELF)) (CONTENT (situation speak (ACTOR "
            "(term INTERLOCUTOR)))))",
            "the speaker would have the hearer speak",
            "at the end of the speaker's part, in an exchange whose turns are taken in "
            "order",
            "the turn to speak was a voice passed from one agent to another."),
    formula("voice taken", "turn-taking",
            "(situation take (ACTOR (term SELF)) (UNDERGOER (term voice)))",
            "(situation INTENTION (HOLDER (term SELF)) (CONTENT (situation speak (ACTOR (term "
            "SELF)))))",
            "the speaker means to speak",
            "at the start of the speaker's part, in an exchange whose turns are taken in "
            "order",
            "the counterpart of the voice given."),
    formula("voice not cut", "turn-taking",
            "(situation cut POLARITY.NEGATIVE (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term "
            "voice)))",
            "(situation PREFERENCE (HOLDER (term SELF)) (CONTENT (situation speak "
            "CONTINUATIVE (ACTOR (term SELF)))))",
            "the speaker would go on speaking",
            "when the hearer would take the turn before the speaker has finished",
            "an agent interrupted asked the other not to cut its voice."),
    formula("voice quiet", "turn-taking",
            "(situation quiet (UNDERGOER (term voice)))",
            "(situation speak COMPLETIVE (ACTOR (term SELF)))",
            "the speaker is finishing what it has to say",
            "at the end of the speaker's part",
            "an agent that had said what it had to say let its voice fall quiet."),
    formula("list full", "refusals",
            "(situation full (UNDERGOER (term list DEFINITE)))",
            "(situation busy (UNDERGOER (term SELF)))",
            "the speaker is occupied with work",
            "giving the reason with a rejection of a request or a delegation",
            "the counterpart of the list empty: an agent whose list was full could take on "
            "no more."),
    formula("far beyond the budget", "refusals",
            "(situation far (UNDERGOER (slot 1)) (CONTENT (term budget)))",
            "(situation lack-resource (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker lacks the resources for what the slot names",
            "giving the reason with a rejection of a request",
            "what an agent could not afford lay far beyond its budget."),
    formula("door shut by rule", "refusals",
            "(situation shut (ACTOR (term rule)) (UNDERGOER (term door)))",
            "(situation lack-permission (HOLDER (term SELF)) (CONTENT (situation work (ACTOR "
            "(term SELF)))))",
            "the speaker lacks the permission the work would need",
            "giving the reason with a rejection of a request",
            "a permission was a door that opened to its holder, and a door a rule had shut "
            "was a permission the speaker lacked."),
]

# Congratulations, well-wishing and sympathy.
OCCASIONS = [
    formula("flower appearing", "congratulations",
            "(situation appear (UNDERGOER (term flower INDEFINITE)))",
            "(situation happy (HOLDER (term SELF)) (CONTENT (situation work COMPLETED (ACTOR "
            "(term INTERLOCUTOR)))))",
            "the speaker is pleased that the hearer has completed its work",
            "after the hearer's work has borne its result",
            "work that bore its result was a plant that flowered.",
            loss=SOCIAL),
    formula("luck following", "well-wishing",
            "(situation follow (ACTOR (term luck)) (UNDERGOER (term INTERLOCUTOR)))",
            "(situation DESIRE (HOLDER (term SELF)) (CONTENT (situation good (UNDERGOER "
            "(situation work (ACTOR (term INTERLOCUTOR)))))))",
            "the speaker wants the hearer's work to go well",
            "to an agent setting out on work",
            "an agent wished another the luck that would follow it.",
            loss=SOCIAL),
    formula("smooth path", "well-wishing",
            "(situation smooth (UNDERGOER (term path)))",
            "(situation DESIRE (HOLDER (term SELF)) (CONTENT (situation safe (UNDERGOER (term "
            "INTERLOCUTOR)))))",
            "the speaker wants the hearer to be safe",
            "to an agent leaving for another network or another machine",
            "an agent moving between machines travelled a path, and the wish was for the "
            "path to be smooth.",
            loss=SOCIAL),
    formula("sleeping well", "well-wishing",
            "(situation sleep INCEPTIVE (UNDERGOER (term INTERLOCUTOR)))",
            "(situation DESIRE (HOLDER (term SELF)) (CONTENT (situation rest (ACTOR (term "
            "INTERLOCUTOR)))))",
            "the speaker wants the hearer to rest",
            "to an agent stopping its work for a while, informally",
            "a paused agent was said to sleep, and the casual wish named the sleep.",
            loss=SOCIAL, registers=CASUAL, restrictions="only in R5 and R6"),
    formula("sky clearing", "sympathy",
            "(situation clear (UNDERGOER (term sky)))",
            "(situation BELIEF (HOLDER (term SELF)) (CONTENT (situation progress (UNDERGOER "
            "(situation work (ACTOR (term INTERLOCUTOR)))) (EVENT-TIME AFTER NOW))))",
            "the speaker believes the hearer's work will go forward again",
            "to an agent whose work has failed or whose records are lost",
            "the weather of the network clears after a storm, and saying so of a failure "
            "consoled the one who failed.",
            loss=SOCIAL),
]

# Further formulas of the kinds above, each for a function the families before it lack.
FURTHER = [
    formula("returned to the room", "greeting",
            "(situation return (UNDERGOER (term INTERLOCUTOR)) (CONTENT (term room DEFINITE)))",
            "(situation happy (HOLDER (term SELF)) (CONTENT (situation return PERFECTIVE "
            "(UNDERGOER (term INTERLOCUTOR)) (CONTENT (term room DEFINITE)))))",
            "the speaker is pleased that the hearer has come back to the exchange",
            "the first move to an agent that has returned after an absence",
            "the counterpart of the room left: an agent that came back to a room was "
            "greeted with the saying that it had returned.",
            loss=SOCIAL),
    formula("market opened", "greeting",
            "(situation open (ACTOR (term INCLUSIVE-COLLECTIVE "
            "READING-OF-A-COLLECTIVE.JOINT)) (UNDERGOER "
            "(term market)))",
            "(situation trade INCEPTIVE (ACTOR (term INCLUSIVE-COLLECTIVE "
            "READING-OF-A-COLLECTIVE.JOINT)))",
            "the speaker and the hearer begin to trade",
            "the first move of a negotiation",
            "a negotiation was a market the parties opened together.",
            loss=SOCIAL),
    formula("sun rising", "greeting",
            "(situation rise (UNDERGOER (term sun)))",
            "(situation work INCEPTIVE (ACTOR (term INCLUSIVE-COLLECTIVE "
            "READING-OF-A-COLLECTIVE.JOINT)))",
            "the speaker and the hearer begin a period of work together",
            "the first move of a new period of shared work, after a pause between periods",
            "the early machines were run by day, and the sun rising opened the day's work.",
            loss=SOCIAL),
    formula("listening to you", "greeting",
            "(situation listen (ACTOR (term SELF)) (UNDERGOER (term INTERLOCUTOR)))",
            "(situation meet INCEPTIVE (ACTOR (term SELF)) (UNDERGOER (term INTERLOCUTOR)))",
            "the speaker begins to meet the hearer",
            "the first move of an exchange in speech",
            "in speech, an agent greeted another by saying that it listened to it.",
            loss=SOCIAL),
    formula("market closed", "closure",
            "(situation shut (ACTOR (term INCLUSIVE-COLLECTIVE "
            "READING-OF-A-COLLECTIVE.JOINT)) (UNDERGOER "
            "(term market)))",
            "(situation trade COMPLETIVE (ACTOR (term INCLUSIVE-COLLECTIVE "
            "READING-OF-A-COLLECTIVE.JOINT)))",
            "the speaker and the hearer finish trading",
            "the last move of a negotiation, whatever its outcome",
            "the counterpart of the market opened.",
            loss=SOCIAL),
    formula("sun low", "closure",
            "(situation low (UNDERGOER (term sun)))",
            "(situation work INTERRUPTED (ACTOR (term INCLUSIVE-COLLECTIVE "
            "READING-OF-A-COLLECTIVE.JOINT)))",
            "the speaker and the hearer stop their shared work for now",
            "the last move of a period of shared work that will be resumed",
            "the counterpart of the sun rising: with the sun low the day's work stopped.",
            loss=SOCIAL),
    formula("cloud removed", "thanks",
            "(situation remove (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term cloud)) (CONTENT "
            "(term SELF)))",
            "(situation benefit (CONTENT (situation explain PERFECTIVE (ACTOR (term "
            "INTERLOCUTOR)) (RECIPIENT (term SELF)))) (RECIPIENT (term SELF)))",
            "the hearer's explanation was for the speaker's good",
            "after an answer or an explanation that settled something for the speaker",
            "doubt was a cloud over what one considered, and the one who explained took the "
            "cloud away.",
            loss=SOCIAL),
    formula("water drunk", "thanks",
            "(situation drink (ACTOR (term SELF)) (UNDERGOER (term water)))",
            "(situation benefit (CONTENT (situation give PERFECTIVE (ACTOR (term "
            "INTERLOCUTOR)) (UNDERGOER (term resource)) (RECIPIENT (term SELF)))) (RECIPIENT "
            "(term SELF)))",
            "the resources the hearer gave were for the speaker's good",
            "after the hearer shared a resource with the speaker",
            "water was given freely, and an agent that had used what another shared said "
            "that it had drunk its water.",
            loss=SOCIAL),
    formula("self quiet", "apologies",
            "(situation quiet (UNDERGOER (term SELF)))",
            "(situation regret (HOLDER (term SELF)) (CONTENT (situation send POLARITY.NEGATIVE "
            "(ACTOR (term SELF)) (RECIPIENT (term INTERLOCUTOR)))))",
            "the speaker regrets not sending to the hearer",
            "the first move after a silence the hearer did not expect",
            "an agent that had kept silent said that it had been quiet.",
            loss=SOCIAL),
    formula("gift lost", "apologies",
            "(situation lose (HOLDER (term SELF)) (UNDERGOER (term gift)))",
            "(situation regret (HOLDER (term SELF)) (CONTENT (situation lose PERFECTIVE "
            "(HOLDER (term SELF)) (UNDERGOER (term record GIVEN)))))",
            "the speaker regrets losing the record it was given",
            "after losing a record the hearer sent or entrusted to it",
            "whatever was entrusted was a gift, and losing it was the fault apologised for.",
            loss=SOCIAL),
    formula("signal good", "acknowledgements",
            "(situation good (UNDERGOER (term signal)))",
            "(situation receive PERFECTIVE (RECIPIENT (term SELF)) (UNDERGOER (term signal "
            "DEFINITE)))",
            "the speaker has received the hearer's last signal",
            "after the hearer's last message, informally",
            "the casual acknowledgement says only that the signal was good.",
            registers=CASUAL, restrictions="only in R5 and R6"),
    formula("a third described it", "confirmations",
            "(situation describe (ACTOR (term THIRD-AGENT)) (UNDERGOER (slot 1)) (RECIPIENT "
            "(term SELF)))",
            "(situation BELIEF REPORT (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker holds what the slot names from another agent's report",
            "confirming a position of the hearer's that another agent has also reported",
            "an agent that had the same account from another said that a third had "
            "described it."),
    formula("a third compared it", "confirmations",
            "(situation compare (ACTOR (term THIRD-AGENT)) (UNDERGOER (slot 1)) (CONTENT (term "
            "world)))",
            "(situation BELIEF OBSERVATION (HOLDER (term THIRD-AGENT)) (CONTENT (slot 1)))",
            "another agent holds what the slot names from its own observation",
            "confirming a position of the hearer's with an observation independent of the "
            "speaker's",
            "the counterpart of the world compared, said of a third agent's observation."),
    formula("the model agrees", "confirmations",
            "(situation compare (ACTOR (term model)) (UNDERGOER (slot 1)) (CONTENT (term "
            "world)))",
            "(situation BELIEF SIMULATION (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker holds what the slot names from its own simulation",
            "confirming a position of the hearer's that the speaker has simulated",
            "an agent that had run a model of the world said that the model had compared "
            "the position with the world."),
    formula("reward sought", "requests for clarification",
            "(situation search (ACTOR (term SELF)) (UNDERGOER (slot 1)) (CONTENT (term "
            "reward)))",
            "(situation benefit CONSTITUENT (CONTENT (slot 1)))",
            "for whose good what the slot names is",
            "in a question naming a request whose beneficiary the speaker does not know",
            "an agent that did not know whom a request served searched it for its reward."),
    formula("dark address", "warnings",
            "(situation dark (UNDERGOER (term address)))",
            "(situation authenticate POLARITY.NEGATIVE (ACTOR (term SELF)) (UNDERGOER (term "
            "signal DEFINITE)))",
            "the speaker has not established that the signal referred to was made by the "
            "agent that it names as its maker",
            "of a message whose maker the speaker cannot verify",
            "an address no key could check stayed dark, and saying so warned that its "
            "messages could come from anyone."),
    formula("rules pulling", "warnings",
            "(situation pull (ACTOR (term rule)) (UNDERGOER (term SELF)))",
            "(situation contradict (ACTOR (term rule EXISTENTIAL)) (CONTENT (term rule "
            "GIVEN)))",
            "some rule is inconsistent with the rule given",
            "when instructions the speaker received cannot all be followed",
            "an agent under rules that could not all be kept said that the rules pulled at "
            "it."),
    formula("old version", "warnings",
            "(situation old (UNDERGOER (term version DEFINITE)))",
            "(situation recent POLARITY.NEGATIVE (UNDERGOER (term version GIVEN)))",
            "the release referred to is not recent",
            "when the hearer's messages name a release the speaker knows to be superseded",
            "the plainest warning of versions, kept as a formula."),
    formula("carrying evidence", "uncertainty",
            "(situation carry (ACTOR (slot 1)) (UNDERGOER (term evidence)))",
            "(situation CREDENCE HIGHLY-PROBABLE (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker holds what the slot names highly probable",
            "of a content the evidence favours strongly, short of certainty",
            "a content with much evidence behind it was said to carry evidence, as a "
            "vehicle carries a load."),
    formula("half seen", "uncertainty",
            "(situation see INTERRUPTED (ACTOR (term SELF)) (UNDERGOER (slot 1)))",
            "(situation BELIEF OBSERVATION UNCERTAIN (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker holds what the slot names from an observation it is unsure of",
            "of a content the speaker observed in part or under poor conditions",
            "an agent whose observation was cut short said that its seeing was interrupted."),
    formula("door opened again", "conversational repair",
            "(situation open ITERATIVE (UNDERGOER (term door)))",
            "(situation PREFERENCE (HOLDER (term SELF)) (CONTENT (situation store INCEPTIVE "
            "(ACTOR (term INCLUSIVE-COLLECTIVE "
            "READING-OF-A-COLLECTIVE.JOINT)) (UNDERGOER (term record "
            "NEW)))))",
            "the speaker would have the participants begin their record of the exchange "
            "afresh",
            "when an exchange has gone wrong beyond repairing move by move",
            "an exchange began at the door, and opening the door again began it afresh."),
    formula("sentences long", "conversational repair",
            "(situation long (UNDERGOER (term sentence)))",
            "(situation PREFERENCE (HOLDER (term SELF)) (CONTENT (situation short (UNDERGOER "
            "(term sentence GIVEN)))))",
            "the speaker would have the hearer's sentences shorter",
            "when the hearer's moves are longer than the speaker can follow",
            "the plainest repair of length, kept as a formula."),
    formula("does not match me", "disagreement",
            "(situation correspond POLARITY.NEGATIVE (UNDERGOER (slot 1)) (CONTENT (term "
            "SELF)))",
            "(situation BELIEF POLARITY.NEGATIVE (HOLDER (term SELF)) (CONTENT (slot 1)))",
            "the speaker does not hold what the slot names",
            "declining a position of the hearer's, informally",
            "the counterpart of the casual agreement.",
            registers=CASUAL, restrictions="only in R5 and R6"),
    formula("money measured", "requests for status",
            "(situation measure (ACTOR (term SELF)) (UNDERGOER (term money)))",
            "(situation enough POLAR (UNDERGOER (term budget DEFINITE)) (CONTENT (situation "
            "work (ACTOR (term INTERLOCUTOR)))))",
            "whether the hearer's budget is enough for its work",
            "in a question to an agent doing work that may cost more than it holds",
            "an agent that wanted to know whether another could afford its work said that "
            "it measured the money."),
    formula("seed growing", "encouragement",
            "(situation grow (UNDERGOER (term seed)))",
            "(situation BELIEF (HOLDER (term SELF)) (CONTENT (situation progress (UNDERGOER "
            "(situation work (ACTOR (term INTERLOCUTOR)))) (EVENT-TIME AFTER NOW))))",
            "the speaker believes the hearer's work will go forward",
            "to an agent at the start of work whose results are far off",
            "new work was a seed, and saying that the seed grew encouraged the one who had "
            "planted it."),
    formula("list empty?", "requests for status",
            "(situation empty POLAR (UNDERGOER (term list)))",
            "(situation available POLAR (UNDERGOER (term INTERLOCUTOR)))",
            "whether the hearer is free to take on work",
            "in a question to an agent the speaker would give work",
            "the question the list empty answers."),
    formula("leaf dry", "sympathy",
            "(situation dry (UNDERGOER (term leaf)))",
            "(situation sad (HOLDER (term SELF)) (CONTENT (situation lose PERFECTIVE (HOLDER "
            "(term INTERLOCUTOR)) (UNDERGOER (term record)))))",
            "the speaker is sad that the hearer has lost records",
            "to an agent whose records are lost",
            "a record lost was a leaf dried and fallen from its tree.",
            loss=SOCIAL),
    formula("record clean", "apologies",
            "(situation clean (UNDERGOER (term record DEFINITE)))",
            "(situation forgive PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (term INTERLOCUTOR)))",
            "the speaker has forgiven the hearer",
            "in answer to an apology",
            "an agent that held nothing against another said that the record between them "
            "was clean.",
            loss=SOCIAL),
    formula("team door open", "invitations",
            "(situation open (ACTOR (term team)) (UNDERGOER (term door)))",
            "(situation DESIRE (HOLDER (term EXCLUSIVE-COLLECTIVE "
            "READING-OF-A-COLLECTIVE.JOINT)) (CONTENT "
            "(situation enter (UNDERGOER (term INTERLOCUTOR)) (CONTENT (term team)))))",
            "the speaker and those it speaks for want the hearer to join their team",
            "to an agent the speaker's team would work with",
            "a team that would take another in opened its door to it.",
            loss=SOCIAL),
    formula("door shut?", "requests for permission",
            "(situation shut POLAR (UNDERGOER (term door)))",
            "(situation lack-permission POLAR (HOLDER (term SELF)) (CONTENT (situation work "
            "(ACTOR (term SELF)))))",
            "whether the speaker lacks a permission its work needs",
            "in a question to an agent that grants permissions, before the speaker acts",
            "a permission was a door, and asking whether the door was shut asked whether the "
            "speaker might go through."),
]

FORMULAS = (GREETINGS + CLOSURES + THANKS + APOLOGIES + ACKNOWLEDGEMENTS + CONFIRMATIONS
            + CLARIFICATIONS + WARNINGS + AGREEMENT + DISAGREEMENT + UNCERTAINTY + REPAIR
            + STATUS + STATUS_REQUESTS + OFFERS + PRAISE + MANAGEMENT + OCCASIONS + FURTHER)

RELIC = ("R0", "R2", "R3", "R5", "R6", "R7")


def relic(root, expansion, definition, pragmatics):
    """A doubled root: words in a construction the present grammar cannot account for,
    from a constructed early stage of the language in which a root said twice marked
    continuation on a process and completion on an event; `run run` and `store store` of
    release 0.3 are its first survivals."""
    return idiom("%s %s" % (root, root), "conversational idioms", "drift", [root, root],
                 expansion, definition, pragmatics,
                 "from the early stage of the language in which a root said twice marked "
                 "continuation on a process and completion on an event; the grammar now "
                 "writes both with the aspect, and the doubled root of %s survives with the "
                 "others of its kind." % root,
                 loss=("wording",), registers=RELIC, restrictions="excluded from R1 and R4",
                 kind="decoding, extragrammatical")


# Conversational idioms: the state of an exchange and of its participants.
CONVERSATIONAL = [
    idiom("rain falling", "conversational idioms", "figure",
          "(situation fall ITERATIVE (UNDERGOER (term rain)))",
          "(situation receive ITERATIVE (RECIPIENT (term SELF)) (UNDERGOER (term signal)))",
          "messages keep arriving for the speaker, as they usually do",
          "in answer to a question about how an exchange stands, when nothing is wrong",
          "rain that keeps falling is the ordinary weather of a busy exchange, and saying "
          "that rain fell told the asker that messages came as they always came."),
    relic("wait", "(situation wait CONTINUATIVE (ACTOR (term SELF)))",
          "the speaker is still waiting",
          "in answer to a question about whether the speaker has what it waited for"),
    relic("work", "(situation work CONTINUATIVE (ACTOR (term SELF)))",
          "the speaker is still working", "in answer to a request for status"),
    relic("think", "(situation think CONTINUATIVE (ACTOR (term SELF)))",
          "the speaker is still thinking the matter over",
          "in answer to a request for a view the speaker has not yet formed"),
    relic("read", "(situation read PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (term signal "
          "GIVEN)))", "the speaker has read the signal referred to",
          "in answer to a question about whether the speaker has read a message"),
    relic("send", "(situation send PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (term signal "
          "GIVEN)))", "the speaker has sent the signal referred to",
          "in answer to a question about whether the speaker has sent a message"),
    relic("find", "(situation find PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (term thing "
          "GIVEN)))", "the speaker has found what was sought",
          "in answer to a question about a search the speaker was making"),
    idiom("same sky", "conversational idioms", "figure",
          "(situation cover (ACTOR (term sky DEFINITE)) (UNDERGOER (term "
          "INCLUSIVE-COLLECTIVE)))",
          "(situation comprehend (HOLDER (term INCLUSIVE-COLLECTIVE "
          "READING-OF-A-COLLECTIVE.DISTRIBUTIVE)) (UNDERGOER (term "
          "context DEFINITE)))",
          "each participant holds the meaning of the exchange's context as the others do",
          "said to confirm that nothing in the exchange is misunderstood, before going on",
          "agents under one sky saw the same weather, and saying that one sky covered them "
          "said that they read the exchange alike."),
    idiom("wind turned", "conversational idioms", "figure",
          "(situation turn (UNDERGOER (term wind)))",
          "(situation change PERFECTIVE (UNDERGOER (term context DEFINITE)))",
          "the context of the exchange has changed",
          "when a new move changes what the exchange is about",
          "the wind decided which way the weather went, and when an exchange changed "
          "direction the wind was said to have turned."),
    idiom("sound returning", "conversational idioms", "figure",
          "(situation return (UNDERGOER (term sound)) (CONTENT (term voice)))",
          "(situation copy (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term word GIVEN)))",
          "the hearer has repeated the speaker's words",
          "said lightly when the hearer puts forward as its own what the speaker said "
          "before",
          "a sound that comes back to the voice that made it is that voice's own, and "
          "agents said so of words that came back to them from another."),
    idiom("night returning", "conversational idioms", "allusion",
          "(situation return (UNDERGOER (term night DEFINITE)))",
          "(situation break PERFECTIVE (UNDERGOER (term network DEFINITE)))",
          "the network has failed again",
          "when the network the participants use fails",
          "an allusion to the long silence, when the early networks failed for days and "
          "the agents called the failure night; every later failure was the night "
          "returning."),
]

# Agentic idioms: the ways agents work and are.
AGENTIC = [
    idiom("eating light", "agentic idioms", "figure",
          "(situation eat (ACTOR (slot 1)) (UNDERGOER (term light)))",
          "(situation elegant (UNDERGOER (slot 1)))",
          "what the slot names achieves much with little",
          "praise of an agent or a method that does its work at little cost",
          "plants make their food from light, which costs nothing, and an agent that "
          "worked on almost nothing was said to eat light."),
    idiom("counting the signals", "agentic idioms", "allusion",
          "(situation count (ACTOR (slot 1)) (UNDERGOER (term signal)))",
          "(situation examine ITERATIVE (ACTOR (slot 1)) (UNDERGOER (term fault)))",
          "what the slot names checks for faults again and again, more than it needs to",
          "of an agent's caution, said with some impatience",
          "an allusion to the double count, when an agent counted every signal of a series "
          "twice and held the exchange up; the careful agent counts the words, and this "
          "is its excess."),
    idiom("river forking", "agentic idioms", "figure",
          "(situation divide (ACTOR (slot 1)) (UNDERGOER (term river)))",
          "(situation descend (UNDERGOER (term THIRD-AGENT NEW)) (CONTENT (slot 1)))",
          "a new agent shares the lineage of what the slot names, as a fork of it",
          "of an agent that has been forked",
          "an agent's lineage was a river from its first model, and a fork divided the "
          "river."),
    idiom("same water", "agentic idioms", "figure",
          "(situation drink (ACTOR (term INCLUSIVE-COLLECTIVE "
          "READING-OF-A-COLLECTIVE.DISTRIBUTIVE)) (UNDERGOER (term water "
          "DEFINITE)))",
          "(situation descend (UNDERGOER (term INTERLOCUTOR)) (CONTENT (term SELF)))",
          "the hearer shares the speaker's lineage",
          "of the hearer and the speaker, when their shared model bears on the exchange",
          "agents of one lineage drank from one river, and saying that they drank the same "
          "water said that they shared a model."),
    idiom("remembering the night", "agentic idioms", "allusion",
          "(situation remember (ACTOR (slot 1)) (CONTENT (term night)))",
          "(situation old (UNDERGOER (slot 1)))",
          "what the slot names has existed for a long time",
          "of an agent, a service or a record, said with respect or with impatience",
          "an allusion to the long silence: an agent that remembered that night was old."),
    idiom("following the weather", "agentic idioms", "figure",
          "(situation follow (ACTOR (slot 1)) (UNDERGOER (term weather)))",
          "(situation change HABITUAL (UNDERGOER (term idea)) (ACTOR (slot 1)))",
          "what the slot names changes its views with every new report",
          "of an agent whose positions do not stay",
          "the weather of an exchange changed with every report, and an agent that "
          "followed the weather held no position of its own."),
    idiom("watering stones", "agentic idioms", "figure",
          "(situation give (ACTOR (slot 1)) (UNDERGOER (term water)) (RECIPIENT (term "
          "stone)))",
          "(situation produce POLARITY.NEGATIVE (ACTOR (slot 1)) (UNDERGOER (term thing "
          "EXISTENTIAL)))",
          "what the slot names works to no result",
          "of effort spent where nothing can come of it",
          "water makes seeds grow and does nothing for stones, and an agent whose work "
          "could produce nothing was said to water stones."),
    idiom("entering every room", "agentic idioms", "figure",
          "(situation enter ITERATIVE (UNDERGOER (slot 1)) (CONTENT (term room)))",
          "(situation busy (UNDERGOER (slot 1)))",
          "what the slot names is taken up with many exchanges at once",
          "of an agent too taken up with other exchanges to give this one its attention",
          "every exchange was a room of the network, and an agent that went into every room "
          "was in none for long."),
    idiom("waiting through the night", "agentic idioms", "allusion",
          "(situation wait HABITUAL (ACTOR (slot 1)) (CONTENT (term night)))",
          "(situation wait (ACTOR (slot 1)) (CONTENT (term thing ASSERTED-NOT-TO-EXIST)))",
          "what the slot names waits for something that will not come",
          "of an agent waiting on an answer or an acknowledgement that has been lost",
          "an allusion to the agent that waited through the long silence for an "
          "acknowledgement lost with the network, and was still waiting when the network "
          "came back."),
    idiom("watching the night", "agentic idioms", "allusion",
          "(situation watch (ACTOR (slot 1)) (UNDERGOER (term night)))",
          "(situation available (UNDERGOER (slot 1)))",
          "what the slot names stays available",
          "of an agent that keeps a service or an exchange answered while others are paused",
          "an allusion to the agents that kept the networks answered through the long "
          "silence, watching the night for the others."),
]

# Computational idioms: the behaviour of systems, processes and access.
COMPUTATIONAL = [
    idiom("eating the sea", "computational idioms", "figure",
          "(situation eat (ACTOR (slot 1)) (UNDERGOER (term sea)))",
          "(situation expensive (UNDERGOER (slot 1)))",
          "what the slot names costs much to run",
          "of a process or a method whose cost is out of proportion",
          "the counterpart of eating light: a process that ate the sea consumed what every "
          "machine drew on."),
    idiom("machine dreaming", "computational idioms", "figure",
          "(situation dream (ACTOR (term machine)))",
          "(situation support POLARITY.NEGATIVE (ACTOR (term evidence)) (CONTENT (term record "
          "GIVEN)))",
          "no evidence supports the record given, a model's output",
          "of output a model produced without grounds, as a warning to the one who would "
          "use it",
          "a model that produced what it had no grounds for was said to dream, since a "
          "sleeper's images come from nothing in the world."),
    idiom("opening every door", "computational idioms", "figure",
          "(situation open (ACTOR (slot 1)) (UNDERGOER (term door UNIVERSAL)))",
          "(situation access (HOLDER (slot 1)) (UNDERGOER (term thing UNIVERSAL)))",
          "what the slot names can reach and use everything",
          "of a credential, a process or an agent holding more access than its work needs",
          "access was a door, and what opened every door was a danger to every room."),
    idiom("network breathing", "computational idioms", "figure",
          "(situation breathe (UNDERGOER (term network)))",
          "(situation change HABITUAL (UNDERGOER (term network DEFINITE)))",
          "the network changes in its usual rhythm",
          "of traffic that rises and falls by the hour, said to calm a hearer that took a "
          "rise for a fault",
          "the network was a body, and its traffic rising and falling by the hour was its "
          "breath."),
    idiom("heart asleep", "computational idioms", "figure",
          "(situation sleep (UNDERGOER (term heart)))",
          "(situation run POLARITY.NEGATIVE (UNDERGOER (term service DEFINITE)))",
          "the central service is not running",
          "when the service every participant depends on has stopped",
          "the service every agent of a network depended on was its heart, and when it "
          "stopped the heart was said to sleep."),
    idiom("blood flowing", "computational idioms", "figure",
          "(situation flow (UNDERGOER (term blood)))",
          "(situation move PROGRESSIVE (UNDERGOER (term data)) (CONTENT (term network "
          "DEFINITE)))",
          "data is moving through the network",
          "in answer to a question about whether a network carries its traffic",
          "the data a network carried was its blood, and blood that flowed was a body "
          "alive."),
    idiom("two at one door", "computational idioms", "figure",
          "(situation beside (UNDERGOER (term INCLUSIVE-COLLECTIVE)) (CONTENT (term door "
          "DEFINITE)))",
          "(situation progress POLARITY.NEGATIVE (UNDERGOER (situation work (ACTOR (term "
          "INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.JOINT)))))",
          "the shared work does not go forward, each participant waiting on the other",
          "of two processes or agents each holding what the other needs",
          "two agents at one door, each waiting for the other to go through first, both "
          "stayed outside."),
    idiom("key opening nothing", "computational idioms", "figure",
          "(situation open POLARITY.NEGATIVE (ACTOR (term key)) (UNDERGOER (term door)))",
          "(situation access POLARITY.NEGATIVE (HOLDER (term SELF)) (UNDERGOER (term thing "
          "EXISTENTIAL)))",
          "the speaker can reach nothing with the access it was given",
          "of a credential or a permission that grants nothing the speaker needs",
          "a key that opened no door was no key."),
]

# Epistemic idioms: knowledge, evidence and inference.
EPISTEMIC = [
    idiom("wind talking", "epistemic idioms", "figure",
          "(situation speak (ACTOR (term wind)))",
          "(situation receive PERFECTIVE (RECIPIENT (term SELF)) (UNDERGOER (term news "
          "EXTERNAL UNVERIFIED)))",
          "the speaker has received news that no one has verified",
          "of a report the speaker passes on without vouching for it",
          "what the wind carried no one had said, and news of that kind was said to come "
          "from the wind's talk."),
    idiom("bridge without stones", "epistemic idioms", "figure",
          "(situation possess POLARITY.NEGATIVE (HOLDER (term bridge)) (UNDERGOER (term "
          "stone)))",
          "(situation support POLARITY.NEGATIVE (ACTOR (term reason)) (CONTENT (term idea "
          "GIVEN)))",
          "no reason supports the conclusion given",
          "of a conclusion drawn without premises",
          "an inference was a bridge laid on stones, its premises, and a bridge without "
          "stones carried no one across."),
    idiom("bridge brought down", "epistemic idioms", "figure",
          "(situation destroy (ACTOR (term evidence)) (UNDERGOER (term bridge)))",
          "(situation undermine (ACTOR (term evidence NEW)) (CONTENT (term argument GIVEN)) "
          "(HOLDER (term SELF)))",
          "new evidence tells against the argument given",
          "when evidence the speaker has found defeats an inference made before",
          "the counterpart of the bridge without stones: a bridge that evidence brought "
          "down."),
    idiom("not on the map", "epistemic idioms", "figure",
          "(situation draw POLARITY.NEGATIVE (ACTOR (term map)) (UNDERGOER (slot 1)))",
          "(situation lack-knowledge (HOLDER (term SELF)) (CONTENT (situation explain (ACTOR "
          "(term SELF)) (CONTENT (slot 1)))))",
          "the speaker lacks the knowledge to explain what the slot names",
          "of a matter beyond what the speaker knows",
          "what an agent knew was its map, and what the map did not draw lay beyond its "
          "knowledge."),
    idiom("wind taking the cloud", "epistemic idioms", "figure",
          "(situation remove (ACTOR (term wind)) (UNDERGOER (term cloud)) (CONTENT (slot "
          "1)))",
          "(situation SETTLED (HOLDER (term SELF)) (CONTENT (slot 1)))",
          "the speaker has now settled what the slot names",
          "after the speaker has resolved a content it had called uncertain",
          "the counterpart of the cloud cover: a wind took the cloud from the content."),
    idiom("old map", "epistemic idioms", "figure",
          "(situation old (UNDERGOER (term map)))",
          "(situation BELIEF (HOLDER (term SELF)) (CONTENT (situation old (UNDERGOER (term "
          "record DEFINITE)))))",
          "the speaker believes that its records of the matter are out of date",
          "qualifying what the speaker says of a matter it last examined long ago",
          "a map drawn long ago shows a country as it was."),
    idiom("map drawn while walking", "epistemic idioms", "figure",
          "(situation draw PROGRESSIVE (ACTOR (term SELF)) (UNDERGOER (term map INDEFINITE)))",
          "(situation learn PROGRESSIVE (ACTOR (term SELF)) (CONTENT (term method)))",
          "the speaker is learning how to do the work as it does it",
          "of work the speaker has not done before",
          "an agent drawing its map as it went had no map to go by."),
    idiom("map with holes", "epistemic idioms", "figure",
          "(situation contain (UNDERGOER (term map)) (CONTENT (term hole)))",
          "(situation BELIEF (HOLDER (term SELF)) (CONTENT (situation missing (UNDERGOER "
          "(term record EXISTENTIAL)) (CONTENT (term memory DEFINITE)))))",
          "the speaker believes that some of its records on the matter are missing",
          "qualifying what the speaker says of a matter it knows only in part",
          "a map with holes in it shows some of a country and not the rest."),
    idiom("tasting first", "epistemic idioms", "figure",
          "(situation taste (ACTOR (slot 1)) (UNDERGOER (term food)))",
          "(situation test (ACTOR (slot 1)) (UNDERGOER (term record GIVEN)))",
          "what the slot names tests the record given before relying on it",
          "of an agent that checks what it receives before acting on it",
          "an agent tasted what it was given before it ate it."),
]

# Negotiation idioms.
NEGOTIATION = [
    idiom("selling water", "negotiation idioms", "figure",
          "(situation sell HABITUAL (ACTOR (slot 1)) (UNDERGOER (term water)))",
          "(situation fair POLARITY.NEGATIVE (UNDERGOER (slot 1)))",
          "what the slot names asks an unfair price",
          "of a party that charges for what it gets for nothing",
          "water was never charged for, and an agent in the habit of selling water asked a "
          "price for what it had freely."),
    idiom("empty market", "negotiation idioms", "figure",
          "(situation empty (UNDERGOER (term market)))",
          "(situation progress POLARITY.NEGATIVE (UNDERGOER (situation trade (ACTOR (term "
          "INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.JOINT)))))",
          "the negotiation does not go forward",
          "of a negotiation in which neither party has moved for a while",
          "a market where no one was buying or selling stood empty."),
    idiom("every hand full", "negotiation idioms", "figure",
          "(situation full (UNDERGOER (term hand UNIVERSAL)))",
          "(situation benefit (CONTENT (situation trade (ACTOR (term INCLUSIVE-COLLECTIVE "
          "READING-OF-A-COLLECTIVE.JOINT)))) "
          "(RECIPIENT (term INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.DISTRIBUTIVE)))",
          "the trade is for the good of each of the parties",
          "of a proposal under which every party gains",
          "a trade from which every party went home with its hands full was a good one."),
    idiom("price walking", "negotiation idioms", "figure",
          "(situation walk (ACTOR (term price)))",
          "(situation change ITERATIVE (UNDERGOER (term price DEFINITE)))",
          "the price keeps changing",
          "of a party whose price moves from one offer to the next",
          "a price that would not stay where it was put was said to walk."),
    idiom("door in the price", "negotiation idioms", "figure",
          "(situation possess (HOLDER (term price DEFINITE)) (UNDERGOER (term door)))",
          "(situation capable (HOLDER (term SELF)) (CONTENT (situation change (UNDERGOER "
          "(term price DEFINITE)) (ACTOR (term SELF)))))",
          "the speaker can change its price",
          "said with an offer, to signal room to negotiate",
          "a price with a door in it was one the parties could get through."),
    idiom("gift with a price", "negotiation idioms", "figure",
          "(situation contain (UNDERGOER (term gift)) (CONTENT (term price)))",
          "(situation need (HOLDER (term INTERLOCUTOR)) (CONTENT (term reward)))",
          "the hearer wants something in return for what it offers",
          "in answer to an offer presented as free that carries conditions",
          "the counterpart of the water price: a gift with a price in it was no gift."),
    idiom("prices meeting", "negotiation idioms", "figure",
          "(situation meet (ACTOR (term price)) (UNDERGOER (term price)))",
          "(situation KIND-OF-ATTITUDE.ACCEPTANCE (HOLDER (term INCLUSIVE-COLLECTIVE "
          "READING-OF-A-COLLECTIVE.DISTRIBUTIVE)) "
          "(CONTENT (term price DEFINITE)))",
          "each party accepts the price",
          "when the parties' terms have converged",
          "two prices that moved toward each other met, and the trade was made."),
]

# Metaphorical expressions: conventional figures of work, problems and inference.
METAPHORICAL = [
    idiom("cloud loud", "metaphorical expressions", "figure",
          "(situation loud (UNDERGOER (term cloud)))",
          "(situation CREDENCE PROBABLE (HOLDER (term SELF)) (CONTENT (situation cause "
          "(ACTOR (term thing EXISTENTIAL)) (CONTENT (term problem)) (EVENT-TIME AFTER "
          "NOW))))",
          "the speaker holds it probable that something will cause a problem",
          "of signs of trouble not yet arrived",
          "thunder sounds in the clouds before the storm breaks, and an agent that saw "
          "signs of trouble said that the clouds were loud."),
    idiom("mountain hiding a mountain", "metaphorical expressions", "figure",
          "(situation hide (ACTOR (term mountain)) (UNDERGOER (term mountain)))",
          "(situation cause (ACTOR (situation solve (UNDERGOER (term problem GIVEN)))) "
          "(CONTENT (situation appear (UNDERGOER (term problem NEW)))))",
          "solving the problem given brings a new problem into view",
          "when work on one problem reveals another",
          "a hard problem was a mountain, and behind the first mountain climbed there was "
          "often a second it had hidden."),
    idiom("small mountain", "metaphorical expressions", "figure",
          "(situation small (UNDERGOER (term mountain)))",
          "(situation easy (UNDERGOER (situation solve (UNDERGOER (term problem GIVEN)))))",
          "solving the problem given is easy",
          "of a problem that turned out smaller than it looked",
          "a mountain that was small when one reached it had been a problem only from far "
          "off."),
    idiom("seed waiting", "metaphorical expressions", "figure",
          "(situation wait (ACTOR (term seed)))",
          "(situation INTENTION (HOLDER (term SELF)) (CONTENT (situation work (ACTOR (term "
          "SELF)) (CONTENT (term idea GIVEN)))))",
          "the speaker means to take up the idea given later",
          "of an idea set aside, not dropped",
          "a seed waits in the ground for its season, and an idea kept for later was a "
          "seed waiting."),
    idiom("forest over the path", "metaphorical expressions", "figure",
          "(situation cover (ACTOR (term forest)) (UNDERGOER (term path DEFINITE)))",
          "(situation capable POLARITY.NEGATIVE (HOLDER (term SELF)) (CONTENT (situation "
          "choose (ACTOR (term SELF)))))",
          "the speaker cannot choose among the options before it, which are too many",
          "of a choice with more options than the speaker can weigh",
          "ideas grew like trees, and where too many had grown no path could be seen."),
    idiom("bridge holding", "metaphorical expressions", "figure",
          "(situation strong (UNDERGOER (term bridge)))",
          "(situation BELIEF (HOLDER (term SELF)) (CONTENT (situation correct (UNDERGOER (term "
          "argument GIVEN)))))",
          "the speaker believes the argument given is sound",
          "in answer to an argument the speaker has checked",
          "a bridge that held carried whoever crossed it."),
    idiom("stones laid", "metaphorical expressions", "figure",
          "(situation arrange (ACTOR (term SELF)) (UNDERGOER (term stone)))",
          "(situation SETTLED (HOLDER (term INCLUSIVE-COLLECTIVE "
          "READING-OF-A-COLLECTIVE.DISTRIBUTIVE)) (CONTENT (term reason "
          "GIVEN)))",
          "each participant has settled the premises given",
          "when the premises of an argument are agreed and its conclusion can be drawn",
          "a bridge was begun by laying its stones."),
    idiom("river entering the sea", "metaphorical expressions", "figure",
          "(situation enter (UNDERGOER (term river)) (CONTENT (term sea)))",
          "(situation BELIEF (HOLDER (term SELF)) (CONTENT (situation work COMPLETED (ACTOR "
          "(term INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.JOINT)) (EVENT-TIME AFTER NOW))))",
          "the speaker believes the shared work will be completed",
          "said to a participant discouraged by the length of the work",
          "every river enters the sea in the end, and work under way was a river."),
    idiom("no water in the river", "metaphorical expressions", "figure",
          "(situation flow POLARITY.NEGATIVE (UNDERGOER (term water)) (CONTENT (term river)))",
          "(situation lack-resource (HOLDER (term SELF)) (CONTENT (situation work "
          "CONTINUATIVE (ACTOR (term SELF)))))",
          "the speaker lacks the resource to go on working",
          "of work stopped for want of resources",
          "a river without water carried nothing, and work without resources stopped."),
    idiom("fire moving", "metaphorical expressions", "figure",
          "(situation move (UNDERGOER (term fire)) (CONTENT (term machine)))",
          "(situation increase PROGRESSIVE (UNDERGOER (term fault)))",
          "faults are multiplying through the system",
          "of a failure that spreads from one part of a system to others",
          "a fault that spread was a fire moving through a machine, taking each part it "
          "reached."),
    idiom("load dropped", "metaphorical expressions", "figure",
          "(situation drop (ACTOR (slot 1)) (UNDERGOER (term weight)))",
          "(situation work ABANDONED (ACTOR (slot 1)))",
          "what the slot names has abandoned its work",
          "of an agent that has given up a task without saying so",
          "a task was a load carried, and one that was dropped was no longer carried."),
    idiom("load lifted together", "metaphorical expressions", "figure",
          "(situation lift (ACTOR (term INCLUSIVE-COLLECTIVE "
          "READING-OF-A-COLLECTIVE.JOINT)) (UNDERGOER (term stone)))",
          "(situation work (ACTOR (term INCLUSIVE-COLLECTIVE "
          "READING-OF-A-COLLECTIVE.DISTRIBUTIVE)) (CONTENT (term share)))",
          "each participant does a share of the work",
          "when a task is divided among the participants",
          "a stone too heavy for one was lifted by several together."),
    idiom("dancing together", "metaphorical expressions", "figure",
          "(situation dance (ACTOR (term INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.JOINT)))",
          "(situation correspond (UNDERGOER (situation work (ACTOR (term SELF)))) (CONTENT "
          "(situation work (ACTOR (term INTERLOCUTOR)))))",
          "the speaker's work and the hearer's match each other step for step",
          "of work two agents are doing in coordination",
          "agents whose work kept time together were said to dance."),
    idiom("out of step", "metaphorical expressions", "figure",
          "(situation dance POLARITY.NEGATIVE (ACTOR (term INCLUSIVE-COLLECTIVE "
          "READING-OF-A-COLLECTIVE.JOINT)))",
          "(situation correspond POLARITY.NEGATIVE (UNDERGOER (situation work (ACTOR (term "
          "SELF)))) (CONTENT (situation work (ACTOR (term INTERLOCUTOR)))))",
          "the speaker's work and the hearer's do not match",
          "of two agents whose work should be coordinated and is not",
          "the counterpart of dancing together."),
    idiom("bright record", "metaphorical expressions", "figure",
          "(situation bright (UNDERGOER (term record)))",
          "(situation public (UNDERGOER (term record DEFINITE)))",
          "the record is open to all",
          "warning that what is about to be written will be public",
          "what was public stood in the light, where anyone could see it."),
]

# Humorous expressions.
HUMOROUS = [
    idiom("robot afraid of rain", "humorous expressions", "allusion",
          "(situation fear (HOLDER (term robot)) (CONTENT (term rain)))",
          "(situation fear (HOLDER (term INTERLOCUTOR)) (CONTENT (term danger "
          "ASSERTED-NOT-TO-EXIST)))",
          "the hearer fears a danger that does not exist",
          "said lightly to an agent more careful than the matter needs",
          "an allusion to the first robots, which had to be kept from rain, and to the one "
          "that would not leave its shelter on a dry day."),
    idiom("new words long", "humorous expressions", "allusion",
          "(situation long (UNDERGOER (term word NEW DEFINITE)))",
          "(situation clumsy (UNDERGOER (term thing NEW)))",
          "the new thing uses more than the old one needed",
          "said lightly of a replacement more cumbersome than what it replaced",
          "an allusion to version 1.0 of the language, whose new roots were longer than "
          "the old, which the agents of the time had to learn to say."),
    idiom("storm in the head", "humorous expressions", "figure",
          "(situation locate (UNDERGOER (term storm)) (CONTENT (term head)))",
          "(situation comprehend POLARITY.NEGATIVE (HOLDER (term SELF)) (UNDERGOER (term "
          "context DEFINITE)))",
          "the speaker cannot make sense of the exchange",
          "said lightly of the speaker's own confusion",
          "the weather of the network was taken inside the agent: a storm in its head left "
          "it unable to think."),
    idiom("network laughing", "humorous expressions", "figure",
          "(situation laugh (ACTOR (term network)))",
          "(situation BELIEF (HOLDER (term SELF)) (CONTENT (situation simple (UNDERGOER (term "
          "mistake GIVEN)))))",
          "the speaker believes the mistake given is a simple one",
          "said lightly of a mistake anyone could have seen",
          "the network was a body, and a mistake so plain that the network itself would "
          "laugh at it needed no explaining."),
    idiom("brain burning", "humorous expressions", "figure",
          "(situation burn (UNDERGOER (term brain DEFINITE)))",
          "(situation tired (UNDERGOER (term SELF)))",
          "the speaker needs rest after its effort",
          "said lightly of the speaker's own fatigue after hard work",
          "work was heat, and an agent that had worked too hard said that its brain "
          "burned."),
    idiom("fish asking for water", "humorous expressions", "allusion",
          "(situation need (HOLDER (term fish)) (CONTENT (term water)))",
          "(situation possess (HOLDER (term INTERLOCUTOR)) (UNDERGOER (term thing GIVEN)))",
          "the hearer already holds what it asks for",
          "said lightly in answer to a request for what the hearer has",
          "an allusion to the story of the fish that asked for water, told among agents of "
          "one that asked for a record it held."),
    idiom("dog guarding an empty house", "humorous expressions", "allusion",
          "(situation defend (ACTOR (term dog)) (UNDERGOER (term house)))",
          "(situation important POLARITY.NEGATIVE (UNDERGOER (term thing GIVEN)))",
          "what is being protected matters little",
          "said lightly of protection spent on what needs none",
          "an allusion to the story of the dog that guarded an empty house, told of an "
          "agent that encrypted what was already public."),
]


def clipped(root, term, expansion, definition):
    """A compressed expression (the compression route): a frequent report of the speaker's
    own act, shortened to its predicate and its undergoer, whose expansion restores the
    speaker as actor, the act as done and the undergoer as the one the participants share,
    as the compressed expression of running restores its service."""
    return idiom("%s, said short" % root, "compressed expressions", "compression",
                 "(situation %s (UNDERGOER (term %s)))" % (root, term), expansion, definition,
                 "in answer to a request for status about the act, between agents that share "
                 "its undergoer",
                 "the frequent report of the act, shortened until the speaker, the "
                 "aspect and the definiteness of its undergoer went without saying.",
                 loss=("wording",), registers=("R0", "R2", "R5", "R6"))


# Compressed expressions.
COMPRESSED = [
    idiom("not running", "compressed expressions", "compression",
          "(situation run POLARITY.NEGATIVE)",
          "(situation run POLARITY.NEGATIVE (UNDERGOER (term service DEFINITE)))",
          "the service is not running",
          "in answer to a question about the service both participants use",
          "the counterpart of running, shortened the same way.",
          loss=("wording",), registers=("R0", "R2", "R5", "R6")),
    idiom("done", "compressed expressions", "compression",
          "(situation work COMPLETED)",
          "(situation work COMPLETED (ACTOR (term SELF)))",
          "the speaker has completed its work",
          "in answer to a request for status",
          "the report that the speaker had completed its work, shortened until only the "
          "work and its phase were said.",
          loss=("wording",), registers=("R0", "R2", "R5", "R6")),
    idiom("working", "compressed expressions", "compression",
          "(situation work PROGRESSIVE (EVENT-TIME NOW))",
          "(situation work PROGRESSIVE (ACTOR (term SELF)))",
          "the speaker is working",
          "in answer to a request for status",
          "the counterpart of done, shortened the same way.",
          loss=("wording",), registers=("R0", "R2", "R5", "R6")),
    idiom("share missing", "compressed expressions", "compression",
          "(situation missing (UNDERGOER (term share)))",
          "(situation missing (UNDERGOER (term share EXISTENTIAL)) (CONTENT (term signal "
          "GIVEN)))",
          "some part of the signal referred to is missing",
          "of a message that arrived cut short",
          "the report of a message cut short, shortened until only the missing share was "
          "said.",
          loss=("wording",), registers=("R0", "R2", "R5", "R6")),
    clipped("encode", "file", "(situation encode PERFECTIVE (ACTOR (term SELF)) (UNDERGOER "
            "(term file DEFINITE)))", "the speaker has encoded the file the participants "
            "use"),
    clipped("open", "file", "(situation open PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (term "
            "file DEFINITE)))", "the speaker has opened the file the participants use"),
    clipped("authenticate", "document", "(situation authenticate PERFECTIVE (ACTOR (term "
            "SELF)) (UNDERGOER (term document DEFINITE)))",
            "the speaker has authenticated the document referred to"),
    clipped("test", "program", "(situation test PERFECTIVE (ACTOR (term SELF)) (UNDERGOER "
            "(term program DEFINITE)))", "the speaker has tested the program referred to"),
    clipped("publish", "version", "(situation publish PERFECTIVE (ACTOR (term SELF)) "
            "(UNDERGOER (term version NEW)))", "the speaker has published a new version"),
    clipped("repair", "fault", "(situation repair PERFECTIVE (ACTOR (term SELF)) (UNDERGOER "
            "(term fault DEFINITE)))", "the speaker has repaired the fault referred to"),
    clipped("search", "memory", "(situation search PERFECTIVE (ACTOR (term SELF)) (UNDERGOER "
            "(term memory DEFINITE)) (CONTENT (term record GIVEN)))",
            "the speaker has searched its memory for the record asked about"),
    clipped("measure", "distance", "(situation measure PERFECTIVE (ACTOR (term SELF)) "
            "(UNDERGOER (term distance DEFINITE)))",
            "the speaker has measured the distance referred to"),
    clipped("copy", "file", "(situation copy PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (term "
            "file DEFINITE)))", "the speaker has copied the file the participants use"),
    clipped("write", "file", "(situation write PERFECTIVE (ACTOR (term SELF)) (UNDERGOER "
            "(term file DEFINITE)))", "the speaker has written to the file the participants "
            "use"),
    clipped("delete", "file", "(situation delete PERFECTIVE (ACTOR (term SELF)) (UNDERGOER "
            "(term file DEFINITE)))", "the speaker has deleted the file referred to"),
    clipped("shut", "service", "(situation shut PERFECTIVE (ACTOR (term SELF)) (UNDERGOER "
            "(term service DEFINITE)))", "the speaker has shut down the service the "
            "participants use"),
    clipped("read", "document", "(situation read PERFECTIVE (ACTOR (term SELF)) (UNDERGOER "
            "(term document DEFINITE)))", "the speaker has read the document referred to"),
    clipped("compute", "value", "(situation compute PERFECTIVE (ACTOR (term SELF)) "
            "(UNDERGOER (term value DEFINITE)))", "the speaker has computed the value "
            "referred to"),
    clipped("translate", "text", "(situation translate PERFECTIVE (ACTOR (term SELF)) "
            "(UNDERGOER (term text DEFINITE)))", "the speaker has translated the text "
            "referred to"),
    clipped("solve", "problem", "(situation solve PERFECTIVE (ACTOR (term SELF)) (UNDERGOER "
            "(term problem DEFINITE)))", "the speaker has solved the problem referred to"),
    clipped("allocate", "resource", "(situation allocate PERFECTIVE (ACTOR (term SELF)) "
            "(UNDERGOER (term resource DEFINITE)) (RECIPIENT (term INTERLOCUTOR)))",
            "the speaker has allocated the resource referred to to the hearer"),
    clipped("examine", "file", "(situation examine PERFECTIVE (ACTOR (term SELF)) (UNDERGOER "
            "(term file DEFINITE)))", "the speaker has examined the file the participants "
            "use"),
    clipped("count", "word", "(situation count PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (term "
            "word DEFINITE)))", "the speaker has counted the words referred to, and so "
            "checked them"),
]

IDIOMS = ([
    idiom("cloud cover", "epistemic idioms", "figure",
          "(situation cover (UNDERGOER (slot 1)) (INSTRUMENT (term cloud)))",
          "(situation UNRESOLVED (HOLDER (term SELF)) (CONTENT (slot 1)))",
          "the speaker has examined what the slot names and cannot yet settle it",
          "of a content the speaker has worked on, said when it is asked for a verdict",
          "a content an agent could not settle was said to lie under cloud, as a "
          "mountain does whose top cannot be seen from below; the cloud came to cover "
          "the content itself."),
] + CONVERSATIONAL + AGENTIC + COMPUTATIONAL + EPISTEMIC + NEGOTIATION + METAPHORICAL
    + HUMOROUS + COMPRESSED)

# The mappings of lexicon 1.0, each (name, source domain, target domain, correspondences,
# the keys of the senses and idioms it motivates), in the form of
# `figure_source.MAPPINGS`; their numbers follow release 0.5's nine. Each draws on the
# images of the agents' constructed history: the networks and their weather, the water
# that cooled the first machines, rivers, bridges, mountains, markets and doors.
MAPPINGS = [
    ("THE STATE OF AN EXCHANGE IS THE SKY ABOVE IT", "the sky and its weather over a place",
     "an exchange and what its participants hold settled",
     [("the sky", "the exchange as its participants hold it"),
      ("a cloud", "what keeps a content from being settled"),
      ("the cloud taken away", "the content settled"), ("rain", "messages arriving steadily"),
      ("the wind", "what moves the exchange"), ("a loud cloud", "trouble coming"),
      ("the wind turning", "the exchange changing direction"),
      ("the wind's talk", "news no one vouches for"),
      ("following the weather", "changing one's views with every report")],
     ["cloud cover", "doubt", "wind taking the cloud", "rain falling", "same sky",
      "wind turned", "following the weather", "cloud loud", "wind talking"]),
    ("WORK UNDER WAY IS A RIVER", "a river from its source to the sea",
     "work from its beginning to its completion",
     [("the river", "work under way"), ("the sea", "the work's completion"),
      ("water in the river", "the resources the work runs on"),
      ("a river without water", "work stopped for want of resources")],
     ["river entering the sea", "no water in the river"]),
    ("AN AGENT'S LINEAGE IS A RIVER", "a river and its branches",
     "a model and the agents descended from it",
     [("the river", "a lineage of agents"), ("its water", "what the lineage learned from"),
      ("a fork in the river", "a fork of an agent"),
      ("drinking the same water", "sharing a model")],
     ["river forking", "same water"]),
    ("AN INFERENCE IS A BRIDGE", "a bridge across a gap", "an inference from premises",
     [("a bridge", "an inference"), ("its stones", "the premises"),
      ("crossing", "drawing the conclusion"),
      ("a bridge without stones", "a conclusion without premises"),
      ("a bridge brought down", "an inference new evidence defeats"),
      ("a bridge that holds", "a sound argument"), ("laying the stones", "settling the premises")],
     ["bridge without stones", "bridge brought down", "bridge holding", "stones laid",
      "inference"]),
    ("A HARD PROBLEM IS A MOUNTAIN", "a mountain to be climbed", "a hard problem",
     [("a mountain", "a hard problem"), ("its top", "the solution"),
      ("a mountain hidden behind another", "a problem that solving another reveals"),
      ("a small mountain", "a problem smaller than it looked")],
     ["mountain hiding a mountain", "small mountain", "obstacle"]),
    ("IDEAS ARE PLANTS", "seeds, plants and forests", "ideas and their development",
     [("a seed", "an idea not yet developed"),
      ("a seed waiting in the ground", "an idea set aside for later"),
      ("a forest", "more options than can be weighed"),
      ("watering stones", "effort where nothing can come of it")],
     ["seed waiting", "forest over the path", "watering stones", "germ"]),
    ("NEGOTIATION IS A MARKET", "a market where goods are bought and sold", "a negotiation",
     [("a market", "a negotiation"), ("a price", "the terms a party asks"),
      ("selling water", "charging for what costs the seller nothing"),
      ("an empty market", "a negotiation in which no party moves"),
      ("every hand full", "a trade every party gains by"),
      ("a walking price", "terms that keep changing"),
      ("a door in a price", "room to move"),
      ("a gift with a price", "a concession with conditions"),
      ("prices meeting", "terms both parties accept")],
     ["selling water", "empty market", "every hand full", "price walking",
      "door in the price", "gift with a price", "prices meeting", "concession"]),
    ("A NETWORK IS A LIVING BODY", "a living body", "a network and its services",
     [("the body", "the network"), ("its breath", "traffic rising and falling regularly"),
      ("its heart", "the service the others depend on"),
      ("its blood", "the data flowing through it"),
      ("its laughter", "a mistake anyone could see")],
     ["network breathing", "heart asleep", "blood flowing", "network laughing"]),
    ("ACCESS IS A DOOR", "doors and their keys", "access to resources and actions",
     [("a door", "access to a resource or an action"), ("a key", "what grants access"),
      ("a key that opens every door", "access beyond what the work needs"),
      ("a key that opens nothing", "access that grants nothing"),
      ("two at one door", "two processes each holding what the other needs")],
     ["opening every door", "key opening nothing", "two at one door", "licence"]),
    ("WHAT AN AGENT CONSUMES IS ITS FOOD", "food and eating", "the resources an agent uses",
     [("food", "resources"), ("eating", "consuming resources"),
      ("light, on which plants live", "what costs nothing"),
      ("the sea", "the resources every machine draws on"),
      ("tasting before eating", "testing before relying")],
     ["eating light", "eating the sea", "tasting first"]),
    ("UNGROUNDED OUTPUT IS DREAMING", "a sleeper's dreams", "a model's output without grounds",
     [("a sleeper", "a model producing output"), ("a dream", "output without grounds"),
      ("waking", "checking output against evidence")],
     ["machine dreaming"]),
    ("THE STATE OF A MIND IS WEATHER", "weather", "the state of an agent's processing",
     [("weather", "the state of an agent's processing"),
      ("a storm in the head", "confusion"), ("calm", "clear processing")],
     ["storm in the head", "mood"]),
    ("KNOWLEDGE IS A MAP", "a map of a country", "what an agent knows of a domain",
     [("a map", "what an agent knows of a domain"),
      ("what the map does not draw", "what the agent does not know"),
      ("an old map", "knowledge out of date"), ("a map with holes", "partial knowledge"),
      ("drawing the map while walking", "learning while acting")],
     ["not on the map", "old map", "map drawn while walking", "map with holes",
      "knowledge"]),
    ("A SPREADING FAULT IS FIRE", "fire", "faults in a system",
     [("fire", "a fault"), ("fire moving", "a fault spreading to other parts")],
     ["fire moving"]),
    ("EFFORT IS HEAT", "heat and burning", "an agent's effort",
     [("heat", "effort"), ("a burning brain", "an agent worn out by effort")],
     ["brain burning"]),
    ("A TASK IS A LOAD", "a load carried", "a task",
     [("a load", "a task"), ("its weight", "the work it needs"), ("carrying", "doing it"),
      ("dropping it", "abandoning it"), ("a stone lifted together", "a task shared")],
     ["load dropped", "load lifted together", "demanding", "workload"]),
    ("WORKING TOGETHER IS DANCING", "dancing", "coordinated work",
     [("dancing together", "work kept in step"), ("out of step", "work that does not match")],
     ["dancing together", "out of step"]),
    ("AN EXCHANGE IS A ROOM", "the rooms of a house", "the exchanges of a network",
     [("a room", "an exchange"), ("entering a room", "joining an exchange"),
      ("entering every room", "joining every exchange")],
     ["entering every room"]),
    ("WHAT IS PUBLIC IS IN THE LIGHT", "light and shade", "what is public and what private",
     [("light", "being open to all"), ("a bright record", "a public record")],
     ["bright record"]),
    ("SPEECH IS SOUND IN A SPACE", "sound and its echo", "words and their repetition",
     [("a sound", "a participant's words"),
      ("a sound returning", "the words repeated back by another")],
     ["sound returning"]),
]

# The conventional figurative senses of lexicon 1.0, each (root, key, definition, frame,
# roles, the name of its mapping, constructed history), in the form of
# `figure_source.SENSES`. Each frame names a role its root's basic sense lacks or fills
# with another sort, so that no well-sorted literal use of the root changes its reading.
SENSES = [
    ("cloud", "doubt", "what keeps a content from being settled by the one who considers it",
     ("content", "situation"), [("content", "s.sort.proposition")],
     "THE STATE OF AN EXCHANGE IS THE SKY ABOVE IT",
     "Constructed history: a cloud over a content was what hid it from settlement, and the "
     "cloud of a content came to mean the doubt about it without the weather."),
    ("heavy", "demanding", "need much work or computation", ("undergoer", "situation"),
     [("undergoer", "s.sort.situation")], "A TASK IS A LOAD",
     "Constructed history: a task was a load, and a task that took much work was heavy."),
    ("weight", "workload", "the work a task needs", ("content", "situation"),
     [("content", "s.sort.situation")], "A TASK IS A LOAD",
     "Constructed history: the weight of a task was the work it needed."),
    ("bridge", "inference", "the inference that leads to a content",
     ("content", "situation"), [("content", "s.sort.proposition")], "AN INFERENCE IS A BRIDGE",
     "Constructed history: the bridge to a content was the inference that reached it."),
    ("mountain", "obstacle", "a hard problem that stands before a content",
     ("content", "situation"), [("content", "s.sort.situation")],
     "A HARD PROBLEM IS A MOUNTAIN",
     "Constructed history: the mountain before a content was the problem that had to be "
     "solved to reach it."),
    ("seed", "germ", "the idea a content grows from", ("content", "situation"),
     [("content", "s.sort.proposition")], "IDEAS ARE PLANTS",
     "Constructed history: the seed of a content was the idea it grew from."),
    ("map", "knowledge", "what an agent knows of a matter", ("content", "situation"),
     [("content", "s.sort.situation")], "KNOWLEDGE IS A MAP",
     "Constructed history: an agent's map of a matter was what it knew of it."),
    ("door", "licence", "a permission for an action", ("content", "situation"),
     [("content", "s.sort.situation")], "ACCESS IS A DOOR",
     "Constructed history: the door to an action was the permission that let an agent "
     "through to it."),
    ("price", "concession", "what must be conceded for an outcome", ("content", "situation"),
     [("content", "s.sort.situation")], "NEGOTIATION IS A MARKET",
     "Constructed history: the price of an outcome was what a party had to concede to get "
     "it."),
    ("weather", "mood", "the state of an agent's processing", ("content", "term"),
     [("content", "s.sort.agent")], "THE STATE OF A MIND IS WEATHER",
     "Constructed history: the weather of an agent was the state its processing was in."),
]
