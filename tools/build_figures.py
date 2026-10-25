"""The figurative part of the language build: lexicon release 0.5, with its roots, its
conventional figurative senses in `lexicon/senses/` and the mappings of
`lexicon/mappings/`. Called by `build_language.py`, whose helpers and order of building it
shares."""
import build_language as B
import convention_source as C
import figure_source as F
import language_source as L
import register_source as R


def build_release_5(third, fourth, roots, root_pool, protected_ball):
    """Release 0.5: its serials follow every earlier entry's, and its roots take the
    root pool's next forms at distance three from every protected word and every act
    word, as release 0.4 drew its own. The release adds no critical form, so the list of
    critical forms and the modulus of the move check word are release 0.4's."""
    serial = (len(L.ROOTS) + len(L.SUFFIXES) + len(L.DERIVATIONS) + len(L.ROOTS_ADDED)
              + len(C.SUFFIXES_ADDED) + len(C.ACT_WORDS) + len(C.COMPOUNDS) + len(C.IDIOMS)
              + len(R.SYNONYMS) + len(R.POLITENESS) + len(R.DICTIONS) + 1)
    ids = iter("lx.%06d" % n for n in range(serial + 1, serial + 1000))
    avoid = set(protected_ball)
    for a in third["acts"]:
        avoid |= B.ball(a["form"])
    words = fourth["synonyms"] + fourth["politeness"] + fourth["dictions"]
    used = {r["form"] for r in roots} | {w["form"] for w in words}
    pool = iter(f for f in root_pool if f not in used and not B.ball(f) & avoid)
    added = [{"key": k, "kind": kind, "sort": sort, "definition": d, "roles": roles,
              "form": next(pool), "identifier": next(ids)}
             for k, kind, sort, d, roles in F.ROOTS]
    keys = {r["key"] for r in roots} | {w["key"] for w in words}
    senses = []
    for root, key, definition, frame, roles, mapping, history in F.SENSES:
        assert root in keys and key not in keys, (root, key)
        senses.append({"root": root, "key": key, "definition": definition, "frame": frame,
                       "roles": roles, "mapping": mapping, "history": history,
                       "identifier": next(ids)})
    return {"roots": added, "senses": senses}


def mapping_id(n):
    return "mp.%06d" % n


def write_release_5(fifth, root_entry, idiom_entry):
    """The entries of release 0.5 and its mappings; returns the entries' identifiers in
    serial order and the mappings' identifiers."""
    categories = {"predicate": "predicate root", "nominal": "nominal root"}
    out = []
    by_key = {}
    for r in fifth["roots"]:
        e = B.entry(int(r["identifier"].split(".")[1]), r["key"], categories[r["kind"]],
                    r["sort"], r["form"], r["definition"], r["roles"], release=F.RELEASE)
        B.dump("lexicon/roots/%s.json" % e["machine identifier"], e)
        root_entry[r["key"]] = e
        by_key[r["key"]] = e
        out.append(e["machine identifier"])
    for s in fifth["senses"]:
        e = sense_entry(s, root_entry[s["root"]], F.RELEASE)
        B.dump("lexicon/senses/%s.json" % e["machine identifier"], e)
        by_key[s["key"]] = e
        out.append(e["machine identifier"])
    mappings = []
    for n, mapping in enumerate(F.MAPPINGS, 1):
        record = mapping_record(n, mapping, lambda key: by_key.get(key) or idiom_entry[key],
                                F.RELEASE)
        B.dump("lexicon/mappings/%s.json" % mapping_id(n), record)
        mappings.append(mapping_id(n))
    return out, mappings


def sense_entry(s, base, release):
    """The entry of a conventional figurative sense of the root `base`: the root's form
    and sort, the frame that selects the sense, and the mapping that motivates it
    (see specification/lexicon.md#figurative-senses-and-conceptual-mappings)."""
    role, filler = s["frame"]
    e = B.entry(int(s["identifier"].split(".")[1]), s["key"], "conventional sense",
                base["sort"], base["orthographic form"], s["definition"], s["roles"],
                {"sense of": base["machine identifier"],
                 "frame": {"role": "g.situations-and-contents.participation." + role,
                           "filler": filler},
                 "motivating mapping": mapping_id(s["mapping"]),
                 "kind": "conventional figurative",
                 "constructed history": s["history"], "declared loss": []},
                release=release)
    e["root"] = base["machine identifier"]
    e["related concepts"] = [base["machine identifier"]]
    return e


def mapping_record(n, mapping, entry_of, release):
    """The record of the `n`th mapping, `entry_of` giving the entry of each sense or
    idiom the mapping motivates by its key."""
    name, source, target, pairs, motivates = mapping
    return {"machine identifier": mapping_id(n), "name": name,
            "source domain": source, "target domain": target,
            "correspondences": [{"source": a, "target": b} for a, b in pairs],
            "motivates": [entry_of(key)["machine identifier"] for key in motivates],
            "version": {"introduced": release, "deprecated": None}}
