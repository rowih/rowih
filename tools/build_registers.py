"""The register part of the language build: lexicon release 0.4, with its register-marked
synonyms, honorific suffix, politeness words and dictions; the settings of the eight
registers in `lexicon/registers/`; and the jargon of the eleven communities in
`lexicon/jargon/`. Called by `build_language.py`, whose helpers and order of building it
shares."""
import build_language as B
import convention_source as C
import language_source as L
import register_source as R
from rowih import formation

# The devices of economy each mode admits.
MODE_DEVICES = {
    "full explicitness": [],
    "normal expression": ["declared defaults", "inheritance", "conventional expressions"],
    "compression": ["declared defaults", "inheritance", "conventional expressions",
                    "shared context", "dialect forms"],
    "idiom": ["declared defaults", "inheritance", "conventional expressions", "idioms"],
    "creative expression": ["declared defaults", "inheritance", "conventional expressions",
                            "marked figures", "creative ambiguity"],
}


def build_release_4(third, classes, roots, check_pool, move_check_forms, root_pool,
                    suffix_pool, protected_ball):
    """Release 0.4: its serials follow every earlier entry's and its forms every earlier
    word's. The register's members are appended to the list of critical forms after the
    act words, which raises the modulus of the move check word; the check words the
    larger modulus needs are the pool's next forms, a form within distance two of a
    protected word passed over, as release 0.3 drew its own. The new words are
    root-shaped, the root pool's next forms at distance three from every protected word
    and every act word."""
    serial = (len(L.ROOTS) + len(L.SUFFIXES) + len(L.DERIVATIONS) + len(L.ROOTS_ADDED)
              + len(C.SUFFIXES_ADDED) + len(C.ACT_WORDS) + len(C.COMPOUNDS) + len(C.IDIOMS))
    ids = iter("lx.%06d" % n for n in range(serial + 1, serial + 1000))
    crit = list(third["critical"])
    for name in R.APPENDED_CRITICAL_RELEASE_4:
        crit += [m["identifier"] for c in classes if c["name"] == name for m in c["members"]]
    modulus = B.next_prime(len(crit) + 1)
    earlier = list(third["forms"])
    added_checks = [f for f in check_pool if f not in earlier and f not in move_check_forms
                    and not B.ball(f) & protected_ball][:modulus - len(earlier)]
    forms = sorted(earlier + added_checks)
    avoid = set(protected_ball)
    for a in third["acts"]:
        avoid |= B.ball(a["form"])
    used = {r["form"] for r in roots}
    pool = iter(f for f in root_pool if f not in used and not B.ball(f) & avoid)
    by_key = {r["key"]: r for r in roots}
    synonyms = [{"key": k, "base": base, "vocabulary": v, "form": next(pool),
                 "identifier": next(ids)} for k, base, v in R.SYNONYMS]
    politeness = [{"key": k, "definition": d, "registers": regs, "form": next(pool),
                   "identifier": next(ids)} for k, d, regs in R.POLITENESS]
    dictions = [{"key": k, "definition": d, "modes": modes, "vocabulary": v,
                 "form": next(pool), "identifier": next(ids)} for k, d, modes, v in R.DICTIONS]
    taken = [s["form"] for s in third["suffixes"]]
    key, base, sort, definition, roles = R.HONORIFIC
    honorific = {"key": key, "base": base, "definition": definition, "roles": roles,
                 "form": next(f for f in suffix_pool[len(L.SUFFIXES):] if f not in taken),
                 "identifier": next(ids)}
    for s in synonyms:
        assert s["base"] in by_key, s
    return {"critical": crit, "modulus": modulus, "forms": forms, "synonyms": synonyms,
            "politeness": politeness, "dictions": dictions, "honorific": honorific}


def write_release_4(fourth, root_entry):
    """The entries of release 0.4; returns their identifiers in serial order."""
    out = []

    def put(sub, e):
        B.dump("lexicon/%s/%s.json" % (sub, e["machine identifier"]), e)
        out.append(e["machine identifier"])

    def serial(ident):
        return int(ident.split(".")[1])

    entries = []
    for s in fourth["synonyms"]:
        base = root_entry[s["base"]]
        e = B.entry(serial(s["identifier"]), s["key"], base["grammatical category"],
                    base["sort"], s["form"],
                    "%s (the %s vocabulary)" % (base["definition"], s["vocabulary"]),
                    [(a["role"], a["sort"]) for a in base["argument structure"]],
                    {"synonym of": base["machine identifier"], "vocabulary": s["vocabulary"],
                     "declared loss": ["register"]}, release=R.RELEASE)
        e["register"] = R.MARKED[s["vocabulary"]]
        entries.append(("roots", e))
    for s in fourth["synonyms"]:
        e = next(x for _, x in entries if x["key"] == s["key"])
        e["synonyms"] = [e2["machine identifier"] for _, e2 in entries
                         if e2.get("synonym of") == e["synonym of"] and e2 is not e] + [
            e["synonym of"]]
    for p in fourth["politeness"]:
        e = B.entry(serial(p["identifier"]), p["key"], "politeness word", "s.sort.move",
                    p["form"], p["definition"], [],
                    {"declared loss": ["relation between participants"]}, release=R.RELEASE)
        e["register"] = p["registers"]
        entries.append(("roots", e))
    for d in fourth["dictions"]:
        e = B.entry(serial(d["identifier"]), d["key"], "diction", "s.sort.kind", d["form"],
                    "the diction that is " + d["definition"], [],
                    {"modes": d["modes"], "vocabulary": d["vocabulary"],
                     "declared loss": ["diction"]}, release=R.RELEASE)
        entries.append(("roots", e))
    h = fourth["honorific"]
    e = B.entry(serial(h["identifier"]), h["key"], "derivational suffix", "s.sort.referent",
                h["form"], h["definition"], h["roles"],
                {"base": h["base"], "keeps": "the sort and roles of its base",
                 "declared loss": ["register"]}, release=R.RELEASE)
    e["phonological form"] = "/-" + "".join(B.IPA[c] for c in h["form"]) + "/"
    e["register"] = ["R7"]
    entries.append(("formation", e))
    for sub, e in sorted(entries, key=lambda x: x[1]["machine identifier"]):
        put(sub, e)
    return out


def write_registers(classes):
    """The eight registers' records: the modes each admits and the devices those modes
    admit, whether it is precision-bound by default, and its setting of each of its
    dimensions with what the checker and the generator read of them."""
    member = {m["name"]: m["identifier"] for c in classes if c["name"] == "register"
              for m in c["members"]}
    for (code, name, use, modes, bound, settings, vocabulary, politeness,
         formulas) in R.REGISTERS:
        devices = []
        for mode in modes:
            devices += [d for d in MODE_DEVICES[mode] if d not in devices]
        B.dump("lexicon/registers/%s.json" % code.lower(), {
            "code": code, "name": name, "member": member[name], "use": use,
            "modes admitted": modes, "devices admitted": devices,
            "precision-bound by default": bound, "settings": settings,
            "vocabulary": vocabulary, "politeness word": politeness,
            "formulas admitted": formulas,
            "order": "canonical" if settings["syntax"] == "canonical" else "free",
            "maxima": "language/protocol.json"})


def term_entry(identifier, key, form, meaning, formed_from, dialect):
    """A term of a dialect with the fields of a lexicon entry that a term added by
    definition carries: its scope, validity, provenance and acceptance status."""
    return {
        "machine identifier": identifier, "term": key, "orthographic form": form,
        "phonological form": "/" + "".join(B.IPA[c] for c in form) + "/",
        "grammatical category": "jargon", "sort": meaning["sort"],
        "semantic type": {"sort": meaning["sort"],
                          "arguments": [a["role"] for a in meaning["arguments"]]},
        "definition": meaning["definition"], "argument structure": meaning["arguments"],
        "formed from": formed_from, "mechanism": meaning.get("mechanism", "root"),
        "register": list(R.ALL),
        "scope": {"dialect": dialect, "version": R.JARGON_VERSION},
        "validity": "from the dialect's release, without end",
        "provenance": "generated from its stems by tools/build_registers.py",
        "acceptance status": "released",
        "version": {"introduced": R.JARGON_VERSION, "deprecated": None},
        "key": key,
    }


def write_jargon(root_entry, suffix_entry) -> dict:
    """The jargon of the eleven communities, the first release of each dialect: every
    term's form is its stems' forms joined by the linker, and its meaning the composition
    the rules of word formation give, computed here with the reader's own functions.
    Returns each release by its dialect, which `build_dialects.write_dialects` numbers and
    writes."""
    known = {e["orthographic form"] for e in root_entry.values()}
    seen = {}
    releases = {}
    for community, slug, terms in R.JARGON:
        out = []
        for n, (key, stems) in enumerate(terms, 1):
            meaning, forms = None, []
            for i, stem in enumerate(stems):
                root, *suffixes = stem
                m = formation.of_entry(root_entry[root])
                form = root_entry[root]["orthographic form"]
                for s in suffixes:
                    m = formation.derive(m, suffix_entry[s])
                    form += suffix_entry[s]["orthographic form"]
                    assert m is not None, (community, key, stem)
                meaning = m if i == 0 else formation.compound(meaning, m)
                assert meaning is not None, (community, key)
                forms.append(form)
            form = B.LINKER.join(forms)
            assert form not in known, (community, key, form)
            assert form not in seen, (community, key, seen.get(form))
            seen[form] = (community, key)
            formed_from = [[root_entry[s[0]]["machine identifier"]]
                           + [suffix_entry[x]["machine identifier"] for x in s[1:]]
                           for s in stems]
            out.append(term_entry("jg.%s.%03d" % (slug, n), key, form, meaning, formed_from,
                                  slug))
        releases[slug] = {
            "dialect": slug, "community": community, "version": R.JARGON_VERSION,
            "date": B.RELEASE_DATES[R.RELEASE], "formed from lexicon": R.RELEASE,
            "reading": "each term means the composition of its stems, as the rules of "
                       "word formation give it",
            "terms": out}
    return releases
