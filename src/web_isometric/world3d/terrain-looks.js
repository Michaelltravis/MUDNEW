// How a room looks when its words say what it is (Push 33): the server reads each room's name,
// description and neighbours and gives it a look (room_looks.py), and terrain.js draws by it.
//  - cave:  rock for walls (every wall and rubble cell a boulder pile, darkened), stalagmites
//           rising from the rock's foot, a fringe of stalactites along the tops of the walls,
//           glowing crystals and mushrooms
//  - mine:  cave rock, plus timber frames along the walls, rails down the main way, lanterns
//           on the posts, ore glinting in the rock
//  - crypt: (stone hall) coffins and sarcophagi for obstacles, bones, skulls and skull-candles
//           for props, cobwebs in the corners
//  - sewer: (stone hall) a channel of foul water with stone rims, pipes in the walls
//  - dungeon: (stone hall) broken walls and rubble
//  - outdoors: desert (cacti, bleached bones), snow (frosted pines, ice), shore (driftwood,
//           pebbles), volcanic (scorched trees, lava cracks)
// Everything placed on the floor that should stop the hero is written into the room's grid as
// BLOCK (the server never sees it: it is scenery, like furniture).
import * as THREE from 'three';
import { trs } from './assets.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

const FLOOR = 0, BLOCK = 1, WATER = 4;
export const UNDERGROUND = new Set(['cave', 'mine']);

// a model with its materials darkened or tinted (cached by name+tint)
const tintCache = new Map();
export function tinted(model, color, key, opts = {}) {
  if (!model) return model;
  const name = `${model.name}#${key}`;
  let t = tintCache.get(name);
  if (!t) {
    const c = new THREE.Color(color);
    const mat = m => {
      const n = m.clone();
      if (n.color) n.color.multiply(c);
      if (opts.emissive) { n.emissive = new THREE.Color(opts.emissive); n.emissiveIntensity = opts.glow || 1; }
      return n;
    };
    t = { name, box: model.box, parts: model.parts.map(p => ({ geometry: p.geometry, material: Array.isArray(p.material) ? p.material.map(mat) : mat(p.material) })) };
    tintCache.set(name, t);
  }
  return t;
}
const heightOf = model => { const s = new THREE.Vector3(); model.box.getSize(s); return Math.max(0.01, s.y); };

const STONE_MAT = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.92, metalness: 0 });
const PLANT_MAT = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.85, metalness: 0 });
const WOOD_MAT = new THREE.MeshStandardMaterial({ color: 0x5a3e24, roughness: 0.9 });
const IRON_MAT = new THREE.MeshStandardMaterial({ color: 0x3a3a3e, roughness: 0.5, metalness: 0.75 });
const CRYSTAL_MATS = {
  cave: new THREE.MeshBasicMaterial({ color: new THREE.Color(0.9, 2.4, 3.8) }),
  mine: new THREE.MeshBasicMaterial({ color: new THREE.Color(2.4, 1.7, 0.5) }),
  lava: new THREE.MeshBasicMaterial({ color: new THREE.Color(1.7, 0.36, 0.03) }),
};
const SEWER_WATER = new THREE.MeshStandardMaterial({ color: 0x2e3a1c, roughness: 0.55, metalness: 0.05, transparent: true, opacity: 0.94 });
const ICE_MAT = new THREE.MeshStandardMaterial({ color: 0xcfe8ff, roughness: 0.08, metalness: 0.1, transparent: true, opacity: 0.7,
  polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
const WEB_MAT = (() => {
  if (typeof document === 'undefined') return null;
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const g = c.getContext('2d');
  g.strokeStyle = 'rgba(230,230,240,0.75)'; g.lineWidth = 1.2;
  for (let i = 0; i < 9; i++) { const a = (i / 8) * Math.PI / 2; g.beginPath(); g.moveTo(0, 0); g.lineTo(Math.cos(a) * 128, Math.sin(a) * 128); g.stroke(); }
  for (let r = 18; r < 128; r += 18) { g.beginPath(); for (let i = 0; i <= 8; i++) { const a = (i / 8) * Math.PI / 2, rr = r + (i % 2 ? -3 : 3); i ? g.lineTo(Math.cos(a) * rr, Math.sin(a) * rr) : g.moveTo(Math.cos(a) * rr, Math.sin(a) * rr); } g.stroke(); }
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  return new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, side: THREE.DoubleSide });
})();

// merged procedural pieces of one material, as one mesh owned by the room
function addMerged(c, geos, material, { shadow = true } = {}) {
  if (!geos.length) return null;
  const g = mergeGeometries(geos, false);
  for (const x of geos) x.dispose();
  if (!g) return null;
  c.owned.push(g);
  const m = new THREE.Mesh(g, material);
  m.castShadow = shadow; m.receiveShadow = true;
  c.group.add(m);
  return m;
}
function colored(geo, color) {
  const col = new THREE.Color(color), n = geo.attributes.position.count, a = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { a[i * 3] = col.r; a[i * 3 + 1] = col.g; a[i * 3 + 2] = col.b; }
  geo.setAttribute('color', new THREE.BufferAttribute(a, 3));
  return geo;
}
function lane(layout) {
  const { W, H, gaps } = layout;
  const mx = Math.floor(W / 2), my = Math.floor(H / 2);
  return (x, y) => ((gaps.north || gaps.south) && Math.abs(x - mx) <= 3) || ((gaps.east || gaps.west) && Math.abs(y - my) <= 2);
}
// floor cells next to a BLOCK cell (where the rock meets the floor)
function rockFoot(layout) {
  const { W, H, grid } = layout, out = [];
  const at = (x, y) => (x < 0 || y < 0 || x >= W || y >= H) ? BLOCK : grid[y * W + x];
  for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) {
    if (at(x, y) !== FLOOR) continue;
    if (at(x + 1, y) === BLOCK || at(x - 1, y) === BLOCK || at(x, y + 1) === BLOCK || at(x, y - 1) === BLOCK) out.push([x, y]);
  }
  return out;
}

// ---------------------------------------------------------------- caves and mines
export function underground(c, look) {
  const { layout, ox, oz, kits, b, rng, occ } = c;
  const { W, H, grid } = layout;
  const N = kits.nature, D = kits.dungeon;
  const at = (x, y) => (x < 0 || y < 0 || x >= W || y >= H) ? BLOCK : grid[y * W + x];
  // the kit's rock is dark and mossy: lifted (a tint above 1) to a pale grey stone, warmer in a mine
  const rockTint = look === 'mine' ? new THREE.Color(1.55, 1.35, 1.15) : new THREE.Color(1.5, 1.48, 1.62);
  const rocks = [1, 2, 3].map(i => tinted(N.get(`Rock_Medium_${i}`), rockTint, `${look}rock`)).filter(Boolean);
  // the walls: a boulder pile on every BLOCK cell, tall on the room's edge, lower inside
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    if (at(x, y) !== BLOCK) continue;
    const edge = x === 0 || y === 0 || x === W - 1 || y === H - 1;
    const rock = rocks[Math.floor(rng() * rocks.length)];
    if (!rock) continue;
    const want = edge ? 2.2 + rng() * 1.4 : 0.9 + rng() * 0.9;
    const s = want / heightOf(rock);
    b.add(occ(rock), trs(ox + x + 0.5 + (rng() - 0.5) * 0.3, -0.1, oz + y + 0.5 + (rng() - 0.5) * 0.3, rng() * 6.28, s * (0.9 + rng() * 0.3), s, s * (0.9 + rng() * 0.3)));
  }
  const stone = [];
  // stalagmites at the rock's foot (they stand in the rock's cell, so the floor stays clear)
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    if (at(x, y) !== BLOCK || rng() > (look === 'cave' ? 0.3 : 0.12)) continue;
    const near = [[1, 0], [-1, 0], [0, 1], [0, -1]].find(([dx, dy]) => at(x + dx, y + dy) === FLOOR);
    if (!near) continue;
    const h = 0.6 + rng() * 1.3, r = 0.12 + rng() * 0.16;
    const g = new THREE.ConeGeometry(r, h, 6);
    g.translate(ox + x + 0.5 + near[0] * 0.45, h / 2, oz + y + 0.5 + near[1] * 0.45);
    stone.push(colored(g, rng() < 0.5 ? 0x6a6258 : 0x585058));
  }
  // stalactites: a fringe hanging from the tops of the walls, leaning into the room
  for (const run of c.runs) {
    for (let i = run.a; i <= run.b; i++) {
      if (rng() > 0.55) continue;
      const h = 0.5 + rng() * 1.1, r = 0.1 + rng() * 0.14;
      const g = new THREE.ConeGeometry(r, h, 5);
      g.rotateX(Math.PI);
      const inset = 0.95;
      const [x, z] = run.horiz
        ? [ox + i + 0.5, oz + run.line + 0.5 + (run.line === 0 ? inset : -inset)]
        : [ox + run.line + 0.5 + (run.line === 0 ? inset : -inset), oz + i + 0.5];
      g.translate(x, 2.9 - h / 2, z);
      stone.push(colored(g, 0x5c5650));
    }
  }
  addMerged(c, stone, STONE_MAT);
  // glowing crystals (a cave) or ore (a mine) in the rock, mushrooms at its foot
  const glow = [];
  for (const [x, y] of rockFoot(layout)) {
    const r = rng();
    if (r < (look === 'cave' ? 0.07 : 0.05)) {
      for (let k = 0; k < 3; k++) {
        const g = new THREE.OctahedronGeometry(0.08 + rng() * 0.12, 0);
        g.scale(1, 2.2, 1);
        g.rotateZ((rng() - 0.5) * 0.9);
        g.translate(ox + x + 0.5 + (rng() - 0.5) * 0.6, 0.15 + rng() * 0.3, oz + y + 0.5 + (rng() - 0.5) * 0.6);
        glow.push(g);
      }
    } else if (look === 'cave' && r < 0.16 && N.get('Mushroom_Common')) {
      b.add(tinted(N.get('Mushroom_Common'), 0xa0c8ff, 'glowshroom', { emissive: 0x4a8ae0, glow: 2.2 }),
        trs(ox + x + 0.5, 0, oz + y + 0.5, rng() * 6.28, 0.9 + rng() * 0.6), { shadow: false });
    } else if (r < 0.24 && N.get('Pebble_Round_1')) {
      b.add(tinted(N.get('Pebble_Round_1'), rockTint, `${look}peb`), trs(ox + x + 0.3 + rng() * 0.4, 0, oz + y + 0.3 + rng() * 0.4, rng() * 6.28, 1.2 + rng()), { shadow: false });
    }
  }
  addMerged(c, glow, CRYSTAL_MATS[look] || CRYSTAL_MATS.cave, { shadow: false });
  if (look === 'mine') mineWorks(c);
  else if (D) {
    // torches along the rock where others have passed, spread out (four, to keep it readable)
    const foot = rockFoot(layout).filter(([x, y]) => !lane(layout)(x, y)).sort((p, q) => p[0] - q[0]);
    const n = Math.min(4, foot.length);
    for (let i = 0; i < n; i++) {
      const [x, y] = foot[Math.floor(((i + 0.2 + rng() * 0.6) / n) * foot.length)];
      b.add(D.get('torch_lit'), trs(ox + x + 0.5, 0.4, oz + y + 0.5, 0, 1.3), { shadow: false });
      c.torches.push(new THREE.Vector3(ox + x + 0.5, 1.4, oz + y + 0.5));
    }
  }
}

// a mine: timber frames along the walls, rails along the main way, lanterns on the posts
function mineWorks(c) {
  const { layout, ox, oz, kits, b, rng } = c;
  const { W, H, gaps } = layout;
  const D = kits.dungeon;
  const wood = [], iron = [];
  const post = (x, z) => { const g = new THREE.BoxGeometry(0.22, 2.5, 0.22); g.translate(x, 1.25, z); wood.push(g); };
  // frames every ~5 m along the north and south walls, a beam across their tops
  for (let x = 3; x < W - 3; x += 5) {
    for (const [y, dz] of [[1, 0.2], [H - 2, -0.2]]) {
      if (layout.grid[y * W + x] !== FLOOR) continue;
      post(ox + x + 0.2, oz + y + 0.5 + dz);
      const beam = new THREE.BoxGeometry(1.6, 0.22, 0.26); beam.translate(ox + x + 0.2, 2.45, oz + y + 0.5 + dz); wood.push(beam);
      if (D && rng() < 0.6) {
        b.add(D.get('torch_lit'), trs(ox + x + 0.2, 1.6, oz + y + 0.5 + dz * 2.5, 0, 1.1), { shadow: false });
        c.torches.push(new THREE.Vector3(ox + x + 0.2, 2.5, oz + y + 0.5 + dz * 2.5));
      }
    }
  }
  // rails down the long way through (east-west if there is one), on sleepers
  const mx = Math.floor(W / 2), my = Math.floor(H / 2);
  if (gaps.east || gaps.west) {
    for (let x = 0; x < W; x++) {
      const s = new THREE.BoxGeometry(0.22, 0.06, 1.3); s.translate(ox + x + 0.5, 0.03, oz + my + 0.5); wood.push(s);
    }
    for (const dz of [-0.4, 0.4]) { const r = new THREE.BoxGeometry(W, 0.07, 0.07); r.translate(ox + W / 2, 0.09, oz + my + 0.5 + dz); iron.push(r); }
  } else if (gaps.north || gaps.south) {
    for (let y = 0; y < H; y++) {
      const s = new THREE.BoxGeometry(1.3, 0.06, 0.22); s.translate(ox + mx + 0.5, 0.03, oz + y + 0.5); wood.push(s);
    }
    for (const dx of [-0.4, 0.4]) { const r = new THREE.BoxGeometry(0.07, 0.07, H); r.translate(ox + mx + 0.5 + dx, 0.09, oz + H / 2); iron.push(r); }
  }
  addMerged(c, wood, WOOD_MAT);
  addMerged(c, iron, IRON_MAT);
  // an ore cart or crates by the rails
  if (D) for (let i = 0; i < 2; i++) {
    const x = 3 + Math.floor(rng() * (W - 6)), y = 2 + Math.floor(rng() * (H - 4));
    if (layout.grid[y * W + x] !== FLOOR || lane(layout)(x, y)) continue;
    b.add(D.get(rng() < 0.5 ? 'crates_stacked' : 'barrel_large'), trs(ox + x + 0.5, 0, oz + y + 0.5, rng() * 6.28, 0.8));
    layout.grid[y * W + x] = BLOCK;
  }
}

// ---------------------------------------------------------------- stone halls
// what replaces the plain interior's crates and candles; returns true when it dressed the room
export function dressHall(c, theme) {
  if (theme === 'crypt') return crypt(c);
  if (theme === 'sewer') return sewer(c);
  return false;
}

function crypt(c) {
  const { layout, ox, oz, kits, b, rng, occ } = c;
  const G = kits.graveyard, D = kits.dungeon;
  if (!G) return false;
  const { W, H, grid } = layout;
  const ln = lane(layout);
  // coffins on the obstacles and in rows along the walls
  for (const o of layout.obstacles || []) {
    const key = o.big ? (rng() < 0.5 ? 'coffin_decorated' : 'coffin') : ['bone_A', 'skull', 'ribcage'][Math.floor(rng() * 3)];
    b.add(o.big ? occ(G.get(key)) : G.get(key), trs(ox + o.x + (o.big ? 1 : 0.5), 0, oz + o.y + (o.big ? 1 : 0.5), Math.floor(rng() * 4) * Math.PI / 2, o.big ? 0.75 : 0.6));
  }
  for (let x = 3; x < W - 3; x += 3) {
    for (const y of [2, H - 3]) {
      if (grid[y * W + x] !== FLOOR || ln(x, y) || rng() < 0.35) continue;
      b.add(occ(G.get(rng() < 0.3 ? 'coffin_decorated' : 'coffin')), trs(ox + x + 0.5, 0, oz + y + 0.5, Math.PI / 2, 0.6));
      grid[y * W + x] = BLOCK;
    }
  }
  // bones, skulls and skull-candles on the floor; candles light it
  for (const p of layout.props || []) {
    const key = ['skull_candle', 'bone_B', 'bone_C', 'skull', 'skull_candle'][Math.floor(rng() * 5)];
    b.add(G.get(key), trs(ox + p.x + 0.5, 0, oz + p.y + 0.5, rng() * 6.28, 0.7), { shadow: false });
    if (key === 'skull_candle') c.torches.push(new THREE.Vector3(ox + p.x + 0.5, 0.6, oz + p.y + 0.5));
  }
  // cobwebs in the corners
  if (WEB_MAT) for (const [cx, cz, yaw] of [[1, 1, 0], [W - 1, 1, -Math.PI / 2], [1, H - 1, Math.PI / 2], [W - 1, H - 1, Math.PI]]) {
    if (rng() < 0.3) continue;
    const g = new THREE.PlaneGeometry(1.6, 1.6);
    g.translate(0.8, -0.8, 0); g.rotateY(Math.PI / 4); g.rotateY(yaw);
    g.translate(ox + cx, 2.55, oz + cz);
    c.owned.push(g);
    const m = new THREE.Mesh(g, WEB_MAT);
    c.group.add(m);
  }
  return true;
}

function sewer(c) {
  const { layout, ox, oz, kits, b, rng } = c;
  const { W, H, grid } = layout;
  const D = kits.dungeon;
  // the channel's water, a little below the walkways, with stone rims along it
  const cells = [];
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (grid[y * W + x] === WATER) cells.push([x, y]);
  if (cells.length) {
    const geo = new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2);
    c.owned.push(geo);
    const wm = new THREE.InstancedMesh(geo, SEWER_WATER, cells.length);
    cells.forEach(([x, y], i) => wm.setMatrixAt(i, trs(ox + x + 0.5, -0.22, oz + y + 0.5, 0, 1.02)));
    wm.receiveShadow = true;
    c.group.add(wm);
    const rim = [];
    for (const [x, y] of cells) for (const dy of [-1, 1]) {
      if (grid[(y + dy) * W + x] === WATER) continue;
      const g = new THREE.BoxGeometry(1, 0.12, 0.18); g.translate(ox + x + 0.5, 0.0, oz + y + 0.5 + dy * 0.5);
      rim.push(colored(g, 0x5a564e));
      const wall = new THREE.BoxGeometry(1, 0.5, 0.06); wall.translate(ox + x + 0.5, -0.25, oz + y + 0.5 + dy * 0.47);
      rim.push(colored(wall, 0x2e2c28));
    }
    addMerged(c, rim, STONE_MAT, { shadow: false });
  }
  // pipes out of the north wall, dribbling into the channel
  const pipes = [];
  for (let x = 3; x < W - 3; x += 6) {
    if (rng() < 0.3) continue;
    const g = new THREE.CylinderGeometry(0.18, 0.18, 0.9, 10); g.rotateX(Math.PI / 2); g.translate(ox + x + 0.5, 1.1, oz + 0.9);
    pipes.push(g);
  }
  addMerged(c, pipes, IRON_MAT);
  // weeds and puddles on the walkways, a lamp or two
  for (const p of layout.props || []) {
    if (D && rng() < 0.3) { b.add(D.get('torch_lit'), trs(ox + p.x + 0.5, 0.4, oz + p.y + 0.5, 0, 1.2), { shadow: false }); c.torches.push(new THREE.Vector3(ox + p.x + 0.5, 1.4, oz + p.y + 0.5)); }
    else if (D) b.add(D.get('barrel_small'), trs(ox + p.x + 0.5, 0, oz + p.y + 0.5, rng() * 6.28, 0.7));
  }
  return true;
}

// ---------------------------------------------------------------- open country
// what grows (or lies) on an outdoor look's edges: [key, kit, tint] lists by look
export function outdoorEdge(theme, kits) {
  const N = kits.nature, G = kits.graveyard;
  if (theme === 'snow') return { trees: ['Pine_1', 'Pine_2'].map(k => tinted(N.get(k), 0xdfe8f0, 'frost')), treeP: 0.35, rock: k => tinted(N.get(k), 0xe8eef4, 'snowrock'), bush: null };
  if (theme === 'volcanic') return { trees: ['DeadTree_1', 'DeadTree_2'].map(k => tinted(N.get(k), 0x2a2420, 'scorch')), treeP: 0.12, rock: k => tinted(N.get(k), 0x3a302c, 'basalt'), bush: null };
  if (theme === 'shore') return { trees: [], treeP: 0, rock: k => N.get(k), bush: null };
  if (theme === 'desert') return { trees: [], treeP: 0, rock: k => tinted(N.get(k), 0xffc890, 'sandstone'), bush: null };
  return null;
}

// scattered on the open ground of an outdoor look (instead of grass and flowers)
export function outdoorDress(c, theme) {
  const { layout, ox, oz, kits, b, rng } = c;
  const { W, H, grid } = layout;
  const N = kits.nature, G = kits.graveyard;
  const ln = lane(layout);
  const solid = [], glow = [];
  for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) {
    if (grid[y * W + x] !== FLOOR) continue;
    const r = rng(), px = ox + x + 0.2 + rng() * 0.6, pz = oz + y + 0.2 + rng() * 0.6, yaw = rng() * 6.28;
    if (theme === 'desert') {
      if (!ln(x, y) && r < 0.025) { cactus(solid, px, pz, rng); grid[y * W + x] = BLOCK; }
      else if (r < 0.04 && G) b.add(tinted(G.get(rng() < 0.5 ? 'bone_A' : 'skull'), 0xf4ecd8, 'bleached'), trs(px, 0, pz, yaw, 0.6), { shadow: false });
      else if (r < 0.07) b.add(tinted(N.get('Pebble_Round_3'), 0xe0c8a0, 'sandpeb'), trs(px, 0, pz, yaw, 1.3), { shadow: false });
    } else if (theme === 'shore') {
      if (r < 0.05) b.add(N.get(rng() < 0.5 ? 'Pebble_Round_1' : 'Pebble_Round_3'), trs(px, 0, pz, yaw, 1.4), { shadow: false });
      else if (!ln(x, y) && r < 0.065) driftwood(solid, px, pz, yaw, rng);
    } else if (theme === 'snow') {
      if (r < 0.03) b.add(tinted(N.get('Rock_Medium_1'), 0xe8eef4, 'snowrock'), trs(px, 0, pz, yaw, 0.25), { shadow: false });
    } else if (theme === 'volcanic') {
      if (r < 0.035) {
        // a jagged crack: a few short segments, each turning a little
        let cx = px, cz = pz, a = yaw;
        for (let k = 0; k < 3 + Math.floor(rng() * 3); k++) {
          const len = 0.35 + rng() * 0.5;
          const g = new THREE.BoxGeometry(len, 0.03, 0.06 + rng() * 0.05);
          g.rotateY(-a); g.translate(cx + Math.cos(a) * len / 2, 0.02, cz + Math.sin(a) * len / 2); glow.push(g);
          cx += Math.cos(a) * len; cz += Math.sin(a) * len; a += (rng() - 0.5) * 1.6;
        }
      }
      else if (r < 0.09) b.add(tinted(N.get('Pebble_Round_1'), 0x2a2420, 'ash'), trs(px, 0, pz, yaw, 1.5), { shadow: false });
    }
  }
  addMerged(c, solid, PLANT_MAT);
  addMerged(c, glow, CRYSTAL_MATS.lava, { shadow: false });
  // snow: the prose's ice as glassy patches
  if (theme === 'snow' && layout.iceCells && layout.iceCells.length) {
    const geo = new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2);
    c.owned.push(geo);
    const im = new THREE.InstancedMesh(geo, ICE_MAT, layout.iceCells.length);
    layout.iceCells.forEach(([x, y], i) => im.setMatrixAt(i, trs(ox + x + 0.5, 0.02, oz + y + 0.5, 0, 1)));
    c.group.add(im);
  }
}

function cactus(out, x, z, rng) {
  const h = 1.2 + rng() * 1.2, col = 0x4f7a3a;
  const trunk = new THREE.CylinderGeometry(0.16, 0.2, h, 8); trunk.translate(x, h / 2, z); out.push(colored(trunk, col));
  for (const side of [-1, 1]) {
    if (rng() < 0.35) continue;
    const ah = 0.4 + rng() * 0.5, y0 = h * (0.35 + rng() * 0.3);
    const elbow = new THREE.CylinderGeometry(0.11, 0.11, 0.35, 7); elbow.rotateZ(Math.PI / 2); elbow.translate(x + side * 0.3, y0, z); out.push(colored(elbow, col));
    const arm = new THREE.CylinderGeometry(0.1, 0.12, ah, 7); arm.translate(x + side * 0.45, y0 + ah / 2, z); out.push(colored(arm, col));
  }
}
function driftwood(out, x, z, yaw, rng) {
  const g = new THREE.CylinderGeometry(0.09, 0.13, 1.2 + rng(), 7);
  g.rotateZ(Math.PI / 2); g.rotateY(yaw); g.translate(x, 0.1, z);
  out.push(colored(g, 0x9a8a72));
}

// ground colours for the looks (terrain.js GROUND adds these)
export const LOOK_GROUND = {
  cave: { a: 0x5c5650, b: 0x766e66, path: 0x7e766c, wet: 0x2a3844 },
  mine: { a: 0x4c4034, b: 0x645444, path: 0x76644e, wet: 0x262c2e },
  snow: { a: 0xd8e2ec, b: 0xf2f6fa, path: 0xb4c0ca, wet: 0x9cc4dc },
  shore: { a: 0xd4c08a, b: 0xe6d6a6, path: 0xc0a874, wet: 0x5a8a98 },
  volcanic: { a: 0x2a2422, b: 0x40342c, path: 0x56443a, wet: 0x4a1a08 },
};
