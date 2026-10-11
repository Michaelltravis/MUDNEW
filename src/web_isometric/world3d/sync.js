// Keeps the server's idea of "which room" in step with the hero, who walks freely.
//  - The hero walks from room A into room B: send "webmove A B" at once, never wait.
//  - move_result ok: confirmed. Refused: the server is still in A; the hero is slid back
//    into A with the server's reason, and any later queued moves are dropped (the server
//    refuses them anyway: they start from rooms it never reached).
//  - A map payload placing the player somewhere the client did not walk to (flee, recall,
//    goto, portals, following a leader, death) relocates the hero: the server's room wins.
export class Sync {
  constructor(host) {
    this.host = host;          // { heroRoomVnum(), refused(res), relocate(vnum), confirmed(vnum) }
    this.confirmed = null;     // the room the server says we are in
    this.queue = [];           // [{from, to, at}]
  }

  start(vnum) { this.confirmed = vnum; this.queue = []; }

  // `dir`: the exit taken (stairs and a doorway can lead to the same room)
  walked(from, to, dir = null) {
    MH.sendCommand(`webmove ${from} ${to}${dir ? ' ' + dir : ''}`, false);
    this.queue.push({ from, to, at: performance.now() });
  }

  onResult(res) {
    const i = this.queue.findIndex(q => q.from === res.from && q.to === res.to);
    if (i < 0) return;                         // a move we already gave up on
    if (res.ok) {
      this.queue.splice(0, i + 1);
      this.confirmed = res.room;
      this.host.confirmed(res.room);
      return;
    }
    this.queue = [];
    this.confirmed = res.room;
    this.host.refused(res);
  }

  onMap(payload) {
    const v = payload && payload.player && payload.player.vnum;
    if (!v) return;
    if (this.queue.some(q => q.to === v)) return;        // our own walk, result to follow
    if (this.queue.length) {
      // a payload from before our queued moves were processed: wait for the results,
      // unless they are overdue (a lost command) — then trust the payload
      if (performance.now() - this.queue[0].at < 4000) return;
      this.queue = [];
    }
    this.confirmed = v;
    if (v !== this.host.heroRoomVnum()) this.host.relocate(v);
  }

  // a move sent long ago with no answer: ask the server where we are
  tick() {
    if (this.queue.length && performance.now() - this.queue[0].at > 4000 && MH.refreshState) {
      this.queue[0].at = performance.now();
      MH.refreshState();
    }
  }
}
