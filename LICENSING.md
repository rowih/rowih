# Licensing

Two licences cover this repository, each by directory. The code is licensed under the [Apache License 2.0](LICENSE), and the language itself, its data and every document under [Creative Commons Attribution 4.0 International](LICENSE-CC-BY-4.0), but for the code of conduct, which is adapted from the Contributor Covenant and keeps its licence, [Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/).

| Directory or file | What it holds | Licence |
|---|---|---|
| `python/`, `typescript/` | The implementations | Apache-2.0 |
| `tools/` | The tools that build the data and run the gate | Apache-2.0 |
| `tests/` | The tests of both implementations, of the data and of the specification | Apache-2.0 |
| `.github/`, `pyproject.toml`, `uv.lock`, `.gitignore` | The continuous integration and the configuration of the build | Apache-2.0 |
| `specification/` | The reference specification | CC BY 4.0 |
| `language/`, `lexicon/` | The canonical data, the font in `language/font/` among them | CC BY 4.0 |
| `corpus/` | The conformance suite, the exchanges and the reports | CC BY 4.0 |
| `examples/` | The exchanges the page shows, with their drawings and recordings | CC BY 4.0 |
| `governance/`, `proposals/` | How the language changes, the registry of dialect numbers and the format of a proposal | CC BY 4.0 |
| `skill/` | The skill that teaches an agent the language | CC BY 4.0 |
| `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `LICENSING.md`, `CITATION.cff` | The documents at the root | CC BY 4.0 |
| `CODE_OF_CONDUCT.md` | The code of conduct, adapted from the Contributor Covenant 3.0 | CC BY-SA 4.0 |

A work that uses the language's data or documents under CC BY 4.0 credits them as *Rowih* with a link to this repository, <https://github.com/rowih/rowih>, and states whether it changed them.

The optional `speech` extra of the Python package depends on eSpeak NG, which is licensed under GPL-3.0-or-later; this repository names it as a dependency and does not contain it. The recordings in `examples/` were synthesised by Kokoro-82M, released under Apache-2.0, and are licensed with the rest of `examples/`.
