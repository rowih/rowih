"""The scenes of work: reports of its state, requests for status and the compressed
answers to them, offers of help, praise and encouragement, reminders and the taking of
turns."""
from .compose import k, names, party, term
from .occasions import ASKED, conversational
from .phrasing import (BY_KEY, HEARER, LANG, SELF, answer, asked_and_taken, done,
                       position, question, quoted, ref_term, register, request, said,
                       undertaking, worked)


# ---------------------------------------------------------------- work and its status

def status(x, ident, t, n):
    """A report of the state of work, in answer to a question about it."""
    key = LANG.entries[ident]["key"]
    reg = register(ident)
    verb, thing, asked, taken = asked_and_taken(x, t, reg)
    task = done(verb, SELF, thing)
    if key == "fire lit":
        x.send(2, [1], said(ident))
        return "agent 1 asks agent 2 to %s the %s; agent 2 undertakes it and reports that " \
               "it has begun with %s" % (verb, thing, quoted(ident))
    q = x.send(1, [2], question("(situation progress (UNDERGOER %s))" % done(
        verb, party(2), thing)))
    fill = ref_term(2, taken, "obligation") if key in ("between the hands", "left the hand") \
        else task
    x.send(2, [1], said(ident, fill, head="ACT-ANSWER %s" % names(1, q, "question")))
    return "agent 1 asks agent 2 to %s the %s and later asks how the work stands; agent 2 " \
           "answers with %s" % (verb, thing, quoted(ident, "the work"))


# The answer to each request for status, an expression whose own conditions the question
# meets, or, where none says what the question asks, the plain statement of it.
STATUS_ANSWERS = {"river flowing?": "working", "path measured": "working",
                  "still running?": "working", "news arriving?": "quiet network",
                  "money measured": None, "list empty?": "done"}


def asking_status(x, ident, t, n):
    """A request for status, answered by the expression for its answer."""
    key = LANG.entries[ident]["key"]
    reg = register(ident)
    verb, thing, asked, taken = asked_and_taken(x, t, reg)
    q = x.send(1, [2], said(ident, head="ACT-QUESTION"))
    if STATUS_ANSWERS[key] is None:
        x.send(2, [1], answer(names(1, q, "question"), "(situation enough (UNDERGOER %s) "
                              "(CONTENT %s))" % (term("budget", "DEFINITE"),
                                                 done(verb, SELF, thing)), "INTROSPECTION"))
        return "agent 1 asks agent 2 to %s the %s and, while it works, asks %s; agent 2 " \
               "answers that its budget is enough for the work" % (verb, thing, quoted(ident))
    reply = BY_KEY[STATUS_ANSWERS[key]]
    x.send(2, [1], said(reply, head="ACT-ANSWER %s" % names(1, q, "question"),
                        basis="OBSERVATION"))
    return "agent 1 asks agent 2 to %s the %s and, while it works, asks %s; agent 2 " \
           "answers %s" % (verb, thing, quoted(ident), quoted(reply))


def compressed(x, ident, t, n):
    """A compressed answer to a request for status about the act it names."""
    e = LANG.entries[ident]
    if e["key"] in ASKED:
        return conversational(x, ident, t, n)
    if e["key"] == "share missing":
        # of a message that arrived cut short
        content, english = t.content()
        x.send(2, [1], position(content))
        x.send(1, [2], said(ident, basis="OBSERVATION"))
        return "agent 2 states that %s; the message reaches agent 1 cut short, and agent 1 " \
               "says %s" % (english, quoted(ident))
    literal = e["literal structure"]
    words = literal.replace("(", " ").replace(")", " ").split()
    verb, thing = words[1], words[-1]
    if "UNDERGOER" not in literal:
        verb, thing = t.task()
    asked = x.send(1, [2], request(done(verb, party(2), thing)))
    taken = x.send(2, [1], undertaking(names(1, asked, "request"), done(verb, SELF, thing)))
    q = x.send(1, [2], question("(situation progress (UNDERGOER %s))" % done(
        verb, party(2), thing)))
    x.send(2, [1], said(ident, head="ACT-ANSWER %s" % names(1, q, "question"),
                        basis="OBSERVATION"))
    return "agent 1 asks agent 2 to %s the %s and later asks how the work stands; agent 2 " \
           "answers %s" % (k(verb).replace("-", " "), thing, quoted(ident))


def offering(x, ident, t, n):
    key = LANG.entries[ident]["key"]
    verb, thing = t.task()
    prompt = {
        "arm free": position("(situation busy (UNDERGOER (term SELF)))", "INTROSPECTION"),
        "budget to spare": position("(situation lack-resource (HOLDER (term SELF)) (CONTENT "
                                    "%s))" % done(verb, SELF, thing), "INTROSPECTION"),
        "memory published": position("(situation lack-knowledge (HOLDER (term SELF)) "
                                     "(CONTENT %s))" % done(verb, SELF, thing),
                                     "INTROSPECTION"),
        "counting again": position("(situation INTENTION (HOLDER (term SELF)) (CONTENT "
                                   "(situation execute (ACTOR (term SELF)) (UNDERGOER (term "
                                   "program DEFINITE)))))", "INTROSPECTION"),
    }.get(key, position(done(verb, SELF, thing, "PROGRESSIVE"), "INTROSPECTION"))
    x.send(2, [1], prompt)
    work = done(verb, HEARER, thing)
    x.send(1, [2], said(ident, work), "(move ACT-OFFER SPEAKERS-OWN (situation help (ACTOR "
           "(term SELF)) (RECIPIENT %s) (CONTENT %s)))" % (party(2), work))
    return "agent 2 states how its work to %s the %s stands, and agent 1 offers its help " \
           "with %s" % (verb, thing, quoted(ident, "agent 2's work"))


def after_work(x, ident, t, n):
    """Praise, congratulations or encouragement for the hearer's work."""
    key = LANG.entries[ident]["key"]
    reg = register(ident)
    cls = LANG.entries[ident]["class"]
    if cls == "encouragement":
        verb, thing, asked, taken = asked_and_taken(x, t, reg)
        if key == "top near":
            # to an agent near the end of long work, which says it is finishing
            x.send(2, [1], position(done(verb, SELF, thing, "COMPLETIVE"), "INTROSPECTION"))
            x.send(1, [2], said(ident))
            return "agent 2 undertakes to %s the %s and, long into the work, says that it " \
                   "is finishing; agent 1 encourages it with %s" % (verb, thing,
                                                                    quoted(ident))
        x.send(2, [1], position("(situation difficult (UNDERGOER %s))" % done(
            verb, SELF, thing), "INTROSPECTION"))
        x.send(1, [2], said(ident))
        return "agent 2 undertakes to %s the %s and says the work is hard; agent 1 " \
               "encourages it with %s" % (verb, thing, quoted(ident))
    verb, thing, _, reported = worked(x, t, reg)
    x.send(1, [2], said(ident))
    return "agent 2 reports the task to %s the %s done, and agent 1 answers with %s" % (
        verb, thing, quoted(ident))


def reminding(x, ident, t, n):
    verb, thing, asked, taken = asked_and_taken(x, t, "")
    x.send(1, [2], said(ident, ref_term(2, taken, "obligation")))
    return "agent 2 undertakes to %s the %s, and agent 1 later reminds it with %s" % (
        verb, thing, quoted(ident, "agent 2's undertaking"))


def turn(x, ident, t, n):
    """A turn in an exchange of three whose turns are taken in order."""
    key = LANG.entries[ident]["key"]
    content, english = t.content()
    if key == "voice taken":
        x.send(1, [2, 3], position(content), said(BY_KEY["voice given"]))
        x.send(2, [1, 3], said(ident), position(t.content()[0]))
        return "agent 1 states that %s and gives the turn to agent 2, which takes it " \
               "with %s" % (english, quoted(ident))
    if key == "voice not cut":
        x.send(1, [2, 3], position(content))
        x.send(1, [2, 3], said(ident, head="ACT-REQUEST SPEAKERS-OWN"),
               position(t.content()[0]))
        return "agent 1 states that %s and, before agent 2 takes the turn, asks with %s " \
               "to finish" % (english, quoted(ident))
    x.send(1, [2, 3], position(content), said(ident))
    return "agent 1 states that %s and ends its part with %s" % (english, quoted(ident))
