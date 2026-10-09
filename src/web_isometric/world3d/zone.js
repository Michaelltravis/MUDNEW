// A whole zone as one continuous space (from the server's /zonemap). Room (cx, cy) covers
// x in [cx*24, cx*24+24), z in [cy*15, cy*15+15). Rooms are laid out lazily, built as meshes
// near the hero and released far away; walking between rooms is just walking. A step into
// another room is legal only through an 'open' exit (mutual + adjacent, door not closed);
// every other exit is a marked passage that triggers a short hop.
import * as THREE from 'three';
import { buildRoom, ROOM_W, ROOM_H, isIndoor } from './terrain.js';

const FLOOR = 0, BLOCK = 1, WATER = 4;
const LIGHTS = 6;
export const REV = { north: 'south', south: 'north', east: 'west', west: 'east', up: 'down', down: 'up' };
const CARD = { north: [0, -1], south: [0, 1], east: [1, 0], west: [-1, 0] };

export async function fetchZonemap(query) {
  const res = await fetch(`/zonemap?${query}`);
  if (!res.ok) throw new Error(`zone map ${query}: ${res.status}`);
  return res.json();
}

export class Zone {
  constructor(engine, kits, zm) {
    this.engine = engine;
    this.kits = kits;
    this.zm = zm;
    this.num = zm.zone;
    this.name = zm.name;
    this.rooms = new Map();
    this.cells = new Map();
    for (const r of zm.rooms) {
      const room = {
        data: r, vnum: r.vnum, name: r.name, cx: r.cell[0], cy: r.cell[1],
        ox: r.cell[0] * ROOM_W, oz: r.cell[1] * ROOM_H, layout: null, built: null, doors: {},
        zoneRef: this,
      };
      for (const [d, e] of Object.entries(r.exits)) if (e.door) room.doors[d] = { ...e.door };
      this.rooms.set(r.vnum, room);
      this.cells.set(`${room.cx},${room.cy}`, room);
    }
    this.group = new THREE.Group();
    this.group.name = `zone_${this.num}`;
    engine.scene.add(this.group);
    this.lights = [];
    for (let i = 0; i < LIGHTS; i++) {
      const l = new THREE.PointLight(0xff9a48, 0, 9, 1.6);
      l.userData.seed = Math.random() * 100;
      this.group.add(l);
      this.lights.push(l);
    }
    this._lightClock = 0;
    this._releaseClock = 0;
  }

  // ---- geometry queries ----
  roomAt(x, z) { return this.cells.get(`${Math.floor(x / ROOM_W)},${Math.floor(z / ROOM_H)}`) || null; }
  centre(room) { return new THREE.Vector3(room.ox + ROOM_W / 2, 0, room.oz + ROOM_H / 2); }

  layoutOf(room) {
    if (!room.layout) {
      const r = room.data;
      const exits = {};
      for (const [d, e] of Object.entries(r.exits)) exits[d] = { to_room: e.to };
      room.layout = MH.generateRoomTopDown({
        vnum: r.vnum, name: r.name, description: r.description, sector: r.sector,
        flags: r.flags, zone: this.num, exits,
      });
    }
    return room.layout;
  }

  // where the hero appears in a room when arriving by `dir` (the gap on that side)
  entry(room, fromDir) {
    const L = this.layoutOf(room);
    const e = (fromDir && L.entries[fromDir]) || L.entries.none;
    return new THREE.Vector3(room.ox + e.x / 16, 0, room.oz + e.y / 16);
  }

  tile(room, x, z) {
    const tx = Math.floor(x - room.ox), ty = Math.floor(z - room.oz);
    if (tx < 0 || ty < 0 || tx >= ROOM_W || ty >= ROOM_H) return BLOCK;
    return this.layoutOf(room).grid[ty * ROOM_W + tx];
  }

  openDir(a, b) {
    for (const [d, e] of Object.entries(a.data.exits)) if (e.kind === 'open' && e.to === b.vnum) return d;
    return null;
  }
  doorClosed(room, dir) { const d = room.doors[dir]; return !!(d && d.closed); }

  // can the hero's body stand at (x, z), coming from room `from`?
  blocked(x, z, from) {
    const r = this.roomAt(x, z);
    if (!r) return true;
    if (from && r !== from) {
      const d = this.openDir(from, r);
      if (!d || this.doorClosed(from, d) || this.doorClosed(r, REV[d])) return true;
    }
    const t = this.tile(r, x, z);
    if (t === BLOCK) return true;
    return t === WATER && !this.layoutOf(r).swim;
  }

  // ---- passages: exits that are not a shared opening ----
  // Returns {dir, exit} when the hero at p (moving with velocity v) is stepping into one.
  passageAt(room, p, v) {
    const L = this.layoutOf(room);
    const lx = p.x - room.ox, lz = p.z - room.oz;
    for (const [d, e] of Object.entries(room.data.exits)) {
      if (e.kind === 'open') continue;
      if (CARD[d]) {
        const g = L.gaps[d];
        if (!g) continue;
        const [dx, dz] = CARD[d];
        const out = v.x * dx + v.y * dz;              // pushing outward through the gap
        const inSpan = dx ? (lz >= g.y0 && lz <= g.y1 + 1) : (lx >= g.x0 && lx <= g.x1 + 1);
        const nearEdge = dx > 0 ? lx > ROOM_W - 1.25 : dx < 0 ? lx < 1.25 : dz > 0 ? lz > ROOM_H - 1.25 : lz < 1.25;
        if (inSpan && nearEdge && out > 0.5) return { dir: d, exit: e };
      } else {
        // stairs and named portals are tiles inside the room
        const t = d === 'up' ? L.stairsUp : d === 'down' ? L.stairsDown : (L.portals || []).find(q => q.name === d);
        if (t && Math.hypot(lx - (t.x + 0.5), lz - (t.y + 0.5)) < 0.85) return { dir: d, exit: e };
      }
    }
    return null;
  }

  // the matching side of a passage in the destination room
  arrival(room, fromRoom, dir) {
    const back = REV[dir];
    const L = this.layoutOf(room);
    if (back && room.data.exits[back] && room.data.exits[back].to === fromRoom.vnum) {
      if (CARD[back]) return this.entry(room, back);
      const t = back === 'up' ? L.stairsUp : back === 'down' ? L.stairsDown : null;
      if (t) return new THREE.Vector3(room.ox + t.x + 0.5 + (back === 'up' ? -1.4 : 1.4), 0, room.oz + t.y + 0.5);
    }
    return this.entry(room, null);
  }

  // ---- streaming ----
  build(room) {
    if (room.built) return;
    room.built = buildRoom(this.layoutOf(room), room.ox, room.oz, this.kits, room);
    this.group.add(room.built.group);
  }
  release(room) {
    if (!room.built) return;
    this.group.remove(room.built.group);
    for (const g of room.built.owned || []) g.dispose();
    room.built = null;
  }
  prebuild(room, radius = 1) {
    for (let dy = -radius; dy <= radius; dy++) for (let dx = -radius; dx <= radius; dx++) {
      const r = this.cells.get(`${room.cx + dx},${room.cy + dy}`);
      if (r) this.build(r);
    }
  }

  update(dt, t, hero, vel) {
    const cx = Math.floor(hero.x / ROOM_W), cy = Math.floor(hero.z / ROOM_H);
    // one room per frame within 2 cells, nearest first, ahead of the hero first
    let best = null, bestD = Infinity;
    for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) {
      const r = this.cells.get(`${cx + dx},${cy + dy}`);
      if (!r || r.built) continue;
      const d = dx * dx + dy * dy - 0.6 * Math.sign(dx * (vel ? vel.x : 0) + dy * (vel ? vel.y : 0));
      if (d < bestD) { bestD = d; best = r; }
    }
    if (best) this.build(best);
    if ((this._releaseClock -= dt) <= 0) {
      this._releaseClock = 1;
      for (const r of this.rooms.values()) if (r.built && (Math.abs(r.cx - cx) > 4 || Math.abs(r.cy - cy) > 4)) this.release(r);
    }
    this.updateLights(dt, t, hero);
  }

  updateLights(dt, t, hero) {
    if ((this._lightClock -= dt) <= 0) {
      this._lightClock = 0.25;
      const all = [];
      for (const r of this.rooms.values()) if (r.built) for (const p of r.built.torches) all.push(p);
      all.sort((a, b) => a.distanceToSquared(hero) - b.distanceToSquared(hero));
      this.lights.forEach((l, i) => {
        const p = all[i];
        if (p && p.distanceToSquared(hero) < 30 * 30) { l.position.copy(p); l.userData.on = true; } else l.userData.on = false;
      });
    }
    for (const l of this.lights) {
      const s = l.userData.seed;
      const flick = 0.85 + Math.sin(t * 9.1 + s) * 0.06 + Math.sin(t * 23.7 + s * 2) * 0.05;
      const want = l.userData.on ? 26 * flick : 0;
      l.intensity += (want - l.intensity) * Math.min(1, dt * 8);
    }
  }

  // live door state from map_data ({state: 'open'|'closed', locked})
  setDoor(room, dir, info) {
    const d = room.doors[dir];
    if (!d || !info) return;
    d.closed = info.state === 'closed';
    d.locked = !!info.locked;
    const mesh = room.built && room.built.doors && room.built.doors[dir];
    if (mesh) mesh.userData.setOpen(!d.closed);
  }

  indoor(room) { return isIndoor(this.layoutOf(room).theme); }

  dispose() {
    for (const r of this.rooms.values()) this.release(r);
    this.engine.scene.remove(this.group);
  }

  // ---- room graph path (for click-to-travel on the minimap) ----
  // Rooms joined by open exits only: walking carries the hero there for real.
  roomPath(from, to) {
    const prev = new Map([[from.vnum, null]]);
    const q = [from];
    while (q.length) {
      const r = q.shift();
      if (r === to) break;
      for (const e of Object.values(r.data.exits)) {
        if (e.kind !== 'open' || prev.has(e.to)) continue;
        const n = this.rooms.get(e.to);
        if (!n) continue;
        prev.set(e.to, r);
        q.push(n);
      }
    }
    if (!prev.has(to.vnum)) return null;
    const path = [];
    for (let r = to; r; r = prev.get(r.vnum)) path.unshift(r);
    return path;
  }
}
