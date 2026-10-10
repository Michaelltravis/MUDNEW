// Monsters, NPCs and other players around the hero, from the near-mode map payload
// (`nearby` rooms, every mob with a stable id). Each stands on one of its room's spawn
// slots; when the server moves it to another room it walks there instead of popping.
// M1 uses the KayKit cast for people and undead and soft wisps for beasts; M2 maps every
// archetype to its own model.
import * as THREE from 'three';
import { spawnCharacter, spawnMob } from './assets.js';
import { beastLook } from './bestiary.js';
import { makeProc } from './proc.js';
import { isHostile } from './targeting.js';

const ANIMAL = /\b(rabbit|hare|fox|wolf|wolves|bear|deer|stag|elk|rat|rats|mouse|spider|snake|serpent|bat|bird|crow|raven|boar|cat|kitten|dog|hound|puppy|horse|pony|cow|bull|sheep|lamb|chicken|hen|rooster|frog|toad|lizard|beetle|ant|bee|wasp|scorpion|crab|fish|eel|squirrel|owl|hawk|eagle|goat|pig|hog|worm|slime|ooze|jelly|mosquito|fly|leech|badger|weasel|otter|duck|goose|swan|vulture|lion|tiger|panther|cougar|lynx|ape|monkey|gorilla|wyrm|drake|dragon|basilisk|griffon|unicorn|centipede|millipede|tick|moth|butterfly|cockroach)\b/;
const UNDEAD = /\b(skeleton|zombie|ghoul|undead|lich|wight|bone|bones|corpse|ghost|spectre|specter|wraith|mummy|revenant|banshee|shade|phantom|vampire)\b/;

export const CLASS_MODEL = {
  warrior: ['barbarian'], paladin: ['knight'], cleric: ['knight', 0xfff0d0], mage: ['mage'],
  necromancer: ['mage', 0x9a7ab8], thief: ['rogue'], assassin: ['rogue_hooded', 0x8a8a9a],
  ranger: ['rogue_hooded', 0xb8d8a8], bard: ['rogue', 0xe0b8e0],
};
export function classModel(cls) {
  const [model, tint] = CLASS_MODEL[String(cls || '').toLowerCase()] || ['knight'];
  return { model, tint };
}

// how high above its feet a creature's nameplate floats
function plateHeight(e) {
  const box = new THREE.Box3().setFromObject(e.root);
  const top = box.max.y - e.root.position.y;
  return Math.max(0.9, Math.min(4, isFinite(top) ? top + 0.35 : 2.75));
}

function hashStr(s) { let h = 2166136261; for (const ch of String(s)) h = Math.imul(h ^ ch.charCodeAt(0), 16777619); return h >>> 0; }

function mobLook(m) {
  const n = String(m.name || '').toLowerCase();
  const h = hashStr(m.id || n);
  const pick = list => list[h % list.length];
  const beast = beastLook(n);
  if (beast) return { beast };
  if (UNDEAD.test(n)) return { model: pick(['skeleton_warrior', 'skeleton_minion', 'skeleton_rogue', 'skeleton_mage']) };
  if (m.shopkeeper) return { model: 'barbarian', tint: 0xf0dcc0 };
  if (m.trainer) return { model: 'knight', tint: 0xf8f0e0 };
  if (/\b(guard|soldier|knight|captain|watch|sentry|warden|cityguard)\b/.test(n)) return { model: 'knight', tint: 0xc8d0e0 };
  if (/\b(mage|wizard|witch|priest|priestess|sage|cleric|monk|acolyte|shaman|druid|sorcer\w*|necromancer|apprentice)\b/.test(n)) return { model: 'mage', tint: pick([0xffffff, 0xd8c8f0, 0xc8e0d0]) };
  if (ANIMAL.test(n)) return { wisp: true };
  if (/\b(orc|orcs|half-orc|hobgoblin|bugbear|gnoll|kobold|bandit|brigand|thug|ruffian|raider|cultist)\b/.test(n))
    return { model: pick(['barbarian', 'rogue_hooded', 'rogue']), tint: pick([0x8fb07a, 0x9a8a7a, 0x8a7a9a]) };
  if (m.hostile) return { model: pick(['barbarian', 'rogue', 'rogue_hooded']), tint: pick([0x9ab88a, 0xb89a8a, 0x8a8aa8]) };
  return { model: pick(['rogue_hooded', 'rogue', 'barbarian', 'knight', 'mage']), tint: pick([0xe8e0d0, 0xd0c8b8, 0xc8d0d8, 0xe0d0c0]) };
}

const WISP_GEO = new THREE.SphereGeometry(0.28, 16, 12);
function makeWisp(hostile) {
  const g = new THREE.Group();
  const core = new THREE.Mesh(WISP_GEO, new THREE.MeshBasicMaterial({
    color: hostile ? new THREE.Color(2.2, 0.7, 0.4) : new THREE.Color(0.9, 1.8, 1.0) }));
  core.position.y = 0.9;
  g.add(core);
  const halo = new THREE.Mesh(WISP_GEO, new THREE.MeshBasicMaterial({
    color: hostile ? 0xff6a3a : 0x8affa8, transparent: true, opacity: 0.25, blending: THREE.AdditiveBlending, depthWrite: false }));
  halo.scale.setScalar(1.9);
  core.add(halo);
  g.userData.core = core;
  return g;
}

export class Entities {
  constructor(engine, plates) {
    this.engine = engine;
    this.plates = plates;          // DOM container for nameplates
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
        const from = this.zone.rooms.get(e.vnum), to = this.zone.rooms.get(w.vnum);
        e.vnum = w.vnum;
        e.goal = this.slot(w.vnum, key);
        // up the stairs or through a far passage: snap there with a puff of dust instead of
        // walking through walls and across the empty space between levels
        const joined = from && to && this.zone.openDir(from, to);
        if (e.root && e.goal && (!joined || e.root.position.distanceTo(e.goal) > 30)) {
          if (this.onSnap) this.onSnap(e.root.position.clone(), e.goal.clone());
          e.root.position.copy(e.goal).setY(e.root.position.y);
          e.goal = null;
        }
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
    const at = this.slot(w.vnum, key);
    if (!at) return;
    const e = { key, kind: w.kind, data: w.data, vnum: w.vnum, root: null, actor: null, goal: null, alive: true };
    this.list.set(key, e);
    e.plate = document.createElement('div');
    e.plate.className = 'plate ' + (w.kind === 'player' ? 'pl' : isHostile(w) ? 'hostile' : (w.data.shopkeeper || w.data.trainer) ? 'npc' : 'neutral');
    e.plate.innerHTML = '<span class="nm"></span><i class="hp"><b></b></i>';
    e.plate.querySelector('.nm').textContent = w.data.name;
    this.plates.appendChild(e.plate);
    const look = w.kind === 'player' ? classModel(w.data.char_class) : mobLook(w.data);
    const grow = w.data.boss ? 1.35 : 1;
    if (look.beast) {
      const b = look.beast;
      const ready = actor => {
        if (!e.alive) return;
        e.actor = actor;
        e.root = actor.root;
        e.fly = b.fly || 0;
        e.root.position.copy(at);
        e.root.rotation.y = (hashStr(key) % 628) / 100;
        actor.play(isHostile(w) ? 'Idle_Combat' : 'Idle', 0, 0.85 + (hashStr(key) % 30) / 100);
        this.engine.scene.add(e.root);
      };
      if (b.proc) ready(makeProc(b.proc, { height: b.h * grow, tint: b.tint, seed: hashStr(key) }));
      else spawnMob(b.mob, { height: b.h * grow, tint: b.tint }).then(ready).catch(() => {});
      return;
    }
    if (look.wisp) {
      e.root = makeWisp(isHostile(w));
      e.root.position.copy(at);
      this.engine.scene.add(e.root);
      return;
    }
    spawnCharacter(look.model, { tint: look.tint, scale: grow !== 1 ? grow : undefined }).then(actor => {
      if (!e.alive) return;
      e.actor = actor;
      e.root = actor.root;
      e.root.position.copy(at);
      e.root.rotation.y = (hashStr(key) % 628) / 100;
      actor.play(isHostile(w) ? 'Idle_Combat' : 'Idle', 0, 0.85 + (hashStr(key) % 30) / 100);
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
      // walking to a new room's spot
      if (e.goal) {
        const p = e.root.position, dx = e.goal.x - p.x, dz = e.goal.z - p.z, d = Math.hypot(dx, dz);
        if (d < 0.1) { e.goal = null; if (e.actor) e.actor.play(isHostile(e) ? 'Idle_Combat' : 'Idle'); }
        else {
          const step = Math.min(d, 3.2 * dt);
          p.x += dx / d * step; p.z += dz / d * step;
          e.root.rotation.y = Math.atan2(dx, dz);
          if (e.actor) e.actor.play('Walking_A', 0.15, 1.1);
        }
      }
      if (e.actor) e.actor.update(dt);
      else if (e.root.userData.core) e.root.userData.core.position.y = 0.9 + Math.sin(t * 2.4 + (hashStr(e.key) % 7)) * 0.12;
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
