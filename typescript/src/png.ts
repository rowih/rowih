// The PNG output of the renderer (specification/writing-system.md#the-renderings), the
// canonical implementation's `png` step for step: a greyscale image as a PNG (ISO/IEC
// 15948:2004) whose image data is one zlib stream (RFC 1950) holding one DEFLATE block
// with the fixed Huffman codes (RFC 1951 § 3.2.6). The compressor is declared: at each
// position it takes the longer of two back-references, the byte one row above and the
// byte before, preferring the row above on a tie, if either is at least three bytes long,
// and otherwise writes the byte as a literal. The transliteration is carried in a tEXt
// chunk with the keyword "Description".

const MAX_MATCH = 258;
const MIN_MATCH = 3;
const WINDOW = 32768;

// RFC 1951 § 3.2.5: the base of each length code from 257 and its extra bits, and the
// base of each distance code and its extra bits.
const LENGTH_BASE = [3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59,
  67, 83, 99, 115, 131, 163, 195, 227, 258];
const LENGTH_EXTRA = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4,
  5, 5, 5, 5, 0];
const DISTANCE_BASE = [1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385,
  513, 769, 1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577];
const DISTANCE_EXTRA = [0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10,
  10, 11, 11, 12, 12, 13, 13];

const CRC_TABLE: number[] = [];
for (let n = 0; n < 256; n++) {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? (0xEDB88320 ^ (c >>> 1)) >>> 0 : c >>> 1;
  CRC_TABLE.push(c);
}

/** The CRC of ISO/IEC 15948 Annex D. */
export function crc32(data: Uint8Array): number {
  let c = 0xFFFFFFFF;
  for (const byte of data) c = (CRC_TABLE[(c ^ byte) & 0xFF] ^ (c >>> 8)) >>> 0;
  return (c ^ 0xFFFFFFFF) >>> 0;
}

/** The checksum of RFC 1950 § 8. */
export function adler32(data: Uint8Array): number {
  let a = 1;
  let b = 0;
  for (let i = 0; i < data.length; i += 5552) {
    const end = Math.min(data.length, i + 5552);
    for (let j = i; j < end; j++) {
      a += data[j];
      b += a;
    }
    a %= 65521;
    b %= 65521;
  }
  return b * 65536 + a;
}

/** A bit stream packed from the least significant bit of each byte (RFC 1951 § 3.1.1). */
class Bits {
  out: number[] = [];
  acc = 0;
  n = 0;

  put(value: number, count: number): void {
    this.acc |= value << this.n;
    this.n += count;
    while (this.n >= 8) {
      this.out.push(this.acc & 0xFF);
      this.acc >>>= 8;
      this.n -= 8;
    }
  }

  /** A Huffman code, which is packed from its most significant bit. */
  huffman(code: number, length: number): void {
    let rev = 0;
    for (let k = 0; k < length; k++) {
      rev = (rev << 1) | (code & 1);
      code >>>= 1;
    }
    this.put(rev, length);
  }

  finish(): number[] {
    if (this.n) this.out.push(this.acc & 0xFF);
    return this.out;
  }
}

function literal(bits: Bits, value: number): void {
  if (value < 144) bits.huffman(0x30 + value, 8);
  else if (value < 256) bits.huffman(0x190 + value - 144, 9);
  else if (value < 280) bits.huffman(value - 256, 7);
  else bits.huffman(0xC0 + value - 280, 8);
}

function match(bits: Bits, length: number, dist: number): void {
  let code = 0;
  while (code + 1 < LENGTH_BASE.length && LENGTH_BASE[code + 1] <= length) code += 1;
  literal(bits, 257 + code);
  bits.put(length - LENGTH_BASE[code], LENGTH_EXTRA[code]);
  let dcode = 0;
  while (dcode + 1 < DISTANCE_BASE.length && DISTANCE_BASE[dcode + 1] <= dist) dcode += 1;
  bits.huffman(dcode, 5);
  bits.put(dist - DISTANCE_BASE[dcode], DISTANCE_EXTRA[dcode]);
}

/** How many bytes from `i` repeat those `dist` before, up to MAX_MATCH. */
function common(data: Uint8Array, i: number, dist: number): number {
  const limit = Math.min(MAX_MATCH, data.length - i);
  let n = 0;
  while (n < limit && data[i + n] === data[i + n - dist]) n += 1;
  return n;
}

/** The declared compressor: one block of fixed Huffman codes, whose back-references are
 * to the byte `stride` before (the row above) or the byte before. */
export function deflate(data: Uint8Array, stride: number): number[] {
  const bits = new Bits();
  bits.put(1, 1); // the final block
  bits.put(1, 2); // fixed Huffman codes
  const useRow = 0 < stride && stride <= WINDOW;
  let i = 0;
  const n = data.length;
  while (i < n) {
    const up = useRow && i >= stride ? common(data, i, stride) : 0;
    const run = i >= 1 ? common(data, i, 1) : 0;
    if (up >= MIN_MATCH && up >= run) {
      match(bits, up, stride);
      i += up;
    } else if (run >= MIN_MATCH) {
      match(bits, run, 1);
      i += run;
    } else {
      literal(bits, data[i]);
      i += 1;
    }
  }
  literal(bits, 256);
  return bits.finish();
}

function u32(value: number): number[] {
  return [(value >>> 24) & 0xFF, (value >>> 16) & 0xFF, (value >>> 8) & 0xFF, value & 0xFF];
}

/** RFC 1950: the header for DEFLATE with a 32 KiB window and no dictionary, the block,
 * and the Adler-32 of the data. */
export function zlibStream(data: Uint8Array, stride: number): number[] {
  return [0x78, 0x01, ...deflate(data, stride), ...u32(adler32(data))];
}

function ascii(s: string): number[] {
  return Array.from(s, (ch) => ch.charCodeAt(0));
}

/** The text as Latin-1, as Python's `str.encode("latin-1")`, which refuses a character
 * beyond it. */
function latin1(s: string): number[] {
  return Array.from(s, (ch) => {
    const c = ch.codePointAt(0) ?? 0;
    if (c > 0xFF) throw new RangeError("a character beyond Latin-1: " + ch);
    return c;
  });
}

function chunk(kind: string, body: number[]): number[] {
  const typed = [...ascii(kind), ...body];
  return [...u32(body.length), ...typed, ...u32(crc32(Uint8Array.from(typed)))];
}

/** A greyscale PNG of `pixels`, rows of `width` bytes from the top, 0 black. */
export function encode(width: number, height: number, pixels: Uint8Array,
  description = ""): Uint8Array {
  const raw = new Uint8Array(height * (width + 1));
  for (let y = 0; y < height; y++) {
    raw[y * (width + 1)] = 0;
    raw.set(pixels.subarray(y * width, (y + 1) * width), y * (width + 1) + 1);
  }
  const out: number[] = [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A];
  out.push(...chunk("IHDR", [...u32(width), ...u32(height), 8, 0, 0, 0, 0]));
  if (description) {
    out.push(...chunk("tEXt", [...ascii("Description"), 0, ...latin1(description)]));
  }
  const idat = zlibStream(raw, width + 1);
  const parts = [Uint8Array.from(out), Uint8Array.from(chunk("IDAT", idat)),
    Uint8Array.from(chunk("IEND", []))];
  const bytes = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
  let at = 0;
  for (const p of parts) {
    bytes.set(p, at);
    at += p.length;
  }
  return bytes;
}
