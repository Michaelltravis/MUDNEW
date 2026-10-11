// Which body parts, pieces and colours dress a character, from the server's look summary
// (src/gear_look.py). Pure: no three.js, so tests/web/gearlook.test.mjs runs it in Node.
// equip.js turns a plan into one mesh from the equipment kit (art3d/chars/equip.glb, whose
// manifest equip.json says what every piece is and which palette columns it paints).
//
// A class keeps its silhouette: its body comes from its own model unless worn armour is two
// or more steps of weight away from what the class starts in (a mage in plate gets the
// knight's torso). Colours always follow the gear: metal and leather by material, cloth by
// the piece's colour, its named set, or the class's own colour; tier 0 is dull and worn.

// a class's own model, the armour weight it starts in (0 cloth, 1 leather, 2 mail, 3 plate),
// and whether it goes hooded when its head is bare
export const CLASS_BASE = {
  warrior: { model: 'barbarian', w: 2 }, paladin: { model: 'knight', w: 2 }, cleric: { model: 'knight', w: 1 },
  mage: { model: 'mage', w: 0 }, necromancer: { model: 'mage', w: 0 }, thief: { model: 'rogue', w: 1 },
  assassin: { model: 'rogue', w: 1, hood: true }, ranger: { model: 'rogue', w: 1, hood: true }, bard: { model: 'rogue', w: 1 },
};
const MODEL_W = { mage: 0, rogue: 1, barbarian: 2, knight: 3 };
const BY_WEIGHT = ['mage', 'rogue', 'barbarian', 'knight'];
export const baseOf = cls => CLASS_BASE[String(cls || '').toLowerCase()] || CLASS_BASE.paladin;

// what a class wears before it finds anything better (player.py's starting kits, as the
// server would describe them): character creation and the demo show this
export function starterLook(cls) {
  const c = String(cls || '').toLowerCase();
  const S = {
    warrior: { main: { k: 'sword', h: 1, m: 'steel' }, off: { k: 'shield', v: 'round', m: 'iron', m2: 'wood' }, head: { k: 'helm', m: 'iron' }, body: { w: 2, m: 'iron' }, legs: { w: 3, m: 'iron' } },
    paladin: { main: { k: 'sword', h: 1, m: 'steel' }, off: { k: 'shield', v: 'round', m: 'iron', m2: 'wood' }, body: { w: 2, m: 'iron' } },
    cleric: { main: { k: 'mace', h: 1, m: 'steel' }, body: { w: 1, m: 'leather' } },
    mage: { main: { k: 'staff', h: 2, m: 'wood_dark' }, off: { k: 'book' }, body: { w: 0 } },
    necromancer: { main: { k: 'staff', h: 2, m: 'wood_dark', m2: 'obsidian' }, body: { w: 0, c: 'black' } },
    thief: { main: { k: 'dagger', h: 1, m: 'steel' }, body: { w: 1, m: 'leather_tan' } },
    ranger: { main: { k: 'bow', h: 2, m: 'wood' }, body: { w: 1, m: 'leather_dark' }, quiver: 1 },
    bard: { main: { k: 'sword', h: 1, m: 'steel' }, off: { k: 'instrument', h: 1, m: 'wood' }, body: { w: 1, m: 'leather' } },
    assassin: { main: { k: 'dagger', h: 1, m: 'steel' }, body: { w: 1, m: 'leather_black' }, back: { k: 'cloak', v: 'rogue', c: 'black' } },
  }[c] || {};
  const look = { v: 1, rn: 0 };
  for (const [k, p] of Object.entries(S)) look[k] = typeof p === 'object' ? { t: 0, ...p } : p;
  look.sig = `starter:${c}`;
  return look;
}

// ---- pieces ----
const MAIN = {
  sword: h => (h === 2 ? 'knight-2H_Sword' : 'knight-1H_Sword'),
  axe: h => (h === 2 ? 'barbarian-2H_Axe' : 'barbarian-1H_Axe'),
  dagger: () => 'rogue-Knife', staff: () => 'mage-2H_Staff', wand: () => 'mage-1H_Wand',
  crossbow: h => (h === 2 ? 'rogue-2H_Crossbow' : 'rogue-1H_Crossbow'), thrown: () => 'rogue-Throwable',
  // until they have shapes of their own, the nearest there is
  spear: () => 'mage-2H_Staff', polearm: () => 'barbarian-2H_Axe', scythe: () => 'barbarian-2H_Axe',
  pick: () => 'barbarian-1H_Axe', claw: () => 'rogue-Knife', whip: () => 'rogue-Knife',
};
// built in code (procgear.js): kind -> shape
export const PROC = { bow: 'bow', mace: 'mace', hammer: 'mace', instrument: 'lute' };
const OFFHAND = { sword: 'knight-1H_Sword_Offhand', axe: 'barbarian-1H_Axe_Offhand', dagger: 'rogue-Knife_Offhand' };
const SHIELD = { round: 'knight-Round_Shield', badge: 'knight-Badge_Shield', square: 'knight-Rectangle_Shield', spike: 'knight-Spike_Shield' };
const SHIELD_PAINTED = { round: 'kit-shield_round_color', badge: 'kit-shield_badge_color', square: 'kit-shield_square_color', spike: 'kit-shield_spikes_color' };
const HEAD = { helm: 'knight-Knight_Helmet', horned: 'barbarian-Barbarian_Hat', hat: 'mage-Mage_Hat' };
const CAPE = { knight: 'knight-Knight_Cape', barbarian: 'barbarian-Barbarian_Cape', mage: 'mage-Mage_Cape', rogue: 'rogue-Rogue_Cape' };
export const WEAPON_KINDS = new Set(['sword', 'axe', 'dagger', 'mace', 'hammer', 'spear', 'polearm', 'scythe', 'pick', 'claw', 'whip', 'staff', 'wand', 'crossbow', 'bow', 'thrown']);

// a hat made for one head sits a little differently on another (tuned in the gear gallery):
// `${piece}@${head model}` -> offset (bone-local metres) and scale
export const FIT = {
  'knight-Knight_Helmet@mage': { t: [0, 0.03, -0.04], s: 1.08 },
  'knight-Knight_Helmet@barbarian': { t: [0, 0.02, -0.01], s: 1.04 },
  'mage-Mage_Hat@knight': { t: [0, -0.03, 0.03], s: 0.95 },
  'mage-Mage_Hat@barbarian': { t: [0, 0, 0.02], s: 0.98 },
  'mage-Mage_Hat@rogue': { t: [0, -0.02, 0.02], s: 0.95 },
  'barbarian-Barbarian_Hat@mage': { t: [0, 0.03, -0.04], s: 1.07 },
  'barbarian-Barbarian_Hat@knight': { t: [0, 0, 0.01], s: 1.0 },
  'knight-Knight_Helmet@rogue': { t: [0, 0, 0], s: 1.0 },
};

// a leather and the lighter leather beside it
const LEATHER_PAIR = { leather: ['leather', 'leather_tan'], leather_tan: ['leather_tan', 'hide'], leather_dark: ['leather_dark', 'leather'],
  leather_black: ['leather_black', 'leather_dark'], leather_red: ['leather_red', 'leather'], hide: ['hide', 'leather_tan'],
  dragonhide: ['dragonhide', 'leather_dark'], snakeskin: ['snakeskin', 'leather_tan'] };

const worn = (name, p) => (p && (p.t || 0) === 0 ? `${name}~worn` : name);
const darkOf = (name, p) => (p && (p.t || 0) === 0 ? `${name}~worn~dark` : `${name}~dark`);

// the cloth colour a piece is painted in: its named set, its own colour, its zone set's, else the class's
function clothOf(p, cls) {
  if (p && p.s) return `set_${p.s}`;
  if (p && p.c) return p.c;
  if (p && p.zc) return p.zc;
  return `class_${String(cls || 'paladin').toLowerCase()}`;
}

// role -> ramp name, for each kind of piece
function armourRoles(a, cls) {
  const r = {};
  if (a && a.w >= 2 && a.m) { r.metal = worn(a.m, a); r.metal_dark = darkOf(a.m, a); }
  if (a && a.w === 1 && a.m) {
    const [main, light] = LEATHER_PAIR[a.m] || [a.m, a.m];
    r.leather = worn(main, a); r.leather_light = worn(light, a);
    r.metal = worn(main, a); r.metal_dark = worn('leather_dark', a);      // a heavier body in leather: its plates are boiled leather
  }
  const cloth = clothOf(a, cls);
  r.cloth = worn(cloth, a); r.cloth_dark = darkOf(cloth, a);
  return r;
}
function weaponRoles(p) {
  const r = {};
  const wooden = ['staff', 'bow', 'wand', 'instrument'].includes(p.k);
  const metal = wooden ? p.m2 : p.m;
  const wood = wooden ? p.m : p.m2;
  if (metal) { r.metal = worn(metal, p); r.metal_dark = darkOf(metal, p); }
  if (wood) r.wood = worn(wood, p);
  if (p.e) r.gem = p.e;
  else if (p.s) r.gem = `set_${p.s}_accent`;
  return r;
}
function shieldRoles(p, cls) {
  const r = { metal: worn(p.m || 'iron', p), metal_dark: darkOf(p.m || 'iron', p) };
  if (p.m2) r.wood = worn(p.m2, p);
  r.gem = p.s ? `set_${p.s}_accent` : p.e || `class_${String(cls || 'paladin').toLowerCase()}`;
  return r;
}
function headRoles(p, cls) {
  if (p.k === 'hat' || p.k === 'hood') { const c = clothOf(p, cls); return { cloth: worn(c, p), cloth_light: worn(c, p) }; }
  if (p.m) return { metal: worn(p.m, p), metal_dark: darkOf(p.m, p) };
  return {};
}
function capeRoles(p, cls) {
  const c = clothOf(p, cls);
  const r = { cloth: worn(c, p), cloth_accent: worn(c, p), cloth_dark: darkOf(c, p) };
  if (p.s || p.c) r.leather_dark = worn(c, p);            // the fur cloak too, when it has a colour or a set
  return r;
}

// the role -> palette column remap of one piece
function remapOf(kit, name, roles) {
  const piece = kit.pieces[name];
  if (!piece) return null;
  const out = {};
  for (const [col, role] of Object.entries(piece.cols)) {
    const target = roles[role];
    if (!target) continue;
    const to = kit.col(target);
    if (to != null && to !== +col) out[col] = to;
  }
  return out;
}

const mountOf = (kit, piece) => kit.pieces[piece] && kit.pieces[piece].mount;

// A look -> {key, parts, props: [{name, remap, fit}], procs: [{shape, piece (whose mount it
// borrows), bone, roles, look}], idle}
export function planLook(look, cls, kit) {
  look = look || starterLook(cls);
  cls = String(cls || '').toLowerCase();
  const base = baseOf(cls);
  // measured from what the class starts in (a cleric's knight body stands for leather), then
  // arms and legs from what the torso stands for
  const torso = look.body && Math.abs(look.body.w - base.w) >= 2 ? BY_WEIGHT[look.body.w] : base.model;
  const refW = torso === base.model ? base.w : MODEL_W[torso];
  const limb = a => (a && Math.abs(a.w - refW) >= 2 ? BY_WEIGHT[a.w] : torso);
  const arms = limb(look.arms), legs = limb(look.legs);
  const hooded = look.head ? look.head.k === 'hood' : base.hood;
  const headModel = base.model;
  const props = [], procs = [];
  const add = (name, roles, fit) => { if (kit.pieces[name]) props.push({ name, remap: remapOf(kit, name, roles || {}), fit: fit || null }); };

  // the body: the class's head, torso, arms and legs from whichever models the armour asks for
  const bodyRoles = armourRoles(look.body, cls);
  const parts = [
    // a hood in its own colour, or the class's
    [hooded ? 'rogue-HeadHooded' : `${headModel}-Head`, hooded ? headRoles(look.head || { k: 'hood', t: 1 }, cls) : {}],
    [`${torso}-Body`, bodyRoles],
    [`${arms}-ArmLeft`, look.arms ? armourRoles(look.arms, cls) : bodyRoles],
    [`${arms}-ArmRight`, look.arms ? armourRoles(look.arms, cls) : bodyRoles],
    [`${legs}-LegLeft`, look.legs ? armourRoles(look.legs, cls) : bodyRoles],
    [`${legs}-LegRight`, look.legs ? armourRoles(look.legs, cls) : bodyRoles],
  ];
  for (const [name, roles] of parts) add(name, roles);

  // the main hand
  const m = look.main;
  if (m) {
    if (PROC[m.k]) procs.push({ shape: PROC[m.k], piece: m.k === 'bow' ? 'knight-1H_Sword_Offhand' : 'knight-1H_Sword', look: m, roles: weaponRoles(m) });
    else if (MAIN[m.k]) {
      const name = m.h === 2 && m.k === 'sword' && (m.t || 0) >= 3 ? 'kit-sword_2handed_color' : MAIN[m.k](m.h);
      add(name, weaponRoles(m));
    }
  }
  // the off hand: a shield, a second weapon, or something held
  const o = look.off;
  const bowInLeft = m && m.k === 'bow';
  if (o && !bowInLeft) {
    if (o.k === 'shield') {
      const v = SHIELD[o.v] ? o.v : 'round';
      const name = (o.t || 0) >= 2 || o.s ? SHIELD_PAINTED[v] : v === 'round' && o.m2 ? 'barbarian-Barbarian_Round_Shield' : SHIELD[v];
      add(name, shieldRoles(o, cls));
    } else if (OFFHAND[o.k]) add(OFFHAND[o.k], weaponRoles(o));
    else if (WEAPON_KINDS.has(o.k) && !PROC[o.k]) add('rogue-Knife_Offhand', weaponRoles(o));
    else if (PROC[o.k]) procs.push({ shape: PROC[o.k], piece: 'knight-1H_Sword_Offhand', look: o, roles: weaponRoles(o) });
    else if (o.k === 'book') add('mage-Spellbook', o.c ? { cloth_accent: worn(o.c, o) } : {});
  }
  // the head
  const h = look.head;
  if (h && HEAD[h.k]) add(HEAD[h.k], headRoles(h, cls), FIT[`${HEAD[h.k]}@${headModel}`]);
  // the back: a cloak, a quiver
  if (look.back) add(CAPE[look.back.v] || CAPE.rogue, capeRoles(look.back, cls));
  if (look.quiver || (m && m.k === 'bow')) add('kit-quiver', {});

  const twoHanded = m && (m.h === 2 || ['spear', 'polearm', 'scythe'].includes(m.k)) && !['bow', 'crossbow', 'staff'].includes(m.k);
  const key = `${look.sig || JSON.stringify(look)}|${cls}`;
  return { key, parts: parts.map(p => p[0]), props, procs, idle: twoHanded ? '2H_Melee_Idle' : 'Idle' };
}

// ---- the swing: what the hand holds decides the blow ----
const ONE_H = ['1H_Melee_Attack_Chop', '1H_Melee_Attack_Slice_Diagonal', '1H_Melee_Attack_Slice_Horizontal'];
const TWO_H = ['2H_Melee_Attack_Chop', '2H_Melee_Attack_Slice', '2H_Melee_Attack_Stab'];
const DUAL = ['Dualwield_Melee_Attack_Stab', 'Dualwield_Melee_Attack_Slice', 'Dualwield_Melee_Attack_Chop'];
// ranged: whether the server shot (the class's auto-attack reach, combat_range.py)
export function swingClips(look, cls, ranged) {
  cls = String(cls || '').toLowerCase();
  const m = look && look.main, o = look && look.off;
  if (ranged) {
    if (m && m.k === 'crossbow') return [m.h === 2 ? '2H_Ranged_Shoot' : '1H_Ranged_Shoot'];
    if (m && m.k === 'bow') return ['2H_Ranged_Shoot'];
    if (/mage|necro|cleric/.test(cls) || (m && ['staff', 'wand'].includes(m.k))) return ['Spellcast_Shoot'];
    return ['Throw'];
  }
  if (!m) return ['Unarmed_Melee_Attack_Punch_A', 'Unarmed_Melee_Attack_Kick'];
  if (o && WEAPON_KINDS.has(o.k) && o.k !== 'bow') return DUAL;
  if (m.k === 'spear' || m.k === 'polearm') return ['2H_Melee_Attack_Stab', '2H_Melee_Attack_Slice'];
  if (m.h === 2 || m.k === 'scythe') return TWO_H;
  if (m.k === 'dagger' || m.k === 'claw') return ['1H_Melee_Attack_Stab', '1H_Melee_Attack_Slice_Diagonal'];
  return ONE_H;
}

// the manifest (equip.json), indexed for planLook
export function kitIndex(manifest) {
  const cols = new Map(manifest.columns.map((c, i) => [c.name, i]));
  return { ...manifest, N: manifest.palette.cols, col: name => (cols.has(name) ? cols.get(name) : null) };
}
