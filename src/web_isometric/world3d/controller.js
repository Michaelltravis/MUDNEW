// Hero movement: WASD / arrows (north = up), click-to-move, attack. Velocity eases
// toward the wanted speed, the body is a circle that slides along walls, and the
// world is a flat plane, so all of this is 2D (x, z).
import * as THREE from 'three';

const RADIUS = 0.36;
const RUN = 5.2, WALK = 2.4;            // m/s
const ACCEL = 32, DECEL = 26;           // m/s^2

export class Controller {
  constructor(engine, actor, blocked) {
    this.engine = engine;
    this.actor = actor;
    this.blocked = blocked;              // (x, z) -> bool, in world metres
    this.pos = actor.root.position;
    this.vel = new THREE.Vector2();
    this.yaw = 0;
    this.keys = new Set();
    this.goal = null;                    // click-to-move target
    this.lock = 0;                       // seconds of attack wind-down
    this.enabled = true;
    const down = e => {
      if (e.target && /INPUT|TEXTAREA/.test(e.target.tagName)) return;
      const k = e.key.toLowerCase();
      if (['w', 'a', 's', 'd', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright', 'shift'].includes(k)) {
        this.keys.add(k); this.goal = null; e.preventDefault();
      }
      if ((k === ' ' || k === 'f') && !e.repeat) { this.attack(); e.preventDefault(); }
    };
    const up = e => this.keys.delete(e.key.toLowerCase());
    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);
    window.addEventListener('blur', () => this.keys.clear());
    // click / hold to move: the ground point under the cursor
    const ray = new THREE.Raycaster(), ndc = new THREE.Vector2(), plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
    const hit = new THREE.Vector3();
    let held = false;
    const aim = e => {
      const r = engine.renderer.domElement.getBoundingClientRect();
      ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
      ray.setFromCamera(ndc, engine.camera);
      if (ray.ray.intersectPlane(plane, hit)) this.goal = new THREE.Vector2(hit.x, hit.z);
    };
    const cv = engine.renderer.domElement;
    cv.addEventListener('pointerdown', e => { if (e.button === 0) { held = true; aim(e); } });
    window.addEventListener('pointermove', e => { if (held) aim(e); });
    window.addEventListener('pointerup', () => { held = false; });
  }

  attack() {
    if (this.lock > 0) return;
    const d = this.actor.once('1H_Melee_Attack_Chop', 0.06, 1.25);
    this.lock = Math.min(0.55, d * 0.7);
  }

  wish() {
    const k = this.keys;
    let x = 0, z = 0;
    if (k.has('a') || k.has('arrowleft')) x -= 1;
    if (k.has('d') || k.has('arrowright')) x += 1;
    if (k.has('w') || k.has('arrowup')) z -= 1;
    if (k.has('s') || k.has('arrowdown')) z += 1;
    if (x || z) { const l = Math.hypot(x, z); return new THREE.Vector2(x / l, z / l); }
    if (this.goal) {
      const dx = this.goal.x - this.pos.x, dz = this.goal.y - this.pos.z, l = Math.hypot(dx, dz);
      if (l < 0.25) { this.goal = null; return new THREE.Vector2(); }
      return new THREE.Vector2(dx / l, dz / l).multiplyScalar(Math.min(1, l / 0.8));
    }
    return new THREE.Vector2();
  }

  free(x, z) {
    // the circle's four extreme points and its centre must be on open ground
    const b = this.blocked;
    return !b(x, z) && !b(x + RADIUS, z) && !b(x - RADIUS, z) && !b(x, z + RADIUS) && !b(x, z - RADIUS)
      && !b(x + RADIUS * 0.7, z + RADIUS * 0.7) && !b(x - RADIUS * 0.7, z + RADIUS * 0.7)
      && !b(x + RADIUS * 0.7, z - RADIUS * 0.7) && !b(x - RADIUS * 0.7, z - RADIUS * 0.7);
  }

  update(dt) {
    this.lock = Math.max(0, this.lock - dt);
    const w = this.enabled && this.lock === 0 ? this.wish() : new THREE.Vector2();
    const top = this.keys.has('shift') ? WALK : RUN;
    const want = w.clone().multiplyScalar(top);
    const dv = want.clone().sub(this.vel);
    const rate = (want.lengthSq() > this.vel.lengthSq() ? ACCEL : DECEL) * dt;
    if (dv.length() > rate) dv.setLength(rate);
    this.vel.add(dv);

    // move each axis on its own: blocked on one, still slide along the other
    const nx = this.pos.x + this.vel.x * dt;
    if (this.free(nx, this.pos.z)) this.pos.x = nx; else this.vel.x = 0;
    const nz = this.pos.z + this.vel.y * dt;
    if (this.free(this.pos.x, nz)) this.pos.z = nz; else this.vel.y = 0;

    const speed = this.vel.length();
    if (speed > 0.15) {
      const target = Math.atan2(this.vel.x, this.vel.y);
      let d = target - this.yaw;
      d = Math.atan2(Math.sin(d), Math.cos(d));
      this.yaw += d * Math.min(1, dt * 14);
    }
    this.actor.root.rotation.y = this.yaw;
    if (this.lock === 0) {
      if (speed > 3.2) this.actor.play('Running_A', 0.15, speed / RUN * 1.05);
      else if (speed > 0.25) this.actor.play('Walking_A', 0.15, Math.max(0.6, speed / WALK));
      else this.actor.play('Idle', 0.25);
    }
    return speed;
  }
}
