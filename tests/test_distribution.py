"""The entries by which hosts find the toolchain: the server's entry for the MCP Registry
(server.json), the plugin and the marketplace that Claude Code reads (.claude-plugin/), and
the line of the package's description by which the registry knows the package as the
entry's. Each names the packages' own release, starts the server the command offers, and
loads the skill the repository holds, and each check refuses an entry planted with the
defect it looks for. The entries are files only the public repository has, so they are in
release/public here and at the root there."""
import copy
import json
import re
from pathlib import Path

import pytest

from rowih import cli

ROOT = Path(__file__).resolve().parent.parent
NAME = "io.github.rowih/rowih"          # the entry's name, in the organisation's namespace
SCHEMA = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"


def public(path: str) -> Path:
    """A file only the public repository has: in release/public here, at the root there."""
    for candidate in (ROOT / "release" / "public" / path, ROOT / path):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(path)


def version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    return re.search(r'^version = "([0-9.]+)"', text, re.M).group(1)


def _json(path: str) -> dict:
    return json.loads(public(path).read_text(encoding="utf-8"))


def server_command() -> list:
    """The command line that starts the server, as the command's own parser accepts it."""
    return ["rowih", "serve"]


# ------------------------------------------------------------- the registry's entry

def entry_problems(entry: dict, release: str) -> list:
    """What keeps `entry` from being the registry's entry for this release's package."""
    problems = []
    if entry.get("$schema") != SCHEMA:
        problems.append("schema")
    if entry.get("name") != NAME:
        problems.append("name")
    for field in ("title", "description"):
        if not 1 <= len(entry.get(field, "")) <= 100:      # the registry's limit
            problems.append(field)
    if entry.get("version") != release:
        problems.append("version")
    if entry.get("repository") != {"url": "https://github.com/rowih/rowih", "source": "github"}:
        problems.append("repository")
    packages = entry.get("packages", [])
    if len(packages) != 1:
        return problems + ["packages"]
    package = packages[0]
    if (package.get("registryType"), package.get("identifier")) != ("pypi", "rowih"):
        problems.append("package")
    if package.get("version") != release:
        problems.append("package version")
    if package.get("runtimeHint") != "uvx" or package.get("transport") != {"type": "stdio"}:
        problems.append("runtime")
    arguments = [a.get("value") for a in package.get("packageArguments", [])
                 if a.get("type") == "positional"]
    if ["rowih"] + arguments != server_command():
        problems.append("arguments")
    return problems


def test_the_entry_names_the_package_at_its_own_release():
    assert entry_problems(_json("server.json"), version()) == []


def test_the_entry_check_refuses_each_planted_defect():
    entry = _json("server.json")
    planted = {
        "name": lambda e: e.update(name="io.github.someone/rowih"),
        "description": lambda e: e.update(description="x" * 101),
        "version": lambda e: e.update(version="0.0.1"),
        "package version": lambda e: e["packages"][0].update(version="0.0.1"),
        "package": lambda e: e["packages"][0].update(identifier="rowih-server"),
        "runtime": lambda e: e["packages"][0].update(runtimeHint="npx"),
        "arguments": lambda e: e["packages"][0].update(packageArguments=[]),
    }
    for problem, plant in planted.items():
        damaged = copy.deepcopy(entry)
        plant(damaged)
        assert problem in entry_problems(damaged, version()), problem


def test_the_command_the_entries_start_is_the_server(capsys):
    assert cli.main(server_command()[1:] + ["--help"]) == 0
    assert capsys.readouterr().out.startswith("usage: rowih serve")
    assert cli.main(["serves", "--help"]) == 2


# -------------------------------------------------------- the package's description

def marker_problems(description: str) -> list:
    """The registry reads `mcp-name: NAME` in the package's description, followed by a
    boundary, and the line stays out of what PyPI shows inside an HTML comment."""
    found = re.findall(r"<!-- mcp-name: (\S+) -->\n", description)
    return [] if found == [NAME] else ["marker"]


def test_the_package_s_description_names_the_entry():
    description = (ROOT / "python" / "README.md").read_text(encoding="utf-8")
    assert marker_problems(description) == []
    assert marker_problems(description.replace(NAME, "io.github.someone/rowih")) == ["marker"]
    assert marker_problems(description.replace("<!-- mcp-name", "<!-- mcp name")) == ["marker"]


# ------------------------------------------------------------- the plugin

def plugin_problems(plugin: dict, release: str, root: Path) -> list:
    """What keeps `plugin` from loading the repository's skill and the released server."""
    problems = []
    if plugin.get("name") != "rowih" or plugin.get("version") != release:
        problems.append("name or version")
    skills = plugin.get("skills", [])
    if not skills or not all((root / s / "rowih" / "SKILL.md").exists() for s in skills):
        problems.append("skills")
    expected = {"command": "uvx", "args": ["--from", "rowih==%s" % release] + server_command()}
    if plugin.get("mcpServers") != {"rowih": expected}:
        problems.append("server")
    return problems


def test_the_plugin_loads_the_skill_and_starts_the_released_server():
    assert plugin_problems(_json(".claude-plugin/plugin.json"), version(), ROOT) == []


def test_the_plugin_check_refuses_each_planted_defect():
    plugin = _json(".claude-plugin/plugin.json")
    planted = {
        "name or version": lambda p: p.update(version="0.0.1"),
        "skills": lambda p: p.update(skills=["./skills/"]),
        "server": lambda p: p["mcpServers"]["rowih"]["args"].__setitem__(1, "rowih"),
    }
    for problem, plant in planted.items():
        damaged = copy.deepcopy(plugin)
        plant(damaged)
        assert problem in plugin_problems(damaged, version(), ROOT), problem


def test_the_marketplace_lists_the_plugin_at_its_own_root():
    marketplace = _json(".claude-plugin/marketplace.json")
    plugin = _json(".claude-plugin/plugin.json")
    assert marketplace["name"] == "rowih" and marketplace["owner"]["name"]
    assert marketplace["description"]
    assert [(p["name"], p["source"]) for p in marketplace["plugins"]] == [(plugin["name"], "./")]


def test_the_pages_install_the_plugin_the_marketplace_lists_at_its_release():
    marketplace = _json(".claude-plugin/marketplace.json")
    install = "/plugin install %s@%s" % (marketplace["plugins"][0]["name"], marketplace["name"])
    for page in ("README.md", "python/README.md"):
        text = (ROOT / page).read_text(encoding="utf-8")
        assert "/plugin marketplace add rowih/rowih" in text and install in text, page
        assert re.findall(r"rowih==([0-9.]+)", text) == [version()], page
