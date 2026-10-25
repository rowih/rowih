"""The checker's rules for conventional language
(specification/lexicon.md#conventional-expressions-and-idioms): the idiom mark, the
declared loss, formations read from their parts, and the act of definition
(specification/lexicon.md#coining-a-word-by-definition; `inv.core-closed`). Each takes the
checker, whose `add` records a diagnostic, so that the checker's own module keeps its
size."""
from __future__ import annotations

from . import formation, idioms, registers
from .lexer import segment

ROOT_ONSET = "r"
ROOT_LENGTH = 5
CRITICAL_DISTANCE = 3


def walk(node):
    """Every dict of a move tree, depth first."""
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from walk(v)
    elif isinstance(node, list):
        for x in node:
            yield from walk(x)


def check_conventions(checker, t: dict):
    """The idioms a move reads by their entries, the losses it declares, and the
    formations it uses."""
    lang = checker.lang
    norm = checker.normaliser()
    incurred = set()
    if t.get("act"):
        incurred.update(lang.entries[t["act"]]["declared loss"])
    # a register written in the head, and a politeness word, a diction and every
    # register-marked word, incur what their entries record
    # (specification/lexicon.md#politeness-words-and-dictions)
    if t.get("register"):
        incurred.add("register")
    for key in ("politeness", "diction"):
        if t.get(key):
            incurred.update(lang.entries[t[key]]["declared loss"])
    if registers.marked_words(t, lang):
        incurred.add("register")
    for node in walk(t["constituents"]):
        if node.get("kind") == "idiom":
            incurred.update(lang.entries[node["entry"]]["declared loss"])
        elif idioms.marked(node):
            entry, _ = idioms.resolve(node, norm)
            if entry is None:
                checker.add("d.checker.idiom-absent", node, expected=[
                    "an idiom of lexicon %s" % lang.version])
            else:
                incurred.update(lang.entries[entry]["declared loss"])
        elif node.get("kind") == "word" and node.get("status") == "formation":
            morphemes = segment(node["form"], lang)
            if morphemes is None or formation.compose(morphemes, lang) is None:
                checker.add("d.checker.formation-unfit", node, detected=[node["form"]],
                            note="a suffix that does not take its stem, or a compound "
                                 "whose head takes no modifier")
    losses = t.get("losses", [])
    if len(set(losses)) != len(losses):
        checker.add("d.checker.ill-typed", t, note="a loss declared twice")
    for loss in losses:
        name = lang.items[loss].name
        if name not in incurred:
            checker.add("d.checker.loss-not-incurred", t, detected=[name],
                        expected=sorted(incurred) or ["no declared loss"])


def distance(a: str, b: str) -> int:
    """The edit distance of two words, every edit of one symbol counting one."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _term_constituent(c: dict, lang) -> bool:
    """Whether a constituent states a defined word: a term holding only a declared-data
    wall of the language's media type, which the protocol states."""
    return (c.get("kind") == "term" and len(c["parts"]) == 1
            and c["parts"][0].get("kind") == "wall"
            and c["parts"][0].get("type") == lang.protocol["media type"])


def _scope_constituent(c: dict) -> bool:
    """Whether a constituent states a definition's scope: a term naming a dialect
    (specification/dialects.md#naming-a-dialect-in-a-message)."""
    return c.get("kind") == "term" and any(p.get("kind") == "dialect" for p in c["parts"])


def scope_of(t: dict) -> int | None:
    """The number of the dialect a definition is scoped to, or None for the exchange."""
    scopes = [c for c in t.get("constituents", []) if _scope_constituent(c)]
    if len(scopes) != 1:
        return None
    return int(next(p["number"] for p in scopes[0]["parts"] if p.get("kind") == "dialect"))


def defined_term(t: dict, lang=None) -> str | None:
    """The word a definition defines, from the one constituent that states it, or None.
    The constituent is found by its form, not its place, since the normal form orders
    a move's constituents canonically."""
    if lang is None:
        from .data import load
        lang = load()
    stating = [c for c in t["constituents"] if _term_constituent(c, lang)]
    if len(stating) != 1:
        return None
    from .lexer import decode_payload
    data = decode_payload(stating[0]["parts"][0]["data"])
    try:
        return data.decode("ascii") if data is not None else None
    except UnicodeDecodeError:
        return None


def root_shaped(word: str, lang) -> bool:
    return (len(word) == ROOT_LENGTH and word[0] == ROOT_ONSET and all(
        (c in lang.consonants) if i % 2 == 0 else (c in lang.vowels)
        for i, c in enumerate(word)))


def check_definition(checker, t: dict):
    """An act of definition states its term, as declared data of the language's media type
    in a term, and then its expansion, a term or a situation of the core. The term is
    shaped as a root, so that it takes suffixes and enters compounds and the lexicon stays
    a prefix code; it reaches no word of the grammar, shadows no word of the release,
    stands at a distance of two from every word and of three from every critical one, and
    its expansion neither contains it nor carries embedded material, whose kind is
    operative force (specification/lexicon.md#coining-a-word-by-definition;
    `inv.core-closed`)."""
    lang = checker.lang
    word = defined_term(t, lang)
    scopes = [c for c in t["constituents"] if _scope_constituent(c)]
    rest = [c for c in t["constituents"] if not _term_constituent(c, lang)
            and c not in scopes]
    if len(scopes) > 1:
        checker.add("d.checker.definition-form", t, note="a definition states one scope")
        return
    if scopes:
        # a definition scoped to a dialect proposes its term to that dialect, and is
        # written in a message that names it
        # (specification/lexicon.md#coining-a-word-by-definition)
        number = scope_of(t)
        named = [n.integer() for n, _, _ in getattr(checker.envelope, "dialects", [])]
        if number not in named:
            checker.add("d.checker.definition-scope", t, detected=["dialect %d" % number],
                        expected=["a dialect the message names"])
    if word is None or len(rest) != 1 or rest[0].get("kind") not in ("term", "situation"):
        checker.add("d.checker.definition-form", t, expected=[
            "a term holding the defined word as %s, then its expansion"
            % lang.protocol["media type"]])
        return
    item = lang.by_form.get(word)
    if item is not None:
        code = "d.checker.definition-shadows" if item.kind in ("root", "derivation") \
            else "d.checker.definition-reaches-the-core"
        checker.add(code, t, detected=[word, item.identifier])
        return
    if not root_shaped(word, lang):
        checker.add("d.checker.definition-form", t, detected=[word],
                    expected=["a word of five symbols beginning %s" % ROOT_ONSET])
        return
    near = confusable(word, lang)
    if near is not None:
        checker.add("d.checker.definition-confusable", t, detected=[word, near])
    expansion = rest[0]
    if any(n.get("kind") == "word" and n.get("form") == word for n in walk(expansion)):
        checker.add("d.checker.definition-recursive", t, detected=[word])
    if any(n.get("kind") in ("wall", "readings") for n in walk(expansion)):
        checker.add("d.checker.definition-carries-force", t,
                    note="a defined term may not stand for embedded material or readings")


def confusable(word: str, lang) -> str | None:
    """The first word of the release a defined term could be confused with: one within
    one edit of it, or a critical word within two."""
    for form, item in sorted(lang.by_form.items()):
        limit = CRITICAL_DISTANCE if (item.critical_code or item.protected) else 2
        if abs(len(form) - len(word)) < limit and distance(word, form) < limit:
            return form
    return None
