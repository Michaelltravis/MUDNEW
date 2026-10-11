// Misthollow: real creature art (Dungeon Crawl Stone Soup, CC0) for the
// non-humanoid bestiary. Resolves a mob name -> a 32x32 DCSS sprite via a
// layered match (file-stem words -> mob-type/variant -> archetype bridge),
// and loads/caches them on demand. Humanoid NPCs use the LPC paperdolls; this
// covers everything else (dragons, undead, demons, beasts, golems, …).
(() => {
  const MH = window.MH = window.MH || {};
  const BASE = '/sprites/dcss/';
  let MAN = null, FILES = null, ready = false;

  // stem index: relPath -> { words:Set, cat, spec(specificity) }
  let INDEX = [];
  const STOP = new Set(['a', 'an', 'the', 'of', 'large', 'small', 'giant', 'great', 'lesser',
    'greater', 'elder', 'ancient', 'young', 'old', 'baby', 'huge', 'tiny', 'dire']);

  function preload(scene) {
    scene.load.json('dcss_manifest', BASE + 'manifest.json');
    scene.load.json('dcss_index', BASE + 'index.json');
  }
  function init(scene) {
    try {
      MAN = scene.cache.json.get('dcss_manifest');
      FILES = scene.cache.json.get('dcss_index');
      if (FILES) {
        INDEX = FILES.map(p => {
          const stem = p.split('/').pop().replace(/\.png$/, '');
          const words = stem.split(/[_\s]+/).filter(Boolean);
          return { path: p, words, n: words.length };
        });
      }
      ready = !!(MAN && FILES);
    } catch (_) { ready = false; }
    return ready;
  }
  const isReady = () => ready;

  // archetype key (from sprites.js MOB_ARCHETYPES) -> a DCSS mobType fallback
  const ARCH2TYPE = {
    dragon: 'dragon', undead: 'undead', demon: 'demon', beast: 'beast', insect: 'spider',
    slime: 'abomination', elemental: 'elemental', aquatic: 'beast', bird: 'small_animal',
    reptile: 'beast', construct: 'golem', celestial: 'angel', fey: 'satyr', plant: 'treant',
    horror: 'abomination', goblinoid: 'goblin', ghost: 'ghost',
  };
  // common synonyms a mob name might use that aren't a file stem
  const SYN = {
    snake: 'adder', serpent: 'anaconda', viper: 'adder', cobra: 'black_mamba',
    spider: 'wolf_spider', arachnid: 'wolf_spider', skeleton: 'skeletal_warrior',
    zombie: 'zombie_gnoll', demon: 'cacodemon', devil: 'red_devil', imp: 'lemure',
    slime: 'jelly', ooze: 'jelly', wisp: 'will_o_the_wisp', sphinx: 'guardian_sphinx',
    naga: 'anaconda', wyrm: 'fire_dragon', drake: 'fire_dragon', wyvern: 'hydra',
    elemental: 'fire_elemental', golem: 'iron_golem', giant: 'stone_giant',
    angel: 'angel', wolf: 'wolf', bear: 'black_bear', cat: 'tiger', rat: 'rat',
    bat: 'bat', frog: 'bullfrog', toad: 'bullfrog', crab: 'octopode', fish: 'electric_eel',
    eel: 'electric_eel', shark: 'electric_eel', squid: 'kraken_head', octopus: 'octopode',
    mushroom: 'wandering_mushroom', fungus: 'toadstool', tree: 'treant', ent: 'treant',
    horse: 'horse', dog: 'hound', hound: 'hound', wolfhound: 'warg', boar: 'hog', pig: 'hog',
    deer: 'deer', stag: 'deer', scorpion: 'scorpion', beetle: 'giant_cockroach',
    roach: 'giant_cockroach', bee: 'killer_bee', wasp: 'hornet', mosquito: 'vampire_mosquito',
    lizard: 'iguana', gecko: 'iguana', crocodile: 'crocodile', alligator: 'alligator',
    wraith: 'wraith', spectre: 'phantom', specter: 'phantom', phantom: 'phantom',
    banshee: 'wraith', ghoul: 'ghoul', mummy: 'mummy', lich: 'lich', vampire: 'vampire',
    gargoyle: 'gargoyle', medusa: 'medusa', harpy: 'harpy', minotaur: 'minotaur',
    cyclops: 'cyclops', titan: 'titan', troll: 'troll', ogre: 'ogre', orc: 'orc',
    goblin: 'goblin', kobold: 'kobold', gnoll: 'gnoll', dwarf: 'dwarf', hobgoblin: 'hobgoblin',
    basilisk: 'basilisk', manticore: 'manticore', chimera: 'chimera', hippogriff: 'hippogriff',
    griffon: 'hippogriff', griffin: 'hippogriff', kraken: 'kraken_head', hydra: 'hydra',
    jelly: 'jelly', abomination: 'abomination_large', tentacle: 'tentacled_monstrosity',
    eye: 'great_orb_of_eyes', beholder: 'great_orb_of_eyes', mindflayer: 'tentacled_monstrosity',
    salamander: 'salamander', faun: 'faun', satyr: 'satyr', nymph: 'water_nymph',
    dryad: 'dryad', fairy: 'butterfly', sprite: 'butterfly', pixie: 'butterfly',
    seraph: 'seraph', cherub: 'cherub', angel: 'angel', revenant: 'revenant',
    poltergeist: 'poltergeist', wight: 'wight', necrophage: 'necrophage', shade: 'shadow_wraith',
    raven: 'raven', crow: 'raven', swan: 'swan', duck: 'duck', rabbit: 'rabbit',
    squirrel: 'squirrel', fox: 'fox', jackal: 'jackal', lion: 'lion', tiger: 'tiger',
    elephant: 'elephant', yak: 'death_yak', shrike: 'caustic_shrike',
  };

  // exact full-name overrides for uniquely-named bosses/creatures whose names
  // carry no generic creature keyword
  const EXACT = {
    death: 'boss/horseman_death.png', famine: 'boss/horseman_famine.png',
    pestilence: 'boss/horseman_pestilence.png', war: 'boss/horseman_war.png',
    androsphinx: 'demihumanoids/guardian_sphinx.png', sphinx: 'demihumanoids/guardian_sphinx.png',
    khufu: 'boss/khufu.png', ignacio: 'boss/ignacio.png', arachne: 'boss/arachne.png',
    'archon prime': 'holy/seraph.png',
  };

  function pathForStem(stem) {
    const e = INDEX.find(i => i.path.endsWith('/' + stem + '.png'));
    return e ? e.path : null;
  }

  // resolve a mob display name -> a DCSS relative path, or null
  function resolve(name) {
    if (!ready) return null;
    const n = String(name || '').toLowerCase();
    const words = n.split(/[^a-z]+/).filter(w => w.length >= 2 && !STOP.has(w));
    if (!words.length) return null;
    const wset = new Set(words);

    // 0) exact full-name / single-word overrides for unique bosses
    const nClean = words.join(' ');
    if (EXACT[nClean]) return EXACT[nClean];
    if (words.length === 1 && EXACT[words[0]]) return EXACT[words[0]];

    // 1) best file-stem match: every word of the stem appears in the name;
    //    prefer the most specific (most words) stem
    let best = null, bestScore = 0;
    for (const e of INDEX) {
      let hit = 0;
      for (const w of e.words) {
        if (wset.has(w) || (w.length >= 4 && words.some(nw => nw.length >= 4 && (nw.startsWith(w) || w.startsWith(nw))))) hit++;
      }
      if (hit === e.n) {
        const score = e.n * 10 + hit;   // full stem match, weight by length
        if (score > bestScore) { bestScore = score; best = e.path; }
      }
    }
    if (best) return best;

    // 2) single-word synonym map (snake, spider, skeleton, …)
    for (const w of words) { if (SYN[w]) { const p = pathForStem(SYN[w]); if (p) return p; } }

    // 3) DCSS mob-type by keyword, honoring variants
    if (MAN && MAN.mobTypes) {
      for (const [type, def] of Object.entries(MAN.mobTypes)) {
        const tk = type.replace(/_/g, ' ');
        if (n.includes(tk) || wset.has(type)) {
          for (const [vk, vp] of Object.entries(def.variants || {})) {
            if (n.includes(vk.replace(/_/g, ' ')) || wset.has(vk)) return vp;
          }
          return def.defaultSprite;
        }
      }
    }

    // 4) bridge through the procedural archetype classifier
    const arch = MH.mobArchetype ? MH.mobArchetype(n).key : null;
    const t = ARCH2TYPE[arch];
    if (t && MAN && MAN.mobTypes[t]) return MAN.mobTypes[t].defaultSprite;
    return null;
  }

  // load (once) and cache a DCSS image; cb(textureKey) when ready
  const pendCb = {};
  function ensure(scene, relPath, cb) {
    const key = 'dcss:' + relPath;
    if (scene.textures.exists(key)) { cb(key); return; }
    if (pendCb[key]) { pendCb[key].push(cb); return; }
    pendCb[key] = [cb];
    scene.load.image(key, BASE + relPath);
    scene.load.once('complete', () => {
      const cbs = pendCb[key] || []; delete pendCb[key];
      const ok = scene.textures.exists(key);
      cbs.forEach(f => { try { f(ok ? key : null); } catch (_) {} });
    });
    scene.load.once('loaderror', () => { const cbs = pendCb[key] || []; delete pendCb[key]; cbs.forEach(f => { try { f(null); } catch (_) {} }); });
    scene.load.start();
  }

  // Bake a dark contour around a loaded creature sprite -> new texture key.
  // Characters need a hard silhouette edge to read against painterly ground
  // (BrowserQuest-style readability); the contour is scaled to the art's own
  // resolution so a 32px sprite gets 1px and a large painted animal ~its
  // equivalent once it is shrunk to tile scale. Cached per (key, color).
  // `thick` multiplies the contour (2 = a bold hostile rim that reads as a
  // red silhouette from across the room, not a hairline).
  function outlined(scene, key, color, thick) {
    const col = color || 'rgba(18,10,14,0.92)';
    const mul = Math.max(1, Math.round(thick || 1));
    const ok = key + '|ol:' + col + (mul > 1 ? '|t' + mul : '');
    if (scene.textures.exists(ok)) return ok;
    try {
      const src = scene.textures.get(key).getSourceImage();
      const w = src.width, h = src.height;
      const t = Math.max(1, Math.round(h / 32)) * mul;   // contour thickness in source px
      const c = document.createElement('canvas');
      c.width = w + t * 2; c.height = h + t * 2;
      const g = c.getContext('2d');
      // silhouette stamped at every offset within the contour radius (a full
      // disc of stamps, so a 2px rim is solid rather than eight corners)
      for (let dx = -t; dx <= t; dx++) for (let dy = -t; dy <= t; dy++) {
        if (!dx && !dy) continue;
        if (dx * dx + dy * dy > t * t + 0.5) continue;
        g.drawImage(src, t + dx, t + dy);
      }
      g.globalCompositeOperation = 'source-in';
      g.fillStyle = col; g.fillRect(0, 0, c.width, c.height);
      g.globalCompositeOperation = 'source-over';
      g.drawImage(src, t, t);
      scene.textures.addCanvas(ok, c);
      return ok;
    } catch (_) { return key; }
  }

  MH.dcss = { preload, init, isReady, resolve, ensure, outlined };
})();
