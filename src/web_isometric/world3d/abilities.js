// Your own action bar and the spellbook's bookkeeping. Pure (no DOM): tests/web run it.
//
// The player payload lists every ability of the class (`abilities`: id, name, type, pct,
// level it unlocks at, known, cost, cooldown, range, target, description) and the bar the
// player arranged (`bar`: 16 ability ids or null — keys 1-8, then Shift+1-8). Abilities are
// learned by reaching their level (at 50%), improve as they are used (to 85%, "Mastered"),
// and a trainer teaches the rest (to 100%).
export const SLOTS = 16;
export const BY_USE = 85;

// what a proficiency is called
export function rankOf(pct) {
  const p = Number(pct) || 0;
  return p >= 100 ? 'Perfected' : p >= BY_USE ? 'Mastered' : p >= 80 ? 'Expert' : p >= 70 ? 'Adept' : p >= 60 ? 'Apprentice' : p > 0 ? 'Novice' : 'Not learned';
}

// the abilities you can put on the bar (passives work on their own)
export const usable = a => !!(a && a.known && !a.passive);
export function knownIds(abilities) {
  return new Set((abilities || []).filter(usable).map(a => a.id));
}

// a bar from the server, kept to abilities you still know, always SLOTS long
export function cleanBar(bar, abilities) {
  const known = knownIds(abilities), out = new Array(SLOTS).fill(null), seen = new Set();
  (Array.isArray(bar) ? bar : []).slice(0, SLOTS).forEach((id, i) => {
    if (id && known.has(id) && !seen.has(id)) { out[i] = id; seen.add(id); }
  });
  return out;
}

// a first bar for a character who never arranged one: the class's usual order, then the rest
// of what is known by the level it came at
export function defaultBar(abilities, order = []) {
  const known = (abilities || []).filter(usable);
  const rank = id => { const i = order.indexOf(id); return i < 0 ? 1e3 : i; };
  const ids = known.slice().sort((a, b) => rank(a.id) - rank(b.id) || (a.level || 0) - (b.level || 0) || String(a.id).localeCompare(b.id))
    .map(a => a.id);
  const bar = new Array(SLOTS).fill(null);
  ids.slice(0, SLOTS).forEach((id, i) => { bar[i] = id; });
  return bar;
}

// newly learned abilities take the first free slots (the top row first); returns where
export function placeNew(bar, ids) {
  const out = bar.slice(), placed = [];
  for (const id of ids) {
    if (out.includes(id)) continue;
    const i = out.indexOf(null);
    if (i < 0) break;
    out[i] = id;
    placed.push({ id, slot: i });
  }
  return { bar: out, placed };
}

// put an ability in a slot: one already on the bar swaps places with what is there
export function putOnBar(bar, id, slot) {
  if (slot < 0 || slot >= SLOTS) return bar.slice();
  const out = bar.slice(), from = out.indexOf(id);
  if (from === slot) return out;
  if (from >= 0) out[from] = out[slot];
  out[slot] = id;
  return out;
}

export function takeOffBar(bar, slot) {
  const out = bar.slice();
  if (slot >= 0 && slot < SLOTS) out[slot] = null;
  return out;
}

// what changed between two payloads: abilities learned, and proficiencies that grew
export function diffAbilities(prev, next) {
  const before = new Map((prev || []).map(a => [a.id, a]));
  const learned = [], improved = [];
  for (const a of next || []) {
    const b = before.get(a.id);
    if (a.known && !(b && b.known)) learned.push(a.id);
    else if (a.known && b && (a.pct || 0) > (b.pct || 0)) improved.push({ id: a.id, from: b.pct || 0, to: a.pct || 0 });
  }
  return { learned, improved };
}

// the line under an ability's name: cost, cooldown, range
export function costLine(a) {
  if (a.passive) return 'Passive — always at work';
  const parts = [];
  if (a.cost) parts.push(`${a.cost} ${a.res || 'mana'}`);
  if (a.cd) parts.push(`${a.cd >= 60 ? `${Math.round(a.cd / 60)} min` : `${a.cd} s`} cooldown`);
  if (a.target === 'self') parts.push('yourself');
  else if (a.target === 'area') parts.push(a.range ? `all around, ${a.range} m` : 'all around');
  else if (a.range) parts.push(a.range <= 3 ? 'melee' : `${a.range} m`);
  return parts.join(' · ');
}
