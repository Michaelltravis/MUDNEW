import { keywordFor } from './hud/shop.js';

// Ground items in the map payload, and the words the MUD's `get` finds them by. Pure (no
// three.js): tested in Node; loot.js draws them.

// the game names a corpse "corpse of <whoever>" (combat.py)
export const isCorpse = item => /\bcorpse of\b/i.test(String((item && (item.name || item.short)) || ''));

// the word the MUD's `get` finds a ground item by, numbered when several share it ("2.corpse")
export function groundKeyword(item, roomItems) {
  const kw = isCorpse(item) ? 'corpse'
    : String(item.name || item.short || 'item').toLowerCase().split(/\s+/).find(w => w.length > 1) || 'item';
  let n = 0;
  for (const it of roomItems) {
    const words = String(it.name || it.short || '').toLowerCase().split(/\s+/);
    if (words.includes(kw) || (kw === 'corpse' && isCorpse(it))) n++;
    if (it === item) break;
  }
  return n > 1 ? `${n}.${kw}` : kw;
}

// every ground item in a payload, keyed so the same item keeps its place: [{key, vnum, item, kw, corpse}]
export function groundItems(payload) {
  const out = [];
  for (const r of (payload && payload.nearby) || []) {
    const seen = {};
    for (const it of (r.items || []).filter(i => !i.fixed)) {        // a fountain or a board is the room's, not loot
      const base = `${r.vnum}:${it.name || it.short}`;
      seen[base] = (seen[base] || 0) + 1;
      out.push({ key: `i${base}#${seen[base]}`, vnum: r.vnum, item: it, kw: groundKeyword(it, r.items), corpse: isCorpse(it) });
    }
  }
  return out;
}

// the rows of a corpse's window: its gold, then each thing in it, with the command that takes it
export function lootRows(corpse, corpseKw) {
  const rows = [];
  const from = `from ${corpseKw || 'corpse'}`;
  if (corpse && corpse.gold > 0) rows.push({ gold: corpse.gold, cmd: `get gold ${from}` });
  const list = (corpse && corpse.contents) || [];
  for (const it of list) rows.push({ item: it, cmd: `get ${keywordFor(it, list)} ${from}` });
  return rows;
}
