"""The rasterisation of a drawing for the PNG output
(specification/writing-system.md#the-renderings).

Every segment of every path is drawn as a stroke of the drawing's width with round ends:
a pixel's ink is how far its centre lies within half the width of the segment, plus half
a pixel, held between 0 and 1, and a pixel takes the most ink any segment gives it, so
that the order of drawing changes nothing. Grey levels are 255 for no ink and 0 for full
ink, the ink rounded to the nearest of 255 steps. The arithmetic is IEEE double precision
in a fixed order, which the TypeScript implementation repeats, so that the two write the
same bytes; each segment's pixels are computed once for its shape and reused wherever it
recurs, which changes no result, since a segment's end points fall on whole pixels.

Embedded material, which the SVG draws as text, is drawn here as the outline of the space
it takes, since the image carries no font; the text is in the image's description.
"""
from __future__ import annotations

import math

WHITE = 255


def _tile(vx: int, vy: int, radius: float) -> list:
    """The ink of a segment from (0, 0) to (vx, vy) in pixels, as (dx, dy, grey) for each
    pixel it touches, the pixel at dx, dy having its centre at (dx + 0.5, dy + 0.5)."""
    reach = int(math.ceil(radius)) + 1
    length2 = vx * vx + vy * vy
    out = []
    for dy in range(min(0, vy) - reach, max(0, vy) + reach):
        for dx in range(min(0, vx) - reach, max(0, vx) + reach):
            wx = dx + 0.5
            wy = dy + 0.5
            t = 0.0
            if length2 > 0:
                t = (wx * vx + wy * vy) / length2
                if t < 0.0:
                    t = 0.0
                elif t > 1.0:
                    t = 1.0
            ex = wx - t * vx
            ey = wy - t * vy
            ink = radius + 0.5 - math.sqrt(ex * ex + ey * ey)
            if ink <= 0.0:
                continue
            if ink > 1.0:
                ink = 1.0
            out.append((dx, dy, WHITE - int(math.floor(255.0 * ink + 0.5))))
    return out


def rasterise(drawing, pixels_per_unit: int) -> tuple:
    """The drawing as (width, height, greys), rows from the top."""
    s = pixels_per_unit
    width, height = drawing.width * s, drawing.height * s
    greys = bytearray([WHITE]) * (width * height)
    tiles = {}
    radii = {"stroke": drawing.stroke * s / 2, "hairline": drawing.hairline * s / 2}

    def segment(ax: int, ay: int, bx: int, by: int, radius: float):
        key = (bx - ax, by - ay, radius)
        if key not in tiles:
            tiles[key] = _tile(bx - ax, by - ay, radius)
        for dx, dy, grey in tiles[key]:
            x, y = ax + dx, ay + dy
            if 0 <= x < width and 0 <= y < height:
                i = y * width + x
                if grey < greys[i]:
                    greys[i] = grey

    for path in drawing.paths:
        r = radii[path.weight]
        pts = [(x * s, y * s) for x, y in path.points]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            segment(ax, ay, bx, by, r)
    for t in drawing.texts:
        x0, x1 = t.x * s, (t.x + t.width) * s
        y0, y1 = (t.y - t.size) * s, t.y * s
        r = radii["hairline"]
        for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)),
                     ((x0, y1), (x0, y0))):
            segment(a[0], a[1], b[0], b[1], r)
    return width, height, greys
