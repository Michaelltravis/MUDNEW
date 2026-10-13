// The dead, on the ground: a creature that dies falls where it stood and stays there as its
// corpse (the map payload's "corpse of <whoever>", loot.js), darkened, over a stain, under the
// gold ring that says it can be looted. A body with a death clip plays it and holds its last
// frame; one without (code-built bodies, props, creatures whose pack has no death) tips over onto
// its side. A hero's corpse, or anything with no body to draw, gets a grave: a mound of earth,
// a few stones and a wooden marker.
import * as THREE from 'three';

// "corpse of the goblin" -> "the goblin"
export const victimOf = name => String(name || '').replace(/^\s*(the\s+)?corpse\s+of\s+/i, '').trim();
// how a name is compared with a creature's ("The Goblin" is "goblin")
export const nameKey = s => String(s || '').toLowerCase().replace(/^(a|an|the)\s+/, '').trim();

// a body that has a real death clip (not one the creature's alias falls back to idle for)
function deathClip(actor) {
  if (!actor || !actor.mixer || typeof actor.action !== 'function') return null;
  if (actor.alias && actor.alias.Death_A === actor.alias.Idle) return null;
  return actor.action('Death_A');
}

// Start a body's fall; returns {update(dt) -> still falling?}. `ground` is the floor's height.
export function fallOver(actor, { ground = 0, side = 1 } = {}) {
  const root = actor.root;
  const clip = deathClip(actor);
  if (clip) {
    actor.mixer.stopAllAction();
    clip.reset();
    clip.setLoop(THREE.LoopOnce, 1);
    clip.clampWhenFinished = true;
    clip.timeScale = 1;
    clip.play();
    let left = clip.getClip().duration + 0.05;
    return {
      update(dt) {
        if (left <= 0) return false;
        actor.mixer.update(Math.min(dt, left));
        left -= dt;
        if (root.position.y > ground) root.position.y = Math.max(ground, root.position.y - dt * 3);   // a flyer drops
        if (left <= 0) settle(root, ground);
        return left > 0;
      },
    };
  }
  // a body built in code (proc.js, kin.js, a prop) has a death of its own, which it holds
  if (!actor.mixer && typeof actor.once === 'function' && typeof actor.update === 'function') {
    let left = (actor.once('Death_A') || 1) + 0.05;
    return {
      update(dt) {
        if (left <= 0) return false;
        actor.update(Math.min(dt, left));
        left -= dt;
        if (root.position.y > ground) root.position.y = Math.max(ground, root.position.y - dt * 3);
        if (left <= 0) settle(root, ground);
        return left > 0;
      },
    };
  }
  // no death at all: tip over onto one side and drop to the floor
  const from = root.rotation.z, to = side * Math.PI / 2, y0 = root.position.y;
  let t = 0;
  const T = 0.55;
  return {
    update(dt) {
      if (t >= T) return false;
      t = Math.min(T, t + dt);
      const k = t / T, e = k * k;                       // falling: slow, then fast
      root.rotation.z = from + (to - from) * e;
      root.position.y = y0 + (ground - y0) * e;
      if (t >= T) settle(root, ground);
      return t < T;
    },
  };
}

// rest a fallen body on the floor: nothing below it, nothing floating above it; one still
// standing after its death (a bat's folded wings, a beetle's crouch) goes over onto its side
export function settle(root, ground = 0) {
  root.updateMatrixWorld(true);
  let box = new THREE.Box3().setFromObject(root);
  if (!isFinite(box.min.y)) return;
  const h = box.max.y - box.min.y, len = Math.max(box.max.x - box.min.x, box.max.z - box.min.z);
  if (h > len * 0.9 && Math.abs(root.rotation.z) < 0.5) {
    root.rotation.z += Math.PI / 2;
    root.updateMatrixWorld(true);
    box = new THREE.Box3().setFromObject(root);
  }
  root.position.y += ground - box.min.y + 0.01;
}

// darken a body (its own copies of the materials: the living keep theirs); returns the copies
export function deaden(root, k = 0.6) {
  const made = [];
  root.traverse(o => {
    if (!o.isMesh || !o.material) return;
    const one = m => {
      const c = m.clone();
      if (c.color) c.color.multiplyScalar(k);
      if (c.emissive) c.emissive.multiplyScalar(0.2);
      made.push(c);
      return c;
    };
    o.material = Array.isArray(o.material) ? o.material.map(one) : one(o.material);
  });
  return made;
}

// how big a body lies: the radius of its footprint on the floor
export function footprint(root) {
  const box = new THREE.Box3().setFromObject(root);
  if (!isFinite(box.min.x)) return 0.6;
  return Math.max(0.35, Math.min(2.5, Math.max(box.max.x - box.min.x, box.max.z - box.min.z) / 2));
}

let stainTex = null;
function stainTexture() {
  if (stainTex) return stainTex;
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const g = c.getContext('2d');
  const grd = g.createRadialGradient(32, 32, 2, 32, 32, 31);
  grd.addColorStop(0, 'rgba(40,12,8,0.85)');
  grd.addColorStop(0.55, 'rgba(36,14,10,0.55)');
  grd.addColorStop(1, 'rgba(30,16,12,0)');
  g.fillStyle = grd;
  g.fillRect(0, 0, 64, 64);
  stainTex = new THREE.CanvasTexture(c);
  stainTex.colorSpace = THREE.SRGBColorSpace;
  return stainTex;
}

// a dark stain on the floor under a body (its geometry and material are its own)
export function stain(r) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(r * 2.2, r * 1.7), new THREE.MeshBasicMaterial({
    map: stainTexture(), transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2 }));
  m.rotation.x = -Math.PI / 2;
  m.position.y = 0.02;
  m.userData.own = true;
  return m;
}

// a grave: a low mound of earth, a few stones round it and a wooden marker at its head
export function grave(rng = Math.random) {
  const g = new THREE.Group();
  const earth = new THREE.MeshStandardMaterial({ color: 0x4b3a2c, roughness: 1 });
  const mound = new THREE.Mesh(new THREE.SphereGeometry(0.5, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2), earth);
  mound.scale.set(0.75, 0.38, 1.25);
  mound.castShadow = mound.receiveShadow = true;
  g.add(mound);
  const rock = new THREE.MeshStandardMaterial({ color: 0x7a766c, roughness: 0.9, flatShading: true });
  for (let i = 0; i < 7; i++) {
    const a = (i / 7) * Math.PI * 2 + rng() * 0.4;
    const r = 0.08 + rng() * 0.07;
    const s = new THREE.Mesh(new THREE.DodecahedronGeometry(r, 0), rock);
    s.position.set(Math.cos(a) * 0.44, r * 0.5, Math.sin(a) * 0.7);       // half sunk in the earth
    s.rotation.set(rng() * 3, rng() * 3, rng() * 3);
    s.castShadow = true;
    g.add(s);
  }
  const wood = new THREE.MeshStandardMaterial({ color: 0x6b4a2e, roughness: 0.9 });
  const post = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.75, 0.08), wood);
  post.position.set(0, 0.37, -0.72);
  const bar = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.07, 0.07), wood);
  bar.position.set(0, 0.55, -0.72);
  post.rotation.z = bar.rotation.z = (rng() - 0.5) * 0.15;      // leaning a little
  post.castShadow = bar.castShadow = true;
  g.add(post, bar);
  g.traverse(o => { o.userData.own = true; });
  return g;
}
