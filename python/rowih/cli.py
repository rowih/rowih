"""The command-line interface (specification/conformance.md#the-command-line). Each
command reads standard input where no file is given. Exit status: 0 when the input drew
no diagnostic, 1 when it drew one, 2 when the command was used wrongly, which includes a
writer's input that cannot be written: notation that does not read, envelope values or a
statement's parts that cannot be written, or a register, mode or diction the language
does not have."""
from __future__ import annotations

import argparse
import json
import sys
import time

from . import api, render
from .diagnostics import InputError
from .generator import Generator, MODES, gloss_lines
from .writer import FIXED_ENVELOPE, Envelope


def _read(path):
    if path and path != "-":
        with open(path, encoding="utf-8") as f:
            return f.read()
    return sys.stdin.read()


def _report(diags) -> int:
    for d in diags:
        print(d.as_text(), file=sys.stderr)
    return 1 if diags else 0


def _writer_options(p, envelope_required: bool) -> None:
    """The options of a command that writes: the register, mode, diction and hearer, and
    the envelope's values, which `write` requires and `generate` takes from the fixed
    envelope where they are not given."""
    p.add_argument("--register", default=None, help="a register by its code or its name")
    p.add_argument("--mode", default=None, choices=MODES)
    p.add_argument("--diction", default=None)
    p.add_argument("--hearer", help="the lexicon version the hearer has stated it holds")
    fixed = FIXED_ENVELOPE
    p.add_argument("--sender", type=int, required=envelope_required,
                   default=None if envelope_required else fixed.sender,
                   help="the sender's participant number")
    p.add_argument("--recipients", type=int, nargs="+", required=envelope_required,
                   default=None if envelope_required else list(fixed.recipients),
                   help="the recipients' participant numbers")
    p.add_argument("--time", default=None if envelope_required else fixed.time,
                   help="the communication time, in seconds since 1970-01-01T00:00:00Z" +
                   ("; the current time where it is not given" if envelope_required else ""))
    p.add_argument("--identifier", type=int, default=1,
                   help="the message's serial on its channel, from 1")
    p.add_argument("--first-entry", type=int, default=1,
                   help="the number of the entry the message's first move adds")
    p.add_argument("--dialect", nargs=2, action="append", default=[],
                   metavar=("NUMBER", "VERSION"), help="a dialect release the message names")
    p.add_argument("--semantic", action="store_true",
                   help="write the semantic check value")


def _envelope(args) -> Envelope:
    dialects = []
    for number, version in args.dialect:
        if not number.isdigit():
            raise api.EnvelopeError("a dialect's number is a whole number, not %r" % number)
        dialects.append((int(number), version))
    when = args.time if args.time is not None else str(int(time.time()))
    return Envelope(args.sender, tuple(args.recipients), when, identifier=args.identifier,
                    first_entry=args.first_entry, dialects=tuple(dialects),
                    semantic=args.semantic)


def _holdings(args):
    from .economy import Holdings
    return Holdings(lexicon=(args.hearer,)) if args.hearer else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="rowih")
    sub = ap.add_subparsers(dest="command")
    from .releases import implementation
    held = list(implementation()["lexicon"])
    for name in ("parse", "gloss", "tokenize", "analyze", "validate"):
        p = sub.add_parser(name)
        p.add_argument("file", nargs="?")
        if name in ("parse", "tokenize"):
            p.add_argument("--lexicon", default=None, choices=held,
                           help="the lexicon release the reader takes as its own")
    p = sub.add_parser("generate")
    p.add_argument("file")
    _writer_options(p, envelope_required=False)
    p = sub.add_parser("write", help="write a message from the notation and check it")
    p.add_argument("file", nargs="?")
    _writer_options(p, envelope_required=True)
    p = sub.add_parser("state", help="write a protocol message and check it")
    p.add_argument("kind", choices=api.STATEMENTS)
    p.add_argument("--sender", type=int, required=True)
    p.add_argument("--recipient", type=int, required=True)
    p.add_argument("--time", default=None, help="the communication time; the current time "
                                                "where it is not given")
    p.add_argument("--channel", type=int, nargs="+", action="append", default=[],
                   metavar="RECIPIENT", help="a channel's recipients, each --channel paired "
                                             "with the --serials that follows it")
    p.add_argument("--serials", type=int, nargs="+", action="append", default=[])
    p.add_argument("--entries", type=int, nargs="+", default=[])
    p.add_argument("--about", help="the file of the received message that lacks names")
    sub.add_parser("serve", help="serve the Model Context Protocol on standard input "
                                 "and output")
    p = sub.add_parser("summary", help="print the grammar summary or the lexicon listing")
    p.add_argument("which", choices=["grammar", "lexicon"])
    p = sub.add_parser("translate")
    p.add_argument("file", nargs="?")
    p.add_argument("--to", required=True)
    p = sub.add_parser("render")
    p.add_argument("file", nargs="?")
    p.add_argument("--format", required=True, choices=["svg", "png", "terminal", "html"])
    p.add_argument("--form", default="display", choices=["display", "compact", "handwritten"])
    p.add_argument("--contrast", default="normal", choices=["normal", "high"])
    p.add_argument("-o", "--output", help="the file to write; required for PNG")
    p = sub.add_parser("speak")
    p.add_argument("file", nargs="?")
    p.add_argument("-o", "--output", help="a WAV file to write, which needs espeak-ng")
    p = sub.add_parser("lookup")
    p.add_argument("term")
    p = sub.add_parser("convert")
    p.add_argument("file", nargs="?")
    p.add_argument("--to", required=True,
                   choices=["transliteration", "native", "canonical", "json"])
    sub.add_parser("version")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    if args.command is None:
        ap.print_usage(sys.stderr)
        return 2

    if args.command == "version":
        print(json.dumps(api.version()))
        return 0
    if args.command == "lookup":
        items = api.lookup(args.term)
        for it in items:
            print("%s\t%s\t%s" % (it.identifier, it.form, it.gloss))
        return 0 if items else 1
    if args.command == "serve":
        from .server import serve
        return serve()
    if args.command == "summary":
        from . import data, summary
        lang = data.load()
        sys.stdout.write(summary.grammar(lang) if args.which == "grammar"
                         else summary.lexicon(lang))
        return 0
    if args.command in ("generate", "write"):
        return _write(args)
    if args.command == "state":
        return _state(args)
    text = _read(args.file)
    if args.command == "tokenize":
        words, diags = api.tokenize(text, args.lexicon)
        for w in words:
            print("%s\t%s\t%s" % (w.span.as_text(), w.form, w.identifier or w.kind))
        return _report(diags)
    if args.command == "convert":
        out, diags = api.convert(text, args.to)
        sys.stdout.write(out)
        return _report(diags)
    if args.command == "speak":
        out, diags = api.speak(text)
        for line in out["lines"]:
            print("%s\t%s\t%s" % (line["prosody"], line["ipa"], line["espeak"]))
        if args.output and out["lines"]:
            if out["audio"] is None:
                print("speak --output needs espeak-ng (the speech extra): %s"
                      % out["synthesiser"], file=sys.stderr)
                return 2
            with open(args.output, "wb") as f:
                f.write(out["audio"])
        return _report(diags)
    a = api.parse(text, lexicon=getattr(args, "lexicon", None))
    if args.command == "validate":
        return _report(a.diagnostics)
    if args.command == "parse":
        sys.stdout.write(a.canonical)
        return _report(a.diagnostics)
    if args.command == "gloss":
        print(gloss_lines(a))
        return _report(a.diagnostics)
    if args.command == "analyze":
        print("encoding: %s" % a.encoding)
        print("words: %d" % len(a.words))
        for i, c in enumerate(a.classes, 1):
            print("move %d: %s" % (i, ", ".join(k for k, v in c.items() if v)))
        print("normal form:")
        sys.stdout.write(a.normal_text)
        return _report(a.diagnostics)
    if args.command == "translate":
        out, changes, diags = api.translate(text, args.to)
        sys.stdout.write(out)
        for i, changed in enumerate(changes, 1):
            print("move %d changes: %s" % (i, ", ".join(changed) or "nothing"),
                  file=sys.stderr)
        return _report(diags)
    if args.command == "render":
        if args.format == "png":
            if not args.output:
                print("render --format png needs --output FILE", file=sys.stderr)
                return 2
            with open(args.output, "wb") as f:
                f.write(render.png(a, form=args.form, contrast=args.contrast))
            return _report(a.diagnostics)
        if args.format == "terminal":
            out = render.terminal(a)
        else:
            fn = render.svg if args.format == "svg" else render.html
            out = fn(a, form=args.form, contrast=args.contrast)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(out)
        else:
            sys.stdout.write(out)
        return _report(a.diagnostics)
    return 2


def _write(args) -> int:
    """`generate` prints the six outputs; `write` prints the one message to send, and the
    diagnostics of reading it back, which a writer checks before sending it."""
    try:
        envelope = _envelope(args)
        if args.command == "generate":
            out = Generator().generate(_read(args.file), register=args.register,
                                       mode=args.mode, holdings=_holdings(args),
                                       diction=args.diction, envelope=envelope)
        else:
            text, diags = api.write(_read(args.file), envelope, register=args.register,
                                    mode=args.mode, holdings=_holdings(args),
                                    diction=args.diction)
    except InputError as e:
        print("%s: %s" % (type(e).__name__, e), file=sys.stderr)
        return 2
    if args.command == "write":
        sys.stdout.write(text)
        return _report(diags)
    for key in ("canonical form", "standard form", "compressed form",
                "human-readable gloss", "transliteration", "native-script rendering"):
        print("== %s" % key)
        print(out[key])
    return 0


def _state(args) -> int:
    if len(args.channel) != len(args.serials):
        print("each --channel is paired with one --serials", file=sys.stderr)
        return 2
    try:
        text, diags = api.state(args.kind, args.sender, args.recipient,
                                args.time if args.time is not None else str(int(time.time())),
                                channels=list(zip(args.channel, args.serials, strict=True)),
                                entries=args.entries,
                                about=_read(args.about) if args.about else None)
    except InputError as e:
        print("%s: %s" % (type(e).__name__, e), file=sys.stderr)
        return 2
    sys.stdout.write(text)
    return _report(diags)


if __name__ == "__main__":
    sys.exit(main())
