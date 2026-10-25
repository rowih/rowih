"""The test interfaces of the obligations of a conformant implementation
(specification/conformance.md#the-conformance-suite): the single-edit, truncation and
transport enumerations, fuzzed input, and the critical projection of an analysis against
which an edit is judged."""
from __future__ import annotations

import random
import unicodedata

from . import api, data
from .checker import move_class

# Declared defaults of the critical classes, which normalisation states wherever their
# class applies: their presence follows from the unit, so a change that only moves where
# they are stated changes no critical value (specification/meaning.md#the-normal-form).
CLAIM_NOTHING = {"g.standing.basis.unstated", "g.standing.strength.unstated",
                 "g.standing.independence-of-a-confirmation.same-source",
                 "g.situations-and-contents.comparator.unstated",
                 "g.situations-and-contents.polarity.affirmative"}
ICV_CODES = {"d.check-values.integrity-mismatch", "d.checker.integrity-value-required"}


# ---------------------------------------------------------------- critical projection

def critical_projection(analysis) -> list:
    """For each move, every critical value of its normal form with the path of units and
    roles that holds it, as a sorted list, together with the head and the class. Two
    analyses with equal projections differ in no critical dimension of the core."""
    lang = data.load()
    out = []
    env = analysis.message.envelope if analysis.message else None
    if env is not None:
        out.append(("envelope", env.sender.text, tuple(r.text for r in env.recipients),
                    env.time.text, env.identifier.text, env.first_entry.text,
                    env.forwarded is not None))
    if analysis.statement is not None:
        # what a protocol message states is critical whole: the messages its sender
        # holds, asks for or has lost (specification/protocol.md#protocol-messages)
        out.append(("statement", repr(analysis.statement)))
    for n in analysis.normal:
        cls = move_class(n)
        items = [("head", tuple(n["adds"]), tuple(n["change"]), n.get("authority"),
                  repr(n.get("deadline")), repr(_strip(n.get("named"))),
                  repr(_strip(n.get("also_named"))),
                  n.get("precision_bound"), tuple(sorted(k for k, v in cls.items() if v)))]
        if n.get("authority_term"):
            items.append(("authority", repr(_strip(n["authority_term"]))))
        found = []
        for i, c in enumerate(n["constituents"]):
            _walk(c, ("move",), found, lang)
        out.append(tuple(items + sorted(found)))
    return out


def _strip(t):
    if isinstance(t, dict):
        return {k: _strip(v) for k, v in t.items() if not k.startswith("_")}
    if isinstance(t, list):
        return [_strip(x) for x in t]
    return t


def _walk(node, path, found, lang):
    k = node.get("kind")
    if k in ("assertion", "situation", "term"):
        p = path + (k,)
        for part in node["parts"]:
            pk = part["kind"]
            if pk == "value":
                item = lang.items.get(part["member"])
                if item is not None and item.critical_code and \
                        part["member"] not in CLAIM_NOTHING:
                    found.append((p, part["member"]))
            elif pk == "quantity":
                found.append((p, "quantity", part.get("comparator"), part["number"],
                              part.get("unit"), part.get("per"), part.get("calibration")))
            elif pk == "party":
                found.append((p, "party", part["number"]))
            elif pk == "dialect":
                found.append((p, "dialect", part["number"]))
            elif pk == "time":
                found.append((p, "time", part["index"], repr(part["spec"])))
            elif pk == "ref":
                found.append((p, "ref", repr(_strip(part))))
            elif pk == "filler":
                _walk(part["filler"], p + (part["role"],), found, lang)
            else:
                _walk(part, p, found, lang)
    elif k == "readings":
        for r in node["readings"]:
            _walk(r, path + ("readings",), found, lang)
    elif k == "wall":
        found.append((path, "wall", node["material"]))
    elif k == "ref":
        found.append((path, "ref", repr(_strip(node))))
    elif k == "same":
        found.append((path, "same"))


# ---------------------------------------------------------------- judging an edit

def judge(original, edited_text: str, canonical: bool) -> dict:
    """The outcome of one edit, with the integrity check value verified and ignored:
    'rejected' when a diagnostic is drawn, 'unchanged' when no critical dimension
    differs, and 'silent' otherwise. In the canonical serialisation a text that differs
    from the canonical serialisation the reader computes is rejected."""
    a = api.parse(edited_text)
    codes = [d.code for d in a.diagnostics]
    layout = canonical and a.message is not None and a.canonical != edited_text
    out = {}
    stated = a.message is not None and a.statement is not None
    for verify in (True, False):
        relevant = codes if verify else [c for c in codes if c not in ICV_CODES]
        if relevant or layout or a.message is None or not (a.moves or stated):
            out[verify] = "rejected"
        elif critical_projection(a) == critical_projection(original):
            out[verify] = "unchanged"
        else:
            out[verify] = "silent"
    return out


# ---------------------------------------------------------------- the enumerations

def symbol_edits(text: str, alphabet: str):
    """Every deletion, insertion and substitution of one character, separators included
    among the characters inserted and substituted."""
    chars = alphabet + " "
    seen = set()
    for i in range(len(text)):
        cand = text[:i] + text[i + 1:]
        if cand not in seen:
            seen.add(cand)
            yield ("delete", i, ""), cand
        for ch in chars:
            if ch != text[i]:
                cand = text[:i] + ch + text[i + 1:]
                if cand not in seen:
                    seen.add(cand)
                    yield ("substitute", i, ch), cand
    for i in range(len(text) + 1):
        for ch in chars:
            cand = text[:i] + ch + text[i:]
            if cand not in seen:
                seen.add(cand)
                yield ("insert", i, ch), cand


def word_edits(text: str, words: list):
    """Every deletion and duplication of one word, and every substitution and insertion
    of one word of the lexicon, line structure kept."""
    lines = [line.split(" ") for line in text.split("\n") if line]
    seen = set()

    def emit(new_lines):
        cand = "".join(" ".join(x) + "\n" for x in new_lines if x)
        if cand in seen or cand == text:
            return None
        seen.add(cand)
        return cand
    for li, line in enumerate(lines):
        for wi in range(len(line)):
            for kind, new in (("delete", line[:wi] + line[wi + 1:]),
                              ("duplicate", line[:wi + 1] + line[wi:])):
                cand = emit(lines[:li] + [new] + lines[li + 1:])
                if cand:
                    yield (kind, li, wi, ""), cand
            for w in words:
                if w != line[wi]:
                    cand = emit(lines[:li] + [line[:wi] + [w] + line[wi + 1:]] + lines[li + 1:])
                    if cand:
                        yield ("substitute", li, wi, w), cand
        for wi in range(len(line) + 1):
            for w in words:
                cand = emit(lines[:li] + [line[:wi] + [w] + line[wi:]] + lines[li + 1:])
                if cand:
                    yield ("insert", li, wi, w), cand


def enumerate_single_edits(text: str, unit: str = "symbol", canonical: bool = False,
                           limit: int | None = None) -> dict:
    """Counts of each outcome over every single edit of `text`, for both settings of
    the integrity check value, with the silent edits listed."""
    lang = data.load()
    original = api.parse(text)
    gen = symbol_edits(text, lang.letters) if unit == "symbol" else \
        word_edits(text, sorted(lang.by_form))
    counts = {True: {"rejected": 0, "unchanged": 0, "silent": 0},
              False: {"rejected": 0, "unchanged": 0, "silent": 0}}
    silent = {True: [], False: []}
    for n, (edit, cand) in enumerate(gen):
        if limit is not None and n >= limit:
            break
        res = judge(original, cand, canonical)
        for verify in (True, False):
            counts[verify][res[verify]] += 1
            if res[verify] == "silent":
                silent[verify].append(edit)
    return {"counts": counts, "silent": silent}


def enumerate_prefixes(text: str, native: bool = False) -> list:
    """Every proper prefix that draws no diagnostic; the obligation is that none does."""
    lang = data.load()
    if native:
        text, _ = api.convert(text, "native")
    survivors = []
    for i in range(len(text)):
        if text[:i].rstrip() == text.rstrip():
            continue    # only trailing separators removed: the same message, not a cut
        a = api.parse(text[:i])
        if not a.diagnostics and a.message is not None and a.moves:
            survivors.append(i)
    return survivors


def _markdown(text: str) -> str:
    """A routine Markdown rendering: line breaks become spaces, emphasis and escapes
    consumed (none occur in the language's alphabet)."""
    out = text
    for ch in "*_#>`\\":
        out = out.replace(ch, "")
    return out.replace("\n", " ")


TRANSFORMATIONS = {
    "nfc": lambda t: unicodedata.normalize("NFC", t),
    "nfd": lambda t: unicodedata.normalize("NFD", t),
    "nfkc": lambda t: unicodedata.normalize("NFKC", t),
    "crlf": lambda t: t.replace("\n", "\r\n"),
    "cr": lambda t: t.replace("\n", "\r"),
    "trailing-whitespace": lambda t: "\n".join(x.rstrip() for x in t.split("\n")),
    "trailing-spaces-added": lambda t: t.replace("\n", "   \n"),
    "wrap-20": lambda t: _wrap(t, 20, True),
    "wrap-7-hard": lambda t: _wrap(t, 7, False),
    "tabs": lambda t: t.replace(" ", "\t"),
    "tab-expansion": lambda t: t.replace("\t", "        "),
    "markdown": _markdown,
    "smart-quotes": lambda t: t.replace('"', "“").replace("'", "’"),
    "html-escape": lambda t: t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"),
    "leading-indent": lambda t: "\n".join("    " + x for x in t.split("\n")),
}


# The transformations that act on characters rather than on layout: each must leave every
# character of a transmitted alphabet as it is, which is how the alphabets meet
# `inv.transport-stable` by their construction
# (specification/writing-system.md#the-native-digital-form).
CHARACTER_TRANSFORMATIONS = ("nfc", "nfd", "nfkc", "markdown", "smart-quotes", "html-escape")


def alphabets(lang=None) -> dict:
    """The characters that spell words in each transmitted encoding, outside its payloads:
    the transliteration's letters and the native digital form's code points, each with the
    space that separates words. Line ends are layout, which carries nothing
    (specification/conformance.md#the-invariants); the transformations that change them
    are survived or detected message by message."""
    lang = lang or data.load()
    return {"transliteration": lang.letters + " ",
            "native": "".join(lang.code_points[c] for c in lang.letters) + " "}


def alphabet_changes(lang=None) -> list:
    """Each (encoding, transformation, character) that a character-level transformation
    changes; the obligation is that there is none."""
    out = []
    for name, chars in alphabets(lang).items():
        for t in CHARACTER_TRANSFORMATIONS:
            for ch in chars:
                if TRANSFORMATIONS[t](ch) != ch:
                    out.append((name, t, ch))
    return out


def _wrap(text: str, width: int, at_words: bool) -> str:
    out = []
    for line in text.split("\n"):
        if at_words:
            cur = ""
            for w in line.split(" "):
                if cur and len(cur) + 1 + len(w) > width:
                    out.append(cur)
                    cur = w
                else:
                    cur = (cur + " " + w) if cur else w
            out.append(cur)
        else:
            out.extend(line[i:i + width] for i in range(0, max(len(line), 1), width))
    return "\n".join(out)


def transform(text: str, name: str, native: bool = False) -> str:
    """The outcome of one routine transport transformation of a message, in the
    transliteration or in the native digital form: 'same' when the analysis is
    unchanged, 'detected' when a diagnostic is drawn, 'changed' otherwise."""
    original = api.parse(text)
    if native:
        text = api.convert(text, "native")[0]
    t = TRANSFORMATIONS[name](text)
    a = api.parse(t)
    if [d.code for d in a.diagnostics] != [d.code for d in original.diagnostics]:
        return "detected"
    same = a.canonical == original.canonical and a.normal_text == original.normal_text
    return "same" if same else "changed"


def fuzz(seed: int, size: int, corpus: list) -> list:
    """Random byte strings and corpus messages altered at random; returns the inputs
    that raised an exception (the obligation is that none does)."""
    rng = random.Random(seed)
    failures = []
    alphabet = data.load().letters + " \n\t2345670123456789cfjqvxz‮​"
    for i in range(size):
        if i % 2 == 0 and corpus:
            base = list(rng.choice(corpus))
            for _ in range(rng.randint(1, 6)):
                op = rng.random()
                pos = rng.randrange(len(base) + 1)
                if op < 0.4 and base:
                    del base[min(pos, len(base) - 1)]
                elif op < 0.8:
                    base.insert(pos, rng.choice(alphabet))
                else:
                    a, b = sorted((rng.randrange(len(base)), rng.randrange(len(base))))
                    base = base[:a] + base[b:a:-1] + base[b:]
            text = "".join(base)
        else:
            text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 200)))
        try:
            api.parse(text)
        except Exception as e:  # the obligation under test: no input raises
            failures.append((text, repr(e)))
    return failures
