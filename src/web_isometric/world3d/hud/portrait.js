// Portraits for the unit frames: a bust of the hero or of whatever is targeted, photographed
// once by a small offscreen renderer (one WebGL context for every portrait) and kept as an image.
// The body comes from the same code that puts it in the world (a class model, or a creature's
// look from looks.js), lit like a painting: warm key light, cool rim, a dark mist behind.
import * as THREE from 'three';
import { spawnCharacter } from '../assets.js';
import { classModel, spawnLook } from '../entities.js';
import { creatureLook } from '../looks.js';

const SIZE = 192;
let studio = null;
const cache = new Map();

function makeStudio() {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = SIZE;
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: true });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;
  const scene = new THREE.Scene();
  scene.add(new THREE.HemisphereLight(0xcfdcff, 0x2a2018, 1.25));
  const key = new THREE.DirectionalLight(0xffe0b0, 2.8); key.position.set(1.6, 2.4, 2.6); scene.add(key);
  const rim = new THREE.DirectionalLight(0x8ab4ff, 2.2); rim.position.set(-2.4, 1.8, -2.2); scene.add(rim);
  const cam = new THREE.PerspectiveCamera(26, 1, 0.05, 60);
  return { canvas, renderer, scene, cam };
}

// photograph an actor's head and shoulders; `bust` is how much of its height to frame
function shoot(actor, { bust = 0.5, turn = 0.45 } = {}) {
  const s = studio || (studio = makeStudio());
  const root = actor.root;
  root.rotation.y = turn;
  s.scene.add(root);
  try { actor.play('Idle', 0); actor.update(0.6); } catch (_) { /* a prop has no clips */ }
  root.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(root);
  const h = Math.max(0.2, box.max.y - box.min.y), w = Math.max(box.max.x - box.min.x, box.max.z - box.min.z);
  const top = box.max.y, frame = Math.max(h * bust, w * 0.62);
  const cy = top - frame * 0.52, cx = (box.max.x + box.min.x) / 2, cz = (box.max.z + box.min.z) / 2;
  const dist = frame / (2 * Math.tan(THREE.MathUtils.degToRad(s.cam.fov / 2))) * 1.08;
  s.cam.position.set(cx + Math.sin(0.15) * dist, cy + frame * 0.08, cz + Math.cos(0.15) * dist);
  s.cam.lookAt(cx, cy, cz);
  s.renderer.setClearColor(0x000000, 0);
  s.renderer.render(s.scene, s.cam);
  const url = s.canvas.toDataURL('image/png');
  s.scene.remove(root);
  return url;
}

// the hero's (or another player's) class portrait
export function classPortrait(cls) {
  const key = `class:${String(cls || '').toLowerCase()}`;
  if (!cache.has(key)) {
    const look = classModel(cls);
    cache.set(key, spawnCharacter(look.model, { tint: look.tint }).then(a => shoot(a, { bust: 0.55 })).catch(() => null));
  }
  return cache.get(key);
}

// a creature's portrait from its payload data (the body looks.js gives it in the world)
export function creaturePortrait(data, kits = null) {
  const look = creatureLook(data || {});
  const b = look.beast;
  const key = b ? `beast:${b.mob || b.proc || (b.prop && b.prop.join('/'))}:${b.tint || ''}:${b.h || ''}` : `person:${look.model}:${look.tint || ''}:${look.flat ? 1 : 0}`;
  if (!cache.has(key)) {
    cache.set(key, spawnLook(look, { kits, seed: 7 }).then(a => shoot(a, { bust: b ? 0.75 : 0.55, turn: b ? 0.7 : 0.45 })).catch(() => null));
  }
  return cache.get(key);
}
