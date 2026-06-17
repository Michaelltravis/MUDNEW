// Misthollow LPC paperdoll compositor.
// Builds a layered, animated character (Phaser Container of Sprites) from a
// loadout derived from the manifest's class defaults + the equipped weapon
// (resolved via item_to_lpc.json). Sheets are 64x64; rows = [up,left,down,
// right]; columns = frames. Loaded on demand and cached. Humanoid only.
(() => {
  const MH = window.MH = window.MH || {};
  const BASE = '/platformer/sprites/lpc/';
  let RULES = null, MAN = null, IDX = null, ready = false;

  // platformer action -> LPC animation file stem
  const ANIM_FILE = { idle: 'idle', walk: 'walk', run: 'walk', attack: 'slash', slash: 'slash',
    thrust: 'thrust', cast: 'spellcast', shoot: 'shoot', hurt: 'hurt' };
  const ROW = { up: 0, left: 1, down: 2, right: 3 };
  // the animations we support / preload per layer
  const ANIMS = ['idle', 'walk', 'slash', 'spellcast', 'hurt'];

  // map a class-default loadout stub -> a real on-disk layer id (sex-aware
  // where the starter pack only ships one sex)
  function torsoLayer(stub, sex) {
    if (stub === 'clothes/robe') return 'torso/clothes/robe/female';   // only female robe shipped
    if (stub === 'armour/leather') return 'torso/armour/leather/male';
    return 'torso/armour/plate/male';
  }
  const LEGS = { 'armour/plate': 'legs/armour/plate/male', 'pants': 'legs/pants/male' };
  const HEAD = { 'helmet/greathelm': 'hat/helmet/greathelm/male', 'helmet/flattop': 'hat/helmet/flattop/male' };
  const HAIR = { 'flat_top_fade': 'hair/flat_top_fade/male', 'xlong': 'hair/xlong/male' };
  const WIELD = { 'sword/arming': 'weapon/sword/arming/universal', 'magic/diamond': 'weapon/magic/diamond/universal',
    'ranged/bow/recurve': 'weapon/ranged/bow/recurve' };
  const SHIELD = { 'crusader': 'shield/crusader' };

  function preload(scene) {
    scene.load.json('lpc_rules', BASE + 'item_to_lpc.json');
    scene.load.json('lpc_manifest', BASE + 'manifest.json');
    scene.load.json('lpc_index', BASE + 'lpc_index.json');
  }
  function init(scene) {
    try {
      RULES = scene.cache.json.get('lpc_rules'); MAN = scene.cache.json.get('lpc_manifest');
      IDX = scene.cache.json.get('lpc_index');
      ready = !!(RULES && MAN && IDX);
    } catch (_) { ready = false; }
    return ready;
  }
  const isReady = () => ready;

  // resolve the equipped weapon -> a weapon layer id (name keyword, then weapon_type)
  function weaponLayer(item) {
    if (!item || !RULES) return null;
    const name = String(item.name || '').toLowerCase();
    for (const rule of RULES.weapon_name_keywords) {
      if (rule.keywords.some(k => name.includes(k))) return rule.layer;
    }
    const wt = String(item.weapon_type || item.type || '').toLowerCase();
    return RULES.weapon_type_fallback[wt] || RULES.weapon_type_fallback.slash;
  }
  // body-armor material keyword -> torso stub (light gear reflection)
  function torsoStubFromItem(item, fallback) {
    const n = String((item && item.name) || '').toLowerCase();
    if (/plate|chain|mail|scale/.test(n)) return 'armour/plate';
    if (/leather|hide|studded|jerkin/.test(n)) return 'armour/leather';
    if (/robe|cloth|silk|vestment|cassock/.test(n)) return 'clothes/robe';
    return fallback;
  }

  // {key,url} for a layer's animation sheet via the resolved index, or null if
  // that layer has no sheet for this animation (caller falls back to walk)
  function sheet(layerId, anim, part) {
    const path = IDX && IDX[`${layerId}|${anim}|${part || ''}`];
    if (!path) return null;
    return { key: 'lpc:' + path, url: BASE + path };
  }

  // Build the ordered layer list (bottom->top) for a character spec.
  // Each entry: { z, layerId, part } where part is null|'fg'|'bg'.
  function resolveLoadout(spec) {
    const cls = String((spec && spec.char_class) || 'warrior').toLowerCase();
    const sex = (spec && spec.sex) === 'female' ? 'female' : 'male';
    const eq = (spec && spec.equipment) || {};
    const def = (MAN.class_default_loadouts_PLACEHOLDER || {})[cls] || MAN.class_default_loadouts_PLACEHOLDER.warrior;
    const out = [];
    const body = sex === 'female' ? 'body/bodies/female' : 'body/bodies/male';

    // weapon: prefer the equipped weapon, else the class default
    const wlayer = (eq.wield && weaponLayer(eq.wield)) || (def.wield && WIELD[def.wield]) || null;
    if (wlayer) { out.push({ z: 'weapon_bg', layerId: wlayer, part: 'bg' }); }
    // shield bg
    const slayer = (eq.shield && SHIELD.crusader) || (def.shield && SHIELD[def.shield]) || null;
    if (slayer) out.push({ z: 'shield_bg', layerId: slayer, part: 'bg' });

    out.push({ z: 'body', layerId: body, part: null });

    // legs
    const legsStub = def.legs || 'pants';
    if (LEGS[legsStub]) out.push({ z: 'legs', layerId: LEGS[legsStub], part: null });
    // feet
    if (def.feet && def.feet.startsWith('boots')) out.push({ z: 'feet', layerId: 'feet/boots/basic/male', part: null });
    // torso (reflect equipped body armor material when present)
    const torsoStub = torsoStubFromItem(eq.body, def.torso || 'armour/leather');
    out.push({ z: 'torso', layerId: torsoLayer(torsoStub, sex), part: null });
    // hair
    if (def.hair && HAIR[def.hair]) out.push({ z: 'hair', layerId: HAIR[def.hair], part: null });
    // head/helmet (only if wearing a head item, or class default greathelm)
    const headStub = (eq.head ? 'helmet/greathelm' : def.head);
    if (headStub && HEAD[headStub]) out.push({ z: 'hat_helmet', layerId: HEAD[headStub], part: null });

    // foreground weapon/shield (over the body)
    if (slayer) out.push({ z: 'shield_fg', layerId: slayer, part: 'fg' });
    if (wlayer) out.push({ z: 'weapon_fg', layerId: wlayer, part: 'fg' });

    // sort by manifest z-order
    const zo = MAN.z_order_bottom_to_top;
    out.sort((a, b) => zo.indexOf(a.z) - zo.indexOf(b.z));
    return out;
  }

  // signature for caching/identity
  function sig(spec) {
    const eq = (spec && spec.equipment) || {};
    return [spec && spec.char_class, spec && spec.sex, eq.wield && eq.wield.name,
      eq.shield && 1, eq.body && eq.body.name, eq.head && 1].join('|');
  }

  // queue dynamic loads, debounced into one loader run
  let pending = null, pendCb = [];
  function need(scene, list, done) {
    const missing = list.filter(s => !scene.textures.exists(s.key));
    if (!missing.length) { done(); return; }
    const seen = new Set();
    for (const s of missing) {
      if (seen.has(s.key)) continue; seen.add(s.key);
      scene.load.spritesheet(s.key, s.url, { frameWidth: 64, frameHeight: 64 });
    }
    pendCb.push(done);
    if (!pending) {
      pending = true;
      const fire = () => { pending = false; const cbs = pendCb.slice(); pendCb = []; cbs.forEach(c => { try { c(); } catch (_) {} }); };
      scene.load.once('complete', fire);
      scene.load.once('loaderror', () => {});   // skip missing sheets silently
      scene.load.start();
    }
  }

  // Create a paperdoll. Returns { container, setAction(action,facing), update(now), refresh(spec), destroy() }
  function makeDoll(scene, spec, scale) {
    const container = scene.add.container(0, 0);
    let layers = [];        // [{ z, layerId, part, sprite, cols, anim }]
    let curAnim = 'walk', curRow = 2, frameI = 0, lastStep = 0, moving = false;

    function colsOf(key) {
      try { const t = scene.textures.get(key); const w = t.getSourceImage().width; return Math.max(1, Math.floor(w / 64)); }
      catch (_) { return 9; }
    }
    function build() {
      layers.forEach(l => l.sprite && l.sprite.destroy());
      layers = resolveLoadout(spec).map(L => Object.assign({}, L, { sprite: null, cols: 9, anim: null }));
      // preload the supported anim sheets for all layers, then create sprites
      const want = [];
      layers.forEach(L => ANIMS.forEach(a => { const s = sheet(L.layerId, a, L.part); if (s) want.push(s); }));
      need(scene, want, () => {
        layers.forEach(L => {
          const sh = sheet(L.layerId, 'walk', L.part) || sheet(L.layerId, 'idle', L.part);
          if (!sh || !scene.textures.exists(sh.key)) return;   // layer not in the starter pack
          const spr = scene.add.image(0, 0, sh.key, 0).setOrigin(0.5, 0.78);
          if (scale) spr.setScale(scale);
          L.sprite = spr; container.add(spr);
        });
        applyAnim();
      });
    }
    function applyAnim() {
      layers.forEach(L => {
        if (!L.sprite) return;
        let sh = sheet(L.layerId, curAnim, L.part);
        if (!sh || !scene.textures.exists(sh.key)) sh = sheet(L.layerId, 'walk', L.part);   // fall back to walk
        if (!sh || !scene.textures.exists(sh.key)) sh = sheet(L.layerId, 'idle', L.part);
        if (!sh || !scene.textures.exists(sh.key)) { L.sprite.setVisible(false); return; }
        L.sprite.setVisible(true);
        if (L.sprite.texture.key !== sh.key) L.sprite.setTexture(sh.key);
        L.cols = colsOf(sh.key);
      });
      frameI = 0;
    }
    const doll = {
      container,
      _oneShot: false,
      setAction(action, facing) {
        const anim = ANIM_FILE[action] || 'walk';
        const row = ROW[facing] != null ? ROW[facing] : 2;
        moving = action === 'walk' || action === 'run';
        const oneShot = ['attack', 'slash', 'thrust', 'cast', 'shoot', 'hurt'].includes(action);
        if (anim !== curAnim) { curAnim = anim; curRow = row; applyAnim(); this._oneShot = oneShot; }
        else { curRow = row; if (oneShot) this._oneShot = true; }
      },
      update(now) {
        if (!layers.length) return;
        // idle holds frame 0; walking/attacks step ~10fps
        const animate = moving || this._oneShot;
        if (animate && now - lastStep > 95) { lastStep = now; frameI++; }
        if (!animate) frameI = 0;
        for (const L of layers) {
          if (!L.sprite || !L.sprite.visible) continue;
          const cols = L.cols || 9;
          const f = curRow * cols + (frameI % cols);
          try { L.sprite.setFrame(f); } catch (_) {}
        }
        if (this._oneShot && frameI >= 5) this._oneShot = false;   // end the swing
      },
      refresh(newSpec) { spec = newSpec || spec; build(); },
      destroy() { layers.forEach(l => l.sprite && l.sprite.destroy()); container.destroy(); },
    };
    build();
    return doll;
  }

  // Only TRUE human NPCs get an LPC doll; monsters/beasts/undead keep their
  // distinctive procedural art. Returns a loadout class string, or null.
  const HUMAN_NPC = [
    { re: /guard|soldier|knight|captain|warrior|fighter|gladiator|mercenary|marshal|swordsman|crusader|paladin|legion|sentinel|watch/, cls: 'warrior' },
    { re: /mage|wizard|sorcer|witch|priest|cleric|acolyte|necromanc|warlock|sage|magus|enchant|scholar/, cls: 'mage' },
    { re: /thief|assassin|bandit|rogue|pickpocket|cutpurse|smuggler|burglar|stalker/, cls: 'thief' },
    { re: /ranger|hunter|scout|archer/, cls: 'ranger' },
    { re: /king|queen|noble|prince|princess|regent|mayor|senator|lord|lady|baron|count|duke|duchess|emir|sultan|emperor/, cls: 'bard' },
    { re: /guide|healer|elder|oracle|seer|keeper|herald|crier|squire|page|apprentice|student|recruit|adept|disciple|brother|sister|father|mother|abbot|nun|deacon|bishop|teacher|tutor|scribe|clerk|advisor|councillor|steward|chancellor|ambassador|envoy|emissary|diplomat|courtier|attendant|aide/, cls: 'bard' },
    { re: /citizen|peasant|villager|baker|merchant|grocer|maid|smith|blacksmith|innkeep|barkeep|bartender|farmer|fisher|miner|servant|peddler|vendor|shopkeep|trainer|guildmaster|man\b|woman\b|child|boy|girl|monk|pilgrim|beggar|drunk|sailor|guildsman|cook|porter|guildmistress|townsfolk|stranger|traveler|traveller|wanderer|hermit|tinker|bard|minstrel|jester|dancer|courtesan|barmaid|wench|urchin|waif|laborer|labourer|worker|guildmember/, cls: 'bard' },
  ];
  function humanoidClass(name, charClass) {
    const cc = String(charClass || '').toLowerCase();
    if (['warrior', 'mage', 'cleric', 'thief', 'ranger', 'paladin', 'necromancer', 'bard', 'assassin'].includes(cc)) return cc;
    const n = String(name || '').toLowerCase();
    for (const h of HUMAN_NPC) if (h.re.test(n)) return h.cls;
    return null;
  }

  MH.lpc = { preload, init, isReady, resolveLoadout, weaponLayer, makeDoll, sig, humanoidClass, ANIMS };
})();
