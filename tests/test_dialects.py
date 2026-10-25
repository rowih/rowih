"""The dialects (specification/dialects.md): each release and its digest, the compressed
forms and the invariant core they leave alone, a dialect named by its message, deprecated
forms, a definition scoped to a dialect, the device of dialect forms and
`inv.devices-admissible`, and the items of dialect negotiation driven through
participants."""
import itertools

import pytest

from rowih import api, conventions, data, dialects, releases
from rowih.economy import Holdings
from rowih.generator import Generator
from rowih.lexicon_checks import levenshtein
from rowih.notation import Reader
from rowih.repair import Participant
from rowih.view import View

from corpus import messages, moves_of

LANG = data.load()
TEXTS = {(i, k): t for i, k, _, t in messages()}
RECORDS = {(i, k): m for i, k, m, _ in messages()}
RELEASES = data.dialect_releases()
T0 = 1759622400
FRAME = ("(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation detect "
         "(ACTOR (term SELF)) (UNDERGOER (term %s DEFINITE)))))")


# ---------------------------------------------------------------- the releases

def test_every_release_states_the_digest_of_its_content():
    """A dialect is named by its number, version and digest, so the digest each release
    states must be the one its canonical text gives; and a change to any form, term or
    deprecation changes it."""
    assert releases.verify_digests() == []
    release = RELEASES[(2, "0.2")]
    changed = dict(release, forms=[dict(f) for f in release["forms"]])
    changed["forms"][0]["expansion"] = dict(changed["forms"][0]["expansion"],
                                            form=changed["forms"][1]["expansion"]["form"])
    assert dialects.digest(changed) != release["digest"]


def test_the_dialects_are_numbered_once_and_six_have_compressed_forms():
    """The dialects of release 1.0 (specification/dialects.md#the-dialects-of-release-10):
    the research, robotics, coding, conversational, security and mathematical dialects,
    each with a compressed form for every current term; the other communities keep their
    terms alone. Every number names one dialect."""
    names = {}
    for (number, version), r in RELEASES.items():
        assert names.setdefault(number, r["dialect"]) == r["dialect"]
    with_forms = {r["dialect"] for r in RELEASES.values() if r.get("forms")}
    assert with_forms == {"science", "robotics", "programming", "conversation", "security",
                          "mathematics"}
    for r in RELEASES.values():
        current = {t["machine identifier"] for t in r["terms"] if not t["version"]["deprecated"]}
        if r.get("forms"):
            assert {f["expansion"]["term"] for f in r["forms"]
                    if not f["version"]["deprecated"]} == current


def test_compressed_forms_keep_the_invariant_core():
    """A dialect adds forms (specification/dialects.md#compressed-forms) and changes the
    meaning of none of the language's. Every compressed form is a word of the root's shape
    that no release of the lexicon spells, at distance two from every word of every
    lexicon release a message of its dialect may name and from every other dialect's form,
    and at three from every protected word, as the release checks hold every word; its
    expansion is a term of its own release, which carries no critical dimension, and it
    stands only in the registers that admit the device of dialect forms."""
    forms = [(r["number"], f) for r in RELEASES.values() for f in r.get("forms", [])]
    later = [data.load(v) for v in releases.implementation()["lexicon"]]
    for number, f in forms:
        form = f["orthographic form"]
        assert len(form) == 5 and form[0] == "r"
        for lang in later:
            for word, item in lang.by_form.items():
                need = 3 if item.protected else 2
                assert levenshtein(form, word) >= need, (form, word)
        release = next(r for r in RELEASES.values() if r["number"] == number
                       and f in r.get("forms", []))
        term = next(t for t in release["terms"]
                    if t["machine identifier"] == f["expansion"]["term"])
        assert term["orthographic form"] == f["expansion"]["form"]
        assert f["register"] == [c for c, r in LANG.registers.items()
                                 if "dialect forms" in r["devices admitted"]]
    for (n1, a), (n2, b) in itertools.combinations(forms, 2):
        if a["orthographic form"] != b["orthographic form"]:
            assert levenshtein(a["orthographic form"], b["orthographic form"]) >= 2
        else:
            assert n1 == n2 and a["machine identifier"] == b["machine identifier"]


def test_every_compressed_form_expands_into_the_core():
    """`inv.realisations-normalise` for the device of dialect forms: a move using each
    compressed form normalises to the bytes of the same move with the term written out,
    which every reader reads by its composition, and its message names the dialect."""
    for (number, version), r in sorted(RELEASES.items()):
        lang = data.load(dialects=((number, version),))
        gen, read = Generator(lang), Reader(lang)
        # a deprecated form is read and never written; its key names the form in force
        for f in [f for f in r.get("forms", []) if not f["version"]["deprecated"]]:
            key = "%s.%s" % (r["dialect"], f["key"].replace(" ", "-"))
            compressed = api.parse(gen.message(read.moves(FRAME % key)))
            plain = api.parse(Generator().message(Reader(LANG).moves(
                FRAME % ('(unknown "%s")' % f["expansion"]["form"]))))
            assert compressed.diagnostics == [] and plain.diagnostics == []
            assert compressed.named["dialects"] == [(number, version, r["digest"])]
            assert compressed.normal_text == plain.normal_text, key


# ---------------------------------------------------------------- naming a dialect

def test_a_dialect_form_is_read_only_where_its_message_names_the_dialect():
    """Adversarial item a11 and `compression/dialect-not-named`: the coding dialect's form
    for deploying is unknown vocabulary in the message that names no dialect, and in the
    message that names the dialect means the term it compresses."""
    unnamed = api.parse(TEXTS[("a11-registers-dialect", 1)])
    named = api.parse(TEXTS[("a11-registers-dialect", 2)])
    assert [d.code for d in unnamed.diagnostics] == ["d.lexer.unknown-word"]
    assert [w.kind for w in unnamed.words if w.form == "raner"] == ["unknown"]
    assert named.diagnostics == []
    deploy = next(t for t in RELEASES[(2, "0.2")]["terms"] if t["term"] == "deploy")
    assert deploy["orthographic form"] in named.normal_text
    assert "raner" not in named.normal_text


def test_a_hearer_lacking_the_named_release_of_a_dialect_reports_it():
    """A hearer that holds no release of the named dialect, or holds it under another
    digest, interprets none of the message's moves and reports the dialect it lacks with
    the dialects it holds (`d.parser.version-unknown`)."""
    text = TEXTS[("e9-dialect-forms", 2)]
    lacking = releases.Reader(dialects=((1, "0.2"),))
    a = api.parse(text, reader=lacking)
    assert [d.code for d in a.diagnostics] == ["d.parser.version-unknown"]
    assert a.lacking == {"dialects": [(2, "0.2", RELEASES[(2, "0.2")]["digest"])]}
    assert a.moves == [] and a.diagnostics[0].expected == ["dialects 1 0.2"]
    other = api.parse(open("corpus/negative/n123-dialect-under-another-digest.txt").read())
    assert "d.parser.version-unknown" in [d.code for d in other.diagnostics]


def test_resources_that_confuse_two_forms_are_refused(monkeypatch):
    """A dialect whose form is one edit from a word of the named lexicon release is
    refused when a message names it, never read one way or the other
    (`d.parser.dialect-conflict`)."""
    release = dict(RELEASES[(2, "0.2")], version="0.3")
    near = LANG.form_of("lx.000004")[:-1] + "b"     # one edit from the root for running
    assert levenshtein(near, LANG.form_of("lx.000004")) == 1
    release["forms"] = [dict(release["forms"][0], **{"orthographic form": near})]
    release["digest"] = dialects.digest(release)
    held = {**RELEASES, (2, "0.3"): release}
    monkeypatch.setattr(data, "dialect_releases", lambda: held)
    data._load_release.cache_clear()
    try:
        lang = data.load(dialects=((2, "0.3"),))
        text = Generator(lang).message(Reader(LANG).moves(FRAME % "service"))
        a = api.parse(text, reader=releases.Reader(dialects=((2, "0.3"),)))
        assert [d.code for d in a.diagnostics] == ["d.parser.dialect-conflict"]
    finally:
        data._load_release.cache_clear()


# ---------------------------------------------------------------- deprecated forms

def test_a_deprecated_term_stays_interpretable_and_is_reported():
    """The mathematical dialect's first term for a proof, deprecated by its release 0.2,
    is read by its composition and reported with its replacement; a quotation of it
    mentions the word and reports nothing; its replacement's compressed form reports
    nothing."""
    used, quoted, replaced = (api.parse(TEXTS[("e9-deprecated-term", k)]) for k in (1, 2, 3))
    assert used.diagnostics == [] and used.moves
    assert [(d["form"], d["deprecated"], d["replaced by"]) for d in used.deprecated] == [
        ("remamumop", "0.2", "jg.mathematics.006")]
    assert "remamumop" in used.normal_text
    assert quoted.deprecated == [] and replaced.deprecated == []
    old = next(t for t in RELEASES[(1, "0.1")]["terms"] if t["term"] == "proof")
    assert old["version"]["deprecated"] is None and old["orthographic form"] == "remamumop"


# ---------------------------------------------------------------- scoped definitions

def test_a_definition_scoped_to_a_dialect_reaches_only_messages_naming_it():
    """A definition may be scoped to a dialect (specification/discourse.md#definitions):
    B's view reads A's word under the definition in the message that names the
    conversational dialect, and not in the one that names no dialect; a definition scoped
    to a dialect its own message does not name is refused
    (`d.checker.definition-scope`)."""
    view = View("2")
    for k in (1, 2, 3, 4):
        view.receive(api.parse(TEXTS[("e9-dialect-definition", k)]))
    (term,) = conventions.terms(view)
    assert term["term"] == "ratid" and term["definition"] == ("1", "1")
    assert term["uses"] == [("1", "2")]
    refused = api.parse(open("corpus/negative/n129-definition-scoped-to-an-unnamed-dialect"
                             ".txt").read())
    assert "d.checker.definition-scope" in [d.code for d in refused.diagnostics]


# ---------------------------------------------------------------- the device

TERMS = [(r["number"], r["version"], r["digest"], f["expansion"]["form"], f["key"])
         for r in RELEASES.values() for f in r.get("forms", [])]


@pytest.mark.parametrize("number,version,digest,expansion,key", TERMS)
def test_the_generator_writes_a_dialect_form_only_to_a_hearer_holding_it(
        number, version, digest, expansion, key):
    """`inv.devices-admissible` for the device of dialect forms: for a meaning a
    compressed form can write and every record of what the hearer holds, the compressed
    form uses a dialect only where the hearer holds it under the digest of the release
    the speaker holds, and the message names that dialect and no other; it normalises to
    the meaning whatever the hearer holds."""
    gen = Generator()
    meaning = Reader(LANG).moves(FRAME % ('(unknown "%s")' % expansion))
    target = api.parse(gen.message(meaning)).normal_text
    other = next(r for r in RELEASES.values() if r["number"] != number and r.get("forms"))
    for held in [(), ((number, version, digest),),
                 ((number, version, "%09d" % ((int(digest) + 1) % 10 ** 9)),),
                 ((other["number"], other["version"], other["digest"]),)]:
        holdings = Holdings(lexicon=(LANG.version,), dialects=held)
        a = api.parse(gen.generate(meaning, holdings=holdings)["compressed form"])
        assert a.diagnostics == [] and a.normal_text == target
        usable = [(n, v, d) for n, v, d in held if RELEASES[(n, v)]["digest"] == d
                  and n == number]
        assert a.named["dialects"] == usable


def test_a_view_learns_the_dialects_its_hearer_holds():
    """The holdings a speaker's view shows of a hearer include the dialects the hearer's
    messages named and those it stated it understands, each with its digest, and nothing
    else."""
    view = View("1")
    view.receive(api.parse(TEXTS[("e9-dialect-negotiation", 5)]))
    assert Holdings.from_view(view, "1", "2").dialects == ()
    a = Participant("1", lambda: float(T0), view=view)
    a.receive(TEXTS[("e9-dialect-negotiation", 4)])
    assert Holdings.from_view(view, "1", "2").dialects == (
        (2, "0.2", RELEASES[(2, "0.2")]["digest"]),)


# ---------------------------------------------------------------- negotiation

class Clock:
    def __init__(self):
        self.now = float(T0)

    def __call__(self):
        return self.now


def statements(person):
    out = [api.parse(text).statement for _, text in person.outbox]
    person.outbox.clear()
    return out


def send(person, item, k, clock, **kw):
    m = RECORDS[(item, k)]
    clock.now = float(m["time"])
    text = person.send(moves_of(m), [str(r) for r in m["recipients"]], **kw)
    person.outbox.clear()
    return text


def statement(item, k):
    return api.parse(TEXTS[(item, k)]).statement


def test_dialect_negotiation_is_what_the_participants_write():
    """e9-dialect-negotiation, the settling of the dialects two agents share
    (specification/dialects.md#settling-the-dialects-two-agents-share): A's statement, its
    message with a security form, B's statement of what it lacks and what it understands,
    and A's restatement and its message in the dialect both hold are what the participants
    write; A records the message B could not interpret."""
    item = "e9-dialect-negotiation"
    clock = Clock()
    offered = releases.Reader(dialects=((2, "0.2"), (8, "0.2")))
    a = Participant("1", clock, reader=offered)
    b = Participant("2", clock, reader=releases.Reader(dialects=((2, "0.2"),)))
    a.negotiate("2")
    assert statements(a) == [statement(item, 1)]
    assert send(a, item, 2, clock, dialects=((8, "0.2"),)) == TEXTS[(item, 2)]
    clock.now = T0 + 20
    b.receive(TEXTS[(item, 2)])
    assert statements(b) == [statement(item, 3), statement(item, 4)]
    assert ("1", "1") not in b.view.entries
    for k in (3, 4):
        a.receive(TEXTS[(item, k)])
    lacked = a.uninterpreted[("2", ("1", ("2",)), 1)]
    assert lacked["dialects"] == [(8, "0.2", RELEASES[(8, "0.2")]["digest"])]
    assert a.common_with("2")["dialects"] == [(2, "0.2", RELEASES[(2, "0.2")]["digest"])]
    assert send(a, item, 6, clock) == TEXTS[(item, 6)]
    assert send(a, item, 7, clock, dialects=((2, "0.2"),)) == TEXTS[(item, 7)]
    for k in (6, 7):
        assert b.receive(TEXTS[(item, k)]) == []
    assert ("1", "2") in b.view.entries and ("1", "3") in b.view.entries
    report = api.parse(TEXTS[(item, 5)])
    assert report.diagnostics == [] and report.classes[0]["inert"]
