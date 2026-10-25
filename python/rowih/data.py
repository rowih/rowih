"""The canonical sources, loaded once: the grammar, the phonology, the protocol schema,
the semantic schema and a release of the lexicon, with the indexes every stage uses."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache

from . import versions

_HERE = os.path.dirname(os.path.abspath(__file__))


def _data_root() -> str:
    """The directory holding `language/` and `lexicon/`: the repository root when the
    package runs from a checkout, and otherwise the `rowih_data` directory a wheel
    installs beside the package."""
    repo = os.path.dirname(os.path.dirname(_HERE))
    if os.path.isfile(os.path.join(repo, "language", "grammar.json")):
        return repo
    return os.path.join(os.path.dirname(_HERE), "rowih_data")


def _load(*parts: str):
    with open(os.path.join(_data_root(), *parts), encoding="utf-8") as f:
        return json.load(f)


@dataclass(frozen=True)
class Item:
    """A word of the lexicon or a bound morpheme, with what it spells."""
    kind: str            # member, structural, move-check, root, derivation, suffix, act,
    #                      idiom, sense, dialect
    identifier: str
    form: str
    gloss: str
    class_id: str = ""   # the closed class of a member
    name: str = ""
    protected: bool = False
    critical_code: int = 0
    sort: str = ""
    category: str = ""


@dataclass
class Language:
    version: str                                    # the lexicon release
    grammar: dict
    phonology: dict
    protocol: dict
    semantics: dict
    release: dict
    entries: dict = field(default_factory=dict)     # lx identifier -> entry
    items: dict = field(default_factory=dict)       # identifier -> Item
    by_form: dict = field(default_factory=dict)     # word form -> Item
    suffixes: dict = field(default_factory=dict)    # suffix form -> Item
    classes: dict = field(default_factory=dict)     # class identifier -> class record
    member_class: dict = field(default_factory=dict)
    move_check_forms: list = field(default_factory=list)
    move_check_value: dict = field(default_factory=dict)
    modulus: int = 0
    letters: str = ""
    consonants: str = ""
    vowels: str = ""
    code_points: dict = field(default_factory=dict)  # letter -> code point
    letters_of: dict = field(default_factory=dict)   # code point -> letter
    onset_length: dict = field(default_factory=dict)
    # a first syllable that fixes a length its onset alone does not, the long root's
    # (specification/sounds-and-words.md#how-a-words-opening-fixes-its-length)
    syllable_length: dict = field(default_factory=dict)
    # the idioms larger than a word
    # (specification/lexicon.md#conventional-expressions-and-idioms): each grammatical
    # one, read by the mark from its literal structure, and each extragrammatical one by
    # the identifiers of its words, in the order of the release
    idioms: list = field(default_factory=list)
    extragrammatical: dict = field(default_factory=dict)  # word identifiers -> entry id
    # the eight registers' records (specification/lexicon.md#registers), by code, and the
    # code of each member of the register class
    registers: dict = field(default_factory=dict)
    register_code: dict = field(default_factory=dict)
    # the conventional figurative senses of each root, in the order of the release, and
    # the mappings that motivate them
    # (specification/lexicon.md#figurative-senses-and-conceptual-mappings); a sense shares
    # its root's form, so it has no place in `by_form`
    senses: dict = field(default_factory=dict)      # root identifier -> [sense identifiers]
    mappings: dict = field(default_factory=dict)    # mapping identifier -> record
    # the writing-system specification (specification/writing-system.md#the-components):
    # the components, the signs drawn whole and the metrics of the forms
    writing: dict = field(default_factory=dict)
    # the language release a message is read under, every word introduced after it being
    # unknown; the dialects it names, each (number, version); the compressed forms of
    # those dialects by identifier; and the terms and entries the named releases have
    # deprecated, by form (specification/dialects.md#what-a-dialect-release-may-hold)
    language: str = ""
    dialects: tuple = ()
    dialect_forms: dict = field(default_factory=dict)
    deprecated: dict = field(default_factory=dict)

    def member(self, identifier: str) -> Item:
        return self.items[identifier]

    def form_of(self, identifier: str) -> str:
        return self.items[identifier].form

    def in_class(self, form: str, class_id: str) -> bool:
        item = self.by_form.get(form)
        return item is not None and item.class_id == class_id

    def length_at(self, form: str, i: int = 0) -> int | None:
        """The length of the morpheme that opens at `i`: its first syllable's where the
        phonology names the syllable, its onset's otherwise, None where neither fixes one
        (`language/phonology.json`, word shapes)."""
        n = self.syllable_length.get(form[i:i + 2])
        return n if n is not None else self.onset_length.get(form[i:i + 1])


def short(identifier: str) -> str:
    return identifier.rsplit(".", 1)[-1]


CURRENT = "1.0"
ENTRY_DIRECTORIES = ("roots", "formation", "idioms", "senses")
REGISTER_CLASS = "g.ambiguity-and-figures.register"
DEFAULT_REGISTER = "R2"


def load(version: str | None = None, language: str | None = None,
         dialects: tuple = ()) -> Language:
    """The release `version` of the lexicon, read under language release `language` (the
    newest where it is None) with the dialects `dialects` names, each (number, version),
    loaded once: every caller shares one copy."""
    return _load_release(version or CURRENT, language, tuple(sorted(dialects)))


@lru_cache(maxsize=32)
def _load_release(version: str, language: str | None = None,
                  dialects: tuple = ()) -> Language:
    grammar = _load("language", "grammar.json")
    lang = Language(version=version, grammar=grammar,
                    phonology=_load("language", "phonology.json"),
                    protocol=_load("language", "protocol.json"),
                    semantics=_load("language", "semantics.json"),
                    release=_load("lexicon", "releases", "%s.json" % version),
                    writing=_load("language", "writing.json"))
    lang.language = language or grammar["version"]
    lang.dialects = dialects
    within = versions.key(lang.language)
    # a release's codes are the first of the list, as many as it states
    # (specification/protocol.md#the-move-check-word): the list only grows, each form
    # appended at its end
    count = lang.release.get("critical forms", len(grammar["critical forms"]))
    critical = {ident: i + 1 for i, ident in enumerate(grammar["critical forms"][:count])}
    for cls in grammar["classes"]:
        lang.classes[cls["identifier"]] = cls
        for m in cls["members"]:
            item = Item("member", m["identifier"], m["form"], m["gloss"], cls["identifier"],
                        m["name"], cls["protected"], critical.get(m["identifier"], 0))
            lang.items[item.identifier] = item
            lang.member_class[item.identifier] = cls["identifier"]
            if versions.key(m.get("introduced", "0.1")) <= within:
                lang.by_form[item.form] = item
    for s in grammar["structural words"]:
        item = Item("structural", s["identifier"], s["form"], s["gloss"], name=s["name"],
                    critical_code=critical.get(s["identifier"], 0))
        lang.items[item.identifier] = item
        if versions.key(s.get("introduced", "0.1")) <= within:
            lang.by_form[item.form] = item
    # a release's modulus is its record's, and its forms the first of the list, as many as
    # the modulus: the list only grows, each form appended at its end
    # (specification/protocol.md#numbers-and-their-check-words)
    mc = grammar["move check word"]
    lang.modulus = lang.release.get("move check modulus", mc["modulus"])
    lang.move_check_forms = list(mc["forms"][:lang.modulus])
    for value, form in enumerate(lang.move_check_forms):
        item = Item("move-check", "g.move-check.%d" % value, form, "CHK%d" % value)
        lang.items[item.identifier] = item
        lang.by_form[form] = item
        lang.move_check_value[form] = value
    stated = _stated_through("fields", version)
    usage = _stated_through("usage", version)
    for ident in lang.release["entries"]:
        sub = next(d for d in ENTRY_DIRECTORIES if os.path.exists(
            os.path.join(_data_root(), "lexicon", d, ident + ".json")))
        e = _load("lexicon", sub, ident + ".json")
        if ident in stated:
            e = dict(e, **stated[ident])
        if ident in usage:
            e = dict(e, **usage[ident])
        lang.entries[ident] = e
        cat = e["grammatical category"]
        kind = {"derivational suffix": "suffix", "derivation": "derivation",
                "compound": "derivation", "act word": "act", "idiom": "idiom",
                "conventional sense": "sense"}.get(cat, "root")
        gloss = e["key"].upper().replace(" ", "-")
        item = Item(kind, ident, e["orthographic form"],
                    "ACT-" + gloss if kind == "act" else gloss, name=e["key"],
                    protected=kind == "act", sort=e["sort"], category=cat,
                    critical_code=critical.get(ident, 0))
        lang.items[ident] = item
        if e["version"].get("deprecated") and versions.key(e["version"]["deprecated"]) <= \
                versions.key(version):
            lang.deprecated[e["orthographic form"]] = {
                "identifier": ident, "deprecated": e["version"]["deprecated"],
                "replaced by": e.get("replaced by")}
        if kind == "suffix":
            lang.suffixes[item.form] = item
        elif kind == "idiom":
            lang.idioms.append(ident)
        elif kind == "sense":
            lang.senses.setdefault(e["sense of"], []).append(ident)
        else:
            lang.by_form[item.form] = item
    for ident in lang.idioms:
        literal = lang.entries[ident]["literal structure"]
        if isinstance(literal, list):
            words = tuple(next(i for i, e in lang.entries.items() if e["key"] == k
                               and lang.items[i].kind == "root") for k in literal)
            lang.extragrammatical[words] = ident
    for ident in lang.release.get("mappings", []):
        lang.mappings[ident] = _load("lexicon", "mappings", ident + ".json")
    for code in ("R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7"):
        record = _load("lexicon", "registers", "%s.json" % code.lower())
        lang.registers[code] = record
        if "member" in record:
            lang.register_code[record["member"]] = code
    phon = lang.phonology
    lang.letters = "".join(s["letter"] for s in phon["symbols"])
    lang.consonants = "".join(s["letter"] for s in phon["symbols"] if s["kind"] == "consonant")
    lang.vowels = "".join(s["letter"] for s in phon["symbols"] if s["kind"] == "vowel")
    for s in phon["symbols"]:
        cp = chr(int(s["code point"][2:], 16))
        lang.code_points[s["letter"]] = cp
        lang.letters_of[cp] = s["letter"]
    for length, onsets in phon["word shapes"]["onsets"].items():
        for o in onsets:
            lang.onset_length[o] = int(length)
    for length, syllables in phon["word shapes"].get("first syllables", {}).items():
        for s in syllables:
            lang.syllable_length[s] = int(length)
    for number, dialect_version in dialects:
        _add_dialect(lang, dialect_releases()[(number, dialect_version)])
    return lang


@lru_cache(maxsize=32)
def _stated_through(directory: str, version: str) -> dict:
    """The fields each lexicon release up to `version` states in `lexicon/<directory>/`
    for entries written before them, merged in release order: in `fields`, those lexicon
    1.0 states for the released entries, and in `usage`, the collocations and examples
    measured from the corpus for every entry. An entry's file stays as released, and a
    reader of a later release reads the entry with these over it."""
    root = os.path.join(_data_root(), "lexicon", directory)
    out = {}
    if not os.path.isdir(root):
        return out
    for name in versions.ordered(n[:-5] for n in os.listdir(root) if n.endswith(".json")):
        if versions.key(name) <= versions.key(version):
            for ident, fields in _load("lexicon", directory, name + ".json").items():
                out.setdefault(ident, {}).update(fields)
    return out


def _add_dialect(lang: Language, release: dict):
    """The compressed forms of a named dialect, each a word whose meaning is the term it
    compresses, and the terms and forms the release deprecates
    (specification/dialects.md#compressed-forms)."""
    for f in release.get("forms", []):
        item = Item("dialect", f["machine identifier"], f["orthographic form"],
                    f["key"].upper().replace(" ", "-"), name=f["key"], sort=f["sort"],
                    category="dialect form")
        lang.items[item.identifier] = item
        lang.by_form[item.form] = item
        record = dict(f, dialect=release["number"], **{"dialect name": release["dialect"],
                                                       "release": release["version"]})
        record.update(_stated_through("usage", lang.version).get(item.identifier, {}))
        lang.dialect_forms[item.identifier] = record
        # an entry of the named dialect, read where the lexicon's entries are read
        lang.entries[item.identifier] = record
        if f["version"]["deprecated"]:
            lang.deprecated[item.form] = {"identifier": item.identifier,
                                          "deprecated": f["version"]["deprecated"],
                                          "replaced by": f.get("replaced by")}
    for t in release["terms"]:
        if t["version"]["deprecated"]:
            lang.deprecated[t["orthographic form"]] = {
                "identifier": t["machine identifier"],
                "deprecated": t["version"]["deprecated"],
                "replaced by": t.get("replaced by"), "dialect": release["number"]}


def in_force(lang: Language, entry: dict) -> bool:
    """Whether an entry is in force in the release `lang` reads: not deprecated in it or
    in an earlier release (specification/dialects.md#what-a-dialect-release-may-hold). A
    deprecated entry stays interpretable, and a key names the entry in force."""
    deprecated = entry["version"].get("deprecated")
    if entry["grammatical category"] == "dialect form":
        # a form is read from the dialect release loaded, which deprecates it or not
        return not deprecated
    return not deprecated or versions.key(deprecated) > versions.key(lang.version)


def class_id(group: str, name: str) -> str:
    return "g.%s.%s" % (group, name)


@lru_cache(maxsize=1)
def dialect_releases() -> dict:
    """Every release of every dialect in `lexicon/jargon/`, by (number, version): the
    jargon, each term formed from core items and read by its composition
    (specification/dialects.md#terms), and the compressed forms of release 0.2 on
    (specification/dialects.md#compressed-forms)."""
    root = os.path.join(_data_root(), "lexicon", "jargon")
    out = {}
    if not os.path.isdir(root):
        return out
    for name in sorted(os.listdir(root)):
        if not os.path.isdir(os.path.join(root, name)):
            continue
        for file in sorted(os.listdir(os.path.join(root, name))):
            if file.endswith(".json"):
                d = _load("lexicon", "jargon", name, file)
                out[(d["number"], d["version"])] = d
    return out


@lru_cache(maxsize=1)
def dialects() -> dict:
    """The latest release of each dialect, by name."""
    out = {}
    for (_, version), d in sorted(dialect_releases().items(),
                                  key=lambda kv: (kv[0][0], versions.key(kv[0][1]))):
        out[d["dialect"]] = d
    return out


@lru_cache(maxsize=1)
def language_releases() -> dict:
    """The record of the language releases (`language/releases.json`)."""
    return _load("language", "releases.json")
