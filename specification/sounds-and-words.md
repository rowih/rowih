# The sounds and the shapes of words

The language has nineteen symbols, and every word is a strict alternation of consonant and vowel opened by a consonant. The opening of a word fixes how long it is, so that a stream of symbols with no spaces in it divides into words in one way only, and the words of a release are kept far enough apart that a single edit of one never yields another. This chapter states the symbols, the syllable and the stress, the rule of length, the distances, and how a message is spoken.

## The symbols

The phonology has fourteen consonants and five vowels. Each symbol is one phoneme, written by one letter of the transliteration, by one code point of the native digital form, and by one component of the writing system ([The writing system](writing-system.md)). The eSpeak column gives the phoneme code the spoken form passes to the eSpeak NG synthesiser.

<!-- generated: symbols -->
| Index | Letter | Kind | Sound | Code point | eSpeak |
|---|---|---|---|---|---|
| 0 | `p` | consonant | /p/ | U+F3A0 | `p` |
| 1 | `t` | consonant | /t/ | U+F3A1 | `t` |
| 2 | `k` | consonant | /k/ | U+F3A2 | `k` |
| 3 | `b` | consonant | /b/ | U+F3A3 | `b` |
| 4 | `d` | consonant | /d/ | U+F3A4 | `d` |
| 5 | `g` | consonant | /ɡ/ | U+F3A5 | `g` |
| 6 | `m` | consonant | /m/ | U+F3A6 | `m` |
| 7 | `n` | consonant | /n/ | U+F3A7 | `n` |
| 8 | `s` | consonant | /s/ | U+F3A8 | `s` |
| 9 | `l` | consonant | /l/ | U+F3A9 | `l` |
| 10 | `r` | consonant | /ɾ/ | U+F3AA | `*` |
| 11 | `w` | consonant | /w/ | U+F3AB | `w` |
| 12 | `y` | consonant | /j/ | U+F3AC | `j` |
| 13 | `h` | consonant | /h/ | U+F3AD | `h` |
| 14 | `a` | vowel | /a/ | U+F3AE | `a` |
| 15 | `e` | vowel | /e/ | U+F3AF | `e` |
| 16 | `i` | vowel | /i/ | U+F3B0 | `i` |
| 17 | `o` | vowel | /o/ | U+F3B1 | `o` |
| 18 | `u` | vowel | /u/ | U+F3B2 | `u` |
<!-- end generated -->

The letter *r* is a tap, /ɾ/, and *y* is the glide /j/. Neither letter has any other value, and no other letter may appear in a word.

## Syllables and stress

Every word alternates consonant and vowel and begins with a consonant. Its syllables are consonant and vowel, and a word whose last symbol is a consonant closes its last syllable with it, so that *kotepu* divides as *ko.te.pu*, *rakut* as *ra.kut*, and *nububin* as *nu.bu.bin*. Primary stress falls on the first syllable of every word, and no other syllable is stressed.

## How a word's opening fixes its length

A word of one morpheme has the length its opening fixes: the first symbol alone, except where the phonology names the first syllable, which then fixes the length in its place. The lexicon is therefore a prefix code, in which no word is the beginning of another.

<!-- generated: onsets -->
| A word opened by | has this many symbols |
|---|---|
| onset `k` | 6 |
| onset `t` | 6 |
| onset `d` | 6 |
| onset `h` | 5 |
| onset `r` | 5 |
| onset `n` | 4 |
| onset `y` | 4 |
| onset `p` | 4 |
| onset `b` | 4 |
| onset `g` | 4 |
| onset `m` | 4 |
| onset `s` | 4 |
| onset `w` | 4 |
| onset `l` | 4 |
| first syllable `nu` | 7 |
<!-- end generated -->

The first syllable *nu* opens the seven-symbol roots of lexicon 1.0, and no word before them began with it, so that every earlier word kept its length when the syllable was named. A word opened by *n* followed by *a*, *e*, *i* or *o* is four symbols long; a word opened by *nu* is seven.

A content word is a root, then any number of suffixes, with the linker *i* opening each further root of a compound. A suffix has four symbols, vowel, consonant, vowel, consonant, and its first vowel is *a*, *e*, *o* or *u*, never *i*. A closed-class member may also take a suffix, as *gehuugow*, 'alternative', is the member *gehu* followed by the suffix *ugow*. Since every root and every suffix ends in a consonant, and every suffix and the linker begin with a vowel, a hearer divides any stream of symbols by three rules:

1. the opening of a morpheme fixes its length;
2. after a morpheme, the vowel *i* opens a further root, whose own opening fixes its length, and *a*, *e*, *o* or *u* opens a suffix of four symbols;
3. a consonant after a morpheme opens the next word.

A stream that these rules do not divide holds no word of the language there. The transliteration separates its words by spaces, and the rules are what divide the spoken form, where no space is heard.

The kinds of word differ in length and opening, so that a hearer knows from a word's first symbols what kind of word it is.

<!-- generated: word-kinds -->
| Kind of word | Symbols | Opened by | Words |
|---|---|---|---|
| member of a protected class | 6 | `d` `k` `t` | 96 |
| act word | 6 | `k` | 25 |
| member of another class | 4 | `b` `g` `l` `m` `n` `p` `s` `w` `y` | 193 |
| structural word | 4 | `l` `w` `y` | 18 |
| move check word | 5 | `h` | 337 |
| root | 5 | `r` | 117 |
| root | 7 | `nu` | 394 |
| diction or politeness word | 5 | `r` | 15 |
| suffix | 4 | `a` `e` `o` `u` | 18 |
<!-- end generated -->

The members of the protected classes carry the force of a move, the standing of an assertion, the polarity of a situation and its times; the act words stand for force. The move check words, opened by *h*, are the only five-symbol words that do not open with *r*. Listed derivations and compounds, the suffixed and compounded words the lexicon names, take the length of their parts, and an idiom or a figurative sense has no form of its own ([The lexicon](lexicon.md)).

## The distances between words

The distance between two words is the number of single-symbol edits that turn one into the other, an edit being the insertion, the deletion or the substitution of one symbol; this is the Levenshtein distance over the nineteen symbols, and a transposition counts as two edits. A release of the lexicon must meet five requirements over all its words, which are the members, the structural words, the move check words, the roots, the listed formations and the act words:

1. every word is at a distance of at least two from every other word;
2. every protected word is at a distance of at least three from every other word;
3. every word begins with a consonant, uses only the nineteen symbols, and, if it has one morpheme, has the length its opening fixes;
4. the words are uniquely decodable, which the Sardinas–Patterson test confirms;
5. no form spells two words.

The first requirement makes a single edit of any word a string that is no word of the release, so that the hearer reports it as unknown rather than reading another word. The second makes a single edit of a protected word nearer to that word than to any other, so that damage to a word carrying a critical dimension cannot be mistaken for damage to another. Both are checked over every word's neighbourhood of one edit when a release is built ([`python/rowih/lexicon_checks.py`](../python/rowih/lexicon_checks.py)).

## The spoken form

A message is spoken line by line: the envelope first, then each move. Each word is said by its phonemes, with the stress on its first syllable; in the IPA the word *rakut* is written *ˈɾa.kut*. A word that is not made of the nineteen symbols, such as the payload of declared data, is not spoken, and a pause stands in its place; this is the one thing the spoken form loses. Consecutive lines are separated by a pause of 400 milliseconds.

The synthesiser is eSpeak NG, driven by phoneme input in the voice `sw`, because that voice renders each phoneme as the table above states it; the tap is passed as `*`, which eSpeak NG renders as [ɾ] in every voice tested, where it renders `r` as the approximant [ɹ] in all of them but Spanish. A move's prosody is fixed by its register and carries no meaning of its own: it changes no phoneme, and the envelope is always spoken flat. A move that states no register is in the standard register, R2.

<!-- generated: register-prosody -->
| Register | Name | Prosody |
|---|---|---|
| R0 | raw | flat |
| R1 | protocol | flat |
| R2 | standard | neutral |
| R3 | explanatory | expressive |
| R4 | formal | measured |
| R5 | casual | expressive |
| R6 | playful | expressive |
| R7 | ceremonial | measured |
<!-- end generated -->

Each prosody sets four parameters of the synthesiser:

<!-- generated: prosody -->
| Setting | Rate (words a minute) | Base pitch (of 100) | Pitch range (of 100) | Gap between words (tens of milliseconds) |
|---|---|---|---|---|
| flat | 175 | 50 | 0 | 0 |
| neutral | 175 | 50 | 50 | 0 |
| expressive | 165 | 55 | 90 | 0 |
| measured | 140 | 45 | 35 | 2 |
<!-- end generated -->

A hearer of speech recovers the words by the three rules of division above, applied to the symbols heard. Synthesis needs the optional `speech` extra of the Python package, which depends on eSpeak NG under GPL-3.0-or-later; the package itself does not contain it. The audio a synthesiser writes is not reproducible byte for byte, so the spoken form is tested by the phonemes the synthesiser reports having said. No human listener has heard the spoken form, and how often a listener would mishear a word, which the distances are meant to guard against, is unmeasured.
