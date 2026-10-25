"""The scenes of grounding, by which the participants keep what they hold in common:
acknowledgement, confirmation, requests for clarification and the repair of messages
lost, damaged or misread."""
from .compose import k, names, party, term
from .phrasing import (BY_KEY, LANG, SELF, answer, done, negated, position, question,
                       quoted, ref_term, register, request, said, undertaking)

# A word the reader's release lacks, carried as declared data and not quoted as a word.
LACKED = "(term word (data \"text/prs.rowih\" \"rapeb\") DEFINITE)"
# The English past participles of the tasks' verbs that do not add -ed or -d.
PAST = {"read": "read", "write": "written"}


# ---------------------------------------------------------------- acknowledging and confirming

# What each acknowledgement answers: the kind of move the hearer sent.
ACKNOWLEDGED = {"at the door": "request", "before the eye": "question",
                "on the list": "request", "words being written": "question"}


def acknowledging(x, ident, t, n):
    key = LANG.entries[ident]["key"]
    reg = register(ident)
    content, english = t.content()
    kind = ACKNOWLEDGED.get(key, "position")
    if key == "every signal counted":
        for _ in range(3):
            first = x.send(2, [1], position(t.content()[0], reg=reg))
        x.send(1, [2], "(move ACT-ACKNOWLEDGEMENT %s)" % names(2, first, "position"),
               said(ident))
        return "agent 2 sends three positions in turn, and agent 1 acknowledges the last " \
               "with %s" % quoted(ident)
    if key == "record moved aside":
        own = x.send(1, [2], position(content, "INFERENCE", "PROBABLE"))
        x.send(2, [1], "(move ACT-CHALLENGE NONE %s (assertion OBSERVATION CERTAIN %s))" % (
            names(1, own, "position"), negated(content)))
        x.send(1, [2], "(move ACT-CORRECTION %s (assertion OBSERVATION CERTAIN %s))" % (
            names(1, own, "position"), negated(content)), said(ident))
        return "agent 1 holds that %s; agent 2 challenges it, and agent 1 corrects itself, " \
               "saying %s" % (english, quoted(ident))
    if key == "waiting":
        promised = x.send(2, [1], "(move ACT-PROMISE SPEAKERS-OWN (situation send (ACTOR "
                          "(term SELF)) (UNDERGOER (term record NEW)) (RECIPIENT %s)))"
                          % party(1))
        x.send(1, [2], "(move ACT-ACKNOWLEDGEMENT %s)" % names(2, promised, "commitment"),
               said(ident))
        return "agent 2 promises to send agent 1 more records, and agent 1 acknowledges " \
               "with %s" % quoted(ident)
    verb, thing = t.task()
    heard = {"request": request(done(verb, party(1), thing), reg),
             "question": question(content, reg)}.get(kind, position(content, reg=reg))
    if key == "wind heard":
        heard = said(BY_KEY["not quiet"], term(t.thing(), "DEFINITE"), basis="INFERENCE",
                     strength="PROBABLE")
    recipients = [1, 3] if key == "thrown on" else [1]
    first = x.send(2, recipients, heard)
    target = names(2, first, "position" if key == "wind heard" else kind)
    x.send(1, [2], "(move ACT-ACKNOWLEDGEMENT%s %s)" % (reg, target),
           said(ident, "(term %s)" % target))
    what = {"request": "asks agent 1 to %s the %s" % (verb, thing),
            "question": "asks whether %s" % english}.get(kind, "states that %s" % english)
    if key == "wind heard":
        what = "warns agent 1 of a problem"
    return "agent 2 %s, and agent 1 acknowledges the move with %s" % (
        what, quoted(ident, "agent 2's move"))


# The basis on which each confirmation confirms.
CONFIRMED = {"memory agrees": "RETRIEVAL", "world compared": "OBSERVATION",
             "value encoded": "COMPUTATION", "rule passed": "INFERENCE",
             "unmoved by wind": "OBSERVATION", "a third described it": "REPORT",
             "a third compared it": "REPORT", "the model agrees": "SIMULATION"}


def confirming(x, ident, t, n):
    key = LANG.entries[ident]["key"]
    content, english = t.content()
    if key == "key turned":
        sent = x.send(2, [1], position(content))
        x.send(1, [2], said(ident, "(term (names-message 2 %d))" % sent, basis="OBSERVATION"))
        return "agent 2 states that %s, and agent 1 confirms that the message is agent 2's " \
               "with %s" % (english, quoted(ident, "agent 2's message"))
    if key == "meaning matched":
        own = x.send(1, [2], position(content))
        asked = x.send(2, [1], question("(situation mean (UNDERGOER %s) (CONTENT %s))" % (
            ref_term(1, own, "position"), content)))
        x.send(1, [2], said(ident, ref_term(2, asked, "question"),
                            head="ACT-ANSWER %s" % names(2, asked, "question")))
        return "agent 1 states that %s; agent 2 asks whether that is what it meant, and " \
               "agent 1 answers with %s" % (english, quoted(ident, "agent 2's question"))
    heard = x.send(2, [1], position(content))
    x.send(1, [2], said(ident, content, head="ACT-CONFIRMATION %s" % names(2, heard,
                                                                            "position"),
                        basis=CONFIRMED[key]))
    return "agent 2 states that %s, and agent 1 confirms it with %s" % (
        english, quoted(ident, "the content that " + english))


# ---------------------------------------------------------------- clarification and repair

def clarifying(x, ident, t, n):
    """A question or a request about the hearer's move, and the hearer's answer."""
    key = LANG.entries[ident]["key"]
    content, english = t.content()
    verb, thing = t.task()
    answered = content
    if key in ("steps asked", "where to cut", "reason sought", "reward sought",
               "plain words asked", "lost from the map"):
        heard = x.send(2, [1], request(done(verb, party(1), thing)))
        target, what = names(2, heard, "request"), "asks agent 1 to %s the %s" % (verb,
                                                                                 thing)
        if key == "lost from the map":
            answered = "(situation inside (UNDERGOER %s) (CONTENT (term room DEFINITE)))" % \
                term(thing, "DEFINITE")
    elif key == "maker sought":
        # work stated without its agent, whose agent the question asks for
        work = "(situation %s PERFECTIVE (UNDERGOER %s))" % (k(verb), term(thing,
                                                                          "DEFINITE"))
        heard = x.send(2, [1], position(work))
        target, what = names(2, heard, "position"), "states that the %s has been %s, " \
            "without saying by whom" % (thing, PAST.get(verb, verb + (
                "d" if verb.endswith("e") else "ed")))
        content = work
        answered = work.replace("(UNDERGOER", "(ACTOR %s) (UNDERGOER" % party(3), 1)
    elif key == "version sought":
        heard = x.send(2, [1], position(content))
        target, what = names(2, heard, "position"), "states that %s with a word agent 1's " \
            "release lacks" % english
        answered = "(situation contain (UNDERGOER (term version (q EXACTLY 2))) (CONTENT " \
            "%s))" % LACKED
    elif key == "meaning asked":
        # a move the speaker leaves open between two readings
        other, other_english = t.content()
        heard = x.send(2, [1], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN "
                       "(readings STRATEGIC %s %s)))" % (content, other))
        target, what = names(2, heard, "position"), "states, leaving it open, that %s or " \
            "that %s" % (english, other_english)
    elif key == "compared with stone":
        heard = x.send(2, [1], "(move ASSERTED-POSITION (assertion OBSERVATION %s))" % content)
        target, what = names(2, heard, "position"), "states that %s, without saying how " \
            "strongly" % english
    elif key == "laughing":
        heard = x.send(2, [1], position(content, reg=" familiar PLAYFUL"))
        target, what = names(2, heard, "position"), "says, playfully, that %s" % english
    elif key == "next step":
        heard = x.send(2, [1], position(done(verb, SELF, thing, "COMPLETED")))
        target, what = names(2, heard, "position"), "reports that it has done the " \
                                                    "step to %s the %s" % (verb, thing)
    else:
        heard = x.send(2, [1], position(content))
        target, what = names(2, heard, "position"), "states that %s" % english
    fill = {"maker sought": content, "lost from the map": term(thing, "DEFINITE"),
            "version sought": LACKED}.get(key, "(term %s)" % target)
    head = "ACT-REQUEST SPEAKERS-OWN" if key == "plain words asked" else "ACT-QUESTION"
    asked = x.send(1, [2], said(ident, fill, head=head))
    if head == "ACT-QUESTION":
        x.send(2, [1], answer(names(1, asked, "question"), answered, "INTROSPECTION",
                              "PROBABLE" if key == "compared with stone" else "CERTAIN"))
    else:
        x.send(2, [1], undertaking(names(1, asked, "request"),
                                   "(situation explain (ACTOR (term SELF)) (CONTENT %s) "
                                   "(RECIPIENT %s))" % (content, party(1))))
    about = {"maker sought": "the work", "lost from the map": "the " + thing,
             "version sought": "the word"}.get(key, "agent 2's move")
    return "agent 2 %s; agent 1 asks about it with %s, and agent 2 answers" % (
        what, quoted(ident, about))


def repairing(x, ident, t, n):
    """A repair of the exchange: a message lost, damaged or misread, or too much at once."""
    key = LANG.entries[ident]["key"]
    content, english = t.content()
    if key == "the words given":
        own = x.send(1, [2], position(content))
        x.send(2, [1], position("(situation mean (UNDERGOER %s) (CONTENT %s))" % (
            ref_term(1, own, "position"), negated(content)), "INFERENCE", "PROBABLE"))
        x.send(1, [2], said(ident, content))
        return "agent 1 states that %s; agent 2 reads it otherwise, and agent 1 restates " \
               "its meaning with %s" % (english, quoted(ident, "the content that " + english))
    if key == "wait for me":
        for _ in range(2):
            x.send(2, [1], position(t.content()[0]))
        x.send(1, [2], said(ident, head="ACT-REQUEST SPEAKERS-OWN"))
        return "agent 2 sends two positions in quick succession, and agent 1 answers with %s" \
            % quoted(ident)
    if key == "sentences long":
        # one move of three contents joined, longer than the speaker can follow
        joined = " ".join("(CONTENT %s)" % c for c in (content, t.content()[0],
                                                       t.content()[0]))
        x.send(2, [1], position("(situation CONJUNCTION %s)" % joined))
        x.send(1, [2], said(ident))
        return "agent 2 states three things in one long move, beginning that %s, and agent " \
               "1 answers with %s" % (english, quoted(ident))
    if key in ("map lost", "door opened again"):
        # messages lost between those that arrive: one leaves the speaker unable to place
        # what follows, and two leave the exchange past repairing move by move
        x.send(2, [1], position(content))
        lost = 1 if key == "map lost" else 2
        for _ in range(lost):
            x.lose(2)
        x.send(2, [1], position(t.content()[0]))
        x.send(1, [2], said(ident))
        return "agent 2 states that %s; %s of its messages never arrive%s, and agent 1 " \
               "answers its next with %s" % (english, "one" if lost == 1 else "two",
                                             "s" if lost == 1 else "", quoted(ident))
    if key == "arrived with you":
        x.send(1, [2], position(content))
        x.send(1, [2], said(ident, head="ACT-QUESTION"))
        return "agent 1 states that %s and, with no acknowledgement, asks %s" % (
            english, quoted(ident))
    if key == "not arrived":
        lost = "(term (mentions-serial 2 %d 1))" % x.lose(2)
        asked = x.send(2, [1], question("(situation read (ACTOR (term INTERLOCUTOR)) "
                                        "(UNDERGOER %s))" % lost))
        x.send(1, [2], said(ident, lost, head="ACT-ANSWER %s" % names(2, asked, "question")))
        return "agent 2 asks whether agent 1 has read a message of its own that never " \
               "came, and agent 1 answers with %s" % quoted(ident, "that message")
    if key == "word not held":
        heard = x.send(2, [1], position(content))
        x.send(1, [2], said(ident, LACKED))
        return "agent 2 states that %s with a word agent 1's release lacks, and agent 1 " \
               "says %s" % (english, quoted(ident, "the word"))
    sent = x.send(2, [1], position(content))
    message = "(term (names-message 2 %d))" % sent
    head = "ACT-REQUEST SPEAKERS-OWN" if key == "give again" else "ASSERTED-POSITION"
    x.send(1, [2], said(ident, message, head=head))
    return "agent 2 states that %s; the message reaches agent 1 damaged or not at all, and " \
           "agent 1 says %s" % (english, quoted(ident, "agent 2's message"))
