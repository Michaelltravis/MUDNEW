// The fight, on screen. The server sends one structured event for every swing, hit, miss,
// defence, cast, heal, death and wind-up, from the same code that prints the combat log, so
// each line you read has its animation: the attacker winds up and swings (or draws, or
// casts), the blow or bolt travels, the target flinches, blocks or sidesteps, a number
// rises. Ranges and positions come with the events (combat v2: distance matters).
import * as THREE from 'three';

// how each ability looks: the user's animation, what flies, how it lands
// kind: melee | shot | bolt | beam | pillar | nova | heal | buff | summon | cone
export const ABILITY_FX = {
  // warrior
  bash: { anim: 'Block_Attack', kind: 'melee', school: 'physical', heavy: true, stun: true },
  cleave: { anim: '2H_Melee_Attack_Spin', kind: 'melee', school: 'physical', wide: true },
  kick: { anim: 'Unarmed_Melee_Attack_Kick', kind: 'melee', school: 'physical' },
  execute: { anim: '2H_Melee_Attack_Chop', kind: 'melee', school: 'blood', heavy: true },
  rally: { anim: 'Cheer', kind: 'nova', school: 'holy', radius: 8 },
  rescue: { anim: 'Block', kind: 'buff', school: 'physical' },
  charge: { anim: '1H_Melee_Attack_Jump_Chop', kind: 'dash', school: 'physical', heavy: true },
  // paladin
  censure: { anim: '1H_Melee_Attack_Slice_Diagonal', kind: 'melee', school: 'holy' },
  order_verdict: { anim: '1H_Melee_Attack_Chop', kind: 'melee', school: 'holy', heavy: true },
  holy_smite: { anim: 'Spellcast_Raise', kind: 'pillar', school: 'holy' },
  absolution: { anim: 'Spellcast_Long', kind: 'heal', school: 'holy' },
  halo_of_reckoning: { anim: 'Spellcast_Raise', kind: 'nova', school: 'holy', radius: 5 },
  turn_undead: { anim: 'Spellcast_Long', kind: 'cone', school: 'holy', radius: 8 },
  // ranger
  truesight_shot: { anim: '1H_Ranged_Shoot', kind: 'shot', school: 'physical' },
  wildbond_strike: { anim: '1H_Melee_Attack_Slice_Horizontal', kind: 'melee', school: 'nature' },
  loosing_storm: { anim: '1H_Ranged_Shoot', kind: 'volley', school: 'physical', radius: 3.5 },
  quarry_mark: { anim: '1H_Ranged_Aiming', kind: 'mark', school: 'nature' },
  call_lightning: { anim: 'Spellcast_Raise', kind: 'beam', school: 'lightning', sky: true },
  // thief / assassin
  backstab: { anim: 'Dualwield_Melee_Attack_Stab', kind: 'melee', school: 'blood', heavy: true },
  circle: { anim: 'Dualwield_Melee_Attack_Slice', kind: 'melee', school: 'blood' },
  trip: { anim: 'Unarmed_Melee_Attack_Kick', kind: 'melee', school: 'physical', stun: true },
  low_blow: { anim: 'Unarmed_Melee_Attack_Punch_A', kind: 'melee', school: 'physical', stun: true },
  pocket_sand: { anim: 'Throw', kind: 'cloud', school: 'physical' },
  jackpot: { anim: 'Dualwield_Melee_Attack_Chop', kind: 'melee', school: 'holy', heavy: true },
  mark: { anim: 'Throw', kind: 'mark', school: 'shadow' },
  expose: { anim: 'Dualwield_Melee_Attack_Slice', kind: 'melee', school: 'shadow' },
  vital: { anim: 'Dualwield_Melee_Attack_Stab', kind: 'melee', school: 'blood', heavy: true },
  feint: { anim: 'Dodge_Left', kind: 'melee', school: 'shadow' },
  execute_contract: { anim: 'Dualwield_Melee_Attack_Chop', kind: 'melee', school: 'shadow', heavy: true },
  fade: { anim: 'Dodge_Backward', kind: 'buff', school: 'shadow' },
  // mage
  magic_missile: { anim: 'Spellcast_Shoot', kind: 'bolt', school: 'arcane', count: 3 },
  fireball: { anim: 'Spellcast_Shoot', kind: 'bolt', school: 'fire', heavy: true, radius: 3, size: 0.38 },
  lightning_bolt: { anim: 'Spellcast_Shoot', kind: 'beam', school: 'lightning' },
  chill_touch: { anim: '1H_Melee_Attack_Stab', kind: 'melee', school: 'frost' },
  sleep: { anim: 'Spellcasting', kind: 'cloud', school: 'arcane' },
  towerbolt: { anim: 'Spellcast_Long', kind: 'bolt', school: 'arcane', heavy: true, size: 0.45 },
  // necromancer
  soul_bolt: { anim: 'Spellcast_Shoot', kind: 'bolt', school: 'necrotic' },
  soul_siphon: { anim: 'Spellcasting', kind: 'drain', school: 'necrotic' },
  animate_dead: { anim: 'Spellcast_Summon', kind: 'summon', school: 'necrotic' },
  soul_reap: { anim: 'Spellcast_Raise', kind: 'nova', school: 'shadow', radius: 4, atTarget: true },
  // cleric
  cure_light: { anim: 'Spellcast_Raise', kind: 'heal', school: 'holy' },
  heal: { anim: 'Spellcast_Long', kind: 'heal', school: 'holy', heavy: true },
  bless: { anim: 'Spellcast_Raise', kind: 'buff', school: 'holy' },
  flamestrike: { anim: 'Spellcast_Raise', kind: 'pillar', school: 'fire', heavy: true, radius: 3 },
  // bard
  mockery: { anim: 'Taunt', kind: 'bolt', school: 'sound' },
  fascinate: { anim: 'Spellcasting', kind: 'cloud', school: 'sound' },
  crescendo: { anim: 'Cheer', kind: 'nova', school: 'sound', radius: 6 },
  discordant_note: { anim: 'Spellcast_Shoot', kind: 'cone', school: 'sound', radius: 7 },
};

// the hero's ordinary swing, by class (the class model carries that weapon)
const SWING = {
  warrior: ['2H_Melee_Attack_Chop', '2H_Melee_Attack_Slice', '2H_Melee_Attack_Stab'],
  paladin: ['1H_Melee_Attack_Chop', '1H_Melee_Attack_Slice_Diagonal', '1H_Melee_Attack_Slice_Horizontal'],
  cleric: ['1H_Melee_Attack_Chop', '1H_Melee_Attack_Slice_Diagonal'],
  thief: ['Dualwield_Melee_Attack_Stab', 'Dualwield_Melee_Attack_Slice', 'Dualwield_Melee_Attack_Chop'],
  assassin: ['Dualwield_Melee_Attack_Stab', 'Dualwield_Melee_Attack_Slice'],
  bard: ['1H_Melee_Attack_Slice_Horizontal', '1H_Melee_Attack_Stab'],
  ranger: ['1H_Ranged_Shoot'],
  mage: ['Spellcast_Shoot'],
  necromancer: ['Spellcast_Shoot'],
};
const RANGED_AUTO = { ranger: { kind: 'shot', school: 'physical' }, mage: { kind: 'bolt', school: 'arcane', size: 0.16 }, necromancer: { kind: 'bolt', school: 'necrotic', size: 0.16 } };

const COLORS = { dmgOut: '#ffe9a8', dmgIn: '#ff6a52', heal: '#7dff8f', miss: '#b8b8c4', crit: '#ffb02a', parry: '#8cc8ff', block: '#9ad0ff', dodge: '#d8e0ff', spell: '#e0b8ff' };

export class CombatView {
  constructor({ engine, fx, ents, getHero, heroName, onOutOfRange, onWound }) {
    this.engine = engine;
    this.fx = fx;
    this.ents = ents;
    this.getHero = getHero;           // () => { actor, ctl, cls }
    this.heroName = heroName;         // () => name
    this.onOutOfRange = onOutOfRange; // (event) => void
    this.onWound = onWound;           // (entity) => void: its health changed
    this.telegraphs = new Map();      // mob id -> telegraph
    this.impacts = new Map();         // "src>dst" -> {at, crit, n}: when this action's blow lands
    this._v = new THREE.Vector3();
  }
  pairKey(a, b) { return `${JSON.stringify(a || null)}>${JSON.stringify(b || null)}`; }
  // the next wound from src to dst should appear when this action's blow lands
  expect(e, delayMs) {
    const k = this.pairKey(e.src, e.dst);
    this.impacts.set(k, { at: performance.now() + delayMs, crit: e.res === 'crit' || e.crit, n: 0 });
  }

  // ---- who is who ----
  resolve(ref) {
    if (!ref) return null;
    const h = this.getHero();
    if (ref.p && h && ref.p.toLowerCase() === String(this.heroName()).toLowerCase()) {
      return { actor: h.actor, root: h.actor.root, hero: true, cls: h.cls };
    }
    const e = ref.m != null ? this.ents.list.get(`m${ref.m}`) : ref.p ? this.ents.list.get(`p${ref.p}`) : null;
    if (!e || !e.root) return null;
    return { actor: e.actor, root: e.root, ent: e, mob: ref.m != null, cls: e.data && e.data.char_class };
  }
  chest(who) { return who.root.position.clone().setY(who.root.position.y + (who.ent && who.ent.plateY ? who.ent.plateY * 0.45 : 1.15)); }
  face(who, other) {
    if (!who || !other) return;
    const a = who.root.position, b = other.root.position;
    if (who.hero) { const h = this.getHero(); h.ctl.face(b.x, b.z); }
    else who.root.rotation.y = Math.atan2(b.x - a.x, b.z - a.z);
  }
  play(who, anim, speed = 1) {
    if (!who || !who.actor) return 0.5;
    if (who.hero) {
      // the hero already swung the moment the key was pressed: don't swing twice
      const ctl = this.getHero().ctl;
      if (performance.now() - (ctl.localSwingAt || 0) > 700) ctl.swing(anim);
      return 0.45;
    }
    return who.actor.once(anim, 0.08, speed) || 0.5;
  }

  // ---- events ----
  // a round's events arrive together; one creature's second and third blows follow its
  // first a beat apart, so a flurry reads as a flurry instead of one blur
  handle(list) {
    const seq = new Map();
    for (const e of list || []) {
      if (e.k === 'move') { this.move(e); continue; }
      if (e.k === 'dmg') { this.wound(e); continue; }
      // deaths after the killing number has risen; stars once the stunning blow has landed
      if (e.k === 'death') { setTimeout(() => this.event(e), 650); continue; }
      if (e.k === 'stun') { setTimeout(() => this.event(e), 360); continue; }
      const key = e.src ? JSON.stringify(e.src) : '_';
      const n = seq.get(key) || 0;
      seq.set(key, n + 1);
      const d = (e.delay_ms || 0) + (e.k === 'attack' ? n * 420 : n * 300);
      if (d > 0) setTimeout(() => this.event(e), d); else this.event(e);
    }
  }

  // a creature moving in a fight (server position, room metres)
  move(e) {
    const ent = e.src && e.src.m != null ? this.ents.list.get(`m${e.src.m}`) : null;
    if (ent) this.ents.place(ent, { x: e.x, z: e.z });
  }

  // a wound: the number rises when the blow that caused it lands (or now, for wounds
  // nothing announced: poison, fire, traps, a creature's special)
  wound(e) {
    const k = this.pairKey(e.src, e.dst);
    const imp = this.impacts.get(k);
    const now = performance.now();
    let delay = 0, crit = false;
    if (imp && now < imp.at + 1800) {
      delay = Math.max(0, imp.at - now) + imp.n * 420;
      crit = imp.crit && imp.n === 0;
      imp.n++;
    }
    const show = () => {
      const dst = this.resolve(e.dst);
      if (!dst) return;
      // the server says what is left after this wound, so the bar never counts a blow twice
      // (the round's own update may already have arrived)
      const killing = e.left != null ? e.left <= 0 : false;
      if (dst.ent && dst.ent.data && e.left != null) { dst.ent.data.hp = e.left; if (this.onWound) this.onWound(dst.ent); }
      const p = this.chest(dst);
      this.fx.text(p, crit ? `${e.amt}!` : `${e.amt}`, { color: dst.hero ? COLORS.dmgIn : crit ? COLORS.crit : COLORS.dmgOut, crit, size: dst.hero ? 17 : 19 });
      if (!imp || imp.n > 1) { this.fx.flash(dst.root, dst.hero ? 0xff2a1a : 0xffe0c0, 0.12); if (e.school) this.fx.impact(p, e.school); }
      if (crit || (dst.hero && e.amt >= 15)) this.fx.shake(crit ? 0.22 : 0.14, 0.2);
      if ((crit || killing) && this.engine.hitStop) this.engine.hitStop(killing ? 90 : 70);
      // a second or third blow in the same round gets its own swing
      if (imp && imp.n > 1) { const src = this.resolve(e.src); if (src && !src.hero) this.play(src, '1H_Melee_Attack_Slice_Diagonal', 1.3); }
    };
    if (delay > 0) setTimeout(show, delay); else show();
  }

  event(e) {
    switch (e.k) {
      case 'attack': return this.attack(e);
      case 'ability': case 'spell': return this.ability(e);
      case 'heal': return this.heal(e);
      case 'buff': case 'debuff': return this.buff(e);
      case 'windup': return this.windup(e);
      case 'resolve': return this.resolveWindup(e);
      case 'cancel': return this.cancelWindup(e);
      case 'death': return this.death(e);
      case 'stun': return this.stun(e);
      case 'oor': return this.onOutOfRange && this.onOutOfRange(e);
      case 'fizzle': return this.fizzle(e);
      default: return null;
    }
  }

  // an ordinary blow (auto-attack), melee or ranged, with its result
  attack(e) {
    const src = this.resolve(e.src), dst = this.resolve(e.dst);
    if (!src) return;
    if (dst) this.face(src, dst);
    const cls = String(src.cls || '').toLowerCase();
    // heroes shoot what their class shoots (arrows, arcane or shadow bolts); creatures as the server says
    const ranged = ((src.hero || !src.mob) && RANGED_AUTO[cls]) || e.ranged;
    let anim;
    if (src.hero || !src.mob) { const list = SWING[cls] || SWING.paladin; anim = list[Math.floor(Math.random() * list.length)]; }
    else anim = ['1H_Melee_Attack_Chop', '1H_Melee_Attack_Slice_Diagonal', '1H_Melee_Attack_Stab'][Math.floor(Math.random() * 3)];
    this.play(src, anim, 1.15);
    if (!dst) return;
    const land = () => this.land(e, src, dst, e.school || 'physical');
    if (ranged) {
      const r = typeof ranged === 'object' ? ranged
        : e.style === 'bolt' ? { kind: 'bolt', school: e.school || 'arcane', size: 0.2 } : { kind: 'shot', school: 'physical' };
      const speed = r.kind === 'shot' ? 26 : 18;
      const flight = 250 + this.chest(src).distanceTo(this.chest(dst)) / speed * 1000;
      this.expect(e, flight);
      this.fx.projectile(this.chest(src), this.chest(dst), { kind: r.kind === 'shot' ? 'arrow' : 'orb', school: r.school, speed, size: r.size || 0.2, delay: 0.25, onHit: () => this.land(e, src, dst, r.school) });
    } else {
      this.expect(e, 300);
      this.fx.slash(src.root.position, dst.root.position, { color: src.hero ? 0xfff0d0 : 0xffb0a0, delay: 0.18 });
      setTimeout(land, 300);
    }
  }

  // where a blow arrives: the number, the flinch, the spark
  land(e, src, dst, school) {
    const p = this.chest(dst);
    const heroHit = dst.hero;
    const res = e.res || (e.amt > 0 ? 'hit' : 'miss');
    if (res === 'hit' || res === 'crit') {
      const crit = e.crit || res === 'crit';
      this.fx.impact(p, school, crit || e.heavy);
      this.fx.flash(dst.root, heroHit ? 0xff2a1a : 0xffe0c0, 0.16);
      if (dst.actor && !dst.hero && !(dst.ent && dst.ent.dying)) dst.actor.once(Math.random() < 0.5 ? 'Hit_A' : 'Hit_B', 0.05, 1.2);
      if (dst.hero) this.getHero().ctl.swing(Math.random() < 0.5 ? 'Hit_A' : 'Hit_B');
      // (the number itself comes with the wound event: the amount actually taken)
    } else {
      const word = { miss: 'Miss', dodge: 'Dodge', parry: 'Parry', block: 'Block', resist: 'Resist', immune: 'Immune' }[res] || res;
      this.fx.text(p, word, { color: COLORS[res] || COLORS.miss, size: 15 });
      if (res === 'parry' || res === 'block') { this.fx.sparks(p, 0xbfe0ff, 10); if (dst.actor && !dst.hero) dst.actor.once('Block_Hit', 0.05, 1.3); }
      if (res === 'dodge' && dst.actor && !dst.hero) dst.actor.once(Math.random() < 0.5 ? 'Dodge_Left' : 'Dodge_Right', 0.05, 1.4);
      if (res === 'dodge' && dst.hero) this.getHero().ctl.swing(Math.random() < 0.5 ? 'Dodge_Left' : 'Dodge_Right');
    }
  }

  // a skill or spell: the user's animation, then what flies and how it lands
  ability(e) {
    const src = this.resolve(e.src), dst = this.resolve(e.dst);
    const name = String(e.ability || e.spell || '').toLowerCase().replace(/[\s']+/g, '_');
    const v = ABILITY_FX[name] || this.guess(name, e);
    const school = e.school || v.school || 'arcane';
    if (src && dst && src !== dst) this.face(src, dst);
    if (src) this.play(src, v.anim || 'Spellcast_Shoot', 1.1);
    const from = src ? this.chest(src) : null;
    const to = dst ? this.chest(dst) : e.at ? new THREE.Vector3(e.at.x, 1, e.at.z) : null;
    const flight = from && to ? from.distanceTo(to) / (v.kind === 'shot' ? 30 : v.heavy ? 14 : 20) * 1000 : 0;
    const LAND = { melee: 320, dash: 330, shot: 300 + flight, volley: 700, bolt: 300 + flight + ((v.count || 1) - 1) * 120,
      beam: 380, drain: 420, pillar: 450, nova: 380, cone: 420, cloud: 380, mark: 400 };
    if (dst) this.expect({ ...e, src: e.src, dst: e.dst }, LAND[v.kind] || 300);
    // a skill or spell lands unless the server says otherwise (parried, resisted...); the
    // number comes with its wound event
    const landAll = () => {
      if (dst && dst !== src) this.land({ ...e, res: e.res || 'hit', heavy: v.heavy }, src, dst, school);
      for (const t of e.also || []) { const w = this.resolve(t.dst); if (w) this.land({ ...t, res: t.res || 'hit', heavy: v.heavy }, src, w, school); }
      // (stuns come from the server as their own events, with their real length)
    };
    switch (v.kind) {
      case 'melee':
        if (src && dst) this.fx.slash(src.root.position, dst.root.position, { color: new THREE.Color().set(this.colorOf(school)).getHex(), wide: v.wide, delay: 0.15 });
        setTimeout(landAll, 320);
        if (v.wide && src) this.fx.shockwave(src.root.position, { school, radius: 3, delay: 0.2 });
        break;
      case 'dash':
        if (src && dst) {
          const start = src.root.position.clone();
          const end = dst.root.position.clone().sub(start).setY(0);
          const len = end.length();
          end.setLength(Math.max(0, len - 1.4)).add(start);
          if (src.hero) this.getHero().ctl.dash(end.x, end.z, 0.28);
          for (let i = 0; i < 6; i++) setTimeout(() => this.fx.p.emit(src.root.position.clone().setY(0.3), { count: 5, color: 0xd8c8a0, speed: 1.5, life: 0.5, size: 0.4, drag: 2 }), i * 45);
        }
        setTimeout(() => { if (dst) this.fx.shockwave(dst.root.position, { school, radius: 2.5 }); landAll(); }, 330);
        break;
      case 'shot':
        if (from && to) this.fx.projectile(from, to, { kind: 'arrow', speed: 30, delay: 0.3, onHit: landAll });
        else landAll();
        break;
      case 'volley':
        if (from && to) for (let i = 0; i < 7; i++) {
          const off = new THREE.Vector3((Math.random() - 0.5) * 2 * (v.radius || 3), 0, (Math.random() - 0.5) * 2 * (v.radius || 3));
          this.fx.projectile(from, to.clone().add(off).setY(0.2), { kind: 'arrow', speed: 24, arc: 2.2, delay: 0.25 + i * 0.06, onHit: p => this.fx.impact(p, 'physical') });
        }
        setTimeout(landAll, 700);
        break;
      case 'bolt': {
        const n = v.count || 1;
        if (from && to) for (let i = 0; i < n; i++) {
          this.fx.projectile(from, to, { school, size: v.size || 0.24, speed: v.heavy ? 14 : 20, arc: n > 1 ? 1.5 + i : 0.4, delay: 0.3 + i * 0.12,
            onHit: p => { if (i === n - 1) { landAll(); if (v.radius) this.fx.shockwave(p, { school, radius: v.radius }); } else this.fx.impact(p, school); } });
        } else landAll();
        break;
      }
      case 'beam':
        if (v.sky && to) { const top = to.clone().setY(9); this.fx.beam(top, to, { school, delay: 0.35 }); }
        else if (from && to) this.fx.beam(from, to, { school, delay: 0.3 });
        setTimeout(landAll, 380);
        break;
      case 'drain':
        if (from && to) { this.fx.beam(to, from, { school, delay: 0.25, time: 0.6 }); }
        setTimeout(landAll, 420);
        break;
      case 'pillar':
        if (to) this.fx.pillar(to, { school, delay: 0.35, radius: v.radius ? 1.4 : 0.9 });
        setTimeout(() => { landAll(); if (v.radius && to) this.fx.shockwave(to, { school, radius: v.radius }); }, 450);
        break;
      case 'nova': {
        const c = v.atTarget && dst ? dst.root.position : src ? src.root.position : to;
        if (c) setTimeout(() => this.fx.shockwave(c, { school, radius: v.radius || 4 }), 280);
        if (c) setTimeout(() => this.fx.p.emit(c.clone().setY(0.6), { count: 40, color: this.colorOf(school), speed: 6, life: 0.5, size: 0.3, drag: 3 }), 300);
        setTimeout(landAll, 380);
        break;
      }
      case 'cone':
        if (src && to) {
          const dir = to.clone().sub(src.root.position).setY(0).normalize();
          for (let i = 0; i < 24; i++) setTimeout(() => this.fx.p.emit(this.chest(src), { count: 3, color: this.colorOf(school), speed: 8, life: 0.45, size: 0.3, dir: dir.clone().multiplyScalar(6), spread: 2, drag: 1.5 }), 250 + i * 10);
        }
        setTimeout(landAll, 420);
        break;
      case 'cloud':
        if (to) setTimeout(() => this.fx.p.emit(to, { count: 30, color: this.colorOf(school), speed: 1.2, up: 0.4, life: 1.1, size: 0.6, grow: 0.6, drag: 1 }), 300);
        setTimeout(landAll, 380);
        break;
      case 'mark':
        if (from && to) this.fx.projectile(from, to, { school, size: 0.12, speed: 26, delay: 0.25 });
        setTimeout(() => { if (dst) this.fx.swirl(dst.root, { school, time: 0.8, rise: 2.4, count: 2 }); landAll(); }, 400);
        break;
      case 'heal':
        return this.heal({ ...e, src: e.src, dst: e.dst || e.src, school });
      case 'buff':
        if (dst || src) this.fx.swirl((dst || src).root, { school, time: 0.9 });
        setTimeout(landAll, 300);
        break;
      case 'summon':
        if (src) { const p = src.root.position.clone().add(new THREE.Vector3(1.2, 0, 0.6)); this.fx.pillar(p, { school, radius: 0.7, delay: 0.4 }); }
        break;
      default:
        setTimeout(landAll, 300);
    }
  }

  // a spell that came apart in the caster's hands: a puff of grey smoke, a few sparks
  fizzle(e) {
    const src = this.resolve(e.src);
    if (!src) return;
    if (!src.hero) this.play(src, 'Spellcast_Shoot', 1.1);
    const p = this.chest(src).add(new THREE.Vector3(0, 0.25, 0));
    setTimeout(() => {
      this.fx.p.emit(p, { count: 18, color: 0x8a8a96, speed: 1.1, up: 0.9, life: 0.9, size: 0.38, grow: 0.5, drag: 1.6 });
      this.fx.sparks(p, this.colorOf(e.school || 'arcane'), 6);
      this.fx.text(p.clone().setY(p.y + 0.5), 'Fizzled', { color: '#b8b0c8', size: 14, rise: 0.6 });
    }, 320);
  }

  guess(name, e) {
    const s = e.school || '';
    if (/heal|cure|mend|restore|renew/.test(name)) return { anim: 'Spellcast_Raise', kind: 'heal', school: 'holy' };
    if (/bless|armor|shield|ward|aura|haste|strength|stoneskin|sanctuary/.test(name)) return { anim: 'Spellcast_Raise', kind: 'buff', school: s || 'holy' };
    if (/fire|flame|burn/.test(name)) return { anim: 'Spellcast_Shoot', kind: 'bolt', school: 'fire' };
    if (/frost|ice|chill|cold/.test(name)) return { anim: 'Spellcast_Shoot', kind: 'bolt', school: 'frost' };
    if (/lightning|shock|thunder/.test(name)) return { anim: 'Spellcast_Shoot', kind: 'beam', school: 'lightning' };
    if (/shoot|shot|arrow|volley/.test(name)) return { anim: '1H_Ranged_Shoot', kind: 'shot', school: 'physical' };
    if (e.k === 'spell') return { anim: 'Spellcast_Shoot', kind: 'bolt', school: s || 'arcane' };
    return { anim: '1H_Melee_Attack_Chop', kind: 'melee', school: s || 'physical' };
  }
  colorOf(school) { return ({ fire: 0xff7a2a, frost: 0x9fd8ff, lightning: 0xbfd8ff, arcane: 0xc87aff, holy: 0xffe8a0, shadow: 0x8a4ad0, necrotic: 0x7aff8a, nature: 0x9aff6a, poison: 0xb8ff5a, sound: 0xffb8ff, blood: 0xd02a2a })[school] || 0xffffff; }

  heal(e) {
    const dst = this.resolve(e.dst) || this.resolve(e.src);
    if (!dst) return;
    this.fx.swirl(dst.root, { school: e.school || 'holy', time: 0.9 });
    setTimeout(() => this.fx.pillar(dst.root.position, { school: e.school || 'holy', radius: 0.7, time: 0.6 }), 150);
    if (e.amt) setTimeout(() => this.fx.text(this.chest(dst), `+${e.amt}`, { color: COLORS.heal, size: 18 }), 300);
  }
  buff(e) {
    const dst = this.resolve(e.dst);
    if (!dst) return;
    this.fx.swirl(dst.root, { school: e.school || (e.k === 'debuff' ? 'shadow' : 'holy'), time: 0.8, count: 2 });
    if (e.name) this.fx.text(this.chest(dst).setY(dst.root.position.y + 2.4), e.name, { color: e.k === 'debuff' ? '#d8a8ff' : '#fff0b0', size: 13, rise: 0.8 });
  }
  stun(e) {
    const dst = this.resolve(e.dst);
    if (!dst) return;
    let t = 0;
    const top = () => dst.root.position.clone().setY(dst.root.position.y + (dst.ent && dst.ent.plateY ? dst.ent.plateY : 2.4) - 0.2);
    this.fx.add({ update: dt => {
      t += dt;
      if (Math.floor(t * 20) % 2 === 0) for (let i = 0; i < 3; i++) {
        const a = t * 6 + i * 2.1;
        this.fx.p.emit(top().add(new THREE.Vector3(Math.cos(a) * 0.45, 0, Math.sin(a) * 0.45)), { count: 1, color: 0xffe066, speed: 0, life: 0.18, size: 0.22 });
      }
      return t < (e.secs || 1.6);
    } });
    this.fx.text(top(), 'Stunned', { color: '#ffe066', size: 13, rise: 0.6 });
  }

  // a creature gathers itself for a big blow: the ground warns you
  windup(e) {
    const src = this.resolve(e.src);
    if (!src) return;
    const a = e.area || {};
    const secs = Math.max(0.4, (e.ms || 1500) / 1000);
    const target = this.resolve(e.dst);
    const center = a.x != null ? new THREE.Vector3(a.x, 0, a.z)
      : a.shape === 'cone' || !a.shape ? src.root.position.clone() : (target ? target.root.position.clone() : src.root.position.clone());
    let facing = 0;
    if (target) { const d = target.root.position.clone().sub(src.root.position); facing = Math.atan2(-d.z, d.x); }
    const t = this.fx.telegraph(center, { shape: a.shape || 'circle', radius: a.r || 2.6, angle: a.angle || Math.PI / 2, facing, time: secs });
    if (!a.x && (a.shape === 'circle' || !a.shape)) t.follow = src.root;
    const key = e.src && e.src.m != null ? `m${e.src.m}` : 'x';
    if (this.telegraphs.get(key)) this.telegraphs.get(key).cancel();
    this.telegraphs.set(key, t);
    if (src.actor) src.actor.once(src.mob ? 'Block' : 'Spellcast_Long', 0.1, 0.8);
    this.fx.text(this.chest(src).setY(src.root.position.y + 2.6), e.label || 'Winding up!', { color: '#ff8a5a', size: 14, rise: 0.5, life: Math.min(1.6, secs) });
  }
  resolveWindup(e) {
    const key = e.src && e.src.m != null ? `m${e.src.m}` : 'x';
    const t = this.telegraphs.get(key);
    if (t) { t.cancel(); this.telegraphs.delete(key); }
    const src = this.resolve(e.src);
    const a = e.area || {};
    // the blow lands on the ground it marked (a heavy blow or a spell where you stood)
    const at = a.x != null ? new THREE.Vector3(a.x, 0, a.z) : src ? src.root.position.clone() : null;
    if (src) {
      const tgt = at && a.x != null ? { root: { position: at } } : null;
      if (tgt) this.face(src, tgt);
      if (src.actor) src.actor.once(e.kind === 'cast' ? 'Spellcast_Shoot' : e.kind === 'aoe' ? '2H_Melee_Attack_Spin' : '2H_Melee_Attack_Chop', 0.06, 1.2);
    }
    if (at) {
      const school = e.school || 'physical';
      if (e.kind === 'cast' && src) this.fx.projectile(this.chest(src), at.clone().setY(0.4), { school, size: 0.3, speed: 18, delay: 0.2, onHit: p => this.fx.impact(p, school, true) });
      setTimeout(() => { this.fx.shockwave(at, { school, radius: a.r || 3 }); this.fx.shake(0.18, 0.25); }, e.kind === 'cast' ? 450 : 250);
    }
    for (const h of e.hits || []) { const d = this.resolve(h.dst); if (d) this.land(h, src, d, e.school || 'physical'); }
    if (e.dodged) for (const ref of e.dodged) { const d = this.resolve(ref); if (d) this.fx.text(this.chest(d), 'Evaded!', { color: '#a8ffd0', size: 16 }); }
  }
  // a wind-up broken before it landed (staggered, kicked, snared, killed, the fight over)
  cancelWindup(e) {
    const key = e.src && e.src.m != null ? `m${e.src.m}` : 'x';
    const t = this.telegraphs.get(key);
    if (t) { t.fade(); this.telegraphs.delete(key); }
    const src = this.resolve(e.src);
    if (!src || e.reason === 'death' || e.reason === 'end') return;
    const p = this.chest(src);
    this.fx.sparks(p, 0xffe066, 16);
    const word = { stagger: 'Staggered!', snare: 'Snared!' }[e.reason] || 'Interrupted!';
    this.fx.text(p.clone().setY(src.root.position.y + 2.6), word, { color: '#ffe066', size: 15, rise: 0.6 });
    if (src.actor && !(src.ent && src.ent.dying)) src.actor.once(Math.random() < 0.5 ? 'Hit_A' : 'Hit_B', 0.05, 1.0);
  }
  death(e) {
    const dst = this.resolve(e.dst);
    if (!dst) return;
    this.fx.p.emit(this.chest(dst), { count: 30, color: 0xd8d0c0, speed: 2.4, up: 0.8, life: 0.9, size: 0.45, grow: 0.6, drag: 1.4 });
  }
}
