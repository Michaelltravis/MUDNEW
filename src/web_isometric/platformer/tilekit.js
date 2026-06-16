// Misthollow tile kit — Phaser wiring ported into the MH namespace.
// Adapted from the handoff's tiles/wiring.js (ES module) to the platformer's
// classic-script / MH-global module style. Loads the three 64px atlases and
// resolves frames straight from misthollow_tiles.json, plus day/night tint.
(() => {
  const MH = window.MH = window.MH || {};

  let M = null;            // the parsed manifest
  let ready = false;

  // server sector_type / platformer theme -> kit terrain key
  const SECTOR_TO_TERRAIN = {
    inside: 'inside', city: 'city', field: 'field', forest: 'forest', hills: 'hills',
    mountain: 'mountain', water_swim: 'shallow', water_noswim: 'deep', underwater: 'underwater',
    desert: 'desert', swamp: 'swamp', dungeon: 'dungeon', cave: 'dungeon', underground: 'dungeon',
    flying: 'field', meadow: 'field', elven: 'forest', default: 'inside',
  };

  // Register the three spritesheets + the manifest json. Call in Boot preload().
  function preload(scene, base = '/platformer/tiles/') {
    const s = 64;
    scene.load.spritesheet('mh_terrain', base + 'terrain_atlas.png', { frameWidth: s, frameHeight: s });
    scene.load.spritesheet('mh_variants', base + 'floor_variants.png', { frameWidth: s, frameHeight: s });
    scene.load.spritesheet('mh_transitions', base + 'terrain_transitions.png', { frameWidth: s, frameHeight: s });
    scene.load.json('mh_tiles', base + 'misthollow_tiles.json');
  }

  // After the loader completes, pull the manifest out of the cache.
  function init(scene) {
    try {
      M = scene.cache.json.get('mh_tiles');
      ready = !!(M && M.atlases && scene.textures.exists('mh_terrain'));
    } catch (_) { ready = false; }
    return ready;
  }

  const isReady = () => ready;
  const terrainFor = sector => SECTOR_TO_TERRAIN[sector] || SECTOR_TO_TERRAIN.default;
  const hasTerrain = terrain => ready && M.atlases.terrain.frames[terrain] != null;

  // frame resolvers — read the manifest's precomputed absolute frame indices
  const terrainFrame = (terrain, piece) => M.atlases.terrain.frames[terrain][piece];
  const transitionFrame = (terrain, dir) => M.atlases.transitions.frames[terrain][dir];
  function floorVariantFrame(terrain) {
    const w = M.atlases.variants.weights, f = M.atlases.variants.frames[terrain];
    let x = Math.random(), i = 0;
    while (i < w.length - 1 && (x -= w[i]) > 0) i++;
    return f[i];
  }

  // in-game hour (0-23) -> day/night phase; matches the HUD recipe
  function phaseForHour(hour) {
    const h = ((hour | 0) % 24 + 24) % 24;
    if (h >= 6 && h <= 16) return 'midday';
    if (h >= 17 && h <= 20) return 'dusk';
    return 'night';
  }
  // map the server's period label onto the kit's three phases
  function phaseForPeriod(period) {
    const p = String(period || '').toLowerCase();
    if (['night', 'midnight'].includes(p)) return 'night';
    if (['dusk', 'evening'].includes(p)) return 'dusk';
    if (['dawn'].includes(p)) return 'dusk';
    return 'midday';
  }
  const tintFor = phase => ready ? parseInt(M.dayNightTint[phase] || M.dayNightTint.midday) : 0xffffff;

  MH.tilekit = {
    preload, init, isReady, terrainFor, hasTerrain,
    terrainFrame, transitionFrame, floorVariantFrame,
    phaseForHour, phaseForPeriod, tintFor, SECTOR_TO_TERRAIN,
    get manifest() { return M; },
  };
})();
