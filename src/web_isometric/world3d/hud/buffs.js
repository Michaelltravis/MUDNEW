// The buff bar's list (hud.js renderBuffs): one icon a spell. A spell sets several affects (Armor
// both its armour and its ward), each its own entry; they show as one, with the longest time left.
export function buffList(aff, max = 12) {
  const seen = new Map();
  for (const a of aff || []) {
    if (!a || !(a.name || a.spell)) continue;
    const k = String(a.name || a.spell).toLowerCase();
    const was = seen.get(k);
    const left = x => (x.remaining != null ? x.remaining : x.duration) || 0;
    if (!was || left(a) > left(was)) seen.set(k, a);
  }
  return [...seen.values()].slice(0, max);
}
