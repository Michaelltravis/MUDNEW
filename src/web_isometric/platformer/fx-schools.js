// Misthollow: the school FX engine. Every ability resolves to a magic
// school and a tier; each school owns a visual + sound signature delivered
// in three acts (cast-up at the caster, delivery, impact + aftermath).
// Flagship abilities override everything with handcrafted sequences.
(() => {
  const MH = window.MH = window.MH || {};

  // ---------------- school resolution ----------------
  const SCHOOLS = [
    [/fireball|burning|flame|fire|inferno|combust|ember|phoenix|pyro|meteor|scorch/i, 'fire'],
    [/frost|ice|chill|cold|blizzard|winter|freez|glacial|sindragosa/i, 'frost'],
    [/lightning|shock|storm|thunder|zap|tesla/i, 'lightning'],
    [/holy|divine|bless|sanctuar|judg|crusad|templar|smite|consecrat|righteous|avenging|lay.?on.?hands|resurrect|spirit|prayer|aegis|word.?of.?glory/i, 'holy'],
    [/heal|cure|mend|renew|lightwell|serenity/i, 'holy'],
    [/shadow|vanish|sneak|hide|backstab|garrote|assassin|stealth|night|umbral|void/i, 'shadow'],
    [/drain|vampir|soul|death|necro|corpse|bone|plague|unholy|grave|lich|animate|abomination|enervat|coil/i, 'blood'],
    [/poison|venom|acid|toxin|envenom/i, 'poison'],
    [/entangle|bark|vine|nature|thorn|grasp|root|camouflage|forage/i, 'nature'],
    [/song|sing|sonata|chant|dirge|melody|sonic|note|discord|crescendo|encore|requiem|hymn|chord|magnum|countersong|fascinate|mockery|anthem|lullaby|ballad/i, 'song'],
    [/arcane|magic|missile|mana|blink|teleport|polymorph|illusion|mirror|displacement|rune|sleep|charm|identify|enchant|dispel/i, 'arcane'],
  ];
  const TIER3 = /meteor|apocalypse|magnum|divine.?intervention|resurrect|earthquake|remorseless|blizzard|abomination|mass.?animate|finger.?of.?death|jackpot|avatar|perfect.?form|warlords|word.?of.?recall|grand.?illusion|void.?erupt|breath.?of.?sindragosa|execute$|soul.?reap/i;
  const TIER2 = /fireball|chain|storm|nova|whirlwind|divine.?storm|crescendo|kill.?command|rapid.?fire|templars|holy.?fire|corpse.?expl|pyro|phoenix|deep.?freeze|cold.?snap|flamestrike|call.?lightning|cleave|charge|lay.?on.?hands|consecrat|turn.?undead|army|harvest|vital|execute.?contract/i;

  function classify(text) {
    const t = String(text || '');
    for (const [re, school] of SCHOOLS) if (re.test(t)) return school;
    return 'physical';
  }
  function tierOf(text) {
    if (TIER3.test(text)) return 3;
    if (TIER2.test(text)) return 2;
    return 1;
  }

  const PAL = {
    fire:      { a: 0xffd080, b: 0xff7a2a, c: 0xc03a10, wash: 0xff7a2a },
    frost:     { a: 0xeaf6ff, b: 0x9adcff, c: 0x4a7ac0, wash: 0x9adcff },
    lightning: { a: 0xffffff, b: 0xbfe2ff, c: 0x6aa0ff, wash: 0xbfe2ff },
    holy:      { a: 0xfff6d0, b: 0xffe080, c: 0xd0a030, wash: 0xffe9a0 },
    shadow:    { a: 0xb09ae0, b: 0x6a4ad0, c: 0x2a1a50, wash: 0x6a4ad0 },
    blood:     { a: 0xd6a0ff, b: 0x9a4ae0, c: 0x501a70, wash: 0x9a4ae0 },
    poison:    { a: 0xd0ff8a, b: 0x8ae04a, c: 0x3a701a, wash: 0x8ae04a },
    nature:    { a: 0xc0ff9a, b: 0x6ab04a, c: 0x2a601a, wash: 0x6ab04a },
    song:      { a: 0xffd0ec, b: 0xff8ad0, c: 0xb04a90, wash: 0xff8ad0 },
    arcane:    { a: 0xeed0ff, b: 0xc792ff, c: 0x7a3ad0, wash: 0xc792ff },
    physical:  { a: 0xffffff, b: 0xd8c8a0, c: 0x8a7a50, wash: 0xd8c8a0 },
  };

  // ---------------- procedural sound ----------------
  let actx = null;
  function ctx() {
    if (!actx) { try { actx = new (window.AudioContext || window.webkitAudioContext)(); } catch (_) {} }
    return actx;
  }
  function tone({ f = 220, f2 = null, type = 'sine', dur = 0.2, vol = 0.06, delay = 0 }) {
    const a = ctx(); if (!a) return;
    const t0 = a.currentTime + delay;
    const o = a.createOscillator(), g = a.createGain();
    o.type = type; o.frequency.setValueAtTime(f, t0);
    if (f2) o.frequency.exponentialRampToValueAtTime(Math.max(20, f2), t0 + dur);
    g.gain.setValueAtTime(vol, t0);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    o.connect(g); g.connect(a.destination);
    o.start(t0); o.stop(t0 + dur + 0.05);
  }
  function hiss({ dur = 0.3, vol = 0.05, delay = 0, low = false }) {
    const a = ctx(); if (!a) return;
    const t0 = a.currentTime + delay;
    const n = a.createBufferSource();
    const buf = a.createBuffer(1, a.sampleRate * dur, a.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length);
    n.buffer = buf;
    const g = a.createGain();
    g.gain.setValueAtTime(vol, t0);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    const flt = a.createBiquadFilter();
    flt.type = low ? 'lowpass' : 'highpass';
    flt.frequency.value = low ? 500 : 2000;
    n.connect(flt); flt.connect(g); g.connect(a.destination);
    n.start(t0);
  }
  const SOUNDS = {
    fire: t => { hiss({ dur: 0.35 + t * 0.15, vol: 0.05 + t * 0.02, low: true }); tone({ f: 120, f2: 60, type: 'sawtooth', dur: 0.3 + t * 0.1, vol: 0.05 }); },
    frost: t => { tone({ f: 1400, f2: 2400, type: 'sine', dur: 0.18, vol: 0.04 }); hiss({ dur: 0.22, vol: 0.035 }); if (t > 1) tone({ f: 700, f2: 200, type: 'triangle', dur: 0.3, vol: 0.05, delay: 0.1 }); },
    lightning: t => { hiss({ dur: 0.12, vol: 0.08 }); tone({ f: 80, f2: 50, type: 'square', dur: 0.18 + t * 0.06, vol: 0.07, delay: 0.02 }); },
    holy: t => { [523, 659, 784].slice(0, 1 + t).forEach((f, i) => tone({ f, type: 'triangle', dur: 0.5, vol: 0.04, delay: i * 0.08 })); },
    shadow: t => { tone({ f: 300, f2: 90, type: 'sine', dur: 0.4, vol: 0.05 }); hiss({ dur: 0.4, vol: 0.02, low: true }); },
    blood: t => { tone({ f: 220, f2: 70, type: 'sawtooth', dur: 0.35 + t * 0.1, vol: 0.05 }); },
    poison: t => { tone({ f: 400, f2: 320, type: 'triangle', dur: 0.3, vol: 0.035 }); hiss({ dur: 0.35, vol: 0.025, low: true }); },
    nature: t => { tone({ f: 520, f2: 660, type: 'sine', dur: 0.25, vol: 0.035 }); hiss({ dur: 0.2, vol: 0.02 }); },
    song: t => { [440, 554, 659, 880].slice(0, 2 + t).forEach((f, i) => tone({ f, type: 'sine', dur: 0.22, vol: 0.04, delay: i * 0.07 })); },
    arcane: t => { tone({ f: 880, f2: 1320, type: 'sine', dur: 0.2, vol: 0.04 }); tone({ f: 440, f2: 660, type: 'triangle', dur: 0.25, vol: 0.03, delay: 0.04 }); },
    physical: t => { hiss({ dur: 0.08, vol: 0.06 }); tone({ f: 150, f2: 70, type: 'triangle', dur: 0.12 + t * 0.05, vol: 0.06 }); },
  };

  // ---------------- primitives ----------------
  function burst(scene, x, y, pal, n, speed, scale) {
    const p = scene.add.particles(x, y, 'px_white', {
      speed: { min: speed * 0.4, max: speed },
      scale: { start: scale, end: 0 },
      alpha: { start: 1, end: 0 },
      tint: [pal.a, pal.b, pal.c],
      lifespan: 520, quantity: n, blendMode: 'ADD',
    }).setDepth(56);
    p.explode(n);
    scene.time.delayedCall(700, () => p.destroy());
  }
  function ringShock(scene, x, y, color, r = 34, dur = 380) {
    const g = scene.add.graphics().setDepth(56);
    const ring = { r: 4, a: 0.9 };
    scene.tweens.add({
      targets: ring, r, a: 0, duration: dur, ease: 'cubic.out',
      onUpdate: () => { g.clear(); g.lineStyle(2.5, color, ring.a); g.strokeCircle(x, y, ring.r); },
      onComplete: () => g.destroy(),
    });
  }
  function glowFlash(scene, x, y, color, scale = 0.6) {
    const im = scene.add.image(x, y, 'fx_glow').setBlendMode(Phaser.BlendModes.ADD)
      .setTint(color).setAlpha(0.9).setScale(scale * 0.4).setDepth(55);
    scene.tweens.add({ targets: im, scale, alpha: 0, duration: 360, ease: 'cubic.out', onComplete: () => im.destroy() });
  }
  function decal(scene, x, y, draw, life = 4200) {
    const g = scene.add.graphics().setDepth(2.5);
    draw(g);
    scene.tweens.add({ targets: g, alpha: 0, duration: life, ease: 'sine.in', onComplete: () => g.destroy() });
    return g;
  }
  function wash(scene, color, alpha = 0.16, dur = 420) {
    const r = scene.add.rectangle(0, 0, scene.pxW, scene.pxH, color, alpha)
      .setOrigin(0, 0).setDepth(58).setBlendMode(Phaser.BlendModes.ADD);
    scene.tweens.add({ targets: r, alpha: 0, duration: dur, onComplete: () => r.destroy() });
  }
  function punch(scene, mag = 0.06, dur = 160) {
    const cam = scene.cameras.main;
    const z = cam.zoom;
    scene.tweens.add({ targets: cam, zoom: z * (1 + mag), duration: dur * 0.4, yoyo: true, ease: 'cubic.out' });
  }
  function shake(scene, dur = 220, intensity = 0.012) {
    scene.cameras.main.shake(dur, intensity);
  }
  function pillar(scene, x, y, pal, h = 110, w = 26) {
    const g = scene.add.graphics().setDepth(56).setBlendMode(Phaser.BlendModes.ADD);
    const st = { a: 0.85, w };
    scene.tweens.add({
      targets: st, a: 0, w: w * 0.3, duration: 700, ease: 'sine.in',
      onUpdate: () => {
        g.clear();
        g.fillGradientStyle(pal.a, pal.a, pal.b, pal.b, st.a, st.a, 0, 0);
        g.fillRect(x - st.w / 2, y - h, st.w, h);
      },
      onComplete: () => g.destroy(),
    });
    glowFlash(scene, x, y, pal.b, 0.7);
  }
  function boltFromSky(scene, x, y, pal) {
    const g = scene.add.graphics().setDepth(57);
    g.lineStyle(2.6, pal.a, 1);
    g.beginPath();
    let cx = x, cy = y - 130;
    g.moveTo(cx, cy);
    while (cy < y - 6) { cx = x + (Math.random() * 18 - 9); cy += 14 + Math.random() * 10; g.lineTo(cx, cy); }
    g.lineTo(x, y);
    g.strokePath();
    scene.tweens.add({ targets: g, alpha: 0, duration: 240, onComplete: () => g.destroy() });
  }
  function runeCircle(scene, x, y, pal, dur = 460, r = 16) {
    const g = scene.add.graphics().setDepth(54).setBlendMode(Phaser.BlendModes.ADD);
    const st = { rot: 0, a: 0.85 };
    scene.tweens.add({
      targets: st, rot: Math.PI, a: 0, duration: dur, ease: 'sine.out',
      onUpdate: () => {
        g.clear();
        g.lineStyle(1.5, pal.b, st.a);
        g.strokeCircle(x, y, r);
        for (let i = 0; i < 6; i++) {
          const a2 = st.rot + i * Math.PI / 3;
          g.fillStyle(pal.a, st.a);
          g.fillRect(x + Math.cos(a2) * r - 1.5, y + Math.sin(a2) * r - 1.5, 3, 3);
        }
      },
      onComplete: () => g.destroy(),
    });
  }
  function risers(scene, x, y, pal, n = 8, glyph = null) {
    for (let i = 0; i < n; i++) {
      const obj = glyph
        ? scene.add.text(x + (Math.random() * 26 - 13), y + 6, glyph, { fontSize: '10px' }).setDepth(56).setAlpha(0.9)
        : scene.add.image(x + (Math.random() * 26 - 13), y + 6, 'px_white').setTint(pal.b).setDepth(56).setScale(1.4).setBlendMode(Phaser.BlendModes.ADD);
      scene.tweens.add({
        targets: obj, y: y - 26 - Math.random() * 18, alpha: 0,
        duration: 600 + Math.random() * 500, delay: i * 60, ease: 'sine.out',
        onComplete: () => obj.destroy(),
      });
    }
  }

  // school-specific impact dressing
  const IMPACTS = {
    fire(scene, x, y, t) {
      burst(scene, x, y, PAL.fire, 14 + t * 10, 90 + t * 40, 0.8);
      decal(scene, x, y, g => { g.fillStyle(0x140a06, 0.5); g.fillEllipse(x, y + 4, 26 + t * 10, 12 + t * 4); }, 5200);
      if (t >= 2) wash(scene, PAL.fire.wash, 0.10 + t * 0.03);
      risers(scene, x, y, PAL.fire, 4 + t * 3);
    },
    frost(scene, x, y, t) {
      const g = decal(scene, x, y, gg => {
        gg.fillStyle(0xbfeaff, 0.30);
        gg.fillEllipse(x, y + 4, 26 + t * 10, 12 + t * 4);
      }, 4600);
      for (let i = 0; i < 5 + t * 3; i++) {
        const a = Math.random() * Math.PI * 2, d = 6 + Math.random() * 14;
        const sx = x + Math.cos(a) * d, sy = y + Math.sin(a) * d;
        const sh = scene.add.graphics().setDepth(56);
        sh.fillStyle(0xeaf6ff, 0.9);
        sh.fillTriangle(sx, sy - 7 - t * 2, sx + 3, sy + 2, sx - 3, sy + 2);
        scene.tweens.add({ targets: sh, alpha: 0, duration: 900 + Math.random() * 600, onComplete: () => sh.destroy() });
      }
      if (t >= 2) wash(scene, PAL.frost.wash, 0.10);
      burst(scene, x, y, PAL.frost, 10 + t * 6, 70, 0.6);
    },
    lightning(scene, x, y, t) {
      boltFromSky(scene, x, y, PAL.lightning);
      if (t >= 2) boltFromSky(scene, x + 10, y + 4, PAL.lightning);
      wash(scene, 0xffffff, 0.10 + t * 0.05, 180);
      burst(scene, x, y, PAL.lightning, 10 + t * 6, 120, 0.6);
      if (t >= 2) shake(scene, 160, 0.008);
    },
    holy(scene, x, y, t) {
      pillar(scene, x, y, PAL.holy, 90 + t * 30, 20 + t * 8);
      decal(scene, x, y, g => { g.lineStyle(1.5, 0xffe9a0, 0.5); g.strokeCircle(x, y + 3, 14 + t * 5); }, 3800);
      if (t >= 2) wash(scene, PAL.holy.wash, 0.12);
      risers(scene, x, y, PAL.holy, 4 + t * 3, '✦');
    },
    shadow(scene, x, y, t) {
      const v = scene.add.image(x, y, 'fx_glow').setTint(0x100a20).setAlpha(0.8).setScale(0.5).setDepth(55);
      scene.tweens.add({ targets: v, scale: 0.1, alpha: 0, angle: 180, duration: 500, onComplete: () => v.destroy() });
      burst(scene, x, y, PAL.shadow, 10 + t * 6, 70, 0.7);
      if (t >= 2) wash(scene, 0x201040, 0.16);
    },
    blood(scene, x, y, t) {
      burst(scene, x, y, PAL.blood, 12 + t * 8, 80, 0.7);
      risers(scene, x, y, PAL.blood, 3 + t * 2, '💀');
      if (t >= 2) wash(scene, PAL.blood.wash, 0.12);
    },
    poison(scene, x, y, t) {
      const p = scene.add.particles(x, y, 'px_white', {
        speed: { min: 4, max: 18 }, scale: { start: 1.6, end: 2.8 },
        alpha: { start: 0.35, end: 0 }, tint: [0x8ae04a, 0x5aa02a],
        lifespan: 1400, frequency: 70,
      }).setDepth(55);
      scene.time.delayedCall(900 + t * 300, () => { p.stop(); scene.time.delayedCall(1500, () => p.destroy()); });
    },
    nature(scene, x, y, t) {
      for (let i = 0; i < 3 + t * 2; i++) {
        const g = scene.add.graphics().setDepth(56);
        const a = (i / (3 + t * 2)) * Math.PI * 2;
        const st = { l: 0 };
        scene.tweens.add({
          targets: st, l: 16 + t * 5, duration: 420, delay: i * 50, ease: 'sine.out',
          onUpdate: () => {
            g.clear(); g.lineStyle(2, 0x6ab04a, 0.85);
            g.beginPath(); g.moveTo(x, y);
            g.lineTo(x + Math.cos(a) * st.l, y + Math.sin(a) * st.l - st.l * 0.5);
            g.strokePath();
          },
          onComplete: () => scene.tweens.add({ targets: g, alpha: 0, duration: 700, onComplete: () => g.destroy() }),
        });
      }
      burst(scene, x, y, PAL.nature, 8 + t * 4, 50, 0.6);
    },
    song(scene, x, y, t) {
      for (let i = 0; i < 5 + t * 3; i++) {
        const n = scene.add.text(x, y, ['♪', '♫', '♬'][i % 3], { fontSize: `${10 + t * 2}px`, color: '#ff8ad0' }).setDepth(56);
        const a = (i / (5 + t * 3)) * Math.PI * 2;
        scene.tweens.add({
          targets: n, x: x + Math.cos(a + 1) * (26 + t * 8), y: y + Math.sin(a + 1) * (22 + t * 6) - 16,
          alpha: 0, angle: 60, duration: 800 + i * 70, ease: 'sine.out', onComplete: () => n.destroy(),
        });
      }
      if (t >= 2) wash(scene, PAL.song.wash, 0.10);
    },
    arcane(scene, x, y, t) {
      runeCircle(scene, x, y, PAL.arcane, 520, 14 + t * 6);
      burst(scene, x, y, PAL.arcane, 10 + t * 7, 90, 0.7);
      if (t >= 2) wash(scene, PAL.arcane.wash, 0.10);
    },
    physical(scene, x, y, t) {
      ringShock(scene, x, y, 0xd8c8a0, 22 + t * 12, 300);
      burst(scene, x, y, PAL.physical, 8 + t * 6, 90, 0.6);
      if (t >= 2) shake(scene, 140, 0.007);
    },
  };

  // ---------------- flagship sequences ----------------
  const FLAGSHIPS = [
    [/meteor/i, (s, c, x, y) => {
      const rock = s.add.image(x - 90, y - 150, 'fx_glow').setTint(0xff7a2a).setScale(0.5).setDepth(57).setBlendMode(Phaser.BlendModes.ADD);
      s.tweens.add({
        targets: rock, x, y, duration: 480, ease: 'quad.in',
        onComplete: () => {
          rock.destroy();
          IMPACTS.fire(s, x, y, 3); ringShock(s, x, y, 0xff7a2a, 60, 500);
          shake(s, 320, 0.02); punch(s, 0.08); wash(s, 0xff7a2a, 0.2);
          SOUNDS.fire(3); hiss({ dur: 0.5, vol: 0.09, low: true });
        },
      });
    }],
    [/fireball|pyroblast/i, (s, c, x, y) => {
      const b = s.add.image(c.x, c.y, 'fx_glow').setTint(0xff9a4a).setScale(0.35).setDepth(57).setBlendMode(Phaser.BlendModes.ADD);
      const trail = s.add.particles(0, 0, 'px_white', { follow: b, speed: 10, scale: { start: 0.8, end: 0 }, tint: [0xffd080, 0xff7a2a], lifespan: 320, frequency: 18, blendMode: 'ADD' }).setDepth(56);
      s.tweens.add({
        targets: b, x, y, duration: 320, ease: 'sine.in',
        onComplete: () => {
          trail.destroy(); b.destroy();
          IMPACTS.fire(s, x, y, 2); ringShock(s, x, y, 0xff7a2a, 44, 420); punch(s, 0.05);
          SOUNDS.fire(2);
        },
      });
    }],
    [/blizzard|remorseless.?winter|cold.?snap|ice.?storm/i, (s, c, x, y) => {
      wash(s, PAL.frost.wash, 0.18, 1400);
      SOUNDS.frost(3);
      for (let i = 0; i < 16; i++) {
        s.time.delayedCall(i * 90, () => {
          const sx = x + (Math.random() * 90 - 45), sy = y + (Math.random() * 60 - 30);
          boltLikeShard(s, sx, sy);
        });
      }
      function boltLikeShard(s2, sx, sy) {
        const sh = s2.add.graphics().setDepth(57);
        sh.fillStyle(0xeaf6ff, 0.95);
        sh.fillTriangle(sx, sy - 90, sx + 3, sy - 78, sx - 3, sy - 78);
        s2.tweens.add({
          targets: sh, y: 84, duration: 240, ease: 'quad.in',
          onComplete: () => { sh.destroy(); IMPACTS.frost(s2, sx, sy, 1); },
        });
      }
    }],
    [/chain.?lightning/i, (s, c, x, y) => {
      const mobs = [...s.entities.values()].filter(e => e.kind === 'mob' && e.sprite).slice(0, 4);
      let px2 = c.x, py2 = c.y;
      const targets = mobs.length ? mobs.map(m => ({ x: m.sprite.x, y: m.sprite.y })) : [{ x, y }];
      targets.forEach((t2, i) => {
        s.time.delayedCall(i * 120, () => {
          const g = s.add.graphics().setDepth(57);
          g.lineStyle(2.4, 0xbfe2ff, 1);
          g.beginPath(); g.moveTo(px2, py2);
          const segs = 5;
          for (let k = 1; k <= segs; k++) {
            g.lineTo(px2 + (t2.x - px2) * (k / segs) + (Math.random() * 14 - 7), py2 + (t2.y - py2) * (k / segs) + (Math.random() * 14 - 7));
          }
          g.strokePath();
          s.tweens.add({ targets: g, alpha: 0, duration: 200, onComplete: () => g.destroy() });
          IMPACTS.lightning(s, t2.x, t2.y, 1);
          px2 = t2.x; py2 = t2.y;
        });
      });
      SOUNDS.lightning(2);
    }],
    [/earthquake/i, (s, c, x, y) => {
      shake(s, 700, 0.022); punch(s, 0.06, 280);
      SOUNDS.physical(3); hiss({ dur: 0.8, vol: 0.08, low: true });
      for (let i = 0; i < 5; i++) {
        decal(s, x + (Math.random() * 80 - 40), y + (Math.random() * 50 - 25), g => {
          g.lineStyle(2, 0x140a06, 0.6);
          let cx2 = x + (Math.random() * 80 - 40), cy2 = y + (Math.random() * 50 - 25);
          g.beginPath(); g.moveTo(cx2, cy2);
          for (let k = 0; k < 4; k++) { cx2 += Math.random() * 24 - 12; cy2 += Math.random() * 16 - 8; g.lineTo(cx2, cy2); }
          g.strokePath();
        }, 5200);
      }
    }],
    [/divine.?intervention|resurrect|word.?of.?recall|lay.?on.?hands/i, (s, c, x, y) => {
      pillar(s, x, y, PAL.holy, 150, 40);
      wash(s, PAL.holy.wash, 0.2, 800);
      ringShock(s, x, y, 0xffe9a0, 56, 700);
      risers(s, x, y, PAL.holy, 12, '✦');
      punch(s, 0.05, 260);
      SOUNDS.holy(3);
    }],
    [/magnum.?opus|crescendo/i, (s, c, x, y) => {
      wash(s, PAL.song.wash, 0.16, 900);
      SOUNDS.song(3);
      for (let i = 0; i < 14; i++) {
        s.time.delayedCall(i * 70, () => {
          const n = s.add.text(c.x, c.y, ['♪', '♫', '♬', '♩'][i % 4], { fontSize: '14px', color: '#ff8ad0' }).setDepth(57);
          const a = (i / 14) * Math.PI * 2;
          s.tweens.add({ targets: n, x: c.x + Math.cos(a) * 70, y: c.y + Math.sin(a) * 50 - 20, alpha: 0, angle: 120, duration: 1100, ease: 'sine.out', onComplete: () => n.destroy() });
        });
      }
      ringShock(s, c.x, c.y, 0xff8ad0, 64, 800);
    }],
    [/apocalypse|mass.?animate|army.?of/i, (s, c, x, y) => {
      wash(s, 0x205020, 0.2, 1000);
      SOUNDS.blood(3); shake(s, 400, 0.012);
      for (let i = 0; i < 8; i++) {
        s.time.delayedCall(i * 110, () => {
          const gx = x + (Math.random() * 90 - 45), gy = y + (Math.random() * 50 - 25);
          IMPACTS.blood(s, gx, gy, 1);
          decal(s, gx, gy, g => { g.fillStyle(0x101408, 0.5); g.fillEllipse(gx, gy + 3, 16, 7); }, 4200);
        });
      }
    }],
    [/corpse.?explosion/i, (s, c, x, y) => {
      IMPACTS.blood(s, x, y, 3);
      ringShock(s, x, y, 0x9a4ae0, 52, 460);
      burst(s, x, y, { a: 0xc04040, b: 0x802020, c: 0x401010 }, 22, 130, 0.9);
      wash(s, 0x802020, 0.14); punch(s, 0.05); shake(s, 220, 0.012);
      SOUNDS.blood(3);
    }],
    [/phoenix/i, (s, c, x, y) => {
      const ph = s.add.particles(c.x, c.y, 'px_white', { speed: 16, scale: { start: 1.2, end: 0 }, tint: [0xffd080, 0xff7a2a], lifespan: 420, frequency: 8, blendMode: 'ADD' }).setDepth(57);
      const carrier = s.add.image(c.x, c.y - 20, 'fx_glow').setTint(0xff9a4a).setScale(0.4).setDepth(57).setBlendMode(Phaser.BlendModes.ADD);
      ph.startFollow(carrier);
      s.tweens.add({
        targets: carrier, x, y: y - 16, duration: 460, ease: 'sine.inOut',
        onComplete: () => {
          ph.destroy(); carrier.destroy();
          IMPACTS.fire(s, x, y, 2); pillar(s, x, y, PAL.fire, 70, 18);
          SOUNDS.fire(2);
        },
      });
    }],
    [/whirlwind|divine.?storm/i, (s, c) => {
      SOUNDS.physical(2);
      for (let i = 0; i < 3; i++) {
        s.time.delayedCall(i * 130, () => ringShock(s, c.x, c.y, i % 2 ? 0xffffff : 0xd8c8a0, 30 + i * 12, 340));
      }
      const g = s.add.graphics().setDepth(57);
      const st = { rot: 0, a: 0.9 };
      s.tweens.add({
        targets: st, rot: Math.PI * 3, a: 0, duration: 600,
        onUpdate: () => {
          g.clear(); g.lineStyle(2.5, 0xffffff, st.a);
          for (let k = 0; k < 3; k++) {
            const a2 = st.rot + k * Math.PI * 2 / 3;
            g.beginPath();
            g.arc(c.x, c.y, 22, a2, a2 + 1.1);
            g.strokePath();
          }
        },
        onComplete: () => g.destroy(),
      });
    }],
    [/execute$|soul.?reap|vital$/i, (s, c, x, y) => {
      if (s.freezeFrame) s.freezeFrame(120);
      const g = s.add.graphics().setDepth(58);
      g.lineStyle(3, 0xffffff, 1);
      g.beginPath(); g.moveTo(x - 18, y - 18); g.lineTo(x + 18, y + 18); g.strokePath();
      s.time.delayedCall(90, () => { g.lineStyle(3, 0xff5050, 1); g.beginPath(); g.moveTo(x + 18, y - 18); g.lineTo(x - 18, y + 18); g.strokePath(); });
      s.tweens.add({ targets: g, alpha: 0, duration: 480, delay: 180, onComplete: () => g.destroy() });
      punch(s, 0.07, 180);
      SOUNDS.physical(3);
    }],
    [/jackpot/i, (s, c, x, y) => {
      SOUNDS.song(2);
      tone({ f: 1040, type: 'square', dur: 0.08, vol: 0.05 }); tone({ f: 1300, type: 'square', dur: 0.1, vol: 0.05, delay: 0.1 });
      for (let i = 0; i < 18; i++) {
        const coin = s.add.image(x, y - 8, 'px_white').setTint(0xffd44a).setScale(2).setDepth(57);
        s.tweens.add({
          targets: coin, x: x + (Math.random() * 60 - 30), y: y + 14,
          duration: 500 + Math.random() * 300, delay: i * 35, ease: 'bounce.out',
          onComplete: () => s.tweens.add({ targets: coin, alpha: 0, duration: 300, onComplete: () => coin.destroy() }),
        });
      }
      glowFlash(s, x, y, 0xffd44a, 0.8);
    }],
    [/raise.?abomination|animate.?dead/i, (s, c, x, y) => {
      shake(s, 300, 0.01);
      decal(s, x, y, g => { g.fillStyle(0x101408, 0.6); g.fillEllipse(x, y + 4, 30, 13); }, 5000);
      burst(s, x, y, { a: 0xe0dac4, b: 0xa89e80, c: 0x6a604a }, 16, 90, 0.7);
      risers(s, x, y, PAL.blood, 6, '💀');
      SOUNDS.blood(2);
    }],
    [/templars.?verdict|holy.?fire|flamestrike/i, (s, c, x, y) => {
      pillar(s, x, y, PAL.holy, 110, 26);
      ringShock(s, x, y, 0xffe9a0, 38, 420);
      punch(s, 0.04);
      SOUNDS.holy(2);
    }],
    [/breath.?of.?sindragosa|deep.?freeze/i, (s, c, x, y) => {
      const p = s.add.particles(c.x, c.y, 'px_white', {
        speed: { min: 80, max: 160 }, scale: { start: 1, end: 0 },
        tint: [0xeaf6ff, 0x9adcff], lifespan: 480, frequency: 8,
        angle: { min: Phaser.Math.RadToDeg(Math.atan2(y - c.y, x - c.x)) - 16, max: Phaser.Math.RadToDeg(Math.atan2(y - c.y, x - c.x)) + 16 },
        blendMode: 'ADD',
      }).setDepth(57);
      s.time.delayedCall(520, () => { p.stop(); s.time.delayedCall(600, () => p.destroy()); });
      s.time.delayedCall(260, () => IMPACTS.frost(s, x, y, 3));
      wash(s, PAL.frost.wash, 0.16, 800);
      SOUNDS.frost(3);
    }],
    [/grand.?illusion|mirror.?image|displacement/i, (s, c) => {
      SOUNDS.arcane(2);
      for (let i = 0; i < 4; i++) {
        const ghost = s.add.sprite(c.x, c.y, c.texture ? c.texture.key : 'td_player_warrior', 'd0')
          .setScale(c.scaleX || 0.25).setAlpha(0.5).setTint(0xc792ff).setDepth(56);
        const a = i * Math.PI / 2;
        s.tweens.add({ targets: ghost, x: c.x + Math.cos(a) * 26, y: c.y + Math.sin(a) * 20, alpha: 0, duration: 900, ease: 'sine.out', onComplete: () => ghost.destroy() });
      }
      runeCircle(s, c.x, c.y, PAL.arcane, 700, 22);
    }],
    [/void.?eruption|shadowform|finger.?of.?death/i, (s, c, x, y) => {
      wash(s, 0x100828, 0.24, 700);
      IMPACTS.shadow(s, x, y, 3);
      ringShock(s, x, y, 0x6a4ad0, 50, 520);
      punch(s, 0.06); SOUNDS.shadow(3);
    }],
  ];

  // ---------------- public API ----------------
  MH.schoolFx = {
    classify, tierOf,
    // returns true when a flagship sequence consumed the cast
    flagship(scene, text, caster, tx, ty) {
      for (const [re, fn] of FLAGSHIPS) {
        if (re.test(text)) {
          try { fn(scene, caster, tx, ty); } catch (_) { return false; }
          return true;
        }
      }
      return false;
    },
    castUp(scene, caster, school) {
      const pal = PAL[school] || PAL.arcane;
      runeCircle(scene, caster.x, caster.y + 8, pal, 360, 13);
    },
    impact(scene, x, y, school, t) {
      const pal = PAL[school] || PAL.physical;
      glowFlash(scene, x, y, pal.b, 0.4 + t * 0.18);
      (IMPACTS[school] || IMPACTS.physical)(scene, x, y, t);
      if (t >= 3) { punch(scene, 0.06); }
      (SOUNDS[school] || SOUNDS.physical)(t);
    },
  };
})();
