// Aiming an area spell (spells.py AIM_RADIUS): the key starts the aim, a circle the size of the
// blast follows the mouse over the ground, a ring round the hero shows how far it may land; a
// left click (or the same key again) casts it there, a right click or Escape lets it go. The
// cast carries the circle's centre in the room's own metres: "cast 'meteor storm' @12.5,7.0".
// The pure parts are in aimlogic.js (tests/web/aim.test.mjs); this is the circle itself.
import * as THREE from 'three';
export { clampAim, aimCommand } from './aimlogic.js';

// ---- the circle on the ground, and the reach round the hero ----
export class AimCircle {
  constructor(scene) {
    this.group = new THREE.Group();
    this.group.visible = false;
    const flat = (geo, color, opacity) => {
      const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color, transparent: true, opacity, depthWrite: false, side: THREE.DoubleSide }));
      m.rotation.x = -Math.PI / 2;
      m.renderOrder = 5;
      return m;
    };
    // the blast: a bright rim, a soft fill, a cross at its heart
    this.rim = flat(new THREE.RingGeometry(0.94, 1, 64), 0xffc060, 0.9);
    this.fill = flat(new THREE.CircleGeometry(1, 48), 0xffa040, 0.16);
    this.heart = flat(new THREE.RingGeometry(0.05, 0.1, 24), 0xffffff, 0.9);
    this.blast = new THREE.Group();
    this.blast.add(this.rim, this.fill, this.heart);
    // the reach: a thin ring round the hero
    this.reach = flat(new THREE.RingGeometry(0.985, 1, 96), 0xffffff, 0.35);
    this.group.add(this.blast, this.reach);
    scene.add(this.group);
    this.t = 0;
  }
  show(radius, range, color = 0xffa040) {
    this.blast.scale.set(radius, 1, radius);
    this.reach.scale.set(range || 0.001, 1, range || 0.001);
    this.reach.visible = !!range;
    this.rim.material.color.set(color);
    this.fill.material.color.set(color);
    this.group.visible = true;
  }
  // where the blast is, where the hero stands, and whether the mouse was beyond reach
  place(at, hero, clamped) {
    this.blast.position.set(at.x, 0.06, at.z);
    this.reach.position.set(hero.x, 0.05, hero.z);
    this.rim.material.opacity = clamped ? 0.55 : 0.9;
  }
  tick(dt) {
    if (!this.group.visible) return;
    this.t += dt;
    this.fill.material.opacity = 0.12 + 0.06 * Math.sin(this.t * 4);
  }
  hide() { this.group.visible = false; }
}
