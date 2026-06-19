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
    // the starter pack only ships a female robe, so any female wears it
    if (sex === 'female') return 'torso/clothes/robe/female';
    if (stub === 'armour/plate') return 'torso/armour/plate/male';
    return 'torso/armour/leather/male';   // leather/cloth/robe (no male robe art) -> leather
  }
  const LEGS = { 'armour/plate': 'legs/armour/plate/male', 'pants': 'legs/pants/male' };
  const HEAD = { 'helmet/greathelm': 'hat/helmet/greathelm/male', 'helmet/flattop': 'hat/helmet/flattop/male' };
  const HAIR = { 'flat_top_fade': 'hair/flat_top_fade/male', 'xlong': 'hair/xlong/male' };
  const WIELD = { 'sword/arming': 'weapon/sword/arming/universal', 'magic/diamond': 'weapon/magic/diamond/universal',
    'ranged/bow/recurve': 'weapon/ranged/bow/recurve' };
  const SHIELD = { 'crusader': 'shield/crusader' };

  // ---- procedural face ----------------------------------------------------
  // The starter LPC bodies ship without facial features and the pack has no
  // eyes/head layers, so we paint a minimal face (eyes + a hint of a mouth)
  // ourselves. The bodies are a chibi proportion (figure in the lower half of
  // the 64-cell; head ~y32-46, centred x≈31), and hair/hat/torso art is
  // authored for a taller standard body, so those layers carry vertical
  // offsets (LAYER_DY) to seat them on the body. Eyes sit on the small face
  // window just under the hairline (~y37).
  const FACE = { up: [], left: [[25, 37]], right: [[37, 37]], down: [[27, 37], [34, 37]] };
  // per-layer vertical nudges (cell px) to align the taller-authored gear/hair
  // onto the lower-sitting chibi body. Body/legs/feet/eyes stay at 0.
  const LAYER_DY = { torso: 7, hair: 11, hat_helmet: 11, arms: 7, cape_back: 7, cape_front: 7 };

  // Per-class flavour built from the LPC layers that ship in the pack but the
  // base loadout never used: a hood (hat/cloth/hood), a cape (cape/solid, two
  // parts), and gloves/bracers (arms/*). Each is tinted (multiplied onto the
  // light-grey source art) so a class reads at a glance — a black-hooded,
  // caped assassin vs. a gold-caped paladin vs. a blue-hooded mage — instead of
  // every non-warrior looking like the same person in leather.
  const GLOVES = 'arms/hands/gloves/male';
  const BRACERS = 'arms/bracers/male';
  const HOOD = 'hat/cloth/hood/adult';
  const CAPE = 'cape/solid';
  const CLASS_KIT = {
    warrior:     { hands: { id: GLOVES,  tint: 0x9aa0aa } },                                   // steel gauntlets
    paladin:     { cape: 0xeadf9a, hands: { id: GLOVES, tint: 0xd8c98a } },                    // white-gold mantle
    ranger:      { hood: 0x5e7a44, hands: { id: BRACERS, tint: 0x7a5a38 } },                   // green hood, leather bracers
    thief:       { hood: 0x49434f, hands: { id: GLOVES,  tint: 0x39353f } },                   // dark hood + gloves
    assassin:    { hood: 0x26262e, cape: 0x1b1b24, hands: { id: GLOVES, tint: 0x26262c } },    // black hood, cloak, gloves
    mage:        { hood: 0x3b3b8e, cape: 0x2e2e7e },                                           // deep-blue wizard
    necromancer: { hood: 0x2c2036, cape: 0x1a1426 },                                           // shadowed violet
    cleric:      { hood: 0xdde6f2, cape: 0xe8eef8 },                                           // white priest mantle
    bard:        { cape: 0x9a5fae },                                                            // colourful minstrel cape
  };
  // paint a face for one facing into a 2D context. (sx,sy)=cell top-left in the
  // target, s=pixels-per-source-pixel. Used for both the doll textures (s=1)
  // and the larger inventory portrait.
  function paintFace(ctx, facing, sx, sy, s) {
    if (facing === 'up') return;
    const px = (x, y, w, h, c) => { ctx.fillStyle = c; ctx.fillRect(sx + x * s, sy + y * s, Math.ceil(w * s), Math.ceil(h * s)); };
    for (const [x, y] of (FACE[facing] || [])) {
      px(x, y - 1, 2, 1, 'rgba(60,42,32,0.5)');  // soft brow shadow
      px(x, y, 2, 2, '#2c1e17');                  // eye
      px(x, y, 1, 1, '#5b4636');                  // tiny highlight
    }
    if (facing === 'down') px(30, 40, 4, 1, 'rgba(120,70,58,0.7)');  // mouth
  }
  const EYE_KEY = { up: null, left: 'mh_eyes_left', right: 'mh_eyes_right', down: 'mh_eyes_down' };
  function ensureEyeTextures(scene) {
    for (const facing of ['left', 'right', 'down']) {
      const key = EYE_KEY[facing];
      if (scene.textures.exists(key)) continue;
      const cv = scene.textures.createCanvas(key, 64, 64);
      if (!cv) continue;
      paintFace(cv.getContext(), facing, 0, 0, 1);
      cv.refresh();
    }
  }

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
  // worn item name -> the closest available LPC armor stub for each slot.
  // The starter pack has plate + leather torso/legs, boots, two helms; anything
  // heavier maps to plate, anything lighter to leather/pants.
  const HEAVY = /plate|chain|mail|scale|splint|banded|brigandine|breastplate|cuirass|half-?plate|full plate|lamellar/;
  function torsoStubFromItem(item, fallback) {
    const n = String((item && item.name) || '').toLowerCase();
    if (!n) return fallback;
    if (HEAVY.test(n)) return 'armour/plate';
    if (/leather|hide|studded|jerkin|brigand/.test(n)) return 'armour/leather';
    if (/robe|cloth|silk|vestment|cassock|tunic|shirt|gown/.test(n)) return 'clothes/robe';
    return 'armour/leather';   // worn but unknown -> a basic leather torso
  }
  function legsStubFromItem(item, fallback) {
    if (!item) return fallback;
    const n = String(item.name || '').toLowerCase();
    if (HEAVY.test(n) || /greave|legplate|cuisse|tasset/.test(n)) return 'armour/plate';
    return 'pants';   // leggings / leather / cloth / unknown
  }
  function headStubFromItem(item, fallback) {
    if (!item) return fallback;
    const n = String(item.name || '').toLowerCase();
    if (/great ?helm|full helm|\bhelm(et)?\b|barbut|armet|sallet|bascinet|casque|visor/.test(n)) return 'helmet/greathelm';
    if (/cap|hood|coif|circlet|crown|\bhat\b|cowl|bandana|mask|tiara|diadem/.test(n)) return 'helmet/flattop';
    return 'helmet/flattop';   // worn head item, unknown -> light cap
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
    out.push({ z: 'eyes', layerId: '__eyes__', part: null });  // procedural face

    // legs
    // legs — reflect worn leg armor; a female's legs sit under the robe, so use pants
    const legsStub = sex === 'female' ? 'pants' : legsStubFromItem(eq.legs, def.legs || 'pants');
    if (LEGS[legsStub]) out.push({ z: 'legs', layerId: LEGS[legsStub], part: null });
    // feet — boots when worn (or a class that defaults to them)
    if (eq.feet || (def.feet && def.feet.startsWith('boots'))) out.push({ z: 'feet', layerId: 'feet/boots/basic/male', part: null });
    // torso — reflect worn body armor (heavy->plate, light->leather, female->robe)
    const torsoStub = torsoStubFromItem(eq.body, def.torso || 'armour/leather');
    out.push({ z: 'torso', layerId: torsoLayer(torsoStub, sex), part: null });

    // --- class flavour: gloves/bracers, hood and cape (tinted per class) ---
    const kit = CLASS_KIT[cls] || {};
    // a worn head item still wins (you see what you equipped); only fall back to
    // the class hood when nothing is worn there
    const wornHead = eq.head ? headStubFromItem(eq.head, null) : null;
    const useHood = kit.hood != null && !wornHead;
    if (kit.hands) out.push({ z: 'arms', layerId: kit.hands.id, part: null, tint: kit.hands.tint });
    if (kit.cape != null) {
      out.push({ z: 'cape_back', layerId: CAPE, part: 'bg', tint: kit.cape });
      out.push({ z: 'cape_front', layerId: CAPE, part: 'fg', tint: kit.cape });
    }
    // hair (varied by per-NPC seed so a crowd isn't identical); a hood replaces it
    if (!useHood) {
      const hairStub = (def.hair && spec.seed != null && spec.seed % 3 === 0) ? 'xlong' : def.hair;
      if (hairStub && HAIR[hairStub]) out.push({ z: 'hair', layerId: HAIR[hairStub], part: null });
    }
    // head — worn headgear (heavy helm vs light cap) wins; else class hood; else class default helm
    const headStub = headStubFromItem(eq.head, def.head);
    if (useHood) out.push({ z: 'hat_helmet', layerId: HOOD, part: null, tint: kit.hood });
    else if (headStub && HEAD[headStub]) out.push({ z: 'hat_helmet', layerId: HEAD[headStub], part: null });

    // foreground weapon/shield (over the body)
    if (slayer) out.push({ z: 'shield_fg', layerId: slayer, part: 'fg' });
    if (wlayer) out.push({ z: 'weapon_fg', layerId: wlayer, part: 'fg' });

    // sort by manifest z-order
    const zo = MAN.z_order_bottom_to_top;
    out.sort((a, b) => zo.indexOf(a.z) - zo.indexOf(b.z));
    // the painted face must sit above the body + torso (which would otherwise
    // cover the small head) but below hair/hat — move it just before them
    const ei = out.findIndex(o => o.layerId === '__eyes__');
    if (ei >= 0) {
      const [eye] = out.splice(ei, 1);
      const hi = out.findIndex(o => o.z === 'hair' || o.z === 'hat_helmet');
      out.splice(hi >= 0 ? hi : out.length, 0, eye);
    }
    return out;
  }

  // signature for caching/identity
  function sig(spec) {
    const eq = (spec && spec.equipment) || {};
    const nm = it => (it && it.name) || '';
    return [spec && spec.char_class, spec && spec.sex, spec && spec.seed,
      nm(eq.wield), nm(eq.shield), nm(eq.body), nm(eq.legs), nm(eq.feet), nm(eq.head)].join('|');
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
  function makeDoll(scene, spec, scale, onBuilt) {
    const container = scene.add.container(0, 0);
    let layers = [];        // [{ z, layerId, part, sprite, cols, anim }]
    let curAnim = 'walk', curRow = 2, frameI = 0, lastStep = 0, moving = false;

    function colsOf(key) {
      try { const t = scene.textures.get(key); const w = t.getSourceImage().width; return Math.max(1, Math.floor(w / 64)); }
      catch (_) { return 9; }
    }
    function build() {
      layers.forEach(l => l.sprite && l.sprite.destroy());
      ensureEyeTextures(scene);
      layers = resolveLoadout(spec).map(L => Object.assign({}, L, { sprite: null, cols: 9, anim: null, isEyes: L.layerId === '__eyes__' }));
      // preload the supported anim sheets for all layers, then create sprites
      const want = [];
      layers.forEach(L => { if (L.isEyes) return; ANIMS.forEach(a => { const s = sheet(L.layerId, a, L.part); if (s) want.push(s); }); });
      need(scene, want, () => {
        layers.forEach(L => {
          if (L.isEyes) {
            const spr = scene.add.image(0, 0, EYE_KEY.down).setOrigin(0.5, 0.78);
            if (scale) spr.setScale(scale);
            L.sprite = spr; container.add(spr); return;
          }
          const sh = sheet(L.layerId, 'walk', L.part) || sheet(L.layerId, 'idle', L.part);
          if (!sh || !scene.textures.exists(sh.key)) return;   // layer not in the starter pack
          const spr = scene.add.image(0, 0, sh.key, 0).setOrigin(0.5, 0.78);
          if (scale) spr.setScale(scale);
          spr.y = (LAYER_DY[L.z] || 0) * (scale || 1);   // seat tall-authored gear on the chibi body
          // a class-tinted layer (hood/cape/gloves) carries a base colour the
          // scene multiplies its day/night tint onto (see scene tintCharacters)
          if (L.tint != null) { spr._baseTint = L.tint; spr.setTint(L.tint); }
          L.sprite = spr; container.add(spr);
        });
        applyAnim();
        if (onBuilt) { try { onBuilt(doll); } catch (_) {} }   // e.g. apply day/night tint once layers exist
      });
    }
    function applyAnim() {
      layers.forEach(L => {
        if (!L.sprite || L.isEyes) return;
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
          if (!L.sprite) continue;
          if (L.isEyes) {   // face: pick eye texture by facing; back of head has none
            const key = EYE_KEY[['up', 'left', 'down', 'right'][curRow] || 'down'];
            if (!key) { L.sprite.setVisible(false); }
            else { L.sprite.setVisible(true); if (L.sprite.texture.key !== key) L.sprite.setTexture(key); }
            continue;
          }
          if (!L.sprite.visible) continue;
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

  // Composite a front-facing (down) paperdoll into a 2D canvas for the
  // inventory/equipment portrait. Reuses the same loadout + sheets as the live
  // doll so the portrait reflects equipped gear. Re-runs itself once any
  // missing sheet finishes loading.
  function drawPortrait(scene, spec, canvas) {
    if (!ready) return;
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const row = 2;                       // down / front-facing
    const draw = Math.min(canvas.width, canvas.height) * 0.96;
    const s = draw / 64;
    const ox = (canvas.width - draw) / 2;
    const oy = (canvas.height - draw) / 2;
    let missing = [];
    for (const L of resolveLoadout(spec)) {
      if (L.isEyes || L.layerId === '__eyes__') { paintFace(ctx, 'down', ox, oy, s); continue; }
      const sh = sheet(L.layerId, 'idle', L.part) || sheet(L.layerId, 'walk', L.part);
      if (!sh) continue;
      if (!scene.textures.exists(sh.key)) { missing.push(sh); continue; }
      const img = scene.textures.get(sh.key).getSourceImage();
      const cols = Math.max(1, Math.floor(img.width / 64));
      const f = row * cols;              // frame 0 of the down row
      const dy = (LAYER_DY[L.z] || 0) * s;
      const sx0 = (f % cols) * 64, sy0 = Math.floor(f / cols) * 64;
      if (L.tint != null) {
        // multiply the class tint onto this layer via a scratch canvas so the
        // portrait matches the live doll (hood/cape/gloves colours)
        const sc = document.createElement('canvas'); sc.width = 64; sc.height = 64;
        const sctx = sc.getContext('2d'); sctx.imageSmoothingEnabled = false;
        sctx.drawImage(img, sx0, sy0, 64, 64, 0, 0, 64, 64);
        sctx.globalCompositeOperation = 'multiply';
        const hex = '#' + ('000000' + (L.tint >>> 0).toString(16)).slice(-6);
        sctx.fillStyle = hex; sctx.fillRect(0, 0, 64, 64);
        sctx.globalCompositeOperation = 'destination-in';
        sctx.drawImage(img, sx0, sy0, 64, 64, 0, 0, 64, 64);
        ctx.drawImage(sc, 0, 0, 64, 64, ox, oy + dy, draw, draw);
        continue;
      }
      ctx.drawImage(img, sx0, sy0, 64, 64, ox, oy + dy, draw, draw);
    }
    if (missing.length) need(scene, missing, () => drawPortrait(scene, spec, canvas));
  }

  MH.lpc = { preload, init, isReady, resolveLoadout, weaponLayer, makeDoll, sig, humanoidClass, drawPortrait, ANIMS };
})();
