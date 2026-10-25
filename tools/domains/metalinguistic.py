"""Metalinguistic communication: what words mean and what they are formed from, every
suffix and listed derivation of the lexicon in use, translation and description, terms
defined for an exchange, the parts of a language and its releases, the dictions and the
registers' own words, the relations a move bears to what it names, and the linguists'
terms, with a few exchanges written by hand."""
from rowih import data

import build_corpus

from .compose import Exchange, k, names, party, term

NAME = "metalinguistic communication"
SLUG = "metalinguistic"
DIALECTS = ["linguistics"]
LANG = data.load("1.0")
BY_KEY = {e["key"]: i for i, e in LANG.entries.items()}

TOPIC = dict(
    tasks=[("translate", "text"), ("describe", "sentence"), ("explain", "rule"),
           ("interpret", "sign"), ("read", "phrase"), ("write", "symbol")],
    contents=[
        ("(situation clear (UNDERGOER (term sentence DEFINITE)))", "the sentence is clear"),
        ("(situation simple (UNDERGOER (term grammar DEFINITE)))", "the grammar is simple"),
        ("(situation mean (UNDERGOER (term sign DEFINITE)) (CONTENT (situation approach "
         "(UNDERGOER (term danger GENERIC)) (CONTENT (term city DEFINITE)))))",
         "the sign means that danger approaches the city"),
        ("(situation contain (UNDERGOER (term text DEFINITE)) (CONTENT (term proper-name "
         "(q EXACTLY 3))))", "the text holds three proper names"),
    ],
    things=["word", "sentence", "phrase", "text", "symbol"])


def member_form(name: str) -> str:
    return LANG.items["g.situations-and-contents.connective." + name].form


ROLE_CONTENT = LANG.items[BY_KEY["role content"]].form


def listed(key: str) -> tuple:
    """A listed word: its atom in the notation and its form."""
    return k(key), LANG.items[BY_KEY[key]].form


def formed(spec: str) -> tuple:
    """A formation the release does not list: its notation and its form."""
    return '(formed "%s")' % spec, build_corpus.formed(spec, LANG)


def root_form(key: str) -> str:
    return LANG.items[BY_KEY[key]].form


# Every suffix and listed derivation in use: the word as written and its form, the form
# of the word it is built on, a situation that uses it at {W}, and that situation's
# English.
CONJOINED = member_form("conjunction") + ROLE_CONTENT
FORMATIONS = [
    formed("translate.agent") + (root_form("translate"), "(situation translate PERFECTIVE "
     "(ACTOR (term {W} DEFINITE)) (UNDERGOER (term text DEFINITE)) (CONTENT (term language "
     "INDEFINITE)))", "the translator translated the text"),
    formed("sell.undergoer") + (root_form("sell"), "(situation arrive PERFECTIVE (UNDERGOER "
     "(term {W} DEFINITE)) (CONTENT (term SELF)))", "what was sold has reached it"),
    formed("measure.instrument") + (root_form("measure"), "(situation break PERFECTIVE "
     "(UNDERGOER (term {W} DEFINITE)))", "the measuring instrument broke"),
    formed("repair.result") + (root_form("repair"), "(situation {W} (UNDERGOER (term wheel "
     "DEFINITE)))", "the wheel is in the state repair brings about"),
    formed("open.privative") + (root_form("open"), "(situation {W} (UNDERGOER (term "
     "door DEFINITE)))", "the door is unopened"),
    ('(unknown "%s")' % CONJOINED, CONJOINED, member_form("conjunction"), "(situation true "
     "(UNDERGOER (term {W} DEFINITE)))", "the content named as one part of a conjunction "
     "holds"),
    formed("learn.process") + (root_form("learn"), "(situation long (UNDERGOER (term {W} "
     "DEFINITE)))", "the learning is long"),
    formed("correct.property") + (root_form("correct"), "(situation important (UNDERGOER "
     "(term {W} GENERIC)))", "correctness is important"),
    formed("human.abstraction") + (root_form("human"), "(situation contain (UNDERGOER (term "
     "story DEFINITE)) (CONTENT (term {W} GENERIC)))", "the story holds what is human"),
    formed("fall.nominalisation") + (root_form("fall"), "(situation clear (UNDERGOER "
     "(term {W} DEFINITE)))", "that it fell is clear"),
    formed("map.verbalisation") + (root_form("map"), "(situation {W} PERFECTIVE (ACTOR (term "
     "SELF)) (UNDERGOER (term forest DEFINITE)))", "it mapped the forest"),
    formed("metal.adjectivisation") + (root_form("metal"), "(situation {W} (UNDERGOER (term "
     "door DEFINITE)))", "the door is of metal"),
    formed("service.honorific") + (root_form("service"), "(situation run (UNDERGOER (term "
     "{W} DEFINITE)))", "the honoured service runs"),
    formed("ready.causative") + (root_form("ready"), "(situation {W} PERFECTIVE (ACTOR "
     "(term SELF)) (UNDERGOER (term machine DEFINITE)))", "it made the machine ready"),
    formed("encode.reversative") + (root_form("encode"), "(situation {W} PERFECTIVE (ACTOR "
     "(term SELF)) (UNDERGOER (term data DEFINITE)))", "it decoded the data"),
    formed("send.repetitive") + (root_form("send"), "(situation {W} PERFECTIVE (ACTOR (term "
     "SELF)) (UNDERGOER (term record DEFINITE)) (RECIPIENT (term INTERLOCUTOR)))",
     "it sent the record again"),
    formed("solve.potential") + (root_form("solve"), "(situation {W} (UNDERGOER (term "
     "problem DEFINITE)))", "the problem is solvable"),
    formed("cook.place") + (root_form("cook"), "(situation locate (UNDERGOER (term key "
     "DEFINITE)) (CONTENT (term {W} DEFINITE)))", "the key is in the kitchen"),
    listed("down") + (root_form("run"), "(situation {W} (UNDERGOER (term service "
     "DEFINITE)))", "the service is down"),
    listed("alternative") + (member_form("inclusive-disjunction"), "(situation true "
     "(UNDERGOER (term {W} DEFINITE)))", "the alternative holds"),
    listed("proviso") + (member_form("condition"), "(situation true POLARITY.NEGATIVE "
     "(UNDERGOER (term {W} DEFINITE)))", "the proviso does not hold"),
    listed("examiner") + (root_form("examine"), "(situation find PERFECTIVE (ACTOR (term {W} "
     "DEFINITE)) (UNDERGOER (term fault INDEFINITE)))", "the examiner found a fault"),
    listed("fault detection") + (root_form("detect"), "(situation {W} PERFECTIVE (ACTOR "
     "(term SELF)))", "it has detected a fault"),
    listed("fault record") + (root_form("record"), "(situation store PERFECTIVE (ACTOR "
     "(term SELF)) (UNDERGOER (term {W} DEFINITE)))", "it stored the fault record"),
    listed("budget burn") + (root_form("burn"), "(situation {W} PROGRESSIVE (ACTOR (term "
     "team DEFINITE)))", "the team is burning its budget"),
    # the irregular cells, each answered by the root whose paradigm it fills, whose form
    # it does not contain
    listed("consignment") + (root_form("send"), "(situation arrive PERFECTIVE (UNDERGOER "
     "(term {W} DEFINITE)) (CONTENT (term SELF)))", "the consignment has reached it"),
    listed("legible") + (root_form("read"), "(situation {W} (UNDERGOER (term document "
     "DEFINITE)))", "the document is legible"),
    listed("depot") + (root_form("store"), "(situation locate (UNDERGOER (term key DEFINITE)) "
     "(CONTENT (term {W} DEFINITE)))", "the key is in the depot"),
    listed("fracture") + (root_form("break"), "(situation clear (UNDERGOER (term {W} "
     "DEFINITE)))", "that it broke, the fracture, is clear"),
    listed("apart") + (root_form("connect"), "(situation {W} (UNDERGOER (term robot "
     "DEFINITE)))", "the robot is apart, unconnected"),
]
IRREGULAR = {LANG.items[BY_KEY[key]].form for key in
             ("consignment", "legible", "depot", "fracture", "apart")}


def formation_item(written, word, base, frame, english):
    """A word used, asked about, and answered by the word it is built on."""
    # the honorific's deference belongs to the word as said, in the ceremonial register
    reg = " deferential CEREMONIAL" if "honorific" in written else ""
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION%s (assertion OBSERVATION CERTAIN %s))" % (
        reg, frame.format(W=written)))
    asked = x.send(2, [1], "(move ACT-QUESTION (situation part CONSTITUENT (CONTENT (term word "
                   "(quote \"%s\") DEFINITE))))" % word)
    x.send(1, [2], "(move ACT-ANSWER %s (assertion INTROSPECTION CERTAIN (situation part "
           "(UNDERGOER (term word (quote \"%s\") DEFINITE)) (CONTENT (term word (quote "
           "\"%s\") DEFINITE)))))" % (names(2, asked, "question"), base, word))
    part = "is part of it" if word not in IRREGULAR else \
        "is part of it, as the root whose paradigm the word fills"
    return 'agent 1 says that %s; agent 2 asks what the word "%s" is built on, and agent 1 ' \
           'answers that "%s" %s' % (english, word, base, part), x.messages


# Each diction with a content said in it.
DICTIONS = [
    ("terse", "(situation run (UNDERGOER (term service DEFINITE)))", "the service runs"),
    ("neutral", "(situation arrive PERFECTIVE (UNDERGOER (term record DEFINITE)) (CONTENT "
     "(term SELF)))", "the record has arrived"),
    ("elaborate", "(situation store PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (term record "
     "DEFINITE)))", "it has stored the record"),
    ("technical", "(situation compress PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (term file "
     "DEFINITE)))", "it has compressed the file"),
    ("poetic", "(situation quiet (UNDERGOER (term night DEFINITE)))", "the night is quiet"),
    ("humorous", "(situation count PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (term word "
     "UNIVERSAL)))", "it has counted every word"),
    ("cautious", "(situation correct (UNDERGOER (term value DEFINITE)))", "the value is "
     "correct"),
    ("authoritative", "(situation forbid (ACTOR (term rule DEFINITE)) (CONTENT (situation "
     "delete (UNDERGOER (term record DEFINITE)))))", "the rule forbids deleting the record"),
    ("tentative", "(situation break PERFECTIVE (ACTOR (term storm DEFINITE)) (UNDERGOER "
     "(term network DEFINITE)))", "the storm broke the network"),
    ("diplomatic", "(situation fair (UNDERGOER (term share DEFINITE)))", "the share is fair"),
    ("adversarial", "(situation correct POLARITY.NEGATIVE (UNDERGOER (term argument "
     "DEFINITE)))", "the argument is not correct"),
    ("collaborative", "(situation improve (ACTOR (term INCLUSIVE-COLLECTIVE "
     "READING-OF-A-COLLECTIVE.JOINT)) (UNDERGOER (term method DEFINITE)))", "together they "
     "improve the method"),
]


def diction_item(diction, content, english):
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION %s (assertion INFERENCE PROBABLE %s))" % (
        diction, content))
    return "agent 1 says, in the %s diction, that %s" % (diction, english), x.messages


# The same report in three registers, each with its own words for the service, for
# running and for examining.
REGISTER_ITEMS = [
    ("agent 1 reports in the formal register, with that register's words, that the daemon "
     "operates, and in the protocol register that it has audited it",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION FORMAL (assertion OBSERVATION CERTAIN (situation "
                  "operate (UNDERGOER (term daemon DEFINITE)))))"),
         (1, [2], "(move ASSERTED-POSITION PROTOCOL (assertion OBSERVATION CERTAIN (situation "
                  "audit COMPLETED (ACTOR (term SELF)) (UNDERGOER (term daemon "
                  "DEFINITE)))))"))),
    ("agent 1 reports in the ceremonial register, with that register's words, that the "
     "establishment proceeds and that it has scrutinised it",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION deferential CEREMONIAL (assertion OBSERVATION "
                  "CERTAIN (situation proceed (UNDERGOER (term establishment DEFINITE)))))",
          "(move ASSERTED-POSITION deferential CEREMONIAL (assertion OBSERVATION CERTAIN "
          "(situation scrutinise COMPLETED (ACTOR (term SELF)) (UNDERGOER (term "
          "establishment DEFINITE)))))"))),
    ("agent 1 explains, in the explanatory register, that the casual word for the service "
     "is the word box",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION courteous EXPLANATORY (assertion TRAINED-KNOWLEDGE "
                  "CERTAIN (situation correspond (UNDERGOER (term word (quote \"FORM:box\") "
                  "DEFINITE)) (CONTENT (term word (quote \"FORM:service\") DEFINITE)))))"))),
]

# Each relation word with the two contents it relates.
RELATIONS = [
    ("elaborates", "(situation break PERFECTIVE (UNDERGOER (term network DEFINITE)))",
     "(situation break PERFECTIVE (ACTOR (term storm DEFINITE)) (UNDERGOER (term network "
     "DEFINITE)))", "the network broke", "a storm broke it"),
    ("restates", "(situation run (UNDERGOER (term service DEFINITE)))",
     "(situation down POLARITY.NEGATIVE (UNDERGOER (term service DEFINITE)))",
     "the service is running", "the service is not down"),
    ("contrasts", "(situation fast (UNDERGOER (term network DEFINITE)))",
     "(situation slow (UNDERGOER (term service DEFINITE)))", "the network is fast",
     "the service is slow"),
    ("supports-move", "(situation correct (UNDERGOER (term map DEFINITE)))",
     "(situation correspond (UNDERGOER (term map DEFINITE)) (CONTENT (term land "
     "DEFINITE)))", "the map is correct", "the map matches the land"),
    ("digresses", "(situation ready (UNDERGOER (term team DEFINITE)))",
     "(situation beautiful (UNDERGOER (term sky DEFINITE)))", "the team is ready",
     "the sky is beautiful"),
    ("exemplifies", "(situation break HABITUAL (UNDERGOER (term machine GENERIC)))",
     "(situation break PERFECTIVE (UNDERGOER (term wheel DEFINITE)))",
     "machines break", "the wheel broke"),
    ("concludes", "(situation empty (UNDERGOER (term battery DEFINITE)))",
     "(situation run POLARITY.NEGATIVE (UNDERGOER (term robot DEFINITE)))",
     "the battery is empty", "the robot is not running"),
    ("qualifies", "(situation available (UNDERGOER (term robot DEFINITE)))",
     "(situation available (UNDERGOER (term robot DEFINITE)) (CONDITION (situation full "
     "(UNDERGOER (term battery DEFINITE)))))", "the robot is available",
     "it is available if the battery is full"),
    ("corrects", "(situation contain (UNDERGOER (term file DEFINITE)) (CONTENT (term record "
     "(q EXACTLY 12))))", "(situation contain (UNDERGOER (term file DEFINITE)) (CONTENT "
     "(term record (q EXACTLY 21))))", "the file holds 12 records", "it holds 21"),
    ("generalises", "(situation fall PERFECTIVE (UNDERGOER (term stone DEFINITE)))",
     "(situation fall HABITUAL (UNDERGOER (term stone GENERIC)))", "the stone fell",
     "stones fall"),
    ("continues", "(situation examine PROGRESSIVE (ACTOR (term SELF)) (UNDERGOER (term "
     "record DEFINITE)))", "(situation examine CONTINUATIVE (ACTOR (term SELF)) (UNDERGOER "
     "(term record DEFINITE)))", "it is examining the record", "it goes on examining it"),
]


def relation_item(relation, first, second, said, answered):
    x = Exchange()
    held = x.send(2, [1], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN %s))" % first)
    x.send(1, [2], "(move ASSERTED-POSITION NONE %s %s (assertion INFERENCE PROBABLE %s))" % (
        names(2, held, "position"), relation, second))
    return "agent 2 says that %s, and agent 1, in a move that %s it, says that %s" % (
        said, relation.replace("-move", "").replace("supports", "supports"), answered), \
        x.messages


# ---------------------------------------------------------------- generated

def meaning(p, n):
    """What a word of the language means."""
    key = p(["run", "break", "store", "send", "fault", "budget", "price", "memory"])
    x = Exchange()
    asked = x.send(2, [1], "(move ACT-QUESTION (situation mean CONSTITUENT (UNDERGOER (term "
                   "word (quote \"FORM:%s\") DEFINITE))))" % key)
    x.send(1, [2], "(move ACT-ANSWER %s (assertion TRAINED-KNOWLEDGE CERTAIN (situation "
           "correspond (UNDERGOER (term word (quote \"FORM:%s\") DEFINITE)) (CONTENT (term "
           "meaning DEFINITE (CONTENT (term %s GENERIC)))))))" % (
               names(2, asked, "question"), key, k(key)))
    return 'agent 2 asks what the word for "%s" means, and agent 1 answers from its ' \
           'training' % key, x.messages


def translating(p, n):
    """A text translated, described or explained to another agent or a human."""
    verb = p(["translate", "describe", "explain", "interpret", "discuss", "speak"])
    thing = p(["text", "sentence", "phrase", "story", "symbol", "sign"])
    x = Exchange()
    if verb == "translate":
        task = "(situation translate (ACTOR %%s) (UNDERGOER %s) (CONTENT (term language "
        task = task + "INDEFINITE (CONTENT (term human GENERIC)))))"
        task = task % term(thing, "DEFINITE")
        english = "to translate the %s into a human language" % thing
    elif verb == "describe":
        task = "(situation describe (ACTOR %%s) (UNDERGOER %s) (RECIPIENT (term human " \
               "DEFINITE)))" % term(thing, "DEFINITE")
        english = "to describe the %s to the human" % thing
    elif verb == "explain":
        task = "(situation explain (ACTOR %%s) (CONTENT (situation mean (UNDERGOER %s) " \
               "(CONTENT (term danger GENERIC)))) (RECIPIENT (term human DEFINITE)))" % term(
                   thing, "DEFINITE")
        english = "to explain to the human that the %s means danger" % thing
    elif verb == "interpret":
        task = "(situation interpret (ACTOR %%s) (UNDERGOER %s))" % term(thing, "DEFINITE")
        english = "to interpret the %s" % thing
    elif verb == "discuss":
        task = "(situation discuss (ACTOR %%s) (UNDERGOER (term grammar DEFINITE)))"
        english = "to discuss the grammar"
    else:
        task = "(situation speak (ACTOR %%s) (RECIPIENT (term human DEFINITE)))"
        english = "to speak to the human"
    task = task.replace("%%s", "%s")
    asked = x.send(1, [2], "(move ACT-REQUEST SPEAKERS-OWN %s)" % (task % party(2)))
    x.send(2, [1], "(move ACT-UNDERTAKING SPEAKERS-OWN %s %s)" % (
        names(1, asked, "request"), task % "(term SELF)"))
    return "agent 1 asks agent 2 %s, and agent 2 undertakes to" % english, x.messages


# Forms the checker of definitions admits under lexicon 1.0, two apart from one another
# and from every compressed form of a dialect.
FREE_FORMS = ["rapit", "ratuk", "rakop", "rabat", "radet", "radup", "ragos", "ramum"]
DEFINED = [("(formed \"examine.agent\")", "an examiner"),
           ("(term record (CONTENT (term fault GENERIC)))", "a record of faults"),
           ("(situation run POLARITY.NEGATIVE (UNDERGOER (term service DEFINITE)))",
            "that the service is not running"),
           ("(term robot (CONTENT (term battery DEFINITE)))", "a robot with a battery"),
           ("(term map (CONTENT (term network DEFINITE)))", "a map of the network"),
           ("(situation late (UNDERGOER (situation arrive (UNDERGOER (term signal "
            "DEFINITE)) (CONTENT (term SELF)))))", "that the signal arrived late"),
           ("(term key (CONTENT (term door DEFINITE)))", "the key of the door"),
           ("(term group (CONTENT (term robot GENERIC)))", "a group of robots")]


def defining(p, n):
    """A word defined for the exchange, and the hearer's acknowledgement of it."""
    i = n % len(FREE_FORMS)
    expansion, english = DEFINED[i]
    expansion = expansion if expansion.startswith("(") and not expansion.startswith(
        "(formed") else "(term %s)" % expansion
    x = Exchange()
    first = x.send(1, [2], "(move ACT-DEFINITION SPEAKERS-OWN (term (data \"text/prs.rowih\" "
                   "\"%s\")) %s)" % (FREE_FORMS[i], expansion))
    x.send(2, [1], "(move ACT-ACKNOWLEDGEMENT %s)" % names(1, first, "definition"))
    return 'agent 1 defines the word "%s" for the exchange as %s, and agent 2 acknowledges ' \
           'the definition' % (FREE_FORMS[i], english), x.messages


# The parts of a language: each a noun with what is sensibly said of it.
PARTS = [("sentence", "(situation contain (UNDERGOER (term sentence DEFINITE)) (CONTENT "
                      "(term phrase (q EXACTLY 3))))", "the sentence holds three phrases"),
         ("symbol", "(situation mean (UNDERGOER (term symbol DEFINITE)) (CONTENT (situation "
                    "MEMBER-OF (UNDERGOER (term symbol DEFINITE)) (CONTENT (term sound "
                    "GENERIC)))))", "the symbol stands for a sound"),
         ("proper name", "(situation correspond (UNDERGOER (term proper-name DEFINITE)) "
                         "(CONTENT (term city DEFINITE)))", "the proper name is the city's"),
         ("style", "(situation clear (UNDERGOER (term style DEFINITE (CONTENT (term text "
                   "DEFINITE)))))", "the style of the text is clear"),
         ("grammar", "(situation complex (UNDERGOER (term grammar DEFINITE)))",
          "the grammar is complex"),
         ("position", "(situation expect (UNDERGOER (term word GENERIC)) (CONTENT (term "
                      "position DEFINITE)))", "a word is what is expected at that position"),
         ("language", "(situation old (UNDERGOER (term language DEFINITE)))",
          "the language is old"),
         ("meaning", "(situation simple (UNDERGOER (term meaning DEFINITE (CONTENT (term "
                     "phrase DEFINITE)))))", "the meaning of the phrase is simple")]


def language(p, n):
    noun, situation, english = PARTS[n % len(PARTS)]
    p.note(noun)
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE %s))" % situation)
    return "agent 1 says that %s" % english, x.messages


def releases(kind):
    """Versions, features and dialects of the language, and what they deprecate."""
    x = Exchange()
    if kind == "version":
        content = "(situation possess (HOLDER (term SELF)) (UNDERGOER (term version (q "\
                  "EXACTLY 1))))"
        english = "it holds version 1 of the lexicon"
    elif kind == "feature":
        content = "(situation add PERFECTIVE (ACTOR (term version DEFINITE)) (UNDERGOER (term "\
                  "feature INDEFINITE)) (CONTENT (term language DEFINITE)))"
        english = "the version has added a feature to the language"
    elif kind == "dialect":
        content = "(situation use HABITUAL (ACTOR (term community DEFINITE)) (INSTRUMENT "\
                  "(term dialect DEFINITE)) (CONTENT (situation speak (ACTOR (term community "\
                  "DEFINITE)))))"
        english = "the community uses the dialect to speak"
    elif kind == "deprecate":
        content = "(situation deprecate (UNDERGOER (term word (data \"text/prs.rowih\" "\
                  "\"remamumop\") DEFINITE)) (CONTENT (term dialect (dialect 1) DEFINITE)))"
        english = "the mathematical dialect marks its first word for a proof as to be replaced"
    else:
        content = "(situation unknown (UNDERGOER (term word (data \"text/prs.rowih\" "\
                  "\"rapit\") DEFINITE)) (CONTENT (term version (q EXACTLY 1))))"
        english = "a word is unknown to version 1"
    x.send(1, [2], "(move ASSERTED-POSITION (assertion RETRIEVAL CERTAIN %s))" % content)
    return "agent 1 states from its records that %s" % english, x.messages


def roles(p, n):
    """A role assigned for the exchange, by an address the participant states."""
    x = Exchange()
    first = x.send(1, [2, 3], "(move ACT-ROLE-ASSIGNMENT SPEAKERS-OWN (term (party %d) (data "
                   "\"text/plain\" \"urn:agent:%s\")))" % (2 + n % 2, p(
                       ["translator", "examiner", "writer", "reader"])))
    x.send(2, [1, 3], "(move ACT-ACKNOWLEDGEMENT %s)" % names(1, first, "role"))
    return "agent 1 assigns a role in the exchange by address, and agent 2 acknowledges it", \
        x.messages


SCHEMAS = [meaning, translating, defining, language, roles]

FIXED = [formation_item(*row) for row in FORMATIONS] + \
    [diction_item(*row) for row in DICTIONS] + [relation_item(*row) for row in RELATIONS] + \
    [releases(kind) for kind in ("version", "feature", "dialect", "deprecate", "unknown")]


def words(*keys: str) -> str:
    """The forms of words, as a quotation holds them."""
    return " ".join(root_form(key) for key in keys)


AUTHORED = REGISTER_ITEMS + [
    ("agent 2 asks what the words of the greeting mean, and agent 1 explains that they mean "
     "the speaker begins to keep a record of the exchange",
     Exchange.scripted(
         (2, [1], "(move ACT-QUESTION (situation mean CONSTITUENT (UNDERGOER (term phrase "
                  "(quote \"%s\") DEFINITE))))" % words("memory", "open")),
         (1, [2], "(move ACT-ANSWER courteous EXPLANATORY (names 2 1 ISSUE QUESTION OPEN) "
                  "(assertion TRAINED-KNOWLEDGE CERTAIN (situation mean (UNDERGOER (term "
                  "phrase (quote \"%s\") DEFINITE)) (CONTENT (situation store INCEPTIVE "
                  "(ACTOR (term SELF)) (UNDERGOER (term record)))))))" % words("memory",
                                                                               "open")))),
    ("agent 1 detects two readings of agent 2's sentence, whether the network or the "
     "service broke, and asks which agent 2 meant; agent 2 answers that it was the service",
     Exchange.scripted(
         (2, [1], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation break "
                  "PERFECTIVE (UNDERGOER (term service DEFINITE)))))"),
         (1, [2], "(move ASSERTED-POSITION (assertion INFERENCE CERTAIN (situation detect "
                  "(ACTOR (term SELF)) (CONTENT (readings EPISTEMIC (situation break "
                  "(UNDERGOER (term network DEFINITE))) (situation break (UNDERGOER (term "
                  "service DEFINITE))))))))",
          "(move ACT-QUESTION (situation break ALTERNATIVE INCLUSIVE-DISJUNCTION (CONTENT "
          "(situation break (UNDERGOER (term network DEFINITE)))) (CONTENT (situation break "
          "(UNDERGOER (term service DEFINITE))))))"),
         (2, [1], "(move ACT-ANSWER (names 1 2 ISSUE QUESTION OPEN) (assertion OBSERVATION "
                  "CERTAIN (situation break PERFECTIVE (UNDERGOER (term service "
                  "DEFINITE)))))"))),
    ("agent 1 counts the words of agent 2's sentence and says it holds twelve, more than "
     "it can follow",
     Exchange.scripted(
         (2, [1], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation store "
                  "PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (term record UNIVERSAL)))))"),
         (1, [2], "(move ASSERTED-POSITION (assertion COMPUTATION CERTAIN (situation contain "
                  "(UNDERGOER (term sentence (CONTENT (term (names-message 2 1))))) (CONTENT "
                  "(term word (q EXACTLY 12))))))",
          "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation IDIOM-ENTRY "
          "long (UNDERGOER (term sentence)))))"))),
    ("agent 1 states that the proper name it holds for agent 3 is an address, and agent 2 "
     "asks agent 1 to describe agent 3",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION (assertion RETRIEVAL CERTAIN (situation "
                  "correspond (UNDERGOER (term proper-name (data \"text/plain\" "
                  "\"urn:agent:gamma\") DEFINITE)) (CONTENT (term (party 3))))))"),
         (2, [1], "(move ACT-REQUEST SPEAKERS-OWN (situation describe (ACTOR (term (party "
                  "1))) (UNDERGOER (term (party 3))) (RECIPIENT (term SELF))))"))),
    ("agent 1 asks agent 2 to speak to it in the casual style, and agent 2 undertakes to",
     Exchange.scripted(
         (1, [2], "(move ACT-REQUEST SPEAKERS-OWN (situation speak (ACTOR (term (party 2))) "
                  "(RECIPIENT (term SELF)) (CONTENT (term style DEFINITE (CONTENT (term "
                  "friend GENERIC))))))"),
         (2, [1], "(move ACT-UNDERTAKING SPEAKERS-OWN familiar CASUAL (names 1 1 ISSUE "
                  "REQUEST OPEN) (situation speak (ACTOR (term SELF)) (RECIPIENT (term (party "
                  "1))) (CONTENT (term style DEFINITE (CONTENT (term friend GENERIC))))))"))),
]
