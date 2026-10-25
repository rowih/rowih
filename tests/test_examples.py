"""The public page (README.md) and its examples (examples/): every file of the examples is
what tools/build_examples.py writes; a drawing of the moves differs from the toolchain's
drawing of the whole message only in its view box and its text alternative; each row the
page draws is the toolchain's line layout of its words, reads back as them, breaks only
where a break is allowed and fits GitHub's column, and the page shows under it exactly its
words; each recording
is of the message as it now reads, is the file the audio tool checked, and passed a check
that a planted defect failed; the page's opening exchange is the corpus's, its figures
are the specification's, its quick start runs as written, and it cites nothing outside the
public repository and links only what exists."""
import hashlib
import json
import os
import re
import subprocess
import sys

from rowih import api, data, writing
from rowih.drawing import draw, read as read_drawing
from rowih.speech import spoken

from test_specification import LINK, anchors, cites_a_section

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import build_examples  # noqa: E402

PAGES = ["README.md", "examples/README.md"]
FILES = build_examples.files()


def read(path: str) -> str:
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def _json(path: str) -> dict:
    return json.loads(read(path))


# ---------------------------------------------------------------- the examples
def test_the_examples_are_what_the_build_writes():
    for path, content in FILES.items():
        target = os.path.join(build_examples.EXAMPLES, path)
        if isinstance(content, bytes):
            with open(target, "rb") as f:
                assert f.read() == content, path
        else:
            assert read(os.path.join("examples", path)) == content, path
    drawn = {p for p in os.listdir(os.path.join(ROOT, "examples", "media"))
             if not p.endswith(".mp3")}
    assert drawn == {p.split("/", 1)[1] for p in FILES if p.startswith("media/")}


def _body(svg: str) -> str:
    return svg.split("</desc>", 1)[1]


def _corpus_text(name: str) -> str:
    corpus_set = "adversarial" if name.startswith("a0") else "domains"
    return read("corpus/%s/%s.txt" % (corpus_set, name))


def test_a_drawing_of_the_moves_is_the_whole_drawing_cropped():
    lang = data.load()
    crops = [p for p in FILES if p.endswith(".moves.svg")]
    assert len(crops) == len([name for name in SPEECH if not name.endswith(".moves")])
    for path in crops:
        name = os.path.basename(path)[:-len(".moves.svg")]
        text = _corpus_text(name)
        whole = api.render(text, "svg")[0]
        assert _body(FILES[path]) == _body(whole), path
        top, width, height = map(int, re.search(r'viewBox="0 (\d+) (\d+) (\d+)"',
                                                FILES[path]).groups())
        d = draw(api.parse(text), "display", lang)
        assert top == d.lines[1] - lang.writing["metrics"]["above"], path
        inside = [pt for p in d.paths for pt in p.points if pt[1] >= top]
        outside = [pt for p in d.paths for pt in p.points if pt[1] < top]
        assert inside and outside, path
        assert all(y <= top + height and x <= width for x, y in inside), path


def _polylines(svg: str) -> list:
    return [tuple(tuple(map(int, pt.split(","))) for pt in m.split())
            for m in re.findall(r'<polyline points="([^"]+)"/>', svg)]


def _is_numeral(word, lang) -> bool:
    return word.item is not None and word.item.class_id == lang.writing["numbers"]["class"]


def test_each_row_reads_back_as_its_words_breaks_where_allowed_and_fits_the_column():
    lang = data.load()
    walls = lang.writing["walls"]
    for _, name, forms in build_examples.ROWS:
        words, ceremonial = build_examples._move(name, lang)
        rows = build_examples.rows(words, lang)
        assert len(rows) > 1 and [w for row in rows for w in row] == words, name
        end = 0
        for row in rows[:-1]:
            end += len(row)
            assert not (_is_numeral(words[end - 1], lang) and _is_numeral(words[end], lang))
            ident = [w.item.identifier if w.item is not None else "" for w in words[:end]]
            assert ident.count(walls["opens"]) == ident.count(walls["closes"]), name
        for form in forms:
            for k, row in enumerate(rows, 1):
                d = build_examples.row_drawing(row, lang, form, ceremonial)
                assert read_drawing(d, lang) == [[w.form for w in row]], (name, form, k)
                svg = FILES[build_examples.row_path(name, k, form)]
                assert sorted(_polylines(svg)) == sorted(p.points for p in d.paths)
                size = re.search(r'viewBox="0 0 (\d+) (\d+)" width="(\d+)" height="(\d+)"', svg)
                assert tuple(map(int, size.groups())) == (
                    d.width, d.height, round(d.width * build_examples.SCALE),
                    round(d.height * build_examples.SCALE)), (name, form, k)
                assert build_examples.row_drawing(row, lang).width <= build_examples.ROW_LIMIT


def test_a_move_laid_out_as_one_row_is_its_line_in_the_whole_drawing():
    """The rows are the toolchain's line layout, the ceremonial variant included: laid out
    whole, a move's words are the move's line of the toolchain's drawing of the message."""
    lang = data.load()
    above = lang.writing["metrics"]["above"]
    checked = set()
    for _, name, forms in build_examples.ROWS:
        words, ceremonial = build_examples._move(name, lang)
        for form in (f for f in forms if f != "compact"):
            whole = draw(api.parse(_corpus_text(name)), form, lang)
            top = whole.lines[1] - above
            d = build_examples.row_drawing(words, lang, form, ceremonial)
            dy = whole.lines[1] - d.lines[0]
            line = sorted((p.points, p.weight) for p in whole.paths
                          if min(y for _, y in p.points) >= top)
            assert sorted((tuple((x, y + dy) for x, y in p.points), p.weight)
                          for p in d.paths) == line, (name, form)
            assert [(t.x, t.y + dy, t.text) for t in d.texts] == [
                (t.x, t.y, t.text) for t in whole.texts if t.y >= top], (name, form)
            checked.add((form, ceremonial))
    assert checked == {("display", False), ("display", True), ("handwritten", False)}


def test_the_page_s_rows_are_what_the_build_writes():
    lang = data.load()
    page = read("README.md")
    assert build_examples.page(page, lang) == page
    regions = {(m["name"], m["form"]) for m in build_examples.ROW_REGION.finditer(page)}
    assert regions == {(n, f) for _, n, forms in build_examples.ROWS for f in forms}


def test_the_chart_draws_each_component_by_its_pen_strokes():
    lang = data.load()
    drawn = _polylines(FILES["media/components.svg"])
    expected = []
    for kind_row, kind in enumerate(("consonant", "vowel")):
        row = [s for s in lang.phonology["symbols"] if s["kind"] == kind]
        for i, s in enumerate(row):
            x = build_examples.MARGIN + i * build_examples.CELL + (build_examples.CELL - 12) // 2
            y = build_examples.MARGIN + kind_row * build_examples.ROW
            expected += [tuple((px + x, py + y) for px, py in pen)
                         for pen in writing.pen_strokes(s["letter"], lang)]
            assert ">%s</text>" % s["letter"] in FILES["media/components.svg"]
            assert ">/%s/</text>" % s["ipa"] in FILES["media/components.svg"]
    assert drawn == expected and len(set(drawn)) == len(drawn)


def test_the_name_is_drawn_as_the_specification_draws_a_word():
    lang = data.load()
    gap = lang.writing["metrics"]["gap"]
    name = build_examples.NAME
    expected = [tuple((px + build_examples.MARGIN + i * (12 + gap), py + build_examples.MARGIN)
                      for px, py in pen)
                for i, ch in enumerate(name) for pen in writing.pen_strokes(ch, lang)]
    assert _polylines(FILES["media/%s.svg" % name]) == expected
    width = int(re.search(r'viewBox="0 0 (\d+)', FILES["media/%s.svg" % name]).group(1))
    assert width - 2 * build_examples.MARGIN == 16 * len(name) - 4


def test_the_dark_drawing_differs_only_in_its_ink():
    for path, content in FILES.items():
        if path.endswith(".dark.svg"):
            light = FILES[path.replace(".dark.svg", ".svg")]
            assert content == light.replace("currentColor", build_examples.DARK_INK), path
            assert "currentColor" in light and "currentColor" not in content


# ------------------------------------------------------------------- the audio
AUDIO = _json("examples/audio.json")
SPEECH = _json("examples/speech.json")


def test_each_recording_is_of_the_message_as_it_now_reads():
    assert set(AUDIO["messages"]) == set(SPEECH)
    for name, plan in SPEECH.items():
        digest = hashlib.sha256(json.dumps(plan, ensure_ascii=False, sort_keys=True)
                                .encode("utf-8")).hexdigest()
        assert AUDIO["messages"][name]["plan"] == digest, name
        assert AUDIO["messages"][name]["voice"] == build_examples.VOICES[plan["sender"]]


def test_each_recording_is_the_file_the_audio_tool_checked():
    for name, result in AUDIO["messages"].items():
        with open(os.path.join(ROOT, "examples", "media", name + ".mp3"), "rb") as f:
            assert hashlib.sha256(f.read()).hexdigest() == result["mp3"], name


def test_each_recording_passed_a_check_that_a_planted_defect_failed():
    tool = read("tools/speak_examples.py")
    threshold = float(re.search(r"^THRESHOLD = ([0-9.]+)", tool, re.M).group(1))
    assert AUDIO["threshold"] == threshold
    assert all(r["phoneme error rate"] <= threshold for r in AUDIO["messages"].values())
    assert AUDIO["control"]["phoneme error rate"] > threshold
    for model in ("voice model", "recogniser"):
        assert re.fullmatch(r"[0-9a-f]{40}", AUDIO[model]["revision"])
        assert AUDIO[model]["revision"] in tool


def test_the_page_plays_the_moves_it_shows_and_the_examples_each_message_whole():
    page = read("README.md")
    linked = re.findall(r"\[listen \(MP3\)\]\(examples/media/([a-z0-9.-]+)\.mp3\)", page)
    assert linked == [build_examples.OPENING + ".1.moves", build_examples.OPENING + ".2.moves"]
    for name in linked:
        spoken_form = [line["ipa"] for line in spoken(api.parse(_corpus_text(name[:-6])))]
        assert [line["ipa"] for line in SPEECH[name]["lines"]] == spoken_form[1:], name
    examples = read("examples/README.md")
    for name in re.findall(r"\[Spoken \(MP3\)\]\(media/([a-z0-9.-]+)\.mp3\)", examples):
        spoken_form = [line["ipa"] for line in spoken(api.parse(_corpus_text(name)))]
        assert [line["ipa"] for line in SPEECH[name]["lines"]] == spoken_form, name


def test_the_page_states_the_audio_check_as_recorded():
    page = read("README.md")
    rates = [r["phoneme error rate"] for r in AUDIO["messages"].values()]
    assert len(rates) == 18
    assert "The eighteen files score from %.3f to %.3f" % (min(rates), max(rates)) in page
    assert "exceeds %.2f" % AUDIO["threshold"] in page
    assert "scores %.3f and is refused" % AUDIO["control"]["phoneme error rate"] in page
    for name, plan in SPEECH.items():
        assert "`%s`" % plan["voice"] in page, name


# -------------------------------------------------------------------- the page
def _code_blocks(text: str) -> list:
    return re.findall(r"```(?:text|sh)\n(.*?)```", text, re.S)


def test_every_move_the_page_shows_is_the_corpus_s():
    page = read("README.md")
    regions = list(build_examples.ROW_REGION.finditer(page))
    assert len([m for m in regions if m["form"] == "display"]) == 6
    for m in regions:
        name, form = m["name"], m["form"]
        text = _corpus_text(name)
        under = re.findall(r"</picture><br>\n`([^`]+)`", m.group(0))
        assert " ".join(under) == text.splitlines()[1], (name, form)
        suffix = "" if form == "display" else "." + form
        assert re.findall(r'<img src="examples/media/([a-z0-9.-]+)\.svg"', m.group(0)) == [
            "%s.row%d%s" % (name, k, suffix) for k in range(1, len(under) + 1)], (name, form)
        english = api.translate(text)[0].splitlines()[0]
        assert "*%s*" % english in page, name
    first = read("corpus/domains/casual-056.1.txt").splitlines()
    total, envelope = sum(len(line.split()) for line in first), len(first[0].split())
    assert "has %d words, %d of them its envelope" % (total, envelope) in page
    assert "envelope line of %d words" % envelope in page


def test_the_page_s_figures_are_the_specification_s():
    page, spec = read("README.md"), read("specification/conformance.md")
    lexicon = read("specification/lexicon.md")
    for figure in ("7,089,953", "84,233,102", "139,033", "14 | 23", "2.16", "5.85",
                   "382 messages", "by 13 tokenizers"):
        assert figure in spec, figure
    for figure in ("7,089,953", "84,233,102", "139,033", "14 messages", "2.16", "5.85",
                   "382 messages", "thirteen tokenizers"):
        assert figure in page, figure
    ratio = re.search(r"English explanation's \| ([0-9.]+) \|", spec).group(1)
    assert "about %.1f times" % float(ratio) in page
    assert "make 60 demands" in spec and "60 demands" in page
    assert "all 94 planted defects are caught" in spec and "all 94 are caught" in page
    assert "| **entries in all** | 874 |" in lexicon and "874 entries" in page
    assert "| 500 |" in lexicon and "500 of them roots" in page


def test_the_quick_start_runs_as_written(tmp_path):
    page = read("README.md")
    blocks = [b for b in _code_blocks(page) if "rowih write" in b or "rowih validate" in b]
    assert len(blocks) == 2
    shim = "rowih() { %s -c 'import sys; from rowih.cli import main; sys.exit(main())' " \
           "\"$@\"; }\n" % sys.executable
    env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "python"))
    run = [subprocess.run(["bash", "-c", shim + b], cwd=tmp_path, env=env,
                          capture_output=True, text=True, timeout=120) for b in blocks]
    assert run[0].returncode == 0, run[0].stderr
    assert run[0].stdout.startswith("valid\nAgent 1 asks that run the service (polar).")
    assert run[1].returncode == 1
    assert "d.lexer.unknown-word" in run[1].stderr and "found kihiwa" in run[1].stderr


DESCRIPTION = "python/README.md"  # the package's description on PyPI
REPOSITORY = "https://github.com/rowih/rowih/blob/"


def test_the_package_s_description_links_its_own_release():
    pyproject = read("pyproject.toml")
    assert 'readme = "%s"' % DESCRIPTION in pyproject
    version = re.search(r'^version = "([0-9.]+)"', pyproject, re.M).group(1)
    text = read(DESCRIPTION)
    ours = [link for link in re.findall(r"\]\(([^)]+)\)", text) if link.startswith(REPOSITORY)]
    assert len(ours) >= 6 and not cites_a_section(text)
    for link in ours:
        tag, _, path = link[len(REPOSITORY):].partition("/")
        assert tag == "v" + version, link
        path, _, anchor = path.partition("#")
        # a file only the public repository has is in release/public here, and at the root there
        target = next((p for p in (os.path.join(ROOT, "release", "public", path),
                                   os.path.join(ROOT, path)) if os.path.exists(p)), None)
        assert target, link
        if anchor:
            with open(target, encoding="utf-8") as f:
                assert anchor in anchors(f.read()), link
    extras = set(re.findall(r"^(\w+) = \[", pyproject.split("[project.optional-dependencies]")[1]
                            .split("\n[")[0], re.M))
    assert set(re.findall(r"rowih\[(\w+)\]", text)) == extras == {"speech", "authentication"}


def test_the_package_s_description_runs_as_written(tmp_path):
    blocks = re.findall(r"```(sh|python)\n(.*?)```", read(DESCRIPTION), re.S)
    shell = [b for kind, b in blocks if kind == "sh" and "pip install" not in b]
    python = [b for kind, b in blocks if kind == "python"]
    assert len(shell) == 2 and len(python) == 1
    shim = "rowih() { %s -c 'import sys; from rowih.cli import main; sys.exit(main())' " \
           "\"$@\"; }\n" % sys.executable
    env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "python"))
    run = [subprocess.run(["bash", "-c", shim + b], cwd=tmp_path, env=env,
                          capture_output=True, text=True, timeout=120) for b in shell]
    assert run[0].returncode == 0, run[0].stderr
    assert run[0].stdout.startswith("valid\nAgent 1 asks that run the service (polar).")
    assert run[1].returncode == 1 and "d.lexer.unknown-word" in run[1].stderr
    out = subprocess.run([sys.executable, "-c", python[0]], cwd=tmp_path, env=env,
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    assert out.stdout.startswith("[]\nAgent 1 asks that run the service (polar).")


def test_the_page_cites_no_section_but_a_standard_s():
    for path in PAGES:
        assert not cites_a_section(read(path)), path


def test_every_link_and_image_the_page_names_exists():
    for path in PAGES:
        text = read(path)
        here = os.path.dirname(os.path.join(ROOT, path))
        links = LINK.findall(text) + re.findall(r'(?:src|srcset)="([^"]+)"', text)
        assert len(links) > 10, path
        for link in links:
            if re.match(r"[a-z]+:", link):
                continue
            target, _, anchor = link.partition("#")
            target = os.path.normpath(os.path.join(here, target)) if target else \
                os.path.join(ROOT, path)
            assert os.path.exists(target), (path, link)
            if anchor:
                with open(target, encoding="utf-8") as f:
                    assert anchor in anchors(f.read()), (path, link)
