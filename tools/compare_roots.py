"""Whether any word of the lexicon resembles a word of a major language or of a
constructed language, under a rule fixed before the comparison: every word of one morpheme
in the open classes, compared by edit distance on a phonemic transcription with the
frequent vocabulary of the major languages and the published word lists of the constructed
ones.

The sources are pinned in `corpus/vocabularies/sources.json`, each by its URL, at a fixed
commit where it has one, and by the SHA-256 of its file; they are fetched into
`corpus/vocabularies/cache/`, which git ignores, and checked against their hashes before
use. A match's meaning is read from English Wiktionary as kaikki.org extracts it, word by
word, into the same cache, and the report records the hash of what was read. The rulings
on related meaning are judgements, kept in `corpus/vocabularies/rulings.json`.

Writes `corpus/reports/root-originality.json`. Run from the repository root:
`python3 tools/compare_roots.py [pin|fetch|compare]`; `pin` is run once for each version
of the comparison. `compare` exits with status 1 when a word awaits its redesign, and 0
otherwise."""
import collections
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vocabularies as V  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))

MANIFEST = os.path.join(ROOT, "corpus", "vocabularies", "sources.json")
RULINGS = os.path.join(ROOT, "corpus", "vocabularies", "rulings.json")
CACHE = os.path.join(ROOT, "corpus", "vocabularies", "cache")
OUT = os.path.join(ROOT, "corpus", "reports", "root-originality.json")
# The rule the report is made under, stated with it.
RULE = ("every word of one morpheme in the open classes is compared, on a reduced "
        "phonemic transcription, with the frequent vocabulary of the twenty major "
        "languages and the published word lists of the constructed languages; a close "
        "match, at an edit distance of at most one segment, whose meaning is related or "
        "offensive is redesigned, and every other close match is retained and reported "
        "with its meaning")
TIMEOUT = 120
FETCH_PAUSE = 0.2       # seconds between requests to kaikki.org
AGENT = "rowih-resemblance-audit/1.0 (+https://github.com/rowih/rowih)"
CLASSES = ("adopted", "convergent", "redesigned", "accidental and retained")


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read()


def cached(name: str) -> str:
    return os.path.join(CACHE, name.replace("/", "__"))


def pin():
    """Fetch every source afresh and write the manifest with each file's SHA-256."""
    os.makedirs(CACHE, exist_ok=True)
    out = []
    for name, url in V.sources():
        data = download(url)
        with open(cached(name), "wb") as f:
            f.write(data)
        out.append({"name": name, "url": url, "sha256": hashlib.sha256(data).hexdigest(),
                    "bytes": len(data)})
        print("pinned %s, %d bytes" % (name, len(data)))
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump({"read": V.READ, "sources": out}, f, ensure_ascii=False, indent=1)
        f.write("\n")


def fetch():
    """Fetch every pinned source missing from the cache, and check every file's hash."""
    with open(MANIFEST, encoding="utf-8") as f:
        manifest = json.load(f)
    os.makedirs(CACHE, exist_ok=True)
    for s in manifest["sources"]:
        path = cached(s["name"])
        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(download(s["url"]))
        with open(path, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        if digest != s["sha256"]:
            raise ValueError("source %s does not match its pinned hash" % s["name"])


def gloss(language: str, word: str) -> dict:
    """What English Wiktionary says of a word, as kaikki.org extracts it: its glosses, the
    tags of its senses, and the hash of the file read; cached, and fetched once."""
    name = "glosses/%s/%s.jsonl" % (language, word)
    path = cached(name)
    if not os.path.exists(path):
        quoted = [urllib.parse.quote(x, safe="") for x in (word[0], word[:2], word)]
        url = V.KAIKKI % ((urllib.parse.quote(language),) + tuple(quoted))
        try:
            data = download(url)
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
            data = b""
        time.sleep(FETCH_PAUSE)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
    with open(path, "rb") as f:
        data = f.read()
    glosses, tags = [], set()
    for line in data.decode("utf-8").splitlines():
        entry = json.loads(line)
        for sense in entry.get("senses", []):
            glosses += sense.get("glosses", [])[:1]
            tags.update(sense.get("tags", []))
    return {"glosses": glosses[:6], "tags": sorted(tags),
            "read": hashlib.sha256(data).hexdigest() if data else None}


def ours() -> list:
    """The words compared: every word of one morpheme in the open classes of lexicon 1.0,
    and the compressed forms of the dialects' newest releases."""
    from rowih import data
    lang = data.load("1.0")
    out = []
    for ident, e in sorted(lang.entries.items()):
        kind = lang.items[ident].kind
        if not data.in_force(lang, e):
            continue
        if kind == "root" or (kind == "derivation" and "irregular" in e):
            out.append((ident, e["key"], e["orthographic form"], e["phonological form"]))
    for d in sorted(data.dialects().values(), key=lambda d: d["number"]):
        for f in d.get("forms", []):
            if not f["version"]["deprecated"]:
                out.append((f["machine identifier"], f["key"], f["orthographic form"],
                            f["phonological form"]))
    return out


def load_rulings() -> dict:
    """The rulings, each kind keyed by (word, language, match)."""
    with open(RULINGS, encoding="utf-8") as f:
        stated = json.load(f)
    out = {kind: {(r["word"], r["language"], r["match"]): r["reason"] for r in stated[kind]}
           for kind in ("related", "not offensive")}
    out["redesigned"] = stated["redesigned"]
    return out


def failed(classes: dict) -> bool:
    """Whether a comparison fails: a close match that is not accidental and retained, so
    that a word awaits its redesign."""
    return any(n for c, n in classes.items() if c != "accidental and retained")


def classify(match: dict, rulings: dict) -> tuple:
    """A close match's class and the reason. A match a list or a sense label marks is
    offensive unless a ruling judges the mark not to be what a hearer takes the word to
    mean; an offensive match, or one a ruling judges related in meaning, is redesigned;
    any other is accidental and retained."""
    key = (match["word"], match["language"], match["match"])
    if match["offensive"]:
        if key in rulings["not offensive"]:
            return "accidental and retained", "marked as offensive (%s), and judged not: %s" \
                % (match["offensive"], rulings["not offensive"][key])
        return "redesigned", "offensive: %s" % match["offensive"]
    if key in rulings["related"]:
        return "redesigned", "related in meaning: %s" % rulings["related"][key]
    return "accidental and retained", "the meaning is unrelated to the word's"


def compare():
    fetch()
    rulings = load_rulings()
    words = ours()
    index = V.Index()
    report_languages = []
    for language in V.languages(cached):
        index.add(language, language["words"])
        report_languages.append({k: v for k, v in language.items() if k != "words"})
    matches = []
    for ident, key, form, phonological in words:
        segments = V.reduce(V.ipa_tokens(phonological.strip("/")))
        for language, entry in index.close(segments):
            matches.append(_match(ident, key, form, language, entry))
    for m in matches:
        if m["kind"] == "major" or m["language"] == "Esperanto":
            m.update(meaning=gloss(m["kaikki"], m["match"]))
            m["offensive"] = m["offensive"] or ", ".join(
                t for t in m["meaning"]["tags"] if t in V.OFFENSIVE_TAGS)
        m["class"], m["reason"] = classify(m, rulings)
    classes = _write(words, report_languages, matches, rulings["redesigned"])
    return 1 if failed(classes) else 0


def _match(ident, key, form, language, entry) -> dict:
    return {"word": form, "entry": ident, "key": key, "language": language["name"],
            "kind": language["kind"], "kaikki": language.get("kaikki"),
            "match": entry.spelling, "transcription": " ".join(entry.segments),
            "meaning": {"glosses": [entry.gloss]} if entry.gloss else None,
            "offensive": "the list for its language" if entry.offensive else ""}


def _write(words, languages, matches, redesigned):
    counts = collections.Counter(m["class"] for m in matches)
    out = {"rule": RULE, "read": V.READ, "words compared": len(words),
           "words": {form: {"entry": ident, "key": key, "phonological form": ph}
                     for ident, key, form, ph in words},
           "languages": languages, "not compared": V.NOT_COMPARED,
           "classes": {c: counts.get(c, 0) for c in CLASSES}, "redesigned": redesigned,
           "matches": [{k: v for k, v in m.items() if k not in ("kind", "kaikki")}
                       for m in sorted(matches, key=lambda m: (m["word"], m["language"],
                                                               m["match"]))]}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("compared %d words: %s" % (len(words), dict(counts)))
    return out["classes"]


if __name__ == "__main__":
    sys.exit({"pin": pin, "fetch": fetch, "compare": compare}[sys.argv[1]]() or 0)
