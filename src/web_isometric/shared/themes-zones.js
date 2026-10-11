// Misthollow: hand-tuned zone themes for the top-down view.
// Every zone maps to one of ~22 visual identities: floor pattern, border
// treatment, prop set, ambient particles and mood lighting. Rooms in
// unmapped zones fall back to the sector themes. All art is procedural
// smooth-canvas, drawn at boot like sprites-smooth.js.
(() => {
  const MH = window.MH = window.MH || {};

  // ---------------- theme specs ----------------
  // floor: base color; floorKind paints the pattern; border/obst share kind+colors
  // ambient: particle weather; glow: light pool tint; mood: scene tint wash
  // light: how the painter bakes illumination into the ground —
  //   enclosed: true = a dark interior (strong vignette, warm torch pools at
  //   the walls, cool daylight spilling in at the exits); false = open sky
  //   (soft vignette, sun shadows cast by the treeline / walls onto the floor)
  //   vig: vignette strength 0..1, vigCol: its color, pool: light-pool color
  //   (open-sky vignettes are deliberately strong: a clearing is brightest
  //   in the middle and sinks into canopy shade at the treeline; a square is
  //   brightest where the sun hits and shaded under the eaves)
  const LIGHT_OUT  = { enclosed: false, vig: 0.30, vigCol: '#06100a', pool: '#fff0c0', dapple: true };
  const LIGHT_SUN  = { enclosed: false, vig: 0.22, vigCol: '#2a1a08', pool: '#fff4d0', dapple: false };
  const LIGHT_IN   = { enclosed: true,  vig: 0.42, vigCol: '#0a0810', pool: '#ffc888' };
  const LIGHT_DARK = { enclosed: true,  vig: 0.78, vigCol: '#060302', pool: '#ffa850' };
  const LIGHT_COLD = { enclosed: true,  vig: 0.50, vigCol: '#0a1018', pool: '#ffd8a8' };
  const T22 = {
    // midgaard: a warm sandstone-and-cobble town; the border is painted by
    // painter.js as the rooftops of the houses that ring each street/square
    // (paintBorder + borderStyle 'roof'), not a brick wall
    midgaard:   { floor: '#a08a66', f2: '#8c7858', acc: '#f2c46a', floorKind: 'cobble', borderKind: 'wall', borderCol: '#6a5846', paintBorder: true, borderStyle: 'roof', roofCols: ['#a8583a', '#5a6a94', '#8a6a40', '#7a4e5e', '#b06a3c', '#4e6a7a'], glow: 0xffc878, mood: 0xffe4b8, moodA: 0.07, ambient: 'motes', light: LIGHT_SUN, props: ['lamppost', 'crate', 'barrel', 'stall', 'banner', 'fountain'] },
    temple:     { floor: '#a29ea8', f2: '#928e9a', acc: '#ffe9a8', floorKind: 'marble', borderKind: 'column', borderCol: '#b4b0c0', glow: 0xffe9a8, mood: 0xfff6e0, moodA: 0.06, ambient: 'motes', light: LIGHT_IN, props: ['pillar', 'candles', 'urn', 'banner', 'statue'] },
    sewer:      { floor: '#3e4a36', f2: '#333e2c', acc: '#9fd6a0', floorKind: 'slimestone', borderKind: 'wall', borderCol: '#2e382a', glow: 0x9fd6a0, mood: 0x9adba0, moodA: 0.07, ambient: 'drips', light: { enclosed: true, vig: 0.55, vigCol: '#040806', pool: '#b8f0a0' }, props: ['mushrooms', 'bones', 'rubble', 'barrel'], water: '#4a6a3a' },
    forest:     { floor: '#529440', f2: '#427a34', acc: '#b8e878', floorKind: 'grass', borderKind: 'tree', borderCol: '#2a6a34', glow: 0xaaffaa, mood: 0xd8ffd0, moodA: 0.05, ambient: 'leaves', light: LIGHT_OUT, props: ['tree', 'bush', 'flowers', 'mushrooms', 'stump', 'rock'] },
    darkforest: { floor: '#34503a', f2: '#2a4230', acc: '#6cae8a', floorKind: 'grass', borderKind: 'deadtree', borderCol: '#1c2a22', glow: 0x86c89a, mood: 0x9ec8b8, moodA: 0.10, ambient: 'fireflies', light: { enclosed: false, vig: 0.36, vigCol: '#060a08', pool: '#b0e0a0', dapple: true }, props: ['deadtree', 'mushrooms', 'web', 'rock', 'bones'] },
    swamp:      { floor: '#4e5838', f2: '#424a2e', acc: '#a8c860', floorKind: 'slimestone', borderKind: 'deadtree', borderCol: '#28301e', glow: 0x9fd6a0, mood: 0xa6c890, moodA: 0.10, ambient: 'fireflies', light: { enclosed: false, vig: 0.30, vigCol: '#080c06', pool: '#c8e890', dapple: true }, props: ['deadtree', 'reeds', 'lilypad', 'mushrooms'], water: '#4a6a42' },
    mines:      { floor: '#4a3e32', f2: '#3c322a', acc: '#d09050', floorKind: 'cracked', borderKind: 'rock', borderCol: '#3a3028', glow: 0xffa868, mood: 0xc8a888, moodA: 0.08, ambient: 'embers', light: LIGHT_DARK, props: ['rock', 'beam', 'crystal', 'rubble', 'barrel'] },
    dwarvenhall:{ floor: '#6a5a4c', f2: '#5c4e42', acc: '#f0a868', floorKind: 'flagstone', borderKind: 'wall', borderCol: '#4e4238', glow: 0xffb868, mood: 0xffd2a8, moodA: 0.07, ambient: 'embers', light: LIGHT_IN, props: ['anvil', 'brazier', 'pillar', 'barrel', 'crate'] },
    desert:     { floor: '#d4b478', f2: '#c4a468', acc: '#fff0b0', floorKind: 'sand', borderKind: 'dune', borderCol: '#a08050', glow: 0xffd9a0, mood: 0xffe8c0, moodA: 0.07, ambient: 'dust', light: LIGHT_SUN, props: ['cactus', 'bones', 'rock', 'urn'] },
    sandstone:  { floor: '#b89a66', f2: '#a88c5c', acc: '#f0d898', floorKind: 'flagstone', borderKind: 'wall', borderCol: '#8a7048', glow: 0xffd9a0, mood: 0xffe4b8, moodA: 0.06, ambient: 'dust', light: LIGHT_SUN, props: ['urn', 'stall', 'banner', 'crate', 'pillar'] },
    drow:       { floor: '#3a3150', f2: '#302846', acc: '#c07cf0', floorKind: 'flagstone', borderKind: 'rock', borderCol: '#28203a', glow: 0xb06ce0, mood: 0x9a7ce0, moodA: 0.12, ambient: 'spores', light: { enclosed: true, vig: 0.6, vigCol: '#06040c', pool: '#c890ff' }, props: ['crystal', 'web', 'mushrooms', 'pillar', 'banner'] },
    castle:     { floor: '#66697a', f2: '#5a5d6c', acc: '#d8b878', floorKind: 'flagstone', borderKind: 'wall', borderCol: '#464a5c', glow: 0xffc878, mood: 0xdce4f0, moodA: 0.05, ambient: 'motes', light: LIGHT_IN, props: ['banner', 'brazier', 'pillar', 'statue', 'crate'] },
    darkcastle: { floor: '#3c3846', f2: '#322e3c', acc: '#d06868', floorKind: 'cracked', borderKind: 'wall', borderCol: '#2a2834', glow: 0xc06868, mood: 0x8a86b0, moodA: 0.12, ambient: 'ash', light: { enclosed: true, vig: 0.6, vigCol: '#08060a', pool: '#ff9060' }, props: ['banner', 'rubble', 'bones', 'brazier', 'statue'] },
    rome:       { floor: '#b0a894', f2: '#a29a88', acc: '#f0d898', floorKind: 'marble', borderKind: 'column', borderCol: '#b8ae9c', glow: 0xffe9a8, mood: 0xfff4dc, moodA: 0.06, ambient: 'motes', light: LIGHT_SUN, props: ['pillar', 'statue', 'urn', 'fountain', 'banner'] },
    elven:      { floor: '#5a8a4c', f2: '#4c7a40', acc: '#d0f0a8', floorKind: 'grass', borderKind: 'tree', borderCol: '#2e6a3a', glow: 0xcfffc0, mood: 0xe8ffe0, moodA: 0.06, ambient: 'petals', light: LIGHT_OUT, props: ['tree', 'flowers', 'lantern', 'fountain', 'bush'] },
    autumn:     { floor: '#8a6a3c', f2: '#7a5c34', acc: '#f0b060', floorKind: 'grass', borderKind: 'tree', borderCol: '#7a4a22', glow: 0xffd9a0, mood: 0xffe0b8, moodA: 0.06, ambient: 'leaves', light: LIGHT_OUT, props: ['tree', 'stump', 'rock', 'bush', 'fence'] },
    frozen:     { floor: '#c4d0dc', f2: '#b4c2d0', acc: '#f0f8ff', floorKind: 'snow', borderKind: 'pine', borderCol: '#3a5648', glow: 0xcfe2ff, mood: 0xdce8ff, moodA: 0.08, ambient: 'snow', light: { enclosed: false, vig: 0.12, vigCol: '#1a2840', pool: '#ffffff', dapple: false }, props: ['pine', 'snowdrift', 'icecrystal', 'rock', 'stump'] },
    necropolis: { floor: '#b8b4a4', f2: '#a6a294', acc: '#e8ead8', floorKind: 'bone', borderKind: 'bone', borderCol: '#7c7a6e', glow: 0xc8dcec, mood: 0xb0c4dc, moodA: 0.14, ambient: 'mist', light: LIGHT_COLD, props: ['gravestone', 'bones', 'deadtree', 'statue', 'brazier'] },
    volcanic:   { floor: '#463434', f2: '#3c2c2c', acc: '#ff9a5a', floorKind: 'cracked', borderKind: 'rock', borderCol: '#2e2426', glow: 0xff8a5a, mood: 0xd09080, moodA: 0.10, ambient: 'embers', light: { enclosed: true, vig: 0.55, vigCol: '#0a0404', pool: '#ff8a40' }, props: ['rock', 'deadtree', 'bones', 'rubble'], water: '#d85a2a' },
    sunken:     { floor: '#c8b88c', f2: '#b8a87c', acc: '#8af0e0', floorKind: 'shallows', borderKind: 'coral', borderCol: '#8a7a5c', glow: 0x66e0ff, mood: 0x8ad8e8, moodA: 0.04, ambient: 'bubbles', light: { enclosed: false, vig: 0.14, vigCol: '#062838', pool: '#c0f8ff', dapple: false }, props: ['coral', 'shell', 'reeds', 'pillar', 'rubble'], water: '#2e8ed0' },
    clockwork:  { floor: '#6e5e4c', f2: '#625444', acc: '#f0c868', floorKind: 'brass', borderKind: 'brass', borderCol: '#463c30', glow: 0xffc868, mood: 0xe8c898, moodA: 0.08, ambient: 'sparks', light: LIGHT_IN, props: ['gear', 'pipe', 'crate', 'brazier', 'barrel'] },
    voidstar:   { floor: '#2e2c4c', f2: '#262440', acc: '#a89aff', floorKind: 'runic', borderKind: 'voidpillar', borderCol: '#1e1c30', glow: 0x9a8aff, mood: 0x8a86d0, moodA: 0.12, ambient: 'stars', light: { enclosed: true, vig: 0.55, vigCol: '#04040c', pool: '#a898ff' }, props: ['runestone', 'crystal', 'pillar', 'bookpile', 'candles'] },
    arcane:     { floor: '#4a4266', f2: '#403a5a', acc: '#b898ff', floorKind: 'runic', borderKind: 'wall', borderCol: '#342e4c', glow: 0xb08aff, mood: 0xb0a0e8, moodA: 0.10, ambient: 'stars', light: { enclosed: true, vig: 0.45, vigCol: '#08060e', pool: '#c0a8ff' }, props: ['bookpile', 'candles', 'runestone', 'crystal', 'urn'] },
    chessboard: { floor: '#d8d4cc', f2: '#34323c', acc: '#e8c168', floorKind: 'checker', borderKind: 'column', borderCol: '#8a8694', glow: 0xffffff, mood: 0xe8e8f4, moodA: 0.05, ambient: 'motes', light: LIGHT_IN, props: ['pillar', 'statue'] },
    meadow:     { floor: '#6a9a44', f2: '#5c8a3c', acc: '#e0f080', floorKind: 'grass', borderKind: 'hedge', borderCol: '#3a6a2c', glow: 0xffe9a8, mood: 0xf0ffd8, moodA: 0.05, ambient: 'petals', light: LIGHT_SUN, props: ['flowers', 'bush', 'fence', 'tree', 'fountain'] },
  };

  // Sector atmospheres: a room's SECTOR can overrule its zone's look. A cave
  // inside a forest zone is still a cave (dark rock, torch pools) and a
  // swimmable room is water no matter which zone owns it. `override`:
  //   'outdoor' = only replace open-sky zone looks (grass/sand/snow/shallows)
  //   'always'  = replace any zone look
  const OUTDOOR_KINDS = ['grass', 'sand', 'snow', 'shallows'];
  // borderKind/borderCol here tell the PAINTER what mass to paint where the
  // zone's (transparent, organic) border sprites would have been
  MH.SECTOR_ATMOS = {
    cave:        { override: 'outdoor', floor: '#4a3a2c', f2: '#3a2d22', acc: '#d8a060', floorKind: 'cracked', borderKind: 'rock', borderCol: '#6a5442', light: LIGHT_DARK, mood: 0xffc890, moodA: 0.06, glow: 0xffa868 },
    underground: { override: 'outdoor', floor: '#4a3a2c', f2: '#3a2d22', acc: '#d8a060', floorKind: 'cracked', borderKind: 'rock', borderCol: '#6a5442', light: LIGHT_DARK, mood: 0xffc890, moodA: 0.06, glow: 0xffa868 },
    dungeon:     { override: 'outdoor', floor: '#56525c', f2: '#4a4650', acc: '#c0b8a8', floorKind: 'flagstone', borderKind: 'wall', borderCol: '#4e4a56', light: LIGHT_DARK },
    inside:      { override: 'outdoor', floor: '#7a6650', f2: '#6c5a46', acc: '#f0c890', floorKind: 'flagstone', borderKind: 'wall', borderCol: '#5c4c3c', light: LIGHT_IN },
    water_swim:  { override: 'always',  floor: '#c8b88c', f2: '#b8a87c', acc: '#8af0e0', floorKind: 'shallows', water: '#2e8ed0', light: { enclosed: false, vig: 0.14, vigCol: '#062838', pool: '#c0f8ff', dapple: false } },
    underwater:  { override: 'always',  floor: '#7a9a8c', f2: '#6a8a7c', acc: '#8af0e0', floorKind: 'shallows', water: '#1e5aa0', deep: true, borderKind: 'coral', borderCol: '#6a6a58', light: { enclosed: false, vig: 0.5, vigCol: '#041828', pool: '#a0e8ff', dapple: false } },
  };
  MH.OUTDOOR_FLOOR_KINDS = OUTDOOR_KINDS;
  // organic border kinds are painted into the room painting by painter.js;
  // their tile sprites are left transparent so the mass shows through
  MH.PAINTED_BORDER_KINDS = ['tree', 'pine', 'deadtree', 'hedge', 'rock', 'dune', 'coral'];
  // resolve the palette a room paints with: zone theme, then sector atmosphere
  MH.roomPalette = function (zt, sector) {
    const atm = MH.SECTOR_ATMOS[sector];
    if (!atm) return zt;
    if (!zt) return Object.assign({}, atm);
    if (atm.override === 'always' || OUTDOOR_KINDS.includes(zt.floorKind)) return Object.assign({}, zt, atm);
    return zt;
  };

  // ---------------- zone number -> theme ----------------
  const Z = {
    9: 'meadow',        // River Island Of Minos
    12: 'temple',       // God Simplex
    15: 'desert',       // The Straight Path
    25: 'arcane',       // High Tower Of Magic
    30: 'midgaard', 31: 'midgaard', 32: 'midgaard', 260: 'midgaard',
    33: 'autumn',       // Three Of Swords
    35: 'forest',       // Miden'Nir
    36: 'chessboard',   // Chessboard of Midgaard
    40: 'mines',        // Moria
    50: 'desert', 53: 'sandstone', 52: 'sandstone', 54: 'sandstone',
    51: 'drow',
    60: 'forest', 61: 'darkforest', 62: 'darkforest', 63: 'darkforest',
    64: 'arcane',       // Rand's Tower
    65: 'dwarvenhall', 100: 'mines',
    66: 'autumn', 67: 'autumn',
    68: 'sunken',       // Sunken Coast
    69: 'volcanic',     // Ashlands
    70: 'sewer', 71: 'sewer', 72: 'sewer', 73: 'sewer',
    79: 'castle',       // Redferne's Residence
    80: 'volcanic',     // Dragon's Domain
    90: 'swamp',
    110: 'elven',
    120: 'rome',
    130: 'sunken',      // Atal'narath
    140: 'necropolis',
    150: 'castle',      // King Welmar's
    160: 'voidstar',    // Plane of Chaos
    180: 'frozen', 190: 'frozen',
    186: 'meadow',      // Newbie Zone
    200: 'darkforest',  // Forest of Shadows
    210: 'mines',       // Tunnel of Sticks
    220: 'darkcastle',  // Castle Apocalypse
    235: 'darkforest',  // Goblin Warrens
    238: 'necropolis',  // Haunted Monastery
    240: 'sunken', 285: 'sunken',
    245: 'darkcastle',  // Shadowspire Citadel
    248: 'clockwork',
    250: 'desert',      // Blood Pit Arena (sand pit)
    270: 'forest',      // Whispering Woods
    280: 'volcanic',    // Ashen Expanse
    290: 'voidstar',    // Black Observatory
    295: 'necropolis',  // Crown of Bone
    300: 'darkcastle',  // Shattered Throne
  };

  MH.zoneThemeKey = zone => Z[zone] || null;
  MH.ZONE_THEMES = T22;

  // ---------------- texture generation ----------------
  const SS = 4;
  function canvasOf(w, h) {
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    const ctx = c.getContext('2d');
    ctx.imageSmoothingEnabled = true;
    return [c, ctx];
  }
  function shade(hex, amt) {
    const n = parseInt(hex.slice(1), 16);
    const cl = v => Math.max(0, Math.min(255, v + amt));
    return `#${(((cl((n >> 16) & 255)) << 16) | ((cl((n >> 8) & 255)) << 8) | cl(n & 255)).toString(16).padStart(6, '0')}`;
  }
  function rr(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  // --- floor pattern painters (variant v in 0..2 varies detail placement) ---
  function paintFloor(ctx, S, t, kind, v) {
    const rng = MH.mulberry32(0xf100 + v * 97);
    ctx.fillStyle = v === 1 ? shade(t.floor, -5) : t.floor;
    ctx.fillRect(0, 0, S, S);
    const det = shade(t.f2, -8), lit = shade(t.floor, 14);
    if (kind === 'cobble' || kind === 'flagstone') {
      const n = kind === 'cobble' ? 3 : 2;
      ctx.strokeStyle = `rgba(10,12,18,0.18)`;
      ctx.lineWidth = 1.4 * SS;
      for (let i = 0; i <= n; i++) {
        const off = (v * 7 % 11) / 11 * (S / n);
        ctx.beginPath(); ctx.moveTo(0, i * S / n + (i % 2 ? off : -off) * 0.2); ctx.lineTo(S, i * S / n); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(i * S / n + off * 0.3, 0); ctx.lineTo(i * S / n, S); ctx.stroke();
      }
      if (v === 2) { ctx.fillStyle = 'rgba(255,255,255,0.05)'; rr(ctx, S * 0.1, S * 0.1, S * 0.36, S * 0.3, S * 0.06); ctx.fill(); }
    } else if (kind === 'grass') {
      ctx.strokeStyle = det; ctx.lineWidth = 1 * SS; ctx.lineCap = 'round';
      for (let i = 0; i < 6 + v * 2; i++) {
        const x = rng() * S, y = rng() * S, h = (2 + rng() * 2.5) * SS;
        ctx.beginPath(); ctx.moveTo(x, y); ctx.quadraticCurveTo(x + 1.4 * SS, y - h * 0.6, x + (rng() - 0.3) * 3 * SS, y - h); ctx.stroke();
      }
      if (v === 2) { ctx.fillStyle = lit; ctx.beginPath(); ctx.arc(S * 0.7, S * 0.3, 1.4 * SS, 0, 7); ctx.fill(); }
    } else if (kind === 'sand') {
      ctx.strokeStyle = 'rgba(255,255,255,0.10)'; ctx.lineWidth = 1.2 * SS;
      for (let i = 0; i < 3; i++) {
        const y = (0.2 + i * 0.3 + v * 0.07) * S;
        ctx.beginPath(); ctx.moveTo(0, y); ctx.quadraticCurveTo(S * 0.5, y - 3 * SS, S, y); ctx.stroke();
      }
    } else if (kind === 'snow') {
      ctx.fillStyle = 'rgba(255,255,255,0.20)';
      for (let i = 0; i < 4 + v; i++) { ctx.beginPath(); ctx.arc(rng() * S, rng() * S, (1 + rng() * 2) * SS, 0, 7); ctx.fill(); }
      ctx.fillStyle = 'rgba(120,140,180,0.10)';
      ctx.beginPath(); ctx.arc(S * (0.3 + v * 0.2), S * 0.7, 3.5 * SS, 0, 7); ctx.fill();
    } else if (kind === 'cracked') {
      ctx.strokeStyle = 'rgba(8,8,10,0.30)'; ctx.lineWidth = 1 * SS; ctx.lineCap = 'round';
      let x = rng() * S, y = 0;
      ctx.beginPath(); ctx.moveTo(x, y);
      for (let i = 0; i < 4; i++) { x += (rng() - 0.5) * S * 0.5; y += S / 4; ctx.lineTo(x, y); }
      ctx.stroke();
      if (v) { ctx.fillStyle = det; ctx.beginPath(); ctx.arc(rng() * S, rng() * S, 1.6 * SS, 0, 7); ctx.fill(); }
    } else if (kind === 'bone') {
      ctx.fillStyle = 'rgba(220,220,200,0.12)';
      for (let i = 0; i < 3 + v; i++) { rr(ctx, rng() * S * 0.8, rng() * S * 0.8, (3 + rng() * 4) * SS, 2 * SS, SS); ctx.fill(); }
      ctx.strokeStyle = 'rgba(10,12,14,0.16)'; ctx.lineWidth = 1.2 * SS;
      ctx.strokeRect(0.5, 0.5, S - 1, S - 1);
    } else if (kind === 'marble') {
      ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.lineWidth = 1 * SS;
      ctx.beginPath(); ctx.moveTo(0, S * (0.2 + v * 0.25)); ctx.bezierCurveTo(S * 0.3, S * 0.4, S * 0.6, S * 0.1, S, S * (0.3 + v * 0.2)); ctx.stroke();
      ctx.strokeStyle = 'rgba(10,12,18,0.14)'; ctx.lineWidth = 1.4 * SS;
      ctx.strokeRect(0.5, 0.5, S - 1, S - 1);
    } else if (kind === 'brass') {
      ctx.strokeStyle = 'rgba(20,14,8,0.25)'; ctx.lineWidth = 1.4 * SS;
      ctx.strokeRect(S * 0.06, S * 0.06, S * 0.88, S * 0.88);
      ctx.fillStyle = 'rgba(255,220,140,0.10)';
      for (const [bx, by] of [[0.15, 0.15], [0.85, 0.15], [0.15, 0.85], [0.85, 0.85]]) {
        ctx.beginPath(); ctx.arc(S * bx, S * by, 1.4 * SS, 0, 7); ctx.fill();
      }
      if (v === 2) { ctx.strokeStyle = 'rgba(255,220,140,0.14)'; ctx.beginPath(); ctx.arc(S / 2, S / 2, S * 0.26, 0, 7); ctx.stroke(); }
    } else if (kind === 'runic') {
      ctx.strokeStyle = `rgba(170,150,255,${v === 2 ? 0.22 : 0.10})`; ctx.lineWidth = 1.2 * SS;
      if (v === 2) { ctx.beginPath(); ctx.arc(S / 2, S / 2, S * 0.3, 0, 7); ctx.stroke(); ctx.beginPath(); ctx.moveTo(S * 0.3, S * 0.62); ctx.lineTo(S * 0.5, S * 0.3); ctx.lineTo(S * 0.7, S * 0.62); ctx.stroke(); }
      else { ctx.beginPath(); ctx.moveTo(rng() * S, rng() * S); ctx.lineTo(rng() * S, rng() * S); ctx.stroke(); }
      ctx.strokeStyle = 'rgba(8,8,14,0.18)'; ctx.lineWidth = 1.2 * SS;
      ctx.strokeRect(0.5, 0.5, S - 1, S - 1);
    } else if (kind === 'slimestone') {
      ctx.strokeStyle = 'rgba(10,14,8,0.22)'; ctx.lineWidth = 1.4 * SS;
      ctx.strokeRect(0.5, 0.5, S - 1, S - 1);
      ctx.fillStyle = 'rgba(140,190,110,0.10)';
      for (let i = 0; i < 2 + v; i++) { ctx.beginPath(); ctx.arc(rng() * S, rng() * S, (2 + rng() * 3) * SS, 0, 7); ctx.fill(); }
    } else if (kind === 'checker') {
      // variant 1 = dark square; plain fill handled by caller tint
    }
    // soft top-light sheen, keeps tiles cohesive
    const g = ctx.createLinearGradient(0, 0, 0, S);
    g.addColorStop(0, 'rgba(255,255,255,0.035)');
    g.addColorStop(1, 'rgba(0,0,0,0.045)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, S, S);
  }

  // --- seamless border-ring painters (return true when handled) ---
  function paintSeamlessBorder(ctx, S, t, kind) {
    const rng = MH.mulberry32(0xb0d3 + kind.length);
    const lobe = (x, y, r, c0, c1) => {
      const g = ctx.createRadialGradient(x - r * 0.35, y - r * 0.4, r * 0.1, x, y, r);
      g.addColorStop(0, c0); g.addColorStop(1, c1);
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill();
    };
    if (kind === 'tree' || kind === 'hedge' || kind === 'deadtree' || kind === 'pine') {
      // a dense canopy band: dark under-storey fills the tile, lit lobes sit on
      // top, and edge-centred lobes continue into the neighbouring tile
      const dead = kind === 'deadtree', pine = kind === 'pine';
      const lo = dead ? '#1a2620' : pine ? '#1c3628' : shade(t.borderCol, -30);
      const mid = dead ? '#33453a' : pine ? '#2e5a40' : shade(t.borderCol, 10);
      const hi = dead ? '#55685a' : pine ? '#5c9a72' : shade(t.borderCol, 78);
      const top = dead ? '#6a7c6c' : pine ? '#8ac094' : shade(t.borderCol, 118);
      ctx.fillStyle = lo; ctx.fillRect(0, 0, S, S);
      // deep shadow gaps between crowns
      ctx.fillStyle = 'rgba(4,10,6,0.55)';
      ctx.beginPath(); ctx.arc(S * 0.5, S * 0.5, S * 0.22, 0, 7); ctx.fill();
      // edge-centred crowns (identical on opposite edges → seamless)
      lobe(0, S * 0.5, S * 0.34, mid, lo); lobe(S, S * 0.5, S * 0.34, mid, lo);
      lobe(S * 0.5, 0, S * 0.34, mid, lo); lobe(S * 0.5, S, S * 0.34, mid, lo);
      lobe(0, 0, S * 0.3, hi, mid); lobe(S, 0, S * 0.3, hi, mid);
      lobe(0, S, S * 0.3, hi, mid); lobe(S, S, S * 0.3, hi, mid);
      // interior crowns, lit from the upper-left
      lobe(S * 0.32, S * 0.36, S * 0.26, top, hi);
      lobe(S * 0.68, S * 0.62, S * 0.24, hi, mid);
      lobe(S * 0.62, S * 0.28, S * 0.18, top, hi);
      // leaf-cluster dabs and a few dark gaps
      ctx.fillStyle = 'rgba(255,255,255,0.12)';
      for (let i = 0; i < 6; i++) { ctx.beginPath(); ctx.arc(S * (0.15 + rng() * 0.7), S * (0.12 + rng() * 0.6), S * (0.03 + rng() * 0.04), 0, 7); ctx.fill(); }
      ctx.fillStyle = 'rgba(0,10,4,0.28)';
      for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.arc(S * (0.15 + rng() * 0.7), S * (0.3 + rng() * 0.6), S * (0.04 + rng() * 0.05), 0, 7); ctx.fill(); }
      if (dead) {
        ctx.strokeStyle = '#141c16'; ctx.lineWidth = 1.4 * SS; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(S * 0.5, S * 0.9); ctx.lineTo(S * 0.48, S * 0.4); ctx.moveTo(S * 0.49, S * 0.6); ctx.lineTo(S * 0.72, S * 0.34); ctx.moveTo(S * 0.49, S * 0.52); ctx.lineTo(S * 0.28, S * 0.3); ctx.stroke();
      }
      return true;
    }
    if (kind === 'rock' || kind === 'dune') {
      // a continuous rock face / dune ridge: dark base, edge-centred lumps
      const dune = kind === 'dune';
      const lo = dune ? shade(t.floor, -40) : shade(t.borderCol, -26);
      const mid = dune ? shade(t.floor, -6) : shade(t.borderCol, 18);
      const hi = dune ? shade(t.floor, 34) : shade(t.borderCol, 64);
      ctx.fillStyle = lo; ctx.fillRect(0, 0, S, S);
      const lump = (x, y, rx, ry, c0, c1) => {
        const g = ctx.createRadialGradient(x - rx * 0.3, y - ry * 0.5, 1, x, y, rx * 1.1);
        g.addColorStop(0, c0); g.addColorStop(1, c1);
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.ellipse(x, y, rx, ry, 0, 0, 7); ctx.fill();
      };
      lump(0, S * 0.5, S * 0.36, S * 0.3, mid, lo); lump(S, S * 0.5, S * 0.36, S * 0.3, mid, lo);
      lump(S * 0.5, 0, S * 0.36, S * 0.3, mid, lo); lump(S * 0.5, S, S * 0.36, S * 0.3, mid, lo);
      lump(S * 0.36, S * 0.42, S * 0.3, S * 0.26, hi, mid);
      lump(S * 0.7, S * 0.66, S * 0.24, S * 0.2, hi, mid);
      ctx.fillStyle = 'rgba(255,255,255,0.12)';
      ctx.beginPath(); ctx.ellipse(S * 0.3, S * 0.32, S * 0.1, S * 0.05, -0.4, 0, 7); ctx.fill();
      ctx.strokeStyle = 'rgba(0,0,0,0.35)'; ctx.lineWidth = SS * 0.8;
      ctx.beginPath(); ctx.moveTo(S * 0.2, S * 0.8); ctx.lineTo(S * 0.42, S * 0.62); ctx.lineTo(S * 0.5, S * 0.78); ctx.stroke();
      return true;
    }
    if (kind === 'wall') {
      // running-bond masonry that continues across tiles: two courses per
      // tile, alternate courses offset by half a brick, lit from the top
      const base = shade(t.borderCol, 4), mortar = shade(t.borderCol, -34);
      ctx.fillStyle = mortar; ctx.fillRect(0, 0, S, S);
      const bw = S / 2, bh = S / 2, gap = 1.2 * SS;
      for (let row = 0; row < 2; row++) {
        const off = row ? bw / 2 : 0;
        for (let i = -1; i <= 2; i++) {
          const x = i * bw + off, y = row * bh;
          const g = ctx.createLinearGradient(0, y, 0, y + bh);
          g.addColorStop(0, shade(base, 30)); g.addColorStop(1, shade(base, -8));
          ctx.fillStyle = g;
          rr(ctx, x + gap / 2, y + gap / 2, bw - gap, bh - gap, 1.5 * SS); ctx.fill();
        }
      }
      ctx.fillStyle = 'rgba(255,255,255,0.06)';
      for (let i = 0; i < 5; i++) ctx.fillRect(rng() * S, rng() * S, 3 * SS, 1.2 * SS);
      ctx.fillStyle = 'rgba(0,0,0,0.10)';
      for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.arc(rng() * S, rng() * S, (1.5 + rng() * 2) * SS, 0, 7); ctx.fill(); }
      return true;
    }
    if (kind === 'bone') {
      // an ossuary wall: stacked pale long-bones with a skull every tile,
      // bone-white on top, cold shadow beneath
      ctx.fillStyle = '#5c5a50'; ctx.fillRect(0, 0, S, S);
      const bone = (x, y, w, h) => {
        const g = ctx.createLinearGradient(0, y, 0, y + h);
        g.addColorStop(0, '#e8e4d4'); g.addColorStop(1, '#a8a494');
        ctx.fillStyle = g;
        rr(ctx, x, y, w, h, h / 2); ctx.fill();
        ctx.fillStyle = '#f4f0e4';
        ctx.beginPath(); ctx.arc(x + h * 0.5, y + h * 0.5, h * 0.55, 0, 7); ctx.arc(x + w - h * 0.5, y + h * 0.5, h * 0.55, 0, 7); ctx.fill();
      };
      const bh = S * 0.16;
      bone(-S * 0.3, S * 0.04, S * 0.8, bh); bone(S * 0.55, S * 0.04, S * 0.8, bh);
      bone(-S * 0.1, S * 0.28, S * 0.7, bh); bone(S * 0.62, S * 0.28, S * 0.6, bh);
      bone(-S * 0.3, S * 0.58, S * 0.8, bh); bone(S * 0.55, S * 0.58, S * 0.8, bh);
      bone(-S * 0.1, S * 0.82, S * 0.7, bh); bone(S * 0.62, S * 0.82, S * 0.6, bh);
      // skull
      const g = ctx.createRadialGradient(S * 0.42, S * 0.42, 1, S * 0.5, S * 0.5, S * 0.2);
      g.addColorStop(0, '#f0ecdc'); g.addColorStop(1, '#a4a090');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(S * 0.5, S * 0.5, S * 0.19, 0, 7); ctx.fill();
      ctx.fillStyle = '#2c2a24';
      ctx.beginPath(); ctx.arc(S * 0.43, S * 0.47, S * 0.05, 0, 7); ctx.arc(S * 0.57, S * 0.47, S * 0.05, 0, 7); ctx.fill();
      ctx.fillRect(S * 0.46, S * 0.6, S * 0.08, S * 0.03);
      const sh = ctx.createLinearGradient(0, 0, 0, S);
      sh.addColorStop(0, 'rgba(255,255,255,0.10)'); sh.addColorStop(1, 'rgba(10,16,24,0.30)');
      ctx.fillStyle = sh; ctx.fillRect(0, 0, S, S);
      return true;
    }
    if (kind === 'coral') {
      // a reef mass: pale rock ridge under water, coral fans and tube sponges
      ctx.fillStyle = '#6a6a58'; ctx.fillRect(0, 0, S, S);
      lobe(0, S * 0.5, S * 0.36, '#a09880', '#5c5a4a'); lobe(S, S * 0.5, S * 0.36, '#a09880', '#5c5a4a');
      lobe(S * 0.5, 0, S * 0.36, '#a09880', '#5c5a4a'); lobe(S * 0.5, S, S * 0.36, '#a09880', '#5c5a4a');
      lobe(S * 0.4, S * 0.4, S * 0.3, '#c0b898', '#7a7460');
      for (const [x, y, r, c] of [[0.22, 0.3, 0.13, '#d85a86'], [0.7, 0.24, 0.11, '#e8845a'], [0.62, 0.72, 0.14, '#38a0a0'], [0.24, 0.76, 0.1, '#e0c060']]) {
        lobe(S * x, S * y, S * r, shade(c, 40), c);
      }
      ctx.strokeStyle = 'rgba(255,255,255,0.25)'; ctx.lineWidth = SS * 0.8;
      ctx.beginPath(); ctx.moveTo(S * 0.5, S * 0.9); ctx.lineTo(S * 0.5, S * 0.55); ctx.moveTo(S * 0.5, S * 0.7); ctx.lineTo(S * 0.6, S * 0.58); ctx.stroke();
      ctx.fillStyle = 'rgba(30,90,140,0.18)'; ctx.fillRect(0, 0, S, S);
      return true;
    }
    return false;
  }

  // --- border / obstacle painters ---
  // seamless=true paints the BORDER-RING version: forms are centred on the
  // tile edges so neighbouring tiles join into one continuous treeline /
  // rock face / wall (BrowserQuest's edges read as masses, not stamps).
  // seamless=false paints a free-standing obstacle with transparent rims.
  function paintBorder(ctx, S, t, kind, seamless) {
    const ORGANIC = ['tree', 'pine', 'deadtree', 'hedge', 'rock', 'dune'].includes(kind);
    if (!ORGANIC && !(seamless && (kind === 'wall' || kind === 'bone' || kind === 'coral'))) {
      ctx.fillStyle = shade(t.borderCol, -14);
      ctx.fillRect(0, 0, S, S);
    } else if (!seamless) {
      const sh = ctx.createRadialGradient(S / 2, S * 0.86, 1, S / 2, S * 0.86, S * 0.5);
      sh.addColorStop(0, 'rgba(8,10,14,0.38)');
      sh.addColorStop(1, 'rgba(8,10,14,0)');
      ctx.fillStyle = sh;
      ctx.beginPath(); ctx.ellipse(S / 2, S * 0.86, S * 0.46, S * 0.18, 0, 0, 7); ctx.fill();
    }
    if (seamless && paintSeamlessBorder(ctx, S, t, kind)) return;
    if (kind === 'tree' || kind === 'pine' || kind === 'deadtree' || kind === 'hedge') {
      const hi = kind === 'deadtree' ? '#5a6656' : kind === 'pine' ? '#679a7c' : shade(t.borderCol, 80);
      const lo = kind === 'deadtree' ? '#20291f' : kind === 'pine' ? '#1e3a2a' : shade(t.borderCol, -22);
      if (kind === 'pine') {
        const g = ctx.createLinearGradient(0, 0, S * 0.6, S);
        g.addColorStop(0, hi); g.addColorStop(1, lo);
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.moveTo(S / 2, S * 0.04); ctx.lineTo(S * 0.88, S * 0.88); ctx.lineTo(S * 0.12, S * 0.88); ctx.closePath(); ctx.fill();
        ctx.fillStyle = 'rgba(255,255,255,0.22)';
        ctx.beginPath(); ctx.moveTo(S / 2, S * 0.04); ctx.lineTo(S * 0.62, S * 0.42); ctx.lineTo(S * 0.38, S * 0.42); ctx.closePath(); ctx.fill();
      } else if (kind === 'hedge') {
        const g = ctx.createLinearGradient(0, 0, 0, S);
        g.addColorStop(0, hi); g.addColorStop(1, lo);
        ctx.fillStyle = g;
        rr(ctx, S * 0.06, S * 0.14, S * 0.88, S * 0.72, S * 0.24); ctx.fill();
        ctx.fillStyle = 'rgba(255,255,255,0.10)';
        ctx.beginPath(); ctx.arc(S * 0.32, S * 0.3, S * 0.12, 0, 7); ctx.arc(S * 0.62, S * 0.26, S * 0.10, 0, 7); ctx.fill();
      } else {
        // trunk peeking beneath the canopy
        ctx.fillStyle = kind === 'deadtree' ? '#2c2620' : '#4a3a28';
        ctx.fillRect(S * 0.46, S * 0.6, S * 0.09, S * 0.28);
        // layered canopy lobes, lit from the upper-left
        const lobe = (x, y, r, c0, c1) => {
          const g = ctx.createRadialGradient(x - r * 0.35, y - r * 0.4, r * 0.15, x, y, r);
          g.addColorStop(0, c0); g.addColorStop(1, c1);
          ctx.fillStyle = g;
          ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill();
        };
        lobe(S * 0.34, S * 0.44, S * 0.26, hi, lo);
        lobe(S * 0.66, S * 0.42, S * 0.24, hi, lo);
        lobe(S * 0.5, S * 0.3, S * 0.26, shade(t.borderCol, 95), t.borderCol);
        // leaf-cluster dabs
        ctx.fillStyle = 'rgba(255,255,255,0.10)';
        ctx.beginPath(); ctx.arc(S * 0.42, S * 0.24, S * 0.07, 0, 7); ctx.arc(S * 0.58, S * 0.34, S * 0.05, 0, 7); ctx.fill();
        if (kind === 'deadtree') {
          ctx.strokeStyle = '#1a241c'; ctx.lineWidth = 1.6 * SS;
          ctx.beginPath(); ctx.moveTo(S / 2, S * 0.3); ctx.lineTo(S / 2, S * 0.86); ctx.moveTo(S / 2, S * 0.5); ctx.lineTo(S * 0.7, S * 0.36); ctx.stroke();
        }
      }
    } else if (kind === 'rock' || kind === 'dune' || kind === 'ice') {
      if (kind === 'rock' || kind === 'dune') {
        // two soft-shaded lumps instead of one square slab
        const c0 = kind === 'dune' ? shade(t.floor, 30) : shade(t.borderCol, 60);
        const c1 = kind === 'dune' ? shade(t.floor, -26) : shade(t.borderCol, -14);
        const lump = (x, y, rx, ry) => {
          const g = ctx.createRadialGradient(x - rx * 0.3, y - ry * 0.5, 2, x, y, rx * 1.15);
          g.addColorStop(0, c0); g.addColorStop(1, c1);
          ctx.fillStyle = g;
          ctx.beginPath(); ctx.ellipse(x, y, rx, ry, 0, 0, 7); ctx.fill();
        };
        lump(S * 0.38, S * 0.58, S * 0.3, S * 0.26);
        lump(S * 0.66, S * 0.62, S * 0.24, S * 0.2);
        ctx.fillStyle = 'rgba(255,255,255,0.14)';
        ctx.beginPath(); ctx.ellipse(S * 0.32, S * 0.46, S * 0.1, S * 0.06, -0.4, 0, 7); ctx.fill();
      } else {
        const g = ctx.createLinearGradient(0, 0, 0, S);
        g.addColorStop(0, '#dceefc'); g.addColorStop(1, '#7e9cc0');
        ctx.fillStyle = g;
        rr(ctx, S * 0.08, S * 0.12, S * 0.84, S * 0.78, S * 0.2);
        ctx.fill();
        ctx.fillStyle = 'rgba(255,255,255,0.12)';
        rr(ctx, S * 0.18, S * 0.2, S * 0.34, S * 0.18, S * 0.09); ctx.fill();
        ctx.strokeStyle = 'rgba(255,255,255,0.4)'; ctx.lineWidth = SS;
        ctx.beginPath(); ctx.moveTo(S * 0.3, S * 0.7); ctx.lineTo(S * 0.5, S * 0.4); ctx.lineTo(S * 0.62, S * 0.6); ctx.stroke();
      }
    } else if (kind === 'bone') {
      const g = ctx.createLinearGradient(0, 0, 0, S);
      g.addColorStop(0, '#b8b4a4'); g.addColorStop(1, '#6e6a5c');
      ctx.fillStyle = g;
      rr(ctx, S * 0.1, S * 0.08, S * 0.8, S * 0.84, S * 0.16); ctx.fill();
      ctx.fillStyle = '#3a382f';
      ctx.beginPath(); ctx.arc(S * 0.36, S * 0.4, S * 0.09, 0, 7); ctx.arc(S * 0.64, S * 0.4, S * 0.09, 0, 7); ctx.fill();
      ctx.fillRect(S * 0.42, S * 0.62, S * 0.16, S * 0.05);
    } else if (kind === 'brass') {
      const g = ctx.createLinearGradient(0, 0, 0, S);
      g.addColorStop(0, '#c89a58'); g.addColorStop(1, '#6e4e28');
      ctx.fillStyle = g;
      rr(ctx, S * 0.05, S * 0.05, S * 0.9, S * 0.9, S * 0.1); ctx.fill();
      ctx.strokeStyle = 'rgba(40,24,8,0.5)'; ctx.lineWidth = 1.4 * SS;
      ctx.beginPath(); ctx.arc(S / 2, S / 2, S * 0.26, 0, 7); ctx.stroke();
      for (let i = 0; i < 8; i++) {
        const a = i * Math.PI / 4;
        ctx.beginPath(); ctx.moveTo(S / 2 + Math.cos(a) * S * 0.26, S / 2 + Math.sin(a) * S * 0.26);
        ctx.lineTo(S / 2 + Math.cos(a) * S * 0.36, S / 2 + Math.sin(a) * S * 0.36); ctx.stroke();
      }
    } else if (kind === 'coral') {
      ctx.fillStyle = '#b14a72'; rr(ctx, S * 0.12, S * 0.2, S * 0.3, S * 0.7, S * 0.15); ctx.fill();
      ctx.fillStyle = '#3a8a8a'; rr(ctx, S * 0.5, S * 0.34, S * 0.32, S * 0.56, S * 0.15); ctx.fill();
      ctx.fillStyle = 'rgba(255,255,255,0.18)';
      ctx.beginPath(); ctx.arc(S * 0.26, S * 0.3, S * 0.06, 0, 7); ctx.arc(S * 0.64, S * 0.42, S * 0.05, 0, 7); ctx.fill();
    } else if (kind === 'column' || kind === 'voidpillar') {
      const g = ctx.createLinearGradient(0, 0, S, 0);
      if (kind === 'voidpillar') { g.addColorStop(0, '#3c3858'); g.addColorStop(0.5, '#5a5488'); g.addColorStop(1, '#2c2844'); }
      else { g.addColorStop(0, shade(t.borderCol, -16)); g.addColorStop(0.5, shade(t.borderCol, 46)); g.addColorStop(1, shade(t.borderCol, -26)); }
      ctx.fillStyle = g;
      ctx.fillRect(S * 0.2, S * 0.08, S * 0.6, S * 0.84);
      ctx.fillRect(S * 0.12, S * 0.04, S * 0.76, S * 0.1);
      ctx.fillRect(S * 0.12, S * 0.86, S * 0.76, S * 0.1);
      if (kind === 'voidpillar') {
        ctx.fillStyle = 'rgba(170,150,255,0.6)';
        ctx.beginPath(); ctx.arc(S / 2, S * 0.46, S * 0.07, 0, 7); ctx.fill();
      }
    } else { // wall
      const g = ctx.createLinearGradient(0, 0, 0, S);
      g.addColorStop(0, shade(t.borderCol, 36));
      g.addColorStop(1, shade(t.borderCol, -16));
      ctx.fillStyle = g;
      rr(ctx, S * 0.04, S * 0.04, S * 0.92, S * 0.92, S * 0.1); ctx.fill();
      ctx.strokeStyle = 'rgba(10,12,18,0.3)'; ctx.lineWidth = SS;
      ctx.beginPath(); ctx.moveTo(S * 0.04, S / 2); ctx.lineTo(S * 0.96, S / 2);
      ctx.moveTo(S / 2, S * 0.04); ctx.lineTo(S / 2, S / 2);
      ctx.moveTo(S * 0.3, S / 2); ctx.lineTo(S * 0.3, S * 0.96);
      ctx.moveTo(S * 0.7, S / 2); ctx.lineTo(S * 0.7, S * 0.96); ctx.stroke();
      ctx.fillStyle = 'rgba(255,255,255,0.07)';
      rr(ctx, S * 0.08, S * 0.08, S * 0.4, S * 0.16, S * 0.06); ctx.fill();
    }
    ctx.strokeStyle = 'rgba(8,10,14,0.4)';
    ctx.lineWidth = 1.2 * SS;
    ctx.strokeRect(0.5, 0.5, S - 1, S - 1);
  }

  // --- shared prop library: drawn into 20x26 logical px, origin bottom-center ---
  const PROP_PAINTERS = {
    tree(ctx, W, H) {
      ctx.fillStyle = '#5a4430'; ctx.fillRect(W * 0.44, H * 0.55, W * 0.12, H * 0.4);
      const g = ctx.createRadialGradient(W * 0.4, H * 0.22, 2, W / 2, H * 0.32, W * 0.5);
      g.addColorStop(0, '#6fbe72'); g.addColorStop(1, '#2c5e34');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(W / 2, H * 0.32, W * 0.42, 0, 7); ctx.fill();
    },
    pine(ctx, W, H) {
      ctx.fillStyle = '#4e3a2a'; ctx.fillRect(W * 0.45, H * 0.7, W * 0.1, H * 0.26);
      ctx.fillStyle = '#3c6e52';
      for (let i = 0; i < 3; i++) {
        const y = H * (0.18 + i * 0.2), w = W * (0.3 + i * 0.12);
        ctx.beginPath(); ctx.moveTo(W / 2, y - H * 0.16); ctx.lineTo(W / 2 + w, y + H * 0.1); ctx.lineTo(W / 2 - w, y + H * 0.1); ctx.closePath(); ctx.fill();
      }
      ctx.fillStyle = 'rgba(235,245,255,0.55)';
      ctx.beginPath(); ctx.moveTo(W / 2, H * 0.02); ctx.lineTo(W * 0.66, H * 0.2); ctx.lineTo(W * 0.34, H * 0.2); ctx.closePath(); ctx.fill();
    },
    deadtree(ctx, W, H) {
      ctx.strokeStyle = '#4a4036'; ctx.lineWidth = 3; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(W / 2, H * 0.96); ctx.lineTo(W / 2, H * 0.3);
      ctx.moveTo(W / 2, H * 0.55); ctx.lineTo(W * 0.78, H * 0.32);
      ctx.moveTo(W / 2, H * 0.45); ctx.lineTo(W * 0.26, H * 0.22); ctx.stroke();
    },
    bush(ctx, W, H) {
      const g = ctx.createRadialGradient(W * 0.4, H * 0.62, 2, W / 2, H * 0.72, W * 0.46);
      g.addColorStop(0, '#5fae62'); g.addColorStop(1, '#2c5e34');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(W * 0.36, H * 0.78, W * 0.24, 0, 7); ctx.arc(W * 0.64, H * 0.76, W * 0.26, 0, 7); ctx.arc(W / 2, H * 0.62, W * 0.24, 0, 7); ctx.fill();
    },
    flowers(ctx, W, H) {
      ctx.strokeStyle = '#3c7040'; ctx.lineWidth = 1.6;
      const heads = [[0.3, 0.62, '#e87a9a'], [0.55, 0.5, '#f0d060'], [0.75, 0.66, '#9a8af0']];
      for (const [fx, fy, col] of heads) {
        ctx.beginPath(); ctx.moveTo(W * fx, H * 0.95); ctx.quadraticCurveTo(W * fx + 2, H * 0.8, W * fx, H * fy + 4); ctx.stroke();
        ctx.fillStyle = col;
        for (let i = 0; i < 5; i++) {
          const a = i * Math.PI * 2 / 5;
          ctx.beginPath(); ctx.arc(W * fx + Math.cos(a) * 3, H * fy + Math.sin(a) * 3, 2.2, 0, 7); ctx.fill();
        }
        ctx.fillStyle = '#fff3c0'; ctx.beginPath(); ctx.arc(W * fx, H * fy, 1.8, 0, 7); ctx.fill();
      }
    },
    mushrooms(ctx, W, H) {
      for (const [mx, s, col] of [[0.32, 1, '#d06a5a'], [0.6, 0.7, '#c8a060'], [0.78, 0.5, '#d06a5a']]) {
        ctx.fillStyle = '#e8e0cc';
        ctx.fillRect(W * mx - 1.5 * s, H * 0.8, 3 * s, H * 0.16);
        ctx.fillStyle = col;
        ctx.beginPath(); ctx.arc(W * mx, H * 0.8, 5 * s, Math.PI, 0); ctx.fill();
        ctx.fillStyle = 'rgba(255,255,255,0.5)';
        ctx.beginPath(); ctx.arc(W * mx - 2 * s, H * 0.76, 1.1 * s, 0, 7); ctx.fill();
      }
    },
    rock(ctx, W, H) {
      const g = ctx.createLinearGradient(0, H * 0.5, 0, H);
      g.addColorStop(0, '#8a8d96'); g.addColorStop(1, '#4e525a');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.moveTo(W * 0.14, H * 0.94); ctx.lineTo(W * 0.24, H * 0.6); ctx.lineTo(W * 0.52, H * 0.5); ctx.lineTo(W * 0.84, H * 0.66); ctx.lineTo(W * 0.88, H * 0.94); ctx.closePath(); ctx.fill();
      ctx.fillStyle = 'rgba(255,255,255,0.14)';
      ctx.beginPath(); ctx.moveTo(W * 0.3, H * 0.62); ctx.lineTo(W * 0.5, H * 0.54); ctx.lineTo(W * 0.56, H * 0.62); ctx.closePath(); ctx.fill();
    },
    crate(ctx, W, H) {
      const g = ctx.createLinearGradient(0, H * 0.5, 0, H);
      g.addColorStop(0, '#a8804e'); g.addColorStop(1, '#6e4e2c');
      ctx.fillStyle = g;
      ctx.fillRect(W * 0.2, H * 0.52, W * 0.6, H * 0.44);
      ctx.strokeStyle = 'rgba(40,24,8,0.55)'; ctx.lineWidth = 1.6;
      ctx.strokeRect(W * 0.2, H * 0.52, W * 0.6, H * 0.44);
      ctx.beginPath(); ctx.moveTo(W * 0.2, H * 0.52); ctx.lineTo(W * 0.8, H * 0.96); ctx.moveTo(W * 0.8, H * 0.52); ctx.lineTo(W * 0.2, H * 0.96); ctx.stroke();
    },
    barrel(ctx, W, H) {
      const g = ctx.createLinearGradient(W * 0.2, 0, W * 0.8, 0);
      g.addColorStop(0, '#6e4e2c'); g.addColorStop(0.5, '#a8804e'); g.addColorStop(1, '#5e421f');
      ctx.fillStyle = g;
      rr(ctx, W * 0.26, H * 0.5, W * 0.48, H * 0.46, 4); ctx.fill();
      ctx.strokeStyle = '#3c2a14'; ctx.lineWidth = 1.6;
      ctx.beginPath(); ctx.moveTo(W * 0.26, H * 0.64); ctx.lineTo(W * 0.74, H * 0.64);
      ctx.moveTo(W * 0.26, H * 0.82); ctx.lineTo(W * 0.74, H * 0.82); ctx.stroke();
    },
    lamppost(ctx, W, H) {
      ctx.strokeStyle = '#2c2f38'; ctx.lineWidth = 2.4; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(W / 2, H * 0.96); ctx.lineTo(W / 2, H * 0.18); ctx.stroke();
      ctx.fillStyle = '#ffd98a';
      ctx.beginPath(); ctx.arc(W / 2, H * 0.14, 3.4, 0, 7); ctx.fill();
      ctx.strokeStyle = '#2c2f38'; ctx.lineWidth = 1.6;
      ctx.strokeRect(W / 2 - 4.4, H * 0.07, 8.8, 8.8);
    },
    lantern(ctx, W, H) {
      ctx.strokeStyle = '#5a6a5a'; ctx.lineWidth = 2; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(W / 2, H * 0.96); ctx.lineTo(W / 2, H * 0.3); ctx.quadraticCurveTo(W / 2, H * 0.18, W * 0.68, H * 0.2); ctx.stroke();
      ctx.fillStyle = '#cfff90';
      ctx.beginPath(); ctx.arc(W * 0.68, H * 0.3, 3.2, 0, 7); ctx.fill();
    },
    brazier(ctx, W, H) {
      ctx.fillStyle = '#3c3a40';
      rr(ctx, W * 0.3, H * 0.6, W * 0.4, H * 0.14, 2); ctx.fill();
      ctx.fillRect(W * 0.44, H * 0.72, W * 0.12, H * 0.22);
      const g = ctx.createRadialGradient(W / 2, H * 0.48, 1, W / 2, H * 0.48, 7);
      g.addColorStop(0, '#fff0a0'); g.addColorStop(0.5, '#ff9a4a'); g.addColorStop(1, 'rgba(255,90,40,0)');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(W / 2, H * 0.48, 7, 0, 7); ctx.fill();
    },
    statue(ctx, W, H) {
      ctx.fillStyle = '#8d8a96';
      rr(ctx, W * 0.28, H * 0.78, W * 0.44, H * 0.18, 2); ctx.fill();
      const g = ctx.createLinearGradient(0, H * 0.2, 0, H * 0.8);
      g.addColorStop(0, '#b0adba'); g.addColorStop(1, '#6e6b78');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(W / 2, H * 0.3, 3.4, 0, 7); ctx.fill();
      rr(ctx, W * 0.38, H * 0.36, W * 0.24, H * 0.42, 3); ctx.fill();
    },
    gravestone(ctx, W, H) {
      const g = ctx.createLinearGradient(0, H * 0.4, 0, H);
      g.addColorStop(0, '#9a978c'); g.addColorStop(1, '#5c5a50');
      ctx.fillStyle = g;
      rr(ctx, W * 0.3, H * 0.46, W * 0.4, H * 0.5, 5); ctx.fill();
      ctx.strokeStyle = 'rgba(30,30,26,0.5)'; ctx.lineWidth = 1.4;
      ctx.beginPath(); ctx.moveTo(W * 0.42, H * 0.62); ctx.lineTo(W * 0.58, H * 0.62);
      ctx.moveTo(W / 2, H * 0.56); ctx.lineTo(W / 2, H * 0.72); ctx.stroke();
    },
    bones(ctx, W, H) {
      ctx.fillStyle = '#d8d4c0';
      rr(ctx, W * 0.2, H * 0.8, W * 0.4, 2.6, 1.3); ctx.fill();
      rr(ctx, W * 0.46, H * 0.88, W * 0.34, 2.4, 1.2); ctx.fill();
      ctx.beginPath(); ctx.arc(W * 0.68, H * 0.74, 4, 0, 7); ctx.fill();
      ctx.fillStyle = '#3a382f';
      ctx.beginPath(); ctx.arc(W * 0.65, H * 0.72, 1.1, 0, 7); ctx.arc(W * 0.72, H * 0.72, 1.1, 0, 7); ctx.fill();
    },
    icecrystal(ctx, W, H) {
      const g = ctx.createLinearGradient(0, H * 0.2, 0, H);
      g.addColorStop(0, '#eaf6ff'); g.addColorStop(1, '#7aa0d0');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.moveTo(W / 2, H * 0.16); ctx.lineTo(W * 0.7, H * 0.6); ctx.lineTo(W * 0.6, H * 0.94); ctx.lineTo(W * 0.4, H * 0.94); ctx.lineTo(W * 0.3, H * 0.6); ctx.closePath(); ctx.fill();
      ctx.fillStyle = 'rgba(255,255,255,0.55)';
      ctx.beginPath(); ctx.moveTo(W / 2, H * 0.2); ctx.lineTo(W * 0.56, H * 0.5); ctx.lineTo(W * 0.46, H * 0.5); ctx.closePath(); ctx.fill();
    },
    crystal(ctx, W, H) {
      const g = ctx.createLinearGradient(0, H * 0.3, 0, H);
      g.addColorStop(0, '#d8b0ff'); g.addColorStop(1, '#6a48b0');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.moveTo(W * 0.36, H * 0.3); ctx.lineTo(W * 0.5, H * 0.94); ctx.lineTo(W * 0.22, H * 0.94); ctx.closePath(); ctx.fill();
      ctx.beginPath(); ctx.moveTo(W * 0.66, H * 0.44); ctx.lineTo(W * 0.82, H * 0.94); ctx.lineTo(W * 0.5, H * 0.94); ctx.closePath(); ctx.fill();
      ctx.fillStyle = 'rgba(255,255,255,0.5)';
      ctx.beginPath(); ctx.moveTo(W * 0.36, H * 0.34); ctx.lineTo(W * 0.42, H * 0.6); ctx.lineTo(W * 0.34, H * 0.56); ctx.closePath(); ctx.fill();
    },
    gear(ctx, W, H) {
      ctx.fillStyle = '#8a6a3a';
      for (let i = 0; i < 8; i++) {
        const a = i * Math.PI / 4;
        ctx.save(); ctx.translate(W / 2, H * 0.66); ctx.rotate(a);
        ctx.fillRect(-1.8, -9, 3.6, 4); ctx.restore();
      }
      ctx.beginPath(); ctx.arc(W / 2, H * 0.66, 7, 0, 7); ctx.fill();
      ctx.fillStyle = '#5a4424';
      ctx.beginPath(); ctx.arc(W / 2, H * 0.66, 2.6, 0, 7); ctx.fill();
    },
    pipe(ctx, W, H) {
      ctx.fillStyle = '#7a5c34';
      ctx.fillRect(W * 0.34, H * 0.4, W * 0.16, H * 0.56);
      rr(ctx, W * 0.26, H * 0.3, W * 0.32, H * 0.14, 3); ctx.fill();
      ctx.fillStyle = 'rgba(255,240,200,0.35)';
      ctx.beginPath(); ctx.arc(W * 0.42, H * 0.24, 2.4, 0, 7); ctx.arc(W * 0.5, H * 0.16, 1.8, 0, 7); ctx.fill();
    },
    banner(ctx, W, H) {
      ctx.strokeStyle = '#4a4036'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(W / 2, H * 0.96); ctx.lineTo(W / 2, H * 0.08); ctx.stroke();
      ctx.fillStyle = '#a83a4a';
      ctx.beginPath(); ctx.moveTo(W / 2 + 1, H * 0.1); ctx.lineTo(W * 0.9, H * 0.14); ctx.lineTo(W * 0.84, H * 0.4); ctx.lineTo(W / 2 + 1, H * 0.36); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#e8c168';
      ctx.beginPath(); ctx.arc(W * 0.68, H * 0.25, 2, 0, 7); ctx.fill();
    },
    stall(ctx, W, H) {
      ctx.fillStyle = '#6e4e2c';
      ctx.fillRect(W * 0.16, H * 0.6, 2.4, H * 0.36); ctx.fillRect(W * 0.8, H * 0.6, 2.4, H * 0.36);
      ctx.fillStyle = '#8a6038'; ctx.fillRect(W * 0.12, H * 0.66, W * 0.76, H * 0.1);
      for (let i = 0; i < 4; i++) {
        ctx.fillStyle = i % 2 ? '#c84a4a' : '#e8e0d0';
        ctx.beginPath();
        ctx.moveTo(W * (0.1 + i * 0.2), H * 0.42); ctx.lineTo(W * (0.3 + i * 0.2), H * 0.42);
        ctx.lineTo(W * (0.28 + i * 0.2), H * 0.56); ctx.lineTo(W * (0.12 + i * 0.2), H * 0.56); ctx.closePath(); ctx.fill();
      }
    },
    fountain(ctx, W, H) {
      // wide lower basin with water
      ctx.fillStyle = '#6f7682';
      ctx.beginPath(); ctx.ellipse(W / 2, H * 0.86, W * 0.46, H * 0.14, 0, 0, 7); ctx.fill();
      ctx.fillStyle = '#3f86b8';
      ctx.beginPath(); ctx.ellipse(W / 2, H * 0.84, W * 0.38, H * 0.10, 0, 0, 7); ctx.fill();
      ctx.fillStyle = 'rgba(185,222,255,0.5)';
      ctx.beginPath(); ctx.ellipse(W * 0.42, H * 0.83, W * 0.12, H * 0.03, 0, 0, 7); ctx.fill();
      // short pedestal + upper tier basin (not a tall post)
      ctx.fillStyle = '#8a909c'; ctx.fillRect(W * 0.45, H * 0.62, W * 0.10, H * 0.18);
      ctx.fillStyle = '#7f868f';
      ctx.beginPath(); ctx.ellipse(W / 2, H * 0.60, W * 0.21, H * 0.06, 0, 0, 7); ctx.fill();
      ctx.fillStyle = '#4a93c8';
      ctx.beginPath(); ctx.ellipse(W / 2, H * 0.59, W * 0.15, H * 0.04, 0, 0, 7); ctx.fill();
      // arcing water jets to read unmistakably as a fountain
      ctx.strokeStyle = 'rgba(195,228,255,0.85)'; ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.moveTo(W / 2, H * 0.5); ctx.quadraticCurveTo(W * 0.64, H * 0.5, W * 0.6, H * 0.6); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(W / 2, H * 0.5); ctx.quadraticCurveTo(W * 0.36, H * 0.5, W * 0.4, H * 0.6); ctx.stroke();
      ctx.fillStyle = 'rgba(205,236,255,0.95)';
      ctx.beginPath(); ctx.arc(W / 2, H * 0.48, 1.8, 0, 7); ctx.fill();
    },
    urn(ctx, W, H) {
      const g = ctx.createLinearGradient(W * 0.3, 0, W * 0.7, 0);
      g.addColorStop(0, '#8a6a48'); g.addColorStop(0.5, '#c8a070'); g.addColorStop(1, '#74542f');
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.moveTo(W * 0.38, H * 0.5); ctx.bezierCurveTo(W * 0.2, H * 0.66, W * 0.26, H * 0.9, W * 0.42, H * 0.94);
      ctx.lineTo(W * 0.58, H * 0.94); ctx.bezierCurveTo(W * 0.74, H * 0.9, W * 0.8, H * 0.66, W * 0.62, H * 0.5);
      ctx.closePath(); ctx.fill();
      ctx.fillRect(W * 0.36, H * 0.44, W * 0.28, H * 0.07);
    },
    bookpile(ctx, W, H) {
      const cols = ['#7a4a3a', '#3a5a7a', '#5a7a4a'];
      cols.forEach((col, i) => {
        ctx.fillStyle = col;
        rr(ctx, W * (0.26 + (i % 2) * 0.06), H * (0.86 - i * 0.1), W * 0.46, H * 0.09, 1.4); ctx.fill();
      });
      ctx.fillStyle = 'rgba(255,245,220,0.7)';
      ctx.fillRect(W * 0.3, H * 0.885, W * 0.38, 1.2);
    },
    candles(ctx, W, H) {
      for (const [cx, h] of [[0.34, 0.2], [0.5, 0.3], [0.66, 0.16]]) {
        ctx.fillStyle = '#e8e0cc';
        ctx.fillRect(W * cx - 1.8, H * (0.96 - h), 3.6, H * h);
        const g = ctx.createRadialGradient(W * cx, H * (0.93 - h), 0.5, W * cx, H * (0.93 - h), 4);
        g.addColorStop(0, '#fff0a0'); g.addColorStop(1, 'rgba(255,160,60,0)');
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(W * cx, H * (0.93 - h), 4, 0, 7); ctx.fill();
      }
    },
    anvil(ctx, W, H) {
      ctx.fillStyle = '#3c4048';
      rr(ctx, W * 0.3, H * 0.82, W * 0.4, H * 0.14, 2); ctx.fill();
      ctx.fillRect(W * 0.42, H * 0.7, W * 0.16, H * 0.14);
      const g = ctx.createLinearGradient(0, H * 0.56, 0, H * 0.72);
      g.addColorStop(0, '#7a7f8c'); g.addColorStop(1, '#4a4e58');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.moveTo(W * 0.16, H * 0.56); ctx.lineTo(W * 0.84, H * 0.56); ctx.lineTo(W * 0.74, H * 0.72); ctx.lineTo(W * 0.32, H * 0.72); ctx.closePath(); ctx.fill();
    },
    pillar(ctx, W, H) {
      const g = ctx.createLinearGradient(W * 0.28, 0, W * 0.72, 0);
      g.addColorStop(0, '#6e6b78'); g.addColorStop(0.5, '#b0adba'); g.addColorStop(1, '#5e5b68');
      ctx.fillStyle = g;
      ctx.fillRect(W * 0.32, H * 0.16, W * 0.36, H * 0.74);
      ctx.fillRect(W * 0.24, H * 0.08, W * 0.52, H * 0.1);
      ctx.fillRect(W * 0.24, H * 0.88, W * 0.52, H * 0.08);
    },
    web(ctx, W, H) {
      ctx.strokeStyle = 'rgba(230,235,245,0.55)'; ctx.lineWidth = 0.9;
      const cx = W * 0.5, cy = H * 0.4;
      for (let i = 0; i < 6; i++) {
        const a = i * Math.PI / 3;
        ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(a) * 9, cy + Math.sin(a) * 9); ctx.stroke();
      }
      for (let r = 3; r <= 9; r += 3) { ctx.beginPath(); ctx.arc(cx, cy, r, 0, 7); ctx.stroke(); }
    },
    reeds(ctx, W, H) {
      ctx.strokeStyle = '#5a8048'; ctx.lineWidth = 1.6; ctx.lineCap = 'round';
      for (const [rx, h, sway] of [[0.3, 0.5, 3], [0.45, 0.62, -2], [0.6, 0.46, 4], [0.74, 0.56, -3]]) {
        ctx.beginPath(); ctx.moveTo(W * rx, H * 0.96);
        ctx.quadraticCurveTo(W * rx + sway, H * (0.96 - h * 0.6), W * rx + sway * 1.5, H * (0.96 - h));
        ctx.stroke();
      }
      ctx.fillStyle = '#7a6038';
      rr(ctx, W * 0.43, H * 0.3, 3, 7, 1.5); ctx.fill();
    },
    lilypad(ctx, W, H) {
      ctx.fillStyle = '#4a8a4e';
      ctx.beginPath(); ctx.ellipse(W / 2, H * 0.84, W * 0.34, H * 0.12, 0, 0.3, Math.PI * 2 - 0.2); ctx.lineTo(W / 2, H * 0.84); ctx.fill();
      ctx.fillStyle = '#e89ab8';
      for (let i = 0; i < 5; i++) {
        const a = i * Math.PI * 2 / 5 - 0.5;
        ctx.beginPath(); ctx.ellipse(W * 0.64 + Math.cos(a) * 3, H * 0.74 + Math.sin(a) * 2, 2.4, 1.4, a, 0, 7); ctx.fill();
      }
    },
    coral(ctx, W, H) {
      ctx.fillStyle = '#c85a82';
      for (const [bx, bh] of [[0.3, 0.4], [0.46, 0.55], [0.62, 0.36]]) {
        rr(ctx, W * bx - 2.2, H * (0.94 - bh), 4.4, H * bh, 2.2); ctx.fill();
      }
      ctx.fillStyle = '#3a9a9a';
      rr(ctx, W * 0.72, H * 0.6, 4, H * 0.34, 2); ctx.fill();
      ctx.fillStyle = 'rgba(255,255,255,0.25)';
      ctx.beginPath(); ctx.arc(W * 0.46, H * 0.42, 1.4, 0, 7); ctx.fill();
    },
    shell(ctx, W, H) {
      const g = ctx.createLinearGradient(0, H * 0.6, 0, H);
      g.addColorStop(0, '#f0d8c0'); g.addColorStop(1, '#b08a68');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(W / 2, H * 0.88, 6.4, Math.PI, 0); ctx.closePath(); ctx.fill();
      ctx.strokeStyle = 'rgba(120,80,50,0.5)'; ctx.lineWidth = 1;
      for (let i = -1; i <= 1; i++) {
        ctx.beginPath(); ctx.moveTo(W / 2, H * 0.88); ctx.lineTo(W / 2 + i * 4, H * 0.88 - 6); ctx.stroke();
      }
    },
    cactus(ctx, W, H) {
      ctx.fillStyle = '#4e8a4a';
      rr(ctx, W * 0.42, H * 0.3, W * 0.16, H * 0.66, 4); ctx.fill();
      rr(ctx, W * 0.2, H * 0.44, W * 0.14, H * 0.2, 3.5); ctx.fill();
      ctx.fillRect(W * 0.3, H * 0.56, W * 0.14, H * 0.06);
      ctx.fillStyle = 'rgba(255,255,255,0.25)';
      rr(ctx, W * 0.45, H * 0.34, 2, H * 0.4, 1); ctx.fill();
    },
    snowdrift(ctx, W, H) {
      const g = ctx.createLinearGradient(0, H * 0.6, 0, H);
      g.addColorStop(0, '#f4f8ff'); g.addColorStop(1, '#b8c8e0');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.moveTo(W * 0.08, H * 0.94);
      ctx.quadraticCurveTo(W * 0.3, H * 0.55, W * 0.55, H * 0.74);
      ctx.quadraticCurveTo(W * 0.75, H * 0.6, W * 0.92, H * 0.94);
      ctx.closePath(); ctx.fill();
    },
    rubble(ctx, W, H) {
      ctx.fillStyle = '#6e6a60';
      for (const [rx, ry, s] of [[0.3, 0.86, 3.4], [0.5, 0.9, 2.6], [0.66, 0.84, 3], [0.44, 0.78, 2.2]]) {
        ctx.beginPath();
        ctx.moveTo(W * rx - s, H * ry + s * 0.6); ctx.lineTo(W * rx, H * ry - s); ctx.lineTo(W * rx + s, H * ry + s * 0.5);
        ctx.closePath(); ctx.fill();
      }
      ctx.fillStyle = 'rgba(255,255,255,0.10)';
      ctx.beginPath(); ctx.arc(W * 0.5, H * 0.84, 1.6, 0, 7); ctx.fill();
    },
    stump(ctx, W, H) {
      const g = ctx.createLinearGradient(0, H * 0.6, 0, H);
      g.addColorStop(0, '#8a6a44'); g.addColorStop(1, '#5a4226');
      ctx.fillStyle = g;
      rr(ctx, W * 0.3, H * 0.64, W * 0.4, H * 0.32, 3); ctx.fill();
      ctx.fillStyle = '#c8a878';
      ctx.beginPath(); ctx.ellipse(W / 2, H * 0.64, W * 0.2, H * 0.07, 0, 0, 7); ctx.fill();
      ctx.strokeStyle = 'rgba(120,80,40,0.6)'; ctx.lineWidth = 0.9;
      ctx.beginPath(); ctx.arc(W / 2, H * 0.64, 2.4, 0, 7); ctx.stroke();
    },
    fence(ctx, W, H) {
      ctx.fillStyle = '#8a6a44';
      ctx.fillRect(W * 0.18, H * 0.6, 2.6, H * 0.36);
      ctx.fillRect(W * 0.76, H * 0.6, 2.6, H * 0.36);
      ctx.fillRect(W * 0.1, H * 0.68, W * 0.8, 2.4);
      ctx.fillRect(W * 0.1, H * 0.82, W * 0.8, 2.4);
    },
    runestone(ctx, W, H) {
      const g = ctx.createLinearGradient(0, H * 0.3, 0, H);
      g.addColorStop(0, '#5a5870'); g.addColorStop(1, '#33324a');
      ctx.fillStyle = g;
      rr(ctx, W * 0.3, H * 0.34, W * 0.4, H * 0.62, 6); ctx.fill();
      ctx.strokeStyle = 'rgba(170,150,255,0.85)'; ctx.lineWidth = 1.4;
      ctx.beginPath();
      ctx.moveTo(W * 0.42, H * 0.74); ctx.lineTo(W / 2, H * 0.46); ctx.lineTo(W * 0.58, H * 0.74);
      ctx.moveTo(W * 0.45, H * 0.64); ctx.lineTo(W * 0.55, H * 0.64);
      ctx.stroke();
    },
    beam(ctx, W, H) {
      ctx.fillStyle = '#6e542f';
      ctx.fillRect(W * 0.22, H * 0.2, 3.4, H * 0.76);
      ctx.fillRect(W * 0.72, H * 0.2, 3.4, H * 0.76);
      ctx.fillRect(W * 0.14, H * 0.14, W * 0.74, 3.4);
      ctx.fillStyle = 'rgba(0,0,0,0.25)';
      ctx.fillRect(W * 0.22, H * 0.2, 3.4, 2);
    },
  };
  // props that glow in the dark get a light pool at placement
  // light-emitting props get a glow + carve light in the dark. Fountains were
  // here too, but the bright top-glow made them read as lamps — removed.
  MH.GLOW_PROPS = { brazier: 0xff9a4a, lamppost: 0xffd98a, lantern: 0xcfff90, candles: 0xffe9a8, crystal: 0xb06ce0, icecrystal: 0x9fd0ff, runestone: 0x9a8aff, pipe: 0xffe8c0 };

  MH.zoneSprites = {
    generateAll(scene) {
      const S = 16 * SS;
      for (const [key, t] of Object.entries(T22)) {
        for (let v = 0; v < 3; v++) {
          const [c, ctx] = canvasOf(S, S);
          paintFloor(ctx, S, t, t.floorKind, v);
          scene.textures.addCanvas(`zt_${key}_floor${v}`, c);
        }
        // organic borders (treelines, rock faces, dunes, reefs) are painted
        // into the room painting as one continuous mass; their sprites stay
        // transparent so no 16px stamp repeats round the room. Without the
        // painter the seamless ring art is used as before.
        const organicKind = MH.PAINTED_BORDER_KINDS.includes(t.borderKind) || !!t.paintBorder;
        const painted = organicKind && !!(MH.painter && MH.painter.enabled !== false);
        {
          const [c, ctx] = canvasOf(S, S);
          if (!painted) paintBorder(ctx, S, t, t.borderKind, true);   // seamless ring
          scene.textures.addCanvas(`zt_${key}_border`, c);
        }
        // obstacles reuse the border painter with a small variation tint;
        // organic obstacles are the biome-shaped treelines / cavern walls
        // roomgen grows INTO the room, so they use the same mass treatment
        for (let i = 0; i < 2; i++) {
          const [c, ctx] = canvasOf(S, S);
          if (!painted) {
            paintBorder(ctx, S, t, t.borderKind, organicKind);
            if (i === 1) {
              ctx.fillStyle = 'rgba(0,0,0,0.12)';
              ctx.fillRect(0, 0, S, S);
            }
          }
          scene.textures.addCanvas(`zt_${key}_obst${i}`, c);
        }
      }
      // shared prop library
      const PW = 20 * SS, PH = 26 * SS;
      for (const [name, painter] of Object.entries(PROP_PAINTERS)) {
        const [c, ctx] = canvasOf(PW, PH);
        ctx.save();
        ctx.scale(SS, SS);
        painter(ctx, 20, 26);
        ctx.restore();
        scene.textures.addCanvas(`zt_prop_${name}`, c);
      }
      // tiny ambient particle shapes
      {
        const [c, ctx] = canvasOf(7 * SS, 7 * SS);
        ctx.fillStyle = '#cfe8a0';
        ctx.beginPath();
        ctx.ellipse(3.5 * SS, 3.5 * SS, 3 * SS, 1.6 * SS, 0.7, 0, 7);
        ctx.fill();
        scene.textures.addCanvas('zt_px_leaf', c);
      }
      // landmark travel art: sewer grate, worn road tile
      {
        const S2 = 16 * SS;
        const [c, ctx] = canvasOf(S2, S2);
        // cobble base
        ctx.fillStyle = '#4c515c'; ctx.fillRect(0, 0, S2, S2);
        // iron ring
        const g = ctx.createRadialGradient(S2 / 2, S2 / 2, S2 * 0.1, S2 / 2, S2 / 2, S2 * 0.46);
        g.addColorStop(0, '#3a3e48'); g.addColorStop(1, '#181b22');
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(S2 / 2, S2 / 2, S2 * 0.42, 0, 7); ctx.fill();
        ctx.strokeStyle = '#6a707c'; ctx.lineWidth = 1.6 * SS;
        ctx.beginPath(); ctx.arc(S2 / 2, S2 / 2, S2 * 0.40, 0, 7); ctx.stroke();
        // grate bars
        ctx.strokeStyle = '#0c0e14'; ctx.lineWidth = 1.8 * SS;
        for (let i = -2; i <= 2; i++) {
          const off = i * S2 * 0.13;
          const half = Math.sqrt(Math.max(0, (S2 * 0.34) ** 2 - off * off));
          ctx.beginPath();
          ctx.moveTo(S2 / 2 + off, S2 / 2 - half);
          ctx.lineTo(S2 / 2 + off, S2 / 2 + half);
          ctx.stroke();
        }
        // a hint of green glow from below
        ctx.fillStyle = 'rgba(140,210,150,0.18)';
        ctx.beginPath(); ctx.arc(S2 / 2, S2 / 2, S2 * 0.3, 0, 7); ctx.fill();
        scene.textures.addCanvas('zt_grate', c);
      }
      {
        const S2 = 16 * SS;
        const [c, ctx] = canvasOf(S2, S2);
        // worn road: translucent overlay tile laid over the floor
        ctx.clearRect(0, 0, S2, S2);
        const g = ctx.createLinearGradient(0, 0, S2, 0);
        g.addColorStop(0, 'rgba(20,16,10,0)');
        g.addColorStop(0.18, 'rgba(20,16,10,0.16)');
        g.addColorStop(0.5, 'rgba(28,22,14,0.22)');
        g.addColorStop(0.82, 'rgba(20,16,10,0.16)');
        g.addColorStop(1, 'rgba(20,16,10,0)');
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, S2, S2);
        // wheel ruts
        ctx.strokeStyle = 'rgba(12,10,6,0.20)'; ctx.lineWidth = 1.2 * SS;
        ctx.beginPath(); ctx.moveTo(S2 * 0.32, 0); ctx.lineTo(S2 * 0.32, S2);
        ctx.moveTo(S2 * 0.68, 0); ctx.lineTo(S2 * 0.68, S2); ctx.stroke();
        // scattered pebbles
        ctx.fillStyle = 'rgba(255,255,255,0.07)';
        for (const [px, py] of [[0.42, 0.2], [0.55, 0.6], [0.4, 0.85], [0.62, 0.32]]) {
          ctx.beginPath(); ctx.arc(S2 * px, S2 * py, 1.1 * SS, 0, 7); ctx.fill();
        }
        scene.textures.addCanvas('zt_road', c);
      }
      {
        const [c, ctx] = canvasOf(6 * SS, 6 * SS);
        const g = ctx.createRadialGradient(3 * SS, 3 * SS, 0.5, 3 * SS, 3 * SS, 3 * SS);
        g.addColorStop(0, 'rgba(255,255,255,1)');
        g.addColorStop(1, 'rgba(255,255,255,0)');
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, 6 * SS, 6 * SS);
        scene.textures.addCanvas('zt_px_soft', c);
      }
    },
  };
})();
