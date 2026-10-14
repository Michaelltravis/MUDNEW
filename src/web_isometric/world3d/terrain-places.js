// The open places an old import typed 'city' that are no town (room_looks.py TOWNLESS, Phase 2 of
// docs/world/room_visuals.md): a village of huts, a camp of tents and stakes, a garden of hedges and
// flower beds, the ruins of a city. Each is open country (terrain.js's outdoor branch) with its own
// edge (outdoorEdge: what stands in the border, what lines the open ground) and its own scatter on
// the open ground (dressPlace). The shapes are built here in the kits' chunky low-poly style.
import * as THREE from 'three';
import { trs } from './assets.js';

const cache = new Map();
function made(name, build) {
  let m = cache.get(name);
  if (!m) {
    const parts = build();
    const box = new THREE.Box3();
    for (const p of parts) { p.geometry.computeBoundingBox(); box.union(p.geometry.boundingBox); }
    m = { name: `place_${name}`, box, parts };
    cache.set(name, m);
  }
  return m;
}
const mats = new Map();
function mat(color, opts = {}) {
  const key = `${color}|${JSON.stringify(opts)}`;
  let m = mats.get(key);
  if (!m) { m = new THREE.MeshStandardMaterial({ color, roughness: 0.92, metalness: 0, flatShading: true, ...opts }); mats.set(key, m); }
  return m;
}
// a deterministic roughening, so a wall is broken but the same every time
function rough(geo, seed, amt) {
  const p = geo.attributes.position;
  let s = seed * 9301 + 49297;
  const rnd = () => { s = (s * 9301 + 49297) % 233280; return s / 233280 - 0.5; };
  const seen = new Map();
  for (let i = 0; i < p.count; i++) {
    const k = `${p.getX(i).toFixed(3)},${p.getY(i).toFixed(3)},${p.getZ(i).toFixed(3)}`;
    let d = seen.get(k);
    if (!d) { d = [rnd() * amt, rnd() * amt * 0.6, rnd() * amt]; seen.set(k, d); }
    p.setXYZ(i, p.getX(i) + d[0], p.getY(i) + d[1], p.getZ(i) + d[2]);
  }
  geo.computeVertexNormals();
  return geo;
}

// ---- a village: round huts of wattle or mud under thatch, a door facing out ----
const WALLS = [0x8a6a48, 0x9c8462, 0x6f5a44];
const THATCH = [0xb89a5a, 0xa48850, 0x8f7a4a];
export function hut(v) {
  return made(`hut${v}`, () => {
    const r = 1.45 + v * 0.15;
    const wall = rough(new THREE.CylinderGeometry(r, r * 1.04, 1.5, 9, 2, true), 31 + v, 0.06).translate(0, 0.75, 0);
    const roof = rough(new THREE.ConeGeometry(r * 1.32, 1.8 + v * 0.2, 9, 2), 41 + v, 0.09).translate(0, 1.5 + (1.8 + v * 0.2) / 2 - 0.05, 0);
    const door = new THREE.BoxGeometry(0.6, 1.05, 0.12).translate(0, 0.53, r - 0.02);
    const floor = new THREE.CircleGeometry(r, 9).rotateX(-Math.PI / 2).translate(0, 0.02, 0);
    return [
      { geometry: wall, material: mat(WALLS[v % 3], { side: THREE.DoubleSide }) },
      { geometry: roof, material: mat(THATCH[v % 3]) },
      { geometry: door, material: mat(0x2e2218) },
      { geometry: floor, material: mat(0x4a3a2a) },
    ];
  });
}
// a woodpile: a few logs stacked
export function logs(v) {
  return made(`logs${v}`, () => {
    const parts = [];
    for (let i = 0; i < 3 + v; i++) {
      const g = new THREE.CylinderGeometry(0.13, 0.14, 1.3, 7).rotateZ(Math.PI / 2);
      g.translate(0, 0.13 + Math.floor(i / 3) * 0.24, (i % 3 - 1) * 0.27 + (Math.floor(i / 3) ? 0.13 : 0));
      parts.push({ geometry: g, material: mat(i % 2 ? 0x6b4a2e : 0x7a5838) });
    }
    return parts;
  });
}

// ---- a camp: hide tents on poles, a palisade stake ----
const HIDES = [0xa08a68, 0x8a6a4a, 0x6e5a44];
export function tent(v) {
  return made(`tent${v}`, () => {
    const L = 2.4, H = 1.6 + v * 0.15, half = 1.2;
    // an A-frame: two sloping hide panels and a ridge pole
    const panel = s => {
      const g = new THREE.PlaneGeometry(L, Math.hypot(H, half), 1, 1);
      g.rotateX(-Math.PI / 2 + s * Math.atan2(H, half));
      g.translate(0, H / 2, s * half / 2);
      return rough(g, 51 + v + (s > 0 ? 1 : 0), 0.05);
    };
    const back = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-L / 2, 0, -half), new THREE.Vector3(-L / 2, H, 0), new THREE.Vector3(-L / 2, 0, half)]);
    back.computeVertexNormals();
    const pole = new THREE.CylinderGeometry(0.04, 0.04, L + 0.4, 5).rotateZ(Math.PI / 2).translate(0, H + 0.02, 0);
    const posts = [-1, 1].map(s => new THREE.CylinderGeometry(0.045, 0.05, H + 0.25, 5).translate(s * (L / 2 + 0.15), (H + 0.25) / 2, 0));
    const hide = mat(HIDES[v % 3], { side: THREE.DoubleSide });
    return [{ geometry: panel(1), material: hide }, { geometry: panel(-1), material: hide }, { geometry: back, material: hide },
      { geometry: pole, material: mat(0x5a4028) }, ...posts.map(g => ({ geometry: g, material: mat(0x5a4028) }))];
  });
}
// a sharpened stake of a palisade, leaning a little
export function stake(v) {
  return made(`stake${v}`, () => {
    const h = 1.5 + v * 0.3;
    const g = new THREE.CylinderGeometry(0.1, 0.13, h, 6).translate(0, h / 2, 0);
    const tip = new THREE.ConeGeometry(0.1, 0.35, 6).translate(0, h + 0.17, 0);
    const lean = new THREE.Matrix4().makeRotationZ(0.08 * (v - 1));
    g.applyMatrix4(lean); tip.applyMatrix4(lean);
    return [{ geometry: g, material: mat(0x6b5236) }, { geometry: tip, material: mat(0x8a7050) }];
  });
}

// ---- a garden: clipped hedges ----
export function hedge(v) {
  return made(`hedge${v}`, () => {
    const g = rough(new THREE.BoxGeometry(1.05, 1.0 + v * 0.15, 1.05, 2, 2, 2), 61 + v, 0.07).translate(0, (1.0 + v * 0.15) / 2, 0);
    return [{ geometry: g, material: mat([0x3f6a32, 0x46743a, 0x365e2c][v % 3]) }];
  });
}

// ---- ruins: broken walls and columns of pale stone (or, where the words say no ruin, whole) ----
const RUIN_STONE = [0xa49c88, 0x938b78, 0xb0a892];
export function wallChunk(v) {
  return made(`wall${v}`, () => {
    // a stretch of wall with a jagged top: three courses, the upper ones broken off
    const parts = [];
    const stone = mat(RUIN_STONE[v % 3]);
    const hs = [[2.0, 1.4 + v * 0.3], [1.4, 0.8], [0.7 - v * 0.15, 0.6]];
    let y = 0;
    hs.forEach(([w, h], i) => {
      const g = rough(new THREE.BoxGeometry(w, h, 0.55, 2, 1, 1), 71 + v * 3 + i, 0.08).translate((i - 1) * 0.25 * (v % 2 ? 1 : -1), y + h / 2, 0);
      parts.push({ geometry: g, material: stone });
      y += h;
    });
    return parts;
  });
}
export function column(v, whole) {
  return made(`column${v}${whole ? 'W' : ''}`, () => {
    const h = whole ? 3.2 : 0.9 + v * 0.7;
    const stone = mat(whole ? 0xe4ded2 : RUIN_STONE[v % 3]);
    const parts = [
      { geometry: new THREE.BoxGeometry(0.85, 0.25, 0.85).translate(0, 0.125, 0), material: stone },
      { geometry: rough(new THREE.CylinderGeometry(0.3, 0.33, h, 10, 1), 81 + v, whole ? 0 : 0.05).translate(0, 0.25 + h / 2, 0), material: stone },
    ];
    if (whole) parts.push({ geometry: new THREE.BoxGeometry(0.8, 0.22, 0.8).translate(0, 0.25 + h + 0.11, 0), material: stone });
    return parts;
  });
}
// a column drum fallen on its side
export function drum(v) {
  return made(`drum${v}`, () => [{ geometry: rough(new THREE.CylinderGeometry(0.3, 0.3, 0.9 + v * 0.4, 10), 91 + v, 0.04).rotateZ(Math.PI / 2).translate(0, 0.3, 0), material: mat(RUIN_STONE[v % 3]) }]);
}

// a terrace: whole columns of white marble on marble paving under the sky (the Gods' Table)
export const PLACES = new Set(['village', 'camp', 'garden', 'ruins', 'terrace']);

// what stands in a place's border: `trees` deep in it, `near` along the open ground's edge
export function placeEdge(theme, kits, layout) {
  const N = kits.nature, G = kits.graveyard, T = kits.town;
  if (theme === 'village') return {
    trees: [hut(0), hut(1), hut(2), N.get('CommonTree_1'), N.get('CommonTree_3'), N.get('Pine_1')], treeP: 0.28,
    near: rng => { const r = rng(); return r < 0.35 ? { model: N.get('Bush_Common'), s: 0.8 + rng() * 0.3 } : r < 0.5 && T ? { model: T.get('fence_wood_straight'), s: 1 } : r < 0.6 ? { model: logs(Math.floor(rng() * 2)), s: 1 } : null; },
  };
  if (theme === 'camp') return {
    trees: [tent(0), tent(1), tent(2), N.get('Pine_1'), N.get('Pine_2'), N.get('DeadTree_1')], treeP: 0.3,
    near: rng => rng() < 0.45 ? { model: stake(Math.floor(rng() * 3)), s: 1 } : rng() < 0.3 ? { model: N.get('Rock_Medium_2'), s: 0.4 } : null,
  };
  if (theme === 'garden') return {
    trees: [N.get('CommonTree_1'), N.get('CommonTree_2'), N.get('CommonTree_3'), hedge(2)], treeP: 0.5,
    near: rng => rng() < 0.7 ? { model: hedge(Math.floor(rng() * 3)), s: 1, yaw: 0 } : { model: N.get('Bush_Common_Flowers'), s: 0.9 },
  };
  if (theme === 'ruins' || theme === 'terrace') {
    const whole = theme === 'terrace';
    return {
      trees: whole ? [column(0, true), column(1, true), N.get('Pine_2')] : [wallChunk(0), wallChunk(1), wallChunk(2), column(1), column(2), N.get('DeadTree_1')],
      treeP: whole ? 0.18 : 0.4,
      near: rng => { const r = rng(); return r < 0.3 ? { model: whole ? column(0, true) : column(Math.floor(rng() * 3)), s: 1, yaw: 0 } : r < 0.5 && !whole ? { model: wallChunk(Math.floor(rng() * 3)), s: 0.7 } : r < 0.65 ? { model: N.get('Bush_Common'), s: 0.7 } : null; },
    };
  }
  return null;
}

// the border cells one step behind the open ground (where a village's huts and a camp's tents
// stand, in sight of the ways through), spaced apart, never across a way out
function ring(layout, rng, gap, most) {
  const { W, H, grid } = layout;
  const depth = new Uint8Array(W * H).fill(255), q = [];
  for (let i = 0; i < W * H; i++) if (grid[i] !== 1) { depth[i] = 0; q.push(i); }
  for (let h = 0; h < q.length; h++) {
    const i = q[h], x = i % W, y = (i / W) | 0;
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const xx = x + dx, yy = y + dy;
      if (xx < 0 || yy < 0 || xx >= W || yy >= H) continue;
      const j = yy * W + xx;
      if (depth[j] > depth[i] + 1) { depth[j] = depth[i] + 1; q.push(j); }
    }
  }
  const cells = [];
  for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) if (depth[y * W + x] === 2) cells.push([x, y]);
  for (let i = cells.length - 1; i > 0; i--) { const j = Math.floor(rng() * (i + 1)); [cells[i], cells[j]] = [cells[j], cells[i]]; }
  const out = [];
  for (const [x, y] of cells) {
    if (out.length >= most) break;
    if (out.some(([a, b]) => Math.hypot(a - x, b - y) < gap)) continue;
    out.push([x, y]);
  }
  return out;
}

// on the open ground of a place (not on the ways through: `ln`)
export function dressPlace(c, theme, ln) {
  const { layout, ox, oz, kits, b, rng, occ } = c;
  const { W, H, grid } = layout;
  const N = kits.nature, G = kits.graveyard, T = kits.town, D = kits.dungeon;
  // a village's huts and a camp's tents, facing the open ground
  if (theme === 'village' || theme === 'camp') {
    const spots = ring(layout, rng, theme === 'village' ? 6 : 4.5, theme === 'village' ? 4 : 5);
    spots.forEach(([x, y], i) => {
      const cx = ox + x + 0.5, cz = oz + y + 0.5, mx = ox + W / 2, mz = oz + H / 2;
      const face = Math.atan2(mx - cx, mz - cz);        // the door toward the middle
      const m = theme === 'village' ? hut(i % 3) : tent(i % 3);
      b.add(occ ? occ(m) : m, trs(cx, 0, cz, face, theme === 'village' ? 0.8 : 0.9));
    });
  }
  const whole = theme === 'terrace';
  for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) {
    if (grid[y * W + x] !== 0) continue;
    const r = rng(), px = ox + x + 0.2 + rng() * 0.6, pz = oz + y + 0.2 + rng() * 0.6, yaw = rng() * 6.28;
    const lane = ln(x, y);
    const put = (m, s) => { if (m) b.add(m, trs(px, 0, pz, yaw, s), { shadow: false }); };
    if (theme === 'village') {
      if (lane) { if (r < 0.04) put(N.get('Pebble_Round_1'), 1.2); continue; }
      if (r < 0.16) put(N.get('Grass_Common_Short'), 0.7 + rng() * 0.3);
      else if (r < 0.18 && T) put(T.get(rng() < 0.5 ? 'sack' : 'crate_B_small'), 1);
      else if (r < 0.19 && D) put(D.get('barrel_small'), 0.9);
    } else if (theme === 'camp') {
      if (lane) { if (r < 0.05) put(N.get('Pebble_Round_3'), 1.2); continue; }
      if (r < 0.06) put(N.get('Grass_Wispy_Tall'), 0.6);
      else if (r < 0.085 && G) put(G.get(rng() < 0.6 ? 'bone_A' : 'bone_B'), 0.9);
      else if (r < 0.1) put(logs(0), 0.8);
      else if (r < 0.11 && T) put(T.get('sack'), 1);
    } else if (theme === 'garden') {
      if (lane) continue;          // a clean gravel path
      if (r < 0.14) put(N.get(rng() < 0.5 ? 'Flower_3_Group' : 'Flower_4_Group'), 0.7 + rng() * 0.3);
      else if (r < 0.3) put(N.get('Grass_Common_Short'), 0.6 + rng() * 0.3);
      else if (r < 0.33) put(N.get('Clover_1'), 0.8);
      else if (r < 0.345) put(N.get('Bush_Common_Flowers'), 0.6);
    } else if (theme === 'ruins' || theme === 'terrace') {
      if (lane) { if (!whole && r < 0.05) put(N.get('Pebble_Round_1'), 1.3); continue; }
      if (whole) { if (r < 0.015) put(N.get('Bush_Common_Flowers'), 0.5); continue; }     // swept marble
      if (r < 0.14) put(N.get(rng() < 0.6 ? 'Grass_Common_Short' : 'Grass_Wispy_Tall'), 0.6 + rng() * 0.3);
      else if (r < 0.18 && D) put(D.get(rng() < 0.5 ? 'rubble_half' : 'rubble_large'), 0.6);
      else if (r < 0.195) put(drum(Math.floor(rng() * 3)), 1);
    }
  }
}
