"""The comparison of the two implementations (`compare_implementations`): the record each
writes of an analysis, as one line of JSON, holding every stage's output, every diagnostic
with its six fields, the check values, the conversions and the renderings. The TypeScript
parser and renderer write the same record (`typescript/src/record.ts`); the two records
must agree byte for byte (specification/conformance.md#the-two-implementations)."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile

from . import api, render, speech
from .structured import diagnostic as _diagnostic, word as _word
from .tree import strip_private

TYPESCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "typescript")
NODE_TIMEOUT = 600


class ParityUnavailable(Exception):
    """The TypeScript implementation cannot be run here: no Node, or no checkout."""


def record(text: str, every_view: bool = False) -> dict:
    """The record of a text. With `every_view`, the record also holds the compact,
    handwritten and high-contrast SVG, drawn from the one analysis, and the SHA-256 of
    the display PNG: the corpus's records hold them, which exercise every form and the
    ceremonial variant, and the records of sampled edits leave them out, since drawing
    and rasterising them would multiply the comparison's time several times over."""
    a = api.parse(text)
    values = api.check_values(text)
    out = {
        "encoding": a.encoding,
        "words": [_word(w) for w in a.words],
        "canonical": a.canonical,
        "moves": [strip_private(t) for t in a.moves],
        "classes": [dict(c) for c in a.classes],
        "normal": a.normal,
        "normal text": a.normal_text,
        "social": a.social,
        "formations": a.formations,
        "diagnostics": [_diagnostic(d) for d in a.diagnostics],
        "statement": a.statement,
        "confidence": a.confidence,
        "integrity": values.get("integrity"),
        "semantic": values.get("semantic"),
        "native": api.convert(text, "native")[0],
        "export": api.convert(text, "json")[0],
        "svg": api.render(text, "svg")[0],
        "html": api.render(text, "html")[0],
        "terminal": api.render(text, "terminal", has_font=True)[0],
        "spoken": speech.spoken(a),
    }
    if every_view:
        out["compact"] = render.svg(a, form="compact")
        out["handwritten"] = render.svg(a, form="handwritten")
        out["high contrast"] = render.svg(a, contrast="high")
        out["png"] = hashlib.sha256(render.png(a)).hexdigest()
    return out


def record_line(text: str, every_view: bool = False) -> str:
    return json.dumps(record(text, every_view), ensure_ascii=False)


def typescript_records(texts: list, every_view: bool = False) -> list:
    """The TypeScript implementation's record of each text, one line each."""
    node = shutil.which("node")
    if node is None or not os.path.isfile(os.path.join(TYPESCRIPT, "tools", "records.ts")):
        raise ParityUnavailable("Node or the TypeScript checkout is absent")
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8",
                                     delete=False) as f:
        json.dump(texts, f, ensure_ascii=False)
        path = f.name
    try:
        proc = subprocess.run([node, "--experimental-strip-types", "--no-warnings",
                               "tools/records.ts", path] + (["--every-view"] if every_view else []),
                              cwd=TYPESCRIPT,
                              capture_output=True, timeout=NODE_TIMEOUT)
    finally:
        os.unlink(path)
    if proc.returncode != 0:
        raise ParityUnavailable("the TypeScript records failed: %s"
                                % proc.stderr.decode("utf-8", "replace")[-2000:])
    lines = proc.stdout.decode("utf-8").split("\n")
    return lines[:-1] if lines and lines[-1] == "" else lines


def interface_records(terms: list) -> dict:
    """What `version` gives and what `lookup` gives for each term, in the shape
    `typescript/tools/interface.ts` writes it."""
    lookups = {t: [{"kind": it.kind, "identifier": it.identifier, "form": it.form,
                    "gloss": it.gloss, "class": it.class_id, "name": it.name, "sort": it.sort,
                    "category": it.category} for it in api.lookup(t)] for t in terms}
    return json.loads(json.dumps({"version": api.version(), "lookups": lookups},
                                 ensure_ascii=False))


def typescript_interface(terms: list) -> dict:
    """The TypeScript implementation's `version` and `lookup` of each term."""
    node = shutil.which("node")
    if node is None or not os.path.isfile(os.path.join(TYPESCRIPT, "tools", "interface.ts")):
        raise ParityUnavailable("Node or the TypeScript checkout is absent")
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8",
                                     delete=False) as f:
        json.dump(terms, f, ensure_ascii=False)
        path = f.name
    try:
        proc = subprocess.run([node, "--experimental-strip-types", "--no-warnings",
                               "tools/interface.ts", path], cwd=TYPESCRIPT,
                              capture_output=True, timeout=NODE_TIMEOUT)
    finally:
        os.unlink(path)
    if proc.returncode != 0:
        raise ParityUnavailable("the TypeScript interface failed: %s"
                                % proc.stderr.decode("utf-8", "replace")[-2000:])
    return json.loads(proc.stdout.decode("utf-8"))


BATCH = 1000


def compare_implementations(texts: list, every_view: bool = False) -> list:
    """Each implementation run twice over the texts, a batch at a time. Returns the
    disagreements, each as (index, which, Python's line, the other line): empty when
    every record agrees byte for byte and each implementation agrees with itself."""
    out = []
    for start in range(0, len(texts), BATCH):
        out += [(start + i, which, a, b) for i, which, a, b in
                _compare_batch(texts[start:start + BATCH], every_view)]
    return out


def _compare_batch(texts: list, every_view: bool) -> list:
    py_first = [record_line(t, every_view) for t in texts]
    py_second = [record_line(t, every_view) for t in texts]
    ts_first = typescript_records(texts, every_view)
    ts_second = typescript_records(texts, every_view)
    out = []
    for i in range(len(texts)):
        if py_first[i] != py_second[i]:
            out.append((i, "python twice", py_first[i], py_second[i]))
        if i >= len(ts_first) or ts_first[i] != ts_second[i]:
            out.append((i, "typescript twice", ts_first[i] if i < len(ts_first) else None,
                        ts_second[i] if i < len(ts_second) else None))
        elif py_first[i] != ts_first[i]:
            out.append((i, "python and typescript", py_first[i], ts_first[i]))
    if len(ts_first) != len(texts):
        out.append((len(texts), "count", str(len(texts)), str(len(ts_first))))
    return out
