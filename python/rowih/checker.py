"""The checker: the class of a move computed from its force
(specification/grammar.md#the-class-of-a-move), the placement of every value at the unit
it applies to, and the rules of the language that a single message can be checked against.
Each finding is a diagnostic."""
from __future__ import annotations

from . import convention_rules, figure_rules, register_rules, registers
from . import discourse_rules as rules
from .data import Language
from .diagnostics import Diagnostic
from .temporal import Temporal, situation_aspect

IN_FORCE_KINDS = {
    ("issue", "request"), ("normative-entry", "commitment"), ("normative-entry", "obligation"),
    ("normative-entry", "permission"), ("normative-entry", "assignment"),
    ("setting", "definition"), ("setting", "version"), ("setting", "role"),
}
OPEN_STATUSES = {"open", "in-force"}

SITUATION_CLASSES = {
    "g.situations-and-contents.aspect", "g.situations-and-contents.polarity",
    "g.situations-and-contents.world-of-evaluation", "g.situations-and-contents.status-of-content",
    "g.situations-and-contents.information-structure", "g.situations-and-contents.kind-of-question",
    "g.attitudes-and-aims.kind-of-attitude", "g.attitudes-and-aims.origin-of-an-aim",
    "g.force.kind-of-normative-entry", "g.force.bindingness",
    "g.attitudes-and-aims.status-of-a-normative-state", "g.attitudes-and-aims.execution-phase",
    "g.situations-and-contents.structural-relation", "g.situations-and-contents.connective",
    "g.standing.basis", "g.standing.strength", "g.ambiguity-and-figures.figurative-type",
    "g.ambiguity-and-figures.idiom-selection",
}
# The idiom mark stands on whatever constituent an idiom's literal structure is, as the
# figurative type does (specification/lexicon.md#conventional-expressions-and-idioms).
ASSERTION_CLASSES = {
    "g.standing.basis", "g.standing.strength", "g.standing.independence-of-a-confirmation",
    "g.situations-and-contents.information-structure", "g.situations-and-contents.status-of-content",
    "g.ambiguity-and-figures.figurative-type", "g.ambiguity-and-figures.idiom-selection",
}
TERM_CLASSES = {
    "g.reference.person", "g.situations-and-contents.quantifier",
    "g.reference.existence-commitment", "g.reference.access", "g.reference.verification",
    "g.reference.discourse-status", "g.reference.specificity",
    "g.reference.reading-of-a-collective", "g.situations-and-contents.information-structure",
    "g.ambiguity-and-figures.figurative-type", "g.ambiguity-and-figures.idiom-selection",
}
TIME_AT = {
    "assertion": {"observation-time", "inference-time", "validity-interval"},
    "situation": {"event-time", "reference-time", "execution-time"},
    "term": set(),
}
FILLER_AT = {
    "assertion": {"g.standing.provenance-link", "g.ambiguity-and-figures.figures-relation"},
    "situation": {"g.situations-and-contents.participation", "g.attitudes-and-aims.counterparty",
                  "g.situations-and-contents.connective",
                  "g.ambiguity-and-figures.figures-relation"},
    "term": {"g.ambiguity-and-figures.figures-relation",
             "g.situations-and-contents.participation", "g.standing.provenance-link"},
}
ATTITUDE_AIMS = {"desire", "goal", "intention", "preference"}

# The kinds an act may name, by its change and outcome
# (specification/grammar.md#the-class-of-a-move). A delegation passes on acceptance, as an
# offer does, so it is accepted or rejected as an offer is
# (specification/discourse.md#requests-offers-commitments-and-delegation); and a
# challenge, whose resolution is grounds or a retraction, is answered by grounds
# (specification/discourse.md#challenges-and-disagreement).
NAMEABLE = {
    ("resolution", "answer"): {("issue", "question"), ("issue", "challenge")},
    ("resolution", "acceptance"): {("issue", "request"), ("issue", "proposal"),
                                   ("normative-entry", "commitment"),
                                   ("normative-entry", "assignment")},
    ("resolution", "rejection"): {("issue", "request"), ("issue", "proposal"),
                                  ("normative-entry", "commitment"),
                                  ("normative-entry", "assignment")},
    ("resolution", "settlement"): {("normative-entry", "obligation"),
                                   ("normative-entry", "assignment")},
    ("resolution", "failure"): {("normative-entry", "obligation"),
                                ("normative-entry", "assignment"), ("issue", "request")},
}
OWN_ENTRY_LOWERINGS = {("asserted-position", None), ("conceded-position", None),
                       ("normative-entry", "commitment"), ("normative-entry", "assignment"),
                       ("normative-entry", "permission"), ("supposition", None),
                       ("summary", None), ("issue", "proposal")}


def short(identifier: str | None) -> str | None:
    return identifier.rsplit(".", 1)[-1] if identifier else None


def entry_kind(ids: list) -> tuple:
    names = [short(i) for i in ids]
    adds = names[0] if names else None
    sub = names[1] if len(names) > 1 and adds in ("issue", "normative-entry", "setting") else None
    return adds, sub


def move_class(t: dict) -> dict:
    """Whether the move is operative, pending and de-escalating, computed from what it
    adds and what it changes, never read from a name
    (specification/grammar.md#the-class-of-a-move)."""
    adds, sub = entry_kind(t["adds"])
    change = [short(i) for i in t["change"]]
    adds_in_force = (adds, sub) in IN_FORCE_KINDS and (adds, sub) != ("issue", "request")
    adds_pending = adds == "issue" and sub in ("request", "proposal")
    named = t.get("named")
    named_in_force = False
    if named and named["ref"] == "names" and named["target"] == "entry":
        nk = entry_kind(named["expected"])
        named_in_force = nk in IN_FORCE_KINDS and short(named["status"]) in OPEN_STATUSES
    c = change[0] if change else None
    outcome = change[1] if c == "resolution" and len(change) > 1 else None
    when = change[-1] if c in ("resolution", "lowering", "acknowledgement") else None
    changing = c in ("resolution", "lowering")
    operative = adds_in_force or (named_in_force and changing and when == "on-the-move")
    pending = (not operative) and (adds_pending or (named_in_force and changing
                                                    and when == "on-acceptance"))
    de_escalating = (named_in_force and when == "on-the-move" and not adds_in_force
                     and (c == "lowering" or (c == "resolution"
                                              and outcome in ("rejection", "settlement"))))
    return {"operative": operative, "pending": pending, "de-escalating": de_escalating,
            "inert": not operative and not pending}


def precision_bound(t: dict) -> bool:
    """Whether a move is precision-bound, by any of three routes: its computed class,
    operative or pending; the speaker's declaration; or a register that carries the class
    by default (specification/grammar.md#precision-bound-moves)."""
    cls = move_class(t)
    return cls["operative"] or cls["pending"] or bool(t.get("precision_bound")) or \
        registers.bound_by_register(t)


class Checker:
    def __init__(self, lang: Language, envelope=None):
        self.lang = lang
        self.envelope = envelope
        self.diags: list[Diagnostic] = []
        self._normaliser = None
        self.named = {}         # the named units of the move being checked

    def normaliser(self):
        """A normaliser of this release, for resolving the idioms a move marks."""
        if self._normaliser is None:
            from .normal import Normaliser
            self._normaliser = Normaliser(self.lang)
        return self._normaliser

    def add(self, code: str, node, expected=(), detected=(), note=""):
        span = node.get("_span") if isinstance(node, dict) else None
        self.diags.append(Diagnostic(code, span, list(expected), list(detected), note=note))

    def check_move(self, t: dict, sender: str | None = None):
        start = len(self.diags)
        cls = move_class(t)
        named = t.get("named")
        adds, sub = entry_kind(t["adds"])
        names_entry = bool(named) and named["ref"] == "names"
        if bool(t["change"]) != names_entry:
            self.add("d.checker.change-without-entry", t,
                     note="change %s with %s" % ("present" if t["change"] else "absent",
                                                  "an entry named" if names_entry
                                                  else "no entry named"))
        if named and named["ref"] == "mentions":
            self.add("d.checker.expectation", named,
                     note="what a move acts on is named, not mentioned")
        rules.check_summary(self, t, adds)
        needs_authority = cls["operative"] or cls["pending"]
        if needs_authority != bool(t.get("authority")):
            self.add("d.checker.authority", t,
                     expected=["authority" if needs_authority else "no authority"])
        if names_entry and named["target"] == "entry" and t["change"]:
            self.check_fit(t, named, sender, adds, sub)
        if cls["de-escalating"] and not t["constituents"]:
            self.add("d.checker.stop-restatement", t,
                     note="a stop restates the content of what it withdraws")
        bound = precision_bound(t)
        self.named = figure_rules.named_units(t["constituents"], {})
        for c in t["constituents"]:
            self.node(c, bound, cls, top=True, move=t)
            if c["kind"] == "assertion":
                rules.check_confirmation(self, t, c)
        if t.get("authority_term"):
            self.node(t["authority_term"], bound, cls, top=False, move=t)
        if t.get("deadline"):
            self.spec(t["deadline"], t)
        convention_rules.check_conventions(self, t)
        register_rules.check_register(self, t)
        if (adds, sub) == ("setting", "definition"):
            convention_rules.check_definition(self, t)
        self.temporal(t, start)

    def temporal(self, t: dict, start: int):
        """Every time of the move on one network (specification/grammar.md#time); a
        contradiction the ordered times already reported is not reported again."""
        net = Temporal(self.lang, self.communication_time())
        failure = net.build(t)
        for part, kind, index in net.ill_typed:
            self.add("d.checker.ill-typed", part, expected=["a time a %s bears" % kind],
                     detected=[index])
        if failure is not None and not any(d.code == "d.checker.ordered-times"
                                           for d in self.diags[start:]):
            self.add("d.checker.times-inconsistent", failure)

    def check_fit(self, t, named, sender, adds, sub):
        change = [short(i) for i in t["change"]]
        nk = entry_kind(named["expected"])
        c = change[0]
        outcome = change[1] if c == "resolution" else None
        own = sender is not None and named["author"] == sender
        if c == "resolution":
            allowed = NAMEABLE.get((c, outcome), set())
            if nk not in allowed:
                self.add("d.checker.fit", named, expected=sorted("%s %s" % k for k in allowed),
                         detected=["%s %s" % nk])
            elif outcome in ("answer", "acceptance", "rejection") and own:
                self.add("d.checker.fit", named,
                         note="an issue is resolved by the participant it is addressed to")
        if c == "lowering" and (nk[0], nk[1]) in OWN_ENTRY_LOWERINGS and sender is not None \
                and not own:
            self.add("d.checker.fit", named, note="a participant lowers only its own %s"
                     % (nk[1] or nk[0]))
        if c == "acknowledgement" and own:
            self.add("d.checker.fit", named, note="an acknowledgement names another's move")
        if adds == "issue" and sub == "challenge" and own:
            self.add("d.checker.fit", named, note="a challenge names another's position")
        if adds == "issue" and sub == "proposal" and change[:2] != ["resolution", "rejection"]:
            # a proposal that names an entry counters it, and a counterproposal declines
            # what it answers (specification/discourse.md#negotiation)
            self.add("d.checker.fit", named, note="a counterproposal declines what it answers")
        if c == "resolution" and outcome in ("settlement", "failure") and \
                nk == ("normative-entry", "assignment") and sender is not None and not own:
            # an action performed at another's request is recorded under the requester's
            # authority, never the performer's
            # (specification/discourse.md#requests-offers-commitments-and-delegation)
            principal = t.get("authority_term") or {}
            parties = [p.get("number") for p in principal.get("parts", [])
                       if p.get("kind") == "party"]
            if short(t.get("authority")) != "on-behalf-of-a-named-principal" or \
                    parties != [named["author"]]:
                self.add("d.checker.authority-attenuates", t,
                         expected=["on behalf of agent %s" % named["author"]],
                         detected=[short(t.get("authority")) or "none"])

    # ------------------------------------------------------------ units
    def node(self, t: dict, bound: bool, cls: dict, top: bool, move: dict):
        k = t["kind"]
        if k in ("assertion", "situation", "term"):
            summary = top and k == "assertion" and \
                entry_kind(move["adds"])[0] == "summary"
            self.unit(t, bound, cls, move, summary)
        elif k == "readings":
            if len(t["readings"]) < 2:
                self.add("d.checker.readings", t, expected=["two or more readings"])
            if bound and short(t["ambiguity"]) == "accidental" and (cls["operative"]
                                                                    or cls["pending"]):
                self.add("d.checker.accidental-in-operative", t)
            elif bound:
                self.add("d.checker.precision-bound", t,
                         note="a precision-bound move has exactly one reading")
            for r in t["readings"]:
                self.node(r, bound, cls, False, move)
        elif k == "wall":
            pass

    def unit(self, t: dict, bound: bool, cls: dict, move: dict, summary: bool = False):
        """`summary` holds for an assertion of a summary, whose standing is a set: the
        bases of one tier and a strength for each calibration
        (specification/discourse.md#summaries-and-confirmations)."""
        kind = t["kind"]
        allowed = {"assertion": ASSERTION_CLASSES, "situation": SITUATION_CLASSES,
                   "term": TERM_CLASSES}[kind]
        parts = t["parts"]
        values = [p for p in parts if p["kind"] == "value"]
        is_attitude = any(p["member"].startswith("g.attitudes-and-aims.kind-of-attitude")
                          for p in values)
        seen_classes = set()
        for p in parts:
            pk = p["kind"]
            if pk == "value":
                c = p["member"].rsplit(".", 1)[0]
                if c not in allowed or (c.startswith("g.standing.") and kind == "situation"
                                        and not is_attitude):
                    self.add("d.checker.ill-typed", p, expected=["a value of a %s" % kind],
                             detected=[p["member"]])
                several = c == "g.situations-and-contents.connective" or (
                    summary and c in ("g.standing.basis", "g.standing.strength"))
                if c in seen_classes and not several:
                    self.add("d.checker.ill-typed", p, note="two values of one class")
                seen_classes.add(c)
            elif pk == "time":
                if short(p["index"]) not in TIME_AT[kind]:
                    self.add("d.checker.ill-typed", p, expected=sorted(TIME_AT[kind]),
                             detected=[p["index"]])
                if p["spec"]["kind"] == "rate" and \
                        situation_aspect(t, self.lang) not in ("iterative", "habitual"):
                    self.add("d.checker.ill-typed", p,
                             expected=["a rate on an iterative or habitual situation"])
                self.spec(p["spec"], p)
            elif pk == "filler":
                c = p["role"].rsplit(".", 1)[0]
                if (c not in FILLER_AT[kind] and not (c.startswith("g.standing.")
                                                      and kind == "situation" and is_attitude)) \
                        or (kind == "term" and c == "g.standing.provenance-link"
                            and p["role"] != "g.standing.provenance-link.source"):
                    self.add("d.checker.ill-typed", p, expected=sorted(FILLER_AT[kind]),
                             detected=[p["role"]])
                self.node(p["filler"], bound, cls, False, move)
            elif pk == "quantity":
                if kind == "assertion" or (kind == "situation" and is_attitude):
                    self.strength(p)
                elif kind != "term":
                    self.add("d.checker.ill-typed", p, expected=["a quantity in a term"])
                if bool(p.get("calibration")) != summary and (
                        summary or kind != "term"):
                    # a summary restates others' numbers, so whose calibration each is
                    # under is said there, and only there
                    self.add("d.checker.ill-typed", p,
                             expected=["the calibrating participant" if summary
                                       else "no calibrating participant"])
                if bound and not fixed_bounds(p):
                    self.add("d.checker.precision-bound", p,
                             note="a vague value without fixed bounds")
            elif pk == "word":
                if p["status"] == "unknown" and bound:
                    self.add("d.checker.unknown-in-precision-bound", p, detected=[p["form"]])
            elif pk == "party" and kind != "term":
                self.add("d.checker.ill-typed", p, expected=["a participant in a term"])
            elif pk == "dialect" and kind != "term":
                self.add("d.checker.ill-typed", p, expected=["a dialect in a term"])
            elif pk in ("assertion", "situation", "term", "readings", "wall", "same", "ref"):
                if pk == "situation" and kind != "assertion":
                    self.add("d.checker.ill-typed", p, note="a situation stands in an "
                             "assertion or after a role")
                if pk in ("assertion", "term"):
                    self.add("d.checker.ill-typed", p, note="a %s stands after a role" % pk)
                self.node(p, bound, cls, False, move)
        if kind == "assertion" and not any(p["kind"] in ("situation", "same", "readings",
                                                         "idiom") for p in parts):
            self.add("d.checker.ill-typed", t, expected=["a situation in the assertion"])
        if summary:
            rules.check_summary_standing(self, t)
        if kind == "term":
            rules.check_referent(self, t)
        if kind == "situation":
            rules.check_collectives(self, t)
        figure_rules.check_unit(self, t, bound, self.named)
        if is_attitude:
            self.own_action(t)
        if kind == "assertion":
            self.ordered_times(t)
            links = [p for p in parts if p["kind"] == "filler"
                     and p["role"].startswith("g.standing.provenance-link.")]
            limit = self.lang.protocol.get("maxima", {}).get("provenance links")
            if limit is not None and len(links) > limit:
                self.add("d.parser.maximum", t, expected=["at most %d provenance links" % limit],
                         detected=["%d" % len(links)])

    def strength(self, p: dict):
        text = p["number"]
        for piece in text.replace("~", "/").split("/") if "~" in text else [text]:
            try:
                v = float(piece)
            except ValueError:
                v = -1.0
            if not 0.0 <= v <= 1.0 or p.get("unit"):
                self.add("d.checker.strength-range", p, expected=["a number within 0 and 1"],
                         detected=[text])
                return

    def own_action(self, t: dict):
        values = {short(p["member"]) for p in t["parts"] if p["kind"] == "value"}
        if "intention" not in values:
            return
        holder = [p["filler"] for p in t["parts"] if p["kind"] == "filler"
                  and short(p["role"]) == "holder"]
        content = [p["filler"] for p in t["parts"] if p["kind"] == "filler"
                   and short(p["role"]) == "content"]
        if not holder or not content or content[0]["kind"] != "situation":
            self.add("d.checker.own-action", t, note="an intention needs a holder and an action")
            return
        if not self.actions_of(content[0], holder[0]):
            self.add("d.checker.own-action", t)

    def actions_of(self, situation: dict, holder: dict) -> bool:
        """Whether a content is an action by the holder, or a plan: a structure of such
        actions joined by a connective (specification/grammar.md#attitudes-and-aims)."""
        if situation.get("kind") != "situation":
            return False
        parts = situation["parts"]
        joined = any(p["kind"] == "value" and p["member"].startswith(
            "g.situations-and-contents.connective.") for p in parts)
        if joined:
            subs = [p["filler"] for p in parts if p["kind"] == "filler"
                    and short(p["role"]) == "content"]
            return bool(subs) and all(self.actions_of(x, holder) for x in subs)
        actors = [p["filler"] for p in parts if p["kind"] == "filler"
                  and short(p["role"]) == "actor"]
        return bool(actors) and same_referent(actors[0], holder)

    # ------------------------------------------------------------ times
    def spec(self, s: dict, node):
        if s["kind"] == "interval":
            self.spec(s["from"], node)
            self.spec(s["until"], node)

    def ordered_times(self, t: dict):
        """Observation before inference before communication
        (specification/grammar.md#time), wherever the times can be placed on the clock or
        ordered by relation."""
        times = {short(p["index"]): p for p in t["parts"] if p["kind"] == "time"}
        comm = self.communication_time()
        points = {}
        for name, p in times.items():
            pt = self.point(p["spec"], comm)
            if pt is not None:
                points[name] = pt
        if comm is not None:
            points["communication-time"] = comm
        order = ["observation-time", "inference-time", "communication-time"]
        for i, a in enumerate(order):
            for b in order[i + 1:]:
                if a in points and b in points and points[a] > points[b]:
                    self.add("d.checker.ordered-times", times.get(a, t),
                             note="%s after %s" % (a, b))
        for name, p in times.items():
            s = p["spec"]
            if s["kind"] == "relation" and s["reference"]["kind"] == "index":
                other = short(s["reference"]["index"])
                rel = short(s["relation"])
                if name in order and other in order:
                    earlier = order.index(name) < order.index(other)
                    wrong = (earlier and rel in ("after", "met-by")) or \
                            (not earlier and rel in ("before", "meets"))
                    if wrong:
                        self.add("d.checker.ordered-times", p,
                                 note="%s %s %s" % (name, rel, other))

    def communication_time(self):
        if self.envelope is None:
            return None
        try:
            return float(self.envelope.time.text)
        except ValueError:
            return None

    def point(self, s: dict, comm):
        unit_seconds = {"second": 1, "minute": 60, "hour": 3600, "day": 86400,
                        "week": 604800, "month": 2629746, "year": 31556952}
        if s["kind"] == "absolute":
            try:
                return float(s["number"])
            except ValueError:
                return None
        if comm is None:
            return None
        if s["kind"] == "now":
            return comm
        if s["kind"] == "offset":
            try:
                n = float(s["number"])
            except ValueError:
                return None
            d = n * unit_seconds[short(s["unit"])]
            return comm - d if short(s["anchor"]) == "ago" else comm + d
        return None


def fixed_bounds(q: dict) -> bool:
    """A quantity whose bounds are fixed: an interval, or a number with a comparator that
    states its precision (invariants, `inv.precision-bound-one-reading`)."""
    if "~" in q["number"]:
        return True
    return short(q.get("comparator")) in ("exactly", "at-least", "at-most")


def same_referent(a: dict, b: dict) -> bool:
    """Two fillers denote the same referent when one stands for the other's name or
    both are the same term written alike."""
    from .normal import name_free_key
    if a.get("kind") == "same" and b.get("name") == a.get("name"):
        return True
    if b.get("kind") == "same" and a.get("name") == b.get("name"):
        return True
    if a.get("kind") == "same" and b.get("kind") == "same":
        return a["name"] == b["name"]
    return name_free_key(a, {}) == name_free_key(b, {})
