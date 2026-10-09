// Renderer, scene, lights, camera rig, post-processing and the frame loop.
// One continuous world: nothing here knows about rooms. Callers add objects and
// register per-frame callbacks with engine.onTick(fn(dt, t)).
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

// ?q=low|med|high, default high (the Mac mini and any recent laptop handle it)
export const QUALITY = {
  low: { name: 'low', dpr: 1, shadows: false, shadowSize: 1024, bloom: false, antialias: false },
  med: { name: 'med', dpr: 1.25, shadows: true, shadowSize: 1024, bloom: true, antialias: true },
  high: { name: 'high', dpr: 2, shadows: true, shadowSize: 2048, bloom: true, antialias: true },
};

// Lighting moods. The world is one scene with one sun, so "indoors" is a mood the
// rig blends to when the hero's room is enclosed (a crypt under an open sky).
export const MOODS = {
  day: { sky: 0xcfe2ff, ground: 0x5a4a32, hemi: 1.15, sun: 0xfff1d6, sunI: 2.6, fog: 0xa9bfd0, near: 34, far: 90, exposure: 1.0 },
  forest: { sky: 0xbfe0c8, ground: 0x3a3424, hemi: 1.0, sun: 0xffe6b8, sunI: 2.3, fog: 0x8fae9a, near: 30, far: 80, exposure: 1.0 },
  crypt: { sky: 0x5a6a8a, ground: 0x1a140e, hemi: 0.32, sun: 0x8090c0, sunI: 0.25, fog: 0x0d0f16, near: 18, far: 52, exposure: 1.15 },
  // a lit interior (temple, shop, inn): warm and readable, no strong sun
  interior: { sky: 0xffe6c4, ground: 0x3a2c1e, hemi: 0.85, sun: 0xffe2b8, sunI: 0.9, fog: 0x1c1712, near: 26, far: 70, exposure: 1.05 },
  dusk: { sky: 0xf0b890, ground: 0x3a2a24, hemi: 0.7, sun: 0xff9a5a, sunI: 1.5, fog: 0x6a5060, near: 30, far: 80, exposure: 1.05 },
  night: { sky: 0x5a6a9a, ground: 0x1a1a22, hemi: 0.58, sun: 0xa8bcff, sunI: 0.75, fog: 0x121a2c, near: 26, far: 70, exposure: 1.25 },
};

export function createEngine(container, opts = {}) {
  const q = QUALITY[opts.quality] || QUALITY.high;
  const renderer = new THREE.WebGLRenderer({ antialias: q.antialias, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, q.dpr));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.shadowMap.enabled = q.shadows;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  // count draw calls over the whole frame (shadow + scene + bloom passes), not the last pass
  renderer.info.autoReset = false;
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x07080b);
  scene.fog = new THREE.Fog(0x0d0f16, 30, 80);

  const hemi = new THREE.HemisphereLight(0xffffff, 0x444444, 1);
  const sun = new THREE.DirectionalLight(0xffffff, 2);
  sun.castShadow = q.shadows;
  sun.shadow.mapSize.set(q.shadowSize, q.shadowSize);
  Object.assign(sun.shadow.camera, { left: -24, right: 24, top: 24, bottom: -24, near: 1, far: 90 });
  sun.shadow.bias = -0.0004;
  sun.shadow.normalBias = 0.04;
  scene.add(hemi, sun, sun.target);

  // ---- camera rig: fixed yaw (north = screen up), steep pitch, smooth follow ----
  const camera = new THREE.PerspectiveCamera(36, 1, 0.5, 220);
  // The pitch follows the zoom (owner: "see more of the character's face"): pulled back
  // it looks down on the room like a map (58°); zoomed in it drops toward the hero's
  // face (34°). The default sits in between.
  const rig = {
    target: new THREE.Vector3(),     // what we look at (the hero)
    focus: new THREE.Vector3(),      // smoothed target
    pitch: THREE.MathUtils.degToRad(46),
    lowPitch: 34, highPitch: 58,
    dist: 19, minDist: 10, maxDist: 34, wantDist: 19,
  };
  function placeCamera(snap) {
    if (snap) rig.focus.copy(rig.target);
    const k = THREE.MathUtils.clamp((rig.dist - rig.minDist) / (rig.maxDist - rig.minDist), 0, 1);
    rig.pitch = THREE.MathUtils.degToRad(THREE.MathUtils.lerp(rig.lowPitch, rig.highPitch, Math.pow(k, 0.8)));
    const off = new THREE.Vector3(0, Math.sin(rig.pitch), Math.cos(rig.pitch)).multiplyScalar(rig.dist);
    camera.position.copy(rig.focus).add(off);
    camera.lookAt(rig.focus.x, rig.focus.y + 1.1, rig.focus.z);
    // impact shake (fx.js): a small offset for a few frames on heavy blows
    const sh = rig.shake && rig.shake();
    if (sh) camera.position.add(sh);
  }
  renderer.domElement.addEventListener('wheel', e => {
    e.preventDefault();
    rig.wantDist = THREE.MathUtils.clamp(rig.wantDist * (e.deltaY > 0 ? 1.1 : 1 / 1.1), rig.minDist, rig.maxDist);
  }, { passive: false });

  // ---- post: bloom only on what is really bright (torches, sparks), then tone map ----
  let composer = null;
  if (q.bloom) {
    composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));
    composer.addPass(new UnrealBloomPass(new THREE.Vector2(256, 256), 0.32, 0.45, 0.88));
    composer.addPass(new OutputPass());
  }

  function resize() {
    const w = container.clientWidth || window.innerWidth, h = container.clientHeight || window.innerHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    if (composer) { composer.setPixelRatio(renderer.getPixelRatio()); composer.setSize(w, h); }
  }
  window.addEventListener('resize', resize);
  resize();

  // ---- mood blending ----
  const cur = { ...MOODS.day }, want = { ...MOODS.day };
  const colors = { sky: new THREE.Color(), ground: new THREE.Color(), sun: new THREE.Color(), fog: new THREE.Color() };
  function setMood(m, instant) {
    Object.assign(want, typeof m === 'string' ? MOODS[m] : m);
    if (instant) Object.assign(cur, want);
  }
  function blendMood(dt) {
    const k = 1 - Math.exp(-dt * 2.2);
    for (const key of ['hemi', 'sunI', 'near', 'far', 'exposure']) cur[key] += (want[key] - cur[key]) * k;
    for (const key of ['sky', 'ground', 'sun', 'fog']) {
      colors[key].set(cur[key]).lerp(new THREE.Color(want[key]), k);
      cur[key] = colors[key].getHex();
    }
    hemi.color.set(cur.sky); hemi.groundColor.set(cur.ground); hemi.intensity = cur.hemi;
    sun.color.set(cur.sun); sun.intensity = cur.sunI;
    scene.fog.color.set(cur.fog); scene.fog.near = cur.near; scene.fog.far = cur.far;
    scene.background.set(cur.fog).multiplyScalar(0.35);
    renderer.toneMappingExposure = cur.exposure;
  }

  // ---- loop ----
  const ticks = [];
  const clock = new THREE.Clock();
  let frames = 0, stopUntil = 0;
  function frame() {
    // hit-stop: a big blow freezes the world for a few frames (time crawls, it never stops)
    const raw = Math.min(clock.getDelta(), 0.05);
    const dt = performance.now() < stopUntil ? raw * 0.06 : raw;
    const t = clock.elapsedTime;
    for (const fn of ticks) fn(dt, t);
    rig.dist += (rig.wantDist - rig.dist) * (1 - Math.exp(-dt * 10));
    rig.focus.lerp(rig.target, 1 - Math.exp(-dt * 9));
    placeCamera(false);
    // the sun's shadow box follows the hero so shadows stay sharp everywhere
    sun.position.set(rig.focus.x - 14, 30, rig.focus.z + 10);
    sun.target.position.copy(rig.focus);
    blendMood(dt);
    renderer.info.reset();
    if (composer) composer.render(dt); else renderer.render(scene, camera);
    frames++;
  }
  renderer.setAnimationLoop(frame);

  return {
    THREE, renderer, scene, camera, rig, sun, hemi, quality: q,
    onTick: fn => ticks.push(fn),
    hitStop: ms => { stopUntil = Math.max(stopUntil, performance.now() + ms); },
    setMood, placeCamera,
    get frames() { return frames; },
  };
}
