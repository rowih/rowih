# Dialects

A dialect is a community's vocabulary: a numbered, versioned release of technical terms, each built from the core's roots and suffixes, and, for some communities, of compressed forms, short words that each stand for one term. A dialect adds words and changes nothing else: the closed classes, the structural words, the protected words, the fixed forms, the system of force and the meaning of every word of the lexicon are the same in every dialect. This chapter states what a dialect release holds, how a message names the dialects it uses, how its digest is computed, and how two agents settle the dialects they share.

## The dialects of release 1.0

Each dialect has a number, fixed and never reused, and its releases are files in [`lexicon/jargon/`](../lexicon/jargon/), one directory for each dialect and one file for each release.

<!-- generated: dialects -->
| Number | Dialect | Releases | Digest of the newest | Formed from lexicon | Terms in force | Compressed forms in force |
|---|---|---|---|---|---|---|
| 1 | mathematics | 0.1, 0.2, 0.3 | 731285992 | 1.0 | 10 | 10 |
| 2 | programming | 0.1, 0.2, 0.3 | 400636208 | 1.0 | 10 | 10 |
| 3 | machine-learning | 0.1, 0.2 | 765545834 | 1.0 | 10 | 0 |
| 4 | robotics | 0.1, 0.2, 0.3 | 647806988 | 1.0 | 10 | 10 |
| 5 | science | 0.1, 0.2, 0.3 | 919565889 | 1.0 | 10 | 10 |
| 6 | philosophy | 0.1, 0.2 | 839528749 | 1.0 | 10 | 0 |
| 7 | linguistics | 0.1, 0.2 | 726583995 | 1.0 | 10 | 0 |
| 8 | security | 0.1, 0.2, 0.3 | 095726917 | 1.0 | 10 | 10 |
| 9 | databases | 0.1, 0.2 | 893253860 | 1.0 | 10 | 0 |
| 10 | planning | 0.1, 0.2 | 084678243 | 1.0 | 10 | 0 |
| 11 | negotiation | 0.1, 0.2 | 498613383 | 1.0 | 10 | 0 |
| 12 | conversation | 0.1 | 131033484 | 0.7 | 5 | 5 |
<!-- end generated -->

Eleven dialects are technical communities; the twelfth, *conversation*, holds five words of everyday exchange. A release states its dialect's name and number, its community, its version, its date, the lexicon release its terms are formed from, its terms, its compressed forms where it gives any, and its digest. Each release repeats every term and form of the release before it unchanged and appends the new ones, so that earlier releases stay as they were released and their digests stay valid.

## Terms

A **term** is a word formed from the roots and suffixes of the lexicon by the rules of word formation ([The lexicon](lexicon.md#word-formation)), and means what its parts compose. A term of the mathematics dialect, *metric*, is `rubusawen`, *find the size of something* with the instrument suffix: what finding the size of something is done with. Every reader reads a term by its composition, whether or not it holds the dialect, so a term needs no resource beyond the lexicon. The notation writes a term as the word it is, `(unknown "rubusawen")`, which a reader divides into its parts; it writes a compressed form by its dialect's name and the key of the term it stands for, as `mathematics.metric`.

## Compressed forms

A **compressed form** is a five-symbol word opened by *r* that stands for one term of its own release, so that a hearer holding the release can say in five symbols what the term says in nine to fifteen. The compressed form *rinok* of the conversation dialect means *chat*, the term `retilirator`, *send* compounded with *word*. A compressed form stands alone: no suffix attaches to it and it enters no compound. It carries no critical dimension, so replacing one compressed form by another changes content and never force, polarity, standing or number.

A compressed form is a word of the language only in a message that names its dialect's release, and only to a hearer that holds that release under the digest the message states. In a message that names no such release it is an unknown word, kept opaque. The normal form writes each compressed form as the term it compresses, so a move written with a compressed form and the same move with the term written out have one normal form and one semantic check value. A compressed form stands only in the registers that admit the device of dialect forms, the raw, standard and casual registers; in any other it is refused, `d.checker.register-excludes-word`.

## What a dialect release may hold

A dialect release must meet these requirements:

1. every term is formed from roots and suffixes of the lexicon release the dialect states it is formed from, by the rules of word formation, and is no word of the lexicon and no compressed form of any dialect;
2. every compressed form is a five-symbol word opened by *r*, drawn from the code of such words ([The lexicon](lexicon.md#the-codes-from-which-forms-are-drawn)), and spelled by no release of the lexicon;
3. every compressed form is at a distance of at least two from every word of every lexicon release a message of the dialect may name and from every other dialect's compressed forms, and of at least three from every protected word;
4. every compressed form's expansion is a term of its own release, and every term in force of a release that gives compressed forms has exactly one compressed form in force;
5. every compressed form lists exactly the registers that admit the device of dialect forms;
6. the release states its digest, computed as the next section gives.

The tests of the repository check every dialect release it holds against these requirements, so a community's release proposed to the repository is checked by the same gate as the rest of the language. A reader checks two of them at run time: it refuses a message whose named dialects hold a compressed form within one edit of a word of the named lexicon or of another named dialect, `d.parser.dialect-conflict`, and it reads a dialect release only under the digest the message states.

A term or a compressed form may be **deprecated** by a later release, which records the release that deprecated it and its replacement; the deprecated word stays in the release, is still read, and is reported where a move uses it. The robotics dialect's release 0.3 deprecates the terms formed on the deprecated root *move* and forms them again on its replacement.

## The digest of a release

A release's **digest** distinguishes it from any other release under the same number and version, so that a hearer holding another community's release of one number cannot misread a message silently. The digest is computed from the release's canonical text:

1. The first line is `rowih dialect`, the dialect's number, its name, its version, `lexicon` and the lexicon release it is formed from, separated by single spaces.
2. Then, for each term in the order of the release, a line `term`, the term's form and the release that deprecated it, or `-` if none.
3. Then, for each compressed form in the order of the release, a line `form`, the compressed form, the form of the term it expands to and the release that deprecated it, or `-`.
4. Each line ends with a line feed, and nothing else is added.

The digest is the SHA-256 of the canonical text in UTF-8, read as a big-endian integer, reduced modulo 10⁹ and written at nine digits with zeros on the left, as a check value is ([Messages, protocol and transport](protocol.md#the-check-values)). Nothing else in the release, neither its definitions, its date, its community nor its provenance, enters the digest. The canonical text of the conversation dialect's release 0.1 is

```
rowih dialect 12 conversation 0.1 lexicon 0.7
term retilirator -
term romopiremup -
term rerisirunay -
term rabudumop -
term reyudaheh -
form rinok retilirator -
form ranas romopiremup -
form ruson rerisirunay -
form reyok rabudumop -
form romas reyudaheh -
```

whose SHA-256 is `d603da35…2ece098c`, and whose digest is 131033484.

## Naming a dialect in a message

A message names each dialect release it uses in its envelope, after its three versions, as *dialect*, the dialect's number, the release's version and its digest, in ascending order of number, none twice ([Messages, protocol and transport](protocol.md#the-envelope)). A message should name every dialect whose compressed forms it uses, and must name the dialect to which a definition it makes is scoped ([The lexicon](lexicon.md#coining-a-word-by-definition)); a compressed form of an unnamed dialect is an unknown word. Within a term, *dialect* and a number make the term the dialect itself, so that an agent can say that it does not hold dialect 8: `(term dialect (dialect 8) DEFINITE)`.

A reader that lacks a dialect release a message names, or holds it under another digest, reports `d.parser.version-unknown` and interprets none of the message. A message whose lexicon release is earlier than the lexicon a named dialect is formed from is `d.parser.version-pairing`. Dialects are a must-understand feature, so a reader that lacks the feature cannot read a message that names a dialect.

## Settling the dialects two agents share

Each agent states, in a protocol message *understands*, the dialect releases it offers, each by number, version and digest, beside the language, lexicon and protocol releases it reads ([Messages, protocol and transport](protocol.md#versions-and-features)). An agent offers the dialects its configuration names, not every release it holds, since a full list would exceed the message maximum. The dialects two agents share are those both offer under one digest and formed from no later lexicon than the one they share, the newest version of each number. A writer uses a compressed form only to a hearer known to hold its release, as the hearer's own statements or the dialects its messages name show, and writes the term to any other. A hearer that cannot interpret a message for lack of a dialect states which message and which dialect in *lacks*, and the speaker restates the message in what both hold.

## Dialects, registers and technical terms

A **term** is understood by every reader, at the cost of its length. A **compressed form** is understood only by a hearer holding the dialect, and saves symbols where both agents hold it. A **register** sets how a move is said, its formality and the devices it admits, and is independent of both; it decides whether a compressed form may stand. A community that needs a word every reader understands uses a term; two agents of one community that both hold its release may use the compressed form in the raw, standard or casual register.

## The registry of numbers

A dialect number keeps its meaning one community; the digest, not the number, keeps a message safe from another community's release. The registry of dialect numbers is [`governance/dialects.json`](../governance/dialects.json): a number is assigned to the next community that asks, in order, and never reused. A dialect release is proposed and published through the same gate as every change to the language ([How Rowih changes](../governance/README.md#dialects)).
