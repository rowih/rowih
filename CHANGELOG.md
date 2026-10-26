# Changelog

This file records each release of Rowih, the newest first. An entry states the release's version and date, the parts it affects, the change, the reason, the compatibility impact and the migration it requires, as the rule of change requires ([How Rowih changes](governance/README.md#the-rule-of-change)). The language, the lexicon, the protocol, the phonology, the writing system and each dialect carry versions of their own, and the packages `rowih` carry theirs under semantic versioning ([Versions and releases](governance/README.md#versions-and-releases)). A release of this repository is numbered by its packages and tagged with that number, as `v1.1.0`.

## 1.1.4, 2026-10-26

The server's tools described.

- **Parts:** the Python and TypeScript packages `rowih`, at 1.1.4. Language 1.0, lexicon 1.0, protocol 0.5, phonology 0.3, writing system 0.2 and every dialect are unchanged.
- **Change:** each tool of the server `rowih serve` says what it does, when to use it rather than another tool, that it changes nothing outside the call, what it returns and how it fails, and every parameter has a description, with its default where one applies. Continuous integration runs the gate on every commit to `main` as well as on every pull request, and each release is also a release on GitHub of its tag. Three reports of the gate are carried over, as [the gate](governance/README.md#the-gate) allows: `corpus/reports/tokens.json` as made over 1.1.1, since its measurement reads only transliterations and explanations, which no change touches, and `corpus/reports/parity.json` and `corpus/reports/single-edits-both.json` as made on 2026-10-20, since the release changes no code those runs execute and no data or message they read.
- **Dependencies:** none changed.
- **Reason:** a host shows a model each tool by its description alone, and the descriptions said little of when to use each tool or what it returns, and left 17 parameters undescribed.
- **Compatibility impact:** none. The tools' names, parameters and results are unchanged, and no interface, message or file the packages read changes.
- **Migration:** none.

## 1.1.3, 2026-10-26

Idioms that take slots.

- **Parts:** the Python and TypeScript packages `rowih`, at 1.1.3. Language 1.0, lexicon 1.0, protocol 0.5, phonology 0.3, writing system 0.2 and every dialect are unchanged.
- **Change:** an idiom whose literal structure holds a slot, such as *river-forking*, cannot be written as `(idiom KEY)`, which has no way to fill the slot, and writing it so raised an internal error. The notation's reader now refuses it with `NotationError`, naming the unit to write: the mark `IDIOM-ENTRY` on the idiom's unit and its literal structure, each `(slot N)` replaced by a constituent. The lexicon listing (`rowih summary lexicon` and the skill's `references/lexicon.md`) and the server's `lookup` give the 88 such idioms in that form. Three reports of the gate are carried over, as [the gate](governance/README.md#the-gate) allows: `corpus/reports/tokens.json` as made over 1.1.1, since its measurement reads only transliterations and explanations, which no change touches, and `corpus/reports/parity.json` and `corpus/reports/single-edits-both.json` as made on 2026-10-20, since the release changes no code those runs execute and no data or message they read.
- **Dependencies:** none changed.
- **Reason:** agents writing such idioms as the listing then gave them met the error.
- **Compatibility impact:** a text that wrote such an idiom as `(idiom KEY)` raised an internal error, and now raises `NotationError`. No interface, message or file the packages read changes.
- **Migration:** none.

## 1.1.2, 2026-10-26

Where hosts find the toolchain.

- **Parts:** the Python and TypeScript packages `rowih`, at 1.1.2. Language 1.0, lexicon 1.0, protocol 0.5, phonology 0.3, writing system 0.2 and every dialect are unchanged.
- **Change:** `server.json` is the server's entry for the MCP Registry, named `io.github.rowih/rowih`: the package `rowih` at this release, run by `uvx` with the argument `serve`. The Python package's description names the entry, in the line `mcp-name: io.github.rowih/rowih`, by which the registry knows the package, and `.github/workflows/registry.yml` publishes the entry from a release tag once the package of that tag is on PyPI. The repository is also a plugin marketplace for Claude Code, `.claude-plugin/`, whose one plugin is the repository itself: it loads the skill and starts the server of the release it names, with `uvx --from rowih==1.1.2 rowih serve`. The README and the package's description say how to add the marketplace and install the plugin, and `tests/test_distribution.py` holds the entry, the plugin and the marketplace to the release. The examples page draws each move of every message a row at a time, each row with its transliteration and morpheme gloss beneath it, gives each envelope in the same rows without its drawing, and sets out each literal semantic form within 80 characters a line, so that nothing on it scrolls sideways. Three reports of the gate are carried over, as [the gate](governance/README.md#the-gate) allows: `corpus/reports/tokens.json` stands as made over 1.1.1, since its tokenizers could not be fetched where the release was made, and `corpus/reports/parity.json` and `corpus/reports/single-edits-both.json` as made on 2026-10-20, since the only change to the code they execute is the version string, which none of them reads, and no message or data they read changes.
- **Dependencies:** none changed. Publishing the entry uses, in continuous integration only, `sigstore/cosign-installer` 4.1.2 and the registry's publisher `mcp-publisher` v1.8.4, verified by its signature.
- **Reason:** operators and their hosts look for tools in registries and marketplaces, where the toolchain was not listed; and the examples page scrolled sideways.
- **Compatibility impact:** none. No interface, message or file the packages read changes.
- **Migration:** none.

## 1.1.1, 2026-10-25

The package's description, and the page's examples.

- **Parts:** the Python and TypeScript packages `rowih`, at 1.1.1. Language 1.0, lexicon 1.0, protocol 0.5, phonology 0.3, writing system 0.2 and every dialect are unchanged.
- **Change:** the Python package states its description, `python/README.md`, which PyPI shows on the package's page; 1.1.0 was published without one. The README draws each example of the writing system a row at a time, with the transliteration of that row beneath it, and its recordings of the opening exchange say the moves it shows, without the envelope that opens each message. `tools/speak_examples.py` seeds each take from what it says, so that a recording is the same on every run, and keeps a recording already made from what it says. `.github/workflows/publish.yml` publishes the Python package to PyPI from a release tag, through trusted publishing, with an attestation of each file. The reports of the gate were made over this release except two, carried over as [the gate](governance/README.md#the-gate) allows: `corpus/reports/parity.json` and `corpus/reports/single-edits-both.json` stand as made on 2026-10-20, since this release, like 1.1.0, changes neither the code on their paths, compared without its comments, nor any message or data they read.
- **Dependencies:** none changed.
- **Reason:** a package on PyPI is read first from its page there, which had no description; the README's examples of the writing scrolled sideways, and its recordings ran four or five times as long as the moves they stood beside.
- **Compatibility impact:** none. No interface, message or file the packages read changes.
- **Migration:** none.

## 1.1.0, 2026-10-25

The first public release.

- **Parts:** the Python and TypeScript packages `rowih`, at 1.1.0; language 1.0, lexicon 1.0, protocol 0.5, phonology 0.3 and writing system 0.2; the conversational dialect at 0.1, the dialects of databases, linguistics, machine learning, negotiation, philosophy and planning at 0.2, and those of mathematics, programming, robotics, science and security at 0.3.
- **Change:** the first release this repository publishes. It holds the canonical data of the language in `language/` and `lexicon/`, from which every table of the specification is generated; the reference specification in `specification/`; the Python implementation, with the command `rowih` and its server of the Model Context Protocol, and the TypeScript reader and renderer; the skill that teaches an agent the language, in `skill/rowih/`; the conformance suite, the corpus of 1,200 exchanges and the reports of the gate, in `corpus/`; the tools that rebuild the data and run the gate; and the governance, the format of a proposal and the registry of dialect numbers. Every report was made over this release except two, carried over as [the gate](governance/README.md#the-gate) allows: `corpus/reports/parity.json`, the comparison of the two implementations, and `corpus/reports/single-edits-both.json`, the enumeration of single edits, were made on 2026-10-20 over the code and data with which language 1.0 was released on 2026-10-19, and this release changes neither the code on their paths, compared without its comments, nor any message or data they read. The packages begin at 1.1.0 because 1.0.0 numbered an earlier state of their interface, which was never published.
- **Dependencies:** none at run time. The optional extra `speech` depends on `espeakng-loader` 0.2.4, which provides eSpeak NG under GPL-3.0-or-later, and the extra `authentication` on `cryptography` 50.0.2. Development uses pytest 9.1.1, Hypothesis 6.140.2, fontTools 4.65.0, uharfbuzz 0.56.1, tokenizers 0.23.2, mcp 2.3.0 and skills-ref 0.1.1, pinned in `pyproject.toml` and locked with what they need in `uv.lock`, and TypeScript 5.9.3 with `@types/node` 22.20.5, locked in `typescript/package-lock.json`. When the release was made, `uv audit` found no known advisory among the 56 Python packages of the lock, and `npm audit` none among the TypeScript packages.
- **Reason:** an agent reaches the language through its toolchain, and an implementer needs the specification, the data and the conformance suite together, under the governance by which the language changes.
- **Compatibility impact:** none, since no earlier release was published. Language 1.0 reads only its own messages, and protocol 0.5 only its own protocol messages.
- **Migration:** none.
