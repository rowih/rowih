"""Word formation (specification/lexicon.md#word-formation): the meaning a derivation or a
compound has from its parts, so that "a previously unseen compound should be interpretable
from its components".

A content word is a stem, a root or a closed-class member followed by suffixes, and then
any number of further stems, each opened by the linker. A suffix is a function of the stem
it follows; a compound's first stem is its head and each further stem a modifier of
everything before it. A predicate head takes its modifier as its undergoer, or as its
content where it has no undergoer; a nominal head takes it as what the head bears on.
Wherever the form built so far is a word the release lists, the listed entry governs,
since a listed formation may mean more or less than its parts give
(specification/lexicon.md#listed-derivations-and-compounds) and is read only as its entry
states (`inv.word-formation`).

Meanings are plain data, so that the builder of the lexicon composes the definitions of
the compounds it lists with these same functions."""
from __future__ import annotations

PREDICATE_SORTS = ("s.sort.event", "s.sort.state", "s.sort.process")
CONNECTIVE = "g.situations-and-contents.connective."
# the roles a predicate head gives its modifier, in order of preference
MODIFIER_ROLES = ("undergoer", "content")
# suffixes whose formation keeps the argument structure of its base
KEEPS_ROLES = ("result", "privative", "reversative", "repetitive")
# suffixes whose formation keeps its base's sort as well: the honorific, which adds only
# the deference the ceremonial register shows (specification/lexicon.md#registers)
KEEPS_BASE = ("honorific",)
# suffixes whose formation adds the actor that brings its base about and keeps the base's
# other roles: the causative of lexicon 1.0, whose causee, the base's own actor, is no
# role of the formation
ADDS_ACTOR = ("causative",)
# suffixes whose formation has one role, its base's undergoer: the potential, which names
# what the base can be done to
TAKES_UNDERGOER = ("potential",)
# suffixes that name the filler of a role of their base
ROLE_NOUNS = ("agent", "undergoer")
ROLE_OF = {"agent": "actor", "undergoer": "undergoer"}


def category(meaning: dict) -> str:
    if meaning.get("connective"):
        return "connective"
    return "predicate" if meaning["sort"] in PREDICATE_SORTS else "nominal"


def of_entry(entry: dict) -> dict:
    """The meaning of a word the release lists: what its entry states."""
    return {"entry": entry["machine identifier"], "sort": entry["sort"],
            "arguments": [dict(a) for a in entry["argument structure"]],
            "definition": entry["definition"]}


def of_member(identifier: str, name: str) -> dict:
    """The meaning of a closed-class member as the base of a formation. Only a connective
    takes a suffix, the relational terms (specification/lexicon.md#word-formation)."""
    return {"entry": identifier, "sort": None, "arguments": [], "definition": name,
            "connective": identifier.startswith(CONNECTIVE)}


def derive(base: dict, suffix: dict) -> dict | None:
    """The formation of `suffix`, a suffix's entry, on `base`; None where the suffix does
    not take a stem of the base's kind or names a role the base lacks."""
    if base is None or category(base) != suffix["base"]:
        return None
    key = suffix["key"]
    sort = suffix["sort"]
    if key in ROLE_NOUNS:
        role = next((a for a in base["arguments"] if a["role"] == ROLE_OF[key]), None)
        if role is None:
            return None
        sort = role["sort"]
        arguments = []
    elif key in KEEPS_BASE:
        sort = base["sort"]
        arguments = [dict(a) for a in base["arguments"]]
    elif key in KEEPS_ROLES:
        arguments = [dict(a) for a in base["arguments"]]
    elif key in ADDS_ACTOR:
        arguments = [dict(a) for a in suffix["argument structure"]] + [
            dict(a) for a in base["arguments"] if a["role"] != "actor"]
    elif key in TAKES_UNDERGOER:
        role = next((a for a in base["arguments"] if a["role"] == "undergoer"), None)
        if role is None:
            return None
        arguments = [dict(role)]
    else:
        arguments = [dict(a) for a in suffix["argument structure"]]
    return {"mechanism": key, "parts": [base, suffix["machine identifier"]], "sort": sort,
            "arguments": arguments,
            "definition": suffix["definition"].replace("the base",
                                                       "[%s]" % base["definition"])}


def compound(head: dict, modifier: dict) -> dict | None:
    """The compound of `head` and `modifier`; None where the head is a predicate with no
    role a modifier takes, or a connective."""
    if head is None or modifier is None:
        return None
    kind = category(head)
    if kind == "predicate":
        role = next((r for r in MODIFIER_ROLES
                     if any(a["role"] == r for a in head["arguments"])), None)
        if role is None:
            return None
        arguments = [dict(a) for a in head["arguments"] if a["role"] != role]
        definition = "[%s], with [%s] as its %s" % (head["definition"],
                                                     modifier["definition"], role)
    elif kind == "nominal":
        arguments = []
        definition = "[%s], bearing on [%s]" % (head["definition"], modifier["definition"])
    else:
        return None
    return {"mechanism": "compound", "parts": [head, modifier], "sort": head["sort"],
            "arguments": arguments, "definition": definition}


def compose(morphemes: list, lang) -> dict | None:
    """The meaning of a content word from its morphemes, as the lexer segments them; None
    where a step of its formation has no meaning."""
    def listed(form, meaning):
        item = lang.by_form.get(form)
        if item is not None and item.kind in ("root", "derivation"):
            return of_entry(lang.entries[item.identifier])
        return meaning

    def stem_start(m):
        if m.kind == "member":
            return of_member(m.identifier, m.name)
        return of_entry(lang.entries[m.identifier])

    stems, current = [], []
    for m in morphemes:
        if m == "linker":
            stems.append(current)
            current = []
        else:
            current.append(m)
    stems.append(current)

    def stem_meaning(stem):
        meaning, form = None, ""
        for i, m in enumerate(stem):
            form += m.form
            meaning = stem_start(m) if i == 0 else derive(meaning, lang.entries[m.identifier])
            meaning = listed(form, meaning)
        return meaning

    meaning = stem_meaning(stems[0])
    form = "".join(m.form for m in stems[0])
    for stem in stems[1:]:
        meaning = compound(meaning, stem_meaning(stem))
        form += "i" + "".join(m.form for m in stem)
        meaning = listed(form, meaning)
    return meaning


def word_sort(p: dict, lang) -> str | None:
    """The sort of a word part of a tree: its entry's, or for a formation the release
    does not list, the sort its parts give; None for an unknown word."""
    if p.get("entry"):
        entry = lang.entries.get(p["entry"])
        return entry["sort"] if entry is not None else None
    if p.get("status") != "formation":
        return None
    from .lexer import segment
    morphemes = segment(p["form"], lang)
    meaning = compose(morphemes, lang) if morphemes else None
    return meaning["sort"] if meaning else None


def regular_word(p: dict, lang) -> dict:
    """A word part with an irregular word written as its regular form, the formation of
    the root and suffix its entry is formed from
    (specification/lexicon.md#listed-derivations-and-compounds), so that the word and the
    formation it stands for have one normal form."""
    entry = lang.entries.get(p.get("entry")) if p.get("entry") else None
    if entry is None or "irregular" not in entry:
        return p
    return dict(p, form=entry["irregular"]["regular form"], entry=None, status="formation")
