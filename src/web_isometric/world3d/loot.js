// What lies on the ground around the hero (the map payload's `nearby[].items`): a corpse is a
// low mound under a slow gold ring, anything else its painted icon (shared/items.js) bobbing
// over a ring in its rarity's colour. Click one to walk over and take it (a corpse: loot it);
// right-click for more. Each sits on one of its room's free spots, the same spot every time.
import * as THREE from 'three';
import { groundItems } from './lootlogic.js';

const RARITY = { common: 0xb8b0a0, uncommon: 0x6fd06f, rare: 0x5aa8ff, epic: 0xc07aff, legendary: 0xffa640, set: 0x5fe0c8 };

function groundRing(color, inner, outer, opacity) {
  const m = new THREE.Mesh(new THREE.RingGeometry(inner, outer, 40), new THREE.MeshBasicMaterial({
    color, transparent: true, opacity, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide }));
  m.rotation.x = -Math.PI / 2;
  m.position.y = 0.03;
  return m;
}

export class GroundLoot {
  // slot(vnum, key) -> a free spot in that room (Entities.slot); icon(item) -> a canvas
  constructor(engine, { slot, icon }) {
    this.engine = engine; this.slot = slot; this.icon = icon;
    this.list = new Map();
    this._v = new THREE.Vector3();
  }

  sync(payload) {
    if (!payload || !Array.isArray(payload.nearby)) return;
    const want = new Map(groundItems(payload).map(g => [g.key, g]));
    for (const [key, l] of this.list) if (!want.has(key)) this.remove(l);
    for (const [key, g] of want) {
      const l = this.list.get(key);
      if (l) { l.item = g.item; l.kw = g.kw; continue; }
      const at = this.slot(g.vnum, g.key);
      if (at) this.add(g, at);
    }
  }

  add(g, at) {
    const root = new THREE.Group();
    root.position.copy(at);
    let bob = null;
    if (g.corpse) {
      const mound = new THREE.Mesh(new THREE.SphereGeometry(0.5, 14, 8), new THREE.MeshStandardMaterial({ color: 0x4a3a32, roughness: 0.95 }));
      mound.scale.set(1.4, 0.32, 0.8);
      mound.position.y = 0.12;
      mound.castShadow = true;
      root.add(mound, groundRing(0xffd27a, 0.75, 0.86, 0.55));
    } else {
      const canvas = this.icon(g.item);
      const tex = new THREE.CanvasTexture(canvas);
      tex.colorSpace = THREE.SRGBColorSpace;
      bob = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false }));
      bob.scale.set(0.55, 0.55, 1);
      bob.position.y = 0.6;
      root.add(bob, groundRing(RARITY[g.item.rarity] || RARITY.common, 0.32, 0.42, 0.7));
    }
    root.userData.loot = g.key;
    this.engine.scene.add(root);
    this.list.set(g.key, { ...g, root, bob, phase: Math.random() * 6.28 });
  }

  remove(l) {
    this.engine.scene.remove(l.root);
    l.root.traverse(o => {
      if (o.geometry) o.geometry.dispose();
      if (o.material) { if (o.material.map) o.material.map.dispose(); o.material.dispose(); }
    });
    this.list.delete(l.key);
  }

  clear() { for (const l of [...this.list.values()]) this.remove(l); }

  // the ground item under a screen point, or null: the nearest whose mark is within a
  // finger's width of it on screen (an icon is small, and the camera is often moving)
  pick(x, y, canvas) {
    if (!this.list.size) return null;
    const r = canvas.getBoundingClientRect();
    const cam = this.engine.camera;
    let best = null, bestD = Infinity;
    for (const l of this.list.values()) {
      const v = this._v.copy(l.root.position).setY(l.corpse ? 0.15 : 0.6).project(cam);
      if (v.z > 1) continue;                                   // behind the camera
      const sx = r.left + (v.x + 1) / 2 * r.width, sy = r.top + (1 - v.y) / 2 * r.height;
      const d = Math.hypot(sx - x, sy - y);
      if (d < (l.corpse ? 46 : 34) && d < bestD) { best = l; bestD = d; }
    }
    return best;
  }

  update(dt, t) {
    for (const l of this.list.values()) {
      if (l.bob) l.bob.position.y = 0.6 + Math.sin(t * 2.2 + l.phase) * 0.08;
      const ring = l.root.children[l.root.children.length - 1];
      if (ring && ring.material) ring.material.opacity = (l.corpse ? 0.35 : 0.5) + Math.sin(t * 3 + l.phase) * 0.2;
    }
  }
}
