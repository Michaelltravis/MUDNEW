// Misthollow: per-ability FX signatures. Every named spell and skill gets
// its OWN animation here, composed from the shared primitive toolkit
// (MH.fx, exposed by fx-schools.js) plus the scene's own helpers. The
// scene consults MH.abilityFx first (see scene-topdown renderAbilityFx),
// so a match here fully owns the cast; anything unmatched falls back to
// the flagship/school engine.
(() => {
  const MH = window.MH = window.MH || {};

  const P = () => MH.fx.PAL;
  const rnd = (a, b) => a + Math.random() * (b - a);

  // ---------- composite helpers (built on MH.fx + scene) ----------
  // a glowing projectile that flies caster->target, trailing, then bursts
  function proj(s, c, tx, ty, color, opt = {}) {
    const size = opt.size || 5, life = opt.life || 240;
    const orb = s.add.image(c.x, c.y - 6, 'fx_glow').setTint(color).setBlendMode(1)
      .setScale(size / 16).setDepth(57);
    const tr = s.add.particles(c.x, c.y - 6, 'px_white', {
      speed: 0, scale: { start: size / 7, end: 0 }, alpha: { start: 0.8, end: 0 },
      tint: color, lifespan: 200, frequency: 18, blendMode: 'ADD',
    }).setDepth(56);
    tr.startFollow(orb);
    s.tweens.add({
      targets: orb, x: tx, y: ty - 6, duration: life, ease: opt.ease || 'sine.in',
      onComplete: () => {
        tr.stop(); s.time.delayedCall(220, () => tr.destroy());
        orb.destroy();
        if (opt.onHit) opt.onHit(tx, ty);
      },
    });
    return orb;
  }
  // straight beam that snaps in then fades
  function beam(s, c, tx, ty, color, w = 3) {
    const g = s.add.graphics().setDepth(57).setBlendMode(1);
    let a = 0.95;
    g.lineStyle(w, color, a); g.beginPath(); g.moveTo(c.x, c.y - 6); g.lineTo(tx, ty - 6); g.strokePath();
    s.tweens.add({ targets: { a }, a: 0, duration: 260, onUpdate: (t, o) => { g.clear(); g.lineStyle(w, color, o.a); g.beginPath(); g.moveTo(c.x, c.y - 6); g.lineTo(tx, ty - 6); g.strokePath(); }, onComplete: () => g.destroy() });
  }
  // melee crescent arc at the target
  function arcSlash(s, x, y, color, opt = {}) {
    const r = opt.r || 18, ang = opt.ang != null ? opt.ang : 0, span = opt.span || 1.6;
    const g = s.add.graphics().setDepth(58).setBlendMode(1);
    const st = { p: 0 };
    s.tweens.add({
      targets: st, p: 1, duration: opt.dur || 170, ease: 'cubic.out',
      onUpdate: () => {
        g.clear(); g.lineStyle(opt.w || 3, color, 1 - st.p);
        g.beginPath(); g.arc(x, y - 6, r, ang - span / 2, ang - span / 2 + span * st.p); g.strokePath();
      },
      onComplete: () => g.destroy(),
    });
  }
  // a floating glyph that rises and fades over a target (marks/debuffs)
  function glyph(s, x, y, txt, color, opt = {}) {
    const t = s.add.text(x, y - 14, txt, { fontSize: (opt.size || 13) + 'px', color: opt.css || '#ffffff' })
      .setOrigin(0.5).setDepth(60).setStroke('#000', 3);
    if (color != null) t.setTint(color);
    s.tweens.add({ targets: t, y: y - 14 - (opt.rise || 16), alpha: 0, duration: opt.life || 850, ease: 'sine.out', onComplete: () => t.destroy() });
  }
  // self aura: rune circle under the caster + rising motes
  function selfAura(s, c, pal, gl) {
    MH.fx.runeCircle(s, c.x, c.y + 8, pal, 520, 15);
    MH.fx.risers(s, c.x, c.y, pal, 7, gl || null);
    MH.fx.glowFlash(s, c.x, c.y - 4, pal.b, 0.7);
  }
  // up to n nearby foes, for chains/cleaves/AoE
  function foes(s, n) {
    return [...s.entities.values()].filter(e => e.kind === 'mob' && e.sprite && e.sprite.active).slice(0, n || 6);
  }
  function sound(school, t = 1) { (MH.fx.SOUNDS[school] || MH.fx.SOUNDS.physical)(t); }

  // ============================================================
  // SIGNATURE REGISTRY  —  [regex, { range, fn }]
  // range drives the step-in/out positioning in playAbilityFx
  // ============================================================
  const SIG = [];
  const add = (re, range, fn) => SIG.push([re, { range, fn }]);

  // ============================ WARRIOR ============================
  // brute steel: heavy arcs, shockwaves, banners — no magic color
  const STEEL = 0xe8e2d0, RAGE = 0xff6a4a, IRON = 0x9aa0b4;

  add(/\bstrike\b/i, 'melee', (s, c, x, y) => {
    arcSlash(s, x, y, STEEL, { r: 16, ang: 0.3, w: 3 });
    MH.fx.glowFlash(s, x, y - 6, STEEL, 0.5); sound('physical', 1);
  });
  add(/mortal.?strike/i, 'melee', (s, c, x, y) => {
    s.freezeFrame && s.freezeFrame(70);
    arcSlash(s, x, y, RAGE, { r: 22, ang: -0.4, w: 5, dur: 200 });
    MH.fx.burst(s, x, y - 6, P().fire, 12, 90, 0.7);
    glyph(s, x, y, '⚔', RAGE); MH.fx.punch(s, 0.05); sound('physical', 2);
  });
  add(/\bbash\b/i, 'melee', (s, c, x, y) => {
    // shield shove: a flat impact disc + knock lines
    MH.fx.ringShock(s, x, y - 6, IRON, 26, 320);
    glyph(s, x, y, '🛡', null, { size: 14 }); MH.fx.shake(s, 140, 0.01); sound('physical', 2);
  });
  add(/shield.?slam/i, 'melee', (s, c, x, y) => {
    MH.fx.ringShock(s, x, y - 6, 0xcfe2ff, 30, 340); MH.fx.ringShock(s, x, y - 6, IRON, 18, 260);
    MH.fx.burst(s, x, y - 6, P().physical, 10, 80, 0.6); MH.fx.punch(s, 0.06); sound('physical', 2);
  });
  add(/shield.?block/i, 'self', (s, c) => {
    const g = s.add.image(c.x, c.y - 6, 'fx_glow').setTint(0xcfe2ff).setBlendMode(1).setScale(0.2).setDepth(40);
    s.tweens.add({ targets: g, scale: 1.0, alpha: 0, duration: 420, onComplete: () => g.destroy() });
    glyph(s, c.x, c.y, '🛡', null); sound('physical', 1);
  });
  add(/\bcleave\b/i, 'melee', (s, c, x, y) => {
    foes(s, 4).forEach((m, i) => s.time.delayedCall(i * 60, () => {
      arcSlash(s, m.sprite.x, m.sprite.y, STEEL, { r: 20, ang: rnd(-1, 1), w: 4 });
      MH.fx.spark && s.spark(m.sprite.x, m.sprite.y - 6, RAGE);
    }));
    sound('physical', 2);
  });
  add(/whirlwind/i, 'melee', (s, c, x, y) => { // (flagship may also fire; this guarantees a look)
    const g = s.add.graphics().setDepth(58).setBlendMode(1); const st = { r: 0 };
    s.tweens.add({ targets: st, r: Math.PI * 4, duration: 500, onUpdate: () => { g.clear(); g.lineStyle(3, STEEL, 0.8); g.beginPath(); g.arc(c.x, c.y - 6, 22, st.r, st.r + 2.2); g.strokePath(); }, onComplete: () => g.destroy() });
    MH.fx.ringShock(s, c.x, c.y - 6, RAGE, 30, 460); sound('physical', 2);
  });
  add(/\bcharge\b/i, 'melee', (s, c, x, y) => {
    // dust trail toward the foe + impact
    const ang = Math.atan2(y - c.y, x - c.x);
    for (let i = 0; i < 6; i++) s.time.delayedCall(i * 24, () => MH.fx.glowFlash(s, c.x + Math.cos(ang) * i * 14, c.y + Math.sin(ang) * i * 14, IRON, 0.3));
    s.time.delayedCall(150, () => { MH.fx.ringShock(s, x, y - 6, STEEL, 26, 300); MH.fx.punch(s, 0.05); });
    sound('physical', 2);
  });
  add(/heroic.?leap/i, 'melee', (s, c, x, y) => {
    s.time.delayedCall(120, () => { MH.fx.ringShock(s, x, y - 6, RAGE, 36, 380); MH.fx.burst(s, x, y - 6, P().fire, 14, 100, 0.7); MH.fx.shake(s, 200, 0.014); });
    sound('physical', 3);
  });
  add(/\bexecute\b/i, 'melee', (s, c, x, y) => {
    s.freezeFrame && s.freezeFrame(110);
    const g = s.add.graphics().setDepth(60); g.lineStyle(4, 0xffffff, 1);
    g.beginPath(); g.moveTo(x - 16, y - 22); g.lineTo(x + 16, y + 10); g.moveTo(x + 16, y - 22); g.lineTo(x - 16, y + 10); g.strokePath();
    s.tweens.add({ targets: g, alpha: 0, duration: 420, onComplete: () => g.destroy() });
    MH.fx.burst(s, x, y - 6, P().blood, 16, 120, 0.8); MH.fx.punch(s, 0.08); MH.fx.shake(s, 180, 0.016); sound('physical', 3);
  });
  add(/overpower|devastating.?blow|sunder.?armor|shattering.?blow|rend\b/i, 'melee', (s, c, x, y) => {
    arcSlash(s, x, y, RAGE, { r: 19, ang: rnd(-0.6, 0.6), w: 4, dur: 180 });
    MH.fx.burst(s, x, y - 6, P().physical, 9, 80, 0.6); MH.fx.spark && s.spark(x, y - 6, STEEL); sound('physical', 2);
  });
  add(/\bkick\b/i, 'melee', (s, c, x, y) => { arcSlash(s, x, y, STEEL, { r: 14, ang: 1.2, w: 3, dur: 130 }); MH.fx.glowFlash(s, x, y - 6, IRON, 0.4); sound('physical', 1); });
  add(/\brescue\b/i, 'self', (s, c) => { selfAura(s, c, P().holy, '✚'); sound('holy', 1); });
  add(/\b(rally|rallying.?cry|battle.?cry|battle.?shout|commanding.?shout|war.?cry|warcry)\b/i, 'self', (s, c) => {
    MH.fx.ringShock(s, c.x, c.y - 6, 0xffd44a, 40, 520);
    MH.fx.risers(s, c.x, c.y, { a: 0xffe9a8, b: 0xffd44a }, 8, '!');
    glyph(s, c.x, c.y - 8, '⚑', 0xffd44a, { size: 16, rise: 22 }); sound('song', 2);
  });
  add(/second.?wind|adrenaline|rage\b|titans.?wrath|avatar.?of.?war/i, 'self', (s, c) => {
    selfAura(s, c, { a: 0xffcaa0, b: 0xff6a4a }, null); MH.fx.punch(s, 0.04); sound('fire', 1);
  });
  add(/shield.?wall|bone.?shield|ignore.?pain|iron|second_attack|third_attack|tactical/i, 'self', (s, c) => {
    const g = s.add.graphics().setDepth(40).setBlendMode(1); const st = { a: 0.6 };
    s.tweens.add({ targets: st, a: 0, duration: 700, onUpdate: () => { g.clear(); g.lineStyle(2, IRON, st.a); g.strokeCircle(c.x, c.y - 6, 16); }, onComplete: () => g.destroy() });
    glyph(s, c.x, c.y, '🛡', null); sound('physical', 1);
  });
  add(/\b(parry|dodge|disarm)\b/i, 'melee', (s, c, x, y) => { arcSlash(s, x, y, IRON, { r: 13, ang: -0.8, w: 2, dur: 120 }); sound('physical', 1); });
  add(/taunt|intimidate|challenge/i, 'ranged', (s, c, x, y) => { glyph(s, x, y, '💢', null, { size: 15 }); MH.fx.ringShock(s, x, y - 6, RAGE, 18, 260); sound('physical', 1); });

  MH.abilityFx = {
    match(text) { const t = String(text || ''); for (const [re, sig] of SIG) if (re.test(t)) return sig; return null; },
    run(scene, text, caster, tx, ty) {
      const sig = this.match(text); if (!sig) return false;
      try { sig.fn(scene, caster, tx, ty); } catch (_) { return false; }
      return true;
    },
    _SIG: SIG, _add: add, _h: { proj, beam, arcSlash, glyph, selfAura, foes, sound, P, rnd },
  };
})();
