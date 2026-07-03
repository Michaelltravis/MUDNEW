// Misthollow painterly ground renderer — Phase 1 of the graphics overhaul.
// Instead of a grid of repeating 16px tiles, each room gets ONE soft-brushed
// PAINTING: a biome color wash, hand-mottled variation, floor-kind brush
// strokes (grass blades, cobbles, marble veins, sand ripples...), soft-edged
// water with foam shorelines, worn dirt paths running to the exits, and
// ambient-occlusion shadow where the floor meets walls. Deterministic per
// room (seeded by vnum) so a room always looks like itself.
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
    forest: ['#46583a', '#3e4f33', 'grass'], field: ['#5a6c3e', '#50613a', 'grass'],
    hills: ['#5c6a40', '#525f3a', 'grass'], swamp: ['#454a34', '#3c402c', 'slimestone'],
    desert: ['#b59a64', '#a98f5a', 'sand'], mountain: ['#6a6e78', '#5e626c', 'cracked'],
    cave: ['#4a4238', '#423a30', 'cracked'], dungeon: ['#3f3a4c', '#383344', 'flagstone'],
    underground: ['#3f3a4c', '#383344', 'flagstone'], inside: ['#5c5044', '#52473c', 'flagstone'],
    city: ['#565b66', '#4c515c', 'cobble'], default: ['#4c5240', '#434838', 'grass'],
  };

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

    const zt = layout.zoneKey && MH.ZONE_THEMES ? MH.ZONE_THEMES[layout.zoneKey] : null;
    const fall = SECTOR_FLOOR[th] || SECTOR_FLOOR.default;
    const base = rgb(zt ? zt.floor : fall[0]);
    const base2 = rgb(zt ? (zt.f2 || zt.floor) : fall[1]);
    const acc = rgb(zt ? zt.acc : '#c8c090');
    const kind = zt ? (zt.floorKind || fall[2]) : fall[2];
    const waterCol = rgb((zt && zt.water) || (MH.THEMES && MH.THEMES[th] && MH.THEMES[th].liquid) || '#3a6a9a');

    const at = (x, y) => (x < 0 || y < 0 || x >= W || y >= H) ? BLOCK : grid[y * W + x];

    // 1) base wash: soft radial center-light over a two-tone ground
    let g = ctx.createRadialGradient(cw / 2, ch / 2, 40, cw / 2, ch / 2, Math.max(cw, ch) * 0.72);
    g.addColorStop(0, css(mix(base, [255, 255, 255], 0.06)));
    g.addColorStop(1, css(base2));
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, cw, ch);
    // sun direction: a whisper of warm light from the top-left
    g = ctx.createLinearGradient(0, 0, cw, ch);
    g.addColorStop(0, 'rgba(255,240,200,0.05)');
    g.addColorStop(0.5, 'rgba(255,240,200,0)');
    g.addColorStop(1, 'rgba(10,10,30,0.06)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, cw, ch);

    // 2) mottling: big soft color blotches (the hand-painted unevenness)
    const blotchCols = [shade(base, 0.86), shade(base, 1.12), mix(base, acc, 0.14), mix(base, base2, 0.5)];
    for (let i = 0; i < 240; i++) {
      const x = rng() * cw, y = rng() * ch, r = (14 + rng() * 46) * SS * 0.75;
      const c = blotchCols[(rng() * blotchCols.length) | 0];
      const gg = ctx.createRadialGradient(x, y, 0, x, y, r);
      gg.addColorStop(0, css(c, 0.05 + rng() * 0.05));
      gg.addColorStop(1, css(c, 0));
      ctx.fillStyle = gg;
      ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill();
    }

    // 3) worn path to each exit gap (painted UNDER the strokes so it melts in)
    if (layout.gaps && (kind === 'grass' || kind === 'sand' || kind === 'slimestone')) {
      const dirt = kind === 'sand' ? shade(base, 0.88) : mix(base, rgb('#8a7248'), 0.5);
      const cx = cw / 2, cy = ch / 2;
      const ends = [];
      if (layout.gaps.north) ends.push([cx, 0]);
      if (layout.gaps.south) ends.push([cx, ch]);
      if (layout.gaps.west) ends.push([0, cy]);
      if (layout.gaps.east) ends.push([cw, cy]);
      ctx.lineCap = 'round';
      for (const [ex, ey] of ends) {
        for (let pass = 0; pass < 3; pass++) {
          ctx.strokeStyle = css(dirt, 0.10 + pass * 0.05);
          ctx.lineWidth = (16 - pass * 4) * SS * 0.6;
          ctx.beginPath();
          ctx.moveTo(cx + (rng() - 0.5) * 8, cy + (rng() - 0.5) * 8);
          ctx.quadraticCurveTo((cx + ex) / 2 + (rng() - 0.5) * 30, (cy + ey) / 2 + (rng() - 0.5) * 30, ex, ey);
          ctx.stroke();
        }
      }
    } else if (layout.gaps && (kind === 'cobble' || kind === 'flagstone' || kind === 'marble')) {
      // worn lighter track over stone
      const wear = mix(base, [255, 255, 255], 0.10);
      const cx = cw / 2, cy = ch / 2;
      ctx.lineCap = 'round';
      for (const [gk, ex, ey] of [['north', cx, 0], ['south', cx, ch], ['west', 0, cy], ['east', cw, cy]]) {
        if (!layout.gaps[gk]) continue;
        ctx.strokeStyle = css(wear, 0.10);
        ctx.lineWidth = 13 * SS * 0.6;
        ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(ex, ey); ctx.stroke();
      }
    }

    // 4) floor-kind brushwork
    if (kind === 'grass') {
      const dk = shade(base, 0.72), lt = mix(shade(base, 1.22), acc, 0.12);
      for (let i = 0; i < 1500; i++) {
        const x = rng() * cw, y = rng() * ch;
        const len = (3 + rng() * 6) * SS, ang = -1.35 + (rng() - 0.5) * 0.8;
        ctx.strokeStyle = css(rng() < 0.5 ? dk : lt, 0.10 + rng() * 0.08);
        ctx.lineWidth = SS * (0.7 + rng() * 0.7);
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + Math.cos(ang) * len, y + Math.sin(ang) * len);
        ctx.stroke();
      }
    } else if (kind === 'cobble' || kind === 'flagstone') {
      // soft slabs: jittered rounded stones with darker seams, painted lightly
      const seam = shade(base2, 0.7);
      const step = kind === 'cobble' ? 10 * SS : 16 * SS;
      for (let yy = 0; yy < ch + step; yy += step) {
        const rowOff = ((yy / step) | 0) % 2 ? step / 2 : 0;
        for (let xx = -step; xx < cw + step; xx += step) {
          const px = xx + rowOff + (rng() - 0.5) * 3 * SS, py = yy + (rng() - 0.5) * 3 * SS;
          const w = step * (0.82 + rng() * 0.2), h = step * (0.7 + rng() * 0.2);
          const lum = 0.92 + rng() * 0.16;
          ctx.fillStyle = css(shade(base, lum), 0.16);
          ctx.beginPath();
          if (ctx.roundRect) ctx.roundRect(px, py, w, h, 3 * SS); else ctx.rect(px, py, w, h);
          ctx.fill();
          ctx.strokeStyle = css(seam, 0.20);
          ctx.lineWidth = SS * 0.8;
          ctx.stroke();
        }
      }
    } else if (kind === 'marble') {
      // polish sheen + wandering pale veins
      for (let i = 0; i < 10; i++) {
        const x = rng() * cw, y = rng() * ch, r = (30 + rng() * 60) * SS;
        const gg = ctx.createRadialGradient(x, y, 0, x, y, r);
        gg.addColorStop(0, 'rgba(255,255,255,0.07)');
        gg.addColorStop(1, 'rgba(255,255,255,0)');
        ctx.fillStyle = gg;
        ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill();
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
      const dk = shade(base, 0.85);
      ctx.lineWidth = SS;
      for (let i = 0; i < 120; i++) {
        const y = rng() * ch, x = rng() * cw, len = (20 + rng() * 60) * SS;
        ctx.strokeStyle = css(dk, 0.10 + rng() * 0.06);
        ctx.beginPath(); ctx.moveTo(x, y);
        ctx.quadraticCurveTo(x + len / 2, y + (rng() - 0.5) * 8 * SS, x + len, y + (rng() - 0.5) * 4 * SS);
        ctx.stroke();
      }
    } else if (kind === 'slimestone') {
      for (let i = 0; i < 90; i++) {
        const x = rng() * cw, y = rng() * ch, r = (5 + rng() * 16) * SS;
        const slick = rng() < 0.4;
        const gg = ctx.createRadialGradient(x, y, 0, x, y, r);
        gg.addColorStop(0, slick ? 'rgba(190,230,170,0.08)' : css(shade(base, 0.7), 0.14));
        gg.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = gg;
        ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill();
      }
    } else if (kind === 'cracked') {
      ctx.lineWidth = SS * 0.8;
      for (let i = 0; i < 16; i++) {
        let x = rng() * cw, y = rng() * ch;
        ctx.strokeStyle = css(shade(base, 0.6), 0.22);
        ctx.beginPath(); ctx.moveTo(x, y);
        for (let s2 = 0; s2 < 4; s2++) { x += (rng() - 0.5) * 34 * SS; y += (rng() - 0.5) * 34 * SS; ctx.lineTo(x, y); }
        ctx.stroke();
      }
    }

    // 4.5) prose accents: the description tints the ground itself
    if (layout.mossy) {
      const moss = mix(base, rgb('#4a7a3a'), 0.6);
      for (let i = 0; i < 110; i++) {
        const x = rng() * cw, y = rng() * ch, r = (6 + rng() * 22) * SS;
        const gg = ctx.createRadialGradient(x, y, 0, x, y, r);
        gg.addColorStop(0, css(moss, 0.10 + rng() * 0.08));
        gg.addColorStop(1, css(moss, 0));
        ctx.fillStyle = gg;
        ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill();
      }
    }
    if (layout.snowy) {
      ctx.fillStyle = 'rgba(235,242,250,0.22)';
      ctx.fillRect(0, 0, cw, ch);
      for (let i = 0; i < 160; i++) {
        const x = rng() * cw, y = rng() * ch, r = (4 + rng() * 18) * SS;
        const gg = ctx.createRadialGradient(x, y, 0, x, y, r);
        gg.addColorStop(0, `rgba(245,250,255,${0.10 + rng() * 0.10})`);
        gg.addColorStop(1, 'rgba(245,250,255,0)');
        ctx.fillStyle = gg;
        ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill();
      }
    }

    // 5) water: deep fill, shallow soft edge, wobbling foam shoreline
    let hasWater = false;
    for (let i = 0; i < grid.length; i++) if (grid[i] === WATER) { hasWater = true; break; }
    if (hasWater) {
      const deep = shade(waterCol, 0.8), shallow = mix(waterCol, [255, 255, 255], 0.18);
      // body
      for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
        if (at(x, y) !== WATER) continue;
        ctx.fillStyle = css(deep, 0.96);
        ctx.fillRect(x * cell, y * cell, cell, cell);
      }
      // shallow gradient lapping onto the shore side
      for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
        if (at(x, y) !== WATER) continue;
        const cx0 = x * cell + cell / 2, cy0 = y * cell + cell / 2;
        const gg = ctx.createRadialGradient(cx0, cy0, cell * 0.2, cx0, cy0, cell * 0.95);
        gg.addColorStop(0, css(shallow, 0.30));
        gg.addColorStop(1, css(shallow, 0));
        ctx.fillStyle = gg;
        ctx.beginPath(); ctx.arc(cx0, cy0, cell * 0.95, 0, 6.283); ctx.fill();
      }
      // foam: paint the water↔floor boundary with wobbling light strokes
      ctx.lineCap = 'round';
      for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
        if (at(x, y) !== WATER) continue;
        const edges = [[0, -1, x * cell, y * cell, (x + 1) * cell, y * cell],
                       [0, 1, x * cell, (y + 1) * cell, (x + 1) * cell, (y + 1) * cell],
                       [-1, 0, x * cell, y * cell, x * cell, (y + 1) * cell],
                       [1, 0, (x + 1) * cell, y * cell, (x + 1) * cell, (y + 1) * cell]];
        for (const [dx, dy, x1, y1, x2, y2] of edges) {
          if (at(x + dx, y + dy) === WATER || at(x + dx, y + dy) === BLOCK) continue;
          for (let pass = 0; pass < 2; pass++) {
            ctx.strokeStyle = `rgba(230,245,250,${pass ? 0.16 : 0.30})`;
            ctx.lineWidth = (pass ? 3.5 : 1.8) * SS * 0.8;
            ctx.beginPath();
            const midx = (x1 + x2) / 2 + (rng() - 0.5) * 3 * SS, midy = (y1 + y2) / 2 + (rng() - 0.5) * 3 * SS;
            ctx.moveTo(x1 + (rng() - 0.5) * 2 * SS, y1 + (rng() - 0.5) * 2 * SS);
            ctx.quadraticCurveTo(midx, midy, x2 + (rng() - 0.5) * 2 * SS, y2 + (rng() - 0.5) * 2 * SS);
            ctx.stroke();
          }
        }
        // ripple highlights inside open water
        if (rng() < 0.3) {
          ctx.strokeStyle = 'rgba(220,240,250,0.12)';
          ctx.lineWidth = SS * 0.8;
          const rx = x * cell + cell * (0.2 + rng() * 0.6), ry = y * cell + cell * (0.2 + rng() * 0.6);
          ctx.beginPath(); ctx.arc(rx, ry, (2 + rng() * 4) * SS, 0.3, 2.6); ctx.stroke();
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
    const AO = 9 * SS;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
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
        gg.addColorStop(0, 'rgba(6,8,14,0.30)');
        gg.addColorStop(1, 'rgba(6,8,14,0)');
        ctx.fillStyle = gg;
        ctx.fillRect(x1, y1, x2 - x1, y2 - y1);
      }
    }

    // 7) unifying speckle grain
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
