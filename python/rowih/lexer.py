"""The tokenizer, the lexer and the morphological analyzer
(specification/notation.md#tokens): bytes to symbols and separators, symbols to words, and
content words to their entries by the lexicon's uniquely decodable code."""
from __future__ import annotations

import base64
from dataclasses import dataclass, field

from .data import Item, Language
from .diagnostics import Diagnostic, Span

SEPARATORS = " \t\n\r"
PAYLOAD_CHARS = set("abcdefghijklmnopqrstuvwxyz234567")
LINKER = "i"
SUFFIX_FIRST = "aeou"


@dataclass
class Token:
    text: str            # the symbols as letters, or the raw characters of a payload
    raw: str
    span: Span
    native: bool = False
    ascii_letters: bool = False


@dataclass
class Word:
    form: str
    span: Span
    item: Item | None = None
    kind: str = "word"                 # word, formation, unknown, payload
    morphemes: list = field(default_factory=list)
    payload: bytes = b""

    @property
    def identifier(self) -> str:
        return self.item.identifier if self.item else ""

    @property
    def class_id(self) -> str:
        return self.item.class_id if self.item else ""


def detect_encoding(text: str, lang: Language) -> str:
    return "native" if any(ch in lang.letters_of for ch in text) else "transliteration"


def tokenize(text: str, lang: Language, encoding: str | None = None):
    """Split text into tokens at separators. Returns (tokens, diagnostics, encoding)."""
    encoding = encoding or detect_encoding(text, lang)
    tokens, diags = [], []
    line, col, start = 1, 1, None
    buf, raw = [], []
    native = asc = False
    start_line = start_col = 0
    # the block the writing-system specification declares
    # (specification/writing-system.md#the-native-digital-form)
    pua_lo, pua_hi = (chr(int(x[2:], 16)) for x in lang.writing["code point block"])
    pua_hi = chr(ord(pua_hi) + 1)

    def flush(end):
        nonlocal buf, raw, native, asc, start
        if start is not None:
            tokens.append(Token("".join(buf), "".join(raw),
                                Span(encoding, start, end, start_line, start_col),
                                native, asc))
        buf, raw, native, asc, start = [], [], False, False, None

    for i, ch in enumerate(text):
        if ch in SEPARATORS:
            flush(i)
        else:
            if start is None:
                start, start_line, start_col = i, line, col
            raw.append(ch)
            if ch in lang.letters_of:
                buf.append(lang.letters_of[ch])
                native = True
            elif ch in PAYLOAD_CHARS:
                buf.append(ch)
                if ch.isalpha():
                    asc = True
            elif pua_lo <= ch < pua_hi:
                diags.append(Diagnostic("d.tokenizer.foreign-use-of-the-range",
                                        Span(encoding, i, i + 1, line, col),
                                        detected=["U+%04X" % ord(ch)]))
                buf.append("?")
            else:
                diags.append(Diagnostic("d.tokenizer.outside-the-alphabet",
                                        Span(encoding, i, i + 1, line, col),
                                        expected=["a symbol or a separator"],
                                        detected=["U+%04X" % ord(ch)]))
                buf.append("?")
        if ch == "\n":
            line, col = line + 1, 1
        else:
            col += 1
    flush(len(text))
    return tokens, diags, encoding


def segment(form: str, lang: Language):
    """The morphemes of a content word, or None. A content word is a root or a
    closed-class member followed by suffixes, with the linker opening each further root
    of a compound; the shapes make the division unique (`language/phonology.json`)."""
    def root_at(i):
        """The root opening at `i`, of the length its first syllable fixes: five symbols
        or, opened by the long root's syllable, seven
        (specification/sounds-and-words.md#how-a-words-opening-fixes-its-length)."""
        n = lang.length_at(form, i)
        item = lang.by_form.get(form[i:i + n]) if n else None
        if item is not None and item.kind == "root":
            return item
        return None

    morphemes = []
    i = 0
    first = root_at(0)
    if first is not None:
        morphemes.append(first)
        i = len(first.form)
    else:
        head = lang.by_form.get(form[:4])
        if head is None or head.kind != "member" or len(form) <= 4:
            return None
        morphemes.append(head)
        i = 4
    while i < len(form):
        ch = form[i]
        if ch == LINKER:
            nxt = root_at(i + 1)
            if nxt is None:
                return None
            morphemes.append("linker")
            morphemes.append(nxt)
            i += 1 + len(nxt.form)
        elif ch in SUFFIX_FIRST:
            suf = lang.suffixes.get(form[i:i + 4])
            if suf is None:
                return None
            morphemes.append(suf)
            i += 4
        else:
            return None
    return morphemes


def _payload_length(nbytes: int) -> int:
    return (8 * nbytes + 4) // 5


def decode_payload(chars: str):
    """RFC 4648 § 6 base 32 in lower case without padding; None unless canonical."""
    if any(c not in PAYLOAD_CHARS for c in chars):
        return None
    padded = chars.upper() + "=" * (-len(chars) % 8)
    try:
        data = base64.b32decode(padded)
    except (ValueError, base64.binascii.Error):
        return None
    if encode_payload(data) != chars:
        return None
    return data


def encode_payload(data: bytes) -> str:
    return base64.b32encode(data).decode("ascii").rstrip("=").lower()


class _Lexer:
    def __init__(self, tokens, lang: Language):
        self.tokens = tokens
        self.lang = lang
        self.words: list[Word] = []
        self.diags: list[Diagnostic] = []
        wall = lang.form_of("g.structure.wall")
        data = lang.form_of("g.message.embedded-material.declared-data")
        self.wall_data = (wall, data)
        # the authentication field, whose signature is a payload after the numbers of its
        # scheme and its length (protocol 0.3); absent from a release before it
        self.authentication = (lang.form_of("g.message.message-field.authentication")
                               if "g.message.message-field.authentication" in lang.items
                               else None)

    def word_of(self, tok: Token) -> Word:
        lang = self.lang
        if tok.ascii_letters and tok.native:
            self.diags.append(Diagnostic("d.tokenizer.mixed-encodings", tok.span,
                                         detected=[tok.raw]))
        item = lang.by_form.get(tok.text)
        if item is not None:
            return Word(tok.text, tok.span, item)
        if any(c not in lang.letters for c in tok.text):
            self.diags.append(Diagnostic("d.lexer.letter-outside-a-payload", tok.span,
                                         expected=["a word"], detected=[tok.raw]))
            return Word(tok.text, tok.span, None, "unknown")
        parts = segment(tok.text, lang)
        if parts is not None:
            return Word(tok.text, tok.span, None, "formation", parts)
        # Kept opaque and reported as unknown in the named version
        # (specification/protocol.md#versions-and-features); the integrity check value,
        # where present, tells an unknown word from a corrupted one.
        self.diags.append(Diagnostic("d.lexer.unknown-word", tok.span,
                                     expected=["a word of lexicon %s" % lang.version],
                                     detected=[tok.raw], recoverability="kept opaque"))
        return Word(tok.text, tok.span, None, "unknown")

    def run(self):
        # One function longer than 50 lines: one loop of a state machine over the tokens,
        # which reads each payload by the length a number before it states; split, its
        # state would pass between functions. `lexer.ts` follows it statement for statement.
        lang = self.lang
        i = 0
        toks = self.tokens
        number_state = None   # collecting the numerals of a payload's length
        # what is still to read: 'number' for a payload's length, 'scheme' for the number
        # of an authentication scheme, which states no length, or a length, an int
        payload_need = []
        while i < len(toks):
            tok = toks[i]
            if payload_need and isinstance(payload_need[0], int):
                need = payload_need.pop(0)
                chars, first_span, j = "", tok.span, i
                while len(chars) < need and j < len(toks):
                    chars += toks[j].raw
                    j += 1
                last = toks[j - 1].span
                span = Span(first_span.encoding, first_span.start, last.end,
                            first_span.line, first_span.column)
                if len(chars) != need:
                    # Short: the tokens ran out, or a further token was needed and did
                    # not end where the length does. Long: one token exceeds the length.
                    code = "d.lexer.payload-long" if j - i == 1 and len(chars) > need \
                        else "d.lexer.payload-short"
                    self.diags.append(Diagnostic(code, span, expected=["%d characters" % need],
                                                 detected=["%d characters" % len(chars)]))
                    self.words.append(Word(chars, span, None, "payload"))
                    payload_need = []
                    i = j
                    continue
                data = decode_payload(chars)
                if data is None:
                    self.diags.append(Diagnostic("d.lexer.payload-character", span,
                                                 expected=["canonical base 32"],
                                                 detected=[chars]))
                    data = b""
                self.words.append(Word(chars, span, None, "payload", payload=data))
                i = j
                continue
            word = self.word_of(tok)
            self.words.append(word)
            i += 1
            # Track `WALL DECLARED-DATA number payload number payload`.
            if (len(self.words) >= 2 and self.words[-2].form == self.wall_data[0]
                    and word.form == self.wall_data[1]):
                payload_need = ["number", "number"]
                number_state = []
                continue
            # Track `AUTHENTICATION number number payload`: the scheme, then the length.
            if self.authentication is not None and word.form == self.authentication:
                payload_need = ["scheme", "number"]
                number_state = []
                continue
            if payload_need and payload_need[0] in ("number", "scheme"):
                if word.item is not None and word.class_id == "g.numbers.numeral":
                    number_state.append(word.item.name)
                elif word.item is not None and word.class_id == "g.numbers.check-word":
                    if payload_need[0] == "scheme":
                        payload_need.pop(0)
                        number_state = []
                        continue
                    digits = "".join(str(_DIGITS.index(n)) for n in number_state
                                     if n in _DIGITS)
                    payload_need.pop(0)
                    n = int(digits) if digits and len(digits) == len(number_state) else 0
                    payload_need.insert(0, _payload_length(n))
                    # after the first payload, the second length follows
                    if len(payload_need) == 2:
                        payload_need = [payload_need[0], "number"]
                    number_state = []
                else:
                    payload_need = []
        return self.words, self.diags


_DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]


def lex(tokens, lang: Language):
    return _Lexer(tokens, lang).run()
