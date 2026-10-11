// Misthollow: Lucifer-collection actors (CC0, see docs/art/SOURCES.md).
// A drop-in for the LPC doll interface the scene already drives:
//   { container, setAction(action, facing), die(), revive(), update(now), dead, destroy() }
// One Phaser sprite per actor; strips are lazily loaded per (pack, anim, dir)
// from art/manifest.json, which tools/art_manifest.py generates from the folder.
(() => {
  const MH = window.MH = window.MH || {};
  // art is served by the aiohttp bridge (:4003, or mud.<host> behind a proxy)
  const BASE = (MH.urls && MH.urls.art) || '/art/';
  let MAN = null, ROLES = null, ready = false;
  const DIRS = ['down', 'up', 'left', 'right'];
  // scene action -> candidate Lucifer anims, first available wins
  const ACTION = {
    idle: ['idle'], walk: ['walk', 'run'], run: ['run', 'walk'],
    attack: ['attack01', 'attack02', 'attack03'], slash: ['attack01'], thrust: ['attack02'], cast: ['attack03', 'attack02', 'attack01'],
    shoot: ['attack01'], hurt: ['hurt'], death: ['death'],
  };
  const ONESHOT = new Set(['attack', 'slash', 'thrust', 'cast', 'shoot', 'hurt']);
  const FPS = { idle: 6, walk: 10, run: 12, attack01: 12, attack02: 12, attack03: 12, hurt: 10, death: 8 };

  function preload(scene) {
    scene.load.json('lucifer_manifest', BASE + 'manifest.json');
    scene.load.json('lucifer_roles', BASE + 'roles.json');
  }
  function init(scene) {
    try { MAN = scene.cache.json.get('lucifer_manifest'); ROLES = scene.cache.json.get('lucifer_roles'); } catch (_) {}
    ready = !!(MAN && MAN.actors && ROLES);
  }
  const isReady = () => ready;

  // ---- resolution -------------------------------------------------------
  // -> pack name; the class recolour rides along as variant() below
  function resolveClass(cls) {
    if (!ready || !cls) return null;
    const e = ROLES.classes[String(cls).toLowerCase()];
    const p = e && (typeof e === 'string' ? e : e.pack);
    return p && MAN.actors[p] ? p : null;
  }
  function variant(cls) {
    const e = ready && cls ? ROLES.classes[String(cls).toLowerCase()] : null;
    if (!e || typeof e === 'string' || (!e.hue && e.sat == null && e.light == null)) return null;
    return { key: String(cls).toLowerCase(), hue: e.hue || 0, sat: e.sat == null ? 1 : e.sat, light: e.light == null ? 1 : e.light, greySat: e.greySat || 0 };
  }
  // bake a recoloured copy of a loaded strip: rotate hue / scale saturation and
  // lightness of coloured pixels, leaving skin tones (warm, mid-light) alone so
  // faces stay human while armour and robes take the class colour
  // the per-pixel class recolour, shared by the Phaser bake and the DOM preview
  function recolourPixels(d, v) {
    for (let i = 0; i < d.length; i += 4) {
      if (d[i + 3] < 8) continue;
      let r = d[i] / 255, gg = d[i + 1] / 255, b = d[i + 2] / 255;
      const mx = Math.max(r, gg, b), mn = Math.min(r, gg, b), l = (mx + mn) / 2;
      let h = 0, s = 0;
      if (mx !== mn) {
        const dd = mx - mn; s = l > 0.5 ? dd / (2 - mx - mn) : dd / (mx + mn);
        h = mx === r ? ((gg - b) / dd + (gg < b ? 6 : 0)) : mx === gg ? ((b - r) / dd + 2) : ((r - gg) / dd + 4);
        h *= 60;
      }
      const skin = s > 0.2 && s < 0.75 && h >= 12 && h <= 42 && l > 0.42 && l < 0.88;
      const grey = s < 0.12;
      if (skin || (grey && !(v.greySat && l > 0.18 && l < 0.8))) { // skin, and greys we leave uncoloured: lightness only
        const L = Math.min(1, l * v.light); const k = l > 0 ? L / l : 1; d[i] = r * k * 255; d[i + 1] = gg * k * 255; d[i + 2] = b * k * 255; continue;
      }
      // grey armour takes the class colour at a muted saturation (steel -> gilt, verdigris, blued)
      if (grey) { h = v.hue; s = v.greySat; } else { h = (h + v.hue + 360) % 360; s = Math.min(1, s * v.sat); }
      const L = Math.min(1, l * v.light);
      const q = L < 0.5 ? L * (1 + s) : L + s - L * s, pp = 2 * L - q;
      const t2c = t => { t = (t + 1) % 1; return t < 1 / 6 ? pp + (q - pp) * 6 * t : t < 0.5 ? q : t < 2 / 3 ? pp + (q - pp) * (2 / 3 - t) * 6 : pp; };
      const hh = h / 360; d[i] = t2c(hh + 1 / 3) * 255; d[i + 1] = t2c(hh) * 255; d[i + 2] = t2c(hh - 1 / 3) * 255;
    }
  }
  function recolour(scene, srcKey, dstKey, v, fw, fh, frames) {
    if (scene.textures.exists(dstKey)) return true;
    try {
      const img = scene.textures.get(srcKey).getSourceImage();
      const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
      const g = c.getContext('2d'); g.drawImage(img, 0, 0);
      const id = g.getImageData(0, 0, c.width, c.height);
      recolourPixels(id.data, v);
      g.putImageData(id, 0, 0);
      scene.textures.addSpriteSheet(dstKey, c, { frameWidth: fw, frameHeight: fh });
      scene.textures.get(dstKey).setFilter(Phaser.Textures.FilterMode.NEAREST);
      if (!scene.anims.exists(dstKey)) {
        const src = scene.anims.get(srcKey);
        scene.anims.create({ key: dstKey, frames: scene.anims.generateFrameNumbers(dstKey, { start: 0, end: frames - 1 }), frameRate: src ? src.frameRate : 10, repeat: src ? src.repeat : -1 });
      }
      return true;
    } catch (_) { return false; }
  }
  // name keywords and mob_ai roles -> pack; 'fallback' means keep the old art
  function mobRule(name, roles, boss) {
    if (!ready) return null;
    const n = String(name || '').toLowerCase();
    const rs = new Set((roles || []).map(r => String(r).toLowerCase()));
    if (boss) rs.add('boss');
    for (const rule of ROLES.mobs) {
      if (rule.match && rule.match.some(k => n.includes(k))) return rule;
      if (rule.roles && rule.roles.some(r => rs.has(r))) return rule;
    }
    return null;
  }
  function resolveMob(name, roles, boss) {
    const rule = mobRule(name, roles, boss);
    return rule && rule.pack !== 'fallback' && MAN.actors[rule.pack] ? rule.pack : null;
  }
  function mobVariant(name, roles, boss) {
    const rule = mobRule(name, roles, boss);
    const v = rule && rule.variant;
    return v ? { key: v.key || rule.pack, hue: v.hue || 0, sat: v.sat == null ? 1 : v.sat, light: v.light == null ? 1 : v.light, greySat: v.greySat || 0 } : null;
  }

  // ---- lazy strip loading ----------------------------------------------
  const pending = {};
  function stripFor(pack, action, facing) {
    const actor = MAN.actors[pack]; if (!actor) return null;
    const dir = DIRS.includes(facing) ? facing : 'down';
    for (const a of (ACTION[action] || ['idle'])) {
      const d = actor.anims[a] && (actor.anims[a][dir] || actor.anims[a].down);
      if (d) return { anim: a, dir: actor.anims[a][dir] ? dir : 'down', ...d };
    }
    const idle = actor.anims.idle && (actor.anims.idle[dir] || actor.anims.idle.down);
    return idle ? { anim: 'idle', dir, ...idle } : null;
  }
  // Strips bypass Phaser's loader: a shared queue stalls when one file sticks
  // in processing, and actors arrive one at a time mid-session. A plain Image
  // (CORS-safe) registered as a spritesheet is race-free.
  function ensureStrip(scene, pack, strip, cb) {
    const key = `luc:${pack}:${strip.anim}:${strip.dir}`;
    if (scene.textures.exists(key)) { cb(key); return; }
    if (pending[key]) { pending[key].push(cb); return; }
    pending[key] = [cb];
    const done = ok => { const cbs = pending[key] || []; delete pending[key]; cbs.forEach(f => { try { f(ok ? key : null); } catch (_) {} }); };
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      try {
        if (!scene.textures.exists(key)) scene.textures.addSpriteSheet(key, img, { frameWidth: strip.w, frameHeight: strip.h });
        const tex = scene.textures.get(key); if (tex) tex.setFilter(Phaser.Textures.FilterMode.NEAREST);
        if (!scene.anims.exists(key)) scene.anims.create({ key, frames: scene.anims.generateFrameNumbers(key, { start: 0, end: strip.frames - 1 }),
          frameRate: FPS[strip.anim] || 10, repeat: (strip.anim === 'idle' || strip.anim === 'walk' || strip.anim === 'run') ? -1 : 0 });
        done(scene.textures.exists(key));
      } catch (e) { console.warn('lucifer strip', key, e); done(false); }
    };
    img.onerror = () => done(false);
    img.src = BASE + strip.file;
  }

  // ---- actor ------------------------------------------------------------
  // scale: tiles per actor height (the scene sizes dolls to ~2 tiles)
  function makeActor(scene, pack, pxHeight, onBuilt, v) {
    const actor = MAN.actors[pack];
    const container = scene.add.container(0, 0);
    const spr = scene.add.sprite(0, 0, '__DEFAULT').setOrigin(0.5, 1).setVisible(false);
    spr.y = 9;                                   // feet on the contact shadow like the other renderers
    container.add(spr);
    const scale = pxHeight / (actor.frame || 48);
    spr.setScale(scale);
    let cur = null, curKey = null, facing = 'down', action = 'idle', built = false;
    const self = {
      container, sprite: spr, pack, _dead: false, _oneShot: false,
      get dead() { return !!this._dead; },
      setAction(a, f) {
        if (this._dead) return;
        if (f) facing = f;
        const want = ONESHOT.has(a);
        // a one-shot in flight finishes before idle/walk may replace it
        if (this._oneShot && !want && spr.anims.isPlaying) return;
        action = a; this._apply(want);
      },
      _apply(oneShot) {
        const strip = stripFor(pack, action, facing); if (!strip) return;
        const key = `luc:${pack}:${strip.anim}:${strip.dir}`;
        if (key === curKey && spr.anims.isPlaying) return;
        cur = strip; curKey = key;
        ensureStrip(scene, pack, strip, k => {
          if (!k || !spr.active || curKey !== key) return;
          if (v) { const vk = k + ':' + v.key; if (recolour(scene, k, vk, v, strip.w, strip.h, strip.frames)) k = vk; }
          spr.setVisible(true);
          spr.play(k);
          this._oneShot = !!oneShot;
          if (oneShot) spr.once('animationcomplete', () => { this._oneShot = false; if (!this._dead) { action = 'idle'; this._apply(false); } });
          if (!built) { built = true; if (onBuilt) { try { onBuilt(self); } catch (_) {} } }
        });
      },
      die() {
        if (this._dead) return;
        this._dead = true; this._oneShot = false;
        const strip = stripFor(pack, 'death', facing); if (!strip) return;
        const key = `luc:${pack}:${strip.anim}:${strip.dir}`; curKey = key;
        ensureStrip(scene, pack, strip, k => { if (!k || !spr.active) return; if (v) { const vk = k + ':' + v.key; if (recolour(scene, k, vk, v, strip.w, strip.h, strip.frames)) k = vk; } spr.setVisible(true); spr.play(k); });
      },
      revive() { if (!this._dead) return; this._dead = false; action = 'idle'; curKey = null; this._apply(false); },
      update() {},                                // Phaser's animation clock drives the frames
      destroy() { try { container.destroy(true); } catch (_) {} },
    };
    self._apply(false);
    return self;
  }

  // ---- DOM preview (character creation) ---------------------------------
  // Animates a class's recoloured idle strip on a plain <canvas> outside
  // Phaser, so the class picker can show the hero you are about to be and
  // play the attack on hover. Returns { setAction(a), destroy() } or null.
  const stripCache = {};
  function loadStrip(file, cb) {
    if (stripCache[file]) { cb(stripCache[file]); return; }
    const img = new Image(); img.crossOrigin = 'anonymous';
    img.onload = () => { stripCache[file] = img; cb(img); };
    img.onerror = () => cb(null);
    img.src = BASE + file;
  }
  function preview(cls, canvas, opts = {}) {
    const pack = resolveClass(cls); if (!pack || !canvas) return null;
    const v = variant(cls);
    const ctx = canvas.getContext('2d'); ctx.imageSmoothingEnabled = false;
    const baked = {};   // anim -> {canvas, w, h, frames}
    let action = 'idle', cur = null, frame = 0, last = 0, raf = 0, alive = true;
    const prep = (a, cb) => {
      const strip = stripFor(pack, a, 'down'); if (!strip) { cb(null); return; }
      if (baked[strip.anim]) { cb(baked[strip.anim]); return; }
      loadStrip(strip.file, img => {
        if (!img) { cb(null); return; }
        const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
        const g = c.getContext('2d'); g.drawImage(img, 0, 0);
        if (v) { try { const id = g.getImageData(0, 0, c.width, c.height); recolourPixels(id.data, v); g.putImageData(id, 0, 0); } catch (_) {} }
        baked[strip.anim] = { canvas: c, w: strip.w, h: strip.h, frames: strip.frames, anim: strip.anim };
        cb(baked[strip.anim]);
      });
    };
    const draw = now => {
      if (!alive) return;
      raf = requestAnimationFrame(draw);
      if (!cur) return;
      const fps = FPS[cur.anim] || 8;
      if (now - last < 1000 / fps) return;
      last = now; frame++;
      if (frame >= cur.frames) { frame = 0; if (action !== 'idle') { action = 'idle'; prep('idle', b => { if (b) { cur = b; frame = 0; } }); return; } }
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const scale = (opts.scale || Math.floor(canvas.height / cur.h)) || 1;
      const dw = cur.w * scale, dh = cur.h * scale;
      ctx.drawImage(cur.canvas, frame * cur.w, 0, cur.w, cur.h, Math.round((canvas.width - dw) / 2), canvas.height - dh, dw, dh);
    };
    prep('idle', b => { if (b) { cur = b; frame = 0; } });
    raf = requestAnimationFrame(draw);
    return {
      setAction(a) { prep(a, b => { if (b && alive) { action = a; cur = b; frame = 0; } }); },
      destroy() { alive = false; cancelAnimationFrame(raf); },
    };
  }

  MH.lucifer = { preload, init, isReady, resolveClass, variant, resolveMob, mobVariant, makeActor, preview };
})();
