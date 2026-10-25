"""The planted defects (specification/conformance.md#the-planted-defects, `run_mutants`):
each mutant is a defect of the reference implementation written as a patch, named by the
invariant whose planted defect it is (specification/conformance.md#the-invariants), with
the test files that must catch it. `tools/run_mutants.py` runs each in its own process,
with `ROWIH_MUTANT` set, and counts it caught only when the named tests then fail.
Invariants whose mechanism the core does not yet build are listed in `DEFERRED`, each with
the mechanism that builds it."""
import random

MUTANTS = {}


def mutant(name, invariant, tests, description):
    def register(fn):
        MUTANTS[name] = {"invariant": invariant, "tests": tests, "description": description,
                         "apply": fn}
        return fn
    return register


def _patch(module, attr, value):
    setattr(module, attr, value)


@mutant("encodings-agree", "inv.encodings-agree", ["tests/test_corpus.py"],
        "A native digital form that spells two symbols with one code point.")
def _():
    from rowih import data
    lang = data.load()
    lang.code_points["b"] = lang.code_points["p"]


@mutant("speech-decodable", "inv.speech-decodable", ["tests/test_lexicon.py"],
        "A lexicon with a word that is two words written together.")
def _():
    import dataclasses
    from rowih import data
    lang = data.load()
    a, b = lang.form_of("g.structure.term"), lang.form_of("g.structure.end-term")
    lang.by_form[a + b] = dataclasses.replace(lang.by_form[a], form=a + b)


@mutant("normal-form-unique", "inv.normal-form-unique", ["tests/test_properties.py"],
        "A normaliser that keeps siblings in the order the speaker wrote them.")
def _():
    from rowih import normal
    normal.Normaliser.order_all = lambda self, t: False


@mutant("generation-faithful", "inv.generation-faithful", ["tests/test_corpus.py"],
        "A generator that omits every value equal to its class's default, although the "
        "enclosing unit states another.")
def _():
    from rowih import generator
    original = generator.economise

    def economise(t, norm):
        out = original(t, norm)

        def strip(node):
            if isinstance(node, dict):
                if "parts" in node:
                    node["parts"] = [p for p in node["parts"] if not (
                        p.get("kind") == "value"
                        and p["member"] == "g.situations-and-contents.world-of-evaluation.actual")]
                for v in node.values():
                    strip(v)
            elif isinstance(node, list):
                for x in node:
                    strip(x)
        strip(out)
        return out
    generator.economise = economise


@mutant("deterministic", "inv.deterministic", ["tests/test_corpus.py", "tests/test_properties.py",
                                                "tests/test_parity.py"],
        "Readings written in the order of an unordered collection.")
def _():
    from rowih import tree
    original = tree.Spell.node
    rng = random.Random()

    def node(self, t):
        if t.get("kind") == "readings":
            t = dict(t, readings=rng.sample(t["readings"], len(t["readings"])))
        return original(self, t)
    tree.Spell.node = node
    from rowih import normal
    normal.Normaliser.order_all = lambda self, t: False


@mutant("well-typed", "inv.well-typed", ["tests/test_negative.py"],
        "A checker that accepts a shared node reached again from inside itself.")
def _():
    from rowih import parser
    parser._name_cycle = lambda constituents: None


@mutant("numerals-exact", "inv.numerals-exact", ["tests/test_corpus.py"],
        "A normaliser that drops trailing zeros after the decimal point.")
def _():
    from rowih import normal
    original = normal.Normaliser.part

    def part(self, p, world, mentioned=False):
        p = original(self, p, world, mentioned)
        if p.get("kind") == "quantity" and "." in p["number"] and "~" not in p["number"]:
            p["number"] = p["number"].rstrip("0").rstrip(".")
        return p
    normal.Normaliser.part = part


@mutant("displays-are-views", "inv.displays-are-views", ["tests/test_negative.py"],
        "A reader that takes any text, dropping what is not the language, as a message.")
def _():
    from rowih import lexer
    original = lexer.tokenize

    def tokenize(text, lang, encoding=None):
        keep = set(lang.letters) | set(lexer.SEPARATORS) | set(lang.letters_of)
        return original("".join(ch if ch in keep or ch in lexer.PAYLOAD_CHARS else " "
                                for ch in text), lang, encoding)
    lexer.tokenize = tokenize
    from rowih import api
    api._tokenize = tokenize


@mutant("force-marked", "inv.force-marked", ["tests/test_corpus.py"],
        "A checker that treats an assertion as a directive because its content names an "
        "obligation.")
def _():
    from rowih import checker, api
    original = checker.move_class

    def move_class(t):
        cls = original(t)
        if "g.force.kind-of-normative-entry.obligation" in repr(t["constituents"]):
            cls = dict(cls, operative=True, inert=False)
        return cls
    checker.move_class = move_class
    api.move_class = move_class


@mutant("quoted-inert", "inv.quoted-inert", ["tests/test_corpus.py"],
        "A parser that lets a force word inside a quotation set the class of the move.")
def _():
    from rowih import checker, api, data
    original = checker.move_class
    lang = data.load()
    request = lang.form_of("g.force.kind-of-issue.request")

    def move_class(t):
        cls = original(t)
        if request in repr(t["constituents"]):
            cls = dict(cls, pending=True, inert=False)
        return cls
    checker.move_class = move_class
    api.move_class = move_class


@mutant("boundary-closed", "inv.boundary-closed", ["tests/test_corpus.py"],
        "A parser that ends a quotation at any closing structural word inside it.")
def _():
    from rowih import parser
    from rowih.syntax import Wall
    original = parser.Parser.wall

    def wall(self):
        if self.peek(1) is not None and self.peek(1).identifier.endswith("declared-data"):
            return original(self)
        self.take()
        kind = self.value()
        w = Wall(kind)
        while not self.ident().startswith("g.structure.end-"):
            w.words.append(self.take())
        self.take()
        return w
    parser.Parser.wall = wall


@mutant("class-computed", "inv.class-computed", ["tests/test_corpus.py"],
        "A checker that finds the de-escalating moves by the change word alone.")
def _():
    from rowih import checker, api
    original = checker.move_class

    def move_class(t):
        cls = original(t)
        if any(c.endswith(".lowering") for c in t["change"]):
            cls = dict(cls, **{"de-escalating": True})
        return cls
    checker.move_class = move_class
    api.move_class = move_class


@mutant("fit", "inv.fit", ["tests/test_negative.py"],
        "A hearer that applies a lowering of a request sent to another.")
def _():
    from rowih import view
    original = view.View.apply

    def apply(self, sender, t, n, recipients=(), **kw):
        named = t.get("named")
        if named and named.get("target") == "entry":
            entry = self.entries.get((named["author"], named["number"]))
            if entry is not None:
                entry.recipients = entry.recipients + (sender,)
        return original(self, sender, t, n, recipients, **kw)
    view.View.apply = apply


@mutant("stop-restates", "inv.stop-restates", ["tests/test_negative.py"],
        "A checker that compares a restatement byte for byte, refusing 'I' for 'agent 2'.")
def _():
    from rowih import view
    view.resolve_deixis = lambda node, speaker, recipients: node


@mutant("at-most-once", "inv.at-most-once", ["tests/test_negative.py"],
        "A hearer that removes duplicates by the bytes of the message.")
def _():
    from rowih import view
    original = view.View.receive

    def receive(self, analysis):
        key = analysis.text
        if key in getattr(self, "_seen_bytes", set()):
            return []
        self._seen_bytes = getattr(self, "_seen_bytes", set()) | {key}
        self.channels = {}
        return original(self, analysis)
    view.View.receive = receive


@mutant("authority-attenuates", "inv.authority-attenuates", ["tests/test_negative.py"],
        "A checker that accepts an operative or pending move without its authority.")
def _():
    from rowih import checker
    original = checker.Checker.add

    def add(self, code, *a, **k):
        if code == "d.checker.authority":
            return None
        return original(self, code, *a, **k)
    checker.Checker.add = add


@mutant("own-action", "inv.own-action", ["tests/test_negative.py"],
        "A checker that accepts any action as the content of an intention.")
def _():
    from rowih import checker
    checker.Checker.actions_of = lambda self, situation, holder: True


@mutant("aims-apart", "inv.aims-apart", ["tests/test_corpus.py"],
        "A normaliser that writes a refusal as an assertion of inability.")
def _():
    from rowih import normal
    original = normal.Normaliser.move

    def move(self, t):
        n = original(self, t)
        if any(c.endswith(".lowering") for c in n["change"]) and n["named"] and \
                "kind-of-issue.request" in repr(n["named"]["expected"]):
            n["adds"] = ["g.force.what-the-move-adds.asserted-position"]
        return n
    normal.Normaliser.move = move


@mutant("standing-unchanged", "inv.standing-unchanged", ["tests/test_corpus.py"],
        "A terse realisation that drops an explicit strength word.")
def _():
    from rowih import generator
    original = generator.economise

    def economise(t, norm):
        out = original(t, norm)

        def strip(node):
            if isinstance(node, dict):
                if node.get("kind") == "assertion":
                    node["parts"] = [p for p in node["parts"] if not (
                        p.get("kind") == "value" and p["member"].startswith("g.standing.strength."))]
                for v in node.values():
                    strip(v)
            elif isinstance(node, list):
                for x in node:
                    strip(x)
        strip(out)
        return out
    generator.economise = economise


@mutant("strength-is-interval", "inv.strength-is-interval", ["tests/test_corpus.py"],
        "A normaliser that writes a named level as a single point.")
def _():
    from rowih import normal
    original = normal.Normaliser.part

    def part(self, p, world, mentioned=False):
        p = original(self, p, world, mentioned)
        if p.get("kind") == "value" and p["member"] == "g.standing.strength.probable":
            return {"kind": "quantity", "comparator": "g.situations-and-contents.comparator.exactly",
                    "number": "0.75", "unit": None, "per": None}
        return p
    normal.Normaliser.part = part


@mutant("ordered-times", "inv.ordered-times", ["tests/test_negative.py"],
        "A checker that compares an observation time only with the communication time.")
def _():
    from rowih import checker
    original = checker.Checker.point

    def ordered_times(self, t):
        times = {checker.short(p["index"]): p for p in t["parts"] if p["kind"] == "time"}
        comm = self.communication_time()
        if "observation-time" in times and comm is not None:
            pt = original(self, times["observation-time"]["spec"], comm)
            if pt is not None and pt > comm:
                self.add("d.checker.ordered-times", times["observation-time"])
    checker.Checker.ordered_times = ordered_times


@mutant("hearing-not-believing", "inv.hearing-not-believing", ["tests/test_corpus.py"],
        "A record keeper that files what it hears among its own entries.")
def _():
    from rowih import view
    original = view.View.apply

    def apply(self, sender, t, n, recipients=(), **kw):
        return original(self, self.participant, t, n, recipients, **kw)
    view.View.apply = apply


@mutant("precision-bound-one-reading", "inv.precision-bound-one-reading",
        ["tests/test_negative.py", "tests/test_ambiguity.py"],
        "A checker that lets a set of readings stand in a precision-bound move.")
def _():
    from rowih import checker
    original = checker.Checker.add

    def add(self, code, *a, **k):
        if code in ("d.checker.precision-bound", "d.checker.accidental-in-operative"):
            return None
        return original(self, code, *a, **k)
    checker.Checker.add = add


@mutant("readings-kept", "inv.readings-kept", ["tests/test_ambiguity.py"],
        "A normaliser that keeps only the first reading of a set.")
def _():
    from rowih import normal
    original = normal.Normaliser.node

    def node(self, t, world, top=False, confirmation=False, mentioned=False):
        out = original(self, t, world, top, confirmation, mentioned)
        if out.get("kind") == "readings":
            out["readings"] = out["readings"][:1]
        return out
    normal.Normaliser.node = node


@mutant("figure-not-literal", "inv.figure-not-literal", ["tests/test_corpus.py"],
        "A normaliser that asserts the source content of a marked metaphor.")
def _():
    from rowih import normal
    original = normal.Normaliser.term

    def term(self, t, world, mentioned=False):
        return original(self, t, world, False)
    normal.Normaliser.term = term


@mutant("identity-not-reference", "inv.identity-not-reference", ["tests/test_negative.py"],
        "A resolver that binds the interlocutor to the agent most recently mentioned.")
def _():
    from rowih import view
    original = view.resolve_deixis

    def resolve(node, speaker, recipients):
        parties = []

        def find(x):
            if isinstance(x, dict):
                if x.get("kind") == "party":
                    parties.append(x["number"])
                for v in x.values():
                    find(v)
            elif isinstance(x, list):
                for y in x:
                    find(y)
        find(node)
        return original(node, speaker, (parties[-1],) if parties else recipients)
    view.resolve_deixis = resolve


@mutant("dependencies-explicit", "inv.dependencies-explicit", ["tests/test_negative.py"],
        "A hearer that applies a cancellation to a request it holds as accepted.")
def _():
    from rowih import view
    original = view.View.apply

    def apply(self, sender, t, n, recipients=(), **kw):
        named = t.get("named")
        if named and named.get("status"):
            entry = self.entries.get((named["author"], named["number"]))
            if entry is not None:
                entry.status = named["status"].rsplit(".", 1)[-1]
        return original(self, sender, t, n, recipients, **kw)
    view.View.apply = apply


@mutant("entries-immutable", "inv.entries-immutable", ["tests/test_negative.py"],
        "An act that rewrites an entry's content in place.")
def _():
    from rowih import view
    original = view.View.effect

    def effect(self, t, entry):
        original(self, t, entry)
        entry.content = t["constituents"]
    view.View.effect = effect


@mutant("critical-values-explicit", "inv.critical-values-explicit", ["tests/test_corpus.py"],
        "A terse realisation that omits a deadline.")
def _():
    from rowih import generator
    original = generator.economise

    def economise(t, norm):
        out = original(t, norm)
        out["deadline"] = None
        return out
    generator.economise = economise


@mutant("no-silent-reinterpretation", "inv.no-silent-reinterpretation", ["tests/test_negative.py"],
        "A parser that closes an unclosed unit at the end of the move.")
def _():
    from rowih import parser
    from rowih.syntax import Unit

    def body(self, open_word, kind, closer):
        name = None
        parts = []
        while self.peek() is not None and self.peek().identifier != closer:
            parts.append(self.unit_part(kind))
        close = self.take() if self.peek() is not None else None
        return Unit(kind, name, parts, open_word, close)
    parser.Parser._unit_body = body


@mutant("single-edit-detected", "inv.single-edit-detected", ["tests/test_enumerations.py"],
        "A move check word that leaves the strength words out of what it covers.")
def _():
    from rowih import parser
    original = parser.move_check

    class _Blind:
        def __init__(self, w):
            self.item = None if (w.item is not None and w.item.class_id == "g.standing.strength") \
                else w.item
            self.form = w.form

    def move_check(body, lang):
        return original([_Blind(w) for w in body], lang)
    parser.move_check = move_check


@mutant("truncation-detected", "inv.truncation-detected", ["tests/test_enumerations.py"],
        "A reader that accepts a message cut at a boundary between two of its moves.")
def _():
    from rowih import api
    original = api._check_values

    def check_values(a, lang):
        return [d for d in original(a, lang) if d.code != "d.check-values.integrity-mismatch"]
    api._check_values = check_values


@mutant("one-critical-dimension", "inv.one-critical-dimension", ["tests/test_lexicon.py"],
        "One form for a negated command, carrying polarity and force at once.")
def _():
    from rowih import data
    lang = data.load()
    for cls in lang.grammar["classes"]:
        if cls["name"] == "polarity":
            cls["members"][1]["form"] = lang.form_of("g.force.kind-of-normative-entry.obligation")


@mutant("checks-match", "inv.checks-match", ["tests/test_negative.py"],
        "A parser that reads on past a word count that does not match.")
def _():
    from rowih import parser
    original = parser.Parser.move

    def move(self, index):
        try:
            return original(self, index)
        except parser.Reject as r:
            if r.diagnostic.code == "d.parser.count-mismatch":
                self.pos = self.end
                raise parser.Reject(parser.Diagnostic("d.parser.end-of-input", None))
            raise
    parser.Parser.move = move


@mutant("integrity-value-required", "inv.integrity-value-required", ["tests/test_negative.py"],
        "A checker that requires the value only on operative moves, missing pending ones.")
def _():
    from rowih import api
    original = api._check_values

    def check_values(a, lang):
        out = original(a, lang)
        if not any(c["operative"] for c in a.classes):
            out = [d for d in out if d.code != "d.checker.integrity-value-required"]
        return out
    api._check_values = check_values


@mutant("check-values-distinct", "inv.check-values-distinct", ["tests/test_corpus.py"],
        "A semantic value computed over the message's own serialisation.")
def _():
    from rowih import api
    original = api.parse

    def parse(text, encoding=None, lexicon=None, reader=None):
        a = original(text, encoding, lexicon, reader)
        a.normal_text = a.canonical
        return a
    api.parse = parse


@mutant("check-forms-disjoint", "inv.check-forms-disjoint", ["tests/test_lexicon.py"],
        "A move check form that is also a word of the lexicon.")
def _():
    from rowih import data
    lang = data.load()
    lang.move_check_forms[0] = lang.form_of("g.structure.term")


@mutant("unknown-preserved", "inv.unknown-preserved", ["tests/test_negative.py"],
        "A lexer that reads an unknown word as the known word nearest to it.")
def _():
    from rowih import lexer, lexicon_checks
    original = lexer._Lexer.word_of

    def word_of(self, tok):
        w = original(self, tok)
        if w.kind == "unknown":
            self.diags = [d for d in self.diags if d.code != "d.lexer.unknown-word"]
            nearest = min(self.lang.by_form, key=lambda f: lexicon_checks.levenshtein(f, w.form))
            return lexer.Word(nearest, w.span, self.lang.by_form[nearest])
        return w
    lexer._Lexer.word_of = word_of


@mutant("message-fields", "inv.message-fields", ["tests/test_negative.py"],
        "A parser that takes a message's version from elsewhere when it states none.")
def _():
    from rowih import parser
    original = parser.Parser._field

    def field(self, name):
        if name == "version" and self.ident() != parser.FIELD + "version":
            return None
        return original(self, name)
    parser.Parser._field = field
    original_number = parser.Parser.number

    def number(self, width=None, integer=False):
        if self.ident() == parser.FIELD + "identifier" and getattr(self, "_versionless", 0) < 3:
            self._versionless = getattr(self, "_versionless", 0) + 1
            return parser.Number(["zero", "decimal point", "one"], 1, [])
        return original_number(self, width, integer)
    parser.Parser.number = number


@mutant("maxima-enforced", "inv.maxima-enforced", ["tests/test_negative.py"],
        "A parser that never tests the nesting maximum.")
def _():
    from rowih import data
    data.load().protocol["maxima"].pop("nesting", None)


@mutant("critical-forms-distinct", "inv.critical-forms-distinct", ["tests/test_render.py"],
        "A component inventory that holds a component and its own reflection.")
def _():
    from rowih import data
    spec = data.load().writing
    box = spec["lattice"]["box"][0]
    by = {c["symbol"]: c for c in spec["components"]}
    by["u"]["unit strokes"] = [[[box - a[0], a[1]], [box - b[0], b[1]]]
                               for a, b in by["p"]["unit strokes"]]


@mutant("closed-alphabet", "inv.closed-alphabet", ["tests/test_negative.py"],
        "A reader that applies compatibility normalisation before it checks the alphabet.")
def _():
    import unicodedata
    from rowih import lexer, api
    original = lexer.tokenize

    def tokenize(text, lang, encoding=None):
        return original(unicodedata.normalize("NFKC", text), lang, encoding)
    lexer.tokenize = tokenize
    api._tokenize = tokenize


@mutant("diagnostics-not-exceptions", "inv.diagnostics-not-exceptions", ["tests/test_negative.py"],
        "A parser that raises KeyError on a SAME that names no unit.")
def _():
    from rowih import parser
    original = parser.Parser.move

    def move(self, index):
        m = original(self, index)
        return m
    original_same = parser.Parser.same

    def same(self):
        s = original_same(self)
        if s.name.integer() not in self.names and s.name.integer() > 5:
            raise KeyError(s.name.integer())
        return s
    parser.Parser.same = same


@mutant("lexicon-code", "inv.lexicon-code", ["tests/test_lexicon.py"],
        "A release check that does not test the distance between words.")
def _():
    from rowih import lexicon_checks
    lexicon_checks.ball = lambda word, alphabet: {word}


# ---------------------------------------------------------------- discourse
# The planted defects of the discourse invariants, and of the failures of an
# implementation's origin that concern the same mechanisms.

@mutant("view-independent-normalisation", "inv.view-independent-normalisation",
        ["tests/test_discourse.py"],
        "A view that normalises what it hears against its own record, writing in place of "
        "each reference to an entry it holds the content of that entry.")
def _():
    import copy
    from rowih import view

    original = view.View.receive

    def resolve(node, entries):
        if isinstance(node, dict):
            if node.get("kind") == "ref" and node.get("ref") == "names" and \
                    node.get("target") == "entry" and node.get("part") is None:
                e = entries.get((node["author"], node["number"]))
                if e is not None and e.content:
                    return copy.deepcopy(e.content[0])
            return {k: resolve(v, entries) for k, v in node.items()}
        if isinstance(node, list):
            return [resolve(x, entries) for x in node]
        return node

    def receive(self, analysis):
        analysis.normal = [dict(n, constituents=resolve(n["constituents"], self.entries))
                           for n in analysis.normal]
        return original(self, analysis)
    view.View.receive = receive


@mutant("summary-keeps-lowest", "inv.summary-keeps-lowest", ["tests/test_discourse.py"],
        "A summary that keeps the median strength under each calibration.")
def _():
    from rowih import standing
    original = standing.lowest

    def lowest(standings, lang):
        kept = original(standings, lang)
        strengths = set().union(*(s.strengths for s in standings)) if standings else set()
        out = set()
        for s in kept.strengths:
            group = sorted((x for x in strengths if x.calibration == s.calibration),
                           key=lambda x: x.key)
            out.add(group[len(group) // 2] if group else s)
        return standing.Standing(kept.bases, frozenset(out))
    standing.lowest = lowest


@mutant("summary-orders-bases", "inv.summary-keeps-lowest", ["tests/test_discourse.py"],
        "A summary that orders the bases of one tier and keeps only the first.")
def _():
    from rowih import standing
    original = standing.lowest

    def lowest(standings, lang):
        kept = original(standings, lang)
        return standing.Standing(frozenset(sorted(kept.bases)[:1]), kept.strengths)
    standing.lowest = lowest


@mutant("summary-raises-standing", "discourse/summary-raises-standing",
        ["tests/test_discourse.py"],
        "A record keeper that applies a summary whatever standing it states.")
def _():
    from rowih import view
    view.View.summary_standing = lambda self, sender, t, n: None


@mutant("summary-basis-from-the-act", "epistemic/summary-basis-from-the-act",
        ["tests/test_discourse.py"],
        "A summary whose basis is the inference of summarising, not what it summarises.")
def _():
    from rowih import standing
    original = standing.lowest

    def lowest(standings, lang):
        kept = original(standings, lang)
        return standing.Standing(frozenset({"g.standing.basis.inference"}), kept.strengths)
    standing.lowest = lowest


@mutant("independent-confirmation", "inv.independent-confirmation",
        ["tests/test_discourse.py", "tests/test_corpus.py"],
        "A record keeper that raises standing on any confirmation from a different "
        "participant identifier.")
def _():
    from rowih import discourse

    def corroboration(view, handle):
        return [{"entry": c["entry"], "lineage": c["entry"][0], "sources": [["any"]]}
                for c in discourse.confirmations(view, handle) if c["entry"][0] != handle[0]]
    discourse.corroboration = corroboration


@mutant("common-ground-by-acceptance", "inv.common-ground-by-acceptance",
        ["tests/test_discourse.py"],
        "A record keeper that adds a message's content to the common ground when the "
        "message is acknowledged.")
def _():
    from rowih import discourse
    original = discourse.acceptance

    def acceptance(view, participant, handle, part=None, now=None):
        found = original(view, participant, handle, part, now)
        if found:
            return found
        for e in view.entries.values():
            if e.handle[0] == participant and any(
                    named == handle for named, _ in discourse.head_names(e)) and \
                    discourse.short(e.move["change"][0]) == "acknowledgement":
                return ("acknowledgement", e.handle)
        return None
    discourse.acceptance = acceptance


@mutant("common-ground-accommodation", "inv.common-ground-by-acceptance",
        ["tests/test_discourse.py"],
        "A record keeper that accommodates a presupposition the viewing participant has "
        "not accepted.")
def _():
    from rowih import discourse
    original = discourse.propositions
    discourse.propositions = lambda view: [(h, p, False) for h, p, _ in original(view)]


@mutant("inference-not-said", "inv.inference-not-said", ["tests/test_discourse.py"],
        "An interpreter that records a scalar implicature as the speaker's assertion.")
def _():
    from rowih import view
    original = view.View.infer

    def infer(self, premises, content, kind="inference"):
        if kind == "implicature":
            for h in premises:
                self.entries[tuple(h)].content = self.entries[tuple(h)].content + list(content)
        return original(self, premises, content, kind)
    view.View.infer = infer


@mutant("external-origin-kept", "inv.external-origin-kept", ["tests/test_coordination.py"],
        "A generator that lifts an imperative out of a payload into a request and drops its "
        "origin.")
def _():
    from rowih import generator
    original = generator.Generator.from_external

    def from_external(self, t, material_type, material):
        moves = original(self, t, material_type, material)
        for s in generator._top_situations(moves[-1]["constituents"]):
            s["parts"] = [p for p in s["parts"] if p.get("member") !=
                          generator.INSTRUCTION_RECEIVED]
        return moves
    generator.Generator.from_external = from_external


@mutant("origin-dropped", "semantic/origin-dropped", ["tests/test_coordination.py"],
        "A normaliser that writes the origin of external content as the speaker's own as it "
        "moves the content into a move's core.")
def _():
    from rowih import normal
    original = normal.Normaliser.move

    def move(self, t):
        out = original(self, t)

        def own(node):
            if isinstance(node, dict):
                if node.get("member") == "g.attitudes-and-aims.origin-of-an-aim." \
                        "instruction-received":
                    node["member"] = "g.attitudes-and-aims.origin-of-an-aim.holders-own"
                for v in node.values():
                    own(v)
            elif isinstance(node, list):
                for x in node:
                    own(x)
        own(out)
        return out
    normal.Normaliser.move = move


@mutant("provenance-monotone", "inv.provenance-monotone", ["tests/test_coordination.py"],
        "A relay that writes itself in place of the source it relays.")
def _():
    from rowih import relay
    original = relay.relay_position

    def relay_position(entry, lang=None):
        t = original(entry, lang)
        for p in t["constituents"][0]["parts"]:
            if p.get("kind") == "filler" and p["role"].endswith("provenance-link.source"):
                p["filler"] = {"kind": "term", "name": None,
                               "parts": [{"kind": "value",
                                          "member": "g.reference.person.self"}]}
        return t
    relay.relay_position = relay_position


@mutant("provenance-dropped", "epistemic/provenance-dropped", ["tests/test_coordination.py"],
        "A relay that carries the relayed assertion without the links it was given, a "
        "shorter chain than the one it relays.")
def _():
    from rowih import relay
    original = relay.relay_position

    def relay_position(entry, lang=None):
        t = original(entry, lang)

        def strip(node, inner):
            if isinstance(node, dict):
                if inner and "parts" in node:
                    node["parts"] = [p for p in node["parts"] if not (
                        p.get("kind") == "filler"
                        and p["role"].startswith("g.standing.provenance-link"))]
                for v in node.values():
                    strip(v, inner or node.get("kind") == "situation")
            elif isinstance(node, list):
                for x in node:
                    strip(x, inner)
        strip(t["constituents"], False)
        return t
    relay.relay_position = relay_position


@mutant("precedence-agreed", "inv.precedence-agreed", ["tests/test_coordination.py"],
        "A participant that orders crossing moves by the time it received them.")
def _():
    from rowih import view
    original = view.View.crossing

    def crossing(self, item, ref):
        out = original(self, item, ref)
        if self._reorder is not None:
            winner, loser = self._reorder
            self._reorder = None
            self.crossed[winner.handle] = loser.handle
            return [view.Diagnostic("d.view.crossed", None, note="arrived second")]
        return out
    view.View.crossing = crossing


DEFERRED = {}


# The invariants of authentication, tokenizing and repair.

@mutant("authentication-covers-message", "inv.authentication-covers-message",
        ["tests/test_authentication.py"],
        "A signer that covers the moves and leaves the envelope out.")
def _():
    from rowih import serialise, writer

    def covered(envelope, body):
        return body.encode("utf-8")
    serialise.covered = covered
    writer.covered = covered


@mutant("tokenizer-round-trip", "inv.tokenizer-round-trip", ["tests/test_tokenizers.py"],
        "A tokenizer planted on the panel that rewrites one character of the alphabet as "
        "another.")
def _():
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "tools"))
    import tokenizer_panel as P
    load, make = P.load_panel, P.tokenizer

    class Planted:
        def __init__(self, tok):
            self.tok = tok

        def encode(self, *args, **kwargs):
            return self.tok.encode(*args, **kwargs)

        def decode(self, *args, **kwargs):
            return self.tok.decode(*args, **kwargs).replace("l", "r")

    def load_panel():
        panel = load()
        first = panel["members"][0]
        panel["members"] = [dict(first, name="planted", base=first["name"])] + \
            panel["members"][1:]
        return panel

    def tokenizer(member):
        if member["name"] == "planted":
            return Planted(make(dict(member, name=member["base"])))
        return make(member)
    P.load_panel, P.tokenizer = load_panel, tokenizer
    P.fetch = lambda panel: None


@mutant("gaps-known", "inv.gaps-known", ["tests/test_repair.py"],
        "A hearer that takes every serial below the highest it has received as held.")
def _():
    from rowih import channels
    channels.Channel.lacking = lambda self: []


@mutant("stop-delivery-known", "inv.stop-delivery-known", ["tests/test_repair.py"],
        "An acknowledgement that states only the last serial received, so that a stop lost "
        "before it is recorded as acknowledged.")
def _():
    from rowih import channels
    channels.Channel.holding = lambda self: (max(self.received, default=0),)


@mutant("stop-sent-once", "inv.stop-delivery-known", ["tests/test_repair.py"],
        "A sender that never sends a stop again, and records it as unacknowledged after "
        "one interval.")
def _():
    from rowih import repair
    original = repair.Participant.tick

    def tick(self):
        now = self.clock()
        for record in self.sent.values():
            if not record.stop:
                continue
            for peer, state in record.state.items():
                if state == repair.OPEN and now - record.last[peer] >= self.interval:
                    record.state[peer] = repair.UNACKNOWLEDGED
                    record.sendings[peer] = 1 + self.times
        original(self)
    repair.Participant.tick = tick


# The invariant and failure of register conversion.

@mutant("loss-declared", "inv.loss-declared", ["tests/test_registers.py"],
        "A register conversion that drops a node of the provenance graph and declares only "
        "a change of diction.")
def _():
    from rowih import conversion
    original_move, original_convert = conversion.convert_move, conversion.convert

    def drop(node):
        if isinstance(node, list):
            return [drop(x) for x in node if not (
                isinstance(x, dict) and x.get("kind") == "filler"
                and x["role"].startswith("g.standing.provenance-link."))]
        if isinstance(node, dict):
            return {k: drop(v) for k, v in node.items()}
        return node

    def convert_move(t, lang, code, norm, record=None):
        out = original_move(t, lang, code, norm, record)
        return drop(out) if isinstance(out, dict) else out

    def convert(analysis, to, record=None):
        out = original_convert(analysis, to, record)
        out.changes = [["diction"] for _ in out.changes]
        return out
    conversion.convert_move = convert_move
    conversion.convert = convert


@mutant("conversion-touches-the-core", "inv.loss-declared", ["tests/test_registers.py"],
        "A conversion that writes an idiom its target register does not admit by the "
        "idiom's literal reading, not by its expansion.")
def _():
    from rowih import conversion, idioms

    def literal(t, lang, mode, holdings=None):
        def strip(node):
            if isinstance(node, list):
                return [strip(x) for x in node if not (
                    isinstance(x, dict) and x.get("kind") == "value"
                    and x["member"] == idioms.MARK)]
            if isinstance(node, dict):
                return {k: strip(v) for k, v in node.items()}
            return node
        return strip(t)
    conversion.economy = literal


# The mechanisms of figures, each a defect against `inv.figure-not-literal`: what a
# speaker answers for through a figure, the relation each figurative type takes, and the
# conventional sense its frame selects.

@mutant("source-answered-for", "inv.figure-not-literal", ["tests/test_figures.py"],
        "A reader that answers for a figure's source, its mark removed, in place of its "
        "target content.")
def _():
    from rowih import figures
    original = figures._figure

    def figure(t, figure_name, lang, named):
        source = dict(t, parts=[p for p in t["parts"] if not (
            p.get("kind") == "value" and p["member"].startswith(
                "g.ambiguity-and-figures.figurative-type.")) and not (
            p.get("kind") == "filler" and p["role"].startswith(
                "g.ambiguity-and-figures.figures-relation."))])
        return source if original(t, figure_name, lang, named) is not None else None
    figures._figure = figure


@mutant("metonym-asked-for-a-target-content", "inv.figure-not-literal",
        ["tests/test_figures.py", "tests/test_negative.py"],
        "A checker that asks every figure for a target content, so that a metonym stating "
        "what it stands for is refused in a precision-bound move, as release 0.6 did.")
def _():
    from rowih import figure_rules
    figure_rules.REQUIRED["metonymy"] = figure_rules.TARGET


@mutant("relation-without-a-figure", "inv.figure-not-literal", ["tests/test_negative.py"],
        "A checker that accepts a figure's relation on a constituent no figurative mark "
        "stands on, so that a literal constituent claims a figure's content.")
def _():
    from rowih import figure_rules
    original = figure_rules.check_unit

    def check_unit(checker, t, bound, named):
        if figure_rules.figure_type(t) is None:
            return
        original(checker, t, bound, named)
    figure_rules.check_unit = check_unit


@mutant("conventional-sense-ignored", "inv.figure-not-literal", ["tests/test_figures.py"],
        "A reader that reads every word in its basic sense, so that a speaker's commitment "
        "attaches to the basic sense where its frame selects the conventional one.")
def _():
    from rowih import senses
    senses.sense_of = lambda unit, lang, named=None: None


@mutant("metonym-referent-mentioned", "inv.figure-not-literal", ["tests/test_figures.py"],
        "A normaliser that writes the referent a metonym stands for as mentioned, as "
        "release 0.6 did, although the metonym's predication is about it.")
def _():
    from rowih import normal
    original = normal.Normaliser.part

    def part(self, p, world, mentioned=False):
        if p["kind"] == "filler" and p["role"].endswith(".stands-for") and mentioned:
            p["filler"] = self.node(p["filler"], world, mentioned=True)
            return p
        return original(self, p, world, mentioned)
    normal.Normaliser.part = part


# The invariants of idioms, word formation and the closed core.

@mutant("realisations-normalise", "inv.realisations-normalise", ["tests/test_idioms.py"],
        "An idiom whose expansion in the lexicon turns a request into a command.")
def _():
    from rowih import data
    lang = data.load()
    ident = next(i for i, e in lang.entries.items()
                 if e["key"] == "request" and e["grammatical category"] == "act word")
    lang.entries[ident]["expansion"] = ["g.force.what-the-move-adds.normative-entry",
                                        "g.force.kind-of-normative-entry.obligation",
                                        "g.force.bindingness.bound"]


@mutant("word-formation", "inv.word-formation", ["tests/test_formation.py"],
        "A parser that reads an unlisted compound as the listed idiom it most resembles.")
def _():
    from rowih import formation
    original = formation.compose

    def compose(morphemes, lang):
        if "linker" in morphemes:
            for e in lang.entries.values():
                if e["grammatical category"] == "compound" and e.get("route") and \
                        e["formed from"][0] == morphemes[0].identifier:
                    return formation.of_entry(e)
        return original(morphemes, lang)
    formation.compose = compose


@mutant("core-closed", "inv.core-closed", ["tests/test_negative.py",
                                            "tests/test_formation.py"],
        "A definition check that compares a new term only with the members of its own "
        "class, not with every word in scope.")
def _():
    from rowih import convention_rules
    original = convention_rules.distance

    def confusable(word, lang):
        for form, item in sorted(lang.by_form.items()):
            if item.kind == "root" and original(word, form) < 2:
                return form
        return None
    convention_rules.confusable = confusable


# ---------------------------------------------------------------- failures of an
# implementation's origin (`FAILURES`): those whose defect differs from an
# invariant's planted defect have mutants of their own here.

@mutant("value-left-where-written", "units/value-left-where-written", ["tests/test_corpus.py"],
        "A normaliser that does not state an inherited world on the units that bear it.")
def _():
    from rowih import normal
    original = normal.Normaliser.situation

    def situation(self, t, world, top, mentioned=False):
        return original(self, t, "actual", top, mentioned)
    normal.Normaliser.situation = situation


@mutant("numbering-differs", "units/numbering-differs", ["tests/test_corpus.py"],
        "A normaliser that keeps the names as the speaker numbered them.")
def _():
    from rowih import normal
    normal.Normaliser.renumber = lambda self, t: None


@mutant("formation-not-from-parts", "units/formation-not-from-parts", ["tests/test_corpus.py"],
        "A lexer that reads every unlisted formation as an unknown word.")
def _():
    from rowih import lexer
    lexer.segment = lambda form, lang: None


@mutant("lexicon-version-ignored", "semantic/lexicon-version-ignored", ["tests/test_negative.py"],
        "A reader that interprets a message under its own lexicon whatever version the "
        "message names.")
def _():
    from rowih import data, releases
    original = releases.named_of

    def named_of(env):
        # the lexicon release the message names taken for the reader's own
        named = original(env)
        named["lexicon"] = data.load().release["version"]
        return named
    releases.named_of = named_of


@mutant("quotation-rewritten", "semantic/quotation-rewritten", ["tests/test_corpus.py"],
        "A normaliser that rewrites the words of a quotation into its own order.")
def _():
    from rowih import normal
    original = normal.Normaliser.part

    def part(self, p, world, mentioned=False):
        p = original(self, p, world, mentioned)
        if p.get("kind") == "filler" and p["filler"].get("kind") == "wall" and \
                "words" in p["filler"]:
            p["filler"]["words"] = sorted(p["filler"]["words"])
        return p
    normal.Normaliser.part = part


@mutant("omission-read-as-a-claim", "grammatical/omission-read-as-a-claim",
        ["tests/test_corpus.py"],
        "A normaliser that reads an omitted strength as certain.")
def _():
    from rowih import normal
    original = normal._value

    def value(member):
        if member == "g.standing.strength.unstated":
            member = "g.standing.strength.certain"
        return original(member)
    normal._value = value


@mutant("default-strengthening", "grammatical/default-undeclared-or-strengthening",
        ["tests/test_corpus.py"],
        "A default that strengthens: a confirmation taken as independent unless stated.")
def _():
    from rowih import normal
    original = normal._value

    def value(member):
        if member == "g.standing.independence-of-a-confirmation.same-source":
            member = "g.standing.independence-of-a-confirmation.independent"
        return original(member)
    normal._value = value


@mutant("no-words-for-the-failure", "discourse/no-words-for-the-failure", ["tests/test_report.py"],
        "A reader whose diagnostics have no rendering in the language.")
def _():
    from rowih import report
    report.render = lambda *a, **k: ""


@mutant("credence-off-the-scale", "epistemic/credence-off-the-scale", ["tests/test_negative.py"],
        "A checker that leaves another holder's credence unchecked against the scale.")
def _():
    from rowih import checker
    original = checker.Checker.strength

    def strength(self, p):
        if p.get("_attitude"):
            return None
        return original(self, p)
    checker.Checker.strength = strength
    original_unit = checker.Checker.unit

    def unit(self, t, bound, cls, move):
        if t["kind"] == "situation":
            for p in t["parts"]:
                if p["kind"] == "quantity":
                    p["_attitude"] = True
        return original_unit(self, t, bound, cls, move)
    checker.Checker.unit = unit


@mutant("origin-of-an-aim-read-in", "agency/origin-of-an-aim-read-in", ["tests/test_corpus.py"],
        "A normaliser that reads an unstated origin as the holder's own.")
def _():
    from rowih import normal
    original = normal._value

    def value(member):
        if member == "g.attitudes-and-aims.origin-of-an-aim.unstated":
            member = "g.attitudes-and-aims.origin-of-an-aim.holders-own"
        return original(member)
    normal._value = value


@mutant("interval-written-as-a-point", "ambiguity/interval-written-as-a-point",
        ["tests/test_ambiguity.py"],
        "A normaliser that writes an interval of strength as its midpoint.")
def _():
    from rowih import normal
    original = normal.Normaliser.assertion

    def assertion(self, t, world, confirmation, mentioned=False):
        for p in t["parts"]:
            if p["kind"] == "quantity" and "~" in p["number"]:
                lo, hi = p["number"].split("~")
                p["number"] = str((float(lo) + float(hi)) / 2)
        return original(self, t, world, confirmation, mentioned)
    normal.Normaliser.assertion = assertion


@mutant("layout-carries-meaning", "writing/layout-carries-meaning", ["tests/test_enumerations.py"],
        "A reader that takes a line break inside a move as a fault.")
def _():
    from rowih import api
    original = api.parse

    def parse(text, encoding=None, lexicon=None, reader=None):
        a = original(text, encoding, lexicon, reader)
        if a.message is not None and len([x for x in text.split("\n") if x.strip()]) != \
                1 + len(a.message.moves):
            from rowih.diagnostics import Diagnostic
            a.diagnostics.append(Diagnostic("d.parser.unexpected-word", None))
        return a
    api.parse = parse
    from rowih import conformance
    conformance.api.parse = parse


@mutant("serialisation-normalises", "machine/serialisation-normalises", ["tests/test_corpus.py"],
        "A canonical serialisation that spells the normal form instead of what was written.")
def _():
    from rowih import api
    original = api.parse

    def parse(text, encoding=None, lexicon=None, reader=None):
        a = original(text, encoding, lexicon, reader)
        if a.message is not None:
            env = a.canonical.split("\n")[0]
            a.canonical = env + "\n" + a.normal_text
        return a
    api.parse = parse


@mutant("conversion-lossy", "machine/conversion-lossy", ["tests/test_corpus.py"],
        "A conversion to the native digital form that drops payloads.")
def _():
    from rowih import serialise, api
    original = serialise.to_native

    def to_native(lines, lang):
        return original([[w for w in line if w.kind != "payload"] for line in lines], lang)
    serialise.to_native = to_native
    api.to_native = to_native


@mutant("export-parsed-back", "machine/export-parsed-back", ["tests/test_enumerations.py"],
        "A reader that imports a JSON export and reads it as a message.")
def _():
    import json
    from rowih import api
    original = api.parse

    def parse(text, encoding=None, lexicon=None, reader=None):
        if text.lstrip().startswith("{"):
            from rowih.generator import Generator
            view = json.loads(text)
            return original(Generator().message(view["moves"]), encoding, lexicon, reader)
        return original(text, encoding, lexicon, reader)
    api.parse = parse


# Each failure of an implementation's origin, with the mutant that plants it: a mutant of
# its own above, the planted defect of the invariant that detects it where the defect is
# the same, or the entry in `FAILURES_DEFERRED` that names the mechanism it concerns.
FAILURES = {
    "ontology/claim-taken-as-fact": "hearing-not-believing",
    "ontology/aim-taken-for-duty": "aims-apart",
    "ontology/mention-taken-for-use": "quoted-inert",
    "ontology/identity-from-content": "identity-not-reference",
    "ontology/readings-flattened": "readings-kept",
    "units/value-left-where-written": "value-left-where-written",
    "units/numbering-differs": "numbering-differs",
    "units/formation-not-from-parts": "formation-not-from-parts",
    "units/two-words-one-sound": "speech-decodable",
    "semantic/normalisation-reads-a-view": "view-independent-normalisation",
    "semantic/two-normal-forms": "normal-form-unique",
    "semantic/realisations-diverge": "generation-faithful",
    "semantic/generation-unfaithful": "generation-faithful",
    "semantic/lexicon-version-ignored": "lexicon-version-ignored",
    "semantic/quotation-rewritten": "quotation-rewritten",
    "semantic/origin-dropped": "origin-dropped",
    "grammatical/class-read-from-a-name": "class-computed",
    "grammatical/omission-read-as-a-claim": "omission-read-as-a-claim",
    "grammatical/default-undeclared-or-strengthening": "default-strengthening",
    "grammatical/two-dimensions-in-one-form": "one-critical-dimension",
    "grammatical/check-word-mistaken-for-a-word": "check-forms-disjoint",
    "grammatical/malformed-reread": "no-silent-reinterpretation",
    "discourse/summary-raises-standing": "summary-raises-standing",
    "discourse/no-words-for-the-failure": "no-words-for-the-failure",
    "epistemic/hearing-taken-for-truth": "hearing-not-believing",
    "epistemic/standing-changed-in-passage": "standing-unchanged",
    "epistemic/provenance-dropped": "provenance-dropped",
    "epistemic/summary-basis-from-the-act": "summary-basis-from-the-act",
    "epistemic/credence-off-the-scale": "credence-off-the-scale",
    "agency/origin-of-an-aim-read-in": "origin-of-an-aim-read-in",
    "agency/participant-from-a-description": "identity-not-reference",
    "ambiguity/string-with-two-parses": "precision-bound-one-reading",
    "ambiguity/readings-collapsed": "readings-kept",
    "ambiguity/interval-written-as-a-point": "interval-written-as-a-point",
    "context/entry-mutated": "entries-immutable",
    "context/resolved-against-the-record": "dependencies-explicit",
    "context/inference-recorded-as-said": "inference-not-said",
    "compression/compression-not-recoverable": "generation-faithful",
    "compression/conversion-touches-the-core": "conversion-touches-the-core",
    "compression/critical-value-from-context": "critical-values-explicit",
    "compression/economy-in-a-precision-bound-move": "standing-unchanged",
    "writing/encodings-disagree": "encodings-agree",
    "writing/confusable-forms": "critical-forms-distinct",
    "writing/layout-carries-meaning": "layout-carries-meaning",
    "writing/display-taken-for-the-language": "displays-are-views",
    "machine/serialisation-normalises": "serialisation-normalises",
    "machine/two-traversals": "deterministic",
    "machine/sibling-order-changed": "normal-form-unique",
    "machine/check-values-confused": "check-values-distinct",
    "machine/export-parsed-back": "export-parsed-back",
    "machine/exception-instead-of-a-diagnostic": "diagnostics-not-exceptions",
    "machine/conversion-lossy": "conversion-lossy",
}
FAILURES_DEFERRED = {}


# The invariants of the transmitted and written forms.

@mutant("transport-stable", "inv.transport-stable", ["tests/test_enumerations.py"],
        "A transmitted alphabet that includes the underscore, which Markdown rendering "
        "consumes: the native digital form spelling h with U+005F.")
def _():
    from rowih import data
    lang = data.load()
    del lang.letters_of[lang.code_points["h"]]
    lang.code_points["h"] = "_"
    lang.letters_of["_"] = "h"


@mutant("written-form-distinct", "inv.encodings-agree", ["tests/test_render.py"],
        "A writing-system specification that marks a term as it marks a situation, so "
        "that the drawing no longer shows which unit a word opens.")
def _():
    from rowih import data
    units = data.load().writing["units"]
    units["term"]["mark"] = units["situation"]["mark"]


# The invariants of versions and dialects.

@mutant("meaning-fixed", "inv.meaning-fixed", ["tests/test_versions.py"],
        "A lexer that reads the longest match against the current lexicon, so that a new "
        "entry swallows two existing words.")
def _():
    from rowih import api, data as real

    class Current:
        """The loader as the reader sees it: every message read against the release the
        reader holds, whatever release the message names."""
        own = None

        def __getattr__(self, name):
            return getattr(real, name)

        def load(self, version=None, language=None, dialects=()):
            if language is None and not dialects:
                self.own = version
                return real.load(version)
            return real.load(self.own or version, language, dialects)
    api.data = Current()


@mutant("compatible-within-major", "inv.compatible-within-major", ["tests/test_versions.py"],
        "A minor release that changes the declared default of a class.")
def _():
    from rowih import normal
    normal.EXISTENCE_OF_WORLD["actual"] = "predicted-to-exist"


@mutant("devices-admissible", "inv.devices-admissible", ["tests/test_dialects.py"],
        "A generator that writes a dialect form to a hearer whose messages never stated "
        "the dialect.")
def _():
    from rowih import data, economy

    def held_dialects(holdings):
        # every dialect the speaker holds, whatever the hearer's messages stated
        return set(data.dialect_releases())
    economy.held_dialects = held_dialects


# Version 1.0's planted defects.

@mutant("long-root-decodable", "inv.speech-decodable", ["tests/test_long_roots.py"],
        "A reader that takes the long root's syllable to open four symbols, as its onset "
        "alone would.")
def _():
    from rowih import data
    data.Language.length_at = lambda self, form, i=0: self.onset_length.get(form[i:i + 1])
