"""The renderer of the native writing system
(specification/writing-system.md#the-renderings): SVG, PNG, HTML and the terminal.

The SVG and the PNG are both written from one drawing (`drawing.draw`), in the display,
compact or handwritten form, with the ceremonial variant for moves in the ceremonial
register. Every rendering is a view made by its receiver, and its text alternative is
the transliteration, which a screen reader can read and which is the ASCII fallback. The
high-contrast rendering draws black on white with strokes half as heavy again; no
distinction depends on colour or on ornament.
"""
from __future__ import annotations

from html import escape

from . import png as png_format
from .data import Language, load
from .drawing import Drawing, draw
from .raster import rasterise

CONTRASTS = ("normal", "high")
HEAVIER = 1.5


def _width(value: float) -> str:
    """A stroke width as the shortest decimal that reads back as the same number."""
    return repr(float(value)).rstrip("0").rstrip(".") if value != int(value) else "%d" % value


def _points(path) -> str:
    return " ".join("%d,%d" % p for p in path.points)


def _heavier(d: Drawing) -> Drawing:
    return Drawing(d.form, d.width, d.height, d.paths, d.texts, d.stroke * HEAVIER,
                   d.hairline * HEAVIER)


def _svg(d: Drawing, alt: str, contrast: str) -> str:
    if contrast == "high":
        d = _heavier(d)
    ink = "#000000" if contrast == "high" else "currentColor"
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" '
             'height="%d" role="img" aria-label="%s"><title>%s</title><desc>A view of the '
             'native written form, made by this receiver.</desc>'
             % (d.width, d.height, d.width, d.height, alt, alt)]
    if contrast == "high":
        parts.append('<rect width="%d" height="%d" fill="#ffffff"/>' % (d.width, d.height))
    for weight, width in (("stroke", d.stroke), ("hairline", d.hairline)):
        paths = [p for p in d.paths if p.weight == weight]
        if paths:
            parts.append('<g fill="none" stroke="%s" stroke-width="%s" '
                         'stroke-linecap="round" stroke-linejoin="round">' % (ink, _width(width)))
            parts += ['<polyline points="%s"/>' % _points(p) for p in paths]
            parts.append("</g>")
    if d.texts:
        parts.append('<g fill="%s" font-family="monospace">' % ink)
        parts += ['<text x="%d" y="%d" font-size="%d">%s</text>'
                  % (t.x, t.y, t.size, escape(t.text)) for t in d.texts]
        parts.append("</g>")
    parts.append("</svg>\n")
    return "".join(parts)


def svg(analysis, lang: Language | None = None, form: str = "display",
        contrast: str = "normal") -> str:
    """The native written form of a parsed message as SVG, a view."""
    lang = lang or load()
    if analysis.message is None:
        return ""
    return _svg(draw(analysis, form, lang), escape(analysis.canonical), contrast)


def png(analysis, lang: Language | None = None, form: str = "display",
        contrast: str = "normal") -> bytes:
    """The native written form of a parsed message as a greyscale PNG, a view, with the
    transliteration as its description."""
    lang = lang or load()
    if analysis.message is None:
        return b""
    d = draw(analysis, form, lang)
    if contrast == "high":
        d = _heavier(d)
    width, height, greys = rasterise(d, lang.writing["pixels per unit"])
    if contrast == "high":
        greys = bytes(0 if g < 128 else 255 for g in greys)
    return png_format.encode(width, height, greys, analysis.canonical)


def terminal(analysis, has_font: bool = False, lang: Language | None = None) -> str:
    """The native digital form where the terminal has the font, else the
    transliteration, never a box or a substitute glyph."""
    lang = lang or load()
    if not has_font:
        return analysis.canonical
    if analysis.message is None:
        return ""
    from .serialise import to_native
    env = analysis.message.envelope
    return to_native([env.words] + analysis.message.lines, lang)


def html(analysis, lang: Language | None = None, form: str = "display",
         contrast: str = "normal", description: str | None = None) -> str:
    """The SVG in a figure whose caption is the transliteration, marked as text in an
    artificial language (BCP 47 `art`) so that a screen reader does not read it as
    English, and, where one is given, the linear semantic description."""
    caption = '<code lang="art">%s</code>' % escape(analysis.canonical)
    if description:
        caption += '<p class="description">%s</p>' % escape(description)
    return ('<figure class="rowih">%s<figcaption>%s</figcaption></figure>\n'
            % (svg(analysis, lang, form, contrast), caption))
