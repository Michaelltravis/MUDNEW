// Misthollow: equipment & item icon factory. Every drop gets real art,
// derived from its type + wear slot + name keywords: a "rusty iron sword"
// comes out rusty, iron, and sword-shaped. Rarity draws the border;
// legendary and set pieces get per-class signature palettes and motifs.
(() => {
  const MH = window.MH = window.MH || {};
  const SS = 4, S = 22 * SS;          // 22px logical icons, supersampled

  // ---------------- palettes ----------------
  const MATERIALS = [
    [/rust|corrod/, { a: '#8a5a3a', b: '#5a3422', shine: 0.15 }],
    [/obsidian|black|shadow|dark|void/, { a: '#3a3644', b: '#1c1a24', shine: 0.35 }],
    [/gold|gilded|royal/, { a: '#e8c168', b: '#a8842e', shine: 0.8 }],
    [/silver|mithril|moon/, { a: '#d8dce8', b: '#8a90a4', shine: 0.85 }],
    [/bronze|copper|brass/, { a: '#c08a4a', b: '#7a5424', shine: 0.6 }],
    [/bone|ivory|skull/, { a: '#e0dac4', b: '#a89e80', shine: 0.2 }],
    [/crystal|diamond|glass|prism/, { a: '#bfe2ff', b: '#6a9ad0', shine: 0.9 }],
    [/flame|fire|ember|inferno|burn/, { a: '#ff8a4a', b: '#c0392a', shine: 0.7 }],
    [/ice|frost|glacial|winter/, { a: '#cfe8ff', b: '#7aa0d0', shine: 0.8 }],
    [/dragon/, { a: '#7ab06a', b: '#3a6a3a', shine: 0.5 }],
    [/holy|blessed|divine|radiant|sun/, { a: '#fff0c0', b: '#d0a850', shine: 0.9 }],
    [/leather|hide/, { a: '#a8804e', b: '#6e4e2c', shine: 0.1 }],
    [/cloth|silk|robe|wool/, { a: '#b09ac0', b: '#6a5a80', shine: 0.05 }],
    [/iron/, { a: '#9aa0ac', b: '#5c6068', shine: 0.5 }],
    [/steel/, { a: '#b8c2d4', b: '#707a8c', shine: 0.7 }],
    [/wood|oak|ash\b/, { a: '#a8804e', b: '#6a4e2c', shine: 0.1 }],
  ];
  const DEFAULT_MAT = {
    weapon: { a: '#b8c2d4', b: '#707a8c', shine: 0.6 },
    armor: { a: '#9aa0ac', b: '#5c6068', shine: 0.4 },
    other: { a: '#a8946a', b: '#6e5e3e', shine: 0.2 },
  };
  const RARITY = {
    common: null, uncommon: '#5fc46a', rare: '#5a8ae8',
    epic: '#b06ce0', legendary: '#ffa838',
  };
  // per-class signature palettes + motif glyphs for high-end gear
  const CLASS_SIG = {
    warrior:     { a: '#e05a4a', b: '#7a2018', motif: 'chevron' },
    paladin:     { a: '#ffe9a8', b: '#b08428', motif: 'sunburst' },
    mage:        { a: '#9a8aff', b: '#4a3aa8', motif: 'eye' },
    necromancer: { a: '#9adba0', b: '#3a6a44', motif: 'skull' },
    thief:       { a: '#b8b2c8', b: '#4a4458', motif: 'fan' },
    assassin:    { a: '#8a5a9a', b: '#3a1a44', motif: 'drop' },
    ranger:      { a: '#8ac06a', b: '#3e6a2e', motif: 'leaf' },
    cleric:      { a: '#cfe2ff', b: '#6a82b0', motif: 'halo' },
    bard:        { a: '#f0b060', b: '#a06428', motif: 'lyre' },
  };
  const CLASS_HINTS = [
    [/blade|war|berserk|gladiat|champion/, 'warrior'],
    [/paladin|crusad|aegis|valor|oath/, 'paladin'],
    [/arcan|mage|sorcer|spell|rune(?!stone)/, 'mage'],
    [/necro|lich|grave|death|bone(?!s)/, 'necromancer'],
    [/thief|shadow(?:fang)?|sneak|cutpurse/, 'thief'],
    [/assassin|venom|poison|night/, 'assassin'],
    [/ranger|hunt|hawk|beast|wild/, 'ranger'],
    [/cleric|priest|saint|prayer|light(?:bring)?/, 'cleric'],
    [/bard|song|lyric|minstrel|chord/, 'bard'],
  ];

  function matFor(name, type) {
    const n = (name || '').toLowerCase();
    for (const [re, m] of MATERIALS) if (re.test(n)) return m;
    return DEFAULT_MAT[type === 'weapon' ? 'weapon' : type === 'armor' ? 'armor' : 'other'];
  }
  function classFor(info) {
    const n = (info.name || '').toLowerCase();
    for (const [re, cls] of CLASS_HINTS) if (re.test(n)) return cls;
    const p = MH.state && MH.state.player;
    return (p && (p.char_class || '').toLowerCase()) || 'warrior';
  }

  // ---------------- shape painters (22x22 logical, ctx pre-scaled) ----------------
  // each painter draws with colors {a: light, b: dark}
  function grad(x, c, x0, y0, x1, y1) {
    const g = x.createLinearGradient(x0, y0, x1, y1);
    g.addColorStop(0, c.a); g.addColorStop(1, c.b);
    return g;
  }
  const SHAPES = {
    sword(x, c) {
      x.fillStyle = grad(x, c, 8, 2, 13, 14);
      x.beginPath(); x.moveTo(11, 1); x.lineTo(13.5, 4); x.lineTo(12.5, 14); x.lineTo(9.5, 14); x.lineTo(8.5, 4); x.closePath(); x.fill();
      x.fillStyle = '#8a6a3a'; x.fillRect(6.5, 14, 9, 2);
      x.fillStyle = '#6a4e2c'; x.fillRect(10, 16, 2, 4.5);
      x.fillStyle = 'rgba(255,255,255,.5)'; x.fillRect(10.6, 2.5, 0.9, 10);
    },
    dagger(x, c) {
      x.fillStyle = grad(x, c, 9, 5, 13, 13);
      x.beginPath(); x.moveTo(11, 4); x.lineTo(13, 7); x.lineTo(11.8, 14); x.lineTo(10.2, 14); x.lineTo(9, 7); x.closePath(); x.fill();
      x.fillStyle = '#5a5464'; x.fillRect(8, 14, 6, 1.6);
      x.fillStyle = '#3c3844'; x.fillRect(10.2, 15.6, 1.6, 3.4);
    },
    axe(x, c) {
      x.fillStyle = '#6a4e2c'; x.fillRect(10.2, 4, 1.8, 15);
      x.fillStyle = grad(x, c, 6, 4, 16, 10);
      x.beginPath(); x.moveTo(11, 4); x.quadraticCurveTo(18, 4.5, 17, 11); x.quadraticCurveTo(13.5, 9.5, 11, 10.5); x.closePath(); x.fill();
      x.beginPath(); x.moveTo(11, 4); x.quadraticCurveTo(4, 4.5, 5, 11); x.quadraticCurveTo(8.5, 9.5, 11, 10.5); x.closePath(); x.fill();
    },
    mace(x, c) {
      x.fillStyle = '#6a4e2c'; x.fillRect(10.2, 8, 1.8, 12);
      x.fillStyle = grad(x, c, 7, 2, 15, 9);
      x.beginPath(); x.arc(11, 6.5, 4.4, 0, 7); x.fill();
      x.fillStyle = c.b;
      for (let i = 0; i < 8; i++) {
        const a = i * Math.PI / 4;
        x.beginPath(); x.arc(11 + Math.cos(a) * 4.4, 6.5 + Math.sin(a) * 4.4, 1, 0, 7); x.fill();
      }
    },
    staff(x, c) {
      x.fillStyle = '#6a4e2c'; x.fillRect(10.2, 5, 1.7, 15.5);
      x.fillStyle = grad(x, c, 8, 1, 14, 7);
      x.beginPath(); x.arc(11, 4.4, 3, 0, 7); x.fill();
      x.fillStyle = 'rgba(255,255,255,.6)';
      x.beginPath(); x.arc(10, 3.4, 1, 0, 7); x.fill();
    },
    bow(x, c) {
      x.strokeStyle = grad(x, c, 5, 3, 15, 19); x.lineWidth = 1.8; x.lineCap = 'round';
      x.beginPath(); x.moveTo(7, 2.5); x.quadraticCurveTo(16, 11, 7, 19.5); x.stroke();
      x.strokeStyle = '#d8d4c0'; x.lineWidth = 0.7;
      x.beginPath(); x.moveTo(7, 2.5); x.lineTo(7, 19.5); x.stroke();
      x.strokeStyle = '#8a6a3a'; x.lineWidth = 1.2;
      x.beginPath(); x.moveTo(6, 11); x.lineTo(15, 11); x.stroke();
    },
    spear(x, c) {
      x.fillStyle = '#6a4e2c'; x.fillRect(10.3, 7, 1.5, 13.5);
      x.fillStyle = grad(x, c, 9, 1, 13, 7);
      x.beginPath(); x.moveTo(11, 1); x.lineTo(13.4, 6.5); x.lineTo(11, 5.6); x.lineTo(8.6, 6.5); x.closePath(); x.fill();
    },
    whip(x, c) {
      x.strokeStyle = grad(x, c, 4, 4, 18, 18); x.lineWidth = 1.7; x.lineCap = 'round';
      x.beginPath(); x.moveTo(5, 18); x.quadraticCurveTo(3, 8, 10, 7); x.quadraticCurveTo(18, 6, 16, 12); x.quadraticCurveTo(14.5, 16, 11, 14); x.stroke();
      x.fillStyle = '#6a4e2c'; x.fillRect(4, 17, 2.4, 4);
    },
    shield(x, c) {
      x.fillStyle = grad(x, c, 6, 3, 16, 18);
      x.beginPath(); x.moveTo(11, 2.5); x.quadraticCurveTo(17.5, 4, 17, 9);
      x.quadraticCurveTo(16.5, 16, 11, 19.5); x.quadraticCurveTo(5.5, 16, 5, 9);
      x.quadraticCurveTo(4.5, 4, 11, 2.5); x.fill();
      x.strokeStyle = 'rgba(255,255,255,.35)'; x.lineWidth = 1;
      x.beginPath(); x.moveTo(11, 4); x.lineTo(11, 18); x.moveTo(6.5, 9.5); x.lineTo(15.5, 9.5); x.stroke();
    },
    helm(x, c) {
      x.fillStyle = grad(x, c, 6, 4, 16, 14);
      x.beginPath(); x.arc(11, 11, 6.2, Math.PI, 0); x.lineTo(17.2, 15); x.lineTo(4.8, 15); x.closePath(); x.fill();
      x.fillStyle = '#1c1a24'; x.fillRect(6.5, 11, 9, 1.6);
      x.fillStyle = c.b; x.fillRect(10.2, 3, 1.6, 4);
    },
    cuirass(x, c) {
      x.fillStyle = grad(x, c, 6, 4, 16, 19);
      x.beginPath(); x.moveTo(6, 4); x.lineTo(16, 4); x.lineTo(17.5, 9); x.lineTo(16, 19); x.lineTo(6, 19); x.lineTo(4.5, 9); x.closePath(); x.fill();
      x.strokeStyle = 'rgba(0,0,0,.35)'; x.lineWidth = 1;
      x.beginPath(); x.moveTo(11, 5); x.lineTo(11, 18); x.moveTo(6, 9); x.quadraticCurveTo(11, 12, 16, 9); x.stroke();
    },
    leggings(x, c) {
      x.fillStyle = grad(x, c, 7, 3, 15, 19);
      x.beginPath(); x.moveTo(6.5, 3); x.lineTo(15.5, 3); x.lineTo(15, 10); x.lineTo(13.5, 19.5); x.lineTo(10.8, 19.5); x.lineTo(11, 11); x.lineTo(11.2, 19.5); x.lineTo(8.5, 19.5); x.lineTo(7, 10); x.closePath(); x.fill();
    },
    boots(x, c) {
      x.fillStyle = grad(x, c, 6, 6, 16, 19);
      x.beginPath(); x.moveTo(7, 4); x.lineTo(11, 4); x.lineTo(11, 13); x.lineTo(16, 15.5); x.lineTo(16, 19) ; x.lineTo(7, 19); x.closePath(); x.fill();
      x.fillStyle = c.b; x.fillRect(7, 17.4, 9, 1.6);
    },
    gauntlets(x, c) {
      x.fillStyle = grad(x, c, 6, 4, 16, 18);
      x.beginPath(); x.moveTo(8, 4); x.lineTo(14, 4); x.lineTo(14.5, 12); x.lineTo(16.5, 13.5); x.lineTo(15.5, 15.5); x.lineTo(13, 14.5); x.lineTo(13, 19) ; x.lineTo(9, 19); x.lineTo(8, 12); x.closePath(); x.fill();
      x.strokeStyle = 'rgba(0,0,0,.3)'; x.lineWidth = 0.8;
      x.beginPath(); x.moveTo(10, 5); x.lineTo(10, 11); x.moveTo(12, 5); x.lineTo(12, 11); x.stroke();
    },
    cloak(x, c) {
      x.fillStyle = grad(x, c, 6, 3, 16, 19);
      x.beginPath(); x.moveTo(11, 2.5); x.quadraticCurveTo(17, 6, 16.5, 19.5); x.lineTo(13, 17.5); x.lineTo(11, 19.5); x.lineTo(9, 17.5); x.lineTo(5.5, 19.5); x.quadraticCurveTo(5, 6, 11, 2.5); x.fill();
      x.fillStyle = '#e8c168'; x.beginPath(); x.arc(11, 5, 1.1, 0, 7); x.fill();
    },
    belt(x, c) {
      x.fillStyle = grad(x, c, 4, 9, 18, 13);
      x.fillRect(3.5, 9, 15, 4);
      x.fillStyle = '#e8c168'; x.fillRect(9, 8, 4, 6);
      x.fillStyle = '#1c1a24'; x.fillRect(10.2, 9.4, 1.6, 3.2);
    },
    ring(x, c) {
      x.strokeStyle = grad(x, c, 7, 6, 15, 18); x.lineWidth = 2.4;
      x.beginPath(); x.arc(11, 12.5, 5, 0, 7); x.stroke();
      x.fillStyle = '#bfe2ff'; x.beginPath();
      x.moveTo(11, 4); x.lineTo(13.4, 6.6); x.lineTo(11, 9); x.lineTo(8.6, 6.6); x.closePath(); x.fill();
    },
    amulet(x, c) {
      x.strokeStyle = '#a8842e'; x.lineWidth = 1;
      x.beginPath(); x.arc(11, 8, 6, Math.PI * 0.85, Math.PI * 0.15); x.stroke();
      x.fillStyle = grad(x, c, 8, 9, 14, 17);
      x.beginPath(); x.moveTo(11, 9.5); x.lineTo(14.5, 13); x.lineTo(11, 18); x.lineTo(7.5, 13); x.closePath(); x.fill();
      x.fillStyle = 'rgba(255,255,255,.5)'; x.beginPath(); x.arc(9.8, 12.4, 0.9, 0, 7); x.fill();
    },
    bracer(x, c) {
      x.fillStyle = grad(x, c, 7, 5, 15, 17);
      x.beginPath(); x.moveTo(7.5, 5); x.lineTo(14.5, 5); x.lineTo(15.5, 17); x.lineTo(6.5, 17); x.closePath(); x.fill();
      x.strokeStyle = 'rgba(0,0,0,.35)'; x.lineWidth = 0.9;
      x.beginPath(); x.moveTo(7.2, 8.5); x.lineTo(14.8, 8.5); x.moveTo(7, 13.5); x.lineTo(15, 13.5); x.stroke();
    },
    potion(x, c) {
      x.fillStyle = '#cfe2f4';
      x.fillRect(9.4, 3, 3.2, 3);
      x.fillStyle = grad(x, c, 7, 8, 15, 19);
      x.beginPath(); x.moveTo(9.4, 6); x.lineTo(12.6, 6); x.lineTo(15.8, 13); x.arc(11, 14.4, 4.9, -0.32, Math.PI + 0.32, false); x.closePath(); x.fill();
      x.fillStyle = 'rgba(255,255,255,.4)'; x.beginPath(); x.arc(9, 13, 1.2, 0, 7); x.fill();
      x.fillStyle = '#8a6a3a'; x.fillRect(9, 2, 4, 1.6);
    },
    scroll(x, c) {
      x.fillStyle = '#e8dec0';
      x.fillRect(6, 4, 10, 14);
      x.fillStyle = '#c8b890'; x.fillRect(6, 4, 10, 2); x.fillRect(6, 16, 10, 2);
      x.strokeStyle = '#8a7a5a'; x.lineWidth = 0.8;
      for (let i = 0; i < 4; i++) { x.beginPath(); x.moveTo(8, 8 + i * 2.2); x.lineTo(14, 8 + i * 2.2); x.stroke(); }
    },
    wand(x, c) {
      x.save(); x.translate(11, 11); x.rotate(-0.7);
      x.fillStyle = grad(x, c, -2, -8, 2, 8); x.fillRect(-1, -8, 2, 16);
      x.restore();
      x.fillStyle = '#fff0c0';
      x.beginPath(); x.arc(16, 5, 1.6, 0, 7); x.fill();
      x.beginPath(); x.arc(18.4, 8, 0.9, 0, 7); x.fill();
    },
    bag(x, c) {
      x.fillStyle = grad(x, c, 6, 7, 16, 19);
      x.beginPath(); x.moveTo(7, 8); x.quadraticCurveTo(4.5, 19, 11, 19.5); x.quadraticCurveTo(17.5, 19, 15, 8); x.closePath(); x.fill();
      x.strokeStyle = '#5a4226'; x.lineWidth = 1.4;
      x.beginPath(); x.moveTo(7, 8); x.quadraticCurveTo(11, 5.5, 15, 8); x.stroke();
      x.fillStyle = '#e8c168'; x.beginPath(); x.arc(11, 8, 1, 0, 7); x.fill();
    },
    chest(x, c) {
      x.fillStyle = grad(x, c, 5, 6, 17, 18);
      x.fillRect(4.5, 9, 13, 9);
      x.beginPath(); x.moveTo(4.5, 9); x.quadraticCurveTo(11, 4, 17.5, 9); x.closePath(); x.fill();
      x.strokeStyle = 'rgba(0,0,0,.4)'; x.lineWidth = 1;
      x.strokeRect(4.5, 9, 13, 9);
      x.fillStyle = '#e8c168'; x.fillRect(9.8, 9.5, 2.4, 4);
    },
    note(x, c) {
      x.fillStyle = '#efe8d4'; x.fillRect(6, 4, 10, 14);
      x.strokeStyle = '#9a8a6a'; x.lineWidth = 0.8;
      for (let i = 0; i < 5; i++) { x.beginPath(); x.moveTo(7.5, 7 + i * 2.2); x.lineTo(14.5, 7 + i * 2.2); x.stroke(); }
      x.fillStyle = '#c0392a'; x.beginPath(); x.arc(14, 16, 1.4, 0, 7); x.fill();
    },
    waterskin(x, c) {
      x.fillStyle = grad(x, c, 6, 6, 16, 19);
      x.beginPath(); x.moveTo(9, 6); x.quadraticCurveTo(4, 12, 8, 18); x.quadraticCurveTo(11, 20, 14, 18); x.quadraticCurveTo(18, 12, 13, 6); x.closePath(); x.fill();
      x.fillStyle = '#5a4226'; x.fillRect(9.8, 3, 2.4, 3.4);
      x.fillStyle = '#3a78b0'; x.beginPath(); x.arc(11, 4, 0.8, 0, 7); x.fill();
    },
    key(x, c) {
      x.strokeStyle = grad(x, c, 6, 5, 16, 17); x.lineWidth = 2;
      x.beginPath(); x.arc(8.5, 7.5, 3, 0, 7); x.stroke();
      x.beginPath(); x.moveTo(10.5, 9.8); x.lineTo(16, 16); x.stroke();
      x.beginPath(); x.moveTo(14, 16.5); x.lineTo(16, 14.8); x.moveTo(12.5, 14.5); x.lineTo(14.2, 13); x.stroke();
    },
    food(x, c) {
      x.fillStyle = '#c89858';
      x.beginPath(); x.ellipse(11, 12, 6.5, 4.4, -0.35, 0, 7); x.fill();
      x.fillStyle = '#e8c890';
      x.beginPath(); x.ellipse(11, 11, 6, 3.6, -0.35, 0, 7); x.fill();
      x.strokeStyle = '#a87838'; x.lineWidth = 0.8;
      for (const [sx, sy] of [[8, 10], [11, 11.5], [14, 9.6]]) { x.beginPath(); x.moveTo(sx, sy); x.lineTo(sx + 1.4, sy - 0.8); x.stroke(); }
    },
    coins(x, c) {
      for (const [cx, cy] of [[8, 14], [13.5, 15], [11, 10]]) {
        x.fillStyle = '#e8c168'; x.beginPath(); x.ellipse(cx, cy, 3.4, 2.4, 0, 0, 7); x.fill();
        x.strokeStyle = '#a8842e'; x.lineWidth = 0.7; x.stroke();
      }
    },
    gem(x, c) {
      x.fillStyle = grad(x, c, 6, 6, 16, 18);
      x.beginPath(); x.moveTo(7, 8); x.lineTo(15, 8); x.lineTo(17, 11); x.lineTo(11, 18.5); x.lineTo(5, 11); x.closePath(); x.fill();
      x.strokeStyle = 'rgba(255,255,255,.45)'; x.lineWidth = 0.7;
      x.beginPath(); x.moveTo(7, 8); x.lineTo(11, 11.5); x.lineTo(15, 8); x.moveTo(11, 11.5); x.lineTo(11, 18); x.stroke();
    },
    torch(x, c) {
      x.fillStyle = '#6a4e2c'; x.fillRect(9.9, 9, 2.2, 11);
      const g = x.createRadialGradient(11, 6, 0.5, 11, 6, 5.5);
      g.addColorStop(0, '#fff0a0'); g.addColorStop(0.5, '#ff9a4a'); g.addColorStop(1, 'rgba(255,90,40,0)');
      x.fillStyle = g; x.beginPath(); x.arc(11, 6, 5.5, 0, 7); x.fill();
    },
    boat(x, c) {
      x.fillStyle = grad(x, c, 5, 12, 17, 18);
      x.beginPath(); x.moveTo(4, 12); x.lineTo(18, 12); x.quadraticCurveTo(16, 18, 11, 18); x.quadraticCurveTo(6, 18, 4, 12); x.fill();
      x.fillStyle = '#e8e0cc'; x.beginPath(); x.moveTo(11, 3); x.lineTo(15.5, 10.5); x.lineTo(11, 10.5); x.closePath(); x.fill();
      x.fillStyle = '#6a4e2c'; x.fillRect(10.6, 3, 0.9, 9);
    },
    sundries(x, c) {
      x.fillStyle = grad(x, c, 6, 7, 16, 17);
      x.fillRect(6, 8, 10, 9);
      x.strokeStyle = 'rgba(0,0,0,.35)'; x.lineWidth = 0.9; x.strokeRect(6, 8, 10, 9);
      x.fillStyle = 'rgba(255,255,255,.25)'; x.fillRect(6, 8, 10, 2);
    },
  };

  // motifs stamped on legendary/set gear, per class
  const MOTIFS = {
    chevron(x, p) { x.strokeStyle = p; x.lineWidth = 1.3; x.beginPath(); x.moveTo(7, 18); x.lineTo(11, 14.5); x.lineTo(15, 18); x.stroke(); },
    sunburst(x, p) { x.strokeStyle = p; x.lineWidth = 1; for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; x.beginPath(); x.moveTo(11 + Math.cos(a) * 1.6, 17 + Math.sin(a) * 1.2); x.lineTo(11 + Math.cos(a) * 3.4, 17 + Math.sin(a) * 2.6); x.stroke(); } },
    eye(x, p) { x.strokeStyle = p; x.lineWidth = 1; x.beginPath(); x.ellipse(11, 17, 3, 1.8, 0, 0, 7); x.stroke(); x.fillStyle = p; x.beginPath(); x.arc(11, 17, 0.9, 0, 7); x.fill(); },
    skull(x, p) { x.fillStyle = p; x.beginPath(); x.arc(11, 16.6, 2.2, 0, 7); x.fill(); x.fillStyle = '#10131e'; x.beginPath(); x.arc(10.2, 16.4, 0.6, 0, 7); x.arc(11.8, 16.4, 0.6, 0, 7); x.fill(); },
    fan(x, p) { x.strokeStyle = p; x.lineWidth = 1; for (let i = -1; i <= 1; i++) { x.beginPath(); x.moveTo(11, 19); x.lineTo(11 + i * 3, 15); x.stroke(); } },
    drop(x, p) { x.fillStyle = p; x.beginPath(); x.moveTo(11, 14.5); x.quadraticCurveTo(13.4, 17.5, 11, 19.2); x.quadraticCurveTo(8.6, 17.5, 11, 14.5); x.fill(); },
    leaf(x, p) { x.fillStyle = p; x.beginPath(); x.moveTo(11, 14.5); x.quadraticCurveTo(15, 16, 11, 19.5); x.quadraticCurveTo(7, 16, 11, 14.5); x.fill(); x.strokeStyle = p; x.lineWidth = 0.6; x.beginPath(); x.moveTo(11, 15); x.lineTo(11, 19); x.stroke(); },
    halo(x, p) { x.strokeStyle = p; x.lineWidth = 1.2; x.beginPath(); x.ellipse(11, 15.4, 3, 1.1, 0, 0, 7); x.stroke(); },
    lyre(x, p) { x.strokeStyle = p; x.lineWidth = 1; x.beginPath(); x.moveTo(9, 19); x.quadraticCurveTo(8, 15, 9.6, 14.5); x.moveTo(13, 19); x.quadraticCurveTo(14, 15, 12.4, 14.5); x.moveTo(9.4, 17); x.lineTo(12.6, 17); x.stroke(); },
  };

  // ---------------- named-set themes: every set piece gets its own
  // palette, sigil border, and emblem so the 4 pieces read as a matched
  // suit, distinct from every other set ----------------
  const SET_EMBLEMS = {
    pickaxe(x, p) { // crossed pickaxes
      x.strokeStyle = p; x.lineWidth = 1.1; x.lineCap = 'round';
      x.beginPath(); x.moveTo(8, 19); x.lineTo(13.5, 14); x.moveTo(14, 19); x.lineTo(8.5, 14); x.stroke();
      x.beginPath(); x.moveTo(11.6, 14.2); x.quadraticCurveTo(14, 13.2, 14.6, 14.6); x.moveTo(10.4, 14.2); x.quadraticCurveTo(8, 13.2, 7.4, 14.6); x.stroke();
    },
    leaf(x, p) { x.fillStyle = p; x.beginPath(); x.moveTo(11, 13.5); x.quadraticCurveTo(15, 16, 11, 19.6); x.quadraticCurveTo(7, 16, 11, 13.5); x.fill();
      x.strokeStyle = '#10131e'; x.lineWidth = 0.5; x.beginPath(); x.moveTo(11, 14.4); x.lineTo(11, 19); x.stroke(); },
    spider(x, p) { x.fillStyle = p; x.beginPath(); x.arc(11, 16.6, 2, 0, 7); x.fill(); x.beginPath(); x.arc(11, 14.6, 1.1, 0, 7); x.fill();
      x.strokeStyle = p; x.lineWidth = 0.8; x.lineCap = 'round';
      for (const dx of [-1, 1]) for (const [y0, y1] of [[15.6, 13.5], [16.4, 15.8], [17.2, 18.6]]) { x.beginPath(); x.moveTo(11 + dx * 1.4, 16.4); x.lineTo(11 + dx * 4.2, y1); x.stroke(); } },
    ankh(x, p) { x.strokeStyle = p; x.lineWidth = 1.2; x.beginPath(); x.arc(11, 14.6, 1.6, 0, 7); x.stroke();
      x.beginPath(); x.moveTo(11, 16); x.lineTo(11, 19.6); x.moveTo(8.6, 17.4); x.lineTo(13.4, 17.4); x.stroke(); },
    rat(x, p) { x.fillStyle = p; x.beginPath(); x.arc(10.5, 16.8, 2.1, 0, 7); x.fill();
      x.beginPath(); x.arc(8.9, 15.2, 1, 0, 7); x.arc(12.1, 15.2, 1, 0, 7); x.fill();
      x.strokeStyle = p; x.lineWidth = 0.8; x.beginPath(); x.moveTo(12.4, 17.4); x.quadraticCurveTo(16, 18, 15, 15.5); x.stroke(); },
    claw(x, p) { x.strokeStyle = p; x.lineWidth = 1.1; x.lineCap = 'round';
      for (const dx of [-2.4, 0, 2.4]) { x.beginPath(); x.moveTo(11 + dx * 0.5, 14); x.quadraticCurveTo(11 + dx, 17, 11 + dx * 1.3, 19.4); x.stroke(); } },
    skull(x, p) { x.fillStyle = p; x.beginPath(); x.arc(11, 16.4, 2.3, 0, 7); x.fill(); x.fillRect(9.6, 17.6, 2.8, 2);
      x.fillStyle = '#10131e'; x.beginPath(); x.arc(10.1, 16.2, 0.7, 0, 7); x.arc(11.9, 16.2, 0.7, 0, 7); x.fill(); },
    chaosstar(x, p) { x.strokeStyle = p; x.lineWidth = 0.9; for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; x.beginPath(); x.moveTo(11, 16.6); x.lineTo(11 + Math.cos(a) * 3.4, 16.6 + Math.sin(a) * 3); x.stroke(); }
      x.fillStyle = p; x.beginPath(); x.arc(11, 16.6, 1, 0, 7); x.fill(); },
    horsemen(x, p) { x.fillStyle = p; x.beginPath(); x.arc(11, 16.4, 2.2, 0, 7); x.fill();
      x.strokeStyle = '#10131e'; x.lineWidth = 0.8; x.beginPath(); x.moveTo(9.6, 15); x.lineTo(12.4, 18); x.moveTo(12.4, 15); x.lineTo(9.6, 18); x.stroke(); },
    snowflake(x, p) { x.strokeStyle = p; x.lineWidth = 0.9; x.lineCap = 'round'; for (let i = 0; i < 6; i++) { const a = i * Math.PI / 3; const ex = 11 + Math.cos(a) * 3.4, ey = 16.6 + Math.sin(a) * 3.4; x.beginPath(); x.moveTo(11, 16.6); x.lineTo(ex, ey);
      x.moveTo(11 + Math.cos(a) * 2.2, 16.6 + Math.sin(a) * 2.2); x.lineTo(11 + Math.cos(a) * 2.2 + Math.cos(a + 1) * 1, 16.6 + Math.sin(a) * 2.2 + Math.sin(a + 1) * 1); x.stroke(); } },
  };
  const SET_THEMES = {
    miners_garb:          { pal: { a: '#c08a4a', b: '#6e4824', shine: 0.5 }, accent: '#e8b860', emblem: 'pickaxe' },
    forest_stalker:       { pal: { a: '#7faa55', b: '#3c5e28', shine: 0.25 }, accent: '#9ad06a', emblem: 'leaf' },
    drow_shadow:          { pal: { a: '#6a5a8a', b: '#241a38', shine: 0.4 }, accent: '#b08aff', emblem: 'spider' },
    pharaohs_legacy:      { pal: { a: '#f0d060', b: '#9a6e1e', shine: 0.85 }, accent: '#ffe9a8', emblem: 'ankh' },
    sewer_rat:            { pal: { a: '#8a8a5a', b: '#48482a', shine: 0.2 }, accent: '#b0b070', emblem: 'rat' },
    dragonscale:          { pal: { a: '#5fae5a', b: '#264e26', shine: 0.55 }, accent: '#8ae060', emblem: 'claw' },
    necromancers_regalia: { pal: { a: '#d8d2bc', b: '#7a7a5a', shine: 0.3 }, accent: '#9adba0', emblem: 'skull' },
    chaos_weave:          { pal: { a: '#b06ce0', b: '#4a2a78', shine: 0.7 }, accent: '#e08aff', emblem: 'chaosstar' },
    apocalypse_raiment:   { pal: { a: '#5a2a2a', b: '#1c1014', shine: 0.4 }, accent: '#e0402a', emblem: 'horsemen' },
    frostlords_mantle:    { pal: { a: '#cfe8ff', b: '#5a82c0', shine: 0.85 }, accent: '#bfe2ff', emblem: 'snowflake' },
  };

  function shapeFor(info) {
    const n = (info.name || '').toLowerCase();
    let t = info.type || info.item_type || 'other';
    if (t === 'other' || !t) {
      // text-only contexts (loot toast lines) still deserve real art
      if (/sword|blade|dagger|axe|mace|hammer|club|bow|spear|whip|staff/.test(n)) t = 'weapon';
      else if (/helm|armor|mail|plate|shield|boot|glove|cloak|belt|ring|amulet|bracer|legging/.test(n)) t = 'armor';
      else if (/potion|elixir|vial/.test(n)) t = 'potion';
      else if (/scroll/.test(n)) t = 'scroll';
      else if (/coin|gold/.test(n)) t = 'money';
      else if (/bread|meat|food|apple|cheese/.test(n)) t = 'food';
      else if (/key\b/.test(n)) t = 'key';
      else if (/bag|sack|chest|pouch/.test(n)) t = 'container';
    }
    const slot = (info.slot || '').toLowerCase();
    if (t === 'weapon') {
      if (/dagger|knife|dirk|stiletto|shiv/.test(n)) return 'dagger';
      if (/axe|cleaver|hatchet/.test(n)) return 'axe';
      if (/mace|hammer|club|morningstar|maul|flail/.test(n)) return 'mace';
      if (/bow|crossbow/.test(n)) return 'bow';
      if (/spear|lance|pike|polearm|halberd|trident/.test(n)) return 'spear';
      if (/whip|lash/.test(n)) return 'whip';
      if (/staff|quarterstaff/.test(n)) return 'staff';
      return 'sword';
    }
    if (t === 'armor' || t === 'worn') {
      if (slot === 'head' || /helm|cap|crown|hood/.test(n)) return 'helm';
      if (slot === 'feet' || /boot|sandal|shoe/.test(n)) return 'boots';
      if (slot === 'hands' || /glove|gauntlet|mitt/.test(n)) return 'gauntlets';
      if (slot === 'legs' || /legging|greave|pant/.test(n)) return 'leggings';
      if (slot === 'shield' || /shield|buckler/.test(n)) return 'shield';
      if (slot === 'about' || /cloak|cape|mantle/.test(n)) return 'cloak';
      if (slot === 'waist' || /belt|girdle|sash/.test(n)) return 'belt';
      if (slot === 'finger' || /ring|band\b/.test(n)) return 'ring';
      if (slot === 'neck' || /amulet|necklace|pendant|medallion|talisman/.test(n)) return 'amulet';
      if (slot === 'wrist' || slot === 'arms' || /bracer|bracelet|sleeve/.test(n)) return 'bracer';
      return 'cuirass';
    }
    return {
      potion: 'potion', scroll: 'scroll', wand: 'wand', staff: 'staff',
      container: /chest|coffer|strongbox/.test(n) ? 'chest' : 'bag',
      note: 'note', drink: 'waterskin', key: 'key', food: 'food',
      money: 'coins', treasure: 'gem', light: 'torch', boat: 'boat',
    }[t] || 'sundries';
  }

  function hexToRgb(h) {
    const m = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(h || '');
    return m ? [parseInt(m[1], 16), parseInt(m[2], 16), parseInt(m[3], 16)] : [255, 255, 255];
  }

  const cache = new Map();
  function draw(ctx, info, size) {
    const setTheme = info.set_key && SET_THEMES[info.set_key];
    const isHigh = info.rarity === 'legendary' || info.rarity === 'epic' || info.set_id || info.set_key;
    // set pieces take their set palette; otherwise legendary/epic take a
    // class signature; everything else gets a material from its name
    const cls = (isHigh && !setTheme) ? classFor(info) : null;
    const mat = setTheme ? setTheme.pal
      : (cls && (info.rarity === 'legendary' || info.set_id)) ? CLASS_SIG[cls]
      : matFor(info.name, info.type || info.item_type);
    ctx.save();
    ctx.scale(size / 22, size / 22);
    // rarity / set backplate + border
    const rc = setTheme ? setTheme.accent : info.set_id ? '#4ad0c0' : RARITY[info.rarity || 'common'];
    ctx.fillStyle = 'rgba(12,14,22,.85)';
    ctx.beginPath(); ctx.roundRect ? ctx.roundRect(0.6, 0.6, 20.8, 20.8, 3) : ctx.rect(0.6, 0.6, 20.8, 20.8); ctx.fill();
    // set pieces get a tinted inner wash so the suit reads at a glance
    if (setTheme) {
      const [r, g, bl] = hexToRgb(setTheme.accent);
      const gr = ctx.createRadialGradient(11, 10, 2, 11, 11, 12);
      gr.addColorStop(0, `rgba(${r},${g},${bl},.20)`); gr.addColorStop(1, `rgba(${r},${g},${bl},0)`);
      ctx.fillStyle = gr; ctx.fillRect(1, 1, 20, 20);
    }
    if (rc) {
      ctx.strokeStyle = rc; ctx.lineWidth = setTheme ? 1.4 : 1.1;
      ctx.beginPath(); ctx.roundRect ? ctx.roundRect(0.9, 0.9, 20.2, 20.2, 2.6) : ctx.rect(0.9, 0.9, 20.2, 20.2); ctx.stroke();
      if (info.rarity === 'legendary' && !setTheme) {
        const g = ctx.createRadialGradient(11, 11, 3, 11, 11, 11);
        g.addColorStop(0, 'rgba(255,168,56,.22)'); g.addColorStop(1, 'rgba(255,168,56,0)');
        ctx.fillStyle = g; ctx.fillRect(1, 1, 20, 20);
      }
    }
    (SHAPES[shapeFor(info)] || SHAPES.sundries)(ctx, mat);
    // emblem: set sigil for set pieces, else class motif for legendary
    if (setTheme) {
      (SET_EMBLEMS[setTheme.emblem] || (() => {}))(ctx, setTheme.accent);
    } else if (cls && (info.rarity === 'legendary' || info.set_id)) {
      (MOTIFS[CLASS_SIG[cls].motif] || MOTIFS.chevron)(ctx, CLASS_SIG[cls].a);
    }
    ctx.restore();
  }

  MH.itemIcons = {
    classFor,
    // a cached Phaser texture for world/ground use
    textureKey(scene, info) {
      const key = 'icon_' + [shapeFor(info), info.rarity || 'c', info.set_key || (info.set_id ? 's' : ''),
        (info.name || '').toLowerCase().replace(/[^a-z]+/g, '').slice(0, 24)].join('_');
      if (!scene.textures.exists(key)) {
        const c = document.createElement('canvas');
        c.width = c.height = S;
        draw(c.getContext('2d'), info, S);
        scene.textures.addCanvas(key, c);
      }
      return key;
    },
    // draw into a DOM canvas (inventory, equipment, loot panels)
    intoCanvas(canvas, info) {
      const size = canvas.width;
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, size, size);
      draw(ctx, info, size);
    },
  };
})();
