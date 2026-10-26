"""The literal semantic notation: a move tree written as an s-expression over the
morphemes' glosses. It is the literal line of the gloss, the form in which corpus items
are authored, and an input the generator accepts.

    (move ASSERTED-POSITION
      (assertion OBSERVATION (OBSERVATION-TIME 5 MINUTE AGO)
        (situation run POLARITY.NEGATIVE (UNDERGOER (term service)))))

Uppercase atoms are glosses of class members; lowercase atoms are the keys of lexicon
entries; `#n` names the unit it follows; `@n` stands for the unit named n. Special
forms: `(q ...)` a quantity, `(party n)`, `(names a n KIND [SUB] STATUS [part k])`,
`(mentions a n)`, `(names-message a first-entry)`, `(names-serial a serial r...)` and
`(mentions-serial a serial r...)`, `(deadline spec)`, `(authority TERM)`,
`(quote "forms")`, `(example "forms")`, `(data "type" "text")`, `(readings KIND ...)`,
`(unknown "form")`, and a time `(INDEX spec)` whose spec is `NOW`, `n`, `n UNIT AGO|HENCE`
or `RELATION target`."""
from __future__ import annotations

import json
import re

from .data import Language, in_force, load
from .diagnostics import InputError
from .lexer import encode_payload

REFERENCE_HEADS = ("names", "mentions", "names-message", "names-serial", "mentions-serial")
TOKEN = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))')
# the symbols a number may be written with, each a numeral of the language: the digits,
# the decimal point, the sign, the ratio, the exponent and the interval
# (specification/notation.md#how-words-are-named); the grammar, not the notation, checks
# how they are arranged
NUMBER = re.compile(r"[0-9.\-/e~]+")
NAME = re.compile(r"[0-9]+")
# the members the notation writes as the head of a list, not as an atom
WRITTEN_BY_HEAD = {
    "g.message.embedded-material.quotation": '(quote "WORDS")',
    "g.message.embedded-material.example": '(example "WORDS")',
    "g.message.embedded-material.declared-data": '(data "TYPE" "TEXT")',
    "g.reference.kind-of-reference.names": "(names A N KIND STATUS)",
    "g.reference.kind-of-reference.mentions": "(mentions A N)",
}


def key_of(entry: dict) -> str:
    """The atom a word is written by: its key, and for a compressed form of a dialect its
    key after the dialect's name, since dialects name their own terms
    (specification/dialects.md#terms)."""
    key = entry["key"].replace(" ", "-")
    if entry["grammatical category"] == "dialect form":
        return "%s.%s" % (entry["dialect name"], key)
    return key

def takes_slots(entry: dict) -> bool:
    """Whether a grammatical idiom's literal structure holds slots, `(slot N)`, for the
    constituents the speaker supplies (specification/lexicon.md#conventional-expressions-and-idioms)."""
    structure = entry.get("literal structure")
    return isinstance(structure, str) and "(slot " in structure


def marked(entry: dict) -> str:
    """A grammatical idiom as the notation writes it: the mark IDIOM-ENTRY on its unit,
    then its literal structure, each `(slot N)` standing for a constituent the speaker
    supplies (specification/notation.md#how-words-are-named)."""
    head, rest = entry["literal structure"].split(" ", 1)
    return "%s IDIOM-ENTRY %s" % (head, rest)


class NotationError(InputError):
    """A text that does not read as the notation: an error of a writer's input, not a
    diagnostic of the language. `Reader.moves` raises it, and nothing else, for any text
    it cannot read."""


def tokens(text: str):
    pos = 0
    out = []
    text = text.strip()
    while pos < len(text):
        m = TOKEN.match(text, pos)
        if not m or m.end() == pos:
            raise NotationError("cannot read at %d: %r" % (pos, text[pos:pos + 20]))
        pos = m.end()
        if m.group(1):
            out.append("(")
        elif m.group(2):
            out.append(")")
        elif m.group(3) is not None:
            # strings take JSON's escapes, so a quoted message keeps its line breaks
            try:
                out.append(("str", json.loads('"%s"' % m.group(3))))
            except json.JSONDecodeError as e:
                raise NotationError("a string at %d takes the escapes of a JSON string: %s"
                                    % (pos, e)) from e
        else:
            out.append(m.group(4))
    return out


def sexp(text: str):
    toks = tokens(text)
    pos = 0

    def read():
        nonlocal pos
        tok = toks[pos]
        pos += 1
        if tok == "(":
            out = []
            while pos < len(toks) and toks[pos] != ")":
                out.append(read())
            if pos == len(toks):
                raise NotationError("a list is not closed: a ( has no )")
            pos += 1
            return out
        if tok == ")":
            raise NotationError("unexpected )")
        return tok
    items = []
    while pos < len(toks):
        items.append(read())
    return items


class Reader:
    def __init__(self, lang: Language | None = None):
        self.lang = lang or load()
        self.by_gloss = {}
        for c in self.lang.grammar["classes"]:
            prefix = c["name"].upper().replace(" ", "-").replace("'", "")
            for m in c["members"]:
                self.by_gloss[m["gloss"]] = m["identifier"]
                # every member may also be written with its class's name before it
                plain = m["gloss"].split(".")[-1]
                self.by_gloss.setdefault("%s.%s" % (prefix, plain), m["identifier"])
        # words are written by their keys; act words by their glosses in a move's head,
        # and idioms larger than a word as (idiom key)
        self.entry_by_key, self.idiom_by_key = {}, {}
        for ident, e in self.lang.entries.items():
            kind = self.lang.items[ident].kind
            if kind == "act":
                self.by_gloss[self.lang.items[ident].gloss] = ident
            elif kind == "idiom":
                self.idiom_by_key[e["key"].replace(" ", "-")] = ident
            elif kind == "sense":
                # a conventional sense is never written: its root is, and the frame the
                # root stands in selects the sense
                # (specification/lexicon.md#figurative-senses-and-conceptual-mappings)
                continue
            elif in_force(self.lang, e):
                self.entry_by_key[key_of(e)] = ident

    def member(self, atom) -> str:
        if not isinstance(atom, str):
            raise NotationError("expected the gloss of a member, not %s" % _shown(atom))
        if atom not in self.by_gloss:
            raise NotationError("no member glossed %s" % atom)
        return self.by_gloss[atom]

    def cls(self, atom: str) -> str:
        return self.member(atom).rsplit(".", 1)[0]

    def is_of(self, atom, class_id: str) -> bool:
        """Whether `atom` is the gloss of a member of the class `class_id`."""
        return isinstance(atom, str) and atom in self.by_gloss and self.cls(atom) == class_id

    def moves(self, text: str) -> list:
        """The move trees of a text in the notation. A text that does not read raises
        `NotationError` and nothing else: each shape the notation fixes is checked where
        it is read, and a list too short or of the wrong kind that a check did not
        foresee is reported as an error of the move it stands in."""
        out = []
        for i, x in enumerate(sexp(text), 1):
            try:
                out.append(self.move(x))
            except NotationError:
                raise
            except (IndexError, KeyError, TypeError, AttributeError, ValueError) as e:
                raise NotationError("move %d does not read as the notation (%s: %s)"
                                    % (i, type(e).__name__, e)) from e
        return out

    def move(self, x) -> dict:
        if not isinstance(x, list) or not x or x[0] != "move":
            raise NotationError("a move is (move ...), not %s" % _shown(x))
        t = {"kind": "move", "adds": [], "change": [], "authority": None,
             "authority_term": None, "deadline": None, "named": None, "also_named": [],
             "relations": [], "precision_bound": False, "constituents": []}
        head_classes = {"g.force.what-the-move-adds", "g.force.kind-of-issue",
                        "g.force.kind-of-normative-entry", "g.force.bindingness",
                        "g.force.kind-of-setting"}
        change_classes = {"g.force.change-made", "g.force.outcome-of-a-resolution",
                          "g.force.extent", "g.force.when-the-change-takes-effect"}
        for item in x[1:]:
            if isinstance(item, str):
                if item == "PRECISION-BOUND":
                    t["precision_bound"] = True
                    continue
                if item in self.entry_by_key:
                    ident = self.entry_by_key[item]
                    # a politeness word and a diction are written in the head by their
                    # keys, as the relation words are
                    # (specification/lexicon.md#politeness-words-and-dictions)
                    category = self.lang.entries[ident]["grammatical category"]
                    if category == "politeness word":
                        t["politeness"] = ident
                    elif category == "diction":
                        t["diction"] = ident
                    else:
                        t["relations"].append(ident)
                    continue
                if item.startswith("ACT-") and item in self.by_gloss:
                    t["act"] = self.by_gloss[item]
                    for m in self.lang.entries[t["act"]]["expansion"]:
                        key = "adds" if m.rsplit(".", 1)[0] in head_classes else "change"
                        t[key].append(m)
                    continue
                c = self.cls(item)
                if c == "g.ambiguity-and-figures.declared-loss":
                    t.setdefault("losses", []).append(self.member(item))
                    continue
                if c == "g.ambiguity-and-figures.register":
                    t["register"] = self.member(item)
                    continue
                if c in head_classes:
                    t["adds"].append(self.member(item))
                elif c in change_classes:
                    t["change"].append(self.member(item))
                elif c == "g.force.authority-claimed":
                    t["authority"] = self.member(item)
                else:
                    raise NotationError("%s does not stand in a move's head" % item)
                continue
            _list(item, "a move's part")
            head = item[0]
            if head == "authority":
                _arity(item, 1, 1, "(authority TERM)")
                t["authority_term"] = self.node(item[1])
            elif head == "deadline":
                _arity(item, 1, None, "(deadline TIME)")
                t["deadline"] = self.spec(item[1:])
            elif head in REFERENCE_HEADS:
                if t["named"] is None:
                    t["named"] = self.ref(item)
                else:
                    t["also_named"].append(self.ref(item))
            else:
                t["constituents"].append(self.node(item))
        return t

    def node(self, x) -> dict:
        if isinstance(x, str):
            if x.startswith("@"):
                return {"kind": "same", "name": _name(x)}
            raise NotationError("a constituent is a list, not %s" % x)
        _list(x, "a constituent")
        head = x[0]
        if head in ("assertion", "situation", "term"):
            t = {"kind": head, "name": None, "parts": []}
            rest = x[1:]
            if rest and isinstance(rest[0], str) and rest[0].startswith("#"):
                t["name"] = _name(rest[0])
                rest = rest[1:]
            for p in rest:
                t["parts"].append(self.part(p))
            return t
        if head == "readings":
            _arity(x, 1, None, "(readings KIND READING ...)")
            return {"kind": "readings", "ambiguity": self.member(x[1]),
                    "readings": [self.node(r) for r in x[2:]]}
        if head in ("quote", "example"):
            _arity(x, 1, 1, '(%s "WORDS")' % head)
            gloss = "QUOTATION" if head == "quote" else "EXAMPLE"
            return {"kind": "wall", "material": self.member(gloss),
                    "words": _string(x[1], "the words of (%s ...)" % head).split()}
        if head == "data":
            _arity(x, 2, 2, '(data "TYPE" "TEXT")')
            return {"kind": "wall", "material": self.member("DECLARED-DATA"),
                    "type": _string(x[1], "the media type of (data ...)"),
                    "data": encode_payload(_string(x[2], "the text of (data ...)")
                                           .encode("utf-8"))}
        if head in REFERENCE_HEADS:
            return self.ref(x)
        if head == "idiom":
            _arity(x, 1, 1, "(idiom KEY)")
            if not isinstance(x[1], str) or x[1] not in self.idiom_by_key:
                raise NotationError("no idiom keyed %s" % _shown(x[1]))
            entry = self.lang.entries[self.idiom_by_key[x[1]]]
            if takes_slots(entry):
                # (idiom KEY) cannot give what a slot stands for
                raise NotationError(
                    "the idiom %s takes constituents the speaker supplies, which (idiom %s) "
                    "cannot give: write %s, with each (slot N) replaced by a constituent"
                    % (x[1], x[1], marked(entry)))
            return {"kind": "idiom", "entry": self.idiom_by_key[x[1]]}
        if head == "slot":
            # the constituent a speaker supplies to an idiom
            # (specification/lexicon.md#conventional-expressions-and-idioms)
            _arity(x, 1, 1, "(slot N)")
            return {"kind": "slot", "slot": _whole(x[1], "the number of (slot ...)")}
        raise NotationError("unknown constituent %s" % _shown(head))

    def part(self, p) -> dict:
        if isinstance(p, str):
            if p.startswith("@"):
                return {"kind": "same", "name": _name(p)}
            if p in self.entry_by_key:
                ident = self.entry_by_key[p]
                return {"kind": "word", "form": self.lang.items[ident].form, "entry": ident,
                        "status": "known"}
            return {"kind": "value", "member": self.member(p)}
        _list(p, "a unit's part")
        head = p[0]
        if head == "q":
            return self.quantity(p[1:])
        if head in ("party", "dialect"):
            _arity(p, 1, 1, "(%s N)" % head)
            return {"kind": head, "number": _number(p[1], "the number of (%s ...)" % head)}
        if head == "unknown":
            from .lexer import segment
            _arity(p, 1, 1, '(unknown "FORM")')
            form = _string(p[1], "the form of (unknown ...)")
            status = "formation" if segment(form, self.lang) is not None else "unknown"
            return {"kind": "word", "form": form, "entry": None, "status": status}
        if head in REFERENCE_HEADS:
            return self.ref(p)
        if head in ("assertion", "situation", "term", "readings", "quote", "example", "data",
                    "idiom", "slot"):
            return self.node(p)
        ident = self.member(head)
        c = ident.rsplit(".", 1)[0]
        if c == "g.time.time-index":
            return {"kind": "time", "index": ident, "spec": self.spec(p[1:], ident)}
        _arity(p, 1, 1, "(%s FILLER)" % head)
        return {"kind": "filler", "role": ident, "filler": self.node(p[1])}

    def quantity(self, items) -> dict:
        q = {"kind": "quantity", "comparator": None, "number": None, "unit": None, "per": None,
             "calibration": None}
        items = list(items)
        if items and self.is_of(items[0], "g.situations-and-contents.comparator"):
            q["comparator"] = self.member(items.pop(0))
        if not items:
            raise NotationError("a quantity (q ...) needs a number")
        q["number"] = _number(items.pop(0), "the number of a quantity")
        while items:
            atom = items.pop(0)
            if isinstance(atom, list) and atom and atom[0] == "party":
                _arity(atom, 1, 1, "(party N)")
                q["calibration"] = _number(atom[1], "the number of (party ...)")
            elif atom == "PER":
                if not items:
                    raise NotationError("PER in a quantity is followed by a time unit")
                q["per"] = self.member(items.pop(0))
            elif isinstance(atom, str) and atom in self.entry_by_key:
                q["unit"] = self.entry_by_key[atom]
            else:
                q["unit"] = self.member(atom)
        return q

    def ref(self, x) -> dict:
        head = x[0]
        if head in ("names-serial", "mentions-serial"):
            # a message by its sender, its serial and its channel's recipients
            # (specification/notation.md#references)
            _arity(x, 3, None, "(%s A S R ...)" % head)
            return {"kind": "ref", "ref": head.split("-")[0], "target": "serial",
                    "author": _number(x[1], "the sender of (%s ...)" % head),
                    "number": _number(x[2], "the serial of (%s ...)" % head),
                    "recipients": [_number(r, "a recipient of (%s ...)" % head)
                                   for r in x[3:]],
                    "expected": [], "status": None, "part": None}
        if head == "names-message":
            # a message is named by its sender and the first entry its envelope states
            _arity(x, 2, 2, "(names-message A F)")
            return {"kind": "ref", "ref": "names", "target": "message",
                    "author": _number(x[1], "the participant of (names-message ...)"),
                    "number": _number(x[2], "the first entry of (names-message ...)"),
                    "expected": [], "status": None, "part": None}
        _arity(x, 2, None, "(%s A N KIND STATUS [part K])" % head)
        r = {"kind": "ref", "ref": head, "target": "entry",
             "author": _number(x[1], "the participant of (%s ...)" % head),
             "number": _number(x[2], "the entry of (%s ...)" % head),
             "expected": [], "status": None, "part": None}
        rest = list(x[3:])
        while rest:
            atom = rest.pop(0)
            if atom == "part":
                if not rest:
                    raise NotationError("part in a reference is followed by the part's number")
                r["part"] = _whole(rest.pop(0), "the part of a reference")
                continue
            ident = self.member(atom)
            if ident.startswith("g.reference.expected-status-of-an-entry."):
                r["status"] = ident
            else:
                r["expected"].append(ident)
        return r

    def spec(self, items, index: str | None = None) -> dict:
        items = list(items)
        if not items:
            raise NotationError("a time (%s ...) needs a time" % (
                self.lang.items[index].gloss if index else "deadline"))
        if index is not None and index.endswith("validity-interval"):
            if len(items) != 2 or "until" in items:
                raise NotationError("VALIDITY-INTERVAL takes two times, from and until, "
                                    "written without until: not %s" % _shown(items))
            first, second = items[0], items[1]
            return {"kind": "interval", "from": self.spec(first if isinstance(first, list)
                                                          else [first]),
                    "until": self.spec(second if isinstance(second, list) else [second])}
        if "until" in items:
            # an interval of any other index (specification/notation.md#times)
            i = items.index("until")
            ends = [items[:i], items[i + 1:]]
            if not ends[0] or not ends[1]:
                raise NotationError("until joins two times: %s" % _shown(items))
            return {"kind": "interval", "from": self.spec(ends[0]), "until": self.spec(ends[1])}
        if len(items) == 1 and isinstance(items[0], list):
            return self.spec(items[0])
        a = items[0]
        if a == "NOW":
            if len(items) != 1:
                raise NotationError("NOW stands alone as a time, not in %s" % _shown(items))
            return {"kind": "now"}
        if self.is_of(a, "g.time.time-relation"):
            target = items[1:]
            if not target:
                raise NotationError("%s is followed by the time it relates to" % a)
            if len(target) == 1 and self.is_of(target[0], "g.time.time-index"):
                ref = {"kind": "index", "index": self.member(target[0])}
            elif len(target) == 1 and isinstance(target[0], list) and target[0] and \
                    isinstance(target[0][0], str) and target[0][0].startswith("@"):
                # an index of a named unit: (@2 EVENT-TIME)
                _arity(target[0], 1, 1, "(@N INDEX)")
                ref = {"kind": "index", "index": self.member(target[0][1]),
                       "unit": {"kind": "same", "name": _name(target[0][0])}}
            else:
                ref = self.spec(target)
            return {"kind": "relation", "relation": self.member(a), "reference": ref}
        comparator = None
        if self.is_of(a, "g.situations-and-contents.comparator"):
            comparator = self.member(a)
            items = items[1:]
            if not items:
                raise NotationError("%s is followed by a duration or a rate" % a)
            a = items[0]
        number = _number(a, "a time")
        if len(items) == 1:
            return {"kind": "absolute", "number": number}
        if items[1] == "PER":
            if len(items) != 3:
                raise NotationError("a rate is written N PER UNIT, not %s" % _shown(items))
            return {"kind": "rate", "comparator": comparator, "number": number,
                    "unit": self.member(items[2])}
        if len(items) == 2:
            return {"kind": "duration", "comparator": comparator, "number": number,
                    "unit": self.member(items[1])}
        if len(items) != 3 or comparator is not None:
            raise NotationError("a time is NOW, N, N UNIT AGO, N UNIT HENCE, a relation, a "
                                "duration or a rate, not %s" % _shown(items))
        return {"kind": "offset", "number": number, "unit": self.member(items[1]),
                "anchor": self.member(items[2])}


def _shown(x) -> str:
    """A part of a text in the notation as its writer wrote it, for an error."""
    if isinstance(x, tuple):
        return json.dumps(x[1], ensure_ascii=False)
    if isinstance(x, list):
        return "(" + " ".join(_shown(y) for y in x) + ")"
    return str(x)


def _list(x, what: str) -> None:
    """A list headed by an atom, as every list but a move's is."""
    if isinstance(x, tuple):
        raise NotationError("%s is not a string: a string stands only in (quote ...), "
                            "(example ...), (data ...) and (unknown ...), not %s"
                            % (what, _shown(x)))
    if not x:
        raise NotationError("an empty list () stands as %s" % what)
    if not isinstance(x[0], str):
        raise NotationError("a list is headed by an atom, not %s" % _shown(x))


def _arity(x: list, least: int, most: int | None, shape: str) -> None:
    n = len(x) - 1
    if n < least or (most is not None and n > most):
        raise NotationError("%s is written %s, not %s" % (x[0], shape, _shown(x)))


def _string(x, what: str) -> str:
    if isinstance(x, tuple):
        return x[1]
    raise NotationError("%s is a string between double quotation marks, not %s"
                        % (what, _shown(x)))


def _number(x, what: str) -> str:
    """A number as the notation writes it: an atom of the numerals' symbols."""
    if isinstance(x, str) and NUMBER.fullmatch(x):
        return x
    raise NotationError("%s is not a number: %s" % (what, _shown(x)))


def _whole(x, what: str) -> int:
    if isinstance(x, str) and NAME.fullmatch(x):
        return int(x)
    raise NotationError("%s is a whole number, not %s" % (what, _shown(x)))


def _name(atom: str) -> int:
    """The number of `#N` or `@N`."""
    if NAME.fullmatch(atom[1:]):
        return int(atom[1:])
    raise NotationError("%s does not name a unit: a unit is named #N and used as @N, N a "
                        "whole number" % atom)


# ---------------------------------------------------------------- writing

class Printer:
    def __init__(self, lang: Language | None = None):
        self.lang = lang or load()

    def g(self, ident: str) -> str:
        return self.lang.items[ident].gloss

    def atom_of(self, item) -> str | None:
        """How the notation writes a word of the lexicon, a member or a morpheme: by its
        gloss, its key, its head or its form, an idiom that takes slots by its marked unit,
        or None where the notation never writes it,
        since the generator writes it (a structural word, a numeral, a check word, a field
        of the envelope or a protocol statement), it is a sense the frame selects, it is
        a bound morpheme, or it is a deprecated root."""
        kind = item.kind
        if kind == "member":
            group = item.class_id.split(".")[1]
            if group in ("numbers", "message", "protocol") and \
                    item.class_id != "g.message.embedded-material":
                return None
            return WRITTEN_BY_HEAD.get(item.identifier, item.gloss)
        if kind == "act":
            return item.gloss
        if kind == "idiom":
            entry = self.lang.entries[item.identifier]
            if takes_slots(entry):
                return marked(entry)
            return "(idiom %s)" % entry["key"].replace(" ", "-")
        if kind == "jargon":
            # a dialect's term is a formation, read from its parts
            return "(unknown %s)" % json.dumps(item.form)
        if kind == "dialect":
            from .data import dialects
            for d in dialects().values():
                for f in d.get("forms", []):
                    if f["machine identifier"] == item.identifier:
                        return "%s.%s" % (d["dialect"], f["key"].replace(" ", "-"))
            return None
        entry = self.lang.entries.get(item.identifier)
        if kind in ("root", "derivation") and entry is not None and in_force(self.lang, entry) \
                and entry["grammatical category"] not in ("derivational suffix",
                                                          "conventional sense"):
            return key_of(entry)
        return None

    def move(self, t: dict) -> str:
        force = list(t["adds"]) + list(t["change"])
        parts = []
        if t.get("act"):
            parts.append(self.g(t["act"]))
            force = force[len(self.lang.entries[t["act"]]["expansion"]):]
        parts += [self.g(i) for i in force]
        if t.get("authority"):
            parts.append(self.g(t["authority"]))
        if t.get("authority_term"):
            parts.append("(authority %s)" % self.node(t["authority_term"]))
        if t.get("deadline"):
            parts.append("(deadline %s)" % self.spec(t["deadline"]))
        if t.get("named"):
            parts.append(self.ref(t["named"]))
        parts += [self.ref(r) for r in t.get("also_named", [])]
        parts += [self.lang.entries[r]["key"].replace(" ", "-") for r in t.get("relations", [])]
        parts += [self.lang.entries[t[k]]["key"].replace(" ", "-")
                  for k in ("politeness", "diction") if t.get(k)]
        parts += [self.g(i) for i in t.get("losses", [])]
        if t.get("register"):
            parts.append(self.g(t["register"]))
        if t.get("precision_bound"):
            parts.append("PRECISION-BOUND")
        parts += [self.node(c) for c in t["constituents"]]
        return "(move %s)" % " ".join(parts)

    def node(self, t: dict) -> str:
        k = t["kind"]
        if k in ("assertion", "situation", "term"):
            head = [k] + (["#%d" % t["name"]] if t.get("name") is not None else [])
            return "(%s)" % " ".join(head + [self.part(p) for p in t["parts"]])
        if k == "same":
            return "@%d" % t["name"]
        if k == "readings":
            return "(readings %s %s)" % (self.g(t["ambiguity"]),
                                         " ".join(self.node(r) for r in t["readings"]))
        if k == "wall":
            if "data" in t:
                from .lexer import decode_payload
                data = decode_payload(t["data"]) or b""
                return "(data %s %s)" % (json.dumps(t["type"]),
                                         json.dumps(data.decode("utf-8", "replace"),
                                                    ensure_ascii=False))
            head = "quote" if t["material"].endswith("quotation") else "example"
            return "(%s %s)" % (head, json.dumps(" ".join(t["words"])))
        if k == "ref":
            return self.ref(t)
        if k == "idiom":
            return "(idiom %s)" % self.lang.entries[t["entry"]]["key"].replace(" ", "-")
        if k == "slot":
            return "(slot %d)" % t["slot"]
        if k == "unstated":
            # what a speaker answers for through a figure whose content it did not state
            # (`figures.answers_for`), printed for a reader of the view
            return "(unstated %s)" % self.g(t["figure"])
        raise ValueError(k)

    def part(self, p: dict) -> str:
        k = p["kind"]
        if k == "value":
            return self.g(p["member"])
        if k == "word":
            if p.get("entry"):
                return key_of(self.lang.entries[p["entry"]])
            return "(unknown %s)" % json.dumps(p["form"])
        if k == "filler":
            return "(%s %s)" % (self.g(p["role"]), self.node(p["filler"]))
        if k == "time":
            return "(%s %s)" % (self.g(p["index"]), self.spec(p["spec"], bare=True,
                                                              index=p["index"]))
        if k == "quantity":
            out = ["q"]
            if p.get("comparator"):
                out.append(self.g(p["comparator"]))
            out.append(p["number"])
            if p.get("unit"):
                u = p["unit"]
                out.append(self.lang.entries[u]["key"].replace(" ", "-") if u.startswith("lx.")
                           else self.g(u))
            if p.get("per"):
                out += ["PER", self.g(p["per"])]
            if p.get("calibration"):
                out.append("(party %s)" % p["calibration"])
            return "(%s)" % " ".join(out)
        if k == "party":
            return "(party %s)" % p["number"]
        if k == "dialect":
            return "(dialect %s)" % p["number"]
        return self.node(p)

    def ref(self, r: dict) -> str:
        if r["target"] == "message":
            return "(names-message %s %s)" % (r["author"], r["number"])
        if r["target"] == "serial":
            return "(%s-serial %s %s %s)" % (r["ref"], r["author"], r["number"],
                                             " ".join(r["recipients"]))
        out = [r["ref"], r["author"], r["number"]] + [self.g(i) for i in r.get("expected", [])]
        if r.get("status"):
            out.append(self.g(r["status"]))
        if r.get("part") is not None:
            out += ["part", str(r["part"])]
        return "(%s)" % " ".join(out)

    def spec(self, s: dict, bare: bool = False, index: str | None = None) -> str:
        k = s["kind"]
        if k == "now":
            text = "NOW"
        elif k == "absolute":
            text = s["number"]
        elif k == "offset":
            text = "%s %s %s" % (s["number"], self.g(s["unit"]), self.g(s["anchor"]))
        elif k == "relation":
            ref = s["reference"]
            if ref["kind"] != "index":
                target = self.spec(ref)
            elif ref.get("unit") is None:
                target = self.g(ref["index"])
            else:
                target = "(@%d %s)" % (ref["unit"]["name"], self.g(ref["index"]))
            text = "%s %s" % (self.g(s["relation"]), target)
        elif k in ("duration", "rate"):
            words = [self.g(s["comparator"])] if s.get("comparator") else []
            words.append(s["number"])
            if k == "rate":
                words.append("PER")
            text = " ".join(words + [self.g(s["unit"])])
        else:
            marker = " " if index is None or index.endswith("validity-interval") else " until "
            return "%s%s%s" % (self.spec(s["from"]), marker, self.spec(s["until"]))
        return text if bare or k in ("now", "absolute") else "(%s)" % text
