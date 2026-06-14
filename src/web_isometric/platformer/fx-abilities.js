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

  // small extras used by casters
  function novaRing(s, x, y, pal, n) { MH.fx.ringShock(s, x, y - 6, pal.b, 38, 420); MH.fx.burst(s, x, y - 6, pal, n || 14, 110, 0.7); }
  function multiBolt(s, c, x, y, color, n, stagger) {
    for (let i = 0; i < n; i++) s.time.delayedCall(i * (stagger || 90), () => proj(s, c, x + rnd(-6, 6), y + rnd(-6, 6), color, { size: 4, life: 200 }));
  }
  function cone(s, c, x, y, pal) {
    const base = Math.atan2(y - c.y, x - c.x);
    const pr = s.add.particles(c.x + Math.cos(base) * 8, c.y - 4 + Math.sin(base) * 8, 'px_white', {
      speed: { min: 80, max: 150 }, angle: { min: Phaser.Math.RadToDeg(base) - 22, max: Phaser.Math.RadToDeg(base) + 22 },
      lifespan: 360, quantity: 7, frequency: 28, tint: [pal.a, pal.b], scale: { start: 0.9, end: 0 }, alpha: { start: 0.9, end: 0 }, blendMode: 'ADD',
    }).setDepth(56);
    s.time.delayedCall(360, () => pr.stop()); s.time.delayedCall(800, () => pr.destroy());
  }

  // ============================ MAGE ============================
  // (fireball/meteor/chain_lightning/blizzard/mirror_image/displacement
  //  keep their flagship cinematics — not re-added here)
  add(/magic.?missile/i, 'ranged', (s, c, x, y) => { multiBolt(s, c, x, y, P().arcane.b, 3, 110); MH.fx.glowFlash(s, x, y - 6, P().arcane.b, 0.5); sound('arcane', 1); });
  add(/burning.?hands/i, 'ranged', (s, c, x, y) => { cone(s, c, x, y, P().fire); MH.fx.decal(s, x, y, g => { g.fillStyle(0x140a06, 0.4); g.fillEllipse(x, y + 4, 24, 10); }); sound('fire', 1); });
  add(/chill.?touch/i, 'ranged', (s, c, x, y) => { proj(s, c, x, y, P().frost.b, { onHit: () => { novaRing(s, x, y, P().frost, 8); glyph(s, x, y, '❄', P().frost.a); } }); sound('frost', 1); });
  add(/lightning.?bolt/i, 'ranged', (s, c, x, y) => { beam(s, c, x, y, P().lightning.a, 3); MH.fx.boltFromSky(s, x, y, P().lightning); MH.fx.spark && s.spark(x, y - 6, P().lightning.b); sound('lightning', 2); });
  add(/color.?spray/i, 'ranged', (s, c, x, y) => { ['fire', 'frost', 'nature', 'arcane', 'song'].forEach((sch, i) => s.time.delayedCall(i * 40, () => cone(s, c, x, y, P()[sch]))); sound('arcane', 2); });
  add(/resonance.?burst|arcane.?explosion/i, 'self', (s, c) => { novaRing(s, c.x, c.y, P().arcane, 24); MH.fx.ringShock(s, c.x, c.y - 6, P().arcane.a, 56, 520); MH.fx.ringShock(s, c.x, c.y - 6, P().arcane.b, 34, 380); MH.fx.punch(s, 0.06); sound('arcane', 2); });
  add(/arcane.?blast/i, 'ranged', (s, c, x, y) => { proj(s, c, x, y, P().arcane.a, { size: 7, onHit: () => novaRing(s, x, y, P().arcane, 16) }); sound('arcane', 2); });
  add(/arcane.?barrage/i, 'ranged', (s, c, x, y) => { multiBolt(s, c, x, y, P().arcane.a, 6, 60); sound('arcane', 2); });
  add(/\bevocation\b/i, 'self', (s, c) => { selfAura(s, c, P().arcane, '✦'); MH.fx.ringShock(s, c.x, c.y - 6, P().arcane.b, 30, 400); sound('arcane', 1); });
  add(/kindling.?focus|combustion/i, 'self', (s, c) => { selfAura(s, c, P().fire, '↑'); sound('fire', 2); });
  add(/rimeheart|icy.?veins/i, 'self', (s, c) => { selfAura(s, c, P().frost, '↑'); sound('frost', 2); });
  add(/quicken|time.?warp/i, 'self', (s, c) => { selfAura(s, c, P().arcane, '⏵'); MH.fx.ringShock(s, c.x, c.y - 6, P().arcane.a, 40, 460); sound('arcane', 2); });
  add(/tower.?echoes|mirror.?image/i, 'self', (s, c) => { for (let i = 0; i < 3; i++) { const g = s.add.image(c.x, c.y - 6, 'fx_glow').setTint(P().arcane.a).setBlendMode(1).setScale(0.5).setDepth(40).setAlpha(0.6); s.tweens.add({ targets: g, x: c.x + (i - 1) * 22, alpha: 0, duration: 600, onComplete: () => g.destroy() }); } sound('arcane', 1); });
  add(/stepwise|phase.?step|mirrorward/i, 'self', (s, c) => { MH.fx.burst(s, c.x, c.y - 6, P().arcane, 12, 110, 0.6); MH.fx.glowFlash(s, c.x, c.y - 6, P().arcane.a, 0.8); sound('arcane', 1); });
  add(/\bsleep\b/i, 'ranged', (s, c, x, y) => { glyph(s, x, y, '💤', null, { size: 15, rise: 20 }); MH.fx.runeCircle(s, x, y, P().shadow, 600, 14); sound('shadow', 1); });
  add(/\b(teleport|blink|fly)\b/i, 'self', (s, c) => { MH.fx.burst(s, c.x, c.y - 6, P().arcane, 14, 120, 0.7); MH.fx.glowFlash(s, c.x, c.y - 6, P().arcane.a, 0.9); sound('arcane', 1); });
  add(/invisibility/i, 'self', (s, c) => { const g = s.add.image(c.x, c.y - 6, 'fx_glow').setTint(P().arcane.a).setBlendMode(1).setScale(0.8).setDepth(40); s.tweens.add({ targets: g, alpha: 0, scale: 0.2, duration: 600, onComplete: () => g.destroy() }); sound('arcane', 1); });
  add(/detect.?magic|identify|scribe|enchant.?weapon/i, 'self', (s, c) => { MH.fx.runeCircle(s, c.x, c.y + 6, P().arcane, 600, 16); glyph(s, c.x, c.y - 6, '✦', P().arcane.a); sound('arcane', 1); });
  add(/mana.?shield|spell.?reflection|stoneskin|ice.?armor|fire.?shield|\barmor\b|\bshield\b/i, 'self', (s, c) => {
    const pal = P().arcane; const g = s.add.graphics().setDepth(40).setBlendMode(1); const st = { a: 0.7 };
    s.tweens.add({ targets: st, a: 0, duration: 800, onUpdate: () => { g.clear(); g.lineStyle(2, pal.b, st.a); g.strokeCircle(c.x, c.y - 6, 17); g.lineStyle(1, pal.a, st.a * 0.6); g.strokeCircle(c.x, c.y - 6, 13); }, onComplete: () => g.destroy() });
    glyph(s, c.x, c.y, '◈', pal.a); sound('arcane', 1);
  });
  add(/protection.?from/i, 'self', (s, c) => { MH.fx.runeCircle(s, c.x, c.y + 6, P().holy, 600, 16); sound('holy', 1); });

  // ============================ CLERIC ============================
  // (divine_intervention/resurrect/word_of_recall/flamestrike/holy_fire
  //  keep their flagships)
  add(/cure.?light|cure.?serious|cure.?critical|prayer.?of.?mending|\bheal\b/i, 'self', (s, c) => {
    MH.fx.risers(s, c.x, c.y, P().holy, 8, '✚'); MH.fx.glowFlash(s, c.x, c.y - 6, P().holy.a, 0.8); MH.fx.ringShock(s, c.x, c.y - 6, P().holy.b, 22, 420); sound('holy', 1);
  });
  add(/group.?heal|spirit.?link|serenity|lightwell/i, 'self', (s, c) => {
    foes(s, 6); MH.fx.ringShock(s, c.x, c.y - 6, P().holy.a, 60, 560);
    MH.fx.risers(s, c.x, c.y, P().holy, 12, '✚'); sound('holy', 2);
  });
  add(/holy.?smite|holysmite/i, 'ranged', (s, c, x, y) => { MH.fx.pillar(s, x, y, P().holy, 90, 18); glyph(s, x, y, '✟', P().holy.a); sound('holy', 2); });
  add(/turn.?undead|dispel.?evil|dispel|mass.?dispel|remove.?curse|remove.?poison/i, 'self', (s, c) => {
    MH.fx.ringShock(s, c.x, c.y - 6, P().holy.a, 48, 500); MH.fx.risers(s, c.x, c.y, P().holy, 8, '✦'); sound('holy', 2);
  });
  add(/\bharm\b/i, 'ranged', (s, c, x, y) => { proj(s, c, x, y, P().shadow.b, { size: 6, onHit: () => MH.fx.burst(s, x, y - 6, P().shadow, 12, 90, 0.7) }); sound('shadow', 2); });
  add(/divine.?word|divine_word|holy.?aura|righteous.?fury|aegis|holy_aura/i, 'self', (s, c) => { selfAura(s, c, P().holy, '✟'); MH.fx.ringShock(s, c.x, c.y - 6, P().holy.a, 40, 460); sound('holy', 2); });
  add(/bless|sanctuary|shield.?of.?faith|divine.?shield|divine.?protection|barkskin|aegis/i, 'self', (s, c) => {
    const g = s.add.graphics().setDepth(40).setBlendMode(1); const st = { a: 0.7 };
    s.tweens.add({ targets: st, a: 0, duration: 800, onUpdate: () => { g.clear(); g.lineStyle(2, P().holy.b, st.a); g.strokeCircle(c.x, c.y - 6, 17); }, onComplete: () => g.destroy() });
    MH.fx.risers(s, c.x, c.y, P().holy, 5, '✦'); glyph(s, c.x, c.y, '✚', P().holy.a); sound('holy', 1);
  });
  add(/earthquake/i, 'self', (s, c) => { MH.fx.shake(s, 600, 0.02); foes(s, 6).forEach(m => MH.fx.ringShock(s, m.sprite.x, m.sprite.y - 6, P().nature.c, 24, 380)); sound('physical', 3); });
  add(/create.?food|create.?water|summon\b/i, 'self', (s, c) => { MH.fx.runeCircle(s, c.x, c.y + 6, P().holy, 600, 16); MH.fx.glowFlash(s, c.x, c.y - 6, P().holy.a, 0.7); sound('holy', 1); });

  // ============================ NECROMANCER ============================
  // (animate_dead/apocalypse/corpse_explosion/finger_of_death keep flagships)
  add(/soul.?bolt/i, 'ranged', (s, c, x, y) => { proj(s, c, x, y, P().shadow.a, { size: 5, onHit: () => MH.fx.burst(s, x, y - 6, P().shadow, 10, 90, 0.6) }); sound('shadow', 1); });
  add(/drain.?soul|vampiric.?touch|energy.?drain|soul.?harvest/i, 'ranged', (s, c, x, y) => {
    beam(s, c, x, y, P().shadow.b, 3);
    // motes flow back to caster
    for (let i = 0; i < 6; i++) s.time.delayedCall(i * 60, () => { const m = s.add.image(x, y - 6, 'px_white').setTint(P().blood.a).setBlendMode(1).setDepth(57); s.tweens.add({ targets: m, x: c.x, y: c.y - 6, alpha: 0, duration: 360, onComplete: () => m.destroy() }); });
    sound('shadow', 2);
  });
  // Soulbinder originals (mistgrasp/wraithfire/mistrot/sever_cord) +
  // legacy names kept so old saves/log lines still animate
  add(/mistgrasp|death.?grip/i, 'ranged', (s, c, x, y) => { beam(s, c, x, y, P().shadow.c, 4); glyph(s, x, y, '✋', P().shadow.a); MH.fx.risers(s, x, y, P().frost, 4); sound('shadow', 2); });
  add(/wraithfire|death.?coil|enervation/i, 'ranged', (s, c, x, y) => { proj(s, c, x, y, P().shadow.a, { ease: 'sine.inout', onHit: () => { novaRing(s, x, y, P().shadow, 14); glyph(s, x, y, '👁', P().shadow.a); } }); sound('shadow', 2); });
  add(/mistrot|plague.?strike/i, 'ranged', (s, c, x, y) => { cone(s, c, x, y, P().poison); MH.fx.decal(s, x, y, g => { g.fillStyle(0x2a3a10, 0.4); g.fillEllipse(x, y + 4, 26, 11); }); glyph(s, x, y, '☣', P().poison.a); sound('poison', 2); });
  add(/sever.?cord|sever.?the.?cord|finger.?of.?death/i, 'ranged', (s, c, x, y) => { s.freezeFrame && s.freezeFrame(90); beam(s, c, x, y, 0xb09ae0, 2); MH.fx.burst(s, x, y - 6, P().shadow, 18, 120, 0.9); glyph(s, x, y, '✂', 0xffffff, { size: 18 }); MH.fx.punch(s, 0.06); sound('shadow', 3); });
  add(/\bpoison\b|weaken|blindness/i, 'ranged', (s, c, x, y) => { cone(s, c, x, y, P().poison); glyph(s, x, y, '☠', P().poison.a); sound('poison', 1); });
  add(/\bfear\b/i, 'ranged', (s, c, x, y) => { glyph(s, x, y, '!', 0x9a4ae0, { size: 18, rise: 22 }); MH.fx.ringShock(s, x, y - 6, P().shadow.b, 22, 320); sound('shadow', 1); });
  add(/soul.?reap|drain_soul/i, 'melee', (s, c, x, y) => { s.freezeFrame && s.freezeFrame(80); MH.fx.burst(s, x, y - 6, P().shadow, 16, 110, 0.8); glyph(s, x, y, '☠', P().shadow.a, { size: 16 }); sound('shadow', 3); });
  add(/bone.?shield|corpse.?shield|summon.?gargoyle/i, 'self', (s, c) => {
    const g = s.add.graphics().setDepth(40); const st = { rot: 0 };
    s.tweens.add({ targets: st, rot: Math.PI * 2, a: 0, duration: 900, onUpdate: () => { g.clear(); g.fillStyle(0xe0dac4, 0.7 * (1 - st.rot / (Math.PI * 2))); for (let i = 0; i < 5; i++) { const a2 = st.rot + i * Math.PI * 0.4; g.fillRect(c.x + Math.cos(a2) * 16 - 1.5, c.y - 6 + Math.sin(a2) * 16 - 3, 3, 6); } }, onComplete: () => g.destroy() });
    sound('shadow', 1);
  });

  // martial/hybrid extras
  function arrowShot(s, c, x, y, color, opt = {}) {
    const ang = Math.atan2(y - c.y, x - c.x);
    const a = s.add.rectangle(c.x, c.y - 6, 12, 1.8, color).setDepth(60).setRotation(ang);
    s.tweens.add({ targets: a, x, y: y - 6, duration: opt.life || 120, ease: 'linear', onComplete: () => { MH.fx.spark && s.spark(x, y - 6, color); a.destroy(); if (opt.onHit) opt.onHit(); } });
  }
  function daggerHit(s, x, y, color) {
    const g = s.add.graphics().setDepth(60); g.lineStyle(2.2, color, 1);
    g.beginPath(); g.moveTo(x - 9, y - 12); g.lineTo(x + 7, y + 4); g.moveTo(x + 8, y - 11); g.lineTo(x - 8, y + 5); g.strokePath();
    s.tweens.add({ targets: g, alpha: 0, duration: 260, onComplete: () => g.destroy() });
    MH.fx.spark && s.spark(x, y - 6, color);
  }
  function notes(s, c, pal, n) {
    for (let i = 0; i < (n || 6); i++) s.time.delayedCall(i * 70, () => glyph(s, c.x + rnd(-16, 16), c.y - rnd(0, 8), ['♪', '♫', '♩'][i % 3], pal.a, { size: rnd(11, 15), rise: rnd(18, 30), life: 900 }));
  }

  // ============================ THIEF / ASSASSIN ============================
  // (jackpot, vital keep flagships)
  add(/backstab|shadowstrike|silence.?strike|nerve.?strike/i, 'melee', (s, c, x, y) => {
    s.freezeFrame && s.freezeFrame(60); daggerHit(s, x, y, 0xb8b2c8);
    MH.fx.burst(s, x, y - 6, P().blood, 10, 90, 0.6); MH.fx.punch(s, 0.04); sound('physical', 2);
  });
  add(/\b(circle|low.?blow|trip|feint|kidney|garrote|hamstring|crippling)\b/i, 'melee', (s, c, x, y) => { daggerHit(s, x, y, 0xb8b2c8); sound('physical', 1); });
  add(/execute.?contract|assassinate|eviscerate|mutilate|envenom/i, 'melee', (s, c, x, y) => {
    s.freezeFrame && s.freezeFrame(90); daggerHit(s, x, y, 0x8a5a9a); daggerHit(s, x + 3, y - 3, 0xd0ff8a);
    MH.fx.burst(s, x, y - 6, P().poison, 12, 100, 0.7); MH.fx.punch(s, 0.06); sound('poison', 2);
  });
  add(/pocket.?sand/i, 'ranged', (s, c, x, y) => { cone(s, c, x, y, { a: 0xe8d8a0, b: 0xc0a060 }); glyph(s, x, y, '✦', 0xe8d8a0); sound('physical', 1); });
  add(/\bsteal\b|pick.?lock|pick.?pocket|\bpick\b/i, 'melee', (s, c, x, y) => { glyph(s, x, y, '🪙', null, { size: 13 }); MH.fx.glowFlash(s, x, y - 6, 0xe8c168, 0.4); sound('arcane', 1); });
  add(/rigged.?dice|perfect.?crime|preparation|cold.?blood|deadly.?poison|crippling.?poison/i, 'self', (s, c) => { selfAura(s, c, { a: 0xb8b2c8, b: 0x6a4a9a }, '✦'); sound('shadow', 1); });
  add(/\b(sneak|hide|vanish|cloak.?of.?shadows|shadow.?dance|blur|camouflage)\b/i, 'self', (s, c) => {
    const g = s.add.image(c.x, c.y - 6, 'fx_glow').setTint(0x6a4a9a).setBlendMode(1).setScale(0.7).setDepth(40);
    s.tweens.add({ targets: g, alpha: 0, scale: 0.2, duration: 500, onComplete: () => g.destroy() });
    MH.fx.risers(s, c.x, c.y, P().shadow, 4); sound('shadow', 1);
  });
  add(/shadow.?step|shadowstep|shadow.?blink|slip.?away/i, 'melee', (s, c, x, y) => { MH.fx.burst(s, c.x, c.y - 6, P().shadow, 8, 80, 0.5); s.time.delayedCall(80, () => { MH.fx.burst(s, x, y - 6, P().shadow, 8, 80, 0.5); daggerHit(s, x, y, 0x8a5a9a); }); sound('shadow', 2); });
  add(/\bmark\b|marked.?for|hunters.?mark|predators.?mark|expose|vendetta|death.?mark/i, 'ranged', (s, c, x, y) => { glyph(s, x, y, '◎', 0xff5a5a, { size: 16, rise: 8, life: 1100 }); MH.fx.ringShock(s, x, y - 6, 0xff5a5a, 16, 280); sound('physical', 1); });
  add(/\bevasion\b|tumble|escape|disengage|preparation/i, 'self', (s, c) => { MH.fx.ringShock(s, c.x, c.y - 6, 0xcfe2ff, 22, 300); sound('physical', 1); });
  add(/fan.?of.?knives|blade.?dance|bladestorm|killing.?spree/i, 'melee', (s, c, x, y) => { for (let i = 0; i < 6; i++) s.time.delayedCall(i * 50, () => { const a = i / 6 * Math.PI * 2; daggerHit(s, c.x + Math.cos(a) * 22, c.y - 6 + Math.sin(a) * 22, 0xb8b2c8); }); sound('physical', 2); });

  // ============================ RANGER ============================
  add(/aimed.?shot|black.?arrow|serpent.?sting|wyvern.?sting/i, 'ranged', (s, c, x, y) => { s.freezeFrame && s.freezeFrame(60); arrowShot(s, c, x, y, 0xeae6d8, { life: 90, onHit: () => MH.fx.burst(s, x, y - 6, P().physical, 8, 80, 0.5) }); sound('physical', 2); });
  add(/rapid.?fire|rapid.?shot|volley|multi.?shot|marked.?shot/i, 'ranged', (s, c, x, y) => { for (let i = 0; i < 5; i++) s.time.delayedCall(i * 70, () => arrowShot(s, c, x + rnd(-8, 8), y + rnd(-8, 8), 0xeae6d8, { life: 90 })); sound('physical', 2); });
  add(/kill.?command|bestial.?wrath|stampede|alpha.?pack|predators/i, 'ranged', (s, c, x, y) => { glyph(s, x, y, '🐾', null, { size: 16 }); MH.fx.ringShock(s, x, y - 6, P().nature.b, 24, 320); MH.fx.burst(s, x, y - 6, P().nature, 10, 90, 0.6); sound('nature', 2); });
  add(/call.?lightning/i, 'ranged', (s, c, x, y) => { MH.fx.boltFromSky(s, x, y, P().lightning); MH.fx.boltFromSky(s, x + rnd(-10, 10), y, P().lightning); MH.fx.spark && s.spark(x, y - 6, P().lightning.b); sound('lightning', 2); });
  add(/faerie.?fire/i, 'ranged', (s, c, x, y) => { glyph(s, x, y, '✦', P().nature.a, { life: 1200, rise: 6 }); MH.fx.runeCircle(s, x, y, P().nature, 600, 14); sound('nature', 1); });
  add(/entangle|\btame\b|\btrack\b|\bscan\b|forage|gather|camouflage_master/i, 'ranged', (s, c, x, y) => { MH.fx.runeCircle(s, x, y, P().nature, 700, 16); MH.fx.risers(s, x, y, P().nature, 5, '🌿'); sound('nature', 1); });
  add(/briskness|aspect|hunters.?mark|barkskin/i, 'self', (s, c) => { selfAura(s, c, P().nature, '🌿'); sound('nature', 1); });
  add(/explosive.?trap|detect.?traps/i, 'ranged', (s, c, x, y) => { MH.fx.ringShock(s, x, y - 6, P().fire.b, 26, 320); MH.fx.burst(s, x, y - 6, P().fire, 10, 90, 0.6); sound('fire', 2); });

  // ============================ PALADIN ============================
  // (templars_verdict, divine_storm keep flagships; shared holy/cure/bless covered)
  add(/\bsmite\b|hammer.?of.?justice|crusader.?strike|crusaders.?judgment|judgment|seal.?of/i, 'ranged', (s, c, x, y) => { MH.fx.boltFromSky(s, x, y, P().holy); MH.fx.glowFlash(s, x, y - 6, P().holy.a, 0.7); glyph(s, x, y, '✟', P().holy.a); sound('holy', 2); });
  add(/word.?of.?glory|hand.?of.?freedom|consecration|avenging.?wrath|sacred.?shield|divine.?favor|holylight|holy.?light|lay.?on/i, 'self', (s, c) => { selfAura(s, c, P().holy, '✚'); MH.fx.ringShock(s, c.x, c.y - 6, P().holy.a, 36, 440); sound('holy', 2); });
  add(/\boath\b|\bswear\b|detect.?evil|sacred|aura/i, 'self', (s, c) => { MH.fx.runeCircle(s, c.x, c.y + 6, P().holy, 700, 18); glyph(s, c.x, c.y - 6, '✟', P().holy.a); sound('holy', 1); });

  // ============================ BARD ============================
  // (crescendo, magnum_opus keep flagships)
  add(/\b(countersong|encore|epic.?tale|hymn.?of.?hope|perform|song|requiem|siren.?song)\b/i, 'self', (s, c) => { notes(s, c, P().song, 7); MH.fx.ringShock(s, c.x, c.y - 6, P().song.b, 34, 460); sound('song', 2); });
  add(/discordant.?note|chord.?of.?disruption|mockery|mock\b|cackle/i, 'ranged', (s, c, x, y) => { notes(s, c, { a: 0xff8ad0, b: 0xb04a90 }, 4); glyph(s, x, y, '♯', 0xff5a5a, { size: 16 }); MH.fx.ringShock(s, x, y - 6, P().song.b, 20, 280); sound('song', 2); });
  add(/charm|fascinate|mass.?charm|lullaby/i, 'ranged', (s, c, x, y) => { glyph(s, x, y, '♥', 0xff8ad0, { size: 15, rise: 18 }); notes(s, { x, y: y }, P().song, 3); sound('song', 1); });
  add(/\b(haste|slow|heroism|briskness|lore|inspire)\b/i, 'self', (s, c) => { notes(s, c, P().song, 5); MH.fx.glowFlash(s, c.x, c.y - 6, P().song.a, 0.6); sound('song', 1); });

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
