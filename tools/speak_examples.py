# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = [
#     "kokoro==0.9.4",
#     "torch==2.14.1",
#     "transformers==5.20.2",
#     "huggingface-hub==2.3.0",
#     "soundfile==0.14.0",
#     "numpy==2.5.4",
# ]
#
# [[tool.uv.index]]
# name = "pytorch-cpu"
# url = "https://download.pytorch.org/whl/cpu"
# explicit = true
#
# [tool.uv.sources]
# torch = { index = "pytorch-cpu" }
# ///
"""Write the audio of the examples, `examples/media/<message>.mp3`, from the phonemes
`tools/build_examples.py` records in `examples/speech.json`, and check each file by ear.

The voice is Kokoro-82M, a neural speech model under Apache-2.0, given each line's
phonemes directly, so that it says the language's sounds and does not guess them from
spelling; each participant speaks in a voice of its own, and lines are separated by the
spoken form's pause. The check is a phoneme recogniser, wav2vec2 fine-tuned on espeak-ng
phoneme labels: it transcribes each MP3 as written, its transcription is reduced to the
nineteen symbols, and its phoneme error rate is the edit distance from the message's
symbols over their number. A file above `THRESHOLD` is refused, except one of
`HEARD_BY_OWNER`, which the repository owner's listening checks instead and which is
refused unless it is the file the owner heard; and on every run the
first message is spoken again with its mid and high vowels exchanged, which the check must
refuse, so that a check that cannot fail is caught. Both models are pinned by revision.
The model draws noise as it speaks, so each take is seeded from its plan's digest and is
the same on every run; a file the record shows was made from its plan is kept and heard
again rather than spoken anew, and no file is written unless every file passes.
The results, with each file's digest, go to `examples/audio.json`, which
`tests/test_examples.py` holds to the files and to `examples/speech.json`.

Run from the repository root, after `tools/build_examples.py`, with uv, which installs
this script's pinned dependencies apart from the project's:
`uv run tools/speak_examples.py`. The models are fetched from Hugging Face on first use.
"""
import hashlib
import io
import json
import os
import sys

import numpy as np
import soundfile as sf
import torch
from huggingface_hub import hf_hub_download
from kokoro import KModel
from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2ForCTC

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES = os.path.join(ROOT, "examples")
VOICE_MODEL = ("hexgrad/Kokoro-82M", "f3ff3571791e39611d31c381e3a41a3af07b4987")
VOICE_WEIGHTS = "kokoro-v1_0.pth"
RECOGNISER = ("facebook/wav2vec2-lv-60-espeak-cv-ft", "ae45363bf3413b374fecd9dc8bc1df0e24c3b7f4")
VOICE_RATE = 24000
RECOGNISER_RATE = 16000
PAUSE_SECONDS = 0.4          # the spoken form's pause between lines
KOKORO_LIMIT = 500           # phoneme characters in one call; the model takes at most 510
MP3_QUALITY = 0.5            # libsndfile's compression level, 0 the best and 1 the smallest
THRESHOLD = 0.15             # fixed before the first full run, on 2026-10-24
# recordings the recogniser cannot judge, each checked instead by the repository owner's
# listening and held to the file the owner heard, by its SHA-256: the name said alone,
# which the recogniser never hears right in Kokoro's voices or eSpeak NG's (2026-10-27)
HEARD_BY_OWNER = {
    "rowih": ("2026-10-27", "1234c0c00bb4b53c42083875f6c04db7ca8ca19a8e7523234728b9f08ac70694"),
}
STRESS = "ˈ"
# what the recogniser writes for a symbol the language writes otherwise
HEARD_AS = {"g": "ɡ", "r": "ɾ", "ɹ": "ɾ"}
# the planted defect: a voice that confuses mid and high vowels
EXCHANGED = str.maketrans({"e": "i", "i": "e", "o": "u", "u": "o"})


def symbols_by_ipa() -> dict:
    with open(os.path.join(ROOT, "language", "phonology.json"), encoding="utf-8") as f:
        return {s["ipa"]: s["letter"] for s in json.load(f)["symbols"]}


def kokoro_word(ipa: str, vowels: set) -> str:
    """A word as Kokoro reads phonemes: espeak-ng's convention, the stress mark before
    the stressed vowel, where the spoken form writes it before the syllable."""
    body = ipa.replace(STRESS, "").replace(".", "")
    first = next(i for i, ch in enumerate(body) if ch in vowels)
    return body[:first] + STRESS + body[first:]


def chunks(words: list) -> list:
    """A line's words in runs short enough for one call of the model."""
    out, run = [], []
    for w in words:
        if run and len(" ".join(run + [w])) > KOKORO_LIMIT:
            out.append(" ".join(run))
            run = []
        run.append(w)
    return out + [" ".join(run)] if run else out


class Voice:
    """Kokoro-82M at its pinned revision, and the voices it has loaded."""

    def __init__(self):
        repo, revision = VOICE_MODEL
        config = hf_hub_download(repo, "config.json", revision=revision)
        weights = hf_hub_download(repo, VOICE_WEIGHTS, revision=revision)
        self.model = KModel(repo_id=repo, config=config, model=weights).eval()
        self.packs = {}

    def pack(self, name: str):
        if name not in self.packs:
            repo, revision = VOICE_MODEL
            path = hf_hub_download(repo, "voices/%s.pt" % name, revision=revision)
            self.packs[name] = torch.load(path, weights_only=True)
        return self.packs[name]

    def speak(self, lines: list, voice: str, vowels: set) -> np.ndarray:
        """The lines spoken in turn, the spoken form's pause between them."""
        pause = np.zeros(int(PAUSE_SECONDS * VOICE_RATE), dtype=np.float32)
        pieces, pack = [], self.pack(voice)
        for line in lines:
            words = [kokoro_word(w, vowels) for w in line.split(" ")]
            for text in chunks(words):
                with torch.no_grad():
                    pieces.append(self.model(text, pack[len(text) - 1], 1.0).numpy())
            pieces.append(pause)
        return np.concatenate(pieces[:-1])


class Ear:
    """The phoneme recogniser at its pinned revision."""

    def __init__(self, by_ipa: dict):
        repo, revision = RECOGNISER
        with open(hf_hub_download(repo, "vocab.json", revision=revision), encoding="utf-8") as f:
            self.tokens = {v: k for k, v in json.load(f).items()}
        self.extractor = Wav2Vec2FeatureExtractor.from_pretrained(repo, revision=revision)
        self.model = Wav2Vec2ForCTC.from_pretrained(repo, revision=revision).eval()
        self.by_ipa = by_ipa

    def hear(self, audio: np.ndarray, rate: int) -> str:
        """The symbols the recogniser hears, by the language's letters."""
        t = np.arange(int(len(audio) * RECOGNISER_RATE / rate)) * rate / RECOGNISER_RATE
        audio = np.interp(t, np.arange(len(audio)), audio).astype(np.float32)
        inputs = self.extractor(audio, sampling_rate=RECOGNISER_RATE, return_tensors="pt")
        with torch.no_grad():
            best = self.model(inputs.input_values).logits[0].argmax(-1).tolist()
        heard, last = [], None
        for i in best:
            token = self.tokens[i]
            if i != last and not (token.startswith("<") or token == "|"):
                heard += [self.by_ipa[HEARD_AS.get(c, c)] for c in token
                          if HEARD_AS.get(c, c) in self.by_ipa]
            last = i
        return "".join(heard)


def distance(a: str, b: str) -> int:
    """The edit distance of two strings: O(len(a) × len(b)) time, O(len(b)) space."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def mp3(audio: np.ndarray) -> bytes:
    out = io.BytesIO()
    sf.write(out, audio, VOICE_RATE, format="MP3", subtype="MPEG_LAYER_III",
             compression_level=MP3_QUALITY)
    return out.getvalue()


def error_rate(ear: Ear, data: bytes, want: str) -> float:
    """The phoneme error rate of an MP3 against the symbols it should say."""
    audio, rate = sf.read(io.BytesIO(data), dtype="float32")
    return distance(want, ear.hear(audio, rate)) / len(want)


def plan_digest(plan: dict) -> str:
    return hashlib.sha256(json.dumps(plan, ensure_ascii=False, sort_keys=True)
                          .encode("utf-8")).hexdigest()


def seed(plan: dict) -> int:
    """The seed of a plan's take: the model draws noise as it speaks, so a take is fixed
    by its plan and not chosen among takes."""
    return int(plan_digest(plan)[:16], 16)


def recorded() -> dict:
    """The record of the files already made, by message, or nothing."""
    path = os.path.join(EXAMPLES, "audio.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)["messages"]


def kept(name: str, plan: dict, record: dict) -> bytes | None:
    """The file already made from this plan, as the record shows, or None."""
    path = os.path.join(EXAMPLES, "media", name + ".mp3")
    entry = record.get(name)
    if entry is None or entry["plan"] != plan_digest(plan) or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        data = f.read()
    return data if hashlib.sha256(data).hexdigest() == entry["mp3"] else None


def main():
    with open(os.path.join(EXAMPLES, "speech.json"), encoding="utf-8") as f:
        speech = json.load(f)
    by_ipa = symbols_by_ipa()
    vowels = {ipa for ipa, letter in by_ipa.items() if letter in "aeiou"}
    voice, ear = Voice(), Ear(by_ipa)
    record, results, made = recorded(), {}, {}
    for name, plan in speech.items():
        lines = [line["ipa"] for line in plan["lines"]]
        want = "".join(by_ipa[c] for line in lines for c in line if c in by_ipa)
        data = kept(name, plan, record)
        if data is None:
            torch.manual_seed(seed(plan))
            data = made[name] = mp3(voice.speak(lines, plan["voice"], vowels))
        rate = error_rate(ear, data, want)
        print("%s: %s, %s, phoneme error rate %.3f"
              % (name, plan["voice"], "made" if name in made else "kept", rate))
        if name in HEARD_BY_OWNER:
            date, digest = HEARD_BY_OWNER[name]
            if hashlib.sha256(data).hexdigest() != digest:
                sys.exit("%s is refused: it is not the take the repository owner heard on "
                         "%s; no file is written" % (name, date))
        elif rate > THRESHOLD:
            sys.exit("%s is refused: its phoneme error rate %.3f exceeds %.2f; no file is "
                     "written" % (name, rate, THRESHOLD))
        results[name] = {"plan": plan_digest(plan), "voice": plan["voice"],
                         "mp3": hashlib.sha256(data).hexdigest(),
                         "phoneme error rate": round(rate, 4)}
        if name in HEARD_BY_OWNER:
            results[name]["heard by"] = "the repository owner, %s" % HEARD_BY_OWNER[name][0]
    control = control_rate(voice, ear, speech, by_ipa, vowels)
    for name, data in made.items():
        with open(os.path.join(EXAMPLES, "media", name + ".mp3"), "wb") as f:
            f.write(data)
    write_record(results, control)


def control_rate(voice: Voice, ear: Ear, speech: dict, by_ipa: dict, vowels: set) -> dict:
    """The planted defect: the first message with its vowels exchanged, which the check
    must refuse."""
    name, plan = next(iter(speech.items()))
    lines = [line["ipa"] for line in plan["lines"]]
    want = "".join(by_ipa[c] for line in lines for c in line if c in by_ipa)
    torch.manual_seed(seed(plan))
    rate = error_rate(ear, mp3(voice.speak([line.translate(EXCHANGED) for line in lines],
                                           plan["voice"], vowels)), want)
    print("control, %s with its vowels exchanged: phoneme error rate %.3f" % (name, rate))
    if rate <= THRESHOLD:
        sys.exit("the check passed the planted defect (%.3f), so it is no check" % rate)
    return {"message": name, "defect": "mid and high vowels exchanged",
            "phoneme error rate": round(rate, 4)}


def write_record(results: dict, control: dict):
    record = {"voice model": {"repository": VOICE_MODEL[0], "revision": VOICE_MODEL[1],
                              "weights": VOICE_WEIGHTS, "licence": "Apache-2.0"},
              "recogniser": {"repository": RECOGNISER[0], "revision": RECOGNISER[1],
                             "licence": "Apache-2.0"},
              "threshold": THRESHOLD, "control": control, "messages": results}
    with open(os.path.join(EXAMPLES, "audio.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    main()
