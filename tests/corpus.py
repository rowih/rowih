"""The conformance corpus as the tests read it
(specification/conformance.md#the-conformance-suite, `run_corpus`)."""
import glob
import json
import os

from rowih import api, data
from rowih.notation import Reader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETS = ["conformance", "attitudes", "adversarial"]
# the directories the corpus-wide tests read, the conformance sets and the negative
# corpus; the domain corpus of version 1.0 has tests of its own (tests/test_domains.py),
# since reading its 2,237 messages in every form would multiply the suite's time
CORPUS_DIRECTORIES = SETS + ["negative"]


def corpus_paths() -> list:
    """Every message file of the corpus-wide tests, in order."""
    return sorted(p for d in CORPUS_DIRECTORIES
                  for p in glob.glob(os.path.join(ROOT, "corpus", d, "*.txt")))


def items():
    out = []
    for name in SETS:
        for item in json.load(open(os.path.join(ROOT, "corpus", "source", name + ".json"),
                                   encoding="utf-8"))["items"]:
            out.append(dict(item, set=name))
    return out


def messages():
    """Every corpus message: (item id, index, source record, transliteration). The record
    carries the first entry its message states, as `first entry`."""
    import sys
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from build_corpus import first_entries
    out = []
    for item in items():
        firsts = first_entries(item, data.load())
        for k, m in enumerate(item["messages"], 1):
            path = os.path.join(ROOT, "corpus", item["set"], "%s.%d.txt" % (item["id"], k))
            with open(path, encoding="utf-8") as f:
                out.append((item["id"], k, dict(m, **{"first entry": firsts[k - 1]}),
                            f.read()))
    return out


def language_of(m):
    """The language a record is written in: the current release, or the release and the
    dialects the record names."""
    import sys
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from build_corpus import language_for
    return language_for(m, data.load())


def in_current_release(m) -> bool:
    """Whether a record is written in the current release with no dialect, as the tests
    that regenerate meanings with the current release's generator need."""
    return "release" not in m and "dialects" not in m


def moves_of(m):
    import sys
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from build_corpus import language_for, substitute
    if "statement" in m:
        return []   # a protocol message carries no moves
    # in the release and with the dialects the record names
    written = language_for(m, data.load())
    return Reader(written).moves(substitute(m["notation"], written))


def run_corpus(test):
    for item_id, k, m, text in messages():
        test(item_id, k, m, text)


def analysis(text):
    return api.parse(text)
