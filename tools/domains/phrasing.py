"""The phrasing of the conventional language in an exchange: the release the entries are
read from, the `Topic` of a domain's exchanges, an entry's literal structure said with the
idiom mark in a register it admits, and the moves that surround it, a request, an
undertaking, a report, a position, a question and an answer."""
from rowih import data

from .compose import Exchange, k, names, party, term

LANG = data.load("1.0")
BY_KEY = {e["key"]: i for i, e in LANG.entries.items()}

# The register an entry is said in where it excludes the standard one, the first of these
# it admits, with the politeness word that register takes.
REGISTERS = [("R5", "familiar CASUAL"), ("R7", "deferential CEREMONIAL"),
             ("R6", "familiar PLAYFUL"), ("R3", "courteous EXPLANATORY"), ("R4", "FORMAL")]
SELF, HEARER = "(term SELF)", "(term INTERLOCUTOR)"


class Topic:
    """The matter of a domain's exchanges: the tasks one agent asks another to do, each a
    predicate with an agent actor and the thing it is done to; the contents a position
    states, each a situation with its English; and the things a remark is about."""

    def __init__(self, picker, tasks, contents, things):
        self.p, self.tasks, self.contents, self.things = picker, tasks, contents, things

    def task(self):
        verbs = []
        for v, _ in self.tasks:
            if v not in verbs:
                verbs.append(v)
        verb = self.p(verbs)
        return verb, self.p([t for v, t in self.tasks if v == verb])

    def content(self):
        english = self.p([e for _, e in self.contents])
        return dict((e, s) for s, e in self.contents)[english], english

    def thing(self):
        return self.p(self.things)


def done(verb, actor, thing, aspect=""):
    aspect = (" " + aspect) if aspect else ""
    return "(situation %s%s (ACTOR %s) (UNDERGOER %s))" % (k(verb), aspect, actor,
                                                          term(thing, "DEFINITE"))


def polar(situation: str) -> str:
    return situation.replace("(situation ", "(situation POLAR ", 1)


def negated(situation: str) -> str:
    return situation.replace("(situation ", "(situation POLARITY.NEGATIVE ", 1)


def register(ident: str) -> str:
    codes = LANG.entries[ident]["register"]
    if "R2" in codes:
        return ""
    return next(" " + words for code, words in REGISTERS if code in codes)


def unit(ident: str, *fills: str) -> str:
    """The entry's literal structure with the idiom mark and its slots filled, or its
    words, for an idiom the grammar does not form."""
    e = LANG.entries[ident]
    if isinstance(e["literal structure"], list):
        return "(idiom %s)" % k(e["key"])
    text = e["literal structure"]
    assert text.startswith("(situation "), ident
    text = text.replace("(situation ", "(situation IDIOM-ENTRY ", 1)
    for n, fill in enumerate(fills, 1):
        text = text.replace("(slot %d)" % n, fill)
    assert "(slot" not in text, ident
    return text


def has_slot(ident: str) -> bool:
    return "(slot 1)" in str(LANG.entries[ident]["literal structure"])


def quoted(ident: str, about: str = "") -> str:
    """The entry's words and its meaning, what fills its slot named in that meaning."""
    e = LANG.entries[ident]
    meaning = e["definition"]
    if about:
        meaning = meaning.replace("what the slot names", about).replace(
            "the expression the slot names", about)
    return '"%s" (%s)' % (e["key"], meaning)


def said(ident, *fills, head="ASSERTED-POSITION", basis="INTROSPECTION",
         strength="CERTAIN", reg=None) -> str:
    """The entry said as the content of a move: an assertion for an asserted position, an
    answer or a confirmation, the bare unit for a question, a request or a
    recommendation."""
    reg = register(ident) if reg is None else reg
    fills = fills[:1] if has_slot(ident) else ()
    if head.startswith(("ACT-QUESTION", "ACT-REQUEST", "ACT-RECOMMENDATION")):
        return "(move %s%s %s)" % (head, reg, unit(ident, *fills))
    return "(move %s%s (assertion %s %s %s))" % (head, reg, basis, strength,
                                                 unit(ident, *fills))


def request(situation, reg=""):
    return "(move ACT-REQUEST SPEAKERS-OWN%s %s)" % (reg, situation)


def undertaking(ref, situation, reg=""):
    return "(move ACT-UNDERTAKING SPEAKERS-OWN%s %s %s)" % (reg, ref, situation)


def report(ref, situation, reg=""):
    return "(move ACT-COMPLETION-REPORT SPEAKERS-OWN%s %s (assertion OBSERVATION CERTAIN " \
           "%s))" % (reg, ref, situation)


def position(situation, basis="OBSERVATION", strength="CERTAIN", reg=""):
    return "(move ASSERTED-POSITION%s (assertion %s %s %s))" % (reg, basis, strength,
                                                                situation)


def question(situation, reg=""):
    return "(move ACT-QUESTION%s %s)" % (reg, polar(situation))


def answer(ref, situation, basis="OBSERVATION", strength="CERTAIN", reg=""):
    return "(move ACT-ANSWER%s %s (assertion %s %s %s))" % (reg, ref, basis, strength,
                                                            situation)


def ref_term(author, number, kind):
    return "(term %s)" % names(author, number, kind)


def asked_and_taken(x: Exchange, t: Topic, reg: str, asker=1, worker=2):
    """Agent `asker` asks `worker` for a task, which it undertakes: the task's verb and
    thing, and the numbers of the request and the undertaking."""
    verb, thing = t.task()
    asked = x.send(asker, [worker], request(done(verb, party(worker), thing), reg))
    taken = x.send(worker, [asker], undertaking(names(asker, asked, "request"),
                                                done(verb, SELF, thing), reg))
    return verb, thing, asked, taken


def worked(x: Exchange, t: Topic, reg: str, asker=1, worker=2):
    """The task asked for and undertaken, then reported done: the task's verb and thing,
    and the numbers of the request and the report."""
    verb, thing, asked, taken = asked_and_taken(x, t, reg, asker, worker)
    reported = x.send(worker, [asker], report(names(worker, taken, "obligation"),
                                              done(verb, SELF, thing, "COMPLETED"), reg))
    return verb, thing, asked, reported
