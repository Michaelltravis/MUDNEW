// Misthollow platformer: procedural pixel-art factory.
// Every texture in the game is drawn here at boot — no image downloads.
// Tiles are 16x16; actors are 24x32 frames on horizontal strips registered
// as Phaser canvas textures with named frames.
(() => {
  const MH = window.MH = window.MH || {};
  const T = 16; // tile size

  // deterministic RNG so textures are identical across sessions
  function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function hashStr(s) {
    let h = 2166136261;
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }
  MH.hashStr = hashStr;

  function shade(hex, amt) {
    const n = parseInt(hex.slice(1), 16);
    const c = v => Math.max(0, Math.min(255, v + amt));
    const r = c((n >> 16) & 255), g = c((n >> 8) & 255), b = c(n & 255);
    return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`;
  }
  function hueShift(hex, deg) {
    const n = parseInt(hex.slice(1), 16);
    let r = ((n >> 16) & 255) / 255, g = ((n >> 8) & 255) / 255, b = (n & 255) / 255;
    const mx = Math.max(r, g, b), mn = Math.min(r, g, b);
    let h = 0, s = 0, l = (mx + mn) / 2;
    if (mx !== mn) {
      const d = mx - mn;
      s = l > 0.5 ? d / (2 - mx - mn) : d / (mx + mn);
      if (mx === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
      else if (mx === g) h = ((b - r) / d + 2) / 6;
      else h = ((r - g) / d + 4) / 6;
    }
    h = (h + deg / 360 + 1) % 1;
    const hue2rgb = (p, q, t) => {
      if (t < 0) t += 1; if (t > 1) t -= 1;
      if (t < 1 / 6) return p + (q - p) * 6 * t;
      if (t < 1 / 2) return q;
      if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
      return p;
    };
    let r2, g2, b2;
    if (s === 0) { r2 = g2 = b2 = l; }
    else {
      const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
      const p = 2 * l - q;
      r2 = hue2rgb(p, q, h + 1 / 3); g2 = hue2rgb(p, q, h); b2 = hue2rgb(p, q, h - 1 / 3);
    }
    const to = v => Math.round(v * 255);
    return `#${((to(r2) << 16) | (to(g2) << 8) | to(b2)).toString(16).padStart(6, '0')}`;
  }

  function canvasOf(w, h) {
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    const ctx = c.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    return [c, ctx];
  }

  // ------------------------------------------------------------------
  // Tile themes, keyed by MUD sector_type.
  // pal: sky gradient, back wall, ground top edge, ground fill A/B, accent, liquid
  // ------------------------------------------------------------------
  const THEMES = {
    inside:     { sky: ['#17141f', '#0e0c14'], wall: '#241f2e', wall2: '#1b1724', top: '#6b5a43', fillA: '#43382b', fillB: '#39301f', accent: '#e0b35c', liquid: null, props: ['table', 'candle', 'shelf'] },
    city:       { sky: ['#2a3242', '#151a26'], wall: '#2e3340', wall2: '#262b36', top: '#7a7f8c', fillA: '#4a4f5c', fillB: '#3e4350', accent: '#e8c168', liquid: null, props: ['lamppost', 'crate', 'barrel'] },
    dungeon:    { sky: ['#120a1c', '#080510'], wall: '#231533', wall2: '#1a0f28', top: '#544266', fillA: '#36284a', fillB: '#2c2040', accent: '#9a6cd6', liquid: null, props: ['torch', 'bones', 'chains'] },
    cave:       { sky: ['#100e0c', '#070605'], wall: '#221c16', wall2: '#191510', top: '#5c4c38', fillA: '#3c3226', fillB: '#322a1e', accent: '#c08a4a', liquid: null, props: ['stalagmite', 'rocks', 'mushroom'] },
    forest:     { sky: ['#1c3322', '#0d1d12'], wall: '#15281a', wall2: '#102014', top: '#3f8a4a', fillA: '#4a3a26', fillB: '#3e3120', accent: '#7ad68a', liquid: null, props: ['tree', 'bush', 'mushroom'] },
    field:      { sky: ['#2c4a5c', '#16293a'], wall: '#1d3344', wall2: '#16293a', top: '#5aa84f', fillA: '#4d3d28', fillB: '#413322', accent: '#cce070', liquid: null, props: ['bush', 'flowers', 'fence'] },
    hills:      { sky: ['#33424e', '#1a242e'], wall: '#26323c', wall2: '#1e2830', top: '#6a8a4e', fillA: '#564633', fillB: '#483a29', accent: '#a8c070', liquid: null, props: ['rocks', 'bush', 'fence'] },
    mountain:   { sky: ['#3a4250', '#1e2430'], wall: '#2c323e', wall2: '#232834', top: '#8a8d96', fillA: '#5c6068', fillB: '#4e525a', accent: '#cdd2dc', liquid: null, props: ['rocks', 'stalagmite', 'snowdrift'] },
    desert:     { sky: ['#5c4a30', '#33271a'], wall: '#46392a', wall2: '#3a2f22', top: '#d6b878', fillA: '#a8905c', fillB: '#96804e', accent: '#f0d898', liquid: null, props: ['cactus', 'rocks', 'bones'] },
    swamp:      { sky: ['#1e2e20', '#0e1810'], wall: '#18261c', wall2: '#121e16', top: '#4a6638', fillA: '#3a3528', fillB: '#302c20', accent: '#86b060', liquid: '#3a5a3a', props: ['deadtree', 'mushroom', 'reeds'] },
    water_swim: { sky: ['#1a3a5c', '#0c1f36'], wall: '#16304a', wall2: '#10263c', top: '#caa86a', fillA: '#9a8050', fillB: '#8a7244', accent: '#6cc0e0', liquid: '#2a5a8a', props: ['reeds', 'rocks', 'shells'] },
    water_noswim: { sky: ['#16334e', '#0a1a2c'], wall: '#122a40', wall2: '#0d2032', top: '#caa86a', fillA: '#9a8050', fillB: '#8a7244', accent: '#6cc0e0', liquid: '#1e4a78', props: ['reeds', 'rocks', 'shells'] },
    underwater: { sky: ['#0c2a46', '#06182c'], wall: '#0a2238', wall2: '#081c2e', top: '#3a6a5a', fillA: '#2c4a44', fillB: '#243e38', accent: '#5ce0c0', liquid: '#0c2a46', props: ['coral', 'shells', 'reeds'] },
    flying:     { sky: ['#4a5a7c', '#28344e'], wall: '#3a4660', wall2: '#303a52', top: '#c8d2e8', fillA: '#9aa6c0', fillB: '#8a96b0', accent: '#ffffff', liquid: null, props: ['cloudpuff', 'cloudpuff', 'cloudpuff'] },
    default:    { sky: ['#1e2230', '#10131e'], wall: '#262b3a', wall2: '#1e2230', top: '#6a6e80', fillA: '#464a58', fillB: '#3c404c', accent: '#9aa0b4', liquid: null, props: ['rocks', 'bush', 'crate'] },
  };
  MH.themeForSector = function (sector) {
    return THEMES[sector] ? sector : 'default';
  };
  MH.THEMES = THEMES;

  function dither(ctx, x, y, w, h, colA, colB, rng, density = 0.35) {
    ctx.fillStyle = colA;
    ctx.fillRect(x, y, w, h);
    ctx.fillStyle = colB;
    for (let py = y; py < y + h; py++) {
      for (let px = x; px < x + w; px++) {
        if (rng() < density) ctx.fillRect(px, py, 1, 1);
      }
    }
  }

  function genThemeTiles(scene, name, p) {
    const rng = mulberry32(hashStr(name));

    // ground (solid) tile: bright top edge + dithered earth
    {
      const [c, ctx] = canvasOf(T, T);
      dither(ctx, 0, 0, T, T, p.fillA, p.fillB, rng);
      ctx.fillStyle = p.top;
      ctx.fillRect(0, 0, T, 3);
      ctx.fillStyle = shade(p.top, 30);
      for (let x = 0; x < T; x += 2) if (rng() < 0.5) ctx.fillRect(x, 0, 1, 1);
      ctx.fillStyle = shade(p.fillB, -20);
      for (let i = 0; i < 4; i++) ctx.fillRect(2 + Math.floor(rng() * 12), 5 + Math.floor(rng() * 9), 2, 1);
      scene.textures.addCanvas(`t_${name}_ground`, c);
    }
    // underground fill (no top edge)
    {
      const [c, ctx] = canvasOf(T, T);
      dither(ctx, 0, 0, T, T, p.fillB, shade(p.fillB, -16), rng);
      scene.textures.addCanvas(`t_${name}_fill`, c);
    }
    // one-way platform: plank with brackets
    {
      const [c, ctx] = canvasOf(T, 8);
      ctx.fillStyle = shade(p.top, -10);
      ctx.fillRect(0, 0, T, 4);
      ctx.fillStyle = p.top;
      ctx.fillRect(0, 0, T, 1);
      ctx.fillStyle = shade(p.fillA, -10);
      ctx.fillRect(1, 4, 2, 3); ctx.fillRect(13, 4, 2, 3);
      scene.textures.addCanvas(`t_${name}_plat`, c);
    }
    // ladder
    {
      const [c, ctx] = canvasOf(T, T);
      ctx.fillStyle = shade(p.accent, -60);
      ctx.fillRect(3, 0, 2, T); ctx.fillRect(11, 0, 2, T);
      ctx.fillStyle = shade(p.accent, -30);
      ctx.fillRect(3, 2, 10, 2); ctx.fillRect(3, 9, 10, 2);
      scene.textures.addCanvas(`t_${name}_ladder`, c);
    }
    // back wall tile (subtle pattern)
    {
      const [c, ctx] = canvasOf(T, T);
      dither(ctx, 0, 0, T, T, p.wall, p.wall2, rng, 0.4);
      ctx.fillStyle = shade(p.wall, -10);
      ctx.fillRect(0, 7, T, 1); ctx.fillRect(0, 15, T, 1);
      ctx.fillRect(7, 0, 1, 8); ctx.fillRect(15, 8, 1, 8);
      scene.textures.addCanvas(`t_${name}_wall`, c);
    }
    // background arched doorway (north exit), 32x48
    {
      const [c, ctx] = canvasOf(32, 48);
      ctx.fillStyle = shade(p.wall, 24);
      ctx.fillRect(2, 12, 28, 36);
      ctx.fillRect(4, 6, 24, 8);
      ctx.fillRect(8, 2, 16, 6);
      ctx.fillStyle = '#06060a';
      ctx.fillRect(6, 16, 20, 32);
      ctx.fillRect(8, 10, 16, 8);
      ctx.fillRect(11, 6, 10, 6);
      ctx.fillStyle = p.accent;
      ctx.fillRect(6, 15, 20, 1);
      scene.textures.addCanvas(`t_${name}_doorN`, c);
    }
    // foreground hatch (south exit), 32x24 floor frame
    {
      const [c, ctx] = canvasOf(32, 24);
      ctx.fillStyle = shade(p.top, -20);
      ctx.fillRect(0, 0, 32, 24);
      ctx.fillStyle = '#08080c';
      ctx.fillRect(3, 3, 26, 18);
      ctx.fillStyle = shade(p.accent, -40);
      for (let y = 5; y < 20; y += 4) ctx.fillRect(4, y, 24, 1);
      ctx.fillStyle = p.accent;
      ctx.fillRect(14, 10, 4, 3);
      scene.textures.addCanvas(`t_${name}_hatch`, c);
    }
    // trapdoor (down exit), 32x10
    {
      const [c, ctx] = canvasOf(32, 10);
      ctx.fillStyle = shade(p.fillB, -30);
      ctx.fillRect(0, 0, 32, 10);
      ctx.fillStyle = shade(p.accent, -50);
      for (let x = 2; x < 30; x += 5) ctx.fillRect(x, 1, 2, 8);
      ctx.fillStyle = p.accent;
      ctx.fillRect(14, 4, 4, 2);
      scene.textures.addCanvas(`t_${name}_trap`, c);
    }
    // water strip: 4 frames
    if (true) {
      const liq = p.liquid || '#2a5a8a';
      const [c, ctx] = canvasOf(T * 4, T);
      for (let f = 0; f < 4; f++) {
        const ox = f * T;
        ctx.fillStyle = liq;
        ctx.fillRect(ox, 0, T, T);
        ctx.fillStyle = shade(liq, 30);
        for (let x = 0; x < T; x += 4) {
          const yy = (x / 4 + f) % 2;
          ctx.fillRect(ox + x, yy, 3, 1);
        }
        ctx.fillStyle = shade(liq, -16);
        ctx.fillRect(ox, 3, T, T - 3);
        ctx.fillStyle = shade(liq, 10);
        for (let i = 0; i < 3; i++) ctx.fillRect(ox + ((f * 5 + i * 6) % 14), 6 + i * 3, 2, 1);
      }
      const tex = scene.textures.addCanvas(`t_${name}_water`, c);
      for (let f = 0; f < 4; f++) tex.add(String(f), 0, f * T, 0, T, T);
    }
    // closed door (for doored exits), 24x40
    {
      const [c, ctx] = canvasOf(24, 40);
      ctx.fillStyle = shade(p.accent, -70);
      ctx.fillRect(0, 0, 24, 40);
      ctx.fillStyle = shade(p.accent, -50);
      ctx.fillRect(2, 2, 20, 36);
      ctx.fillStyle = shade(p.accent, -80);
      ctx.fillRect(11, 2, 2, 36);
      ctx.fillStyle = p.accent;
      ctx.fillRect(16, 19, 3, 3);
      scene.textures.addCanvas(`t_${name}_door`, c);
    }
    // props
    p.props.forEach((propName, i) => {
      const key = `t_${name}_prop${i}`;
      if (scene.textures.exists(key)) return;
      scene.textures.addCanvas(key, drawProp(propName, p, mulberry32(hashStr(name + propName))));
    });
  }

  function drawProp(kind, p, rng) {
    const draw = {
      table: (ctx) => {
        ctx.fillStyle = shade(p.accent, -50); ctx.fillRect(2, 12, 28, 3);
        ctx.fillRect(4, 15, 3, 9); ctx.fillRect(25, 15, 3, 9);
      },
      candle: (ctx) => {
        ctx.fillStyle = '#d8d0b8'; ctx.fillRect(14, 14, 4, 8);
        ctx.fillStyle = '#f0c050'; ctx.fillRect(15, 10, 2, 4);
        ctx.fillStyle = '#fff0a0'; ctx.fillRect(15, 9, 2, 2);
      },
      shelf: (ctx) => {
        ctx.fillStyle = shade(p.accent, -55); ctx.fillRect(4, 4, 24, 2); ctx.fillRect(4, 14, 24, 2);
        const cols = ['#a05a5a', '#5a7aa0', '#6aa05a', '#a0905a'];
        for (let i = 0; i < 5; i++) { ctx.fillStyle = cols[i % 4]; ctx.fillRect(6 + i * 4, 6 + (i % 2), 3, 8 - (i % 2)); }
      },
      lamppost: (ctx) => {
        ctx.fillStyle = '#3a3e48'; ctx.fillRect(14, 4, 3, 20);
        ctx.fillStyle = '#23252c'; ctx.fillRect(11, 22, 9, 2);
        ctx.fillStyle = '#ffdd88'; ctx.fillRect(12, 0, 7, 5);
      },
      crate: (ctx) => {
        ctx.fillStyle = '#8a6a40'; ctx.fillRect(6, 8, 18, 16);
        ctx.fillStyle = '#6a4e2c'; ctx.fillRect(6, 8, 18, 2); ctx.fillRect(6, 15, 18, 2);
        ctx.fillRect(6, 8, 2, 16); ctx.fillRect(22, 8, 2, 16);
      },
      barrel: (ctx) => {
        ctx.fillStyle = '#7a5a36'; ctx.fillRect(8, 8, 14, 16);
        ctx.fillStyle = '#5c4226'; ctx.fillRect(8, 11, 14, 2); ctx.fillRect(8, 19, 14, 2);
      },
      torch: (ctx) => {
        ctx.fillStyle = '#5c4226'; ctx.fillRect(14, 10, 3, 13);
        ctx.fillStyle = '#f08030'; ctx.fillRect(12, 4, 7, 7);
        ctx.fillStyle = '#ffd060'; ctx.fillRect(14, 5, 3, 4);
      },
      bones: (ctx) => {
        ctx.fillStyle = '#cfc8b8';
        ctx.fillRect(6, 20, 8, 2); ctx.fillRect(16, 22, 9, 2); ctx.fillRect(12, 16, 2, 6);
        ctx.fillRect(20, 14, 5, 5);
        ctx.fillStyle = '#222'; ctx.fillRect(21, 16, 1, 1); ctx.fillRect(23, 16, 1, 1);
      },
      chains: (ctx) => {
        ctx.fillStyle = '#6a707c';
        for (let y = 0; y < 22; y += 4) { ctx.fillRect(10, y, 2, 3); ctx.fillRect(20, y + 2, 2, 3); }
      },
      stalagmite: (ctx) => {
        ctx.fillStyle = shade(p.fillA, 16);
        ctx.fillRect(13, 8, 6, 16); ctx.fillRect(11, 16, 10, 8); ctx.fillRect(14, 4, 3, 4);
      },
      rocks: (ctx) => {
        ctx.fillStyle = shade(p.fillA, 12); ctx.fillRect(6, 16, 10, 8); ctx.fillRect(15, 19, 11, 5);
        ctx.fillStyle = shade(p.fillA, 28); ctx.fillRect(7, 16, 4, 2); ctx.fillRect(17, 19, 4, 2);
      },
      mushroom: (ctx) => {
        ctx.fillStyle = '#d8d0c0'; ctx.fillRect(14, 16, 4, 8);
        ctx.fillStyle = '#b05a8a'; ctx.fillRect(10, 12, 12, 5);
        ctx.fillStyle = '#e0a8c8'; ctx.fillRect(12, 13, 2, 2); ctx.fillRect(18, 14, 2, 2);
      },
      tree: (ctx) => {
        ctx.fillStyle = '#5c4226'; ctx.fillRect(14, 14, 4, 10);
        ctx.fillStyle = '#2d6a38'; ctx.fillRect(6, 2, 20, 14);
        ctx.fillStyle = '#3f8a4a'; ctx.fillRect(8, 4, 7, 5); ctx.fillRect(18, 8, 6, 4);
      },
      deadtree: (ctx) => {
        ctx.fillStyle = '#4a4036'; ctx.fillRect(14, 8, 4, 16);
        ctx.fillRect(8, 6, 8, 2); ctx.fillRect(18, 10, 8, 2); ctx.fillRect(10, 2, 2, 6);
      },
      bush: (ctx) => {
        ctx.fillStyle = '#2d6a38'; ctx.fillRect(8, 14, 16, 10);
        ctx.fillStyle = '#3f8a4a'; ctx.fillRect(10, 15, 5, 4); ctx.fillRect(18, 17, 4, 3);
      },
      flowers: (ctx) => {
        ctx.fillStyle = '#3f8a4a'; ctx.fillRect(8, 18, 1, 6); ctx.fillRect(15, 16, 1, 8); ctx.fillRect(22, 19, 1, 5);
        ctx.fillStyle = '#e06c8a'; ctx.fillRect(7, 16, 3, 3);
        ctx.fillStyle = '#e8c168'; ctx.fillRect(14, 13, 3, 3);
        ctx.fillStyle = '#8a9ae0'; ctx.fillRect(21, 17, 3, 3);
      },
      fence: (ctx) => {
        ctx.fillStyle = '#6a5638';
        ctx.fillRect(6, 12, 2, 12); ctx.fillRect(15, 12, 2, 12); ctx.fillRect(24, 12, 2, 12);
        ctx.fillRect(4, 14, 24, 2); ctx.fillRect(4, 19, 24, 2);
      },
      cactus: (ctx) => {
        ctx.fillStyle = '#4a8a4a'; ctx.fillRect(14, 6, 5, 18);
        ctx.fillRect(8, 10, 6, 3); ctx.fillRect(8, 6, 3, 7); ctx.fillRect(19, 13, 6, 3); ctx.fillRect(22, 9, 3, 7);
      },
      snowdrift: (ctx) => {
        ctx.fillStyle = '#e8eef8'; ctx.fillRect(4, 19, 24, 5); ctx.fillRect(8, 16, 14, 3);
      },
      reeds: (ctx) => {
        ctx.fillStyle = '#5a8a4a';
        for (let i = 0; i < 5; i++) ctx.fillRect(7 + i * 4, 8 + (i % 3) * 3, 2, 16 - (i % 3) * 3);
        ctx.fillStyle = '#7a6a42'; ctx.fillRect(7, 6, 2, 4); ctx.fillRect(19, 4, 2, 5);
      },
      shells: (ctx) => {
        ctx.fillStyle = '#e0d0b8'; ctx.fillRect(8, 20, 5, 4); ctx.fillRect(18, 21, 6, 3);
        ctx.fillStyle = '#c0a890'; ctx.fillRect(9, 20, 1, 4); ctx.fillRect(20, 21, 1, 3);
      },
      coral: (ctx) => {
        ctx.fillStyle = '#d6608a'; ctx.fillRect(8, 12, 3, 12); ctx.fillRect(6, 8, 3, 6); ctx.fillRect(12, 10, 2, 6);
        ctx.fillStyle = '#e09a50'; ctx.fillRect(18, 14, 3, 10); ctx.fillRect(21, 10, 3, 8);
      },
      cloudpuff: (ctx) => {
        ctx.fillStyle = 'rgba(240,245,255,0.85)'; ctx.fillRect(4, 14, 24, 8); ctx.fillRect(8, 10, 14, 5);
      },
    };
    const [c, ctx] = canvasOf(32, 24);
    (draw[kind] || draw.rocks)(ctx, rng);
    return c;
  }

  // ------------------------------------------------------------------
  // Actors: 24x32 frames. One humanoid template, dressed per class/archetype.
  // Frames: idle0 idle1 walk0 walk1 walk2 walk3 jump climb0 climb1
  //         attack0 attack1 cast0 cast1 hurt death   (15 frames)
  // ------------------------------------------------------------------
  const FRAMES = ['idle0', 'idle1', 'walk0', 'walk1', 'walk2', 'walk3', 'jump',
    'climb0', 'climb1', 'attack0', 'attack1', 'cast0', 'cast1', 'hurt', 'death'];
  const FW = 24, FH = 32;

  function drawHumanoid(ctx, ox, frame, pal) {
    // pal: { skin, outfit, outfit2, hair, trim, weapon }
    const cx = ox + 12; // center
    const legSpread = { walk0: 3, walk1: 1, walk2: 3, walk3: 1, jump: 2 }[frame] ?? 1;
    const bob = (frame === 'idle1' || frame === 'walk1' || frame === 'walk3') ? 1 : 0;
    const isClimb = frame.startsWith('climb');
    const isAttack = frame.startsWith('attack');
    const isCast = frame.startsWith('cast');
    const isHurt = frame === 'hurt';
    const isDeath = frame === 'death';

    if (isDeath) {
      // lying down
      ctx.fillStyle = pal.outfit; ctx.fillRect(ox + 3, 26, 14, 5);
      ctx.fillStyle = pal.skin; ctx.fillRect(ox + 17, 25, 5, 5);
      ctx.fillStyle = pal.hair; ctx.fillRect(ox + 19, 24, 4, 2);
      return;
    }

    const headY = 6 + bob, bodyY = 13 + bob, legY = 22 + bob;
    // legs
    ctx.fillStyle = pal.outfit2;
    ctx.fillRect(cx - 1 - legSpread, legY, 3, 9 - bob);
    ctx.fillRect(cx - 1 + legSpread, legY, 3, 9 - bob);
    // body
    ctx.fillStyle = pal.outfit;
    ctx.fillRect(cx - 4, bodyY, 9, 9);
    ctx.fillStyle = pal.trim;
    ctx.fillRect(cx - 4, bodyY + 7, 9, 2);
    // head
    ctx.fillStyle = pal.skin;
    ctx.fillRect(cx - 3, headY, 7, 7);
    ctx.fillStyle = pal.hair;
    ctx.fillRect(cx - 3, headY - 1, 7, 3);
    // eye (facing right)
    ctx.fillStyle = '#101018';
    ctx.fillRect(cx + 2, headY + 3, 1, 1);
    if (isHurt) { ctx.fillStyle = '#e04040'; ctx.fillRect(cx - 4, bodyY, 9, 2); }

    // arms
    ctx.fillStyle = pal.skin;
    if (isClimb) {
      const up = frame === 'climb0' ? 0 : 3;
      ctx.fillRect(cx - 6, bodyY - 3 + up, 2, 7);
      ctx.fillRect(cx + 5, bodyY - up, 2, 7);
    } else if (isAttack) {
      const reach = frame === 'attack0' ? 4 : 8;
      ctx.fillRect(cx + 4, bodyY + 1, reach, 2);
      // weapon swing
      ctx.fillStyle = pal.weapon;
      if (frame === 'attack0') ctx.fillRect(cx + 7, bodyY - 6, 2, 8);
      else ctx.fillRect(cx + 9, bodyY, 9, 2);
    } else if (isCast) {
      ctx.fillRect(cx + 4, bodyY - 2, 2, 5);
      ctx.fillStyle = frame === 'cast0' ? '#9ad6ff' : '#ffe080';
      ctx.fillRect(cx + 5, bodyY - 6, 4, 4);
    } else {
      ctx.fillRect(cx - 6, bodyY + 1, 2, 6);
      ctx.fillRect(cx + 5, bodyY + 1, 2, 6);
      // idle weapon at side
      ctx.fillStyle = pal.weapon;
      ctx.fillRect(cx + 6, bodyY - 3, 2, 7);
    }
  }

  function accessory(ctx, ox, frame, kind, pal) {
    if (frame === 'death') return;
    const bob = (frame === 'idle1' || frame === 'walk1' || frame === 'walk3') ? 1 : 0;
    const cx = ox + 12, headY = 6 + bob;
    switch (kind) {
      case 'helm':
        ctx.fillStyle = '#9aa2b0'; ctx.fillRect(cx - 3, headY - 2, 7, 3); break;
      case 'wizardhat':
        ctx.fillStyle = pal.trim; ctx.fillRect(cx - 5, headY - 1, 11, 2); ctx.fillRect(cx - 2, headY - 5, 5, 4); break;
      case 'hood':
        ctx.fillStyle = shade(pal.outfit, -20); ctx.fillRect(cx - 4, headY - 2, 9, 4); break;
      case 'circlet':
        ctx.fillStyle = '#e8c168'; ctx.fillRect(cx - 3, headY, 7, 1); break;
      case 'crown':
        ctx.fillStyle = '#ffd44a'; ctx.fillRect(cx - 3, headY - 3, 7, 2); ctx.fillRect(cx - 3, headY - 5, 1, 2); ctx.fillRect(cx, headY - 5, 1, 2); ctx.fillRect(cx + 3, headY - 5, 1, 2); break;
      case 'apron':
        ctx.fillStyle = '#e8e0d0'; ctx.fillRect(cx - 3, 15 + bob, 7, 6); break;
      case 'skullstaff':
        if (!frame.startsWith('attack')) { ctx.fillStyle = '#4a3a5c'; ctx.fillRect(cx + 8, headY - 2, 2, 18); ctx.fillStyle = '#e8e8d8'; ctx.fillRect(cx + 7, headY - 5, 4, 4); }
        break;
      case 'lute':
        ctx.fillStyle = '#a8742c'; ctx.fillRect(cx - 9, 14 + bob, 5, 7); ctx.fillRect(cx - 5, 12 + bob, 4, 2); break;
      case 'bow':
        ctx.fillStyle = '#7a5a30'; ctx.fillRect(cx - 9, headY + 2, 2, 14); break;
      case 'shield':
        ctx.fillStyle = '#8a929e'; ctx.fillRect(cx - 9, 14 + bob, 4, 7); ctx.fillStyle = '#e8c168'; ctx.fillRect(cx - 8, 16 + bob, 2, 2); break;
    }
  }

  const CLASS_LOOKS = {
    warrior:     { pal: { skin: '#d8a878', outfit: '#8a3a32', outfit2: '#5c2a24', hair: '#6a4a2a', trim: '#b8b8c0', weapon: '#c8ccd8' }, acc: ['helm'] },
    mage:        { pal: { skin: '#d8a878', outfit: '#3a4a9a', outfit2: '#2a3470', hair: '#d8d0c0', trim: '#7a8ae0', weapon: '#8a6a3a' }, acc: ['wizardhat'] },
    cleric:      { pal: { skin: '#d8a878', outfit: '#d8d2bc', outfit2: '#a8a28c', hair: '#8a6a4a', trim: '#e8c168', weapon: '#9aa2b0' }, acc: ['circlet'] },
    thief:       { pal: { skin: '#c89868', outfit: '#3a3a44', outfit2: '#26262e', hair: '#2a2a32', trim: '#5c5c6a', weapon: '#aab0bc' }, acc: ['hood'] },
    ranger:      { pal: { skin: '#c89868', outfit: '#3a6a3a', outfit2: '#2a4a2a', hair: '#7a5a30', trim: '#6a4a2a', weapon: '#7a5a30' }, acc: ['bow'] },
    paladin:     { pal: { skin: '#d8a878', outfit: '#c0c4d0', outfit2: '#8a8e9a', hair: '#e8d8a8', trim: '#e8c168', weapon: '#d8dce8' }, acc: ['helm', 'shield'] },
    necromancer: { pal: { skin: '#b8a8a0', outfit: '#2a1a3a', outfit2: '#1c1028', hair: '#48304a', trim: '#7a4a9a', weapon: '#4a3a5c' }, acc: ['skullstaff'] },
    bard:        { pal: { skin: '#d8a878', outfit: '#8a4a8a', outfit2: '#5c305c', hair: '#a8542c', trim: '#e8c168', weapon: '#a8742c' }, acc: ['lute'] },
  };

  // quadruped / blob / flyer mob bodies
  function drawQuadruped(ctx, ox, frame, pal, big) {
    if (frame === 'death') {
      ctx.fillStyle = pal.outfit; ctx.fillRect(ox + 2, 27, 18, 4);
      return;
    }
    const bob = (frame === 'idle1' || frame === 'walk1' || frame === 'walk3') ? 1 : 0;
    const stride = frame.startsWith('walk') ? (frame === 'walk0' || frame === 'walk2' ? 2 : 0) : 1;
    const bodyY = 16 + bob;
    ctx.fillStyle = pal.outfit;
    ctx.fillRect(ox + 2, bodyY, 16, 8); // body
    ctx.fillStyle = pal.outfit2;
    ctx.fillRect(ox + 2 + stride, bodyY + 8, 3, 7 - bob);
    ctx.fillRect(ox + 14 - stride, bodyY + 8, 3, 7 - bob);
    // head
    ctx.fillStyle = pal.outfit;
    ctx.fillRect(ox + 15, bodyY - 6, 7, 8);
    ctx.fillStyle = '#101018';
    ctx.fillRect(ox + 20, bodyY - 4, 1, 1);
    // ears / horns
    ctx.fillStyle = pal.trim;
    ctx.fillRect(ox + 16, bodyY - 8, 2, 3);
    if (big) { ctx.fillRect(ox + 20, bodyY - 8, 2, 3); ctx.fillStyle = pal.trim; ctx.fillRect(ox, bodyY + 1, 3, 2); } // tail
    if (frame.startsWith('attack')) { ctx.fillStyle = '#fff'; ctx.fillRect(ox + 21, bodyY - 2, 2, 2); }
    if (frame === 'hurt') { ctx.fillStyle = '#e04040'; ctx.fillRect(ox + 2, bodyY, 16, 2); }
  }
  function drawBlob(ctx, ox, frame, pal) {
    if (frame === 'death') { ctx.fillStyle = pal.outfit; ctx.fillRect(ox + 4, 29, 16, 2); return; }
    const squish = (frame === 'idle1' || frame === 'walk1' || frame === 'walk3') ? 2 : 0;
    ctx.fillStyle = pal.outfit;
    ctx.fillRect(ox + 4, 16 + squish, 16, 15 - squish);
    ctx.fillRect(ox + 6, 13 + squish, 12, 4);
    ctx.fillStyle = shade(pal.outfit, 30);
    ctx.fillRect(ox + 6, 15 + squish, 4, 3);
    ctx.fillStyle = '#101018';
    ctx.fillRect(ox + 9, 19 + squish, 2, 2); ctx.fillRect(ox + 14, 19 + squish, 2, 2);
    if (frame === 'hurt') { ctx.fillStyle = '#e04040'; ctx.fillRect(ox + 4, 16 + squish, 16, 2); }
  }
  function drawFlyer(ctx, ox, frame, pal) {
    if (frame === 'death') { ctx.fillStyle = pal.outfit; ctx.fillRect(ox + 6, 28, 12, 3); return; }
    const flap = (frame === 'idle1' || frame === 'walk1' || frame === 'walk3') ? -4 : 2;
    const y = 14;
    ctx.fillStyle = pal.outfit;
    ctx.fillRect(ox + 8, y, 8, 10);     // body
    ctx.fillStyle = pal.outfit2;
    ctx.fillRect(ox + 1, y + flap, 7, 4);   // left wing
    ctx.fillRect(ox + 16, y + flap, 7, 4);  // right wing
    ctx.fillStyle = pal.outfit;
    ctx.fillRect(ox + 10, y - 5, 6, 6);  // head
    ctx.fillStyle = '#101018';
    ctx.fillRect(ox + 14, y - 3, 1, 1);
    ctx.fillStyle = pal.trim;
    ctx.fillRect(ox + 16, y - 2, 3, 2);  // beak
    if (frame === 'hurt') { ctx.fillStyle = '#e04040'; ctx.fillRect(ox + 8, y, 8, 2); }
  }

  // archetype classification, extended from client2d MOB_TYPE_RULES
  const MOB_ARCHETYPES = [
    { terms: ['dragon', 'wyvern', 'drake'], key: 'dragon', body: 'quad', pal: { outfit: '#a83a2a', outfit2: '#7a2a1e', trim: '#e8c168' }, big: true },
    { terms: ['goblin', 'gnoll', 'orc', 'kobold', 'troll', 'ogre'], key: 'goblinoid', body: 'human', pal: { skin: '#6a9a4a', outfit: '#5c4a32', outfit2: '#42362a', hair: '#3a4a2a', trim: '#7a6a4a', weapon: '#8a8e9a' } },
    { terms: ['skeleton', 'zombie', 'ghoul', 'lich', 'vampire', 'wight', 'wraith', 'undead', 'corpse'], key: 'undead', body: 'human', pal: { skin: '#cfc8b8', outfit: '#3a3a40', outfit2: '#2a2a2e', hair: '#cfc8b8', trim: '#5a5a64', weapon: '#9aa2b0' } },
    { terms: ['ghost', 'spirit', 'specter', 'phantom', 'shade'], key: 'ghost', body: 'flyer', pal: { outfit: '#b8c8e0', outfit2: '#8aa0c0', trim: '#e8f0ff' }, alpha: 0.6 },
    { terms: ['demon', 'devil', 'imp', 'fiend'], key: 'demon', body: 'human', pal: { skin: '#b03a3a', outfit: '#3a1a1a', outfit2: '#2a1010', hair: '#1a0a0a', trim: '#e85c2a', weapon: '#2a2a32' } },
    { terms: ['wolf', 'bear', 'lion', 'cat', 'dog', 'boar', 'rat', 'horse', 'deer', 'cow', 'pig', 'fox', 'beast'], key: 'beast', body: 'quad', pal: { outfit: '#7a5a3a', outfit2: '#5c4228', trim: '#4a3620' } },
    { terms: ['spider', 'scorpion', 'beetle', 'ant', 'insect', 'centipede', 'roach'], key: 'insect', body: 'quad', pal: { outfit: '#3a3a2a', outfit2: '#26261c', trim: '#a8a04a' } },
    { terms: ['slime', 'ooze', 'pudding', 'jelly', 'blob'], key: 'slime', body: 'blob', pal: { outfit: '#4aa86a', outfit2: '#338050', trim: '#7ad68a' } },
    { terms: ['elemental', 'golem', 'gargoyle'], key: 'elemental', body: 'human', pal: { skin: '#8a8d96', outfit: '#6a6e7a', outfit2: '#52565e', hair: '#8a8d96', trim: '#cdd2dc', weapon: '#5c606a' } },
    { terms: ['fish', 'shark', 'eel', 'octopus', 'crab', 'kraken', 'merman', 'siren'], key: 'aquatic', body: 'blob', pal: { outfit: '#3a7a9a', outfit2: '#2a5a74', trim: '#6cc0e0' } },
    { terms: ['bird', 'hawk', 'eagle', 'raven', 'crow', 'bat', 'owl', 'vulture'], key: 'bird', body: 'flyer', pal: { outfit: '#4a4250', outfit2: '#36303c', trim: '#e8c168' } },
    { terms: ['guard', 'soldier', 'knight', 'captain', 'warrior', 'fighter'], key: 'guard', body: 'human', pal: { skin: '#d8a878', outfit: '#5c6a8a', outfit2: '#424d66', hair: '#5a4a32', trim: '#9aa2b0', weapon: '#c8ccd8' }, acc: ['helm'] },
    { terms: ['mage', 'wizard', 'sorcerer', 'witch', 'shaman', 'priest', 'cleric', 'acolyte'], key: 'caster', body: 'human', pal: { skin: '#d8a878', outfit: '#4a3a7a', outfit2: '#362a5a', hair: '#8a8a96', trim: '#9a8ae0', weapon: '#8a6a3a' }, acc: ['wizardhat'] },
  ];
  const DEFAULT_ARCHETYPE = { key: 'citizen', body: 'human', pal: { skin: '#d8a878', outfit: '#6a5a48', outfit2: '#4e4234', hair: '#5a4a32', trim: '#8a7a62', weapon: '#7a5a30' } };

  MH.mobArchetype = function mobArchetype(name) {
    const lower = String(name || '').toLowerCase();
    for (const rule of MOB_ARCHETYPES) {
      if (rule.terms.some(t => lower.includes(t))) return rule;
    }
    return DEFAULT_ARCHETYPE;
  };

  function genActorSheet(scene, key, body, pal, accs, alpha) {
    if (scene.textures.exists(key)) return;
    const [c, ctx] = canvasOf(FW * FRAMES.length, FH);
    if (alpha) ctx.globalAlpha = alpha;
    FRAMES.forEach((frame, i) => {
      const ox = i * FW;
      if (body === 'quad') drawQuadruped(ctx, ox, frame, pal, !!pal.big);
      else if (body === 'blob') drawBlob(ctx, ox, frame, pal);
      else if (body === 'flyer') drawFlyer(ctx, ox, frame, pal);
      else {
        drawHumanoid(ctx, ox, frame, pal);
        (accs || []).forEach(a => accessory(ctx, ox, frame, a, pal));
      }
    });
    const tex = scene.textures.addCanvas(key, c);
    FRAMES.forEach((frame, i) => tex.add(frame, 0, i * FW, 0, FW, FH));
  }

  // items: 16x16 glyphs keyed by item_type
  function genItemIcons(scene) {
    const draws = {
      weapon: ctx => { ctx.fillStyle = '#c8ccd8'; ctx.fillRect(7, 2, 2, 9); ctx.fillStyle = '#e8c168'; ctx.fillRect(5, 10, 6, 2); ctx.fillStyle = '#8a6a3a'; ctx.fillRect(7, 12, 2, 3); },
      armor: ctx => { ctx.fillStyle = '#8a929e'; ctx.fillRect(4, 3, 8, 9); ctx.fillRect(2, 4, 2, 4); ctx.fillRect(12, 4, 2, 4); ctx.fillStyle = '#aab2be'; ctx.fillRect(6, 4, 4, 3); },
      potion: ctx => { ctx.fillStyle = '#d0d8e8'; ctx.fillRect(6, 2, 4, 3); ctx.fillStyle = '#c04a8a'; ctx.fillRect(4, 5, 8, 8); ctx.fillStyle = '#e07ab0'; ctx.fillRect(5, 6, 3, 3); },
      scroll: ctx => { ctx.fillStyle = '#e0d8c0'; ctx.fillRect(3, 3, 10, 10); ctx.fillStyle = '#8a7a5a'; ctx.fillRect(5, 5, 6, 1); ctx.fillRect(5, 8, 6, 1); ctx.fillRect(5, 11, 4, 1); },
      food: ctx => { ctx.fillStyle = '#c08a4a'; ctx.fillRect(4, 5, 8, 7); ctx.fillStyle = '#e0b070'; ctx.fillRect(5, 6, 6, 2); },
      drink: ctx => { ctx.fillStyle = '#7a5a36'; ctx.fillRect(5, 4, 6, 10); ctx.fillRect(4, 6, 8, 5); ctx.fillStyle = '#5c4226'; ctx.fillRect(5, 8, 6, 1); },
      key: ctx => { ctx.fillStyle = '#e8c168'; ctx.fillRect(4, 4, 4, 4); ctx.fillRect(7, 6, 7, 2); ctx.fillRect(11, 8, 1, 2); ctx.fillRect(13, 8, 1, 2); },
      light: ctx => { ctx.fillStyle = '#ffd060'; ctx.fillRect(6, 3, 4, 5); ctx.fillStyle = '#8a6a3a'; ctx.fillRect(6, 8, 4, 6); },
      container: ctx => { ctx.fillStyle = '#8a6a40'; ctx.fillRect(3, 6, 10, 8); ctx.fillStyle = '#6a4e2c'; ctx.fillRect(3, 6, 10, 2); ctx.fillStyle = '#e8c168'; ctx.fillRect(7, 9, 2, 2); },
      treasure: ctx => { ctx.fillStyle = '#e8c168'; ctx.fillRect(5, 7, 6, 6); ctx.fillRect(7, 5, 2, 2); ctx.fillStyle = '#fff0b0'; ctx.fillRect(6, 8, 2, 2); },
      wand: ctx => { ctx.fillStyle = '#8a6a3a'; ctx.fillRect(7, 5, 2, 9); ctx.fillStyle = '#9ad6ff'; ctx.fillRect(6, 2, 4, 4); },
      other: ctx => { ctx.fillStyle = '#9aa0b4'; ctx.fillRect(5, 5, 6, 6); ctx.fillStyle = '#c8ccd8'; ctx.fillRect(6, 6, 2, 2); },
    };
    for (const [kind, fn] of Object.entries(draws)) {
      const [c, ctx] = canvasOf(16, 16);
      fn(ctx);
      scene.textures.addCanvas(`item_${kind}`, c);
    }
  }

  function genParticles(scene) {
    {
      const [c, ctx] = canvasOf(4, 4);
      ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, 4, 4);
      scene.textures.addCanvas('px_white', c);
    }
    {
      const [c, ctx] = canvasOf(6, 6);
      ctx.fillStyle = '#ffe080'; ctx.fillRect(1, 1, 4, 4); ctx.fillRect(0, 2, 6, 2); ctx.fillRect(2, 0, 2, 6);
      scene.textures.addCanvas('px_star', c);
    }
    {
      const [c, ctx] = canvasOf(8, 8);
      ctx.fillStyle = 'rgba(220,220,230,0.8)'; ctx.fillRect(1, 1, 6, 6);
      scene.textures.addCanvas('px_poof', c);
    }
    {
      const [c, ctx] = canvasOf(2, 6);
      ctx.fillStyle = 'rgba(160,190,230,0.7)'; ctx.fillRect(0, 0, 2, 6);
      scene.textures.addCanvas('px_rain', c);
    }
    {
      const [c, ctx] = canvasOf(3, 3);
      ctx.fillStyle = 'rgba(150,200,255,0.6)'; ctx.fillRect(0, 0, 3, 3);
      scene.textures.addCanvas('px_bubble', c);
    }
  }

  // ------------------------------------------------------------------
  MH.sprites = {
    FRAMES, FW, FH, T,

    generateAll(scene) {
      for (const [name, p] of Object.entries(THEMES)) genThemeTiles(scene, name, p);
      for (const [cls, look] of Object.entries(CLASS_LOOKS)) {
        genActorSheet(scene, `player_${cls}`, 'human', look.pal, look.acc);
      }
      for (const rule of MOB_ARCHETYPES.concat([DEFAULT_ARCHETYPE])) {
        const pal = Object.assign({ skin: '#d8a878', hair: '#5a4a32', weapon: '#8a8e9a', big: rule.big }, rule.pal);
        genActorSheet(scene, `mob_${rule.key}`, rule.body, pal, rule.acc, rule.alpha);
      }
      genItemIcons(scene);
      genParticles(scene);
      this.registerAnims(scene);
    },

    registerAnims(scene) {
      const actorKeys = Object.keys(CLASS_LOOKS).map(c => `player_${c}`)
        .concat(MOB_ARCHETYPES.concat([DEFAULT_ARCHETYPE]).map(r => `mob_${r.key}`));
      for (const key of actorKeys) {
        const mk = (anim, frames, rate, repeat = -1) => {
          if (scene.anims.exists(`${key}_${anim}`)) return;
          scene.anims.create({
            key: `${key}_${anim}`,
            frames: frames.map(f => ({ key, frame: f })),
            frameRate: rate, repeat,
          });
        };
        mk('idle', ['idle0', 'idle1'], 2);
        mk('walk', ['walk0', 'walk1', 'walk2', 'walk3'], 8);
        mk('climb', ['climb0', 'climb1'], 5);
        mk('attack', ['attack0', 'attack1'], 10, 0);
        mk('cast', ['cast0', 'cast1'], 6, 0);
        mk('hurt', ['hurt'], 1, 0);
        mk('death', ['death'], 1, 0);
      }
      for (const name of Object.keys(THEMES)) {
        if (!scene.anims.exists(`water_${name}`)) {
          scene.anims.create({
            key: `water_${name}`,
            frames: [0, 1, 2, 3].map(f => ({ key: `t_${name}_water`, frame: String(f) })),
            frameRate: 4, repeat: -1,
          });
        }
      }
    },

    playerKey(charClass) {
      const cls = String(charClass || '').toLowerCase();
      return CLASS_LOOKS[cls] ? `player_${cls}` : 'player_warrior';
    },
    mobKey(name) {
      return `mob_${MH.mobArchetype(name).key}`;
    },
    itemKey(type) {
      const t = String(type || 'other').toLowerCase();
      const known = ['weapon', 'armor', 'potion', 'scroll', 'food', 'drink', 'key', 'light', 'container', 'treasure', 'wand'];
      return `item_${known.includes(t) ? t : 'other'}`;
    },
  };

  MH.mulberry32 = mulberry32;
})();
