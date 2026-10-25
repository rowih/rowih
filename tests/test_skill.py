"""The skill in the Agent Skills format (skill/rowih): valid by the format's reference
validator, its references what tools/build_skill.py writes from the data and the
specification, and everything it tells an agent true of the toolchain: each example
move writes without a diagnostic, each tool and command it names exists, and each file
it links is in the skill."""
import re
import shlex
import sys
from pathlib import Path

from rowih import api, cli
from rowih.server import Server
from rowih.writer import Envelope

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skill" / "rowih"
TEXT = (SKILL / "SKILL.md").read_text(encoding="utf-8")
FRONT, BODY = TEXT.split("---\n")[1], TEXT.split("---\n", 2)[2]
sys.path.insert(0, str(ROOT / "tools"))


def test_the_skill_is_valid_by_the_reference_validator():
    from skills_ref import read_properties, validate
    assert validate(SKILL) == []
    properties = read_properties(SKILL)
    assert properties.name == "rowih" == SKILL.name
    assert len(properties.description) <= 1024 and len(properties.compatibility) <= 500


def test_the_validator_refuses_a_skill_that_breaks_the_format(tmp_path):
    from skills_ref import validate
    bad = tmp_path / "rowih"
    bad.mkdir()
    (bad / "SKILL.md").write_text(TEXT.replace("name: rowih", "name: Rowih"), encoding="utf-8")
    assert validate(bad) != []


def test_the_body_keeps_to_the_size_the_format_recommends():
    assert len(BODY.splitlines()) < 500
    # under about 5,000 tokens, at the four characters a token the format's guidance
    # assumes for English
    assert len(BODY) < 20000


def test_the_metadata_names_the_releases_the_toolchain_is():
    version = api.version()
    for key in ("language", "lexicon", "protocol"):
        assert '%s: "%s"' % (key, version[key]) in FRONT


def test_the_references_are_what_the_build_writes():
    import build_skill
    for path, text in build_skill.references().items():
        assert (SKILL / path).read_text(encoding="utf-8") == text, path


def test_the_references_cite_nothing_outside_the_skill():
    for path in (SKILL / "references").iterdir():
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)]+)\)", text):
            assert target.startswith("#"), (path.name, target)


def test_every_file_the_skill_links_is_in_the_skill():
    targets = re.findall(r"\]\(([^)#]+)", BODY)
    assert targets and all((SKILL / t).is_file() for t in targets)


def _example_moves() -> list:
    blocks = re.findall(r"```\n(.*?)```", BODY, re.S)
    return [line for block in blocks for line in block.splitlines()
            if line.startswith("(move ")]


def test_each_example_move_writes_without_a_diagnostic():
    moves = _example_moves()
    assert len(moves) == 5
    for move in moves:
        # a move that names participant 1's entry is participant 2's reply to it
        reply = "(names 1 " in move
        text, diags = api.write(move, Envelope(2 if reply else 1, (1,) if reply else (2,),
                                               1761300000))
        assert diags == [], (move, [d.code for d in diags])


def test_each_tool_the_skill_names_is_a_tool_of_the_server():
    offered = {t.name for t in Server().offer.tools}
    table = BODY.split("| Task | Tool | Command |")[1].split("\n\n")[0]
    named = set(re.findall(r"^\| [^|]+ \| `([a-z_]+)`", table, re.M))
    assert named and named <= offered
    resources = set(re.findall(r"`(rowih://[a-z/]+)`", BODY))
    assert resources and resources <= set(Server().offer.resources)


def test_each_command_the_skill_shows_parses(tmp_path, capsys):
    commands = re.findall(r"`(rowih [^`]+)`", BODY) + [
        line for line in re.findall(r"```\n(.*?)```", BODY, re.S)
        for line in line.splitlines() if line.startswith("rowih ")]
    assert len(commands) > 8
    moves = tmp_path / "moves.txt"
    moves.write_text(_example_moves()[0], encoding="utf-8")
    message = tmp_path / "message.txt"
    message.write_text(api.write(_example_moves()[0], Envelope(1, (2,), 1761300000))[0],
                       encoding="utf-8")
    for command in commands:
        words = shlex.split(command.replace("[N ...]", "").replace("TERM", "run")
                            .replace("KIND", "understands"))[1:]
        # `write` reads moves in the notation; every other command reads a message
        source = moves if words[0] == "write" else message
        words = [str(moves) if w == "moves.txt" else str(source) if w == "FILE" else
                 "1" if w == "N" else w for w in words]
        if words[0] == "write" and "--time" not in words:
            words += ["--time", "1761300000"]
        if words[0] == "render":
            words += ["-o", str(tmp_path / "out.svg")]
        assert cli.main(words) == 0, command
        capsys.readouterr()


def test_the_skill_says_what_a_message_looks_like_truly():
    # a move without a payload, whose words are all the language's own
    move = next(m for m in _example_moves() if "(data " not in m)
    text = api.write(move, Envelope(1, (2,), 1761300000))[0]
    assert text.split()[0] == "wila" and "wila" in FRONT
    native = api.convert(text, "native")[0]
    assert all("" <= ch <= "" for ch in native if not ch.isspace())
    assert "U+F3A0 to U+F3B2" in FRONT and "text/prs.rowih" in TEXT
