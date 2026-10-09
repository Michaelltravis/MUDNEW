// /play?gallery=dungeon|nature — every model of a kit in a row, for checking art and
// scale with the game camera. A development page, not part of the game.
import * as THREE from 'three';
import { trs } from './assets.js';

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
