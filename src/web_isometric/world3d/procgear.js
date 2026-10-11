// Weapons the art packs don't have, built in code in the KayKit low-poly style and painted
// from the same palette as everything else (equip.js merges them into the hero's mesh).
// Each shape is made in the frame of a KayKit sword: the hand holds the origin and the
// weapon runs along +Y. Plain arrays out, so tests/web can run the builders in Node.
//
// paint(role) gives a palette column's u for a role: 'wood', 'wood_dark', 'wood_pale',
// 'metal', 'metal_dark', 'leather', 'string', 'hole', 'gem'. The v coordinate is the shade
// within the ramp: faces looking up are light, faces looking down dark, as in the pack.

class Mesh {
  constructor(paint) { this.paint = paint; this.p = []; this.n = []; this.uv = []; this.i = []; }
  get count() { return this.p.length / 3; }
  vert(x, y, z, nx, ny, nz, role) {
    const l = Math.hypot(nx, ny, nz) || 1;
    nx /= l; ny /= l; nz /= l;
    this.p.push(x, y, z); this.n.push(nx, ny, nz);
    this.uv.push(this.paint(role), 0.16 + 0.56 * (1 - (ny + 1) / 2));
    return this.count - 1;
  }
  tri(a, b, c) { this.i.push(a, b, c); }
  // a flat-shaded quad (a, b, c, d counter-clockwise seen from outside)
  quad(a, b, c, d, role) {
    const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2], vx = d[0] - a[0], vy = d[1] - a[1], vz = d[2] - a[2];
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    const k = [a, b, c, d].map(q => this.vert(q[0], q[1], q[2], nx, ny, nz, role));
    this.tri(k[0], k[1], k[2]); this.tri(k[0], k[2], k[3]);
  }
  box(cx, cy, cz, sx, sy, sz, role) {
    const x0 = cx - sx / 2, x1 = cx + sx / 2, y0 = cy - sy / 2, y1 = cy + sy / 2, z0 = cz - sz / 2, z1 = cz + sz / 2;
    this.quad([x0, y1, z0], [x0, y1, z1], [x1, y1, z1], [x1, y1, z0], role);     // top
    this.quad([x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1], role);     // bottom
    this.quad([x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1], role);     // +z
    this.quad([x1, y0, z0], [x0, y0, z0], [x0, y1, z0], [x1, y1, z0], role);     // -z
    this.quad([x1, y0, z1], [x1, y0, z0], [x1, y1, z0], [x1, y1, z1], role);     // +x
    this.quad([x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0], role);     // -x
  }
  // a smooth tube through points [[x,y,z,r], ...], `seg` sides, capped
  tube(pts, seg, role) {
    const rings = [];
    for (let k = 0; k < pts.length; k++) {
      const [x, y, z, r] = pts[k];
      const a = pts[Math.max(0, k - 1)], b = pts[Math.min(pts.length - 1, k + 1)];
      let tx = b[0] - a[0], ty = b[1] - a[1], tz = b[2] - a[2];
      const tl = Math.hypot(tx, ty, tz) || 1; tx /= tl; ty /= tl; tz /= tl;
      // a frame around the tangent
      let ux = 0, uy = 0, uz = 1;
      if (Math.abs(tz) > 0.9) { ux = 1; uz = 0; }
      let bx = ty * uz - tz * uy, by = tz * ux - tx * uz, bz = tx * uy - ty * ux;
      const bl = Math.hypot(bx, by, bz) || 1; bx /= bl; by /= bl; bz /= bl;
      const nx2 = by * tz - bz * ty, ny2 = bz * tx - bx * tz, nz2 = bx * ty - by * tx;
      const ring = [];
      for (let s = 0; s < seg; s++) {
        const t = s / seg * Math.PI * 2, c = Math.cos(t), si = Math.sin(t);
        const nx = bx * c + nx2 * si, ny = by * c + ny2 * si, nz = bz * c + nz2 * si;
        ring.push(this.vert(x + nx * r, y + ny * r, z + nz * r, nx, ny, nz, role));
      }
      rings.push(ring);
    }
    for (let k = 0; k + 1 < rings.length; k++) {
      for (let s = 0; s < seg; s++) {
        const a = rings[k][s], b = rings[k][(s + 1) % seg], c = rings[k + 1][(s + 1) % seg], d = rings[k + 1][s];
        this.tri(a, b, c); this.tri(a, c, d);
      }
    }
    // caps
    for (const [k, dir] of [[0, -1], [rings.length - 1, 1]]) {
      const [x, y, z] = pts[k];
      const nb = pts[k + (dir < 0 ? 1 : -1)] || pts[k];
      const cn = [x - nb[0], y - nb[1], z - nb[2]].map(v => v * dir * -1);
      const centre = this.vert(x, y, z, cn[0] || 0, cn[1] || 1, cn[2] || 0, role);
      for (let s = 0; s < seg; s++) {
        const a = rings[k][s], b = rings[k][(s + 1) % seg];
        if (dir > 0) this.tri(centre, a, b); else this.tri(centre, b, a);
      }
    }
  }
  // a low-poly ball (an octahedron split once), flat-shaded
  ball(cx, cy, cz, rx, ry, rz, role) {
    const V = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]];
    const F = [[2, 4, 0], [2, 0, 5], [2, 5, 1], [2, 1, 4], [3, 0, 4], [3, 5, 0], [3, 1, 5], [3, 4, 1]];
    const mid = (a, b) => { const m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2]; const l = Math.hypot(...m); return m.map(v => v / l); };
    const put = v => [cx + v[0] * rx, cy + v[1] * ry, cz + v[2] * rz];
    for (const [i, j, k] of F) {
      const a = V[i], b = V[j], c = V[k], ab = mid(a, b), bc = mid(b, c), ca = mid(c, a);
      for (const t of [[a, ab, ca], [ab, b, bc], [ca, bc, c], [ab, bc, ca]]) {
        const [p, q, r] = t.map(put);
        const ux = q[0] - p[0], uy = q[1] - p[1], uz = q[2] - p[2], vx = r[0] - p[0], vy = r[1] - p[1], vz = r[2] - p[2];
        const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
        const k0 = this.vert(...p, nx, ny, nz, role), k1 = this.vert(...q, nx, ny, nz, role), k2 = this.vert(...r, nx, ny, nz, role);
        this.tri(k0, k1, k2);
      }
    }
  }
  done() {
    return { position: new Float32Array(this.p), normal: new Float32Array(this.n), uv: new Float32Array(this.uv),
      index: this.count > 65535 ? new Uint32Array(this.i) : new Uint16Array(this.i) };
  }
}

// a longbow: two curved limbs, a leather grip, a string
function bow(m, look) {
  // chunky, as the pack's weapons are: a thick riser, limbs that thin and curl at the tips
  const H = 0.95, BEND = 0.26;
  const limb = [];
  for (let k = 0; k <= 12; k++) {
    const t = k / 12 * 2 - 1;                       // -1 .. 1 along the bow
    const y = t * H;
    const z = -BEND * t * t + 0.05 * Math.sign(t) * Math.max(0, Math.abs(t) - 0.85) * 6;   // recurved tips
    const r = 0.07 - 0.04 * Math.abs(t);
    limb.push([0, y, z, r]);
  }
  m.tube(limb, 7, 'wood');
  m.tube([[0, -0.16, 0.004, 0.08], [0, 0.16, 0.004, 0.08]], 7, 'leather');         // the grip
  m.tube([[0, -H, -BEND + 0.03, 0.012], [0, H, -BEND + 0.03, 0.012]], 4, 'string');
  for (const s of [-1, 1]) m.ball(0, s * H, -BEND + 0.02, 0.045, 0.06, 0.045, look && look.m2 ? 'metal' : 'wood_dark');   // nocks
  return m.done();
}

// a mace: a wooden haft, a metal head with flanges, a pommel
function mace(m, look) {
  m.tube([[0, -0.32, 0, 0.036], [0, 0.55, 0, 0.034]], 6, 'wood');
  m.tube([[0, -0.2, 0, 0.042], [0, 0.08, 0, 0.042]], 6, 'leather');                // the grip
  m.ball(0, -0.36, 0, 0.055, 0.05, 0.055, 'metal');                                   // pommel
  m.ball(0, 0.68, 0, 0.15, 0.17, 0.15, 'metal');                                      // head
  for (let k = 0; k < 6; k++) {                                                       // flanges
    const a = k / 6 * Math.PI * 2;
    const x = Math.cos(a) * 0.15, z = Math.sin(a) * 0.15;
    m.box(x, 0.68, z, Math.abs(Math.cos(a)) * 0.1 + 0.03, 0.26, Math.abs(Math.sin(a)) * 0.1 + 0.03, 'metal_dark');
  }
  m.ball(0, 0.86, 0, 0.05, 0.06, 0.05, 'metal');                                      // the cap
  return m.done();
}

// a lute: a round-backed body hanging below the hand, the neck in the hand, a bent pegbox
function lute(m, look) {
  m.ball(0, -0.42, 0, 0.3, 0.4, 0.14, 'wood');                                        // the bowl
  m.box(0, -0.42, 0.085, 0.42, 0.56, 0.04, 'wood_pale');                              // the soundboard
  m.tube([[0, -0.4, 0.106, 0.075], [0, -0.4, 0.112, 0.075]], 8, 'hole');              // the rose
  m.box(0, 0.12, 0.05, 0.1, 0.62, 0.06, 'wood_dark');                                 // the neck
  m.box(0, 0.5, 0.0, 0.11, 0.18, 0.05, 'wood_dark');                                  // the pegbox
  for (const s of [-1, 1]) for (let k = 0; k < 3; k++) m.box(s * 0.075, 0.45 + k * 0.05, 0, 0.05, 0.02, 0.02, 'wood');
  for (const x of [-0.03, -0.01, 0.01, 0.03]) m.box(x, -0.12, 0.112, 0.006, 1.0, 0.006, 'string');
  return m.done();
}

export const SHAPES = { bow, mace, lute };

// build a shape: { position, normal, uv, index }
export function buildProc(shape, look, paint) {
  const fn = SHAPES[shape];
  if (!fn) return null;
  return fn(new Mesh(paint), look || {});
}
