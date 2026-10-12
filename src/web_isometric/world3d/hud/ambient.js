// The world's murmurs in /play (the owner: "incorporate this into the game visual instead of the
// text like the old MUD"). The server's ambient lines (ambient_lines.py: only lines that fit the
// place) come here as events, never as chat: each plays its sound from where it comes from, a
// creature heard next door pings its room on the minimap and shows an arrow at the screen's edge
// with what it is, and the line itself is a caption only if the player asks for captions
// (Settings). No imports: the pure parts are tested in Node.

// a compass way as a world step (x east, z south); up and down come from where you stand
export const DIRS = { north: [0, -1], south: [0, 1], east: [1, 0], west: [-1, 0], up: [0, 0], down: [0, 0],
  northeast: [0.7, -0.7], northwest: [-0.7, -0.7], southeast: [0.7, 0.7], southwest: [-0.7, 0.7] };

// where a murmur sounds from (world x, z): the room it comes from, else the way it comes from, else
// somewhere about you (a place's own sounds: the smithy down the lane)
export function sourceOf(m, hero, centreOf, rng = Math.random) {
  if (m && m.room != null) {
    const c = centreOf && centreOf(m.room);
    if (c) return { x: c.x, z: c.z };
  }
  const v = m && DIRS[m.dir];
  if (v && (v[0] || v[1])) return { x: hero.x + v[0] * 14, z: hero.z + v[1] * 14 };
  const a = rng() * Math.PI * 2, d = 6 + rng() * 6;
  return { x: hero.x + Math.cos(a) * d, z: hero.z + Math.sin(a) * d };
}

// what a creature heard is called on the cue: its name without "a"/"the", capitalised
export function labelOf(m) {
  const n = String((m && m.name) || '').trim().replace(/^(a|an|the)\s+/i, '');
  return n ? n[0].toUpperCase() + n.slice(1) : 'Footsteps';
}

// the cue a murmur gets: a creature next door, or nothing (a place's sounds are only heard)
export function cueOf(m) {
  if (!m || m.key !== 'presence') return null;
  return { label: labelOf(m), dir: m.dir || '', room: m.room ?? null, moving: !!m.moving };
}

// the screen angle (radians clockwise from up) toward a world point, for a camera turned by yaw
// (audio.js: screen-right is (cos yaw, -sin yaw))
export function screenAngle(from, to, yaw = 0) {
  const dx = to.x - from.x, dz = to.z - from.z;
  const right = dx * Math.cos(yaw) - dz * Math.sin(yaw);
  const up = -dx * Math.sin(yaw) - dz * Math.cos(yaw);
  return Math.atan2(right, up);
}

const CUE_MS = 4200, CAPTION_MS = 6000;

// root: the #amb-cue element (an arrow and a label); caption: #amb-caption
export function createAmbient({ sound, hero, camYaw, centreOf, minimaps = [], root, caption, captions }) {
  let cue = null, capT = 0;
  function on(m) {
    if (!m) return;
    const h = hero();
    if (!h) return;
    const at = sourceOf(m, h, centreOf);
    if (m.sound && sound) sound.play(m.sound, { at });
    const c = cueOf(m);
    if (c) {
      if (c.room != null) for (const mm of minimaps) mm && mm.ping(c.room, 'danger');
      cue = { ...c, at, t0: performance.now() };
      root.querySelector('.lab').textContent = c.label;
      root.querySelector('.sub').textContent = c.moving ? 'moving nearby' : c.dir === 'up' ? 'above' : c.dir === 'down' ? 'below' : `to the ${c.dir}`;
      root.classList.remove('hidden');
    }
    if (captions && captions() && m.text && caption) {
      caption.textContent = m.text;
      caption.classList.remove('hidden');
      capT = performance.now();
    }
  }
  // every frame: the arrow points at what was heard as the hero and camera move; then fades
  function update() {
    const now = performance.now();
    if (capT && now - capT > CAPTION_MS) { caption.classList.add('hidden'); capT = 0; }
    if (!cue) return;
    const age = (now - cue.t0) / CUE_MS;
    if (age >= 1) { cue = null; root.classList.add('hidden'); return; }
    const h = hero();
    if (!h) return;
    const ang = screenAngle(h, cue.at, camYaw ? camYaw() : 0);
    const w = window.innerWidth, hh = window.innerHeight, R = Math.min(w, hh) * 0.36;
    const x = w / 2 + Math.sin(ang) * R, y = hh / 2 - Math.cos(ang) * R;
    root.style.transform = `translate(${x.toFixed(0)}px, ${y.toFixed(0)}px) translate(-50%, -50%)`;
    root.querySelector('.arrow').style.transform = `rotate(${ang}rad)`;
    root.style.opacity = String(age < 0.75 ? 1 : 1 - (age - 0.75) / 0.25);
  }
  return { on, update };
}
