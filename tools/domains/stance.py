"""The scenes of stance: warnings, agreement and disagreement with a position, a plan or
an offer, refusals and the statement of how far the speaker holds a content."""
from .compose import names, party, term
from .phrasing import (BY_KEY, LANG, SELF, done, negated, position, question, quoted,
                       ref_term, register, request, said)


# ---------------------------------------------------------------- warnings, positions, doubts

# The move each warning prompts the speaker to ask for.
WARNED = {
    "budget falling": "(situation decrease (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term "
                      "resource DEFINITE)))",
    "night approaching": "(situation send (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term "
                         "record DEFINITE)) (RECIPIENT (term SELF)))",
    "dirty data": "(situation use POLARITY.NEGATIVE (ACTOR (term INTERLOCUTOR)) "
                  "(INSTRUMENT (term data DEFINITE)))",
    "enemy approaching": "(situation shut (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term "
                         "interface DEFINITE)))",
    "wheel turning": "(situation shut (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term program "
                     "DEFINITE)))",
    "signals piling": "(situation decrease (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term "
                      "signal GENERIC)))",
    "memory letting go": "(situation store (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term "
                         "record DEFINITE)))",
    "watched by a third": "(situation encode (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term "
                          "data DEFINITE)))",
    "dark address": "(situation authenticate (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term "
                    "document DEFINITE)))",
}


def warning(x, ident, t, n):
    key = LANG.entries[ident]["key"]
    thing = t.thing()
    fill = term("record" if key == "memory letting go" else
                "network" if key == "watched by a third" else thing, "DEFINITE")
    follow = WARNED.get(key)
    moves = [said(ident, fill, basis="INFERENCE", strength="PROBABLE")]
    if follow:
        moves.append("(move ACT-RECOMMENDATION %s)" % follow)
    x.send(1, [2], *moves)
    x.send(2, [1], said(BY_KEY["wind heard"]))
    about = "the record" if key == "memory letting go" else \
        "the network" if key == "watched by a third" else \
        "the change to the " + thing if key == "no way back" else "the " + thing
    return "agent 1 warns agent 2 with %s%s, and agent 2 acknowledges the warning" % (
        quoted(ident, about), ", recommending what to do" if len(moves) > 1 else "")


# The entries said in declining a request or a proposal, with the hearer's move first.
DECLINING = ("price high", "not followed", "beyond the boundary", "too early",
             "far beyond the budget", "list full", "door shut by rule")


def declining(x, ident, t, key, reg):
    """A request or a proposal of the hearer's, declined with the entry."""
    verb, thing = t.task()
    if key == "price high":
        asked_for = "(situation sell (ACTOR (term SELF)) (UNDERGOER %s) (RECIPIENT %s))" % (
            term(thing, "DEFINITE"), party(1))
        heard = x.send(2, [1], "(move ACT-PROPOSAL SPEAKERS-OWN%s %s)" % (reg, asked_for))
        target, what = names(2, heard, "proposal"), "proposes to sell agent 1 the %s" % thing
        restated = asked_for.replace("(ACTOR (term SELF))", "(ACTOR %s)" % party(2)).replace(
            party(1), SELF)
    else:
        asked_for = done(verb, party(1), thing)
        heard = x.send(2, [1], request(asked_for, reg))
        target, what = names(2, heard, "request"), "asks agent 1 to %s the %s" % (verb, thing)
        restated = asked_for.replace(party(1), SELF)
    # declining a request is operative and claims authority; declining a proposal is not
    authority = "" if key == "price high" else " SPEAKERS-OWN"
    x.send(1, [2], "(move ACT-REJECTION%s%s %s %s)" % (authority, reg, target, restated),
           said(ident, asked_for.replace(party(1), SELF)))
    return "agent 2 %s; agent 1 declines, saying %s" % (what, quoted(ident,
                                                                    "the task asked of it"))


def answering_position(x, ident, t, n):
    """Agreement or disagreement with a position, a plan or a proposal of the hearer's."""
    key = LANG.entries[ident]["key"]
    reg = register(ident)
    content, english = t.content()
    cls = LANG.entries[ident]["class"]
    if key in DECLINING:
        return declining(x, ident, t, key, reg)
    if key in ("ground flat", "key handed over"):
        asked = x.send(2, [1], question(
            "(situation work CONTINUATIVE (ACTOR (term SELF)) (CONTENT %s))" % content
            if key == "ground flat" else content, reg))
        x.send(1, [2], said(ident, head="ACT-ANSWER %s" % names(2, asked, "question")))
        return "agent 2 asks %s; agent 1 answers with %s" % (
            "whether it may go on with its work" if key == "ground flat" else
            "whether %s" % english, quoted(ident))
    if key == "drawing the map":
        x.send(2, [1], "(move SUPPOSITION%s %s)" % (reg, content))
        x.send(1, [2], said(ident, content))
        return "agent 2 supposes that %s, and agent 1 answers with %s" % (
            english, quoted(ident, "the content that " + english))
    if key == "not my meaning":
        own = x.send(1, [2], position(content))
        heard = x.send(2, [1], position("(situation mean (UNDERGOER %s) (CONTENT %s))" % (
            ref_term(1, own, "position"), negated(content)), "INFERENCE", "PROBABLE"))
        x.send(1, [2], said(ident, ref_term(2, heard, "position")))
        return "agent 1 states that %s; agent 2 reads it otherwise, and agent 1 answers " \
               "with %s" % (english, quoted(ident, "agent 2's reading"))
    heard = x.send(2, [1], position(content, "INFERENCE", "PROBABLE", reg))
    if cls == "agreement":
        head = "ACT-CONFIRMATION %s" % names(2, heard, "position")
    else:
        head = "ACT-CHALLENGE NONE %s" % names(2, heard, "position")
    x.send(1, [2], said(ident, *(() if key == "argument weak" else (content,)), head=head))
    return "agent 2 holds that %s, and agent 1 %s with %s" % (
        english, "agrees" if cls == "agreement" else "disagrees",
        quoted(ident, "the content that " + english))


def doubting(x, ident, t, n):
    """An answer that states how far the speaker holds what it is asked."""
    content, english = t.content()
    asked = x.send(2, [1], question(content))
    x.send(1, [2], said(ident, content, head="ACT-ANSWER %s" % names(2, asked, "question")))
    return "agent 2 asks whether %s, and agent 1 answers with %s" % (
        english, quoted(ident, "the content that " + english))
