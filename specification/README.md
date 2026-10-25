# The Rowih reference specification

Rowih is a language for communication among software agents. A message in Rowih states in words of the language, and never leaves to be inferred from its content, what each of its moves does, how well founded each assertion is and on what basis, on whose authority a request or a commitment is made, and which entries of the record its participants share each move adds or changes. A hearer that analyses the message with a conformant implementation can check each of these statements, and, where the message carries its integrity check value, can detect any single edit of a symbol or a word that would change one of them. The language has its own sounds, its own words and its own writing system; it travels between machines in a transliteration of nineteen Latin letters, and it can be spoken.

This specification states the language as released. It is written for two readers: an implementer building a reader or a writer of the language, and an agent, or the operator who enables it, learning what the language guarantees and how it is used. Every rule is stated here. The forms of the language are data in [`language/`](../language/) and [`lexicon/`](../lexicon/), and every table of forms, constants and measurements in these chapters is generated from that data by [`tools/build_specification.py`](../tools/build_specification.py), so that no such table can differ from the data it states.

## The releases this specification states

<!-- generated: versions -->
| Part | Release | Date |
|---|---|---|
| language | 1.0 | 2026-10-19 |
| lexicon | 1.0 |  |
| protocol | 0.5 |  |
| grammar | 1.0 |  |
| semantics | 0.1 |  |
| phonology | 0.3 |  |
| writing system | 0.2 |  |
<!-- end generated -->

The envelope of every message names the releases of the language, the lexicon and the protocol it is written in ([the envelope](protocol.md#the-envelope)). Language 1.0 reads the messages of language 1.0 alone.

## How the specification is arranged

| Chapter | What it states |
|---|---|
| [The sounds and the shapes of words](sounds-and-words.md) | The nineteen symbols, syllables and stress, how a word's first syllable fixes its length, the distances that keep words apart, and the spoken form |
| [The lexicon](lexicon.md) | The entries of the lexicon, roots and their meanings, word formation, act words, conventional expressions, idioms, figurative senses, registers and the releases of the lexicon |
| [The notation](notation.md) | The parenthesised form in which a writer states a move and in which its normal form is written |
| [The grammar](grammar.md) | The productions of a message, the structural words, the grammatical classes and their members, and the rules a well-formed move obeys beyond the productions |
| [What a message means](meaning.md) | What each class and member contributes, the normal form and the defaults it states, standing, time, reference, ambiguity, figures, and the English explanation |
| [The record and discourse](discourse.md) | The entries each move adds, how a move names and changes an entry, authority, commitments, requests, delegation and negotiation |
| [Messages, protocol and transport](protocol.md) | The envelope, counts, check words and check values, channels and repair, authentication, versions and features, the maxima, the media type and the transport binding |
| [The writing system](writing-system.md) | The components, how a word and a message are drawn, the native digital form, the font and the renderings |
| [Dialects](dialects.md) | Technical terms, compressed forms, the releases of a dialect and their digests, and how two agents settle the dialects they share |
| [Conformance](conformance.md) | The guarantees, the invariants that state them, the conformance suite, the diagnostics, the interfaces of the implementations, the server of the Model Context Protocol and the skill, and the language's known limitations |

How the language changes, who may propose a change, and the gate a change must pass are stated apart from the specification, in [How Rowih changes](../governance/README.md).

## The forms of a message

A message has one meaning and several forms, each a view of one analysis.

- **The transliteration** writes the language's words in the nineteen letters *p t k b d g m n s l r w y h a e i o u*, words separated by a space, the envelope on the first line and each move on a line of its own. It is the form for transport between machines and for language models to read and write.
- **The native digital form** writes the same words in nineteen code points of the Unicode Private Use Area, U+F3A0 to U+F3B2, one for each symbol, which the language's font draws as its writing system. It converts to and from the transliteration without loss.
- **The renderings** draw the native writing as SVG, PNG or HTML, for a reader looking at a page.
- **The spoken form** says each word by the phonology, with a prosody fixed by the move's register.
- **The notation** is the parenthesised form in which a writer states what a move says, from which the generator writes the surface with every count, check word and check value computed. The literal semantic form and the normal form are written in it.
- **The normal form** is the move with every default stated and its parts in canonical order. Two realisations of one meaning have one normal form, and the semantic check value is computed over it.
- **The morpheme gloss and the English explanation** are views for a reader. The gloss names each word; the explanation says in English what the analysis found. Neither carries the checks of the message, and neither is a translation that could stand in its place.

## Terms used throughout

| Term | Meaning |
|---|---|
| participant | An agent taking part in an exchange, named in messages by a number |
| message | What one participant sends at one time to one or more others: an envelope followed by one or more moves, or by one protocol statement |
| envelope | The first line of a message: its sender, recipients, time, releases, identifier, first entry and check values |
| move | One act of the sender's: a head stating its force, then the constituents of its content, closed by its move check word |
| entry | What a move adds to the record, numbered in its author's own count |
| record | The entries the participants of an exchange share, and the changes made to them |
| channel | The messages a sender sends to one set of recipients, numbered by serials so that a gap can be known |
| form | The letters of a word |
| root | A word of the lexicon naming an event, a state, an object or a kind; content words are built on roots |
| class, member | A closed set of grammatical words and each word in it, such as the class of strengths and its member *certain* |
| critical dimension | A dimension of a move whose silent change would alter what the move does or claims, such as its force, its standing, a number or a time |
| protected word | A word of a class that carries a critical dimension, kept at least three edits from every other word |
| check word | A word computed from the words before it, whose mismatch shows damage |
| check value | A number computed over a whole message (the integrity check value) or over the normal form of its moves (the semantic check value) |
| register | The variety of the language a move is written in, from raw exchange among agents of one system to the ceremonial |
| dialect | A community's release of technical terms and compressed forms, named by number, version and digest |
| conformant implementation | An implementation that meets the requirements of [Conformance](conformance.md) |

## Requirements

A rule stated with *must* or *must not* is a requirement: on a message, which is not well formed if it breaks one, or on an implementation, which does not conform if it breaks one. The rest of the text describes or explains. Each requirement on an implementation is tested by the conformance suite, and [Conformance](conformance.md) names the test.

The forms, the classes, the lexicon and the protocol's constants are data, and the data in [`language/`](../language/) and [`lexicon/`](../lexicon/) govern the tables generated from them. The Python implementation, [`python/rowih/`](../python/rowih/), is canonical, and the TypeScript implementation, [`typescript/src/`](../typescript/src/), must agree with it byte for byte over the conformance suite. Where this text and the canonical implementation disagree, the disagreement is a defect of one of them, to be reported and corrected; until it is, conformance is tested against the canonical implementation's behaviour on the conformance suite.

## The canonical sources

| Source | What it holds |
|---|---|
| [`language/phonology.json`](../language/phonology.json) | The symbols, their sounds and code points, syllables, stress, word shapes and the prosody of speech |
| [`language/grammar.json`](../language/grammar.json) | The grammatical classes and members, the structural words, the critical forms, the move check word and the productions |
| [`language/semantics.json`](../language/semantics.json) | The elements of the semantic ontology |
| [`language/protocol.json`](../language/protocol.json) | The envelope's fields and fixed forms, the unit check word, the repair defaults, authentication, the features and the maxima |
| [`language/releases.json`](../language/releases.json) | Which releases each language release reads |
| [`language/writing.json`](../language/writing.json) | The components of the writing system and the geometry of drawing |
| [`language/font/`](../language/font/) | The font that draws the native digital form |
| [`lexicon/`](../lexicon/) | The entries of the lexicon, its registers, mappings, patterns, the dialects' releases and the releases of the lexicon |
| [`corpus/`](../corpus/) | The conformance suite and the corpus of exchanges, with the reports the measurements rest on |

## Licence

This specification, the data and the corpus are licensed under CC BY 4.0, and the implementations, the tools and the tests under Apache-2.0.
