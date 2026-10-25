"""The explanation in English (specification/meaning.md#the-english-explanation):
generated deterministically from the normal form, a view marked as its generating
receiver's, never an encoding and never parsed back into the language.

It says each unit's predicate and participants and every value the normal form holds that
is not the default the normaliser supplies where the value stands, so that what a speaker
leaves to a default is left unsaid in English too and nothing a speaker or an entry's
expansion states is dropped."""
from __future__ import annotations

from . import normal, senses
from .checker import entry_kind, move_class, short
from .data import Language, load
from .figure_rules import RELATION, figure_type

WORLD = "g.situations-and-contents.world-of-evaluation"
QUANTIFIER = "g.situations-and-contents.quantifier"
# the determiner a quantifier is said with; one English has no determiner for is said by
# its name after the noun
DETERMINERS = {"definite": "the", "indefinite": "a", "universal": "every",
               "existential": "some", "distributive": "each"}
PERSONS = {"self": "me", "interlocutor": "you"}
# the classes whose value is said as its situation's predicate
PREDICATES = ("g.attitudes-and-aims.kind-of-attitude", "g.force.kind-of-normative-entry",
              "g.situations-and-contents.structural-relation")

ACT_NAMES = [
    # (adds, sub, change, outcome) -> act; None matches anything
    (("issue", "question", None, None), "asks"),
    (("issue", "request", None, None), "requests"),
    (("issue", "proposal", None, None), "proposes"),
    (("issue", "challenge", None, None), "challenges"),
    (("normative-entry", "obligation", None, None), "commands"),
    (("normative-entry", "commitment", None, None), "commits"),
    (("normative-entry", "permission", None, None), "permits"),
    (("normative-entry", "assignment", None, None), "delegates"),
    (("normative-entry", "recommendation", None, None), "recommends"),
    (("setting", None, None, None), "declares"),
    (("supposition", None, None, None), "supposes"),
    (("summary", None, None, None), "summarises"),
    (("conceded-position", None, None, None), "concedes"),
    (("asserted-position", None, "resolution", "answer"), "answers"),
    (("asserted-position", None, "resolution", "settlement"), "reports complete"),
    (("asserted-position", None, "lowering", None), "corrects itself"),
    (("asserted-position", None, None, None), "asserts"),
    (("nothing-beyond-its-own-record", None, "resolution", "acceptance"), "accepts"),
    (("nothing-beyond-its-own-record", None, "resolution", "rejection"), "rejects"),
    (("nothing-beyond-its-own-record", None, "resolution", "settlement"), "settles"),
    (("nothing-beyond-its-own-record", None, "resolution", "failure"), "reports failure of"),
    (("nothing-beyond-its-own-record", None, "lowering", None), "withdraws"),
    (("nothing-beyond-its-own-record", None, "acknowledgement", None), "acknowledges"),
]


class English:
    def __init__(self, lang: Language | None = None, sender: str = "1"):
        self.lang = lang or load()
        self.sender = sender
        self.in_source = False      # within the source of a marked figure
        self.world = "actual"       # the world of the enclosing content

    def value_word(self, member: str) -> str:
        """The words a value is said with."""
        cls, value = member.rsplit(".", 1)
        if cls == QUANTIFIER and value in DETERMINERS:
            return DETERMINERS[value]
        if member == "g.situations-and-contents.polarity.negative":
            return "not"
        if cls == "g.reference.person" and value in PERSONS:
            return PERSONS[value]
        return self.lang.items[member].name

    def is_default(self, member: str, unit: dict) -> bool:
        """Whether the normaliser supplies the value where it stands in `unit`: its class's
        default member, or the default its place fixes (normal.py)."""
        cls, value = member.rsplit(".", 1)
        status = self.lang.classes[cls]["status"]
        if "default member" in status:
            return member == status["default member"]
        if cls == "g.situations-and-contents.aspect":
            return value == normal.lexical_aspect(unit["parts"], self.lang)
        if cls == WORLD:
            return value == self.world
        if cls == "g.reference.existence-commitment":
            return value == normal.default_existence(self.world, self.in_source)
        if cls == "g.reference.discourse-status":
            return value == normal.default_discourse_status(unit["parts"])
        return False

    def key(self, ident, unit: dict | None = None):
        """A word's key, in the conventional sense its unit's frame selects where it has
        one (specification/lexicon.md#figurative-senses-and-conceptual-mappings), and in
        its basic sense inside a figure's source, which the figure's mark asks to be read
        by comparison with it."""
        if unit is not None and not self.in_source:
            ident = senses.entry_read(unit, self.lang) or ident
        return self.lang.entries[ident]["key"]

    def act(self, t: dict) -> str:
        adds, sub = entry_kind(t["adds"])
        change = [short(c) for c in t["change"]]
        c = change[0] if change else None
        outcome = change[1] if c == "resolution" and len(change) > 1 else None
        # the most specific description first: those that state a change and an outcome
        ordered = sorted(ACT_NAMES, key=lambda e: (e[0][2] is None, e[0][3] is None))
        if c == "resolution" and outcome == "acceptance":
            return "accepts"
        for (a, s, ch, out), name in ordered:
            if a == adds and (s is None or s == sub) and (ch is None or ch == c) and \
                    (out is None or out == outcome):
                return name
        return "says"

    def move(self, t: dict) -> str:
        self.world = normal.starting_world(entry_kind(t["adds"])[0])
        speaker = "Agent %s" % self.sender
        verb = self.act(t)
        bits = []
        cls = move_class(t)
        if t.get("named"):
            bits.append(self.ref(t["named"]))
        bits += [self.ref(r) for r in t.get("also_named", [])]
        content = "; ".join(self.node(c) for c in t["constituents"])
        sentence = "%s %s" % (speaker, verb)
        if bits:
            sentence += " " + ", ".join(bits)
        if content:
            sentence += (": " if bits else " that ") + content
        if t.get("relations"):
            sentence += " (relation: %s)" % ", ".join(self.key(r) for r in t["relations"])
        if t.get("authority"):
            authority = self.lang.items[t["authority"]].name
            if t.get("authority_term"):
                authority += ", %s" % self.node(t["authority_term"])
            sentence += " (authority: %s)" % authority
        if t.get("deadline"):
            sentence += " (deadline: %s)" % self.spec(t["deadline"])
        tags = [k for k in ("operative", "pending", "de-escalating") if cls[k]]
        if tags:
            sentence += " [%s]" % ", ".join(tags)
        return sentence + "."

    def ref(self, r: dict) -> str:
        if r["target"] == "message":
            return "message %s of agent %s" % (r["number"], r["author"])
        if r["target"] == "serial":
            text = "message %s of agent %s's channel to %s" % (
                r["number"], r["author"], ", ".join(r["recipients"]))
            return "the mention of " + text if r["ref"] == "mentions" else text
        kind = " ".join(self.lang.items[i].name for i in r.get("expected", []))
        who = "its own" if r["author"] == self.sender else "agent %s's" % r["author"]
        text = "%s %s (entry %s)" % (who, kind or "entry", r["number"])
        if r["ref"] == "mentions":
            text = "the mention of " + text
        if r.get("part") is not None:
            text += ", part %d" % r["part"]
        return text

    def node(self, t: dict) -> str:
        k = t["kind"]
        if k in ("assertion", "situation", "term") and figure_type(t) is not None and \
                not self.in_source:
            self.in_source = True
            try:
                return self.node(t)
            finally:
                self.in_source = False
        if k == "assertion":
            return self.assertion(t)
        if k == "situation":
            return self.situation(t)
        if k == "term":
            return self.term(t)
        if k == "same":
            return "the same thing (%d)" % t["name"]
        if k == "readings":
            kind = self.lang.items[t["ambiguity"]].name
            return "either %s (%s ambiguity)" % (" or ".join(self.node(r) for r in t["readings"]),
                                                kind)
        if k == "wall":
            if "data" in t:
                return "data of type %s" % t["type"]
            return "the quoted words " + self.quoted(t)
        if k == "ref":
            return self.ref(t)
        return k

    def assertion(self, t: dict) -> str:
        grounds = []
        sits = []
        for p in t["parts"]:
            if p["kind"] == "value":
                if not self.is_default(p["member"], t):
                    grounds.append(self.value_word(p["member"]))
            elif p["kind"] == "quantity":
                calibrated = " as agent %s calibrates it" % p["calibration"] \
                    if p.get("calibration") else ""
                number = p["number"].replace("~", " to ")
                if p.get("comparator") and not self.is_default(p["comparator"], t):
                    number = "%s %s" % (self.value_word(p["comparator"]), number)
                grounds.append("with strength %s%s" % (number, calibrated))
            elif p["kind"] == "time":
                grounds.append("%s %s" % (self.lang.items[p["index"]].name, self.spec(p["spec"])))
            elif p["kind"] == "filler":
                grounds.append("%s: %s" % (self.lang.items[p["role"]].name, self.filler(p)))
            elif p["kind"] in ("situation", "same", "readings"):
                sits.append(self.node(p))
        text = " and ".join(sits)
        if grounds:
            text += " (%s)" % "; ".join(grounds)
        return text

    def situation(self, t: dict) -> str:
        """The situation in its world, which the values of its contents are read in."""
        outer = self.world
        self.world = next((short(p["member"]) for p in t["parts"] if p["kind"] == "value"
                           and p["member"].startswith(WORLD + ".")), outer)
        try:
            return self._situation(t, outer)
        finally:
            self.world = outer

    def _situation(self, t: dict, outer: str) -> str:
        pred = None
        relation = negative = False
        roles = {}
        mods = []
        connective = None
        for p in t["parts"]:
            if p["kind"] == "word":
                pred = self.key(p["entry"], t) if p.get("entry") else "‹%s›" % p["form"]
            elif p["kind"] == "filler":
                roles.setdefault(short(p["role"]), []).append(self.filler(p))
            elif p["kind"] == "value":
                ident = p["member"]
                c = ident.rsplit(".", 1)[0]
                if c == WORLD:
                    if short(ident) != outer:
                        mods.append(self.value_word(ident))
                elif c == "g.situations-and-contents.connective":
                    connective = self.value_word(ident)
                elif c in PREDICATES:
                    pred = self.value_word(ident)
                    relation = c == PREDICATES[2]
                elif self.is_default(ident, t):
                    continue
                elif ident.endswith("polarity.negative"):
                    negative = True
                else:
                    mods.append(self.value_word(ident))
            elif p["kind"] == "time":
                mods.append("%s %s" % (self.lang.items[p["index"]].name, self.spec(p["spec"])))
        if connective and "content" in roles:
            core = (" %s " % connective).join(roles.pop("content"))
            if negative:
                core = "not (%s)" % core
        else:
            # a structural relation holds between its undergoer and its content
            subjects = ("actor", "holder") + (("undergoer",) if relation else ())
            subject = next((r for r in subjects if r in roles), None)
            pieces = [roles[subject].pop(0) if subject else "", "not" if negative else "",
                      pred or ""]
            if subject and not roles[subject]:
                del roles[subject]
            for role in ("undergoer", "recipient", "instrument", "content"):
                prefix = {"recipient": "to ", "instrument": "with ",
                          "content": "" if relation else "that "}.get(role, "")
                pieces += [prefix + v for v in roles.pop(role, [])]
            core = " ".join(x for x in pieces if x)
        if "condition" in roles:
            core += " if " + " and ".join(roles.pop("condition"))
        for role, vals in roles.items():
            core += " (%s: %s)" % (role, ", ".join(vals))
        if mods:
            core += " (%s)" % ", ".join(mods)
        return core

    def filler(self, p: dict) -> str:
        """A role's filler; what a figure means is outside its source, and is read with
        the senses its frames select."""
        if not p["role"].startswith(RELATION):
            return self.node(p["filler"])
        outer, self.in_source = self.in_source, False
        try:
            return self.node(p["filler"])
        finally:
            self.in_source = outer

    def term(self, t: dict) -> str:
        words, determiners, mods = [], [], []
        for p in t["parts"]:
            k = p["kind"]
            if k == "word":
                words.append(self.key(p["entry"], t) if p.get("entry")
                             else "‹%s›" % p["form"])
            elif k == "party":
                words.append("me" if p["number"] == self.sender else "agent %s" % p["number"])
            elif k == "dialect":
                words.append("dialect %s" % p["number"])
            elif k == "value":
                ident = p["member"]
                if ident.startswith("g.reference.person."):
                    words.append(self.value_word(ident))
                elif self.is_default(ident, t):
                    continue
                elif ident.rsplit(".", 1)[0] == QUANTIFIER and short(ident) in DETERMINERS:
                    determiners.append(self.value_word(ident))
                else:
                    mods.append(self.value_word(ident))
            elif k == "quantity":
                q = []
                if p.get("comparator") and not self.is_default(p["comparator"], t):
                    q.append(self.value_word(p["comparator"]))
                q.append(p["number"].replace("~", " to "))
                if p.get("unit"):
                    u = p["unit"]
                    q.append(self.key(u) if u.startswith("lx.") else self.lang.items[u].name)
                if p.get("per"):
                    q.append("per " + self.lang.items[p["per"]].name)
                words.append(" ".join(q))
            elif k == "ref":
                words.append(self.ref(p))
            elif k == "filler":
                words.append("(%s %s)" % (self.lang.items[p["role"]].name, self.filler(p)))
            elif k == "wall":
                words.append(self.quoted(p) if "data" not in p
                             else "data of type %s" % p["type"])
        text = " ".join(determiners + (words or ["something"]))
        if mods:
            text += " (%s)" % ", ".join(mods)
        return text

    def quoted(self, wall: dict) -> str:
        """Quoted words in their own forms, with what each means where every one is a word
        of the lexicon."""
        text = "“%s”" % " ".join(wall["words"])
        items = [self.lang.by_form.get(w) for w in wall["words"]]
        if items and all(items):
            text += " (%s)" % " ".join(
                self.lang.entries[i.identifier]["key"] if i.identifier in self.lang.entries
                else i.name or i.gloss.lower() for i in items)
        return text

    def spec(self, s: dict) -> str:
        k = s["kind"]
        if k == "now":
            return "now"
        if k == "absolute":
            return "at %s" % s["number"]
        if k == "offset":
            return "%s %s %s" % (s["number"], self.lang.items[s["unit"]].name,
                                 self.lang.items[s["anchor"]].name)
        if k == "relation":
            ref = s["reference"]
            if ref["kind"] != "index":
                target = self.spec(ref)
            elif ref.get("unit") is None:
                target = self.lang.items[ref["index"]].name
            else:
                target = "the %s of [%d]" % (self.lang.items[ref["index"]].name,
                                            ref["unit"]["name"])
            return "%s %s" % (self.lang.items[s["relation"]].name, target)
        if k in ("duration", "rate"):
            bound = self.lang.items[s["comparator"]].name + " " if s.get("comparator") else ""
            unit = self.lang.items[s["unit"]].name
            if k == "rate":
                return "%s%s per %s" % (bound, s["number"], unit)
            return "for %s%s %s" % (bound, s["number"], unit)
        return "from %s until %s" % (self.spec(s["from"]), self.spec(s["until"]))
