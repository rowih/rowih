"""The normal form (specification/meaning.md#the-normal-form): every default stated, every
value stated on every unit that bears it, the siblings of every unit in canonical order,
and the shared nodes numbered in the normal form's traversal. Normalisation reads the
move, the grammar and the lexicon release, and nothing any participant holds."""
from __future__ import annotations

import copy
import hashlib

from . import dialects, formation, idioms, registers, versions
from .checker import entry_kind, short
from .data import Language
from .tree import Spell, strip_private

ASPECT_OF_SORT = {"s.sort.event": "perfective", "s.sort.state": "stative",
                  "s.sort.process": "progressive"}
EXISTENCE_OF_WORLD = {"actual": "asserted-to-exist", "within-a-supposition": "within-a-supposition",
                      "within-a-fiction": "within-a-declared-fiction",
                      "counterfactual": "mentioned-without-existence-asserted"}
AIMS = {"desire", "goal", "intention", "preference"}
# Persons fixed by the exchange itself: the speaker, its hearer, and the two together.
GIVEN_PERSONS = {"g.reference.person.self", "g.reference.person.interlocutor",
                 "g.reference.person.inclusive-collective"}
UNIT_KINDS = ("assertion", "situation", "term")


def _value(member: str) -> dict:
    return {"kind": "value", "member": member}


def _values(parts, class_id):
    return [p for p in parts if p["kind"] == "value" and p["member"].startswith(class_id + ".")]


# The defaults that depend on where a value stands
# (specification/meaning.md#the-normal-form), which the normaliser supplies and the
# explanation in English leaves unsaid.

def starting_world(adds: str) -> str:
    """The world a move's contents are evaluated in where none is written."""
    return "within-a-supposition" if adds == "supposition" else "actual"


def lexical_aspect(parts: list, lang: Language) -> str | None:
    """The aspect a situation takes where none is written: its root's lexical aspect, read
    from the sort of its first word, or stative for an attitude or a reported normative
    state; a situation that joins contents by a connective takes none."""
    if _values(parts, "g.situations-and-contents.connective") or any(
            p["kind"] == "filler" and short(p["role"]) == "condition" for p in parts):
        return None
    aspect = None
    for p in parts:
        if p["kind"] == "word" and (p.get("entry") or p.get("status") == "formation"):
            aspect = ASPECT_OF_SORT.get(formation.word_sort(p, lang))
            break
    if aspect is None and (_values(parts, "g.attitudes-and-aims.kind-of-attitude")
                           or _values(parts, "g.force.kind-of-normative-entry")):
        aspect = "stative"
    return aspect


def default_existence(world: str, mentioned: bool) -> str:
    """A referent's existence commitment where none is written: that of the world of the
    enclosing content, or mentioned without existence asserted inside a figure's source."""
    return "mentioned-without-existence-asserted" if mentioned else EXISTENCE_OF_WORLD[world]


def default_discourse_status(parts: list) -> str:
    """New where first written and given after (specification/meaning.md#the-normal-form):
    a referent reached through a reference was written first in the entry it names, and a
    participant was introduced when the exchange opened."""
    given = any(p["kind"] in ("ref", "party", "dialect") or (
        p["kind"] == "value" and p["member"] in GIVEN_PERSONS) for p in parts)
    return "given" if given else "new"


class Normaliser:
    def __init__(self, lang: Language):
        self.lang = lang
        self.spell = Spell(lang)
        cls_index = {c["identifier"]: i for i, c in enumerate(lang.grammar["classes"])}
        self.class_index = cls_index
        self.member_index = {m["identifier"]: j for c in lang.grammar["classes"]
                             for j, m in enumerate(c["members"])}
        self.resolved = []      # the idioms the last move read by their entries

    # ------------------------------------------------------------ defaults
    def move(self, t: dict) -> dict:
        t = copy.deepcopy(strip_private(t))
        # the act word, the declared loss, the politeness word, the diction and the
        # register are the social and textual component's, which the normal form sets
        # aside (specification/lexicon.md#registers)
        for key in registers.SOCIAL_KEYS:
            t.pop(key, None)
        self.resolved = []
        # a compressed form of a named dialect is written as the term it compresses,
        # before any default is read from a word's sort
        # (specification/dialects.md#compressed-forms)
        dialects.expand(t, self.lang)
        adds, sub = entry_kind(t["adds"])
        world = starting_world(adds)
        confirmation = False
        named = t.get("named")
        if named and named["ref"] == "names" and not [c for c in t["change"]
                                                      if short(c) != "none"]:
            confirmation = adds == "asserted-position" and \
                entry_kind(named["expected"])[0] in ("asserted-position", "conceded-position")
        if t.get("also_named"):
            # the entries a summary names are a set, in canonical order
            refs = sorted([t["named"]] + t["also_named"], key=reference_key)
            t["named"], t["also_named"] = refs[0], refs[1:]
        # A situation that is an action stands directly in a move that adds an issue
        # other than a question or a normative entry, or that restates one it names.
        named_kind = entry_kind(named["expected"]) if named and named.get("expected") else \
            (None, None)
        action_move = (adds in ("issue", "normative-entry") and sub not in ("question",
                                                                         "challenge")) or (
            named_kind[0] in ("issue", "normative-entry")
            and named_kind[1] not in ("question", "challenge"))
        t["constituents"] = [self.node(c, world, top=action_move,
                                       confirmation=confirmation) for c in t["constituents"]]
        if t.get("authority_term"):
            t["authority_term"] = self.node(t["authority_term"], world)
        # Order to a fixed point: a sibling's key reads the digests of the shared nodes
        # it names, which ordering their own parts may change; the graph is acyclic, so
        # the passes settle within its depth.
        if not cyclic(t):
            for _ in range(64):
                if not self.order_all(t):
                    break
        self.renumber(t)
        return t

    def node(self, t: dict, world: str, top: bool = False, confirmation: bool = False,
             mentioned: bool = False) -> dict:
        """`mentioned` holds inside the source content of a figure, which is mentioned and
        not asserted; a figure's target content is asserted under the standing of its
        assertion, and so is the referent a metonym stands for, which its predication is
        about, so the flag ends at either relation (specification/meaning.md#figures)."""
        k = t["kind"]
        if k == "idiom":
            # an extragrammatical idiom, recognised by its words: the core holds its
            # expansion (specification/meaning.md#the-normal-form)
            self.resolved.append(t["entry"])
            return self.node(idioms.expansion(self.lang, t["entry"]), world, top,
                             confirmation, mentioned)
        if idioms.marked(t):
            entry, bindings = idioms.resolve(t, self, world, mentioned)
            if entry is None:
                # no entry of the release has this literal structure; the checker refuses
                # it, and the literal reading stands with the mark
                u = self.node(idioms.unmarked(t), world, top, confirmation, mentioned)
                u["parts"].append(_value(idioms.MARK))
                return u
            self.resolved.append(entry)
            return self.node(idioms.fill(idioms.expansion(self.lang, entry), bindings),
                             world, top, confirmation, mentioned)
        if k in UNIT_KINDS and any(p["kind"] == "value" and p["member"].startswith(
                "g.ambiguity-and-figures.figurative-type.") for p in t["parts"]):
            mentioned = True
        if k == "assertion":
            return self.assertion(t, world, confirmation, mentioned)
        if k == "situation":
            return self.situation(t, world, top, mentioned)
        if k == "term":
            return self.term(t, world, mentioned)
        if k == "readings":
            t["readings"] = [self.node(r, world, mentioned=mentioned) for r in t["readings"]]
            return t
        return t

    def assertion(self, t, world, confirmation, mentioned=False):
        parts = t["parts"]
        if not _values(parts, "g.standing.basis"):
            parts.append(_value("g.standing.basis.unstated"))
        if not _values(parts, "g.standing.strength") and not any(p["kind"] == "quantity"
                                                                  for p in parts):
            parts.append(_value("g.standing.strength.unstated"))
        if confirmation and not _values(parts, "g.standing.independence-of-a-confirmation"):
            parts.append(_value("g.standing.independence-of-a-confirmation.same-source"))
        if not _values(parts, "g.situations-and-contents.status-of-content"):
            pass
        t["parts"] = [self.part(p, world, mentioned) for p in parts]
        return t

    def situation(self, t, world, top, mentioned=False):
        parts = t["parts"]
        written = _values(parts, "g.situations-and-contents.world-of-evaluation")
        if written:
            world = short(written[0]["member"])
        else:
            parts.append(_value("g.situations-and-contents.world-of-evaluation." + world))
        if not _values(parts, "g.situations-and-contents.polarity"):
            parts.append(_value("g.situations-and-contents.polarity.affirmative"))
        if not _values(parts, "g.situations-and-contents.status-of-content"):
            parts.append(_value("g.situations-and-contents.status-of-content.at-issue"))
        attitude = _values(parts, "g.attitudes-and-aims.kind-of-attitude")
        report = _values(parts, "g.force.kind-of-normative-entry")
        connective = _values(parts, "g.situations-and-contents.connective") or any(
            p["kind"] == "filler" and short(p["role"]) == "condition" for p in parts)
        if not _values(parts, "g.situations-and-contents.aspect"):
            aspect = lexical_aspect(parts, self.lang)
            if aspect is not None:
                parts.append(_value("g.situations-and-contents.aspect." + aspect))
        if attitude:
            if not _values(parts, "g.standing.basis"):
                parts.append(_value("g.standing.basis.unstated"))
            if not _values(parts, "g.standing.strength") and not any(
                    p["kind"] == "quantity" for p in parts):
                parts.append(_value("g.standing.strength.unstated"))
        if (attitude and short(attitude[0]["member"]) in AIMS) or report:
            if not _values(parts, "g.attitudes-and-aims.origin-of-an-aim"):
                parts.append(_value("g.attitudes-and-aims.origin-of-an-aim.unstated"))
        if top and not attitude and not report and not connective:
            if not _values(parts, "g.attitudes-and-aims.execution-phase"):
                parts.append(_value("g.attitudes-and-aims.execution-phase.unstated"))
        # from language 1.0 each content a connective joins is an action as the whole
        # would be, and takes its default phase, so that a part restated alone has the
        # normal form it has within the whole (specification/meaning.md#the-normal-form)
        joined = top and not attitude and not report and \
            _values(parts, "g.situations-and-contents.connective") and \
            versions.key(self.lang.language) >= versions.key("1.0")
        t["parts"] = [self.conjunct(p, world, mentioned) if joined and p["kind"] == "filler"
                      and short(p["role"]) == "content" else self.part(p, world, mentioned)
                      for p in parts]
        return t

    def conjunct(self, p: dict, world: str, mentioned: bool) -> dict:
        p["filler"] = self.node(p["filler"], world, top=True, mentioned=mentioned)
        return p

    def term(self, t, world, mentioned=False):
        parts = t["parts"]
        referent = any(p["kind"] in ("word", "party", "dialect", "ref") or (
            p["kind"] == "value" and p["member"].startswith("g.reference.person."))
            for p in parts)
        if referent:
            if not _values(parts, "g.reference.existence-commitment"):
                parts.append(_value("g.reference.existence-commitment." +
                                    default_existence(world, mentioned)))
            if not _values(parts, "g.reference.discourse-status"):
                parts.append(_value("g.reference.discourse-status." +
                                    default_discourse_status(parts)))
            external = any(p["kind"] == "value" and p["member"] in (
                "g.reference.access.external", "g.reference.person.external-source")
                for p in parts)
            if external and not _values(parts, "g.reference.verification"):
                parts.append(_value("g.reference.verification.unverified"))
        t["parts"] = [self.part(p, world, mentioned) for p in parts]
        return t

    def part(self, p: dict, world: str, mentioned: bool = False) -> dict:
        k = p["kind"]
        if k == "word":
            # a register-marked word is written as its base
            # (specification/meaning.md#the-normal-form), and an irregular word as its
            # regular form (specification/lexicon.md#listed-derivations-and-compounds)
            return formation.regular_word(registers.base_word(p, self.lang), self.lang)
        if k == "filler":
            inner = mentioned and not p["role"].endswith((".target-content", ".stands-for"))
            p["filler"] = self.node(p["filler"], world, mentioned=inner)
        elif k == "quantity" and not p.get("comparator"):
            p["comparator"] = "g.situations-and-contents.comparator.unstated"
        elif k in UNIT_KINDS or k in ("readings", "idiom"):
            return self.node(p, world, mentioned=mentioned)
        return p

    # ------------------------------------------------------------ order
    def rank(self, p: dict) -> tuple:
        k = p["kind"]
        if k == "word":
            return (0,)
        if k == "value":
            c = p["member"].rsplit(".", 1)[0]
            return (1, self.class_index.get(c, 99), self.member_index.get(p["member"], 99))
        if k == "time":
            return (2, self.member_index.get(p["index"], 99))
        if k == "quantity":
            return (3,)
        if k == "party":
            return (4,)
        if k == "dialect":
            return (4, 1)
        if k == "ref":
            return (5,)
        if k == "filler":
            c = p["role"].rsplit(".", 1)[0]
            return (6, self.class_index.get(c, 99), self.member_index.get(p["role"], 99))
        return (7, {"assertion": 0, "situation": 1, "term": 2, "readings": 3, "wall": 4,
                    "same": 5}.get(k, 9))

    def order_all(self, t: dict) -> bool:
        """One pass of canonical ordering over the move, deepest lists first. Returns
        whether anything moved."""
        named = {}
        collect_named(t, named)
        changed = False

        def visit(node):
            nonlocal changed
            if isinstance(node, dict):
                for v in node.values():
                    visit(v)
                for key in ("parts", "constituents", "readings"):
                    if key in node and isinstance(node[key], list):
                        new = sorted(node[key], key=lambda p: (
                            self.rank(p), name_free_key(p, named, self.spell)))
                        if new != node[key]:
                            node[key] = new
                            changed = True
            elif isinstance(node, list):
                for x in node:
                    visit(x)
        visit(t)
        return changed

    # ------------------------------------------------------------ names
    def renumber(self, t: dict):
        """Number the shared nodes in the order the normal form's traversal reaches them."""
        order = []

        def walk(node):
            if isinstance(node, dict):
                if node.get("kind") in UNIT_KINDS and node.get("name") is not None:
                    order.append(node["name"])
                for key in ("authority_term", "constituents", "parts", "filler", "readings"):
                    if key in node and node[key] is not None:
                        walk(node[key])
            elif isinstance(node, list):
                for x in node:
                    walk(x)
        walk(t)
        mapping = {old: i + 1 for i, old in enumerate(order)}

        def apply(node):
            if isinstance(node, dict):
                if node.get("kind") in UNIT_KINDS and node.get("name") is not None:
                    node["name"] = mapping[node["name"]]
                if node.get("kind") == "same" and node.get("name") in mapping:
                    node["name"] = mapping[node["name"]]
                for v in node.values():
                    apply(v)
            elif isinstance(node, list):
                for x in node:
                    apply(x)
        apply(t)


def reference_key(r: dict) -> tuple:
    """The canonical order of references: by author, number, a serial's recipients and
    part, as numbers."""
    return (r["target"], int(r["author"]), int(r["number"]),
            tuple(int(x) for x in r.get("recipients", ())),
            -1 if r.get("part") is None else r["part"], r["ref"])


def cyclic(t: dict) -> bool:
    """Whether a tree's shared names form a cycle; such a tree is ill-formed, which the
    parser reports, and it is left unordered rather than recursed on."""
    named = {}
    collect_named(t, named)
    reach = {}
    for n, node in named.items():
        inner = set()
        _refs(node["parts"], inner)
        reach[n] = inner
    state = {}

    def visit(n):
        state[n] = 1
        for m in reach.get(n, ()):
            if state.get(m) == 1 or (m not in state and visit(m)):
                return True
        state[n] = 2
        return False
    return any(n not in state and visit(n) for n in sorted(reach))


def _refs(node, out):
    if isinstance(node, dict):
        if node.get("kind") == "same":
            out.add(node["name"])
        if node.get("kind") in UNIT_KINDS and node.get("name") is not None:
            out.add(node["name"])
            return
        for v in node.values():
            _refs(v, out)
    elif isinstance(node, list):
        for x in node:
            _refs(x, out)


def collect_named(node, named: dict):
    if isinstance(node, dict):
        if node.get("kind") in UNIT_KINDS and node.get("name") is not None:
            named[node["name"]] = node
        for v in node.values():
            collect_named(v, named)
    elif isinstance(node, list):
        for x in node:
            collect_named(x, named)


def name_free_key(node: dict, named: dict, spell: Spell | None = None) -> str:
    """The name-free serialisation of a node: its words with its own name left out,
    every shared node it contains standing as its digest, and every SAME as the digest
    of the node it names."""
    if spell is None:
        from .data import load
        spell = Spell(load())
    if node.get("kind") == "filler":
        # a role with its constituent: the constituent's name, too, stands as its digest,
        # so that the order never depends on numbering
        # (specification/meaning.md#the-normal-form)
        return " ".join(_nf_part(node, named, spell))
    return " ".join(_nf_words(node, named, spell, top=True))


def digest(node: dict, named: dict, spell: Spell) -> str:
    return "#" + hashlib.sha256(name_free_key(node, named, spell).encode("utf-8")).hexdigest()


def _nf_words(node, named, spell, top=False) -> list:
    k = node.get("kind")
    if k in UNIT_KINDS:
        if node.get("name") is not None and not top:
            return [digest(node, named, spell)]
        out = [spell.f("g.structure.%s" % k)]
        for p in node["parts"]:
            out += _nf_part(p, named, spell)
        out.append(spell.f("g.structure.end-%s" % k))
        return out
    if k == "same":
        target = named.get(node["name"])
        return [digest(target, named, spell) if target is not None else "#%d" % node["name"]]
    if k == "readings":
        out = [spell.f("g.structure.readings"), spell.f(node["ambiguity"])]
        for r in node["readings"]:
            out += _nf_words(r, named, spell)
        out.append(spell.f("g.structure.end-readings"))
        return out
    return spell.part(node) if k != "ref" else spell.ref(node)


def _nf_part(p, named, spell) -> list:
    k = p["kind"]
    if k == "filler":
        return [spell.f(p["role"])] + _nf_words(p["filler"], named, spell)
    if k in UNIT_KINDS or k in ("same", "readings"):
        return _nf_words(p, named, spell)
    if k == "time":
        # a time reference to a named unit stands as that unit's digest
        return spell.part(p, same=lambda name: _nf_words({"kind": "same", "name": name},
                                                         named, spell))
    return spell.part(p)
