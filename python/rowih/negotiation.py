"""Version and feature negotiation (specification/protocol.md#versions-and-features).

An agent states what it reads in the protocol statement `UNDERSTANDS`: the language,
lexicon and protocol releases it reads, the dialect releases it holds, each with its
digest, and the features it lacks. Two agents that have exchanged these statements need no
further round, since each computes the same common subset by one rule, as each computes
the precedence of crossing moves (specification/discourse.md#crossing-moves): for the
language, the latest release both read; for the lexicon, the latest release both read that
a message of that language may name; for the protocol, the latest version both read; every
dialect release both hold under one digest, the latest of each dialect; and every feature
either lacks. Agents degrade to their common subset
(specification/protocol.md#versions-and-features), and a speaker writes nothing outside it
to a hearer whose statement it holds.

A hearer that cannot interpret a message states `LACKS`, naming the message by its
channel and serial and what of it the hearer lacks; the speaker restates the message's
moves within the common subset, or both record a loss (failure modes, `protocol/
version-mismatch`)."""
from __future__ import annotations

from . import data, releases, versions


def understood_parts(reader: releases.Reader = releases.FULL) -> list:
    """The parts of the statement `UNDERSTANDS` for a reader: the dialects it offers are
    those it is configured with, since holding a dialect is not offering it for an
    exchange, and a statement, like any message, stays within the message maximum."""
    reads = reader.reads()
    held = data.dialect_releases()
    parts = [(kind, tuple(versions.ordered(reads[kind])))
             for kind in ("language", "lexicon", "protocol")]
    parts += [("dialect", number, version, held[(number, version)]["digest"])
              for number, version in (reader.dialects or ()) if (number, version) in held]
    if reads["lacking"]:
        parts.append(("lacking", tuple(sorted(reads["lacking"]))))
    return parts


def read_statement(parts) -> dict:
    """What a statement of `UNDERSTANDS`, or the lacking parts of `LACKS`, states."""
    out = {"language": [], "lexicon": [], "protocol": [], "dialects": [], "lacking": []}
    for part in parts:
        kind = part[0]
        if kind in ("language", "lexicon", "protocol"):
            out[kind] = list(part[1])
        elif kind == "dialect":
            out["dialects"].append((int(part[1]), part[2], part[3]))
        elif kind == "lacking":
            out["lacking"] = list(part[1])
    return out


def common(mine: dict, theirs: dict) -> dict | None:
    """The common subset of two statements, or None where they share no language, lexicon
    or protocol release a message can be written in."""
    language = _latest(set(mine["language"]) & set(theirs["language"]))
    protocol = _latest(set(mine["protocol"]) & set(theirs["protocol"]))
    if language is None or protocol is None:
        return None
    record = next(r for r in data.language_releases()["language"]
                  if r["language"] == language)
    least = record.get("least lexicon", record["lexicon"])
    lexicon = _latest(v for v in set(mine["lexicon"]) & set(theirs["lexicon"])
                      if versions.key(least) <= versions.key(v))
    if lexicon is None:
        return None
    shared = set(map(tuple, mine["dialects"])) & set(map(tuple, theirs["dialects"]))
    latest = {}
    for number, version, digest in shared:
        held = data.dialect_releases().get((number, version))
        if held is None or versions.key(held["formed from lexicon"]) > versions.key(lexicon):
            continue
        if number not in latest or versions.key(version) > versions.key(latest[number][1]):
            latest[number] = (number, version, digest)
    return {"language": language, "lexicon": lexicon, "protocol": protocol,
            "dialects": [latest[n] for n in sorted(latest)],
            "lacking": sorted(set(mine["lacking"]) | set(theirs["lacking"]))}


def _latest(found) -> str | None:
    found = list(found)
    return max(found, key=versions.key) if found else None


def lacks_parts(channel: tuple, serial: int, lacking: dict) -> list:
    """The parts of `LACKS` for a message, by its channel's recipients and its serial,
    from what an analysis found the reader to lack of it."""
    parts = [("channel", tuple(int(r) for r in channel), (int(serial),))]
    for kind in ("language", "lexicon", "protocol"):
        for version in lacking.get(kind, []):
            parts.append((kind, (version,)))
    for number, version, digest in sorted(lacking.get("dialects", [])):
        parts.append(("dialect", number, version, digest))
    if lacking.get("features"):
        parts.append(("lacking", tuple(sorted(lacking["features"]))))
    return parts
