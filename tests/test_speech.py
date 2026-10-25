"""The spoken form (specification/sounds-and-words.md#the-spoken-form): every phoneme
rendered by espeak-ng as the phonology states it, with the stress on each word's first
syllable; each line in the prosody its register's setting names, which changes no phoneme;
and a stream of phonemes without stresses or pauses divided into its words in one way only
(`inv.speech-decodable`)."""
import pytest

from rowih import api, data, speech, synthesis

from corpus import messages

LANG = data.load()
IPA = {s["letter"]: s["ipa"] for s in LANG.phonology["symbols"]}


def _rendered(phonemes):
    return [p for p in phonemes if p not in ("_", "_:")]


def test_every_word_of_the_lexicon_is_rendered_as_the_phonology_states():
    """espeak-ng's own report of what it rendered, for every form of the lexicon: each
    symbol its declared phoneme, and the first vowel stressed."""
    for form in sorted(LANG.by_form):
        _, reported = synthesis.say("[[" + speech.espeak(form) + "]]")
        want = [("ˈ" if i == 1 else "") + IPA[c] for i, c in enumerate(form)]
        assert _rendered(reported) == want, form


def test_the_tap_is_rendered_as_a_tap():
    """The phonology's code for *r* renders [ɾ]; espeak-ng's `r` would render [ɹ]."""
    assert LANG.phonology["symbols"][LANG.letters.index("r")]["espeak"] == "*"
    _, reported = synthesis.say("[['ra*a]]")
    assert "ɾ" in "".join(reported)


def test_syllables_are_consonant_and_vowel_the_last_closed_by_a_final_consonant():
    assert speech.syllables("kotepu", LANG) == ["ko", "te", "pu"]
    assert speech.syllables("rakut", LANG) == ["ra", "kut"]
    assert speech.ipa("rakut", LANG) == "ˈɾa.kut"


@pytest.mark.parametrize("item", ["d01-simple-fact.1", "e5-registers.6"])
def test_prosody_follows_the_register_and_changes_no_phoneme(item):
    """A message's lines are spoken in its registers' prosody, the envelope flat; and
    every prosody renders a line with the same phonemes."""
    text = next(t for i, k, _, t in messages() if "%s.%d" % (i, k) == item)
    a = api.parse(text)
    lines = speech.spoken(a, LANG)
    assert lines[0]["prosody"] == "flat"
    for line, social in zip(lines[1:], a.social):
        assert line["prosody"] == LANG.registers[social["register"]]["settings"]["prosody"]
    reports = {name: _rendered(synthesis.say(lines[1]["espeak"], name)[1])
               for name in LANG.phonology["prosody"]}
    assert len({tuple(r) for r in reports.values()}) == 1


def test_every_spoken_line_divides_into_its_words_without_stress_or_pause():
    """The spoken lines of the corpus, their stresses and pauses taken away, divide into
    their words in one way: speech is an encoding when its prosody is lost."""
    count = 0
    for _, _, _, text in messages():
        a = api.parse(text)
        if a.message is None:
            continue
        for line in [a.message.envelope.words] + a.message.lines:
            if all(speech._speakable(w, LANG) for w in line):
                words = [w.form for w in line]
                assert speech.decode("".join(words), LANG) == words
                count += 1
    assert count > 600


def test_what_espeak_ng_says_divides_into_the_words_of_the_line():
    """The phonemes espeak-ng reports for a whole message, mapped back to symbols and
    run together, divide into the words of each line."""
    _, _, _, text = messages()[0]
    a = api.parse(text)
    back = {v: k for k, v in IPA.items()}
    _, reported = synthesis.synthesise(a, LANG)
    for line, phonemes in zip([a.message.envelope.words] + a.message.lines, reported):
        stream = "".join(back[p.replace("ˈ", "")] for p in _rendered(phonemes))
        assert speech.decode(stream, LANG) == [w.form for w in line]


def test_audio_is_a_wave_file_of_the_whole_message():
    _, _, _, text = messages()[0]
    audio, reported = synthesis.synthesise(api.parse(text), LANG)
    assert audio[:4] == b"RIFF" and audio[8:16] == b"WAVEfmt "
    assert len(reported) == 1 + len(api.parse(text).message.lines)


def test_the_command_line_speaks_each_line_and_writes_the_audio(tmp_path, capsys):
    from rowih import cli
    _, _, _, text = messages()[0]
    source = tmp_path / "message.txt"
    source.write_text(text, encoding="utf-8")
    wav = tmp_path / "message.wav"
    assert cli.main(["speak", str(source), "-o", str(wav)]) == 0
    printed = capsys.readouterr().out.splitlines()
    spoken = speech.spoken(api.parse(text))
    assert printed == ["%s\t%s\t%s" % (s["prosody"], s["ipa"], s["espeak"]) for s in spoken]
    assert wav.read_bytes()[:4] == b"RIFF" and wav.read_bytes()[8:12] == b"WAVE"


# ------------------------------------------------------- where the synthesiser's data are
def _loader():
    return pytest.importorskip("espeakng_loader")


def test_a_long_path_to_the_synthesiser_s_data_is_reached(tmp_path):
    """espeak-ng keeps the path to its data in 160 bytes and, given a longer one, ends the
    process; the engine reaches a longer path through a short link, so that a package
    installed deep in a file system still speaks. The engine is made in a process of its
    own, since without the link that process would end."""
    import subprocess
    import sys
    loader = _loader()
    deep = tmp_path / ("d" * 90) / ("e" * 90)
    deep.mkdir(parents=True)
    (deep / "espeak-ng-data").symlink_to(loader.get_data_path(), target_is_directory=True)
    code = ("import espeakng_loader\n"
            "espeakng_loader.get_data_path = lambda: %r\n"
            "from rowih import data, speech, synthesis\n"
            "form = sorted(data.load().by_form)[0]\n"
            "samples, phonemes = synthesis.say('[[' + speech.espeak(form) + ']]')\n"
            "print(len(samples) > 1000, len(phonemes) > 1)\n"
            % str(deep / "espeak-ng-data"))
    run = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                         timeout=120)
    assert run.returncode == 0, run.stderr
    assert run.stdout.split() == ["True", "True"]


def test_missing_data_are_reported_and_do_not_end_the_process(tmp_path, monkeypatch):
    loader = _loader()
    (tmp_path / "espeak-ng-data").mkdir()
    monkeypatch.setattr(loader, "get_data_path", lambda: str(tmp_path / "espeak-ng-data"))
    with pytest.raises(synthesis.SynthesiserUnavailable, match="data"):
        synthesis._Engine()


def test_a_long_path_no_link_can_shorten_is_reported(tmp_path, monkeypatch):
    loader = _loader()
    deep = tmp_path / ("d" * 90) / ("e" * 90)
    deep.mkdir(parents=True)
    (deep / "espeak-ng-data").symlink_to(loader.get_data_path(), target_is_directory=True)
    monkeypatch.setattr(loader, "get_data_path", lambda: str(deep / "espeak-ng-data"))

    def refuse(*args, **kwargs):
        raise OSError("no links here")
    monkeypatch.setattr(synthesis.os, "symlink", refuse)
    with pytest.raises(synthesis.SynthesiserUnavailable, match="longer than espeak-ng"):
        synthesis._Engine()
