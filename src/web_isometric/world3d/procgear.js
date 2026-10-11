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
    // (each ring turns clockwise about the tube's direction: wound so the faces look out)
    for (let k = 0; k + 1 < rings.length; k++) {
      for (let s = 0; s < seg; s++) {
        const a = rings[k][s], b = rings[k][(s + 1) % seg], c = rings[k + 1][(s + 1) % seg], d = rings[k + 1][s];
        this.tri(a, c, b); this.tri(a, d, c);
      }
    }
    // caps, facing out of each end
    for (const [k, dir] of [[0, -1], [rings.length - 1, 1]]) {
      const [x, y, z] = pts[k];
      const nb = pts[k + (dir < 0 ? 1 : -1)] || pts[k];
      const cn = [x - nb[0], y - nb[1], z - nb[2]];
      const centre = this.vert(x, y, z, cn[0] || 0, cn[1] || 1, cn[2] || 0, role);
      for (let s = 0; s < seg; s++) {
        const a = rings[k][s], b = rings[k][(s + 1) % seg];
        if (dir > 0) this.tri(centre, b, a); else this.tri(centre, a, b);
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

// ---- the rest of the armoury ----
// a war hammer (a maul with two hands): a square head with a spike behind
function hammer(m, look) {
  const big = (look.h || 1) === 2, top = big ? 1.0 : 0.6;
  m.tube([[0, big ? -0.55 : -0.3, 0, 0.038], [0, top, 0, 0.036]], 6, 'wood');
  m.tube([[0, -0.2, 0, 0.044], [0, 0.08, 0, 0.044]], 6, 'leather');
  m.box(0, top + 0.06, 0, big ? 0.5 : 0.34, big ? 0.28 : 0.2, big ? 0.28 : 0.2, 'metal');
  m.box(0, top + 0.06, 0, big ? 0.54 : 0.37, 0.05, big ? 0.3 : 0.22, 'metal_dark');      // a band round the head
  m.tube([[-0.12, top + 0.06, 0, 0.05], [-(big ? 0.42 : 0.3), top + 0.1, 0, 0.004]], 5, 'metal_dark');
  return m.done();
}
// a spear: a long ash shaft, a leaf blade, a butt cap
function spear(m) {
  m.tube([[0, -0.85, 0, 0.034], [0, 1.3, 0, 0.032]], 6, 'wood');
  m.tube([[0, -0.15, 0, 0.04], [0, 0.15, 0, 0.04]], 6, 'leather');
  m.tube([[0, 1.28, 0, 0.05], [0, 1.4, 0, 0.09], [0, 1.6, 0, 0.06], [0, 1.78, 0, 0.004]], 4, 'metal');
  m.ball(0, -0.88, 0, 0.045, 0.05, 0.045, 'metal_dark');
  return m.done();
}
// a polearm: a halberd's axe blade and spike on a long shaft
function polearm(m) {
  m.tube([[0, -0.85, 0, 0.034], [0, 1.45, 0, 0.032]], 6, 'wood');
  m.tube([[0, -0.15, 0, 0.04], [0, 0.15, 0, 0.04]], 6, 'leather');
  m.quad([0.03, 1.05, -0.02], [0.36, 0.98, -0.02], [0.4, 1.42, -0.02], [0.03, 1.34, -0.02], 'metal');
  m.quad([0.03, 1.34, 0.02], [0.4, 1.42, 0.02], [0.36, 0.98, 0.02], [0.03, 1.05, 0.02], 'metal');
  m.box(0.22, 1.2, 0, 0.36, 0.03, 0.05, 'metal_dark');
  m.tube([[0, 1.42, 0, 0.04], [0, 1.75, 0, 0.004]], 4, 'metal');                         // the spike
  m.tube([[-0.03, 1.2, 0, 0.03], [-0.22, 1.32, 0, 0.004]], 4, 'metal');                  // the back hook
  return m.done();
}
// a scythe: a bent snath and a long curved blade
function scythe(m) {
  m.tube([[0, -0.6, 0, 0.034], [0.02, 0.3, 0, 0.033], [0, 1.3, 0, 0.032]], 6, 'wood');
  m.tube([[0.05, 0.25, 0, 0.03], [0.22, 0.28, 0, 0.026]], 5, 'wood');                  // the grip peg
  const blade = [];
  for (let k = 0; k <= 8; k++) { const t = k / 8; blade.push([0.04 + t * 0.85, 1.3 - t * t * 0.3, 0, 0.05 * (1 - t) + 0.006]); }
  m.tube(blade, 3, 'metal');
  return m.done();
}
// a pick: a short haft, a curved head pointed both ways
function pick(m) {
  m.tube([[0, -0.3, 0, 0.036], [0, 0.62, 0, 0.034]], 6, 'wood');
  m.tube([[-0.42, 0.52, 0, 0.004], [-0.2, 0.62, 0, 0.04], [0, 0.66, 0, 0.055], [0.2, 0.62, 0, 0.04], [0.42, 0.52, 0, 0.004]], 5, 'metal');
  return m.done();
}
// a whip: a wrapped handle and a lash that hangs in a curl
function whip(m) {
  m.tube([[0, -0.15, 0, 0.034], [0, 0.18, 0, 0.03]], 6, 'leather');
  const lash = [];
  for (let k = 0; k <= 14; k++) { const t = k / 14; lash.push([Math.sin(t * 5) * 0.12 * t, 0.18 + t * 0.95, Math.cos(t * 4) * 0.1 * t - 0.1 * t, 0.022 * (1 - t) + 0.006]); }
  m.tube(lash, 4, 'leather');
  return m.done();
}
// claws over the knuckles: three hooked blades
function claw(m) {
  m.box(0, 0.02, 0, 0.2, 0.08, 0.1, 'leather');
  for (const x of [-0.065, 0, 0.065]) m.tube([[x, 0.05, 0, 0.022], [x, 0.3, 0.03, 0.014], [x, 0.46, 0.1, 0.003]], 4, 'metal');
  return m.done();
}
// instruments held in the off hand
function lyre(m) {
  m.box(0, -0.42, 0, 0.32, 0.12, 0.08, 'wood');                                         // the soundbox
  for (const s of [-1, 1]) m.tube([[s * 0.12, -0.38, 0, 0.03], [s * 0.2, -0.1, 0, 0.032], [s * 0.15, 0.08, 0, 0.03], [s * 0.2, 0.18, 0, 0.026]], 5, 'wood_dark');
  m.tube([[-0.19, 0.1, 0, 0.022], [0.19, 0.1, 0, 0.022]], 5, 'wood_dark');               // the yoke
  for (const x of [-0.06, -0.02, 0.02, 0.06]) m.box(x, -0.15, 0.03, 0.006, 0.5, 0.006, 'string');
  return m.done();
}
function harp(m) {
  m.tube([[-0.15, -0.55, 0, 0.04], [-0.15, 0.3, 0, 0.04]], 6, 'wood');                  // the pillar
  m.tube([[-0.15, 0.3, 0, 0.035], [0.05, 0.36, 0, 0.035], [0.25, 0.2, 0, 0.035]], 6, 'wood_dark');   // the neck
  m.box(0.08, -0.2, 0, 0.12, 0.8, 0.1, 'wood_pale');                                    // the soundbox
  for (let k = 0; k < 6; k++) { const x = -0.12 + k * 0.05; m.box(x, -0.05 - k * 0.03, 0.02, 0.005, 0.6 - k * 0.06, 0.005, 'string'); }
  return m.done();
}
function flute(m) {
  m.tube([[0, -0.15, 0, 0.026], [0, 0.6, 0, 0.026]], 6, 'wood_pale');
  for (let k = 0; k < 5; k++) m.ball(0, 0.15 + k * 0.08, 0.024, 0.012, 0.012, 0.006, 'hole');
  m.tube([[0, 0.6, 0, 0.03], [0, 0.64, 0, 0.03]], 6, 'metal');
  return m.done();
}
function drum(m) {
  m.tube([[0, -0.5, 0, 0.2], [0, -0.22, 0, 0.2]], 10, 'wood_pale');
  for (const y of [-0.5, -0.22]) m.tube([[0, y - 0.012, 0, 0.215], [0, y + 0.012, 0, 0.215]], 10, 'wood_dark');
  m.tube([[0, -0.21, 0, 0.012], [0, 0.02, 0, 0.012]], 4, 'leather');                   // the strap
  return m.done();
}
function horn(m) {
  const pts = [];
  for (let k = 0; k <= 10; k++) { const t = k / 10; pts.push([Math.sin(t * 2.2) * 0.22, -0.3 + t * 0.55, Math.cos(t * 2.2) * 0.12 - 0.12, 0.018 + t * t * 0.09]); }
  m.tube(pts, 7, 'bone');
  for (const t of [0.35, 0.7]) m.ball(Math.sin(t * 2.2) * 0.22, -0.3 + t * 0.55, Math.cos(t * 2.2) * 0.12 - 0.12, 0.05 + t * 0.06, 0.02, 0.05 + t * 0.06, 'metal');
  return m.done();
}
// held light and focus: an orb in a cradle, a swinging censer, a lantern, a torch
function orb(m) {
  m.ball(0, 0.16, 0, 0.14, 0.14, 0.14, 'gem');
  for (let k = 0; k < 3; k++) { const a = k / 3 * Math.PI * 2; m.tube([[0, -0.02, 0, 0.02], [Math.cos(a) * 0.11, 0.1, Math.sin(a) * 0.11, 0.014]], 4, 'metal'); }
  return m.done();
}
function censer(m) {
  m.tube([[0, 0.0, 0, 0.008], [0, -0.42, 0, 0.008]], 3, 'metal_dark');
  m.ball(0, -0.52, 0, 0.12, 0.11, 0.12, 'metal');
  m.tube([[0, -0.52, 0, 0.125], [0, -0.5, 0, 0.125]], 8, 'hole');
  m.ball(0, -0.4, 0, 0.04, 0.03, 0.04, 'metal');
  return m.done();
}
function lantern(m) {
  m.tube([[0, 0.0, 0, 0.012], [0, -0.16, 0, 0.012]], 4, 'metal_dark');
  m.box(0, -0.2, 0, 0.18, 0.04, 0.18, 'metal_dark');
  m.box(0, -0.36, 0, 0.14, 0.26, 0.14, 'gem');                                         // the light
  for (const [x, z] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) m.box(x * 0.08, -0.36, z * 0.08, 0.025, 0.28, 0.025, 'metal_dark');
  m.box(0, -0.51, 0, 0.18, 0.04, 0.18, 'metal_dark');
  return m.done();
}
function torch(m) {
  m.tube([[0, -0.35, 0, 0.032], [0, 0.42, 0, 0.042]], 6, 'wood');
  m.tube([[0, 0.38, 0, 0.055], [0, 0.48, 0, 0.055]], 6, 'leather');
  m.ball(0, 0.58, 0, 0.09, 0.15, 0.09, 'gem');                                         // the flame
  return m.done();
}

export const SHAPES = { bow, mace, lute, hammer, spear, polearm, scythe, pick, whip, claw, lyre, harp, flute, drum, horn, orb, censer, lantern, torch };

// ---- add-ons: small pieces that make finer gear finer ----
// Each is built in the frame of the piece it sits on (equip.js passes where: a point and sizes
// worked out from that piece's own bounds), so it lands right on any body.

// a gem: an octahedron (a pommel stone, a shield's centre, a crown's jewel)
function gem(m, at) {
  const [x, y, z] = at.p, r = at.r || 0.05;
  m.ball(x, y, z, r, r * 1.3, r, 'gem');
  return m.done();
}
// a shield boss: a domed metal centre, facing +z
function boss(m, at) {
  const [x, y, z] = at.p, r = at.r || 0.12;
  m.ball(x, y, z, r, r, r * 0.55, 'metal');
  m.ball(x, y, z + r * 0.5, r * 0.35, r * 0.35, r * 0.25, 'gem');
  return m.done();
}
// a crest along the top of a helm, front to back (a plume in the class's colour)
function crest(m, at) {
  const [x, y, z] = at.p, l = at.r || 0.3;
  const pts = [];
  for (let k = 0; k <= 8; k++) { const t = k / 8; pts.push([x, y + Math.sin(t * Math.PI) * l * 0.5, z + (t - 0.5) * l * 2, 0.085 * Math.sin(t * Math.PI) + 0.03]); }
  m.tube(pts, 6, 'cloth');
  return m.done();
}
// a pauldron on a shoulder (in the rig's frame: the arm runs along x)
function pauldron(m, at) {
  const [x, y, z] = at.p, r = at.r || 0.16, s = at.side || 1;
  m.ball(x, y, z, r * 1.25, r * 0.7, r * 1.15, 'metal');
  m.ball(x + s * r * 0.55, y - r * 0.15, z, r * 0.8, r * 0.45, r * 0.95, 'metal_dark');
  if (at.spikes) for (const dz of [-0.4, 0.4]) m.tube([[x + s * r * 0.2, y + r * 0.45, z + dz * r, 0.04], [x + s * r * 0.5, y + r * 1.3, z + dz * r, 0.003]], 4, 'metal_dark');
  return m.done();
}
// a crown or a circlet round the top of the head
function crown(m, at) {
  const [x, y, z] = at.p, r = at.r || 0.42, rz = at.rz || r * 0.92, circlet = at.variant === 'circlet';
  const ring = [];
  for (let k = 0; k <= 16; k++) { const a = k / 16 * Math.PI * 2; ring.push([x + Math.cos(a) * r, y, z + Math.sin(a) * rz, circlet ? 0.025 : 0.045]); }
  m.tube(ring, 5, 'metal');
  if (!circlet) for (let k = 0; k < 8; k++) {
    const a = k / 8 * Math.PI * 2;
    m.tube([[x + Math.cos(a) * r, y, z + Math.sin(a) * rz, 0.05], [x + Math.cos(a) * r * 1.02, y + 0.16, z + Math.sin(a) * rz * 1.02, 0.004]], 4, 'metal');
  }
  m.ball(x, y + (circlet ? 0 : 0.03), z + rz + 0.01, 0.045, 0.06, 0.03, 'gem');
  return m.done();
}

// a class's emblem, flat on the back of its cloak (shared/items.js CLASS_SIG motifs)
const star = (n, r0, r1) => Array.from({ length: n * 2 }, (_, k) => { const a = k / (n * 2) * Math.PI * 2 + Math.PI / 2; const r = k % 2 ? r1 : r0; return [Math.cos(a) * r, Math.sin(a) * r]; });
const lens = (w, h) => [...Array.from({ length: 8 }, (_, k) => { const a = Math.PI * k / 7; return [-Math.cos(a) * w, Math.sin(a) * h]; }), ...Array.from({ length: 6 }, (_, k) => { const a = Math.PI * (k + 1) / 7; return [Math.cos(a) * w, -Math.sin(a) * h]; })];
export const MOTIFS = {
  warrior: [[-1, 0.7], [-1, 0.15], [0, -0.75], [1, 0.15], [1, 0.7], [0, -0.2]],                       // chevron
  paladin: star(8, 1, 0.55),                                                                         // sunburst
  mage: lens(1, 0.6),                                                                                // an eye
  necromancer: [[-0.7, 0.9], [0.7, 0.9], [0.9, 0.2], [0.45, -0.25], [0.45, -0.9], [-0.45, -0.9], [-0.45, -0.25], [-0.9, 0.2]],   // a skull
  thief: [[0, -0.9], [0.95, 0.4], [0.6, 0.85], [0, 0.95], [-0.6, 0.85], [-0.95, 0.4]],              // a fan
  assassin: [[0, 1], [0.55, -0.15], [0.45, -0.6], [0, -0.9], [-0.45, -0.6], [-0.55, -0.15]],        // a drop
  ranger: [[0, 1], [0.5, 0.35], [0.45, -0.3], [0, -1], [-0.45, -0.3], [-0.5, 0.35]],                // a leaf
  cleric: [[-0.3, 1], [0.3, 1], [0.3, 0.3], [1, 0.3], [1, -0.3], [0.3, -0.3], [0.3, -1], [-0.3, -1], [-0.3, -0.3], [-1, -0.3], [-1, 0.3], [-0.3, 0.3]],   // a cross
  bard: [[-0.8, 1], [-0.5, 1], [-0.45, -0.2], [0.45, -0.2], [0.5, 1], [0.8, 1], [0.7, -0.6], [0, -0.95], [-0.7, -0.6]],   // a lyre
};
// ear clipping, for the concave ones
function triangulate(poly) {
  const idx = poly.map((_, i) => i), out = [];
  const area = poly.reduce((a, p, i) => { const q = poly[(i + 1) % poly.length]; return a + p[0] * q[1] - q[0] * p[1]; }, 0);
  const ccw = area > 0;
  const inside = (p, a, b, c) => {
    const d = (u, v, w) => (u[0] - w[0]) * (v[1] - w[1]) - (v[0] - w[0]) * (u[1] - w[1]);
    const d1 = d(p, a, b), d2 = d(p, b, c), d3 = d(p, c, a);
    return !((d1 < 0 || d2 < 0 || d3 < 0) && (d1 > 0 || d2 > 0 || d3 > 0));
  };
  let guard = 0;
  while (idx.length > 3 && guard++ < 500) {
    let cut = false;
    for (let i = 0; i < idx.length; i++) {
      const ia = idx[(i + idx.length - 1) % idx.length], ib = idx[i], ic = idx[(i + 1) % idx.length];
      const a = poly[ia], b = poly[ib], c = poly[ic];
      const cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
      if ((cross > 0) !== ccw) continue;
      if (idx.some(j => j !== ia && j !== ib && j !== ic && inside(poly[j], a, b, c))) continue;
      out.push(ccw ? [ia, ib, ic] : [ia, ic, ib]);
      idx.splice(i, 1);
      cut = true;
      break;
    }
    if (!cut) break;
  }
  if (idx.length === 3) out.push(ccw ? [idx[0], idx[1], idx[2]] : [idx[0], idx[2], idx[1]]);
  return out;
}
function emblem(m, at) {
  const poly = MOTIFS[at.motif] || MOTIFS.paladin, s = at.r || 0.14, [x, y, z] = at.p, d = 0.025, lean = at.lean || 0;
  const tris = triangulate(poly);
  // the face looks out of the cloak's back (-z), a thin rim round it; it leans as the cloth does
  const zOf = py => z + py * s * lean;
  const face = (dz, nz) => poly.map(([px, py]) => m.vert(x + px * s, y + py * s, zOf(py) + dz, 0, lean * -nz, nz, 'gold'));
  const back = face(0, 1), front = face(-d, -1);
  for (const [a, b, c] of tris) { m.tri(front[a], front[c], front[b]); m.tri(back[a], back[b], back[c]); }
  for (let i = 0; i < poly.length; i++) {
    const p = poly[i], q = poly[(i + 1) % poly.length];
    m.quad([x + p[0] * s, y + p[1] * s, zOf(p[1]) - d], [x + q[0] * s, y + q[1] * s, zOf(q[1]) - d], [x + q[0] * s, y + q[1] * s, zOf(q[1])], [x + p[0] * s, y + p[1] * s, zOf(p[1])], 'gold');
  }
  return m.done();
}

export const ADDONS = { gem, boss, crest, pauldron, crown, emblem };

// turned over along y (a lantern made to hang from a hip, carried in a hand instead)
function flipY(a) {
  for (let i = 1; i < a.position.length; i += 3) { a.position[i] = -a.position[i]; a.normal[i] = -a.normal[i]; }
  for (let i = 0; i < a.uv.length / 2; i++) a.uv[i * 2 + 1] = 0.16 + 0.56 * (1 - (a.normal[i * 3 + 1] + 1) / 2);
  for (let i = 0; i < a.index.length; i += 3) { const t = a.index[i + 1]; a.index[i + 1] = a.index[i + 2]; a.index[i + 2] = t; }
  return a;
}
// what hangs from where it is held: carried in a hand, it hangs out along the hand's +y
export const HANGING = new Set(['lantern', 'censer', 'drum']);

// build a shape or an add-on: { position, normal, uv, index }
export function buildProc(shape, look, paint, { flip = false } = {}) {
  const fn = SHAPES[shape];
  if (!fn) return null;
  const a = fn(new Mesh(paint), look || {});
  return flip ? flipY(a) : a;
}
export function buildAddon(kind, at, paint) {
  const fn = ADDONS[kind];
  if (!fn) return null;
  return fn(new Mesh(paint), at || {});
}
