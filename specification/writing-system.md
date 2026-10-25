# The writing system

The language has a writing system of its own: one component for each of its nineteen symbols, drawn on a small lattice, a word being the cluster of its components side by side. The units of a move are drawn as sides joined by rules beneath the words they enclose, numbers stand in frames, protected words are overlined and embedded material stands between walls, so that the structure a reader of the transliteration finds by the brackets is visible on the page. Nothing in colour or in layout carries meaning, and every drawing is a view of the message that can be read back to its words. This chapter states the components, how a word and a message are drawn, the native digital form, the font and the renderings.

## The components

A component is drawn on a lattice of ten points in three rows, the upper and lower rows of three points and the middle row of four, each row half a column across from the next:

| Row (y) | Points (x) |
|---|---|
| 0 | 2, 6, 10 |
| 6 | 0, 4, 8, 12 |
| 12 | 2, 6, 10 |

Coordinates are in lattice units, x to the right and y downward, within a box twelve units wide and twelve tall. A **unit stroke** joins two points four units apart in a row, or two neighbouring points of neighbouring rows; there are nineteen, and none is upright, so that an upright line in a drawing is never part of a component. The lattice maps onto itself under the turn by half a circle and the mirrors about the upright and the level axes.

Each component is a set of four or six unit strokes, written in at most two strokes of the pen, each from its left end. The pen strokes are listed in [`language/writing.json`](../language/writing.json), and they draw exactly the unit strokes of the component.

<!-- generated: components -->
| Symbol | Code point | Pen strokes, each a polyline of lattice points |
|---|---|---|
| `p` | U+F3A0 | (6,12) (2,12) (0,6) (12,6) (10,0) |
| `t` | U+F3A1 | (4,6) (8,6) (10,0) (12,6) (8,6) (6,12) (10,12) |
| `k` | U+F3A2 | (4,6) (6,0) (8,6) (10,0) (12,6) (10,12) (8,6) |
| `b` | U+F3A3 | (0,6) (4,6) (6,0) (10,0) (12,6) (10,12) ; (4,6) (6,12) |
| `d` | U+F3A4 | (2,0) (6,12) (8,6) (12,6) (10,12) ; (2,12) (6,12) |
| `g` | U+F3A5 | (2,0) (4,6) (6,0) (10,0) ; (2,12) (4,6) (6,12) (10,12) |
| `m` | U+F3A6 | (6,0) (2,0) (4,6) (2,12) (10,12) (12,6) |
| `n` | U+F3A7 | (0,6) (8,6) (6,0) (10,0) ; (8,6) (6,12) (10,12) |
| `s` | U+F3A8 | (6,0) (2,0) (4,6) (8,6) (10,12) |
| `l` | U+F3A9 | (2,0) (0,6) (4,6) (6,12) (8,6) (12,6) (10,0) |
| `r` | U+F3AA | (2,12) (0,6) (4,6) (2,0) (6,0) (8,6) ; (4,6) (6,12) |
| `w` | U+F3AB | (2,12) (0,6) (2,0) (10,0) (12,6) ; (4,6) (6,0) |
| `y` | U+F3AC | (2,0) (4,6) (6,0) (10,0) ; (2,12) (6,12) (8,6) (4,6) |
| `h` | U+F3AD | (0,6) (4,6) (2,12) (10,12) (6,0) |
| `a` | U+F3AE | (2,0) (4,6) (6,0) (10,12) ; (4,6) (6,12) (8,6) |
| `e` | U+F3AF | (2,0) (4,6) (12,6) ; (2,12) (4,6) |
| `i` | U+F3B0 | (0,6) (2,0) (6,0) (4,6) (8,6) (6,12) (10,12) |
| `o` | U+F3B1 | (0,6) (2,0) (4,6) (8,6) (10,0) (12,6) (10,12) |
| `u` | U+F3B2 | (2,0) (10,0) (12,6) (8,6) (10,12) ; (6,12) (8,6) |
<!-- end generated -->

The distance between two components is one minus the Jaccard similarity of their sets of unit strokes, the least over the lattice's turns and mirrors of the second, so that no component is another turned or mirrored. The least distance between two components is 0.667, in 72 pairs, and the mean 0.753. The visual distance between two forms of one length is the sum of the distances of the components at the positions where they differ, and forms of different lengths are told apart by their length. Over the 507 pairs of words of one length that differ in a critical dimension, the least visual distance is 1.467, in nine pairs, above the 1.333 that two components at the least distance would give, and the mean is 2.812. The components were chosen by a seeded search over every admissible set of strokes, and assigned to the symbols to make the least distance between critical words as large as it could be.

## Drawing a word and a line

A word is drawn as its components, left to right, each in its own box, with four units between components and eight between words, so a word of *n* symbols is 16*n* − 4 units wide. The drawing of a message is a stack of lines, the envelope first and then each move.

- **Units.** The opening and the closing word of an assertion, a situation, a term or a set of readings are drawn as upright **sides**, each bearing the mark of its unit above it, and the two sides of a unit are joined by a **rule** beneath the line. A unit's rule lies lower the more units it encloses, so that nesting can be read from the depth of the rules. A side whose unit is not closed on the line is drawn with a short foot turned toward its unit's inside. The mark of a unit is a closed figure whose number of sides names it:

<!-- generated: unit-marks -->
| Unit | Opened and closed by | Sides of its mark | Mark |
|---|---|---|---|
| assertion | `wora` … `woye` | 3 | (0,0) (2,-6) (4,0) (0,0) |
| situation | `wopi` … `woko` | 4 | (0,0) (2,-6) (6,-6) (4,0) (0,0) |
| term | `wodu` … `wuwa` | 4 | (0,0) (2,-6) (6,-6) (8,0) (0,0) |
| readings | `wuhe` … `wuti` | 6 | (0,0) (-2,-6) (2,-12) (6,-12) (8,-6) (4,0) (0,0) |
<!-- end generated -->

- **Walls.** The two words that enclose embedded material are drawn as **walls**, two uprights four units apart running the depth of the line, each with a tick at its top turned toward the inside. Quotations, examples and declared data are enclosed alike, and are told apart by the word that follows the opening wall.
- **Numbers.** A run of numerals is drawn inside a **frame**, a hexagon pointed at both ends; its digits are clusters like any word.
- **Protected words.** The words of force, standing, time and polarity are drawn with an **overline**.
- **Payloads.** The base-32 text of a payload, and any character of a damaged message that is not a symbol, is drawn as text.
- **The envelope** is drawn between two strip rules, above and below its line.
- **The ceremonial register.** A move in the ceremonial register is drawn with a serif across each free end of each component, and its rules and overlines doubled.

The drawing has three forms. The **display** form draws the components at their size on the lattice. The **compact** form is the display form at half size, every coordinate halved. The **handwritten** form joins the components of a word by hairlines, from where the pen leaves one to where it starts the next. The ceremonial variant applies to any of them.

<!-- generated: writing-metrics -->
| Metric | Value |
|---|---|
| gap | 4 |
| word gap | 8 |
| side | 8 |
| frame space | 8 |
| above | 16 |
| rule depth | 8 |
| rule step | 4 |
| below | 6 |
| overline | 4 |
| frame | 12 |
| strip | 8 |
| margin | 8 |
| line gap | 4 |
| character | 6 |
| text size | 8 |
| stroke | 1.5 |
| hairline | 0.75 |
| pixels per unit | 4 |
| serif | 2 |
| double | 2 |
<!-- end generated -->

The metrics are in lattice units, except the stroke and hairline widths, which are the widths of the drawn lines in those units, and *pixels per unit*, the scale of the raster image. Every metric but the two widths is even, so that the compact form halves every coordinate exactly.

A drawing loses nothing the transliteration has: the canonical implementation reads every line of a drawing back to its words from its geometry alone, the components by their unit strokes, the sides by their marks and rules, the walls by their ticks and the text as text, and its tests read back the drawings of the corpus in all three forms.

## The native digital form

The native digital form writes each symbol as one code point of the Unicode Private Use Area, from U+F3A0 for *p* to U+F3B2 for *u*, in the order of [The sounds and the shapes of words](sounds-and-words.md#the-symbols); the code points U+F3B3 to U+F3BF of the declared block are reserved. Payloads are written as their ASCII text, words are separated by U+0020 and each line ends with U+000A. The native digital form and the transliteration are two spellings of one string of symbols, and convert into each other without loss. A text is in the native digital form if any of its characters is one of the nineteen code points; a code point of the block that is not a symbol is reported as foreign use, `d.tokenizer.foreign-use-of-the-range`, and a word mixing the two spellings as `d.tokenizer.mixed-encodings`. No code point of the block has a decomposition, so Unicode normalisation leaves the native digital form unchanged.

The block lies in the part of the Private Use Area that the Under-ConScript Unicode Registry reserves for hacks and corporate use, and outside the ranges that the Nerd Fonts icon set fills, so that a common system font is unlikely to draw something else in its place. The native digital form is about six times as costly in tokens as the transliteration, since each code point is three bytes in UTF-8, and the transliteration is the form for transport among language models ([Conformance](conformance.md#token-measurements)).

## The font

The font [`language/font/rowih.ttf`](../language/font/rowih.ttf) draws the native digital form. It is built deterministically from [`language/writing.json`](../language/writing.json) by [`tools/build_font.py`](../tools/build_font.py), and a test compares the committed font with a fresh build. A lattice unit is 50 font units, so a component is 600 units square on an em of 1,000, and advances 800. Each pen stroke is drawn as rectangles and octagons of the stroke's width, joined by a nonzero fill.

The font holds a glyph for each of the nineteen symbols, a glyph for the space, and, through the OpenType feature `liga`, glyphs for the opening and closing words of the units and walls, drawn as lone sides and walls, and for each protected word, drawn with its overline; a ligature applies only to a whole word, never within a longer one. The stylistic set `ss01`, named *Ceremonial*, gives the ceremonial variant of every glyph. A font cannot join two sides by a rule, frame a number or join a word's components by hairlines, so text set in the font shows units as lone sides; a system that does not apply ligatures shows the sides and protected words as plain clusters, and loses no word.

## The renderings

The canonical implementation renders a message as SVG, PNG, HTML or text for a terminal, in any of the three forms, in normal or high contrast. Every rendering is a view made by its receiver, and its text alternative is the canonical transliteration.

- **SVG.** One SVG user unit is one lattice unit. The image is titled with the transliteration and described as "A view of the native written form, made by this receiver."; its lines are drawn as polylines with round caps and joins, in `currentColor`, or in black on white in high contrast.
- **PNG.** An eight-bit greyscale image at four pixels a lattice unit. Each segment is drawn as a stroke with round ends, a pixel taking the darkest grey any segment gives it, so the order of drawing does not matter; text, which the image cannot carry without a font, is drawn as the outline of its box. The image is compressed by a fixed procedure, so that the two implementations write the same bytes. In high contrast every grey is made black or white, and the strokes are half as wide again.
- **HTML.** The SVG within a `figure` of class `rowih`, captioned with the transliteration marked as the artificial language `art`, so that a screen reader does not read it as English.
- **Terminal.** The native digital form where the terminal has the font, and the transliteration otherwise, never a box or a substitute glyph. The command `rowih render --format terminal` cannot tell whether the terminal has the font and prints the transliteration.

## What the writing system has been tested on

A language model given only the key to the components read random strings of five components drawn as the language draws a word: all 100 at 48 and at 24 pixels a component, and 44 of 100 at 12 pixels, its errors falling on the pairs the measure of distance predicts. The raster scale of four pixels a unit, which draws a component 48 pixels tall in the display form and 24 in the compact form, was chosen from that reading. No human reader has read the writing system, so the size at which a person reads it, and the confusions a person makes, are unmeasured. The components were also compared, as drawn, with 34 reference alphabets, and pass the three criteria of that comparison.
