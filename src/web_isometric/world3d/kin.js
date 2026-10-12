// The creature kit: a body built from a recipe (kinrecipe.js), each kind of creature its own.
// A few skeletons (four-legged beasts, birds, swimmers; more in later pushes), each with parts
// that swap in and out (heads, ears, horns, tails, wings, fins), proportions, a coat and its
// markings. Low-poly primitives with flat shading, to sit with the rest of the art, animated in
// code through proc.js's ProcActor (idle, walk, attack, hit, death), so entities.js treats a kit
// body like any other. Built 1 m tall; `height` scales it.
import * as THREE from 'three';
import { ProcActor } from './proc.js';
import { rng } from './kinrecipe.js';

const mat = (color, extra = {}) => new THREE.MeshStandardMaterial({ color, roughness: 0.85, flatShading: true, ...extra });
const DARK_EYE = new THREE.MeshBasicMaterial({ color: 0x141210 });
const GLOW_EYE = new THREE.MeshBasicMaterial({ color: new THREE.Color(2.0, 0.9, 0.25) });
const HOOF = mat(0x2e2824), HORN = mat(0xd8ceb4), BEAK = mat(0xd8a040), PINK = mat(0xc88a8a);
const sph = (r, w = 8, h = 6) => new THREE.SphereGeometry(r, w, h);
const cyl = (a, b, len, n = 6) => new THREE.CylinderGeometry(a, b, len, n);
const cone = (r, len, n = 6) => new THREE.ConeGeometry(r, len, n);
const box = (x, y, z) => new THREE.BoxGeometry(x, y, z);

function m(geo, material, x = 0, y = 0, z = 0, sx = 1, sy = 1, sz = 1) {
  const o = new THREE.Mesh(geo, material);
  o.position.set(x, y, z);
  o.scale.set(sx, sy, sz);
  o.castShadow = true;
  return o;
}
function grp(parent, x = 0, y = 0, z = 0) {
  const g = new THREE.Group();
  g.position.set(x, y, z);
  parent.add(g);
  return g;
}
// a limb hanging down from its joint (a cylinder whose top is at the group's origin)
function limb(len, r0, r1, material) {
  const geo = cyl(r0, r1, len, 6);
  geo.translate(0, -len / 2, 0);
  return m(geo, material);
}

// ---------------------------------------------------------------- four-legged beasts
function quad(k) {
  const root = new THREE.Group(), body = new THREE.Group();
  root.add(body);
  const coat = mat(k.c.main), belly = mat(k.c.belly), accent = mat(k.c.accent);
  const eye = k.c.eye === 'glow' ? GLOW_EYE : DARK_EYE;
  const scaled = k.fur === 'scale', shaggy = k.fur === 'shaggy';
  const L = k.leg, G = k.girth, D = k.len, sprawl = k.gait === 'sprawl';
  const torsoY = (sprawl ? L * 0.7 : L) + G * 0.85;
  const torso = m(sph(0.5, 10, 8), coat, 0, torsoY, 0, G * 1.9, G * 1.8, D);
  body.add(torso);
  body.add(m(sph(0.5, 9, 7), belly, 0, torsoY - G * 0.28, 0.02, G * 1.6, G * 1.2, D * 0.86));
  if (shaggy) for (let i = 0; i < 7; i++) {
    const z = D * (0.38 - i * 0.12), s = 0.55 + ((k.seed >> i) & 3) * 0.08;
    body.add(m(sph(G * 0.42 * s, 6, 5), coat, ((i % 2) - 0.5) * G * 0.5, torsoY + G * 0.72, z, 1.2, 0.8, 1.3));
  }
  // markings
  if (k.pattern === 'saddle') body.add(m(sph(0.5, 10, 6), accent, 0, torsoY + G * 0.3, -D * 0.05, G * 1.75, G * 1.2, D * 0.7));
  if (k.pattern === 'stripes') for (let i = 0; i < 5; i++) body.add(m(box(G * 1.95, G * 0.5, 0.035), accent, 0, torsoY + G * 0.35, D * (0.3 - i * 0.14)));
  if (k.pattern === 'spots') { const r = rng(k.seed + 7); for (let i = 0; i < 7; i++) body.add(m(sph(G * 0.16, 6, 4), accent, (r() - 0.5) * G * 1.4, torsoY + G * (0.45 + r() * 0.35), (r() - 0.5) * D * 0.8, 1, 0.4, 1)); }
  if (k.spikes || scaled) for (let i = 0; i < 6; i++) body.add(m(cone(G * 0.12, G * (k.spikes ? 0.5 : 0.25), 4), accent, 0, torsoY + G * 0.95, D * (0.36 - i * 0.14)));
  // legs: hips under the torso's four corners
  const legs = [];
  const hoofed = /^(long|snout)$/.test(k.head) || k.horns !== 'none' || k.tail === 'tuft';
  const legR = Math.max(0.035, G * (shaggy ? 0.2 : 0.16));
  for (const [sx, sz] of [[-1, 1], [1, 1], [-1, -1], [1, -1]]) {
    const hip = grp(body, sx * G * 0.6, torsoY - G * 0.35, sz * D * 0.32);
    const len = sprawl ? L * 0.95 : L + G * 0.5;
    const leg = limb(len, legR, legR * 0.75, k.pattern === 'socks' ? coat : coat);
    if (sprawl) hip.rotation.z = sx * 0.9;
    hip.add(leg);
    hip.add(m(sph(legR * 1.15, 6, 4), hoofed ? HOOF : k.pattern === 'socks' ? belly : accent, 0, -len, 0.02, 1, 0.6, 1.3));
    if (k.pattern === 'socks') hip.add(m(cyl(legR * 1.02, legR * 0.85, len * 0.3, 6), belly, 0, -len * 0.82, 0));
    legs.push({ hip, phase: sx * sz > 0 ? 0 : Math.PI });
  }
  // neck and head at the front
  const neck = grp(body, 0, torsoY + G * 0.35, D * 0.42);
  const N = Math.max(0.08, k.neck);
  const neckMesh = m(cyl(G * 0.42, G * 0.55, N + G * 0.4, 7), coat);
  neckMesh.position.set(0, N * 0.35, N * 0.25);
  neckMesh.rotation.x = 0.6;
  neck.add(neckMesh);
  if (k.mane) for (let i = 0; i < 5; i++) neck.add(m(box(0.05, G * 0.35, G * 0.3), accent, 0, N * 0.2 + i * N * 0.16 + G * 0.2, N * 0.05 + i * N * 0.07 - G * 0.25));
  const head = grp(neck, 0, N * 0.7 + G * 0.15, N * 0.55 + G * 0.2);
  const H = G * 0.95 * k.headSize;
  head.add(m(sph(H * 0.5, 8, 6), coat, 0, 0, 0, 1, 0.95, 1.05));
  if (k.head === 'pointed') head.add(m(cone(H * 0.32, H * 0.8, 7), coat, 0, -H * 0.08, H * 0.6).rotateX(Math.PI / 2));
  if (k.head === 'long') head.add(m(cyl(H * 0.22, H * 0.3, H * 1.0, 7), coat, 0, -H * 0.12, H * 0.62).rotateX(Math.PI / 2));
  if (k.head === 'blunt') head.add(m(sph(H * 0.3, 7, 5), belly, 0, -H * 0.14, H * 0.4, 1.1, 0.8, 0.9));
  if (k.head === 'snout') { head.add(m(cyl(H * 0.24, H * 0.28, H * 0.45, 8), coat, 0, -H * 0.06, H * 0.5).rotateX(Math.PI / 2)); head.add(m(cyl(H * 0.2, H * 0.2, 0.02, 8), PINK, 0, -H * 0.06, H * 0.73).rotateX(Math.PI / 2)); }
  const tipZ = { pointed: H * 0.98, long: H * 1.1, blunt: H * 0.62, snout: H * 0.74 }[k.head] || H * 0.6;
  head.add(m(sph(H * 0.07, 5, 4), DARK_EYE, 0, -H * 0.06, tipZ));
  if (k.pattern === 'blaze') head.add(m(box(H * 0.14, 0.02, H * 0.7), belly, 0, H * 0.4, H * 0.25));
  for (const s of [-1, 1]) head.add(m(sph(H * 0.075, 6, 4), eye, s * H * 0.24, H * 0.1, H * 0.34));
  // ears
  const E = H * k.earSize;
  for (const s of [-1, 1]) {
    if (k.ears === 'pointed') head.add(m(cone(E * 0.13, E * 0.34, 4), coat, s * H * 0.24, H * 0.42, -H * 0.04).rotateZ(-s * 0.25));
    else if (k.ears === 'tall') head.add(m(cone(E * 0.14, E * 0.55, 4), coat, s * H * 0.24, H * 0.52, -H * 0.04).rotateZ(-s * 0.2));
    else if (k.ears === 'round') head.add(m(sph(E * 0.14, 6, 4), accent, s * H * 0.3, H * 0.38, -H * 0.05, 1, 1, 0.5));
    else if (k.ears === 'floppy') head.add(m(sph(E * 0.16, 6, 4), accent, s * H * 0.42, H * 0.12, -H * 0.05, 0.5, 1.4, 0.9));
    else if (k.ears === 'long') head.add(m(sph(E * 0.14, 6, 4), coat, s * H * 0.16, H * 0.82, -H * 0.12, 0.6, 3.0, 0.5).rotateZ(-s * 0.12));
  }
  // horns
  for (const s of [-1, 1]) {
    if (k.horns === 'horns') { const h = m(cone(H * 0.08, H * 0.6, 6), HORN, s * H * 0.42, H * 0.36, 0); h.rotation.z = -s * 1.0; head.add(h); }
    else if (k.horns === 'curled') { const t = new THREE.Mesh(new THREE.TorusGeometry(H * 0.2, H * 0.06, 5, 10, Math.PI * 1.4), HORN); t.position.set(s * H * 0.3, H * 0.3, -H * 0.05); t.rotation.y = s * Math.PI / 2; t.castShadow = true; head.add(t); }
    else if (k.horns === 'antlers') {
      const a = grp(head, s * H * 0.18, H * 0.4, -H * 0.05);
      a.rotation.z = -s * 0.45;
      a.add(m(cyl(H * 0.03, H * 0.04, H * 0.9, 5), HORN, 0, H * 0.45, 0));
      for (let i = 0; i < 3; i++) { const b = m(cyl(H * 0.022, H * 0.03, H * 0.4, 4), HORN, s * H * 0.12, H * (0.35 + i * 0.22), H * 0.08); b.rotation.z = -s * 0.9; b.rotation.x = 0.3; a.add(b); }
    } else if (k.horns === 'tusks') { const t = m(cone(H * 0.08, H * 0.45, 5), HORN, s * H * 0.2, -H * 0.02, tipZ * 0.8); t.rotation.x = -0.25; t.rotation.z = -s * 0.35; head.add(t); }
  }
  if (k.horns === 'spike') { const h = m(cone(H * 0.07, H * 0.8, 6), HORN, 0, H * 0.55, H * 0.25); h.rotation.x = 0.4; head.add(h); }
  // tail
  const tail = grp(body, 0, torsoY + G * 0.25, -D * 0.48);
  const T = k.tailLen;
  if (k.tail === 'bushy') { const t = m(sph(G * 0.32, 7, 5), coat, 0, -G * 0.2 * T, -G * 0.55 * T, 0.8, 0.8, 2.0 * T); t.rotation.x = 0.6; tail.add(t); tail.add(m(sph(G * 0.18, 6, 4), belly, 0, -G * 0.55 * T, -G * 1.05 * T)); }
  else if (k.tail === 'thin' || k.tail === 'long') { const n = k.tail === 'long' ? 7 : 5; for (let i = 0; i < n; i++) tail.add(m(sph(G * (0.1 - i * 0.008), 5, 4), coat, 0, -i * G * 0.06, -i * G * 0.22 * T)); }
  else if (k.tail === 'tuft') { tail.add(m(cyl(G * 0.05, G * 0.04, G * 0.9 * T, 5), coat, 0, -G * 0.45 * T, -G * 0.1).rotateX(0.3)); tail.add(m(sph(G * 0.14, 6, 4), accent, 0, -G * 0.9 * T, -G * 0.3, 0.8, 1.4, 0.8)); }
  else if (k.tail === 'curl') { const t = new THREE.Mesh(new THREE.TorusGeometry(G * 0.12, G * 0.035, 4, 8, Math.PI * 1.6), PINK); t.position.set(0, 0, -G * 0.1); t.castShadow = true; tail.add(t); }
  else if (k.tail === 'puff') tail.add(m(sph(G * 0.2, 6, 5), belly));
  else if (k.tail === 'stub') tail.add(m(sph(G * 0.12, 5, 4), coat, 0, 0, -G * 0.05));
  else if (k.gait === 'sprawl' || k.tail === 'scale') for (let i = 0; i < 6; i++) tail.add(m(sph(G * (0.2 - i * 0.03), 5, 4), coat, 0, -i * G * 0.04, -i * G * 0.3));
  const hopper = k.gait === 'hop';
  return finish(root, body, (t, st, a) => {
    const sp = st === 'walk' ? (hopper ? 9 : 11) : 2;
    if (hopper) {
      const h = st === 'walk' ? Math.max(0, Math.sin(t * sp)) : 0;
      body.position.y = h * 0.18;
      legs.forEach(l => { l.hip.rotation.x = st === 'walk' ? Math.sin(t * sp) * 0.6 : 0; });
    } else {
      body.position.y = st === 'walk' ? Math.abs(Math.sin(t * sp)) * 0.025 : Math.sin(t * 1.6) * 0.006;
      legs.forEach(l => { l.hip.rotation.x = st === 'walk' ? Math.sin(t * sp + l.phase) * 0.55 : Math.sin(t * 1.2 + l.phase) * 0.02; });
      if (sprawl) body.rotation.y = st === 'walk' ? Math.sin(t * sp) * 0.12 : 0;
    }
    torso.scale.y = G * 1.8 * (1 + Math.sin(t * 2.2) * 0.015);
    tail.rotation.y = Math.sin(t * (st === 'walk' ? 9 : 2.2)) * (k.tail === 'stub' ? 0.1 : 0.4);
    const strike = st === 'attack' ? Math.sin(a * Math.PI) : 0;
    neck.rotation.x = strike * (k.horns !== 'none' ? 0.7 : 0.45) + (st === 'idle' ? Math.sin(t * 0.7) * 0.06 : 0);
    neck.position.z = D * 0.42 + strike * 0.12;
    body.rotation.x = st === 'hit' ? -Math.sin(a * Math.PI) * 0.15 : (hopper ? 0 : 0);
  });
}

// ---------------------------------------------------------------- birds
function bird(k) {
  const root = new THREE.Group(), body = new THREE.Group();
  root.add(body);
  const plume = mat(k.c.main), breast = mat(k.c.belly), accent = mat(k.c.accent);
  const eye = k.c.eye === 'glow' ? GLOW_EYE : DARK_EYE;
  const upright = k.stance === 'upright', leather = k.wingType === 'leather';
  const L = k.leg, G = k.girth;
  const bodyY = L + G * (upright ? 1.25 : 0.85);
  const torso = m(sph(0.5, 10, 8), plume, 0, bodyY, 0, G * 1.5, G * (upright ? 2.6 : 1.6), G * (upright ? 1.4 : 2.3));
  if (!upright) torso.rotation.x = -0.25;
  body.add(torso);
  body.add(m(sph(0.5, 9, 7), breast, 0, bodyY - G * 0.12, G * 0.22, G * 1.25, G * (upright ? 2.2 : 1.3), G * (upright ? 1.0 : 1.6)));
  if (k.pattern === 'collar') body.add(m(new THREE.TorusGeometry(G * 0.42, G * 0.08, 4, 10), accent, 0, bodyY + G * (upright ? 1.0 : 0.62), G * 0.55).rotateX(Math.PI / 2.4));
  // head on its neck
  const neck = grp(body, 0, bodyY + G * (upright ? 1.1 : 0.55), G * (upright ? 0.15 : 0.8));
  const NL = k.neckLong ? G * 1.6 : G * 0.25;
  if (k.neckLong) neck.add(m(cyl(G * 0.13, G * 0.18, NL, 6), plume, 0, NL / 2, 0.05));
  const head = grp(neck, 0, NL + G * 0.2, k.neckLong ? 0.08 : 0);
  const H = G * 0.9 * k.headSize;
  head.add(m(sph(H * 0.5, 8, 6), k.pattern === 'cap' ? accent : plume));
  if (k.pattern === 'cap') head.add(m(sph(H * 0.5, 8, 6), breast, 0, -H * 0.12, H * 0.05, 0.95, 0.7, 0.95));
  const beakLen = { short: H * 0.35, hook: H * 0.4, straight: H * 0.55, long: H * 1.4, flat: H * 0.5, snout: H * 0.15 }[k.beak] || H * 0.35;
  if (k.beak === 'flat') head.add(m(box(H * 0.32, H * 0.08, beakLen), BEAK, 0, -H * 0.08, H * 0.42 + beakLen / 2));
  else if (k.beak === 'snout') head.add(m(sph(H * 0.18, 6, 4), plume, 0, -H * 0.05, H * 0.45));
  else {
    head.add(m(cone(H * 0.12, beakLen, 5), BEAK, 0, -H * 0.04, H * 0.42 + beakLen / 2).rotateX(Math.PI / 2));
    if (k.beak === 'hook') head.add(m(cone(H * 0.06, H * 0.16, 4), BEAK, 0, -H * 0.16, H * 0.42 + beakLen * 0.9).rotateX(Math.PI));
  }
  if (k.face === 'owl') for (const s of [-1, 1]) { head.add(m(sph(H * 0.2, 8, 4), breast, s * H * 0.2, H * 0.06, H * 0.36, 1, 1, 0.3)); head.add(m(sph(H * 0.09, 6, 4), k.c.eye === 'glow' ? GLOW_EYE : mat(0xe8b830), s * H * 0.2, H * 0.06, H * 0.43)); }
  else for (const s of [-1, 1]) head.add(m(sph(H * 0.08, 6, 4), eye, s * H * 0.34, H * 0.1, H * 0.2));
  if (k.ears) for (const s of [-1, 1]) head.add(m(cone(H * 0.15, H * 0.5, 4), accent, s * H * 0.22, H * 0.5, -H * 0.02));
  if (k.crest === 'tuft') for (let i = 0; i < 3; i++) head.add(m(cone(H * 0.06, H * 0.4, 4), accent, 0, H * 0.55, -H * 0.1 - i * H * 0.12).rotateX(-0.6 - i * 0.2));
  if (k.crest === 'comb') for (let i = 0; i < 3; i++) head.add(m(box(0.03, H * 0.22, H * 0.14), mat(0xc83020), 0, H * 0.55, H * 0.1 - i * H * 0.13));
  // wings
  const wings = [];
  const W = k.wing;
  for (const s of [-1, 1]) {
    const sh = grp(body, s * G * 0.7, bodyY + G * 0.35, upright ? 0 : G * 0.25);
    if (leather) {
      const arm = m(cyl(0.02, 0.015, W, 4), accent, s * W * 0.5, 0, 0); arm.rotation.z = Math.PI / 2; sh.add(arm);
      const web = new THREE.Mesh(new THREE.ConeGeometry(W * 0.5, W * 0.9, 3, 1), mat(k.c.accent, { side: THREE.DoubleSide }));
      web.scale.set(1, 1, 0.05); web.rotation.z = s * Math.PI / 2; web.position.set(s * W * 0.45, -W * 0.15, 0); web.castShadow = true; sh.add(web);
    } else {
      sh.add(m(sph(0.5, 8, 5), plume, s * W * 0.25, -G * 0.15, -W * 0.25, W * 0.6, 0.08, W * 0.9).rotateY(s * 0.15));
      if (k.pattern === 'bars') for (let i = 0; i < 3; i++) sh.add(m(box(W * 0.5, 0.05, 0.03), accent, s * W * 0.25, -G * 0.11, -W * (0.05 + i * 0.16)));
    }
    if (upright) sh.rotation.z = s * 0.15;
    wings.push({ sh, s });
  }
  // tail
  if (k.tail === 'fan') body.add(m(cone(G * 0.45, G * 1.0, 5), accent, 0, bodyY - G * 0.05, -G * 1.15, 1, 0.15, 1).rotateX(-Math.PI / 2 + 0.25));
  if (k.tail === 'plume') for (let i = 0; i < 3; i++) body.add(m(box(0.04, G * 0.9, G * 0.25), accent, (i - 1) * 0.06, bodyY + G * 0.3, -G * 0.95).rotateX(-0.5 - i * 0.15));
  // legs
  const legs = [];
  for (const s of [-1, 1]) {
    const hip = grp(body, s * G * 0.3, bodyY - G * (upright ? 1.0 : 0.6), upright ? 0.05 : 0);
    hip.add(limb(L + G * 0.2, 0.025, 0.02, BEAK));
    hip.add(m(box(0.12, 0.02, 0.16), BEAK, 0, -(L + G * 0.2), 0.05));
    legs.push(hip);
  }
  const flier = !upright;
  return finish(root, body, (t, st, a) => {
    const walking = st === 'walk';
    const flap = walking && flier ? Math.sin(t * (leather ? 16 : 13)) : Math.sin(t * 2) * 0.05;
    wings.forEach(({ sh, s }) => { sh.rotation.z = s * (walking && flier ? 0.2 + flap * 0.9 : (upright ? 0.15 + Math.sin(t * 8) * (walking ? 0.25 : 0.02) : 0.05 + flap * 0.1)); });
    if (upright) { body.rotation.z = walking ? Math.sin(t * 7) * 0.12 : 0; legs.forEach((l, i) => { l.rotation.x = walking ? Math.sin(t * 7 + i * Math.PI) * 0.4 : 0; }); }
    else legs.forEach((l, i) => { l.rotation.x = walking ? -0.9 : Math.sin(t * 1.3 + i) * 0.03; });
    body.position.y = walking && flier ? 0.08 + flap * 0.04 : Math.sin(t * 1.8) * 0.006;
    const strike = st === 'attack' ? Math.sin(a * Math.PI) : 0;
    neck.rotation.x = strike * 0.8 + (st === 'idle' ? Math.max(0, Math.sin(t * 0.9)) * 0.25 : 0);
    head.rotation.y = st === 'idle' ? Math.sin(t * 0.6) * 0.4 : 0;
    body.rotation.x = st === 'hit' ? -Math.sin(a * Math.PI) * 0.2 : 0;
  });
}

// ---------------------------------------------------------------- swimmers
function fish(k) {
  const root = new THREE.Group(), body = new THREE.Group();
  root.add(body);
  const skin = mat(k.c.main), under = mat(k.c.belly), accent = mat(k.c.accent);
  const eye = k.c.eye === 'glow' ? GLOW_EYE : DARK_EYE;
  const G = k.girth, D = k.len, F = k.finSize;
  const y = G * 0.9 + 0.05;
  const hull = grp(body, 0, y, 0);
  hull.add(m(sph(0.5, 12, 8), skin, 0, 0, 0, G * 1.3, G * 1.6, D));
  hull.add(m(sph(0.5, 10, 6), under, 0, -G * 0.28, 0.02, G * 1.15, G * 1.0, D * 0.9));
  if (k.pattern === 'stripes') for (let i = 0; i < 4; i++) hull.add(m(box(G * 1.32, G * 1.2, 0.03), accent, 0, G * 0.1, D * (0.25 - i * 0.15)));
  if (k.pattern === 'spots') { const r = rng(k.seed + 3); for (let i = 0; i < 8; i++) { const s = r() < 0.5 ? -1 : 1; hull.add(m(sph(G * 0.1, 5, 4), accent, s * G * 0.6, (r() - 0.3) * G * 0.6, (r() - 0.5) * D * 0.7, 0.4, 1, 1)); } }
  // snout and face
  const front = D * 0.48;
  if (k.snout === 'pointed') hull.add(m(cone(G * 0.42, D * 0.32, 8), skin, 0, -G * 0.05, front + D * 0.1).rotateX(Math.PI / 2));
  if (k.snout === 'hammer') { hull.add(m(box(G * 2.2, G * 0.3, G * 0.4), skin, 0, G * 0.05, front + G * 0.15)); for (const s of [-1, 1]) hull.add(m(sph(G * 0.1, 5, 4), eye, s * G * 1.08, G * 0.12, front + G * 0.15)); }
  if (k.snout === 'whisker') { hull.add(m(sph(G * 0.32, 8, 6), under, 0, -G * 0.1, front + G * 0.05, 1.2, 0.8, 1)); for (const s of [-1, 1]) for (let i = 0; i < 2; i++) hull.add(m(cyl(0.006, 0.004, G * 0.5, 3), DARK_EYE, s * G * 0.3, -G * 0.08 - i * 0.03, front + G * 0.2).rotateZ(s * Math.PI / 2.2)); }
  if (k.snout !== 'hammer') for (const s of [-1, 1]) hull.add(m(sph(G * 0.06, 6, 4), eye, s * G * 0.58, G * 0.2, front - D * 0.1));
  // fins
  if (k.dorsal === 'small') hull.add(m(cone(G * 0.35, G * 0.6, 4), accent, 0, G * 0.85, -D * 0.05, 0.2, 1, 1.4));
  if (k.dorsal === 'tall') hull.add(m(cone(G * 0.4, G * 1.3 * F, 4), skin, 0, G * 1.1, -D * 0.02, 0.15, 1, 1.2).rotateX(-0.35));
  if (k.dorsal === 'ridge') for (let i = 0; i < 7; i++) hull.add(m(cone(G * 0.12, G * 0.3, 4), accent, 0, G * 0.78, D * (0.3 - i * 0.1), 0.3, 1, 1));
  const fins = [];
  for (const s of [-1, 1]) {
    const fg = grp(hull, s * G * 0.6, -G * 0.3, D * 0.18);
    const big = k.flippers || k.fins === 'wings';
    fg.add(m(sph(0.5, 6, 4), k.fins === 'wings' ? accent : skin, s * G * (big ? 0.5 : 0.25), 0, -G * 0.2, G * (big ? 1.2 : 0.55) * F, 0.06, G * (big ? 0.8 : 0.45) * F));
    fins.push({ fg, s });
  }
  // the tail
  const tail = grp(body, 0, y, -D * 0.48);
  if (k.tail === 'fork') for (const s of [-1, 1]) tail.add(m(cone(G * 0.3, G * 0.9 * F, 4), accent, 0, s * G * 0.32, -G * 0.4, 0.15, 1, 1).rotateX(-Math.PI / 2 + s * 0.6));
  if (k.tail === 'flukes') for (const s of [-1, 1]) tail.add(m(sph(0.5, 6, 4), skin, s * G * 0.45, 0, -G * 0.35, G * 1.0 * F, 0.08, G * 0.55 * F).rotateY(-s * 0.4));
  if (k.tail === 'flippers') for (const s of [-1, 1]) tail.add(m(sph(0.5, 6, 4), skin, s * G * 0.22, -G * 0.15, -G * 0.4, G * 0.5, 0.08, G * 0.9));
  return finish(root, body, (t, st, a) => {
    const swim = st === 'walk';
    const sp = swim ? 7 : 2.4;
    tail.rotation.y = Math.sin(t * sp) * (swim ? 0.55 : 0.25);
    body.rotation.y = Math.sin(t * sp + 1.2) * (swim ? 0.08 : 0.03);
    body.position.y = Math.sin(t * 1.5) * 0.03;
    fins.forEach(({ fg, s }) => { fg.rotation.z = s * Math.sin(t * sp * 0.8) * (k.flippers ? 0.4 : 0.25); });
    const strike = st === 'attack' ? Math.sin(a * Math.PI) : 0;
    body.position.z = strike * 0.25;
    body.rotation.x = -strike * 0.25 + (st === 'hit' ? Math.sin(a * Math.PI * 3) * 0.1 : 0);
  });
}

// scale to 1 m tall, feet on the ground, and hand over as a ProcActor
function finish(root, body, animate) {
  root.updateMatrixWorld(true);
  const bb = new THREE.Box3().setFromObject(root);
  // a creature's size is its height, or most of its length when it is long and low (a lizard,
  // a shark): a giant lizard grows long, not tall as a house
  const h = Math.max(0.05, bb.max.y - bb.min.y, (bb.max.z - bb.min.z) * 0.6);
  const inner = new THREE.Group();
  while (root.children.length) inner.add(root.children[0]);
  inner.scale.setScalar(1 / h);
  inner.position.y = -bb.min.y / h;
  root.add(inner);
  return new ProcActor(root, body, animate);
}

const BUILD = { quad, bird, fish };
export const KIN_PLANS = Object.keys(BUILD);

// a creature body from its recipe, `height` metres tall
export function makeKin(recipe, { height = 1 } = {}) {
  const a = BUILD[recipe.plan](recipe);
  a.root.scale.setScalar(height);
  return a;
}
