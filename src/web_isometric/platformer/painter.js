// Misthollow painterly ground renderer — Phase 1 of the graphics overhaul.
// Instead of a grid of repeating 16px tiles, each room gets ONE soft-brushed
// PAINTING: a biome color wash, hand-mottled variation, floor-kind brush
// strokes (grass blades, cobbles, marble veins, sand ripples...), soft-edged
// water with foam shorelines, worn dirt paths running to the exits, and
// ambient-occlusion shadow where the floor meets walls. Deterministic per
// room (seeded by vnum) so a room always looks like itself.
//
// Atmosphere pass (gauntlet dry-01): the painting also carries the room's
// LIGHT. Open-sky biomes get sun shadows thrown by the treeline/walls and
// dappled canopy light; enclosed biomes (caves, dungeons, halls) get a dark
// vignette with warm pools baked under every wall torch the scene will hang,
// pale daylight spilling in at the exits and a hearth pool at the centre.
// Sectors can overrule zone looks (a cave in a forest zone paints as a cave,
// a swimmable room paints as clear shallow water over sand).
//
// Mass pass (gauntlet graphics-01): organic borders — treelines, rock faces,
// dune ridges, coral reefs — are painted INTO the picture as one continuous
// jittered mass (themes-zones leaves their tile sprites transparent), so the
// edge of a forest room is a canopy and a cave wall is rock, not a 16px
// stamp repeated round the room. Paths wander instead of running straight.
(() => {
  const MH = window.MH = window.MH || {};
  const SS = 2;   // supersample over the 16px tile grid (crisp at camera zoom)

  // ---- tiny color kit ------------------------------------------------------
  function rgb(hex) {
    const h = hex.replace('#', '');
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }
  function css([r, g, b], a = 1) { return `rgba(${r | 0},${g | 0},${b | 0},${a})`; }
  function mix(a, b, t) { return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; }
  function shade(c, f) { return [c[0] * f, c[1] * f, c[2] * f].map(v => Math.max(0, Math.min(255, v))); }

  // fallback palettes when a room has no zone theme (generic sectors)
  const SECTOR_FLOOR = {
    forest: ['#4c8438', '#3e7030', 'grass'], field: ['#6a9a44', '#5c8a3c', 'grass'],
    hills: ['#6c8a44', '#5e7a3c', 'grass'], swamp: ['#4e5838', '#424a2e', 'slimestone'],
    desert: ['#d4b478', '#c4a468', 'sand'], mountain: ['#7a7e88', '#6c7078', 'cracked'],
    cave: ['#4a3a2c', '#3a2d22', 'cracked'], dungeon: ['#56525c', '#4a4650', 'flagstone'],
    underground: ['#4a3a2c', '#3a2d22', 'cracked'], inside: ['#7a6650', '#6c5a46', 'flagstone'],
    city: ['#8d7d66', '#7b6c57', 'cobble'], water_swim: ['#c8b88c', '#b8a87c', 'shallows'],
    underwater: ['#7a9a8c', '#6a8a7c', 'shallows'], water_noswim: ['#6a9a44', '#5c8a3c', 'grass'],
    default: ['#5c7a44', '#50693c', 'grass'],
  };
  // light model per generic sector (zone themes carry their own `light`)
  const SECTOR_LIGHT = {
    cave: { enclosed: true, vig: 0.78, vigCol: '#060302', pool: '#ffa850' },
    underground: { enclosed: true, vig: 0.78, vigCol: '#060302', pool: '#ffa850' },
    dungeon: { enclosed: true, vig: 0.58, vigCol: '#06050a', pool: '#ffb468' },
    inside: { enclosed: true, vig: 0.42, vigCol: '#0a0810', pool: '#ffc888' },
    city: { enclosed: false, vig: 0.10, vigCol: '#2a1a08', pool: '#fff4d0', dapple: false },
    desert: { enclosed: false, vig: 0.08, vigCol: '#2a1a08', pool: '#fff4d0', dapple: false },
    mountain: { enclosed: false, vig: 0.18, vigCol: '#101820', pool: '#fff4d0', dapple: false },
    water_swim: { enclosed: false, vig: 0.14, vigCol: '#062838', pool: '#c0f8ff', dapple: false },
    underwater: { enclosed: false, vig: 0.5, vigCol: '#041828', pool: '#a0e8ff', dapple: false },
    default: { enclosed: false, vig: 0.16, vigCol: '#0c1410', pool: '#fff0c0', dapple: true },
  };

  // The scene hangs wall torches with this exact walk (decorateWalls); we
  // replay it so the baked light pools sit under the real torches.
  const WALL_SETS = {
    city: ['wd_banner', 'wd_torch', 'wd_vine'], inside: ['wd_banner', 'wd_torch'],
    cave: ['wd_torch', 'wd_moss'], dungeon: ['wd_torch', 'wd_banner'], underground: ['wd_torch', 'wd_moss'],
    mountain: ['wd_moss'], forest: ['wd_vine', 'wd_moss'], swamp: ['wd_vine', 'wd_moss'],
    field: ['wd_vine'], hills: ['wd_moss'], desert: [], default: ['wd_moss'],
  };
  function wallTorches(layout, th, BLOCK, FLOOR) {
    const gfx = MH.gfx || {};
    if (gfx.quality === 'low') return [];
    const set = WALL_SETS[th] || WALL_SETS.default;
    if (!set.length) return [];
    const rng = MH.mulberry32((layout.vnum ^ 0x4d2b9) >>> 0);
    const grid = layout.grid, W = layout.W, H = layout.H;
    const dens = gfx.quality === 'medium' ? 0.12 : 0.18;
    const out = [];
    let placed = 0;
    for (let y = 0; y < H - 1 && placed < 16; y++) {
      for (let x = 1; x < W - 1 && placed < 16; x++) {
        if (grid[y * W + x] !== BLOCK || grid[(y + 1) * W + x] !== FLOOR) continue;
        if (rng() > dens) continue;
        const name = set[(rng() * set.length) | 0];
        if (name === 'wd_torch') out.push({ x: x + 0.5, y: y + 0.96 - 0.5 });   // in cells
        placed++;
      }
    }
    return out;
  }

  // border kinds whose tile sprites are transparent: the painter owns them
  const PAINTED_KINDS = MH.PAINTED_BORDER_KINDS || ['tree', 'pine', 'deadtree', 'hedge', 'rock', 'dune', 'coral'];
  const CANOPY_KINDS = ['tree', 'pine', 'deadtree', 'hedge'];

  // ---- the painting --------------------------------------------------------
  function paint(scene, layout, th) {
    const TD = MH.TD;
    if (!TD) return null;
    const { T, FLOOR, BLOCK, WATER } = TD;
    const W = layout.W, H = layout.H, grid = layout.grid;
    const key = `paint_${layout.vnum}`;
    if (scene.textures.exists(key)) scene.textures.remove(key);
    const cw = W * T * SS, ch = H * T * SS, cell = T * SS;
    const cv = document.createElement('canvas');
    cv.width = cw; cv.height = ch;
    const ctx = cv.getContext('2d');
    const rng = MH.mulberry32((layout.vnum ^ 0x9e3779b9) >>> 0);

    const zt0 = layout.zoneKey && MH.ZONE_THEMES ? MH.ZONE_THEMES[layout.zoneKey] : null;
    const zt = MH.roomPalette ? MH.roomPalette(zt0, th) : zt0;
    const fall = SECTOR_FLOOR[th] || SECTOR_FLOOR.default;
    const base = rgb(zt ? zt.floor : fall[0]);
    const base2 = rgb(zt ? (zt.f2 || zt.floor) : fall[1]);
    const acc = rgb(zt ? zt.acc : '#e8e0a0');
    const kind = zt ? (zt.floorKind || fall[2]) : fall[2];
    const waterCol = rgb((zt && zt.water) || (MH.THEMES && MH.THEMES[th] && MH.THEMES[th].liquid) || '#3a8ad0');
    const light = (zt && zt.light) || SECTOR_LIGHT[th] || SECTOR_LIGHT.default;
    const enclosed = !!light.enclosed || !!layout.dark;
    const poolCol = rgb(light.pool || '#fff0c0');
    const vigCol = rgb(light.vigCol || '#0a0810');
    // which block mass (if any) this painting owns: the ZONE decides whether
    // the tile sprites are transparent, the resolved palette decides the look
    // (a cave sector inside a forest zone paints rock where the trees would be)
    const zoneOrganic = !!(zt0 && PAINTED_KINDS.includes(zt0.borderKind));
    const massKind = zoneOrganic ? ((zt && zt.borderKind) || 'rock') : null;
    const borderCol = rgb((zt && zt.borderCol) || (zt0 && zt0.borderCol) || '#4a4a4a');

    const at = (x, y) => (x < 0 || y < 0 || x >= W || y >= H) ? BLOCK : grid[y * W + x];
    const blocks = [];
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (grid[y * W + x] === BLOCK) blocks.push([x, y]);
    const jit = amt => (rng() - 0.5) * amt * cell;
    const softDisc = (x, y, r, col, a0, a1 = 0) => {
      const gg = ctx.createRadialGradient(x, y, 0, x, y, r);
      gg.addColorStop(0, css(col, a0));
      gg.addColorStop(1, css(col, a1));
      ctx.fillStyle = gg;
      ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill();
    };

    // 1) base wash: soft radial center-light over a two-tone ground
    let g = ctx.createRadialGradient(cw / 2, ch / 2, 40, cw / 2, ch / 2, Math.max(cw, ch) * 0.72);
    g.addColorStop(0, css(mix(base, [255, 255, 255], enclosed ? 0.04 : 0.08)));
    g.addColorStop(1, css(base2));
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, cw, ch);
    // sun direction: warm light from the top-left, cool shade bottom-right
    g = ctx.createLinearGradient(0, 0, cw, ch);
    g.addColorStop(0, enclosed ? 'rgba(255,220,180,0.03)' : 'rgba(255,240,200,0.07)');
    g.addColorStop(0.5, 'rgba(255,240,200,0)');
    g.addColorStop(1, enclosed ? 'rgba(4,4,12,0.10)' : 'rgba(10,20,40,0.07)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, cw, ch);

    // 2) mottling: big soft color blotches (the hand-painted unevenness)
    const blotchCols = [shade(base, 0.84), shade(base, 1.14), mix(base, acc, 0.16), mix(base, base2, 0.5)];
    for (let i = 0; i < 260; i++) {
      const x = rng() * cw, y = rng() * ch, r = (14 + rng() * 50) * SS * 0.75;
      const c = blotchCols[(rng() * blotchCols.length) | 0];
      softDisc(x, y, r, c, 0.06 + rng() * 0.06);
    }

    // 3) worn path to each exit gap (painted UNDER the strokes so it melts in)
    if (layout.gaps && (kind === 'grass' || kind === 'sand' || kind === 'slimestone' || kind === 'snow')) {
      // a real dirt road: it WANDERS between the room's heart and each exit
      // (BrowserQuest's brown paths snake through the green; a straight cross
      // reads as a grid line), with a darker worn edge and a paler trodden core
      const dirt = kind === 'sand' ? shade(base, 0.84) : kind === 'snow' ? mix(base, rgb('#8a8070'), 0.45)
        : kind === 'slimestone' ? mix(base, rgb('#5a4a30'), 0.6) : mix(base, rgb('#7a5632'), 0.8);
      const edgeCol = shade(dirt, 0.74), core = mix(dirt, rgb('#c8a878'), 0.3);
      const cx = cw / 2, cy = ch / 2;
      const ends = [];
      if (layout.gaps.north) ends.push([cx, 0]);
      if (layout.gaps.south) ends.push([cx, ch]);
      if (layout.gaps.west) ends.push([0, cy]);
      if (layout.gaps.east) ends.push([cw, cy]);
      ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      const wobble = (ex, ey, amp) => {
        // polyline centre -> exit with perpendicular wander that dies at the exit
        const pts = [[cx, cy]];
        const dx = ex - cx, dy = ey - cy, len = Math.hypot(dx, dy);
        const nx = -dy / len, ny = dx / len;
        const N = 5;
        for (let i = 1; i < N; i++) {
          const t = i / N, fade = Math.sin(t * Math.PI);
          const off = (rng() - 0.5) * 2 * amp * fade;
          pts.push([cx + dx * t + nx * off, cy + dy * t + ny * off]);
        }
        pts.push([ex, ey]);
        return pts;
      };
      const strokePath = (pts, col, a, w) => {
        ctx.strokeStyle = css(col, a); ctx.lineWidth = w;
        ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
        for (let i = 1; i < pts.length - 1; i++) {
          const mx = (pts[i][0] + pts[i + 1][0]) / 2, my = (pts[i][1] + pts[i + 1][1]) / 2;
          ctx.quadraticCurveTo(pts[i][0], pts[i][1], mx, my);
        }
        ctx.lineTo(pts[pts.length - 1][0], pts[pts.length - 1][1]);
        ctx.stroke();
      };
      const roads = ends.map(([ex, ey]) => wobble(ex, ey, cell * 1.1));
      for (const pts of roads) strokePath(pts, edgeCol, 0.34, cell * 2.0);   // soft worn verge
      for (const pts of roads) strokePath(pts, dirt, 0.72, cell * 1.45);     // the road
      for (const pts of roads) strokePath(pts, core, 0.38, cell * 0.7);      // trodden core
      // ruts and pebbles along the way
      for (const pts of roads) for (let i = 0; i < 30; i++) {
        const p = pts[1 + ((rng() * (pts.length - 2)) | 0)], q = pts[(rng() * pts.length) | 0];
        const t = rng(), x = p[0] + (q[0] - p[0]) * t + jit(0.9), y = p[1] + (q[1] - p[1]) * t + jit(0.9);
        ctx.fillStyle = css(rng() < 0.5 ? shade(dirt, 0.7) : mix(dirt, [255, 255, 255], 0.3), 0.4);
        ctx.beginPath(); ctx.arc(x, y, (0.6 + rng()) * SS, 0, 6.283); ctx.fill();
      }
      // trodden centre where the paths meet
      if (ends.length) softDisc(cx, cy, cell * 2.2, dirt, 0.55);
    } else if (layout.gaps && (kind === 'cobble' || kind === 'flagstone' || kind === 'marble' || kind === 'bone')) {
      // worn lighter track over stone
      const wear = mix(base, [255, 255, 255], 0.12);
      const cx = cw / 2, cy = ch / 2;
      ctx.lineCap = 'round';
      for (const [gk, ex, ey] of [['north', cx, 0], ['south', cx, ch], ['west', 0, cy], ['east', cw, cy]]) {
        if (!layout.gaps[gk]) continue;
        ctx.strokeStyle = css(wear, 0.12);
        ctx.lineWidth = 14 * SS * 0.6;
        ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(ex, ey); ctx.stroke();
      }
    }

    // 4) floor-kind brushwork
    if (kind === 'grass') {
      const dk = shade(base, 0.68), lt = mix(shade(base, 1.28), acc, 0.2);
      // meadow patches: sunlit lighter sweeps and shaded darker hollows so the
      // green is a field with shape, not one flat fill
      for (let i = 0; i < 12; i++) softDisc(rng() * cw, rng() * ch, cell * (1.6 + rng() * 2.2), mix(shade(base, 1.2), acc, 0.35), 0.16 + rng() * 0.1);
      for (let i = 0; i < 9; i++) softDisc(rng() * cw, rng() * ch, cell * (1.4 + rng() * 2.0), shade(base, 0.74), 0.16 + rng() * 0.1);
      for (let i = 0; i < 1900; i++) {
        const x = rng() * cw, y = rng() * ch;
        const len = (3 + rng() * 7) * SS, ang = -1.35 + (rng() - 0.5) * 0.8;
        ctx.strokeStyle = css(rng() < 0.5 ? dk : lt, 0.11 + rng() * 0.10);
        ctx.lineWidth = SS * (0.7 + rng() * 0.8);
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + Math.cos(ang) * len, y + Math.sin(ang) * len);
        ctx.stroke();
      }
      // clover / wildflower flecks
      for (let i = 0; i < 70; i++) {
        const x = rng() * cw, y = rng() * ch;
        const fc = rng() < 0.7 ? mix(acc, [255, 255, 255], 0.3) : (rng() < 0.5 ? [240, 200, 90] : [230, 160, 190]);
        ctx.fillStyle = css(fc, 0.35 + rng() * 0.3);
        ctx.beginPath(); ctx.arc(x, y, (0.8 + rng() * 0.9) * SS, 0, 6.283); ctx.fill();
      }
    } else if (kind === 'cobble' || kind === 'flagstone') {
      // irregular slabs: jittered sizes, rotation and tone — no two rows line up
      const seam = shade(base2, 0.62);
      const step = kind === 'cobble' ? 11 * SS : 17 * SS;
      for (let yy = -step; yy < ch + step; yy += step * (0.85 + rng() * 0.3)) {
        const rowOff = rng() * step;
        for (let xx = -step; xx < cw + step; xx += step * (0.8 + rng() * 0.4)) {
          const px = xx + rowOff + (rng() - 0.5) * 4 * SS, py = yy + (rng() - 0.5) * 4 * SS;
          const w = step * (0.7 + rng() * 0.45), h = step * (0.6 + rng() * 0.4);
          const lum = 0.8 + rng() * 0.38;
          ctx.save();
          ctx.translate(px + w / 2, py + h / 2);
          ctx.rotate((rng() - 0.5) * 0.18);
          ctx.fillStyle = css(mix(shade(base, lum), acc, rng() * 0.08), 0.26);
          ctx.beginPath();
          if (ctx.roundRect) ctx.roundRect(-w / 2, -h / 2, w, h, 3.5 * SS); else ctx.rect(-w / 2, -h / 2, w, h);
          ctx.fill();
          ctx.strokeStyle = css(seam, 0.22);
          ctx.lineWidth = SS * 0.9;
          ctx.stroke();
          ctx.restore();
        }
      }
    } else if (kind === 'marble') {
      // polish sheen + wandering pale veins
      for (let i = 0; i < 10; i++) {
        const x = rng() * cw, y = rng() * ch, r = (30 + rng() * 60) * SS;
        softDisc(x, y, r, [255, 255, 255], 0.08);
      }
      ctx.lineWidth = SS * 0.7;
      for (let i = 0; i < 14; i++) {
        let x = rng() * cw, y = rng() * ch;
        ctx.strokeStyle = `rgba(255,255,255,${0.05 + rng() * 0.05})`;
        ctx.beginPath(); ctx.moveTo(x, y);
        for (let s2 = 0; s2 < 6; s2++) { x += (rng() - 0.3) * 40 * SS; y += (rng() - 0.5) * 26 * SS; ctx.lineTo(x, y); }
        ctx.stroke();
      }
    } else if (kind === 'sand') {
      const dk = shade(base, 0.84);
      ctx.lineWidth = SS;
      for (let i = 0; i < 140; i++) {
        const y = rng() * ch, x = rng() * cw, len = (20 + rng() * 60) * SS;
        ctx.strokeStyle = css(dk, 0.10 + rng() * 0.08);
        ctx.beginPath(); ctx.moveTo(x, y);
        ctx.quadraticCurveTo(x + len / 2, y + (rng() - 0.5) * 8 * SS, x + len, y + (rng() - 0.5) * 4 * SS);
        ctx.stroke();
      }
    } else if (kind === 'slimestone') {
      for (let i = 0; i < 90; i++) {
        const x = rng() * cw, y = rng() * ch, r = (5 + rng() * 16) * SS;
        const slick = rng() < 0.4;
        softDisc(x, y, r, slick ? [190, 230, 170] : shade(base, 0.7), slick ? 0.09 : 0.14);
      }
    } else if (kind === 'cracked') {
      // rock floor: fissures, rubble flecks and a few darker slabs
      for (let i = 0; i < 40; i++) softDisc(rng() * cw, rng() * ch, (8 + rng() * 22) * SS, shade(base, 0.7), 0.16);
      ctx.lineWidth = SS * 0.9;
      for (let i = 0; i < 22; i++) {
        let x = rng() * cw, y = rng() * ch;
        ctx.strokeStyle = css(shade(base, 0.5), 0.26);
        ctx.beginPath(); ctx.moveTo(x, y);
        for (let s2 = 0; s2 < 4; s2++) { x += (rng() - 0.5) * 34 * SS; y += (rng() - 0.5) * 34 * SS; ctx.lineTo(x, y); }
        ctx.stroke();
      }
      for (let i = 0; i < 120; i++) {
        ctx.fillStyle = css(rng() < 0.5 ? shade(base, 1.35) : shade(base, 0.55), 0.3);
        ctx.beginPath(); ctx.arc(rng() * cw, rng() * ch, (0.8 + rng() * 1.4) * SS, 0, 6.283); ctx.fill();
      }
    } else if (kind === 'bone') {
      // bone mosaic: long pale bones and knuckles set in cold grey grout
      const grout = shade(base2, 0.78);
      for (let i = 0; i < 60; i++) softDisc(rng() * cw, rng() * ch, (8 + rng() * 20) * SS, grout, 0.16);
      const pale = mix(acc, [255, 255, 255], 0.2), dim = shade(base, 0.9);
      ctx.lineCap = 'round';
      for (let i = 0; i < 260; i++) {
        const x = rng() * cw, y = rng() * ch, len = (5 + rng() * 12) * SS, ang = rng() * 6.283;
        ctx.strokeStyle = css(rng() < 0.6 ? pale : dim, 0.22 + rng() * 0.18);
        ctx.lineWidth = SS * (1.6 + rng() * 1.4);
        ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + Math.cos(ang) * len, y + Math.sin(ang) * len); ctx.stroke();
      }
      // skulls: pale discs with two dark sockets, scattered sparsely
      for (let i = 0; i < 26; i++) {
        const x = rng() * cw, y = rng() * ch, r = (2.4 + rng() * 1.6) * SS;
        ctx.fillStyle = css(pale, 0.55); ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill();
        ctx.fillStyle = 'rgba(30,30,40,0.5)';
        ctx.beginPath(); ctx.arc(x - r * 0.35, y - r * 0.1, r * 0.22, 0, 6.283); ctx.arc(x + r * 0.35, y - r * 0.1, r * 0.22, 0, 6.283); ctx.fill();
      }
      // cold cast over the whole mosaic
      ctx.fillStyle = 'rgba(150,180,210,0.07)'; ctx.fillRect(0, 0, cw, ch);
    } else if (kind === 'snow') {
      ctx.fillStyle = 'rgba(240,246,255,0.18)'; ctx.fillRect(0, 0, cw, ch);
      for (let i = 0; i < 160; i++) softDisc(rng() * cw, rng() * ch, (5 + rng() * 20) * SS, [250, 253, 255], 0.12 + rng() * 0.12);
      for (let i = 0; i < 80; i++) softDisc(rng() * cw, rng() * ch, (6 + rng() * 18) * SS, [120, 145, 190], 0.08 + rng() * 0.06);
    } else if (kind === 'runic') {
      const ink = mix(acc, [255, 255, 255], 0.1);
      ctx.lineWidth = SS * 0.9;
      for (let i = 0; i < 9; i++) {
        const x = rng() * cw, y = rng() * ch, r = (12 + rng() * 26) * SS;
        ctx.strokeStyle = css(ink, 0.10 + rng() * 0.08);
        ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.stroke();
        ctx.beginPath(); ctx.arc(x, y, r * 0.7, 0, 6.283); ctx.stroke();
        for (let k = 0; k < 5; k++) { const a = k * 1.2566 - 1.57; ctx.beginPath(); ctx.moveTo(x + Math.cos(a) * r * 0.7, y + Math.sin(a) * r * 0.7); ctx.lineTo(x + Math.cos(a + 2.513) * r * 0.7, y + Math.sin(a + 2.513) * r * 0.7); ctx.stroke(); }
        softDisc(x, y, r * 1.1, ink, 0.05);
      }
    } else if (kind === 'brass') {
      const step = 16 * SS;
      for (let yy = 0; yy < ch; yy += step) for (let xx = 0; xx < cw; xx += step) {
        ctx.strokeStyle = 'rgba(20,14,8,0.22)'; ctx.lineWidth = SS;
        ctx.strokeRect(xx + SS, yy + SS, step - 2 * SS, step - 2 * SS);
        ctx.fillStyle = 'rgba(255,220,140,0.14)';
        for (const [bx, by] of [[0.15, 0.15], [0.85, 0.15], [0.15, 0.85], [0.85, 0.85]]) { ctx.beginPath(); ctx.arc(xx + step * bx, yy + step * by, 1.2 * SS, 0, 6.283); ctx.fill(); }
      }
    } else if (kind === 'checker') {
      for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
        if ((x + y) % 2) { ctx.fillStyle = css(base2, 0.9); ctx.fillRect(x * cell, y * cell, cell, cell); }
      }
    } else if (kind === 'shallows') {
      // the whole room is clear shallow water over sand: ripples in the sand,
      // then a turquoise water wash that deepens toward the walls, then a
      // caustic light-net dancing on the bottom
      const dk = shade(base, 0.86);
      ctx.lineWidth = SS;
      for (let i = 0; i < 160; i++) {
        const y = rng() * ch, x = rng() * cw, len = (16 + rng() * 50) * SS;
        ctx.strokeStyle = css(dk, 0.12 + rng() * 0.08);
        ctx.beginPath(); ctx.moveTo(x, y);
        ctx.quadraticCurveTo(x + len / 2, y + (rng() - 0.5) * 6 * SS, x + len, y + (rng() - 0.5) * 3 * SS);
        ctx.stroke();
      }
      for (let i = 0; i < 40; i++) softDisc(rng() * cw, rng() * ch, (4 + rng() * 10) * SS, mix(base, [60, 120, 80], 0.5), 0.18);  // weed patches
      const deep = zt && zt.deep;
      // the scene lays its own flat blue swim wash (and a blue colour grade)
      // over the whole room, so the painting has to carry the contrast: a
      // bright sandbar in the middle that stays visible through the wash,
      // saturated turquoise around it, deep blue-black against the reef
      // (the wash colours below are pre-compensated for that overlay: a
      // cream-yellow sandbar, an over-bright cyan mid, a near-black rim —
      // after the scene's blue they land as sand, turquoise and deep blue)
      if (!deep) {
        // (no yellow survives a 35% blue wash — the sandbar is painted as
        // near-white so it lands as pale, sunlit shallows)
        const sandLit = [236, 255, 240];
        softDisc(cw / 2, ch / 2, Math.min(cw, ch) * 0.5, sandLit, 0.85);
        for (let i = 0; i < 6; i++) softDisc(cw * (0.22 + rng() * 0.56), ch * (0.22 + rng() * 0.56), cell * (1.6 + rng() * 2.4), [248, 255, 250], 0.6);
      }
      const midCol = deep ? mix(waterCol, [90, 215, 225], 0.45) : [80, 222, 228];
      const rimCol = deep ? shade(waterCol, 0.4) : [14, 46, 96];
      const wg = ctx.createRadialGradient(cw / 2, ch / 2, Math.min(cw, ch) * 0.06, cw / 2, ch / 2, Math.max(cw, ch) * 0.68);
      wg.addColorStop(0, css(mix(waterCol, [170, 245, 235], 0.65), deep ? 0.55 : 0.04));
      wg.addColorStop(0.4, css(midCol, deep ? 0.8 : 0.5));
      wg.addColorStop(0.72, css(deep ? mix(waterCol, [40, 120, 200], 0.3) : [30, 130, 205], 0.88));
      wg.addColorStop(1, css(rimCol, 0.97));
      ctx.fillStyle = wg; ctx.fillRect(0, 0, cw, ch);
      // deeper water hugs every reef / wall mass
      const deepCol = deep ? shade(waterCol, 0.4) : [10, 40, 90];
      for (const [bx, by] of blocks) {
        if (at(bx, by + 1) !== FLOOR && at(bx, by - 1) !== FLOOR && at(bx + 1, by) !== FLOOR && at(bx - 1, by) !== FLOOR) continue;
        softDisc(bx * cell + cell / 2, by * cell + cell / 2, cell * 2.1, deepCol, 0.5);
      }
      // caustics: a fine bright light-net dancing on the sand (additive, so it
      // still sparkles through the scene's wash)
      ctx.lineCap = 'round';
      ctx.globalCompositeOperation = 'lighter';
      for (let i = 0; i < 320; i++) {
        let x = rng() * cw, y = rng() * ch;
        ctx.strokeStyle = `rgba(235,252,255,${0.14 + rng() * 0.22})`;
        ctx.lineWidth = SS * (0.5 + rng() * 0.7);
        ctx.beginPath(); ctx.moveTo(x, y);
        for (let s2 = 0; s2 < 3; s2++) { x += (rng() - 0.5) * 12 * SS; y += (rng() - 0.5) * 8 * SS; ctx.lineTo(x, y); }
        ctx.stroke();
      }
      // long slow swell lines and surface glints
      ctx.lineWidth = SS * 0.9;
      for (let i = 0; i < 26; i++) {
        const y = rng() * ch, x = rng() * cw, len = (30 + rng() * 90) * SS;
        ctx.strokeStyle = `rgba(220,245,255,${0.10 + rng() * 0.12})`;
        ctx.beginPath(); ctx.moveTo(x, y);
        ctx.quadraticCurveTo(x + len / 2, y + (rng() - 0.5) * 10 * SS, x + len, y + (rng() - 0.5) * 4 * SS);
        ctx.stroke();
      }
      for (let i = 0; i < 110; i++) {
        ctx.strokeStyle = `rgba(255,255,255,${0.16 + rng() * 0.24})`; ctx.lineWidth = SS * 0.8;
        const x = rng() * cw, y = rng() * ch, l = (3 + rng() * 6) * SS;
        ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + l, y - l * 0.15); ctx.stroke();
      }
      ctx.globalCompositeOperation = 'source-over';
    }

    // 4.5) prose accents: the description tints the ground itself
    if (layout.mossy) {
      const moss = mix(base, rgb('#4a7a3a'), 0.6);
      for (let i = 0; i < 110; i++) softDisc(rng() * cw, rng() * ch, (6 + rng() * 22) * SS, moss, 0.10 + rng() * 0.08);
    }
    if (layout.snowy && kind !== 'snow') {
      ctx.fillStyle = 'rgba(235,242,250,0.22)';
      ctx.fillRect(0, 0, cw, ch);
      for (let i = 0; i < 160; i++) softDisc(rng() * cw, rng() * ch, (4 + rng() * 18) * SS, [245, 250, 255], 0.10 + rng() * 0.10);
    }

    // 5) water: clear shallows near the shore, deeper blue away from it,
    // soft painted edges, a wobbling foam line and caustics in the shallows
    let hasWater = false;
    for (let i = 0; i < grid.length; i++) if (grid[i] === WATER) { hasWater = true; break; }
    if (hasWater) {
      // depth = distance (in cells) from the nearest shore cell
      const depth = new Float32Array(W * H).fill(9);
      for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
        if (at(x, y) !== WATER) continue;
        let d = 9;
        for (let dy = -3; dy <= 3; dy++) for (let dx = -3; dx <= 3; dx++) {
          const c = at(x + dx, y + dy);
          if (c !== WATER && c !== BLOCK) d = Math.min(d, Math.max(Math.abs(dx), Math.abs(dy)));
        }
        depth[y * W + x] = d;
      }
      const sandy = mix(base, [255, 240, 200], 0.25);
      const shallow = mix(mix(waterCol, [255, 255, 255], 0.35), sandy, 0.35), deep = shade(waterCol, 0.72);
      // body: overlapping soft discs so the edge is brushed, not stepped
      for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
        if (at(x, y) !== WATER) continue;
        const t = Math.min(1, (depth[y * W + x] - 1) / 2.2);
        const col = mix(shallow, deep, Math.max(0, t));
        const cx0 = x * cell + cell / 2, cy0 = y * cell + cell / 2;
        ctx.fillStyle = css(col, 0.92);
        ctx.fillRect(x * cell, y * cell, cell, cell);
        softDisc(cx0, cy0, cell * 0.95, col, 0.5);
      }
      // shore: a pale wet-sand rim lapping onto the floor side, then foam
      ctx.lineCap = 'round';
      for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
        if (at(x, y) !== WATER) continue;
        const edges = [[0, -1, x * cell, y * cell, (x + 1) * cell, y * cell],
                       [0, 1, x * cell, (y + 1) * cell, (x + 1) * cell, (y + 1) * cell],
                       [-1, 0, x * cell, y * cell, x * cell, (y + 1) * cell],
                       [1, 0, (x + 1) * cell, y * cell, (x + 1) * cell, (y + 1) * cell]];
        for (const [dx, dy, x1, y1, x2, y2] of edges) {
          if (at(x + dx, y + dy) === WATER || at(x + dx, y + dy) === BLOCK) continue;
          // wet sand outside the water line
          ctx.strokeStyle = css(mix(base, [255, 245, 210], 0.35), 0.35);
          ctx.lineWidth = 5 * SS;
          ctx.beginPath(); ctx.moveTo(x1 + dx * 3 * SS, y1 + dy * 3 * SS); ctx.lineTo(x2 + dx * 3 * SS, y2 + dy * 3 * SS); ctx.stroke();
          for (let pass = 0; pass < 2; pass++) {
            ctx.strokeStyle = `rgba(235,248,252,${pass ? 0.18 : 0.42})`;
            ctx.lineWidth = (pass ? 3.5 : 1.8) * SS * 0.8;
            ctx.beginPath();
            const midx = (x1 + x2) / 2 + (rng() - 0.5) * 3 * SS, midy = (y1 + y2) / 2 + (rng() - 0.5) * 3 * SS;
            ctx.moveTo(x1 + (rng() - 0.5) * 2 * SS, y1 + (rng() - 0.5) * 2 * SS);
            ctx.quadraticCurveTo(midx, midy, x2 + (rng() - 0.5) * 2 * SS, y2 + (rng() - 0.5) * 2 * SS);
            ctx.stroke();
          }
        }
        // caustics in the shallows, ripple arcs in open water
        const d = depth[y * W + x];
        if (d <= 2) {
          for (let k = 0; k < 3; k++) {
            let px = x * cell + rng() * cell, py = y * cell + rng() * cell;
            ctx.strokeStyle = `rgba(230,250,255,${0.10 + rng() * 0.14})`;
            ctx.lineWidth = SS * (0.7 + rng());
            ctx.beginPath(); ctx.moveTo(px, py);
            for (let s2 = 0; s2 < 3; s2++) { px += (rng() - 0.5) * 12 * SS; py += (rng() - 0.5) * 8 * SS; ctx.lineTo(px, py); }
            ctx.stroke();
          }
        } else if (rng() < 0.45) {
          ctx.strokeStyle = 'rgba(220,240,250,0.16)';
          ctx.lineWidth = SS * 0.8;
          const rx = x * cell + cell * (0.2 + rng() * 0.6), ry = y * cell + cell * (0.2 + rng() * 0.6);
          ctx.beginPath(); ctx.arc(rx, ry, (2 + rng() * 5) * SS, 0.3, 2.6); ctx.stroke();
        }
      }
    }

    // 5.5) frozen water: an ice sheet where the water used to be (the grid
    // cells were converted to walkable floor; iceCells remembers them)
    if (layout.icy && layout.iceCells && layout.iceCells.length) {
      for (const i of layout.iceCells) {
        const x = (i % W) * cell, y = ((i / W) | 0) * cell;
        ctx.fillStyle = 'rgba(196,222,242,0.88)';
        ctx.fillRect(x, y, cell, cell);
        const gg = ctx.createRadialGradient(x + cell / 2, y + cell / 2, 0, x + cell / 2, y + cell / 2, cell * 0.7);
        gg.addColorStop(0, 'rgba(255,255,255,0.18)');
        gg.addColorStop(1, 'rgba(255,255,255,0)');
        ctx.fillStyle = gg;
        ctx.fillRect(x, y, cell, cell);
      }
      // hairline cracks wandering across the sheet
      ctx.strokeStyle = 'rgba(140,175,205,0.5)';
      ctx.lineWidth = SS * 0.6;
      for (let k = 0; k < Math.max(3, layout.iceCells.length / 4); k++) {
        const i = layout.iceCells[(rng() * layout.iceCells.length) | 0];
        let x = (i % W) * cell + rng() * cell, y = ((i / W) | 0) * cell + rng() * cell;
        ctx.beginPath(); ctx.moveTo(x, y);
        for (let s2 = 0; s2 < 3; s2++) { x += (rng() - 0.5) * cell; y += (rng() - 0.5) * cell; ctx.lineTo(x, y); }
        ctx.stroke();
      }
    }

    // 6) ambient occlusion: floor darkens where it meets walls/obstacles —
    // grounds the wall sprites into the painting
    const AO = (enclosed ? 12 : 7) * SS;
    const aoA = enclosed ? 0.42 : 0.20;
    // (organic masses get round contact shadows in 6.5 instead — straight
    // strips would step along their bumpy outline)
    const rectAO = !massKind || massKind === 'wall';
    for (let y = 0; rectAO && y < H; y++) for (let x = 0; x < W; x++) {
      if (at(x, y) !== FLOOR) continue;
      const px = x * cell, py = y * cell;
      const sides = [[0, -1, px, py, px + cell, py + AO, 'v0'], [0, 1, px, py + cell - AO, px + cell, py + cell, 'v1'],
                     [-1, 0, px, py, px + AO, py + cell, 'h0'], [1, 0, px + cell - AO, py, px + cell, py + cell, 'h1']];
      for (const [dx, dy, x1, y1, x2, y2, dir] of sides) {
        if (at(x + dx, y + dy) !== BLOCK) continue;
        let gg;
        if (dir === 'v0') gg = ctx.createLinearGradient(0, y1, 0, y2);
        else if (dir === 'v1') gg = ctx.createLinearGradient(0, y2, 0, y1);
        else if (dir === 'h0') gg = ctx.createLinearGradient(x1, 0, x2, 0);
        else gg = ctx.createLinearGradient(x2, 0, x1, 0);
        gg.addColorStop(0, `rgba(6,8,14,${aoA})`);
        gg.addColorStop(1, 'rgba(6,8,14,0)');
        ctx.fillStyle = gg;
        ctx.fillRect(x1, y1, x2 - x1, y2 - y1);
      }
    }

    // 6.5) BLOCK MASSES — the painter owns organic borders (see header)
    if (massKind && blocks.length) {
      const lobe = (x, y, r, c0, c1, lit = true) => {
        const gg = lit ? ctx.createRadialGradient(x - r * 0.35, y - r * 0.4, r * 0.08, x, y, r)
          : ctx.createRadialGradient(x, y, 0, x, y, r);
        gg.addColorStop(0, css(c0)); gg.addColorStop(1, css(c1));
        ctx.fillStyle = gg; ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill();
      };
      const lump = (x, y, rx, ry, c0, c1) => {
        const gg = ctx.createRadialGradient(x - rx * 0.3, y - ry * 0.55, 1, x, y, rx * 1.1);
        gg.addColorStop(0, css(c0)); gg.addColorStop(1, css(c1));
        ctx.fillStyle = gg; ctx.beginPath(); ctx.ellipse(x, y, rx, ry, 0, 0, 6.283); ctx.fill();
      };
      const openSide = (x, y) => at(x, y + 1) === FLOOR || at(x, y - 1) === FLOOR || at(x + 1, y) === FLOOR || at(x - 1, y) === FLOOR;
      const centre = ([x, y]) => [x * cell + cell / 2, y * cell + cell / 2];
      if (CANOPY_KINDS.includes(massKind)) {
        const dead = massKind === 'deadtree', pine = massKind === 'pine';
        const lo = dead ? rgb('#1a261e') : pine ? rgb('#163022') : shade(borderCol, 0.48);
        const mid = dead ? rgb('#34463a') : pine ? rgb('#2a583c') : shade(borderCol, 1.0);
        const hi = dead ? rgb('#586a5a') : pine ? rgb('#5a9a6e') : mix(shade(borderCol, 1.55), acc, 0.12);
        const top = dead ? rgb('#7a8c7a') : pine ? rgb('#8ec898') : mix(shade(borderCol, 1.95), [255, 255, 220], 0.18);
        // 1) under-storey silhouette: dark blobs that spill a little past the cells
        for (const b of blocks) {
          const [cx0, cy0] = centre(b);
          ctx.fillStyle = css(lo); ctx.fillRect(b[0] * cell, b[1] * cell, cell, cell);
          for (let k = 0; k < 3; k++) lobe(cx0 + jit(0.7), cy0 + jit(0.7), cell * (0.5 + rng() * 0.22), lo, shade(lo, 0.85), false);
        }
        // 2) crowns lit from the upper-left
        for (const b of blocks) {
          const [cx0, cy0] = centre(b);
          for (let k = 0; k < 2; k++) lobe(cx0 + jit(0.6), cy0 + jit(0.6), cell * (0.36 + rng() * 0.2), mid, lo);
        }
        // 3) sunlit tops, leaf dabs, dark gaps, dead branches
        for (const b of blocks) {
          const [cx0, cy0] = centre(b);
          lobe(cx0 - cell * 0.1 + jit(0.4), cy0 - cell * 0.12 + jit(0.4), cell * (0.22 + rng() * 0.14), top, hi);
          if (rng() < 0.65) lobe(cx0 + jit(0.7), cy0 + jit(0.7), cell * (0.13 + rng() * 0.1), hi, mid);
          if (rng() < 0.5) softDisc(cx0 + jit(0.8), cy0 + jit(0.8), cell * 0.18, lo, 0.75);
          if (dead && rng() < 0.7) {
            ctx.strokeStyle = 'rgba(14,20,16,0.9)'; ctx.lineWidth = SS * 1.1; ctx.lineCap = 'round';
            const bx = cx0 + jit(0.5), by = cy0 + cell * 0.35;
            ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(bx + jit(0.2), by - cell * 0.5);
            ctx.moveTo(bx + jit(0.1), by - cell * 0.25); ctx.lineTo(bx + cell * 0.25 + jit(0.2), by - cell * 0.5); ctx.stroke();
          }
        }
      } else if (massKind === 'rock' || massKind === 'dune') {
        const dune = massKind === 'dune';
        const src = dune ? base : borderCol;
        const lo = dune ? shade(src, 0.7) : shade(src, 0.46), mid = dune ? shade(src, 0.95) : shade(src, 0.98);
        const hi = dune ? shade(src, 1.16) : shade(src, 1.28), top = mix(shade(src, dune ? 1.3 : 1.6), [255, 250, 240], 0.2);
        // 1) silhouette: the cell plus a boulder at every corner, so the edge
        // of the mass is a bumpy ridge rather than a row of squares
        for (const b of blocks) {
          const [cx0, cy0] = centre(b);
          ctx.fillStyle = css(lo); ctx.fillRect(b[0] * cell, b[1] * cell, cell, cell);
          for (const [ox, oy] of [[-0.5, -0.5], [0.5, -0.5], [-0.5, 0.5], [0.5, 0.5], [0, -0.5], [0, 0.5], [-0.5, 0], [0.5, 0]])
            lump(cx0 + ox * cell + jit(0.25), cy0 + oy * cell + jit(0.25), cell * (0.34 + rng() * 0.14), cell * (0.3 + rng() * 0.12), shade(lo, 0.95), shade(lo, 0.72));
        }
        // 2) boulders: mostly mid-dark stone with a lit upper-left face, two
        // per cell so they read as individual rocks rather than a mush
        for (const b of blocks) {
          const [cx0, cy0] = centre(b);
          for (let k = 0; k < 2; k++) {
            const rx = cell * (0.36 + rng() * 0.2), ry = cell * (dune ? 0.2 : 0.28) + rng() * cell * 0.14;
            const x = cx0 + jit(0.7), y = cy0 + jit(0.7);
            lump(x, y, rx, ry, hi, shade(mid, 0.8));
            // crisp rim on the sunward edge
            ctx.strokeStyle = css(top, 0.5); ctx.lineWidth = SS * 0.9;
            ctx.beginPath(); ctx.ellipse(x, y, rx * 0.86, ry * 0.86, 0, 3.4, 5.4); ctx.stroke();
          }
        }
        // 3) cracks and crevices
        for (const b of blocks) {
          const [cx0, cy0] = centre(b);
          if (!dune && rng() < 0.7) {
            ctx.strokeStyle = css(shade(lo, 0.6), 0.8); ctx.lineWidth = SS * 0.9; ctx.lineCap = 'round';
            let x = cx0 + jit(0.6), y = cy0 + jit(0.6);
            ctx.beginPath(); ctx.moveTo(x, y);
            for (let s2 = 0; s2 < 3; s2++) { x += jit(0.6); y += jit(0.6); ctx.lineTo(x, y); }
            ctx.stroke();
          }
          if (rng() < 0.4) softDisc(cx0 + jit(0.7), cy0 + jit(0.7), cell * 0.16, shade(lo, 0.6), 0.7);
          if (dune && rng() < 0.6) {
            ctx.strokeStyle = css(top, 0.35); ctx.lineWidth = SS * 0.8;
            ctx.beginPath(); ctx.moveTo(cx0 - cell * 0.4, cy0 + jit(0.3)); ctx.quadraticCurveTo(cx0, cy0 - cell * 0.25 + jit(0.2), cx0 + cell * 0.45, cy0 + jit(0.3)); ctx.stroke();
          }
        }
      } else if (massKind === 'coral') {
        // (colours are pushed warm and bright on purpose: the scene lays a
        // flat blue swim wash over the whole room and these have to survive it)
        const rLo = rgb('#3c3e38'), rMid = rgb('#8c8870'), rHi = rgb('#d0c8a4'), rTop = rgb('#fff6dc');
        const corals = ['#ff5aa0', '#ff9a58', '#48d0d0', '#ffe070', '#e078f0', '#ffb8d0'].map(rgb);
        // reef rock: a bumpy ridge (a boulder at every corner and edge)
        for (const b of blocks) {
          const [cx0, cy0] = centre(b);
          ctx.fillStyle = css(rLo); ctx.fillRect(b[0] * cell, b[1] * cell, cell, cell);
          for (const [ox, oy] of [[-0.5, -0.5], [0.5, -0.5], [-0.5, 0.5], [0.5, 0.5], [0, -0.5], [0, 0.5], [-0.5, 0], [0.5, 0]])
            lump(cx0 + ox * cell + jit(0.25), cy0 + oy * cell + jit(0.25), cell * (0.34 + rng() * 0.14), cell * (0.3 + rng() * 0.12), shade(rLo, 1.1), shade(rLo, 0.75));
        }
        for (const b of blocks) {
          const [cx0, cy0] = centre(b);
          for (let k = 0; k < 2; k++) {
            const rx = cell * (0.32 + rng() * 0.2), ry = cell * (0.26 + rng() * 0.16), x = cx0 + jit(0.7), y = cy0 + jit(0.7);
            lump(x, y, rx, ry, rHi, rMid);
            ctx.strokeStyle = css(rTop, 0.5); ctx.lineWidth = SS * 0.9;
            ctx.beginPath(); ctx.ellipse(x, y, rx * 0.86, ry * 0.86, 0, 3.4, 5.4); ctx.stroke();
          }
        }
        // coral heads, fans and tube sponges in reef colours
        for (const b of blocks) {
          const [cx0, cy0] = centre(b);
          const n = 2 + ((rng() * 2) | 0);
          for (let k = 0; k < n; k++) {
            const c = corals[(rng() * corals.length) | 0];
            const x = cx0 + jit(0.7), y = cy0 + jit(0.7), r = cell * (0.1 + rng() * 0.12);
            if (rng() < 0.65) lobe(x, y, r, mix(c, [255, 255, 255], 0.35), c);
            else {  // tube sponge / sea fan
              ctx.strokeStyle = css(c, 0.95); ctx.lineWidth = SS * (1.2 + rng()); ctx.lineCap = 'round';
              ctx.beginPath(); ctx.moveTo(x, y + r); ctx.lineTo(x + jit(0.15), y - r * 1.3);
              ctx.moveTo(x, y + r * 0.2); ctx.lineTo(x + r * 0.9, y - r * 0.9); ctx.stroke();
            }
          }
        }
        // foam where the swell breaks on the reef (the scene's own swim wash
        // already sinks the reef under water)
        // — as scattered breaking-wave dabs and short arcs just off the reef,
        // never a line traced along the cell edge (that draws the grid)
        ctx.lineCap = 'round';
        for (const [bx, by] of blocks) {
          for (const [dx, dy] of [[0, 1], [0, -1], [1, 0], [-1, 0]]) {
            if (at(bx + dx, by + dy) !== FLOOR) continue;
            const ex = bx * cell + cell / 2 + dx * cell * 0.62, ey = by * cell + cell / 2 + dy * cell * 0.62;
            const n = 2 + ((rng() * 2) | 0);
            for (let k = 0; k < n; k++) {
              const x = ex + (dy !== 0 ? jit(0.9) : jit(0.25)), y = ey + (dx !== 0 ? jit(0.9) : jit(0.25));
              softDisc(x, y, cell * (0.12 + rng() * 0.12), [240, 250, 255], 0.55);
              ctx.strokeStyle = `rgba(245,252,255,${0.3 + rng() * 0.3})`; ctx.lineWidth = SS * (0.7 + rng() * 0.6);
              const a0 = rng() * 6.283;
              ctx.beginPath(); ctx.arc(x, y, cell * (0.1 + rng() * 0.14), a0, a0 + 1.4 + rng()); ctx.stroke();
            }
          }
        }
      } else {
        // 'wall' (a dungeon / indoor sector inside an organic zone): running-
        // bond masonry laid on a world grid so courses run across every cell
        const mortar = shade(borderCol, 0.5), brick = borderCol;
        const bw = cell / 2, bh = cell / 2;
        const tone = (k, c) => 0.86 + ((((k * 73856093) ^ (c * 19349663)) >>> 0) % 1000) / 1000 * 0.3;
        for (const b of blocks) {
          const px = b[0] * cell, py = b[1] * cell;
          ctx.save(); ctx.beginPath(); ctx.rect(px, py, cell, cell); ctx.clip();
          ctx.fillStyle = css(mortar); ctx.fillRect(px, py, cell, cell);
          for (let c = (py / bh) | 0; c <= ((py + cell) / bh | 0); c++) {
            const off = c % 2 ? bw / 2 : 0;
            for (let k = ((px - off) / bw | 0) - 1; k <= ((px + cell - off) / bw | 0); k++) {
              const x = k * bw + off, y = c * bh;
              const gg = ctx.createLinearGradient(0, y, 0, y + bh);
              const t = tone(k, c);
              gg.addColorStop(0, css(shade(brick, 1.25 * t))); gg.addColorStop(1, css(shade(brick, 0.92 * t)));
              ctx.fillStyle = gg;
              ctx.beginPath();
              if (ctx.roundRect) ctx.roundRect(x + SS * 0.6, y + SS * 0.6, bw - SS * 1.2, bh - SS * 1.2, SS); else ctx.rect(x + SS * 0.6, y + SS * 0.6, bw - SS * 1.2, bh - SS * 1.2);
              ctx.fill();
            }
          }
          ctx.restore();
        }
      }
      // every mass darkens the floor it meets: a soft round contact shadow
      // (this replaces the straight-edged AO strips, which stepped along an
      // organic outline), stronger below/right where the sun cannot reach
      for (const [bx, by] of blocks) {
        if (!openSide(bx, by)) continue;
        softDisc(bx * cell + cell * 0.5, by * cell + cell * 0.5, cell * 1.35, [6, 8, 14], enclosed ? 0.5 : 0.3);
        softDisc(bx * cell + cell * 0.75, by * cell + cell * 0.8, cell * 1.0, [6, 8, 14], enclosed ? 0.3 : 0.2);
      }
    }

    // 7) LIGHT — the pass that makes the room a lit place, not a flat field
    if (!enclosed) {
      // 7a) sun from the upper-left: every block (treeline, wall, boulder)
      // throws a soft shadow down and to the right onto the floor
      const sh = [8, 12, 22];
      const canopy = massKind && CANOPY_KINDS.includes(massKind);
      const shR = canopy ? 1.35 : 1.05;
      for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
        if (at(x, y) !== BLOCK) continue;
        // only blocks with open floor below/right matter
        if (at(x, y + 1) !== FLOOR && at(x + 1, y) !== FLOOR && at(x + 1, y + 1) !== FLOOR) continue;
        const cx0 = x * cell + cell * 0.85, cy0 = y * cell + cell * 0.95;
        const gg = ctx.createRadialGradient(cx0, cy0, cell * 0.1, cx0, cy0, cell * shR);
        gg.addColorStop(0, css(sh, canopy ? 0.36 : 0.30));
        gg.addColorStop(0.55, css(sh, 0.16));
        gg.addColorStop(1, css(sh, 0));
        ctx.fillStyle = gg;
        ctx.beginPath(); ctx.ellipse(cx0, cy0, cell * shR, cell * shR * 0.76, 0, 0, 6.283); ctx.fill();
      }
      // 7a') a straight cast-shadow band under every wall run and along the
      // right of every left-hand wall — architecture throws a hard sun shadow
      for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
        if (at(x, y) !== BLOCK) continue;
        const px = x * cell, py = y * cell;
        if (at(x, y + 1) === FLOOR) {
          const gg = ctx.createLinearGradient(0, py + cell, 0, py + cell * 1.8);
          gg.addColorStop(0, css(sh, canopy ? 0.34 : 0.30)); gg.addColorStop(1, css(sh, 0));
          ctx.fillStyle = gg; ctx.fillRect(px - cell * 0.1, py + cell, cell * 1.2, cell * 0.8);
        }
        if (at(x + 1, y) === FLOOR) {
          const gg = ctx.createLinearGradient(px + cell, 0, px + cell * 1.45, 0);
          gg.addColorStop(0, css(sh, 0.22)); gg.addColorStop(1, css(sh, 0));
          ctx.fillStyle = gg; ctx.fillRect(px + cell, py, cell * 0.45, cell * 1.1);
        }
      }
      // 7b) dappled light through the canopy: warm sun-spots on the ground
      if (light.dapple !== false) {
        ctx.globalCompositeOperation = 'lighter';
        const sun = mix(poolCol, acc, 0.3);
        for (let i = 0; i < 26; i++) {
          const x = rng() * cw, y = rng() * ch, r = (16 + rng() * 34) * SS;
          softDisc(x, y, r, sun, 0.05 + rng() * 0.06);
        }
        ctx.globalCompositeOperation = 'source-over';
      }
    }
    // 7c) vignette: the room darkens toward its walls (strong indoors)
    if (light.vig > 0) {
      const vr = Math.max(cw, ch) * (enclosed ? 0.68 : 0.78);
      const vg = ctx.createRadialGradient(cw / 2, ch / 2, Math.min(cw, ch) * (enclosed ? 0.14 : 0.3), cw / 2, ch / 2, vr);
      vg.addColorStop(0, css(vigCol, 0));
      vg.addColorStop(enclosed ? 0.55 : 0.7, css(vigCol, light.vig * 0.45));
      vg.addColorStop(1, css(vigCol, light.vig));
      ctx.fillStyle = vg; ctx.fillRect(0, 0, cw, ch);
      if (enclosed) {
        // corners fall to near-black
        for (const [x, y] of [[0, 0], [cw, 0], [0, ch], [cw, ch]]) softDisc(x, y, Math.min(cw, ch) * 0.55, vigCol, light.vig * 0.8);
      }
    }
    // 7d) baked light pools
    if (enclosed) {
      const pools = [];
      // the wall torches the scene will hang (same RNG walk)
      for (const t of wallTorches(layout, th, BLOCK, FLOOR)) pools.push({ x: t.x * cell, y: t.y * cell, r: 6.2 * cell, a: 1.0, col: poolCol, torch: true });
      // daylight / corridor light spilling in at each exit
      const cx = cw / 2, cy = ch / 2;
      const dayCol = light.enclosed && th !== 'inside' ? [200, 225, 240] : poolCol;
      if (layout.gaps) {
        if (layout.gaps.north) pools.push({ x: cx, y: cell * 0.5, r: 3.6 * cell, a: 0.32, col: dayCol });
        if (layout.gaps.south) pools.push({ x: cx, y: ch - cell * 0.5, r: 3.6 * cell, a: 0.32, col: dayCol });
        if (layout.gaps.west) pools.push({ x: cell * 0.5, y: cy, r: 3.6 * cell, a: 0.32, col: dayCol });
        if (layout.gaps.east) pools.push({ x: cw - cell * 0.5, y: cy, r: 3.6 * cell, a: 0.32, col: dayCol });
      }
      // a hearth / lantern pool at the heart of the room so the middle,
      // where actors stand, is the brightest spot
      // (in the darkest places — caves, mines — the hearth stays dim so the
      // torches, not the middle of the floor, are the room's light)
      const hearthA = Math.max(0.3, 0.62 - Math.max(0, light.vig - 0.55) * 1.2);
      pools.push({ x: cx + (rng() - 0.5) * cell * 2, y: cy + (rng() - 0.5) * cell, r: (hearthA < 0.5 ? 5.0 : 6.0) * cell, a: hearthA, col: poolCol });
      ctx.globalCompositeOperation = 'lighter';
      for (const p of pools) {
        const gg = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r);
        gg.addColorStop(0, css(p.col, p.a));
        gg.addColorStop(0.28, css(p.col, p.a * 0.42));
        gg.addColorStop(0.62, css(p.col, p.a * 0.12));
        gg.addColorStop(1, css(p.col, 0));
        ctx.fillStyle = gg;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 6.283); ctx.fill();
      }
      ctx.globalCompositeOperation = 'source-over';
      // a second, normal-blend pass tints the lit floor toward the light's
      // colour so pools read as warm firelight rather than grey brightness
      for (const p of pools) softDisc(p.x, p.y, p.r * 0.7, p.col, p.a * (p.torch ? 0.4 : 0.28));
      // warm floor stain right under each torch (soot + heat glow) and a hot
      // core so the flame visibly owns its pool
      for (const p of pools) {
        if (!p.torch) continue;
        softDisc(p.x, p.y + cell * 0.4, cell * 1.1, mix(p.col, [255, 120, 40], 0.4), 0.22);
        ctx.globalCompositeOperation = 'lighter';
        softDisc(p.x, p.y + cell * 0.3, cell * 1.6, mix(p.col, [255, 240, 200], 0.5), 0.5);
        ctx.globalCompositeOperation = 'source-over';
      }
    }

    // 8) unifying speckle grain
    for (let i = 0; i < 1600; i++) {
      const x = rng() * cw, y = rng() * ch;
      ctx.fillStyle = rng() < 0.5 ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.05)';
      ctx.fillRect(x, y, SS, SS);
    }

    scene.textures.addCanvas(key, cv);
    return key;
  }

  MH.painter = { enabled: true, SS, paint };
})();
