// What you can do about a blow that is coming (a creature's wind-up, combat_events 'windup'):
// Q braces (halves a heavy or area blow and shrugs off its stun), E sidesteps out of it (your own
// swing is spent), X interrupts a cast. They are everyone's (the server's `brace`, `sidestep`,
// `interrupt`, each on its own cooldown) and need no slot on the bar. Pure: tested in Node.

export const REACTIONS = {
  q: { cmd: 'brace', label: 'Brace' },
  e: { cmd: 'sidestep', label: 'Sidestep' },
  x: { cmd: 'interrupt', label: 'Interrupt' },
};

// the keys that answer this wind-up: a cast can be interrupted (when the server says so) or
// braced; a heavy or area blow braced or stepped out of
export function reactionKeys(w) {
  if (!w) return [];
  const kind = w.kind || 'heavy';
  const keys = [];
  if (kind === 'cast') {
    if (w.interruptible) keys.push('x');          // the event says so only when it can be
    keys.push('q');
  } else {
    keys.push('q', 'e');
    if (w.interruptible) keys.push('x');
  }
  return keys;
}

// is this wind-up the hero's problem? aimed at them, or its marked ground holds them
export function threatens(e, isHero, inArea) {
  if (!e || e.k !== 'windup') return false;
  return !!((e.dst && isHero(e.dst)) || (inArea && inArea(e)));
}

// one wind-up at a time: the newest that threatens the hero, until it lands or is broken
export class ReactionPrompt {
  constructor() { this.cur = null; }
  windup(e, now) {
    const ms = Math.max(400, e.ms || 1500);
    this.cur = { src: e.src && e.src.m, label: e.label || 'A heavy blow', kind: e.kind || 'heavy',
      interruptible: e.interruptible, until: now + ms + 250, span: ms + 250, keys: reactionKeys(e), used: null };
    return this.cur;
  }
  end(srcId) { if (this.cur && (srcId == null || this.cur.src === srcId)) this.cur = null; }
  // the command a key press sends, or null (no wind-up, not one of its keys, or already answered)
  press(key, now) {
    const c = this.cur;
    if (!c || now > c.until) { this.cur = null; return null; }
    const k = String(key || '').toLowerCase();
    if (!c.keys.includes(k) || c.used) return null;
    c.used = k;
    return REACTIONS[k].cmd;
  }
  active(now) { if (this.cur && now > this.cur.until) this.cur = null; return this.cur; }
}
