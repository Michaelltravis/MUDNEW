// Death traps look like death in /play: the flag is read, the abyss is carved without cutting any
// way in off from another, and the hero is stopped at the edge (E dares it).
//   node --test tests/web/
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import { isDeadly, carveAbyss } from '../../src/web_isometric/world3d/deathlogic.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
globalThis.window = globalThis;
globalThis.document = globalThis.document || { createElement: () => ({ getContext: () => null }) };
for (const f of ['world3d/hud-shim.js', 'shared/themes-zones.js', 'shared/roomgen.js']) {
  vm.runInThisContext(fs.readFileSync(path.join(ROOT, 'src/web_isometric', f), 'utf8'), { filename: f });
}
const MH = globalThis.MH;
const W = 24, H = 15, BLOCK = 1;

function deathRooms() {
  const out = [];
  const dir = path.join(ROOT, 'world/zones');
  for (const f of fs.readdirSync(dir).filter(f => /^zone_.*\.json$/.test(f))) {
    const data = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
    const list = Array.isArray(data.rooms) ? data.rooms : Object.values(data.rooms || {});
    for (const r of list) if (r && isDeadly(r.flags)) out.push({ ...r, zone: data.number });
  }
  return out;
}

test('which rooms kill', () => {
  assert.ok(isDeadly(['deathtrap']) && isDeadly(['dark', 'death']));
  assert.ok(!isDeadly(['dark', 'indoors']) && !isDeadly(undefined) && !isDeadly([]));
  assert.ok(deathRooms().length >= 20, 'the world has its death traps');
});

test('the abyss never cuts one way in off from another', () => {
  const rooms = deathRooms();
  let carved = 0;
  for (const r of rooms) {
    const exits = {};
    for (const [d, e] of Object.entries(r.exits || {})) if (e && e.to_room != null) exits[d] = { to_room: e.to_room };
    const L = MH.generateRoomTopDown({ vnum: r.vnum, name: r.name, description: r.description || '', sector: r.sector_type,
      flags: r.flags, zone: r.zone, exits });
    const before = L.grid.filter(t => t === BLOCK).length;
    const rng = MH.mulberry32(r.vnum);
    const pts = carveAbyss(L, rng);
    if (pts) carved++;
    // flood from the first way in: every other way in (and the stairs) is reached
    const g = L.gaps || {}, mx = Math.floor(W / 2), my = Math.floor(H / 2);
    const want = [g.north && [mx, 0], g.south && [mx, H - 1], g.west && [0, my], g.east && [W - 1, my],
      L.stairsUp && [L.stairsUp.x, L.stairsUp.y], L.stairsDown && [L.stairsDown.x, L.stairsDown.y]].filter(Boolean);
    if (want.length < 2) continue;
    const seen = new Uint8Array(W * H), q = [want[0]];
    seen[want[0][1] * W + want[0][0]] = 1;
    while (q.length) {
      const [x, y] = q.pop();
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const xx = x + dx, yy = y + dy;
        if (xx < 0 || yy < 0 || xx >= W || yy >= H || seen[yy * W + xx] || L.grid[yy * W + xx] === BLOCK) continue;
        seen[yy * W + xx] = 1; q.push([xx, yy]);
      }
    }
    assert.ok(want.every(([x, y]) => seen[y * W + x]), `${r.vnum} ${r.name}: every way in still reaches every other`);
    if (pts) assert.ok(L.grid.filter(t => t === BLOCK).length > before, `${r.vnum}: the abyss is carved`);
  }
  assert.ok(carved >= rooms.length * 0.8, `most death traps get their abyss (${carved}/${rooms.length})`);
});

test('drawn in the room, stopped at the edge, red on the minimap', () => {
  const read = f => fs.readFileSync(path.join(ROOT, 'src/web_isometric/world3d', f), 'utf8');
  const terrain = read('terrain.js'), zone = read('zone.js'), main = read('main.js'), mini = read('hud/minimap.js');
  assert.match(terrain, /isDeadly\(.*\)\) deathTrap\(ctx\(\)\)/, 'terrain draws a death trap');
  assert.match(zone, /if \(this\.deadly\(r\)\) return true/, 'walking across into one is blocked');
  assert.match(zone, /blocked: 'deadly'/, 'and taking a passage into one');
  assert.match(main, /Certain death lies beyond/, 'the hero is told');
  assert.match(main, /zone\.dared\.add/, 'E dares it');
  assert.match(mini, /isDeadly\(r\.data\.flags\) \? DEADLY/, 'the minimap marks it');
});
