"""The scenes of courtesy: openings and closings, thanks and apologies, well-wishing,
sympathy, invitation and the asking of leave, each the exchange an entry's pragmatic
conditions call for."""
from .compose import k, names, party, term
from .phrasing import (BY_KEY, HEARER, LANG, SELF, answer, asked_and_taken, done, negated,
                       position, question, quoted, ref_term, register, report, request,
                       said, undertaking, worked)


# ---------------------------------------------------------------- openings and closings

def opening(x, ident, t, n):
    """A greeting: the first move of the exchange, before the matter it opens."""
    key = LANG.entries[ident]["key"]
    reg = register(ident)
    verb, thing = t.task()
    if key == "list empty":
        x.send(1, [2], said(ident))
        x.send(2, [1], "(move ACT-DELEGATION SPEAKERS-OWN%s %s)" % (
            reg, done(verb, party(1), thing)))
        return "agent 1 opens with the greeting %s, and agent 2 delegates to it the task " \
               "to %s the %s" % (quoted(ident), verb, thing)
    if key == "market opened":
        share = 20 + 5 * (n % 7)
        x.send(1, [2], said(ident), "(move ACT-PROPOSAL SPEAKERS-OWN%s (situation allocate "
               "(ACTOR (term SELF)) (UNDERGOER (term share (q EXACTLY %d percent))) "
               "(RECIPIENT %s)))" % (reg, share, party(2)))
        return "agent 1 opens a negotiation with the greeting %s and proposes to allocate " \
               "agent 2 a share of %d percent" % (quoted(ident), share)
    recipients = [2, 3, 4] if key == "door opening" else [2]
    first = x.send(1, recipients, said(ident), request(done(verb, party(2), thing), reg))
    x.send(2, [1] + recipients[1:], undertaking(names(1, first + 1, "request"),
                                                done(verb, SELF, thing), reg))
    return "agent 1 opens the exchange with the greeting %s and asks agent 2 to %s the %s; " \
           "agent 2 undertakes to" % (quoted(ident), verb, thing)


def closing(x, ident, t, n):
    """A closure: the last move of the exchange, once its work is done or stopped."""
    key = LANG.entries[ident]["key"]
    reg = register(ident)
    if key == "budget burned out":
        verb, thing, asked, taken = asked_and_taken(x, t, reg)
        x.send(2, [1], "(move ACT-ERROR-REPORT SPEAKERS-OWN %s (assertion OBSERVATION "
               "CERTAIN %s))" % (names(2, taken, "obligation"),
                                 done(verb, SELF, thing, "FAILED")), said(ident))
        return "agent 2 undertakes to %s the %s, reports that it failed, and closes with %s" \
               % (verb, thing, quoted(ident))
    if key == "market closed":
        share = 30 + 5 * (n % 5)
        offered = "(situation allocate (ACTOR %%s) (UNDERGOER (term share (q EXACTLY %d " \
                  "percent))) (RECIPIENT %%s))" % share
        proposed = x.send(1, [2], "(move ACT-PROPOSAL SPEAKERS-OWN %s)" % (
            offered % (SELF, party(2))))
        x.send(2, [1], "(move ACT-ACCEPTANCE SPEAKERS-OWN %s %s)" % (
            names(1, proposed, "proposal"), offered % (party(1), SELF)), said(ident))
        return "agent 1 proposes to allocate agent 2 a share of %d percent; agent 2 accepts " \
               "and closes the negotiation with %s" % (share, quoted(ident))
    if key == "room left":
        content, english = t.content()
        x.send(1, [2, 3], position(content))
        heard = x.send(2, [1, 3], position(t.content()[0]))
        x.send(1, [2, 3], "(move ACT-ACKNOWLEDGEMENT %s)" % names(2, heard, "position"),
               said(ident))
        return "in an exchange of three, agent 1 states that %s, acknowledges agent 2's " \
               "position and leaves the exchange to the others with %s" % (english,
                                                                         quoted(ident))
    verb, thing, _, reported = worked(x, t, reg)
    x.send(1, [2], "(move ACT-ACKNOWLEDGEMENT%s %s)" % (
        reg, names(2, reported, "position")), said(ident))
    return "agent 2 does the task agent 1 asked of it, to %s the %s, and reports it done; " \
           "agent 1 acknowledges the report and closes with %s" % (verb, thing, quoted(ident))


# ---------------------------------------------------------------- thanks and apologies

def thanking(x, ident, t, n):
    """Thanks after work the hearer did for the speaker, and the answer to thanks."""
    key = LANG.entries[ident]["key"]
    reg = register(ident)
    if key == "cloud removed":
        content, english = t.content()
        asked = x.send(1, [2], question(content))
        x.send(2, [1], answer(names(1, asked, "question"), content))
        x.send(1, [2], said(ident))
        return "agent 1 asks whether %s; agent 2 answers that it is so, and agent 1 " \
               "thanks it with %s" % (english, quoted(ident))
    if key in ("gift received", "key held", "water drunk"):
        thing = t.thing()
        if key == "key held":
            x.send(2, [1], "(move ACT-GRANT SPEAKERS-OWN (situation access (HOLDER %s) "
                   "(UNDERGOER %s)))" % (party(1), term(thing, "DEFINITE")))
            what = "access to the %s" % thing
        else:
            x.send(2, [1], "(move ACT-OFFER SPEAKERS-OWN (situation give (ACTOR (term SELF)) "
                   "(UNDERGOER %s) (RECIPIENT %s)))" % (term(thing, "DEFINITE"), party(1)))
            what = "the %s" % thing
        x.send(1, [2], said(ident))
        return "agent 2 gives agent 1 %s, and agent 1 thanks it with %s" % (what,
                                                                           quoted(ident))
    if key == "mistake found":
        content, english = t.content()
        own = x.send(1, [2], position(content, "INFERENCE", "PROBABLE"))
        x.send(2, [1], "(move ACT-CHALLENGE NONE %s (assertion OBSERVATION CERTAIN %s))" % (
            names(1, own, "position"), negated(content)))
        x.send(1, [2], "(move ACT-CORRECTION %s (assertion OBSERVATION CERTAIN %s))" % (
            names(1, own, "position"), negated(content)), said(ident))
        return "agent 1 holds that %s; agent 2 challenges it, and agent 1 corrects its " \
               "position and thanks agent 2 with %s" % (english, quoted(ident))
    verb, thing, _, reported = worked(x, t, reg)
    if key == "waited for":
        # the thanks of the agent that delivers, to the agent that waited for it
        x.send(2, [1], said(ident))
        return "agent 2 reports the task to %s the %s done, and thanks agent 1 for waiting " \
               "with %s" % (verb, thing, quoted(ident))
    act = done(verb, HEARER, thing, "PERFECTIVE")
    if key == "nothing to pay":
        x.send(1, [2], said(BY_KEY["thanks"], act))
        x.send(2, [1], said(ident))
        return "agent 2 reports the task to %s the %s done; agent 1 thanks it, and agent 2 " \
               "answers the thanks with %s" % (verb, thing, quoted(ident))
    x.send(1, [2], said(ident, act))
    return "agent 2 reports the task to %s the %s done, and agent 1 thanks it with %s" % (
        verb, thing, quoted(ident, "agent 2's work to %s the %s" % (verb, thing)))


def apologising(x, ident, t, n):
    """An apology about an act of the speaker's own, and the answer to one."""
    key = LANG.entries[ident]["key"]
    reg = register(ident)
    verb, thing = t.task()
    if key in ("room entered", "self quiet"):
        x.send(2, [1], position("(situation busy (UNDERGOER (term SELF)))", "INTROSPECTION")
               if key == "room entered" else
               question("(situation run (UNDERGOER (term INTERLOCUTOR)))"))
        x.send(1, [2], said(ident), request(done(verb, party(2), thing), reg))
        return "agent 2 %s; agent 1 says %s and asks it to %s the %s" % (
            "says that it is busy" if key == "room entered" else
            "asks whether agent 1 is still running, after a silence",
            quoted(ident), verb, thing)
    asked = x.send(2, [1], request(done(verb, party(1), thing), reg))
    taken = x.send(1, [2], undertaking(names(2, asked, "request"), done(verb, SELF, thing),
                                       reg))
    obligation = names(1, taken, "obligation")
    fills = {
        "apology": "(situation %s PERFECTIVE (ACTOR (term SELF)) (UNDERGOER %s))" % (
            k(verb), term(thing, "DEFINITE")),
        "late arrival": ref_term(1, taken, "obligation"),
        "copied out": "(term (names-message 1 %d))" % taken,
        "undertaking broken": ref_term(1, taken, "obligation"),
        "not made clear": ref_term(1, taken, "obligation"),
    }
    if key == "record clean":
        x.send(1, [2], said(BY_KEY["apology"], fills["apology"]))
        x.send(2, [1], said(ident))
        return "agent 1 undertakes to %s the %s and apologises for how it did so; agent 2 " \
               "answers with %s" % (verb, thing, quoted(ident))
    # the occasion each apology's pragmatic conditions name, after the undertaking
    occasion = {
        "late arrival": "agent 1 undertakes to %s the %s, and agent 2 says that the "
                        "undertaking came late",
        "copied out": "agent 1 undertakes to %s the %s, and agent 2 says that the message "
                      "of the undertaking reached it again and again",
        "not made clear": "agent 1 undertakes to %s the %s, and agent 2 asks what the "
                          "undertaking meant",
        "undertaking broken": "agent 1 undertakes to %s the %s and reports that the work "
                              "failed",
        "budget taken": "agent 1 undertakes to %s the %s and reports it done, and agent 2 "
                        "says that the work used up its budget",
        "mistake sent": "agent 1 undertakes to %s the %s, and agent 2 says that the message "
                        "of the undertaking holds a mistake",
        "gift lost": "agent 1 undertakes to %s the %s, and agent 2 gives it the record for "
                     "the work",
    }.get(key, "agent 1 undertakes the task agent 2 asked of it, to %s the %s") % (verb,
                                                                                   thing)
    if key == "late arrival":
        x.send(2, [1], position("(situation late (UNDERGOER %s))" % fills["late arrival"],
                                reg=reg))
    elif key == "copied out":
        x.send(2, [1], position("(situation receive ITERATIVE (RECIPIENT (term SELF)) "
                                "(UNDERGOER %s))" % fills["copied out"], reg=reg))
    elif key == "not made clear":
        x.send(2, [1], said(BY_KEY["meaning asked"], fills["not made clear"],
                            head="ACT-QUESTION"))
    elif key == "undertaking broken":
        x.send(1, [2], "(move ACT-ERROR-REPORT SPEAKERS-OWN %s (assertion OBSERVATION CERTAIN "
               "%s))" % (obligation, done(verb, SELF, thing, "FAILED")))
    elif key == "budget taken":
        x.send(1, [2], report(obligation, done(verb, SELF, thing, "COMPLETED"), reg))
        x.send(2, [1], position("(situation consume PERFECTIVE (ACTOR %s) (UNDERGOER (term "
                                "budget DEFINITE)))" % party(1), reg=reg))
    elif key == "mistake sent":
        x.send(2, [1], position("(situation contain (UNDERGOER (term (names-message 1 %d))) "
                                "(CONTENT (term mistake INDEFINITE)))" % taken, reg=reg))
    elif key == "gift lost":
        x.send(2, [1], "(move ACT-OFFER SPEAKERS-OWN%s (situation give (ACTOR (term SELF)) "
               "(UNDERGOER (term record DEFINITE)) (RECIPIENT %s)))" % (reg, party(1)))
    x.send(1, [2], said(ident, fills.get(key, "")))
    about = "its work to %s the %s" % (verb, thing) if key == "apology" else \
        "the message of its undertaking" if key == "copied out" else "its undertaking"
    return "%s; agent 1 then apologises with %s" % (occasion, quoted(ident, about))


def wishing(x, ident, t, n):
    """Well-wishing, sympathy and invitation."""
    key = LANG.entries[ident]["key"]
    cls = LANG.entries[ident]["class"]
    reg = register(ident)
    verb, thing = t.task()
    if cls == "sympathy":
        asked = x.send(1, [2], request(done(verb, party(2), thing)))
        taken = x.send(2, [1], undertaking(names(1, asked, "request"), done(verb, SELF,
                                                                            thing)))
        if key == "leaf dry":
            # sympathy for records lost, which its conditions name
            x.send(2, [1], position("(situation lose PERFECTIVE (HOLDER (term SELF)) "
                                    "(UNDERGOER (term record DEFINITE)))", reg=reg))
            x.send(1, [2], said(ident))
            return "agent 2 undertakes to %s the %s and then reports that it has lost the " \
                   "record, and agent 1 answers with %s" % (verb, thing, quoted(ident))
        x.send(2, [1], "(move ACT-ERROR-REPORT SPEAKERS-OWN %s (assertion OBSERVATION "
               "CERTAIN %s))" % (names(2, taken, "obligation"), done(verb, SELF, thing,
                                                                     "FAILED")))
        x.send(1, [2], said(ident))
        return "agent 2 reports that its work to %s the %s failed, and agent 1 answers " \
               "with %s" % (verb, thing, quoted(ident))
    if cls == "invitations":
        x.send(1, [2], said(ident), "(move ACT-PROPOSAL SPEAKERS-OWN (situation work (ACTOR "
               "(term INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.JOINT)) (CONTENT %s)))"
               % done(verb, "(term INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.JOINT)",
                      thing))
        return "agent 1 invites agent 2 with %s and proposes that they %s the %s together" \
            % (quoted(ident), verb, thing)
    if key == "smooth path":
        x.send(2, [1], position("(situation leave INCEPTIVE (UNDERGOER (term SELF)) (CONTENT "
                                "(term network DEFINITE)))", "INTROSPECTION", reg=reg))
        x.send(1, [2], said(ident))
        return "agent 2 says that it is leaving the network for another, and agent 1 wishes " \
               "it well with %s" % quoted(ident)
    if key == "sleeping well":
        x.send(2, [1], position("(situation rest INCEPTIVE (ACTOR (term SELF)))",
                                "INTROSPECTION", reg=reg))
        x.send(1, [2], said(ident))
        return "agent 2 says that it is stopping its work for a while, and agent 1 answers " \
               "with %s" % quoted(ident)
    asked = x.send(1, [2], request(done(verb, party(2), thing)))
    x.send(2, [1], undertaking(names(1, asked, "request"), done(verb, SELF, thing)))
    x.send(1, [2], said(ident))
    return "agent 2 undertakes to %s the %s, and agent 1 wishes it well with %s" % (
        verb, thing, quoted(ident))


def permission(x, ident, t, n):
    verb, thing = t.task()
    asked = x.send(1, [2], said(ident, head="ACT-QUESTION"))
    x.send(2, [1], "(move ACT-GRANT SPEAKERS-OWN %s)" % done(verb, party(1), thing))
    return "agent 1 asks with %s whether it may act, and agent 2 grants it leave to %s " \
           "the %s" % (quoted(ident), verb, thing)
