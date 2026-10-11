// What the right-click menu offers for what is under the cursor. Pure (no DOM): tested in Node.
// Each verb is {label, cmd} (a server command to send), {label, act} (something main.js does:
// 'attack', 'target', 'walk', 'inventory', 'character', 'door:<action>') or {label} (greyed).
import { doorVerbs } from '../doorlogic.js';
import { refFor, isHostile } from '../targeting.js';

const cap = s => s ? s[0].toUpperCase() + s.slice(1) : s;
const keyword = name => {
  const words = String(name || '').toLowerCase().replace(/[^a-z' ]/g, '').split(/\s+/)
    .filter(w => w && !['a', 'an', 'the', 'some', 'of'].includes(w));
  return words[words.length - 1] || 'mob';
};

// hit: {kind: 'mob'|'player'|'self'|'door'|'ground', ent?, door?: {dir, info}, point?}
// ctx: {skills: [{id, label, spell}] (targetable bar abilities), posture, inCombat}
export function verbsFor(hit, ctx = {}) {
  if (!hit) return { title: '', items: [] };
  if (hit.kind === 'mob') {
    const d = hit.ent.data || {};
    const ref = refFor(hit.ent), kw = keyword(d.name);
    const title = `${cap(d.name || 'creature')}${d.level ? ` · level ${d.level}` : ''}`;
    const npc = d.shopkeeper || d.trainer || d.quest || ['innkeeper', 'banker', 'healer', 'stable_master', 'receptionist'].includes(d.special);
    const items = [];
    if (npc && !isHostile(hit.ent)) {
      items.push({ label: 'Talk', cmd: `talk ${kw}` });
      if (d.shopkeeper) items.push({ label: 'Shop', cmd: 'list' });
      if (d.trainer) items.push({ label: 'Master your abilities', act: 'trainer' });
      if (d.special === 'innkeeper' || d.special === 'receptionist') items.push({ label: 'Rent a room', cmd: 'rent' });
      if (d.special === 'banker') items.push({ label: 'Bank balance', cmd: 'balance' });
      items.push({ label: 'Look', cmd: `look ${kw}` }, { label: 'Target', act: 'target' }, { label: 'Attack', act: 'attack' });
    } else {
      items.push({ label: 'Attack', act: 'attack' });
      for (const s of (ctx.skills || []).slice(0, 3)) items.push({ label: s.label, act: `ability:${s.id}` });
      items.push({ label: 'Target', act: 'target' }, { label: 'Consider', cmd: `consider ${ref}` }, { label: 'Look', cmd: `look ${kw}` });
      if (d.quest) items.push({ label: 'Talk', cmd: `talk ${kw}` });
    }
    return { title, items };
  }
  if (hit.kind === 'player') {
    const d = hit.ent.data || {};
    const name = String(d.name || '').split(/\s+/)[0];
    // inviting, following and trading need them in your room (the server's rule)
    const near = ctx.room == null || hit.ent.vnum === ctx.room;
    const far = label => ({ label: `${label} (walk closer)` });
    return {
      title: `${name}${d.level ? ` · level ${d.level}` : ''}${d.char_class ? ` ${d.char_class}` : ''}${d.groupmate ? ' · your group' : ''}`,
      items: [
        { label: 'Look', cmd: `look ${name}` },
        { label: 'Whisper…', act: `tell:${name}` },
        d.groupmate ? { label: 'In your group' } : near ? { label: 'Invite to group', cmd: `group invite ${name}` } : far('Invite to group'),
        near ? { label: 'Follow', cmd: `follow ${name}` } : far('Follow'),
        { label: 'Assist', cmd: `assist ${name}` },
        near ? { label: 'Trade', cmd: `trade ${name}` } : far('Trade'),
        { label: 'Target', act: 'target' },
      ],
    };
  }
  if (hit.kind === 'door') {
    const info = hit.door.info || {};
    return {
      title: cap(info.label || 'door'),
      items: doorVerbs(info).map(v => (v.action ? { label: v.label, act: `door:${v.action}` } : { label: v.label })),
    };
  }
  if (hit.kind === 'self') {
    const p = ctx.posture || 'standing';
    const items = [{ label: 'Character', act: 'character' }, { label: 'Inventory', act: 'inventory' }, { label: 'Score', cmd: 'score' }];
    if (!ctx.inCombat) {
      if (p !== 'standing') items.push({ label: 'Stand up', cmd: 'stand' });
      if (p !== 'resting') items.push({ label: 'Rest', cmd: 'rest' });
      if (p !== 'sleeping') items.push({ label: 'Sleep', cmd: 'sleep' });
      items.push({ label: 'Recall to town', cmd: 'recall' });
    } else items.push({ label: 'Flee', cmd: 'flee' });
    if (ctx.inGroup) items.push({ label: 'Leave group', cmd: 'group leave' });
    return { title: 'You', items };
  }
  return { title: '', items: [{ label: 'Walk here', act: 'walk' }] };
}
