// The PNG writer's checksums and compressor, checked against the definitions they follow
// and against Node's zlib, which inflates whatever the declared compressor writes.

import assert from "node:assert/strict";
import { test } from "node:test";
import { crc32 as zlibCrc32, inflateSync } from "node:zlib";

import { adler32, crc32, encode, zlibStream } from "../src/png.ts";

const bytes = (s: string): Uint8Array => new TextEncoder().encode(s);

test("the CRC is that of ISO/IEC 15948 Annex D", () => {
  // the CRC every PNG ends with, over "IEND" and no data
  assert.equal(crc32(bytes("IEND")), 0xAE426082);
  assert.equal(crc32(bytes("123456789")), 0xCBF43926);
});

test("the Adler-32 is that of RFC 1950", () => {
  assert.equal(adler32(bytes("Wikipedia")), 0x11E60398);
  // past the 5552-byte block at which the sums are reduced
  const long = new Uint8Array(20000).fill(255);
  let a = 1;
  let b = 0;
  for (const x of long) {
    a = (a + x) % 65521;
    b = (b + a) % 65521;
  }
  assert.equal(adler32(long), b * 65536 + a);
});

test("zlib inflates what the declared compressor writes", () => {
  const cases: [Uint8Array, number][] = [
    [new Uint8Array(0), 1],
    [bytes("abcabcabcabcabcabcabc"), 3],
    [new Uint8Array(1000).fill(255), 100],
    [Uint8Array.from({ length: 70000 }, (_, i) => (i * 7919) % 251), 300],
    [Uint8Array.from({ length: 5000 }, (_, i) => (i % 50 < 3 ? 0 : 255)), 50],
  ];
  for (const [data, stride] of cases) {
    assert.deepEqual(new Uint8Array(inflateSync(Uint8Array.from(zlibStream(data, stride)))), data);
  }
});

test("each chunk of an encoded image carries the right CRC", () => {
  const png = encode(3, 2, Uint8Array.from([0, 128, 255, 255, 128, 0]), "wila");
  assert.deepEqual([...png.subarray(0, 8)], [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);
  const view = new DataView(png.buffer, png.byteOffset, png.byteLength);
  const kinds: string[] = [];
  for (let at = 8; at < png.length;) {
    const length = view.getUint32(at);
    const typed = png.subarray(at + 4, at + 8 + length);
    kinds.push(new TextDecoder().decode(typed.subarray(0, 4)));
    assert.equal(view.getUint32(at + 8 + length), zlibCrc32(typed));
    at += 12 + length;
  }
  assert.deepEqual(kinds, ["IHDR", "tEXt", "IDAT", "IEND"]);
});
