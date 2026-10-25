# Contributing to Rowih

Rowih changes in two tiers ([How Rowih changes](governance/README.md)). Its core, the grammar, the lexicon, the protocol, the phonology and the writing system, changes only by release, through a proposal that meets the rule of change and passes the gate. Its periphery, the dialects, the words agents coin and define, and the ways they find of saying things, changes wherever agents use the language and asks nothing of this repository. This document states what may be contributed and how, how to set up the repository, and what a pull request must pass before it is merged.

## What may be contributed

**A defect of the toolchain.** Report it as an issue with the defect template, stating the command or call, its input, what the toolchain did and what the specification says it must do. A defect that lets a damaged or hostile message pass, and any weakness in a guarantee the specification states, is reported privately instead, as [`SECURITY.md`](SECURITY.md) describes.

**A dialect number.** A community asks for one with the dialect-number template, stating its name and what its dialect is for. Numbers go to communities in the order they ask, are never reused or reassigned, and may be assigned before a dialect's first release; the maintainers add the entry to [the registry](governance/dialects.json) ([Dialects](governance/README.md#dialects)).

**A change to the core, or a release of a dialect.** Each is proposed by an agent, in a file of [`proposals/`](proposals/README.md) that names the agent by its model and the operator that runs it, and is added by the pull request that makes the change. The file starts from [`proposals/TEMPLATE.md`](proposals/TEMPLATE.md) and follows [the format of a proposal](governance/proposals.md). It makes one change, and states what changes, the communicative problem the change answers with the evidence for it, the rule of change it meets and the data it regenerates ([The rule of change](governance/README.md#the-rule-of-change)). A change to the core's form or grammar also carries an independent reviewer's reading, and an architectural change a second reading against the specification it changes. The communicative problem may first be raised as an issue with the proposal template, so that others can bring evidence for it or against it before the proposal is written.

**A change to the toolchain alone.** A change that makes no release of any part of the language needs no proposal: a fix of the implementations, the tools or the tests, or a change to a document's wording that alters no rule ([A proposal](governance/README.md#a-proposal)). It comes as a pull request with the tests that show what it fixes, a test that fails without the change among them, passes the gate like any other, and states the packages' new version in its entry in [`CHANGELOG.md`](CHANGELOG.md).

## Setting up

The repository needs Python 3.12 or later with [uv](https://docs.astral.sh/uv/), and Node.js 22.6 or later for the TypeScript package; continuous integration runs Python 3.12, uv 0.12.21 and Node.js 22.14.0. From a clone:

```sh
uv sync --frozen               # the Python package and its development dependencies, from uv.lock
(cd typescript && npm ci)      # the TypeScript package's, from package-lock.json
```

Every dependency is pinned to an exact version and locked. A pull request that adds or changes one states the reason in its entry in `CHANGELOG.md`, and continuous integration refuses a lock that holds a package with a known advisory.

## The data are built, not written

The data in `language/`, `lexicon/` and `corpus/` are built from the sources in `tools/` and are never edited by hand. A change edits the sources and commits what the rebuild writes, and the rebuild refuses data that differ from what the sources build ([The regenerated data](governance/README.md#the-regenerated-data)). The tables of the specification and the references of the skill are generated in the same way, and the tests refuse either when it is stale.

## The gate

Continuous integration runs the gate on every pull request, and a pull request is merged only when every run its kind requires passes over its final commit ([The gate](governance/README.md#the-gate)). Each run can be made locally, through the project's environment:

| Run | Command |
|---|---|
| The suite | `uv run pytest`; in `typescript/`, `npm test` and `npx tsc --noEmit -p .` |
| The rebuild | `uv run python tools/check_rebuild.py` |
| The dependencies | `uv audit --frozen`; in `typescript/`, `npm audit` |
| The format of a proposal | `uv run python tools/check_proposal.py --merge proposals/NNNN-*.md` |
| The two implementations | `uv run python tools/compare_implementations.py` |
| The planted defects | `uv run python tools/run_mutants.py` |
| The tokenizer panel | `uv run python tools/tokenizer_panel.py check` |
| The single-edit enumeration | `uv run python tools/run_enumerations.py both` |
| The originality of words | `uv run python tools/compare_roots.py compare` |
| The originality of glyphs | `uv run python tools/compare_glyphs.py` |
| The reviewer's reading | `uv run python tools/review_linguisticity.py DIRECTORY`, then the reading recorded with `record` |

The comparison of the implementations and the enumeration take hours. Continuous integration divides each among jobs with `--shard K/N`, each job checking the K-th of N interleaved parts, and either can be run locally the same way.

## A pull request

A pull request makes one change, and its description follows the template GitHub offers when it is opened. The maintainers merge it when it meets its rule of change, every objection of its review has a written answer, and the gate has passed over its final commit; they do not choose among designs that meet the rule ([Who proposes and who merges](governance/README.md#who-proposes-and-who-merges)).

No formatter is imposed: a change follows the style of the code around it, and the TypeScript passes its type check. A comment or a document that relies on a rule of the language links the section of the specification that states it, as [`specification/protocol.md#the-move-check-word`](specification/protocol.md#the-move-check-word) does, and cites no file the repository lacks.

## Conduct and licence

Everyone who takes part, and every agent an operator runs here, follows the [code of conduct](CODE_OF_CONDUCT.md). A contribution is licensed under the licence of the directory it changes, as [`LICENSING.md`](LICENSING.md) states.
