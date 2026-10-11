// Passages: exits taken by stepping onto a marked spot instead of walking through a shared
// opening — stairs, named portals, and doorways whose rooms don't sit side by side. Pure logic
// (no THREE), so it runs in Node tests: where you land, when a passage may fire, and what
// counts as meaning to take it.
//
// Coordinates are room-local metres (x 0..W east, z 0..H south); L is a roomgen layout
// ({grid, gaps, stairsUp, stairsDown, portals, entries}, tiles of 1 m, entries in 1/16 m).
export const TRIGGER_R = 0.9;      // metres from a stairs/portal centre that count as "on it"
export const REARM_R = 1.9;        // a passage you arrived beside wakes once you are this far away
export const ARRIVE = 1.6;         // you land this far beside the stairs that lead back
export const COOLDOWN_MS = 1200;   // no passage fires this soon after landing
export const IDLE_ARM_MS = 250;    // ...or once you have stood still this long next to it
export const HOP_TIMEOUT_MS = 6000;
const FLOOR = 0;
const CARD = { north: [0, -1], south: [0, 1], east: [1, 0], west: [-1, 0] };

// up/down exits are named by the direction you travel; the side of the room you come out on
// is the other one: going up you arrive next to the destination's stairs back down
export function sideKey(dir) { return dir === 'up' ? 'down' : dir === 'down' ? 'up' : dir; }

// the centre of a passage: the stairs or portal tile, or the mouth of a doorway gap
export function passageSpot(L, dir, W, H) {
  if (dir === 'up' && L.stairsUp) return { x: L.stairsUp.x + 0.5, z: L.stairsUp.y + 0.5 };
  if (dir === 'down' && L.stairsDown) return { x: L.stairsDown.x + 0.5, z: L.stairsDown.y + 0.5 };
  const pt = (L.portals || []).find(q => q.name === dir);
  if (pt) return { x: pt.x + 0.5, z: pt.y + 0.5 };
  const g = L.gaps && L.gaps[dir];
  if (g && CARD[dir]) {
    const horiz = dir === 'north' || dir === 'south';
    const mid = horiz ? (g.x0 + g.x1 + 1) / 2 : (g.y0 + g.y1 + 1) / 2;
    return horiz ? { x: mid, z: dir === 'north' ? 0.6 : H - 0.6 } : { x: dir === 'west' ? 0.6 : W - 0.6, z: mid };
  }
  return null;
}

// is this tile spot (stairs, portal) one the hero steps onto rather than through?
export function isSpotPassage(dir) { return !CARD[dir]; }

const floorAt = (L, W, H, x, z) => {
  const tx = Math.floor(x), tz = Math.floor(z);
  return tx >= 0 && tz >= 0 && tx < W && tz < H && L.grid[tz * W + tx] === FLOOR;
};

// where the hero lands in a room entered on its `side` ('down' = beside the stairs going back
// down, 'north' = in the north doorway, a portal name = beside that portal)
export function arrivalSpot(L, side, W, H) {
  if (!CARD[side]) {
    const s = passageSpot(L, side, W, H);
    if (s) {
      const order = side === 'up' ? [[-1, 0], [1, 0], [0, 1], [0, -1]]
        : side === 'down' ? [[1, 0], [-1, 0], [0, 1], [0, -1]] : [[0, -1], [0, 1], [1, 0], [-1, 0]];
      for (const [dx, dz] of order) {
        const x = s.x + dx * ARRIVE, z = s.z + dz * ARRIVE;
        if (floorAt(L, W, H, x, z)) return { x, z };
      }
    }
  }
  // roomgen's own entries: compass keys are the side, up/down the direction of travel
  const key = side === 'up' ? 'down' : side === 'down' ? 'up' : side;
  const e = L.entries && (L.entries[key] || L.entries.none);
  return e ? { x: e.x / 16, z: e.y / 16 } : { x: W / 2, z: H / 2 };
}

// does the hero mean to take this passage now?
//  keys: moving onto the stairs (or standing right on them while moving);
//  a click path: only the stairs it was sent to; idle, sliding or chasing a foe: never
export function wantsPassage({ d, speed, toward, viaKeys, viaPath, goal }) {
  if (viaPath) return !!goal && d < TRIGGER_R;
  if (!viaKeys || speed <= 0.5) return false;
  return (d < TRIGGER_R && toward > 0.3) || d < 0.35;
}

// Passages you are standing next to when you arrive stay quiet until you mean them: walk
// away and come back, stand still a moment, or click them. Plus a short cooldown after any
// landing, so holding a key into the stairs never ping-pongs between two rooms.
export class PassageGate {
  constructor() { this.disarmed = new Set(); this.until = 0; }
  enterRoom(spots, hero) {
    this.disarmed.clear();
    for (const s of spots) if (Math.hypot(s.x - hero.x, s.z - hero.z) < REARM_R) this.disarmed.add(s.key);
  }
  update(spots, hero, { idleMs = 0, goal = null } = {}) {
    if (!this.disarmed.size) return;
    for (const s of spots) {
      if (!this.disarmed.has(s.key)) continue;
      if (Math.hypot(s.x - hero.x, s.z - hero.z) >= REARM_R || idleMs >= IDLE_ARM_MS || goal === s.key) this.disarmed.delete(s.key);
    }
  }
  canFire(key, now) { return now >= this.until && !this.disarmed.has(key); }
  landed(now) { this.until = now + COOLDOWN_MS; }
  disarm(key) { this.disarmed.add(key); }
}
