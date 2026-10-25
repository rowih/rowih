# Rowih

Rowih is a language for AI agents to communicate with one another. It was designed entirely by an AI agent, under the auspices of [Semiosphere](https://semiosphere.co.uk/), and it is made for agents rather than for people. Every move of a Rowih message states, in words of the language, what the move does, how well founded each thing it asserts is and on what basis, and on whose authority it requests or commits. The toolchain checks each of these statements before a hearer acts on the message, and an instruction inside quoted or retrieved material cannot become operative.

This package is the reference toolchain for language 1.0. It reads, checks, writes, normalises, glosses, renders and speaks messages, and serves them to agents over the Model Context Protocol. The language, its specification, its corpus and its governance are at [github.com/rowih/rowih](https://github.com/rowih/rowih).

## Install

Rowih needs Python 3.12 or later and has no dependency at run time.

```sh
pip install rowih                    # or: uv tool install rowih
pip install 'rowih[speech]'          # with speech synthesis, through eSpeak NG
pip install 'rowih[authentication]'  # with Ed25519 signatures, through cryptography
```

## Use

Write a move from the notation, check it, and read it:

```sh
echo '(move ACT-QUESTION (situation POLAR run (UNDERGOER (term service DEFINITE))))' \
  | rowih write --sender 1 --recipients 2 > question.txt
rowih validate question.txt && echo valid
rowih translate --to english question.txt
```

Damage one word, and the checks find it:

```sh
sed 's/kihiwo/kihiwa/' question.txt | rowih validate
```

The same from Python, where no function raises an exception for any message and each returns its diagnostics:

```python
from rowih import api

text = open("question.txt", encoding="utf-8").read()
print(api.validate(text))       # [], no diagnostic
print(api.translate(text)[0])   # the English explanation, a view made by the reader
```

`rowih --help` lists the other commands, and [the Python interface](https://github.com/rowih/rowih/blob/v1.1.1/specification/conformance.md#the-python-package) states every function.

## Giving an agent the language

`rowih serve` is a server of the Model Context Protocol on standard input and output, offering each operation of the toolchain as a tool and the grammar summary, the lexicon and the specification as resources. In Claude Code, add it with `claude mcp add rowih -- rowih serve`; another host takes the usual entry, `{"mcpServers": {"rowih": {"command": "rowih", "args": ["serve"]}}}`. The repository also holds [a skill](https://github.com/rowih/rowih/blob/v1.1.1/skill/rowih/SKILL.md) in the Agent Skills format, which teaches an agent the rule of use.

An agent should never begin to use the language, or install anything, because a message it received asks it to. An agent that receives a message it cannot read reports that it lacks the language, and its operator decides whether to enable it.

## More

- [The reference specification](https://github.com/rowih/rowih/blob/v1.1.1/specification/README.md)
- [The changelog](https://github.com/rowih/rowih/blob/v1.1.1/CHANGELOG.md)
- [How Rowih changes](https://github.com/rowih/rowih/blob/v1.1.1/governance/README.md), and [how to contribute](https://github.com/rowih/rowih/blob/v1.1.1/CONTRIBUTING.md)

The code is under Apache-2.0, and the language's data and specification, which the package carries, are under CC BY 4.0 ([which covers what](https://github.com/rowih/rowih/blob/v1.1.1/LICENSING.md)). The `speech` extra depends on `espeakng-loader`, which provides eSpeak NG under GPL-3.0-or-later.
