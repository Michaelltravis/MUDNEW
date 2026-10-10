// Monsters, NPCs and other players around the hero, from the near-mode map payload
// (`nearby` rooms, every mob with a stable id). Each stands on one of its room's spawn
// slots; when the server moves it to another room it walks there instead of popping.
// Which body each creature gets is decided in looks.js.
import * as THREE from 'three';
import { spawnCharacter, spawnMob } from './assets.js';
import { creatureLook, hashStr } from './looks.js';
import { makeProc, makeProp } from './proc.js';
import { isHostile } from './targeting.js';

export const CLASS_MODEL = {
  warrior: ['barbarian'], paladin: ['knight'], cleric: ['knight', 0xfff0d0], mage: ['mage'],
  necromancer: ['mage', 0x9a7ab8], thief: ['rogue'], assassin: ['rogue_hooded', 0x8a8a9a],
  ranger: ['rogue_hooded', 0xb8d8a8], bard: ['rogue', 0xe0b8e0],
};
export function classModel(cls) {
  const [model, tint] = CLASS_MODEL[String(cls || '').toLowerCase()] || ['knight'];
  return { model, tint };
}

// the body for a look (looks.js): a creature model, a procedural body, a kit prop or a person
export function spawnLook(look, { kits = null, seed = 0 } = {}) {
  const b = look.beast;
  if (!b) return spawnCharacter(look.model, { tint: look.tint, scale: look.scale, loadout: look.loadout, flat: look.flat });
  if (b.proc) return Promise.resolve(makeProc(b.proc, { height: b.h, tint: b.tint, seed }));
  if (b.prop) {
    const model = kits && kits[b.prop[0]] && kits[b.prop[0]].get(b.prop[1]);
    return Promise.resolve(model ? makeProp(model, { size: b.h, tint: b.tint }) : makeProc('slime', { height: 0.8, seed }));
  }
  return spawnMob(b.mob, { height: b.h, tint: b.tint });
}

// how high above its feet a creature's nameplate floats
function plateHeight(e) {
  const box = new THREE.Box3().setFromObject(e.root);
  const top = box.max.y - e.root.position.y;
  return Math.max(0.9, Math.min(4, isFinite(top) ? top + 0.35 : 2.75));
}

export class Entities {
  constructor(engine, plates, kits = null) {
    this.engine = engine;
    this.plates = plates;          // DOM container for nameplates
    this.kits = kits;              // static models, for creatures that are props (a mimic)
    this.zone = null;
    this.list = new Map();         // key -> entity
    this.target = null;            // key of the selected entity
    this.dying = [];               // fallen creatures, removed after their death animation
    this.hero = null;              // hero position (combat facing)
    this._v = new THREE.Vector3();
  }

  setZone(zone) {
    for (const e of this.list.values()) this.remove(e, true);
    this.list.clear();
    this.zone = zone;
  }

  slot(roomVnum, key) {
    const room = this.zone && this.zone.rooms.get(roomVnum);
    if (!room) return null;
    const L = this.zone.layoutOf(room);
    const h = hashStr(key);
    const s = L.spawnSlots[h % L.spawnSlots.length];
    const jx = ((h >>> 8) % 100) / 100 - 0.5, jz = ((h >>> 16) % 100) / 100 - 0.5;
    return new THREE.Vector3(room.ox + s.x / 16 + jx * 0.8, 0, room.oz + s.y / 16 + jz * 0.8);
  }

  // a server position (room-local metres) for a creature in a fight: walk it there
  place(e, m) {
    if (m.x == null || m.z == null || !this.zone) return;
    const room = this.zone.rooms.get(e.vnum);
    if (!room) return;
    const goal = new THREE.Vector3(room.ox + m.x, 0, room.oz + m.z);
    if (!e.root || e.root.position.distanceTo(goal) > 0.15) e.goal = goal;
  }

  // a creature or player changed rooms: walk there if the rooms open onto each other, else
  // snap there (stairs, a far passage, recall, a portal) with a puff of dust
  moveTo(e, vnum) {
    const from = this.zone.rooms.get(e.vnum), to = this.zone.rooms.get(vnum);
    e.vnum = vnum;
    e.goal = this.slot(vnum, e.key);
    const joined = from && to && this.zone.openDir(from, to);
    if (e.root && e.goal && (!joined || e.root.position.distanceTo(e.goal) > 30)) {
      if (this.onSnap) this.onSnap(e.root.position.clone(), e.goal.clone());
      e.root.position.copy(e.goal).setY(e.root.position.y);
      e.goal = null;
    }
  }

  // another web player's position, relayed by the server: their hero follows it
  presence({ name, vnum, x, z }) {
    const e = name && this.list.get(`p${name}`);
    if (!e || !this.zone || !this.zone.rooms.get(vnum)) return;   // not drawn yet: the next payload brings them
    if (e.vnum !== vnum) this.moveTo(e, vnum);
    e.data.x = x; e.data.z = z;
    this.place(e, e.data);
  }

  // another player changed rooms some other way (recall, a portal, following a leader)
  playerMoved({ name, to }) {
    const e = this.list.get(`p${name}`);
    if (!e || !this.zone) return;
    if (!this.zone.rooms.get(to)) { this.remove(e, true); return; }   // out of this zone: gone from view
    if (e.vnum !== to) this.moveTo(e, to);
  }

  // payload.nearby: [{vnum, mobs, players, doors, items}]
  sync(payload, selfName) {
    // a payload without `nearby` (an older /state reply) says nothing about who is around:
    // keep what we have instead of clearing the world
    if (!this.zone || !payload || !Array.isArray(payload.nearby)) return;
    const want = new Map();
    for (const r of payload.nearby || []) {
      const room = this.zone.rooms.get(r.vnum);
      if (!room) continue;
      for (const [dir, info] of Object.entries(r.doors || {})) this.zone.setDoor(room, dir, info);
      for (const m of r.mobs || []) want.set(`m${m.id}`, { kind: 'mob', data: m, vnum: r.vnum });
      for (const p of r.players || []) if (p.name !== selfName) want.set(`p${p.name}`, { kind: 'player', data: p, vnum: r.vnum });
    }
    for (const [key, e] of this.list) if (!want.has(key)) this.remove(e);
    for (const [key, w] of want) {
      const e = this.list.get(key);
      if (!e) { this.create(key, w); continue; }
      e.data = w.data;
      this.markHostile(e);
      if (e.vnum !== w.vnum) {
        this.moveTo(e, w.vnum);
        if (w.data.x != null) this.place(e, w.data);
      } else this.place(e, w.data);
    }
  }

  // per-round vitals for the hero's room (combat_update)
  combat(payload) {
    for (const m of payload.mobs || []) {
      const e = m.id != null ? this.list.get(`m${m.id}`) : null;
      if (!e) continue;
      Object.assign(e.data, m);
      this.place(e, m);
      if (m.fighting && e.actor && e.root && this.hero) {
        e.root.rotation.y = Math.atan2(this.hero.x - e.root.position.x, this.hero.z - e.root.position.z);
        e.actor.once(['1H_Melee_Attack_Chop', '1H_Melee_Attack_Slice_Diagonal', '1H_Melee_Attack_Stab'][(hashStr(e.key) + Date.now()) % 3], 0.08, 1.1);
      }
    }
  }

  create(key, w) {
    // where the server says it stands (a web player, a creature in a fight), else a spawn slot
    const room = this.zone && this.zone.rooms.get(w.vnum);
    const at = room && w.data.x != null && w.data.z != null ? new THREE.Vector3(room.ox + w.data.x, 0, room.oz + w.data.z) : this.slot(w.vnum, key);
    if (!at) return;
    const e = { key, kind: w.kind, data: w.data, vnum: w.vnum, root: null, actor: null, goal: null, alive: true };
    this.list.set(key, e);
    e.plate = document.createElement('div');
    e.plate.className = 'plate ' + (w.kind === 'player' ? 'pl' : isHostile(w) ? 'hostile' : (w.data.shopkeeper || w.data.trainer) ? 'npc' : 'neutral');
    e.plate.innerHTML = '<span class="nm"></span><i class="hp"><b></b></i>';
    e.plate.querySelector('.nm').textContent = w.data.name;
    this.plates.appendChild(e.plate);
    const look = w.kind === 'player' ? classModel(w.data.char_class) : creatureLook(w.data);
    e.look = look;
    e.fly = (look.beast ? look.beast.fly : look.fly) || 0;
    e.still = !!look.still;        // a statue: no breathing while it stands guard
    spawnLook(look, { kits: this.kits, seed: hashStr(key) }).then(actor => {
      if (!e.alive) return;
      e.actor = actor;
      e.root = actor.root;
      e.root.position.copy(at);
      e.root.rotation.y = (hashStr(key) % 628) / 100;
      actor.play(isHostile(w) ? 'Idle_Combat' : 'Idle', 0, e.still ? 0 : 0.85 + (hashStr(key) % 30) / 100);
      this.engine.scene.add(e.root);
    }).catch(() => {});
  }

  remove(e, now) {
    e.alive = false;
    if (e.plate) e.plate.remove();
    if (this.target === e.key) this.setTarget(null);
    this.list.delete(e.key);
    if (!e.root) return;
    // a creature that was fighting or out of health died: let it fall, then clear it away
    const died = !now && e.actor && e.kind === 'mob' && ((e.data.maxHp && e.data.hp <= 0) || e.data.fighting);
    if (!died) { this.engine.scene.remove(e.root); return; }
    e.actor.once('Death_A', 0.1, 1);
    e.actor.play('Death_A');
    this.dying.push({ e, left: 2.2 });
  }

  // a creature that turns on you gets a hostile (red) nameplate
  markHostile(e) {
    if (!e || !e.plate || e.kind !== 'mob') return;
    const h = isHostile(e);
    e.plate.classList.toggle('hostile', h);
    if (h) e.plate.classList.remove('neutral');
  }

  // byHand: the player chose it (a click, Tab): auto-targeting leaves it alone a moment
  setTarget(key, { byHand = false } = {}) {
    const prev = this.target && this.list.get(this.target);
    if (prev && prev.plate) prev.plate.classList.remove('targeted');
    this.target = key;
    const e = key && this.list.get(key);
    if (e && byHand) e.pickedAt = Date.now();
    if (e && e.plate) e.plate.classList.add('targeted');
    MH.bus.emit(e ? 'target.set' : 'target.clear', e ? { key, kind: e.kind, ...e.data, vnum: e.vnum } : null);
  }

  get targeted() { return this.target ? this.list.get(this.target) || null : null; }

  // nearest entity to a screen point (page px), for click-to-target
  pick(px, py, maxPx = 42) {
    const cam = this.engine.camera, cv = this.engine.renderer.domElement.getBoundingClientRect();
    let best = null, bestD = maxPx;
    for (const e of this.list.values()) {
      if (!e.root) continue;
      this._v.copy(e.root.position).setY(1.1).project(cam);
      if (this._v.z > 1) continue;
      const sx = cv.left + (this._v.x + 1) / 2 * cv.width, sy = cv.top + (1 - this._v.y) / 2 * cv.height;
      const d = Math.hypot(sx - px, sy - py);
      if (d < bestD) { bestD = d; best = e; }
    }
    return best;
  }

  update(dt, t, hero) {
    this.hero = hero;
    for (let i = this.dying.length - 1; i >= 0; i--) {
      const d = this.dying[i];
      d.e.actor.update(dt);
      if ((d.left -= dt) <= 0) { this.engine.scene.remove(d.e.root); this.dying.splice(i, 1); }
    }
    for (const e of this.list.values()) {
      if (!e.root) continue;
      // walking to a new room's spot (other players keep up with where they really are:
      // the further behind, the faster they run)
      if (e.goal) {
        const p = e.root.position, dx = e.goal.x - p.x, dz = e.goal.z - p.z, d = Math.hypot(dx, dz);
        if (d < 0.1) { e.goal = null; if (e.actor) e.actor.play(isHostile(e) ? 'Idle_Combat' : 'Idle', 0.18, e.still ? 0 : 1); }
        else {
          const speed = e.kind === 'player' ? Math.min(9, Math.max(3.2, d * 4)) : 3.2;
          const step = Math.min(d, speed * dt);
          p.x += dx / d * step; p.z += dz / d * step;
          e.root.rotation.y = Math.atan2(dx, dz);
          if (e.actor) e.actor.play(speed > 4.5 ? 'Running_A' : 'Walking_A', 0.15, 1.1);
        }
      }
      if (e.actor) e.actor.update(dt);
      if (e.fly) e.root.position.y = e.fly + Math.sin(t * 2.1 + (hashStr(e.key) % 9)) * 0.12;
    }
  }

  // nameplates, once the camera is placed for this frame (engine late tick)
  layoutPlates(hero) {
    if (!hero) return;
    const cam = this.engine.camera, cv = this.engine.renderer.domElement;
    const w = cv.clientWidth, h = cv.clientHeight;
    for (const e of this.list.values()) {
      if (!e.root) continue;
      const dist = e.root.position.distanceTo(hero);
      const show = dist < 26 || this.target === e.key;
      if (!show) { e.plate.style.display = 'none'; continue; }
      this._v.copy(e.root.position).setY(e.root.position.y + (e.plateY || (e.plateY = plateHeight(e)))).project(cam);
      if (this._v.z > 1 || Math.abs(this._v.x) > 1.1 || Math.abs(this._v.y) > 1.1) { e.plate.style.display = 'none'; continue; }
      e.plate.style.display = '';
      e.plate.style.transform = `translate(${((this._v.x + 1) / 2 * w).toFixed(1)}px, ${((1 - this._v.y) / 2 * h).toFixed(1)}px) translate(-50%, -100%)`;
      const hp = e.data.maxHp ? e.data.hp / e.data.maxHp : 1;
      e.plate.classList.toggle('hurt', hp < 0.999);
      e.plate.querySelector('.hp b').style.width = `${Math.max(0, Math.min(1, hp)) * 100}%`;
      e.plate.style.opacity = this.target === e.key ? 1 : Math.max(0.25, Math.min(1, (28 - dist) / 8));
    }
  }
}
