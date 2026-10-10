// /play?gallery=dungeon|nature — every model of a kit in a row, for checking art and
// scale with the game camera. A development page, not part of the game.
import * as THREE from 'three';
import { trs, spawnMob, mobIndexReady } from './assets.js';
import { creatureLook } from './looks.js';
import { spawnLook } from './entities.js';

export function showGallery(engine, kit, scale = 1) {
  const only = new URLSearchParams(location.search).get('only');
  const names = [...kit.keys()].filter(n => !only || only.split(',').some(o => n.includes(o)));
  const cols = 8, step = 5;
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(cols * step + 6, Math.ceil(names.length / cols) * step + 6),
    new THREE.MeshStandardMaterial({ color: 0x6d6a60, roughness: 1 }));
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(cols * step / 2 - step / 2, 0, Math.ceil(names.length / cols) * step / 2 - step / 2);
  floor.receiveShadow = true;
  engine.scene.add(floor);
  names.forEach((n, i) => {
    const m = kit.get(n);
    for (const p of m.parts) {
      const mesh = new THREE.Mesh(p.geometry, p.material);
      mesh.applyMatrix4(trs((i % cols) * step, 0, Math.floor(i / cols) * step, 0, scale));
      mesh.castShadow = mesh.receiveShadow = true;
      engine.scene.add(mesh);
    }
  });
  names.forEach((n, i) => engine.scene.add(new THREE.ArrowHelper(new THREE.Vector3(0, 0, 1),
    new THREE.Vector3((i % cols) * step, 0.05, Math.floor(i / cols) * step), 2.2, 0xff3030, 0.5, 0.3)));
  console.log('gallery order:', names.join(', '));
  engine.setMood('day', true);
  return new THREE.Vector3(cols * step / 2, 0, step * 1.5);
}

// every creature model in a row, each with an arrow along +Z (the way actors face)
export async function showMobGallery(engine) {
  const index = await mobIndexReady();
  const only = new URLSearchParams(location.search).get('only');
  const names = Object.keys(index).sort().filter(n => !only || only.split(',').includes(n));
  const cols = Math.min(8, names.length), step = 4;
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(cols * step + 6, Math.ceil(names.length / cols) * step + 6),
    new THREE.MeshStandardMaterial({ color: 0x6d6a60, roughness: 1 }));
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(cols * step / 2 - step / 2, 0, Math.ceil(names.length / cols) * step / 2 - step / 2);
  floor.receiveShadow = true;
  engine.scene.add(floor);
  const actors = [];
  for (let i = 0; i < names.length; i++) {
    const a = await spawnMob(names[i], { height: 1.4 });
    const x = (i % cols) * step, z = Math.floor(i / cols) * step;
    a.root.position.set(x, 0, z);
    a.play('Idle', 0);
    engine.scene.add(a.root);
    engine.scene.add(new THREE.ArrowHelper(new THREE.Vector3(0, 0, 1), new THREE.Vector3(x, 0.05, z), 1.6, 0xff3030, 0.4, 0.25));
    actors.push(a);
  }
  engine.onTick(dt => actors.forEach(a => a.update(dt)));
  console.log('mob gallery order:', names.join(', '));
  engine.setMood('day', true);
  return new THREE.Vector3(cols * step / 2, 0, step * 1.5);
}

// creatures at their in-game sizes beside a knight, from descriptions the MUD uses (each
// through looks.js, exactly as the game picks them), labelled
const SAMPLES = ['the green gelatinous blob', 'the giant hornet', 'the goat herder', 'a goblin mushroom farmer', 'the Spider Queen',
  'the mimic', 'the Book Monster', 'the dancing sword', 'the magic carpet', 'the broom', 'the stone golem', 'the statue of Indra',
  'a fire elemental', 'the djinn', 'A tiny pixie', 'the sea hag', 'the merman', 'a lizard man', 'the baker', 'the cityguard',
  "the mages' guildmaster", 'an orc shaman', 'a skeletal warrior', 'a rotting zombie', 'an ancient lich', 'a vampire spawn',
  'the Black Rook', 'the White Bishop', 'a possessed suit of armor', 'the red dragon', 'the baby dragon', 'a black bear',
  'the large, grey wolf', 'the giant earth beetle', 'a sewer crocodile', 'the dragon turtle', 'a hell hound', 'the ancient tree',
  'the myconoid', 'a ghostly mermaid', { short: 'the Sewer King', long: 'A massive rat-man standing here.', boss: true }];

export async function showBeastGallery(engine, kits) {
  const only = new URLSearchParams(location.search).get('only');
  const list = [{ short: 'the knight (hero)' }, ...SAMPLES.map(s => typeof s === 'string' ? { short: s } : s)]
    .filter(m => !only || only.split(',').some(o => m.short.toLowerCase().includes(o)));
  const cols = 10, step = 3.2, rows = Math.ceil(list.length / cols);
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(cols * step + 6, rows * step * 1.4 + 6), new THREE.MeshStandardMaterial({ color: 0x6f7a5a, roughness: 1 }));
  floor.rotation.x = -Math.PI / 2; floor.position.set((cols - 1) * step / 2, 0, (rows - 1) * step * 0.7); floor.receiveShadow = true;
  engine.scene.add(floor);
  const actors = [], labels = [];
  for (let i = 0; i < list.length; i++) {
    const m = list[i], x = (i % cols) * step, z = Math.floor(i / cols) * step * 1.4;
    const look = i === 0 ? { model: 'knight' } : creatureLook({ ...m, pv: i });
    const a = await spawnLook(look, { kits, seed: i });
    const fly = look.beast ? look.beast.fly : look.fly;
    a.root.position.set(x, fly || 0, z);
    a.play('Idle', 0, look.still ? 0 : 1);
    engine.scene.add(a.root);
    actors.push(a);
    const el = document.createElement('div');
    el.textContent = m.short;
    el.style.cssText = 'position:fixed;left:0;top:0;font:11px sans-serif;color:#fff;background:#0008;padding:1px 4px;border-radius:3px;pointer-events:none;white-space:nowrap;z-index:50';
    document.body.appendChild(el);
    labels.push({ el, at: new THREE.Vector3(x, -0.2, z + 0.9) });
  }
  const v = new THREE.Vector3();
  engine.onTick(dt => {
    actors.forEach(a => a.update(dt));
    const cv = engine.renderer.domElement.getBoundingClientRect();
    for (const l of labels) {
      v.copy(l.at).project(engine.camera);
      l.el.style.display = v.z > 1 ? 'none' : '';
      l.el.style.transform = `translate(${(cv.left + (v.x + 1) / 2 * cv.width).toFixed(0)}px, ${(cv.top + (1 - v.y) / 2 * cv.height).toFixed(0)}px) translate(-50%, 0)`;
    }
  });
  console.log('beast gallery:', list.map(m => m.short).join(', '));
  engine.setMood('day', true);
  return new THREE.Vector3((cols - 1) * step / 2, 0, (rows - 1) * step * 0.6);
}
