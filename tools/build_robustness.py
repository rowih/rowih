"""The robustness part of the build: the words of language 0.9, appended after every
earlier word so that nothing earlier moves; the critical forms and the modulus of lexicon
release 0.6, with its roots; and the protocol register's fixed forms, which a later build
must reproduce unchanged.

Called from `build_language.py`, whose helpers it uses."""
import robustness_source as RB

import build_language as B
import figure_source as F
import language_source as L
import convention_source as C
import register_source as R


def append_words(classes: list, structural: list) -> tuple:
    """Add the members, classes and structural words of language 0.9 to the grammar.
    Returns the members and the structural words in the order they take forms, after
    every word of earlier versions."""
    members = []
    for class_name, member, version, reason in RB.APPENDED_MEMBERS:
        cls = next(c for c in classes if c["name"] == class_name)
        m = {"identifier": "%s.%s" % (cls["identifier"], B.slug(member)), "name": member,
             "gloss": B.label(member), "introduced": version, "reason": reason}
        cls["members"].append(m)
        members.append(m)
    for group, name, words, serves, applies, scope, reason in RB.APPENDED_CLASSES:
        gid = "g.%s.%s" % (B.slug(group), B.slug(name))
        cls = {"identifier": gid, "group": group, "name": name,
               "members": [{"identifier": "%s.%s" % (gid, B.slug(w)), "name": w,
                            "gloss": B.label(w), "introduced": RB.LANGUAGE_VERSION,
                            "reason": reason} for w in words],
               "serves": serves, "applies to": applies, "status": {"kind": "obligatory"},
               "critical dimension": None, "scope": scope,
               "protected": False, "compatibility": "must-understand",
               "introduced": RB.LANGUAGE_VERSION}
        classes.append(cls)
        members.extend(cls["members"])
    words = []
    for name, description, version in RB.APPENDED_STRUCTURAL:
        s = {"identifier": "g.structure.%s" % B.slug(name), "name": name,
             "gloss": B.label(name), "description": description, "introduced": version}
        structural.append(s)
        words.append(s)
    return members, words


def build_release_6(fourth: dict, roots: list, root_pool: list, check_pool: list,
                    protected_ball: set, third: dict) -> dict:
    """Release 0.6: its serials follow every earlier entry's, and its roots take the root
    pool's next forms at distance three from every protected word and every act word, as
    release 0.5 drew its own. The message serial is appended to the list of critical
    forms; the modulus of the move check word is the least prime greater than one more
    than the list's length, with the pool's next check words where it grows."""
    serial = (len(L.ROOTS) + len(L.SUFFIXES) + len(L.DERIVATIONS) + len(L.ROOTS_ADDED)
              + len(C.SUFFIXES_ADDED) + len(C.ACT_WORDS) + len(C.COMPOUNDS) + len(C.IDIOMS)
              + len(R.SYNONYMS) + len(R.POLITENESS) + len(R.DICTIONS) + len(F.ROOTS)
              + len(F.SENSES) + 1)
    ids = iter("lx.%06d" % n for n in range(serial + 1, serial + 1000))
    avoid = set(protected_ball)
    for a in third["acts"]:
        avoid |= B.ball(a["form"])
    words = fourth["synonyms"] + fourth["politeness"] + fourth["dictions"]
    used = ({r["form"] for r in roots} | {w["form"] for w in words}
            | {r["form"] for r in fourth["fifth"]["roots"]})
    pool = iter(f for f in root_pool if f not in used and not B.ball(f) & avoid)
    added = [{"key": k, "kind": kind, "sort": sort, "definition": d, "roles": roles,
              "form": next(pool), "identifier": next(ids)}
             for k, kind, sort, d, roles in RB.ROOTS]
    crit = list(fourth["critical"]) + ["g.structure.%s" % B.slug(n)
                                       for n in RB.APPENDED_CRITICAL_STRUCTURAL]
    modulus = B.next_prime(len(crit) + 1)
    earlier = list(fourth["forms"])
    added_checks = [f for f in check_pool if f not in earlier
                    and not B.ball(f) & protected_ball][:modulus - len(earlier)]
    return {"roots": added, "critical": crit, "modulus": modulus,
            "forms": sorted(earlier + added_checks)}


def write_release_6(sixth: dict, root_entry: dict) -> list:
    """The entries of release 0.6; returns their identifiers in serial order."""
    out = []
    for r in sixth["roots"]:
        e = B.entry(int(r["identifier"].split(".")[1]), r["key"], "predicate root",
                    r["sort"], r["form"], r["definition"], r["roles"], release=RB.RELEASE)
        B.dump("lexicon/roots/%s.json" % e["machine identifier"], e)
        root_entry[r["key"]] = e
        out.append(e["machine identifier"])
    return out


def protocol_additions(classes: list, prior: dict | None) -> dict:
    """What protocol 0.3 adds to the protocol schema: the fixed forms with their forms,
    the rule of the statement check word, the defaults of the rules of repair and the
    authentication schemes. A build that would change a fixed form stops, since those
    forms mean the same in every version."""
    fixed = {}
    for cls in classes:
        if cls["identifier"] in RB.FIXED_CLASSES:
            for m in cls["members"]:
                fixed[m["identifier"]] = m["form"]
    if prior and "fixed forms" in prior:
        # the fixed forms of these classes; a later protocol's own fixed forms are checked
        # by its part of the build (`build_dialects.protocol_additions`)
        for ident, form in prior["fixed forms"].items():
            if ident.rsplit(".", 1)[0] in RB.FIXED_CLASSES and fixed.get(ident) != form:
                raise SystemExit("the fixed form of %s would change from %s to %s"
                                 % (ident, form, fixed.get(ident)))
        if prior.get("fixed widths", RB.FIXED_WIDTHS) != RB.FIXED_WIDTHS:
            raise SystemExit("the fixed widths would change")
    return {
        "envelope": "a unit with its own count and check word, the fields from the sender to "
                    "the semantic check value inside it, and the authentication and the "
                    "integrity check value after it (protocol 0.3)",
        "protocol message": "a message whose identifier and first entry are zero, which "
                            "takes no serial on its channel and adds no entry, carries one "
                            "statement in place of moves, has one recipient and carries the "
                            "integrity check value (protocol 0.3)",
        "fixed forms": fixed,
        "fixed from": RB.PROTOCOL_VERSION,
        "fixed widths": RB.FIXED_WIDTHS,
        "unit check word": {
            "modulus": RB.UNIT_CHECK_MODULUS, "codes": RB.UNIT_CODES,
            "applies to": "the envelope and the statement of a protocol message",
            "rule": "each word between the unit's count and its check word, at position i "
                    "from 0, adds its code times (i mod 10) + 1, a member's own code "
                    "before its class's, and a word with neither adds 0; the sum modulo "
                    "11 is written as the number check word of that value"},
        "repair defaults": RB.REPAIR_DEFAULTS,
        "authentication schemes": {str(k): v for k, v in RB.AUTHENTICATION_SCHEMES.items()},
        "authentication": "the signature covers the canonical serialisation of the message "
                          "without its authentication and integrity check value fields; "
                          "the integrity check value covers the signature",
    }
