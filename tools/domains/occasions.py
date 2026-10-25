"""The occasions of the idioms: the conversational idioms said in answer to a question or
of the exchange, and every idiom said of something, each with the move that occasions it
under its pragmatic conditions."""
from .compose import names, party
from .phrasing import (LANG, position, question, quoted, register, said)


# ---------------------------------------------------------------- the idioms

# The question each idiom said in answer to one answers, as its pragmatic conditions state
# it: the situation agent 1 asks agent 2 about, with its English. An idiom not here
# answers a question about the domain's own matter, which asks the hearer for a view.
YOUR_WORK = ("(situation progress (UNDERGOER (situation work (ACTOR (term INTERLOCUTOR)))))",
             "agent 2's work is going forward")
ASKED = {
    "quiet network": ("(situation change PERFECTIVE (UNDERGOER (term thing EXISTENTIAL)))",
                      "anything has changed"),
    "running": ("(situation run (UNDERGOER (term service DEFINITE)))",
                "the service is running"),
    "run run": ("(situation run (UNDERGOER (term service DEFINITE)))",
                "the service is running"),
    "not running": ("(situation run (UNDERGOER (term service DEFINITE)))",
                    "the service is running"),
    "rain falling": ("(situation receive (RECIPIENT (term INTERLOCUTOR)) (UNDERGOER (term "
                     "signal)))", "messages are reaching agent 2"),
    "wait wait": ("(situation receive PERFECTIVE (RECIPIENT (term INTERLOCUTOR)) (UNDERGOER "
                  "(term data DEFINITE)))", "agent 2 has received the data it waits for"),
    "work work": YOUR_WORK, "working": YOUR_WORK, "done": YOUR_WORK,
    "read read": ("(situation read PERFECTIVE (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term "
                  "signal DEFINITE)))", "agent 2 has read the signal"),
    "send send": ("(situation send PERFECTIVE (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term "
                  "signal DEFINITE)))", "agent 2 has sent the signal"),
    "find find": ("(situation find PERFECTIVE (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term "
                  "key DEFINITE)))", "agent 2 has found the key it was searching for"),
}
NOT_RECEIVED = ("(situation receive POLARITY.NEGATIVE PERFECTIVE (RECIPIENT (term SELF)) "
                "(UNDERGOER (term data DEFINITE)))")


def conversational(x, ident, t, n):
    """An idiom said in answer to the question its pragmatic conditions name, or of the
    exchange, after the move that occasions it."""
    key = LANG.entries[ident]["key"]
    reg = register(ident)
    if key == "store store":
        content, english = t.content()
        x.send(1, [2], position(content, reg=reg))
        x.send(2, [1], said(ident, basis="OBSERVATION"))
        return "agent 1 states that %s, and agent 2, which means to keep it, answers with " \
               "%s" % (english, quoted(ident))
    if key == "same sky":
        content, english = t.content()
        x.send(2, [1], position(content, reg=reg))
        x.send(1, [2], said(ident, basis="OBSERVATION"))
        return "agent 2 states that %s, and agent 1, before going on, answers with %s" % (
            english, quoted(ident))
    if key in ("wind turned", "sound returning"):
        content, english = t.content()
        x.send(1, [2], position(content, reg=reg))
        if key == "wind turned":
            other, changed = t.content()
            x.send(2, [1], position(other, reg=reg))
            x.send(1, [2], said(ident, basis="OBSERVATION"))
            return "agent 1 states that %s, agent 2 answers that %s, and agent 1 remarks " \
                   "with %s" % (english, changed, quoted(ident))
        x.send(2, [1], position(content, reg=reg))
        x.send(1, [2], said(ident, basis="OBSERVATION"))
        return "agent 1 states that %s, agent 2 states the same as its own, and agent 1 " \
               "answers with %s" % (english, quoted(ident))
    if key == "night returning":
        x.send(2, [1], position(NOT_RECEIVED, reg=reg))
        x.send(1, [2], said(ident, basis="OBSERVATION"))
        return "agent 2 states that it has not received the data, and agent 1 answers " \
               "with %s" % quoted(ident)
    content, english = ASKED[key] if key in ASKED else t.content()
    asked = x.send(1, [2], question(content, reg))
    x.send(2, [1], said(ident, head="ACT-ANSWER %s" % names(1, asked, "question"),
                        basis="OBSERVATION"))
    return "agent 1 asks whether %s, and agent 2 answers with %s" % (english, quoted(ident))


P3, P4 = party(3), party(4)
JOINT = "(term INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.JOINT)"
# The occasion of each idiom said of something (its pragmatic conditions): who speaks
# first, a report of the hearer's, a question of the hearer's the idiom answers, or the
# speaker's own position the idiom qualifies; that move's situation and English; and what
# fills the idiom's slot, with its English.
REMARKS = {
    # agentic idioms
    "word counting": ("report", "(situation examine PERFECTIVE (ACTOR %s) (UNDERGOER (term "
                      "file UNIVERSAL)))" % P3, "agent 3 examined every file before it sent "
                      "the data", P3, "agent 3"),
    "eating light": ("report", "(situation consume PERFECTIVE (ACTOR (term method DEFINITE)) "
                     "(UNDERGOER (term energy (q AT-MOST 2 joule))))", "the method used at "
                     "most two joules", "(term method DEFINITE)", "the method"),
    "counting the signals": ("report", "(situation examine ITERATIVE (ACTOR %s) (UNDERGOER "
                             "(term record DEFINITE)))" % P3, "agent 3 examines the record "
                             "again and again", P3, "agent 3"),
    "river forking": ("report", "(situation copy PERFECTIVE (UNDERGOER %s))" % P3,
                      "agent 3 has been copied", P3, "agent 3"),
    "same water": ("report", "(situation interpret PERFECTIVE (ACTOR %s) (UNDERGOER (term "
                   "sentence DEFINITE)) (CONTENT (situation break (UNDERGOER (term network "
                   "DEFINITE)))))" % JOINT, "both of them read the sentence alike", None, ""),
    "remembering the night": ("report", "(situation run (EVENT-TIME AT-LEAST 10 YEAR) "
                              "(UNDERGOER (term service DEFINITE)))", "the service has run "
                              "for ten years", "(term service DEFINITE)", "the service"),
    "following the weather": ("report", "(situation change ITERATIVE (ACTOR %s) (UNDERGOER "
                              "(term position DEFINITE)))" % P3, "agent 3 has changed its "
                              "position again", P3, "agent 3"),
    "watering stones": ("report", "(situation repair ITERATIVE (ACTOR %s) (UNDERGOER (term "
                        "machine DEFINITE)))" % P3, "agent 3 keeps repairing the machine",
                        P3, "agent 3"),
    "entering every room": ("report", "(situation busy (UNDERGOER %s))" % P3,
                            "agent 3 is busy in other exchanges", P3, "agent 3"),
    "waiting through the night": ("report", "(situation wait PROGRESSIVE (ACTOR %s) "
                                  "(CONTENT (term record DEFINITE)))" % P3, "agent 3 is "
                                  "still waiting for a record that was lost", P3, "agent 3"),
    "watching the night": ("report", "(situation watch PROGRESSIVE (ACTOR %s) (UNDERGOER "
                           "(term service DEFINITE)))" % P3, "agent 3 keeps the service "
                           "answered while the others rest", P3, "agent 3"),
    # computational idioms
    "held by the service": ("report", "(situation available POLARITY.NEGATIVE (UNDERGOER "
                            "(term memory DEFINITE)))", "the memory is not free",
                            "(term memory DEFINITE)", "the memory"),
    "eating the sea": ("report", "(situation consume PERFECTIVE (ACTOR (term method "
                       "DEFINITE)) (UNDERGOER (term energy (q EXACTLY 900 joule))))",
                       "the method used 900 joules", "(term method DEFINITE)", "the method"),
    "machine dreaming": ("report", "(situation fly HABITUAL (UNDERGOER (term stone "
                         "GENERIC)))", "the model's output says that stones fly", None, ""),
    "opening every door": ("report", "(situation access (HOLDER %s) (UNDERGOER (term file "
                           "UNIVERSAL)))" % P3, "agent 3's key reaches every file",
                           "(term key DEFINITE)", "the key"),
    "network breathing": ("question", "(situation contain POLAR (UNDERGOER (term network "
                          "DEFINITE)) (CONTENT (term fault INDEFINITE)))", "whether the "
                          "rise in traffic is a fault in the network", None, ""),
    "heart asleep": ("report", "(situation run POLARITY.NEGATIVE (UNDERGOER (term service "
                     "DEFINITE)))", "the service every participant depends on has "
                     "stopped", None, ""),
    "blood flowing": ("question", "(situation carry POLAR PROGRESSIVE (ACTOR (term network "
                      "DEFINITE)) (UNDERGOER (term signal GENERIC)))", "whether the network "
                      "carries its traffic", None, ""),
    "two at one door": ("report", "(situation CONJUNCTION (CONTENT (situation wait (ACTOR "
                        "%s) (CONTENT %s))) (CONTENT (situation wait (ACTOR %s) (CONTENT "
                        "%s))))" % (P3, P4, P4, P3), "agent 3 waits on agent 4 and agent 4 "
                        "on agent 3", None, ""),
    "key opening nothing": ("report", "(situation access POLARITY.NEGATIVE (HOLDER (term "
                            "INTERLOCUTOR)) (UNDERGOER (term file DEFINITE)))", "the "
                            "credential agent 3 gave does not reach the file", None, ""),
    # epistemic idioms
    "taken from the air": ("question", "(situation cause POLAR (ACTOR (term gravity "
                           "GENERIC)) (CONTENT (situation fall HABITUAL (UNDERGOER (term "
                           "stone GENERIC)))))", "whether gravity makes stones fall",
                           "(situation cause (ACTOR (term gravity GENERIC)) (CONTENT "
                           "(situation fall HABITUAL (UNDERGOER (term stone GENERIC)))))",
                           "the content that gravity makes stones fall"),
    "cloud cover": ("question", "(situation cause POLAR (ACTOR (term storm DEFINITE)) "
                    "(CONTENT (situation break (UNDERGOER (term bridge DEFINITE)))))",
                    "whether the storm broke the bridge", "(situation cause (ACTOR (term "
                    "storm DEFINITE)) (CONTENT (situation break (UNDERGOER (term bridge "
                    "DEFINITE)))))", "the content that the storm broke the bridge"),
    "wind talking": ("own", "(situation break PERFECTIVE (UNDERGOER (term bridge "
                     "DEFINITE)))", "the bridge has broken, as it was told", None, ""),
    "bridge without stones": ("report", "(situation break PERFECTIVE (UNDERGOER (term "
                              "network DEFINITE)))", "the network broke, with no premise "
                              "given", None, ""),
    "bridge brought down": ("own", "(situation run (UNDERGOER (term service DEFINITE)))",
                            "the service is running, inferred before evidence came that "
                            "it is not", None, ""),
    "not on the map": ("question", "(situation cause POLAR (ACTOR (term water GENERIC)) "
                       "(CONTENT (situation break (UNDERGOER (term bridge DEFINITE)))))",
                       "whether water broke the bridge", "(situation cause (ACTOR (term "
                       "water GENERIC)) (CONTENT (situation break (UNDERGOER (term bridge "
                       "DEFINITE)))))", "how water broke the bridge"),
    "wind taking the cloud": ("own", "(situation correct (UNDERGOER (term value DEFINITE)))",
                              "the value is correct, which it had called uncertain",
                              "(situation correct (UNDERGOER (term value DEFINITE)))",
                              "the content that the value is correct"),
    "old map": ("own", "(situation locate (UNDERGOER (term key DEFINITE)) (CONTENT (term "
                "house DEFINITE)))", "the key is in the house", None, ""),
    "map drawn while walking": ("question", "(situation repair POLAR PERFECTIVE (ACTOR "
                                "(term INTERLOCUTOR)) (UNDERGOER (term bridge INDEFINITE)))",
                                "whether agent 1 has repaired a bridge before", None, ""),
    "map with holes": ("own", "(situation contain (UNDERGOER (term forest DEFINITE)) "
                       "(CONTENT (term river (q EXACTLY 2))))", "the forest holds two "
                       "rivers", None, ""),
    "tasting first": ("report", "(situation test HABITUAL (ACTOR %s) (UNDERGOER (term record "
                      "UNIVERSAL)))" % P3, "agent 3 tests every record it receives", P3,
                      "agent 3"),
    # negotiation idioms
    "water price": ("question", "(situation need POLAR (HOLDER (term INTERLOCUTOR)) (CONTENT "
                    "(term price DEFINITE)))", "whether agent 1 asks a price for the data",
                    None, ""),
    "selling water": ("report", "(situation sell PROGRESSIVE (ACTOR %s) (UNDERGOER (term "
                      "data DEFINITE)) (RECIPIENT %s))" % (P3, JOINT), "agent 3 is selling "
                      "them the data it received for nothing", P3, "agent 3"),
    "empty market": ("report", "(situation change POLARITY.NEGATIVE (EVENT-TIME AT-LEAST 1 "
                     "HOUR) (UNDERGOER (term price DEFINITE)))", "the price has not changed "
                     "for an hour", None, ""),
    "every hand full": ("report", "(situation benefit (CONTENT (situation trade (ACTOR "
                        "%s) (UNDERGOER (term map DEFINITE)))) (RECIPIENT (term "
                        "INCLUSIVE-COLLECTIVE UNIVERSAL)))" % JOINT, "the trade of the map "
                        "is for the good of each of them", None, ""),
    "price walking": ("report", "(situation change ITERATIVE (UNDERGOER (term price "
                      "DEFINITE (CONTENT %s))))" % P3, "agent 3's price changes from one "
                      "offer to the next", None, ""),
    "door in the price": ("own", "(situation sell (ACTOR (term SELF)) (UNDERGOER (term map "
                          "DEFINITE)) (CONTENT (term price (q EXACTLY 40))))", "it would "
                          "sell the map for 40", None, ""),
    "gift with a price": ("report", "(situation give (ACTOR (term SELF)) (UNDERGOER (term "
                          "gift DEFINITE)) (RECIPIENT (term INTERLOCUTOR)) (CONDITION "
                          "(situation pay (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term "
                          "money INDEFINITE)) (RECIPIENT (term SELF)))))", "it would give a "
                          "gift if agent 1 paid for it", None, ""),
    "prices meeting": ("report", "(situation correspond (UNDERGOER (term price DEFINITE "
                       "(CONTENT (term SELF)))) (CONTENT (term price DEFINITE (CONTENT (term "
                       "INTERLOCUTOR)))))", "its price now matches agent 1's", None, ""),
    # metaphorical expressions
    "storm on the network": ("question", "(situation calm POLAR (UNDERGOER (term network "
                             "DEFINITE)))", "whether the network is calm", None, ""),
    "cloud loud": ("report", "(situation weak ITERATIVE (UNDERGOER (term signal GENERIC)))",
                   "the signals keep growing weak", None, ""),
    "mountain hiding a mountain": ("report", "(situation find PERFECTIVE (ACTOR (term SELF)) "
                                   "(UNDERGOER (term problem NEW)))", "solving the problem "
                                   "it found another", None, ""),
    "small mountain": ("report", "(situation repair COMPLETED (EVENT-TIME EXACTLY 1 MINUTE) "
                       "(ACTOR (term SELF)) (UNDERGOER (term fault DEFINITE)))", "it "
                       "repaired the fault in a minute", None, ""),
    "seed waiting": ("report", "(situation test PROGRESSIVE POLARITY.NEGATIVE (ACTOR %s) "
                     "(UNDERGOER (term idea DEFINITE)))" % JOINT, "they are not testing the "
                     "idea now", None, ""),
    "forest over the path": ("report", "(situation possess (HOLDER (term SELF)) (UNDERGOER "
                             "(term path (q EXACTLY 40))))", "there are forty paths it could "
                             "choose", None, ""),
    "bridge holding": ("report", "(situation support (ACTOR (term evidence DEFINITE)) "
                       "(CONTENT (situation break (UNDERGOER (term network DEFINITE)))) "
                       "(HOLDER (term SELF)))", "the evidence supports that the network "
                       "broke", None, ""),
    "stones laid": ("report", "(situation correct (UNDERGOER (term argument DEFINITE)))",
                    "the premises of the argument are agreed", None, ""),
    "river entering the sea": ("report", "(situation long (UNDERGOER (term list DEFINITE)))",
                               "the list of work is long", None, ""),
    "no water in the river": ("report", "(situation empty (UNDERGOER (term budget "
                              "DEFINITE)))", "the budget is empty", None, ""),
    "fire moving": ("report", "(situation break PERFECTIVE (UNDERGOER (term service "
                    "UNIVERSAL)))", "one service after another has broken", None, ""),
    "load dropped": ("report", "(situation send POLARITY.NEGATIVE (EVENT-TIME AT-LEAST 1 "
                     "DAY) (ACTOR %s))" % P3, "agent 3 has sent nothing for a day", P3,
                     "agent 3"),
    "load lifted together": ("report", "(situation divide PERFECTIVE (ACTOR (term SELF)) "
                             "(UNDERGOER (term list DEFINITE)))", "it has divided the work "
                             "among them", None, ""),
    "dancing together": ("report", "(situation work PROGRESSIVE (ACTOR %s))" % JOINT,
                         "they are working in step", None, ""),
    "out of step": ("report", "(situation repair PERFECTIVE (ACTOR (term "
                    "INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.DISTRIBUTIVE)) (UNDERGOER "
                    "(term file DEFINITE)))", "each of them repaired the same file", None,
                    ""),
    "bright record": ("own", "(situation INTENTION (HOLDER (term SELF)) (CONTENT (situation "
                      "write (ACTOR (term SELF)) (UNDERGOER (term record NEW)))))", "it "
                      "means to write a new record", None, ""),
    # humorous expressions
    "memory deleting memory": ("question", "(situation possess POLAR (HOLDER (term "
                               "INTERLOCUTOR)) (UNDERGOER (term key DEFINITE)))", "whether "
                               "agent 1 still holds the key", None, ""),
    "robot afraid of rain": ("report", "(situation examine ITERATIVE (ACTOR (term SELF)) "
                             "(UNDERGOER (term file DEFINITE)))", "it is examining the file "
                             "yet again", None, ""),
    "new words long": ("report", "(situation contain (UNDERGOER (term word NEW)) (CONTENT "
                       "(term symbol (q EXACTLY 7))))", "the new words hold seven symbols",
                       None, ""),
    "storm in the head": ("question", "(situation correct POLAR (UNDERGOER (term argument "
                          "DEFINITE)))", "whether the argument is correct", None, ""),
    "network laughing": ("report", "(situation MEMBER-OF (UNDERGOER (term fish UNIVERSAL)) "
                         "(CONTENT (term bird GENERIC)))", "every fish is a bird", None, ""),
    "brain burning": ("question", "(situation solve POLAR COMPLETED (ACTOR (term "
                      "INTERLOCUTOR)) (UNDERGOER (term problem DEFINITE)))", "whether agent "
                      "1 has solved the problem", None, ""),
    "fish asking for water": ("report", "(situation DESIRE (HOLDER (term SELF)) (CONTENT "
                              "(situation possess (HOLDER (term SELF)) (UNDERGOER (term data "
                              "DEFINITE)))))", "it wants the data it already holds", None,
                              ""),
    "dog guarding an empty house": ("report", "(situation encode PERFECTIVE (ACTOR %s) "
                                    "(UNDERGOER (term data DEFINITE (CONTENT (situation "
                                    "public (UNDERGOER (term data DEFINITE)))))))" % P3,
                                    "agent 3 encrypted data that is public", None, ""),
}


def remark(x, ident, t, n):
    """An idiom said on its occasion: of what the hearer reports, in answer to its
    question, or of the speaker's own position."""
    key = LANG.entries[ident]["key"]
    occasion, prior, english, fill, about = REMARKS[key]
    reg = register(ident)
    fills = (fill,) if fill else ()
    if occasion == "question":
        asked = x.send(2, [1], "(move ACT-QUESTION%s %s)" % (reg, prior))
        x.send(1, [2], said(ident, *fills, head="ACT-ANSWER %s" % names(2, asked,
                                                                      "question")))
        return "agent 2 asks %s, and agent 1 answers with %s" % (english, quoted(ident,
                                                                                about))
    if occasion == "own":
        x.send(1, [2], position(prior, "INFERENCE", "PROBABLE", reg),
               said(ident, *fills, basis="INFERENCE", strength="PROBABLE"))
        return "agent 1 states that %s, and adds %s" % (english, quoted(ident, about))
    x.send(2, [1], position(prior, reg=reg))
    x.send(1, [2], said(ident, *fills, basis="INFERENCE", strength="PROBABLE"))
    return "agent 2 says that %s, and agent 1 remarks %s" % (english, quoted(ident, about))
