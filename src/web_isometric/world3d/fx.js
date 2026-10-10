// Combat visuals: one pooled particle system (a single draw call), projectiles, beams,
// slash arcs, light pillars, ground telegraphs, floating combat text, hit flashes and
// camera shake. Everything is fire-and-forget: fx.update(dt) advances it all.
import * as THREE from 'three';

const MAX = 3000;

// ---- particles: additive soft dots, CPU-simulated, one THREE.Points ----
class Particles {
  constructor(scene) {
    this.pos = new Float32Array(MAX * 3);
    this.col = new Float32Array(MAX * 3);
    this.size = new Float32Array(MAX);
    this.alpha = new Float32Array(MAX);
    this.vel = new Float32Array(MAX * 3);
    this.life = new Float32Array(MAX);
    this.max = new Float32Array(MAX);
    this.grav = new Float32Array(MAX);
    this.drag = new Float32Array(MAX);
    this.grow = new Float32Array(MAX);
    this.n = 0;
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(this.pos, 3).setUsage(THREE.DynamicDrawUsage));
    g.setAttribute('color', new THREE.BufferAttribute(this.col, 3).setUsage(THREE.DynamicDrawUsage));
    g.setAttribute('size', new THREE.BufferAttribute(this.size, 1).setUsage(THREE.DynamicDrawUsage));
    g.setAttribute('alpha', new THREE.BufferAttribute(this.alpha, 1).setUsage(THREE.DynamicDrawUsage));
    g.setDrawRange(0, 0);
    const m = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      uniforms: { uScale: { value: 300 } },
      vertexShader: `attribute float size; attribute float alpha; attribute vec3 color; varying vec3 vC; varying float vA;
        uniform float uScale;
        void main() { vC = color; vA = alpha; vec4 mv = modelViewMatrix * vec4(position, 1.0);
          gl_PointSize = size * uScale / -mv.z; gl_Position = projectionMatrix * mv; }`,
      fragmentShader: `varying vec3 vC; varying float vA;
        void main() { vec2 d = gl_PointCoord - 0.5; float r = length(d); if (r > 0.5) discard;
          float a = smoothstep(0.5, 0.0, r); gl_FragColor = vec4(vC * a * vA, a * vA); }`,
    });
    this.points = new THREE.Points(g, m);
    this.points.frustumCulled = false;
    this.points.renderOrder = 10;
    scene.add(this.points);
    this.geo = g;
  }
  emit(p, { count = 10, color = 0xffffff, speed = 2, up = 0, life = 0.6, size = 0.25, gravity = 0, spread = 1, drag = 1.5, grow = 0, jitter = 0, dir = null } = {}) {
    const c = new THREE.Color(color);
    for (let k = 0; k < count && this.n < MAX; k++) {
      const i = this.n++;
      this.pos[i * 3] = p.x + (Math.random() - 0.5) * jitter;
      this.pos[i * 3 + 1] = p.y + (Math.random() - 0.5) * jitter;
      this.pos[i * 3 + 2] = p.z + (Math.random() - 0.5) * jitter;
      let vx = (Math.random() - 0.5) * 2, vy = (Math.random() - 0.5) * 2, vz = (Math.random() - 0.5) * 2;
      const l = Math.hypot(vx, vy, vz) || 1;
      vx = vx / l * spread; vy = vy / l * spread; vz = vz / l * spread;
      if (dir) { vx += dir.x; vy += dir.y; vz += dir.z; }
      const s = speed * (0.5 + Math.random() * 0.7);
      this.vel[i * 3] = vx * s; this.vel[i * 3 + 1] = vy * s + up; this.vel[i * 3 + 2] = vz * s;
      this.col[i * 3] = c.r; this.col[i * 3 + 1] = c.g; this.col[i * 3 + 2] = c.b;
      this.size[i] = size * (0.6 + Math.random() * 0.8);
      this.life[i] = this.max[i] = life * (0.6 + Math.random() * 0.6);
      this.alpha[i] = 1;
      this.grav[i] = gravity; this.drag[i] = drag; this.grow[i] = grow;
    }
  }
  update(dt) {
    let i = 0;
    while (i < this.n) {
      this.life[i] -= dt;
      if (this.life[i] <= 0) { this.kill(i); continue; }
      const d = Math.max(0, 1 - this.drag[i] * dt);
      this.vel[i * 3] *= d; this.vel[i * 3 + 1] = this.vel[i * 3 + 1] * d - this.grav[i] * dt; this.vel[i * 3 + 2] *= d;
      this.pos[i * 3] += this.vel[i * 3] * dt; this.pos[i * 3 + 1] += this.vel[i * 3 + 1] * dt; this.pos[i * 3 + 2] += this.vel[i * 3 + 2] * dt;
      const k = this.life[i] / this.max[i];
      this.alpha[i] = Math.min(1, k * 2.2);
      this.size[i] += this.grow[i] * dt;
      i++;
    }
    for (const a of ['position', 'color', 'size', 'alpha']) this.geo.attributes[a].needsUpdate = true;
    this.geo.setDrawRange(0, this.n);
  }
  kill(i) {
    const j = --this.n;
    if (i === j) return;
    for (let k = 0; k < 3; k++) { this.pos[i * 3 + k] = this.pos[j * 3 + k]; this.vel[i * 3 + k] = this.vel[j * 3 + k]; this.col[i * 3 + k] = this.col[j * 3 + k]; }
    this.size[i] = this.size[j]; this.alpha[i] = this.alpha[j]; this.life[i] = this.life[j]; this.max[i] = this.max[j];
    this.grav[i] = this.grav[j]; this.drag[i] = this.drag[j]; this.grow[i] = this.grow[j];
  }
}

// ---- schools: colours for spells and impacts ----
export const SCHOOL = {
  fire: { core: new THREE.Color(4, 1.6, 0.4), spark: 0xff7a2a, smoke: 0x5a3020 },
  frost: { core: new THREE.Color(1.2, 2.6, 4), spark: 0x9fd8ff, smoke: 0xdaf2ff },
  lightning: { core: new THREE.Color(2.4, 2.6, 4.5), spark: 0xbfd8ff, smoke: 0x8a9aff },
  arcane: { core: new THREE.Color(2.6, 1.0, 4.2), spark: 0xc87aff, smoke: 0x6a3aa8 },
  holy: { core: new THREE.Color(4, 3.4, 1.6), spark: 0xffe8a0, smoke: 0xfff4d0 },
  shadow: { core: new THREE.Color(1.4, 0.4, 2.2), spark: 0x8a4ad0, smoke: 0x2a1040 },
  necrotic: { core: new THREE.Color(0.8, 2.6, 0.9), spark: 0x7aff8a, smoke: 0x1a3a1a },
  nature: { core: new THREE.Color(1.2, 3, 0.8), spark: 0x9aff6a, smoke: 0x3a6a2a },
  poison: { core: new THREE.Color(1.2, 2.6, 0.4), spark: 0xb8ff5a, smoke: 0x4a6a1a },
  sound: { core: new THREE.Color(3, 2, 3.6), spark: 0xffb8ff, smoke: 0x8a5aa8 },
  physical: { core: new THREE.Color(3, 3, 3), spark: 0xffffff, smoke: 0x888888 },
  blood: { core: new THREE.Color(2.8, 0.3, 0.3), spark: 0xd02a2a, smoke: 0x5a0a0a },
};

const _v = new THREE.Vector3(), _w = new THREE.Vector3();

export class FX {
  constructor(engine, overlay) {
    this.engine = engine;
    this.scene = engine.scene;
    this.p = new Particles(engine.scene);
    this.items = [];                   // live effects: {update(dt) -> keep?}
    this.overlay = overlay;            // DOM layer for floating text
    this.texts = [];
    this.shakeT = 0; this.shakeMag = 0;
    engine.onTick(dt => this.update(dt));
    // floating text is placed once the camera has moved for this frame (no lag while orbiting)
    if (engine.onLateTick) engine.onLateTick(dt => this.updateTexts(dt)); else this._textsInTick = true;
    engine.rig.shake = () => this.shakeOffset();
  }

  add(item) { this.items.push(item); return item; }

  update(dt) {
    this.p.update(dt);
    for (let i = this.items.length - 1; i >= 0; i--) if (!this.items[i].update(dt)) { this.items[i].dispose && this.items[i].dispose(); this.items.splice(i, 1); }
    if (this._textsInTick) this.updateTexts(dt);
    if (this.shakeT > 0) this.shakeT -= dt;
  }

  // ---- screen feedback ----
  shake(mag = 0.15, time = 0.22) { this.shakeMag = Math.max(this.shakeMag * (this.shakeT > 0 ? 1 : 0), mag); this.shakeT = Math.max(this.shakeT, time); }
  shakeOffset() {
    if (this.shakeT <= 0) return null;
    const m = this.shakeMag * Math.min(1, this.shakeT / 0.12);
    return _w.set((Math.random() - 0.5) * m, (Math.random() - 0.5) * m, (Math.random() - 0.5) * m);
  }

  // ---- floating combat text ----
  text(pos, str, { color = '#ffffff', size = 18, crit = false, rise = 1.4, life = 1.1, side = 0 } = {}) {
    const d = document.createElement('div');
    d.className = 'fct' + (crit ? ' crit' : '');
    d.textContent = str;
    d.style.color = color;
    d.style.fontSize = `${crit ? size * 1.45 : size}px`;
    this.overlay.appendChild(d);
    // words born together over the same head (a flurry, a crit and a stun) fan out instead
    // of printing on top of each other
    let stack = 0;
    for (const o of this.texts) if (o.t < 0.45 && o.p0.distanceToSquared(pos) < 0.5) stack++;
    const fan = stack ? (stack % 2 ? 0.45 : -0.45) * Math.ceil(stack / 2) : 0;
    // fan out along the screen's left-right, whichever way the camera has been turned
    const right = new THREE.Vector3(1, 0, 0).applyQuaternion(this.engine.camera.quaternion).setY(0).normalize();
    const p = pos.clone().addScaledVector(right, side + fan + (Math.random() - 0.5) * 0.3)
      .add(new THREE.Vector3(0, stack * 0.3, 0));
    this.texts.push({ d, p0: pos.clone(), p, t: 0, life, rise, crit });
  }
  updateTexts(dt) {
    const cam = this.engine.camera, cv = this.engine.renderer.domElement;
    const w = cv.clientWidth, h = cv.clientHeight;
    for (let i = this.texts.length - 1; i >= 0; i--) {
      const x = this.texts[i];
      x.t += dt;
      if (x.t >= x.life) { x.d.remove(); this.texts.splice(i, 1); continue; }
      const k = x.t / x.life;
      _v.copy(x.p).setY(x.p.y + x.rise * (1 - Math.pow(1 - k, 2))).project(cam);
      const pop = x.crit ? 1 + Math.max(0, 0.6 - x.t * 4) : 1 + Math.max(0, 0.25 - x.t * 2);
      x.d.style.transform = `translate(${((_v.x + 1) / 2 * w).toFixed(1)}px, ${((1 - _v.y) / 2 * h).toFixed(1)}px) translate(-50%, -50%) scale(${pop.toFixed(2)})`;
      x.d.style.opacity = k < 0.7 ? 1 : 1 - (k - 0.7) / 0.3;
    }
  }

  // ---- hit flash: the body glows for a moment (materials are per actor) ----
  flash(root, color = 0xff3a2a, time = 0.18) {
    if (!root) return;
    const mats = [];
    root.traverse(o => { if (o.isMesh && o.material && o.material.emissive) mats.push(o.material); });
    const c = new THREE.Color(color);
    let t = time;
    // remember each material's own glow once: overlapping flashes must not keep the red
    for (const m of mats) if (!m.userData.baseEmissive) m.userData.baseEmissive = m.emissive.clone();
    const token = {};
    for (const m of mats) m.userData.flashToken = token;
    this.add({ update: dt => {
      t -= dt;
      const k = Math.max(0, t / time);
      for (const m of mats) {
        if (m.userData.flashToken !== token) continue;          // a newer flash owns it now
        m.emissive.copy(m.userData.baseEmissive).lerp(c, k * 0.9);
      }
      return t > 0;
    } });
  }

  // ---- bursts ----
  impact(p, school = 'physical', big = false) {
    const s = SCHOOL[school] || SCHOOL.physical;
    this.p.emit(p, { count: big ? 34 : 16, color: s.spark, speed: big ? 5 : 3.5, life: 0.45, size: big ? 0.32 : 0.22, gravity: 4, drag: 2.5 });
    this.p.emit(p, { count: big ? 10 : 5, color: s.smoke, speed: 1, up: 0.8, life: 0.7, size: 0.5, grow: 0.8, drag: 1 });
    this.light(p, s.core, big ? 7 : 4, 0.22);
  }
  sparks(p, color = 0xffe0a0, n = 12) { this.p.emit(p, { count: n, color, speed: 4, life: 0.3, size: 0.16, gravity: 6, drag: 2 }); }

  // a short-lived point light (pooled small: at most a few at once)
  light(p, color, intensity = 5, time = 0.25) {
    if ((this._lights = (this._lights || 0)) >= 4) return;
    const l = new THREE.PointLight(color instanceof THREE.Color ? color : new THREE.Color(color), intensity, 6, 1.6);
    l.position.copy(p);
    this.scene.add(l);
    this._lights++;
    let t = time;
    this.add({ update: dt => { t -= dt; l.intensity = intensity * Math.max(0, t / time); return t > 0; },
      dispose: () => { this.scene.remove(l); l.dispose(); this._lights--; } });
  }

  // ---- melee: a bright arc swept in front of the attacker ----
  slash(from, to, { color = 0xffffff, wide = false, delay = 0 } = {}) {
    const dir = _v.copy(to).sub(from).setY(0).normalize();
    const geo = new THREE.RingGeometry(wide ? 1.0 : 0.7, wide ? 2.1 : 1.35, 24, 1, -Math.PI * (wide ? 0.85 : 0.45), Math.PI * (wide ? 1.7 : 0.9));
    const mat = new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(2.2), transparent: true, opacity: 0,
      side: THREE.DoubleSide, blending: THREE.AdditiveBlending, depthWrite: false });
    const m = new THREE.Mesh(geo, mat);
    m.rotation.x = -Math.PI / 2;
    m.rotation.z = Math.atan2(dir.x, dir.z) - Math.PI / 2;
    m.position.copy(from).setY(1.05).addScaledVector(dir, wide ? 0.2 : 0.55);
    let t = -delay;
    this.scene.add(m);
    return this.add({ update: dt => {
      t += dt;
      if (t < 0) return true;
      const k = t / 0.22;
      mat.opacity = k < 0.3 ? k / 0.3 : Math.max(0, 1 - (k - 0.3) / 0.7);
      m.rotation.z += dt * 9 * (wide ? 1.4 : 1);
      return k < 1;
    }, dispose: () => { this.scene.remove(m); geo.dispose(); mat.dispose(); } });
  }

  // ---- projectiles: a glowing head with a trail, flies from -> to, then onHit ----
  projectile(from, to, { school = 'arcane', speed = 16, size = 0.22, arc = 0.4, kind = 'orb', onHit = null, delay = 0 } = {}) {
    const s = SCHOOL[school] || SCHOOL.arcane;
    const head = kind === 'arrow' ? arrowMesh() : new THREE.Mesh(new THREE.SphereGeometry(size, 12, 8), new THREE.MeshBasicMaterial({ color: s.core }));
    const start = from.clone(), end = to.clone();
    const dist = start.distanceTo(end);
    const dur = Math.max(0.12, dist / speed);
    let t = -delay;
    head.visible = false;
    this.scene.add(head);
    const self = this;
    return this.add({ update(dt) {
      t += dt;
      if (t < 0) return true;
      head.visible = true;
      const k = Math.min(1, t / dur);
      head.position.lerpVectors(start, end, k);
      head.position.y += Math.sin(k * Math.PI) * arc * dist * 0.08;
      if (kind === 'arrow') { _v.copy(end).sub(start).normalize(); head.lookAt(head.position.clone().add(_v)); }
      else self.p.emit(head.position, { count: 2, color: s.spark, speed: 0.4, life: 0.35, size: size * 1.4, drag: 3 });
      if (k >= 1) { if (onHit) onHit(end); return false; }
      return true;
    }, dispose() { self.scene.remove(head); } });
  }

  // ---- lightning: a jagged beam that flickers ----
  beam(from, to, { school = 'lightning', time = 0.28, delay = 0 } = {}) {
    const s = SCHOOL[school] || SCHOOL.lightning;
    const pts = [];
    const segs = 10;
    for (let i = 0; i <= segs; i++) pts.push(new THREE.Vector3());
    const geo = new THREE.BufferGeometry().setFromPoints(pts);
    const mat = new THREE.LineBasicMaterial({ color: s.core, transparent: true });
    const line = new THREE.Line(geo, mat);
    line.frustumCulled = false;
    let t = -delay, jag = 0;
    const self = this;
    this.scene.add(line);
    return this.add({ update(dt) {
      t += dt;
      if (t < 0) { line.visible = false; return true; }
      line.visible = true;
      if ((jag -= dt) <= 0) {
        jag = 0.04;
        const a = geo.attributes.position;
        for (let i = 0; i <= segs; i++) {
          _v.lerpVectors(from, to, i / segs);
          const off = i === 0 || i === segs ? 0 : 0.35;
          a.setXYZ(i, _v.x + (Math.random() - 0.5) * off, _v.y + (Math.random() - 0.5) * off, _v.z + (Math.random() - 0.5) * off);
        }
        a.needsUpdate = true;
      }
      mat.opacity = Math.max(0, 1 - t / time);
      return t < time;
    }, dispose() { self.scene.remove(line); geo.dispose(); mat.dispose(); } });
  }

  // ---- a column of light from the sky (holy smite, heals, judgement) ----
  pillar(p, { school = 'holy', radius = 0.9, height = 7, time = 0.7, delay = 0 } = {}) {
    const s = SCHOOL[school] || SCHOOL.holy;
    const geo = new THREE.CylinderGeometry(radius, radius * 1.15, height, 20, 1, true).translate(0, height / 2, 0);
    const mat = new THREE.MeshBasicMaterial({ color: s.core, transparent: true, opacity: 0, side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending, depthWrite: false });
    const m = new THREE.Mesh(geo, mat);
    m.position.copy(p).setY(0);
    let t = -delay, burst = false;
    const self = this;
    this.scene.add(m);
    return this.add({ update(dt) {
      t += dt;
      if (t < 0) return true;
      const k = t / time;
      mat.opacity = (k < 0.2 ? k / 0.2 : Math.max(0, 1 - (k - 0.2) / 0.8)) * 0.55;
      m.scale.set(1 - k * 0.4, 1, 1 - k * 0.4);
      if (!burst) { burst = true; self.p.emit(_v.copy(p).setY(0.3), { count: 26, color: s.spark, speed: 3, up: 1.5, life: 0.7, size: 0.26, drag: 2 }); }
      return k < 1;
    }, dispose() { self.scene.remove(m); geo.dispose(); mat.dispose(); } });
  }

  // ---- swirl around a body: heals, buffs, auras, summons ----
  swirl(target, { school = 'holy', time = 1.0, rise = 2.2, count = 3 } = {}) {
    const s = SCHOOL[school] || SCHOOL.holy;
    let t = 0, acc = 0;
    const self = this;
    return this.add({ update(dt) {
      t += dt; acc += dt;
      const p = target.position || target;
      while (acc > 0.03) {
        acc -= 0.03;
        for (let i = 0; i < count; i++) {
          const a = t * 9 + i * (Math.PI * 2 / count);
          _v.set(p.x + Math.cos(a) * 0.7, (t / time) * rise, p.z + Math.sin(a) * 0.7);
          self.p.emit(_v, { count: 1, color: s.spark, speed: 0.2, up: 0.6, life: 0.6, size: 0.2, drag: 2 });
        }
      }
      return t < time;
    } });
  }

  // ---- ground ring that expands (AoE, shouts, stomps) ----
  shockwave(p, { school = 'physical', radius = 4, time = 0.45, delay = 0 } = {}) {
    const s = SCHOOL[school] || SCHOOL.physical;
    const geo = new THREE.RingGeometry(0.85, 1, 48);
    const mat = new THREE.MeshBasicMaterial({ color: s.core, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
    const m = new THREE.Mesh(geo, mat);
    m.rotation.x = -Math.PI / 2;
    m.position.copy(p).setY(0.08);
    let t = -delay;
    const self = this;
    this.scene.add(m);
    return this.add({ update(dt) {
      t += dt;
      if (t < 0) return true;
      const k = t / time;
      m.scale.setScalar(0.3 + k * radius);
      mat.opacity = Math.max(0, 1 - k) * 0.9;
      return k < 1;
    }, dispose() { self.scene.remove(m); geo.dispose(); mat.dispose(); } });
  }

  // ---- telegraph: a danger zone on the floor that fills until the blow lands ----
  telegraph(center, { shape = 'circle', radius = 3, angle = Math.PI / 2, facing = 0, time = 1.5, color = 0xff3a28 } = {}) {
    const g = new THREE.Group();
    const thetaStart = shape === 'cone' ? facing - angle / 2 : 0, thetaLen = shape === 'cone' ? angle : Math.PI * 2;
    const baseGeo = new THREE.CircleGeometry(1, 48, thetaStart, thetaLen);
    const edgeGeo = new THREE.RingGeometry(0.96, 1, 48, 1, thetaStart, thetaLen);
    const fillMat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.16, depthWrite: false });
    const edgeMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(2), transparent: true, opacity: 0.85, depthWrite: false });
    const growMat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.32, depthWrite: false });
    const base = new THREE.Mesh(baseGeo, fillMat), edge = new THREE.Mesh(edgeGeo, edgeMat), grow = new THREE.Mesh(baseGeo, growMat);
    for (const m of [base, edge, grow]) { m.rotation.x = -Math.PI / 2; m.renderOrder = 3; g.add(m); }
    // circle angles start on +X and turn toward -Z in this flat frame; match world yaw
    g.rotation.y = 0;
    g.position.copy(center).setY(0.06);
    g.scale.setScalar(radius);
    let t = 0;
    const self = this;
    this.scene.add(g);
    const item = this.add({ update(dt) {
      t += dt;
      if (item.fading != null) {          // broken before it landed: the mark drains away
        item.fading -= dt;
        const a = Math.max(0, item.fading / 0.3);
        fillMat.opacity = 0.16 * a; edgeMat.opacity = 0.85 * a; growMat.opacity = 0.32 * a;
        g.scale.setScalar(radius * (1 + (1 - a) * 0.15));
        return item.fading > 0;
      }
      const k = Math.min(1, t / time);
      grow.scale.setScalar(k);
      edgeMat.opacity = 0.6 + Math.sin(t * 18) * 0.25 * k;
      if (item.follow) g.position.copy(item.follow.position).setY(0.06);
      return t < time + 0.15 && !item.cancelled;
    }, dispose() { self.scene.remove(g); baseGeo.dispose(); edgeGeo.dispose(); fillMat.dispose(); edgeMat.dispose(); growMat.dispose(); } });
    item.cancel = () => { item.cancelled = true; };
    item.fade = () => { if (item.fading == null) item.fading = 0.3; };
    return item;
  }
}

function arrowMesh() {
  const g = new THREE.Group();
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.9, 5), new THREE.MeshStandardMaterial({ color: 0x8a6a42 }));
  shaft.rotation.x = Math.PI / 2;
  const tip = new THREE.Mesh(new THREE.ConeGeometry(0.05, 0.16, 6), new THREE.MeshStandardMaterial({ color: 0xc8ccd4, metalness: 0.6, roughness: 0.3 }));
  tip.rotation.x = Math.PI / 2; tip.position.z = 0.5;
  const fl = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.01, 0.16), new THREE.MeshStandardMaterial({ color: 0xe8e0d0 }));
  fl.position.z = -0.4;
  g.add(shaft, tip, fl);
  return g;
}
