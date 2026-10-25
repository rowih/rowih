"""Write the tables of the reference specification from the canonical sources.

The reference specification, `specification/`, states the language's rules in prose, and
its tables are generated here from `language/` and `lexicon/`, so that no table can drift
from the data it states. Each table stands in a chapter between two markers:

    <!-- generated: NAME -->
    ...
    <!-- end generated -->

Every text taken from the data passes through `stated_in_full`, which refuses one that
cites a section of anything but a published standard: the specification states each rule
itself, and a reader holds nothing else to look a section up in.

The file is longer than the project's five hundred lines because it holds one short
function for each of the specification's tables, so that every path from the data to the
text can be audited in one place beside the registry that names it.

Run from the repository root: `python3 tools/build_specification.py` rewrites every
generated block; with `--check` it changes nothing, names each block that differs from what
this tool writes, and exits with status 1 if any does."""
import json
import os
import re
import sys
from typing import Callable

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPECIFICATION = os.path.join(ROOT, "specification")
OPENING = re.compile(r"<!-- generated: ([a-z0-9:-]+) -->\n")
CLOSING = "<!-- end generated -->"

# A section of a published standard, which a text may cite; no other section sign may
# stand in a text the specification takes from the data.
SECTION_SIGN = "\u00a7"
STANDARD_SECTION = re.compile(r"RFC \d+ " + SECTION_SIGN + r" [\d.]+")
FIRST_PUBLIC = "1.0"
ENTRY_DIRECTORIES = ("roots", "formation", "idioms", "senses")


class CitationLeft(ValueError):
    """A text taken from the data cites a section of something other than a published
    standard, which the specification's reader cannot look up."""


def stated_in_full(text: str) -> str:
    """`text`, which must cite no section but a published standard's."""
    if SECTION_SIGN in STANDARD_SECTION.sub("", text):
        raise CitationLeft(text)
    return text


def load(*parts: str):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return json.load(f)


def cell(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def table(header: tuple, rows: list) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(cell(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def versions() -> str:
    """The releases the specification states, from the release record and the data."""
    release = next(r for r in load("language", "releases.json")["language"]
                   if r["language"] == FIRST_PUBLIC)
    rows = [("language", release["language"], release["date"]),
            ("lexicon", release["lexicon"], ""),
            ("protocol", load("language", "protocol.json")["version"], ""),
            ("grammar", load("language", "grammar.json")["version"], ""),
            ("semantics", load("language", "semantics.json")["version"], ""),
            ("phonology", load("language", "phonology.json")["version"], ""),
            ("writing system", load("language", "writing.json")["version"], "")]
    return table(("Part", "Release", "Date"), rows)


def symbols() -> str:
    rows = [(s["index"], "`%s`" % s["letter"], s["kind"], "/%s/" % s["ipa"],
             s["code point"], "`%s`" % s["espeak"])
            for s in load("language", "phonology.json")["symbols"]]
    return table(("Index", "Letter", "Kind", "Sound", "Code point", "eSpeak"), rows)


def onsets() -> str:
    shapes = load("language", "phonology.json")["word shapes"]
    rows = [("onset `%s`" % letter, length)
            for length, letters in sorted(shapes["onsets"].items(), key=lambda i: -int(i[0]))
            for letter in letters]
    rows += [("first syllable `%s`" % syllable, length)
             for length, syllables in shapes["first syllables"].items()
             for syllable in syllables]
    return table(("A word opened by", "has this many symbols"), rows)


def prosody() -> str:
    p = load("language", "phonology.json")
    rows = [(name, v["rate"], v["pitch"], v["range"], v["word gap"])
            for name, v in p["prosody"].items()]
    return table(("Setting", "Rate (words a minute)", "Base pitch (of 100)",
                  "Pitch range (of 100)", "Gap between words (tens of milliseconds)"), rows)


def lexicon_release() -> dict:
    """The lexicon release that the language release this specification states names."""
    release = next(r for r in load("language", "releases.json")["language"]
                   if r["language"] == FIRST_PUBLIC)
    return load("lexicon", "releases", release["lexicon"] + ".json")


def entry(identifier: str) -> dict:
    for directory in ENTRY_DIRECTORIES:
        path = os.path.join(ROOT, "lexicon", directory, identifier + ".json")
        if os.path.exists(path):
            return load("lexicon", directory, identifier + ".json")
    raise KeyError(identifier)


# The kind of word each grammatical category of a lexicon entry gives; an idiom or a sense
# is not a word of its own, the one being said in other words and the other sharing its
# root's form.
WORD_KIND = {"predicate root": "root", "nominal root": "root", "unit of measure": "root",
             "discourse relation": "root", "diction": "diction or politeness word",
             "politeness word": "diction or politeness word", "act word": "act word",
             "derivational suffix": "suffix"}
WORD_KINDS = ("member of a protected class", "act word", "member of another class",
              "structural word", "move check word", "root", "diction or politeness word",
              "suffix")


def opening(form: str, first_syllables: set) -> str:
    return form[:2] if form[:2] in first_syllables else form[0]


def word_kinds() -> str:
    """Each kind of word with its lengths, the openings that fix them and its count."""
    g = load("language", "grammar.json")
    shapes = load("language", "phonology.json")["word shapes"]
    syllables = {s for group in shapes["first syllables"].values() for s in group}
    found: dict = {}

    def add(kind: str, form: str) -> None:
        openings, count = found.get((kind, len(form)), (set(), 0))
        found[(kind, len(form))] = (openings | {opening(form, syllables)}, count + 1)

    for c in g["classes"]:
        for m in c["members"]:
            add("member of a protected class" if c.get("protected")
                else "member of another class", m["form"])
    for s in g["structural words"]:
        add("structural word", s["form"])
    for form in g["move check word"]["forms"]:
        add("move check word", form)
    for identifier in lexicon_release()["entries"]:
        e = entry(identifier)
        kind = WORD_KIND.get(e["grammatical category"])
        if kind:
            add(kind, e["orthographic form"].lstrip("-"))
    rows = [(kind, length, " ".join("`%s`" % o for o in sorted(openings)), count)
            for (kind, length), (openings, count)
            in sorted(found.items(), key=lambda i: (WORD_KINDS.index(i[0][0]), i[0][1]))]
    return table(("Kind of word", "Symbols", "Opened by", "Words"), rows)


def entries() -> list:
    return [entry(identifier) for identifier in lexicon_release()["entries"]]


def glosses() -> dict:
    """Every closed-class member's gloss, by its identifier."""
    return {m["identifier"]: m["gloss"]
            for c in load("language", "grammar.json")["classes"] for m in c["members"]}


ROOT_CATEGORIES = ("predicate root", "nominal root", "unit of measure", "discourse relation")


def lexicon_totals() -> str:
    """What the lexicon release holds, by the grammatical category of its entries, with
    the roots in force counted apart."""
    release = lexicon_release()
    counts: dict = {}
    for e in entries():
        counts[e["grammatical category"]] = counts.get(e["grammatical category"], 0) + 1
    in_force = sum(1 for e in entries() if e["grammatical category"] in ROOT_CATEGORIES
                   and not e["version"].get("deprecated") and "synonym of" not in e)
    patterns = load("lexicon", "patterns", release["version"] + ".json")
    rows = [(category, n) for category, n in sorted(counts.items())]
    rows += [("**entries in all**", len(release["entries"])),
             ("roots in force, register synonyms and deprecated roots aside", in_force),
             ("conceptual mappings", len(release["mappings"])),
             ("productive patterns of formation", len(patterns["patterns"]))]
    return table(("Entries", "Count"), rows)


def suffixes() -> str:
    rows = [("`%s`" % e["orthographic form"].lstrip("-"), e["key"], e["base"],
             "`%s`" % e["sort"], e["definition"])
            for e in entries() if e["grammatical category"] == "derivational suffix"]
    return table(("Suffix", "Name", "Takes a base that is", "Gives the sort", "Meaning"), rows)


def act_words() -> str:
    gloss = glosses()
    rows = [("`%s`" % e["orthographic form"], e["key"],
             " ".join(gloss[m] for m in e["expansion"]))
            for e in entries() if e["grammatical category"] == "act word"]
    return table(("Act word", "Act", "Stands for"), rows)


def social_words() -> str:
    rows = [("`%s`" % e["orthographic form"], e["key"], e["grammatical category"],
             " ".join(e["register"]))
            for e in entries() if e["grammatical category"] in ("politeness word", "diction")]
    return table(("Word", "Name", "Kind", "Registers"), rows)


def senses() -> str:
    by_id = {e["machine identifier"]: e for e in entries()}
    mappings = {i: load("lexicon", "mappings", i + ".json")["name"]
                for i in lexicon_release()["mappings"]}
    rows = [(e["key"], "%s `%s`" % (by_id[e["sense of"]]["key"], e["orthographic form"]),
             "`%s` filled by a %s" % (e["frame"]["role"].rsplit(".", 1)[1], e["frame"]["filler"]),
             mappings[e["motivating mapping"]], e["definition"])
            for e in entries() if e["grammatical category"] == "conventional sense"]
    return table(("Sense", "Of the root", "Selected where", "Motivated by", "Meaning"), rows)


def registers() -> str:
    rows = []
    for code in range(len(os.listdir(os.path.join(ROOT, "lexicon", "registers")))):
        r = load("lexicon", "registers", "r%d.json" % code)
        rows.append((r["code"], r["name"], r["use"], ", ".join(r["modes admitted"]),
                     ", ".join(r["devices admitted"]),
                     "yes" if r["precision-bound by default"] else "no",
                     "yes" if r["formulas admitted"] else "no", r["order"],
                     r["politeness word"] or "none"))
    return table(("Register", "Name", "Use", "Modes", "Devices", "Precision-bound",
                  "Formulas", "Order", "Politeness word"), rows)


def excluded_patterns() -> str:
    release = lexicon_release()
    counts: dict = {}
    for x in load("lexicon", "patterns", release["version"] + ".json")["excluded"]:
        counts[x["reason"]] = counts.get(x["reason"], 0) + 1
    return table(("Combinations excluded because", "Count"), sorted(counts.items()))


def qualified_glosses() -> str:
    """The members whose gloss recurs in another class, which the notation writes with
    their class's label before a full stop."""
    rows = [("`%s`" % m["gloss"], "`%s`" % m["identifier"])
            for c in load("language", "grammar.json")["classes"] for m in c["members"]
            if "." in m["gloss"]]
    return table(("Written", "Member"), rows)


def members_of(identifier: str) -> list:
    return next(c["members"] for c in load("language", "grammar.json")["classes"]
                if c["identifier"] == identifier)


def basis_tiers() -> str:
    rows = [(m["tier"], "`%s` %s" % (m["form"], m["gloss"]))
            for m in sorted(members_of("g.standing.basis"), key=lambda m: m["tier"])]
    return table(("Tier", "Basis"), rows)


def strength_intervals() -> str:
    rows = []
    for m in members_of("g.standing.strength"):
        i = m["interval"]
        rows.append(("`%s` %s" % (m["form"], m["gloss"]),
                     "%s%s, %s]" % ("(" if i["lower open"] else "[", i["lower"], i["upper"])))
    return table(("Strength", "Interval of probability"), rows)


def ontology() -> str:
    """The elements of the semantic ontology, by family and by where each is placed."""
    found: dict = {}
    for e in load("language", "semantics.json")["elements"]:
        found.setdefault((e["family"], e["placement"]), []).append(e["name"])
    rows = [(family, placement, len(names), ", ".join(names))
            for (family, placement), names in found.items()]
    return table(("Family", "Placed in", "Elements", "Names"), rows)


def repair_defaults() -> str:
    d = load("language", "protocol.json")["repair defaults"]
    rows = [("the quiet interval, after which an addressee acknowledges", "%s seconds"
             % d["quiet interval"]),
            ("the interval before a message or a request is sent again", "%s seconds"
             % d["interval before sending again"]),
            ("the times a message or a request is sent again", d["times sent again"])]
    return table(("Default", "Value"), rows)


def authentication_schemes() -> str:
    schemes = load("language", "protocol.json")["authentication schemes"]
    rows = [(number, s["name"], s["specification"], s["signature bytes"], s["public key bytes"])
            for number, s in schemes.items()]
    return table(("Scheme", "Name", "Specification", "Signature bytes", "Public key bytes"),
                 rows)


def reads() -> str:
    """What the language release this specification states reads."""
    releases = load("language", "releases.json")
    language = next(r for r in releases["language"] if r["language"] == FIRST_PUBLIC)
    protocol = next(r for r in releases["protocol"] if r["protocol"] == language["protocol"])
    rows = [("language %s" % language["language"], ", ".join(language["reads"]),
             language["least lexicon"]),
            ("protocol %s" % protocol["protocol"], ", ".join(protocol["reads"]), "")]
    return table(("Release", "Reads the messages of", "Least lexicon"), rows)


def polyline(points: list) -> str:
    return " ".join("(%s,%s)" % (x, y) for x, y in points)


def components() -> str:
    rows = [("`%s`" % c["symbol"], c["code point"],
             " ; ".join(polyline(s) for s in c["pen strokes"]))
            for c in load("language", "writing.json")["components"]]
    return table(("Symbol", "Code point", "Pen strokes, each a polyline of lattice points"),
                 rows)


def unit_marks() -> str:
    forms = {s["identifier"]: s["form"]
             for s in load("language", "grammar.json")["structural words"]}
    units = load("language", "writing.json")["units"]
    rows = [(name, "`%s` … `%s`" % (forms[u["opens"]], forms[u["closes"]]),
             len(u["mark"]) - 1, polyline(u["mark"])) for name, u in units.items()]
    return table(("Unit", "Opened and closed by", "Sides of its mark", "Mark"), rows)


def writing_metrics() -> str:
    w = load("language", "writing.json")
    rows = [(name, value) for name, value in w["metrics"].items()]
    rows += [(name, w[name]) for name in ("pixels per unit", "serif", "double")]
    return table(("Metric", "Value"), rows)


def version_key(version: str) -> tuple:
    major, minor = version.split(".")
    return int(major), int(minor)


def dialect_releases() -> dict:
    """Every dialect's releases, by its name, oldest first."""
    found: dict = {}
    jargon = os.path.join(ROOT, "lexicon", "jargon")
    for name in sorted(os.listdir(jargon)):
        versions = sorted((f[:-len(".json")] for f in os.listdir(os.path.join(jargon, name))),
                          key=version_key)
        found[name] = [load("lexicon", "jargon", name, v + ".json") for v in versions]
    return found


def in_force(records: list) -> int:
    return sum(1 for r in records if not r["version"].get("deprecated"))


def dialects() -> str:
    rows = []
    for name, releases in dialect_releases().items():
        newest = releases[-1]
        rows.append((newest["number"], name, ", ".join(r["version"] for r in releases),
                     newest["digest"], newest["formed from lexicon"],
                     in_force(newest["terms"]), in_force(newest.get("forms", []))))
    rows.sort(key=lambda r: r[0])
    return table(("Number", "Dialect", "Releases", "Digest of the newest",
                  "Formed from lexicon", "Terms in force", "Compressed forms in force"), rows)


def diagnostics() -> str:
    """The registry of diagnostics, read from the canonical implementation."""
    sys.path.insert(0, os.path.join(ROOT, "python"))
    from rowih.diagnostics import CODES
    return table(("Code", "Condition"),
                 [("`%s`" % code, stated_in_full(text)) for code, text in CODES.items()])


def mutants() -> str:
    """Each planted defect, the invariant or failure it plants, and whether the tests
    caught it, from the report of the last run."""
    results = load("corpus", "reports", "mutants.json")["results"]
    rows = [("`%s`" % r["invariant"], name, stated_in_full(r["description"]),
             "yes" if r["caught"] else "no")
            for name, r in sorted(results.items(), key=lambda i: (i[1]["invariant"], i[0]))]
    return table(("Plants a breach of", "Defect", "What the defect does", "Caught"), rows)


SUITE = (("conformance", "conformance"), ("attitudes", "attitudes"),
         ("adversarial", "adversarial"), ("negative", "negative"), ("domains", "domains"))


def suite() -> str:
    rows = []
    for directory, source in SUITE:
        items = load("corpus", "source", source + ".json")["items"]
        texts = [f for f in os.listdir(os.path.join(ROOT, "corpus", directory))
                 if f.endswith(".txt")]
        rows.append(("`corpus/%s/`" % directory, format(len(items), ","),
                     format(len(texts), ",")))
    rows.append(("`corpus/source/ambiguity.json`",
                 len(load("corpus", "source", "ambiguity.json")["items"]), ""))
    return table(("Set", "Items", "Message files"), rows)


def median(values: list) -> float:
    s, n = sorted(values), len(values)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def tokens() -> str:
    report = load("corpus", "reports", "tokens.json")
    panel = report["tokenizers"].values()
    rows = []
    for label, key in (("tokens a word, transliteration", "tokens per word"),
                       ("tokens a move, transliteration, its envelope's share included",
                        "tokens per move"),
                       ("tokens of the native digital form over the transliteration's",
                        "native over transliteration"),
                       ("tokens of the transliteration over the English explanation's",
                        "transliteration over English")):
        values = [t[key] for t in panel]
        rows.append((label, "%.2f" % median(values),
                     "%.2f to %.2f" % (min(values), max(values))))
    head = "Measured over %d messages, %s words and %s moves, by %d tokenizers.\n\n" % (
        report["messages"], format(report["units"]["words"], ","),
        format(report["units"]["moves"], ","), len(report["tokenizers"]))
    return head + table(("Quantity", "Median", "Range"), rows)


def register_prosody() -> str:
    rows = []
    for code in range(len(os.listdir(os.path.join(ROOT, "lexicon", "registers")))):
        r = load("lexicon", "registers", "r%d.json" % code)
        rows.append((r["code"], r["name"], r["settings"]["prosody"]))
    return table(("Register", "Name", "Prosody"), rows)


def structural_words() -> str:
    rows = [("`%s`" % s["form"], s["gloss"], stated_in_full(s["description"]),
             s["introduced"]) for s in load("language", "grammar.json")["structural words"]]
    return table(("Form", "Gloss", "What it does", "Since"), rows)


def status(cls: dict) -> str:
    s = cls["status"]
    if s["kind"] == "obligatory":
        return "obligatory"
    return "default: %s (%s)" % (s["default"], s["kind of default"])


def dimension(cls: dict) -> str:
    text = cls.get("critical dimension") or ""
    if cls.get("protected"):
        text = (text + "; protected").lstrip("; ")
    return text


def members(cls: dict) -> str:
    return " · ".join("`%s` %s" % (m["form"], m["gloss"]) for m in cls["members"])


def classes_of(group: str) -> Callable[[], str]:
    """The table of one group's classes: what each applies to, its status, the critical
    dimension it carries and its members with their forms."""
    def block() -> str:
        rows = [("%s<br>`%s`" % (c["name"], c["identifier"]),
                 stated_in_full(c["applies to"]), status(c), dimension(c), members(c))
                for c in load("language", "grammar.json")["classes"] if c["group"] == group]
        return table(("Class", "Applies to", "Status", "Critical dimension", "Members"), rows)
    return block


def productions() -> str:
    """The productions without the opening paragraph, which recounts the releases that
    added each production."""
    body = load("language", "grammar.json")["productions"].split("\n\n", 1)[1]
    return "```\n" + stated_in_full(body).rstrip() + "\n```"


def fixed_forms() -> str:
    rows = [("`%s`" % form, "`%s`" % identifier)
            for identifier, form in load("language", "protocol.json")["fixed forms"].items()]
    return table(("Form", "Identifier"), rows)


def unit_check_codes() -> str:
    rule = load("language", "protocol.json")["unit check word"]
    rows = [("`%s`" % identifier, code) for identifier, code in rule["codes"].items()]
    return table(("Word or class", "Code"), rows)


def move_check_forms() -> str:
    """The forms of the move check word in order of value, ten to a line."""
    forms = load("language", "grammar.json")["move check word"]["forms"]
    width = 10
    lines = ["%3d  %s" % (i, " ".join(forms[i:i + width])) for i in range(0, len(forms), width)]
    return "```\n" + "\n".join(lines) + "\n```"


def features() -> str:
    rows = [(f["number"], f["name"], f["flag"], f["introduced"], f["reason"])
            for f in load("language", "protocol.json")["features"]]
    return table(("Number", "Feature", "Flag", "Since protocol", "Why"), rows)


def maxima() -> str:
    m = load("language", "protocol.json")["maxima"]
    return table(("Limit", "Maximum"), [(k, v) for k, v in m.items() if k != "rule"])


GROUPS = ("force", "standing", "attitudes and aims", "situations and contents", "reference",
          "time", "numbers", "ambiguity and figures", "message", "protocol")
BLOCKS: dict = {
    "versions": versions,
    "symbols": symbols,
    "onsets": onsets,
    "prosody": prosody,
    "word-kinds": word_kinds,
    "register-prosody": register_prosody,
    "lexicon-totals": lexicon_totals,
    "suffixes": suffixes,
    "act-words": act_words,
    "social-words": social_words,
    "senses": senses,
    "registers": registers,
    "excluded-patterns": excluded_patterns,
    "qualified-glosses": qualified_glosses,
    "basis-tiers": basis_tiers,
    "strength-intervals": strength_intervals,
    "ontology": ontology,
    "repair-defaults": repair_defaults,
    "authentication-schemes": authentication_schemes,
    "reads": reads,
    "components": components,
    "unit-marks": unit_marks,
    "writing-metrics": writing_metrics,
    "dialects": dialects,
    "diagnostics": diagnostics,
    "mutants": mutants,
    "suite": suite,
    "tokens": tokens,
    "structural-words": structural_words,
    "productions": productions,
    "fixed-forms": fixed_forms,
    "unit-check-codes": unit_check_codes,
    "move-check-forms": move_check_forms,
    "features": features,
    "maxima": maxima,
}
BLOCKS.update({"classes:" + g.replace(" ", "-"): classes_of(g) for g in GROUPS})


class UnknownBlock(KeyError):
    """A chapter names a generated block this tool does not write."""


def regenerate(text: str, path: str) -> str:
    """`text` with each generated block written afresh."""
    out, at = [], 0
    for opening in OPENING.finditer(text):
        name = opening.group(1)
        if name not in BLOCKS:
            raise UnknownBlock("%s: %s" % (path, name))
        end = text.index(CLOSING, opening.end())
        out += [text[at:opening.end()], BLOCKS[name](), "\n"]
        at = end
    return "".join(out) + text[at:]


def chapters() -> list:
    return sorted(os.path.join(SPECIFICATION, n) for n in os.listdir(SPECIFICATION)
                  if n.endswith(".md"))


def main() -> int:
    check = "--check" in sys.argv[1:]
    differing = []
    for path in chapters():
        with open(path, encoding="utf-8") as f:
            text = f.read()
        fresh = regenerate(text, path)
        if fresh == text:
            continue
        differing.append(os.path.relpath(path, ROOT))
        if not check:
            with open(path, "w", encoding="utf-8") as f:
                f.write(fresh)
    verb = "differs" if check else "rewritten"
    for path in differing:
        print("%s: %s" % (path, verb))
    return 1 if check and differing else 0


if __name__ == "__main__":
    sys.exit(main())
