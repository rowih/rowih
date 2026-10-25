"""Speech synthesis through espeak-ng (specification/sounds-and-words.md#the-spoken-form):
the spoken form of each line rendered from phoneme input, in the voice the phonology names
and the prosody each line's register sets, the lines joined by the phonology's pause, as
16-bit mono WAV. espeak-ng's own report of each phoneme it rendered is returned beside the
audio, which is how the tests check what was spoken rather than what was asked for.

espeak-ng is loaded from the `espeakng-loader` package (the `speech` extra), through its
C interface (`speak_lib.h`, espeak-ng 1.52.0). It keeps one state for the process, so the
library is initialised once and every synthesis sets all of its parameters. The phonemes
of a line are a function of the line; its samples are not quite, since espeak-ng carries
its pitch flutter from one utterance to the next, so that the k-th line a process speaks
sounds the same in every process and a line spoken twice differs by a few samples.
"""
from __future__ import annotations

import atexit
import ctypes
import os
import struct
import tempfile

from . import speech
from .data import Language, load

AUDIO_OUTPUT_SYNCHRONOUS = 2
INITIALIZE_PHONEME_EVENTS_IPA = 0x0001 | 0x0002
CHARS_UTF8 = 1
PHONEMES = 0x100
EVENT_LIST_TERMINATED = 0
EVENT_PHONEME = 7
RATE, VOLUME, PITCH, RANGE, WORDGAP = 1, 2, 3, 4, 7
POSITION_CHARACTER = 1
# espeak-ng keeps the path to its data, the directory given it with "/espeak-ng-data" and a
# terminating byte, in 160 bytes; given a longer directory it falls back to the one compiled
# into the library, finds no data there and ends the process. A longer directory is reached
# through a short link made for the process.
MAX_DATA_DIRECTORY = 144


class SynthesiserUnavailable(Exception):
    """espeak-ng cannot be loaded: the `speech` extra is not installed, or the library
    does not initialise."""


class _Event(ctypes.Structure):
    _fields_ = [("type", ctypes.c_int), ("unique_identifier", ctypes.c_uint),
                ("text_position", ctypes.c_int), ("length", ctypes.c_int),
                ("audio_position", ctypes.c_int), ("sample", ctypes.c_int),
                ("user_data", ctypes.c_void_p), ("id", ctypes.c_char * 8)]


_CALLBACK = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int,
                             ctypes.POINTER(_Event))


def _remove_link(directory: str) -> None:
    """Remove the short link to espeak-ng's data, and the directory made to hold it."""
    try:
        os.unlink(os.path.join(directory, "espeak-ng-data"))
        os.rmdir(directory)
    except FileNotFoundError:
        pass


def _data_directory(data_path: str) -> str:
    """The directory to give espeak-ng, the one that holds `data_path`, its
    `espeak-ng-data`: the loader's own, or a short link to it made for the process where
    the loader's path is longer than espeak-ng accepts."""
    if not os.path.isfile(os.path.join(data_path, "phontab")):
        raise SynthesiserUnavailable("espeak-ng's data are not at %s" % data_path)
    directory = os.path.dirname(data_path)
    if len(directory.encode()) <= MAX_DATA_DIRECTORY:
        return directory
    short = tempfile.mkdtemp(prefix="rowih-espeak-")
    try:
        if len(short.encode()) > MAX_DATA_DIRECTORY:
            raise OSError("the temporary directory %s is itself too long" % short)
        os.symlink(data_path, os.path.join(short, "espeak-ng-data"), target_is_directory=True)
    except OSError as e:
        os.rmdir(short)
        raise SynthesiserUnavailable(
            "the path to espeak-ng's data, %s, is longer than espeak-ng accepts, and no "
            "shorter link to it could be made: %s" % (directory, e)) from e
    atexit.register(_remove_link, short)
    return short


class _Engine:
    """The process's one espeak-ng instance (scope: per process)."""

    def __init__(self):
        try:
            import espeakng_loader
        except ImportError as e:
            raise SynthesiserUnavailable("install the speech extra (espeakng-loader)") from e
        path = espeakng_loader.get_library_path()
        try:
            self.lib = ctypes.CDLL(path)
        except OSError as e:
            raise SynthesiserUnavailable("espeak-ng did not load from %s" % path) from e
        data_dir = _data_directory(espeakng_loader.get_data_path())
        self.rate = self.lib.espeak_Initialize(AUDIO_OUTPUT_SYNCHRONOUS, 0,
                                               data_dir.encode(), INITIALIZE_PHONEME_EVENTS_IPA)
        if self.rate <= 0:
            raise SynthesiserUnavailable("espeak-ng did not initialise (%d)" % self.rate)
        self.samples, self.phonemes = [], []
        self._callback = _CALLBACK(self._receive)
        self.lib.espeak_SetSynthCallback(self._callback)

    def _receive(self, wav, count, events):
        if wav and count > 0:
            self.samples.extend(wav[i] for i in range(count))
        i = 0
        while events[i].type != EVENT_LIST_TERMINATED:
            if events[i].type == EVENT_PHONEME:
                name = events[i].id.decode("utf-8", "replace")
                if name:
                    self.phonemes.append(name)
            i += 1
        return 0

    def say(self, phoneme_input: str, voice: str, prosody: dict) -> tuple:
        if self.lib.espeak_SetVoiceByName(voice.encode()) != 0:
            raise SynthesiserUnavailable("espeak-ng has no voice %r" % voice)
        for param, key in ((RATE, "rate"), (PITCH, "pitch"), (RANGE, "range"),
                           (WORDGAP, "word gap")):
            self.lib.espeak_SetParameter(param, prosody[key], 0)
        self.lib.espeak_SetParameter(VOLUME, 100, 0)
        self.samples, self.phonemes = [], []
        text = phoneme_input.encode("utf-8")
        uid = ctypes.c_uint(0)
        self.lib.espeak_Synth(text, len(text) + 1, 0, POSITION_CHARACTER, 0,
                              CHARS_UTF8 | PHONEMES, ctypes.byref(uid), None)
        self.lib.espeak_Synchronize()
        return list(self.samples), list(self.phonemes)


_ENGINE = []


def engine() -> _Engine:
    if not _ENGINE:
        _ENGINE.append(_Engine())
    return _ENGINE[0]


def say(phoneme_input: str, prosody: str = "neutral", lang: Language | None = None) -> tuple:
    """Samples and the phonemes espeak-ng reports for one line of phoneme input."""
    lang = lang or load()
    return engine().say(phoneme_input, lang.phonology["espeak voice"],
                        lang.phonology["prosody"][prosody])


def wav(samples: list, rate: int) -> bytes:
    """16-bit mono PCM in a RIFF WAVE file."""
    body = struct.pack("<%dh" % len(samples), *samples)
    return (b"RIFF" + struct.pack("<I", 36 + len(body)) + b"WAVEfmt "
            + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16)
            + b"data" + struct.pack("<I", len(body)) + body)


def synthesise(analysis, lang: Language | None = None) -> tuple:
    """The spoken message as WAV, and espeak-ng's phonemes for each line."""
    lang = lang or load()
    e = engine()
    pause = [0] * (e.rate * lang.phonology["pause between lines"] // 1000)
    samples, reported = [], []
    for i, line in enumerate(speech.spoken(analysis, lang)):
        s, p = say(line["espeak"], line["prosody"], lang)
        if i:
            samples += pause
        samples += s
        reported.append(p)
    return wav(samples, e.rate), reported
