"""The checks a release of the lexicon must pass before it is published, run as
`check_release` and, for the dangling-suffix test of unique decodability,
`check_decodability`."""
from __future__ import annotations

import itertools

from . import formation, versions
from .data import Language, in_force

EVERY_ENTRY_FIELDS = [
    "root", "phonological form", "orthographic form", "grammatical category", "sort",
    "semantic type", "definition", "semantic primitives", "argument structure",
    "derivational behaviour", "register", "collocations", "synonyms", "antonyms",
    "related concepts", "machine identifier", "examples", "version",
]
# The fields of an idiom (specification/lexicon.md#conventional-expressions-and-idioms),
# with those the checks below add: which parts of its literal structure carry which parts
# of its expansion, its kind, its constructed history and what its expansion loses. An act
# word is a conventional expression and carries them too.
IDIOM_FIELDS = [
    "literal structure", "pragmatic conditions", "usage restrictions", "route",
    "expansion", "decomposition", "kind", "constructed history", "declared loss",
]
PLACEHOLDER = "(term record DEFINITE)"
# the release from which the rules below hold that lexicon 1.0 adds: an idiom fills only
# the roles the entries its words are read as take, and an idiom whose route is a figure
# is motivated by a mapping; the entries of earlier releases predate them and stay as
# released
FROM_RELEASE = "1.0"
# the kinds of word that are one morpheme, whose length their opening fixes
SIMPLE_KINDS = ("member", "structural", "move-check", "root", "act")


def ball(word: str, alphabet: str) -> set:
    """Every string within one edit (deletion, insertion or substitution) of `word`."""
    out = {word}
    for i in range(len(word)):
        out.add(word[:i] + word[i + 1:])
        for ch in alphabet:
            out.add(word[:i] + ch + word[i + 1:])
    for i in range(len(word) + 1):
        for ch in alphabet:
            out.add(word[:i] + ch + word[i:])
    return out


def levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def check_decodability(words) -> list:
    """The Sardinas-Patterson test: returns the dangling suffixes that are words, empty
    exactly when the code is uniquely decodable. Complexity O(k * |C|^2 * L) for k rounds
    over a code of |C| words of length at most L, bounded since every dangling suffix is a
    suffix of a codeword."""
    code = set(words)
    current = set()
    for a in code:
        for b in code:
            if a != b and b.startswith(a):
                current.add(b[len(a):])
    seen = set()
    hits = set()
    while current:
        hits |= current & code
        seen |= current
        nxt = set()
        for s in current:
            for c in code:
                if c.startswith(s) and c != s:
                    nxt.add(c[len(s):])
                if s.startswith(c) and s != c:
                    nxt.add(s[len(c):])
        current = nxt - seen
    return sorted(hits)


def _is_prime(k: int) -> bool:
    return k > 1 and all(k % d for d in range(2, int(k ** 0.5) + 1))


def check_release(lang: Language) -> list:
    """Every finding against the release; an empty list means it passes."""
    findings = []
    alphabet = lang.letters
    words = sorted(lang.by_form)
    protected = [w for w in words if lang.by_form[w].protected]

    for w in words:
        if not w or w[0] not in lang.consonants:
            findings.append(("not-consonant-initial", w))
        if any(ch not in alphabet for ch in w):
            findings.append(("outside-the-alphabet", w))
        # a word of one morpheme has the length its first syllable fixes, so that a hearer
        # divides a stream by its openings
        # (specification/sounds-and-words.md#how-a-words-opening-fixes-its-length)
        if lang.by_form[w].kind in SIMPLE_KINDS and lang.length_at(w) != len(w):
            findings.append(("length-not-fixed-by-opening", w))

    wordset = set(words)
    for w in words:
        near = (ball(w, alphabet) - {w}) & wordset
        for other in sorted(near):
            if w < other:
                findings.append(("distance-below-two", "%s %s" % (w, other)))

    balls = {w: ball(w, alphabet) for w in words}
    for p in protected:
        for w in words:
            if w != p and balls[p] & balls[w]:
                findings.append(("protected-distance-below-three", "%s %s" % (p, w)))

    for w in check_decodability(words):
        findings.append(("not-uniquely-decodable", w))

    # Every form spells one thing: no form is shared by two members, a structural word,
    # a move check form or an entry, read from the sources themselves rather than from
    # the index built over them (inv.one-critical-dimension, inv.check-forms-disjoint).
    spelled = {}
    sources = [(m["form"], m["identifier"]) for c in lang.grammar["classes"]
               for m in c["members"]]
    sources += [(x["form"], x["identifier"]) for x in lang.grammar["structural words"]]
    sources += [(f, "move check %d" % i) for i, f in enumerate(lang.move_check_forms)]
    # an idiom's orthographic form is the words of its literal structure, which spell
    # their own entries (specification/lexicon.md#conventional-expressions-and-idioms),
    # and a conventional sense spells its root's form, the frame it stands in selecting it
    # (specification/lexicon.md#figurative-senses-and-conceptual-mappings)
    sources += [(e["orthographic form"], ident) for ident, e in lang.entries.items()
                if e["grammatical category"] not in ("idiom", "conventional sense")]
    for form, ident in sources:
        if form in spelled:
            findings.append(("form-spells-two-things", "%s %s %s" % (form, spelled[form], ident)))
        spelled[form] = ident

    for ident, e in lang.entries.items():
        fields = EVERY_ENTRY_FIELDS + (IDIOM_FIELDS if e["grammatical category"] in (
            "idiom", "act word") else [])
        for f in fields:
            if f not in e:
                findings.append(("entry-field-missing", "%s %s" % (ident, f)))
    findings += check_senses(lang)
    findings += check_irregularity(lang)
    if versions.key(lang.version)[0] >= 1:
        findings += check_fields(lang)
    if not findings:
        # the checks of idioms read every entry, so they run on a release whose entries
        # are whole
        findings += check_idioms(lang)

    # the modulus by the rule of the release's major version
    # (specification/protocol.md#numbers-and-their-check-words): from major version 1 the
    # largest prime not above the admissible forms, within major version 0 the least prime
    # greater than one more than the critical forms
    n_critical = lang.release.get("critical forms", len(lang.grammar["critical forms"]))
    p = lang.modulus
    if versions.key(lang.version)[0] >= 1:
        expected = lang.grammar["move check word"]["admissible forms"]
        while not _is_prime(expected):
            expected -= 1
    else:
        expected = n_critical + 2
        while not _is_prime(expected):
            expected += 1
    if p != expected or p <= n_critical + 1:
        findings.append(("modulus-not-by-rule", "%d %d" % (p, expected)))
    if len(lang.move_check_forms) != p:
        findings.append(("move-check-forms-not-modulus", str(len(lang.move_check_forms))))
    if len(set(lang.move_check_forms)) != len(lang.move_check_forms):
        findings.append(("move-check-forms-repeat", ""))
    return findings


ROOT_CATEGORIES = ("predicate root", "nominal root", "unit of measure", "discourse relation")
INVERSE = {"kind of": "has kind", "has kind": "kind of", "part of": "has part",
           "has part": "part of", "involves": "involved in", "involved in": "involves"}


def check_fields(lang: Language) -> list:
    """From major version 1, every root states the derivations the rules of formation give
    it and at least one related concept; every synonym, antonym and related concept names
    an entry of the release, and is stated by that entry in turn, a near synonym and an
    antonym as they are and a related concept by its inverse relation."""
    findings = []
    for ident, e in lang.entries.items():
        # a deprecated root stays as released, and its replacement states its fields
        if e["grammatical category"] not in ROOT_CATEGORIES or "synonym of" in e \
                or not in_force(lang, e):
            continue
        if not e["related concepts"]:
            findings.append(("root-without-related-concept", ident))
        if not e["derivational behaviour"]:
            findings.append(("root-without-derivations", ident))
        for d in e["derivational behaviour"]:
            suffix = lang.entries.get(d["suffix"])
            regular = e["orthographic form"] + suffix["orthographic form"] if suffix else None
            # an irregular cell states its own form and its regular form beside it
            cell = lang.entries.get(d.get("listed"), {}) if "regular form" in d else {}
            if suffix is None or d.get("regular form", d["form"]) != regular or (
                    "regular form" in d and (cell.get("formed from") != [ident, d["suffix"]]
                                             or d["form"] != cell["orthographic form"])):
                findings.append(("derivation-misstated", "%s %s" % (ident, d["suffix"])))
        stated = [("synonyms", s["entry"], s.get("dimension"), s.get("difference"))
                  for s in e["synonyms"] if s.get("dimension") == "near"]
        stated += [("antonyms", a["entry"], None, None) for a in e["antonyms"]]
        for field, other, dimension, difference in stated:
            back = lang.entries.get(other, {}).get(field, [])
            if not any(b["entry"] == ident and b.get("dimension") == dimension
                       and b.get("difference") == difference for b in back):
                findings.append(("relation-not-mutual", "%s %s %s" % (ident, field, other)))
        for r in e["related concepts"]:
            back = lang.entries.get(r["entry"], {}).get("related concepts", [])
            if not any(b["entry"] == ident and b["relation"] == INVERSE.get(r["relation"])
                       for b in back):
                findings.append(("relation-not-mutual", "%s related %s" % (ident, r["entry"])))
    return findings


# the reasons an irregularity may have
IRREGULARITY_REASONS = ("frequency", "a constructed historical development",
                        "a functional pressure")


def check_irregularity(lang: Language) -> list:
    """Every irregularity has a documented reason, a lexicon entry and a test. A listed
    formation is regular, its form its parts' forms in order, a compound's joined by the
    linker, unless its entry states the irregularity: its kind, its regular form, one of
    the listed reasons, and its constructed history. An irregular derivation means exactly
    what its root and suffix compose
    (specification/lexicon.md#listed-derivations-and-compounds)."""
    findings = []
    for ident, e in lang.entries.items():
        if "formed from" not in e:
            continue
        parts = [lang.items[x].form for x in e["formed from"]]
        regular = ("i" if e["grammatical category"] == "compound" else "").join(parts)
        stated = e.get("irregular")
        if stated is None:
            if e["orthographic form"] != regular:
                findings.append(("irregularity-undocumented", ident))
            continue
        history = e.get("constructed history", "")
        if (stated.get("regular form") != regular or e["orthographic form"] == regular
                or not stated.get("kind") or stated.get("reason") not in IRREGULARITY_REASONS
                or not history.startswith("Constructed history: ")):
            findings.append(("irregularity-undocumented", ident))
            continue
        root, suffix = (lang.entries.get(x) for x in e["formed from"])
        meaning = formation.derive(formation.of_entry(root), suffix) \
            if root is not None and suffix is not None else None
        if meaning is None or (meaning["sort"], meaning["definition"], meaning["arguments"]) \
                != (e["sort"], e["definition"], e["argument structure"]):
            findings.append(("irregularity-misread", ident))
    return findings


FRAME_FILLERS = ("situation", "term")
PARTICIPATION = "g.situations-and-contents.participation."


def check_senses(lang: Language) -> list:
    """Every conventional sense extends a root of the release, spells its form, keeps its
    sort and names a frame of one participation role and a kind of filler; no two senses
    of one form share a frame, so that no unit selects two; and every sense names a
    mapping of the release that lists it, each mapping pairing elements of its source and
    target and motivating only senses and idioms whose route is a figure
    (specification/lexicon.md#figurative-senses-and-conceptual-mappings)."""
    findings = []
    frames = {}
    for ident, e in lang.entries.items():
        if e["grammatical category"] != "conventional sense":
            continue
        root = lang.entries.get(e.get("sense of"))
        if root is None or lang.items[e["sense of"]].kind != "root":
            findings.append(("sense-without-root", ident))
            continue
        if e["orthographic form"] != root["orthographic form"] or e["sort"] != root["sort"]:
            findings.append(("sense-differs-from-root", ident))
        frame = e.get("frame") or {}
        if not str(frame.get("role", "")).startswith(PARTICIPATION) or \
                frame["role"] not in lang.items or frame.get("filler") not in FRAME_FILLERS:
            findings.append(("sense-frame-ill-formed", ident))
            continue
        key = (e["sense of"], frame["role"], frame["filler"])
        if key in frames:
            findings.append(("sense-frames-overlap", "%s %s" % (frames[key], ident)))
        frames[key] = ident
        mapping = lang.mappings.get(e.get("motivating mapping"))
        if mapping is None or ident not in mapping["motivates"]:
            findings.append(("sense-without-mapping", ident))
    motivated = {t for m in lang.mappings.values() for t in m["motivates"]}
    for ident in lang.idioms:
        if lang.entries[ident].get("route") == "figure" and ident not in motivated and \
                _since(lang, ident):
            findings.append(("figure-without-mapping", ident))
    for ident, m in lang.mappings.items():
        if not m["correspondences"] or any(not c.get("source") or not c.get("target")
                                           for c in m["correspondences"]):
            findings.append(("mapping-without-correspondences", ident))
        for target in m["motivates"]:
            e = lang.entries.get(target)
            if e is None or not (e["grammatical category"] == "conventional sense" or (
                    e["grammatical category"] == "idiom" and e.get("route") == "figure")):
                findings.append(("mapping-motivates-no-figure", "%s %s" % (ident, target)))
    return findings


def _slots(node) -> set:
    if isinstance(node, dict):
        if node.get("kind") == "slot":
            return {node["slot"]}
        return set().union(*[_slots(v) for v in node.values()]) if node else set()
    if isinstance(node, list):
        return set().union(*[_slots(x) for x in node]) if node else set()
    return set()


def check_idioms(lang: Language) -> list:
    """Every act word expands to a head the parser reads; every idiom's literal structure
    and expansion are well-formed, with every slot the literal structure takes carried
    into the expansion and no idiom inside an expansion, so that expansion is one level
    deep; and no constituent selects two entries, so that a form determines its entry."""
    from . import idioms
    from .api import parse
    from .generator import Generator
    from .normal import Normaliser
    from .notation import Reader, sexp
    findings = []
    gen = Generator(lang)
    reader = Reader(lang)
    norm = Normaliser(lang)

    def clean(notation: str) -> list:
        text = gen.message(reader.moves(notation), "full explicitness")
        return [d.code for d in parse(text).diagnostics]

    for ident, e in lang.entries.items():
        if e["grammatical category"] == "act word":
            head = " ".join(lang.items[m].gloss for m in e["expansion"])
            for code in clean("(move %s %s)" % (lang.items[ident].gloss, _act_body(head))):
                if code.startswith("d.parser."):
                    findings.append(("act-word-expansion", "%s %s" % (ident, code)))
    filled = {}
    for ident in lang.idioms:
        e = lang.entries[ident]
        expansion = e["expansion"]
        if isinstance(e["literal structure"], list):
            used = set()
        else:
            literal = e["literal structure"]
            used = _slots(reader.node(sexp(literal)[0]))
            for n in used:
                literal = literal.replace("(slot %d)" % n, PLACEHOLDER)
            filled[ident] = literal
            for code in clean("(move ASSERTED-POSITION (assertion %s))" % literal):
                findings.append(("idiom-literal-ill-formed", "%s %s" % (ident, code)))
        if _slots(reader.node(sexp(expansion)[0])) != used:
            findings.append(("idiom-slots-differ", ident))
        if "(slot" in expansion and not used:
            findings.append(("idiom-slots-differ", ident))
        for n in used:
            expansion = expansion.replace("(slot %d)" % n, PLACEHOLDER)
        if "IDIOM-ENTRY" in expansion or "(idiom " in expansion:
            findings.append(("idiom-inside-an-expansion", ident))
        for code in clean("(move ASSERTED-POSITION (assertion %s))" % expansion):
            findings.append(("idiom-expansion-ill-formed", "%s %s" % (ident, code)))
        if _since(lang, ident):
            trees = [idioms.expansion(lang, ident)]
            if not isinstance(e["literal structure"], list):
                trees.append(idioms.literal(lang, ident))
            for tree in trees:
                for word, role in _roles_not_taken(lang, tree):
                    findings.append(("idiom-role-not-taken", "%s %s %s" % (ident, word, role)))
    grammatical = idioms.grammatical(lang)
    patterns = {i: norm.node(idioms.literal(lang, i), "actual") for i in grammatical}
    literals = {i: idioms.literal(lang, i) for i in grammatical}
    critical = {i: _critical_values(lang, norm, i) for i in grammatical}
    coded = _coded(lang)
    for i in grammatical:
        # an idiom whose literal structure is its expansion adds nothing by its mark, so
        # the writer leaves the mark out and no hearer can tell the entry was used
        if patterns[i] == norm.node(idioms.expansion(lang, i), "actual"):
            findings.append(("idiom-literal-is-its-expansion", i))
    for a, b in itertools.combinations(sorted(patterns), 2):
        if idioms.unify(patterns[a], patterns[b]):
            findings.append(("idiom-form-selects-two", "%s %s" % (a, b)))
        elif critical[a] != critical[b] and \
                idioms.substitutions(patterns[a], patterns[b], coded) < idioms.FAR:
            # one substitution of a word without a code would turn the one marked idiom
            # into the other, and with it a critical value of the core, which only the
            # integrity check value would then detect (`inv.single-edit-detected`); the
            # distance is counted between the normal forms the reader matches, with the
            # defaults supplied, since a literal that writes its root's default aspect
            # stands as near another as one that leaves it to the default
            findings.append(("idiom-one-edit-from-another", "%s %s" % (a, b)))
    return findings


def _since(lang: Language, ident: str) -> bool:
    """Whether the entry was introduced by FROM_RELEASE or later."""
    return versions.key(lang.entries[ident]["version"]["introduced"]) >= \
        versions.key(FROM_RELEASE)


def _roles_not_taken(lang: Language, tree) -> list:
    """Each (word, role) of a situation of `tree` that fills a participation role the entry
    its word is read as, a root or a conventional sense, does not take; a situation whose
    predicate is a value, an attitude, has no entry and is passed over."""
    from . import senses
    found = []

    def walk(x):
        if isinstance(x, dict):
            if x.get("kind") == "situation":
                ident = senses.entry_read(x, lang)
                if ident is not None:
                    taken = {a["role"] for a in lang.entries[ident]["argument structure"]}
                    for p in x["parts"]:
                        if p.get("kind") == "filler" and p["role"].startswith(PARTICIPATION) \
                                and p["role"][len(PARTICIPATION):] not in taken:
                            found.append((lang.entries[ident]["key"],
                                          p["role"][len(PARTICIPATION):]))
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(tree)
    return found


def _coded(lang: Language):
    def critical(identifier):
        item = lang.items.get(identifier)
        return item is not None and (item.critical_code > 0 or item.protected)
    return critical


def _critical_values(lang: Language, norm, entry: str) -> list:
    """The critical values an idiom's expansion writes into the core, with the units and
    roles that hold them, as the single-edit enumeration compares them; slots aside."""
    from . import idioms
    from .conformance import _walk
    found = []
    _walk(norm.node(idioms.expansion(lang, entry), "actual"), ("move",), found, lang)
    return sorted(found, key=repr)


def _act_body(head: str) -> str:
    """A move body that completes a head an act word expands to, for checking that the
    parser reads it: a reference where the head changes an entry, an authority and a
    content. Whether the act fits what it names is the checker's, and not asked here."""
    out = []
    if any(w in head.split() for w in ("RESOLUTION", "LOWERING", "ACKNOWLEDGEMENT", "NONE")):
        out.append("SPEAKERS-OWN (names 2 1 ISSUE PROPOSAL OPEN)")
    else:
        out.append("SPEAKERS-OWN")
    return " ".join(out) + " (situation examine (ACTOR (term SELF)) (UNDERGOER (term record)))"
