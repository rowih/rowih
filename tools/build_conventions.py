"""The idiom part of the language build: lexicon release 0.3, its act words, idioms,
suffixes and compounds, the entries it writes and the trees of its idioms in
`lexicon/semantic/`. Called by `build_language.py`, whose helpers and order of building it
shares; kept apart so that each script stays one concern."""
import re

import build_language as B
import convention_source as C
import language_source as L
from rowih import formation


def build_release_3(rng, classes, critical, check_pool, move_check_forms, roots,
                    suffix_pool, ordinary_ball, protected_ball):
    """Lexicon release 0.3: its serials follow every earlier entry's and its forms every
    earlier word's, so that nothing earlier moves. The act words are force words, six
    symbols at distance three from every word, drawn after the earlier protected words;
    their codes follow every earlier code, which raises the modulus of the move check
    word, and the check words the larger modulus needs are the pool's next forms, a form
    within distance two of a protected word passed over."""
    serial = len(L.ROOTS) + len(L.SUFFIXES) + len(L.DERIVATIONS) + len(L.ROOTS_ADDED)
    ids = iter("lx.%06d" % n for n in range(serial + 1, serial + 1000))
    member_id = {m["gloss"]: m["identifier"] for c in classes for m in c["members"]}
    acts = [{"key": key, "expansion": [member_id[g] for g in glosses], "acts": named,
             "answers": answers, "identifier": None}
            for key, glosses, named, answers in C.ACT_WORDS]
    suffixes = [{"key": k, "base": b, "sort": s, "definition": d, "roles": r,
                 "form": f} for (k, b, s, d, r), f in
                zip(C.SUFFIXES_ADDED, suffix_pool[len(L.SUFFIXES):])]
    for s in suffixes:
        s["identifier"] = next(ids)
    for a in acts:
        a["identifier"] = next(ids)
    crit = list(critical)
    for name in C.APPENDED_CRITICAL_RELEASE_3:
        crit += [m["identifier"] for c in classes if c["name"] == name for m in c["members"]]
    crit += [a["identifier"] for a in acts]
    modulus = B.next_prime(len(crit) + 1)
    later_roots = set()
    for r in roots:
        if "release" in r:
            later_roots |= B.ball(r["form"])
    added_checks = [f for f in check_pool[len(move_check_forms):]
                    if not B.ball(f) & protected_ball][:modulus - len(move_check_forms)]
    forms = sorted(move_check_forms + added_checks)
    avoid = ordinary_ball | later_roots
    for f in added_checks:
        avoid |= B.ball(f)
    taken = set(protected_ball)
    for a in acts:
        for _ in range(200000):
            w = "k" + "".join(rng.choice(B.VOWELS) if i % 2 == 0 else rng.choice(B.CONSONANTS)
                              for i in range(5))
            b = B.ball(w)
            if b & avoid or b & taken:
                continue
            a["form"] = w
            taken |= b
            break
        else:
            raise SystemExit("no form for the act word %s" % a["key"])
    root_form = {r["key"]: r["form"] for r in roots}
    compounds = [{"key": k, "stems": stems, "definition": d, "route": route,
                  "history": h, "form": "i".join(root_form[s] for s in stems),
                  "identifier": next(ids)} for k, stems, d, route, h in C.COMPOUNDS]
    idioms = [dict(i, identifier=next(ids)) for i in C.IDIOMS]
    return {"critical": crit, "modulus": modulus, "forms": forms, "acts": acts,
            "suffixes": suffixes, "compounds": compounds, "idioms": idioms}


def idiom_words(literal, root_entry):
    """The forms of the content words of an idiom's literal structure, in order: its
    orthographic form, the structure itself being recorded beside it."""
    if isinstance(literal, list):
        return " ".join(root_entry[k]["orthographic form"] for k in literal)
    # the notation writes a key of several words with hyphens (`notation.key_of`)
    keys = [k.replace("-", " ") for k in re.findall(r"[(\s]([a-z][a-z-]*)(?=[\s)])", literal)]
    keys = [k for k in keys if k in root_entry]
    return " ".join(root_entry[k]["orthographic form"] for k in keys)


def decomposition(idiom):
    """Which part of the literal structure carries which part of the expansion: each slot,
    with the role it fills in each (see
    specification/lexicon.md#conventional-expressions-and-idioms)."""
    if isinstance(idiom["literal"], list):
        return []
    found = re.compile(r"\(([A-Z][A-Z.-]*) \(slot (\d+)\)\)")
    lit = {n: r for r, n in found.findall(idiom["literal"])}
    exp = {n: r for r, n in found.findall(idiom["expansion"])}
    return [{"slot": int(n), "literal role": lit[n], "expansion role": exp.get(n)}
            for n in sorted(lit)]


def write_release_3(third, root_entry, classes):
    """The entries of release 0.3, written where their kind belongs; returns their
    identifiers in serial order."""
    out = []
    gloss = {m["identifier"]: m["gloss"] for c in classes for m in c["members"]}

    def put(sub, e):
        B.dump("lexicon/%s/%s.json" % (sub, e["machine identifier"]), e)
        out.append(e["machine identifier"])

    def serial(ident):
        return int(ident.split(".")[1])

    for s in third["suffixes"]:
        e = B.entry(serial(s["identifier"]), s["key"], "derivational suffix", s["sort"],
                  s["form"], s["definition"], s["roles"], {"base": s["base"]},
                  release=C.RELEASE)
        e["phonological form"] = "/-" + "".join(B.IPA[c] for c in s["form"]) + "/"
        put("formation", e)
    for a in third["acts"]:
        words = " ".join(gloss[m] for m in a["expansion"])
        e = B.entry(serial(a["identifier"]), a["key"], "act word", "s.sort.move", a["form"],
                  "the conventional expression of %s: %s" % (", ".join(a["acts"]), words),
                  [], {"expansion": a["expansion"], "acts": a["acts"],
                       "answers": a["answers"], "kind": "encoding, grammatical",
                       "route": "compression", "literal structure": a["form"],
                       "decomposition": [], "pragmatic conditions":
                           "wherever the head it expands may be written",
                       "usage restrictions": "none", "declared loss": [],
                       "constructed history": "Constructed history: the head %s, frequent "
                       "enough to be said as one word, shortened to the force word that "
                       "now stands for it." % words},
                  release=C.RELEASE)
        put("idioms", e)
    for c in third["compounds"]:
        head, *mods = [root_entry[k] for k in c["stems"]]
        meaning = formation.of_entry(head)
        for m in mods:
            meaning = formation.compound(meaning, formation.of_entry(m))
        definition = c["definition"] or meaning["definition"]
        e = B.entry(serial(c["identifier"]), c["key"], "compound", meaning["sort"], c["form"],
                  definition, [(a["role"], a["sort"]) for a in meaning["arguments"]],
                  {"formed from": [root_entry[k]["machine identifier"] for k in c["stems"]],
                   "composition": meaning["definition"], "route": c["route"],
                   "constructed history": c["history"]},
                  release=C.RELEASE)
        e["root"] = head["machine identifier"]
        put("formation", e)
    for i in third["idioms"]:
        put("idioms", idiom_entry(i, root_entry, serial(i["identifier"]), C.RELEASE))
    return out


def idiom_entry(i, root_entry, serial, release):
    """The entry of an idiom larger than a word: the forms of its words, its literal
    structure and expansion, and the fields an idiom adds to those of any lexicon
    entry."""
    words = idiom_words(i["literal"], root_entry)
    e = B.entry(serial, i["key"], "idiom", "s.sort.situation", words.replace(" ", ""),
                i["definition"], [],
                {"class": i["class"], "kind": i["kind"], "route": i["route"],
                 "literal structure": i["literal"], "expansion": i["expansion"],
                 "decomposition": decomposition(i),
                 "pragmatic conditions": i["pragmatics"],
                 "usage restrictions": i["restrictions"], "declared loss": i["loss"],
                 "constructed history": i["history"]},
                release=release)
    e["register"] = i["registers"]
    e["orthographic form"] = words
    e["phonological form"] = "/" + " ".join(
        "".join(B.IPA[c] for c in w) for w in e["orthographic form"].split()) + "/"
    return e


def write_semantic():
    """Each idiom's literal structure and expansion as trees of the semantic
    representation, with slots, in `lexicon/semantic/` (see
    specification/lexicon.md#conventional-expressions-and-idioms): what both
    implementations read, so that neither needs the notation. Written once the language
    files exist, since the notation is read against them."""
    from rowih import data
    from rowih.notation import Reader, sexp
    data._load_release.cache_clear()
    lang = data.load(B.LEXICON_VERSION)
    reader = Reader(lang)
    for ident in lang.idioms:
        e = lang.entries[ident]
        literal = e["literal structure"]
        B.dump("lexicon/semantic/%s.json" % ident, {
            "machine identifier": ident,
            "literal structure": next(list(w) for w, i in lang.extragrammatical.items()
                                      if i == ident) if isinstance(literal, list)
            else reader.node(sexp(literal)[0]),
            "expansion": reader.node(sexp(e["expansion"])[0]),
            "generated from": "lexicon/idioms/%s.json" % ident})
