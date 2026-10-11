/* ============================================================
   Misthollow Tile Kit — Phaser 3 wiring
   Loads the three atlases, resolves frames from misthollow_tiles.json,
   builds rooms from server descriptors, auto-applies terrain transitions,
   and tints the world by time-of-day (matches the HUD).
   ------------------------------------------------------------
   Files expected alongside this one:
     terrain_atlas.png        16 x 13  (structural pieces)
     floor_variants.png        4 x 13  (base + 3 variants)
     terrain_transitions.png   8 x 13  (feathered overlays, transparent)
     misthollow_tiles.json     index manifest
   ============================================================ */

let M = null;

/** Load the manifest once. Call and await before using the helpers. */
export async function loadManifest(base = 'tiles/') {
  M = await fetch(base + 'misthollow_tiles.json').then(r => r.json());
  return M;
}

/** Register the three spritesheets. Call in your Scene.preload(). */
export function preloadTiles(scene, base = 'tiles/') {
  const s = 64;
  scene.load.spritesheet('mh_terrain',     base + 'terrain_atlas.png',      { frameWidth: s, frameHeight: s });
  scene.load.spritesheet('mh_variants',    base + 'floor_variants.png',     { frameWidth: s, frameHeight: s });
  scene.load.spritesheet('mh_transitions', base + 'terrain_transitions.png',{ frameWidth: s, frameHeight: s });
}

/* ---- frame resolvers (read straight from the manifest's precomputed maps) ---- */
export const terrainFrame    = (terrain, piece) => M.atlases.terrain.frames[terrain][piece];
export const transitionFrame = (terrain, dir)   => M.atlases.transitions.frames[terrain][dir];

/** Weighted pick of a floor variant frame (0=base, 1..3=variants). */
export function floorVariantFrame(terrain) {
  const w = M.atlases.variants.weights, f = M.atlases.variants.frames[terrain];
  let x = Math.random(), i = 0;
  while (i < w.length - 1 && (x -= w[i]) > 0) i++;
  return f[i];
}

/* ---- build a room from a server descriptor ----
   desc = { floor, wall, cols, rows, exits:{N:[c],E:[r],S:[c],W:[r]}, features:[{r,c,piece}] }
   Returns { map, floorLayer }. */
export function buildRoom(scene, desc) {
  const map = scene.make.tilemap({ tileWidth: 64, tileHeight: 64, width: desc.cols, height: desc.rows });
  const ts = map.addTilesetImage('mh_terrain');
  const floor = map.createBlankLayer('floor', ts);
  const ex = desc.exits || {};
  const has = (arr, v) => Array.isArray(arr) && arr.includes(v);

  for (let r = 0; r < desc.rows; r++) {
    for (let c = 0; c < desc.cols; c++) {
      const N = r === 0, S = r === desc.rows - 1, W = c === 0, E = c === desc.cols - 1;
      let piece;
      if      (N && W) piece = 'cornerNW';
      else if (N && E) piece = 'cornerNE';
      else if (S && E) piece = 'cornerSE';
      else if (S && W) piece = 'cornerSW';
      else if (N) piece = has(ex.N, c) ? 'openN' : 'wallN';
      else if (S) piece = has(ex.S, c) ? 'openS' : 'wallS';
      else if (W) piece = has(ex.W, r) ? 'openW' : 'wallW';
      else if (E) piece = has(ex.E, r) ? 'openE' : 'wallE';
      else {
        const f = (desc.features || []).find(f => f.r === r && f.c === c);
        piece = f ? f.piece : null;
      }
      if (piece) floor.putTileAt(terrainFrame(desc.wall && (N||S||W||E) ? desc.wall : desc.floor, piece), c, r);
      else       floor.putTileAt(floorVariantFrame(desc.floor) <= terrainFrame(desc.floor,'floorAlt')
                                 ? floorVariantFrame(desc.floor) : terrainFrame(desc.floor,'floor'), c, r);
    }
  }
  return { map, floorLayer: floor };
}

/* ---- auto-apply transition overlays ----
   grid = 2D array (grid[r][c] = terrain key) describing the floor terrain of each cell.
   Stamps feathered overlays on a separate layer so neighbours blend.
   Honours manifest.blendPriority (a terrain only feathers over LOWER-priority neighbours). */
export function applyTransitions(scene, grid, map) {
  const rows = grid.length, cols = grid[0].length;
  const ts = map.addTilesetImage('mh_transitions');
  const layer = map.createBlankLayer('transitions', ts);
  const prio = t => M.blendPriority.indexOf(t);
  const at = (r, c) => (r >= 0 && r < rows && c >= 0 && c < cols) ? grid[r][c] : null;
  const edges = { N: [-1, 0], E: [0, 1], S: [1, 0], W: [0, -1] };

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const T = grid[r][c];
      // edges: neighbour of a different, lower-priority terrain → feather T toward that side
      for (const d of M.autotile.edgeDirs) {
        const n = at(r + edges[d][0], c + edges[d][1]);
        if (n && n !== T && prio(n) < prio(T)) layer.putTileAt(transitionFrame(T, d), c, r);
      }
      // outer corners: diagonal differs while both shared orthogonals match T
      for (const d of M.autotile.cornerDirs) {
        const [a, b] = M.autotile.cornerNeighbours[d];
        const diag = { NW: [-1, -1], NE: [-1, 1], SE: [1, 1], SW: [1, -1] }[d];
        const nd = at(r + diag[0], c + diag[1]);
        const na = at(r + edges[a][0], c + edges[a][1]);
        const nb = at(r + edges[b][0], c + edges[b][1]);
        if (nd && nd !== T && prio(nd) < prio(T) && na === T && nb === T)
          layer.putTileAt(transitionFrame(T, d), c, r);
      }
    }
  }
  return layer;
}

/* ---- day/night tint (matches the HUD) ---- */
export function setTimeOfDay(layers, phase) {
  const tint = parseInt(M.dayNightTint[phase]); // 'midday' | 'dusk' | 'night'
  (Array.isArray(layers) ? layers : [layers]).forEach(l => l.setTint(tint));
}
