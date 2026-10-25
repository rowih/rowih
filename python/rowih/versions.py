"""Version identifiers (specification/protocol.md#versions-and-features). A version is two
integers, its major and minor numbers, written with the decimal point between them and
neither with a leading zero; versions are compared as pairs of integers, so that 0.10
follows 0.9 and is not 0.1."""
from __future__ import annotations

import re

_FORM = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z")


def parse(text: str) -> tuple[int, int] | None:
    """The major and minor numbers of `text`, or None where it is not a version."""
    m = _FORM.match(text)
    return (int(m.group(1)), int(m.group(2))) if m else None


def well_formed(text: str) -> bool:
    return parse(text) is not None


def key(text: str) -> tuple[int, int]:
    """The sort key of a version; a text that is not one is refused."""
    pair = parse(text)
    if pair is None:
        raise ValueError("not a version: %r" % text)
    return pair


def major(text: str) -> int:
    return key(text)[0]


def ordered(texts) -> list:
    """The versions in ascending order."""
    return sorted(texts, key=key)
