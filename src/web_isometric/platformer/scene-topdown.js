// Misthollow: Zelda-style top-down room scene (the default view).
// One MUD room = one screen; the four cardinal exits are gaps in the border
// ring — walk off the edge and the screen slides to the next room. Up/down
// are staircase tiles, named passages are portal arches. The MUD server
// stays authoritative exactly as in the side-view client.
(() => {
  const MH = window.MH = window.MH || {};
  const TD = () => MH.TD;

  class TopRoomScene extends Phaser.Scene {
    constructor() {
      super('TopRoom');
      this.layout = null;
      this.entities = new Map();
      this.target = null;
      this.lastVnum = null;
    }

    create() {
      const { W, H, T } = TD();
      this.pxW = W * T; this.pxH = H * T;
      this.physics.world.gravity.y = 0;
      this.physics.world.setBounds(0, 0, this.pxW, this.pxH);
      this.cameras.main.setBounds(0, 0, this.pxW, this.pxH);
      this.cameras.main.setRoundPixels(true);
      // integer zoom for crisp pixels at any window size
      const fit = () => {
        const raw = Math.min(this.scale.width / this.pxW, this.scale.height / this.pxH);
        const z = Phaser.Math.Clamp(Math.floor(raw * 4) / 4, 1.5, 4.5);
        this.cameras.main.setZoom(z);
        this.cameras.main.centerOn(this.pxW / 2, this.pxH / 2);
      };
      fit();
      this.scale.on('resize', fit);

      // cinematic grade (WebGL only): falls back gracefully on canvas
      try {
        if (this.cameras.main.postFX) {
          this.cameras.main.postFX.addVignette(0.5, 0.5, 1.0, 0.32);
          const cm = this.cameras.main.postFX.addColorMatrix();
          cm.saturate(0.14, true);
        }
      } catch (_) { /* older GPU / canvas renderer */ }

      this.solids = this.physics.add.staticGroup();
      this.tileLayer = this.add.layer();
      this.bgLayer = this.add.layer().setDepth(-10);

      this.player = this.physics.add.sprite(this.pxW / 2, this.pxH / 2, 'td_player_warrior', 'd0');
      this.player.setScale(1 / MH.SMOOTH_SS);
      this.player.setSize(11 * MH.SMOOTH_SS, 10 * MH.SMOOTH_SS).setOffset(6.5 * MH.SMOOTH_SS, 12 * MH.SMOOTH_SS);
      this.player.setDepth(10);
      this.player.setCollideWorldBounds(true);
      this.player.body.setAllowGravity(false);
      this.facing = 'd';
      this.physics.add.collider(this.player, this.solids);

      this.heroGlow = this.add.image(this.player.x, this.player.y, 'fx_glow')
        .setBlendMode(Phaser.BlendModes.ADD).setAlpha(0.13).setScale(0.55)
        .setDepth(9).setTint(0xfff2cc);
      this.tweens.add({ targets: this.heroGlow, alpha: 0.18, scale: 0.62, duration: 1600, yoyo: true, repeat: -1, ease: 'sine.inOut' });

      this.keys = this.input.keyboard.addKeys({
        left: 'A', right: 'D', up: 'W', down: 'S',
        left2: 'LEFT', right2: 'RIGHT', up2: 'UP', down2: 'DOWN',
        attack: 'F', attack2: 'SPACE',
      });
      this.input.keyboard.on('keydown-F', () => this.tryAttack());
      this.input.keyboard.on('keydown-SPACE', () => this.tryAttack());

      this.dead = false;
      this.exitSuppress = 0;   // ms timestamp before which exit tiles are inert
      this.autoNav = null;     // {path:[{x,y}], action:{dir}}

      // darkness overlay
      this.darkRT = this.add.renderTexture(0, 0, this.pxW, this.pxH).setOrigin(0, 0).setDepth(40).setVisible(false);
      if (!this.textures.exists('px_light')) {
        const lc = document.createElement('canvas');
        lc.width = lc.height = 256;
        const lctx = lc.getContext('2d');
        const grad = lctx.createRadialGradient(128, 128, 10, 128, 128, 128);
        grad.addColorStop(0, 'rgba(255,255,255,1)');
        grad.addColorStop(1, 'rgba(255,255,255,0)');
        lctx.fillStyle = grad;
        lctx.fillRect(0, 0, 256, 256);
        this.textures.addCanvas('px_light', lc);
      }
      this.nightTint = this.add.rectangle(0, 0, this.pxW, this.pxH, 0x101830, 0).setOrigin(0, 0).setDepth(42);
      this.weatherEmitter = null;
      this.bubbleEmitter = null;

      MH.bus.on('map', payload => this.onMap(payload));
      MH.bus.on('combat.update', payload => this.onCombatUpdate(payload));
      MH.bus.on('combat.hit', e => this.fxHit(e));
      MH.bus.on('combat.miss', e => this.fxMiss(e));
      MH.bus.on('combat.taken', e => this.fxTaken(e));
      MH.bus.on('defense.parry', e => this.fxDeflect('PARRY', 0xd5dde9, e.from));
      MH.bus.on('defense.dodge', e => this.fxSidestep());
      MH.bus.on('defense.block', () => this.fxDeflect('BLOCK', 0xe8c168));
      MH.bus.on('attack.parried', e => this.fxTargetDeflect(e.target, 'parried'));
      MH.bus.on('attack.dodged', e => this.fxTargetDeflect(e.target, 'dodged'));
      MH.bus.on('attack.blocked', e => this.fxTargetDeflect(e.target, 'blocked'));
      this.input.keyboard.on('keydown-TAB', e => { e.preventDefault(); this.cycleTarget(); });
      MH.bus.on('player.exp', e => this.fxExp(e));
      MH.bus.on('walk.step', dir => this.requestMove(dir));
      MH.bus.on('nav.goto', dir => this.navTo(dir));
      MH.bus.on('player.attack', () => this.tryAttack());
      MH.bus.on('combat.flee', e => this.fxFlee(e));
      MH.bus.on('combat.state', on => { if (!on) this.preferredRange = null; });
      MH.bus.on('player.heal', () => this.fxHeal());
      MH.bus.on('terminal.echo', cmd => {
        const c = String(cmd);
        const m = c.match(/^cast '([^']+)'/i);
        if (m) this.lastAbility = { name: m[1], ts: Date.now() };
        else if (this.abilityFxFor(c.split(/\s+/)[0] || '')) this.lastAbility = { name: c.split(/\s+/)[0], ts: Date.now() };
      });
      MH.bus.on('mob.death', e => this.fxMobDeath(e));
      MH.bus.on('player.death', () => this.fxPlayerDeath());
      MH.bus.on('level.up', () => this.fxLevelUp());
      MH.bus.on('move.blocked', e => this.onMoveBlocked(e));
      MH.bus.on('ui.typing', on => { this.input.keyboard.enabled = !on; });
      MH.bus.on('chat', e => this.fxChatBubble(e));
      MH.bus.on('ambient.candidate', e => this.fxAmbient(e));

      if (MH.state.lastPayload) this.onMap(MH.state.lastPayload);
    }

    playerTex() { return MH.tdSprites.playerKey(MH.state.player && MH.state.player.char_class); }

    classRange() {
      const cls = String((MH.state.player && MH.state.player.char_class) || '').toLowerCase();
      return ['mage', 'necromancer', 'cleric', 'bard'].includes(cls) ? 60
        : cls === 'ranger' ? 64 : 24;
    }

    // never render Phaser's NULL missing-texture box: substitute and log
    safeTex(key, fallback) {
      if (this.textures.exists(key)) return key;
      console.warn(`[misthollow] missing texture '${key}', using '${fallback}'`);
      return fallback;
    }

    // ---------- room construction ----------
    buildRoom(layout, entryDir) {
      const { T, BLOCK, WATER } = TD();
      this.layout = layout;
      this.dead = false;
      this.target = null;
      this.autoNav = null;
      this.exitSuppress = Date.now() + 700;
      MH.bus.emit('target.clear');

      this.tileLayer.removeAll(true);
      this.bgLayer.removeAll(true);
      this.solids.clear(true, true);
      for (const ent of this.entities.values()) this.destroyEntity(ent);
      this.entities.clear();
      if (this.exitZones) this.exitZones.forEach(z => z.destroy());
      this.exitZones = [];
      if (this.featureZones) this.featureZones.forEach(z => z.destroy());
      this.featureZones = [];
      this.corpses = [];
      if (this.weatherEmitter) { this.weatherEmitter.destroy(); this.weatherEmitter = null; }
      if (this.bubbleEmitter) { this.bubbleEmitter.destroy(); this.bubbleEmitter = null; }

      const th = layout.theme;
      const zk = layout.zoneKey && this.textures.exists(`zt_${layout.zoneKey}_floor0`) ? layout.zoneKey : null;
      const zt = zk ? MH.ZONE_THEMES[zk] : null;
      const checker = zt && zt.floorKind === 'checker';

      // floor everywhere, then border/obstacles/water from the grid
      const vrng = MH.mulberry32(layout.vnum ^ 0xf10c);
      for (let y = 0; y < layout.H; y++) {
        for (let x = 0; x < layout.W; x++) {
          const cell = layout.grid[y * layout.W + x];
          let img;
          if (zk) {
            // seeded variant mix: mostly plain, some detailed; checker themes alternate dark tiles
            const r = vrng();
            const v = checker ? 0 : (r < 0.55 ? 0 : r < 0.8 ? 1 : 2);
            img = this.add.image(x * T, y * T, `zt_${zk}_floor${v}`).setOrigin(0, 0).setDisplaySize(T, T);
            if (checker && (x + y) % 2) img.setTint(0x3c3a48);
            else if (!checker && (x + y) % 2) img.setTint(0xf6f6f6);
          } else {
            img = this.add.image(x * T, y * T, `td_${th}_floor`).setOrigin(0, 0).setDisplaySize(T, T);
            if ((x + y) % 2) img.setTint(0xf4f4f4);   // subtle checker
          }
          this.bgLayer.add(img);
          if (cell === BLOCK) {
            const isBorder = x === 0 || y === 0 || x === layout.W - 1 || y === layout.H - 1;
            const ob = layout.obstacles && layout.obstacles.find(o =>
              x >= o.x && x < o.x + (o.big ? 2 : 1) && y >= o.y && y < o.y + (o.big ? 2 : 1));
            const key = zk
              ? (isBorder ? `zt_${zk}_border` : `zt_${zk}_obst${ob ? ob.idx % 2 : 0}`)
              : (isBorder ? `td_${th}_border` : `td_${th}_obst${ob ? ob.idx : 0}`);
            const blockImg = this.add.image(x * T, y * T, key).setOrigin(0, 0).setDisplaySize(T, T).setDepth(1);
            this.tileLayer.add(blockImg);
          } else if (cell === WATER) {
            const spr = this.add.sprite(x * T, y * T, 'sm_water', '0').setOrigin(0, 0).setDisplaySize(T, T).setDepth(1).setAlpha(0.95);
            spr.play('sm_water_anim');
            const liquid = (zt && zt.water) || (MH.THEMES[th] && MH.THEMES[th].liquid) || '#3a6a9a';
            spr.setTint(Phaser.Display.Color.HexStringToColor(liquid).color | 0x404040);
            this.tileLayer.add(spr);
          }
        }
      }
      // swimmable rooms get a translucent water wash over the whole floor
      if (layout.swim) {
        const wash = this.add.rectangle(0, 0, this.pxW, this.pxH, 0x1a4a7a, 0.35).setOrigin(0, 0).setDepth(2);
        this.bgLayer.add(wash);
      }

      // merged static bodies per row for BLOCK and (non-swim) WATER cells
      for (let y = 0; y < layout.H; y++) {
        let run = -1;
        for (let x = 0; x <= layout.W; x++) {
          const solid = x < layout.W && (layout.grid[y * layout.W + x] === BLOCK || layout.grid[y * layout.W + x] === WATER);
          if (solid && run < 0) run = x;
          else if (!solid && run >= 0) {
            const zone = this.add.zone(run * T, y * T, (x - run) * T, T).setOrigin(0, 0);
            this.physics.add.existing(zone, true);
            this.solids.add(zone);
            run = -1;
          }
        }
      }

      this.buildFeatures(layout, th);
      this.buildAtmosphere(layout, th);

      // props, gravestones, prose
      const propSet = ['forest', 'field', 'swamp', 'hills'].includes(th)
        ? ['sm_prop_bush', 'sm_prop_bush', 'sm_prop_crate']
        : ['city', 'inside'].includes(th)
          ? ['sm_prop_lamp', 'sm_prop_crate', 'sm_prop_crate']
          : ['sm_prop_crate', 'sm_prop_lamp', 'sm_prop_bush'];
      for (const prop of layout.props) {
        if (prop.name && this.textures.exists(`zt_prop_${prop.name}`)) {
          const img = this.add.image(prop.x * T + T / 2, (prop.y + 1) * T, `zt_prop_${prop.name}`)
            .setOrigin(0.5, 1).setDepth(3).setScale((prop.scale || 1) / MH.SMOOTH_SS);
          this.tileLayer.add(img);
          const glowTint = MH.GLOW_PROPS && MH.GLOW_PROPS[prop.name];
          if (glowTint) {
            const g = this.add.image(prop.x * T + T / 2, prop.y * T + T * 0.3, 'fx_glow')
              .setBlendMode(Phaser.BlendModes.ADD).setAlpha(0.22).setScale(0.32).setTint(glowTint).setDepth(35);
            this.tweens.add({ targets: g, alpha: 0.34, duration: 900 + (prop.x * 137 % 700), yoyo: true, repeat: -1, ease: 'sine.inOut' });
            this.tileLayer.add(g);
          }
        } else {
          const img = this.add.image(prop.x * T, (prop.y + 1) * T, propSet[prop.idx % 3])
            .setOrigin(0.25, 1).setDepth(3).setScale(0.85 / MH.SMOOTH_SS);
          this.tileLayer.add(img);
        }
      }
      this.placeGravestones(layout);
      this.placeProse(layout);

      // place player
      const entry = layout.entries[entryDir] || layout.entries.none;
      this.player.setTexture(this.playerTex(), 'd0');
      this.player.setPosition(entry.x, entry.y);
      this.player.setVelocity(0, 0);
      this.player.clearTint();
      this.player.setAlpha(1);
      this.facing = entryDir === 'north' ? 'd' : entryDir === 'south' ? 'u' : entryDir === 'west' ? 's' : entryDir === 'east' ? 's' : 'd';
      this.player.setFlipX(entryDir === 'east');

      this.darkRT.setVisible(!!layout.dark);
    }

    // Ori-style mood pass: themed light pools, god rays, drifting motes.
    // All procedural, all additive-blended over the pixel art.
    buildAtmosphere(layout, th) {
      const { T } = TD();
      const GLOW = {
        forest: 0xaaffaa, field: 0xffe9a8, hills: 0xffe9a8, mountain: 0xcfe2ff,
        desert: 0xffd9a0, swamp: 0x9fd6a0, inside: 0xffb868, city: 0xffc878,
        dungeon: 0xb08aff, cave: 0xffa868, underwater: 0x66e0ff,
        water_swim: 0x9fd9ff, water_noswim: 0x9fd9ff, flying: 0xffffff, default: 0xaac4ff,
      };
      const zt = layout.zoneKey && MH.ZONE_THEMES ? MH.ZONE_THEMES[layout.zoneKey] : null;
      const glowTint = (zt && zt.glow) || GLOW[th] || GLOW.default;
      const rng = MH.mulberry32(layout.vnum + 777);
      if (this.fxList) this.fxList.forEach(o => o.destroy());
      this.fxList = [];

      // zone mood wash: a whisper of the theme's color over everything
      if (zt && zt.mood) {
        const wash = this.add.rectangle(0, 0, this.pxW, this.pxH, zt.mood, zt.moodA || 0.06)
          .setOrigin(0, 0).setDepth(33).setBlendMode(Phaser.BlendModes.OVERLAY);
        this.fxList.push(wash);
      }

      // soft pools of colored light
      const pools = 2 + Math.floor(rng() * 2);
      for (let i = 0; i < pools; i++) {
        const g = this.add.image(40 + rng() * (this.pxW - 80), 30 + rng() * (this.pxH - 60), 'fx_glow')
          .setBlendMode(Phaser.BlendModes.ADD)
          .setAlpha(0.035 + rng() * 0.035)
          .setScale(1.1 + rng() * 1.1)
          .setTint(glowTint).setDepth(35);
        this.tweens.add({ targets: g, alpha: g.alpha + 0.05, duration: 2400 + rng() * 2200, yoyo: true, repeat: -1, ease: 'sine.inOut' });
        this.fxList.push(g);
      }

      // god rays slanting in from above for sunlit themes
      if (['forest', 'field', 'hills', 'mountain', 'desert', 'swamp', 'water_swim', 'water_noswim', 'flying'].includes(th)) {
        for (let i = 0; i < 3; i++) {
          const ray = this.add.image(60 + rng() * (this.pxW - 120), -8, 'fx_ray')
            .setOrigin(0.5, 0)
            .setBlendMode(Phaser.BlendModes.ADD)
            .setAlpha(0.03 + rng() * 0.03)
            .setRotation(0.25 + rng() * 0.15)
            .setTint(th === 'underwater' ? 0x88d8ff : 0xfff0c0)
            .setDepth(36);
          this.tweens.add({ targets: ray, alpha: ray.alpha + 0.05, x: ray.x + 14, duration: 5200 + rng() * 2600, yoyo: true, repeat: -1, ease: 'sine.inOut' });
          this.fxList.push(ray);
        }
      }
      if (th === 'underwater') {
        for (let i = 0; i < 3; i++) {
          const ray = this.add.image(60 + rng() * (this.pxW - 120), -8, 'fx_ray')
            .setOrigin(0.5, 0).setBlendMode(Phaser.BlendModes.ADD)
            .setAlpha(0.07).setRotation(0.18 + rng() * 0.1).setTint(0x88e0ff).setDepth(36);
          this.tweens.add({ targets: ray, x: ray.x + 18, duration: 6400, yoyo: true, repeat: -1, ease: 'sine.inOut' });
          this.fxList.push(ray);
        }
      }

      // themed ambient weather (zone themes), falling back to drifting motes
      const ambient = zt ? zt.ambient : 'motes';
      const soft = this.textures.exists('zt_px_soft') ? 'zt_px_soft' : 'px_white';
      const leaf = this.textures.exists('zt_px_leaf') ? 'zt_px_leaf' : 'px_white';
      const fullX = { min: 10, max: this.pxW - 10 };
      const addAmb = cfg => {
        const p = this.add.particles(0, 0, cfg.tex || soft, cfg).setDepth(34);
        this.fxList.push(p);
        return p;
      };
      if (ambient === 'leaves' || ambient === 'petals') {
        addAmb({
          tex: leaf, x: fullX, y: -8,
          tint: ambient === 'petals' ? [0xf0b8d0, 0xffe0ec, 0xe89ab8] : [0xc8d870, 0xe0b860, 0xa8c860],
          scale: { start: 0.32, end: 0.22 }, alpha: { start: 0.9, end: 0 },
          speedY: { min: 12, max: 26 }, speedX: { min: -14, max: 14 },
          rotate: { start: 0, end: 360 }, lifespan: 11000, frequency: 560,
        });
      } else if (ambient === 'snow') {
        addAmb({
          x: fullX, y: -6, tint: 0xffffff,
          scale: { start: 0.34, end: 0.2 }, alpha: { start: 0.85, end: 0.1 },
          speedY: { min: 14, max: 30 }, speedX: { min: -10, max: 10 },
          lifespan: 10000, frequency: 220,
        });
      } else if (ambient === 'embers' || ambient === 'sparks') {
        addAmb({
          x: fullX, y: this.pxH + 4,
          tint: ambient === 'sparks' ? [0xffe9a8, 0xffc868] : [0xff9a4a, 0xff5a2a, 0xffd080],
          scale: { start: 0.3, end: 0.05 }, alpha: { start: 0.9, end: 0 },
          speedY: { min: -34, max: -14 }, speedX: { min: -8, max: 8 },
          lifespan: 5200, frequency: ambient === 'sparks' ? 480 : 300, blendMode: 'ADD',
        });
      } else if (ambient === 'ash') {
        addAmb({
          x: fullX, y: -6, tint: [0x9a9a9a, 0x6e6a66, 0xc0b8b0],
          scale: { start: 0.26, end: 0.12 }, alpha: { start: 0.6, end: 0 },
          speedY: { min: 8, max: 18 }, speedX: { min: -12, max: 12 },
          lifespan: 12000, frequency: 420,
        });
      } else if (ambient === 'bubbles') {
        addAmb({
          x: fullX, y: this.pxH + 4, tint: 0xbfe8ff,
          scale: { start: 0.16, end: 0.4 }, alpha: { start: 0.55, end: 0 },
          speedY: { min: -26, max: -12 }, speedX: { min: -6, max: 6 },
          lifespan: 8000, frequency: 380, blendMode: 'ADD',
        });
      } else if (ambient === 'fireflies') {
        const ff = addAmb({
          x: fullX, y: { min: 20, max: this.pxH - 20 }, tint: [0xbfff80, 0xdfff9a],
          scale: { start: 0.4, end: 0.08 }, alpha: { start: 0.9, end: 0 },
          speedX: { min: -14, max: 14 }, speedY: { min: -10, max: 10 },
          lifespan: 4200, frequency: 520, blendMode: 'ADD',
        });
      } else if (ambient === 'stars') {
        addAmb({
          x: fullX, y: { min: 10, max: this.pxH - 10 }, tint: [0xffffff, 0xb0a8ff, 0x9ad8ff],
          scale: { start: 0.05, end: 0.4 }, alpha: { start: 0, end: 0.9 },
          speedX: 0, speedY: 0, lifespan: 2600, frequency: 360, blendMode: 'ADD',
        });
      } else if (ambient === 'drips') {
        addAmb({
          x: fullX, y: -4, tint: 0x9fd6a0,
          scale: { start: 0.22, end: 0.1 }, alpha: { start: 0.7, end: 0 },
          speedY: { min: 60, max: 110 }, speedX: 0,
          lifespan: 2400, frequency: 700,
        });
      } else if (ambient === 'mist') {
        addAmb({
          x: fullX, y: { min: this.pxH * 0.4, max: this.pxH - 14 }, tint: 0xaac8aa,
          scale: { start: 1.6, end: 3.2 }, alpha: { start: 0.0, end: 0.10 },
          speedX: { min: 4, max: 14 }, speedY: { min: -2, max: 2 },
          lifespan: 9000, frequency: 800, blendMode: 'SCREEN',
        });
      } else if (ambient === 'dust') {
        addAmb({
          x: -8, y: { min: 16, max: this.pxH - 16 }, tint: 0xe8d8a8,
          scale: { start: 0.3, end: 0.1 }, alpha: { start: 0.4, end: 0 },
          speedX: { min: 26, max: 52 }, speedY: { min: -4, max: 4 },
          lifespan: 9000, frequency: 520,
        });
      } else if (ambient === 'spores') {
        addAmb({
          x: fullX, y: { min: 14, max: this.pxH - 14 }, tint: [0xb06ce0, 0xd8a0ff],
          scale: { start: 0.28, end: 0.06 }, alpha: { start: 0.7, end: 0 },
          speedX: { min: -8, max: 8 }, speedY: { min: -12, max: -2 },
          lifespan: 6500, frequency: 460, blendMode: 'ADD',
        });
      } else {
        const moteTint = ['forest', 'swamp'].includes(th) ? 0xbfff80
          : ['dungeon', 'cave', 'inside', 'default'].includes(th) ? 0xd8c8a0
          : glowTint;
        addAmb({
          tex: 'px_white',
          x: { min: 20, max: this.pxW - 20 }, y: { min: 20, max: this.pxH - 20 },
          scale: { start: 0.5, end: 0.1 }, alpha: { start: 0.5, end: 0 },
          tint: moteTint, speedX: { min: -6, max: 6 }, speedY: { min: -8, max: 2 },
          lifespan: 7000, frequency: 420, blendMode: 'ADD',
        });
      }

      // glows on the travel features
      const featureGlow = (x, y, tint, scale = 0.45, alpha = 0.3) => {
        const g = this.add.image(x, y, 'fx_glow').setBlendMode(Phaser.BlendModes.ADD)
          .setAlpha(alpha).setScale(scale).setTint(tint).setDepth(35);
        this.tweens.add({ targets: g, alpha: alpha + 0.12, duration: 1200, yoyo: true, repeat: -1, ease: 'sine.inOut' });
        this.fxList.push(g);
      };
      if (layout.stairsUp) featureGlow(layout.stairsUp.x * T + T / 2, layout.stairsUp.y * T + T / 2, 0xffe9a8);
      if (layout.stairsDown) featureGlow(layout.stairsDown.x * T + T / 2, layout.stairsDown.y * T + T / 2, 0x8899ff, 0.4, 0.22);
      for (const p of layout.portals) featureGlow(p.x * T + T / 2, p.y * T + T / 2, 0xc080ff, 0.55, 0.35);
    }

    buildFeatures(layout, th) {
      const { T } = TD();
      const addExitZone = (x, y, w, h, dir) => {
        const zone = this.add.zone(x, y, w, h).setOrigin(0, 0);
        this.physics.add.existing(zone, true);
        zone.exitDir = dir;
        this.exitZones.push(zone);
      };
      const signpost = (dir, x, y) => {
        const zone = layout.exits[dir] && layout.exits[dir].to_zone;
        if (!zone) return;
        const post = this.add.text(x, y, `→ ${zone}`, {
          fontFamily: 'Trebuchet MS, Verdana, sans-serif', resolution: 3, fontSize: '7px', fontStyle: 'italic', color: '#e8c168',
          backgroundColor: '#10131ea8', padding: { x: 2, y: 1 },
        }).setOrigin(0.5, 0.5).setDepth(5).setAlpha(0.9);
        this.tileLayer.add(post);
      };
      const doorIn = dir => {
        const d = layout.exits[dir] && layout.exits[dir].door;
        if (d && d.state !== 'open') return d;
        return null;
      };
      const drawDoor = (dir, x, y, vertical) => {
        if (!doorIn(dir)) return;
        const img = this.add.image(x, y, `t_${th}_door`).setOrigin(0.5, 0.5).setDepth(4)
          .setDisplaySize(vertical ? 12 : 40, vertical ? 40 : 12);
        img.doorDir = dir;
        this.tileLayer.push ? this.tileLayer.push(img) : this.tileLayer.add(img);
      };

      const midX = Math.floor(layout.W / 2), midY = Math.floor(layout.H / 2);
      if (layout.gaps.north) {
        addExitZone((midX - 2) * T, -6, 5 * T, T * 0.8, 'north');
        signpost('north', midX * T + T / 2, 2.4 * T);
        drawDoor('north', midX * T + T / 2, 0.5 * T, false);
      }
      if (layout.gaps.south) {
        addExitZone((midX - 2) * T, (layout.H - 0.4) * T, 5 * T, T, 'south');
        signpost('south', midX * T + T / 2, (layout.H - 2.4) * T);
        drawDoor('south', midX * T + T / 2, (layout.H - 0.5) * T, false);
      }
      if (layout.gaps.west) {
        addExitZone(-6, (midY - 2) * T, T * 0.8, 5 * T, 'west');
        signpost('west', 3.6 * T, midY * T + T / 2);
        drawDoor('west', 0.5 * T, midY * T + T / 2, true);
      }
      if (layout.gaps.east) {
        addExitZone((layout.W - 0.4) * T, (midY - 2) * T, T, 5 * T, 'east');
        signpost('east', (layout.W - 3.6) * T, midY * T + T / 2);
        drawDoor('east', (layout.W - 0.5) * T, midY * T + T / 2, true);
      }
      const addFeatureZone = (fx, fy, dir, texKey) => {
        const img = this.add.image(fx * T, fy * T, texKey).setOrigin(0, 0).setDisplaySize(T, T).setDepth(2);
        this.tileLayer.add(img);
        const zone = this.add.zone(fx * T + 5, fy * T + 5, T - 10, T - 10).setOrigin(0, 0);
        this.physics.add.existing(zone, true);
        zone.exitDir = dir;
        this.featureZones.push(zone);
      };
      if (layout.stairsUp) {
        addFeatureZone(layout.stairsUp.x, layout.stairsUp.y, 'up', 'td_stairs_up');
        signpost('up', layout.stairsUp.x * T + T / 2, (layout.stairsUp.y - 1) * T);
      }
      if (layout.stairsDown) {
        addFeatureZone(layout.stairsDown.x, layout.stairsDown.y, 'down', 'td_stairs_down');
        signpost('down', layout.stairsDown.x * T + T / 2, (layout.stairsDown.y - 1) * T);
      }
      for (const p of layout.portals) {
        const spr = this.add.sprite(p.x * T + T / 2, (p.y + 1) * T, 'sm_portal', '0').setOrigin(0.5, 1).setDepth(3).setScale(0.75 / MH.SMOOTH_SS);
        spr.play('sm_portal_anim');
        this.tileLayer.add(spr);
        const zone = this.add.zone(p.x * T, p.y * T, T, T).setOrigin(0, 0);
        this.physics.add.existing(zone, true);
        zone.exitDir = p.name;
        this.featureZones.push(zone);
        const hint = this.add.text(p.x * T + T / 2, (p.y - 1.2) * T, p.name, {
          fontFamily: 'Trebuchet MS, Verdana, sans-serif', resolution: 3, fontSize: '7px', color: '#b87cf0',
        }).setOrigin(0.5, 1).setDepth(3);
        this.tileLayer.add(hint);
        signpost(p.name, p.x * T + T / 2, (p.y - 2) * T);
      }
    }

    placeProse(layout) {
      if (!layout.description) return;
      const rng = MH.mulberry32(layout.vnum + 99);
      const frags = layout.description.replace(/\n/g, ' ').split(/(?<=[.!?])\s+/)
        .map(s => s.trim()).filter(s => s.length > 15 && s.length <= 60);
      Phaser.Utils.Array.Shuffle(frags);
      frags.slice(0, 2).forEach((frag, i) => {
        const tx = this.add.text(36 + rng() * (this.pxW - 260), 28 + i * 26, frag, {
          fontFamily: 'Georgia, serif', resolution: 3, fontSize: '8px', fontStyle: 'italic', color: '#fdf6e3',
        }).setAlpha(0.20).setDepth(4).setShadow(0, 1, '#000000', 2);
        this.tweens.add({ targets: tx, y: tx.y - 6, duration: 9000 + rng() * 3000, yoyo: true, repeat: -1, ease: 'sine.inOut' });
        this.bgLayer.add(tx);
      });
    }

    deathLog() {
      try { return JSON.parse(localStorage.getItem('misthollow_deaths')) || []; } catch (_) { return []; }
    }
    recordDeath() {
      if (!this.layout) return;
      const deaths = this.deathLog();
      deaths.push({ vnum: this.layout.vnum, name: MH.state.playerName, ts: Date.now() });
      while (deaths.length > 25) deaths.shift();
      try { localStorage.setItem('misthollow_deaths', JSON.stringify(deaths)); } catch (_) {}
    }
    placeGravestones(layout) {
      const { T } = TD();
      const stones = Array.isArray(layout.gravestones)
        ? layout.gravestones
        : this.deathLog().filter(d => d.vnum === layout.vnum);
      stones.slice(0, 5).forEach((d, i) => {
        const sx = (4 + (MH.hashStr(String(d.ts) + (d.name || '')) % (layout.W - 8))) * T;
        const sy = (3 + ((MH.hashStr(d.name || 'x') + i) % (layout.H - 6))) * T;
        const g = this.add.image(sx, sy, 'sm_grave').setOrigin(0.5, 1).setDepth(3).setScale(0.85 / MH.SMOOTH_SS);
        this.tileLayer.add(g);
        const slain = d.killer ? `${d.name}, slain by ${d.killer}` : d.name;
        const label = this.add.text(sx, sy - 18, `here lies ${slain}`, {
          fontFamily: 'Trebuchet MS, Verdana, sans-serif', resolution: 3, fontSize: '7px', fontStyle: 'italic', color: '#8a90a4',
        }).setOrigin(0.5, 1).setAlpha(0.7).setDepth(3);
        this.tileLayer.add(label);
      });
    }

    // ---------- entities ----------
    syncEntities(roomEntry) {
      if (!this.layout) return;
      const want = new Map();
      (roomEntry.mobs || []).forEach((mob, i) => want.set(`mob:${mob.name}:${i}`, { kind: 'mob', data: mob, idx: i }));
      (roomEntry.players || []).forEach((p, i) => want.set(`pl:${p.name}`, { kind: 'player', data: p, idx: i + 4 }));
      (roomEntry.items || []).forEach((it, i) => want.set(`it:${it.name}:${i}`, { kind: 'item', data: it, idx: i }));
      for (const [key, ent] of this.entities) {
        if (!want.has(key)) { this.destroyEntity(ent); this.entities.delete(key); }
      }
      for (const [key, spec] of want) {
        const existing = this.entities.get(key);
        if (existing) { this.updateEntity(existing, spec.data); continue; }
        this.entities.set(key, this.spawnEntity(key, spec));
      }
    }

    spawnEntity(key, spec) {
      const slots = this.layout.spawnSlots;
      const slot = slots[(MH.hashStr(key) + spec.idx) % slots.length];
      const ent = { key, kind: spec.kind, data: spec.data };

      if (spec.kind === 'item') {
        const isCorpse = /corpse/i.test(spec.data.name || '');
        const texKey = isCorpse ? 'sm_corpse' : this.safeTex(MH.smoothSprites.itemKey(spec.data.type), 'fx_glow');
        ent.sprite = this.add.image(slot.x, slot.y, texKey).setDepth(5).setScale(0.9 / MH.SMOOTH_SS);
        if (!isCorpse) {
          this.tweens.add({ targets: ent.sprite, y: slot.y - 3, duration: 900, yoyo: true, repeat: -1, ease: 'sine.inOut' });
        }
        ent.sprite.setInteractive({ useHandCursor: true });
        ent.sprite.on('pointerdown', () => {
          if (isCorpse) MH.bus.emit('loot.corpse');
          else MH.sendCommand(`get ${MH.mobKeyword(spec.data.name)}`);
        });
        if (isCorpse) {
          ent.label = this.add.text(slot.x, slot.y - 12, this.shortName(spec.data.name), {
            fontFamily: 'Trebuchet MS, Verdana, sans-serif', resolution: 3, fontSize: '6px', color: '#9a8f80',
          }).setOrigin(0.5, 1).setDepth(5).setAlpha(0.8);
        }
        return ent;
      }

      const tex = this.safeTex(spec.kind === 'player' ? MH.tdSprites.playerKey(spec.data.char_class) : MH.tdSprites.mobKey(spec.data.name), 'td_mob_citizen');
      ent.sprite = this.add.sprite(slot.x, slot.y, tex, 'd0').setDepth(8);
      ent.sprite.setScale((spec.data.boss ? 1.5 : 1) / MH.SMOOTH_SS);
      ent.sprite.play(`${tex}_walkd`);
      ent.sprite.anims.pause();
      ent.homeX = slot.x; ent.homeY = slot.y;

      const labelColor = spec.kind === 'player' ? '#6ca8e0' : (spec.data.hostile ? '#e06c6c' : (spec.data.shopkeeper ? '#e8c168' : '#c8ccd8'));
      ent.label = this.add.text(slot.x, slot.y - 18, this.shortName(spec.data.name), {
        fontFamily: 'Trebuchet MS, Verdana, sans-serif', resolution: 3, fontSize: '7px', color: labelColor,
      }).setOrigin(0.5, 1).setDepth(9);
      ent.hpbar = this.add.graphics().setDepth(9);
      this.drawHpBar(ent);

      ent.sprite.setInteractive({ useHandCursor: true });
      ent.sprite.on('pointerdown', pointer => {
        if (spec.kind !== 'mob') return;
        if (spec.data.shopkeeper) MH.bus.emit('shop.open', spec.data);
        else if (ent.data.hostile || ent.data.fighting || (pointer.event && pointer.event.shiftKey)) this.attackEntity(ent);
        else MH.bus.emit('npc.talk', { name: ent.data.name, quest: ent.data.quest || '' });
      });
      this.updateQuestMark(ent);
      ent.sprite.on('pointerover', pointer => MH.bus.emit('mob.tip', { data: ent.data, kind: ent.kind, x: pointer.event.clientX, y: pointer.event.clientY }));
      ent.sprite.on('pointermove', pointer => MH.bus.emit('mob.tip', { data: ent.data, kind: ent.kind, x: pointer.event.clientX, y: pointer.event.clientY }));
      ent.sprite.on('pointerout', () => MH.bus.emit('mob.tip.hide'));

      // idle breathing: everything alive moves a little
      ent.breath = this.tweens.add({
        targets: ent.sprite, scaleY: ent.sprite.scaleY * 1.04, duration: 1100 + (MH.hashStr(key) % 600),
        yoyo: true, repeat: -1, ease: 'sine.inOut', delay: MH.hashStr(key) % 800,
      });
      if (spec.kind === 'mob' && !spec.data.shopkeeper) {
        if (spec.data.hostile) ent.stalker = true;
        else ent.wanderAt = Date.now() + 1500 + (MH.hashStr(key) % 3000);
      }
      return ent;
    }

    updateQuestMark(ent) {
      const q = ent.data && ent.data.quest;
      if (q && !ent.questMark) {
        ent.questMark = this.add.text(ent.sprite.x, ent.sprite.y - 26, q, {
          fontFamily: 'Georgia, serif', resolution: 3, fontSize: '14px', fontStyle: 'bold',
          color: q === '?' ? '#7dff9a' : '#ffd44a', stroke: '#000', strokeThickness: 3,
        }).setOrigin(0.5, 1).setDepth(20);
        this.tweens.add({ targets: ent.questMark, y: ent.questMark.y - 4, duration: 700, yoyo: true, repeat: -1, ease: 'sine.inOut' });
      } else if (!q && ent.questMark) {
        ent.questMark.destroy();
        ent.questMark = null;
      } else if (q && ent.questMark) {
        ent.questMark.setText(q).setColor(q === '?' ? '#7dff9a' : '#ffd44a');
      }
    }

    updateEntity(ent, data) {
      ent.data = data;
      this.drawHpBar(ent);
      this.updateQuestMark(ent);
      // loud telegraph: red swords + red name over whoever is attacking YOU
      if (data.fighting && !ent.fightMark) {
        ent.fightMark = this.add.text(ent.sprite.x, ent.sprite.y - 26, '⚔', {
          fontFamily: 'Trebuchet MS, Verdana, sans-serif', resolution: 3, fontSize: '12px', color: '#ff5050', stroke: '#000', strokeThickness: 2,
        }).setOrigin(0.5, 1).setDepth(20);
        this.tweens.add({ targets: ent.fightMark, scale: 1.3, duration: 380, yoyo: true, repeat: -1 });
        if (ent.label) ent.label.setColor('#ff5050');
      } else if (!data.fighting && ent.fightMark) {
        ent.fightMark.destroy();
        ent.fightMark = null;
        if (ent.label) ent.label.setColor(ent.kind === 'player' ? '#6ca8e0' : (data.hostile ? '#e06c6c' : '#c8ccd8'));
      }
      if (this.target && this.target.key === ent.key) MH.bus.emit('target.update', data);
    }
    drawHpBar(ent) {
      if (!ent.hpbar) return;
      ent.hpbar.clear();
      const max = ent.data.maxHp || ent.data.max_hp;
      const hp = ent.data.hp;
      if (!max || hp == null) return;
      const frac = Math.max(0, Math.min(1, hp / max));
      // badly wounded mobs visibly smolder
      if (frac < 0.3 && !ent.smoke && ent.sprite) {
        ent.smoke = this.add.particles(0, 0, 'px_poof', {
          follow: ent.sprite, followOffset: { x: 0, y: -8 },
          speedY: { min: -16, max: -8 }, lifespan: 900, frequency: 350,
          scale: { start: 0.5, end: 0 }, alpha: { start: 0.4, end: 0 },
        }).setDepth(7);
      } else if (frac >= 0.3 && ent.smoke) {
        ent.smoke.destroy();
        ent.smoke = null;
      }
      const x = ent.sprite.x - 9, y = ent.sprite.y - 16;
      ent.hpbar.fillStyle(0x000000, 0.7).fillRect(x, y, 18, 2);
      ent.hpbar.fillStyle(frac > 0.5 ? 0x6fd685 : frac > 0.25 ? 0xe8c168 : 0xe06c6c, 1).fillRect(x, y, 18 * frac, 2);
    }
    destroyEntity(ent) {
      if (ent.patrol) ent.patrol.stop();
      if (ent.breath) ent.breath.stop();
      if (ent.wanderTween) ent.wanderTween.stop();
      if (ent.smoke) ent.smoke.destroy();
      ['sprite', 'label', 'hpbar', 'fightMark', 'questMark'].forEach(k => { if (ent[k]) ent[k].destroy(); });
    }
    shortName(name) {
      const n = String(name || '');
      return n.length > 20 ? n.slice(0, 19) + '…' : n;
    }

    // ---------- combat ----------
    nearestMob(maxDist = 60, arcFacing = null) {
      let best = null, bestD = maxDist;
      const fdx = { d: 0, u: 0, s: this.player.flipX ? -1 : 1 }[arcFacing] ?? 0;
      const fdy = { d: 1, u: -1, s: 0 }[arcFacing] ?? 0;
      for (const ent of this.entities.values()) {
        if (ent.kind !== 'mob' || ent.data.shopkeeper) continue;
        const dx = ent.sprite.x - this.player.x, dy = ent.sprite.y - this.player.y;
        const d = Math.hypot(dx, dy);
        if (d >= bestD) continue;
        if (arcFacing && d > 18) {
          const dot = (dx * fdx + dy * fdy) / (d || 1);
          if (dot < 0.3) continue; // outside the thrust arc
        }
        best = ent; bestD = d;
      }
      return best;
    }
    tryAttack() {
      if (this.dead || !this.layout) return;
      // sword thrust animation regardless
      const tex = this.playerTex();
      this.afterimage(this.player, 0xd0e0ff);
      this.player.setFrame(`atk_${this.facing}`);
      this.time.delayedCall(180, () => { if (!this.dead) this.player.setFrame(`${this.facing}0`); });
      if (this.layout.peaceful) { MH.bus.emit('flash', 'A calm presence here forbids violence.'); return; }
      const ent = this.target && this.entities.has(this.target.key) ? this.entities.get(this.target.key) : this.nearestMob(60, this.facing);
      if (!ent) return;
      this.attackEntity(ent);
    }
    attackEntity(ent) {
      this.target = ent;
      MH.bus.emit('target.set', ent.data);
      MH.sendCommand(`kill ${MH.mobKeyword(ent.data.name)}`);
      // face the target
      const dx = ent.sprite.x - this.player.x, dy = ent.sprite.y - this.player.y;
      this.facing = Math.abs(dx) > Math.abs(dy) ? 's' : (dy > 0 ? 'd' : 'u');
      this.player.setFlipX(this.facing === 's' && dx < 0);
      this.player.setFrame(`atk_${this.facing}`);
      this.time.delayedCall(180, () => { if (!this.dead) this.player.setFrame(`${this.facing}0`); });
    }
    findEntityByText(text) {
      const lower = String(text || '').toLowerCase();
      for (const ent of this.entities.values()) {
        if (ent.kind !== 'mob') continue;
        const name = String(ent.data.name || '').toLowerCase();
        if (lower.includes(MH.mobKeyword(name)) || name.includes(lower) || lower.includes(name)) return ent;
      }
      return null;
    }

    // ---------- per-class ability effects ----------
    // every class reads differently in combat: warriors shock the earth,
    // rangers loose arrows, necromancers drain life, bards weaponize music
    // Audited from config.CLASSES: 70 skills + 100 spells across 9 classes.
    // Every ability gets a visual TYPE, a COLOR, and a RANGE class that
    // drives positioning: melee abilities step you in, ranged ones hold
    // distance, self/ally effects play on you.
    static ABILITY_FX = [
      // --- precision strikes & shadow work ---
      [/backstab|assassinate|garrote|execute_contract|execute contract|vital/i, { type: 'shadowstrike', color: 0x8a8af0, range: 'melee' }],
      [/shadow.?step|vanish|sneak|hide|invisibility|blink/i,                    { type: 'stealth', color: 0x6a6af0, range: 'self' }],
      [/feint|trip|low.?blow|circle/i,                                          { type: 'impact', color: 0xc0c8d8, range: 'melee' }],
      [/pocket.?sand/i,                                                         { type: 'cone', color: 0xd8c08a, range: 'close' }],
      [/steal|rigged|jackpot/i,                                                 { type: 'coins', color: 0xffd44a, range: 'melee' }],
      [/mark|expose|hunters.?mark|track|scan/i,                                 { type: 'mark', color: 0xff5050, range: 'ranged' }],
      // --- warrior steel ---
      [/bash|slam|hammer of justice/i,                                          { type: 'shockwave', color: 0xd8c8a0, range: 'melee' }],
      [/cleave|whirlwind|divine.?storm/i,                                       { type: 'bigslash', color: 0xffffff, range: 'melee' }],
      [/charge|death.?grip/i,                                                   { type: 'dash', color: 0xd8c8a0, range: 'ranged' }],
      [/kick|punch|strike|smite$|execute/i,                                     { type: 'impact', color: 0xffe080, range: 'melee' }],
      [/rally|heroism|oath|doctrine|swear|evolve|briskness|haste|icy.?veins|time.?warp/i, { type: 'rally', color: 0xffd44a, range: 'self' }],
      // --- ranger ---
      [/aimed.?shot|rapid.?fire|kill.?command|shot|arrow/i,                     { type: 'arrow', color: 0xd8e8c0, range: 'ranged' }],
      [/entangle|barkskin/i,                                                    { type: 'vines', color: 0x6ab04a, range: 'ranged' }],
      [/faerie.?fire/i,                                                         { type: 'mark', color: 0xd070ff, range: 'ranged' }],
      // --- holy ---
      [/holy.?smite|holy.?fire|flamestrike|judgement|templars|crusaders|divine.?word|word.?of.?glory|dispel.?evil/i, { type: 'column', color: 0xffe9a0, range: 'ranged' }],
      [/turn.?undead|consecration|righteous|avenging/i,                         { type: 'nova', color: 0xffe9a0, range: 'self' }],
      [/cure|heal|mend|lightwell|serenity|resurrect|spirit.?link|word.?of.?recall/i, { type: 'healburst', color: 0x7dff9a, range: 'ally' }],
      [/bless|sanctuary|aegis|holy.?aura|divine.?(shield|protection|intervention)|shield.?of.?faith|hand.?of.?freedom|protection.?from/i, { type: 'buff', color: 0xffe9a0, range: 'self' }],
      // --- necromancy ---
      [/drain|vampiric|energy.?drain|soul.?(reap|harvest)/i,                    { type: 'drain', color: 0xb05ae0, range: 'ranged' }],
      [/chill.?touch|plague.?strike|touch/i,                                    { type: 'touch', color: 0x9adcff, range: 'melee' }],
      [/soul.?bolt|death.?coil|finger.?of.?death|harm$|enervation/i,            { type: 'bolt', color: 0xb05ae0, range: 'ranged' }],
      [/fear|weaken|blindness|curse|mockery|slow$/i,                            { type: 'debuff', color: 0x8a4ad6, range: 'ranged' }],
      [/poison|venom|acid/i,                                                    { type: 'debuff', color: 0x9ee05a, range: 'ranged' }],
      [/animate.?dead|summon|gargoyle|corpse.?shield|bone.?shield|apocalypse/i, { type: 'nova', color: 0x8a4ad6, range: 'self' }],
      // --- bard ---
      [/song|sing|chant|dirge|melody|sonic|note|discord|crescendo|encore|requiem|hymn|chord|epic.?tale|magnum|countersong|fascinate|charm|siren/i, { type: 'notes', color: 0xffa8d8, range: 'ranged' }],
      [/sleep/i,                                                                { type: 'sleep', color: 0xb8c4e8, range: 'ranged' }],
      // --- arcane artillery ---
      [/magic.?missile|arcane.?barrage/i,                                       { type: 'missiles', color: 0xc792ff, range: 'ranged' }],
      [/burning.?hands|color.?spray|breathes|breath/i,                          { type: 'cone', color: 0xff8a3c, range: 'close' }],
      [/fireball|combustion/i,                                                  { type: 'bigbolt', color: 0xff8a3c, range: 'ranged' }],
      [/meteor/i,                                                               { type: 'meteor', color: 0xff8a3c, range: 'ranged' }],
      [/chain.?lightning/i,                                                     { type: 'chainzap', color: 0x9adcff, range: 'ranged' }],
      [/lightning|call.?lightning|shock|storm/i,                                { type: 'zap', color: 0x9adcff, range: 'ranged' }],
      [/arcane.?(blast|explosion)|earthquake/i,                                 { type: 'nova', color: 0xc792ff, range: 'self' }],
      [/frost|ice|chill|cold/i,                                                 { type: 'bolt', color: 0xbfeaff, range: 'ranged' }],
      [/fire|burn|flame|inferno/i,                                              { type: 'bolt', color: 0xff8a3c, range: 'ranged' }],
      [/armor|shield$|stoneskin|mirror.?image|displacement|mana.?shield|spell.?reflection|ice.?armor|fire.?shield/i, { type: 'buff', color: 0x9adcff, range: 'self' }],
      [/missile|arcane|magic|blast/i,                                           { type: 'bolt', color: 0xc792ff, range: 'ranged' }],
    ];
    abilityFxFor(text) {
      for (const [re, fx] of TopRoomScene.ABILITY_FX) {
        if (re.test(text)) return fx;
      }
      return null;
    }
    playAbilityFx(fx, target) {
      const tx = target ? target.x : this.player.x + 30;
      const ty = target ? target.y : this.player.y;
      // range drives positioning: melee/close abilities step you in,
      // ranged ones back you off - distance becomes legible
      const dist = Math.hypot(tx - this.player.x, ty - this.player.y);
      this.preferredRange = { melee: 24, close: 30, ranged: 64 }[fx.range] || this.preferredRange;
      const M = TD().T * 1.6;
      if ((fx.range === 'melee' && dist > 30) || (fx.range === 'close' && dist > 40)) {
        const want = fx.range === 'melee' ? 20 : 30;
        const ang = Math.atan2(ty - this.player.y, tx - this.player.x);
        this.tweens.add({
          targets: this.player,
          x: Phaser.Math.Clamp(tx - Math.cos(ang) * want, M, this.pxW - M),
          y: Phaser.Math.Clamp(ty - Math.sin(ang) * want, M, this.pxH - M),
          duration: 140, ease: 'cubic.in',
          onComplete: () => this.renderAbilityFx(fx, tx, ty),
        });
        return;
      }
      if (fx.range === 'ranged' && target && dist < 34) {
        const ang = Math.atan2(this.player.y - ty, this.player.x - tx);
        this.tweens.add({
          targets: this.player,
          x: Phaser.Math.Clamp(this.player.x + Math.cos(ang) * 22, M, this.pxW - M),
          y: Phaser.Math.Clamp(this.player.y + Math.sin(ang) * 22, M, this.pxH - M),
          duration: 130, ease: 'cubic.out',
          onComplete: () => this.renderAbilityFx(fx, tx, ty),
        });
        return;
      }
      this.renderAbilityFx(fx, tx, ty);
    }
    renderAbilityFx(fx, tx, ty) {
      const px = this.player.x, py = this.player.y;
      switch (fx.type) {
        case 'bolt':
          this.projectileFx(px, py - 6, tx, ty - 6, fx.color);
          break;
        case 'missiles': {
          for (let i = 0; i < 3; i++) {
            this.time.delayedCall(i * 110, () => this.projectileFx(px, py - 6 + (i - 1) * 3, tx, ty - 6, fx.color));
          }
          break;
        }
        case 'arrow': {
          const arrow = this.add.rectangle(px, py - 6, 10, 1.6, 0xeae6d8).setDepth(60);
          arrow.setRotation(Math.atan2(ty - py, tx - px));
          this.tweens.add({ targets: arrow, x: tx, y: ty - 6, duration: 130, ease: 'linear',
            onComplete: () => { this.spark(tx, ty - 6, fx.color); arrow.destroy(); } });
          break;
        }
        case 'cone': {
          const base = Math.atan2(ty - py, tx - px);
          const fan = this.add.particles(px + Math.cos(base) * 8, py - 4 + Math.sin(base) * 8, 'px_white', {
            speed: { min: 70, max: 130 },
            angle: { min: Phaser.Math.RadToDeg(base) - 24, max: Phaser.Math.RadToDeg(base) + 24 },
            lifespan: 360, quantity: 6, frequency: 30,
            scale: { start: 0.9, end: 0 }, tint: [fx.color, 0xfff0c0], blendMode: 'ADD',
          }).setDepth(60);
          this.time.delayedCall(420, () => fan.stop());
          this.time.delayedCall(900, () => fan.destroy());
          break;
        }
        case 'zap': {
          const g = this.add.graphics().setDepth(60);
          const seg = 6;
          for (const [width, color, alpha] of [[3, fx.color, 0.9], [1.2, 0xffffff, 1]]) {
            g.lineStyle(width, color, alpha);
            g.beginPath();
            g.moveTo(px, py - 8);
            for (let i = 1; i <= seg; i++) {
              const t = i / seg;
              g.lineTo(px + (tx - px) * t + (i < seg ? (Math.random() * 14 - 7) : 0),
                       (py - 8) + ((ty - 6) - (py - 8)) * t + (i < seg ? (Math.random() * 14 - 7) : 0));
            }
            g.strokePath();
          }
          this.cameras.main.flash(90, 160, 200, 255, false);
          this.spark(tx, ty - 6, fx.color);
          this.tweens.add({ targets: g, alpha: 0, duration: 200, delay: 60, onComplete: () => g.destroy() });
          break;
        }
        case 'chainzap': {
          this.renderAbilityFx({ type: 'zap', color: fx.color }, tx, ty);
          const second = [...this.entities.values()].find(e =>
            e.kind === 'mob' && e.sprite && Math.hypot(e.sprite.x - tx, e.sprite.y - ty) > 6 &&
            Math.hypot(e.sprite.x - tx, e.sprite.y - ty) < 70);
          if (second) {
            this.time.delayedCall(140, () => {
              const g2 = this.add.graphics().setDepth(60);
              g2.lineStyle(2, fx.color, 0.85);
              g2.lineBetween(tx, ty - 6, second.sprite.x, second.sprite.y - 6);
              this.spark(second.sprite.x, second.sprite.y - 6, fx.color);
              this.tweens.add({ targets: g2, alpha: 0, duration: 220, onComplete: () => g2.destroy() });
            });
          }
          break;
        }
        case 'bigbolt': {
          const bolt = this.add.image(px, py - 6, 'fx_glow')
            .setBlendMode(Phaser.BlendModes.ADD).setScale(0.45).setTint(fx.color).setDepth(60);
          this.tweens.add({
            targets: bolt, x: tx, y: ty - 6, duration: 330, ease: 'sine.in',
            onComplete: () => {
              bolt.destroy();
              const ring = this.add.circle(tx, ty - 4, 5).setStrokeStyle(3, fx.color, 0.9).setDepth(60);
              this.tweens.add({ targets: ring, radius: 30, alpha: 0, duration: 380, ease: 'cubic.out', onComplete: () => ring.destroy() });
              const burst = this.add.particles(tx, ty - 6, 'px_white', {
                speed: { min: 50, max: 140 }, lifespan: 450, quantity: 20,
                scale: { start: 1, end: 0 }, tint: [fx.color, 0xfff0c0], blendMode: 'ADD', emitting: false,
              }).setDepth(60);
              burst.explode(20);
              this.cameras.main.shake(110, 0.005);
              this.time.delayedCall(700, () => burst.destroy());
            },
          });
          break;
        }
        case 'meteor': {
          for (let i = 0; i < 3; i++) {
            const ox = tx + (i - 1) * 18 + (Math.random() * 10 - 5);
            this.time.delayedCall(i * 160, () => {
              const rock = this.add.image(ox + 26, ty - 110, 'fx_glow')
                .setBlendMode(Phaser.BlendModes.ADD).setScale(0.35).setTint(fx.color).setDepth(60);
              this.tweens.add({
                targets: rock, x: ox, y: ty - 4, duration: 240, ease: 'cubic.in',
                onComplete: () => {
                  rock.destroy();
                  this.renderAbilityFx({ type: 'shockwave', color: fx.color }, ox, ty);
                },
              });
            });
          }
          break;
        }
        case 'touch': {
          const hand = this.add.image(tx, ty - 8, 'fx_glow')
            .setBlendMode(Phaser.BlendModes.ADD).setScale(0.08).setTint(fx.color).setDepth(60);
          this.tweens.add({ targets: hand, scale: 0.42, alpha: 0, duration: 360, ease: 'cubic.out', onComplete: () => hand.destroy() });
          this.spark(tx, ty - 6, fx.color);
          break;
        }
        case 'column': {
          const beam = this.add.rectangle(tx, ty - 60, 14, 0, fx.color, 0.55).setOrigin(0.5, 0)
            .setBlendMode(Phaser.BlendModes.ADD).setDepth(60);
          this.tweens.add({ targets: beam, height: 64, duration: 160, ease: 'cubic.in',
            onComplete: () => {
              this.spark(tx, ty - 6, fx.color);
              this.tweens.add({ targets: beam, alpha: 0, duration: 260, onComplete: () => beam.destroy() });
            } });
          break;
        }
        case 'shockwave': {
          const ring = this.add.circle(tx, ty, 4).setStrokeStyle(2.5, fx.color, 0.9).setDepth(60);
          this.tweens.add({ targets: ring, radius: 26, alpha: 0, duration: 320, ease: 'cubic.out', onComplete: () => ring.destroy() });
          this.cameras.main.shake(70, 0.003);
          break;
        }
        case 'nova': {
          const ring = this.add.circle(px, py, 6).setStrokeStyle(3, fx.color, 0.9).setDepth(60);
          this.tweens.add({ targets: ring, radius: 52, alpha: 0, duration: 480, ease: 'cubic.out', onComplete: () => ring.destroy() });
          const ring2 = this.add.circle(px, py, 4).setStrokeStyle(1.5, 0xffffff, 0.7).setDepth(60);
          this.tweens.add({ targets: ring2, radius: 38, alpha: 0, duration: 420, delay: 80, ease: 'cubic.out', onComplete: () => ring2.destroy() });
          this.cameras.main.shake(90, 0.004);
          break;
        }
        case 'bigslash':
          this.slashFx(tx, ty, px >= tx ? tx - 10 : tx + 10);
          this.time.delayedCall(90, () => this.slashFx(tx, ty - 4, px >= tx ? tx + 10 : tx - 10));
          break;
        case 'shadowstrike': {
          const ghost = this.add.sprite(px, py, this.playerTex(), 'atk_s')
            .setScale(1 / MH.SMOOTH_SS).setAlpha(0.5).setTint(0x6a6af0).setDepth(60);
          this.tweens.add({ targets: ghost, x: tx + (px < tx ? 12 : -12), y: ty, alpha: 0.9, duration: 110,
            onComplete: () => {
              this.slashFx(tx, ty, ghost.x);
              this.tweens.add({ targets: ghost, alpha: 0, duration: 180, onComplete: () => ghost.destroy() });
            } });
          break;
        }
        case 'dash': {
          const v = { x: tx - px, y: ty - py };
          const d = Math.hypot(v.x, v.y) || 1;
          this.tweens.add({ targets: this.player, x: tx - (v.x / d) * 16, y: ty - (v.y / d) * 16, duration: 130, ease: 'cubic.in',
            onComplete: () => this.renderAbilityFx({ type: 'shockwave', color: fx.color }, tx, ty) });
          break;
        }
        case 'drain':
          this.projectileFx(px, py - 6, tx, ty - 6, fx.color);
          this.time.delayedCall(320, () => {
            const back = this.add.particles(tx, ty - 6, 'px_white', {
              speed: 10, lifespan: 600, quantity: 3, scale: { start: 0.6, end: 0 },
              tint: 0x7dff9a, blendMode: 'ADD',
            }).setDepth(60);
            const orb = this.add.image(tx, ty - 6, 'fx_glow').setScale(0.15).setTint(0x7dff9a)
              .setBlendMode(Phaser.BlendModes.ADD).setDepth(60);
            back.startFollow(orb);
            this.tweens.add({ targets: orb, x: this.player.x, y: this.player.y - 6, duration: 380, ease: 'sine.out',
              onComplete: () => { this.fxHeal(); orb.destroy(); this.time.delayedCall(400, () => back.destroy()); } });
          });
          break;
        case 'notes': {
          for (let i = 0; i < 4; i++) {
            const note = this.add.text(px, py - 10, i % 2 ? '♪' : '♫', {
              fontFamily: 'Georgia, serif', resolution: 3, fontSize: '10px', color: '#ffa8d8',
            }).setOrigin(0.5).setDepth(60).setAlpha(0.9);
            this.tweens.add({ targets: note, x: tx + (i - 1.5) * 8, y: ty - 14 - i * 4, alpha: 0,
              duration: 600 + i * 110, ease: 'sine.out', delay: i * 70, onComplete: () => note.destroy() });
          }
          this.time.delayedCall(500, () => this.spark(tx, ty - 6, fx.color));
          break;
        }
        case 'debuff': {
          for (let i = 0; i < 6; i++) {
            const mote = this.add.image(tx, ty - 36, 'px_white').setTint(fx.color)
              .setBlendMode(Phaser.BlendModes.ADD).setScale(0.8).setDepth(60);
            const ang0 = (i / 6) * Math.PI * 2;
            this.tweens.add({
              targets: mote, duration: 520, delay: i * 40, ease: 'sine.in',
              x: tx, y: ty - 4, scale: 0.1,
              onUpdate: (tw, t2) => {
                const k = tw.progress;
                t2.x = tx + Math.cos(ang0 + k * 4) * 14 * (1 - k);
                t2.y = (ty - 36) + 32 * k;
              },
              onComplete: () => mote.destroy(),
            });
          }
          break;
        }
        case 'sleep': {
          const z = this.add.text(tx, ty - 18, 'z Z z', {
            fontFamily: 'Georgia, serif', resolution: 3, fontSize: '10px', fontStyle: 'italic', color: '#b8c4e8',
          }).setOrigin(0.5).setDepth(60);
          this.tweens.add({ targets: z, y: ty - 34, alpha: 0, duration: 1300, ease: 'sine.out', onComplete: () => z.destroy() });
          break;
        }
        case 'vines': {
          const g = this.add.graphics().setDepth(60);
          g.lineStyle(2, fx.color, 0.9);
          for (let i = 0; i < 3; i++) {
            g.beginPath();
            g.arc(tx, ty + 2 - i * 4, 9 - i * 2, Math.PI * 0.1 * i, Math.PI * (1.6 + 0.1 * i));
            g.strokePath();
          }
          this.tweens.add({ targets: g, alpha: 0, duration: 900, delay: 350, onComplete: () => g.destroy() });
          break;
        }
        case 'mark': {
          const ring = this.add.circle(tx, ty - 8, 13).setStrokeStyle(2, fx.color, 0.95).setDepth(60);
          const cross = this.add.text(tx, ty - 8, '+', {
            fontFamily: 'Trebuchet MS, Verdana, sans-serif', resolution: 3, fontSize: '12px', color: '#ff6a6a',
          }).setOrigin(0.5).setDepth(60);
          this.tweens.add({ targets: ring, scale: 0.55, duration: 260, ease: 'cubic.in' });
          this.tweens.add({ targets: [ring, cross], alpha: 0, duration: 400, delay: 500, onComplete: () => { ring.destroy(); cross.destroy(); } });
          break;
        }
        case 'coins': {
          for (let i = 0; i < 5; i++) {
            const coin = this.add.image(tx + (Math.random() * 12 - 6), ty - 8, 'px_star')
              .setTint(0xffd44a).setDepth(60).setScale(1.1);
            this.tweens.add({
              targets: coin, x: px, y: py - 6, duration: 320 + i * 70, ease: 'cubic.in',
              delay: i * 60, onComplete: () => coin.destroy(),
            });
          }
          break;
        }
        case 'rally': {
          const up = this.add.particles(px, py + 4, 'px_star', {
            x: { min: -12, max: 12 }, speedY: { min: -55, max: -30 }, lifespan: 700,
            quantity: 3, scale: { start: 1, end: 0 }, tint: fx.color, blendMode: 'ADD',
          }).setDepth(60);
          this.time.delayedCall(800, () => up.destroy());
          this.zoomPunch();
          break;
        }
        case 'stealth': {
          this.player.setAlpha(0.35);
          const ghost = this.add.particles(px, py, 'px_poof', {
            speed: 14, lifespan: 500, quantity: 8, scale: { start: 0.9, end: 0 }, emitting: false,
          }).setDepth(60);
          ghost.explode(8);
          this.time.delayedCall(2200, () => { this.player.setAlpha(1); ghost.destroy(); });
          break;
        }
        case 'healburst':
          this.fxHeal();
          break;
        case 'impact':
        default:
          this.spark(tx, ty - 6, fx.color);
          this.slashFx(tx, ty, px >= tx ? tx - 10 : tx + 10);
          break;
      }
    }

    static SPELL_ELEMENTS = [
      [/fire|burn|flame|inferno/i, 0xff8a3c],
      [/lightning|shock|storm/i, 0x9adcff],
      [/chill|frost|ice|cone of cold/i, 0xbfeaff],
      [/missile|force|arcane|magic/i, 0xc792ff],
      [/acid|poison|venom/i, 0x9ee05a],
      [/holy|smite|divine|flamestrike/i, 0xffe9a0],
      [/harm|drain|necro|shadow|curse/i, 0xb05ae0],
    ];
    elementFor(text) {
      for (const [re, color] of TopRoomScene.SPELL_ELEMENTS) {
        if (re.test(text)) return color;
      }
      return null;
    }
    projectileFx(x0, y0, x1, y1, color) {
      const bolt = this.add.image(x0, y0, 'fx_glow')
        .setBlendMode(Phaser.BlendModes.ADD).setScale(0.22).setTint(color).setDepth(60);
      const trail = this.add.particles(x0, y0, 'px_white', {
        speed: 8, lifespan: 280, quantity: 2, scale: { start: 0.5, end: 0 },
        alpha: { start: 0.8, end: 0 }, tint: color, blendMode: 'ADD',
      }).setDepth(59);
      trail.startFollow(bolt);
      this.tweens.add({
        targets: bolt, x: x1, y: y1, duration: 230, ease: 'sine.in',
        onComplete: () => {
          const burst = this.add.particles(x1, y1, 'px_white', {
            speed: { min: 40, max: 110 }, lifespan: 380, quantity: 14,
            scale: { start: 0.9, end: 0 }, tint: color, blendMode: 'ADD', emitting: false,
          }).setDepth(60);
          burst.explode(14);
          const flash = this.add.image(x1, y1, 'fx_glow').setBlendMode(Phaser.BlendModes.ADD)
            .setScale(0.5).setTint(color).setDepth(60);
          this.tweens.add({ targets: flash, scale: 0.1, alpha: 0, duration: 260, onComplete: () => flash.destroy() });
          this.time.delayedCall(600, () => { burst.destroy(); trail.destroy(); });
          bolt.destroy();
        },
      });
    }
    slashFx(x, y, towardX) {
      const arc = this.add.image(x, y - 4, 'fx_slash')
        .setScale(0.9 / MH.SMOOTH_SS).setDepth(60)
        .setFlipX(towardX < x).setAlpha(0.95)
        .setRotation((towardX < x ? -0.5 : 0.5));
      this.tweens.add({
        targets: arc, rotation: arc.rotation + (towardX < x ? -1.1 : 1.1), alpha: 0,
        scale: 1.15 / MH.SMOOTH_SS, duration: 220, ease: 'cubic.out',
        onComplete: () => arc.destroy(),
      });
    }
    fxHeal() {
      const rise = this.add.particles(this.player.x, this.player.y + 6, 'px_white', {
        x: { min: -8, max: 8 }, speedY: { min: -45, max: -25 }, lifespan: 800,
        quantity: 3, scale: { start: 0.7, end: 0 }, tint: 0x7dff9a, blendMode: 'ADD',
      }).setDepth(60);
      this.time.delayedCall(900, () => rise.destroy());
    }

    // ---------- FX (shared design with the side view) ----------
    dmgStyle(dmg) {
      if (dmg == null) return { color: '#ffe080', size: 9, shake: 0 };
      if (dmg <= 4) return { color: '#d8dce8', size: 8, shake: 0 };
      if (dmg <= 12) return { color: '#7ad68a', size: 9, shake: 0 };
      if (dmg <= 24) return { color: '#e8c168', size: 10, shake: 0 };
      if (dmg <= 48) return { color: '#ffd44a', size: 12, shake: 0.002 };
      if (dmg <= 80) return { color: '#ff6a4a', size: 14, shake: 0.004 };
      return { color: '#ff4ae0', size: 16, shake: 0.007 };
    }
    fxHit(e) {
      const ent = this.findEntityByText(e.target) || this.target;
      if (!ent || !ent.sprite) return;
      ent.sprite.setTintFill(0xffffff);
      this.time.delayedCall(80, () => ent.sprite && ent.sprite.clearTint());
      const ang = Math.atan2(ent.sprite.y - this.player.y, ent.sprite.x - this.player.x);
      const kb = e.dmg != null ? Math.min(12, 4 + e.dmg * 0.25) : 5;
      this.tweens.add({ targets: ent.sprite, x: ent.sprite.x + Math.cos(ang) * kb, y: ent.sprite.y + Math.sin(ang) * kb, duration: 70, yoyo: true });
      this.squash(ent.sprite);
      this.impactLines(ent.sprite.x, ent.sprite.y - 6);
      if (e.dmg != null && e.dmg >= 8) this.freezeFrame(e.dmg >= 25 ? 95 : 60);
      if (e.dmg != null && e.dmg >= 5) this.bloodSplat(ent.sprite.x, ent.sprite.y, e.dmg >= 20);
      this.afterimage(this.player);
      // class ability in flight? play its signature effect. otherwise steel.
      const fx = this.abilityFxFor(e.line || '')
        || (this.lastAbility && Date.now() - this.lastAbility.ts < 4000 ? this.abilityFxFor(this.lastAbility.name) : null);
      if (fx) this.playAbilityFx(fx, ent.sprite);
      else this.slashFx(ent.sprite.x, ent.sprite.y, this.player.x >= ent.sprite.x ? ent.sprite.x - 10 : ent.sprite.x + 10);
      this.spark(ent.sprite.x, ent.sprite.y - 6, (fx && fx.color) || 0xffe080);
      const st = this.dmgStyle(e.dmg);
      if (st.shake) this.cameras.main.shake(90, st.shake);
      if (e.dmg != null && e.dmg >= 25) this.zoomPunch();
      this.damageNumber(ent.sprite.x, ent.sprite.y - 16, e.dmg != null ? String(e.dmg) : 'hit', st.color, st.size);
    }
    fxMiss(e) {
      const ent = this.findEntityByText(e.target) || this.target;
      if (ent && ent.sprite) this.damageNumber(ent.sprite.x, ent.sprite.y - 16, 'miss', '#7a8094', 8);
    }
    fxTaken(e) {
      this.player.setTintFill(0xff6060);
      this.time.delayedCall(90, () => this.player.clearTint());
      const st = this.dmgStyle(e && e.dmg);
      this.cameras.main.shake(80, Math.max(0.004, st.shake));
      this.squash(this.player);
      this.impactLines(this.player.x, this.player.y - 6, 0xff8080);
      if (e && e.dmg != null && e.dmg >= 6) {
        this.freezeFrame(e.dmg >= 20 ? 90 : 55);
        this.bloodSplat(this.player.x, this.player.y, e.dmg >= 15);
      }
      const atk = e && e.from ? this.findEntityByText(e.from) : null;
      const inColor = this.elementFor((e && e.line) || '');
      if (atk && atk.sprite && inColor) {
        this.projectileFx(atk.sprite.x, atk.sprite.y - 6, this.player.x, this.player.y - 6, inColor);
      }
      if (atk && atk.sprite) {
        const ang = Math.atan2(this.player.y - atk.sprite.y, this.player.x - atk.sprite.x);
        const m = TD().T * 1.6;
        this.player.x = Phaser.Math.Clamp(this.player.x + Math.cos(ang) * 6, m, this.pxW - m);
        this.player.y = Phaser.Math.Clamp(this.player.y + Math.sin(ang) * 6, m, this.pxH - m);
        // attacker lunges at you so the hit has a visible author
        this.tweens.add({
          targets: atk.sprite,
          x: atk.sprite.x + Math.cos(ang) * 9,
          y: atk.sprite.y + Math.sin(ang) * 9,
          duration: 90, yoyo: true, ease: 'cubic.out',
        });
        // mark them even if the server payload hasn't flagged it yet
        if (!atk.data.fighting) this.updateEntity(atk, Object.assign({}, atk.data, { fighting: true }));
      }
      this.damageNumber(this.player.x, this.player.y - 18, e && e.dmg != null ? `-${e.dmg}` : '✦', '#e06c6c', st.size);
    }
    // flee = an involuntary room exit: dash toward that edge so the
    // following screen-slide reads as ESCAPING, not teleporting
    fxFlee(e) {
      MH.bus.emit('flash', e.dir ? `You flee ${e.dir}!` : 'You flee!');
      if (e.dir && ['north', 'south', 'east', 'west', 'up', 'down'].includes(e.dir)) {
        MH.state.pendingMove = { dir: e.dir, sentAt: Date.now() };
      }
      const v = { north: [0, -1], south: [0, 1], east: [1, 0], west: [-1, 0] }[e.dir] || [0, 0];
      const streak = this.add.particles(this.player.x, this.player.y, 'px_white', {
        speedX: { min: -v[0] * 120 - 20, max: -v[0] * 120 + 20 },
        speedY: { min: -v[1] * 120 - 20, max: -v[1] * 120 + 20 },
        lifespan: 350, quantity: 4, scale: { start: 0.7, end: 0 },
        alpha: { start: 0.8, end: 0 }, tint: 0xfff0c0, blendMode: 'ADD', emitting: false,
      }).setDepth(60);
      streak.explode(14);
      this.time.delayedCall(500, () => streak.destroy());
      if (v[0] || v[1]) {
        this.tweens.add({ targets: this.player, x: this.player.x + v[0] * 30, y: this.player.y + v[1] * 30, duration: 240, ease: 'cubic.in' });
      }
    }

    // hit-stop: the universal crunch. freeze the world for a few frames
    // on solid impacts (Vlambeer/Hades school of game feel)
    freezeFrame(ms = 70) {
      if (this._frozen) return;
      this._frozen = true;
      this.tweens.timeScale = 0.05;
      this.physics.world.timeScale = 10;
      this.anims.globalTimeScale = 0.05;
      setTimeout(() => {
        this.tweens.timeScale = 1;
        this.physics.world.timeScale = 1;
        this.anims.globalTimeScale = 1;
        this._frozen = false;
      }, ms);
    }
    // squash & stretch: bodies deform on impact
    squash(sprite) {
      if (!sprite || !sprite.active) return;
      const sx = sprite.scaleX, sy = sprite.scaleY;
      this.tweens.add({
        targets: sprite, scaleX: sx * 1.28, scaleY: sy * 0.72,
        duration: 60, yoyo: true, ease: 'cubic.out',
        onComplete: () => { if (sprite.active) sprite.setScale(sx, sy); },
      });
    }
    // impact frame: radial white lines snapping out from the hit point
    impactLines(x, y, color = 0xffffff) {
      const g = this.add.graphics().setDepth(61);
      for (let i = 0; i < 6; i++) {
        const a = (i / 6) * Math.PI * 2 + Math.random() * 0.4;
        g.lineStyle(1.4, color, 0.95);
        g.lineBetween(x + Math.cos(a) * 5, y + Math.sin(a) * 5, x + Math.cos(a) * 13, y + Math.sin(a) * 13);
      }
      this.tweens.add({ targets: g, alpha: 0, duration: 140, onComplete: () => g.destroy() });
    }
    // wounds stay on the floor
    bloodSplat(x, y, heavy = false) {
      const g = this.add.graphics().setDepth(2);
      g.fillStyle(0x6a1818, heavy ? 0.5 : 0.35);
      for (let i = 0; i < (heavy ? 5 : 3); i++) {
        g.fillEllipse(x + (Math.random() * 14 - 7), y + 6 + (Math.random() * 8 - 4), 5 + Math.random() * 5, 3 + Math.random() * 3);
      }
      this.tileLayer.add(g);
      this.tweens.add({ targets: g, alpha: 0, duration: 2500, delay: 6000, onComplete: () => g.destroy() });
    }
    // afterimage trail for dashes and strikes
    afterimage(sprite, tint = 0xffffff) {
      if (!sprite || !sprite.active) return;
      const ghost = this.add.image(sprite.x, sprite.y, sprite.texture.key, sprite.frame.name)
        .setScale(sprite.scaleX, sprite.scaleY).setFlipX(sprite.flipX)
        .setAlpha(0.4).setTint(tint).setDepth(sprite.depth - 0.1);
      this.tweens.add({ targets: ghost, alpha: 0, duration: 220, onComplete: () => ghost.destroy() });
    }

    zoomPunch() {
      const cam = this.cameras.main;
      const base = cam.zoom;
      this.tweens.add({ targets: cam, zoom: base * 1.035, duration: 70, yoyo: true, ease: 'cubic.out' });
    }

    // your defensive skills firing - make them feel earned
    fxDeflect(word, color, from) {
      const x = this.player.x, y = this.player.y;
      const arc = this.add.circle(x, y - 4, 14).setStrokeStyle(2.5, color, 0.95)
        .setBlendMode(Phaser.BlendModes.ADD).setDepth(61);
      this.tweens.add({ targets: arc, radius: 20, alpha: 0, duration: 320, ease: 'cubic.out', onComplete: () => arc.destroy() });
      this.spark(x + 8, y - 8, color);
      this.damageNumber(x, y - 22, word, '#d5dde9', 11);
      // riposte feel: face the attacker
      const atk = from ? this.findEntityByText(from) : null;
      if (atk && atk.sprite) this.setFacing(atk.sprite.x - x, atk.sprite.y - y);
    }
    fxSidestep() {
      // quick ghost-dash to the side
      this.afterimage(this.player, 0xbcd2ff);
      const side = Math.random() < 0.5 ? -1 : 1;
      const m = TD().T * 1.6;
      const nx = Phaser.Math.Clamp(this.player.x + side * 14, m, this.pxW - m);
      this.tweens.add({ targets: this.player, x: nx, duration: 110, yoyo: true, ease: 'cubic.out' });
      this.damageNumber(this.player.x, this.player.y - 22, 'DODGE', '#bcd2ff', 11);
    }
    fxTargetDeflect(name, word) {
      const ent = this.findEntityByText(name) || this.target;
      if (!ent || !ent.sprite) return;
      this.damageNumber(ent.sprite.x, ent.sprite.y - 18, word, '#9aa2b4', 9);
      this.spark(ent.sprite.x, ent.sprite.y - 8, 0x9aa2b4);
      if (word === 'dodged') {
        const side = Math.random() < 0.5 ? -1 : 1;
        this.tweens.add({ targets: ent.sprite, x: ent.sprite.x + side * 12, duration: 100, yoyo: true, ease: 'cubic.out' });
      }
    }

    // Tab cycles hostile targets by distance
    cycleTarget() {
      const mobs = [...this.entities.values()].filter(e => e.kind === 'mob' && !e.data.shopkeeper && e.sprite)
        .sort((a, b) => Phaser.Math.Distance.Between(this.player.x, this.player.y, a.sprite.x, a.sprite.y)
                      - Phaser.Math.Distance.Between(this.player.x, this.player.y, b.sprite.x, b.sprite.y));
      if (!mobs.length) return;
      const idx = this.target ? mobs.findIndex(m => m.key === this.target.key) : -1;
      const next = mobs[(idx + 1) % mobs.length];
      this.target = next;
      MH.bus.emit('target.set', next.data);
      this.setFacing(next.sprite.x - this.player.x, next.sprite.y - this.player.y);
      // target ping
      const ring = this.add.circle(next.sprite.x, next.sprite.y - 6, 16).setStrokeStyle(2, 0xe8c168, 0.9).setDepth(61);
      this.tweens.add({ targets: ring, radius: 8, alpha: 0, duration: 360, ease: 'cubic.in', onComplete: () => ring.destroy() });
    }

    fxExp(e) {
      const t = this.add.text(this.player.x, this.player.y - 22, `+${e.amount} xp`, {
        fontFamily: 'Trebuchet MS, Verdana, sans-serif', resolution: 3, fontSize: '9px', color: '#e8c168', stroke: '#000', strokeThickness: 2,
      }).setOrigin(0.5).setDepth(60);
      this.tweens.add({ targets: t, y: t.y - 18, alpha: 0, duration: 1400, ease: 'sine.out', onComplete: () => t.destroy() });
    }
    fxMobDeath(e) {
      const ent = this.findEntityByText(e.name) || this.target;
      if (ent && ent.sprite) {
        const dx = ent.sprite.x, dy = ent.sprite.y;
        // the killing blow earns drama: freeze, flash, shatter, and a
        // soul drifting free of the body
        this.freezeFrame(110);
        ent.sprite.setTintFill(0xffffff);
        this.time.delayedCall(90, () => ent.sprite && ent.sprite.active && ent.sprite.clearTint());
        const shards = this.add.particles(dx, dy - 6, 'px_white', {
          speed: { min: 60, max: 150 }, lifespan: 520, quantity: 12,
          scale: { start: 1.1, end: 0 }, tint: [0xffffff, 0xd0d6e4], emitting: false,
          gravityY: 160,
        }).setDepth(60);
        shards.explode(12);
        this.time.delayedCall(800, () => shards.destroy());
        const soul = this.add.image(dx, dy - 8, 'fx_glow')
          .setBlendMode(Phaser.BlendModes.ADD).setScale(0.16).setTint(0xbcd2ff).setAlpha(0.85).setDepth(60);
        this.tweens.add({ targets: soul, y: dy - 42, alpha: 0, scale: 0.05, duration: 1400, ease: 'sine.out', onComplete: () => soul.destroy() });
        this.bloodSplat(dx, dy, true);
        ent.sprite.setFrame('death');
        this.poof(ent.sprite.x, ent.sprite.y);
        // a body remains where it fell (the lootable corpse item follows
        // in the next payload; this is the visual continuity)
        const corpse = this.add.image(ent.sprite.x, ent.sprite.y + 4, 'sm_corpse')
          .setScale(0.9 / MH.SMOOTH_SS).setDepth(4).setAlpha(0);
        this.tweens.add({ targets: corpse, alpha: 1, duration: 400, delay: 250 });
        corpse.setInteractive({ useHandCursor: true });
        corpse.on('pointerdown', () => MH.bus.emit('loot.corpse'));
        (this.corpses = this.corpses || []).push(corpse);
        if (this.corpses.length > 8) { const old = this.corpses.shift(); old.destroy(); }
        this.tileLayer.add(corpse);
      }
      if (this.target && ent === this.target) { this.target = null; MH.bus.emit('target.clear'); }
    }
    fxPlayerDeath() {
      this.dead = true;
      this.recordDeath();
      this.player.setFrame('death');
      this.cameras.main.fade(1200, 0, 0, 0, false, (_c, t) => {
        if (t === 1) {
          this.time.delayedCall(600, () => { MH.refreshState(); this.cameras.main.fadeIn(600); this.dead = false; });
        }
      });
      MH.bus.emit('flash', 'You have died. The realm reclaims you…');
    }
    fxLevelUp() {
      const emitter = this.add.particles(this.player.x, this.player.y - 6, 'px_star', {
        speed: { min: 30, max: 100 }, lifespan: 900, quantity: 20, scale: { start: 1, end: 0 }, emitting: false,
      }).setDepth(60);
      emitter.explode(20);
      this.time.delayedCall(1200, () => emitter.destroy());
    }
    fxChatBubble(e) {
      const m = e.line.match(/^(\w+) says?,? '?(.*?)'?$/i);
      if (!m) return;
      for (const ent of this.entities.values()) {
        if (ent.label && ent.data.name && String(ent.data.name).toLowerCase().includes(m[1].toLowerCase())) {
          this.bubbleOver(ent, m[2]);
          break;
        }
      }
    }
    fxAmbient(e) {
      const line = e.line.trim();
      if (!line || line.length > 110) return;
      if (/\d+\/\d+(hp|mp|mv)/i.test(line) || /^>/.test(line) || /^\[/.test(line)) return;
      const lower = line.toLowerCase();
      for (const ent of this.entities.values()) {
        if (ent.kind !== 'mob') continue;
        const kw = MH.mobKeyword(ent.data.name);
        if (kw.length > 2 && lower.includes(kw)) { this.bubbleOver(ent, line, '#b8c0d4'); return; }
      }
      if (!/^(you hear|a |an |the |somewhere|in the distance|dust|wind|water|shadows)/i.test(line)) return;
      const t = this.add.text(40 + Math.random() * (this.pxW - 200), 40 + Math.random() * 100, line, {
        fontFamily: 'Georgia, serif', resolution: 3, fontSize: '9px', fontStyle: 'italic', color: '#e8e2d0',
      }).setAlpha(0).setDepth(45).setShadow(0, 1, '#000000', 2);
      this.tweens.add({ targets: t, alpha: 0.45, duration: 900, yoyo: true, hold: 3600, onComplete: () => t.destroy() });
    }
    bubbleOver(ent, text, color = '#dce4f0') {
      if (!ent || !ent.sprite) return;
      const bubble = this.add.text(ent.sprite.x, ent.sprite.y - 24, String(text).slice(0, 50), {
        fontFamily: 'Trebuchet MS, Verdana, sans-serif', resolution: 3, fontSize: '7px', color, backgroundColor: '#10131ecc',
        padding: { x: 3, y: 1 }, wordWrap: { width: 120 },
      }).setOrigin(0.5, 1).setDepth(60);
      this.tweens.add({ targets: bubble, y: bubble.y - 6, alpha: 0, delay: 2800, duration: 700, onComplete: () => bubble.destroy() });
    }
    spark(x, y, color) {
      const emitter = this.add.particles(x, y, 'px_white', {
        speed: { min: 30, max: 90 }, lifespan: 300, quantity: 8, scale: { start: 0.8, end: 0 }, tint: color, emitting: false,
      }).setDepth(60);
      emitter.explode(8);
      this.time.delayedCall(500, () => emitter.destroy());
    }
    poof(x, y) {
      const emitter = this.add.particles(x, y, 'px_poof', {
        speed: { min: 15, max: 55 }, lifespan: 500, quantity: 12, scale: { start: 1, end: 0 }, emitting: false,
      }).setDepth(60);
      emitter.explode(12);
      this.time.delayedCall(700, () => emitter.destroy());
    }
    damageNumber(x, y, text, color, size = 9) {
      const crit = size >= 12;
      const t = this.add.text(x + (Math.random() * 10 - 5), y, text, {
        fontFamily: 'Trebuchet MS, Verdana, sans-serif', resolution: 3,
        fontSize: `${crit ? size + 3 : size}px`, color,
        stroke: '#000', strokeThickness: crit ? 3 : 2,
        fontStyle: crit ? 'bold' : 'normal',
      }).setOrigin(0.5).setDepth(62).setScale(crit ? 2.4 : 1.4);
      this.tweens.add({ targets: t, scale: 1, duration: crit ? 160 : 110, ease: 'back.out' });
      this.tweens.add({
        targets: t, y: y - (crit ? 24 : 16), x: t.x + (Math.random() * 24 - 12),
        alpha: 0, duration: crit ? 950 : 800, delay: 110, onComplete: () => t.destroy(),
      });
      if (crit) this.impactLines(x, y, Phaser.Display.Color.HexStringToColor(color).color);
    }

    // ---------- movement / exits ----------
    onMoveBlocked(e) {
      const pm = MH.state.pendingMove;
      MH.state.pendingMove = null;
      MH.bus.emit('flash', e.line);
      this.exitSuppress = Date.now() + 900;
      if (!pm) return;
      // step back toward the room center
      const cx = this.pxW / 2, cy = this.pxH / 2;
      const ang = Math.atan2(cy - this.player.y, cx - this.player.x);
      this.player.x += Math.cos(ang) * 14;
      this.player.y += Math.sin(ang) * 14;
      const door = this.layout && this.layout.exits[pm.dir] && this.layout.exits[pm.dir].door;
      if (door && /closed/i.test(e.line)) MH.sendCommand(`open ${door.name} ${pm.dir}`);
    }

    requestMove(dir) {
      const st = MH.state;
      if (st.pendingMove && Date.now() - st.pendingMove.sentAt < 2500) return;
      st.pendingMove = { dir, sentAt: Date.now() };
      this.exitSuppress = Date.now() + 700;   // no double-fire while in flight
      MH.sendCommand(dir);
    }

    // compass / Shift+key: BFS a path on the grid and walk it
    navTo(dir) {
      const L = this.layout;
      if (!L || this.dead) return;
      if (!Object.prototype.hasOwnProperty.call(L.exits || {}, dir)) {
        MH.bus.emit('flash', `There is no exit ${dir} here.`);
        return;
      }
      const { T, BLOCK, WATER } = TD();
      const midX = Math.floor(L.W / 2), midY = Math.floor(L.H / 2);
      let goal = null;
      if (dir === 'north') goal = [midX, 0];
      else if (dir === 'south') goal = [midX, L.H - 1];
      else if (dir === 'west') goal = [0, midY];
      else if (dir === 'east') goal = [L.W - 1, midY];
      else if (dir === 'up' && L.stairsUp) goal = [L.stairsUp.x, L.stairsUp.y];
      else if (dir === 'down' && L.stairsDown) goal = [L.stairsDown.x, L.stairsDown.y];
      else {
        const p = (L.portals || []).find(pt => pt.name === dir);
        if (p) goal = [p.x, p.y];
      }
      if (!goal) { this.requestMove(dir); return; }
      // feature tiles teleport on touch; never path across one en route
      const avoid = new Set();
      if (L.stairsUp) avoid.add(L.stairsUp.y * L.W + L.stairsUp.x);
      if (L.stairsDown) avoid.add(L.stairsDown.y * L.W + L.stairsDown.x);
      (L.portals || []).forEach(p => avoid.add(p.y * L.W + p.x));
      avoid.delete(goal[1] * L.W + goal[0]);
      // BFS from the player's tile
      const sx = Phaser.Math.Clamp(Math.floor(this.player.x / T), 0, L.W - 1);
      const sy = Phaser.Math.Clamp(Math.floor(this.player.y / T), 0, L.H - 1);
      const prev = new Map([[sy * L.W + sx, -1]]);
      const q = [[sx, sy]];
      let found = false;
      while (q.length && !found) {
        const [x, y] = q.shift();
        for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          const nx = x + dx, ny = y + dy;
          if (nx < 0 || ny < 0 || nx >= L.W || ny >= L.H) continue;
          const i = ny * L.W + nx;
          if (prev.has(i)) continue;
          const cell = L.grid[i];
          if (cell === BLOCK || cell === WATER || avoid.has(i)) continue;
          prev.set(i, y * L.W + x);
          if (nx === goal[0] && ny === goal[1]) { found = true; break; }
          q.push([nx, ny]);
        }
      }
      const gi = goal[1] * L.W + goal[0];
      if (!prev.has(gi)) { this.requestMove(dir); return; }
      const path = [];
      let cur = gi;
      while (cur !== -1 && cur !== (sy * L.W + sx)) {
        path.unshift({ x: (cur % L.W) * T + T / 2, y: Math.floor(cur / L.W) * T + T / 2 });
        cur = prev.get(cur);
      }
      this.exitSuppress = 0; // walking into the exit should fire it
      this.autoNav = { path, dir };
    }

    // ---------- map payload ----------
    onMap(payload) {
      const cur = payload.current_room;
      const player = payload.player;
      if (!player) return;
      const roomEntry = (payload.rooms || []).find(r => r.vnum === player.vnum) || { mobs: [], players: [], items: [] };
      const roomData = cur && cur.vnum === player.vnum
        ? Object.assign({}, cur)
        : { vnum: player.vnum, name: roomEntry.name, description: '', sector: roomEntry.sector, flags: roomEntry.flags || [], exits: {} };
      roomData.zone = roomEntry.zone;
      if (!cur || cur.vnum !== player.vnum) {
        (roomEntry.exits || []).forEach(d => { roomData.exits[d] = { to_room: null, door: (roomEntry.doors || {})[d] || null }; });
      } else {
        for (const [d, ex] of Object.entries(roomData.exits || {})) {
          if (roomEntry.doors && roomEntry.doors[d]) ex.door = roomEntry.doors[d];
        }
      }

      if (this.lastVnum !== player.vnum) {
        const pm = MH.state.pendingMove;
        const moveDir = pm ? pm.dir : null;
        MH.state.pendingMove = null;
        this.lastVnum = player.vnum;
        const layout = MH.generateRoomTopDown(roomData);
        this.slideTransition(layout, moveDir);
        MH.bus.emit('room.entered', { room: roomData, zoneName: roomEntry.zoneName });
      }
      this.syncEntities(roomEntry);
      this.applyAtmosphere(payload);
    }

    // Zelda screen-slide: snapshot the old room, build the new one beneath,
    // slide the snapshot off in the direction of travel.
    slideTransition(layout, moveDir) {
      const ARRIVAL = { east: 'west', west: 'east', north: 'south', south: 'north', up: 'up', down: 'down' };
      const entryDir = moveDir ? (ARRIVAL[moveDir] || moveDir) : 'none';
      const slide = { north: [0, this.pxH], south: [0, -this.pxH], east: [-this.pxW, 0], west: [this.pxW, 0] }[moveDir];

      let snap = null;
      if (slide && this.layout) {
        try {
          snap = this.add.renderTexture(0, 0, this.pxW, this.pxH).setOrigin(0, 0).setDepth(900);
          // RenderTexture can't draw a Layer object itself - draw its children
          snap.draw(this.bgLayer.list.slice());
          snap.draw(this.tileLayer.list.slice());
          for (const ent of this.entities.values()) { if (ent.sprite) snap.draw(ent.sprite); }
          snap.draw(this.player);
        } catch (err) {
          // a broken slide must never block the room rebuild
          if (snap) { snap.destroy(); snap = null; }
        }
      }
      this.buildRoom(layout, entryDir);
      if (snap) {
        this.tweens.add({
          targets: snap, x: slide[0], y: slide[1], duration: 380, ease: 'cubic.inOut',
          onComplete: () => snap.destroy(),
        });
      } else {
        this.cameras.main.fadeIn(200, 0, 0, 0);
      }
    }

    onCombatUpdate(payload) {
      if (!this.layout || payload.vnum !== this.layout.vnum) return;
      // the MUD fights in rounds: give each round a visible beat - the
      // fighters feint toward each other as the server resolves the exchange
      if (payload.in_combat) {
        // telegraph: ~1.5s into the round (just before the next exchange),
        // the attacker rears up - you can FEEL the hit coming
        this.time.delayedCall(1450, () => {
          if (!MH.state.inCombat) return;
          for (const ent2 of this.entities.values()) {
            if (!ent2.data || !ent2.data.fighting || !ent2.sprite || !ent2.sprite.active) continue;
            this.tweens.add({ targets: ent2.sprite, scaleX: ent2.sprite.scaleX * 1.12, scaleY: ent2.sprite.scaleY * 1.12, duration: 160, yoyo: true });
            ent2.sprite.setTint(0xffb0a0);
            this.time.delayedCall(330, () => ent2.sprite && ent2.sprite.active && ent2.sprite.clearTint());
            break;
          }
        });
        for (const ent of this.entities.values()) {
          if (!ent.data || !ent.data.fighting || !ent.sprite) continue;
          const ang = Math.atan2(this.player.y - ent.sprite.y, this.player.x - ent.sprite.x);
          this.tweens.add({
            targets: ent.sprite, x: ent.sprite.x + Math.cos(ang) * 6, y: ent.sprite.y + Math.sin(ang) * 6,
            duration: 120, yoyo: true, ease: 'cubic.out',
          });
          this.tweens.add({
            targets: this.player, x: this.player.x - Math.cos(ang) * 4, y: this.player.y - Math.sin(ang) * 4,
            duration: 120, yoyo: true, ease: 'cubic.out', delay: 60,
          });
          break;
        }
      }
      (payload.mobs || []).forEach((mob, i) => {
        const ent = this.entities.get(`mob:${mob.name}:${i}`);
        if (!ent) return;
        this.updateEntity(ent, Object.assign({}, ent.data, mob));
        if (mob.fighting && !this.target) { this.target = ent; MH.bus.emit('target.set', ent.data); }
      });
      (payload.players || []).forEach(p => {
        const ent = this.entities.get(`pl:${p.name}`);
        if (ent) this.updateEntity(ent, Object.assign({}, ent.data, p));
      });
    }

    applyAtmosphere(payload) {
      const period = payload.time && payload.time.period;
      const outdoor = this.layout && !['inside', 'dungeon', 'cave', 'default'].includes(this.layout.theme);
      let alpha = 0, color = 0x101830;
      if (outdoor) {
        if (period === 'night' || period === 'midnight') alpha = 0.38;
        else if (period === 'evening' || period === 'dusk') { alpha = 0.22; color = 0x40280f; }
        else if (period === 'dawn' || period === 'morning') { alpha = 0.10; color = 0x402a20; }
      }
      this.nightTint.setFillStyle(color, alpha);
      const precip = payload.weather && payload.weather.precipitation;
      const wantRain = outdoor && precip && precip !== 'none';
      if (wantRain && !this.weatherEmitter) {
        const snow = /snow/i.test(precip);
        this.weatherEmitter = this.add.particles(0, -10, snow ? 'px_bubble' : 'px_rain', {
          x: { min: 0, max: this.pxW }, speedY: snow ? { min: 20, max: 45 } : { min: 180, max: 260 },
          speedX: snow ? { min: -10, max: 10 } : -20, lifespan: 2000, quantity: snow ? 1 : 3, alpha: 0.7,
        }).setDepth(45);
      } else if (!wantRain && this.weatherEmitter) {
        this.weatherEmitter.destroy();
        this.weatherEmitter = null;
      }
      if (this.layout && this.layout.swim && !this.bubbleEmitter) {
        this.bubbleEmitter = this.add.particles(0, this.pxH, 'px_bubble', {
          x: { min: 0, max: this.pxW }, speedY: { min: -35, max: -12 }, lifespan: 3500, quantity: 1, alpha: 0.5,
        }).setDepth(45);
      }
    }

    // ---------- update loop ----------
    update() {
      if (!this.layout || this.dead) return;
      const k = this.keys;
      const pad = this.input.gamepad && this.input.gamepad.total ? this.input.gamepad.getPad(0) : null;
      let ax = 0, ay = 0;
      if (pad) {
        const gx = pad.axes.length ? pad.axes[0].getValue() : 0;
        const gy = pad.axes.length > 1 ? pad.axes[1].getValue() : 0;
        if (Math.abs(gx) > 0.3) ax = gx;
        if (Math.abs(gy) > 0.3) ay = gy;
        if (pad.left) ax = -1; if (pad.right) ax = 1;
        if (pad.up) ay = -1; if (pad.down) ay = 1;
        if (pad.A && !this._padA) this.tryAttack();
        this._padA = pad.A;
      }
      if (k.left.isDown || k.left2.isDown) ax = -1;
      if (k.right.isDown || k.right2.isDown) ax = 1;
      if (k.up.isDown || k.up2.isDown) ay = -1;
      if (k.down.isDown || k.down2.isDown) ay = 1;

      // a move that never got an answer (lost line, eaten message) must not
      // wedge the input forever
      if (MH.state.pendingMove && Date.now() - MH.state.pendingMove.sentAt > 4000) MH.state.pendingMove = null;
      // keyboard can never stay wedged off while the game has focus
      if (!this.input.keyboard.enabled) {
        const a = document.activeElement;
        if (!a || a === document.body || a.tagName === 'CANVAS') this.input.keyboard.enabled = true;
      }
      // combat flag with no living opponent in the room clears itself
      if (MH.state.inCombat) {
        const anyFighter = [...this.entities.values()].some(e => e.kind === 'mob' && e.data && e.data.fighting);
        if (!anyFighter) {
          this._combatIdle = (this._combatIdle || 0) + this.game.loop.delta;
          if (this._combatIdle > 7000) { MH.setCombat(false); this._combatIdle = 0; }
        } else {
          this._combatIdle = 0;
        }
      } else {
        this._combatIdle = 0;
      }
      const locked = !!MH.state.pendingMove && Date.now() - MH.state.pendingMove.sentAt < 2500;
      const manual = ax !== 0 || ay !== 0;
      if (manual && this.autoNav) this.autoNav = null;

      const baseSpeed = this.layout.swim ? 70 : 110;
      if (locked) {
        this.player.setVelocity(0, 0);
      } else if (this.autoNav && this.autoNav.path.length) {
        const wp = this.autoNav.path[0];
        const dx = wp.x - this.player.x, dy = wp.y - this.player.y;
        const d = Math.hypot(dx, dy);
        if (d < 4) this.autoNav.path.shift();
        else {
          this.player.setVelocity((dx / d) * baseSpeed, (dy / d) * baseSpeed);
          this.setFacing(dx, dy);
          this.playWalk();
        }
        if (!this.autoNav.path.length) { this.player.setVelocity(0, 0); this.autoNav = null; }
      } else if (manual) {
        const len = Math.hypot(ax, ay) || 1;
        let vx = (ax / len) * baseSpeed, vy = (ay / len) * baseSpeed;
        // gap magnetism: pressing into a border wall near a doorway slides
        // you along the wall into the opening (forgiving Zelda doors)
        const L = this.layout, T = TD().T;
        const body = this.player.body;
        const gapMidX = Math.floor(L.W / 2) * T + T / 2;
        const gapMidY = Math.floor(L.H / 2) * T + T / 2;
        const PULL = 70, RANGE = 4.5 * T;
        if (ax < 0 && body.blocked.left && L.gaps.west && Math.abs(this.player.y - gapMidY) < RANGE && vy === 0) {
          vy = Math.sign(gapMidY - this.player.y) * PULL;
        } else if (ax > 0 && body.blocked.right && L.gaps.east && Math.abs(this.player.y - gapMidY) < RANGE && vy === 0) {
          vy = Math.sign(gapMidY - this.player.y) * PULL;
        } else if (ay < 0 && body.blocked.up && L.gaps.north && Math.abs(this.player.x - gapMidX) < RANGE && vx === 0) {
          vx = Math.sign(gapMidX - this.player.x) * PULL;
        } else if (ay > 0 && body.blocked.down && L.gaps.south && Math.abs(this.player.x - gapMidX) < RANGE && vx === 0) {
          vx = Math.sign(gapMidX - this.player.x) * PULL;
        }
        this.player.setVelocity(vx, vy);
        this.setFacing(ax, ay);
        this.playWalk();
      } else {
        this.player.setVelocity(0, 0);
        this.player.anims.stop();
        this.player.setFrame(`${this.facing}0`);
      }

      // exits: physics overlap OR proximity+intent (pressing toward a gap
      // mouth within 16px) - two independent triggers so a missed overlap
      // can never strand anyone. Gated states explain themselves.
      {
        const b = this.player.body;
        const pb = new Phaser.Geom.Rectangle(b.x, b.y, b.width, b.height);
        let wantExit = null;
        for (const zone of this.exitZones.concat(this.featureZones || [])) {
          if (Phaser.Geom.Rectangle.Overlaps(zone.getBounds(), pb)) { wantExit = zone.exitDir; break; }
        }
        if (!wantExit && this.layout && this.layout.gaps) {
          const midX = Math.floor(this.layout.W / 2) * TD().T + TD().T / 2;
          const midY = Math.floor(this.layout.H / 2) * TD().T + TD().T / 2;
          const near = (gx, gy) => Math.hypot(this.player.x - gx, this.player.y - gy) < 22;
          if (this.layout.gaps.north && ay < 0 && near(midX, TD().T * 1.2)) wantExit = 'north';
          else if (this.layout.gaps.south && ay > 0 && near(midX, this.pxH - TD().T * 1.2)) wantExit = 'south';
          else if (this.layout.gaps.west && ax < 0 && near(TD().T * 1.2, midY)) wantExit = 'west';
          else if (this.layout.gaps.east && ax > 0 && near(this.pxW - TD().T * 1.2, midY)) wantExit = 'east';
        }
        if (wantExit) {
          if (MH.state.inCombat) {
            if (!this._gateFlash || now - this._gateFlash > 2500) {
              this._gateFlash = now;
              MH.bus.emit('flash', "You're fighting! Flee to escape, or finish it.");
            }
          } else if (locked || Date.now() <= this.exitSuppress) {
            // in-flight or cooling down: silent, resolves within a second
          } else {
            this.requestMove(wantExit);
          }
        }
      }

      const now = Date.now();

      // combat dance: face your target and circle it like a duelist - the
      // strafing is cosmetic, but it makes the 2s rounds feel alive
      const tgtEnt = MH.state.inCombat && this.target && this.entities.get(this.target.key);
      if (tgtEnt && tgtEnt.sprite && !manual && !this.autoNav && !locked && !this.dead) {
        const tgt = tgtEnt.sprite;
        this.setFacing(tgt.x - this.player.x, tgt.y - this.player.y);
        // comfort band: only reposition when clearly out of range - no
        // constant magnetic drag
        const want = this.preferredRange || this.classRange();
        const d0 = Phaser.Math.Distance.Between(this.player.x, this.player.y, tgt.x, tgt.y);
        if (d0 > want + 16 || d0 < Math.max(12, want - 14)) {
          const m = TD().T * 1.6;
          const ringD = Phaser.Math.Clamp(d0, want - 4, want + 4);
          const baseAng = Math.atan2(this.player.y - tgt.y, this.player.x - tgt.x);
          const ox = Phaser.Math.Clamp(tgt.x + Math.cos(baseAng) * ringD, m, this.pxW - m);
          const oy = Phaser.Math.Clamp(tgt.y + Math.sin(baseAng) * ringD, m, this.pxH - m);
          const ddx = ox - this.player.x, ddy = oy - this.player.y;
          const dd = Math.hypot(ddx, ddy);
          if (dd > 3) this.player.setVelocity((ddx / dd) * Math.min(34, dd * 2), (ddy / dd) * Math.min(34, dd * 2));
        } else {
          this.player.setVelocity(0, 0);
        }
        // ready stance: subtle bounce instead of statue idle
        if (!this.player.anims.isPlaying) {
          this.player.setFrame(`${this.facing}${Math.floor(now / 320) % 2}`);
        }
      }

      // calm NPCs wander to nearby spots, walk there, then idle
      for (const ent of this.entities.values()) {
        if (ent.kind !== 'mob' || ent.stalker || (ent.data && ent.data.fighting) || ent.data.shopkeeper) continue;
        if (!ent.wanderAt || now < ent.wanderAt || ent.wanderTween) continue;
        const L = this.layout, T2 = TD().T;
        const tx = Phaser.Math.Clamp(ent.homeX + (Math.random() * 90 - 45), 2.5 * T2, this.pxW - 2.5 * T2);
        const ty = Phaser.Math.Clamp(ent.homeY + (Math.random() * 60 - 30), 2.5 * T2, this.pxH - 2.5 * T2);
        const cell = L.grid[Math.floor(ty / T2) * L.W + Math.floor(tx / T2)];
        if (cell !== 0) { ent.wanderAt = now + 1200; continue; }
        const dist = Phaser.Math.Distance.Between(ent.sprite.x, ent.sprite.y, tx, ty);
        const tex = ent.sprite.texture.key;
        const anim = Math.abs(tx - ent.sprite.x) > Math.abs(ty - ent.sprite.y) ? `${tex}_walks` : (ty > ent.sprite.y ? `${tex}_walkd` : `${tex}_walku`);
        ent.sprite.setFlipX(tx < ent.sprite.x && anim.endsWith('walks'));
        ent.sprite.play(anim);
        ent.wanderTween = this.tweens.add({
          targets: ent.sprite, x: tx, y: ty, duration: (dist / 26) * 1000, ease: 'sine.inOut',
          onComplete: () => {
            ent.wanderTween = null;
            ent.wanderAt = Date.now() + 2500 + Math.random() * 5000;
            ent.sprite.anims.stop();
            ent.sprite.setFrame('d0');
          },
        });
      }

      // mob brains: approach with a weave, circle at fighting range with
      // occasional direction flips, back off when too close, keep apart
      // from each other, and never walk into walls
      const dt = this.game.loop.delta / 1000;
      const L2 = this.layout, T2 = TD().T;
      const walkable = (x, y) => {
        const cx = Math.floor(x / T2), cy = Math.floor(y / T2);
        if (cx < 1 || cy < 1 || cx >= L2.W - 1 || cy >= L2.H - 1) return false;
        return L2.grid[cy * L2.W + cx] === 0;
      };
      const fighters = [...this.entities.values()].filter(e =>
        e.kind === 'mob' && e.sprite && (e.stalker || (e.data && e.data.fighting)));
      for (const ent of fighters) {
        if (!ent.ai) ent.ai = { dir: (MH.hashStr(ent.key) % 2) ? 1 : -1, nextFlip: now + 1000 + (MH.hashStr(ent.key) % 1500) };
        const dx = this.player.x - ent.sprite.x, dy = this.player.y - ent.sprite.y;
        const d = Math.hypot(dx, dy) || 1;
        const casterMob = /caster|ghost|elemental/.test(ent.sprite.texture.key);
        const ring = ent.data.fighting ? (casterMob ? 52 : 22) : 30;
        let vx = 0, vy = 0;
        if (d > ring + 22) {
          // approach with a hunting weave, not a beeline
          const sp = ent.data.fighting ? 78 : 46;
          const weave = Math.sin(now / 480 + MH.hashStr(ent.key)) * 0.45;
          const a = Math.atan2(dy, dx) + weave;
          vx = Math.cos(a) * sp;
          vy = Math.sin(a) * sp;
        } else if (d < ring - 8) {
          // too close: give ground
          vx = -(dx / d) * 34;
          vy = -(dy / d) * 34;
        } else if (ent.data.fighting) {
          // circle the player, flipping direction unpredictably
          if (now > ent.ai.nextFlip) {
            if (Math.random() < 0.6) ent.ai.dir *= -1;
            ent.ai.nextFlip = now + 1100 + Math.random() * 1900;
          }
          vx = (-dy / d) * 26 * ent.ai.dir;
          vy = (dx / d) * 26 * ent.ai.dir;
        }
        // personal space: mobs shoulder each other apart
        for (const other of fighters) {
          if (other === ent || !other.sprite) continue;
          const sx = ent.sprite.x - other.sprite.x, sy = ent.sprite.y - other.sprite.y;
          const sd = Math.hypot(sx, sy);
          if (sd > 0.01 && sd < 16) { vx += (sx / sd) * 28; vy += (sy / sd) * 28; }
        }
        // axis-wise wall respect
        const nx = ent.sprite.x + vx * dt, ny = ent.sprite.y + vy * dt;
        if (walkable(nx, ent.sprite.y)) ent.sprite.x = nx;
        if (walkable(ent.sprite.x, ny)) ent.sprite.y = ny;
        const moving = Math.abs(vx) + Math.abs(vy) > 4;
        const tex = ent.sprite.texture.key;
        if (moving) {
          const anim = Math.abs(dx) > Math.abs(dy) ? `${tex}_walks` : (dy > 0 ? `${tex}_walkd` : `${tex}_walku`);
          ent.sprite.setFlipX(Math.abs(dx) > Math.abs(dy) && dx < 0);
          if (!ent.sprite.anims.isPlaying || ent.sprite.anims.currentAnim.key !== anim) ent.sprite.play(anim);
        } else if (ent.sprite.anims.isPlaying) {
          ent.sprite.anims.stop();
        }
      }

      {
        const m = TD().T * 1.1;
        this.player.x = Phaser.Math.Clamp(this.player.x, m, this.pxW - m);
        this.player.y = Phaser.Math.Clamp(this.player.y, m, this.pxH - m);
      }
      if (this.heroGlow) { this.heroGlow.x = this.player.x; this.heroGlow.y = this.player.y; }

      // footstep dust gives weight to movement
      const moving = Math.abs(this.player.body.velocity.x) + Math.abs(this.player.body.velocity.y) > 10;
      if (moving && (!this._lastStep || now - this._lastStep > 260)) {
        this._lastStep = now;
        const puff = this.add.image(this.player.x, this.player.y + 9, 'px_poof')
          .setScale(0.6).setAlpha(0.35).setDepth(6);
        this.tweens.add({ targets: puff, scale: 1.3, alpha: 0, duration: 380, onComplete: () => puff.destroy() });
      }

      // labels + hp bars follow
      for (const ent of this.entities.values()) {
        if (ent.label && ent.sprite) { ent.label.x = ent.sprite.x; ent.label.y = ent.sprite.y - (ent.data.boss ? 26 : 18); }
        if (ent.fightMark && ent.sprite) { ent.fightMark.x = ent.sprite.x; ent.fightMark.y = ent.sprite.y - 26; }
        if (ent.questMark && ent.sprite) { ent.questMark.x = ent.sprite.x; }
        if (ent.hpbar && ent.sprite) this.drawHpBar(ent);
      }
      // depth-sort actors by y so overlap reads correctly
      this.player.setDepth(10 + this.player.y / 1000);
      for (const ent of this.entities.values()) {
        if (ent.sprite && ent.kind !== 'item') ent.sprite.setDepth(10 + ent.sprite.y / 1000);
      }

      if (this.layout.dark && this.darkRT.visible) {
        this.darkRT.clear();
        this.darkRT.fill(0x000008, 0.88);
        this.darkRT.erase('px_light', this.player.x - 128, this.player.y - 128);
      }
    }

    setFacing(dx, dy) {
      if (Math.abs(dx) > Math.abs(dy)) { this.facing = 's'; this.player.setFlipX(dx < 0); }
      else if (dy > 0) this.facing = 'd';
      else if (dy < 0) this.facing = 'u';
    }
    playWalk() {
      const tex = this.playerTex();
      const anim = `${tex}_walk${this.facing}`;
      if (!this.player.anims.isPlaying || this.player.anims.currentAnim.key !== anim) this.player.play(anim);
    }
  }

  MH.TopRoomScene = TopRoomScene;
})();
