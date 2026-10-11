// Heroes dressed in what they wear. The equipment kit (art3d/chars/equip.glb, built by
// tools/art3d/build.mjs 'equip') holds every adventurer body part and piece on one rig,
// painted from one palette. A character is dressed by merging the parts and pieces their
// look asks for (gearlook.js planLook) into ONE skinned mesh: two draw calls (the mesh and
// its shadow) however much they wear, recoloured by moving each piece's UVs to other palette
// columns. Re-dressing swaps that mesh's geometry in place, so the skeleton, the animation
// mixer and everything that holds the actor stay as they are.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { loadArt, loadAnims, floatAttr, Actor } from './assets.js';
import { planLook, kitIndex } from './gearlook.js';
import { buildProc } from './procgear.js';

const ART = new URL('../art3d/', import.meta.url).href;
const CACHE_MAX = 48;
let kitPromise = null;

// three.js drops dots from node names ('handslot.r' -> 'handslotr')
export const boneKey = name => String(name || '').replace(/[[\].:/]/g, '').replace(/\s/g, '_');

export function loadEquipKit() {
  if (!kitPromise) {
    kitPromise = Promise.all([loadArt('chars/equip.glb'), fetch(ART + 'chars/equip.json').then(r => r.json())])
      .then(([gltf, manifest]) => makeKit(gltf, manifest));
  }
  return kitPromise;
}

function intAttr(attr) {
  const n = attr.count, out = new Uint16Array(n * 4);
  for (let i = 0; i < n; i++) { out[i * 4] = attr.getX(i); out[i * 4 + 1] = attr.getY(i); out[i * 4 + 2] = attr.getZ(i); out[i * 4 + 3] = attr.getW(i); }
  return new THREE.BufferAttribute(out, 4);
}

// every piece as plain float geometry in the rig's rest pose, skinned to its bones (a hat or
// a sword wholly to the bone it hangs from)
function makeKit(gltf, manifest) {
  const kit = kitIndex(manifest);
  const scene = gltf.scene;
  scene.updateMatrixWorld(true);
  let skinned = null;
  scene.traverse(o => { if (!skinned && o.isSkinnedMesh) skinned = o; });
  const bones = skinned.skeleton.bones;
  kit.boneNames = bones.map(b => b.name);
  kit.boneIndex = new Map(bones.map((b, i) => [b.name, i]));
  kit.rest = bones.map(b => b.matrixWorld.clone());
  kit.inverses = kit.rest.map(m => m.clone().invert());
  kit.rigNode = skinned.parent;            // 'Rig': the bones (and, in the kit, the parts)
  kit.material = skinned.material;
  kit.geo = new Map();
  kit.cache = new Map();
  scene.traverse(o => {
    if (!o.isMesh) return;
    const src = o.geometry;
    const M = o.isSkinnedMesh
      ? new THREE.Matrix4().multiplyMatrices(o.skeleton.bones[0].matrixWorld, o.skeleton.boneInverses[0]).multiply(o.bindMatrix)
      : o.matrixWorld.clone();
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', floatAttr(src.attributes.position));
    g.setAttribute('normal', floatAttr(src.attributes.normal));
    g.setAttribute('uv', floatAttr(src.attributes.uv));
    g.applyMatrix4(M);
    const n = src.attributes.position.count;
    if (o.isSkinnedMesh) {
      g.setAttribute('skinIndex', intAttr(src.attributes.skinIndex));
      g.setAttribute('skinWeight', floatAttr(src.attributes.skinWeight));
    } else {
      const b = kit.boneIndex.get(o.parent.name) || 0;
      const si = new Uint16Array(n * 4), sw = new Float32Array(n * 4);
      for (let i = 0; i < n; i++) { si[i * 4] = b; sw[i * 4] = 1; }
      g.setAttribute('skinIndex', new THREE.BufferAttribute(si, 4));
      g.setAttribute('skinWeight', new THREE.BufferAttribute(sw, 4));
    }
    g.setIndex(new THREE.BufferAttribute(src.index.array.slice(), 1));
    kit.geo.set(o.name, g);
  });
  return kit;
}

// the bones alone, for one actor
function cloneBones(node) {
  const c = node.clone(false);
  for (const ch of node.children) if (!ch.isMesh) c.add(cloneBones(ch));
  return c;
}

function recolour(g, remap, N) {
  const uv = g.attributes.uv.array;
  for (let i = 0; i < uv.length; i += 2) {
    const to = remap[Math.floor(uv[i] * N)];
    if (to !== undefined) uv[i] = (to + 0.5) / N;
  }
}

// a hat made for another head: moved and scaled about the bone it hangs from
const _t = new THREE.Vector3(), _s = new THREE.Vector3(), _q = new THREE.Quaternion();
function fitTo(g, fit, bone, kit) {
  const b = kit.boneIndex.get(boneKey(bone));
  if (b == null) return;
  const F = new THREE.Matrix4().compose(_t.fromArray(fit.t || [0, 0, 0]), _q.identity(), _s.setScalar(fit.s || 1));
  g.applyMatrix4(new THREE.Matrix4().multiplyMatrices(kit.rest[b], F).multiply(kit.inverses[b]));
}

// what each role of a built-in-code piece is painted with, unless its look says otherwise
const PROC_PAINT = { wood: 'wood', wood_dark: 'wood_dark', wood_pale: 'wood_pale', metal: 'steel', metal_dark: 'steel~dark',
  leather: 'leather_dark', string: 'white', hole: 'black~dark', gem: 'gem_red' };
function procGeometry(kit, pr) {
  const donor = kit.pieces[pr.piece];
  if (!donor) return null;
  const b = kit.boneIndex.get(boneKey(donor.bone));
  const worn = (pr.look && (pr.look.t || 0) === 0);
  const paint = role => {
    let name = pr.roles[role];
    if (!name) { name = PROC_PAINT[role] || 'steel'; if (worn && kit.col(`${name}~worn`) != null && role !== 'string' && role !== 'hole') name = `${name}~worn`; }
    const c = kit.col(name) ?? kit.col(PROC_PAINT[role] || 'steel') ?? 0;
    return (c + 0.5) / kit.N;
  };
  const a = buildProc(pr.shape, pr.look, paint);
  if (!a) return null;
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(a.position, 3));
  g.setAttribute('normal', new THREE.BufferAttribute(a.normal, 3));
  g.setAttribute('uv', new THREE.BufferAttribute(a.uv, 2));
  g.setIndex(new THREE.BufferAttribute(a.index, 1));
  const m = donor.mount;
  const local = new THREE.Matrix4().compose(_t.fromArray(m.t), _q.fromArray(m.r), _s.fromArray(m.s));
  g.applyMatrix4(new THREE.Matrix4().multiplyMatrices(kit.rest[b], local));
  const n = a.position.length / 3, si = new Uint16Array(n * 4), sw = new Float32Array(n * 4);
  for (let i = 0; i < n; i++) { si[i * 4] = b; sw[i * 4] = 1; }
  g.setAttribute('skinIndex', new THREE.BufferAttribute(si, 4));
  g.setAttribute('skinWeight', new THREE.BufferAttribute(sw, 4));
  return g;
}

// one merged geometry for a plan (shared by everyone who looks the same)
export function assemble(kit, plan) {
  const hit = kit.cache.get(plan.key);
  if (hit) { kit.cache.delete(plan.key); kit.cache.set(plan.key, hit); return hit; }
  const parts = [];
  for (const it of plan.props) {
    const src = kit.geo.get(it.name);
    if (!src) continue;
    const remap = it.remap && Object.keys(it.remap).length ? it.remap : null;
    if (!remap && !it.fit) { parts.push(src); continue; }
    const g = src.clone();
    if (remap) recolour(g, remap, kit.N);
    if (it.fit) fitTo(g, it.fit, kit.pieces[it.name].bone, kit);
    parts.push(g);
  }
  for (const pr of plan.procs) { const g = procGeometry(kit, pr); if (g) parts.push(g); }
  const merged = mergeGeometries(parts, false);
  kit.cache.set(plan.key, merged);
  while (kit.cache.size > CACHE_MAX) {
    const [k, old] = kit.cache.entries().next().value;
    kit.cache.delete(k);
    old.dispose();
  }
  return merged;
}

// a dressed character: its own bones, one mesh, the shared clips
export async function spawnDressed(look, cls, opts = {}) {
  const [kit, clips] = await Promise.all([loadEquipKit(), loadAnims()]);
  const root = new THREE.Group();
  const rig = cloneBones(kit.rigNode);
  root.add(rig);
  const byName = new Map();
  rig.traverse(o => byName.set(o.name, o));
  const skeleton = new THREE.Skeleton(kit.boneNames.map(n => byName.get(n)), kit.inverses.map(m => m.clone()));
  const plan = planLook(look, cls, kit);
  const mesh = new THREE.SkinnedMesh(assemble(kit, plan), kit.material.clone());
  mesh.bind(skeleton, new THREE.Matrix4());
  mesh.castShadow = mesh.receiveShadow = true;
  // skinned bounds would lag the pose: a fixed, generous sphere lets it be culled off-screen
  mesh.boundingSphere = new THREE.Sphere(new THREE.Vector3(0, 1.1, 0), 3.2);   // a swung greatsword included
  mesh.name = 'dressed';
  root.add(mesh);
  if (opts.scale) root.scale.setScalar(opts.scale);
  const actor = new Actor(root, clips);
  actor.gear = { kit, mesh, plan, cls, sig: look && look.sig };
  actor.idle = plan.idle;
  return actor;
}

// put a dressed actor into another look; false when nothing changed
export function dress(actor, look, cls) {
  const g = actor && actor.gear;
  if (!g) return false;
  const sig = look && look.sig;
  if (sig === g.sig && cls === g.cls) return false;
  const plan = planLook(look, cls, g.kit);
  g.mesh.geometry = assemble(g.kit, plan);
  Object.assign(g, { plan, sig, cls });
  actor.idle = plan.idle;
  return true;
}
