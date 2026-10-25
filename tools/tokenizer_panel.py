"""The tokenizer panel (specification/conformance.md#token-measurements): a named,
versioned panel of the tokenizers through which language models that act as agents read
and write, each pinned to a revision of its repository and to the SHA-256 of its file, in
`corpus/tokenizers/panel.json`. The files are fetched into `corpus/tokenizers/cache/`,
which git ignores, and checked against their hashes before use.

`check_panel` encodes the transliteration of every corpus message with each tokenizer
and decodes it, and reports every text that does not come back byte for byte
(`inv.tokenizer-round-trip`). `measure` counts tokens against the language's units, the
word, the move and the node of the normal form, for the transliteration, the native
digital form and the English gloss of the same messages, and writes
`corpus/reports/tokens.json`.

Run from the repository root: `python3 tools/tokenizer_panel.py [fetch|check|measure]`.
`check` exits with status 1 when a tokenizer of the panel does not return a text byte for
byte, or the control returns one, and 0 otherwise.
`pin` resolves the panel's sources afresh and writes the manifest; it is run once for
each version of the panel."""
import hashlib
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))
sys.path.insert(0, os.path.join(ROOT, "tests"))

PANEL = os.path.join(ROOT, "corpus", "tokenizers", "panel.json")
CACHE = os.path.join(ROOT, "corpus", "tokenizers", "cache")
TIMEOUT = 120
SOURCE = "https://huggingface.co/%s/resolve/%s/tokenizer.json"

# The panel's members, each (name, the family of models that reads through it,
# repository), and the control, a tokenizer no agent model of the panel reads through,
# whose normaliser is known to rewrite whitespace: the check run on it must report
# failures, or the check is not sound. Llama and Gemma are gated and Claude's tokenizer
# is not published, so none of them is on the panel.
MEMBERS = [
    ("o200k harmony", "OpenAI GPT-4o, o-series and gpt-oss", "openai/gpt-oss-20b"),
    ("cl100k", "OpenAI GPT-4 and Microsoft Phi-4", "microsoft/phi-4"),
    ("qwen2", "Qwen 2.5", "Qwen/Qwen2.5-7B-Instruct"),
    ("deepseek-v3", "DeepSeek V3", "deepseek-ai/DeepSeek-V3"),
    ("tekken", "Mistral NeMo", "mistralai/Mistral-Nemo-Instruct-2407"),
    ("mistral v3", "Mistral 7B v0.3", "mistralai/Mistral-7B-Instruct-v0.3"),
    ("llama 2 sentencepiece", "Microsoft Phi-3.5", "microsoft/Phi-3.5-mini-instruct"),
    ("dolma2", "AllenAI OLMo 2", "allenai/OLMo-2-1124-7B-Instruct"),
    ("granite", "IBM Granite 3.1", "ibm-granite/granite-3.1-8b-instruct"),
    ("smollm2", "Hugging Face SmolLM2", "HuggingFaceTB/SmolLM2-1.7B-Instruct"),
    ("glm-4.5", "Z.ai GLM 4.5", "zai-org/GLM-4.5"),
    ("falcon3", "TII Falcon 3", "tiiuae/Falcon3-7B-Instruct"),
    ("gpt-neox", "EleutherAI GPT-NeoX and Pythia", "EleutherAI/gpt-neox-20b"),
]
CONTROL = ("t5", "Google T5, a control: its normaliser rewrites whitespace",
           "google-t5/t5-base")


def _get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
        return response.read()


def pin(revisions: dict) -> dict:
    """The manifest of panel version 1, from the revision of each repository: each file
    downloaded once, hashed and kept in the cache."""
    def record(name, family, repository):
        revision = revisions[repository]
        data = _get(SOURCE % (repository, revision))
        _keep(name, data)
        return {"name": name, "family": family, "repository": repository,
                "revision": revision, "file": "tokenizer.json",
                "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    return {"name": "rowih tokenizer panel", "version": 1,
            "pinned": "2026-10-13",
            "rule": "decoding the encoding of a transliteration, with no special tokens "
                    "added and none skipped, returns it byte for byte",
            "members": [record(*m) for m in MEMBERS], "control": record(*CONTROL)}


def _path(name: str) -> str:
    return os.path.join(CACHE, name.replace(" ", "-") + ".json")


def _keep(name: str, data: bytes):
    os.makedirs(CACHE, exist_ok=True)
    with open(_path(name), "wb") as f:
        f.write(data)


def load_panel() -> dict:
    with open(PANEL, encoding="utf-8") as f:
        return json.load(f)


def fetch(panel: dict):
    """Fetch every file the panel names that the cache lacks, and check every file
    against its hash; a mismatch stops, since a tokenizer that changed is another
    tokenizer."""
    for m in panel["members"] + [panel["control"]]:
        path = _path(m["name"])
        if not os.path.exists(path):
            _keep(m["name"], _get(SOURCE % (m["repository"], m["revision"])))
        with open(path, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        if digest != m["sha256"]:
            raise SystemExit("%s: the cached file's SHA-256 is %s, the panel's %s"
                             % (m["name"], digest, m["sha256"]))


def tokenizer(member: dict):
    from tokenizers import Tokenizer
    return Tokenizer.from_file(_path(member["name"]))


def round_trip(tok, text: str) -> str:
    return tok.decode(tok.encode(text, add_special_tokens=False).ids,
                      skip_special_tokens=False)


def check_panel(panel: dict, texts: list, members=None) -> dict:
    """`check_panel(panel)`: for each tokenizer, the texts whose decoded encoding differs
    from them, each with the first offset at which it does."""
    out = {}
    for m in members if members is not None else panel["members"]:
        tok = tokenizer(m) if isinstance(m, dict) else m[1]
        name = m["name"] if isinstance(m, dict) else m[0]
        failures = []
        for i, text in enumerate(texts):
            back = round_trip(tok, text)
            if back != text:
                at = next((k for k, (a, b) in enumerate(zip(text, back)) if a != b),
                          min(len(text), len(back)))
                failures.append({"text": i, "at": at, "found": back[at:at + 20],
                                 "expected": text[at:at + 20]})
        out[name] = failures
    return out


def corpus_texts() -> list:
    from corpus import messages
    return [t for _, _, _, t in messages()]


def measure(panel: dict) -> dict:
    """Tokens against the language's units for every corpus message: its words, its
    moves and the nodes of its normal form, in the transliteration, the native digital
    form and the English gloss."""
    from rowih import api
    from rowih.english import English
    texts = corpus_texts()
    rows = []
    for text in texts:
        a = api.parse(text)
        native = api.convert(text, "native")[0]
        rows.append({"words": len(a.words), "moves": len(a.moves),
                     "nodes": sum(_nodes(n) for n in a.normal), "transliteration": text,
                     "native": native, "english": "".join(
                         English(sender=a.message.envelope.sender.text).move(n) + "\n"
                         for n in a.normal)})
    totals = {k: sum(r[k] for r in rows) for k in ("words", "moves", "nodes")}
    out = {"panel": "%s %d" % (panel["name"], panel["version"]), "messages": len(rows),
           "units": totals, "characters": {k: sum(len(r[k]) for r in rows)
                                           for k in ("transliteration", "native", "english")},
           "tokenizers": {}}
    for m in panel["members"]:
        tok = tokenizer(m)
        counts = {k: sum(len(tok.encode(r[k], add_special_tokens=False).ids) for r in rows)
                  for k in ("transliteration", "native", "english")}
        out["tokenizers"][m["name"]] = {
            "family": m["family"], "tokens": counts,
            "tokens per word": round(counts["transliteration"] / totals["words"], 3),
            "tokens per move": round(counts["transliteration"] / totals["moves"], 2),
            "tokens per node of the normal form": round(counts["transliteration"]
                                                        / totals["nodes"], 3),
            "native over transliteration": round(counts["native"]
                                                 / counts["transliteration"], 3),
            "transliteration over English": round(counts["transliteration"]
                                                  / counts["english"], 3)}
    return out


def _nodes(node) -> int:
    if isinstance(node, list):
        return sum(_nodes(x) for x in node)
    if isinstance(node, dict):
        own = 1 if node.get("kind") else 0
        return own + sum(_nodes(v) for k, v in node.items() if not k.startswith("_"))
    return 0


def check_failed(failures: dict, control: list, texts: list) -> bool:
    """Whether a check failed: a tokenizer of the panel did not return a text byte for
    byte, or the control, which must return none, returned one."""
    return any(failures.values()) or len(control) != len(texts)


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "check"
    if command == "pin":
        revisions = dict(arg.split("@") for arg in sys.argv[2:])
        manifest = pin(revisions)
        os.makedirs(os.path.dirname(PANEL), exist_ok=True)
        with open(PANEL, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=1)
            f.write("\n")
        return 0
    panel = load_panel()
    fetch(panel)
    if command == "check":
        texts = corpus_texts()
        failures = check_panel(panel, texts)
        control = check_panel(panel, texts, [panel["control"]])
        for name, found in failures.items():
            print("%-24s %d of %d texts not returned" % (name, len(found), len(texts)))
        print("control %-16s %d of %d texts not returned"
              % (panel["control"]["name"], len(control[panel["control"]["name"]]), len(texts)))
        return 1 if check_failed(failures, control[panel["control"]["name"]], texts) else 0
    elif command == "measure":
        report = measure(panel)
        with open(os.path.join(ROOT, "corpus", "reports", "tokens.json"), "w",
                  encoding="utf-8") as f:
            json.dump(report, f, indent=1)
            f.write("\n")
        for name, r in report["tokenizers"].items():
            print("%-24s %s" % (name, {k: v for k, v in r.items() if k != "family"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
