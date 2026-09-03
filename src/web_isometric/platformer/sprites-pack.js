// Misthollow: artist sprite pack integration (Kenney "Tiny Dungeon", CC0).
// Hand-drawn 16x16 pixel characters replace the procedural actor sheets
// under the same td_player_* / td_mob_* keys and frame names, so every
// existing system (animation, combat FX, markers, tooltips) just works.
// Variants are derived with hue rotation so the full cast stays distinct.
(() => {
  const MH = window.MH = window.MH || {};
  const TILE = 16, GAP = 0, COLS = 12;   // tilemap_packed.png: 192x176, gapless grid
  const FRAMES = ['d0', 'd1', 'u0', 'u1', 's0', 's1', 'atk_d', 'atk_u', 'atk_s', 'hurt', 'death', 'rest', 'sleep'];

  // tile index = row * 12 + col in tilemap_packed.png
  const CAST = {
    // ---- player classes ----
    player_warrior:     { tile: 96 },                       // open-face knight
    player_paladin:     { tile: 97 },                       // full-helm knight
    player_mage:        { tile: 84 },                       // purple wizard
    player_necromancer: { tile: 84, hue: 110, dark: 0.25 }, // wizard, sickly green-violet
    player_thief:       { tile: 98 },                       // hooded rogue
    player_assassin:    { tile: 98, dark: 0.35 },           // rogue in black
    player_ranger:      { tile: 112 },                      // headband hunter
    player_cleric:      { tile: 100 },                      // robed elder
    player_bard:        { tile: 99, hue: 30 },              // performer
    // ---- mob archetypes ----
    mob_citizen:        { tile: 85 },
    mob_guard:          { tile: 96, hue: 160 },             // steel-blue knight
    mob_caster:         { tile: 84, hue: 200 },
    mob_goblinoid:      { tile: 109, hue: 70 },             // cyclops gone green
    mob_undead:         { tile: 87 },
    mob_ghost:          { tile: 121, alpha: 0.75 },
    mob_demon:          { tile: 110 },
    mob_dragon:         { tile: 110, hue: -20, scale: 1.45 },
    mob_beast:          { tile: 123 },                      // rat/beast
    mob_bird:           { tile: 120 },                      // bat
    mob_insect:         { tile: 122 },                      // spider
    mob_slime:          { tile: 108 },
    mob_aquatic:        { tile: 108, hue: 130 },            // blue slime
    mob_elemental:      { tile: 124 },                      // stone golem
    // ---- coverage audit additions ----
    mob_reptile:        { tile: 123, hue: 95, dark: 0.05 }, // green scaled quadruped
    mob_construct:      { tile: 124, dark: 0.15 },          // animate stone
    mob_celestial:      { tile: 121, hue: 35, alpha: 0.95 },// radiant winged
    mob_fey:            { tile: 121, hue: 250, alpha: 0.85, scale: 0.85 },
    mob_plant:          { tile: 108, hue: 55 },             // verdant mass
    mob_rogue:          { tile: 98, dark: 0.2 },            // hooded cutthroat
    mob_noble:          { tile: 85, hue: 25, crown: true },
    mob_horror:         { tile: 122, hue: 230, scale: 1.2 },// too many eyes
    // ---- guildmasters: the class look, crowned in gold ----
    gm_warrior:         { tile: 96, crown: true },
    gm_paladin:         { tile: 97, crown: true },
    gm_mage:            { tile: 84, crown: true },
    gm_necromancer:     { tile: 84, hue: 110, dark: 0.25, crown: true },
    gm_thief:           { tile: 98, crown: true },
    gm_assassin:        { tile: 98, dark: 0.35, crown: true },
    gm_ranger:          { tile: 112, crown: true },
    gm_cleric:          { tile: 100, crown: true },
    gm_bard:            { tile: 99, hue: 30, crown: true },
  };

  function tileRect(idx) {
    const col = idx % COLS, row = Math.floor(idx / COLS);
    return { x: col * (TILE + GAP), y: row * (TILE + GAP) };
  }

  // build one of our 11-frame actor sheets from a single hand-drawn tile:
  // bob for walking, lunge for attacks, flash for hurt, topple for death
  function buildSheet(scene, key, spec) {
    const SS = MH.SMOOTH_SS;
    const FW = 24 * SS, FH = 24 * SS;
    const src = scene.textures.get('pack_tiny').getSourceImage();
    const { x: sx, y: sy } = tileRect(spec.tile);

    const c = document.createElement('canvas');
    c.width = FW * FRAMES.length;
    c.height = FH;
    const ctx = c.getContext('2d');
    ctx.imageSmoothingEnabled = false;   // crisp pixel scaling
    const filt = [];
    if (spec.hue) filt.push(`hue-rotate(${spec.hue}deg)`);
    if (spec.dark) filt.push(`brightness(${1 - spec.dark})`);
    const filter = filt.join(' ') || 'none';

    const draw = (i, dx, dy, rot = 0, flash = false, alpha = 1) => {
      const ox = i * FW;
      // 16px art at x5 in the 96px frame box; spec.scale grows big mobs
      // (dragons) as far as the frame allows
      const size = Math.round(TILE * 5 * Math.min(spec.scale || 1, 1.18));
      // clamp inside this frame's box so lunge offsets never bleed into
      // the neighboring frame
      const px = Math.max(ox, Math.min(ox + FW - size, ox + (FW - size) / 2 + dx * SS));
      const py = Math.max(0, Math.min(FH - size, FH - size - 2 * SS + dy * SS));
      ctx.save();
      ctx.globalAlpha = (spec.alpha || 1) * alpha;
      ctx.filter = filter;
      if (rot) {
        ctx.translate(px + size / 2, py + size / 2);
        ctx.rotate(rot);
        ctx.drawImage(src, sx, sy, TILE, TILE, -size / 2, -size / 2, size, size);
      } else {
        ctx.drawImage(src, sx, sy, TILE, TILE, px, py, size, size);
      }
      ctx.restore();
      if (spec.crown && i !== 10 && i !== 12) {
        // a gold circlet floats above the brow on every living frame
        const cw = size * 0.34, cx2 = px + size / 2 - cw / 2, cy2 = py + size * 0.02;
        ctx.fillStyle = '#ffd44a';
        ctx.fillRect(cx2, cy2 + cw * 0.18, cw, cw * 0.12);
        for (const fx of [0, 0.42, 0.84]) {
          ctx.fillRect(cx2 + cw * fx, cy2, cw * 0.16, cw * 0.2);
        }
      }
      if (flash) {
        ctx.save();
        ctx.globalCompositeOperation = 'source-atop';
        ctx.fillStyle = 'rgba(255,80,80,0.45)';
        ctx.fillRect(ox, 0, FW, FH);
        ctx.restore();
      }
    };

    draw(0, 0, 0);            // d0
    draw(1, 0, -1);           // d1 (walk bob)
    draw(2, 0, 0);            // u0
    draw(3, 0, -1);           // u1
    draw(4, 0, 0);            // s0 (runtime flipX handles left)
    draw(5, 0, -1);           // s1
    draw(6, 0, 2);            // atk_d lunge
    draw(7, 0, -2);           // atk_u
    draw(8, 2, 0);            // atk_s
    draw(9, 0, 0, 0, true);   // hurt
    draw(10, 0, 3, Math.PI / 2, false, 0.85); // death topple
    draw(11, 0, 4);           // rest: same art, sunk toward the floor (seated)
    draw(12, 0, 5, Math.PI / 2, false, 0.95);  // sleep: lying on its side
    {
      // drifting z's over the sleeper
      const sx2 = 12 * FW;
      ctx.save(); ctx.filter = 'none'; ctx.globalAlpha = 1;
      ctx.fillStyle = '#cfe2ff';
      ctx.font = `bold ${5 * SS}px monospace`; ctx.fillText('z', sx2 + FW - 22 * SS, 26 * SS);
      ctx.font = `bold ${7 * SS}px monospace`; ctx.fillText('z', sx2 + FW - 16 * SS, 18 * SS);
      ctx.restore();
    }

    if (scene.textures.exists(key)) scene.textures.remove(key);
    const tex = scene.textures.addCanvas(key, c);
    FRAMES.forEach((f, i) => tex.add(f, 0, i * FW, 0, FW, FH));
  }

  MH.packSprites = {
    // call after smooth generation; overrides actor sheets with artist art
    apply(scene) {
      if (!scene.textures.exists('pack_tiny')) {
        console.warn('[misthollow] sprite pack not loaded; procedural actors stay');
        return false;
      }
      for (const [name, spec] of Object.entries(CAST)) {
        buildSheet(scene, `td_${name}`, spec);
      }
      // animations reference texture keys + frame names, both unchanged,
      // but Phaser caches frame objects per anim - rebuild them
      for (const name of Object.keys(CAST)) {
        const key = `td_${name}`;
        ['walkd', 'walku', 'walks', 'hurt', 'death', 'rest', 'sleep'].forEach(a => {
          const ak = `${key}_${a}`;
          if (scene.anims.exists(ak)) scene.anims.remove(ak);
        });
      }
      MH.tdSprites.registerAnims(scene);
      return true;
    },
  };
})();
