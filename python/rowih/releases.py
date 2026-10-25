"""The releases a reader reads, and the release a message is read under
(specification/protocol.md#versions-and-features).

A message is read under the language release, the lexicon release and the dialect
releases it names, and under nothing a participant holds. A reader reads the messages of
each language release its own release lists under `reads` in `language/releases.json`,
each with the meaning that release gave it; every lexicon release from the least its
earliest language release may name; the protocol messages of each protocol version its
own reads; and every dialect release it holds whose digest is the one the message states.
What a message names and the reader does not read is reported, with what the reader does
read, and the message is not interpreted under anything else."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import data, dialects, versions


@dataclass(frozen=True)
class Reader:
    """What a reader holds. A field left None holds everything this implementation reads;
    `lacking` names the features, by number, the reader lacks (protocol 0.4)."""
    language: tuple | None = None
    lexicon: tuple | None = None
    protocol: tuple | None = None
    dialects: tuple | None = None       # (number, version) pairs
    lacking: frozenset = frozenset()

    def reads(self) -> dict:
        own = implementation()
        out = {k: tuple(getattr(self, k)) if getattr(self, k) is not None else own[k]
               for k in ("language", "lexicon", "protocol", "dialects")}
        out["lacking"] = tuple(sorted(self.lacking))
        return out


FULL = Reader()


def _language_record(version: str) -> dict | None:
    return next((r for r in data.language_releases()["language"]
                 if r["language"] == version), None)


def implementation() -> dict:
    """What this implementation reads: the language releases its own release lists, each
    lexicon release on disk from the least those releases may name, the protocol versions
    its own protocol reads, and every dialect release on disk."""
    lang = data.load()
    own = _language_record(lang.grammar["version"])
    language = tuple(versions.ordered(own["reads"]))
    least = min((_language_record(v).get("least lexicon", v) for v in language),
                key=versions.key)
    lexicon = tuple(v for v in _lexicon_releases()
                    if versions.key(least) <= versions.key(v))
    protocol = tuple(next(p["reads"] for p in data.language_releases()["protocol"]
                          if p["protocol"] == lang.protocol["version"]))
    held = tuple(sorted(data.dialect_releases(), key=lambda k: (k[0], versions.key(k[1]))))
    return {"language": language, "lexicon": lexicon, "protocol": protocol,
            "dialects": held}


def _lexicon_releases() -> list:
    import os
    root = os.path.join(data._data_root(), "lexicon", "releases")
    return versions.ordered(name[:-5] for name in os.listdir(root) if name.endswith(".json"))


@dataclass
class Resolution:
    """What a message names, and either the arguments of `data.load` it is read under or
    what the reader lacks of it, each by its kind and what the message names."""
    named: dict
    load: dict | None = None
    lacking: dict = field(default_factory=dict)
    pairing: list = field(default_factory=list)      # what the message pairs wrongly


def named_of(env) -> dict:
    return {"language": env.version[0].text, "lexicon": env.version[1].text,
            "protocol": env.version[2].text,
            "dialects": [(n.integer(), v.text, d.text) for n, v, d in env.dialects]}


def resolve(env, reader: Reader = FULL) -> Resolution:
    named = named_of(env)
    reads = reader.reads()
    res = Resolution(named)
    for kind in ("language", "lexicon", "protocol"):
        if named[kind] not in reads[kind]:
            res.lacking.setdefault(kind, []).append(named[kind])
    held = data.dialect_releases()
    for number, version, digest in named["dialects"]:
        release = held.get((number, version))
        if (number, version) not in reads["dialects"] or release is None or \
                release["digest"] != digest:
            res.lacking.setdefault("dialects", []).append((number, version, digest))
    if named["dialects"] and DIALECTS_FEATURE in reader.lacking:
        res.lacking.setdefault("features", []).append(DIALECTS_FEATURE)
    if res.lacking:
        return res
    record = _language_record(named["language"])
    least = record.get("least lexicon", record["lexicon"])
    if versions.key(named["lexicon"]) < versions.key(least):
        res.pairing.append("language %s names a lexicon from %s" % (named["language"], least))
    for number, version, _ in named["dialects"]:
        formed = held[(number, version)]["formed from lexicon"]
        if versions.key(named["lexicon"]) < versions.key(formed):
            res.pairing.append("dialect %d %s is formed from lexicon %s"
                               % (number, version, formed))
    if not res.pairing:
        res.load = {"version": named["lexicon"], "language": named["language"],
                    "dialects": tuple((n, v) for n, v, _ in named["dialects"])}
    return res


DIALECTS_FEATURE = 11


def conflicts(lang) -> list:
    """The pairs of forms a message's resources would confuse: a compressed form of a
    named dialect within one edit of a word of the named lexicon release or of another
    named dialect's form (specification/dialects.md#terms)."""
    from .lexicon_checks import levenshtein as distance
    forms = [(f["orthographic form"], f["machine identifier"])
             for f in lang.dialect_forms.values()]
    out = []
    for i, (form, ident) in enumerate(forms):
        for other, item in lang.by_form.items():
            if item.identifier != ident and item.kind != "move-check" and \
                    len(other) == len(form) and distance(form, other) < 2:
                out.append((ident, item.identifier))
        for form2, ident2 in forms[i + 1:]:
            if form2 == form:
                out.append((ident, ident2))
    return out


def digest_of(number: int, version: str) -> str | None:
    release = data.dialect_releases().get((number, version))
    return release["digest"] if release is not None else None


def verify_digests() -> list:
    """Every dialect release whose stated digest is not the digest of its content."""
    return [k for k, r in data.dialect_releases().items() if r["digest"] != dialects.digest(r)]


def check_releases(record: dict | None = None) -> list:
    """Every finding against the record of language releases: a release that does not read
    itself, or, from major version 1, one that does not read every earlier release of its
    major version (specification/protocol.md#versions-and-features); the pre-release
    series of major version 0 is exempt. An empty list means the record passes."""
    record = record or data.language_releases()
    out = []
    seen = []
    for r in record["language"]:
        version = r["language"]
        if version not in r["reads"]:
            out.append(("does not read itself", version))
        major = versions.major(version)
        if major >= 1:
            for earlier in seen:
                if versions.major(earlier) == major and earlier not in r["reads"]:
                    out.append(("drops an earlier release", "%s %s" % (version, earlier)))
        seen.append(version)
    return out
