// Stairs and passages in the 3D client (world3d/passages.js), checked against every real room.
//   node --test tests/web/
// For each room with stairs or portals: where you land is floor, reachable from the room's
// middle, beside the right stairs and outside their trigger; the gate keeps you from bouncing
// straight back; a click path only takes the stairs it was sent to.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import {
  sideKey, arrivalSpot, passageSpot, wantsPassage, PassageGate,
  TRIGGER_R, REARM_R, COOLDOWN_MS, IDLE_ARM_MS,
} from '../../src/web_isometric/world3d/passages.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const W = 24, H = 15, FLOOR = 0;

// the browser scripts that lay rooms out (roomgen) need a window and a little of the old client
globalThis.window = globalThis;
globalThis.document = { createElement: () => ({ getContext: () => null }) };
for (const f of ['world3d/hud-shim.js', 'platformer/themes-zones.js', 'platformer/roomgen.js']) {
  vm.runInThisContext(fs.readFileSync(path.join(ROOT, 'src/web_isometric', f), 'utf8'), { filename: f });
}
const MH = globalThis.MH;

function loadRooms() {
  const out = [];
  const dir = path.join(ROOT, 'world/zones');
  for (const f of fs.readdirSync(dir).filter(f => /^zone_.*\.json$/.test(f))) {
    const data = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
    const list = Array.isArray(data.rooms) ? data.rooms : Object.values(data.rooms || {});
    for (const r of list) if (r && r.vnum != null) out.push({ ...r, zone: data.number });
  }
  return out;
}
const layoutOf = r => {
  const exits = {};
  for (const [d, e] of Object.entries(r.exits || {})) if (e && !e.hidden && e.to_room != null) exits[d] = { to_room: e.to_room };
  return MH.generateRoomTopDown({ vnum: r.vnum, name: r.name, description: r.description || '', sector: r.sector_type,
    flags: r.flags || [], zone: r.zone, exits });
};
const floorAt = (L, x, z) => L.grid[Math.floor(z) * W + Math.floor(x)] === FLOOR;
function reachable(L, from, to) {
  const seen = new Set();
  const q = [[Math.floor(from.x), Math.floor(from.z)]];
  const goal = `${Math.floor(to.x)},${Math.floor(to.z)}`;
  while (q.length) {
    const [x, z] = q.shift();
    const k = `${x},${z}`;
    if (seen.has(k)) continue;
    seen.add(k);
    if (k === goal) return true;
    for (const [dx, dz] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const nx = x + dx, nz = z + dz;
      if (nx >= 0 && nz >= 0 && nx < W && nz < H && L.grid[nz * W + nx] !== 1) q.push([nx, nz]);
    }
  }
  return false;
}

test('up and down are named by direction of travel; the side you land on is the other', () => {
  assert.equal(sideKey('up'), 'down');
  assert.equal(sideKey('down'), 'up');
  assert.equal(sideKey('north'), 'north');
  assert.equal(sideKey('portal'), 'portal');
});

test('every stairs and portal room: you land on floor, beside the right stairs, outside their trigger', () => {
  const rooms = loadRooms().filter(r => Object.keys(r.exits || {}).some(d => !['north', 'south', 'east', 'west'].includes(d)));
  assert.ok(rooms.length > 300, `expected many stairs rooms, got ${rooms.length}`);
  const bad = [];
  for (const r of rooms) {
    const L = layoutOf(r);
    const middle = { x: W / 2, z: H / 2 };
    for (const side of Object.keys(r.exits)) {
      if (['north', 'south', 'east', 'west'].includes(side)) continue;
      const spot = passageSpot(L, side, W, H);
      const at = arrivalSpot(L, side, W, H);
      if (!floorAt(L, at.x, at.z)) { bad.push(`${r.vnum} ${side}: lands on a wall`); continue; }
      if (!reachable(L, at, middle)) { bad.push(`${r.vnum} ${side}: landing cut off`); continue; }
      if (!spot) continue;
      const d = Math.hypot(at.x - spot.x, at.z - spot.z);
      if (d > 2.2) bad.push(`${r.vnum} ${side}: lands ${d.toFixed(1)} m from its stairs`);
      if (d < TRIGGER_R + 0.5) bad.push(`${r.vnum} ${side}: lands inside the trigger (${d.toFixed(2)} m)`);
      // never next to the OTHER stairs (the mirrored-arrival bug)
      const other = side === 'up' ? passageSpot(L, 'down', W, H) : side === 'down' ? passageSpot(L, 'up', W, H) : null;
      if (other && Math.hypot(at.x - other.x, at.z - other.z) < d) bad.push(`${r.vnum} ${side}: lands nearer the other stairs`);
    }
  }
  assert.deepEqual(bad.slice(0, 15), [], `${bad.length} bad landings`);
});

test('the gate: arrive beside the stairs, a key held toward them does not hop back', () => {
  const g = new PassageGate();
  const spots = [{ key: 'up', x: 16.5, z: 4.5 }];
  const hero = { x: 14.9, z: 4.5 };            // landed 1.6 m west of the up stairs
  g.enterRoom(spots, hero);
  g.landed(1000);
  assert.equal(g.canFire('up', 1000 + COOLDOWN_MS + 10), false, 'disarmed while still beside it');
  // keep walking into it, never idle: stays quiet
  g.update(spots, { x: 15.8, z: 4.5 }, { idleMs: 0 });
  assert.equal(g.canFire('up', 5000), false);
  // stand still a moment: now it means it
  g.update(spots, { x: 15.8, z: 4.5 }, { idleMs: IDLE_ARM_MS + 1 });
  assert.equal(g.canFire('up', 5000), true);
});

test('the gate: walking away re-arms; the cooldown holds after landing; a click arms it', () => {
  const g = new PassageGate();
  const spots = [{ key: 'down', x: 7.5, z: 4.5 }, { key: 'up', x: 16.5, z: 4.5 }];
  g.enterRoom(spots, { x: 9.1, z: 4.5 });
  assert.equal(g.canFire('up', 0), true, 'far stairs stay armed');
  assert.equal(g.canFire('down', 0), false);
  g.update(spots, { x: 7.5 + REARM_R + 0.1, z: 4.5 }, { idleMs: 0 });
  assert.equal(g.canFire('down', 0), true);
  g.landed(100);
  assert.equal(g.canFire('down', 100 + COOLDOWN_MS - 1), false);
  assert.equal(g.canFire('down', 100 + COOLDOWN_MS + 1), true);
  g.disarm('up');
  g.update(spots, { x: 15, z: 4.5 }, { goal: 'up' });
  assert.equal(g.canFire('up', 9e9), true);
});

test('intent: keys moving onto the stairs fire; a path fires only for its goal; idle never', () => {
  assert.equal(wantsPassage({ d: 0.8, speed: 4, toward: 0.9, viaKeys: true }), true);
  assert.equal(wantsPassage({ d: 0.8, speed: 4, toward: -0.9, viaKeys: true }), false, 'walking away');
  assert.equal(wantsPassage({ d: 0.3, speed: 4, toward: -0.9, viaKeys: true }), true, 'right on top');
  assert.equal(wantsPassage({ d: 0.5, speed: 0.2, toward: 1, viaKeys: true }), false, 'barely moving');
  assert.equal(wantsPassage({ d: 0.5, speed: 4, toward: 1, viaPath: true, goal: false }), false, 'a path past the stairs');
  assert.equal(wantsPassage({ d: 0.5, speed: 4, toward: 1, viaPath: true, goal: true }), true, 'a click on the stairs');
  assert.equal(wantsPassage({ d: 0.5, speed: 4, toward: 1 }), false, 'chasing or sliding');
});
