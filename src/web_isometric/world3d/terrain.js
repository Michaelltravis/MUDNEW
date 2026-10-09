// Turns a room layout (MH.generateRoomTopDown: a 24x15 tile grid of FLOOR / BLOCK /
// WATER with gaps, obstacles and props) into 3D at a world offset. 1 tile = 1 m.
// World axes: x = east, z = south, y = up; a room's tile (0,0) corner sits at origin.
import * as THREE from 'three';
import { Batcher, trs } from './assets.js';
import { cutout } from './cutout.js';

export const ROOM_W = 24, ROOM_H = 15;
const FLOOR = 0, BLOCK = 1, WATER = 4;

const INDOOR = new Set(['inside', 'dungeon', 'cave']);
export const isIndoor = theme => INDOOR.has(theme);

// ---- deterministic noise (world-space, so neighbouring rooms join seamlessly) ----
function hash2(x, y) {
  let h = (Math.imul(x | 0, 374761393) + Math.imul(y | 0, 668265263)) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}
function vnoise(x, y) {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
  const a = hash2(xi, yi), b = hash2(xi + 1, yi), c = hash2(xi, yi + 1), d = hash2(xi + 1, yi + 1);
  return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
}
const fbm = (x, y) => vnoise(x, y) * 0.55 + vnoise(x * 2.1 + 17, y * 2.1 - 9) * 0.3 + vnoise(x * 4.3 - 5, y * 4.3 + 3) * 0.15;

const GROUND = {
  forest: { a: 0x45682f, b: 0x6a8f3e, path: 0x7b6343, wet: 0x2f4a32 },
  field: { a: 0x6f9445, b: 0x9bb65a, path: 0x8f7650, wet: 0x3c5a3a },
  hills: { a: 0x66874a, b: 0x8fa35e, path: 0x8a7352, wet: 0x3c5a3a },
  swamp: { a: 0x3f4b2c, b: 0x5a6436, path: 0x4c4130, wet: 0x26301f },
  desert: { a: 0xc9ab73, b: 0xdcc394, path: 0xb39062, wet: 0x8a6e48 },
  mountain: { a: 0x77746a, b: 0x8f8a7c, path: 0x6c6252, wet: 0x4a4c48 },
  default: { a: 0x5f7f44, b: 0x86a050, path: 0x85704e, wet: 0x3c5a3a },
};

// occluders get their own material copies with the see-through cut; floors keep theirs
const occCache = new WeakMap();
function occluder(mat) {
  if (Array.isArray(mat)) return mat.map(occluder);
  let m = occCache.get(mat);
  if (!m) { m = cutout.apply(mat.clone()); occCache.set(mat, m); }
  return m;
}
function asOccluder(model) {
  if (!model || model.occ) return model && model.occ;
  model.occ = { name: model.name + '#occ', box: model.box, parts: model.parts.map(p => ({ geometry: p.geometry, material: occluder(p.material) })) };
  return model.occ;
}

function runs(grid, W, H) {
  // maximal straight BLOCK runs along the four border lines (the room's walls)
  const out = [];
  const at = (x, y) => grid[y * W + x];
  for (const y of [0, H - 1]) {
    let x = 0;
    while (x < W) {
      if (at(x, y) !== BLOCK) { x++; continue; }
      const x0 = x; while (x < W && at(x, y) === BLOCK) x++;
      out.push({ horiz: true, line: y, a: x0, b: x - 1 });
    }
  }
  for (const x of [0, W - 1]) {
    let y = 1;
    while (y < H - 1) {
      if (at(x, y) !== BLOCK) { y++; continue; }
      const y0 = y; while (y < H - 1 && at(x, y) === BLOCK) y++;
      out.push({ horiz: false, line: x, a: y0, b: y - 1 });
    }
  }
  return out;
}

export function buildRoom(layout, ox, oz, kits) {
  const { grid, W, H } = layout;
  const theme = layout.theme;
  const rng = MH.mulberry32((layout.vnum * 2246822519) ^ 0x3d);
  const group = new THREE.Group();
  group.name = `room_${layout.vnum}`;
  const torches = [];
  const b = new Batcher();
  const at = (x, y) => (x < 0 || y < 0 || x >= W || y >= H) ? BLOCK : grid[y * W + x];
  const D = kits.dungeon, N = kits.nature;

  if (isIndoor(theme)) {
    // ---- floor: KayKit stone tiles at 1 m ----
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      // under everything but the wall ring (obstacles stand ON the floor)
      if (at(x, y) === BLOCK && (x === 0 || y === 0 || x === W - 1 || y === H - 1)) continue;
      const r = rng();
      const key = r < 0.07 ? 'floor_tile_small_broken_A' : r < 0.13 ? 'floor_tile_small_weeds_A' : 'floor_tile_small';
      b.add(D.get(key), trs(ox + x + 0.5, -0.05, oz + y + 0.5, Math.floor(rng() * 4) * Math.PI / 2, 0.5, 0.5, 0.5), { shadow: false });
    }
    // ---- walls: border runs as stretched KayKit wall pieces ----
    const wall = asOccluder(D.get('wall'));
    const WALL_H = 2.6;
    for (const run of runs(grid, W, H)) {
      const L = run.b - run.a + 1;
      const n = Math.max(1, Math.round(L / 4)), w = L / n;
      for (let i = 0; i < n; i++) {
        const along = run.a + (i + 0.5) * w;
        const [x, z, yaw] = run.horiz ? [ox + along, oz + run.line + 0.5, 0] : [ox + run.line + 0.5, oz + along, Math.PI / 2];
        b.add(wall, trs(x, 0, z, yaw, w / 4, WALL_H / 4, 1));
      }
      // torches on the north wall, facing into the room, every ~6 m
      if (run.horiz && run.line === 0 && L >= 4) {
        for (let tx = run.a + 2; tx <= run.b - 1; tx += 6) {
          if (at(tx, 1) === BLOCK) continue;
          b.add(D.get('torch_mounted'), trs(ox + tx + 0.5, 1.55, oz + 1.0, 0, 1), { shadow: false });
          torches.push(new THREE.Vector3(ox + tx + 0.5, 2.15, oz + 1.45));
        }
      }
    }
    // ---- interior obstacles (they block in the grid) ----
    for (const o of layout.obstacles || []) {
      if (o.big) {
        const key = rng() < 0.55 ? 'pillar' : rng() < 0.5 ? 'crates_stacked' : 'barrel_large';
        const s = key === 'pillar' ? 1 : 0.9;
        b.add(asOccluder(D.get(key)), trs(ox + o.x + 1, 0, oz + o.y + 1, Math.floor(rng() * 4) * Math.PI / 2, s, key === 'pillar' ? 0.66 : s, s));
      } else {
        const key = ['barrel_small', 'box_large', 'column'][Math.floor(rng() * 3)];
        const s = key === 'box_large' ? 0.62 : key === 'column' ? 1.1 : 0.9;
        b.add(D.get(key), trs(ox + o.x + 0.5, 0, oz + o.y + 0.5, rng() * Math.PI * 2, s));
      }
    }
    // ---- decorative props (walk-through): small things only ----
    for (const p of layout.props || []) {
      const key = ['candle_triple', 'candle_lit', 'coin_stack_large', 'candle_triple'][Math.floor(rng() * 4)];
      const s = key === 'coin_stack_large' ? 0.45 : 0.9;
      b.add(D.get(key), trs(ox + p.x + 0.5, 0, oz + p.y + 0.5, rng() * Math.PI * 2, s), { shadow: false });
    }
  } else {
    // ---- ground: one vertex-coloured sheet, noise in world space, dirt paths to exits ----
    const pal = GROUND[theme] || GROUND.default;
    const SEG = 2;
    const geo = new THREE.PlaneGeometry(W, H, W * SEG, H * SEG);
    geo.rotateX(-Math.PI / 2);
    geo.translate(ox + W / 2, 0, oz + H / 2);
    const pos = geo.attributes.position;
    const col = new Float32Array(pos.count * 3);
    const cA = new THREE.Color(pal.a), cB = new THREE.Color(pal.b), cP = new THREE.Color(pal.path), cW = new THREE.Color(pal.wet);
    const c = new THREE.Color();
    const midX = Math.floor(W / 2) + 0.5, midY = Math.floor(H / 2) + 0.5;
    const g = layout.gaps || {};
    for (let i = 0; i < pos.count; i++) {
      const wx = pos.getX(i), wz = pos.getZ(i);
      const lx = wx - ox, lz = wz - oz;
      const n = fbm(wx * 0.18, wz * 0.18);
      c.copy(cA).lerp(cB, THREE.MathUtils.smoothstep(n, 0.3, 0.75));
      // paths: from the room centre out through each gap
      let d = 99;
      if (g.north && lz <= midY) d = Math.min(d, Math.abs(lx - midX));
      if (g.south && lz >= midY) d = Math.min(d, Math.abs(lx - midX));
      if (g.west && lx <= midX) d = Math.min(d, Math.abs(lz - midY));
      if (g.east && lx >= midX) d = Math.min(d, Math.abs(lz - midY));
      d = Math.min(d, Math.hypot(lx - midX, lz - midY) - 1.2);
      const pw = (1 - THREE.MathUtils.smoothstep(d + (n - 0.5) * 1.6, 0.6, 1.9)) * 0.85;
      if (pw > 0) c.lerp(cP, pw);
      // darken under the treeline and around water
      // (vertices on the far edges belong to the last tile, not the void beyond it)
      const tx = Math.min(W - 1, Math.floor(lx)), ty = Math.min(H - 1, Math.floor(lz));
      if (at(tx, ty) === BLOCK) c.multiplyScalar(0.72);
      if (at(tx, ty) === WATER) c.lerp(cW, 0.8);
      col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;
      pos.setY(i, (n - 0.5) * 0.12 - (at(tx, ty) === WATER ? 0.35 : 0));
    }
    geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
    geo.computeVertexNormals();
    const ground = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.95, metalness: 0 }));
    ground.receiveShadow = true;
    group.add(ground);

    // water surface
    const wq = [];
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (at(x, y) === WATER) wq.push([x, y]);
    if (wq.length) {
      const wg = new THREE.PlaneGeometry(1, 1);
      wg.rotateX(-Math.PI / 2);
      const wm = new THREE.InstancedMesh(wg, WATER_MAT, wq.length);
      wq.forEach(([x, y], i) => wm.setMatrixAt(i, trs(ox + x + 0.5, -0.12, oz + y + 0.5, 0, 1.02)));
      wm.receiveShadow = true;
      group.add(wm);
    }

    // ---- the treeline: BLOCK cells become trees, bushes and rocks ----
    const depth = new Uint8Array(W * H).fill(255);
    const q = [];
    for (let i = 0; i < W * H; i++) if (grid[i] !== BLOCK) { depth[i] = 0; q.push(i); }
    for (let h = 0; h < q.length; h++) {
      const i = q[h], x = i % W, y = (i / W) | 0;
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [-1, -1], [1, -1], [-1, 1]]) {
        const xx = x + dx, yy = y + dy;
        if (xx < 0 || yy < 0 || xx >= W || yy >= H) continue;
        const j = yy * W + xx;
        if (depth[j] > depth[i] + 1) { depth[j] = depth[i] + 1; q.push(j); }
      }
    }
    const trees = theme === 'swamp' ? ['DeadTree_1', 'DeadTree_2', 'Pine_1'] :
      theme === 'desert' ? [] :
      ['CommonTree_1', 'CommonTree_2', 'CommonTree_3', 'CommonTree_1', 'Pine_1', 'Pine_2'];
    const treeP = theme === 'forest' ? 0.5 : theme === 'swamp' ? 0.3 : theme === 'desert' ? 0 : 0.22;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      if (at(x, y) !== BLOCK) continue;
      const dd = depth[y * W + x];
      const jx = (rng() - 0.5) * 0.6, jz = (rng() - 0.5) * 0.6;
      const px = ox + x + 0.5 + jx, pz = oz + y + 0.5 + jz, yaw = rng() * Math.PI * 2;
      const r = rng();
      if (dd >= 2 && trees.length && r < treeP) {
        const key = trees[Math.floor(rng() * trees.length)];
        b.add(asOccluder(N.get(key)), trs(px, 0, pz, yaw, 0.55 + rng() * 0.3));
      } else if (dd <= 2 && r < 0.62) {
        const rr = rng();
        const key = theme === 'desert' || rr < 0.18 ? `Rock_Medium_${1 + Math.floor(rng() * 3)}` : rr < 0.8 ? 'Bush_Common' : 'Bush_Common_Flowers';
        const s = key.startsWith('Rock') ? 0.45 + rng() * 0.3 : 0.75 + rng() * 0.4;
        b.add(asOccluder(N.get(key)), trs(px, 0, pz, yaw, s));
      } else if (r < 0.85) {
        b.add(N.get('Fern_1'), trs(px, 0, pz, yaw, 0.7 + rng() * 0.4), { shadow: false });
      }
    }
    // obstacles inside the room: boulders and thickets
    for (const o of layout.obstacles || []) {
      const cx = ox + o.x + (o.big ? 1 : 0.5), cz = oz + o.y + (o.big ? 1 : 0.5);
      const key = rng() < 0.6 ? `Rock_Medium_${1 + Math.floor(rng() * 3)}` : 'Bush_Common';
      const s = o.big ? 0.75 : 0.42;
      b.add(asOccluder(N.get(key)), trs(cx, 0, cz, rng() * Math.PI * 2, key === 'Bush_Common' ? s * 1.6 : s));
    }
    // ground clutter on open floor (not on the paths)
    if (theme !== 'desert') {
      for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) {
        if (at(x, y) !== FLOOR) continue;
        const onPath = (g.north || g.south) && Math.abs(x + 0.5 - midX) < 2 || (g.east || g.west) && Math.abs(y + 0.5 - midY) < 2;
        const r = rng();
        const px = ox + x + 0.2 + rng() * 0.6, pz = oz + y + 0.2 + rng() * 0.6, yaw = rng() * 6.28;
        if (onPath) { if (r < 0.06) b.add(N.get('Pebble_Round_1'), trs(px, 0, pz, yaw, 1.4), { shadow: false }); continue; }
        if (r < 0.26) b.add(N.get(rng() < 0.7 ? 'Grass_Common_Short' : 'Grass_Wispy_Tall'), trs(px, 0, pz, yaw, 0.7 + rng() * 0.4), { shadow: false });
        else if (r < 0.31) b.add(N.get('Clover_1'), trs(px, 0, pz, yaw, 0.8), { shadow: false });
        else if (r < 0.34) b.add(N.get(rng() < 0.5 ? 'Flower_3_Group' : 'Flower_4_Group'), trs(px, 0, pz, yaw, 0.6), { shadow: false });
        else if (r < 0.35) b.add(N.get('Mushroom_Common'), trs(px, 0, pz, yaw, 0.9), { shadow: false });
      }
    }
  }

  b.build(group);
  // flames: tiny HDR spheres so the bloom pass picks them up
  for (const t of torches) {
    const f = new THREE.Mesh(FLAME_GEO, FLAME_MAT);
    f.position.copy(t).add(new THREE.Vector3(0, -0.05, -0.12));
    group.add(f);
  }
  return { group, torches, layout, ox, oz };
}

const WATER_MAT = new THREE.MeshStandardMaterial({ color: 0x2f6f86, roughness: 0.12, metalness: 0.2, transparent: true, opacity: 0.82 });
const FLAME_GEO = new THREE.SphereGeometry(0.11, 10, 8);
const FLAME_MAT = new THREE.MeshBasicMaterial({ color: new THREE.Color(6, 3.2, 1.1) });
