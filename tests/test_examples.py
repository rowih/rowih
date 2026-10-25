"""The public page (README.md) and its examples (examples/): every file of the examples is
what tools/build_examples.py writes; a drawing of the moves differs from the toolchain's
drawing of the whole message only in its view box and its text alternative; each recording
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
from rowih.drawing import draw

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
    crops = [p for p in FILES if re.search(r"\.moves(\.[a-z]+)?\.svg$", p) and
             not p.endswith(".dark.svg")]
    assert len(crops) == len(SPEECH) + len(build_examples.WRITING) + len(
        build_examples.OTHER_FORMS)
    for path in crops:
        name, _, rest = os.path.basename(path).partition(".moves")
        form = rest[1:-len(".svg")] or "display"
        text = _corpus_text(name)
        whole = api.render(text, "svg", form=form)[0]
        assert _body(FILES[path]) == _body(whole), path
        top, width, height = map(int, re.search(r'viewBox="0 (\d+) (\d+) (\d+)"',
                                                FILES[path]).groups())
        d = draw(api.parse(text), form, lang)
        scale = 2 if form == "compact" else 1
        assert top == d.lines[1] - lang.writing["metrics"]["above"] // scale, path
        inside = [pt for p in d.paths for pt in p.points if pt[1] >= top]
        outside = [pt for p in d.paths for pt in p.points if pt[1] < top]
        assert inside and outside, path
        assert all(y <= top + height and x <= width for x, y in inside), path


def _polylines(svg: str) -> list:
    return [tuple(tuple(map(int, pt.split(","))) for pt in m.split())
            for m in re.findall(r'<polyline points="([^"]+)"/>', svg)]


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


def test_the_page_states_the_audio_check_as_recorded():
    page = read("README.md")
    rates = [r["phoneme error rate"] for r in AUDIO["messages"].values()]
    assert len(rates) == 16
    assert "The sixteen files score from %.3f to %.3f" % (min(rates), max(rates)) in page
    assert "exceeds %.2f" % AUDIO["threshold"] in page
    assert "scores %.3f and is refused" % AUDIO["control"]["phoneme error rate"] in page
    for name, plan in SPEECH.items():
        assert "`%s`" % plan["voice"] in page, name


# -------------------------------------------------------------------- the page
def _code_blocks(text: str) -> list:
    return re.findall(r"```(?:text|sh)\n(.*?)```", text, re.S)


def test_every_move_the_page_shows_is_the_corpus_s():
    page = read("README.md")
    blocks = _code_blocks(page)
    shown = re.findall(r'<img src="examples/media/([a-z0-9.-]+)\.moves\.svg"', page)
    assert len(shown) == 6
    for name in shown:
        text = _corpus_text(name)
        assert text.splitlines()[1] + "\n" in blocks, name
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
