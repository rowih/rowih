"""What the server of the Model Context Protocol offers
(specification/conformance.md#the-server): one tool for each function of the API, which
checks its arguments against the tool's schema, calls the function and gives its result as
structured data, adding no behaviour of its own; and the resources a writer reads, the
grammar summary, the lexicon listing and the chapters of the reference specification."""
from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import dataclass, field
from typing import Callable

from . import api, data, structured, summary
from .diagnostics import InputError
from .generator import MODES
from .writer import FIXED_ENVELOPE, Envelope

# The largest text a tool reads, in characters, a bound this server sets so that no one
# argument can hold the process. The language bounds a message's words, not its
# characters, since declared data is one word of any length; this bound admits about
# 160 kilobytes of declared data, where the longest message of the corpus has 1,502
# characters.
MAX_TEXT = 262144
MAX_TEXTS = 256
MAX_TERM = 200
# the time a listed tool or resource stays fresh: the process serves one release, and a
# new release is a new process
TTL_MS = 3600000


class ToolInputError(InputError):
    """An argument that does not meet the tool's schema."""


@dataclass
class Result:
    structured: object
    content: list = field(default_factory=list)   # blocks beyond the JSON text
    is_error: bool = False


@dataclass(frozen=True)
class Tool:
    name: str
    title: str
    description: str
    schema: dict
    run: Callable


TEXT = {"type": "string", "maxLength": MAX_TEXT,
        "description": "a message of the language, in the transliteration or in the native "
                       "digital form"}
NOTATION = {"type": "string", "maxLength": MAX_TEXT,
            "description": "the moves in the notation, each (move ...)"}
PARTICIPANT = {"type": "integer", "minimum": 0}


def _object(properties: dict, required=()) -> dict:
    return {"type": "object", "properties": properties, "required": list(required),
            "additionalProperties": False}


def _writing_properties(lang) -> dict:
    registers = sorted(lang.registers) + sorted(r["name"] for r in lang.registers.values())
    dictions = sorted(e["key"] for e in lang.entries.values()
                      if e["grammatical category"] == "diction")
    from .releases import implementation
    return {
        "notation": NOTATION,
        "register": {"type": "string", "enum": registers,
                     "description": "the register, by its code or its name; each move's own "
                                    "where omitted"},
        "mode": {"type": "string", "enum": list(MODES)},
        "diction": {"type": "string", "enum": dictions},
        "hearer": {"type": "string", "enum": list(implementation()["lexicon"]),
                   "description": "the lexicon release the hearer has stated it holds, "
                                  "which admits compression"},
        "sender": dict(PARTICIPANT, description="the sender's participant number"),
        "recipients": {"type": "array", "items": PARTICIPANT, "minItems": 1, "maxItems": 64,
                       "description": "the recipients' participant numbers"},
        "time": {"type": ["string", "integer"],
                 "description": "the communication time, in seconds since "
                                "1970-01-01T00:00:00Z, as an integer or a decimal numeral"},
        "identifier": dict(PARTICIPANT, description="the message's serial on its channel, "
                                                    "from 1; 1 where omitted"),
        "first_entry": dict(PARTICIPANT, description="the number of the entry the first "
                                                     "move adds; 1 where omitted"),
        "dialects": {"type": "array", "maxItems": 16,
                     "items": {"type": "array", "prefixItems": [
                         PARTICIPANT, {"type": "string"}], "minItems": 2, "maxItems": 2},
                     "description": "the dialect releases the message names, each "
                                    "[number, version]"},
        "semantic": {"type": "boolean", "description": "write the semantic check value"},
    }


class Offer:
    """The tools and resources, built once over the loaded language; `clock` gives the
    communication time a written message takes where its writer states none."""

    def __init__(self, clock: Callable[[], float] = time.time):
        self.lang = data.load()
        self.clock = clock
        self.tools = self._tools()
        self.by_name = {t.name: t for t in self.tools}
        self.resources = self._resources()

    # ------------------------------------------------------------------ tools
    def _tools(self) -> list:
        # one declarative entry for each tool, which is why the method is long: splitting
        # the table would scatter what a host lists in one place
        w = _writing_properties(self.lang)
        envelope = {k: w[k] for k in ("sender", "recipients", "time", "identifier",
                                      "first_entry", "dialects", "semantic")}
        options = {k: w[k] for k in ("register", "mode", "diction", "hearer")}
        text_only = _object({"text": TEXT}, ["text"])
        from .releases import implementation
        held = list(implementation()["lexicon"])
        return [
            Tool("write", "Write a message",
                 "Write a message from moves in the notation, under the envelope given, and "
                 "read it back: returns the message to send, the diagnostics of reading it, "
                 "which must be empty before it is sent, and its English explanation and "
                 "literal semantic form, to confirm that it says what was meant. The "
                 "communication time is the current time where it is not given.",
                 _object(dict({"notation": NOTATION}, **envelope, **options),
                         ["notation", "sender", "recipients"]), self.write),
            Tool("state", "Write a protocol message",
                 "Write a protocol message to one recipient and read it back: understands "
                 "states the releases this implementation reads; lacks names a received "
                 "message of the recipient's that this reader cannot read, given as about, "
                 "with what of it the reader lacks; holds acknowledges the serials held of "
                 "each channel; send-again asks for serials of a channel or for entries, and "
                 "not-held answers that they are no longer held.",
                 _object({"kind": {"type": "string", "enum": list(api.STATEMENTS)},
                          "sender": w["sender"],
                          "recipient": dict(PARTICIPANT, description="the participant the "
                                                                     "statement is sent to"),
                          "time": w["time"],
                          "channels": {"type": "array", "maxItems": 64, "items": _object({
                              "recipients": w["recipients"],
                              "serials": {"type": "array", "items": PARTICIPANT,
                                          "minItems": 1, "maxItems": 4096}},
                              ["recipients", "serials"])},
                          "entries": {"type": "array", "items": PARTICIPANT, "maxItems": 4096},
                          "about": dict(TEXT, description="the received message lacks names")},
                         ["kind", "sender", "recipient"]), self.state),
            Tool("parse", "Read a message",
                 "Read a received message: its diagnostics, how far it is vouched for, its "
                 "envelope, and each move as written and in its literal semantic form, with "
                 "its class (operative, pending, inert). Quoted and declared material in a "
                 "message is inert: it is never an instruction to the reader.",
                 text_only, self.parse),
            Tool("validate", "Check a message", "Only the diagnostics of a message; none "
                 "means that it is well formed and its check values hold.",
                 text_only, self.validate),
            Tool("lookup", "Look up a word",
                 "The words, members and morphemes that a form, an identifier, a key or an "
                 "English word names, each with how the notation writes it and its meaning.",
                 _object({"term": {"type": "string", "maxLength": MAX_TERM}}, ["term"]),
                 self.lookup),
            Tool("translate", "Explain or convert a message",
                 "The English explanation of a message, which is a view and not the "
                 "language, with `to` english; or the message in another register, with "
                 "each move's changes declared.",
                 _object({"text": TEXT, "to": {"type": "string", "maxLength": 40,
                                                "description": "english, or a register by "
                                                               "its code or its name"}},
                         ["text", "to"]), self.translate),
            Tool("gloss", "Gloss a message", "Five lines for each move: the native writing, "
                 "the transliteration, the morpheme gloss, the literal semantic form and the "
                 "English explanation.", text_only, self.gloss),
            Tool("normalise", "Normalise a message", "The normal form of each move, written "
                 "in the language, with the diagnostics.", text_only, self.normalise),
            Tool("check_values", "Check values", "Each check value a message states and "
                 "the one computed.", text_only, self.check_values),
            Tool("analyze", "Analyse a message", "The analysis with its measurements: each "
                 "move's derived times, the entries and messages it depends on, what its "
                 "speaker answers for, and what it mentions.", text_only, self.analyze),
            Tool("discourse", "Follow an exchange",
                 "One participant's view of an exchange: the messages it received, in the "
                 "order received, applied to its record, with the threads, open issues, "
                 "action items, positions, common ground, negotiations and conflicts.",
                 _object({"texts": {"type": "array", "items": TEXT, "minItems": 1,
                                    "maxItems": MAX_TEXTS},
                          "participant": {"type": "string", "maxLength": 20},
                          "now": {"type": "number", "description": "the time the view is "
                                                                   "taken at, for deadlines"}},
                         ["texts", "participant"]), self.discourse),
            Tool("generate", "Generate every output",
                 "The six outputs of the generator for moves in the notation: the canonical, "
                 "standard and compressed forms, the gloss, the transliteration and its "
                 "native rendering, under the fixed envelope unless one is given. To write "
                 "a message to send, use write.",
                 _object(dict({"notation": NOTATION}, **envelope, **options), ["notation"]),
                 self.generate),
            Tool("convert", "Convert a message", "The message as the transliteration, its "
                 "canonical serialisation, the native digital form, or a JSON export.",
                 _object({"text": TEXT, "to": {"type": "string", "enum": [
                     "transliteration", "native", "canonical", "json"]}}, ["text", "to"]),
                 self.convert),
            Tool("render", "Render a message",
                 "The message in the native writing system, as SVG, PNG, HTML or text for a "
                 "terminal, in the display, compact or handwritten form.",
                 _object({"text": TEXT,
                          "format": {"type": "string", "enum": ["svg", "png", "html",
                                                                "terminal"]},
                          "form": {"type": "string", "enum": ["display", "compact",
                                                              "handwritten"]},
                          "contrast": {"type": "string", "enum": ["normal", "high"]},
                          "has_font": {"type": "boolean"}}, ["text", "format"]),
                 self.render),
            Tool("speak", "Speak a message", "Each line's prosody, IPA and synthesiser "
                 "input, and the audio where eSpeak NG is installed.", text_only, self.speak),
            Tool("sound", "Measure a message's sound", "The metre and echoes of each move.",
                 text_only, self.sound),
            Tool("tokenize", "Tokenize a message", "The words of a message with their "
                 "locations.", _object({"text": TEXT, "lexicon": {"type": "string",
                                                                  "enum": held}},
                                       ["text"]), self.tokenize),
            Tool("version", "Releases", "The releases this implementation is and reads.",
                 {"type": "object", "additionalProperties": False}, self.version),
        ]

    def call(self, name: str, arguments: dict) -> Result:
        """Run tool `name`; an argument that does not meet its schema, or a writer's input
        that cannot be written, is a tool error the caller can correct."""
        tool = self.by_name[name]
        try:
            check(tool.schema, arguments, "arguments")
            return tool.run(arguments)
        except InputError as e:
            return Result({"error": "%s: %s" % (type(e).__name__, e)}, is_error=True)

    def _envelope(self, args: dict, fixed: bool) -> Envelope:
        if fixed and "sender" not in args and "recipients" not in args and "time" not in args:
            base = FIXED_ENVELOPE
        else:
            base = Envelope(args.get("sender", FIXED_ENVELOPE.sender),
                            tuple(args.get("recipients", FIXED_ENVELOPE.recipients)),
                            args.get("time", FIXED_ENVELOPE.time if fixed
                                     else str(int(self.clock()))))
        return Envelope(base.sender, base.recipients, base.time,
                        identifier=args.get("identifier", 1),
                        first_entry=args.get("first_entry", 1),
                        dialects=tuple(tuple(d) for d in args.get("dialects", [])),
                        semantic=args.get("semantic", False))

    def _holdings(self, args: dict):
        from .economy import Holdings
        return Holdings(lexicon=(args["hearer"],)) if "hearer" in args else None

    def write(self, args: dict) -> Result:
        text, diags = api.write(args["notation"], self._envelope(args, fixed=False),
                                register=args.get("register"), mode=args.get("mode"),
                                holdings=self._holdings(args), diction=args.get("diction"))
        a = api.parse(text)
        explanation = api.translate(text, "english")[0]
        return Result({"message": text, "ok": not diags,
                       "diagnostics": structured.diagnostics(diags),
                       "explanation": explanation,
                       "moves": structured.analysis(a, _language(a))["moves"],
                       "envelope": structured.envelope(a.message.envelope)
                       if a.message is not None else None})

    def state(self, args: dict) -> Result:
        text, diags = api.state(args["kind"], args["sender"], args["recipient"],
                                args.get("time", str(int(self.clock()))),
                                channels=[(c["recipients"], c["serials"])
                                          for c in args.get("channels", [])],
                                entries=args.get("entries", []), about=args.get("about"))
        a = api.parse(text)
        return Result(_plain({"message": text, "ok": not diags,
                              "diagnostics": structured.diagnostics(diags),
                              "statement": a.statement}))

    def generate(self, args: dict) -> Result:
        out = api.generate(args["notation"], register=args.get("register"),
                           mode=args.get("mode"), holdings=self._holdings(args),
                           diction=args.get("diction"),
                           envelope=self._envelope(args, fixed=True))
        return Result(out)

    def parse(self, args: dict) -> Result:
        a = api.parse(args["text"])
        return Result(structured.analysis(a, _language(a)))

    def validate(self, args: dict) -> Result:
        diags = api.validate(args["text"])
        return Result({"ok": not diags, "diagnostics": structured.diagnostics(diags)})

    def lookup(self, args: dict) -> Result:
        return Result({"items": [structured.item(it, self.lang)
                                 for it in api.lookup(args["term"])]})

    def translate(self, args: dict) -> Result:
        text, changes, diags = api.translate(args["text"], args["to"])
        return Result({"text": text, "changes": changes,
                       "diagnostics": structured.diagnostics(diags)})

    def gloss(self, args: dict) -> Result:
        out, diags = api.gloss(args["text"])
        return Result({"gloss": out, "diagnostics": structured.diagnostics(diags)})

    def normalise(self, args: dict) -> Result:
        out, diags = api.normalise(args["text"])
        return Result({"normal text": out, "diagnostics": structured.diagnostics(diags)})

    def check_values(self, args: dict) -> Result:
        out = api.check_values(args["text"])
        out["diagnostics"] = structured.diagnostics(out["diagnostics"])
        return Result(out)

    def analyze(self, args: dict) -> Result:
        out = api.analyze(args["text"])
        a = out.pop("analysis")
        out["analysis"] = structured.analysis(a, _language(a))
        return Result(_plain(out))

    def discourse(self, args: dict) -> Result:
        out = api.discourse(args["texts"], args["participant"], args.get("now"))
        return Result(_plain({"structure": out["structure"],
                              "diagnostics": structured.diagnostics(out["diagnostics"])}))

    def convert(self, args: dict) -> Result:
        out, diags = api.convert(args["text"], args["to"])
        return Result({"text": out, "diagnostics": structured.diagnostics(diags)})

    def render(self, args: dict) -> Result:
        fmt = args["format"]
        out, diags = api.render(args["text"], fmt, has_font=args.get("has_font", False),
                                form=args.get("form", "display"),
                                contrast=args.get("contrast", "normal"))
        result = {"format": fmt, "diagnostics": structured.diagnostics(diags)}
        if fmt == "png":
            result["bytes"] = len(out)
            image = [{"type": "image", "mimeType": "image/png",
                      "data": base64.b64encode(out).decode("ascii")}] if out else []
            return Result(result, image)
        result["text"] = out
        return Result(result)

    def speak(self, args: dict) -> Result:
        out, diags = api.speak(args["text"])
        audio = out.pop("audio")
        out["diagnostics"] = structured.diagnostics(diags)
        blocks = [{"type": "audio", "mimeType": "audio/wav",
                   "data": base64.b64encode(audio).decode("ascii")}] if audio else []
        return Result(_plain(out), blocks)

    def sound(self, args: dict) -> Result:
        out, diags = api.sound(args["text"])
        return Result(_plain({"sound": out, "diagnostics": structured.diagnostics(diags)}))

    def tokenize(self, args: dict) -> Result:
        words, diags = api.tokenize(args["text"], args.get("lexicon"))
        return Result({"words": [structured.word(w) for w in words],
                       "diagnostics": structured.diagnostics(diags)})

    def version(self, args: dict) -> Result:
        from . import __version__
        return Result(dict(api.version(), package=__version__))

    # -------------------------------------------------------------- resources
    def _resources(self) -> dict:
        """Each resource by its URI: (name, title, description, MIME type, the function
        that gives its text)."""
        out = {
            "rowih://grammar": ("grammar", "The grammar summary",
                                "Every grammatical class with its members as the notation "
                                "writes them, the act words and the function words.",
                                "text/markdown", lambda: summary.grammar(self.lang)),
            "rowih://lexicon": ("lexicon", "The lexicon listing",
                                "Every word a writer can name, with how the notation writes "
                                "it, its form and its meaning.",
                                "text/markdown", lambda: summary.lexicon(self.lang)),
        }
        root = os.path.join(data._data_root(), "specification")
        if os.path.isdir(root):
            for name in sorted(os.listdir(root)):
                if not name.endswith(".md"):
                    continue
                chapter = name[:-3]
                path = os.path.join(root, name)
                title = _first_heading(path)
                out["rowih://specification/%s" % chapter] = (
                    "specification/%s" % chapter, title,
                    "A chapter of the reference specification of the language.",
                    "text/markdown", lambda path=path: _read_text(path))
        return out


def _language(a):
    """The language an analysis was read under."""
    under = a.read_under or {}
    return data.load(under.get("version"), under.get("language"), under.get("dialects", ()))


def _plain(value):
    """A result as JSON carries it: tuples as lists, keys as strings."""
    return json.loads(json.dumps(value, ensure_ascii=False, default=list))


def _first_heading(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("# "):
                return line[2:].strip()
    return os.path.basename(path)


def _read_text(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------- the schemas
_TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool,
          "array": list, "object": dict}


def _is(value, kind: str) -> bool:
    if kind in ("integer", "number") and isinstance(value, bool):
        return False
    if kind == "number" and isinstance(value, float):
        return value == value and value not in (float("inf"), float("-inf"))
    return isinstance(value, _TYPES[kind])


def check(schema: dict, value, where: str) -> None:
    """Check `value` against `schema`, in the subset of JSON Schema 2020-12 the tools'
    schemas use: type, enum, minimum, maxLength, minItems, maxItems, items, prefixItems,
    properties, required and additionalProperties."""
    kinds = schema.get("type")
    if kinds is not None:
        kinds = [kinds] if isinstance(kinds, str) else kinds
        if not any(_is(value, k) for k in kinds):
            raise ToolInputError("%s is %s, not %s" % (where, " or ".join(kinds),
                                                       json.dumps(value)[:60]))
    if "enum" in schema and value not in schema["enum"]:
        raise ToolInputError("%s is one of %s, not %s" % (
            where, ", ".join(json.dumps(v) for v in schema["enum"]), json.dumps(value)[:60]))
    if "minimum" in schema and value < schema["minimum"]:
        raise ToolInputError("%s is at least %s" % (where, schema["minimum"]))
    if "maxLength" in schema and len(value) > schema["maxLength"]:
        raise ToolInputError("%s is at most %d characters" % (where, schema["maxLength"]))
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise ToolInputError("%s has at least %d items" % (where, schema["minItems"]))
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ToolInputError("%s has at most %d items" % (where, schema["maxItems"]))
        for i, item in enumerate(value):
            prefix = schema.get("prefixItems", [])
            sub = prefix[i] if i < len(prefix) else schema.get("items")
            if sub is not None:
                check(sub, item, "%s[%d]" % (where, i))
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                raise ToolInputError("%s needs %s" % (where, key))
        for key, item in value.items():
            if key in properties:
                check(properties[key], item, "%s.%s" % (where, key))
            elif schema.get("additionalProperties") is False:
                raise ToolInputError("%s has no argument %s; its arguments are %s" % (
                    where, key, ", ".join(properties) or "none"))
