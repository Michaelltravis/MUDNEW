// Is this an upgrade? (hud/inventory.js: the tooltip's comparison with what you wear, the green
// arrow on a better piece in the pack). Pure, so tests/web/gearcompare.test.mjs can check it.
// An item is scored for the wearer's class: a weapon's average damage, its armour, and what its
// affects add, each stat weighed by how much the class leans on it.

export const slotOf = s => String(s || '').replace(/\d$/, '');

// '2d6+3' -> 10
export function avgDice(dice) {
  const m = /^\s*(\d+)\s*d\s*(\d+)\s*([+-]\s*\d+)?/i.exec(String(dice || ''));
  if (!m) return 0;
  return +m[1] * (+m[2] + 1) / 2 + (m[3] ? +m[3].replace(/\s/g, '') : 0);
}

const ALIAS = { intelligence: 'int', wisdom: 'wis', strength: 'str', dexterity: 'dex', constitution: 'con', charisma: 'cha',
  max_hit: 'hp', max_hp: 'hp', hit: 'hp', max_mana: 'mana', max_move: 'move' };
const PRIMARY = { warrior: 'str', paladin: 'str', thief: 'dex', assassin: 'dex', ranger: 'dex', mage: 'int', necromancer: 'int',
  cleric: 'wis', bard: 'cha' };
const CASTER = new Set(['mage', 'necromancer', 'cleric', 'paladin', 'bard']);

// what an item gives: { damage, armour, <stat>: n, ... }
export function statsOf(item) {
  const s = {};
  if (!item) return s;
  if (item.damage_dice) s.damage = avgDice(item.damage_dice);
  if (item.armor) s.armour = +item.armor || 0;
  for (const a of item.affects || []) {
    let k = String(a.location || a.stat || a.type || a.name || '').toLowerCase();
    const v = +(a.modifier ?? a.value ?? a.amount ?? 0);
    if (!k || !v) continue;
    k = ALIAS[k] || k;
    s[k] = (s[k] || 0) + v;
  }
  return s;
}

function weight(k, cls) {
  const caster = CASTER.has(cls);
  if (k === 'damage') return caster && cls !== 'paladin' ? 1 : 3;
  if (k === 'armour' || k === 'armor') return 1;
  if (k === 'damroll') return caster && cls !== 'paladin' ? 1 : 3;
  if (k === 'hitroll') return caster && cls !== 'paladin' ? 0.7 : 2;
  if (k === 'hp') return 0.15;
  if (k === 'mana') return caster ? 0.25 : 0.02;
  if (k === 'move') return 0.02;
  if (k === 'spell_power') return caster ? 2.5 : 0.2;
  if (k === 'heal_power') return cls === 'cleric' || cls === 'paladin' ? 2.5 : 0.2;
  if (['str', 'dex', 'con', 'int', 'wis', 'cha'].includes(k)) return PRIMARY[cls] === k ? 2.6 : k === 'con' ? 1.4 : 1;
  if (k.endsWith('_resist')) return 0.3;
  return 0.5;                                  // a skill (sneak +1, backstab +2) and the like
}

export function score(item, cls = '') {
  let total = 0;
  for (const [k, v] of Object.entries(statsOf(item))) total += v * weight(k, String(cls).toLowerCase());
  return total;
}

// the worn piece this one would replace: the one in its slot, the weaker of two (rings,
// necklaces, wrists), the weapon hand for a weapon; null for an empty slot
export function wornFor(item, equipment = {}) {
  if (!item) return { slot: null, worn: null };
  const want = item.type === 'weapon' ? 'wield' : slotOf(item.slot);
  if (!want) return { slot: null, worn: null };
  const slots = Object.keys(equipment).length ? Object.keys(equipment) : [want];
  const mine = slots.filter(k => slotOf(k) === want);
  if (!mine.length) return { slot: want, worn: null };
  const empty = mine.find(k => !equipment[k]);
  if (empty) return { slot: empty, worn: null };
  let best = mine[0];
  for (const k of mine) if (score(equipment[k]) < score(equipment[best])) best = k;
  return { slot: best, worn: equipment[best] };
}

// the comparison a tooltip shows: each stat's change, the overall change, and whether it is
// clearly better for this class (an empty slot filled by anything useful counts)
export function compare(item, equipment, cls = '') {
  const { slot, worn } = wornFor(item, equipment);
  if (!slot) return null;
  const a = statsOf(item), b = statsOf(worn);
  const rows = [];
  for (const k of new Set([...Object.keys(a), ...Object.keys(b)])) {
    const d = (a[k] || 0) - (b[k] || 0);
    if (Math.abs(d) >= 0.05) rows.push({ k, delta: Math.round(d * 10) / 10 });
  }
  rows.sort((x, y) => Math.abs(weight(y.k, cls) * y.delta) - Math.abs(weight(x.k, cls) * x.delta));
  const diff = score(item, cls) - score(worn, cls);
  return { slot, worn, rows, diff, better: worn ? diff > 0.5 : score(item, cls) > 0 };
}
