// Misthollow: Lucifer tileset props (CC0, docs/art/SOURCES.md).
// After themes-zones paints its procedural `zt_prop_<name>` canvases, this
// replaces the ones we have real art for with crops from the Lucifer atlases,
// so every existing prop placement/glow/interaction path draws the new art.
// A crop is found by flood-filling alpha from a seed point, so seeds only
// need to land inside the sprite rather than on exact rectangles.
(() => {
  const MH = window.MH = window.MH || {};
  const ATLAS = {
    dungeon: 'lucifer-dungeon-tileset/Png/DungeonTileset.png',
    outer: 'lucifer-exterior-tileset/Png/OuterTileset.png',
  };
  // name -> { atlas, seed: [x, y] inside the sprite, max: [w, h] search box }
  const PROPS = {
    brazier:    { atlas: 'dungeon', seed: [560, 20],  max: [32, 64], fitH: 18 },   // candelabra flame
    lantern:    { atlas: 'dungeon', seed: [496, 20],  max: [32, 64], fitH: 16 },   // wall torch
    candles:    { atlas: 'dungeon', seed: [560, 150], max: [32, 64], fitH: 22 },   // candle stand
    pillar:     { atlas: 'dungeon', seed: [592, 150], max: [32, 64] },   // stone column
    banner:     { atlas: 'dungeon', seed: [496, 100], max: [32, 64], fitH: 22 },   // red hanging banner
    barrel:     { atlas: 'dungeon', seed: [560, 110], max: [32, 32], fitH: 14 },
    statue:     { atlas: 'dungeon', seed: [432, 160], max: [32, 64], fitH: 17 },   // armoured knight statue
    gravestone: { atlas: 'outer',   seed: [944, 14],  max: [32, 32], fitH: 14 },
    runestone:  { atlas: 'outer',   seed: [976, 14],  max: [32, 32], fitH: 15 },   // cross marker
    pine:       { atlas: 'outer',   seed: [1248, 40], max: [64, 96] },
    tree:       { atlas: 'outer',   seed: [1248, 40], max: [64, 96] },
    rock:       { atlas: 'outer',   seed: [1152, 50], max: [64, 32], fitH: 16 },
    bush:       { atlas: 'outer',   seed: [1168, 80], max: [32, 32], fitH: 14 },
    urn:        { atlas: 'outer',   seed: [1072, 80], max: [32, 32], fitH: 14 },   // potted plant
    fence:      { atlas: 'outer',   seed: [1000, 110], max: [64, 32], fitH: 14 },
    lamppost:   { atlas: 'outer',   seed: [1072, 150], max: [16, 96] },  // standing pole
  };
  const report = {};

  function preload(scene) {
    const base = (MH.urls && MH.urls.art) || '/art/';
    for (const [k, url] of Object.entries(ATLAS)) scene.load.image('luc_atlas_' + k, base + url);
  }

  // bounding box of the alpha-connected region around the seed, clamped to max
  function cropBox(img, sx, sy, mw, mh) {
    const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
    const g = c.getContext('2d'); g.drawImage(img, 0, 0);
    const x0 = Math.max(0, sx - mw), y0 = Math.max(0, sy - mh);
    const x1 = Math.min(img.width, sx + mw), y1 = Math.min(img.height, sy + mh);
    const W = x1 - x0, H = y1 - y0;
    const d = g.getImageData(x0, y0, W, H).data;
    const a = (x, y) => d[((y - y0) * W + (x - x0)) * 4 + 3] > 8;
    if (!a(sx, sy)) {   // seed on transparent px: look for the nearest opaque one
      let best = null, bd = 1e9;
      for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) if (a(x, y)) { const dd = (x - sx) ** 2 + (y - sy) ** 2; if (dd < bd) { bd = dd; best = [x, y]; } }
      if (!best || bd > 12 * 12) return null;
      [sx, sy] = best;
    }
    const seen = new Uint8Array(W * H); const st = [[sx, sy]];
    let minx = sx, maxx = sx, miny = sy, maxy = sy;
    while (st.length) {
      const [x, y] = st.pop();
      if (x < x0 || y < y0 || x >= x1 || y >= y1) continue;
      const i = (y - y0) * W + (x - x0); if (seen[i] || !a(x, y)) continue; seen[i] = 1;
      if (x < minx) minx = x; if (x > maxx) maxx = x; if (y < miny) miny = y; if (y > maxy) maxy = y;
      // 8-connected with a 1px tolerance gap so thin outlines don't split a sprite
      for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) if (dx || dy) st.push([x + dx, y + dy]);
    }
    return { img, x: minx, y: miny, w: maxx - minx + 1, h: maxy - miny + 1 };
  }

  function apply(scene) {
    const SS = MH.SMOOTH_SS || 4;
    const imgs = {};
    for (const k of Object.keys(ATLAS)) { const t = scene.textures.get('luc_atlas_' + k); imgs[k] = t && t.key !== '__MISSING' ? t.getSourceImage() : null; }
    for (const [name, spec] of Object.entries(PROPS)) {
      const img = imgs[spec.atlas]; if (!img) { report[name] = 'no atlas'; continue; }
      const box = cropBox(img, spec.seed[0], spec.seed[1], spec.max[0], spec.max[1]);
      if (!box || box.w < 6 || box.h < 6) { report[name] = 'no crop'; continue; }
      // themes-zones props are 20x26 logical px at SS and every placement
      // scales by (mul / SS), so fit each crop into that same box: the art
      // then lands at the size the set-piece code already tuned for.
      const fit = Math.min(1, 20 / box.w, (spec.fitH || 26) / box.h);
      const lw = Math.max(1, Math.round(box.w * fit)), lh = Math.max(1, Math.round(box.h * fit));
      const c = document.createElement('canvas'); c.width = lw * SS; c.height = lh * SS;
      const g = c.getContext('2d'); g.imageSmoothingEnabled = fit < 1;   // smooth only when shrinking
      g.drawImage(img, box.x, box.y, box.w, box.h, 0, 0, c.width, c.height);
      const key = `zt_prop_${name}`;
      if (scene.textures.exists(key)) scene.textures.remove(key);
      scene.textures.addCanvas(key, c);
      scene.textures.get(key).setFilter(Phaser.Textures.FilterMode.NEAREST);
      report[name] = `${box.w}x${box.h}@${box.x},${box.y}`;
    }
    MH.luciferTiles.report = report;
  }
  MH.luciferTiles = { preload, apply, report };
})();
