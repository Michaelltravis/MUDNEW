// The continuous world: rooms placed on a grid of cells in one coordinate space.
// Room (cx, cy) covers x in [cx*24, cx*24+24), z in [cy*15, cy*15+15). Nothing ever
// re-origins; walking from one room into the next is just walking.
import * as THREE from 'three';
import { buildRoom, isIndoor, ROOM_W, ROOM_H } from './terrain.js';

const FLOOR = 0, BLOCK = 1, WATER = 4;
const LIGHTS = 6;   // real point lights, handed to the torches nearest the hero

export class World {
  constructor(engine, kits) {
    this.engine = engine;
    this.kits = kits;
    this.rooms = new Map();      // "cx,cy" -> room
    this.byVnum = new Map();
    this.torches = [];
    this.lights = [];
    for (let i = 0; i < LIGHTS; i++) {
      const l = new THREE.PointLight(0xff9a48, 0, 9, 1.6);
      l.userData.seed = Math.random() * 100;
      engine.scene.add(l);
      this.lights.push(l);
    }
    this._lightClock = 0;
  }

  addRoom(roomData, cx, cy) {
    const layout = MH.generateRoomTopDown(roomData);
    const ox = cx * ROOM_W, oz = cy * ROOM_H;
    const built = buildRoom(layout, ox, oz, this.kits);
    const room = { ...built, cx, cy, vnum: layout.vnum, name: roomData.name || '', indoor: isIndoor(layout.theme), theme: layout.theme };
    this.rooms.set(`${cx},${cy}`, room);
    this.byVnum.set(room.vnum, room);
    this.torches.push(...built.torches);
    this.engine.scene.add(built.group);
    return room;
  }

  roomAt(x, z) {
    return this.rooms.get(`${Math.floor(x / ROOM_W)},${Math.floor(z / ROOM_H)}`) || null;
  }

  tile(x, z) {
    const r = this.roomAt(x, z);
    if (!r) return BLOCK;
    const tx = Math.floor(x - r.ox), ty = Math.floor(z - r.oz);
    return r.layout.grid[ty * ROOM_W + tx];
  }

  blocked(x, z) { return this.tile(x, z) !== FLOOR; }

  centre(room) { return new THREE.Vector3(room.ox + ROOM_W / 2, 0, room.oz + ROOM_H / 2); }

  // torch light pool: the nearest torches get the real lights, with a little flicker
  update(dt, t, hero) {
    this._lightClock -= dt;
    if (this._lightClock <= 0) {
      this._lightClock = 0.25;
      const near = this.torches
        .map(p => ({ p, d: p.distanceToSquared(hero) }))
        .sort((a, b) => a.d - b.d).slice(0, LIGHTS);
      this.lights.forEach((l, i) => {
        const n = near[i];
        if (n && n.d < 30 * 30) { l.position.copy(n.p); l.userData.on = true; } else l.userData.on = false;
      });
    }
    for (const l of this.lights) {
      const s = l.userData.seed;
      const flick = 0.85 + Math.sin(t * 9.1 + s) * 0.06 + Math.sin(t * 23.7 + s * 2) * 0.05;
      const want = l.userData.on ? 26 * flick : 0;
      l.intensity += (want - l.intensity) * Math.min(1, dt * 8);
    }
  }
}
