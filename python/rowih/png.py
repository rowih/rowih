"""The PNG output of the renderer (specification/writing-system.md#the-renderings).

A greyscale image is written as a PNG (ISO/IEC 15948:2004) whose image data is one zlib
stream (RFC 1950) holding one DEFLATE block with the fixed Huffman codes (RFC 1951
§ 3.2.6). The compressor is declared, so that the TypeScript implementation, which
writes the same bytes, can follow it step by step: at each position it takes the longer
of two back-references, the byte one row above and the byte before, preferring the row
above on a tie, if either is at least three bytes long, and otherwise writes the byte as
a literal. Every row is preceded by filter type 0. The image's text alternative, the
transliteration, is carried in a tEXt chunk with the keyword "Description".
"""
from __future__ import annotations

import struct

MAX_MATCH = 258
MIN_MATCH = 3
WINDOW = 32768

# RFC 1951 § 3.2.5: the base of each length code from 257 and its extra bits, and the
# base of each distance code and its extra bits.
LENGTH_BASE = [3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59,
               67, 83, 99, 115, 131, 163, 195, 227, 258]
LENGTH_EXTRA = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4,
                5, 5, 5, 5, 0]
DISTANCE_BASE = [1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513,
                 769, 1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577]
DISTANCE_EXTRA = [0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10,
                  10, 11, 11, 12, 12, 13, 13]


def _crc_table() -> list:
    table = []
    for n in range(256):
        c = n
        for _ in range(8):
            c = (0xEDB88320 ^ (c >> 1)) if c & 1 else (c >> 1)
        table.append(c)
    return table


CRC_TABLE = _crc_table()


def crc32(data: bytes) -> int:
    """The CRC of ISO/IEC 15948 Annex D."""
    c = 0xFFFFFFFF
    for byte in data:
        c = CRC_TABLE[(c ^ byte) & 0xFF] ^ (c >> 8)
    return c ^ 0xFFFFFFFF


def adler32(data: bytes) -> int:
    """The checksum of RFC 1950 § 8."""
    a, b = 1, 0
    for i in range(0, len(data), 5552):
        for byte in data[i:i + 5552]:
            a += byte
            b += a
        a %= 65521
        b %= 65521
    return (b << 16) | a


class _Bits:
    """A bit stream packed from the least significant bit of each byte (RFC 1951 § 3.1.1)."""

    def __init__(self):
        self.out = bytearray()
        self.acc = 0
        self.n = 0

    def put(self, value: int, count: int):
        self.acc |= value << self.n
        self.n += count
        while self.n >= 8:
            self.out.append(self.acc & 0xFF)
            self.acc >>= 8
            self.n -= 8

    def huffman(self, code: int, length: int):
        """A Huffman code, which is packed from its most significant bit."""
        rev = 0
        for _ in range(length):
            rev = (rev << 1) | (code & 1)
            code >>= 1
        self.put(rev, length)

    def finish(self) -> bytes:
        if self.n:
            self.out.append(self.acc & 0xFF)
        return bytes(self.out)


def _literal(bits: _Bits, value: int):
    if value < 144:
        bits.huffman(0x30 + value, 8)
    elif value < 256:
        bits.huffman(0x190 + value - 144, 9)
    elif value < 280:
        bits.huffman(value - 256, 7)
    else:
        bits.huffman(0xC0 + value - 280, 8)


def _match(bits: _Bits, length: int, dist: int):
    code = 0
    while code + 1 < len(LENGTH_BASE) and LENGTH_BASE[code + 1] <= length:
        code += 1
    _literal(bits, 257 + code)
    bits.put(length - LENGTH_BASE[code], LENGTH_EXTRA[code])
    dcode = 0
    while dcode + 1 < len(DISTANCE_BASE) and DISTANCE_BASE[dcode + 1] <= dist:
        dcode += 1
    bits.huffman(dcode, 5)
    bits.put(dist - DISTANCE_BASE[dcode], DISTANCE_EXTRA[dcode])


def _common(data: bytes, i: int, dist: int) -> int:
    """How many bytes from `i` repeat those `dist` before, up to MAX_MATCH."""
    limit = min(MAX_MATCH, len(data) - i)
    if data[i:i + limit] == data[i - dist:i - dist + limit]:
        return limit
    n = 0
    while n < limit and data[i + n] == data[i + n - dist]:
        n += 1
    return n


def deflate(data: bytes, stride: int) -> bytes:
    """The declared compressor: one block of fixed Huffman codes, whose back-references
    are to the byte `stride` before (the row above) or the byte before."""
    bits = _Bits()
    bits.put(1, 1)      # the final block
    bits.put(1, 2)      # fixed Huffman codes
    use_row = 0 < stride <= WINDOW
    i, n = 0, len(data)
    while i < n:
        up = _common(data, i, stride) if use_row and i >= stride else 0
        run = _common(data, i, 1) if i >= 1 else 0
        if up >= MIN_MATCH and up >= run:
            _match(bits, up, stride)
            i += up
        elif run >= MIN_MATCH:
            _match(bits, run, 1)
            i += run
        else:
            _literal(bits, data[i])
            i += 1
    _literal(bits, 256)
    return bits.finish()


def zlib_stream(data: bytes, stride: int) -> bytes:
    """RFC 1950: the header for DEFLATE with a 32 KiB window and no dictionary, the
    block, and the Adler-32 of the data."""
    return b"\x78\x01" + deflate(data, stride) + struct.pack(">I", adler32(data))


def _chunk(kind: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", crc32(kind + body))


def encode(width: int, height: int, pixels, description: str = "") -> bytes:
    """A greyscale PNG of `pixels`, rows of `width` bytes from the top, 0 black."""
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw += bytes(pixels[y * width:(y + 1) * width])
    out = b"\x89PNG\r\n\x1a\n"
    out += _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
    if description:
        out += _chunk(b"tEXt", b"Description\x00" + description.encode("latin-1"))
    out += _chunk(b"IDAT", zlib_stream(bytes(raw), width + 1))
    out += _chunk(b"IEND", b"")
    return out
