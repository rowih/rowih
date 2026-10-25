"""The version system (specification/protocol.md#versions-and-features): version
identifiers, the record of the releases, the release comparison that tests
`inv.compatible-within-major` and `inv.meaning-fixed`, the reading of a message under the
release it names, the feature registry and readers that lack features, version
negotiation, and each matter of versioning in turn."""
import copy
import json
import os
import random
import sys

import pytest

from rowih import api, data, features, negotiation, releases, versions
from rowih.data import Item
from rowih.lexicon_checks import ball
from rowih.repair import Participant

from corpus import ROOT, messages, moves_of

sys.path.insert(0, os.path.join(ROOT, "tools"))
from record_release import record  # noqa: E402

LANG = data.load()
MESSAGES = messages()
TEXTS = {(i, k): t for i, k, _, t in MESSAGES}
RECORDS = {(i, k): m for i, k, m, _ in MESSAGES}
T0 = 1759622400


def plain(x):
    return json.loads(json.dumps(x))


# ---------------------------------------------------------------- identifiers

def test_versions_are_pairs_of_integers():
    """A version is two integers with the decimal point between them, compared as pairs,
    so that 0.10 follows 0.9 and is not 0.1; a leading zero gives a version two
    spellings and is refused."""
    assert versions.ordered(["0.10", "0.9", "1.0", "0.1"]) == ["0.1", "0.9", "0.10", "1.0"]
    assert versions.key("0.10") != versions.key("0.1")
    for bad in ("0.010", "00.1", "1", "1.2.3", "a.b", ".1", "1."):
        assert not versions.well_formed(bad), bad
    refused = api.parse(open(os.path.join(ROOT, "corpus", "negative",
                                          "n121-version-with-a-leading-zero.txt")).read())
    assert [d.code for d in refused.diagnostics] == ["d.parser.number-form"]


# ---------------------------------------------------------------- the releases

def test_the_record_of_releases_is_whole_and_ordered():
    """Every language release from the core's states the protocol and lexicon it was
    released with and reads itself; 0.10 reads 0.9 and no earlier release, whose
    envelope no later reader can find; 1.0, the first public release, reads itself alone,
    since no population held a pre-release, with protocol 0.5, which reads its own
    protocol messages alone; and its messages name lexicon 1.0 or later."""
    record_ = data.language_releases()
    langs = [r["language"] for r in record_["language"]]
    assert langs == ["0.%d" % n for n in range(1, 11)] + ["1.0"]
    for r in record_["language"]:
        assert r["language"] in r["reads"]
        assert os.path.exists(os.path.join(ROOT, "lexicon", "releases", r["lexicon"] + ".json"))
    assert next(r for r in record_["language"] if r["language"] == "0.10")["reads"] == \
        ["0.9", "0.10"]
    one = next(r for r in record_["language"] if r["language"] == "1.0")
    assert one["reads"] == ["1.0"] and one["least lexicon"] == "1.0"
    assert one["protocol"] == "0.5" and LANG.protocol["version"] == "0.5"
    own = releases.implementation()
    assert own["language"] == ("1.0",)
    assert own["lexicon"] == ("1.0",)
    assert own["protocol"] == ("0.5",)
    assert releases.check_releases(record_) == []


def test_the_release_rule_refuses_a_major_release_that_drops_an_earlier_one():
    """From major version 1, a release reads every earlier release of its major version
    (governance/README.md#versions-and-releases); a record whose 1.1 reads 1.1 alone is
    refused, and the pre-release series is exempt."""
    record_ = copy.deepcopy(data.language_releases())
    record_["language"] += [
        {"language": "1.1", "date": "", "protocol": "0.4", "lexicon": "1.0", "reads": ["1.1"]}]
    assert releases.check_releases(record_) == [("drops an earlier release", "1.1 1.0")]


@pytest.mark.parametrize("release,messages_,protocol_messages", [("1.0", 382, 14)])
def test_inv_compatible_within_major_every_message_of_an_earlier_release_reads_alike(
        release, messages_, protocol_messages):
    """`inv.compatible-within-major` and `inv.meaning-fixed` by the release comparison
    (specification/conformance.md#the-invariants): every message of a release's corpus, as
    that release's own code recorded its analysis, analyses identically under every
    release that declares that it reads it: its diagnostics, its moves' classes, its
    normal form, its social and textual component, its formations, its statement where it
    is a protocol message, its confidence and its canonical layout. Release 1.0 reads no
    earlier release; its own record, which a later release will read, is held to its code
    here, so that the record a release is tagged with is the one its code writes."""
    archived = json.load(open(os.path.join(ROOT, "corpus", "releases", release + ".json")))
    assert archived["language"] == release and len(archived["items"]) == messages_
    protocol = 0
    for item in archived["items"]:
        assert plain(record(api.parse(item["text"]))) == item["record"], item["path"]
        protocol += item["record"]["statement"] is not None
    assert protocol == protocol_messages


# ---------------------------------------------------------------- inv.meaning-fixed

# the current lexicon release, and the later one the test of `inv.meaning-fixed` makes
CURRENT, LATER = data.CURRENT, "1.1"


def _augmented(seed: int):
    """Release 1.1, made for the test from the current release by entries meeting the
    lexicon's rules added at random: long roots, as every root from version 1.0 is
    (specification/sounds-and-words.md#how-a-words-opening-fixes-its-length), at distance
    two from every word and every dialect's compressed form and three from every protected
    word, and formations of the corpus listed with a meaning their parts do not give, as a
    frequent formation drifts. Returns the release and the forms it adds."""
    from build_version1 import long_code
    rng = random.Random(seed)
    lang = data._load_release.__wrapped__(CURRENT)
    lang.version = LATER
    lang.release = dict(lang.release, version=LATER)
    taken = set(lang.by_form)
    near = set()
    for word, item in lang.by_form.items():
        near |= ball(word, lang.letters)
        if item.protected:
            for w in ball(word, lang.letters):
                near |= ball(w, lang.letters)
    # nor near any registered dialect's compressed form, as the language's own releases
    # keep clear of them
    for r in data.dialect_releases().values():
        for f in r.get("forms", []):
            near |= ball(f["orthographic form"], lang.letters)
    pool = long_code()
    rng.shuffle(pool)
    added = []
    for form in pool:
        if len(added) == 6:
            break
        if form in taken or form in near:
            continue
        ident = "lx.9%05d" % len(added)
        lang.entries[ident] = dict(lang.entries["lx.000006"], key="random %d" % len(added),
                                   **{"orthographic form": form, "machine identifier": ident})
        lang.items[ident] = lang.by_form[form] = Item("root", ident, form, "RANDOM",
                                                      name="random", sort="s.sort.object")
        near |= ball(form, lang.letters)
        added.append(form)
    formations = sorted({w.form for _, _, _, t in MESSAGES for w in api.parse(t).words
                         if w.kind == "formation"})
    for k, form in enumerate(rng.sample(formations, 3)):
        ident = "lx.8%05d" % k
        template = next(e for e in lang.entries.values()
                        if e["grammatical category"] == "compound")
        lang.entries[ident] = dict(template, key="drift %d" % k, sort="s.sort.kind",
                                   **{"orthographic form": form, "machine identifier": ident,
                                      "definition": "a meaning its parts do not give"})
        lang.items[ident] = lang.by_form[form] = Item("derivation", ident, form, "DRIFT",
                                                      name="drift", sort="s.sort.kind",
                                                      category="compound")
        added.append(form)
    return lang, added


def _with_release(monkeypatch, lang):
    original = data._load_release
    loaded = {}

    def load(version, language=None, dialects=()):
        if version != LATER:
            return original(version, language, dialects)
        if (language, dialects) not in loaded:
            # the release with the entries added, read under the named language release
            # with the named dialects, as `data.load` reads a release from disk
            out = copy.deepcopy(lang)
            out.language, out.dialects = language or out.language, dialects
            for number, version_ in dialects:
                data._add_dialect(out, data.dialect_releases()[(number, version_)])
            loaded[(language, dialects)] = out
        return loaded[(language, dialects)]
    monkeypatch.setattr(data, "_load_release", load)


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_inv_meaning_fixed_a_later_release_changes_no_message_already_sent(monkeypatch, seed):
    """`inv.meaning-fixed`: every corpus message analyses identically when the reader's
    own release has entries added at random, since it is read under the release it names;
    and restated to name the release with the entries added, every message analyses
    identically except those that contain a new entry's form, written or as a compressed
    form's expansion, whose analysis is the new release's to give
    (specification/conformance.md#the-invariants)."""
    lang, added = _augmented(seed)
    _with_release(monkeypatch, lang)
    reader = releases.Reader(lexicon=releases.implementation()["lexicon"] + (LATER,))
    changed = containing = 0
    for item_id, k, m, text in MESSAGES:
        a = api.parse(text)
        assert plain(record(api.parse(text, lexicon=LATER, reader=reader))) == plain(record(a))
        if a.message is None or a.message.envelope.is_protocol or \
                a.named["lexicon"] != CURRENT:
            continue
        restated = _restated(text, a.named["language"])
        b = api.parse(restated, reader=reader)
        # a form the message writes, or the expansion of a compressed form it writes
        contains = any(w.form in added for w in a.words) or \
            bool(set(a.normal_text.split()) & set(added))
        containing += contains
        if contains:
            changed += (plain(b.normal), b.formations) != (plain(a.normal), a.formations)
            continue
        assert (plain(b.normal), b.normal_text, b.classes, b.social, b.formations) == (
            plain(a.normal), a.normal_text, a.classes, a.social, a.formations), (item_id, k)
    assert containing > 0 and changed > 0


def _restated(text: str, language: str) -> str:
    """The message naming the later lexicon release in place of the current one: the
    lexicon's number follows the language's in the version field, and the two are
    written alike where the releases share a number."""
    current, later = " ".join(_version_words(CURRENT)), " ".join(_version_words(LATER))
    named = " ".join(_version_words(language))
    field = text.index(LANG.form_of("g.message.message-field.version") + " ")
    start = text.index(named, field) + len(named)
    at = text.index(current, start)
    return text[:at] + later + text[at + len(current):]


def _version_words(version: str) -> list:
    from rowih.writer import Writer
    return Writer(LANG).number(version)


# ---------------------------------------------------------------- reading under a release

# Release 1.0 reads no earlier release, so the mechanism by which a later release reads an
# earlier one is shown on a release of the development series, which a reader is
# configured here to hold beside 1.0, as a later release will hold 1.0 beside itself.
DEVELOPMENT = releases.Reader(language=("0.9", "1.0"), lexicon=("0.6", "0.7", "1.0"),
                              protocol=("0.3", "0.4", "0.5"))
BROKEN = "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation break COMPLETED " \
    "(UNDERGOER (term network DEFINITE)))))"


def written_under(notation, lexicon=None, language=None, identifier=1):
    """The message `notation` writes, in the release of the lexicon and the language
    named, the current release where they are None."""
    from rowih.generator import Generator
    from rowih.notation import Reader as Notation
    gen = Generator(data.load(lexicon, language))
    return gen.message(Notation(gen.lang).moves(notation), identifier=identifier)


def test_a_message_is_read_under_the_release_it_names():
    """A message written as release 0.9 wrote it is read, by a reader that holds 0.9,
    under language 0.9 and lexicon 0.6, to the normal form the same meaning has at the
    current release, 1.0; a root of lexicon 0.7 in a message naming 0.6 is unknown
    vocabulary, and in one naming a later release is the root. A reader that holds
    lexicon 0.6 finds a message of 1.0 naming it to pair releases wrongly, and the current
    release, which reads no lexicon before 1.0, does not read it."""
    have = "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation possess " \
        "(HOLDER (term SELF)) (UNDERGOER (term %s DEFINITE)))))"
    old = api.parse(written_under(BROKEN, "0.6", "0.9"), reader=DEVELOPMENT)
    new = api.parse(written_under(BROKEN, identifier=2))
    unknown = api.parse(written_under(have % '(unknown "rowew")', "0.6", "0.9", 3),
                        reader=DEVELOPMENT)
    known = api.parse(written_under(have % "version", identifier=4))
    assert old.read_under == {"version": "0.6", "language": "0.9", "dialects": (),
                              "protocol": "0.3"}
    assert new.read_under["language"] == "1.0" and plain(old.normal) == plain(new.normal)
    # the normal text writes each move's check word under its release's modulus, 227 for
    # lexicon 0.6 and 337 for 1.0, and differs in nothing else
    differ = [(x, y) for x, y in zip(old.normal_text.split(), new.normal_text.split())
              if x != y]
    assert len(old.normal_text.split()) == len(new.normal_text.split())
    assert differ and all(y in LANG.move_check_value for _, y in differ)
    assert [d.code for d in unknown.diagnostics] == ["d.lexer.unknown-word"]
    assert known.diagnostics == [] and "rowew" in known.normal_text
    text = open(os.path.join(ROOT, "corpus", "negative",
                             "n124-lexicon-before-the-least.txt")).read()
    assert [d.code for d in api.parse(text, reader=DEVELOPMENT).diagnostics] == [
        "d.parser.version-pairing"]
    assert [d.code for d in api.parse(text).diagnostics] == ["d.parser.version-unknown"]


def test_a_word_of_a_later_language_release_is_unknown_in_an_earlier_one():
    """Every grammar word states the release that introduced it, and under an earlier
    release a later word is unknown: the dialect word, in a message naming language 0.9,
    is kept opaque rather than read as 0.10 reads it, and a root of lexicon 0.7 in a
    message naming 0.6 is unknown, by a reader that holds 0.9. A message of a language
    release after the reader's is read under nothing, and is reported."""
    lang = data.load("0.6", "0.9")
    assert "g.structure.dialect" in lang.items
    assert LANG.form_of("g.structure.dialect") not in lang.by_form
    assert lang.items["g.structure.dialect"].critical_code == 0
    for cls in LANG.grammar["classes"]:
        for m in cls["members"]:
            assert versions.well_formed(m["introduced"])
    later_root = "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation possess " \
        "(HOLDER (term SELF)) (UNDERGOER (term (unknown \"rowew\") DEFINITE)))))"
    refused = api.parse(written_under(later_root, "0.6", "0.9"), reader=DEVELOPMENT)
    assert [d.code for d in refused.diagnostics] == ["d.lexer.unknown-word"]
    later = api.parse(open(os.path.join(ROOT, "corpus", "negative",
                                        "n130-message-of-a-later-release.txt")).read())
    (d,) = later.diagnostics
    assert d.code == "d.parser.version-unknown" and d.detected == ["language 1.1"]


def test_a_reader_lacking_a_release_reports_what_it_reads():
    """A reader of language 0.9 alone, given a message of the current release, 1.0,
    interprets none of it and reports the language and lexicon it lacks, with what it
    reads."""
    reader = releases.Reader(language=("0.9",), lexicon=("0.6",), dialects=())
    a = api.parse(TEXTS[("s01-observed", 1)], reader=reader)
    assert a.lacking == {"language": ["1.0"], "lexicon": ["1.0"]}
    (d,) = a.diagnostics
    assert d.code == "d.parser.version-unknown" and d.expected == ["language 0.9",
                                                                   "lexicon 0.6"]
    assert d.detected == ["language 1.0", "lexicon 1.0"]


# ---------------------------------------------------------------- features

def test_the_feature_registry_flags_every_feature():
    """Every feature has a number, a release and a flag, and no may-ignore feature has a
    word that carries a critical dimension; every grammar word a release after the core
    added belongs to a feature or is a fixed form, which every reader holds."""
    registry = features.registry(LANG)
    assert [f["number"] for f in registry] == list(range(1, 12))
    for f in registry:
        assert f["flag"] in (features.MUST, features.MAY)
        assert versions.well_formed(f["introduced"])
    for item in LANG.items.values():
        number = features.of_item(item, LANG)
        if number is not None and features.flag(LANG, number) == features.MAY:
            assert item.critical_code == 0 and not item.protected, item.identifier
    fixed = set(LANG.protocol["fixed forms"])
    for cls in LANG.grammar["classes"]:
        for m in cls["members"]:
            if m["introduced"] != "0.1":
                item = LANG.items[m["identifier"]]
                assert features.of_item(item, LANG) is not None or m["identifier"] in fixed \
                    or m["identifier"] == "g.message.message-field.first-entry", m
    for s in LANG.grammar["structural words"]:
        if s["introduced"] != "0.1":
            assert features.of_item(LANG.items[s["identifier"]], LANG) is not None, s


@pytest.mark.parametrize("number", range(1, 12))
def test_a_reader_lacking_a_feature_rejects_or_passes_over_it(number):
    """Over every corpus message, a reader lacking a must-understand feature rejects
    exactly the moves that use it, naming the feature, and reads every other move as a
    reader holding the feature does; a reader lacking a may-ignore feature rejects
    nothing, and gives every move the normal form a reader holding the feature gives,
    except that a word of the feature standing as content is kept opaque, as any word a
    reader lacks is. A message that names dialects, to a reader lacking them, is
    interpreted not at all; the authentication field, which a reader lacking it passes
    over, is covered by the integrity check value it still checks."""
    flag = features.flag(LANG, number)
    reader = releases.Reader(lacking=frozenset({number}))
    used_somewhere = False
    for item_id, k, m, text in MESSAGES:
        full = api.parse(text)
        if full.message is None:
            continue
        lacking = api.parse(text, reader=reader)
        if full.message.envelope.authentication is not None and number == 10:
            used_somewhere = True
            assert plain(record(lacking)) == plain(record(full))
            continue
        if not full.moves:
            continue
        if lacking.lacking.get("features") and "d.parser.version-unknown" in [
                d.code for d in lacking.diagnostics]:
            used_somewhere = True       # a message naming dialects, the feature lacked
            assert lacking.moves == [] and full.named["dialects"]
            continue
        uses = [number in features.used_by_words(mv.body[:-1], LANG)
                for mv in full.message.moves]
        reading = {i for i, s in enumerate(full.social) if number in features.used_by_reading(
            full.moves[i], s["idioms"], LANG)}
        used_somewhere |= any(uses) or bool(reading)
        codes = [d.code for d in lacking.diagnostics]
        if flag == features.MUST:
            rejected = {i for i, u in enumerate(uses) if u or i in reading}
            assert lacking.normal == [n for i, n in enumerate(full.normal)
                                      if i not in rejected], (item_id, k)
            assert codes.count("d.parser.feature-lacking") == len(rejected), (item_id, k)
            continue
        assert "d.parser.feature-lacking" not in codes and len(lacking.normal) == len(full.normal)
        opaque = [d for d in lacking.diagnostics
                  if d.note == "a word of a feature this reader lacks"]
        if not opaque:
            assert lacking.normal == full.normal, (item_id, k)
    assert used_somewhere, "no corpus message uses feature %d" % number


def test_the_features_item_is_what_the_participants_write():
    """e9-features: B lacks the idioms and the dictions. It states so; it passes over the
    diction of A's first move and applies it; it rejects A's second move, read by an
    idiom, naming the message and the feature; and it applies A's restatement in full
    explicitness, the idiom's expansion in its place."""
    item = "e9-features"
    now = [float(T0)]
    b = Participant("2", lambda: now[0], reader=releases.Reader(dialects=(),
                                                                lacking=frozenset({3, 7})))
    b.negotiate("1")
    assert [api.parse(t).statement for _, t in b.outbox] == [
        api.parse(TEXTS[(item, 1)]).statement]
    b.outbox.clear()
    now[0] = T0 + 30
    for k in (2, 3):
        b.receive(TEXTS[(item, k)])
    assert ("1", "1") in b.view.entries and ("1", "2") not in b.view.entries
    lacks = [api.parse(t).statement for _, t in b.outbox if api.parse(t).statement["kind"] ==
             "lacks"]
    assert lacks == [api.parse(TEXTS[(item, 4)]).statement]
    b.receive(TEXTS[(item, 5)])
    assert ("1", "3") in b.view.entries
    held = api.parse(TEXTS[(item, 2)], reader=b.view.reader)
    assert held.ignored == [{"move": 1, "features": [7]}]
    assert held.normal == api.parse(TEXTS[(item, 2)]).normal


# ---------------------------------------------------------------- negotiation

def test_a_speaker_finds_no_common_subset_with_a_reader_of_another_release():
    """B reads language 0.9 and lexicon 0.6, a release 1.0 does not read; B names A's
    message of 1.0 with the releases it lacks and states what it reads, and A, holding
    that statement, finds no common subset to write in. A release that both read is the
    common one, by the rule the next test checks."""
    now = [float(T0)]
    a = Participant("1", lambda: now[0])
    b = Participant("2", lambda: now[0], reader=releases.Reader(
        language=("0.9",), lexicon=("0.6",), protocol=("0.3", "0.4"), dialects=()))
    now[0] = T0
    text = a.send(moves_of(RECORDS[("s01-observed", 1)]), ["2"])
    now[0] = T0 + 10
    b.receive(text)
    stated = [api.parse(t).statement for _, t in b.outbox]
    assert [s_["kind"] for s_ in stated] == ["lacks", "understands"]
    assert ["language", ("1.0",)] in [[p[0], tuple(p[1])] for p in stated[0]["parts"]]
    assert ["language", ("0.9",)] in [[p[0], tuple(p[1])] for p in stated[1]["parts"]]
    for _, t in b.outbox:
        a.receive(t)
    assert a.common_with("2") is None


def test_the_common_subset_is_computed_alike_by_both():
    """The common subset
    (specification/dialects.md#settling-the-dialects-two-agents-share): the latest release
    each reads of the language, a lexicon release the chosen language may name, the latest
    protocol both read, the dialects both offer under one digest, and every feature either
    lacks; computed the same from either side, and None where no language is shared. A
    reader offers the dialects it is configured to offer, none by default."""
    full = negotiation.read_statement(negotiation.understood_parts(releases.Reader(
        dialects=((2, "0.2"), (8, "0.2")))))
    assert negotiation.read_statement(negotiation.understood_parts())["dialects"] == []
    older = negotiation.read_statement(negotiation.understood_parts(releases.Reader(
        language=("0.9", "1.0"), lexicon=("0.6", "0.7", "1.0"), dialects=((2, "0.2"),),
        lacking=frozenset({3}))))
    both = negotiation.common(full, older)
    assert both == negotiation.common(older, full)
    assert both["language"] == "1.0" and both["lexicon"] == "1.0"
    assert both["dialects"] == [(2, "0.2", releases.digest_of(2, "0.2"))]
    assert both["lacking"] == [3]
    none = dict(older, language=["0.9"])
    assert negotiation.common(full, none) is None


# --------------------------------------------------- the matters of versioning

MATTERS_OF_VERSIONING = {
    "language version": "the version field's first version, read under the release named",
    "dialect version": "each dialect named in the version field with its version and digest",
    "lexicon version": "the version field's second version, the release normalisation reads",
    "protocol version": "the version field's third version, and what a protocol reads",
    "deprecated forms": "a release's deprecation of a term or form, reported and read",
    "compatibility markers": "the feature registry's must-understand and may-ignore flags",
    "feature negotiation": "UNDERSTANDS and LACKS, and the common subset both compute",
}


def test_each_matter_of_versioning_item_by_item():
    """Each of the seven matters of versioning has its mechanism, and each mechanism is
    shown at work on a corpus message; and an agent can say 'I understand version X but
    not feature Y' in a form every later version reads."""
    assert len(MATTERS_OF_VERSIONING) == 7
    named = api.parse(TEXTS[("e9-dialect-negotiation", 7)]).named
    assert (named["language"], named["lexicon"], named["protocol"]) == ("1.0", "1.0", "0.5")
    assert named["dialects"] == [(2, "0.2", releases.digest_of(2, "0.2"))]
    assert api.parse(TEXTS[("e9-deprecated-term", 1)]).deprecated
    assert {f["flag"] for f in features.registry(LANG)} == {features.MUST, features.MAY}
    stated = api.parse(TEXTS[("e9-features", 1)]).statement
    assert stated["kind"] == "understands" and ["lacking", (3, 7)] in [
        [p[0], tuple(p[1])] for p in stated["parts"] if p[0] == "lacking"]
    fixed = LANG.protocol["fixed forms"]
    for ident in LANG.protocol["fixed forms added"]["0.4"]:
        assert fixed[ident] == LANG.form_of(ident)


# ---------------------------------------------------------------- the statements' own check

STATEMENTS = [
    ("understands", [("language", ("0.9", "0.10")), ("lexicon", ("0.7",)),
                     ("protocol", ("0.4",)), ("dialect", 2, "0.2", "982007073"),
                     ("lacking", (3, 7))]),
    ("lacks", [("channel", (2,), (4,)), ("lexicon", ("0.7",)),
               ("dialect", 8, "0.2", "449435470"), ("lacking", (3,))]),
]


def _statement_words(kind: str, parts: list) -> tuple:
    """A protocol message holding the statement, without its integrity check value, and
    the number of its envelope's words, written with the release the parser now reads."""
    from rowih.writer import Writer
    w = Writer(data.load())
    env = w.envelope(sender=2, recipients=(1,), identifier=0, first_entry=0)
    words = w.message(env, [w.statement(kind, parts)]).split()
    k = words.index(w.w("g.message.message-field.integrity-check-value"))
    return words[:k] + words[k + 1 + 10:], len(env)


def _single_edits(words: list, start: int):
    """Each deletion, substitution and insertion of one word at a position from `start`
    on, with its position."""
    vocabulary = sorted({x for x in LANG.by_form if len(x) == 4})
    for i in range(start, len(words)):
        yield i, words[:i] + words[i + 1:]
        for x in vocabulary:
            if x != words[i]:
                yield i, words[:i] + [x] + words[i + 1:]
        for x in vocabulary:
            yield i, words[:i] + [x] + words[i:]


@pytest.mark.parametrize("kind,parts", STATEMENTS)
def test_every_single_edit_of_a_negotiation_statement_is_detected(kind, parts):
    """The statements of version negotiation take codes of the unit check word that other
    words also take, every residue being in use; their count, check word, numbers' check
    words and order detect every substitution, insertion and deletion of a word, the
    integrity check value aside: each edit is rejected or leaves the statement as it
    was."""
    without, start = _statement_words(kind, parts)
    original = api.parse(" ".join(without)).statement
    assert original is not None and original["kind"] == kind
    for i, edited in _single_edits(without, start):
        a = api.parse(" ".join(edited))
        assert a.statement is None or a.statement == original, (i, edited[i - 1:i + 2])


@pytest.mark.parametrize("kind,parts", STATEMENTS)
def test_the_statement_enumeration_finds_an_edit_once_the_unit_check_word_is_disabled(
        monkeypatch, kind, parts):
    """The enumeration above can fail: with every code of the unit check word's rule
    zero, the check word detects no edit of the words it covers, and some single edit
    changes what the statement states."""
    # the language the parser reads now, which an earlier test that clears the cache of
    # releases may have loaded again since this module's
    lang = data.load()
    rule = copy.deepcopy(lang.protocol["unit check word"])
    rule["codes"] = {}
    monkeypatch.setitem(lang.protocol, "unit check word", rule)
    without, start = _statement_words(kind, parts)
    original = api.parse(" ".join(without)).statement
    assert original is not None and original["kind"] == kind
    assert any(api.parse(" ".join(edited)).statement not in (None, original)
               for _, edited in _single_edits(without, start))
