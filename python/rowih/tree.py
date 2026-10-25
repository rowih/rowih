"""The semantic representation's tree: each move as plain data, identifiers in place of
forms, so that it is both what normalisation and checking work on and what an export
writes and an import reads (specification/meaning.md#the-normal-form).

`from_ast` reads the AST; `words_of_move` writes a move tree back as words, which is the
generator's morphology and orthography stages and the normal form's serialisation.
Keys beginning with an underscore carry spans for diagnostics and are never written.
"""
from __future__ import annotations

from .data import Language
from .syntax import (ContentWord, DialectName, Filler, Idiom, IndexOf, Move, Number, Party, Quantity,
                     ReadingSet, Reference, Same, TimeSpec, TimeValue, Unit, Value, Wall)


# ---------------------------------------------------------------- AST to tree

def from_ast_move(move: Move) -> dict:
    h = move.head
    t = {"kind": "move",
         "adds": [v.member for v in h.adds],
         "change": [v.member for v in h.change],
         "authority": h.authority.member if h.authority else None,
         "authority_term": unit_tree(h.authority_term) if h.authority_term else None,
         "deadline": spec_tree(h.deadline) if h.deadline else None,
         "named": ref_tree(h.named) if h.named else None,
         "also_named": [ref_tree(r) for r in h.also_named],
         "relations": [cw.word.identifier for cw in h.relations],
         "precision_bound": h.precision_bound is not None,
         "constituents": [node_tree(c) for c in move.constituents],
         "_span": move.words[0].span if move.words else None}
    # the social and textual component's choices, kept only where made, so that a move
    # without them has none of these keys
    # (specification/lexicon.md#conventional-expressions-and-idioms)
    if h.act is not None:
        t["act"] = h.act.identifier
    if h.losses:
        t["losses"] = [v.member for v in h.losses]
    # and those of the politeness word and diction
    # (specification/lexicon.md#politeness-words-and-dictions)
    if h.politeness is not None:
        t["politeness"] = h.politeness.identifier
    if h.diction is not None:
        t["diction"] = h.diction.identifier
    if h.register is not None:
        t["register"] = h.register.member
    return t


def node_tree(node) -> dict:
    if isinstance(node, Unit):
        return unit_tree(node)
    if isinstance(node, Same):
        return {"kind": "same", "name": node.name.integer()}
    if isinstance(node, Wall):
        return wall_tree(node)
    if isinstance(node, ReadingSet):
        return {"kind": "readings", "ambiguity": node.kind.member,
                "readings": [node_tree(r) for r in node.readings],
                "_span": node.kind.word.span}
    if isinstance(node, Reference):
        return ref_tree(node)
    if isinstance(node, Idiom):
        return {"kind": "idiom", "entry": node.entry, "_span": node.words[0].span}
    raise TypeError(type(node).__name__)


def unit_tree(u: Unit) -> dict:
    return {"kind": u.kind, "name": u.name.integer() if u.name else None,
            "parts": [part_tree(p) for p in u.parts], "_span": u.open_word.span}


def part_tree(p) -> dict:
    if isinstance(p, Value):
        return {"kind": "value", "member": p.member, "_span": p.word.span}
    if isinstance(p, ContentWord):
        w = p.word
        status = "known" if w.item is not None else w.kind
        return {"kind": "word", "form": w.form,
                "entry": w.item.identifier if w.item is not None else None,
                "status": status, "_span": w.span}
    if isinstance(p, Filler):
        return {"kind": "filler", "role": p.role.member, "filler": node_tree(p.filler),
                "_span": p.role.word.span}
    if isinstance(p, TimeValue):
        return {"kind": "time", "index": p.index.member, "spec": spec_tree(p.spec),
                "_span": p.index.word.span}
    if isinstance(p, Quantity):
        unit = None
        if isinstance(p.unit, Value):
            unit = p.unit.member
        elif isinstance(p.unit, ContentWord):
            unit = p.unit.word.identifier
        return {"kind": "quantity", "comparator": p.comparator.member if p.comparator else None,
                "number": p.number.text, "unit": unit,
                "per": p.per.member if p.per else None,
                "calibration": p.calibration.text if p.calibration else None,
                "_span": p.number.words[0].span}
    if isinstance(p, Party):
        return {"kind": "party", "number": p.number.text}
    if isinstance(p, DialectName):
        return {"kind": "dialect", "number": p.number.text}
    if isinstance(p, Reference):
        return ref_tree(p)
    return node_tree(p)


def ref_tree(r: Reference) -> dict:
    tree = {"kind": "ref", "ref": r.kind, "target": r.target, "author": r.author.text,
            "number": r.number.text, "expected": [v.member for v in r.expected],
            "status": r.status.member if r.status else None,
            "part": r.part.integer() if r.part else None,
            "_span": r.words[0].span if r.words else None}
    if r.target == "serial":
        # a message by its serial on the channel its recipients name, the serial written
        # without the zeros of its fixed width (specification/notation.md#references)
        tree["number"] = str(r.number.integer())
        tree["recipients"] = [n.text for n in r.recipients]
    return tree


def spec_tree(s: TimeSpec) -> dict:
    if s.kind == "now":
        return {"kind": "now"}
    if s.kind == "absolute":
        return {"kind": "absolute", "number": s.number.text}
    if s.kind == "offset":
        return {"kind": "offset", "number": s.number.text, "unit": s.unit.member,
                "anchor": s.anchor.member}
    if s.kind == "relation":
        ref = s.reference
        if isinstance(ref, Value):
            ref_t = {"kind": "index", "index": ref.member}
        elif isinstance(ref, IndexOf):
            ref_t = {"kind": "index", "index": ref.index.member,
                     "unit": {"kind": "same", "name": ref.same.name.integer()}}
        else:
            ref_t = spec_tree(ref)
        return {"kind": "relation", "relation": s.relation.member, "reference": ref_t}
    if s.kind == "interval":
        return {"kind": "interval", "from": spec_tree(s.reference), "until": spec_tree(s.until)}
    if s.kind in ("duration", "rate"):
        return {"kind": s.kind, "comparator": s.comparator.member if s.comparator else None,
                "number": s.number.text, "unit": s.unit.member}
    raise ValueError(s.kind)


def wall_tree(w: Wall) -> dict:
    if w.kind.name == "declared-data":
        return {"kind": "wall", "material": w.kind.member,
                "type": w.type_payload.payload.decode("ascii"),
                "data": w.payload.form, "_span": w.kind.word.span}
    return {"kind": "wall", "material": w.kind.member, "words": [x.form for x in w.words],
            "_span": w.kind.word.span}


# ---------------------------------------------------------------- tree to words

class Spell:
    """Writes trees as word forms."""

    def __init__(self, lang: Language):
        from .writer import Writer
        self.lang = lang
        self.wr = Writer(lang)

    def f(self, identifier: str) -> str:
        return self.lang.items[identifier].form

    def move_body(self, t: dict) -> list:
        force = list(t["adds"]) + list(t["change"])
        if t.get("act"):
            # the act word stands for the force values its entry expands to
            covered = self.lang.entries[t["act"]]["expansion"]
            assert force[:len(covered)] == covered, (t["act"], force)
            out = [self.f(t["act"])] + [self.f(i) for i in force[len(covered):]]
        else:
            out = [self.f(i) for i in force]
        if t.get("authority"):
            out.append(self.f(t["authority"]))
            if t.get("authority_term"):
                out += self.node(t["authority_term"])
        if t.get("deadline"):
            out.append(self.f("g.time.time-index.deadline"))
            out += self.spec(t["deadline"])
        if t.get("named"):
            out += self.ref(t["named"])
        for r in t.get("also_named", []):
            out += self.ref(r)
        out += [self.f(i) for i in t.get("relations", [])]
        for key in ("politeness", "diction"):
            if t.get(key):
                out.append(self.f(t[key]))
        out += [self.f(i) for i in t.get("losses", [])]
        if t.get("register"):
            out.append(self.f(t["register"]))
        if t.get("precision_bound"):
            out.append(self.f("g.ambiguity-and-figures.precision-bound-declaration."
                              "precision-bound"))
        for c in t["constituents"]:
            out += self.node(c)
        return out

    def move(self, t: dict) -> list:
        return self.wr.move(self.move_body(t))

    def node(self, t: dict) -> list:
        k = t["kind"]
        if k in ("assertion", "situation", "term"):
            out = [self.f("g.structure.%s" % k)]
            if t.get("name") is not None:
                out += [self.f("g.structure.name")] + self.wr.name(t["name"])
            for p in t["parts"]:
                out += self.part(p)
            out.append(self.f("g.structure.end-%s" % k))
            return out
        if k == "same":
            return [self.f("g.structure.same")] + self.wr.name(t["name"])
        if k == "wall":
            out = [self.f("g.structure.wall"), self.f(t["material"])]
            if "data" in t:
                type_bytes = t["type"].encode("ascii")
                from .lexer import decode_payload
                data = decode_payload(t["data"]) or b""
                out += self.wr.payload(type_bytes) + self.wr.number(str(len(data))) + [t["data"]]
            else:
                out += list(t["words"])
            out.append(self.f("g.structure.end-wall"))
            return out
        if k == "readings":
            out = [self.f("g.structure.readings"), self.f(t["ambiguity"])]
            for r in t["readings"]:
                out += self.node(r)
            out.append(self.f("g.structure.end-readings"))
            return out
        if k == "ref":
            return self.ref(t)
        if k == "idiom":
            from .idioms import literal
            return [self.f(w) for w in literal(self.lang, t["entry"])]
        raise ValueError(k)

    def part(self, p: dict, same=None) -> list:
        """`same`, where given, writes the SAME of a time reference in place of its name
        (the name-free key of the normal form)."""
        k = p["kind"]
        if k == "value":
            return [self.f(p["member"])]
        if k == "word":
            return [p["form"]]
        if k == "filler":
            return [self.f(p["role"])] + self.node(p["filler"])
        if k == "time":
            return [self.f(p["index"])] + self.spec(p["spec"], p["index"], same)
        if k == "quantity":
            out = [self.f(p["comparator"])] if p.get("comparator") else []
            out += self.wr.number(p["number"])
            if p.get("unit"):
                out.append(self.f(p["unit"]))
            if p.get("per"):
                out += [self.f("g.time.time-anchor.per"), self.f(p["per"])]
            if p.get("calibration"):
                out += [self.f("g.structure.party")] + self.wr.number(p["calibration"])
            return out
        if k == "party":
            return [self.f("g.structure.party")] + self.wr.number(p["number"])
        if k == "dialect":
            return [self.f("g.structure.dialect")] + self.wr.number(p["number"])
        return self.node(p)

    def ref(self, r: dict) -> list:
        out = [self.f("g.reference.kind-of-reference.%s" % r["ref"])]
        if r["target"] == "message":
            # a message is named by its sender and the first entry its envelope states,
            # which no other message of that sender states
            # (specification/notation.md#references)
            out += [self.f("g.structure.message-target")] + self.wr.number(r["author"])
            out += self.wr.number(r["number"])
        elif r["target"] == "serial":
            out += [self.f("g.structure.message-serial")] + self.wr.number(r["author"])
            out += self.wr.number(r["number"], self.lang.protocol["identifier width"])
            for recipient in r["recipients"]:
                out += self.wr.number(recipient)
        else:
            out += self.wr.number(r["author"]) + self.wr.number(r["number"])
            out += [self.f(i) for i in r.get("expected", [])]
            if r.get("status"):
                out.append(self.f(r["status"]))
        if r.get("part") is not None:
            out += [self.f("g.structure.part")] + self.wr.name(r["part"])
        return out

    def spec(self, s: dict, index: str | None = None, same=None) -> list:
        k = s["kind"]
        if k == "now":
            return [self.f("g.time.time-anchor.now")]
        if k == "absolute":
            return self.wr.number(s["number"])
        if k == "offset":
            return self.wr.number(s["number"]) + [self.f(s["unit"]), self.f(s["anchor"])]
        if k == "relation":
            ref = s["reference"]
            if ref["kind"] != "index":
                tail = self.spec(ref)
            elif ref.get("unit") is None:
                tail = [self.f(ref["index"])]
            else:
                name = ref["unit"]["name"]
                tail = (same(name) if same else
                        [self.f("g.structure.same")] + self.wr.name(name)) + [self.f(ref["index"])]
            return [self.f(s["relation"])] + tail
        if k == "interval":
            # the validity interval is always one and writes its pair unmarked; any other
            # index marks its end with UNTIL (specification/notation.md#times)
            marker = [] if index == "g.time.time-index.validity-interval" \
                else [self.f("g.structure.until")]
            return self.spec(s["from"], same=same) + marker + self.spec(s["until"], same=same)
        if k in ("duration", "rate"):
            out = [self.f(s["comparator"])] if s.get("comparator") else []
            out += self.wr.number(s["number"])
            if k == "rate":
                out.append(self.f("g.time.time-anchor.per"))
            return out + [self.f(s["unit"])]
        raise ValueError(k)


def strip_private(t):
    """The tree without its underscore keys, as an export writes it."""
    if isinstance(t, dict):
        return {k: strip_private(v) for k, v in t.items() if not k.startswith("_")}
    if isinstance(t, list):
        return [strip_private(x) for x in t]
    return t


def number_text(n: Number) -> str:
    return n.text
