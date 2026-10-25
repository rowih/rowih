"""Record how a release of the language reads its own corpus, for the release comparison.

Writes `corpus/releases/<language version>.json`: every message of the conformance,
attitude and adversarial corpora with the analysis the release gives it, as the release
that wrote it read it. A later release reads each message again and must give the same
record wherever it declares that it reads the earlier release (`language/releases.json`).
The negative corpus is left out: compatibility keeps what was valid, and a later release
may make valid what an earlier one refused.

Run from the repository root, with the release's own code, before anything of a later
release is built: `python3 tools/record_release.py`.
"""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))

from rowih import api, data  # noqa: E402

DIRECTORIES = ("conformance", "attitudes", "adversarial")


def record(a) -> dict:
    """What the comparison holds a later release to: every diagnostic by its code, each
    move's computed class, the normal form as serialised, the social and textual
    component, the meaning of each unlisted formation, a protocol message's statement,
    the confidence, and the canonical layout by its SHA-256."""
    return {
        "diagnostics": [d.code for d in a.diagnostics],
        "classes": list(a.classes),
        "normal": a.normal_text,
        "social": a.social,
        "formations": a.formations,
        "statement": a.statement,
        "confidence": a.confidence,
        "canonical": hashlib.sha256(a.canonical.encode("utf-8")).hexdigest(),
    }


def corpus_paths() -> list:
    out = []
    for d in DIRECTORIES:
        for name in sorted(os.listdir(os.path.join(ROOT, "corpus", d))):
            if name.endswith(".txt"):
                out.append("corpus/%s/%s" % (d, name))
    return out


def main():
    lang = data.load()
    items = []
    for path in corpus_paths():
        with open(os.path.join(ROOT, path), encoding="utf-8") as f:
            text = f.read()
        items.append({"path": path, "text": text, "record": record(api.parse(text))})
    version = lang.grammar["version"]
    out = {"language": version, "lexicon": lang.release["version"],
           "protocol": lang.protocol["version"], "items": items}
    path = os.path.join(ROOT, "corpus", "releases", "%s.json" % version)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("%s: %d messages" % (path, len(items)))


if __name__ == "__main__":
    main()
