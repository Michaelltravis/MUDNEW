// Misthollow: Lucifer-collection actors (CC0, see docs/art/SOURCES.md).
// A drop-in for the LPC doll interface the scene already drives:
//   { container, setAction(action, facing), die(), revive(), update(now), dead, destroy() }
// One Phaser sprite per actor; strips are lazily loaded per (pack, anim, dir)
// from art/manifest.json, which tools/art_manifest.py generates from the folder.
(() => {
  const MH = window.MH = window.MH || {};
  const BASE = '/art/';
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
  function resolveClass(cls) {
    if (!ready || !cls) return null;
    const p = ROLES.classes[String(cls).toLowerCase()];
    return p && MAN.actors[p] ? p : null;
  }
  // name keywords and mob_ai roles -> pack; 'fallback' means keep the old art
  function resolveMob(name, roles, boss) {
    if (!ready) return null;
    const n = String(name || '').toLowerCase();
    const rs = new Set((roles || []).map(r => String(r).toLowerCase()));
    if (boss) rs.add('boss');
    for (const rule of ROLES.mobs) {
      if (rule.match && rule.match.some(k => n.includes(k))) return rule.pack === 'fallback' ? null : rule.pack;
      if (rule.roles && rule.roles.some(r => rs.has(r))) return rule.pack === 'fallback' ? null : rule.pack;
    }
    return null;
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
  function ensureStrip(scene, pack, strip, cb) {
    const key = `luc:${pack}:${strip.anim}:${strip.dir}`;
    if (scene.textures.exists(key)) { cb(key); return; }
    if (pending[key]) { pending[key].push(cb); return; }
    pending[key] = [cb];
    scene.load.spritesheet(key, BASE + strip.file, { frameWidth: strip.w, frameHeight: strip.h });
    scene.load.once('complete', () => {
      const cbs = pending[key] || []; delete pending[key];
      const ok = scene.textures.exists(key);
      if (ok && !scene.anims.exists(key)) {
        scene.textures.get(key).setFilter(Phaser.Textures.FilterMode.NEAREST);
        scene.anims.create({ key, frames: scene.anims.generateFrameNumbers(key, { start: 0, end: strip.frames - 1 }),
          frameRate: FPS[strip.anim] || 10, repeat: (strip.anim === 'idle' || strip.anim === 'walk' || strip.anim === 'run') ? -1 : 0 });
      }
      cbs.forEach(f => { try { f(ok ? key : null); } catch (_) {} });
    });
    scene.load.start();
  }

  // ---- actor ------------------------------------------------------------
  // scale: tiles per actor height (the scene sizes dolls to ~2 tiles)
  function makeActor(scene, pack, pxHeight, onBuilt) {
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
        ensureStrip(scene, pack, strip, k => { if (k && spr.active) { spr.setVisible(true); spr.play(k); } });
      },
      revive() { if (!this._dead) return; this._dead = false; action = 'idle'; curKey = null; this._apply(false); },
      update() {},                                // Phaser's animation clock drives the frames
      destroy() { try { container.destroy(true); } catch (_) {} },
    };
    self._apply(false);
    return self;
  }

  MH.lucifer = { preload, init, isReady, resolveClass, resolveMob, makeActor };
})();
