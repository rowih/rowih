"""The vocabularies the resemblance audit compares the lexicon with
(`tools/compare_roots.py`): the sources, each pinned at a commit where it has one; the
readers of each list; the orthographies by which a constructed language's spelling is
transcribed; the reduction of a transcription to the segments a hearer of the language
would distinguish; and the index that finds every word within one segment of another."""
import collections
import csv
import io
import json
import re
import tarfile
import unicodedata
import xml.etree.ElementTree as ElementTree

READ = "2026-10-18"
FREQUENT = 10000        # the most frequent word forms of a language's list
GITHUB = "https://raw.githubusercontent.com/%s/%s/%s"
WIKIPRON = ("CUNY-CL/wikipron", "d282e848a211ea31cfd730f0ced8bc8cdab9e83d",
            "data/scrape/tsv/%s.tsv")
FREQUENCY = ("hermitdave/FrequencyWords", "525f9b560de45753a5ea01069454e72e9aa541c6",
             "content/2018/%s/%s_full.txt")
OFFENSIVE = ("LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words",
             "5faf2ba42d7b1c0977169ec3611df25a3c08eb13", "%s")
KAIKKI = "https://kaikki.org/dictionary/%s/meaning/%s/%s/%s.jsonl"
TARBALL = "https://codeload.github.com/%s/tar.gz/%s"
# the labels of a Wiktionary sense that make a word offensive
OFFENSIVE_TAGS = ("vulgar", "offensive", "derogatory", "obscene", "slur", "ethnic-slur")

# The major languages: (name, Wiktionary's name for it, its FrequencyWords list, its
# WikiPron files, broad where WikiPron has one, its list of offensive words).
MAJOR = [
    ("English", "English", "en", ["eng_latn_us_broad", "eng_latn_uk_broad"], "en"),
    ("Mandarin Chinese", "Chinese", "zh_cn", ["cmn_hani_standard_broad"], "zh"),
    ("Hindi", "Hindi", "hi", ["hin_deva_broad"], "hi"),
    ("Spanish", "Spanish", "es", ["spa_latn_la_broad", "spa_latn_ca_broad"], "es"),
    ("Modern Standard Arabic", "Arabic", "ar", ["ara_arab_broad"], "ar"),
    ("French", "French", "fr", ["fra_latn_broad"], "fr"),
    ("Bengali", "Bengali", "bn", ["ben_beng_dhaka_broad"], None),
    ("Portuguese", "Portuguese", "pt_br", ["por_latn_bz_broad"], "pt"),
    ("Indonesian", "Indonesian", "id", ["ind_latn_broad"], None),
    ("Urdu", "Urdu", "ur", ["urd_arab_broad"], None),
    ("Russian", "Russian", "ru", ["rus_cyrl_narrow"], "ru"),
    ("German", "German", "de", ["deu_latn_broad"], "de"),
    ("Japanese", "Japanese", "ja", ["jpn_hira_narrow", "jpn_kana_narrow", "jpn_hani_narrow"],
     "ja"),
    ("Egyptian Arabic", "Egyptian Arabic", None, ["arz_arab_broad"], None),
    ("Marathi", "Marathi", None, ["mar_deva_broad"], None),
    ("Vietnamese", "Vietnamese", "vi", ["vie_latn_hanoi_narrow"], None),
    ("Telugu", "Telugu", "te", ["tel_telu_broad"], None),
    ("Swahili", "Swahili", None, ["swa_latn_broad"], None),
    ("Hausa", "Hausa", None, ["hau_latn_broad"], None),
    ("Turkish", "Turkish", "tr", ["tur_latn_broad"], "tr"),
]
NOT_COMPARED = [
    {"name": "Nigerian Pidgin", "reason": "neither WikiPron nor FrequencyWords has a list "
     "for it, and no transcribed vocabulary of it was found"},
    {"name": "Wilkins's philosophical language", "reason": "its words are built from the "
     "tables of the Essay (1668) rather than published as a list of words"},
    {"name": "Blissymbolics", "reason": "its symbols have no spoken form to transcribe"},
]
# The constructed languages' sources, each a file or a repository at a fixed commit.
CONSTRUCTED = {
    "lojban gismu": "https://www.lojban.org/publications/wordlists/gismu.txt",
    "lojban cmavo": "https://www.lojban.org/publications/wordlists/cmavo.txt",
    "loglan words": GITHUB % ("torrua/LOD", "8320296ddc262a9f2807870a40782117bf9ced94",
                              "tables/Words.txt"),
    "loglan spellings": GITHUB % ("torrua/LOD", "8320296ddc262a9f2807870a40782117bf9ced94",
                                  "tables/WordSpell.txt"),
    "loglan definitions": GITHUB % ("torrua/LOD", "8320296ddc262a9f2807870a40782117bf9ced94",
                                    "tables/WordDefinition.txt"),
    "toki pona": GITHUB % ("lipu-linku/sona", "ff32a2776548bd17673d6abfd41927d027f806c2",
                           "api/src/raw/v1/words.json"),
    "esperanto": GITHUB % (WIKIPRON[0], WIKIPRON[1], WIKIPRON[2] % "epo_latn_broad"),
    "esperanto offensive": GITHUB % (OFFENSIVE[0], OFFENSIVE[1], "eo"),
    "laadan": GITHUB % ("corscheid/laadan-dict", "87685a0c3ae43cf4c4a7eec6b422bbbad997ad35",
                        "lib/dictionary_laadan.ts"),
    "klingon": TARBALL % ("De7vID/klingon-assistant-data",
                          "0f6018ece74a3f5a4b61ddcd4c7a28b010bb7fd0"),
    "klingon offensive": GITHUB % (OFFENSIVE[0], OFFENSIVE[1], "tlh"),
    "eldamo": GITHUB % ("pfstrack/eldamo", "4071c9caa95caca905c96af2505d5252045e2aaa",
                        "src/data/eldamo-data.xml"),
    "solresol": GITHUB % ("Itamal/SolReSol", "3b719627e53d874d707e6cee2d811bc0f0f4abdb",
                          "Solresol%20Dictionary%20-%20Solresol%20Dictionary.csv"),
    "ithkuil": TARBALL % ("yuorb/lexicon-json", "9c3ffe270ff4a534f44b08d4da29cff4ea10034b"),
}

Entry = collections.namedtuple("Entry", "spelling segments gloss offensive")


def sources() -> list:
    """Every file the comparison reads, as (name, URL)."""
    out = []
    for name, _, frequency, files, offensive in MAJOR:
        if frequency:
            out.append(("frequency %s" % frequency,
                        GITHUB % (FREQUENCY[0], FREQUENCY[1], FREQUENCY[2] % (frequency,
                                                                              frequency))))
        out += [("wikipron %s" % f, GITHUB % (WIKIPRON[0], WIKIPRON[1], WIKIPRON[2] % f))
                for f in files]
        if offensive:
            out.append(("offensive %s" % offensive,
                        GITHUB % (OFFENSIVE[0], OFFENSIVE[1], OFFENSIVE[2] % offensive)))
    return out + sorted(CONSTRUCTED.items())


# ------------------------------------------------------------------ the reduction
VOWELS = {**dict.fromkeys("aäɑɐæɶɒʌ", "a"), **dict.fromkeys("eɛøœ", "e"),
          **dict.fromkeys("iɪyʏɨ", "i"), **dict.fromkeys("oɔɵɤ", "o"),
          **dict.fromkeys("uʊɯʉ", "u"), **dict.fromkeys("əɚɘɜɝɞ", "ə")}
MERGED = {**dict.fromkeys("ɾrɹʁʀɽɻɺ", "r"), **dict.fromkeys("lɫʎɬɭɮʟ", "l"),
          **dict.fromkeys("nŋɲɴɳ", "n"), "ɡ": "g"}
# stress, length, syllable boundaries, ties and the modifiers written on a segment
# (aspiration, palatalisation, labialisation and the like); tone letters and numbers
REMOVED = set("ˈˌːˑ.‿͜͡-ʰʱʲʷˠˤⁿˡʼ˞") | set("˥˦˧˨˩¹²³⁴⁵⁰0123456789")


KEPT = ("ç",)


def reduce(tokens) -> tuple:
    """A transcription reduced to the segments compared: the language's five vowels and
    the schwa, one rhotic, one lateral, one nasal other than m, and every other segment as
    written."""
    out = []
    for token in tokens:
        for letter in token:
            # an IPA letter that decomposition would strip to another letter
            for c in (letter,) if letter in KEPT else unicodedata.normalize("NFD", letter):
                if unicodedata.combining(c) or c in REMOVED or c.isspace():
                    continue
                out.append(VOWELS.get(c) or MERGED.get(c) or c)
    return tuple(out)


def ipa_tokens(text: str) -> list:
    """An IPA string as one token per character; the reduction joins nothing."""
    return list(text)


def skeleton(segments: tuple) -> tuple:
    return tuple(s for s in segments if s not in "aeiouə")


# ------------------------------------------------------------------ orthographies
def transcribe(spelling: str, table: list) -> tuple:
    """A spelling transcribed by an orthography: each (letters, IPA) tried longest first;
    a letter the table does not name stands for itself."""
    table = sorted(table, key=lambda t: -len(t[0]))
    out, i = [], 0
    while i < len(spelling):
        for letters, ipa in table:
            if spelling.startswith(letters, i):
                out.append(ipa)
                i += len(letters)
                break
        else:
            out.append(spelling[i])
            i += 1
    return reduce(out)


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))


# Each orthography from the language's own description.
LOJBAN = [("'", "h"), ("c", "ʃ"), ("j", "ʒ"), ("x", "x"), ("y", "ə"), (".", ""), (",", "")]
LOGLAN = [("c", "ʃ"), ("j", "ʒ"), ("q", "θ"), ("x", "x"), ("y", "ə"), ("w", "y"),
          ("r", "ɹ")]
TOKI_PONA = [("j", "j")]
LAADAN = [("th", "θ"), ("sh", "ʃ"), ("zh", "ʒ"), ("lh", "ɬ"), ("y", "j"), ("r", "ɹ")]
KLINGON = [("tlh", "tɬ"), ("ch", "tʃ"), ("gh", "ɣ"), ("ng", "ŋ"), ("H", "x"), ("Q", "qχ"),
           ("D", "ɖ"), ("S", "ʂ"), ("I", "ɪ"), ("j", "dʒ"), ("y", "j"), ("'", "ʔ")]
QUENYA = [("qu", "kw"), ("hy", "ç"), ("hw", "ʍ"), ("c", "k"), ("x", "ks"), ("y", "j"),
          ("th", "θ"), ("ñ", "ŋ")]
SINDARIN = [("ch", "χ"), ("th", "θ"), ("dh", "ð"), ("lh", "ɬ"), ("rh", "r"), ("ph", "f"),
            ("hw", "ʍ"), ("ng", "ŋ"), ("c", "k"), ("y", "y")]
SOLRESOL = [("do", "do"), ("re", "re"), ("mi", "mi"), ("fa", "fa"), ("sol", "sol"),
            ("la", "la"), ("si", "si")]
ITHKUIL = [("c", "ts"), ("č", "tʃ"), ("j", "dʒ"), ("ẓ", "dz"), ("š", "ʃ"), ("ž", "ʒ"),
           ("ţ", "θ"), ("ḑ", "ð"), ("ļ", "ɬ"), ("ř", "ʁ"), ("ň", "ŋ"), ("y", "j")]


def loglan_spelling(word: str) -> tuple:
    """Loglan's i and u before a vowel are its semivowels."""
    word = re.sub(r"i(?=[aeiou])", "J", re.sub(r"u(?=[aeiou])", "W", word))
    return transcribe(word, LOGLAN + [("J", "j"), ("W", "w")])


def laadan_spelling(word: str) -> tuple:
    """Láadan marks tone with the acute and length by doubling, neither compared."""
    plain = strip_accents(word.lower())
    return transcribe(re.sub(r"([aeiou])\1", r"\1", plain), LAADAN)


# ------------------------------------------------------------------ the readers
def read_text(cached, name: str) -> str:
    with open(cached(name), encoding="utf-8") as f:
        return f.read()


def wikipron(cached, files: list) -> dict:
    """Every transcription of each word, by the word in lower case: (spelling, phones)."""
    out = collections.defaultdict(list)
    for f in files:
        for line in read_text(cached, "wikipron %s" % f).splitlines():
            word, phones = line.split("\t")
            out[word.lower()].append((word, phones))
    return out


def major(cached, row) -> dict:
    """A major language's frequent vocabulary, transcribed, with its list of offensive
    words compared as well, transcribed where WikiPron has them."""
    name, wiktionary, frequency, files, offensive = row
    pron = wikipron(cached, files)
    if frequency:
        listed = [line.split(" ")[0] for line in
                  read_text(cached, "frequency %s" % frequency).splitlines()][:FREQUENT]
    else:
        listed = sorted(pron)
    bad = set()
    if offensive:
        bad = {w.strip().lower() for w in read_text(cached, "offensive %s" % offensive)
               .splitlines() if w.strip()}
    chosen = list(dict.fromkeys(listed + sorted(bad & set(pron))))
    words = [Entry(spelling, reduce(phones.split()), None, key in bad)
             for key in chosen for spelling, phones in pron.get(key, [])]
    return {"name": name, "kind": "major", "kaikki": wiktionary,
            "frequent": len(listed), "transcribed": sum(1 for w in listed if w in pron),
            "offensive words compared": len(bad & set(pron)), "words": words}


def lojban(cached) -> list:
    out = []
    for line in read_text(cached, "lojban gismu").splitlines()[1:]:
        if line[1:6].strip():
            out.append(Entry(line[1:6].strip(), transcribe(line[1:6].strip(), LOJBAN),
                             line[20:40].strip(), False))
    for line in read_text(cached, "lojban cmavo").splitlines()[1:]:
        word = line[0:11].strip().strip(".")
        if word and " " not in word:
            out.append(Entry(word, transcribe(word, LOJBAN), line[20:62].strip(), False))
    return out


def loglan(cached) -> list:
    """Loglan's words other than its affixes, with the first gloss of each."""
    kinds = {}
    for line in read_text(cached, "loglan words").splitlines():
        fields = line.split("@")
        kinds[fields[0]] = fields[1]
    glosses = {}
    for line in read_text(cached, "loglan definitions").splitlines():
        fields = line.split("@")
        found = re.search("«([^»]*)»", fields[4]) if len(fields) > 4 else None
        if found and fields[0] not in glosses:
            glosses[fields[0]] = found.group(1)
    out = []
    for line in read_text(cached, "loglan spellings").splitlines():
        ident, spelling = line.split("@")[:2]
        if kinds.get(ident) != "Afx" and re.fullmatch("[a-z]+", spelling):
            out.append(Entry(spelling, loglan_spelling(spelling), glosses.get(ident), False))
    return out


def toki_pona(cached) -> list:
    words = json.loads(read_text(cached, "toki pona"))
    return [Entry(w, transcribe(w, TOKI_PONA),
                  v.get("translations", {}).get("en", {}).get("definition"), False)
            for w, v in sorted(words.items()) if v.get("usage_category") != "sandbox"]


def esperanto(cached) -> list:
    bad = {w.strip().lower() for w in read_text(cached, "esperanto offensive").splitlines()}
    out = []
    for line in read_text(cached, "esperanto").splitlines():
        word, phones = line.split("\t")
        out.append(Entry(word, reduce(phones.split()), None, word.lower() in bad))
    return out


def laadan(cached) -> list:
    text = read_text(cached, "laadan")
    rows = json.loads(text[text.index("= [") + 2:text.rindex("]") + 1])
    return [Entry(r["laadan"], laadan_spelling(r["laadan"]), r["english"], False)
            for r in rows if re.fullmatch(r"[^\s\-/()]+", r["laadan"])]


def _yaml_value(line: str) -> str:
    value = line.split(":", 1)[1].strip()
    if value.startswith("'") and value.endswith("'"):
        value = value[1:-1].replace("''", "'")
    return value


def klingon_entry(text: str) -> tuple:
    """A boQwI' entry's word, part of speech, status and English definition."""
    fields = {}
    for line in text.splitlines():
        for key in ("entry_name", "part_of_speech", "status"):
            if line.startswith("  %s:" % key):
                fields[key] = _yaml_value(line)
        # the definition stands on its own line, or as the first of its parts' texts
        if line.startswith("  definition:") and _yaml_value(line):
            fields.setdefault("definition", _yaml_value(line))
        if line.startswith("    text:"):
            fields.setdefault("definition", _yaml_value(line))
    return (fields.get("entry_name", ""), fields.get("part_of_speech", ""),
            fields.get("status", ""), fields.get("definition"))


KLINGON_WORDS = ("nouns", "verbs", "adverbials", "exclamations", "conjunctions", "questions")


def klingon(cached) -> list:
    """Okrand's canonical words, names left out, as boQwI' records them."""
    bad = {w.strip() for w in read_text(cached, "klingon offensive").splitlines()}
    out = []
    with tarfile.open(cached("klingon"), "r:gz") as tar:
        for member in tar:
            parts = member.name.split("/")
            if not member.isfile() or len(parts) < 4 or parts[1] != "entries" \
                    or parts[2] not in KLINGON_WORDS or not member.name.endswith(".yaml"):
                continue
            word, pos, status, definition = klingon_entry(
                tar.extractfile(member).read().decode("utf-8"))
            if status == "canonical" and "name" not in pos and re.fullmatch(
                    r"[A-Za-z']+", word):
                out.append(Entry(word, transcribe(word, KLINGON), definition, word in bad))
    return out


ELDAMO_SKIPPED = ("phoneme", "phrase", "text", "root", "affix", "prefix", "suffix", "infix",
                  "grammar")


def eldamo(cached, code: str) -> list:
    """Tolkien's words of one language in Eldamo, names and phrases left out."""
    table = QUENYA if code == "q" else SINDARIN
    out = []
    for _, element in ElementTree.iterparse(cached("eldamo"), events=("end",)):
        if element.tag != "word" or element.get("l") != code:
            continue
        word, speech = element.get("v", ""), element.get("speech", "")
        if speech not in ELDAMO_SKIPPED and not speech.endswith("name") and re.fullmatch(
                r"[^\s\[\]\-()?!.,]+", word):
            out.append(Entry(word, transcribe(word.lower(), table), element.get("gloss"),
                             False))
    return out


def solresol(cached) -> list:
    out = []
    for row in csv.reader(io.StringIO(read_text(cached, "solresol"))):
        word = row[0].strip().lower() if row else ""
        if word and re.fullmatch("(do|re|mi|fa|sol|la|si)+", word):
            out.append(Entry(word, transcribe(word, SOLRESOL), row[1].strip(), False))
    return out


def ithkuil(cached) -> list:
    """New Ithkuil's roots, consonants alone, compared by their consonants."""
    out = []
    with tarfile.open(cached("ithkuil"), "r:gz") as tar:
        for member in tar:
            if member.isfile() and "/lexicon/en/roots/" in member.name \
                    and member.name.endswith(".json"):
                for root in json.loads(tar.extractfile(member).read().decode("utf-8")):
                    letters = root["root"].lower()
                    out.append(Entry(letters, transcribe(letters, ITHKUIL), _ithkuil_gloss(
                        root), False))
    return out


def _ithkuil_gloss(root: dict) -> str | None:
    """A root's gloss: what it refers to, or the first of its stems."""
    if root.get("refers"):
        return root["refers"]
    stem = (root.get("stems") or [None])[0]
    return stem.get("BSC") if isinstance(stem, dict) else stem


def constructed(cached) -> list:
    """The constructed languages' lists, each as the comparison reads it."""
    rows = [("Lojban", lojban(cached)), ("Loglan", loglan(cached)),
            ("Toki Pona", toki_pona(cached)), ("Esperanto", esperanto(cached)),
            ("Láadan", laadan(cached)), ("Klingon", klingon(cached)),
            ("Quenya", eldamo(cached, "q")), ("Sindarin", eldamo(cached, "s")),
            ("Solresol", solresol(cached)), ("New Ithkuil", ithkuil(cached))]
    return [{"name": name, "kind": "constructed", "kaikki": "Esperanto" if name ==
             "Esperanto" else None, "listed": len(words), "words": words,
             "compared by": "consonants" if name == "New Ithkuil" else "segments"}
            for name, words in rows]


def languages(cached) -> list:
    return [major(cached, row) for row in MAJOR] + constructed(cached)


# ------------------------------------------------------------------ the index
class Index:
    """Every word of every language, found by its segments within an edit distance of
    one: a word is stored whole and with each segment deleted, so that a word one
    insertion, deletion or substitution away shares a key with it. A language compared by
    its consonants is stored by its consonants, and only an identical sequence is found.
    Building is O(n L) for n words of at most L segments, a query O(L)."""

    def __init__(self):
        self.whole = collections.defaultdict(list)
        self.deleted = collections.defaultdict(list)
        self.substituted = collections.defaultdict(list)
        self.consonants = collections.defaultdict(list)

    def add(self, language: dict, words: list):
        for w in words:
            if language.get("compared by") == "consonants":
                self.consonants[skeleton(w.segments)].append((language, w))
                continue
            s = w.segments
            self.whole[s].append((language, w))
            for i in range(len(s)):
                self.deleted[s[:i] + s[i + 1:]].append((language, w))
                self.substituted[i, s[:i] + s[i + 1:]].append((language, w))

    def close(self, s: tuple) -> list:
        """Every word at a distance of at most one segment from `s`, once each."""
        found = self.whole[s] + self.deleted[s] + self.consonants[skeleton(s)]
        for i in range(len(s)):
            rest = s[:i] + s[i + 1:]
            found += self.whole[rest] + self.substituted[i, rest]
        seen, out = set(), []
        for language, w in found:
            if (language["name"], w) not in seen:
                seen.add((language["name"], w))
                out.append((language, w))
        return out
