// Real-time combat on the client (action_combat.py is the authority): the hero's swing clock
// and the global cooldown as the server last told them, running on between messages, so the
// attack key can show a blow at once when one is due and the HUD can draw the swing ring, the
// perfect-strike window and the cooldown sweep. Pure: no DOM, no three.js (Node tests).
export class ActionClock {
  constructor({ swing = 3, gcd = 1, perfect = 0.6, grace = 0.15 } = {}) {
    this.configure({ swing, gcd, perfect, grace });
    this.nextAt = 0;          // ms (performance.now) when the next swing is due
    this.gcdUntil = 0;        // ms when skills and casts may be used again
    this.queued = false;      // pressed before the clock came round (the swing comes by itself)
  }
  // /combatdata's `action`: {swing, gcd, perfect, grace} in seconds
  configure(d) {
    if (!d) return;
    if (d.swing) this.swing = d.swing * 1000;
    if (d.gcd) this.gcd = d.gcd * 1000;
    if (d.perfect) this.perfect = d.perfect * 1000;
    if (d.grace != null) this.grace = d.grace * 1000;
  }
  // the server's word on a swing: {res, next_ms, gcd_ms}. A cooldown the client has just
  // started is kept until the server says otherwise about that skill itself (res 'gcd'): a
  // swing's word may have left before the server saw the skill
  told(e, now) {
    if (!e) return;
    if (e.next_ms != null) this.nextAt = now + e.next_ms;
    if (e.gcd_ms != null) this.gcdUntil = e.res === 'gcd' ? now + e.gcd_ms : Math.max(this.gcdUntil, now + e.gcd_ms);
    if (e.res && e.res !== 'not_ready' && e.res !== 'perfect' && e.res !== 'gcd') this.queued = false;
  }
  ready(now) { return now >= this.nextAt; }
  // the attack key: a blow lands now (play it at once; the server's answer corrects the clock),
  // or it is early (the next swing comes by itself; inside the perfect window it lands perfectly)
  press(now) {
    if (this.ready(now)) {
      this.nextAt = now + this.swing;
      this.queued = false;
      return { swing: true, perfect: false };
    }
    this.queued = true;
    return { swing: false, perfect: this.inPerfect(now) };
  }
  // 0..1 of the way from the last swing to the next
  progress(now) {
    if (!this.nextAt) return 1;
    const p = 1 - (this.nextAt - now) / this.swing;
    return Math.max(0, Math.min(1, p));
  }
  inPerfect(now) { return now >= this.nextAt - this.perfect && now <= this.nextAt + this.grace; }
  gcdLeft(now) { return Math.max(0, this.gcdUntil - now); }
  // a skill or cast sent: its cooldown starts now (the server corrects it if it refused)
  startGcd(now) { this.gcdUntil = now + this.gcd; }
}
