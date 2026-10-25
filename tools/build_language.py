"""Build the canonical sources of the language core from `language_source.py`.

Writes `language/phonology.json`, `language/grammar.json`, `language/semantics.json`,
`language/protocol.json`, the entries of `lexicon/roots/`, `lexicon/formation/`,
`lexicon/idioms/`, `lexicon/senses/` and `lexicon/grammar/`, the idioms' trees in
`lexicon/semantic/`, the registers of `lexicon/registers/`, the dialects of
`lexicon/jargon/`, the mappings of `lexicon/mappings/` and the release manifests of
`lexicon/releases/`, one for each release. The forms are assigned here, deterministically, under the rules
recorded in each file; `rowih.lexicon_checks` verifies them.

Run from the repository root: `python3 tools/build_language.py`.

One script longer than 500 lines: every canonical file is written in the order the forms
depend on, the core's words first and each later release's after them, so that no earlier
form moves; the idiom part is `build_conventions.py`, the register part
`build_registers.py` and the figure part `build_figures.py`.
"""
import json
import os
import random
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import convention_source as C  # noqa: E402
import figure_source as F  # noqa: E402
import language_source as L  # noqa: E402
import register_source as R  # noqa: E402
import robustness_source as RB  # noqa: E402
import semantics_source as S  # noqa: E402
import dialect_source as D  # noqa: E402
import version1_source as V  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "python"))
from rowih import versions  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = "0.1"
# The language releases, in order. 0.2 adds the expression of time; 0.3 adds discourse,
# and moves the protocol register to 0.2 by adding the envelope's first entry. 0.4 moves
# the lexicon to 0.2, whose release adds the roots of `L.ROOTS_ADDED`; the first lexicon
# release stays as it was, entries and forms alike. 0.5 moves the lexicon to 0.3, whose
# release adds the act words, idioms, suffixes and compounds of `convention_source.py`.
# 0.6 adds the register and moves the lexicon to 0.4, whose release adds the synonyms,
# suffix, politeness words and dictions of `register_source.py`; the jargon of
# `lexicon/jargon/` is formed from it. 0.7 fits each figure's relation to its type and
# moves the lexicon to 0.5, whose release adds the roots, conventional senses and mappings
# of `figure_source.py`. 0.8 takes the native digital form's code points from the
# writing-system specification's block, states in the phonology the espeak-ng code that
# renders the tap and the prosody of each register's setting, and has `build_writing.py`
# write the specification itself. 0.9 moves the protocol to 0.3 and the lexicon to 0.6,
# with the words, fixed forms and roots of `robustness_source.py`. 0.10 moves the protocol
# to 0.4 and the lexicon to 0.7, with the words, roots, features, dialect releases and
# record of releases of `dialect_source.py`. 1.0 moves the language and the lexicon to 1.0
# and the phonology to 0.3, with the long roots, the modulus of major version 1 and the
# record of releases of `version1_source.py`. Its public release names the language Rowih
# and moves the protocol to 0.5, whose media type is the name's.
LANGUAGE_VERSION = V.LANGUAGE_VERSION
PROTOCOL_VERSION = V.PROTOCOL_VERSION
LEXICON_VERSION = V.RELEASE
RELEASE_DATES = {"0.1": "2026-10-04", "0.2": "2026-10-10", "0.3": "2026-10-10",
                 "0.4": "2026-10-10", "0.5": "2026-10-11", "0.6": "2026-10-13",
                 D.RELEASE: D.RELEASE_DATE, V.RELEASE: V.RELEASE_DATE}
SEED = 39

CONSONANTS = "ptkbdgmnslrwyh"
VOWELS = "aeiou"
ALPHABET = CONSONANTS + VOWELS
IPA = {"p": "p", "t": "t", "k": "k", "b": "b", "d": "d", "g": "ɡ", "m": "m", "n": "n",
       "s": "s", "l": "l", "r": "ɾ", "w": "w", "y": "j", "h": "h",
       "a": "a", "e": "e", "i": "i", "o": "o", "u": "u"}
# espeak-ng's code for the tap is `*`; its `r` is the approximant in every voice but
# Spanish.
ESPEAK = {"y": "j", "r": "*"}
PHONOLOGY_VERSION = V.PHONOLOGY_VERSION
# Swahili's phonemes include all nineteen, and its vowels are these five and no others,
# so that its voice renders each phoneme as the IPA states it.
ESPEAK_VOICE = "sw"
# The prosody of each setting of the register transformation, as espeak-ng parameters:
# words a minute, base pitch and pitch range out of 100, and the pause between words in
# tens of milliseconds; and the pause between lines in milliseconds. Prosody is fixed by
# the register and carries nothing of its own.
PROSODY = {
    "flat": {"rate": 175, "pitch": 50, "range": 0, "word gap": 0},
    "neutral": {"rate": 175, "pitch": 50, "range": 50, "word gap": 0},
    "expressive": {"rate": 165, "pitch": 55, "range": 90, "word gap": 0},
    "measured": {"rate": 140, "pitch": 45, "range": 35, "word gap": 2},
}
LINE_PAUSE = 400

# The onset of a word fixes its length, so the lexicon is a prefix code.
ONSETS = {
    6: "ktd",            # protected words, at distance three
    5: "hr",             # move check words (h) and roots (r)
    4: "nypbgmswl",      # particles: numerals (n), number check words (y), the rest
}
# A first syllable that fixes a length its onset alone does not: the long root's.
FIRST_SYLLABLES = {V.LONG_ROOT_LENGTH: [V.LONG_ROOT_SYLLABLE]}
PROTECTED_ONSET = {"force": "k", "standing": "t", "polarity": "t", "time": "d"}
SUFFIX_FIRST_VOWELS = "aeou"
LINKER = "i"


def slug(name):
    name = name.lower().replace("'", "")
    name = re.sub(r"^(an?|the) ", "", name)
    return re.sub(r"[^a-z0-9]+", "-", name).strip("-")


def label(name):
    return slug(name).upper()


# ---------------------------------------------------------------- distance helpers

def ball(word):
    """Every string within one edit of `word` over the alphabet, the word included."""
    out = {word}
    for i in range(len(word)):
        out.add(word[:i] + word[i + 1:])
        for ch in ALPHABET:
            out.add(word[:i] + ch + word[i + 1:])
    for i in range(len(word) + 1):
        for ch in ALPHABET:
            out.add(word[:i] + ch + word[i:])
    return out


def particle_code(onset_index, onset):
    """All 25 words of an onset in the 4-symbol code at distance two.

    The medial consonant is fixed by the onset and the two vowels, so two words that
    agree in three positions agree in the fourth: c2 = (a + v1 + 2 v2) mod 14, with a
    distinct for each onset.
    """
    words = []
    for v1 in range(5):
        for v2 in range(5):
            c2 = CONSONANTS[(onset_index + v1 + 2 * v2) % 14]
            words.append(onset + VOWELS[v1] + c2 + VOWELS[v2])
    return words


def five_code(onset_index, onset):
    """The 350 words of an onset in the 5-symbol code at distance two:
    c3 = (a + v1 + 2 v2 + 3 c2) mod 14."""
    words = []
    for v1 in range(5):
        for c2 in range(14):
            for v2 in range(5):
                c3 = CONSONANTS[(onset_index + v1 + 2 * v2 + 3 * c2) % 14]
                words.append(onset + VOWELS[v1] + CONSONANTS[c2] + VOWELS[v2] + c3)
    return words


def suffix_code():
    """Suffixes VCVC whose first vowel is not the linker, at distance two."""
    words = []
    for v1 in SUFFIX_FIRST_VOWELS:
        for c1 in range(14):
            for v2 in range(5):
                c2 = CONSONANTS[(VOWELS.index(v1) + 2 * v2 + 3 * c1) % 14]
                words.append(v1 + CONSONANTS[c1] + VOWELS[v2] + c2)
    return words


def next_prime(n):
    def is_prime(k):
        return k > 1 and all(k % d for d in range(2, int(k ** 0.5) + 1))
    k = n + 1
    while not is_prime(k):
        k += 1
    return k


# ---------------------------------------------------------------- the ontology

def semantics():
    elements = [{"identifier": ident, "family": ident.split(".")[1], "name": name,
                 "placement": placement} for ident, name, placement in S.ELEMENTS]
    assert len(elements) == 101
    return {"version": VERSION, "elements": elements}


# ---------------------------------------------------------------- forms

def core_classes() -> list:
    """The grammatical classes as the core fixed them, before any later release appended
    a member or a class."""
    classes = []
    for group, name, members, status, critical, serves, applies, scope in L.CLASSES:
        gid = "g.%s.%s" % (slug(group), slug(name))
        if status == "obligatory":
            st = {"kind": "obligatory"}
        else:
            st = {"kind": "default", "default": status[1], "kind of default": status[2]}
            mem_slugs = [slug(m) for m in members]
            if slug(status[1]) in mem_slugs:
                st["default member"] = "%s.%s" % (gid, slug(status[1]))
        protected = group in L.PROTECTED_GROUPS or name in L.PROTECTED_CLASSES
        classes.append({
            "identifier": gid, "group": group, "name": name,
            "members": [{"identifier": "%s.%s" % (gid, slug(m)), "name": m,
                         "gloss": label(m)} for m in members],
            "serves": serves, "applies to": applies, "status": st,
            "critical dimension": critical, "scope": scope,
            "protected": protected, "compatibility": "must-understand",
        })
    return classes


def build():
    rng = random.Random(SEED)
    classes = core_classes()
    # Members added by later versions join their class after the core's classes.
    appended = []
    for class_name, member, version, reason in L.APPENDED_MEMBERS:
        cls = next(c for c in classes if c["name"] == class_name)
        m = {"identifier": "%s.%s" % (cls["identifier"], slug(member)), "name": member,
             "gloss": label(member), "introduced": version, "reason": reason}
        cls["members"].append(m)
        appended.append(m)
    for (group, name, members, status, critical, serves, applies, scope, version,
         reason) in C.APPENDED_CLASSES + R.APPENDED_CLASSES:
        gid = "g.%s.%s" % (slug(group), slug(name))
        st = {"kind": "default", "default": status[1], "kind of default": status[2]}
        cls = {"identifier": gid, "group": group, "name": name,
               "members": [{"identifier": "%s.%s" % (gid, slug(m)), "name": m,
                            "gloss": label(m), "introduced": version, "reason": reason}
                           for m in members],
               "serves": serves, "applies to": applies, "status": st,
               "critical dimension": critical, "scope": scope,
               "protected": False, "compatibility": "must-understand",
               "introduced": version}
        classes.append(cls)
        appended.extend(cls["members"])
    # the robustness words take forms after every earlier word's
    import build_robustness
    structural = [{"identifier": "g.structure.%s" % slug(n), "name": n, "gloss": label(n),
                   "description": d} for n, d in L.STRUCTURAL]
    eighth = build_robustness.append_words(classes, structural)
    import build_dialects
    ninth = build_dialects.append_words(classes, structural)
    for cls in classes:
        for m in cls["members"]:
            if cls["name"] == "strength":
                lo, hi, lo_open = L.STRENGTH_INTERVALS[m["name"]]
                m["interval"] = {"lower": lo, "upper": hi, "lower open": lo_open}
            elif cls["name"] == "basis":
                m["tier"] = L.BASIS_TIERS[m["name"]]
    # A gloss is stable and unique: a member whose name recurs in another class is glossed
    # with its class's name before it.
    counts = {}
    for cls in classes:
        for m in cls["members"]:
            counts[m["gloss"]] = counts.get(m["gloss"], 0) + 1
    for cls in classes:
        for m in cls["members"]:
            if counts[m["gloss"]] > 1:
                m["gloss"] = "%s.%s" % (label(cls["name"]), m["gloss"])

    # The particle code, onset by onset.
    particle_pool = {}
    for i, onset in enumerate(ONSETS[4]):
        particle_pool[onset] = particle_code(i, onset)
    numerals = next(c for c in classes if c["name"] == "numeral")
    checks = next(c for c in classes if c["name"] == "check word")
    for member, form in zip(numerals["members"], particle_pool["n"]):
        member["form"] = form
    for member, form in zip(checks["members"], particle_pool["y"]):
        member["form"] = form
    used = {"n": len(numerals["members"]), "y": len(checks["members"])}
    general = [o for o in ONSETS[4] if o not in "n"]
    queue = []
    for cls in classes:
        if cls["protected"] or cls["name"] in ("numeral", "check word"):
            continue
        queue.extend(m for m in cls["members"] if "introduced" not in m)
    queue.extend(s for s in structural if "introduced" not in s)
    # members of later versions take the next forms, after every earlier word
    queue.extend(m for m in appended if not next(
        c for c in classes if m in c["members"])["protected"])
    queue.extend(eighth[0] + eighth[1])
    queue.extend(ninth[0] + ninth[1])
    slots = []
    for onset in [o for o in general if o != "y"] + ["y"]:
        slots.extend(particle_pool[onset][used.get(onset, 0):])
    assert len(queue) <= len(slots), (len(queue), len(slots))
    for item, form in zip(queue, slots):
        item["form"] = form

    # Critical forms, in the order of the classes and their members; the modulus of the move
    # check word.
    critical = [m["identifier"] for c in classes if c["critical dimension"] for m in c["members"]]
    assert len(critical) == 151, len(critical)
    # the release's list continues past the grammar's members (language_source.py)
    for name in L.APPENDED_CRITICAL_CLASSES:
        critical += [m["identifier"] for c in classes if c["name"] == name for m in c["members"]]
    critical += ["g.structure.%s" % slug(n) for n in L.APPENDED_CRITICAL_STRUCTURAL]

    # Roots and move check words: the 5-symbol code.
    check_pool = five_code(0, "h")
    root_pool = five_code(1, "r")
    rng.shuffle(check_pool)
    rng.shuffle(root_pool)
    roots = []
    serial = 0
    for (key, kind, sort, definition, roles), form in zip(L.ROOTS, root_pool):
        serial += 1
        roots.append({"key": key, "kind": kind, "sort": sort, "definition": definition,
                      "roles": roles, "form": form})
        if kind == "unit":
            critical.append("lx.%06d" % serial)
    for name in L.APPENDED_CRITICAL_LATER:
        critical += [m["identifier"] for c in classes if c["name"] == name for m in c["members"]]
    modulus = next_prime(len(critical) + 1)
    move_check_forms = sorted(check_pool[:modulus])

    suffix_pool = suffix_code()
    rng.shuffle(suffix_pool)
    suffixes = []
    for (key, base, sort, definition), form in zip(L.SUFFIXES, suffix_pool):
        suffixes.append({"key": key, "base": base, "sort": sort, "definition": definition,
                         "form": form})

    # Every word but the protected ones, with the derivations listed.
    member_form = {m["identifier"]: m["form"] for c in classes for m in c["members"]
                   if "form" in m}
    member_by_name = {m["name"]: m for c in classes for m in c["members"]}
    root_by_key = {r["key"]: r for r in roots}
    suffix_by_key = {s["key"]: s for s in suffixes}
    derivations = []
    for key, base, suffix, definition in L.DERIVATIONS:
        if base in root_by_key:
            base_form, base_ref = root_by_key[base]["form"], ("root", base)
        else:
            base_form, base_ref = member_by_name[base]["form"], ("member",
                                                                  member_by_name[base]["identifier"])
        derivations.append({"key": key, "base": base_ref, "suffix": suffix,
                            "definition": definition,
                            "form": base_form + suffix_by_key[suffix]["form"]})

    ordinary = (list(member_form.values()) + [s["form"] for s in structural]
                + move_check_forms + [r["form"] for r in roots]
                + [d["form"] for d in derivations])
    assert len(set(ordinary)) == len(ordinary)
    ordinary_ball = set()
    for w in ordinary:
        ordinary_ball |= ball(w)

    # Protected words: six symbols, at distance three from every word.
    protected_ball = set()
    for cls in classes:
        if not cls["protected"]:
            continue
        onset = PROTECTED_ONSET.get(cls["group"]) or PROTECTED_ONSET[cls["name"]]
        for member in cls["members"]:
            for _ in range(200000):
                w = onset + "".join(rng.choice(VOWELS) if i % 2 == 0 else rng.choice(CONSONANTS)
                                    for i in range(5))
                b = ball(w)
                if b & ordinary_ball or b & protected_ball:
                    continue
                member["form"] = w
                protected_ball |= b
                break
            else:
                raise SystemExit("no protected form for %s" % member["identifier"])

    # Roots of later releases take the pool's next forms, after the protected words are
    # drawn, so that no earlier form moves; a form within distance two of a protected word
    # is passed over, since a critical word stands at distance three from every word.
    pool = iter(root_pool[len(L.ROOTS):])
    for key, kind, sort, definition, roles, release in L.ROOTS_ADDED:
        form = next(f for f in pool if not ball(f) & protected_ball)
        roots.append({"key": key, "kind": kind, "sort": sort, "definition": definition,
                      "roles": roles, "form": form, "release": release})

    import build_conventions
    third = build_conventions.build_release_3(rng, classes, critical, check_pool,
                                              move_check_forms, roots, suffix_pool,
                                              ordinary_ball, protected_ball)
    import build_registers
    fourth = build_registers.build_release_4(third, classes, roots, check_pool,
                                             move_check_forms, root_pool, suffix_pool,
                                             protected_ball)
    import build_figures
    fourth["fifth"] = build_figures.build_release_5(third, fourth, roots, root_pool,
                                                    protected_ball)
    fourth["sixth"] = build_robustness.build_release_6(fourth, roots, root_pool, check_pool,
                                                       protected_ball, third)
    fourth["seventh"] = build_dialects.build_release_7(fourth, roots, root_pool,
                                                       protected_ball, third)
    import build_version1
    fourth["version 1"] = build_version1.build_release(fourth, protected_ball, third,
                                                       check_pool, roots, root_pool,
                                                       suffix_pool)
    # every word now states the release that introduced it
    build_dialects.mark_introduced(classes, structural)
    return (classes, structural, critical, modulus, move_check_forms, roots, suffixes,
            derivations, third, fourth)




# ---------------------------------------------------------------- writing

def dump(path, data):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=False)
        f.write("\n")


def phonology():
    import writing_source
    base = writing_source.CODE_POINT_BLOCK[0]
    symbols = []
    for i, ch in enumerate(ALPHABET):
        symbols.append({"index": i, "letter": ch,
                        "kind": "consonant" if ch in CONSONANTS else "vowel",
                        "ipa": IPA[ch], "espeak": ESPEAK.get(ch, ch),
                        "code point": "U+%04X" % (base + i)})
    return {
        "version": PHONOLOGY_VERSION,
        "symbols": symbols,
        "code point range": ["U+%04X" % base, "U+%04X" % (base + len(ALPHABET) - 1)],
        "espeak voice": ESPEAK_VOICE,
        "prosody": PROSODY,
        "pause between lines": LINE_PAUSE,
        "stress": "primary stress on the first syllable of every word",
        "syllables": "CV, and CVC at the end of a word whose last symbol is a consonant",
        "word shapes": {
            "rule": "every word alternates consonant and vowel from a consonant, and its "
                    "first syllable fixes its length: the onset alone, except where the "
                    "first syllables name the syllable, so the lexicon is a prefix code",
            "onsets": {str(k): v for k, v in ONSETS.items()},
            "first syllables": {str(k): v for k, v in FIRST_SYLLABLES.items()},
            "content words": "a root, then any number of suffixes (VCVC, the first vowel "
                             "not i), with i linking each further root of a compound",
        },
    }


def protocol():
    return {
        "version": PROTOCOL_VERSION,
        "name width": 2,
        "identifier width": 6,
        "check value width": RB.CHECK_VALUE_WIDTH,
        "message fields": ["sender", "recipients", "communication time", "version",
                           "identifier", "first entry", "forwarded", "semantic check value",
                           "authentication", "integrity check value"],
        "field order": "the order of `message fields`; forwarded, the semantic check value "
                       "and authentication may be absent, and the integrity check value is "
                       "required on every message that carries an operative or a pending "
                       "move and on every protocol message",
        "first entry": "the number, in the sender's count of its own entries from one, of "
                       "the entry the message's first move adds; the k-th move adds the "
                       "entry numbered first entry + k - 1 (protocol 0.2)",
        "media type": V.MEDIA_TYPE,
        "encoding parameter": ["transliteration", "native"],
    }


def entry(serial, key, category, sort, form, definition, roles, extra=None, release=VERSION):
    e = {
        "machine identifier": "lx.%06d" % serial,
        "root": "lx.%06d" % serial,
        "phonological form": "/" + "".join(IPA[c] for c in form) + "/",
        "orthographic form": form,
        "grammatical category": category,
        "sort": sort,
        "semantic type": {"sort": sort, "arguments": [r for r, s in roles if r != "dimension"]},
        "definition": definition,
        "semantic primitives": [sort],
        "argument structure": [{"role": r, "sort": s} for r, s in roles if r != "dimension"],
        "derivational behaviour": [],
        "register": ["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7"],
        "collocations": [], "synonyms": [], "antonyms": [], "related concepts": [],
        "examples": [],
        "version": {"introduced": release, "deprecated": None},
        "key": key,
    }
    dims = [s for r, s in roles if r == "dimension"]
    if dims:
        e["dimension"] = dims[0]
    if extra:
        e.update(extra)
    return e


def main():
    (classes, structural, critical, modulus, move_check_forms,
     roots, suffixes, derivations, third, fourth) = build()
    phon = phonology()
    dump("language/phonology.json", phon)
    dump("language/semantics.json", semantics())
    proto = protocol()
    existing = os.path.join(ROOT, "language", "protocol.json")
    prior = None
    if os.path.exists(existing):
        # the maxima are fixed from the conformance corpus by tools/compute_maxima.py
        prior = json.load(open(existing, encoding="utf-8"))
        if "maxima" in prior:
            proto["maxima"] = prior["maxima"]
    import build_robustness
    proto.update(build_robustness.protocol_additions(classes, prior))
    import build_dialects
    proto.update(build_dialects.protocol_additions(classes, structural, prior))
    proto["unit check word"]["codes"] = proto.pop("unit check word codes")
    dump("language/protocol.json", proto)
    grammar = {
        "version": LANGUAGE_VERSION,
        "classes": classes,
        "structural words": structural,
        "critical forms": fourth["version 1"]["critical"],
        # a release's modulus and forms are the first of these, as many as its record
        # states
        "move check word": {"modulus": fourth["version 1"]["modulus"],
                            "forms": fourth["version 1"]["forms"],
                            "admissible forms": fourth["version 1"]["admissible"],
                            "rule": V.MODULUS_RULE},
        "productions": open(os.path.join(ROOT, "tools", "productions.txt"),
                            encoding="utf-8").read(),
    }
    dump("language/grammar.json", grammar)

    for sub in ("roots", "formation", "idioms", "senses", "semantic", "grammar", "registers",
                "releases", "jargon", "mappings", "fields", "patterns"):
        d = os.path.join(ROOT, "lexicon", sub)
        os.makedirs(d, exist_ok=True)
        for name in os.listdir(d):
            if os.path.isdir(os.path.join(d, name)):
                shutil.rmtree(os.path.join(d, name))
            else:
                os.remove(os.path.join(d, name))
    manifest = []
    serial = 0
    root_id, root_entry = {}, {}
    categories = {"predicate": "predicate root", "nominal": "nominal root",
                  "unit": "unit of measure", "relation": "discourse relation"}
    for r in roots:
        if "release" in r:
            continue
        serial += 1
        e = entry(serial, r["key"], categories[r["kind"]], r["sort"], r["form"],
                  r["definition"], r["roles"])
        root_id[r["key"]] = e["machine identifier"]
        root_entry[r["key"]] = e
        dump("lexicon/roots/%s.json" % e["machine identifier"], e)
        manifest.append(e["machine identifier"])
    suffix_id = {}
    for s in suffixes:
        serial += 1
        e = entry(serial, s["key"], "derivational suffix", s["sort"], s["form"],
                  s["definition"], [], {"base": s["base"]})
        e["phonological form"] = "/-" + "".join(IPA[c] for c in s["form"]) + "/"
        suffix_id[s["key"]] = e["machine identifier"]
        dump("lexicon/formation/%s.json" % e["machine identifier"], e)
        manifest.append(e["machine identifier"])
    member_ids = {m["identifier"] for c in classes for m in c["members"]}
    for d in derivations:
        serial += 1
        kind, base = d["base"]
        base_ref = root_id[base] if kind == "root" else base
        sort = next(s["sort"] for s in suffixes if s["key"] == d["suffix"])
        e = entry(serial, d["key"], "derivation", sort, d["form"], d["definition"], [],
                  {"formed from": [base_ref, suffix_id[d["suffix"]]]})
        e["root"] = base_ref if kind == "root" else e["machine identifier"]
        assert kind == "root" or base in member_ids
        dump("lexicon/formation/%s.json" % e["machine identifier"], e)
        manifest.append(e["machine identifier"])
    # each release lists every entry of the releases before it, and the entries of later
    # releases take serials after every entry of the first
    manifests = {VERSION: list(manifest)}
    for r in roots:
        if "release" not in r:
            continue
        serial += 1
        e = entry(serial, r["key"], categories[r["kind"]], r["sort"], r["form"],
                  r["definition"], r["roles"], release=r["release"])
        dump("lexicon/roots/%s.json" % e["machine identifier"], e)
        root_entry[r["key"]] = e
        manifest.append(e["machine identifier"])
        manifests[r["release"]] = list(manifest)
    import build_conventions
    manifests[C.RELEASE] = manifest + build_conventions.write_release_3(third, root_entry,
                                                                        classes)
    import build_registers
    manifests[R.RELEASE] = manifests[C.RELEASE] + build_registers.write_release_4(fourth,
                                                                                 root_entry)
    import build_figures
    idiom_entry = {}
    for name in sorted(os.listdir(os.path.join(ROOT, "lexicon", "idioms"))):
        e = json.load(open(os.path.join(ROOT, "lexicon", "idioms", name), encoding="utf-8"))
        idiom_entry[e["key"]] = e
    added, mappings = build_figures.write_release_5(fourth["fifth"], root_entry, idiom_entry)
    manifests[F.RELEASE] = manifests[R.RELEASE] + added
    manifests[RB.RELEASE] = manifests[F.RELEASE] + build_robustness.write_release_6(
        fourth["sixth"], root_entry)
    manifests[D.RELEASE] = manifests[RB.RELEASE] + build_dialects.write_release_7(
        fourth["seventh"], root_entry)
    import build_version1
    added, mappings_1, replaced = build_version1.write_release(fourth["version 1"],
                                                                root_entry)
    manifests[V.RELEASE] = manifests[D.RELEASE] + added
    # the fields of the grammar words, once every root and suffix is written, and the
    # productive patterns of word formation
    build_version1.write_fields()
    build_version1.write_patterns()
    for cls in classes:
        for m in cls["members"]:
            record = {
                "machine identifier": m["identifier"], "orthographic form": m["form"],
                "phonological form": "/" + "".join(IPA[c] for c in m["form"]) + "/",
                "grammatical category": cls["name"], "gloss": m["gloss"],
                "generated from": "language/grammar.json",
                "version": {"introduced": m.get("introduced", VERSION)}}
            for key in ("interval", "tier"):
                if key in m:
                    record[key] = m[key]
            dump("lexicon/grammar/%s.json" % m["identifier"], record)
    build_registers.write_registers(classes)
    suffix_entry = {}
    for name in sorted(os.listdir(os.path.join(ROOT, "lexicon", "formation"))):
        e = json.load(open(os.path.join(ROOT, "lexicon", "formation", name), encoding="utf-8"))
        if e["grammatical category"] == "derivational suffix":
            suffix_entry[e["key"]] = e
    first = build_registers.write_jargon(root_entry, suffix_entry)
    released = build_dialects.write_dialects(root_entry, suffix_entry, first,
                                             fourth["seventh"])
    build_version1.write_dialects(root_entry, suffix_entry, released, fourth["version 1"],
                                  replaced)
    build_dialects.write_releases(D.LANGUAGE_RELEASES + [V.LANGUAGE_RELEASE],
                                  dict(D.LEAST_LEXICON, **{V.LANGUAGE_VERSION:
                                                           V.LEAST_LEXICON}),
                                  dict(D.PROTOCOL_READS, **V.PROTOCOL_READS))
    assert max(manifests, key=versions.key) == LEXICON_VERSION, sorted(manifests)
    for release, entries in manifests.items():
        # each release states its own count of critical forms and its own modulus
        at = versions.key(release)
        stage = (fourth["version 1"] if at >= versions.key(V.RELEASE)
                 else fourth["seventh"] if at >= versions.key(D.RELEASE)
                 else fourth["sixth"] if at >= versions.key(RB.RELEASE)
                 else fourth if at >= versions.key(R.RELEASE)
                 else third if at >= versions.key(C.RELEASE) else None)
        record = {
            "version": release, "date": RELEASE_DATES[release], "entries": entries,
            "grammar": "language/grammar.json",
            "critical forms": len(stage["critical"]) if stage else len(critical),
            "move check modulus": stage["modulus"] if stage else modulus}
        if at >= versions.key(F.RELEASE):
            # the mappings motivating the conventional senses, a part of the lexicon from
            # release 0.5
            record["mappings"] = mappings + (mappings_1 if at >= versions.key(V.RELEASE)
                                             else [])
        dump("lexicon/releases/%s.json" % release, record)
    build_conventions.write_semantic()
    import build_writing
    with open(os.path.join(ROOT, "language", "grammar.json"), encoding="utf-8") as f:
        build_writing.write(json.load(f), phon)
    # the font is drawn from the specification just written (see
    # specification/writing-system.md#the-font), so the language loaded earlier in this
    # run, with the specification it had, is set aside first
    import build_font
    from rowih import data
    data._load_release.cache_clear()
    build_font.main()
    print("classes %d, members %d, structural %d, roots %d, suffixes %d, derivations %d, "
          "critical %d, modulus %d" % (len(classes), sum(len(c["members"]) for c in classes),
                                       len(structural), len(roots), len(suffixes),
                                       len(derivations), len(fourth["version 1"]["critical"]),
                                       fourth["version 1"]["modulus"]))


if __name__ == "__main__":
    main()
