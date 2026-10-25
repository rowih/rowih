"""Version 1.0's part of the build: the long roots of lexicon 1.0, drawn from the
long-root code (see specification/lexicon.md#the-codes-from-which-forms-are-drawn) after
every earlier word; the move check word of major version 1, whose modulus is the largest
prime the h code admits and whose new forms follow the released ones, so that a released
form keeps its value (see specification/protocol.md#the-move-check-word); and the entries
of the release.

Called from `build_language.py`, whose helpers it uses."""
import json
import os
import random

import build_conventions as BC
import build_dialects as BD
import build_figures as BF
import build_language as B
import dialect_source as D
import figure_source as F
import language_source as L
import version1_conventions as VC
import version1_source as V


def long_code() -> list:
    """The 4,900 long roots: the syllable nu, then c2 v2 c3 v3, and c4 fixed by them
    so that any two differ in at least two symbols."""
    words = []
    for c2 in range(14):
        for v2 in range(5):
            for c3 in range(14):
                for v3 in range(5):
                    c4 = (V.LONG_ROOT_OFFSET + c2 + 2 * v2 + 3 * c3 + 4 * v3) % 14
                    words.append(V.LONG_ROOT_SYLLABLE + B.CONSONANTS[c2] + B.VOWELS[v2]
                                 + B.CONSONANTS[c3] + B.VOWELS[v3] + B.CONSONANTS[c4])
    return words


def largest_prime(n: int) -> int:
    """The largest prime not above `n`."""
    k = n
    while k > 1 and not all(k % d for d in range(2, int(k ** 0.5) + 1)):
        k -= 1
    return k


def _first_serial() -> int:
    """The serial before lexicon 1.0's first: release 0.7's last root's."""
    return BD._first_serial() + len(D.ROOTS)


def build_release(fourth: dict, protected_ball: set, third: dict, check_pool: list,
                  roots_before: list, root_pool: list, suffix_pool: list) -> dict:
    """Lexicon 1.0: its roots take the long code's forms in a seeded order, passing over
    any form within distance two of a protected word or an act word, as every root since
    release 0.2 has been drawn; the roots of units join the list of critical forms; the
    move check word takes the largest prime the h code admits, its released forms first;
    the compressed forms of the dialects' new terms take the short code's next forms, as
    release 0.7's did; and the suffixes take the suffix code's next forms, after the
    honorific's. The suffixes, formulas, idioms and senses take the serials after the
    roots', in that order. The irregular cells take the short code's next forms after the
    compressed forms', and the serials after the senses'."""
    seventh = fourth["seventh"]
    avoid = set(protected_ball)
    for a in third["acts"]:
        avoid |= B.ball(a["form"])
    pool = long_code()
    random.Random(B.SEED).shuffle(pool)
    forms = iter(f for f in pool if not B.ball(f) & avoid)
    first = _first_serial() + 1
    roots = [{"key": k, "kind": kind, "sort": sort, "definition": d, "roles": roles,
              "form": next(forms), "identifier": "lx.%06d" % (first + n)}
             for n, (k, kind, sort, d, roles) in enumerate(V.ROOTS)]
    crit = list(seventh["critical"]) + [r["identifier"] for r in roots if r["kind"] == "unit"]
    released = list(seventh["forms"])
    admissible = [f for f in check_pool if not B.ball(f) & avoid]
    assert set(released) <= set(admissible)
    modulus = largest_prime(len(admissible))
    # the rule of major version 0 kept the modulus above one more than the critical forms
    assert modulus > len(crit) + 1, (modulus, len(crit))
    added = [f for f in admissible if f not in set(released)][:modulus - len(released)]
    words = fourth["synonyms"] + fourth["politeness"] + fourth["dictions"]
    used = ({r["form"] for r in roots_before} | {w["form"] for w in words}
            | {r["form"] for r in fourth["fifth"]["roots"]}
            | {r["form"] for r in fourth["sixth"]["roots"]}
            | {r["form"] for r in seventh["roots"]}
            | {f["form"] for f in seventh["dialect forms"]})
    short = iter(f for f in root_pool if f not in used and not B.ball(f) & avoid)
    dialect_forms = [{"dialect": slug, "key": key, "form": next(short)}
                     for slug, terms in V.TERMS if slug in D.WITH_FORMS for key, _ in terms]
    ids = iter("lx.%06d" % n for n in range(first + len(V.ROOTS), first + len(V.ROOTS) + 2000))
    taken = {s["form"] for s in third["suffixes"]} | {fourth["honorific"]["form"]}
    free = iter(f for f in suffix_pool[len(L.SUFFIXES):] if f not in taken)
    suffixes = [{"key": k, "base": b, "sort": s, "definition": d, "roles": r,
                 "form": next(free), "identifier": next(ids)}
                for k, b, s, d, r in V.SUFFIXES]
    formulas = [dict(i, identifier=next(ids)) for i in VC.FORMULAS]
    idioms = [dict(i, identifier=next(ids)) for i in VC.IDIOMS]
    keys = {r["key"] for r in roots_before} | {r["key"] for r in roots}
    # a sense names its mapping, whose number follows release 0.5's nine
    number = {m[0]: len(F.MAPPINGS) + n for n, m in enumerate(VC.MAPPINGS, 1)}
    senses = []
    for root, key, definition, frame, roles, mapping, history in VC.SENSES:
        assert root in keys and key not in keys, (root, key)
        senses.append({"root": root, "key": key, "definition": definition, "frame": frame,
                       "roles": roles, "mapping": number[mapping], "history": history,
                       "identifier": next(ids)})
    irregular = [{"key": key, "root": root, "suffix": suffix, "history": history,
                  "form": next(short), "identifier": next(ids)}
                 for key, root, suffix, history in V.IRREGULAR]
    # the redesigns of the resemblance audit take the short code's forms after every
    # other, so that no form drawn before them moves
    clean = (f for f in short if f not in V.REJECTED)
    for f in dialect_forms:
        if (f["dialect"], f["key"]) in V.REDESIGNED_FORMS:
            f.update(form=next(clean), rejected=f["form"])
    # a replacement is a root of lexicon 1.0, so it takes the long code's next form
    fresh = (f for f in forms if f not in V.REJECTED)
    replacements = [{"key": key, "form": next(fresh), "identifier": next(ids)}
                    for key in V.REPLACED_ROOTS]
    return {"roots": roots, "critical": crit, "modulus": modulus, "forms": released + added,
            "admissible": len(admissible), "dialect forms": dialect_forms,
            "suffixes": suffixes, "formulas": formulas, "idioms": idioms, "senses": senses,
            "irregular": irregular, "replacements": replacements, "reserve": clean}


def _next_version(version: str) -> str:
    major, minor = version.split(".")
    return "%s.%d" % (major, int(minor) + 1)


def write_dialects(root_entry: dict, suffix_entry: dict, released: dict, release: dict,
                   replaced: dict):
    """The next release of each technical community's dialect (see
    specification/dialects.md#what-a-dialect-release-may-hold): its latest release's terms
    and forms unchanged, the new terms after them, and in a dialect that gives compressed
    forms a form for each new term. A term formed on a root lexicon 1.0 replaces is
    deprecated with its form and formed again on the new root, with a new form. Each
    release is complete in itself, formed from lexicon 1.0, and named by its digest."""
    from rowih import dialects
    by_dialect = {}
    for f in release["dialect forms"]:
        by_dialect.setdefault(f["dialect"], []).append(f)
    taken = {e["orthographic form"] for e in root_entry.values()}
    seen = {t["orthographic form"] for r in released.values() for t in r["terms"]}
    current_roots = dict(root_entry, **replaced)
    for slug, new_terms in V.TERMS:
        latest = max((r for (s, _), r in released.items() if s == slug),
                     key=lambda r: [int(x) for x in r["version"].split(".")])
        version = _next_version(latest["version"])
        terms = [dict(t) for t in latest["terms"]]
        for key, stems in new_terms:
            t = BD._term(slug, len(terms) + 1, key, stems, current_roots, suffix_entry,
                         version, "generated from its stems by tools/build_version1.py")
            assert t["orthographic form"] not in taken | seen, (slug, key)
            seen.add(t["orthographic form"])
            terms.append(t)
        reformed = _reform(slug, terms, root_entry, suffix_entry, replaced, version)
        record = {"dialect": slug, "number": D.DIALECT_NUMBERS[slug],
                  "community": latest["community"], "version": version,
                  "date": V.RELEASE_DATE, "formed from lexicon": V.RELEASE,
                  "reading": latest["reading"], "terms": terms}
        if "forms" in latest:
            forms = [dict(f) for f in latest["forms"]]
            for r in by_dialect[slug]:
                term = next(t for t in terms if t["term"] == r["key"]
                            and not t["version"]["deprecated"])
                forms.append(BD._form_entry(slug, len(forms) + 1, r, term, version))
            for old, new in reformed:
                f = next(f for f in forms if f["expansion"]["term"] == old["machine identifier"])
                entry = BD._form_entry(slug, len(forms) + 1, {"form": next(release["reserve"])},
                                       new, version)
                f["version"] = dict(f["version"], deprecated=version)
                f["replaced by"] = entry["machine identifier"]
                forms.append(entry)
            current = [t["term"] for t in terms if not t["version"]["deprecated"]]
            assert sorted(f["key"] for f in forms if not f["version"]["deprecated"]) \
                == sorted(current), slug
            record["forms"] = forms
        record["digest"] = dialects.digest(record)
        B.dump("lexicon/jargon/%s/%s.json" % (slug, version), record)


def _reform(slug, terms, root_entry, suffix_entry, replaced, version) -> list:
    """Each current term formed on a replaced root, deprecated in `version` and formed
    again on the new root, the new term appended; returns (old, new) pairs."""
    old_root = {root_entry[k]["machine identifier"]: k for k in replaced}
    root_key = {e["machine identifier"]: k for k, e in root_entry.items()}
    suffix_key = {e["machine identifier"]: k for k, e in suffix_entry.items()}
    out = []
    for t in list(terms):
        if t["version"]["deprecated"] or not any(s[0] in old_root for s in t["formed from"]):
            continue
        stems = [[root_key[s[0]]] + [suffix_key[x] for x in s[1:]] for s in t["formed from"]]
        new = BD._term(slug, len(terms) + 1, t["term"], stems, dict(root_entry, **replaced),
                       suffix_entry, version, "formed again by tools/build_version1.py "
                                              "on the root that replaces a redesigned "
                                              "one")
        t["version"] = dict(t["version"], deprecated=version)
        t["replaced by"] = new["machine identifier"]
        terms.append(new)
        out.append((t, new))
    return out


def _serial(identifier: str) -> int:
    return int(identifier.split(".")[1])


def write_release(release: dict, root_entry: dict) -> tuple:
    """The entries of lexicon 1.0 and the mappings it adds; returns the entries'
    identifiers in serial order, the mappings' identifiers, and the roots that replace
    released ones by key."""
    out = []
    categories = {"predicate": "predicate root", "nominal": "nominal root",
                  "unit": "unit of measure", "relation": "discourse relation"}
    for r in release["roots"]:
        e = B.entry(_serial(r["identifier"]), r["key"], categories[r["kind"]],
                    r["sort"], r["form"], r["definition"], r["roles"], release=V.RELEASE)
        B.dump("lexicon/roots/%s.json" % e["machine identifier"], e)
        root_entry[r["key"]] = e
        out.append(e["machine identifier"])
    for s in release["suffixes"]:
        e = B.entry(_serial(s["identifier"]), s["key"], "derivational suffix", s["sort"],
                    s["form"], s["definition"], s["roles"], {"base": s["base"]},
                    release=V.RELEASE)
        e["phonological form"] = "/-" + "".join(B.IPA[c] for c in s["form"]) + "/"
        B.dump("lexicon/formation/%s.json" % e["machine identifier"], e)
        out.append(e["machine identifier"])
    by_key = {}
    for i in release["formulas"] + release["idioms"]:
        e = BC.idiom_entry(i, root_entry, _serial(i["identifier"]), V.RELEASE)
        B.dump("lexicon/idioms/%s.json" % e["machine identifier"], e)
        by_key[i["key"]] = e
        out.append(e["machine identifier"])
    for s in release["senses"]:
        e = BF.sense_entry(s, root_entry[s["root"]], V.RELEASE)
        B.dump("lexicon/senses/%s.json" % e["machine identifier"], e)
        by_key[s["key"]] = e
        out.append(e["machine identifier"])
    out += write_irregular(release["irregular"], root_entry)
    replaced = write_replacements(release["replacements"], root_entry)
    out += [e["machine identifier"] for e in replaced.values()]
    mappings = []
    for n, mapping in enumerate(VC.MAPPINGS, len(F.MAPPINGS) + 1):
        record = BF.mapping_record(n, mapping, by_key.__getitem__, V.RELEASE)
        B.dump("lexicon/mappings/%s.json" % record["machine identifier"], record)
        mappings.append(record["machine identifier"])
    return out, mappings, replaced


def _formation_entries() -> list:
    """Every entry written so far to `lexicon/formation/`, in the order of its files."""
    out = []
    for name in sorted(os.listdir(os.path.join(B.ROOT, "lexicon", "formation"))):
        with open(os.path.join(B.ROOT, "lexicon", "formation", name), encoding="utf-8") as f:
            out.append(json.load(f))
    return out


def write_irregular(cells: list, root_entry: dict) -> list:
    """The irregular cells of lexicon 1.0 (see
    specification/lexicon.md#listed-derivations-and-compounds): each a listed derivation
    formed from its root and suffix, its sort, roles and definition what the two compose,
    its form a word of its own, and its regular form, reason and constructed history
    stated. Returns their identifiers."""
    from rowih import formation
    suffix_entry = {e["key"]: e for e in _formation_entries()
                    if e["grammatical category"] == "derivational suffix"}
    out = []
    for c in cells:
        root, suffix = root_entry[c["root"]], suffix_entry[c["suffix"]]
        meaning = formation.derive(formation.of_entry(root), suffix)
        roles = [(a["role"], a["sort"]) for a in meaning["arguments"]]
        e = B.entry(_serial(c["identifier"]), c["key"], "derivation", meaning["sort"],
                    c["form"], meaning["definition"], roles, {
                        "formed from": [root["machine identifier"],
                                        suffix["machine identifier"]],
                        "irregular": {
                            "kind": "suppletion",
                            "regular form": root["orthographic form"]
                            + suffix["orthographic form"],
                            "reason": "a constructed historical development"},
                        "constructed history": c["history"]}, release=V.RELEASE)
        e["root"] = root["machine identifier"]
        B.dump("lexicon/formation/%s.json" % e["machine identifier"], e)
        out.append(e["machine identifier"])
    return out


def write_replacements(replacements: list, root_entry: dict) -> dict:
    """The roots that replace released ones the resemblance audit redesigned: each the
    released entry's meaning under a new identifier and form, introduced in lexicon 1.0,
    and the released entry deprecated in it, replaced by the new one; the released entry
    stays interpretable. Returns the new entries by key, leaving `root_entry` to the
    released ones, from which the earlier dialect releases are formed."""
    out = {}
    for r in replacements:
        old = root_entry[r["key"]]
        new = B.entry(_serial(r["identifier"]), r["key"], old["grammatical category"],
                      old["sort"], r["form"], old["definition"],
                      [(a["role"], a["sort"]) for a in old["argument structure"]],
                      {"replaces": old["machine identifier"]}, release=V.RELEASE)
        B.dump("lexicon/roots/%s.json" % new["machine identifier"], new)
        B.dump("lexicon/roots/%s.json" % old["machine identifier"], dict(
            old, version=dict(old["version"], deprecated=V.RELEASE),
            **{"replaced by": new["machine identifier"]}))
        out[r["key"]] = new
    return out


def _deprecated(e: dict) -> bool:
    return bool(e["version"].get("deprecated"))


ROOT_CATEGORIES = ("predicate root", "nominal root", "unit of measure", "discourse relation")
INVERSE = {"kind of": "has kind", "part of": "has part", "involves": "involved in"}


def write_fields():
    """The fields that lexicon 1.0 states for each of its 500 roots: the derivations the
    rules of formation give it, its synonyms, of register and near, its antonyms and its
    related concepts, each relation read in both directions. A root of lexicon 1.0 carries
    them in its entry; a released root's entry stays as released, and
    `lexicon/fields/1.0.json` states them for it, which a reader of lexicon 1.0 or later
    reads over the entry."""
    from rowih import formation
    entries = {}
    for name in sorted(os.listdir(os.path.join(B.ROOT, "lexicon", "roots"))):
        with open(os.path.join(B.ROOT, "lexicon", "roots", name), encoding="utf-8") as f:
            e = json.load(f)
        entries[e["machine identifier"]] = e
    roots = {e["key"]: e for e in entries.values()
             if e["grammatical category"] in ROOT_CATEGORIES and "synonym of" not in e
             and not _deprecated(e)}
    assert len(roots) == 500, len(roots)
    formations = _formation_entries()
    suffixes = [e for e in formations if e["grammatical category"] == "derivational suffix"]
    # a formation the lexicon lists is read as its entry states (`inv.word-formation`),
    # and an irregular cell has its own form, its regular form beside it
    listed = {e["orthographic form"]: e["machine identifier"] for e in formations
              if e["grammatical category"] != "derivational suffix" and "irregular" not in e}
    irregular = {tuple(e["formed from"]): e for e in formations if "irregular" in e}
    ident = {k: e["machine identifier"] for k, e in roots.items()}
    fields = {i: {"derivational behaviour": [], "synonyms": [], "antonyms": [],
                  "related concepts": []} for i in ident.values()}
    for e in roots.values():
        base = formation.of_entry(e)
        for s in suffixes:
            d = formation.derive(base, s)
            if d is not None:
                form = e["orthographic form"] + s["orthographic form"]
                stated = {"suffix": s["machine identifier"], "mechanism": s["key"],
                          "form": form, "sort": d["sort"], "definition": d["definition"]}
                cell = irregular.get((e["machine identifier"], s["machine identifier"]))
                if cell is not None:
                    stated.update(form=cell["orthographic form"], listed=cell[
                        "machine identifier"], **{"regular form": form})
                elif form in listed:
                    stated["listed"] = listed[form]
                fields[e["machine identifier"]]["derivational behaviour"].append(stated)
    for e in entries.values():
        if e.get("synonym of") in fields:
            fields[e["synonym of"]]["synonyms"].append({
                "entry": e["machine identifier"], "dimension": "register",
                "registers": e["register"]})
    for a, b, difference in V.NEAR_SYNONYMS:
        for x, y in ((a, b), (b, a)):
            fields[ident[x]]["synonyms"].append({"entry": ident[y], "dimension": "near",
                                                 "difference": difference})
    for a, b in V.ANTONYMS:
        fields[ident[a]]["antonyms"].append({"entry": ident[b]})
        fields[ident[b]]["antonyms"].append({"entry": ident[a]})
    for relation, pairs in (("kind of", V.KIND_OF), ("part of", V.PART_OF),
                            ("involves", V.INVOLVES)):
        for a, b in pairs:
            fields[ident[a]]["related concepts"].append({"entry": ident[b],
                                                         "relation": relation})
            fields[ident[b]]["related concepts"].append({"entry": ident[a],
                                                         "relation": INVERSE[relation]})
    overlay = {}
    for i, f in sorted(fields.items()):
        e = entries[i]
        if e["version"]["introduced"] == V.RELEASE:
            B.dump("lexicon/roots/%s.json" % i, dict(e, **f))
        else:
            overlay[i] = f
    B.dump("lexicon/fields/%s.json" % V.RELEASE, overlay)


# Suffixes whose meaning presupposes an event or a process in their base: what an action is
# done with, a process under way, the state an action brings about, the undoing and the
# repetition of an action, where it happens, and that it can be done to something.
PRESUPPOSE_EVENT = ("instrument", "process", "result", "reversative", "repetitive", "place",
                    "potential")
# the rotation that spreads the patterns' examples over the roots
EXAMPLE_STRIDE = 37
COMPOUNDING = [
    ("compound with a predicate head taking its undergoer",
     lambda m: any(a["role"] == "undergoer" for a in m["arguments"])),
    ("compound with a predicate head taking its content",
     lambda m: not any(a["role"] == "undergoer" for a in m["arguments"])
     and any(a["role"] == "content" for a in m["arguments"])),
    ("compound with a nominal head", lambda m: True),
]


def excluded(first: str, second: str, meaning: dict) -> str | None:
    """Why the formation of the suffix `second` on a formation of `first`, whose meaning is
    `meaning`, is no productive pattern though the rules admit it; None where it is one."""
    if first == second:
        return "the same suffix twice, whose second step cancels the first or adds nothing"
    if first == "honorific":
        return ("the honorific inside a formation: the deference it adds belongs to the "
                "word as it is said, not to a stem")
    if second == "abstraction" and meaning["sort"] == "s.sort.kind":
        return "the abstraction of a kind, which is the kind itself"
    if second in PRESUPPOSE_EVENT and meaning["sort"] == "s.sort.state":
        return "a suffix that presupposes an event or a process, on a state"
    return None


def _load_dir(sub: str) -> list:
    out = []
    for name in sorted(os.listdir(os.path.join(B.ROOT, "lexicon", sub))):
        with open(os.path.join(B.ROOT, "lexicon", sub, name), encoding="utf-8") as f:
            out.append(json.load(f))
    return out


def _sort_from(mechanism: str) -> str | None:
    if mechanism in ("agent", "undergoer"):
        return "its base's %s" % {"agent": "actor", "undergoer": "undergoer"}[mechanism]
    if mechanism in ("honorific", "compound"):
        return "its base" if mechanism == "honorific" else "its head"
    return None


def write_patterns():
    """The productive patterns of word formation in lexicon 1.0 (see
    specification/lexicon.md#the-productive-patterns): each suffix, each of the three
    functions of compounding, and each formation of one suffix on another that the rules
    admit over some stem, with the combinations the rules admit that are no productive
    pattern and the reason for each. Each pattern states the stem it takes, its meaning
    over a base X and an example over a root, all computed by `rowih.formation`, which
    both implementations mirror."""
    from rowih import formation
    roots = [e for e in _load_dir("roots")
             if e["grammatical category"] in ROOT_CATEGORIES and "synonym of" not in e]
    suffixes = [e for e in _load_dir("formation")
                if e["grammatical category"] == "derivational suffix"]
    with open(os.path.join(B.ROOT, "language", "grammar.json"), encoding="utf-8") as f:
        grammar = json.load(f)
    conjunction = next(m for c in grammar["classes"] for m in c["members"]
                       if m["identifier"] == formation.CONNECTIVE + "conjunction")

    def example(n, fits):
        start = (n * EXAMPLE_STRIDE) % len(roots)
        for e in roots[start:] + roots[:start]:
            found = fits(e)
            if found is not None:
                return e, found
        return None, None

    def over_x(base_entry, steps):
        meaning = dict(formation.of_entry(base_entry), definition="X")
        for s in steps:
            meaning = formation.derive(meaning, s)
        return meaning

    def stated(n, mechanisms, takes, root, form, meaning, schema):
        record = {"identifier": "fp.%03d" % n, "mechanisms": mechanisms, "takes": takes,
                  "gives": meaning["sort"], "meaning": schema,
                  "example": {"stems": root, "form": form, "definition": meaning["definition"],
                              "roles": [a["role"] for a in meaning["arguments"]]}}
        if _sort_from(mechanisms[-1]):
            record["sort from"] = _sort_from(mechanisms[-1])
        return record

    patterns, rejected = [], []
    for s in suffixes:
        n = len(patterns) + 1
        if s["base"] == "connective":
            base = formation.of_member(conjunction["identifier"], conjunction["name"])
            meaning = formation.derive(base, s)
            schema = formation.derive(dict(base, definition="X"), s)["definition"]
            patterns.append(stated(n, [s["key"]], "connective", [conjunction["name"]],
                                   conjunction["form"] + s["orthographic form"], meaning,
                                   schema))
            continue
        e, meaning = example(n, lambda r: formation.derive(formation.of_entry(r), s))
        patterns.append(stated(n, [s["key"]], s["base"], [e["key"]],
                               e["orthographic form"] + s["orthographic form"], meaning,
                               over_x(e, [s])["definition"]))
    nominals = [e for e in roots if formation.category(formation.of_entry(e)) == "nominal"]
    for name, takes_head in COMPOUNDING:
        n = len(patterns) + 1
        modifier = nominals[(n * EXAMPLE_STRIDE) % len(nominals)]
        head_kind = "nominal" if "nominal head" in name else "predicate"

        def fits(r):
            m = formation.of_entry(r)
            if formation.category(m) != head_kind or not takes_head(m):
                return None
            return formation.compound(m, formation.of_entry(modifier))
        e, meaning = example(n, fits)
        schema = formation.compound(dict(formation.of_entry(e), definition="X"),
                                    dict(formation.of_entry(modifier), definition="Y"))
        record = stated(n, ["compound"], head_kind, [e["key"], modifier["key"]],
                        e["orthographic form"] + "i" + modifier["orthographic form"],
                        meaning, schema["definition"])
        record["function"] = name
        patterns.append(record)
    for first in suffixes:
        for second in suffixes:
            n = len(patterns) + len(rejected) + 1

            def fits(r):
                m = formation.derive(formation.of_entry(r), first)
                return formation.derive(m, second) if m is not None else None
            e, meaning = example(n, fits)
            if e is None:
                continue
            keys = [first["key"], second["key"]]
            why = excluded(first["key"], second["key"],
                           formation.derive(formation.of_entry(e), first))
            if why is not None:
                rejected.append({"mechanisms": keys, "reason": why})
                continue
            patterns.append(stated(len(patterns) + 1, keys, first["base"], [e["key"]],
                                   e["orthographic form"] + first["orthographic form"]
                                   + second["orthographic form"], meaning,
                                   over_x(e, [first, second])["definition"]))
    B.dump("lexicon/patterns/%s.json" % V.RELEASE, {
        "version": V.RELEASE,
        "rule": "every suffix, every function of compounding, and every formation of one "
                "suffix on another that the rules of formation admit over some root, except "
                "those excluded with their reasons; each is productive, applying to every "
                "stem of the kind it takes",
        "patterns": patterns, "excluded": rejected})
