"""Compare the Python and the TypeScript implementations (see
specification/conformance.md#the-two-implementations) over every corpus message, every
negative item, each message in the native digital form, and a seeded sample of each
message's single-symbol and single-word edits and of random characters written into it,
which reach the diagnostics the corpus alone does not. Each implementation runs twice; the
records must agree byte for byte. Writes `corpus/reports/parity.json`. Run from the
repository root: `python3 tools/compare_implementations.py [per-message] [seed]
[--shard K/N]`.

With `--shard K/N` the run compares the K-th of N interleaved parts of the texts, which
the seed draws in full first, and writes no report. Exit status: 1 when the
implementations disagree on any text, 0 otherwise."""
import glob
import json
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))

from rowih import api, data, parity  # noqa: E402
from rowih.conformance import symbol_edits, word_edits  # noqa: E402
from run_enumerations import arguments, share  # noqa: E402


# Characters a damaged or hostile text may hold: separators, letters of the payload
# alphabet, a letter outside it, the first and last code points of the native form, one
# reserved in its block and one just past the block, an astral character, a right-to-left
# override and the byte-order mark.
FOREIGN = [" ", "\t", "\r", "\n", "2", "7", "q", "\u00e9", "\uf3a0", "\uf3b2", "\uf3b3", "\uf3c0",
           "\U0001f600", "\u202e", "\ufeff", "?", "0"]


def damaged(text, rng):
    chars = list(text)
    for _ in range(rng.randint(1, 3)):
        k = rng.randrange(len(chars) + 1)
        if rng.random() < 0.5 and k < len(chars):
            chars[k] = rng.choice(FOREIGN)
        else:
            chars.insert(k, rng.choice(FOREIGN))
    return "".join(chars)


def main() -> int:
    args, shard = arguments(sys.argv[1:])
    per = int(args[0]) if args else 120
    seed = int(args[1]) if len(args) > 1 else 39
    lang = data.load()
    rng = random.Random(seed)
    # the conformance sets and the negative corpus, as tests/corpus.py names them; the
    # domain corpus, compared once without damage by tests/test_domains.py, would
    # multiply the damaged variants past what a run can hold
    paths = sorted(p for d in ("conformance", "attitudes", "adversarial", "negative")
                   for p in glob.glob(os.path.join(ROOT, "corpus", d, "*.txt")))
    texts, origin = [], []
    for p in paths:
        text = open(p, encoding="utf-8").read()
        name = os.path.relpath(p, os.path.join(ROOT, "corpus"))
        texts.append(text)
        origin.append([name, "as written"])
        native = api.convert(text, "native")[0]
        if native:
            texts.append(native)
            origin.append([name, "native digital form"])
        for _ in range(per // 4):
            texts.append(damaged(text, rng))
            origin.append([name, "foreign characters"])
        for unit, edits in (("symbol", symbol_edits(text, lang.letters)),
                            ("word", word_edits(text, sorted(lang.by_form)))):
            cands = [c for _, c in edits]
            for c in rng.sample(cands, min(per, len(cands))):
                texts.append(c)
                origin.append([name, unit + " edit"])
    part = share(range(len(texts)), shard)
    texts, origin = [texts[i] for i in part], [origin[i] for i in part]
    start = time.time()
    disagreements = parity.compare_implementations(texts)
    report = {"texts": len(texts), "messages": len(paths), "per message and unit": per,
              "seed": seed, "disagreements": len(disagreements),
              "examples": [{"origin": origin[i], "which": which, "text": texts[i]}
                           for i, which, _, _ in disagreements[:20]],
              "seconds": round(time.time() - start)}
    if shard is None:
        with open(os.path.join(ROOT, "corpus", "reports", "parity.json"), "w",
                  encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
            f.write("\n")
    print("%d texts from %d messages: %d disagreements in %ds"
          % (len(texts), len(paths), len(disagreements), report["seconds"]))
    return 1 if disagreements else 0


if __name__ == "__main__":
    sys.exit(main())
