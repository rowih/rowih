"""The writer's interface (specification/conformance.md#the-interfaces): a message written
from the notation under the envelope its writer gives, read back so that the writer sees
its diagnostics before sending it; the errors of a writer's input, raised and never
reported as diagnostics; and the commands that write and read, whose options take
effect."""
import os
import random
import time

import pytest

from rowih import api, cli, data
from rowih.diagnostics import InputError
from rowih.notation import NotationError, Printer
from rowih.writer import FIXED_ENVELOPE, Envelope, EnvelopeError, OptionError

from corpus import in_current_release, items, moves_of

LANG = data.load()
NOTATION = ("(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (OBSERVATION-TIME 5 "
            "MINUTE AGO) (situation run POLARITY.NEGATIVE (UNDERGOER (term service "
            "DEFINITE)))))")
REQUEST = ("(move ISSUE REQUEST SPEAKERS-OWN (deadline 2 HOUR HENCE) (situation examine "
           "(ACTOR (term (party 2))) (UNDERGOER (term fault DEFINITE))))")


def envelope_of(text):
    return api.parse(text).message.envelope


# ------------------------------------------------------------------ the envelope
def test_an_envelope_takes_its_values_as_a_writer_gives_them():
    e = Envelope(3, [1, 2], 1761300000, identifier=4, first_entry=9,
                 dialects=[(2, "0.3"), (1, "0.3")], semantic=True)
    assert e.recipients == (1, 2) and e.time == "1761300000"
    assert e.dialects == ((1, "0.3"), (2, "0.3"))
    assert Envelope(1, (2,), "1761300000.25").time == "1761300000.25"


@pytest.mark.parametrize("args,kwargs", [
    ((-1, (2,), "1"), {}), ((True, (2,), "1"), {}), (("1", (2,), "1"), {}),
    ((1, "2", "1"), {}), ((1, 2, "1"), {}), ((1, (2, -3), "1"), {}),
    ((1, (2,), "noon"), {}), ((1, (2,), 1.5), {}), ((1, (2,), "1e9"), {}),
    ((1, (2,), "1"), {"identifier": 1.0}), ((1, (2,), "1"), {"first_entry": -1}),
    ((1, (2,), "1"), {"dialects": [(99, "0.1")]}), ((1, (2,), "1"), {"dialects": [3]}),
    ((1, (2,), "1"), {"semantic": "yes"}), ((1, (2,), "1"), {"integrity": 1}),
])
def test_envelope_values_that_cannot_be_written_are_refused(args, kwargs):
    with pytest.raises(EnvelopeError):
        Envelope(*args, **kwargs)


def test_the_fixed_envelope_is_the_one_generate_always_wrote():
    assert (FIXED_ENVELOPE.sender, FIXED_ENVELOPE.recipients, FIXED_ENVELOPE.time,
            FIXED_ENVELOPE.identifier, FIXED_ENVELOPE.first_entry) == (
        1, (2,), "1759622400", 1, 1)
    assert api.generate(NOTATION) == api.generate(NOTATION, envelope=FIXED_ENVELOPE)


# ---------------------------------------------------------------------- writing
def test_write_writes_the_envelope_the_writer_gives():
    text, diags = api.write(REQUEST, Envelope(3, (1, 2), "1761300000.5", identifier=12,
                                              first_entry=40, semantic=True))
    assert diags == []
    e = envelope_of(text)
    assert (e.sender.text, [r.text for r in e.recipients], e.time.text, e.identifier.text,
            e.first_entry.text) == ("3", ["1", "2"], "1761300000.5", "000012", "40")
    a = api.parse(text)
    assert a.confidence == "verified" and e.semantic is not None
    assert api.check_values(text)["semantic"]["stated"] == \
        api.check_values(text)["semantic"]["computed"]


def test_write_names_the_dialects_its_envelope_names():
    text, diags = api.write(NOTATION, Envelope(1, (2,), 1761300000, dialects=[(1, "0.3")]))
    assert diags == []
    assert [d[:2] for d in api.parse(text).named["dialects"]] == [(1, "0.3")]


def test_write_is_the_transliteration_generate_writes_under_the_same_envelope():
    printer = Printer(LANG)
    rng = random.Random(20261024)
    moves = [m for item in items() for m in item["messages"] if in_current_release(m)]
    envelope = Envelope(2, (1, 3), 1761300000, identifier=5, first_entry=7)
    for m in rng.sample(moves, 25):
        notation = " ".join(printer.move(t) for t in moves_of(m))
        assert api.write(notation, envelope)[0] == \
            api.generate(notation, envelope=envelope)["transliteration"]


def test_write_reports_what_reading_its_message_finds():
    text, diags = api.write("(move)", Envelope(1, (2,), 1761300000))
    assert text and diags and diags == api.parse(text).diagnostics


def test_a_register_is_named_by_its_code_or_its_name():
    e = Envelope(1, (2,), 1761300000)
    assert api.write(NOTATION, e, register="R4") == api.write(NOTATION, e, register="formal")


@pytest.mark.parametrize("kwargs", [{"register": "posh"}, {"mode": "loud"},
                                    {"diction": "grumpy"}, {"register": 4}])
def test_options_the_language_lacks_are_refused(kwargs):
    with pytest.raises(OptionError):
        api.write(NOTATION, Envelope(1, (2,), 1761300000), **kwargs)
    with pytest.raises(OptionError):
        api.generate(NOTATION, **kwargs)


def test_a_writer_s_input_errors_are_one_class():
    for error in (NotationError, EnvelopeError, OptionError):
        assert issubclass(error, InputError) and issubclass(error, ValueError)
    with pytest.raises(InputError):
        api.write("(move", Envelope(1, (2,), 1))


# ----------------------------------------------------------- reading's options
def test_a_lexicon_release_not_held_is_refused_and_a_held_one_read():
    text = api.write(NOTATION, Envelope(1, (2,), 1761300000))[0]
    assert api.parse(text, lexicon="1.0").diagnostics == []
    a = api.parse(text, lexicon="0.9")
    assert [d.code for d in a.diagnostics] == ["d.parser.unexpected-word"]
    assert a.diagnostics[0].detected == ["0.9"] and a.message is None
    words, diags = api.tokenize(text, lexicon="0.9")
    assert words == [] and diags[0].expected == ["1.0"]


# ------------------------------------------------------------------ the command
def _source(tmp_path, notation=NOTATION):
    path = tmp_path / "moves.txt"
    path.write_text(notation, encoding="utf-8")
    return str(path)


def test_the_write_command_prints_the_message_to_send(tmp_path, capsys):
    assert cli.main(["write", _source(tmp_path), "--sender", "3", "--recipients", "1", "2",
                     "--time", "1761300000", "--identifier", "4", "--first-entry", "9",
                     "--register", "formal"]) == 0
    out = capsys.readouterr()
    assert out.err == ""
    assert out.out == api.write(NOTATION, Envelope(3, (1, 2), 1761300000, identifier=4,
                                                   first_entry=9), register="R4")[0]


def test_the_write_command_takes_the_current_time_where_none_is_given(tmp_path, capsys):
    before = int(time.time())
    assert cli.main(["write", _source(tmp_path), "--sender", "1", "--recipients", "2"]) == 0
    stated = int(envelope_of(capsys.readouterr().out).time.text)
    assert before <= stated <= int(time.time())


def test_the_write_command_exits_one_on_a_diagnostic_and_two_on_bad_input(tmp_path, capsys):
    assert cli.main(["write", _source(tmp_path, "(move)"), "--sender", "1",
                     "--recipients", "2", "--time", "1"]) == 1
    assert capsys.readouterr().err.startswith("d.")
    assert cli.main(["write", _source(tmp_path, "(move FOO)"), "--sender", "1",
                     "--recipients", "2"]) == 2
    assert capsys.readouterr().err.startswith("NotationError: no member glossed FOO")
    assert cli.main(["write", _source(tmp_path), "--sender", "1", "--recipients", "2",
                     "--time", "noon"]) == 2
    assert capsys.readouterr().err.startswith("EnvelopeError")
    assert cli.main(["write", _source(tmp_path), "--sender", "1", "--recipients", "2",
                     "--dialect", "x", "0.1"]) == 2
    assert cli.main(["write", _source(tmp_path), "--recipients", "2"]) == 2


def test_the_generate_command_writes_under_the_envelope_given(tmp_path, capsys):
    assert cli.main(["generate", _source(tmp_path), "--sender", "5", "--recipients", "6",
                     "--time", "1761300000"]) == 0
    out = capsys.readouterr().out
    standard = out.split("== standard form\n")[1].split("\n== ")[0]
    assert envelope_of(standard).sender.text == "5"
    assert cli.main(["generate", _source(tmp_path), "--mode", "loud"]) == 2


def test_the_reading_commands_take_their_options(tmp_path, capsys):
    text = api.write(NOTATION, Envelope(1, (2,), 1761300000))[0]
    path = tmp_path / "message.txt"
    path.write_text(text, encoding="utf-8")
    assert cli.main(["parse", str(path), "--lexicon", "1.0"]) == 0
    assert cli.main(["parse", str(path), "--lexicon", "0.9"]) == 2
    assert cli.main(["tokenize", str(path), "--lexicon", "1.0"]) == 0
    assert cli.main(["tokenize", str(path), "--lexicon", "0.9"]) == 2
    # a declared encoding changed nothing the commands print, and is no option of theirs
    assert cli.main(["tokenize", str(path), "--encoding", "native"]) == 2


def test_the_summary_command_prints_the_summary_and_the_listing(capsys):
    from rowih import summary
    assert cli.main(["summary", "grammar"]) == 0
    assert capsys.readouterr().out == summary.grammar(LANG)
    assert cli.main(["summary", "lexicon"]) == 0
    assert capsys.readouterr().out == summary.lexicon(LANG)


def test_the_package_states_the_version_its_metadata_states():
    import os
    import tomllib
    import rowih
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "pyproject.toml"), "rb") as f:
        assert rowih.__version__ == tomllib.load(f)["project"]["version"]


# ----------------------------------------------------------- protocol messages
LACKING = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "corpus",
                       "negative", "n123-dialect-under-another-digest.txt")


@pytest.mark.parametrize("kind,kwargs,parts", [
    ("understands", {}, [["language", ["1.0"]], ["lexicon", ["1.0"]], ["protocol", ["0.5"]]]),
    ("holds", {"channels": [((2,), (3,)), ((2, 3), (1, 4))]},
     [["channel", [2], [3]], ["channel", [2, 3], [1, 4]]]),
    ("send-again", {"channels": [((2,), (4, 5))], "entries": [7]},
     [["channel", [2], [4, 5]], ["entries", [7]]]),
    ("not-held", {"entries": [1, 2]}, [["entries", [1, 2]]]),
])
def test_state_writes_each_statement_as_a_protocol_message(kind, kwargs, parts):
    text, diags = api.state(kind, 2, 1, 1761300000, **kwargs)
    assert diags == []
    a = api.parse(text)
    env = a.message.envelope
    assert (env.sender.text, [r.text for r in env.recipients], env.identifier.integer(),
            env.first_entry.integer()) == ("2", ["1"], 0, 0)
    assert a.statement["kind"] == kind
    assert [[p[0]] + [list(x) if isinstance(x, tuple) else x for x in p[1:]]
            for p in a.statement["parts"]] == parts


def test_lacks_names_the_message_and_what_of_it_the_reader_lacks():
    with open(LACKING, encoding="utf-8") as f:
        about = f.read()
    a = api.parse(about)
    sender = int(a.message.envelope.sender.text)
    text, diags = api.state("lacks", 2, sender, 1761300000, about=about)
    assert diags == []
    parts = api.parse(text).statement["parts"]
    assert parts[0] == ["channel", tuple(int(r.text) for r in a.message.envelope.recipients),
                        (a.message.envelope.identifier.integer(),)]
    assert parts[1] == ["dialect"] + list(a.lacking["dialects"][0])


@pytest.mark.parametrize("kind,kwargs", [
    ("shout", {}), ("holds", {}), ("holds", {"entries": [1], "channels": [((2,), (1,))]}),
    ("understands", {"entries": [1]}), ("send-again", {}), ("lacks", {}),
    ("lacks", {"about": "wila"}), ("holds", {"about": "x", "channels": [((2,), (1,))]}),
    ("holds", {"channels": [((2,), ())]}), ("holds", {"channels": [(2, (1,))]}),
    ("holds", {"channels": [((-2,), (1,))]}), ("not-held", {"entries": [True]}),
])
def test_statement_parts_that_cannot_be_written_are_refused(kind, kwargs):
    with pytest.raises(api.StatementError):
        api.state(kind, 2, 1, 1761300000, **kwargs)


def test_lacks_goes_only_to_the_sender_of_a_message_it_lacks():
    with open(LACKING, encoding="utf-8") as f:
        about = f.read()
    sender = int(api.parse(about).message.envelope.sender.text)
    with pytest.raises(api.StatementError, match="goes to the sender"):
        api.state("lacks", 2, sender + 1, 1761300000, about=about)
    held = api.write(NOTATION, Envelope(1, (2,), 1761300000))[0]
    with pytest.raises(api.StatementError, match="lacks nothing"):
        api.state("lacks", 2, 1, 1761300000, about=held)


def test_the_state_command_writes_a_protocol_message(tmp_path, capsys):
    assert cli.main(["state", "holds", "--sender", "2", "--recipient", "1", "--time",
                     "1761300000", "--channel", "2", "--serials", "3"]) == 0
    assert capsys.readouterr().out == api.state("holds", 2, 1, 1761300000,
                                                channels=[((2,), (3,))])[0]
    with open(LACKING, encoding="utf-8") as f:
        sender = api.parse(f.read()).message.envelope.sender.text
    assert cli.main(["state", "lacks", "--sender", "9", "--recipient", sender, "--time",
                     "1761300000", "--about", LACKING]) == 0
    assert api.parse(capsys.readouterr().out).statement["kind"] == "lacks"
    assert cli.main(["state", "lacks", "--sender", "9", "--recipient", str(int(sender) + 1),
                     "--about", LACKING]) == 2
    assert capsys.readouterr().err.startswith("StatementError")
    assert cli.main(["state", "holds", "--sender", "2", "--recipient", "1",
                     "--channel", "2"]) == 2
    assert cli.main(["state", "shout", "--sender", "2", "--recipient", "1"]) == 2
