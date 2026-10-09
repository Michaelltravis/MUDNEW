// /play?gallery=dungeon|nature — every model of a kit in a row, for checking art and
// scale with the game camera. A development page, not part of the game.
import * as THREE from 'three';
import { trs, spawnMob, mobIndexReady, spawnCharacter } from './assets.js';
import { BESTIARY } from './bestiary.js';
import { makeProc } from './proc.js';

export function showGallery(engine, kit) {
  const names = [...kit.keys()];
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
      mesh.applyMatrix4(trs((i % cols) * step, 0, Math.floor(i / cols) * step, 0, 1));
      mesh.castShadow = mesh.receiveShadow = true;
      engine.scene.add(mesh);
    }
  });
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

// creatures at their in-game sizes beside a knight, by the names the MUD uses
export async function showBeastGallery(engine) {
  const names = ['knight', 'rat', 'spider', 'snake', 'rabbit', 'slime', 'wolf', 'fox', 'bear', 'deer', 'bat', 'dog', 'cat',
    'boar', 'raven', 'crab', 'beetle', 'dragon', 'demon', 'imp', 'ghost', 'ogre', 'yeti', 'treant', 'mushroom', 'beholder'];
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(60, 20), new THREE.MeshStandardMaterial({ color: 0x6f7a5a, roughness: 1 }));
  floor.rotation.x = -Math.PI / 2; floor.position.set(14, 0, 4); floor.receiveShadow = true;
  engine.scene.add(floor);
  const actors = [];
  for (let i = 0; i < names.length; i++) {
    const n = names[i], x = (i % 13) * 2.3, z = Math.floor(i / 13) * 4.5;
    let a;
    if (n === 'knight') a = await spawnCharacter('knight');
    else {
      const look = (BESTIARY.find(([re]) => re.test(n)) || [])[1];
      if (!look) continue;
      a = look.proc ? makeProc(look.proc, { height: look.h, tint: look.tint }) : await spawnMob(look.mob, { height: look.h, tint: look.tint });
      if (look.fly) a.root.position.y = look.fly;
    }
    a.root.position.x = x; a.root.position.z = z;
    a.play('Idle', 0);
    engine.scene.add(a.root);
    actors.push(a);
  }
  engine.onTick(dt => actors.forEach(a => a.update(dt)));
  console.log('beast gallery:', names.join(', '));
  engine.setMood('day', true);
  return new THREE.Vector3(6, 0, 1.5);
}
