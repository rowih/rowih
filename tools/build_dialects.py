"""The dialect part of the build: the words of language 0.10, appended after every earlier
word so that nothing earlier moves, and the release each grammar word was introduced in;
lexicon release 0.7, its roots, critical forms and modulus; the dialect releases with
their compressed forms; the feature registry and the fixed forms protocol 0.4 adds; and
the record of the language releases.

Called from `build_language.py`, whose helpers it uses."""
import build_language as B
import build_registers as BR
import convention_source as C
import dialect_source as D
import figure_source as F
import language_source as L
import register_source as R
import robustness_source as RB
from rowih import dialects, formation, versions


def mark_introduced(classes: list, structural: list):
    """Every class, member and structural word states the language release that
    introduced it, the core's release where it states none."""
    for cls in classes:
        cls.setdefault("introduced", B.VERSION)
        for m in cls["members"]:
            m.setdefault("introduced", cls["introduced"])
    for s in structural:
        name = s["name"]
        s.setdefault("introduced", D.INTRODUCED_STRUCTURAL.get(name, B.VERSION))


def append_words(classes: list, structural: list) -> tuple:
    """Add the members and structural words of language 0.10 to the grammar. Returns them
    in the order they take forms, after every word of earlier versions."""
    members = []
    for class_name, member, version, reason in D.APPENDED_MEMBERS:
        cls = next(c for c in classes if c["name"] == class_name)
        m = {"identifier": "%s.%s" % (cls["identifier"], B.slug(member)), "name": member,
             "gloss": B.label(member), "introduced": version, "reason": reason}
        cls["members"].append(m)
        members.append(m)
    words = []
    for name, description, version in D.APPENDED_STRUCTURAL:
        s = {"identifier": "g.structure.%s" % B.slug(name), "name": name,
             "gloss": B.label(name), "description": description, "introduced": version}
        structural.append(s)
        words.append(s)
    return members, words


def _first_serial() -> int:
    """The serial before release 0.7's first, counted as release 0.6 counts its own."""
    return (len(L.ROOTS) + len(L.SUFFIXES) + len(L.DERIVATIONS) + len(L.ROOTS_ADDED)
            + len(C.SUFFIXES_ADDED) + len(C.ACT_WORDS) + len(C.COMPOUNDS) + len(C.IDIOMS)
            + len(R.SYNONYMS) + len(R.POLITENESS) + len(R.DICTIONS) + len(F.ROOTS)
            + len(F.SENSES) + len(RB.ROOTS) + 1)


def build_release_7(fourth: dict, roots: list, root_pool: list, protected_ball: set,
                    third: dict) -> dict:
    """Release 0.7: its roots take the root pool's next forms at distance three from every
    protected word and every act word, as releases 0.5 and 0.6 drew theirs, and then the
    compressed forms of the dialects take the forms after them, under the same rule, so
    that no root of the release can be confused with a dialect form. The dialect word is
    appended to the list of critical forms, whose modulus stays 227."""
    sixth = fourth["sixth"]
    ids = iter("lx.%06d" % n for n in range(_first_serial() + 1, _first_serial() + 1000))
    avoid = set(protected_ball)
    for a in third["acts"]:
        avoid |= B.ball(a["form"])
    words = fourth["synonyms"] + fourth["politeness"] + fourth["dictions"]
    used = ({r["form"] for r in roots} | {w["form"] for w in words}
            | {r["form"] for r in fourth["fifth"]["roots"]} | {r["form"] for r in sixth["roots"]})
    pool = iter(f for f in root_pool if f not in used and not B.ball(f) & avoid)
    added = [{"key": k, "kind": kind, "sort": sort, "definition": d, "roles": roles,
              "form": next(pool), "identifier": next(ids)}
             for k, kind, sort, d, roles in D.ROOTS]
    crit = list(sixth["critical"]) + ["g.structure.%s" % B.slug(n)
                                      for n in D.APPENDED_CRITICAL_STRUCTURAL]
    modulus = B.next_prime(len(crit) + 1)
    assert modulus == sixth["modulus"], (modulus, sixth["modulus"])
    forms = []
    for slug in D.WITH_FORMS:
        for key in _form_keys(slug):
            forms.append({"dialect": slug, "key": key, "form": next(pool)})
    return {"roots": added, "critical": crit, "modulus": modulus, "forms": sixth["forms"],
            "dialect forms": forms}


def _jargon(slug: str) -> list:
    """The terms of a dialect's first release, as `register_source.JARGON` gives them."""
    if slug == D.CONVERSATION[1]:
        return D.CONVERSATION[2]
    return next(terms for _, s, terms in R.JARGON if s == slug)


def _form_keys(slug: str) -> list:
    """The terms of a dialect's latest release that take a compressed form: every term but
    those it deprecates, a replacement in place of the term it replaces."""
    return [key for key, _ in _jargon(slug)]


def write_release_7(seventh: dict, root_entry: dict) -> list:
    """The entries of release 0.7; returns their identifiers in serial order."""
    out = []
    categories = {"predicate": "predicate root", "nominal": "nominal root"}
    for r in seventh["roots"]:
        e = B.entry(int(r["identifier"].split(".")[1]), r["key"], categories[r["kind"]],
                    r["sort"], r["form"], r["definition"], r["roles"], release=D.RELEASE)
        B.dump("lexicon/roots/%s.json" % e["machine identifier"], e)
        root_entry[r["key"]] = e
        out.append(e["machine identifier"])
    return out


def _term(slug, n, key, stems, root_entry, suffix_entry, version, provenance):
    meaning, forms = None, []
    for i, stem in enumerate(stems):
        root, *suffixes = stem
        m = formation.of_entry(root_entry[root])
        form = root_entry[root]["orthographic form"]
        for s in suffixes:
            m = formation.derive(m, suffix_entry[s])
            form += suffix_entry[s]["orthographic form"]
            assert m is not None, (slug, key, stem)
        meaning = m if i == 0 else formation.compound(meaning, m)
        assert meaning is not None, (slug, key)
        forms.append(form)
    formed_from = [[root_entry[s[0]]["machine identifier"]]
                   + [suffix_entry[x]["machine identifier"] for x in s[1:]] for s in stems]
    e = BR.term_entry("jg.%s.%03d" % (slug, n), key, B.LINKER.join(forms), meaning,
                      formed_from, slug)
    e["scope"]["version"] = version
    e["version"] = {"introduced": version, "deprecated": None}
    e["provenance"] = provenance
    return e


def _admitting(device: str) -> list:
    """The registers one of whose modes admits `device`."""
    out = []
    for code, _, _, modes, *_ in R.REGISTERS:
        if any(device in BR.MODE_DEVICES[mode] for mode in modes):
            out.append(code)
    return out


def _form_entry(slug, n, record, term, version):
    """A compressed form: a word of the root's shape whose meaning is the term it
    compresses, which the normal form writes in its place."""
    form = record["form"]
    ident = "dl.%s.%03d" % (slug, n)
    return {
        "machine identifier": ident, "root": ident, "term": term["term"],
        "orthographic form": form,
        "phonological form": "/" + "".join(B.IPA[c] for c in form) + "/",
        "grammatical category": "dialect form", "sort": term["sort"],
        "semantic type": term["semantic type"],
        "definition": "the compressed form of the term %s: %s" % (term["term"],
                                                                 term["definition"]),
        "semantic primitives": [term["sort"]],
        "argument structure": term["argument structure"],
        "derivational behaviour": [],
        "collocations": [], "synonyms": [{"entry": term["machine identifier"],
                                          "dimension": "compression"}],
        "antonyms": [], "related concepts": [], "examples": [],
        "expansion": {"term": term["machine identifier"],
                      "form": term["orthographic form"]},
        "mechanism": "compression",
        "register": _admitting("dialect forms"),
        "scope": {"dialect": slug, "version": version},
        "validity": "from the dialect's release, without end",
        "provenance": "assigned by tools/build_dialects.py from the root pool",
        "acceptance status": "released",
        "version": {"introduced": version, "deprecated": None},
        "key": term["term"],
    }


def write_dialects(root_entry: dict, suffix_entry: dict, first: dict, seventh: dict):
    """The dialect releases: each community's first release, which
    `build_registers.write_jargon` returned, unchanged in its terms and now numbered;
    release 0.2 of each dialect that takes compressed forms, with every term of 0.1, its
    replacements and a form for each current term; and the conversational dialect's first
    release, its terms and forms together."""
    taken = {e["orthographic form"] for e in root_entry.values()}
    by_dialect = {}
    for f in seventh["dialect forms"]:
        by_dialect.setdefault(f["dialect"], []).append(f)
    out = {}
    for slug, record in first.items():
        record = dict(record, number=D.DIALECT_NUMBERS[slug])
        record["digest"] = dialects.digest(record)
        B.dump("lexicon/jargon/%s/%s.json" % (slug, record["version"]), record)
        out[(slug, record["version"])] = record
        if slug not in D.WITH_FORMS:
            continue
        terms = [dict(t) for t in record["terms"]]
        for dialect, key, stems, reason in D.REPLACED_TERMS:
            if dialect != slug:
                continue
            old = next(t for t in terms if t["term"] == key)
            new = _term(slug, len(terms) + 1, key, stems, root_entry, suffix_entry,
                        D.DIALECT_VERSION, "replaces %s, deprecated: %s"
                        % (old["machine identifier"], reason))
            old["version"] = dict(old["version"], deprecated=D.DIALECT_VERSION)
            old["replaced by"] = new["machine identifier"]
            terms.append(new)
        out[(slug, D.DIALECT_VERSION)] = _write_with_forms(
            slug, record["community"], D.DIALECT_VERSION, terms, by_dialect[slug])
    slug, community, stems_by_key = D.CONVERSATION
    terms = [_term(slug, n, key, stems, root_entry, suffix_entry, "0.1",
                   "generated from its stems by tools/build_dialects.py")
             for n, (key, stems) in enumerate(stems_by_key, 1)]
    out[(slug, "0.1")] = _write_with_forms(slug, community, "0.1", terms, by_dialect[slug])
    for record in out.values():
        for t in record["terms"]:
            assert t["orthographic form"] not in taken, (t["machine identifier"])
    return out


def _write_with_forms(slug, community, version, terms, assigned):
    current = [t for t in terms if not t["version"]["deprecated"]]
    keys = [r["key"] for r in assigned]
    assert sorted(keys) == sorted(t["term"] for t in current), (slug, keys)
    forms = [_form_entry(slug, n, r, next(t for t in current if t["term"] == r["key"]),
                         version) for n, r in enumerate(assigned, 1)]
    record = {"dialect": slug, "number": D.DIALECT_NUMBERS[slug], "community": community,
              "version": version, "date": D.RELEASE_DATE, "formed from lexicon": D.RELEASE,
              "reading": "each term means the composition of its stems, as the rules of "
                         "word formation give it; each compressed form means the term it "
                         "compresses, which a hearer computes only from this release",
              "terms": terms, "forms": forms}
    record["digest"] = dialects.digest(record)
    B.dump("lexicon/jargon/%s/%s.json" % (slug, version), record)
    return record


def protocol_additions(classes: list, structural: list, prior: dict | None) -> dict:
    """What protocol 0.4 adds to the protocol schema: the fixed forms of version
    negotiation, the codes of the unit check word for them, and the feature registry.
    A build that would change a fixed form or a feature stops."""
    fixed = {}
    for cls in classes:
        if cls["identifier"] in RB.FIXED_CLASSES:
            for m in cls["members"]:
                fixed[m["identifier"]] = m["form"]
    for s in structural:
        if s["identifier"] in D.FIXED_STRUCTURAL:
            fixed[s["identifier"]] = s["form"]
    if prior and "fixed forms" in prior:
        for ident, form in prior["fixed forms"].items():
            if fixed.get(ident) != form:
                raise SystemExit("the fixed form of %s would change from %s to %s"
                                 % (ident, form, fixed.get(ident)))
    features = []
    for number, name, introduced, flag, members, reason in D.FEATURES:
        features.append(dict({"number": number, "name": name, "introduced": introduced,
                              "flag": flag, "reason": reason}, **members))
    if prior and "features" in prior:
        for old in prior["features"]:
            new = next((f for f in features if f["number"] == old["number"]), None)
            if new != old:
                raise SystemExit("feature %d would change" % old["number"])
    codes = dict(RB.UNIT_CODES)
    for ident, code in D.UNIT_CODES.items():
        assert ident not in codes, ident
        codes[ident] = code
    added = sorted(set(fixed) - set(_fixed_of_0_3(classes)))
    return {
        "fixed forms": fixed,
        "fixed forms added": {D.PROTOCOL_VERSION: added},
        "unit check word codes": codes,
        "features": features,
        "feature rule": "a word belongs to a feature by its class, its own identifier or "
                        "the grammatical category of its lexicon entry, and a "
                        "conventional sense where a frame selects it; a reader lacking a "
                        "may-ignore feature passes over its words in a move's head and "
                        "keeps a word of it standing as content opaque, and a reader "
                        "lacking a must-understand feature rejects every move that uses "
                        "it",
        "language releases": "language/releases.json",
    }


def _fixed_of_0_3(classes: list) -> list:
    out = []
    for cls in classes:
        if cls["identifier"] in RB.FIXED_CLASSES:
            out += [m["identifier"] for m in cls["members"]
                    if m.get("introduced") != D.LANGUAGE_VERSION]
    return out


def write_releases(language_releases: list = D.LANGUAGE_RELEASES,
                   least_lexicon: dict = D.LEAST_LEXICON,
                   protocol_reads: dict = D.PROTOCOL_READS):
    """`language/releases.json`: every language release with the protocol and lexicon it
    was released with, the least lexicon release a message of it may name, and the
    releases whose messages it reads with the same meaning; and what each protocol
    version reads of the protocol messages of others. Later versions pass their releases
    in."""
    out = []
    for version, date, protocol, lexicon, reads in language_releases:
        record = {"language": version, "date": date, "protocol": protocol,
                  "lexicon": lexicon, "reads": reads}
        if version in least_lexicon:
            record["least lexicon"] = least_lexicon[version]
        out.append(record)
    assert [r["language"] for r in out] == versions.ordered(r["language"] for r in out)
    B.dump("language/releases.json", {
        "rule": "a reader of a release reads the messages of each release it lists under "
                "`reads` with the meaning that release gave them, and a message of a "
                "language release names a lexicon release no earlier than its `least "
                "lexicon`; from major version 1 a release reads every earlier release of "
                "its major version",
        "language": out,
        "protocol": [{"protocol": p, "reads": r} for p, r in protocol_reads.items()]})
