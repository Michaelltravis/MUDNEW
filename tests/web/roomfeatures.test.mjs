// What a room's words say stands in it (room_features.py -> zone map `features`), placed by
// shared/roomgen.js: on open floor, off the ways through, never shutting a way out; the blocking
// ones are walls to the walker; a room's own centrepiece nearest the middle.
//   node --test tests/web/
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const W = 24, H = 15, FLOOR = 0, BLOCK = 1;
globalThis.window = globalThis;
globalThis.document = globalThis.document || { createElement: () => ({ getContext: () => null }) };
for (const f of ['world3d/hud-shim.js', 'shared/themes-zones.js', 'shared/roomgen.js']) {
  vm.runInThisContext(fs.readFileSync(path.join(ROOT, 'src/web_isometric', f), 'utf8'), { filename: f });
}
const MH = globalThis.MH;

const ALL_WAYS = { north: { to_room: 1 }, south: { to_room: 2 }, east: { to_room: 3 }, west: { to_room: 4 } };
const SETS = [
  // A Sharp Bend In The Stone Circle [24641]
  { look: 'stones', sector: 'city', name: 'A Sharp Bend In The Stone Circle', features: [{ k: 'standing_stone', n: 2, main: true, c: 'red' }, { k: 'stake_holes', n: 1 }] },
  { look: 'stones', sector: 'city', name: 'At The Slaughter Stone', features: [{ k: 'altar', n: 2, main: true, c: 'black' }, { k: 'chains', n: 1 }] },
  { look: 'inside', sector: 'inside', name: 'The Great Hall Of Orschnag', features: [{ k: 'brazier', n: 2 }, { k: 'banner', n: 4 }, { k: 'skull', n: 2 }, { k: 'bones', n: 3 }, { k: 'throne', n: 1 }, { k: 'blood', n: 1 }, { k: 'chains', n: 1 }] },
  { look: 'crypt', sector: 'inside', name: "The Vampire Lord's Den", features: [{ k: 'coffin', n: 3 }, { k: 'brazier', n: 2 }, { k: 'throne', n: 1 }] },
  { look: 'field', sector: 'field', name: 'The Raven Camp', features: [{ k: 'tent', n: 3 }, { k: 'brazier', n: 1 }, { k: 'pole', n: 3 }, { k: 'stake', n: 5 }, { k: 'cairn', n: 2 }] },
];
const exitsSets = [ALL_WAYS, { north: ALL_WAYS.north, south: ALL_WAYS.south }, { east: ALL_WAYS.east, west: ALL_WAYS.west }, { north: ALL_WAYS.north, east: ALL_WAYS.east }];

function reach(L) {
  const seen = new Uint8Array(W * H);
  let start = -1;
  for (let i = 0; i < W * H && start < 0; i++) if (L.grid[i] === FLOOR && (i % W) === Math.floor(W / 2)) start = i;
  if (start < 0) return seen;
  const q = [start]; seen[start] = 1;
  while (q.length) {
    const i = q.shift(), x = i % W, y = (i / W) | 0;
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const xx = x + dx, yy = y + dy, j = yy * W + xx;
      if (xx < 0 || yy < 0 || xx >= W || yy >= H || seen[j] || L.grid[j] !== FLOOR) continue;
      seen[j] = 1; q.push(j);
    }
  }
  return seen;
}
function* rooms() {
  let vnum = 990100;
  for (const s of SETS) for (const exits of exitsSets) for (let k = 0; k < 6; k++) {
    yield { ...s, description: '', vnum: vnum++, exits, zone: 476 };
  }
}

test('features are placed, and no way out is shut by them', () => {
  let wanted = 0, placed = 0;
  for (const r of rooms()) {
    const L = MH.generateRoomTopDown(r);
    assert.ok(Array.isArray(L.features), 'the layout lists its features');
    wanted += r.features.reduce((a, f) => a + f.n, 0);
    placed += L.features.length;
    const seen = reach(L), g = L.gaps || {}, mx = Math.floor(W / 2), my = Math.floor(H / 2);
    const edge = (side) => {
      // some cell of the gap on that side is reached
      for (let d = -2; d <= 2; d++) {
        const i = side === 'north' ? mx + d : side === 'south' ? (H - 1) * W + mx + d : side === 'west' ? (my + d) * W : (my + d) * W + W - 1;
        if (seen[i]) return true;
      }
      return false;
    };
    for (const side of ['north', 'south', 'east', 'west']) if (g[side]) assert.ok(edge(side), `${r.name} ${r.vnum}: the ${side} way stays open`);
    for (const f of L.features) {
      for (let dy = 0; dy < f.h; dy++) for (let dx = 0; dx < f.w; dx++) {
        const i = (f.y + dy) * W + f.x + dx;
        if (f.block) assert.equal(L.grid[i], BLOCK, `${r.name}: a ${f.k} is solid to the walker`);
        assert.ok(f.x + dx > 0 && f.y + dy > 0 && f.x + dx < W - 1 && f.y + dy < H - 1, `${r.name}: a ${f.k} stands inside the room`);
      }
    }
  }
  assert.ok(placed >= wanted * 0.75, `most of what the words name is drawn (${placed} of ${wanted})`);
});

test("a room's centrepiece stands nearest the middle", () => {
  let nearer = 0, n = 0;
  for (const r of rooms()) {
    if (r.name !== 'At The Slaughter Stone') continue;
    const L = MH.generateRoomTopDown(r);
    const alt = L.features.filter(f => f.k === 'altar');
    const main = alt.find(f => f.main), other = alt.find(f => !f.main);
    if (!main || !other) continue;
    const d = f => Math.hypot(f.x + f.w / 2 - W / 2, f.y + f.h / 2 - H / 2);
    n++; nearer += d(main) <= d(other);
    assert.equal(alt.filter(f => f.main).length, 1, 'only one is the centrepiece');
  }
  assert.ok(n > 0 && nearer >= n * 0.75, `the main altar is the nearer the middle (${nearer} of ${n})`);
});

test('the colour said of a feature comes with it; a room without features has none', () => {
  const L = MH.generateRoomTopDown({ ...SETS[0], description: '', vnum: 990001, exits: ALL_WAYS, zone: 476 });
  assert.ok(L.features.some(f => f.k === 'standing_stone' && f.c === 'red'), 'the stone wrapped in red wool');
  const bare = MH.generateRoomTopDown({ look: 'field', sector: 'field', name: 'A Field', description: '', vnum: 990002, exits: ALL_WAYS, zone: 1 });
  assert.deepEqual(bare.features, []);
  assert.equal(MH.generateRoomTopDown({ ...SETS[0], vnum: 990003, exits: ALL_WAYS, zone: 476 }).theme, 'stones', 'the stone circle has its own look');
});
