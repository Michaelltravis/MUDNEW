// The hero (or another player) riding their mount (Push 34): a steed built from the creature kit
// (kin.js), by the mount's key: a horse's build and coat, a nightmare black with burning eyes and
// hooves, a griffin a lion's body with wings, a clockwork steed brass, a stag, a boar, a camel, a
// panther, a warg. Saddle and blanket on its back (barding for war mounts). The steed is a child
// of the rider's root, so it goes wherever they go; the rider's own body sits up on the saddle
// in a seated pose. On foot, nothing changes.
import * as THREE from 'three';
import { kinRecipe } from './kinrecipe.js';
import { makeKin } from './kin.js';
import { steedSpec } from './steedlogic.js';
export { STEEDS, steedSpec } from './steedlogic.js';

// a kit body `height` tall stands about this much shorter than a rider of that height (it is
// long, not tall), so steeds are drawn this much bigger
const KIN_SCALE = 1.25;
const FACE = 0;

const SADDLE_MAT = new THREE.MeshStandardMaterial({ color: 0x5a3418, roughness: 0.7 });
const FLAME_MAT = new THREE.MeshBasicMaterial({ color: new THREE.Color(2.6, 0.9, 0.2) });
const hash = s => { let h = 2166136261; for (const ch of String(s)) h = Math.imul(h ^ ch.charCodeAt(0), 16777619); return h >>> 0; };


// a steed for a mount key, sized to a rider `riderH` metres tall:
// { root, actor, saddleY, spec, update(dt, moving, speed) }
export function makeSteed(key, riderH = 1.7) {
  const base = steedSpec(key);
  const spec = { ...base, height: base.height * riderH * KIN_SCALE };
  const recipe = kinRecipe(spec.body, spec.words, hash(key), spec.tint);
  const actor = makeKin(recipe, { height: spec.height });
  actor.root.rotation.y = FACE;          // the kit's creatures face +z, as a rider does
  const root = new THREE.Group();
  root.name = `steed_${key}`;
  root.add(actor.root);
  const saddleY = spec.height * spec.back;
  // the saddle and its blanket (or barding) on the back
  const blanket = new THREE.Mesh(new THREE.BoxGeometry(spec.height * 0.36, 0.05, spec.height * 0.32),
    new THREE.MeshStandardMaterial({ color: spec.extra.barding || 0x7a2a22, roughness: 0.85 }));
  blanket.position.set(0, saddleY - 0.02, 0);
  root.add(blanket);
  if (spec.extra.barding) {
    for (const side of [-1, 1]) {
      const flap = new THREE.Mesh(new THREE.BoxGeometry(0.04, spec.height * 0.22, spec.height * 0.46), blanket.material);
      flap.position.set(side * spec.height * 0.18, saddleY - spec.height * 0.11, 0);
      root.add(flap);
    }
  }
  const saddle = new THREE.Mesh(new THREE.BoxGeometry(spec.height * 0.24, 0.1, spec.height * 0.2), SADDLE_MAT);
  saddle.position.set(0, saddleY + 0.04, 0);
  const pommel = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.14, 0.06), SADDLE_MAT);
  pommel.position.set(0, saddleY + 0.12, spec.height * 0.1);
  root.add(saddle, pommel);
  // wings at the shoulders (a griffin)
  const wings = [];
  if (spec.extra.wings) {
    const mat = new THREE.MeshStandardMaterial({ color: spec.extra.wings, roughness: 0.8, side: THREE.DoubleSide, flatShading: true });
    for (const side of [-1, 1]) {
      const g = new THREE.BufferGeometry();
      const L = spec.height * 0.55;
      g.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0.15, side * L, 0.25, -0.1, side * L * 0.55, -0.05, -0.45, 0, 0, -0.25], 3));
      g.setIndex([0, 1, 2, 0, 2, 3]);
      g.computeVertexNormals();
      const w = new THREE.Mesh(g, mat);
      w.position.set(side * spec.height * 0.12, saddleY + 0.05, spec.height * 0.12);
      w.userData.side = side;
      root.add(w);
      wings.push(w);
    }
  }
  // burning hooves (a nightmare)
  const flames = [];
  if (spec.extra.flames) {
    const geo = new THREE.SphereGeometry(0.09, 8, 6);
    for (const [x, z] of [[-1, 1], [1, 1], [-1, -1], [1, -1]]) {
      const f = new THREE.Mesh(geo, FLAME_MAT);
      f.position.set(x * spec.height * 0.12, 0.08, z * spec.height * 0.24);
      root.add(f);
      flames.push(f);
    }
  }
  // a faint glow about it (a celestial or arcane mount)
  if (spec.extra.glow) {
    const l = new THREE.PointLight(spec.extra.glow, 2.2, 4, 1.6);
    l.position.set(0, saddleY, 0);
    root.add(l);
  }
  let t = 0;
  function update(dt, moving, speed = 1) {
    t += dt;
    actor.play(moving ? 'Walking_A' : 'Idle');
    actor.update(dt * (moving ? Math.max(0.8, speed) : 1));
    for (const w of wings) w.rotation.z = w.userData.side * (0.12 + Math.sin(t * (moving ? 6 : 2)) * (moving ? 0.3 : 0.08));
    for (const f of flames) f.scale.setScalar(0.8 + Math.sin(t * 12 + f.position.x * 9) * 0.25);
  }
  return { root, actor, saddleY, spec, update };
}

// The riding pose: the rig has no riding clip, so a rider plays their idle (or an attack, a cast)
// and the legs are set astride on top of it each frame. Each leg bone is aimed along a direction in
// the rider's own frame (x: out to that side, y: up, z: forward): thighs out over the steed's back,
// shins down its flanks, feet forward in the stirrups. Aiming (not fixed angles) works whatever
// axes the rig's bones were authored in.
export const RIDE_POSE = {
  upperleg: [0.85, -0.35, 0.45],
  lowerleg: [0.12, -1, 0.1],
  foot: [0.12, -0.25, 1],
};
const PARTS = [['upperleg', 'lowerleg'], ['lowerleg', 'foot'], ['foot', null]];
const norm = n => String(n || '').toLowerCase().replace(/[^a-z]/g, '');
function legBones(rider) {
  const out = {};
  rider.root.traverse(o => {
    if (!o.isBone) return;
    const n = norm(o.name);
    for (const [part] of PARTS) for (const side of ['l', 'r']) {
      if (n === part + side && !out[part + side]) out[part + side] = o;
    }
    if (n === 'hips' && !out.hips) out.hips = o;
  });
  return out;
}
const _a = new THREE.Vector3(), _b = new THREE.Vector3(), _want = new THREE.Vector3();
const _qw = new THREE.Quaternion(), _qp = new THREE.Quaternion(), _qd = new THREE.Quaternion(), _qr = new THREE.Quaternion();
// a bone's pointing direction in the world: toward its child bone (the foot has none: its own +y)
function boneDir(bone, child, out) {
  bone.getWorldPosition(_a);
  if (child) return out.copy(child.getWorldPosition(_b)).sub(_a).normalize();
  return out.set(0, 1, 0).applyQuaternion(bone.getWorldQuaternion(_qw)).normalize();
}
// set the legs astride (call after the rider's animation update, every frame: the mixer poses the
// bones from the clip each time, so nothing piles up)
export function ridePose(state, root) {
  if (!state || !state.bones || !root) return;
  root.updateWorldMatrix(true, true);
  root.getWorldQuaternion(_qr);
  for (const side of ['l', 'r']) {
    const sx = side === 'l' ? 1 : -1;
    for (const [part, next] of PARTS) {
      const bone = state.bones[part + side];
      if (!bone || !bone.parent) continue;
      const child = next ? state.bones[next + side] : null;
      const w = RIDE_POSE[part];
      _want.set(w[0] * sx, w[1], w[2]).normalize().applyQuaternion(_qr);
      const cur = boneDir(bone, child, new THREE.Vector3());
      _qd.setFromUnitVectors(cur, _want);
      bone.getWorldQuaternion(_qw);
      bone.parent.getWorldQuaternion(_qp);
      bone.quaternion.copy(_qp.invert().multiply(_qd.multiply(_qw)));
      bone.updateWorldMatrix(false, true);
    }
  }
}

// Put a rider on (or off) a steed. `rider` is an actor with `.root` (its first child is the body
// model); returns the riding state, or null on foot.
export function mountRider(rider, key, prev = null) {
  if (prev && prev.key === key) return prev;
  if (prev) {
    rider.root.remove(prev.steed.root);
    for (const [c, y] of prev.lifted) c.position.y = y;
  }
  if (!key) return null;
  // the rider's height, standing (before anything is lifted)
  const box = new THREE.Box3().setFromObject(rider.root);
  const riderH = Math.max(0.8, (box.max.y - box.min.y) / Math.max(1e-3, rider.root.scale.y || 1));
  const steed = makeSteed(key, riderH);
  // the hips' height standing: the rider goes up until their hips sit on the saddle
  const bones = legBones(rider);
  let hipsH = riderH * 0.42;
  if (bones.hips) {
    rider.root.updateMatrixWorld(true);
    const v = bones.hips.getWorldPosition(new THREE.Vector3());
    hipsH = (v.y - box.min.y) / Math.max(1e-3, rider.root.scale.y || 1);
  }
  const lift = Math.max(0, steed.saddleY - hipsH + riderH * 0.01);
  const lifted = rider.root.children.filter(c => !String(c.name).startsWith('steed_')).map(c => [c, c.position.y]);
  for (const [c, y] of lifted) c.position.y = y + lift;
  rider.root.add(steed.root);
  return { key, steed, lifted, bones, scale: riderH, pose: () => ridePose({ bones }, rider.root) };
}
