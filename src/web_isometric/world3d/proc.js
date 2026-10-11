// Procedural low-poly creatures for staples no free model pack covers: rat, spider, snake,
// lizard, rabbit, slime — plus kit props that come to life (makeProp). Built from primitives with flat
// shading (to sit with the low-poly art) and animated in code. Same interface as assets.Actor (play / once / update), so entities.js
// treats them like any other body. Built 1 m tall at scale 1; `height` scales them.
import * as THREE from 'three';

const flat = (color, extra = {}) => new THREE.MeshStandardMaterial({ color, roughness: 0.8, flatShading: true, ...extra });
const EYE = new THREE.MeshBasicMaterial({ color: 0x111111 });
const RED_EYE = new THREE.MeshBasicMaterial({ color: new THREE.Color(2.2, 0.25, 0.2) });
const sphere = (r, w = 8, h = 6) => new THREE.SphereGeometry(r, w, h);

function mesh(geo, mat, x = 0, y = 0, z = 0, sx = 1, sy = 1, sz = 1) {
  const m = new THREE.Mesh(geo, mat);
  m.position.set(x, y, z);
  m.scale.set(sx, sy, sz);
  m.castShadow = true;
  return m;
}

// which motion a game animation name means
function stateOf(name) {
  if (/Death/.test(name)) return 'death';
  if (/Hit/.test(name)) return 'hit';
  if (/Attack|Spellcast|Bite|Throw|Kick|Punch/.test(name)) return 'attack';
  if (/Walk|Run/.test(name)) return 'walk';
  return 'idle';
}

class ProcActor {
  constructor(root, body, animate) {
    this.root = root;
    this.body = body;           // the part that bobs / falls over
    this.animate = animate;     // (t, state, k) => void
    this.state = 'idle';
    this.base = 'idle';
    this.t = Math.random() * 10;
    this.k = 0;                 // progress of a one-shot (0..1)
    this.dur = 0;
  }
  play(name) { const s = stateOf(name); this.base = s; if (this.dur <= 0) this.state = s; }
  once(name, fade, timeScale = 1) {
    this.state = stateOf(name);
    this.dur = (this.state === 'death' ? 1.0 : 0.55) / timeScale;
    this.k = 0;
    if (this.state === 'death') this.base = 'death';
    return this.dur;
  }
  update(dt) {
    this.t += dt;
    if (this.dur > 0) {
      this.k = Math.min(1, this.k + dt / this.dur);
      if (this.k >= 1) { this.dur = 0; if (this.state !== 'death') this.state = this.base; }
    }
    if (this.state === 'death' || this.base === 'death') {
      const k = this.state === 'death' ? this.k : 1;
      this.body.rotation.z = k * Math.PI / 2 * 0.95;
      this.body.position.y = -k * 0.08;
      return;
    }
    this.animate(this.t, this.state, this.k);
  }
}

function rat(color) {
  const root = new THREE.Group(), body = new THREE.Group();
  root.add(body);
  const fur = flat(color), pink = flat(0xd89aa0), dark = flat(0x2a2422);
  body.add(mesh(sphere(0.5, 9, 7), fur, 0, 0.42, -0.1, 0.62, 0.55, 1.0));
  const head = new THREE.Group(); head.position.set(0, 0.5, 0.48); body.add(head);
  head.add(mesh(new THREE.ConeGeometry(0.24, 0.5, 8), fur, 0, 0, 0.16, 1, 1, 1).rotateX(Math.PI / 2));
  head.add(mesh(sphere(0.06), pink, 0, 0, 0.42));
  for (const s of [-1, 1]) {
    head.add(mesh(sphere(0.13, 8, 5), pink, s * 0.17, 0.2, -0.02, 1, 1, 0.35));
    head.add(mesh(sphere(0.045), EYE, s * 0.12, 0.08, 0.2));
  }
  const tail = new THREE.Group(); tail.position.set(0, 0.36, -0.6); body.add(tail);
  for (let i = 0; i < 6; i++) tail.add(mesh(sphere(0.06 - i * 0.008, 6, 4), pink, 0, -i * 0.03, -i * 0.13));
  const feet = [];
  for (const [x, z] of [[-0.2, 0.25], [0.2, 0.25], [-0.2, -0.3], [0.2, -0.3]]) { const f = mesh(sphere(0.08, 6, 4), dark, x, 0.06, z); body.add(f); feet.push(f); }
  return new ProcActor(root, body, (t, st, k) => {
    const sp = st === 'walk' ? 18 : 3;
    body.position.y = st === 'walk' ? Math.abs(Math.sin(t * sp)) * 0.06 : Math.sin(t * 2) * 0.01;
    tail.rotation.y = Math.sin(t * (st === 'walk' ? 10 : 2.4)) * 0.5;
    head.rotation.x = st === 'attack' ? -Math.sin(k * Math.PI) * 0.6 : Math.sin(t * 5) * 0.05;
    head.position.z = 0.48 + (st === 'attack' ? Math.sin(k * Math.PI) * 0.18 : 0);
    feet.forEach((f, i) => { f.position.y = 0.06 + (st === 'walk' ? Math.max(0, Math.sin(t * sp + i * 1.6)) * 0.08 : 0); });
  });
}

function spider(color) {
  const root = new THREE.Group(), body = new THREE.Group();
  root.add(body);
  const shell = flat(color), mark = flat(0x9a2a24), leg = flat(new THREE.Color(color).multiplyScalar(0.8));
  const abdomen = mesh(sphere(0.5, 10, 8), shell, 0, 0.55, -0.42, 0.95, 0.8, 1.1);
  body.add(abdomen);
  body.add(mesh(sphere(0.18, 8, 6), mark, 0, 0.92, -0.42, 1, 0.4, 1.2));
  const ceph = mesh(sphere(0.3, 9, 7), shell, 0, 0.5, 0.18, 1, 0.8, 1.05);
  body.add(ceph);
  for (const [x, y] of [[-0.09, 0.62], [0.09, 0.62], [-0.16, 0.56], [0.16, 0.56]]) body.add(mesh(sphere(0.045, 6, 4), RED_EYE, x, y, 0.45));
  const fang = []; for (const s of [-1, 1]) { const f = mesh(new THREE.ConeGeometry(0.04, 0.16, 5), flat(0x222222), s * 0.07, 0.36, 0.44); f.rotation.x = Math.PI; body.add(f); fang.push(f); }
  const legs = [];
  const upperGeo = new THREE.CylinderGeometry(0.035, 0.03, 0.55, 5).translate(0, 0.275, 0);
  const lowerGeo = new THREE.CylinderGeometry(0.03, 0.012, 0.62, 5).translate(0, -0.31, 0);
  for (let i = 0; i < 8; i++) {
    const side = i < 4 ? -1 : 1, j = i % 4;
    const hip = new THREE.Group();
    hip.position.set(side * 0.2, 0.52, 0.32 - j * 0.16);
    hip.rotation.y = side * (0.5 - j * 0.35) + (side < 0 ? Math.PI : 0);
    const up = new THREE.Mesh(upperGeo, leg); up.rotation.z = -0.95; up.castShadow = true;
    const knee = new THREE.Group(); knee.position.set(0.45, 0.32, 0);
    const lo = new THREE.Mesh(lowerGeo, leg); lo.rotation.z = 0.35; lo.castShadow = true;
    knee.add(lo); hip.add(up); hip.add(knee);
    body.add(hip);
    legs.push({ hip, phase: (j % 2 === 0 ? 0 : Math.PI) + (side < 0 ? 0 : Math.PI) });
  }
  return new ProcActor(root, body, (t, st, k) => {
    const sp = st === 'walk' ? 14 : 2;
    legs.forEach(l => {
      const s = Math.sin(t * sp + l.phase);
      l.hip.rotation.x = st === 'walk' ? s * 0.35 : s * 0.04;
      l.hip.position.y = 0.52 + (st === 'walk' ? Math.max(0, s) * 0.06 : 0);
    });
    body.position.y = st === 'walk' ? Math.sin(t * sp * 2) * 0.02 : Math.sin(t * 1.5) * 0.015;
    const strike = st === 'attack' ? Math.sin(k * Math.PI) : 0;
    ceph.rotation.x = -strike * 0.4;
    fang.forEach(f => { f.rotation.z = (f.position.x > 0 ? -1 : 1) * strike * 0.5; });
    abdomen.scale.y = 0.8 + Math.sin(t * 3) * 0.02;
  });
}

function snake(color) {
  const root = new THREE.Group(), body = new THREE.Group();
  root.add(body);
  const skin = flat(color), belly = flat(new THREE.Color(color).lerp(new THREE.Color(0xe8d8a0), 0.5));
  const segs = [];
  for (let i = 0; i < 12; i++) {
    const r = 0.17 - i * 0.01;
    const s = mesh(sphere(r, 8, 6), i % 3 === 1 ? belly : skin, 0, r, -i * 0.2);
    body.add(s); segs.push(s);
  }
  const head = new THREE.Group(); body.add(head);
  head.add(mesh(sphere(0.2, 8, 6), skin, 0, 0, 0.1, 1, 0.75, 1.35));
  for (const s of [-1, 1]) head.add(mesh(sphere(0.045), EYE, s * 0.11, 0.07, 0.22));
  const tongue = mesh(new THREE.BoxGeometry(0.03, 0.01, 0.2), flat(0xd03040), 0, -0.03, 0.4); head.add(tongue);
  return new ProcActor(root, body, (t, st, k) => {
    const sp = st === 'walk' ? 9 : 2.2, amp = st === 'walk' ? 0.22 : 0.08;
    segs.forEach((s, i) => { s.position.x = Math.sin(t * sp - i * 0.6) * amp * (i / 12 + 0.3); });
    const rear = st === 'attack' ? Math.sin(k * Math.PI) : 0;
    head.position.set(Math.sin(t * sp + 0.6) * amp * 0.3, 0.25 + 0.3 + rear * 0.25, 0.2 + rear * 0.3);
    head.rotation.x = -0.25 + rear * 0.3;
    tongue.visible = Math.sin(t * 7) > 0.6 || st === 'attack';
  });
}

// crocodiles, lizards, basilisks: a long low body, a snout, four splayed legs, a sweeping tail
function lizard(color) {
  const root = new THREE.Group(), body = new THREE.Group();
  root.add(body);
  const skin = flat(color), dark = flat(new THREE.Color(color).multiplyScalar(0.7));
  const belly = flat(new THREE.Color(color).lerp(new THREE.Color(0xe8d8a0), 0.45));
  body.add(mesh(sphere(0.5, 10, 7), skin, 0, 0.3, 0, 0.55, 0.32, 1.25));
  body.add(mesh(sphere(0.4, 8, 6), belly, 0, 0.22, 0, 0.5, 0.2, 1.1));
  for (let i = 0; i < 4; i++) body.add(mesh(new THREE.ConeGeometry(0.05, 0.1, 4), dark, 0, 0.45, 0.35 - i * 0.22));
  const head = new THREE.Group(); head.position.set(0, 0.32, 0.62); body.add(head);
  head.add(mesh(sphere(0.2, 8, 6), skin, 0, 0, 0.05, 1, 0.7, 1.2));
  head.add(mesh(new THREE.BoxGeometry(0.22, 0.08, 0.42), skin, 0, -0.04, 0.3));
  for (const s of [-1, 1]) head.add(mesh(sphere(0.045), EYE, s * 0.1, 0.1, 0.12));
  const legGeo = new THREE.CylinderGeometry(0.06, 0.05, 0.28, 6);
  const legs = [];
  for (const [x, z] of [[-1, 0.35], [1, 0.35], [-1, -0.35], [1, -0.35]]) {
    const hip = new THREE.Group(); hip.position.set(x * 0.24, 0.24, z); body.add(hip);
    const leg = mesh(legGeo, dark, x * 0.1, -0.1, 0); leg.rotation.z = x * 0.9; hip.add(leg);
    hip.add(mesh(sphere(0.07, 6, 4), dark, x * 0.2, -0.2, 0.04, 1.2, 0.5, 1.4));
    legs.push({ hip, phase: x * z > 0 ? 0 : Math.PI });
  }
  const tail = [];
  for (let i = 0; i < 7; i++) { const s = mesh(sphere(Math.max(0.03, 0.14 - i * 0.017), 7, 5), skin, 0, 0.25 - i * 0.02, -0.6 - i * 0.17); body.add(s); tail.push(s); }
  return new ProcActor(root, body, (t, st, k) => {
    const walk = st === 'walk', sp = walk ? 12 : 1.6;
    legs.forEach(l => { l.hip.rotation.x = (walk ? 0.5 : 0.03) * Math.sin(t * sp + l.phase); });
    body.rotation.y = walk ? Math.sin(t * sp) * 0.08 : 0;
    tail.forEach((s, i) => { s.position.x = Math.sin(t * (walk ? sp : 1.2) - i * 0.5) * (walk ? 0.05 : 0.02) * (i + 1); });
    const bite = st === 'attack' ? Math.sin(k * Math.PI) : 0;
    head.rotation.x = -bite * 0.35;
    head.position.z = 0.62 + bite * 0.12;
  });
}

function rabbit(color) {
  const root = new THREE.Group(), body = new THREE.Group();
  root.add(body);
  const fur = flat(color), white = flat(0xf2ede4), pink = flat(0xe4a8b0);
  body.add(mesh(sphere(0.32, 9, 7), fur, 0, 0.36, -0.05, 1, 0.95, 1.2));
  const head = new THREE.Group(); head.position.set(0, 0.68, 0.25); body.add(head);
  head.add(mesh(sphere(0.22, 9, 7), fur));
  for (const s of [-1, 1]) {
    const ear = new THREE.Group(); ear.position.set(s * 0.09, 0.16, -0.02); head.add(ear);
    ear.add(mesh(sphere(0.08, 6, 5), fur, 0, 0.2, 0, 0.7, 2.6, 0.45));
    ear.add(mesh(sphere(0.05, 6, 5), pink, 0, 0.2, 0.025, 0.6, 2.2, 0.3));
    ear.userData.side = s;
    head.add(mesh(sphere(0.04), EYE, s * 0.13, 0.04, 0.15));
  }
  head.add(mesh(sphere(0.035), pink, 0, -0.02, 0.21));
  body.add(mesh(sphere(0.1, 6, 5), white, 0, 0.35, -0.42));
  const ears = head.children.filter(c => c.userData.side);
  return new ProcActor(root, body, (t, st, k) => {
    const hop = st === 'walk' ? Math.abs(Math.sin(t * 9)) : 0;
    body.position.y = hop * 0.22;
    body.rotation.x = st === 'walk' ? -Math.cos(t * 9) * 0.12 : 0;
    ears.forEach(e => { e.rotation.z = e.userData.side * (0.15 + Math.sin(t * 3 + e.userData.side) * 0.08); e.rotation.x = -hop * 0.3; });
    head.rotation.x = st === 'attack' ? -Math.sin(k * Math.PI) * 0.5 : Math.sin(t * 1.3) * 0.05;
  });
}

function slime(color) {
  const root = new THREE.Group(), body = new THREE.Group();
  root.add(body);
  const goo = new THREE.MeshStandardMaterial({ color, roughness: 0.25, metalness: 0.05, transparent: true, opacity: 0.85 });
  const blob = mesh(sphere(0.5, 14, 10), goo, 0, 0.42, 0, 1, 0.85, 1);
  body.add(blob);
  body.add(mesh(sphere(0.2, 8, 6), flat(new THREE.Color(color).multiplyScalar(0.6)), 0, 0.38, 0, 1, 0.8, 1));
  for (const s of [-1, 1]) body.add(mesh(sphere(0.07, 8, 6), EYE, s * 0.16, 0.6, 0.4));
  return new ProcActor(root, body, (t, st, k) => {
    const sp = st === 'walk' ? 8 : 2.5;
    const w = Math.sin(t * sp);
    const hop = st === 'walk' ? Math.max(0, w) : 0;
    body.position.y = hop * 0.25;
    blob.scale.set(1 + w * 0.06 - hop * 0.08, 0.85 - w * 0.06 + hop * 0.12, 1 + w * 0.06 - hop * 0.08);
    if (st === 'attack') { const a = Math.sin(k * Math.PI); blob.scale.set(1 + a * 0.25, 0.85 - a * 0.25, 1 + a * 0.25); }
  });
}

const BUILDERS = { rat, spider, snake, lizard, rabbit, slime };
const COLORS = {
  rat: [0x6f6158, 0x8a7a6a, 0x504844], spider: [0x2e2a36, 0x3a2e24, 0x4a3a52], snake: [0x4e7a3c, 0x6a5a2c, 0x3a6a6a],
  lizard: [0x5a7a3a, 0x7a6a3a, 0x4a6a5a],
  rabbit: [0xb59a7c, 0x9a8670, 0xd8ccc0], slime: [0x5fcf6a, 0x6aa8e8, 0xd06ad0],
};

// A kit model come to life (a mimic is a chest, a living book, a dancing sword): it hops along,
// lunges to bite, shudders when hit and tips over when it dies. `size` is its longest side in
// metres; it owns its materials, so a hit flash touches only this one.
export function makeProp(model, { size = 1, tint = null } = {}) {
  const root = new THREE.Group(), body = new THREE.Group(), inner = new THREE.Group();
  root.add(body);
  body.add(inner);
  const dim = model.box.getSize(new THREE.Vector3());
  const k = size / Math.max(dim.x, dim.y, dim.z, 0.01);
  inner.scale.setScalar(k);
  inner.position.set(-(model.box.min.x + model.box.max.x) / 2 * k, -model.box.min.y * k, -(model.box.min.z + model.box.max.z) / 2 * k);
  const own = m => { const c = m.clone(); if (tint != null && c.color) c.color.multiply(new THREE.Color(tint)); return c; };
  for (const p of model.parts) {
    const mesh = new THREE.Mesh(p.geometry, Array.isArray(p.material) ? p.material.map(own) : own(p.material));
    mesh.castShadow = true;
    inner.add(mesh);
  }
  return new ProcActor(root, body, (t, st, a) => {
    const hop = st === 'walk' ? Math.abs(Math.sin(t * 9)) : 0;
    const lunge = st === 'attack' ? Math.sin(a * Math.PI) : 0;
    body.position.set(0, hop * 0.2 * size + Math.sin(t * 2) * 0.01 * size, lunge * 0.3 * size);
    body.rotation.set(-lunge * 0.35, 0, st === 'hit' ? Math.sin(a * Math.PI * 3) * 0.12 : Math.sin(t * 1.7) * 0.02);
  });
}

export function makeProc(kind, { height = 1, tint = null, seed = 0 } = {}) {
  const list = COLORS[kind] || [0x888888];
  const a = BUILDERS[kind](tint != null ? tint : list[Math.abs(seed) % list.length]);
  a.root.scale.setScalar(height);
  return a;
}
