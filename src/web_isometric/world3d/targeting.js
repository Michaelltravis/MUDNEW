// Who you are aiming at, and how a command names them. Pure (no THREE, no DOM): tested in Node.
//
// Entities are the client's records ({key, kind, vnum, data, aggroAt, pickedAt}); `data` comes
// from the server (name, hostile, flags, fighting, shopkeeper, trainer, quest, hp...).

// is this creature against you? (the server's `hostile` field is never set for most; its
// flags say 'aggressive'; anything fighting you or that hit you lately counts too)
export function isHostile(e, now = Date.now()) {
  if (!e || e.kind !== 'mob') return false;
  const d = e.data || {};
  return !!(d.hostile || d.fighting || (Array.isArray(d.flags) && d.flags.includes('aggressive'))
    || (e.aggroAt && now - e.aggroAt < 20000));
}

const fightingYou = (e, now) => !!(e && ((e.data && e.data.fighting) || (e.aggroAt && now - e.aggroAt < 6000)));
const deadOrGone = e => !e || (e.data && e.data.maxHp && e.data.hp != null && e.data.hp <= 0);

// Something attacked you: should the target switch to it?
//  switch: no target, a dead one, a player or a friendly NPC, one in another room, or one
//          that is not fighting you;
//  keep:   a live creature fighting you, or a hostile you picked by hand moments ago.
export function shouldRetarget(cur, attacker, roomVnum, now = Date.now()) {
  if (!attacker || attacker === cur) return false;
  if (!cur || deadOrGone(cur)) return true;
  if (cur.kind !== 'mob') return true;
  if (cur.vnum !== roomVnum) return true;
  if (cur.pickedAt && now - cur.pickedAt < 4000 && isHostile(cur, now)) return false;
  if (fightingYou(cur, now)) return false;
  return true;
}

// your target died: the creature that hit you most recently (within 8 s, in your room)
export function retargetOnDeath(list, roomVnum, now = Date.now()) {
  let best = null;
  for (const e of list) {
    if (e.kind !== 'mob' || e.vnum !== roomVnum || deadOrGone(e) || !e.aggroAt || now - e.aggroAt > 8000) continue;
    if (!best || e.aggroAt > best.aggroAt) best = e;
  }
  return best;
}

// how a command names an entity: '#<id>' for a creature (the server turns it into the right
// keyword), the name for another player
export function refFor(e) {
  if (!e) return '';
  if (e.kind === 'mob' && e.data && e.data.id != null) return `#${e.data.id}`;
  return String((e.data && e.data.name) || '').split(/\s+/)[0].toLowerCase();
}

// the command an action-bar ability sends: spells by their spoken name, skills by their id
// with underscores ("order verdict" would reach the pet-order command, "holy smite" the
// cleric's holy fire)
export function abilityCommand(ab, ref) {
  const base = ab.spell ? `cast '${ab.id.replace(/_/g, ' ')}'` : ab.id;
  return ref ? `${base} ${ref}` : base;
}

// how dangerous a creature is to you, by the levels between you (the target frame, nameplates)
export function conOf(level, mine) {
  const d = (Number(level) || 1) - (Number(mine) || 1);
  return d >= 5 ? { key: 'deadly', label: 'Deadly' } : d >= 3 ? { key: 'hard', label: 'Hard' }
    : d >= -2 ? { key: 'even', label: 'Even match' } : d >= -5 ? { key: 'easy', label: 'Easy' } : { key: 'trivial', label: 'Trivial' };
}
