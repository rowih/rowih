// The rasterisation of a drawing for the PNG output
// (specification/writing-system.md#the-renderings), the canonical implementation's
// `raster` step for step: every segment of every path is a stroke of the drawing's width
// with round ends; a pixel's ink is how far its centre lies within half the width of the
// segment, plus half a pixel, held between 0 and 1, and a pixel takes the most ink any
// segment gives it. The arithmetic is IEEE double precision in the same order as the
// Python, so that the two write the same bytes. Embedded material is drawn as the outline
// of the space it takes, since the image carries no font.

import { type Drawing } from "./drawing.ts";

const WHITE = 255;

/** The ink of a segment from (0, 0) to (vx, vy) in pixels, as dx, dy, grey for each
 * pixel it touches, the pixel at dx, dy having its centre at (dx + 0.5, dy + 0.5). */
function tile(vx: number, vy: number, radius: number): number[] {
  const reach = Math.ceil(radius) + 1;
  const length2 = vx * vx + vy * vy;
  const out: number[] = [];
  for (let dy = Math.min(0, vy) - reach; dy < Math.max(0, vy) + reach; dy++) {
    for (let dx = Math.min(0, vx) - reach; dx < Math.max(0, vx) + reach; dx++) {
      const wx = dx + 0.5;
      const wy = dy + 0.5;
      let t = 0.0;
      if (length2 > 0) {
        t = (wx * vx + wy * vy) / length2;
        if (t < 0.0) t = 0.0;
        else if (t > 1.0) t = 1.0;
      }
      const ex = wx - t * vx;
      const ey = wy - t * vy;
      let ink = radius + 0.5 - Math.sqrt(ex * ex + ey * ey);
      if (ink <= 0.0) continue;
      if (ink > 1.0) ink = 1.0;
      out.push(dx, dy, WHITE - Math.floor(255.0 * ink + 0.5));
    }
  }
  return out;
}

/** The drawing as width, height and greys, rows from the top. */
export function rasterise(drawing: Drawing, pixelsPerUnit: number): [number, number, Uint8Array] {
  const s = pixelsPerUnit;
  const width = drawing.width * s;
  const height = drawing.height * s;
  const greys = new Uint8Array(width * height).fill(WHITE);
  const tiles = new Map<string, number[]>();
  const radii = { stroke: drawing.stroke * s / 2, hairline: drawing.hairline * s / 2 };

  function segment(ax: number, ay: number, bx: number, by: number, radius: number): void {
    const key = (bx - ax) + "," + (by - ay) + "," + radius;
    let ink = tiles.get(key);
    if (ink === undefined) {
      ink = tile(bx - ax, by - ay, radius);
      tiles.set(key, ink);
    }
    for (let k = 0; k < ink.length; k += 3) {
      const x = ax + ink[k];
      const y = ay + ink[k + 1];
      if (0 <= x && x < width && 0 <= y && y < height) {
        const i = y * width + x;
        if (ink[k + 2] < greys[i]) greys[i] = ink[k + 2];
      }
    }
  }

  for (const path of drawing.paths) {
    const r = radii[path.weight];
    for (let k = 0; k + 1 < path.points.length; k++) {
      const [ax, ay] = path.points[k];
      const [bx, by] = path.points[k + 1];
      segment(ax * s, ay * s, bx * s, by * s, r);
    }
  }
  for (const t of drawing.texts) {
    const x0 = t.x * s;
    const x1 = (t.x + t.width) * s;
    const y0 = (t.y - t.size) * s;
    const y1 = t.y * s;
    const r = radii.hairline;
    segment(x0, y0, x1, y0, r);
    segment(x1, y0, x1, y1, r);
    segment(x1, y1, x0, y1, r);
    segment(x0, y1, x0, y0, r);
  }
  return [width, height, greys];
}
