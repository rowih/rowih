"""The API. No function raises an exception for any message: each returns its result
together with its diagnostics. A writer's input is another matter: `generate` and `write`
raise `InputError`, and nothing else, for a text that does not read as the notation
(`NotationError`), envelope values that cannot be written (`EnvelopeError`) or a register,
mode or diction the language does not have (`OptionError`), and `state` raises it for a
statement's parts it cannot write (`StatementError`), since these are errors of what the
writer gave and not of a message.

The module is one file past the usual length because it is the interface the
specification lists, every function in one place; what a function does beyond calling
the stages lives in the module it names."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from . import data, formation, registers
from .checker import Checker, move_class, precision_bound
from .diagnostics import Diagnostic, InputError  # noqa: F401
from .lexer import lex, tokenize as _tokenize
from .normal import Normaliser
from .notation import NotationError  # noqa: F401
from .parser import parse_words
from .serialise import canonical_lines, check_value, to_native
from .tree import Spell, from_ast_move, strip_private
from .statements import STATEMENTS  # noqa: F401
from .writer import (FIXED_ENVELOPE, Envelope, EnvelopeError, OptionError,  # noqa: F401
                     StatementError)


@dataclass
class Analysis:
    text: str
    encoding: str
    words: list = field(default_factory=list)
    message: object = None
    moves: list = field(default_factory=list)        # move trees
    normal: list = field(default_factory=list)       # normal-form move trees
    classes: list = field(default_factory=list)      # computed class of each move
    diagnostics: list = field(default_factory=list)
    canonical: str = ""
    normal_text: str = ""
    # the social and textual component of each move: the act word and the idioms its
    # realisation chose, the losses it declares and its register, diction, politeness word
    # and register-marked words (specification/lexicon.md#registers)
    social: list = field(default_factory=list)
    # the meaning each formation the release does not list has from its parts
    formations: list = field(default_factory=list)
    # the statement of a protocol message, which carries no moves
    # (specification/protocol.md#protocol-messages): what it states and its parts, each a
    # channel with serials or entries
    statement: dict | None = None
    # what the message names of the releases (its language, lexicon and protocol versions
    # and its dialects), the arguments of `data.load` it was read under, and what of it
    # the reader lacked, by kind (specification/dialects.md#naming-a-dialect-in-a-message)
    named: dict = field(default_factory=dict)
    read_under: dict = field(default_factory=dict)
    lacking: dict = field(default_factory=dict)
    # the features a reader passed over, by move, and the words the named releases have
    # deprecated (specification/protocol.md#versions-and-features;
    # specification/dialects.md#what-a-dialect-release-may-hold)
    ignored: list = field(default_factory=list)
    deprecated: list = field(default_factory=list)
    # how far what was parsed is vouched for in transit
    # (specification/protocol.md#the-check-values): `verified` where the integrity check
    # value matched, `lowered` where it did not, so that what parsed may be damaged, and
    # `unchecked` where the message carries none and rests on the language's redundancy
    confidence: str = "unchecked"

    @property
    def ok(self) -> bool:
        return not self.diagnostics


def parse(text: str, encoding: str | None = None, lexicon: str | None = None,
          reader=None) -> Analysis:
    """The analysis of a message, read under the language, lexicon and dialect releases it
    names (specification/dialects.md#naming-a-dialect-in-a-message) by a reader that holds
    what `reader` states, every release this implementation reads by default. `lexicon` is
    the release the reader takes as its own, the current one by default."""
    from . import releases
    reader = reader or releases.FULL
    refused = _unheld_lexicon(lexicon, reader)
    if refused is not None:
        return Analysis(text, encoding or "", diagnostics=[refused])
    own = data.load(lexicon)
    a = _read(text, encoding, own)
    if a.message is None:
        return a
    env = a.message.envelope
    if env.is_protocol:
        return _protocol(a, own)
    res = releases.resolve(env, reader)
    a.named = res.named
    span = env.version[0].words[0].span
    if res.lacking:
        # Normalisation reads only what the message names, so what the reader lacks of it
        # is reported, with what the reader reads, and the moves are not interpreted
        # under anything else (specification/protocol.md#versions-and-features).
        a.lacking = res.lacking
        reads = reader.reads()
        # the words the reader lacks for want of what the message names are the lack
        # this diagnostic reports, not each a word of its own
        a.diagnostics = [d for d in a.diagnostics if d.code != "d.lexer.unknown-word"]
        a.diagnostics.append(Diagnostic(
            "d.parser.version-unknown", span,
            expected=_reads_text(reads, res.lacking), detected=_lacking_text(res.lacking),
            recoverability="restate in what the reader reads"))
        return a
    if res.pairing:
        a.diagnostics.append(Diagnostic("d.parser.version-pairing", span,
                                        detected=res.pairing))
        return a
    lang = data.load(**res.load)
    if (lang.version, lang.language, lang.dialects) != (own.version, own.language,
                                                        own.dialects):
        a = _read(text, encoding, lang)
        a.named = res.named
        if a.message is None:
            return a
        env = a.message.envelope
    a.read_under = dict(res.load, protocol=res.named["protocol"])
    clashes = releases.conflicts(lang) if lang.dialect_forms else []
    if clashes:
        a.diagnostics.append(Diagnostic("d.parser.dialect-conflict", span,
                                        detected=["%s %s" % c for c in clashes]))
        return a
    _interpret(a, lang, reader)
    a.deprecated = _deprecated(a.moves, lang)
    a.formations = [{"form": w.form, "meaning": formation.compose(w.morphemes, lang)}
                    for w in a.words if w.kind == "formation"]
    a.diagnostics += _check_values(a, lang)
    return a


def _unheld_lexicon(lexicon: str | None, reader=None):
    """The diagnostic for a lexicon release `reader` does not hold, every release this
    implementation reads where it is None, which it cannot take as its own, as an option
    of `render` or `convert` it does not know is refused; None for one it holds."""
    if lexicon is None:
        return None
    from . import releases
    held = list((reader or releases.FULL).reads()["lexicon"])
    if lexicon in held:
        return None
    return Diagnostic("d.parser.unexpected-word", None, expected=held, detected=[lexicon],
                      note="a lexicon release this implementation does not hold")


def _read(text: str, encoding: str | None, lang) -> Analysis:
    tokens, diags, enc = _tokenize(text, lang, encoding)
    words, ldiags = lex(tokens, lang)
    a = Analysis(text, enc, words, diagnostics=diags + ldiags)
    message, pdiags = parse_words(words, lang)
    a.diagnostics += pdiags
    a.message = message
    if message is not None:
        a.canonical = canonical_lines(message.envelope.words, message.lines)
    return a


def _interpret(a: Analysis, lang, reader) -> None:
    """Check and normalise each move, a reader lacking a must-understand feature the move
    uses rejecting it and one lacking a may-ignore feature passing over its words
    (specification/protocol.md#versions-and-features)."""
    from . import features
    env = a.message.envelope
    sender = env.sender.text
    checker = Checker(lang, env)
    norm = Normaliser(lang)
    spell = Spell(lang)
    lines, kept = [], []
    for m in a.message.moves:
        t = from_ast_move(m)
        lacking = set()
        if reader.lacking:
            used = features.used_by_words(m.body[:-1], lang)
            lacking = {f for f in used if f in reader.lacking}
            if _reject(a, m, lang, [f for f in lacking
                                    if features.flag(lang, f) == features.MUST]):
                continue
            _pass_over(a, m, t, lang, lacking, used)
        checker_mark = len(checker.diags)
        checker.check_move(t, sender)
        n = norm.move(t)
        if reader.lacking:
            late = features.used_by_reading(t, norm.resolved, lang) & reader.lacking
            if _reject(a, m, lang, sorted(late)):
                del checker.diags[checker_mark:]
                continue
        kept.append(m)
        a.moves.append(t)
        a.classes.append(move_class(t))
        a.normal.append(n)
        a.social.append(_social(t, norm.resolved, lang))
        if norm.resolved:
            # the expansion must fit where the idiom stands
            # (specification/lexicon.md#conventional-expressions-and-idioms)
            known = {d.code for d in checker.diags}
            inner = Checker(lang, env)
            # in the move's own register, which the normal form sets aside
            inner.check_move(registers.carry(t, n), sender)
            for d in inner.diags:
                if d.code not in known:
                    d.location = t.get("_span")
                    checker.diags.append(d)
        lines.append(" ".join(spell.move(n)))
    a.message.moves = kept
    a.diagnostics += checker.diags
    a.normal_text = "".join(line + "\n" for line in lines)


def _reject(a: Analysis, m, lang, numbers: list) -> bool:
    """Reject a move for the must-understand features `numbers` the reader lacks."""
    if not numbers:
        return False
    a.diagnostics.append(Diagnostic(
        "d.parser.feature-lacking", m.words[0].span,
        detected=["feature %d" % n for n in sorted(numbers)],
        recoverability="restate without the feature"))
    a.lacking.setdefault("features", [])
    a.lacking["features"] = sorted(set(a.lacking["features"]) | set(numbers))
    return True


def _pass_over(a: Analysis, m, t: dict, lang, lacking: set, used: dict) -> None:
    """Pass over the words of the may-ignore features the reader lacks: in the head, where
    the social and textual component records them, they are dropped; standing as content,
    each is kept opaque and reported as a word the reader lacks."""
    from . import features
    may = sorted(f for f in lacking if features.flag(lang, f) == features.MAY)
    if not may:
        return
    ignored = {w.identifier for f in may for w in used[f]}
    for key in ("politeness", "diction"):
        if t.get(key) in ignored:
            t.pop(key)
    t["losses"] = [x for x in t.get("losses", []) if x not in ignored]
    for node in features._walk(t["constituents"]):
        if node.get("kind") == "word" and node.get("entry") in ignored:
            node.update(entry=None, status="unknown")
            a.diagnostics.append(Diagnostic("d.lexer.unknown-word", node.get("_span"),
                                            detected=[node["form"]],
                                            recoverability="kept opaque",
                                            note="a word of a feature this reader lacks"))
    a.ignored.append({"move": m.index, "features": may})


def _deprecated(moves: list, lang) -> list:
    """Every word the moves use that a release the message names has deprecated: still
    interpretable, and reported
    (specification/dialects.md#what-a-dialect-release-may-hold). A word inside a quotation
    or other embedded material is mentioned, not used, and is not reported."""
    from .features import _walk
    out = []
    for t in moves:
        used = [lang.items[t[k]].form for k in ("act", "politeness", "diction") if t.get(k)]
        used += [n["form"] for n in _walk(t["constituents"]) if n.get("kind") == "word"]
        for form in used:
            found = lang.deprecated.get(form)
            if found is not None:
                out.append(dict(found, form=form))
    return out


def _reads_text(reads: dict, lacking: dict) -> list:
    out = []
    for kind in ("language", "lexicon", "protocol"):
        if kind in lacking:
            out.append("%s %s" % (kind, " ".join(reads[kind])))
    if "dialects" in lacking:
        out.append("dialects " + (" ".join("%d %s" % d for d in reads["dialects"]) or "none"))
    if "features" in lacking:
        out.append("lacking features %s" % " ".join(map(str, reads["lacking"])))
    return out


def _lacking_text(lacking: dict) -> list:
    out = ["%s %s" % (kind, v) for kind in ("language", "lexicon", "protocol")
           for v in lacking.get(kind, [])]
    out += ["dialect %d %s %s" % d for d in lacking.get("dialects", [])]
    out += ["feature %d" % f for f in lacking.get("features", [])]
    return out


def _protocol(a: Analysis, lang) -> Analysis:
    """A protocol message, read whatever version it states, since every word it can hold
    is a fixed form its statement and its check values."""
    statement = a.message.statement
    if statement is not None:
        a.statement = {"kind": statement.kind, "parts": [list(p) for p in statement.parts]}
        a.diagnostics += _check_values(a, lang)
    return a


def _social(t: dict, resolved: list, lang) -> dict:
    """The social and textual component's records of a move as the analysis keeps them:
    its act word and the idioms it read, the losses it declares, its register, diction and
    politeness word, and its register-marked words
    (specification/lexicon.md#registers)."""
    return {"act": t.get("act"), "idioms": list(resolved),
            "losses": list(t.get("losses", [])), "register": registers.code(t, lang),
            "diction": t.get("diction"), "politeness": t.get("politeness"),
            "marked": registers.marked_words(t, lang)}


def _check_values(a: Analysis, lang) -> list:
    env = a.message.envelope
    out = []
    # every precision-bound move, by any route
    # (specification/grammar.md#precision-bound-moves), needs the value
    # (`inv.integrity-value-required`) and so does every protocol message (protocol 0.3)
    needs = env.is_protocol or any(precision_bound(t) for t in a.moves)
    if needs and env.integrity is None:
        out.append(Diagnostic("d.checker.integrity-value-required",
                              env.words[0].span if env.words else None,
                              expected=["an integrity check value"]))
    integrity_ok = True
    if env.integrity is not None and len(a.message.lines) > 0:
        without = canonical_lines(env.words, a.message.lines, drop=env.integrity_words)
        computed = check_value(without)
        a.confidence = "verified"
        if computed != env.integrity.integer():
            integrity_ok = False
            a.confidence = "lowered"
            out.append(Diagnostic("d.check-values.integrity-mismatch",
                                  env.integrity.words[0].span,
                                  expected=[_check_text(computed, lang)],
                                  detected=[env.integrity.text],
                                  recoverability="send again"))
    if env.semantic is not None and integrity_ok:
        computed = check_value(a.normal_text)
        if computed != env.semantic.integer():
            out.append(Diagnostic("d.check-values.semantic-mismatch",
                                  env.semantic.words[0].span,
                                  expected=[_check_text(computed, lang)],
                                  detected=[env.semantic.text]))
    return out


def _check_text(value: int, lang) -> str:
    return "%0*d" % (lang.protocol["check value width"], value)


def validate(text: str, encoding: str | None = None) -> list:
    return parse(text, encoding).diagnostics


def normalise(text: str) -> tuple:
    a = parse(text)
    return a.normal_text, a.diagnostics


def check_values(text: str) -> dict:
    a = parse(text)
    env = a.message.envelope if a.message else None
    result = {"diagnostics": a.diagnostics}
    if env is not None:
        lang = data.load()
        result["integrity"] = {
            "stated": env.integrity.text if env.integrity else None,
            "computed": _check_text(check_value(canonical_lines(
                env.words, a.message.lines, drop=env.integrity_words)), lang)}
        result["semantic"] = {"stated": env.semantic.text if env.semantic else None,
                              "computed": _check_text(check_value(a.normal_text), lang)}
    return result


def convert(text: str, to: str) -> tuple:
    """To the transliteration (canonical layout), the native digital form, the canonical
    serialisation, or a JSON export marked as a view."""
    a = parse(text)
    lang = data.load()
    if a.message is None:
        return "", a.diagnostics
    env = a.message.envelope
    lines = [env.words] + a.message.lines
    if to in ("transliteration", "canonical"):
        return a.canonical, a.diagnostics
    if to == "native":
        return to_native(lines, lang), a.diagnostics
    if to == "json":
        view = {"view": "export", "made from": a.encoding,
                "note": "an export of the analysis; never parsed as the language",
                "envelope": {"sender": env.sender.text,
                             "recipients": [r.text for r in env.recipients],
                             "communication time": env.time.text,
                             "version": [v.text for v in env.version],
                             "identifier": env.identifier.text,
                             "first entry": env.first_entry.text},
                "moves": [strip_private(t) for t in a.moves]}
        if a.statement is not None:
            view["statement"] = a.statement
        return json.dumps(view, ensure_ascii=False, indent=1) + "\n", a.diagnostics
    return "", [Diagnostic("d.parser.unexpected-word", None, expected=[
        "transliteration", "native", "canonical", "json"], detected=[to])]


def render(text: str, format: str = "svg", has_font: bool = False, form: str = "display",
           contrast: str = "normal") -> tuple:
    """The rendering of a message in a format of the writing system: SVG, PNG (bytes),
    HTML, or the terminal representation, in the display, compact or handwritten form, at
    normal or high contrast (specification/writing-system.md#the-renderings)."""
    from .drawing import FORMS
    from .render import CONTRASTS, html, png, svg, terminal
    a = parse(text)
    if form not in FORMS or contrast not in CONTRASTS:
        return "", [Diagnostic("d.parser.unexpected-word", None,
                               expected=list(FORMS) + list(CONTRASTS),
                               detected=[form, contrast])]
    if format == "svg":
        return svg(a, form=form, contrast=contrast), a.diagnostics
    if format == "png":
        return png(a, form=form, contrast=contrast), a.diagnostics
    if format == "html":
        return html(a, form=form, contrast=contrast), a.diagnostics
    if format == "terminal":
        return terminal(a, has_font), a.diagnostics
    return "", [Diagnostic("d.parser.unexpected-word", None,
                           expected=["svg", "png", "html", "terminal"], detected=[format])]


def speak(text: str) -> tuple:
    """The spoken message (specification/sounds-and-words.md#the-spoken-form): its lines
    as spoken, with their prosody, IPA and espeak-ng input, and, where espeak-ng is
    installed (the `speech` extra), the audio as WAV with the phonemes espeak-ng reports
    for each line; where it is not, `synthesiser` says why and the audio is None."""
    from .speech import spoken
    a = parse(text)
    out = {"lines": spoken(a), "audio": None, "phonemes": None, "synthesiser": "espeak-ng"}
    if a.message is not None:
        from .synthesis import SynthesiserUnavailable, synthesise
        try:
            out["audio"], out["phonemes"] = synthesise(a)
        except SynthesiserUnavailable as e:
            out["synthesiser"] = "unavailable: %s" % e
    return out, a.diagnostics


def sound(text: str) -> tuple:
    """The measure and echoes of each move of a message."""
    from .verse import sound as verse_sound
    a = parse(text)
    return verse_sound(a), a.diagnostics


def gloss(text: str) -> tuple:
    """The five lines for each move."""
    from .generator import gloss_lines
    a = parse(text)
    return gloss_lines(a), a.diagnostics


def analyze(text: str) -> dict:
    """The analysis, with every stage's output, and its measurements: for each move its
    derived times, the entries and messages it depends on, and what its speaker answers
    for and mentions through its figures (specification/meaning.md#figures)."""
    from .figures import answers_for, sources
    from .temporal import derived
    from .view import dependencies
    a = parse(text)
    comm = None
    if a.message is not None:
        try:
            comm = float(a.message.envelope.time.text)
        except ValueError:
            comm = None
    lang = data.load()
    return {"analysis": a, "measurements": {"words": len(a.words), "moves": len(a.moves),
                                            "diagnostics": len(a.diagnostics)},
            "times": [derived(t, lang, comm) for t in a.moves],
            "dependencies": [[list(d) for d in dependencies(t)] for t in a.moves],
            "answers for": [answers_for(n["constituents"], lang) for n in a.normal],
            "mentions": [sources(n["constituents"]) for n in a.normal]}


def discourse(texts: list, participant: str, now: float | None = None) -> dict:
    """One participant's view of an exchange
    (specification/discourse.md#how-a-participant-receives-a-message): the messages it
    received, in the order received, applied to its record, with what the record derives:
    the threads, the open issues, the action items, the positions with their
    corroboration, the common ground under the conventions the participants stated, the
    negotiations and the conflicts."""
    from .coordination import structure
    from .view import View
    view = View(str(participant))
    diagnostics = []
    for text in texts:
        diagnostics += view.hear(text)
    return {"view": view, "structure": structure(view, now), "diagnostics": diagnostics}


def translate(text: str, to: str = "english", record: dict | None = None) -> tuple:
    """The message in register `to`, by its code or its name, with the changes each move
    makes to the social and textual component declared
    (specification/lexicon.md#registers); or, where `to` is English, the explanation, a
    view, which declares nothing since it is not the language. `record` maps the handle of
    an entry a move names in place of restating it to the entry's content and recipients,
    for a target register that restates it. Returns the text, the changes and the
    diagnostics."""
    from .english import English
    a = parse(text)
    if to.lower() != "english":
        from .conversion import convert as convert_register
        out = convert_register(a, to, record)
        return out.text, out.changes, out.diagnostics
    if a.message is None:
        return "", [], a.diagnostics
    e = English(sender=a.message.envelope.sender.text)
    lines = [e.move(n) for n in a.normal]
    lines.append("(an explanation made by this receiver; a view, not the language)")
    return "".join(line + "\n" for line in lines), [], a.diagnostics


def generate(meaning, register: str | None = None, mode: str | None = None,
             holdings=None, diction: str | None = None,
             envelope: Envelope = FIXED_ENVELOPE) -> dict:
    """The six outputs of the generator
    (specification/notation.md#what-the-generator-writes) from a semantic representation:
    move trees, or a text in the literal semantic notation; `holdings`, an
    `economy.Holdings`, says what the hearer holds Each message is written under
    `envelope`, from participant 1 to participant 2 at a fixed time where none is
    given."""
    from .generator import Generator
    return Generator().generate(meaning, register=register, mode=mode, holdings=holdings,
                                diction=diction, envelope=envelope)


def write(meaning, envelope: Envelope, register: str | None = None,
          mode: str | None = None, holdings=None, diction: str | None = None,
          signer=None) -> tuple:
    """The message a writer sends, written from `meaning` (move trees, or a text in the
    notation) under `envelope`, in `register` and `mode` as `generate` writes its
    transliteration, and signed where `signer`, a (scheme, sign) pair, is given; with the
    diagnostics of reading it back, which a writer checks before sending it, since the
    generator writes what the notation states and the reader judges it."""
    from .generator import Generator
    text = Generator().write(meaning, envelope, register=register, mode=mode,
                             holdings=holdings, diction=diction, signer=signer)
    return text, parse(text).diagnostics


def state(kind: str, sender: int, recipient: int, time, channels=(), entries=(),
          about: str | None = None, signer=None) -> tuple:
    """A protocol message from `sender` to `recipient`
    (specification/protocol.md#protocol-messages), with the diagnostics of reading it
    back. `understands` states the releases this implementation reads and the features it
    lacks, and takes nothing more; `lacks` names the received message `about`, which must
    be the recipient's, with what of it this reader lacks; `holds` states, for each
    channel in `channels`, a pair of its recipients and the serials held; `send-again` and
    `not-held` name such channels' serials and the numbers of entries in `entries`."""
    from .statements import write_statement
    text = write_statement(kind, sender, recipient, time, channels, entries, about, signer)
    return text, parse(text).diagnostics


def tokenize(text: str, lexicon: str | None = None) -> tuple:
    """The words of a text with their locations, under the lexicon release `lexicon`, the
    current one where it is None."""
    refused = _unheld_lexicon(lexicon)
    if refused is not None:
        return [], [refused]
    lang = data.load(lexicon)
    tokens, diags, enc = _tokenize(text, lang)
    words, ldiags = lex(tokens, lang)
    return words, diags + ldiags


def lookup(term: str) -> list:
    """The words, members and morphemes that match a form, an identifier or English words,
    and the terms of the dialects that match one (specification/dialects.md#terms)."""
    lang = data.load()
    term_l = term.lower()
    out = []
    for item in lang.items.values():
        if term_l in (item.form, item.identifier.lower()) or term_l == item.name.lower() \
                or term_l in item.gloss.lower().replace("-", " ").split():
            out.append(item)
    for d in data.dialects().values():
        for t in d["terms"]:
            if term_l in (t["orthographic form"], t["machine identifier"].lower(),
                          t["term"].lower()):
                out.append(data.Item("jargon", t["machine identifier"], t["orthographic form"],
                                     t["term"].upper().replace(" ", "-"), name=t["term"],
                                     sort=t["sort"], category="jargon"))
        # the compressed forms of a dialect's newest release
        # (specification/dialects.md#compressed-forms)
        for f in d.get("forms", []):
            if term_l in (f["orthographic form"], f["machine identifier"].lower(),
                          f["term"].lower()):
                out.append(data.Item("dialect", f["machine identifier"], f["orthographic form"],
                                     f["key"].upper().replace(" ", "-"), name=f["key"],
                                     sort=f["sort"], category="dialect form"))
    return out


def version() -> dict:
    """The versions this implementation understands: its own language, lexicon and
    protocol releases, its newest release of each dialect by name, and every release of
    each kind it reads (specification/dialects.md#naming-a-dialect-in-a-message), which a
    statement of `UNDERSTANDS` lists."""
    from . import releases
    lang = data.load()
    reads = releases.implementation()
    return {"language": lang.grammar["version"], "lexicon": lang.release["version"],
            "protocol": lang.protocol["version"],
            "dialects": {name: d["version"] for name, d in data.dialects().items()},
            "reads": {"language": list(reads["language"]), "lexicon": list(reads["lexicon"]),
                      "protocol": list(reads["protocol"]),
                      "dialects": [list(d) for d in reads["dialects"]]}}
