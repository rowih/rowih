"""Run the single-edit enumeration over every message of the conformance, attitude and
adversarial sets whose original draws no diagnostic: every deletion, insertion and
substitution of one symbol and of one word, judged in the transliteration and in the
canonical serialisation, with the integrity check value verified and ignored
(specification/conformance.md#the-enumerations). Writes
`corpus/reports/single-edits-<unit>.json`. Run from the repository root: `python3
tools/run_enumerations.py [symbol|word|both] [workers] [--shard K/N]`.

With `--shard K/N` the run checks the K-th of N interleaved parts of its jobs and writes
no report, so that continuous integration can divide it among jobs whose parts together
are the whole run. Exit status: 1 when the run finds an exception or an edit that changes
a critical value silently where the integrity check value is verified, 0 otherwise."""
import glob
import json
import os
import re
import sys
import time
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))

from rowih import api, data  # noqa: E402
from rowih.conformance import critical_projection, symbol_edits, word_edits, ICV_CODES  # noqa: E402


def share(items: list, shard) -> list:
    """The part of a run that `shard`, written `K/N`, checks: the K-th of N interleaved
    parts, K counted from 1, so that the parts are disjoint, differ in size by at most one
    and together are the run. Every item where `shard` is None."""
    if shard is None:
        return list(items)
    m = re.fullmatch(r"(\d+)/(\d+)", shard)
    if not m or not 1 <= int(m.group(1)) <= int(m.group(2)):
        raise ValueError("a shard is K/N with 1 <= K <= N, not %r" % shard)
    return list(items)[int(m.group(1)) - 1::int(m.group(2))]


def arguments(argv: list) -> tuple:
    """The positional arguments of a command line, and its shard, `--shard K/N`."""
    args, shard = list(argv), None
    if "--shard" in args:
        i = args.index("--shard")
        if i + 1 >= len(args):
            raise ValueError("--shard needs K/N")
        shard = args[i + 1]
        del args[i:i + 2]
    return args, shard


def failed(totals: dict, exceptions: list) -> bool:
    """Whether a run found a fault: an input that raised, or an edit that changed a
    critical value silently where the integrity check value is verified."""
    return bool(exceptions) or any(counts["silent"] for unit in totals.values()
                                   for key, counts in unit.items()
                                   if key.endswith("/verified"))


def run_one(args):
    path, unit = args
    text = open(path, encoding="utf-8").read()
    lang = data.load()
    first = api.parse(text)
    original = critical_projection(first)
    # the words of the current release and of the release and dialects the message is
    # read under, so that a compressed form is put for every word
    under = first.read_under or {}
    vocabulary = set(lang.by_form) | set(data.load(under.get("version"), under.get("language"),
                                                   under.get("dialects", ())).by_form)
    edits = symbol_edits(text, lang.letters) if unit == "symbol" else \
        word_edits(text, sorted(vocabulary))
    counts = {}
    silent = []
    exceptions = []
    for edit, cand in edits:
        try:
            a = api.parse(cand)
        except Exception as e:  # recorded as a finding: no input may raise
            exceptions.append([list(edit), repr(e)])
            continue
        codes = [d.code for d in a.diagnostics]
        layout_differs = a.message is not None and a.canonical != cand
        proj = None
        for encoding in ("transliteration", "canonical"):
            for verify in (True, False):
                relevant = codes if verify else [c for c in codes if c not in ICV_CODES]
                # a protocol message is judged by its statement, any other by its moves
                if relevant or a.message is None or not (a.moves or a.statement) or (
                        encoding == "canonical" and layout_differs):
                    outcome = "rejected"
                else:
                    if proj is None:
                        proj = critical_projection(a)
                    outcome = "unchanged" if proj == original else "silent"
                key = "%s/%s" % (encoding, "verified" if verify else "ignored")
                counts.setdefault(key, {"rejected": 0, "unchanged": 0, "silent": 0})
                counts[key][outcome] += 1
                if outcome == "silent":
                    silent.append([key, list(edit)])
    return os.path.basename(path), unit, counts, silent, exceptions


def main() -> int:
    args, shard = arguments(sys.argv[1:])
    which = args[0] if args else "both"
    workers = int(args[1]) if len(args) > 1 else 8
    units = ["symbol", "word"] if which == "both" else [which]
    candidates = sorted(p for s in ("conformance", "attitudes", "adversarial")
                        for p in glob.glob(os.path.join(ROOT, "corpus", s, "*.txt")))
    # A message whose original already draws a diagnostic (an unknown word, kept opaque)
    # would count every edit of it as detected, so it is listed and left out.
    excluded = [os.path.basename(p) for p in candidates
                if api.parse(open(p, encoding="utf-8").read()).diagnostics]
    paths = [p for p in candidates if os.path.basename(p) not in excluded]
    jobs = share([(p, u) for u in units for p in paths], shard)
    start = time.time()
    totals = {}
    silent_all = []
    exceptions_all = []
    with Pool(workers) as pool:
        for name, unit, counts, silent, exc in pool.imap_unordered(run_one, jobs):
            exceptions_all.extend([name, unit] + e for e in exc)
            for key, c in counts.items():
                t = totals.setdefault(unit, {}).setdefault(key, {"rejected": 0, "unchanged": 0,
                                                                 "silent": 0})
                for k, v in c.items():
                    t[k] += v
            for s in silent:
                silent_all.append([name, unit] + s)
            print(name, unit, "silent %d exceptions %d" % (len(silent), len(exc)), flush=True)
    print(json.dumps(totals, indent=1))
    if shard is None:
        report = {"messages": len(paths), "excluded": excluded, "units": units,
                  "totals": totals, "silent": sorted(silent_all),
                  "exceptions": exceptions_all, "seconds": round(time.time() - start)}
        out = os.path.join(ROOT, "corpus", "reports", "single-edits-%s.json" % which)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=1)
            f.write("\n")
    return 1 if failed(totals, exceptions_all) else 0


if __name__ == "__main__":
    sys.exit(main())
