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
      this.input.mouse && this.input.mouse.disableContextMenu();
      // street life: friendly NPCs murmur idle chatter now and then
      this.time.addEvent({ delay: 7000, loop: true, callback: () => this.npcChatter() });
      this.physics.world.setBounds(0, 0, this.pxW, this.pxH);
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

      // right-click on open ground: your own action menu
      this.input.on('pointerdown', (pointer, over) => {
        if (!(pointer.rightButtonDown && pointer.rightButtonDown())) return;
        if (over && over.length) return;   // an entity menu took it
        if (MH.contextMenu) MH.contextMenu('self', null, pointer.event.clientX, pointer.event.clientY);
      });

      // cinematic grade + bloom (WebGL only): falls back gracefully on canvas
      try {
        if (this.cameras.main.postFX) {
          this.cameras.main.postFX.addVignette(0.5, 0.5, 1.1, 0.12);
          // bloom makes bright FX (fire/holy/lightning) and light sources glow
          // (the heaviest postFX — gated by graphics quality). Kept gentle so it
          // accents lights instead of washing the whole scene into haze.
          if (!MH.gfx || MH.gfx.bloom) {
            this.bloomFx = this.cameras.main.postFX.addBloom(0xffffff, 1, 1, 0.7, 0.5, 5);
          }
          const cm = this.cameras.main.postFX.addColorMatrix();
          cm.saturate(0.18, true);
          cm.contrast(0.12, true);
          this.gradeFx = cm;
        }
      } catch (_) { /* older GPU / canvas renderer */ }
      // react to live graphics-quality changes: toggle bloom + rebuild room FX
      MH.bus.on('gfx.changed', () => this.onGfxChanged());
      // occasional ambient sound keyed to the zone + time of day
      this.time.addEvent({ delay: 5500, loop: true, callback: () => this.ambientSfx() });

      this.solids = this.physics.add.staticGroup();
      this.tileLayer = this.add.layer();
      this.bgLayer = this.add.layer().setDepth(-10);
      // parallax depth: overlay atmosphere drifts opposite to the player so the
      // scene reads as layered planes instead of one flat sheet. Containers are
      // offset wholesale each frame, leaving each child's own tweens intact.
      this.pxFar = this.add.container(0, 0).setDepth(8);    // behind the actors
      this.pxNear = this.add.container(0, 0).setDepth(44);  // foreground haze
      this.rimTint = 0xfff2cc;

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
      // rim-light: an additive copy of the sprite, scaled up a touch and nudged
      // toward the light, so a bright edge peeks out and the actor pops off the
      // floor. Synced to the live frame each tick.
      this.playerRim = this.add.sprite(this.player.x, this.player.y, 'td_player_warrior', 'd0')
        .setScale(this.player.scaleX * 1.08).setDepth(9.6)
        .setBlendMode(Phaser.BlendModes.ADD).setAlpha(0.3).setTint(this.rimTint)
        .setVisible(!MH.gfx || MH.gfx.rim);
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
      // soft drop-shadow blob, drawn under every actor to ground them
      if (!this.textures.exists('px_shadow')) {
        const sc = document.createElement('canvas');
        sc.width = 64; sc.height = 32;
        const sx = sc.getContext('2d');
        const sg = sx.createRadialGradient(32, 16, 2, 32, 16, 30);
        sg.addColorStop(0, 'rgba(0,0,0,0.55)');
        sg.addColorStop(0.6, 'rgba(0,0,0,0.28)');
        sg.addColorStop(1, 'rgba(0,0,0,0)');
        sx.fillStyle = sg;
        sx.save(); sx.translate(32, 16); sx.scale(1, 0.42); sx.beginPath();
        sx.arc(0, 0, 30, 0, 7); sx.fill(); sx.restore();
        this.textures.addCanvas('px_shadow', sc);
      }
      // ground-detail decals (white, tinted to the theme at placement) used to
      // break up the flat tile grid — pebbles, grass blades, cracks, patches
      const mkTex = (key, w, h, draw) => {
        if (this.textures.exists(key)) return;
        const c = document.createElement('canvas'); c.width = w; c.height = h;
        draw(c.getContext('2d')); this.textures.addCanvas(key, c);
      };
      mkTex('gd_speck', 16, 16, g => {
        g.fillStyle = '#fff';
        const pts = [[3, 4], [9, 3], [6, 9], [12, 11], [4, 12], [11, 6]];
        for (const [px, py] of pts) g.fillRect(px, py, 1 + (px % 2), 1 + (py % 2));
      });
      mkTex('gd_blades', 16, 16, g => {
        g.strokeStyle = '#fff'; g.lineWidth = 1;
        for (const bx of [4, 7, 9, 12]) { g.beginPath(); g.moveTo(bx, 15); g.lineTo(bx + (bx % 3) - 1, 15 - (5 + bx % 4)); g.stroke(); }
      });
      mkTex('gd_crack', 20, 20, g => {
        g.strokeStyle = '#fff'; g.lineWidth = 1;
        g.beginPath(); g.moveTo(2, 5); g.lineTo(8, 9); g.lineTo(6, 14); g.lineTo(13, 12); g.lineTo(18, 16); g.stroke();
      });
      mkTex('gd_patch', 24, 24, g => {
        const rg = g.createRadialGradient(12, 12, 1, 12, 12, 12);
        rg.addColorStop(0, 'rgba(255,255,255,0.9)'); rg.addColorStop(1, 'rgba(255,255,255,0)');
        g.fillStyle = rg; g.beginPath(); g.arc(12, 12, 12, 0, 7); g.fill();
      });
      // soft directional edge-shadow strip (dark → transparent) to ground walls
      mkTex('gd_edge', 32, 24, g => {
        const lg = g.createLinearGradient(0, 0, 0, 24);
        lg.addColorStop(0, 'rgba(0,0,0,0.42)'); lg.addColorStop(1, 'rgba(0,0,0,0)');
        g.fillStyle = lg; g.fillRect(0, 0, 32, 24);
      });
      // wall-mounted decoration decals (mounted on inward-facing walls)
      mkTex('wd_torch', 14, 22, g => {
        g.fillStyle = '#3a2c1c'; g.fillRect(6, 9, 2, 11);                 // bracket
        g.fillStyle = '#5a4630'; g.fillRect(4, 8, 6, 3);                  // cup
        g.fillStyle = '#ff8a2a'; g.beginPath(); g.ellipse(7, 5, 3.4, 5, 0, 0, 7); g.fill();   // flame
        g.fillStyle = '#ffd060'; g.beginPath(); g.ellipse(7, 6, 1.8, 3, 0, 0, 7); g.fill();
      });
      mkTex('wd_banner', 16, 24, g => {                                  // white, tinted at placement
        g.fillStyle = '#5a4a2a'; g.fillRect(2, 1, 12, 2);                // rod
        g.fillStyle = '#fff';
        g.beginPath(); g.moveTo(3, 3); g.lineTo(13, 3); g.lineTo(13, 18); g.lineTo(8, 22); g.lineTo(3, 18); g.closePath(); g.fill();
        g.fillStyle = 'rgba(0,0,0,0.18)'; g.fillRect(7, 5, 2, 12);       // crease
      });
      mkTex('wd_moss', 20, 14, g => {
        g.fillStyle = '#fff';
        for (const [mx, my, r] of [[5, 8, 4], [11, 6, 3], [14, 10, 3.5], [8, 11, 2.5]]) { g.beginPath(); g.arc(mx, my, r, 0, 7); g.fill(); }
      });
      mkTex('wd_vine', 14, 26, g => {
        g.strokeStyle = '#fff'; g.lineWidth = 1.4;
        g.beginPath(); g.moveTo(7, 0); g.quadraticCurveTo(3, 8, 7, 14); g.quadraticCurveTo(11, 20, 6, 26); g.stroke();
        g.fillStyle = '#fff';
        for (const [vx, vy] of [[4, 6], [10, 12], [4, 18], [9, 22]]) { g.beginPath(); g.ellipse(vx, vy, 2.4, 1.4, 0.6, 0, 7); g.fill(); }
      });
      // ambient wildlife (tinted at placement): a flyer and a ground critter
      mkTex('cr_fly', 12, 8, g => {                  // bird/bat/butterfly silhouette
        g.fillStyle = '#fff';
        g.beginPath(); g.ellipse(6, 4, 1.6, 1.2, 0, 0, 7); g.fill();      // body
        g.beginPath(); g.moveTo(6, 4); g.quadraticCurveTo(1, 0, 0, 3); g.quadraticCurveTo(3, 4, 6, 4); g.fill();   // L wing
        g.beginPath(); g.moveTo(6, 4); g.quadraticCurveTo(11, 0, 12, 3); g.quadraticCurveTo(9, 4, 6, 4); g.fill();  // R wing
      });
      mkTex('cr_bug', 9, 9, g => {                   // butterfly/insect
        g.fillStyle = '#fff';
        g.beginPath(); g.arc(3, 4, 2.4, 0, 7); g.fill(); g.beginPath(); g.arc(6, 5, 2.2, 0, 7); g.fill();
        g.fillStyle = 'rgba(0,0,0,0.3)'; g.fillRect(4, 3, 1, 4);
      });
      mkTex('cr_ground', 12, 7, g => {               // rat/lizard/fish
        g.fillStyle = '#fff';
        g.beginPath(); g.ellipse(6, 4, 4, 2, 0, 0, 7); g.fill();          // body
        g.beginPath(); g.moveTo(10, 4); g.lineTo(12, 2); g.lineTo(12, 6); g.fill();  // tail
        g.fillStyle = 'rgba(0,0,0,0.4)'; for (const lx of [4, 6, 8]) g.fillRect(lx, 6, 1, 1);  // legs
      });
      // extra landmark centrepieces (keyed as zt_prop_* so they slot in directly)
      mkTex('zt_prop_campfire', 30, 26, g => {
        g.fillStyle = '#5a5048';                                          // ring stones
        for (const sx of [4, 10, 18, 24]) { g.beginPath(); g.arc(sx, 22, 3, 0, 7); g.fill(); }
        g.strokeStyle = '#6a4a2a'; g.lineWidth = 2.4;                     // crossed logs
        g.beginPath(); g.moveTo(7, 23); g.lineTo(22, 17); g.moveTo(22, 23); g.lineTo(7, 17); g.stroke();
        g.fillStyle = '#ff8a2a'; g.beginPath(); g.moveTo(15, 4); g.quadraticCurveTo(9, 14, 15, 18); g.quadraticCurveTo(21, 14, 15, 4); g.fill();
        g.fillStyle = '#ffd861'; g.beginPath(); g.moveTo(15, 9); g.quadraticCurveTo(12, 14, 15, 17); g.quadraticCurveTo(18, 14, 15, 9); g.fill();
      });
      mkTex('zt_prop_well', 30, 30, g => {
        g.fillStyle = '#7a7f8c'; g.beginPath(); g.ellipse(15, 23, 11, 5, 0, 0, 7); g.fill();   // rim
        g.fillStyle = '#2a4a66'; g.beginPath(); g.ellipse(15, 23, 7.5, 3.2, 0, 0, 7); g.fill(); // water
        g.fillStyle = '#6a7078'; g.fillRect(4, 12, 3, 12); g.fillRect(23, 12, 3, 12);           // posts
        g.fillStyle = '#5a4030'; g.beginPath(); g.moveTo(2, 12); g.lineTo(15, 3); g.lineTo(28, 12); g.closePath(); g.fill();  // roof
      });
      mkTex('zt_prop_altar', 28, 26, g => {
        g.fillStyle = '#6a6678'; g.fillRect(6, 14, 16, 10);               // base
        g.fillStyle = '#8a8698'; g.fillRect(3, 11, 22, 4);                // slab
        const rg = g.createRadialGradient(14, 9, 1, 14, 9, 10);
        rg.addColorStop(0, 'rgba(200,160,255,0.95)'); rg.addColorStop(1, 'rgba(200,160,255,0)');
        g.fillStyle = rg; g.beginPath(); g.arc(14, 9, 9, 0, 7); g.fill();  // holy glow
      });
      this.playerShadow = this.add.image(this.player.x, this.player.y, 'px_shadow')
        .setDepth(5).setAlpha(0.4).setScale(0.34);
      this.nightTint = this.add.rectangle(0, 0, this.pxW, this.pxH, 0x101830, 0).setOrigin(0, 0).setDepth(42);
      // cinematic colour-cast layer: a soft per-zone/time grade laid over the scene
      this.gradeCast = this.add.rectangle(0, 0, this.pxW, this.pxH, 0x000000, 0)
        .setOrigin(0, 0).setDepth(41).setBlendMode(Phaser.BlendModes.OVERLAY);
      // reusable off-screen stamp used to carve light pools out of the darkness layer
      this.lightStamp = this.add.image(0, 0, 'px_light').setVisible(false);
      // screen-edge vignette texture (clear centre, solid edge) used for the
      // damage pulse and lightning wash — tinted at pulse time
      if (!this.textures.exists('px_vignette')) {
        const vc = document.createElement('canvas');
        vc.width = vc.height = 256;
        const vx = vc.getContext('2d');
        const vg = vx.createRadialGradient(128, 128, 60, 128, 128, 150);
        vg.addColorStop(0, 'rgba(255,255,255,0)');
        vg.addColorStop(0.7, 'rgba(255,255,255,0.15)');
        vg.addColorStop(1, 'rgba(255,255,255,1)');
        vx.fillStyle = vg;
        vx.fillRect(0, 0, 256, 256);
        this.textures.addCanvas('px_vignette', vc);
      }
      // red combat-damage vignette + a full-screen flash plate (lightning/crits)
      this.dmgVignette = this.add.image(this.pxW / 2, this.pxH / 2, 'px_vignette')
        .setDisplaySize(this.pxW, this.pxH).setDepth(48).setAlpha(0)
        .setTint(0xe02020).setScrollFactor(0);
      this.screenFlash = this.add.rectangle(0, 0, this.pxW, this.pxH, 0xffffff, 0)
        .setOrigin(0, 0).setDepth(49).setBlendMode(Phaser.BlendModes.ADD);
      this.weatherEmitter = null;
      this.rainSplash = null;
      this.heatHaze = null;
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
      MH.bus.on('mob.move', e => this.onMobMove(e));
      this.pendingArrivals = {};
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
      MH.bus.on('ui.typing', on => {
        this.input.keyboard.enabled = !on;
        // enabled=false alone doesn't stop Phaser preventDefaulting WASD/arrows/
        // space, which would swallow them from text fields — toggle capture too
        try { if (on) this.input.keyboard.disableGlobalCapture(); else this.input.keyboard.enableGlobalCapture(); } catch (_) {}
      });
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
      const { T, FLOOR, BLOCK, WATER } = TD();
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
      this.lightSources = [];
      this.corpses = [];
      if (this.weatherEmitter) { this.weatherEmitter.destroy(); this.weatherEmitter = null; }
      if (this.rainFar) { this.rainFar.destroy(); this.rainFar = null; }
      if (this.rainSplash) { this.rainSplash.destroy(); this.rainSplash = null; }
      if (this.heatHaze) { this.heatHaze.destroy(); this.heatHaze = null; }
      if (this.fogEmitter) { this.fogEmitter.destroy(); this.fogEmitter = null; }
      if (this.wornAura) { this.wornAura.destroy(); this.wornAura = null; }
      if (this.bubbleEmitter) { this.bubbleEmitter.destroy(); this.bubbleEmitter = null; }
      if (this.critters) { this.critters.forEach(c => { this.tweens.killTweensOf(c); c.destroy(); }); }
      this.critters = [];
      this.reactiveProps = [];   // props that sway/flare when the player passes
      // tall props live in the scene root (not the tile layer) so they y-sort
      // against the player for walk-behind occlusion; track them to clean up
      if (this.occluders) { this.occluders.forEach(o => o.destroy()); }
      this.occluders = [];
      if (this.groundWeather) { this.groundWeather.forEach(o => o.destroy()); this.groundWeather = null; }

      const th = layout.theme;
      const zk = layout.zoneKey && this.textures.exists(`zt_${layout.zoneKey}_floor0`) ? layout.zoneKey : null;
      const zt = zk ? MH.ZONE_THEMES[zk] : null;
      const checker = zt && zt.floorKind === 'checker';

      // real terrain tile kit (handoff art) when available for this sector,
      // else fall back to the procedural floor/border generators
      const kit = MH.tilekit && MH.tilekit.isReady() ? MH.tilekit : null;
      const kitTerrain = kit ? kit.terrainFor(layout.sector || layout.theme) : null;
      const useKit = !!(kit && kitTerrain && kit.hasTerrain(kitTerrain));
      this.kitTiles = [];

      // floor everywhere, then border/obstacles/water from the grid
      const vrng = MH.mulberry32(layout.vnum ^ 0xf10c);
      const Wd = layout.W, Hd = layout.H;
      for (let y = 0; y < Hd; y++) {
        for (let x = 0; x < Wd; x++) {
          const cell = layout.grid[y * Wd + x];
          if (useKit) {
            // base floor on every cell from the variants atlas
            const floorImg = this.add.image(x * T, y * T, 'mh_variants', kit.floorVariantFrame(kitTerrain))
              .setOrigin(0, 0).setDisplaySize(T, T);
            this.bgLayer.add(floorImg); this.kitTiles.push(floorImg);
            const N = y === 0, S = y === Hd - 1, Wl = x === 0, E = x === Wd - 1;
            const border = N || S || Wl || E;
            let piece = null;
            if (border) {
              const gap = cell === FLOOR;   // walkable border cell = an exit opening
              if (N && Wl) piece = 'cornerNW'; else if (N && E) piece = 'cornerNE';
              else if (S && E) piece = 'cornerSE'; else if (S && Wl) piece = 'cornerSW';
              else if (N) piece = gap ? 'openN' : 'wallN';
              else if (S) piece = gap ? 'openS' : 'wallS';
              else if (Wl) piece = gap ? 'openW' : 'wallW';
              else if (E) piece = gap ? 'openE' : 'wallE';
            } else if (layout.stairsUp && x === layout.stairsUp.x && y === layout.stairsUp.y) {
              piece = 'stairUp';
            } else if (layout.stairsDown && x === layout.stairsDown.x && y === layout.stairsDown.y) {
              piece = 'stairDown';
            } else if (cell === BLOCK) {
              piece = 'wallN';   // interior obstacle
            }
            if (piece) {
              const top = this.add.image(x * T, y * T, 'mh_terrain', kit.terrainFrame(kitTerrain, piece))
                .setOrigin(0, 0).setDisplaySize(T, T).setDepth(1);
              this.tileLayer.add(top); this.kitTiles.push(top);
            } else if (cell === WATER) {
              const spr = this.add.sprite(x * T, y * T, 'sm_water', '0').setOrigin(0, 0).setDisplaySize(T, T).setDepth(1).setAlpha(0.95);
              spr.play('sm_water_anim');
              const liquid = (zt && zt.water) || (MH.THEMES[th] && MH.THEMES[th].liquid) || '#3a6a9a';
              spr.setTint(Phaser.Display.Color.HexStringToColor(liquid).color | 0x404040);
              this.tileLayer.add(spr);
            }
            continue;
          }
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
      // day/night grade on the kit tiles (world-layer only)
      if (useKit) this.applyKitTint();
      // scatter ground detail + ground the walls with edge shadows
      this.decorateGround(layout, th);
      this.decorateWalls(layout, th);

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

      // worn roads run from the room's heart to each cardinal gap - the
      // town's paths out are visible at a glance
      if (this.textures.exists('zt_road') && layout.gaps) {
        const midXt = Math.floor(layout.W / 2), midYt = Math.floor(layout.H / 2);
        const lay = (x, y, vertical) => {
          const img = this.add.image(x * T + T / 2, y * T + T / 2, 'zt_road')
            .setDisplaySize(T, T).setDepth(0.5).setAlpha(0.9);
          if (!vertical) img.setRotation(Math.PI / 2);
          this.bgLayer.add(img);
        };
        if (layout.gaps.north) for (let y = 0; y <= midYt; y++) lay(midXt, y, true);
        if (layout.gaps.south) for (let y = midYt; y < layout.H; y++) lay(midXt, y, true);
        if (layout.gaps.west) for (let x = 0; x <= midXt; x++) lay(x, midYt, false);
        if (layout.gaps.east) for (let x = midXt; x < layout.W; x++) lay(x, midYt, false);
        // gateway pillars where a road leaves for another zone
        if (this.textures.exists('zt_prop_pillar')) {
          const flank = (x1, y1, x2, y2) => {
            for (const [fx, fy] of [[x1, y1], [x2, y2]]) {
              const pl = this.add.image(fx * T + T / 2, (fy + 1) * T, 'zt_prop_pillar')
                .setOrigin(0.5, 1).setDepth(3).setScale(1 / MH.SMOOTH_SS);
              this.tileLayer.add(pl);
            }
          };
          const xz = d => layout.exits[d] && layout.exits[d].to_zone;
          if (layout.gaps.north && xz('north')) flank(midXt - 3, 1, midXt + 3, 1);
          if (layout.gaps.south && xz('south')) flank(midXt - 3, layout.H - 3, midXt + 3, layout.H - 3);
          if (layout.gaps.west && xz('west')) flank(1, midYt - 3, 1, midYt + 2);
          if (layout.gaps.east && xz('east')) flank(layout.W - 2, midYt - 3, layout.W - 2, midYt + 2);
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
        // drop-shadow grounds every prop on the floor
        this.tileLayer.add(this.add.image(prop.x * T + T / 2, (prop.y + 1) * T - 1, 'px_shadow')
          .setDepth(2.5).setAlpha(0.3).setScale(0.26 * (prop.scale || 1)));
        if (prop.name && this.textures.exists(`zt_prop_${prop.name}`)) {
          const img = this.add.image(prop.x * T + T / 2, (prop.y + 1) * T, `zt_prop_${prop.name}`)
            .setOrigin(0.5, 1).setDepth(3).setScale((prop.scale || 1) / MH.SMOOTH_SS);
          // scenery rewards curiosity: flavor text, and some of it is usable
          if (MH.PROP_FLAVOR && MH.PROP_FLAVOR[prop.name]) {
            img.setInteractive({ useHandCursor: true });
            img.on('pointerdown', pointer => {
              if (!MH.immersion) return;
              const cx = pointer.event.clientX, cy = pointer.event.clientY;
              const acts = [];
              if (prop.name === 'fountain') {
                acts.push({ label: '🜄 Drink', fn: () => MH.sendCommand('drink') });
                const p = MH.state.player || {};
                for (const it of (p.inventory || []).filter(i => (i.item_type || i.type) === 'drink').slice(0, 3)) {
                  acts.push({ label: `⚱ Fill ${(it.short || it.name).slice(0, 18)}`, fn: () => MH.sendCommand(`fill ${MH.mobKeyword(it.name)}`) });
                }
              } else if (['stump', 'bench'].includes(prop.name)) {
                acts.push({ label: '🪑 Sit', fn: () => MH.sendCommand('sit') });
                acts.push({ label: '😴 Rest', fn: () => MH.sendCommand('rest') });
              } else if (prop.name === 'brazier' || prop.name === 'candles') {
                acts.push({ label: '😴 Rest by the warmth', fn: () => MH.sendCommand('rest') });
              }
              acts.push({ label: '👁 Examine', fn: () => MH.immersion.propFlavor(prop.name) });
              if (acts.length > 1 && MH.popover) MH.popover.show(cx, cy, (MH.PROP_FLAVOR[prop.name] || [prop.name])[0], acts);
              else MH.immersion.propFlavor(prop.name);
            });
          }
          this.tileLayer.add(img);
          const glowTint = MH.GLOW_PROPS && MH.GLOW_PROPS[prop.name];
          if (glowTint) {
            const gx = prop.x * T + T / 2, gy = prop.y * T + T * 0.3;
            const g = this.add.image(gx, gy, 'fx_glow')
              .setBlendMode(Phaser.BlendModes.ADD).setAlpha(0.22).setScale(0.32).setTint(glowTint).setDepth(35);
            this.tweens.add({ targets: g, alpha: 0.34, duration: 900 + (prop.x * 137 % 700), yoyo: true, repeat: -1, ease: 'sine.inOut' });
            this.tileLayer.add(g);
            // a torch/brazier/candle also carves a flickering pool of light out of the dark
            this.lightSources.push({ x: gx, y: gy, r: 78, seed: (prop.x * 53 + prop.y * 17) % 1000 });
          }
        } else {
          const img = this.add.image(prop.x * T, (prop.y + 1) * T, propSet[prop.idx % 3])
            .setOrigin(0.25, 1).setDepth(3).setScale(0.85 / MH.SMOOTH_SS);
          this.tileLayer.add(img);
        }
      }
      this.placeGravestones(layout);
      this.placeLandmark(layout, th);
      this.decorateFromDescription(layout, th);
      this.applySignatureRoom(layout, th);
      this.scatterClutter(layout, th);
      this.spawnCritters(layout, th);
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
      MH.bus.emit('zone.theme', { zoneKey: layout.zoneKey, theme: layout.theme, dark: !!layout.dark });
    }

    // Phase 1 room richness: scatter themed ground detail over the flat tile
    // grid (grass, pebbles, cracks, mossy patches) and lay soft edge-shadows
    // where the floor meets walls/obstacles, so the room reads as a real place.
    decorateGround(layout, th) {
      const { T, FLOOR, BLOCK } = TD();
      const DECO = {
        field:    { tex: ['gd_blades', 'gd_speck', 'gd_patch'], tint: [0x6e8a4a, 0x8a7a4a], density: 0.20 },
        forest:   { tex: ['gd_blades', 'gd_patch', 'gd_speck'], tint: [0x4c7a3c, 0x6a5a3a], density: 0.24 },
        swamp:    { tex: ['gd_patch', 'gd_blades', 'gd_speck'], tint: [0x5a6a3a, 0x4a5a4a], density: 0.22 },
        hills:    { tex: ['gd_blades', 'gd_speck'], tint: [0x7a8a4a, 0x8a7a50], density: 0.18 },
        desert:   { tex: ['gd_speck', 'gd_crack'], tint: [0xc9a35a, 0xb8924a], density: 0.15 },
        mountain: { tex: ['gd_crack', 'gd_speck'], tint: [0x8a90a0, 0x6a7080], density: 0.16 },
        cave:     { tex: ['gd_crack', 'gd_speck', 'gd_patch'], tint: [0x5a5060, 0x6a5a4a], density: 0.20 },
        dungeon:  { tex: ['gd_crack', 'gd_speck'], tint: [0x4a4458, 0x5a5060], density: 0.18 },
        underground: { tex: ['gd_crack', 'gd_speck'], tint: [0x4a4458, 0x5a5060], density: 0.18 },
        inside:   { tex: ['gd_speck', 'gd_patch'], tint: [0x6a5a3a, 0x5a5048], density: 0.10 },
        city:     { tex: ['gd_speck', 'gd_crack'], tint: [0x6a6258, 0x7a7068], density: 0.10 },
        default:  { tex: ['gd_speck', 'gd_patch'], tint: [0x6a6458, 0x5a5448], density: 0.12 },
      };
      const cfg = DECO[th] || DECO.default;
      const rng = MH.mulberry32((layout.vnum ^ 0x5bd1e9) >>> 0);
      const grid = layout.grid, W = layout.W, H = layout.H;
      const isFloor = (x, y) => x >= 0 && y >= 0 && x < W && y < H && grid[y * W + x] === FLOOR;
      const isBlock = (x, y) => x < 0 || y < 0 || x >= W || y >= H || grid[y * W + x] === BLOCK;
      for (let y = 1; y < H - 1; y++) {
        for (let x = 1; x < W - 1; x++) {
          if (!isFloor(x, y)) continue;
          // scatter detail decals
          if (rng() < cfg.density) {
            const tex = cfg.tex[(rng() * cfg.tex.length) | 0];
            const tint = cfg.tint[(rng() * cfg.tint.length) | 0];
            const d = this.add.image(x * T + 2 + rng() * (T - 4), y * T + 2 + rng() * (T - 4), tex)
              .setDepth(0.4).setAlpha(0.18 + rng() * 0.22).setTint(tint)
              .setScale(0.5 + rng() * 0.7).setRotation(tex === 'gd_blades' ? 0 : rng() * 6.28);
            this.tileLayer.add(d);
          }
          // edge shadows against adjacent walls/obstacles, grounding them
          const sides = [[0, -1, 0], [0, 1, 180], [-1, 0, 270], [1, 0, 90]];
          for (const [dx, dy, deg] of sides) {
            if (!isBlock(x + dx, y + dy)) continue;
            const e = this.add.image(x * T + T / 2, y * T + T / 2, 'gd_edge')
              .setDisplaySize(T, T * 0.7).setOrigin(0.5, 0).setDepth(0.6).setAlpha(0.55)
              .setAngle(deg);
            // origin pin: rotate around centre then shove to the wall side
            e.x = x * T + T / 2 + dx * (T / 2);
            e.y = y * T + T / 2 + dy * (T / 2);
            this.tileLayer.add(e);
          }
        }
      }
    }

    // Ambient wildlife: a few themed critters wander each room — butterflies
    // and birds in the wilds, bats and rats in the dark, pigeons in the city,
    // fish in the water — so rooms feel inhabited and alive, not static.
    spawnCritters(layout, th) {
      if (MH.gfx && MH.gfx.quality === 'low') return;
      const { T } = TD();
      // [texture, tint, flying, count]
      const SET = {
        field: [['cr_bug', 0xf0d860, 1, 3], ['cr_fly', 0x303030, 1, 1]],
        meadow: [['cr_bug', 0xf0a0d0, 1, 3]], hills: [['cr_bug', 0xf0d860, 1, 2]],
        forest: [['cr_bug', 0xf0a0d0, 1, 2], ['cr_fly', 0x282828, 1, 1]],
        elven: [['cr_bug', 0xbff0a0, 1, 3]],
        swamp: [['cr_bug', 0x9adf6a, 1, 3]],
        cave: [['cr_fly', 0x1a1a24, 1, 3], ['cr_ground', 0x6a5a4a, 0, 1]],
        dungeon: [['cr_fly', 0x1a1a24, 1, 2], ['cr_ground', 0x5a4a3a, 0, 1]],
        underground: [['cr_ground', 0x5a4a3a, 0, 2]],
        mountain: [['cr_fly', 0xdedede, 1, 2]],
        desert: [['cr_ground', 0xc9a35a, 0, 2]],
        inside: [['cr_ground', 0x6a5a4a, 0, 2]],
        city: [['cr_fly', 0x8a8a8a, 1, 2], ['cr_ground', 0x5a4a3a, 0, 1]],
        underwater: [['cr_ground', 0x8fd0ff, 0, 4]], water_swim: [['cr_ground', 0x8fd0ff, 0, 3]], water_noswim: [['cr_ground', 0x8fd0ff, 0, 2]],
        default: [['cr_bug', 0xf0d860, 1, 2]],
      };
      let groups = SET[th] || SET.default;
      // day/night fauna swap: fireflies drift through the wilds after dark
      const period = (MH.state.lastPayload && MH.state.lastPayload.time && MH.state.lastPayload.time.period) || 'day';
      const night = ['night', 'midnight', 'evening', 'dusk'].includes(period);
      const NIGHT = {
        field: [['cr_bug', 0xc8ff70, 1, 4, true]], meadow: [['cr_bug', 0xc8ff70, 1, 4, true]],
        hills: [['cr_bug', 0xc8ff70, 1, 3, true]], forest: [['cr_bug', 0xbfff80, 1, 4, true], ['cr_fly', 0x202028, 1, 1]],
        elven: [['cr_bug', 0xd0ffa0, 1, 4, true]], swamp: [['cr_bug', 0x9aff80, 1, 4, true]],
      };
      if (night && NIGHT[th]) groups = NIGHT[th];
      const qMul = (MH.gfx && MH.gfx.quality === 'medium') ? 0.6 : 1;
      const rng = MH.mulberry32((layout.vnum ^ 0x7c1d) >>> 0);
      const m = T * 2;
      for (const [tex, tint, fly, n, glow] of groups) {
        const cnt = Math.max(1, Math.round(n * qMul));
        for (let i = 0; i < cnt; i++) {
          const x = m + rng() * (this.pxW - m * 2);
          const y = fly ? T * 1.4 + rng() * (this.pxH * 0.5) : m + rng() * (this.pxH - m * 2);
          const c = this.add.image(x, y, tex).setTint(tint).setDepth(fly ? 12 : 6)
            .setScale(fly ? 0.9 : 0.85).setAlpha(fly ? 0.92 : 0.95);
          if (glow) {   // fireflies: additive bloom + a soft blink
            c.setBlendMode(Phaser.BlendModes.ADD).setScale(0.7);
            this.tweens.add({ targets: c, alpha: 0.25, duration: 900 + rng() * 700, yoyo: true, repeat: -1, ease: 'sine.inOut' });
          }
          // movement state, driven each frame in updateInner (robust, no tween chains)
          c.fly = !!fly; c.baseScaleX = c.scaleX; c.flapPhase = rng() * 6.28; c.glow = !!glow;
          c.spd = fly ? (glow ? 14 + rng() * 12 : 28 + rng() * 22) : 18 + rng() * 14;
          c.tx = m + rng() * (this.pxW - m * 2);
          c.ty = fly ? T * 1.4 + rng() * (this.pxH * 0.5) : m + rng() * (this.pxH - m * 2);
          c.pauseUntil = 0;
          this.critters.push(c);
        }
      }
    }
    // occasional ambient sound: birdsong/crickets in the wilds, drips in caves,
    // wind on the heights, and a steady crackle near a campfire
    ambientSfx() {
      if (!this.layout || !MH.sfx || this.dead) return;
      const th = this.layout.theme;
      const period = (MH.state.lastPayload && MH.state.lastPayload.time && MH.state.lastPayload.time.period) || 'day';
      const night = ['night', 'midnight', 'evening', 'dusk'].includes(period);
      if (this._campfire) MH.sfx.crackle();
      if (Math.random() > 0.55) return;   // sparse, not every tick
      if (['field', 'forest', 'hills', 'swamp', 'meadow', 'elven'].includes(th)) { if (night) MH.sfx.cricket(); else MH.sfx.birdChirp(); }
      else if (['cave', 'dungeon', 'underground'].includes(th)) MH.sfx.drip();
      else if (['mountain', 'desert'].includes(th)) MH.sfx.wind();
      else if (th === 'city' && !night) MH.sfx.birdChirp();
    }
    // frame-driven critter wander (called from updateInner)
    updateCritters(now, dt) {
      if (!this.critters || !this.critters.length) return;
      const { T } = TD();
      const m = T * 2;
      for (const c of this.critters) {
        if (!c.active) continue;
        if (now >= c.pauseUntil) {
          const dx = c.tx - c.x, dy = c.ty - c.y, d = Math.hypot(dx, dy);
          if (d < 4) {
            // arrived: brief pause, then pick a fresh destination
            c.pauseUntil = now + (c.fly ? 120 : 350) + Math.random() * (c.fly ? 500 : 1100);
            c.tx = m + Math.random() * (this.pxW - m * 2);
            c.ty = c.fly ? T * 1.4 + Math.random() * (this.pxH * 0.5) : m + Math.random() * (this.pxH - m * 2);
          } else {
            const v = c.spd * dt;
            c.x += (dx / d) * v; c.y += (dy / d) * v;
            c.setFlipX(dx < 0);
          }
        }
        if (c.fly) c.scaleX = c.baseScaleX * (0.5 + 0.5 * Math.abs(Math.sin(now * 0.018 + c.flapPhase)));  // wing flap
      }
    }

    // ---- Phase 3: rooms as spaces ----
    // Tall props you can walk behind. They go in the scene root (not the tile
    // layer) at a y-based depth in the player's band so the player is occluded
    // when standing behind them, and draws in front when standing below them.
    isTallProp(name) {
      return ['tree', 'pine', 'deadtree', 'pillar', 'statue', 'runestone', 'lamppost',
        'crystal', 'icecrystal', 'stall', 'fountain', 'brazier', 'anvil', 'gravestone', 'banner'].includes(name);
    }
    // Add a prop image with correct layering: tall ones occlude (root, depth
    // 10+y), the rest are flat scenery in the tile layer (depth 3+y).
    addPropImage(img, baseY, name) {
      if (this.isTallProp(name)) {
        img.setDepth(10 + baseY / 1000);
        (this.occluders = this.occluders || []).push(img);
      } else {
        img.setDepth(3 + baseY / 1000);
        this.tileLayer.add(img);
      }
      return img;
    }

    // ---- Phase 4: signature hero rooms ----
    // Spawn one fully-featured prop at a grid cell (shadow, glow, reactivity,
    // interaction) — the building block for curated set-pieces.
    GLOW_FOR(name) {
      return ({ fountain: 0x9fd9ff, well: 0x9fd9ff, crystal: 0xc792ff, icecrystal: 0x9fd0ff, statue: 0xffe9c0,
        runestone: 0xffd089, brazier: 0xff9a4a, campfire: 0xff9a4a, candles: 0xffe9a8, lamppost: 0xffd98a,
        lantern: 0xcfff90, altar: 0xc8a0ff, mushrooms: 0xb06ce0 })[name];
    }
    spawnFeatureProp(name, cellX, cellY, scaleMul) {
      if (!this.textures.exists(`zt_prop_${name}`) || !this.layout) return null;
      const { T, FLOOR } = TD();
      const W = this.layout.W, H = this.layout.H, grid = this.layout.grid;
      cellX = Math.round(cellX); cellY = Math.round(cellY);
      if (cellX < 1 || cellY < 1 || cellX > W - 2 || cellY > H - 2) return null;
      if (grid[cellY * W + cellX] !== FLOOR) return null;
      const bx = cellX * T + T / 2, by = (cellY + 1) * T;
      const scale = (scaleMul || 1.2) / MH.SMOOTH_SS;
      this.tileLayer.add(this.add.image(bx, by - 1, 'px_shadow').setDepth(2.6).setAlpha(0.32).setScale(scale * 0.4));
      const img = this.add.image(bx, by, `zt_prop_${name}`).setOrigin(0.5, 1).setScale(scale);
      this.addPropImage(img, by, name);
      const SWAY = new Set(['tree', 'pine', 'deadtree', 'bush', 'flowers', 'mushrooms', 'reeds', 'lilypad', 'cactus', 'stump', 'coral']);
      const g = this.GLOW_FOR(name);
      if (g) {
        const glow = this.add.image(bx, by - T * 0.6, 'fx_glow').setBlendMode(Phaser.BlendModes.ADD)
          .setAlpha(0.13).setScale(0.55).setTint(g).setDepth(34);
        this.tweens.add({ targets: glow, alpha: 0.24, scale: 0.72, duration: 2000, yoyo: true, repeat: -1, ease: 'sine.inOut' });
        this.fxList && this.fxList.push(glow);
        if (name === 'fountain') this.registerReactive(img, 'ripple');
        else this.registerReactive(img, 'flare', { glow, glowMax: 0.13, tint: g });
      } else if (SWAY.has(name)) this.registerReactive(img, 'sway', { tint: g || 0x8fbf6a });
      img.setInteractive({ useHandCursor: true });
      img.on('pointerdown', pointer => {
        if (pointer.rightButtonDown && pointer.rightButtonDown()) return;
        const acts = this.propActions(name, bx, by);
        if (MH.popover) MH.popover.show(pointer.event.clientX, pointer.event.clientY, (MH.PROP_FLAVOR && MH.PROP_FLAVOR[name] ? MH.PROP_FLAVOR[name][0] : name), acts);
      });
      img.on('pointerover', () => MH.bus.emit('flash', `${MH.PROP_FLAVOR && MH.PROP_FLAVOR[name] ? MH.PROP_FLAVOR[name][0] : name} — click to interact`));
      return img;
    }
    // a soft coloured light wash that gives a hero room its own mood
    signatureWash(color, alpha) {
      const r = this.add.rectangle(0, 0, this.pxW, this.pxH, color, alpha || 0.1)
        .setOrigin(0, 0).setBlendMode(Phaser.BlendModes.SCREEN).setDepth(31);
      this.tileLayer.add(r);
    }
    // Detect a named hero room and dress it with a curated set-piece + mood.
    // Symmetric compositions around the room centre make these feel built.
    applySignatureRoom(layout, th) {
      const name = (layout.name || '').toLowerCase();
      if (!name) return;
      const W = layout.W, H = layout.H, cx = Math.floor(W / 2), cy = Math.floor(H / 2);
      const pair = (prop, dx, dy, sc) => { this.spawnFeatureProp(prop, cx - dx, cy + dy, sc); this.spawnFeatureProp(prop, cx + dx, cy + dy, sc); };
      const center = (prop, sc) => this.spawnFeatureProp(prop, cx, cy, sc);
      if (/throne|hall of kings|royal court/.test(name)) {
        center('statue', 1.7); pair('brazier', 3, 0, 1.2); pair('pillar', 5, -2, 1.5); this.signatureWash(0xffcf6a, 0.1);
      } else if (/temple|shrine|chapel|sanctuary|cathedral|altar/.test(name)) {
        center('altar', 1.5); pair('candles', 2, 1, 1.1); pair('pillar', 4, -1, 1.5); this.signatureWash(0xbfe0ff, 0.1);
      } else if (/tavern|\binn\b|alehouse|\bpub\b|drunk|tankard/.test(name)) {
        pair('barrel', 4, 2, 1.1); pair('crate', 5, 0, 1); center('candles', 0.9); this.signatureWash(0xffb060, 0.11);
      } else if (/librar|archive|scriptorium|study|reading/.test(name)) {
        pair('bookpile', 4, -1, 1.2); pair('bookpile', 4, 2, 1.1); center('candles', 0.9); this.signatureWash(0xbfd0e8, 0.08);
      } else if (/forge|smith|anvil|foundry/.test(name)) {
        center('anvil', 1.4); pair('brazier', 3, 1, 1.2); pair('crate', 5, -1, 1); this.signatureWash(0xff9a4a, 0.12);
      } else if (/fountain|plaza|square|courtyard/.test(name)) {
        center('fountain', 1.7); pair('lamppost', 5, -2, 1.3); pair('flowers', 3, 2, 1); this.signatureWash(0xcfe0ff, 0.07);
      } else if (/bank|vault|treasur|counting house/.test(name)) {
        center('statue', 1.5); pair('pillar', 4, -1, 1.5); pair('urn', 3, 2, 1); this.signatureWash(0xffe0a0, 0.09);
      } else if (/guild|barracks|armor|arena|training/.test(name)) {
        pair('banner', 5, -2, 1.2); pair('crate', 4, 1, 1); center('runestone', 1.2); this.signatureWash(0xffd9a0, 0.08);
      } else if (/graveyard|cemeter|crypt|tomb|catacomb|mausoleum|sepulch/.test(name)) {
        pair('gravestone', 3, 0, 1.2); pair('deadtree', 5, -1, 1.4); center('candles', 0.9); this.signatureWash(0x9a86c8, 0.1);
      } else if (/garden|grove|orchard|arbor/.test(name)) {
        pair('tree', 4, -1, 1.5); pair('flowers', 2, 2, 1.1); center('fountain', 1.3); this.signatureWash(0xbfe8a0, 0.08);
      }
    }

    // ---- Phase 1: living, reactive rooms ----
    // Register a prop so it responds when the player passes: 'sway' (plants
    // wobble + shed a leaf), 'flare' (fire/light brightens), 'ripple' (water).
    registerReactive(img, kind, opts) {
      if (!this.reactiveProps) this.reactiveProps = [];
      this.reactiveProps.push(Object.assign({ img, kind, cd: 0 }, opts || {}));
    }
    leafPuff(x, y, tint) {
      const tex = this.textures.exists('zt_px_leaf') ? 'zt_px_leaf' : 'px_white';
      const e = this.add.particles(x, y, tex, {
        speedX: { min: -18, max: 18 }, speedY: { min: -26, max: -6 }, gravityY: 36,
        lifespan: 760, quantity: 2, scale: { start: 0.7, end: 0 }, alpha: { start: 0.9, end: 0 },
        rotate: { min: 0, max: 360 }, tint: tint || 0x8fbf6a, emitting: false,
      }).setDepth(9);
      e.explode(2);
      this.time.delayedCall(900, () => e.destroy());
    }
    dustPuff(x, y) {
      const e = this.add.particles(x, y, this.textures.exists('zt_px_soft') ? 'zt_px_soft' : 'px_white', {
        speedX: { min: -14, max: 14 }, speedY: { min: -6, max: 2 }, lifespan: 420, quantity: 2,
        scale: { start: 0.5, end: 0 }, alpha: { start: 0.35, end: 0 }, tint: 0xbfae90, emitting: false,
      }).setDepth(4);
      e.explode(2);
      this.time.delayedCall(500, () => e.destroy());
    }
    // called each frame: critters flush, plants sway, fires flare, water ripples,
    // dust kicks up under a moving player — the room answers your presence
    reactToPlayer(now, dt) {
      if (!this.player) return;
      const px = this.player.x, py = this.player.y, { T } = TD();
      // critters flee when you get close
      if (this.critters) {
        const m = T * 2;
        for (const c of this.critters) {
          if (!c.active) continue;
          const dx = c.x - px, dy = c.y - py, d2 = dx * dx + dy * dy;
          const R = c.fly ? 50 : 40;
          if (d2 < R * R) {
            const d = Math.sqrt(d2) || 1;
            c.tx = Phaser.Math.Clamp(c.x + (dx / d) * 130, m, this.pxW - m);
            c.ty = Phaser.Math.Clamp(c.y + (dy / d) * 130, c.fly ? T : m, this.pxH - m);
            c.pauseUntil = 0;
            if (!c._fleeUntil) { c._fleeUntil = now + 1100; c._spd0 = c.spd; c.spd = c.spd * 2.4; }
          } else if (c._fleeUntil && now > c._fleeUntil) { c._fleeUntil = 0; c.spd = c._spd0 || c.spd; }
        }
      }
      // reactive props
      if (this.reactiveProps) {
        for (const rp of this.reactiveProps) {
          if (!rp.img || !rp.img.active) continue;
          const dx = rp.img.x - px, dy = rp.img.y - py, d2 = dx * dx + dy * dy;
          if (rp.kind === 'sway') {
            if (d2 < 28 * 28 && now > rp.cd) {
              rp.cd = now + 650;
              if (this.motionOk()) {
                const dir = dx < 0 ? -1 : 1;
                this.tweens.add({ targets: rp.img, angle: { from: dir * -8, to: 0 }, duration: 540, ease: 'elastic.out' });
                this.leafPuff(rp.img.x, rp.img.y - rp.img.displayHeight * 0.5, rp.tint);
              }
            }
          } else if (rp.kind === 'flare' && rp.glow && rp.glow.active) {
            const near = d2 < 64 * 64;
            if (near && now > rp.cd) {
              rp.cd = now + 900;
              this.tweens.add({ targets: rp.glow, alpha: (rp.glowMax || 0.2) * 2.1, scale: rp.glow.scaleX * 1.5, duration: 240, yoyo: true, ease: 'sine.out' });
              this.spark(rp.img.x, rp.img.y - rp.img.displayHeight * 0.6, rp.tint || 0xffd060);
            }
          } else if (rp.kind === 'ripple') {
            if (d2 < 40 * 40 && now > rp.cd) {
              rp.cd = now + 750;
              if (MH.fx && MH.fx.ringShock) MH.fx.ringShock(this, rp.img.x, rp.img.y - 4, 0x9fd9ff, 9, 360);
            }
          }
        }
      }
      // walk-behind: fade a tall prop when the player is hidden behind it so
      // you never fully lose your character
      if (this.occluders) {
        for (const o of this.occluders) {
          if (!o.active) continue;
          const behind = py < o.y && py > o.y - o.displayHeight && Math.abs(o.x - px) < o.displayWidth * 0.42;
          const want = behind ? 0.5 : 1;
          if (Math.abs(o.alpha - want) > 0.01) o.setAlpha(Phaser.Math.Linear(o.alpha, want, 0.18));
        }
      }
      // dust under a moving player on dry ground
      if (this._pPrev) {
        const moved = Math.hypot(px - this._pPrev.x, py - this._pPrev.y);
        const dry = !this.layout.swim && !['water_swim', 'water_noswim', 'underwater'].includes(this.layout.theme);
        if (moved > 0.6 && dry && now > (this._dustCd || 0) && this.motionOk()) {
          this._dustCd = now + 230;
          this.dustPuff(px, py + 2);
        }
      }
      this._pPrev = { x: px, y: py };
    }

    // Phase 4: wall-mounted decoration on inward-facing walls — torches (which
    // also light dark rooms), hanging banners, moss, and vines — so the walls
    // read as surfaces with stuff on them, not bare blocks.
    decorateWalls(layout, th) {
      if (MH.gfx && MH.gfx.quality === 'low') return;
      const { T, FLOOR, BLOCK } = TD();
      const SETS = {
        city: ['wd_banner', 'wd_torch', 'wd_vine'], inside: ['wd_banner', 'wd_torch'],
        cave: ['wd_torch', 'wd_moss'], dungeon: ['wd_torch', 'wd_banner'], underground: ['wd_torch', 'wd_moss'],
        mountain: ['wd_moss'], forest: ['wd_vine', 'wd_moss'], swamp: ['wd_vine', 'wd_moss'],
        field: ['wd_vine'], hills: ['wd_moss'], desert: [], default: ['wd_moss'],
      };
      const set = SETS[th] || SETS.default;
      if (!set.length) return;
      const zt = layout.zoneKey && MH.ZONE_THEMES ? MH.ZONE_THEMES[layout.zoneKey] : null;
      const bannerTint = (zt && zt.glow) || 0xc24a4a;
      const rng = MH.mulberry32((layout.vnum ^ 0x4d2b9) >>> 0);
      const grid = layout.grid, W = layout.W, H = layout.H;
      const dens = (MH.gfx && MH.gfx.quality === 'medium') ? 0.12 : 0.18;
      let placed = 0;
      for (let y = 0; y < H - 1 && placed < 16; y++) {
        for (let x = 1; x < W - 1 && placed < 16; x++) {
          if (grid[y * W + x] !== BLOCK || grid[(y + 1) * W + x] !== FLOOR) continue;  // south-facing wall
          if (rng() > dens) continue;
          const name = set[(rng() * set.length) | 0];
          const bx = x * T + T / 2, by = y * T + T * 0.96;
          if (name === 'wd_torch') {
            this.tileLayer.add(this.add.image(bx, by, 'wd_torch').setOrigin(0.5, 1).setDepth(2.3).setScale(0.85));
            const gy = by - T * 0.5;
            const glow = this.add.image(bx, gy, 'fx_glow').setBlendMode(Phaser.BlendModes.ADD)
              .setAlpha(0.22).setScale(0.3).setTint(0xff9a4a).setDepth(35);
            this.tweens.add({ targets: glow, alpha: 0.34, scale: 0.36, duration: 700 + rng() * 500, yoyo: true, repeat: -1, ease: 'sine.inOut' });
            this.tileLayer.add(glow); this.fxList && this.fxList.push(glow);
            if (this.lightSources) this.lightSources.push({ x: bx, y: gy, r: 66, seed: (x * 41 + y * 13) % 1000 });
          } else {
            const tint = name === 'wd_banner' ? bannerTint : name === 'wd_vine' ? 0x4c7a3c : 0x5a8a4a;
            this.tileLayer.add(this.add.image(bx, by, name).setOrigin(0.5, 1).setDepth(2.3).setTint(tint).setScale(0.85).setAlpha(name === 'wd_moss' ? 0.85 : 1));
          }
          placed++;
        }
      }
    }

    // Phase 3: denser, themed clutter (cosmetic, non-blocking) clustered near
    // walls to fill the empty floor, plus a couple of "discovery" glints that
    // reward wandering the room — the exploration ask. Quality-scaled.
    // Read the room's actual prose and place props that match what it describes,
    // so a room that says "a marble fountain" gets a fountain, "ancient tomes
    // line the shelves" gets bookpiles, etc. Deterministic per-vnum so a room
    // always looks the same. This is what makes each room feel hand-placed.
    decorateFromDescription(layout, th) {
      const text = ((layout.name || '') + ' . ' + (layout.description || '')).toLowerCase();
      if (!text.trim()) return;
      const { T, FLOOR, BLOCK } = TD();
      // keyword -> prop. First match wins per prop; order matters for specificity.
      // [regex, propName, placement]  placement: 'wall' | 'edge' | 'center' | 'any'
      const RULES = [
        [/\bfountain|water spout|bubbling spring|basin\b/, 'fountain', 'center'],
        [/\bwell\b|wishing well/, 'fountain', 'center'],
        [/\baltar|shrine|sacrificial/, 'runestone', 'center'],
        [/\bstatue|idol|effigy|monument|sculpture|figure of|likeness of/, 'statue', 'center'],
        [/\bpillar|column|colonnade|pillars/, 'pillar', 'edge'],
        [/\brunestone|runic|standing stone|obelisk|monolith|carved stone/, 'runestone', 'center'],
        [/\banvil|forge|smithy|bellows/, 'anvil', 'edge'],
        [/\bbrazier|hearth|fire ?pit|bonfire|campfire|roaring fire|coals|embers|fireplace/, 'brazier', 'center'],
        [/\bcandle|candelabra|tapers/, 'candles', 'wall'],
        [/\blamppost|street ?lamp|gaslight|lamp post/, 'lamppost', 'edge'],
        [/\blantern/, 'lantern', 'wall'],
        [/\bbanner|flag|pennant|tapestr/, 'banner', 'wall'],
        [/\bbook|tome|scroll|librar|shelves|bookshelf|grimoire/, 'bookpile', 'wall'],
        [/\bgear|cog|machine|mechanism|machinery|clockwork/, 'gear', 'edge'],
        [/\bpipe|plumbing|conduit/, 'pipe', 'wall'],
        [/\bcrate|crates|cargo|supplies|\bbox(es)?\b/, 'crate', 'wall'],
        [/\bbarrel|cask|keg|barrels/, 'barrel', 'wall'],
        [/\burn|vase|amphora|\bpot(s|tery)?\b/, 'urn', 'wall'],
        [/\bstall|market|vendor|cart|booth|wares/, 'stall', 'edge'],
        [/\bfence|railing|palisade|paddock/, 'fence', 'edge'],
        [/\bgrave|tomb|headstone|sepulchre|crypt|burial/, 'gravestone', 'edge'],
        [/\bbones|skeleton|skull|remains|carcass|corpse/, 'bones', 'edge'],
        [/\bcobweb|\bweb\b|webbing|spider/, 'web', 'wall'],
        [/\brubble|debris|ruins|collapsed|broken stone|crumbling/, 'rubble', 'edge'],
        [/\bcrystal|geode|gemstone|glowing crystal|quartz/, 'crystal', 'edge'],
        [/\bicicle|frozen|ice crystal|sheet of ice/, 'icecrystal', 'edge'],
        [/\bsnow|snowdrift|drift of/, 'snowdrift', 'edge'],
        [/\bmushroom|fungus|fungal|toadstool/, 'mushrooms', 'edge'],
        [/\breed|rushes|cattail|marsh grass/, 'reeds', 'edge'],
        [/\blily|lilypad|lily pad/, 'lilypad', 'any'],
        [/\bcactus|cacti|succulent/, 'cactus', 'edge'],
        [/\bflower|blossom|bloom|petal|wildflower|garden bed/, 'flowers', 'edge'],
        [/\bpine|fir tree|evergreen|conifer|spruce/, 'pine', 'edge'],
        [/\bdead tree|withered tree|gnarled|bare branch|leafless/, 'deadtree', 'edge'],
        [/\bstump|fallen tree|fallen log|\blog\b/, 'stump', 'edge'],
        [/\bbush|shrub|hedge|thicket|bramble|undergrowth/, 'bush', 'edge'],
        [/\btree|oak|elm|willow|birch|maple|grove|orchard/, 'tree', 'edge'],
        [/\bboulder|\brock|stones|stony|rocky/, 'rock', 'edge'],
        [/\bcoral|reef/, 'coral', 'edge'],
        [/\bshell|seashell|conch/, 'shell', 'edge'],
      ];
      const picks = [];
      const seen = new Set();
      for (const [re, prop, place] of RULES) {
        if (picks.length >= 4) break;
        if (seen.has(prop)) continue;
        if (re.test(text) && this.textures.exists(`zt_prop_${prop}`)) { seen.add(prop); picks.push({ prop, place }); }
      }
      if (!picks.length) return;

      const grid = layout.grid, W = layout.W, H = layout.H;
      const cx = Math.floor(W / 2), cy = Math.floor(H / 2);
      const taken = new Set((layout.props || []).map(p => `${p.x},${p.y}`));
      const isFloor = (x, y) => x > 1 && y > 1 && x < W - 2 && y < H - 2 && grid[y * W + x] === FLOOR && !taken.has(`${x},${y}`);
      const nearWall = (x, y) => grid[(y - 1) * W + x] === BLOCK || grid[(y + 1) * W + x] === BLOCK
        || grid[y * W + x - 1] === BLOCK || grid[y * W + x + 1] === BLOCK;
      const GLOWN = { fountain: 0x9fd9ff, crystal: 0xc792ff, icecrystal: 0x9fd0ff, statue: 0xffe9c0,
        runestone: 0xffd089, brazier: 0xff9a4a, candles: 0xffe9a8, lamppost: 0xffd98a, lantern: 0xcfff90, mushrooms: 0xb06ce0 };
      const INTERACT = { fountain: 'water', brazier: 'warm', runestone: 'holy', statue: 'holy', candles: 'warm' };

      picks.forEach((pick, idx) => {
        const rng = MH.mulberry32((layout.vnum ^ (0x51ed2 + idx * 0x9e37)) >>> 0);
        // find a fitting free cell for this placement style
        let best = null;
        for (let g = 0; g < 80 && !best; g++) {
          const x = 2 + ((rng() * (W - 4)) | 0), y = 2 + ((rng() * (H - 4)) | 0);
          if (!isFloor(x, y)) continue;
          const wall = nearWall(x, y);
          const central = Math.abs(x - cx) < 3 && Math.abs(y - cy) < 3;
          if (pick.place === 'center' && (central || g > 50)) best = { x, y };
          else if (pick.place === 'wall' && wall) best = { x, y };
          else if (pick.place === 'edge' && (wall || g > 40)) best = { x, y };
          else if (pick.place === 'any') best = { x, y };
          else if (g > 60) best = { x, y };   // fallback: take any floor
        }
        if (!best) return;
        taken.add(`${best.x},${best.y}`);
        const name = pick.prop;
        const bx = best.x * T + T / 2, by = (best.y + 1) * T;
        const scale = (pick.place === 'center' ? 1.5 : 1.1 + rng() * 0.25) / MH.SMOOTH_SS;
        this.tileLayer.add(this.add.image(bx, by - 1, 'px_shadow').setDepth(2.6).setAlpha(0.32).setScale(scale * 0.4));
        const img = this.add.image(bx, by, `zt_prop_${name}`).setOrigin(0.5, 1).setScale(scale);
        this.addPropImage(img, by, name);
        // glowing features pulse softly and draw the eye
        const SWAY = new Set(['tree', 'pine', 'deadtree', 'bush', 'flowers', 'mushrooms', 'reeds', 'lilypad', 'cactus', 'stump', 'coral']);
        if (GLOWN[name]) {
          const glow = this.add.image(bx, by - T * 0.6, 'fx_glow').setBlendMode(Phaser.BlendModes.ADD)
            .setAlpha(0.12).setScale(0.5).setTint(GLOWN[name]).setDepth(34);
          this.tweens.add({ targets: glow, alpha: 0.22, scale: 0.66, duration: 2000, yoyo: true, repeat: -1, ease: 'sine.inOut' });
          this.fxList && this.fxList.push(glow);
          if (name === 'fountain') this.registerReactive(img, 'ripple');
          else this.registerReactive(img, 'flare', { glow, glowMax: 0.12, tint: GLOWN[name] });
        } else if (SWAY.has(name)) {
          this.registerReactive(img, 'sway', { tint: GLOWN[name] || 0x8fbf6a });
        }
        // examine / interact: these are the features the prose called out
        img.setInteractive({ useHandCursor: true });
        img.on('pointerdown', pointer => {
          if (pointer.rightButtonDown && pointer.rightButtonDown()) return;
          const acts = this.propActions(name, bx, by);
          const label = (MH.PROP_FLAVOR && MH.PROP_FLAVOR[name] ? MH.PROP_FLAVOR[name][0] : name);
          if (MH.popover) MH.popover.show(pointer.event.clientX, pointer.event.clientY, label, acts);
        });
        img.on('pointerover', () => MH.bus.emit('flash', `${MH.PROP_FLAVOR && MH.PROP_FLAVOR[name] ? MH.PROP_FLAVOR[name][0] : name} — click to interact`));
      });
    }

    // Phase 2: the verbs a prop offers — what you can DO with it. Shared by
    // landmarks and prose-props so every feature is genuinely interactive, with
    // a little ceremony (a ripple, warm light, a blessing) when you use it.
    propActions(name, bx, by) {
      const { T } = TD();
      const P = MH.fx && MH.fx.PAL;
      const react = kind => {
        try {
          if (kind === 'water') { if (MH.fx) MH.fx.ringShock(this, bx, by - T * 0.3, 0x9fd9ff, 14, 420); this.spark(bx, by - T * 0.3, 0x9fd9ff); }
          else if (kind === 'warm') { if (MH.fx) MH.fx.risers(this, bx, by - T * 0.4, P ? P.fire : { a: 0xffd060, b: 0xff8a2a }, 5); this.cameras.main.flash(120, 50, 25, 0); }
          else if (kind === 'holy') { if (MH.fx) { MH.fx.pillar(this, bx, by, P ? P.holy : { a: 0xfff6d0, b: 0xffe080 }, 90, 22); MH.fx.ringShock(this, bx, by - T * 0.4, 0xffe9a8, 18, 520); } this.flashScreen(0xfff2d0, 0.2, 380); MH.bus.emit('flash', 'You feel a fleeting blessing settle over you.'); }
          else if (kind === 'dust') { this.dustPuff(bx, by - 2); }
        } catch (_) {}
      };
      const search = () => (MH.immersion && MH.immersion.runInfo ? MH.immersion.runInfo('search', 'You search') : MH.sendCommand('search'));
      const examine = () => MH.immersion && MH.immersion.propFlavor && MH.immersion.propFlavor(name);
      const acts = [];
      // primary verb per prop family
      if (['fountain', 'well'].includes(name)) acts.push({ label: '🜄 Drink', fn: () => { react('water'); MH.sendCommand('drink'); } });
      if (['brazier', 'campfire', 'candles', 'lantern', 'lamppost'].includes(name)) acts.push({ label: '😴 Warm yourself', fn: () => { react('warm'); MH.sendCommand('rest'); } });
      if (['altar', 'statue', 'runestone'].includes(name)) acts.push({ label: '🙏 Pray', fn: () => { react('holy'); MH.sendCommand('pray'); } });
      if (['stall'].includes(name)) acts.push({ label: '🛒 Browse wares', fn: () => (MH.immersion && MH.immersion.runInfo ? MH.immersion.runInfo('list', 'Wares for sale') : MH.sendCommand('list')) });
      if (['bookpile', 'banner'].includes(name)) acts.push({ label: '📖 Read', fn: () => examine() });
      if (['gravestone'].includes(name)) acts.push({ label: '🕯 Pay respects', fn: () => { react('holy'); examine(); } });
      if (['crate', 'barrel', 'urn'].includes(name)) acts.push({ label: '📦 Search inside', fn: () => { react('dust'); search(); } });
      if (['bones', 'rubble', 'web', 'mushrooms'].includes(name)) acts.push({ label: '🔍 Sift through', fn: () => { react('dust'); search(); } });
      // universal verbs
      acts.push({ label: '🔍 Search around it', fn: search });
      acts.push({ label: '👁 Examine', fn: examine });
      return acts;
    }

    scatterClutter(layout, th) {
      const { T, FLOOR, BLOCK } = TD();
      const CLUTTER = {
        field: ['flowers', 'rock', 'bush', 'reeds'], forest: ['mushrooms', 'flowers', 'rock', 'bush'],
        swamp: ['reeds', 'mushrooms', 'rock', 'bones'], hills: ['rock', 'bush', 'flowers'],
        desert: ['rock', 'bones', 'cactus'], mountain: ['rock', 'bones'],
        cave: ['rock', 'mushrooms', 'bones', 'crystal'], dungeon: ['rubble', 'bones', 'urn', 'web'],
        underground: ['rubble', 'crystal', 'bones'], inside: ['crate', 'barrel', 'urn', 'bookpile'],
        city: ['crate', 'barrel', 'urn'], default: ['rock', 'bush'],
      };
      const set = (CLUTTER[th] || CLUTTER.default).filter(n => this.textures.exists(`zt_prop_${n}`));
      const pScale = (MH.gfx && MH.gfx.particleScale != null) ? MH.gfx.particleScale : 1;
      const rng = MH.mulberry32((layout.vnum ^ 0x9e3a17) >>> 0);
      const grid = layout.grid, W = layout.W, H = layout.H;
      const cx = Math.floor(W / 2), cy = Math.floor(H / 2);
      const taken = new Set((layout.props || []).map(p => `${p.x},${p.y}`));
      if (set.length) {
        // lean on the prose-driven props instead: only a light sprinkle of
        // generic clutter, biased to the walls so the floor stays open
        const count = Math.round((2 + rng() * 3) * (0.5 + pScale * 0.5));
        let placed = 0, guard = 0;
        while (placed < count && guard++ < 240) {
          const x = 2 + ((rng() * (W - 4)) | 0), y = 2 + ((rng() * (H - 4)) | 0);
          if (grid[y * W + x] !== FLOOR) continue;
          if (Math.abs(x - cx) < 2 && Math.abs(y - cy) < 2) continue;   // keep centre/landmark clear
          if (taken.has(`${x},${y}`)) continue;
          const nearWall = grid[(y - 1) * W + x] === BLOCK || grid[(y + 1) * W + x] === BLOCK
            || grid[y * W + x - 1] === BLOCK || grid[y * W + x + 1] === BLOCK;
          if (!nearWall && rng() < 0.5) continue;   // bias clutter toward walls/edges
          taken.add(`${x},${y}`);
          const name = set[(rng() * set.length) | 0];
          const bx = x * T + T / 2, by = (y + 1) * T;
          this.tileLayer.add(this.add.image(bx, by - 1, 'px_shadow').setDepth(2.5).setAlpha(0.24).setScale(0.18));
          const cimg = this.add.image(bx, by, `zt_prop_${name}`).setOrigin(0.5, 1)
            .setDepth(3 + by / 1000).setScale((0.5 + rng() * 0.35) / MH.SMOOTH_SS);
          this.tileLayer.add(cimg);
          // small plants brush as you pass
          if (['flowers', 'reeds', 'bush', 'mushrooms'].includes(name)) this.registerReactive(cimg, 'sway', { tint: 0x8fbf6a });
          // searchable clutter (containers, remains) is clickable for loot/lore
          if (['crate', 'barrel', 'urn', 'bones', 'rubble'].includes(name)) {
            cimg.setInteractive({ useHandCursor: true });
            cimg.on('pointerdown', pointer => {
              if (pointer.rightButtonDown && pointer.rightButtonDown()) return;
              const acts = this.propActions(name, bx, by);
              if (MH.popover) MH.popover.show(pointer.event.clientX, pointer.event.clientY, (MH.PROP_FLAVOR && MH.PROP_FLAVOR[name] ? MH.PROP_FLAVOR[name][0] : name), acts);
            });
            cimg.on('pointerover', () => MH.bus.emit('flash', `${MH.PROP_FLAVOR && MH.PROP_FLAVOR[name] ? MH.PROP_FLAVOR[name][0] : name} — click to search`));
          }
          placed++;
        }
      }
      // discovery glints: faint sparkles inviting a search, rewarding wandering
      const spots = 1 + (rng() < 0.45 ? 1 : 0);
      for (let i = 0, g = 0; i < spots && g < 60; g++) {
        const x = 2 + ((rng() * (W - 4)) | 0), y = 2 + ((rng() * (H - 4)) | 0);
        if (grid[y * W + x] !== FLOOR || (Math.abs(x - cx) < 2 && Math.abs(y - cy) < 2) || taken.has(`${x},${y}`)) continue;
        taken.add(`${x},${y}`);
        i++;
        const gx = x * T + T / 2, gy = y * T + T / 2;
        const glint = this.add.image(gx, gy, 'fx_glow').setBlendMode(Phaser.BlendModes.ADD)
          .setAlpha(0.0).setScale(0.12).setTint(0xffe9a8).setDepth(4).setInteractive({ useHandCursor: true });
        this.tweens.add({ targets: glint, alpha: 0.5, scale: 0.2, duration: 700, yoyo: true, repeat: -1, repeatDelay: 2600, ease: 'sine.inOut' });
        glint.on('pointerdown', () => {
          this.spark(gx, gy, 0xffe9a8);
          if (MH.immersion && MH.immersion.runInfo) MH.immersion.runInfo('search', 'You search the spot');
          else MH.sendCommand('search');
        });
        glint.on('pointerover', () => MH.bus.emit('flash', 'Something glints here — click to search'));
        this.fxList && this.fxList.push(glint);
      }
    }

    // Phase 2: a per-room landmark centrepiece — a focal feature seeded by the
    // room so each place has identity and a destination worth crossing to. Built
    // from existing prop art, scaled up, with a glow, a draw-the-eye glint, and
    // an examine/interact so wandering the room is rewarded (exploration).
    placeLandmark(layout, th) {
      if (this._landmarkGlint) { this._landmarkGlint.remove(); this._landmarkGlint = null; }
      this._campfire = null;
      const { T, FLOOR } = TD();
      const CENTER = {
        field: ['statue', 'runestone', 'fountain', 'well', 'campfire', 'tree'],
        hills: ['runestone', 'rock', 'campfire', 'statue', 'tree'],
        forest: ['tree', 'deadtree', 'campfire', 'mushrooms', 'altar'],
        swamp: ['deadtree', 'altar', 'statue', 'mushrooms'],
        desert: ['pillar', 'statue', 'well', 'campfire', 'cactus'],
        mountain: ['crystal', 'campfire', 'rock', 'runestone'],
        cave: ['crystal', 'campfire', 'altar', 'rock', 'mushrooms'],
        dungeon: ['altar', 'statue', 'runestone', 'pillar'],
        underground: ['crystal', 'altar', 'runestone', 'pillar'],
        inside: ['statue', 'fountain', 'well', 'altar', 'anvil'],
        city: ['fountain', 'well', 'statue', 'runestone', 'stall'],
        default: ['statue', 'runestone', 'campfire', 'rock'],
      };
      const rng = MH.mulberry32((layout.vnum ^ 0x1a7f3) >>> 0);
      // only ~70% of rooms get a landmark, so they stay special
      if (rng() > 0.7) return;
      const cands = (CENTER[th] || CENTER.default).filter(n => this.textures.exists(`zt_prop_${n}`));
      if (!cands.length) return;
      const name = cands[(rng() * cands.length) | 0];
      // a clear floor cell near the centre (spiral out until one is free)
      const grid = layout.grid, W = layout.W, H = layout.H;
      const cx = Math.floor(W / 2), cy = Math.floor(H / 2);
      const free = (x, y) => x > 1 && y > 1 && x < W - 2 && y < H - 2 && grid[y * W + x] === FLOOR
        && !(layout.props || []).some(p => Math.abs(p.x - x) < 2 && Math.abs(p.y - y) < 2);
      let lx = cx, ly = cy, found = free(cx, cy);
      for (let r = 1; !found && r <= 5; r++) {
        for (let a = 0; a < 8 && !found; a++) {
          const tx = cx + Math.round(Math.cos(a / 8 * 6.28) * r), ty = cy + Math.round(Math.sin(a / 8 * 6.28) * r);
          if (free(tx, ty)) { lx = tx; ly = ty; found = true; }
        }
      }
      if (!found) return;
      const baseX = lx * T + T / 2, baseY = (ly + 1) * T;
      if (['campfire', 'brazier'].includes(name)) this._campfire = { x: baseX, y: baseY }; else this._campfire = null;
      const scale = 2.4 / MH.SMOOTH_SS;
      // shadow + glow ground and highlight it
      this.add.image(baseX, baseY - 1, 'px_shadow').setDepth(3 + baseY / 1000 - 0.01).setAlpha(0.42).setScale(0.85);
      const GLOWN = { fountain: 0x9fd9ff, well: 0x9fd9ff, crystal: 0xc792ff, statue: 0xffe9c0, runestone: 0xffd089, mushrooms: 0xb06ce0, deadtree: 0x9ab69a, tree: 0xaaffaa, campfire: 0xff9a4a, altar: 0xc8a0ff };
      const glow = this.add.image(baseX, baseY - T, 'fx_glow').setBlendMode(Phaser.BlendModes.ADD)
        .setAlpha(0.16).setScale(0.7).setTint(GLOWN[name] || 0xffe9a8).setDepth(35);
      this.tweens.add({ targets: glow, alpha: 0.28, scale: 0.85, duration: 1800, yoyo: true, repeat: -1, ease: 'sine.inOut' });
      this.fxList && this.fxList.push(glow);
      const img = this.add.image(baseX, baseY, `zt_prop_${name}`).setOrigin(0.5, 1).setScale(scale);
      this.addPropImage(img, baseY, name);
      // the centrepiece reacts to your presence too
      if (['fountain', 'well'].includes(name)) this.registerReactive(img, 'ripple');
      else if (['campfire', 'brazier'].includes(name)) this.registerReactive(img, 'flare', { glow, glowMax: 0.16, tint: GLOWN[name] || 0xff9a4a });
      else if (['tree', 'deadtree', 'mushrooms', 'cactus'].includes(name)) this.registerReactive(img, 'sway', { tint: GLOWN[name] || 0x8fbf6a });
      // a periodic glint to draw the eye and invite exploration
      this._landmarkGlint = this.time.addEvent({
        delay: 3200 + rng() * 2600, loop: true,
        callback: () => { if (img.active) this.spark(baseX, baseY - T * 1.4, GLOWN[name] || 0xffe9a8); },
      });
      // examine + interact: the room's point of interest (shared verb set)
      img.setInteractive({ useHandCursor: true });
      img.on('pointerdown', pointer => {
        if (pointer.rightButtonDown && pointer.rightButtonDown()) return;
        const acts = this.propActions(name, baseX, baseY);
        if (MH.popover && acts.length) MH.popover.show(pointer.event.clientX, pointer.event.clientY, (MH.PROP_FLAVOR && MH.PROP_FLAVOR[name] ? MH.PROP_FLAVOR[name][0] : name), acts);
      });
      img.on('pointerover', () => MH.bus.emit('flash', `${MH.PROP_FLAVOR && MH.PROP_FLAVOR[name] ? MH.PROP_FLAVOR[name][0] : name} — click to interact`));
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
      if (this.pxFar) this.pxFar.removeAll(true);
      if (this.pxNear) this.pxNear.removeAll(true);
      this.pxFar.setPosition(0, 0);
      this.pxNear.setPosition(0, 0);

      const gfx = MH.gfx || {};
      const pScale = gfx.particleScale != null ? gfx.particleScale : 1;

      // parallax planes: soft light clouds behind the actors (far, slow) and a
      // few large blurred motes in front (near, fast). Children animate locally;
      // the containers are slid by player offset in update() for the depth feel.
      if (gfx.parallax !== false) {
        for (let i = 0; i < 4; i++) {
          const fx = this.add.image(rng() * this.pxW, rng() * this.pxH, 'fx_glow')
            .setBlendMode(Phaser.BlendModes.ADD).setAlpha(0.03 + rng() * 0.03)
            .setScale(1.6 + rng() * 1.4).setTint(glowTint);
          this.tweens.add({ targets: fx, alpha: fx.alpha + 0.03, duration: 3000 + rng() * 2000, yoyo: true, repeat: -1, ease: 'sine.inOut' });
          this.pxFar.add(fx);
        }
        for (let i = 0; i < 2; i++) {
          const nx = this.add.image(rng() * this.pxW, rng() * this.pxH, 'fx_glow')
            .setBlendMode(Phaser.BlendModes.ADD).setAlpha(0.015 + rng() * 0.02)
            .setScale(1.8 + rng() * 1.2).setTint(glowTint);
          this.tweens.add({ targets: nx, x: nx.x + (rng() - 0.5) * 40, duration: 5000 + rng() * 3000, yoyo: true, repeat: -1, ease: 'sine.inOut' });
          this.pxNear.add(nx);
        }
      }

      // zone mood wash: a whisper of the theme's color over everything
      if (zt && zt.mood) {
        const wash = this.add.rectangle(0, 0, this.pxW, this.pxH, zt.mood, zt.moodA || 0.06)
          .setOrigin(0, 0).setDepth(33).setBlendMode(Phaser.BlendModes.OVERLAY);
        this.fxList.push(wash);
      }

      // soft pools of colored light
      const pools = gfx.lightPools != null ? gfx.lightPools : 2 + Math.floor(rng() * 2);
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
      // indoor window shafts: a couple of bright sun-beams with drifting dust
      const detailFx = !MH.gfx || MH.gfx.particleScale >= 0.5;
      if (['inside', 'city', 'dungeon'].includes(th)) {
        const beams = th === 'inside' ? 2 : 1;
        for (let i = 0; i < beams; i++) {
          const bx = (0.28 + 0.4 * i + rng() * 0.18) * this.pxW;
          const ray = this.add.image(bx, -8, 'fx_ray').setOrigin(0.5, 0).setBlendMode(Phaser.BlendModes.ADD)
            .setAlpha(0.06 + rng() * 0.04).setRotation(0.30 + rng() * 0.1).setScale(1.3, 1.7)
            .setTint(th === 'dungeon' ? 0xbcd0ff : 0xfff0d0).setDepth(36);
          this.tweens.add({ targets: ray, alpha: ray.alpha + 0.04, duration: 5000 + rng() * 2000, yoyo: true, repeat: -1, ease: 'sine.inOut' });
          this.fxList.push(ray);
          if (detailFx) {
            const dust = this.add.particles(bx, this.pxH * 0.3, 'px_white', {
              x: { min: -22, max: 22 }, y: { min: -40, max: this.pxH * 0.4 }, tint: 0xfff0d0,
              scale: { start: 0.13, end: 0 }, alpha: { start: 0, end: 0.5 }, speedY: { min: 4, max: 12 }, speedX: { min: -3, max: 3 },
              lifespan: 6000, frequency: 600, blendMode: 'ADD',
            }).setDepth(36);
            this.fxList.push(dust);
          }
        }
      }
      // forest canopy dapple: soft shifting light spots on the floor
      if (['forest', 'swamp'].includes(th)) {
        const spots = 3 + Math.floor(rng() * 3);
        for (let i = 0; i < spots; i++) {
          const dp = this.add.image(40 + rng() * (this.pxW - 80), 50 + rng() * (this.pxH - 100), 'fx_glow')
            .setBlendMode(Phaser.BlendModes.ADD).setAlpha(0.05 + rng() * 0.05).setScale(0.5 + rng() * 0.5)
            .setTint(0xeaffc0).setDepth(3.5);
          this.tweens.add({ targets: dp, alpha: dp.alpha + 0.05, x: dp.x + (rng() - 0.5) * 22, duration: 4000 + rng() * 3000, yoyo: true, repeat: -1, ease: 'sine.inOut' });
          this.fxList.push(dp);
        }
      }

      // themed ambient weather (zone themes), falling back to drifting motes
      const ambient = zt ? zt.ambient : 'motes';
      const soft = this.textures.exists('zt_px_soft') ? 'zt_px_soft' : 'px_white';
      const leaf = this.textures.exists('zt_px_leaf') ? 'zt_px_leaf' : 'px_white';
      const fullX = { min: 10, max: this.pxW - 10 };
      const addAmb = cfg => {
        // thin out ambient particles at lower graphics quality
        if (pScale < 1 && cfg.frequency) cfg = Object.assign({}, cfg, { frequency: cfg.frequency / pScale });
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
        if (this.lightSources) this.lightSources.push({ x, y, r: 64, seed: (x * 31 + y * 7) % 1000 });
      };
      if (layout.stairsUp) featureGlow(layout.stairsUp.x * T + T / 2, layout.stairsUp.y * T + T / 2, 0xffe9a8);
      if (layout.stairsDown) featureGlow(layout.stairsDown.x * T + T / 2, layout.stairsDown.y * T + T / 2, 0x8899ff, 0.4, 0.22);
      for (const p of layout.portals) featureGlow(p.x * T + T / 2, p.y * T + T / 2, 0xc080ff, 0.55, 0.35);

      // water caustics: dappled, slowly rippling light cast across the floor of
      // any watery room — the single most "alive" thing about real water
      if (gfx.caustics !== false && (['underwater', 'water_swim', 'water_noswim'].includes(th) || layout.swim)) {
        const caustic = th === 'underwater' ? 0xaef0ff : 0xbfe8ff;
        const count = th === 'underwater' ? 9 : 6;
        for (let i = 0; i < count; i++) {
          const cx = 40 + rng() * (this.pxW - 80);
          const cy = 40 + rng() * (this.pxH - 80);
          const g = this.add.image(cx, cy, 'px_light')
            .setBlendMode(Phaser.BlendModes.ADD)
            .setAlpha(0.05 + rng() * 0.06)
            .setScale(0.45 + rng() * 0.6)
            .setTint(caustic).setDepth(4);
          this.tweens.add({
            targets: g,
            x: cx + (rng() - 0.5) * 46, y: cy + (rng() - 0.5) * 34,
            scaleX: g.scaleX * (1.3 + rng() * 0.5), scaleY: g.scaleY * (0.65 + rng() * 0.3),
            alpha: g.alpha + 0.06,
            duration: 2400 + rng() * 2600, yoyo: true, repeat: -1, ease: 'sine.inOut',
          });
          this.fxList.push(g);
        }
      }
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
      const featureHint = (x, y, text, color) => {
        const t = this.add.text(x, y, text, {
          fontFamily: 'Trebuchet MS, Verdana, sans-serif', resolution: 3, fontSize: '7px', color,
        }).setOrigin(0.5, 1).setDepth(3).setAlpha(0.85);
        this.tileLayer.add(t);
      };
      if (layout.stairsUp) {
        addFeatureZone(layout.stairsUp.x, layout.stairsUp.y, 'up', 'td_stairs_up');
        signpost('up', layout.stairsUp.x * T + T / 2, (layout.stairsUp.y - 1) * T);
        if (!(layout.exits.up && layout.exits.up.to_zone)) {
          featureHint(layout.stairsUp.x * T + T / 2, layout.stairsUp.y * T - 2, '▲ up', '#ffe9a8');
        }
      }
      if (layout.stairsDown) {
        // in town, a down-exit is a sewer grate, not a stairwell
        const urban = ['midgaard', 'sewer'].includes(layout.zoneKey) || ['city', 'inside'].includes(th);
        const downTex = urban && this.textures.exists('zt_grate') ? 'zt_grate' : 'td_stairs_down';
        addFeatureZone(layout.stairsDown.x, layout.stairsDown.y, 'down', downTex);
        signpost('down', layout.stairsDown.x * T + T / 2, (layout.stairsDown.y - 1) * T);
        if (!(layout.exits.down && layout.exits.down.to_zone)) {
          featureHint(layout.stairsDown.x * T + T / 2, layout.stairsDown.y * T - 2, '▼ down', '#9fb8ff');
        }
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
      // the room-description card (top-center, first visit + 'L' to re-read)
      // is the clean home for prose now; the floating in-world text duplicated
      // it and cluttered the Aether view, so it's disabled.
      return;
      // eslint-disable-next-line no-unreachable
      if (!layout.description) return;
      const rng = MH.mulberry32(layout.vnum + 99);
      const frags = layout.description.replace(/\n/g, ' ').split(/(?<=[.!?])\s+/)
        .map(s => s.trim()).filter(s => s.length > 15 && s.length <= 60);
      Phaser.Utils.Array.Shuffle(frags);
      frags.slice(0, 2).forEach((frag, i) => {
        const tx = this.add.text(36 + rng() * (this.pxW - 260), 28 + i * 26, frag, {
          fontFamily: 'Georgia, serif', resolution: 3, fontSize: '8px', fontStyle: 'italic', color: '#fdf6e3',
        }).setAlpha(0.14).setDepth(4).setShadow(0, 1, '#000000', 2);
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
        if (!want.has(key)) {
          if (ent.leaving) continue;          // walking off under its own tween
          this.destroyEntity(ent);
          this.entities.delete(key);
        }
      }
      for (const [key, spec] of want) {
        const existing = this.entities.get(key);
        if (existing) { this.updateEntity(existing, spec.data); continue; }
        this.entities.set(key, this.spawnEntity(key, spec));
      }
    }

    spawnEntity(key, spec) {
      const slots = this.layout.spawnSlots;
      let slot = slots[(MH.hashStr(key) + spec.idx) % slots.length];
      const ent = { key, kind: spec.kind, data: spec.data };

      if (spec.kind === 'item') {
        const isCorpse = /corpse/i.test(spec.data.name || '');
        let texKey;
        if (isCorpse) texKey = 'sm_corpse';
        else if (MH.itemIcons) texKey = MH.itemIcons.textureKey(this, spec.data);
        else texKey = this.safeTex(MH.smoothSprites.itemKey(spec.data.type), 'fx_glow');
        ent.sprite = this.add.image(slot.x, slot.y, texKey).setDepth(5)
          .setScale((isCorpse ? 0.9 : 0.75) / MH.SMOOTH_SS);
        if (!isCorpse) {
          this.tweens.add({ targets: ent.sprite, y: slot.y - 3, duration: 900, yoyo: true, repeat: -1, ease: 'sine.inOut' });
          const rar = spec.data.rarity;
          if (rar === 'legendary' || rar === 'epic' || spec.data.set_id) {
            const tint = spec.data.set_id ? 0x4ad0c0 : (rar === 'legendary' ? 0xffa838 : 0xb06ce0);
            const g = this.add.image(slot.x, slot.y, 'fx_glow').setBlendMode(Phaser.BlendModes.ADD)
              .setAlpha(0.3).setScale(0.3).setTint(tint).setDepth(4);
            this.tweens.add({ targets: g, alpha: 0.48, duration: 800, yoyo: true, repeat: -1, ease: 'sine.inOut' });
            ent.smoke = g;   // cleaned up with the entity
          }
        }
        ent.sprite.setInteractive({ useHandCursor: true });
        ent.sprite.on('pointerdown', pointer => {
          const rb = pointer.rightButtonDown && pointer.rightButtonDown();
          if (isCorpse && !rb) MH.bus.emit('loot.corpse');
          else if (isCorpse && rb && MH.popover) MH.popover.show(pointer.event.clientX, pointer.event.clientY, spec.data.name, [
            { label: '✋ Loot all', fn: () => MH.bus.emit('loot.corpse') },
            { label: '👁 Look', fn: () => MH.immersion.lookAt('corpse') },
            { label: '🔪 Butcher', fn: () => MH.sendCommand('butcher corpse') },
          ]);
          else if (MH.objectActions) MH.objectActions(spec.data, pointer.event.clientX, pointer.event.clientY);
          else MH.sendCommand(`get ${MH.mobKeyword(spec.data.name)}`);
        });
        if (isCorpse) {
          ent.label = this.add.text(slot.x, slot.y - 12, this.shortName(spec.data.name), {
            fontFamily: 'Trebuchet MS, Verdana, sans-serif', resolution: 3, fontSize: '6px', color: '#9a8f80',
          }).setOrigin(0.5, 1).setDepth(5).setAlpha(0.8);
        }
        return ent;
      }

      let texWanted;
      if (spec.kind === 'player') {
        texWanted = MH.tdSprites.playerKey(spec.data.char_class);
      } else if (spec.data.trainer) {
        // guildmasters wear their class's face, crowned in gold. Most are
        // named just 'guildmaster', so the guild HALL names the class.
        const room = (MH.state.currentRoom && MH.state.currentRoom.name) || '';
        const n = `${spec.data.name || ''} ${room}`.toLowerCase();
        const cls = /paladin|holy order/.test(n) ? 'paladin'
          : /necro/.test(n) ? 'necromancer'
          : /sword|warrior|fight|armory|barrack/.test(n) ? 'warrior'
          : /mage|magic|wizard|arcan/.test(n) ? 'mage'
          : /assassin/.test(n) ? 'assassin'
          : /thie|rogue/.test(n) ? 'thief'
          : /ranger|hunt/.test(n) ? 'ranger'
          : /cleric|priest|temple|sanctum/.test(n) ? 'cleric'
          : /bard|song|minstrel/.test(n) ? 'bard' : null;
        texWanted = cls ? `td_gm_${cls}` : 'td_mob_noble';   // crowned dignitary by default
      } else {
        texWanted = MH.tdSprites.mobKey(spec.data.name);
      }
      const tex = this.safeTex(texWanted, 'td_mob_citizen');
      // a fresh arrival enters from the doorway it actually used
      const arr = spec.kind === 'mob' && this.pendingArrivals && this.pendingArrivals[spec.data.name];
      if (arr && Date.now() - arr.at < 4000) {
        delete this.pendingArrivals[spec.data.name];
        const gp = this.gapPoint(arr.dir);
        const destX = slot.x, destY = slot.y;
        slot = { x: gp.x, y: gp.y };
        this.time.delayedCall(30, () => {
          const ent2 = this.entities.get(key);
          if (ent2 && ent2.sprite) {
            this.tweens.add({
              targets: ent2.sprite, x: destX, y: destY, duration: 900, ease: 'sine.out',
              onUpdate: () => { if (ent2.label) { ent2.label.x = ent2.sprite.x; ent2.label.y = ent2.sprite.y - 18; } },
              onComplete: () => { ent2.homeX = destX; ent2.homeY = destY; },
            });
            const cue = this.add.text(gp.x, gp.y - 20, `from ${arr.dir}`, {
              fontFamily: 'Trebuchet MS, Verdana, sans-serif', resolution: 3, fontSize: '8px',
              color: '#c8ccd8', backgroundColor: '#10131ea8', padding: { x: 3, y: 1 },
            }).setOrigin(0.5, 1).setDepth(40);
            this.tweens.add({ targets: cue, y: cue.y - 10, alpha: 0, duration: 1600, onComplete: () => cue.destroy() });
          }
        });
      }
      ent.sprite = this.add.sprite(slot.x, slot.y, tex, 'd0').setDepth(8);
      ent.sprite.setScale((spec.data.boss ? 1.5 : 1) / MH.SMOOTH_SS);
      if (spec.kind !== 'item') {
        ent.shadow = this.add.image(slot.x, slot.y + 9, 'px_shadow')
          .setDepth(5).setAlpha(0.34).setScale((spec.data.boss ? 0.5 : 0.32));
        // matching rim-light so mobs and NPCs pop off the floor too
        ent.rim = this.add.sprite(slot.x, slot.y, tex, 'd0')
          .setScale(ent.sprite.scaleX * 1.08).setDepth(7.9)
          .setBlendMode(Phaser.BlendModes.ADD).setAlpha(spec.data.boss ? 0.34 : 0.26).setTint(this.rimTint);
      }
      ent.sprite.play(`${tex}_walkd`);
      ent.sprite.anims.pause();
      // mobs described as asleep/at rest spawn in that pose
      if (spec.kind === 'mob' && (spec.data.pose === 'sleeping' || spec.data.pose === 'resting') && !spec.data.fighting) {
        ent.sprite.anims.stop();
        ent.sprite.setFrame(spec.data.pose === 'sleeping' ? 'sleep' : 'rest');
      }
      ent.homeX = slot.x; ent.homeY = slot.y;

      const labelColor = spec.kind === 'player' ? '#6ca8e0' : (spec.data.hostile ? '#e06c6c' : (spec.data.shopkeeper ? '#e8c168' : '#c8ccd8'));
      ent.label = this.add.text(slot.x, slot.y - 18, this.shortName(spec.data.name), {
        fontFamily: 'Trebuchet MS, Verdana, sans-serif', resolution: 3, fontSize: '7px', color: labelColor,
      }).setOrigin(0.5, 1).setDepth(9);
      ent.hpbar = this.add.graphics().setDepth(9);
      this.drawHpBar(ent);

      ent.sprite.setInteractive({ useHandCursor: true });
      ent.sprite.on('pointerdown', pointer => {
        // right-click anyone: the full verb menu
        if (pointer.rightButtonDown && pointer.rightButtonDown()) {
          if (MH.contextMenu) MH.contextMenu(spec.kind === 'player' ? 'player' : 'mob', ent.data, pointer.event.clientX, pointer.event.clientY);
          return;
        }
        if (spec.kind !== 'mob') return;
        // left-click always targets, so spells/abilities aim at who you clicked
        this.targetEntity(ent);
        if (spec.data.shopkeeper) MH.bus.emit('shop.open', spec.data);
        else if (spec.data.trainer) MH.bus.emit('training.open', spec.data);
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
      // New art for every actor: explicit human role -> LPC paperdoll; a creature
      // keyword -> real DCSS art; otherwise (proper-named townsfolk) -> a generic
      // LPC person. ent.sprite stays the hidden logic/physics anchor.
      this.attachArt(ent, spec);
      return ent;
    }
    attachArt(ent, spec) {
      const lpcOK = MH.lpc && MH.lpc.isReady(), dcssOK = MH.dcss && MH.dcss.isReady();
      if (spec.kind === 'player') { if (lpcOK) this.attachDollAs(ent, spec, spec.data.char_class || 'warrior'); return; }
      const name = spec.data.name;
      const humanRole = lpcOK ? MH.lpc.humanoidClass(name, spec.data.char_class) : null;
      const creature = dcssOK ? MH.dcss.resolve(name) : null;
      if (humanRole) this.attachDollAs(ent, spec, humanRole);
      else if (creature) this.attachCreatureArt(ent, spec, creature);
      else if (lpcOK && !spec.data.boss) this.attachDollAs(ent, spec, 'bard');   // generic person
      // else: keep the procedural sprite (subsystems not ready / odd boss)
    }
    // build an LPC doll for an entity with an explicit class loadout
    attachDollAs(ent, spec, cls) {
      if (!MH.lpc || !MH.lpc.isReady() || ent.doll || !cls) return;
      const dscale = Math.max(0.32, (ent.sprite.displayHeight / 64) * 1.0);   // ~match sprite height
      // the player keeps its real identity; NPCs vary by name-hash so towns
      // aren't full of identical twins (mixed sexes + hairstyles)
      const seed = MH.hashStr(spec.data.name || '');
      const sex = spec.kind === 'player' ? (spec.data.sex || 'male') : (seed % 2 ? 'female' : 'male');
      ent.doll = MH.lpc.makeDoll(this, { char_class: cls, sex, equipment: spec.data.equipment || {}, seed: spec.kind === 'player' ? null : seed }, dscale,
        () => this.tintCharacters());   // apply day/night tint once layers exist
      ent.doll.container.setDepth(ent.sprite.depth || 8);
      ent.sprite.setAlpha(0);
      if (ent.rim) ent.rim.setVisible(false);
    }
    // real creature art (DCSS) for monsters; a single 32px image overlaid on
    // the hidden procedural sprite, with a gentle idle bob
    attachCreatureArt(ent, spec, path) {
      if (!MH.dcss || !MH.dcss.isReady() || ent.art || spec.kind === 'player') return;
      path = path || MH.dcss.resolve(spec.data.name);
      if (!path) return;   // nothing matched -> keep the procedural sprite
      const s = ent.sprite, big = spec.data.boss;
      s.setAlpha(0);                       // hide procedural now; no pre-load flash
      if (ent.rim) ent.rim.setVisible(false);
      MH.dcss.ensure(this, path, key => {
        if (!s || !s.active) return;
        if (!key) { s.setAlpha(1); if (ent.rim) ent.rim.setVisible(true); return; }   // load failed -> restore
        const img = this.add.image(s.x, s.y - 6, key).setOrigin(0.5, 0.9);
        // DCSS frames are 32px; scale up to ~1.4 tiles (bosses larger), crisp
        const sc = (TD().T * (big ? 2.3 : 1.7)) / 32;
        img.setScale(sc).setDepth(s.depth || 8);
        img.texture.setFilter(Phaser.Textures.FilterMode.NEAREST);
        img.setTint(this._charTint || 0xffffff);   // sit in the day/night scene
        ent.art = img;
        ent.artPhase = (MH.hashStr(spec.data.name) % 628) / 100;   // idle-bob phase
        s.setAlpha(0);
        if (ent.rim) ent.rim.setVisible(false);
      });
    }

    npcChatter() {
      if (!this.layout || this.dead || !MH.CHATTER || Math.random() > 0.4) return;
      const talkers = [...this.entities.values()].filter(e =>
        e.kind === 'mob' && e.sprite && e.sprite.active && !e.data.hostile && !e.data.fighting && !e.bubble);
      if (!talkers.length) return;
      const ent = talkers[Math.floor(Math.random() * talkers.length)];
      const arch = (this.safeTex(MH.tdSprites.mobKey(ent.data.name), 'td_mob_citizen') || '').replace('td_mob_', '');
      const lines = ent.data.shopkeeper ? MH.CHATTER.shopkeeper
        : MH.CHATTER[arch] || MH.CHATTER.citizen;
      const text = lines[Math.floor(Math.random() * lines.length)];
      const bubble = this.add.text(ent.sprite.x, ent.sprite.y - 22, text, {
        fontFamily: 'Georgia, serif', resolution: 3, fontSize: '7px', fontStyle: 'italic',
        color: '#e8e4d8', backgroundColor: '#10131ec8', padding: { x: 4, y: 2 },
        wordWrap: { width: 110 },
      }).setOrigin(0.5, 1).setDepth(30).setAlpha(0);
      ent.bubble = bubble;
      this.tweens.add({ targets: bubble, alpha: 1, y: bubble.y - 3, duration: 280 });
      this.time.delayedCall(2600 + text.length * 35, () => {
        this.tweens.add({
          targets: bubble, alpha: 0, duration: 320,
          onComplete: () => { bubble.destroy(); if (ent.bubble === bubble) ent.bubble = null; },
        });
      });
    }

    updateQuestMark(ent) {
      const q = ent.data && ent.data.quest;
      const d = ent.data || {};
      const svc = ent.kind === 'mob' ? (d.shopkeeper ? '🪙' : d.trainer ? '📖' : null) : null;
      if (svc && !ent.serviceMark) {
        ent.serviceMark = this.add.text(ent.sprite.x + 9, ent.sprite.y - 24, svc, {
          fontSize: '9px', resolution: 3,
        }).setOrigin(0.5).setDepth(9);
        this.tweens.add({ targets: ent.serviceMark, y: ent.serviceMark.y - 3, duration: 900, yoyo: true, repeat: -1, ease: 'sine.inOut' });
      } else if (!svc && ent.serviceMark) {
        ent.serviceMark.destroy();
        ent.serviceMark = null;
      }
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
      if (data.fighting && !ent.engageRing) {
        ent.engageRing = this.add.graphics().setDepth(9.5);
      } else if (!data.fighting && ent.engageRing) {
        ent.engageRing.destroy();
        ent.engageRing = null;
      }
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
      // if the thing we're targeting is being removed (it died, fled, or left),
      // drop the target so the frame doesn't linger with stale HP and casts
      // don't keep firing at a corpse
      if (this.target === ent) { this.target = null; MH.bus.emit('target.clear'); }
      if (ent.patrol) ent.patrol.stop();
      if (ent.breath) ent.breath.stop();
      if (ent.wanderTween) ent.wanderTween.stop();
      if (ent.smoke) ent.smoke.destroy();
      if (ent.doll) { ent.doll.destroy(); ent.doll = null; }
      if (ent.artBob) { ent.artBob.stop(); ent.artBob = null; }
      if (ent.art) { ent.art.destroy(); ent.art = null; }
      ['sprite', 'label', 'hpbar', 'fightMark', 'questMark', 'bubble', 'engageRing', 'serviceMark', 'shadow', 'rim'].forEach(k => { if (ent[k]) ent[k].destroy(); });
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
      this._atkFrame = this.time.now;   // doll swing signal
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
      // per-ability signature registry is authoritative — every named spell/
      // skill resolves here first, so each gets its own unique animation
      if (MH.abilityFx) {
        const sig = MH.abilityFx.match(text);
        if (sig) return { type: 'signature', text, range: sig.range || 'ranged', color: sig.color || 0xffffff };
      }
      for (const [re, fx] of TopRoomScene.ABILITY_FX) {
        if (re.test(text)) return { ...fx, text };
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
      // 1) per-ability signature (unique animation per spell/skill)
      if (fx.text && MH.abilityFx && MH.abilityFx.run(this, fx.text, this.player, tx, ty)) return;
      // 2) flagship cinematic, else school-flavored cast-up + impact under
      //    the classic type visuals
      const SFX = MH.schoolFx;
      if (SFX && fx.text) {
        if (SFX.flagship(this, fx.text, this.player, tx, ty)) return;
        const school = SFX.classify(fx.text);
        SFX.castUp(this, this.player, school);
        SFX.impact(this, tx, ty, school, SFX.tierOf(fx.text));
      }
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
              this.camShake(110, 0.005);
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
          this.camShake(70, 0.003);
          break;
        }
        case 'nova': {
          const ring = this.add.circle(px, py, 6).setStrokeStyle(3, fx.color, 0.9).setDepth(60);
          this.tweens.add({ targets: ring, radius: 52, alpha: 0, duration: 480, ease: 'cubic.out', onComplete: () => ring.destroy() });
          const ring2 = this.add.circle(px, py, 4).setStrokeStyle(1.5, 0xffffff, 0.7).setDepth(60);
          this.tweens.add({ targets: ring2, radius: 38, alpha: 0, duration: 420, delay: 80, ease: 'cubic.out', onComplete: () => ring2.destroy() });
          this.camShake(90, 0.004);
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
      if (MH.sfx) MH.sfx.swing();
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
      if (MH.sfx) MH.sfx.heal();
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
    // the visible body for an entity / the player (LPC doll or DCSS art, else
    // the procedural sprite) — combat juice must play on whatever is on screen
    entVisual(ent) { return (ent && ent.doll && ent.doll.container) || (ent && ent.art) || (ent && ent.sprite); }
    playerVisual() { return (this.playerDoll && this.playerDoll.container) || this.player; }
    // white/colored hit flash that also works on a layered doll Container;
    // restores to the current day/night character tint (not plain white)
    flashFill(obj, color, ms) {
      if (!obj) return;
      const back = this._charTint || 0xffffff;
      const apply = o => { if (o && o.setTintFill) { o.setTintFill(color); this.time.delayedCall(ms || 80, () => { if (o.active) o.setTint(back); }); } };
      if (obj.setTintFill && !obj.list) apply(obj);
      else if (obj.list) obj.list.forEach(apply);   // Container: tint each layer
      else apply(obj);
    }
    // multiply dolls + DCSS art by a readable per-phase tint so characters sit
    // in the day/night scene instead of looking bright/pasted-on
    tintCharacters() {
      const t = this._charTint || 0xffffff;
      const tintOne = o => { if (!o) return; if (o.list) o.list.forEach(c => c.setTint && c.setTint(t)); else if (o.setTint) o.setTint(t); };
      if (this.playerDoll) tintOne(this.playerDoll.container);
      for (const ent of this.entities.values()) {
        if (ent.doll) tintOne(ent.doll.container);
        else if (ent.art) ent.art.setTint(t);
      }
    }
    fxHit(e) {
      const ent = this.findEntityByText(e.target) || this.target;
      if (!ent || !ent.sprite) return;
      const vis = this.entVisual(ent);
      this.flashFill(vis, 0xffffff);
      const ang = Math.atan2(ent.sprite.y - this.player.y, ent.sprite.x - this.player.x);
      const kb = e.dmg != null ? Math.min(12, 4 + e.dmg * 0.25) : 5;
      // knockback drives the hidden anchor; the visible art follows it each frame
      this.tweens.add({ targets: ent.sprite, x: ent.sprite.x + Math.cos(ang) * kb, y: ent.sprite.y + Math.sin(ang) * kb, duration: 70, yoyo: true });
      this.squash(vis);
      this.impactLines(ent.sprite.x, ent.sprite.y - 6);
      if (e.dmg != null && e.dmg >= 8) this.freezeFrame(e.dmg >= 25 ? 95 : 60);
      if (e.dmg != null && e.dmg >= 5) this.bloodSplat(ent.sprite.x, ent.sprite.y, e.dmg >= 20);
      this.afterimage(this.player);
      // class ability in flight? play its signature effect. otherwise steel.
      // prefer the precise ability just used (clean key) over the combat line
      const fx = (this.lastAbility && Date.now() - this.lastAbility.ts < 4000 ? this.abilityFxFor(this.lastAbility.name) : null)
        || this.abilityFxFor(e.line || '');
      if (fx) this.playAbilityFx(fx, ent.sprite);
      else this.slashFx(ent.sprite.x, ent.sprite.y, this.player.x >= ent.sprite.x ? ent.sprite.x - 10 : ent.sprite.x + 10);
      // the connecting thud — louder the harder it lands (ability stings carry their own audio)
      if (MH.sfx && e.dmg != null) MH.sfx.impact(e.dmg >= 25 ? 2.5 : e.dmg >= 10 ? 1.5 : 1);
      this.spark(ent.sprite.x, ent.sprite.y - 6, (fx && fx.color) || 0xffe080);
      const st = this.dmgStyle(e.dmg);
      if (st.shake) this.camShake(90, st.shake);
      if (e.dmg != null && e.dmg >= 25) { this.zoomPunch(); this.flashScreen(0xfff2d0, 0.28, 160); this.lensKick(); }
      this.damageNumber(ent.sprite.x, ent.sprite.y - 16, e.dmg != null ? String(e.dmg) : 'hit', st.color, st.size);
    }
    fxMiss(e) {
      const ent = this.findEntityByText(e.target) || this.target;
      if (ent && ent.sprite) this.damageNumber(ent.sprite.x, ent.sprite.y - 16, 'miss', '#7a8094', 8);
    }
    fxTaken(e) {
      const pv = this.playerVisual();
      this.flashFill(pv, 0xff6060, 90);
      const st = this.dmgStyle(e && e.dmg);
      this.camShake(80, Math.max(0.004, st.shake));
      this.dmgPulse(e && e.dmg);
      if (MH.sfx) MH.sfx.hurt(e && e.dmg >= 20 ? 2 : 1);
      this.squash(pv);
      this.impactLines(this.player.x, this.player.y - 6, 0xff8080);
      if (e && e.dmg != null && e.dmg >= 6) {
        this.freezeFrame(e.dmg >= 20 ? 90 : 55);
        this.bloodSplat(this.player.x, this.player.y, e.dmg >= 15);
        if (e.dmg >= 20) this.lensKick();
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
    // is jarring motion allowed? (false when the player chose reduced motion)
    motionOk() { return !MH.gfx || MH.gfx.motion; }
    // gentle camera shake that respects the reduced-motion setting
    camShake(dur, intensity) {
      if (!this.motionOk()) return;
      this.cameras.main.shake(dur, intensity);
    }
    freezeFrame(ms = 70) {
      if (!this.motionOk()) return;
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
    // slow-motion beat: ramp time down then back, for the big cinematic moments
    slowMo(ms = 300, scale = 0.35) {
      if (!this.motionOk()) return;
      this.tweens.timeScale = scale;
      this.anims.globalTimeScale = scale;
      this.physics.world.timeScale = 1 / scale;
      if (this._slowTimer) clearTimeout(this._slowTimer);
      this._slowTimer = setTimeout(() => {
        this.tweens.timeScale = 1;
        this.anims.globalTimeScale = 1;
        this.physics.world.timeScale = 1;
        this._slowTimer = null;
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
      if (!this.motionOk()) return;
      const cam = this.cameras.main;
      const base = cam.zoom;
      this.tweens.add({ targets: cam, zoom: base * 1.035, duration: 70, yoyo: true, ease: 'cubic.out' });
    }
    // red screen-edge pulse when you take a hit — scales with the damage
    // (kept even on reduced motion, but softer, since it's informative)
    dmgPulse(dmg) {
      if (!this.dmgVignette) return;
      const cap = this.motionOk() ? 0.6 : 0.28;
      const a = Phaser.Math.Clamp(0.22 + (dmg || 0) * 0.012, 0.18, cap);
      this.tweens.killTweensOf(this.dmgVignette);
      this.dmgVignette.setTint(0xe02020).setAlpha(a);
      this.tweens.add({ targets: this.dmgVignette, alpha: 0, duration: 420, ease: 'cubic.out' });
    }
    // a brief full-screen wash (white crits, blue-white lightning)
    flashScreen(color = 0xffffff, alpha = 0.5, dur = 220) {
      if (!this.screenFlash) return;
      if (!this.motionOk()) alpha = Math.min(alpha, 0.12);   // calm the flash, don't kill the cue
      this.tweens.killTweensOf(this.screenFlash);
      this.screenFlash.setFillStyle(color, alpha);
      this.screenFlash.fillAlpha = alpha;
      this.tweens.add({ targets: this.screenFlash, fillAlpha: 0, duration: dur, ease: 'cubic.out' });
    }
    // lens "kick" on a heavy blow: a quick barrel-distortion punch (WebGL only)
    lensKick() {
      if (!this.motionOk()) return;
      const cam = this.cameras.main;
      if (!cam.postFX || !cam.postFX.addBarrel) return;
      if (this._barrelBusy) return;
      this._barrelBusy = true;
      let barrel;
      try { barrel = cam.postFX.addBarrel(1.18); } catch (_) { this._barrelBusy = false; return; }
      this.tweens.add({
        targets: barrel, amount: 1.0, duration: 180, ease: 'cubic.out',
        onComplete: () => { try { cam.postFX.remove(barrel); } catch (_) {} this._barrelBusy = false; },
      });
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
    // set the current target (shared by Tab-cycle and click-to-target)
    targetEntity(ent) {
      if (!ent || !ent.sprite) return;
      this.target = ent;
      MH.bus.emit('target.set', ent.data);
      this.setFacing(ent.sprite.x - this.player.x, ent.sprite.y - this.player.y);
      const ring = this.add.circle(ent.sprite.x, ent.sprite.y - 6, 16).setStrokeStyle(2, 0xe8c168, 0.9).setDepth(61);
      this.tweens.add({ targets: ring, radius: 8, alpha: 0, duration: 360, ease: 'cubic.in', onComplete: () => ring.destroy() });
    }
    cycleTarget() {
      const mobs = [...this.entities.values()].filter(e => e.kind === 'mob' && !e.data.shopkeeper && e.sprite)
        .sort((a, b) => Phaser.Math.Distance.Between(this.player.x, this.player.y, a.sprite.x, a.sprite.y)
                      - Phaser.Math.Distance.Between(this.player.x, this.player.y, b.sprite.x, b.sprite.y));
      if (!mobs.length) return;
      const idx = this.target ? mobs.findIndex(m => m.key === this.target.key) : -1;
      this.targetEntity(mobs[(idx + 1) % mobs.length]);
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
        if (MH.sfx) MH.sfx.impact(2.5);
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
      // a beat of slow-mo + a low death knell, the world greys out, then fades
      this.slowMo(700, 0.25);
      try {
        if (MH.fx && MH.fx.tone) {
          MH.fx.tone({ f: 200, f2: 48, type: 'sawtooth', dur: 1.0, vol: 0.07 });
          MH.fx.tone({ f: 120, f2: 36, type: 'sine', dur: 1.4, vol: 0.05, delay: 0.12 });
        }
      } catch (_) {}
      if (this.gradeFx && this.gradeFx.reset) { this.gradeFx.reset(); this.gradeFx.grayscale(0.85, true); }
      this.cameras.main.fade(1600, 0, 0, 0, false, (_c, t) => {
        if (t === 1) {
          this.time.delayedCall(700, () => {
            this._gradeKey = null;   // let the grade re-apply on respawn
            MH.refreshState();
            this.cameras.main.fadeIn(700);
            this.dead = false;
          });
        }
      });
      MH.bus.emit('flash', 'You have died. The realm reclaims you…');
    }
    fxLevelUp() {
      const x = this.player.x, y = this.player.y;
      const PAL = MH.fx && MH.fx.PAL;
      // a pillar of golden light, expanding rings, a chime, and a beat of slow-mo
      try {
        if (MH.fx && PAL) {
          MH.fx.pillar(this, x, y, PAL.holy, 130, 30);
          MH.fx.ringShock(this, x, y - 4, PAL.holy.b, 30, 520);
          this.time.delayedCall(150, () => MH.fx.ringShock(this, x, y - 4, PAL.holy.a, 22, 620));
          if (MH.fx.SOUNDS && MH.fx.SOUNDS.holy) MH.fx.SOUNDS.holy(3);
        }
      } catch (_) {}
      const emitter = this.add.particles(x, y - 6, 'px_star', {
        speed: { min: 40, max: 130 }, lifespan: 1100, quantity: 28, scale: { start: 1.2, end: 0 },
        tint: [0xffe9a8, 0xfff4d0, 0xffffff], emitting: false, gravityY: -30,
      }).setDepth(61);
      emitter.explode(28);
      this.time.delayedCall(1500, () => emitter.destroy());
      // "LEVEL UP!" banner rises over the hero
      const txt = this.add.text(x, y - 30, 'LEVEL UP!', {
        fontFamily: 'Georgia, serif', resolution: 3, fontSize: '16px', color: '#ffe9a8',
        stroke: '#3a2400', strokeThickness: 4, fontStyle: 'bold',
      }).setOrigin(0.5).setDepth(63).setScale(0.4).setAlpha(0);
      this.tweens.add({ targets: txt, scale: 1, alpha: 1, y: y - 46, duration: 320, ease: 'back.out' });
      this.tweens.add({ targets: txt, alpha: 0, y: y - 64, delay: 1100, duration: 520, onComplete: () => txt.destroy() });
      this.cameras.main.flash(180, 255, 240, 190);
      this.slowMo(240, 0.4);
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
      const door = this.layout && this.layout.exits[pm.dir] && this.layout.exits[pm.dir].door;
      if (door && /closed/i.test(e.line)) {
        // a closed door we can open: do it, don't treat as a hard block
        MH.sendCommand(`open ${door.name} ${pm.dir}`);
      } else {
        // a real refusal (class/level lock, exhaustion, no way): remember it
        // so we stop ramming the wall and re-spamming the command. The flash
        // already told the player why; they can pick another direction.
        this._blockedDir = pm.dir;
        this._blockedUntil = Date.now() + 3500;
      }
      // step back toward the room center so we're off the gap mouth
      const cx = this.pxW / 2, cy = this.pxH / 2;
      const ang = Math.atan2(cy - this.player.y, cx - this.player.x);
      this.player.x += Math.cos(ang) * 18;
      this.player.y += Math.sin(ang) * 18;
    }

    // draw a mob's head-and-shoulders into a DOM canvas (duel card)
    mobPortrait(canvas, name) {
      try {
        const ent = [...this.entities.values()].find(e2 =>
          e2.kind === 'mob' && e2.data && e2.data.name === name && e2.sprite);
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        let tex = ent && ent.sprite ? ent.sprite.texture : null;
        if (!tex && MH.mobKeyFor) tex = null;
        if (!tex) {
          // no live entity (different room, summoned test): classify by name
          const key = MH.smoothSprites && MH.smoothSprites.mobKey ? MH.smoothSprites.mobKey(name)
            : `td_mob_${(MH.mobArchetype ? MH.mobArchetype(name).key : 'citizen')}`;
          if (this.textures.exists(key)) tex = this.textures.get(key);
        }
        if (!tex) return false;
        const f = tex.get('d0');
        ctx.imageSmoothingEnabled = false;
        const sz = Math.min(canvas.width, canvas.height) * 1.5;
        ctx.drawImage(tex.getSourceImage(), f.cutX, f.cutY + f.cutHeight * 0.06, f.cutWidth, f.cutHeight * 0.62,
          (canvas.width - sz) / 2, 2, sz, sz * 0.8);
        return true;
      } catch (_) { return false; }
    }

    // a patrolling NPC walks OFF toward its exit (with a direction cue)
    // instead of blinking out - and walks IN from where it came
    gapPoint(dir) {
      const { T } = TD();
      const midX = Math.floor(this.layout.W / 2) * T + T / 2;
      const midY = Math.floor(this.layout.H / 2) * T + T / 2;
      return {
        north: { x: midX, y: T }, south: { x: midX, y: this.pxH - T },
        west: { x: T, y: midY }, east: { x: this.pxW - T, y: midY },
        up: this.layout.stairsUp ? { x: this.layout.stairsUp.x * T, y: this.layout.stairsUp.y * T } : { x: midX, y: midY },
        down: this.layout.stairsDown ? { x: this.layout.stairsDown.x * T, y: this.layout.stairsDown.y * T } : { x: midX, y: midY },
      }[dir] || { x: midX, y: midY };
    }

    onMobMove(e) {
      if (!this.layout || e.vnum !== this.layout.vnum || !e.name) return;
      if (e.action === 'leave') {
        const ent = [...this.entities.values()].find(en =>
          en.kind === 'mob' && en.data && en.data.name === e.name && en.sprite && !en.leaving);
        if (!ent) return;
        ent.leaving = true;
        const gp = this.gapPoint(e.dir);
        const cue = this.add.text(ent.sprite.x, ent.sprite.y - 24, `→ ${e.dir}`, {
          fontFamily: 'Trebuchet MS, Verdana, sans-serif', resolution: 3, fontSize: '8px',
          color: '#c8ccd8', backgroundColor: '#10131ea8', padding: { x: 3, y: 1 },
        }).setOrigin(0.5, 1).setDepth(40);
        this.tweens.add({ targets: cue, y: cue.y - 10, alpha: 0, duration: 1600, onComplete: () => cue.destroy() });
        this.tweens.add({
          targets: ent.sprite, x: gp.x, y: gp.y, alpha: 0.1,
          duration: 850, ease: 'sine.in',
          onUpdate: () => { if (ent.label) { ent.label.x = ent.sprite.x; ent.label.y = ent.sprite.y - 18; } },
          onComplete: () => { const key = ent.key; this.destroyEntity(ent); this.entities.delete(key); },
        });
      } else if (e.action === 'arrive') {
        // remembered until the roster payload (sent right behind this
        // event) actually spawns the mob
        this.pendingArrivals[e.name] = { dir: e.dir, at: Date.now() };
      }
    }

    targetByName(name) {
      const ent = [...this.entities.values()].find(e2 =>
        e2.kind === 'mob' && e2.data && e2.data.name === name);
      if (!ent) return false;
      this.target = { key: ent.key };
      MH.bus.emit('target.set', ent.data);
      return true;
    }

    travelFlourish(dir) {
      const CARD = ['north', 'south', 'east', 'west'];
      if (CARD.includes(dir)) return;
      const swirl = this.add.particles(this.player.x, this.player.y, 'px_white', {
        speed: { min: 20, max: 60 }, scale: { start: 0.6, end: 0 }, alpha: { start: 0.9, end: 0 },
        tint: dir === 'up' || dir === 'down' ? 0xcfe2ff : 0xc080ff,
        lifespan: 600, quantity: 14, blendMode: 'ADD',
      }).setDepth(50);
      this.time.delayedCall(700, () => swirl.destroy());
    }

    requestMove(dir) {
      const st = MH.state;
      if (st.pendingMove && Date.now() - st.pendingMove.sentAt < 2500) return;
      st.pendingMove = { dir, sentAt: Date.now() };
      this.exitSuppress = Date.now() + 700;   // no double-fire while in flight
      this.travelFlourish(dir);
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
        this._blockedDir = null;   // moved rooms: clear any refusal memory
        this.lastVnum = player.vnum;
        const layout = MH.generateRoomTopDown(roomData);
        this.slideTransition(layout, moveDir);
        MH.bus.emit('room.entered', { room: roomData, zoneName: roomEntry.zoneName });
      }
      this.syncEntities(roomEntry);
      this.applyAtmosphere(payload);
      this.syncWornAura(payload.player);
      this.syncPlayerDoll(payload.player);
      this.detectRoomChanges(roomData);
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
      // a brief wipe tinted to the destination zone, so arrivals feel like a
      // place-change rather than a hard cut
      try {
        const zt = layout.zoneKey && MH.ZONE_THEMES ? MH.ZONE_THEMES[layout.zoneKey] : null;
        const TINT = { forest: 0x6aff8a, field: 0xffe9a8, swamp: 0x8ab06a, cave: 0x8a90c8, dungeon: 0xb08aff, desert: 0xffd9a0, mountain: 0xcfe2ff, inside: 0xffd0a0, city: 0xffe0a0, underwater: 0x66e0ff };
        this.flashScreen((zt && zt.glow) || TINT[layout.theme] || 0xffe9c0, 0.16, 300);
      } catch (_) {}
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

    // class-colored aura when wearing legendaries / a full set
    syncWornAura(p) {
      const want = p && p.aura;
      if (want && !this.wornAura) {
        const cls = ((p.char_class || '') + '').toLowerCase();
        const tint = { warrior: 0xe05a4a, paladin: 0xffe9a8, mage: 0x9a8aff, necromancer: 0x9adba0,
          thief: 0xb8b2c8, assassin: 0x8a5a9a, ranger: 0x8ac06a, cleric: 0xcfe2ff, bard: 0xf0b060 }[cls] || 0xe8c168;
        this.wornAura = this.add.image(this.player.x, this.player.y, 'fx_glow')
          .setBlendMode(Phaser.BlendModes.ADD).setAlpha(0.30).setScale(0.34).setTint(tint).setDepth(7);
        this.tweens.add({ targets: this.wornAura, alpha: 0.45, scale: 0.4, duration: 1100, yoyo: true, repeat: -1, ease: 'sine.inOut' });
      } else if (!want && this.wornAura) {
        this.wornAura.destroy();
        this.wornAura = null;
      }
    }

    // same-room changes: a secret exit revealed by search appears in place
    // with a flourish. Deliberately conservative - only a genuinely NEW exit
    // direction triggers a rebuild, and never while the player is mid-move,
    // so this can never disturb navigation.
    detectRoomChanges(roomData) {
      if (!this.layout || roomData.vnum !== this.layout.vnum || !roomData.exits) return;
      if (MH.state.pendingMove || this.autoNav) return;   // never rebuild mid-move
      const fresh = Object.keys(roomData.exits).filter(d => !(d in (this.layout.exits || {})));
      if (!fresh.length) return;
      const px = this.player.x, py = this.player.y;
      const suppress = this.exitSuppress;
      const layout = MH.generateRoomTopDown(Object.assign({}, roomData));
      layout.zoneKey = this.layout.zoneKey;
      this.buildRoom(layout, 'none');
      this.player.setPosition(px, py);
      this.exitSuppress = suppress;   // an in-place rebuild must not re-gate exits
      const { T } = TD();
      const midX = Math.floor(layout.W / 2) * T, midY = Math.floor(layout.H / 2) * T;
      const SPOT = { north: [midX, T], south: [midX, this.pxH - T], west: [T, midY], east: [this.pxW - T, midY],
        up: layout.stairsUp ? [layout.stairsUp.x * T, layout.stairsUp.y * T] : [midX, midY],
        down: layout.stairsDown ? [layout.stairsDown.x * T, layout.stairsDown.y * T] : [midX, midY] };
      for (const d of fresh) {
        const [fx, fy] = SPOT[d] || [midX, midY];
        this.revealBurst(fx, fy);
        MH.bus.emit('flash', `A hidden way opens to the ${d}!`);
      }
    }

    revealBurst(x, y) {
      const burst = this.add.particles(x, y, 'px_white', {
        speed: { min: 30, max: 90 }, scale: { start: 0.7, end: 0 }, alpha: { start: 1, end: 0 },
        tint: [0xffe9a8, 0xe8c168, 0xffffff], lifespan: 700, quantity: 18, blendMode: 'ADD',
      }).setDepth(50);
      this.time.delayedCall(800, () => burst.destroy());
      this.cameras.main.flash(120, 255, 235, 180);
      MH.bus.emit('ambient.sound', 'chime');
    }

    // multiply the tile-kit floor/wall tiles by the day/night phase tint
    // (the kit's own world grade); the chrome never shifts hue
    applyKitTint() {
      if (!MH.tilekit || !MH.tilekit.isReady() || !this.kitTiles || !this.kitTiles.length) return;
      const period = (MH.state.lastPayload && MH.state.lastPayload.time && MH.state.lastPayload.time.period) || 'day';
      const phase = MH.tilekit.phaseForPeriod(period);
      const tint = MH.tilekit.tintFor(phase);
      for (const t of this.kitTiles) { if (t && t.active) t.setTint(tint); }
    }
    applyAtmosphere(payload) {
      const period = payload.time && payload.time.period;
      const outdoor = this.layout && !['inside', 'dungeon', 'cave', 'default'].includes(this.layout.theme);
      // readable per-phase character tint (lighter than the floor's so dolls
      // stay legible), applied to dolls + DCSS art for scene cohesion
      const phase = MH.tilekit ? MH.tilekit.phaseForPeriod(period) : 'midday';
      const CHAR_TINT = { midday: 0xeef3fb, dusk: 0xffcfa0, night: 0x9aa6d8 };
      this._charTint = (outdoor ? CHAR_TINT[phase] : 0xffffff) || 0xffffff;
      this.tintCharacters();
      // when the tile kit renders the room, its per-tile phase tint IS the
      // day/night grade — re-tint it and skip the dark overlay (no double-dim)
      const kitActive = !!(this.kitTiles && this.kitTiles.length && MH.tilekit && MH.tilekit.isReady());
      let alpha = 0, color = 0x1a2440;
      if (outdoor && !kitActive) {
        // keep night readable: a light tint that reads as evening, not a blackout
        if (period === 'night' || period === 'midnight') alpha = 0.18;
        else if (period === 'evening' || period === 'dusk') { alpha = 0.11; color = 0x40280f; }
        else if (period === 'dawn' || period === 'morning') { alpha = 0.06; color = 0x402a20; }
      }
      if (kitActive) this.applyKitTint();
      this.nightTint.setFillStyle(color, alpha);
      const precip = payload.weather && payload.weather.precipitation;
      const skyNow = (payload.weather && payload.weather.sky) || 'clear';
      const wantRain = outdoor && precip && precip !== 'none';
      if (wantRain && !this.weatherEmitter) {
        const snow = /snow/i.test(precip);
        const stormy = skyNow === 'stormy';
        if (snow) {
          this.weatherEmitter = this.add.particles(0, -10, 'px_bubble', {
            x: { min: 0, max: this.pxW }, speedY: { min: 20, max: 45 },
            speedX: { min: -10, max: 10 }, lifespan: 2000, quantity: 1, alpha: 0.7,
          }).setDepth(45);
        } else {
          // wind-driven rain: angled streaks, heavier in a storm, with a faint
          // far layer for depth and ground splashes where it lands
          const wind = stormy ? -120 : -55;
          const layers = MH.gfx ? MH.gfx.weatherLayers : 3;
          this.weatherEmitter = this.add.particles(0, -10, 'px_rain', {
            x: { min: -40, max: this.pxW }, speedY: stormy ? { min: 320, max: 430 } : { min: 220, max: 300 },
            speedX: { min: wind - 30, max: wind + 10 }, rotate: stormy ? -18 : -12,
            scaleY: stormy ? { min: 1.4, max: 2.2 } : { min: 1.0, max: 1.6 },
            lifespan: 1500, quantity: stormy ? 6 : 3, alpha: stormy ? 0.6 : 0.5,
          }).setDepth(45);
          if (layers >= 3) {
            this.rainFar = this.add.particles(0, -10, 'px_rain', {
              x: { min: -40, max: this.pxW }, speedY: { min: 180, max: 240 },
              speedX: { min: wind - 10, max: wind + 20 }, rotate: stormy ? -18 : -12,
              scaleX: 0.6, scaleY: 0.9, lifespan: 1600, quantity: stormy ? 3 : 1, alpha: 0.22,
            }).setDepth(8);
          }
          if (layers >= 2) {
            this.rainSplash = this.add.particles(0, 0, 'px_white', {
              x: { min: 0, max: this.pxW }, y: { min: this.pxH * 0.35, max: this.pxH - 6 },
              scaleX: { start: 0.5, end: 1.4 }, scaleY: { start: 0.5, end: 0.1 },
              alpha: { start: 0.5, end: 0 }, tint: 0xbcd0e0,
              lifespan: 360, frequency: stormy ? 60 : 130, blendMode: 'SCREEN',
            }).setDepth(7);
          }
        }
      } else if (!wantRain && this.weatherEmitter) {
        this.weatherEmitter.destroy();
        this.weatherEmitter = null;
        if (this.rainFar) { this.rainFar.destroy(); this.rainFar = null; }
        if (this.rainSplash) { this.rainSplash.destroy(); this.rainSplash = null; }
      }
      // ground weather: rain pools the floor with reflective puddles, snow
      // settles into pale drifts — laid once, cleared when the weather lifts
      const isSnow = wantRain && /snow/i.test(precip || '');
      const wantGround = wantRain && this.layout && !this.layout.swim;
      if (wantGround && !this.groundWeather) {
        this.groundWeather = [];
        const grd = this.layout.grid, gW = this.layout.W, gH = this.layout.H, gT = TD().T;
        const grng = MH.mulberry32((this.layout.vnum ^ (isSnow ? 0x5e0 : 0x9a7)) >>> 0);
        const n = 6 + Math.floor(grng() * 6);
        let made = 0, tries = 0;
        while (made < n && tries++ < 120) {
          const gx = 2 + ((grng() * (gW - 4)) | 0), gy = 2 + ((grng() * (gH - 4)) | 0);
          if (grd[gy * gW + gx] !== TD().FLOOR) continue;
          const bx = gx * gT + gT / 2, by = gy * gT + gT / 2;
          if (isSnow) {
            const s = this.add.image(bx, by, 'gd_patch').setDepth(0.5).setAlpha(0.5 + grng() * 0.3)
              .setTint(0xffffff).setScale(0.7 + grng() * 0.7);
            this.groundWeather.push(s);
          } else {
            const pud = this.add.image(bx, by, 'gd_patch').setDepth(0.5).setAlpha(0.28 + grng() * 0.16)
              .setTint(0x6a86a0).setScale(0.8 + grng() * 0.7).setBlendMode(Phaser.BlendModes.SCREEN);
            this.groundWeather.push(pud);
            this.tweens.add({ targets: pud, alpha: pud.alpha + 0.1, duration: 1400 + grng() * 1200, yoyo: true, repeat: -1, ease: 'sine.inOut' });
          }
          made++;
        }
      } else if (!wantGround && this.groundWeather) {
        this.groundWeather.forEach(o => o.destroy());
        this.groundWeather = null;
      }
      if (this.layout && this.layout.swim && !this.bubbleEmitter) {
        this.bubbleEmitter = this.add.particles(0, this.pxH, 'px_bubble', {
          x: { min: 0, max: this.pxW }, speedY: { min: -35, max: -12 }, lifespan: 3500, quantity: 1, alpha: 0.5,
        }).setDepth(45);
      }

      // sky moods: rolling fog, storm lightning
      const sky = (payload.weather && payload.weather.sky) || 'clear';
      const wantFog = outdoor && sky === 'foggy';
      if (wantFog && !this.fogEmitter) {
        this.fogEmitter = this.add.particles(0, 0, this.textures.exists('zt_px_soft') ? 'zt_px_soft' : 'px_white', {
          x: { min: -20, max: this.pxW }, y: { min: 10, max: this.pxH - 10 },
          tint: 0xc8d0dc, scale: { start: 2.5, end: 4.5 }, alpha: { start: 0, end: 0.13 },
          speedX: { min: 6, max: 16 }, speedY: { min: -2, max: 2 },
          lifespan: 9000, frequency: 420, blendMode: 'SCREEN',
        }).setDepth(46);
      } else if (!wantFog && this.fogEmitter) {
        this.fogEmitter.destroy();
        this.fogEmitter = null;
      }
      const storming = outdoor && sky === 'stormy';
      if (storming && (!this._nextBolt || Date.now() > this._nextBolt)) {
        this._nextBolt = Date.now() + 6000 + Math.random() * 14000;
        // a jagged bolt strikes a random spot, washing the whole room in a
        // cold blue-white flicker (a stutter-flash sells the strike)
        try { if (MH.fx && MH.fx.boltFromSky) MH.fx.boltFromSky(this, Phaser.Math.Between(40, this.pxW - 40), Phaser.Math.Between(this.pxH * 0.3, this.pxH * 0.7), MH.fx.PAL.lightning); } catch (_) {}
        this.flashScreen(0xcfe0ff, 0.55, 140);
        this.time.delayedCall(110, () => this.flashScreen(0xdfeaff, 0.35, 200));
        this.cameras.main.flash(120, 210, 222, 255);
        MH.bus.emit('ambient.sound', 'thunder');
      }

      // desert heat-shimmer: warm haze rising off the ground on hot, clear days
      const wantHaze = (!MH.gfx || MH.gfx.caustics) && this.layout && this.layout.theme === 'desert'
        && !['night', 'midnight', 'evening', 'dusk'].includes(period)
        && sky !== 'stormy' && !wantRain;
      if (wantHaze && !this.heatHaze) {
        this.heatHaze = this.add.particles(0, 0, this.textures.exists('zt_px_soft') ? 'zt_px_soft' : 'px_white', {
          x: { min: 0, max: this.pxW }, y: { min: this.pxH * 0.45, max: this.pxH - 4 },
          tint: 0xffe0a8, scaleX: { start: 1.2, end: 2.0 }, scaleY: { start: 0.4, end: 1.1 },
          alpha: { start: 0, end: 0.07 }, speedY: { min: -22, max: -10 }, speedX: { min: -4, max: 4 },
          lifespan: 2600, frequency: 240, blendMode: 'SCREEN',
        }).setDepth(33);
      } else if (!wantHaze && this.heatHaze) {
        this.heatHaze.destroy();
        this.heatHaze = null;
      }
      this.updateColorGrade(period, this.layout && this.layout.theme, sky);
      this.updateSignatureMist();
    }

    // Quality changed live: add/remove bloom, then rebuild the room's
    // atmosphere (parallax/caustics/particle density) and rim-lights.
    onGfxChanged() {
      try {
        const pfx = this.cameras.main.postFX;
        if (pfx) {
          if (MH.gfx.bloom && !this.bloomFx) {
            this.bloomFx = pfx.addBloom(0xffffff, 1, 1, 0.7, 0.5, 5);
            this._gradeKey = null;   // re-apply bloom tint
          } else if (!MH.gfx.bloom && this.bloomFx) {
            pfx.remove(this.bloomFx); this.bloomFx = null;
          }
        }
      } catch (_) {}
      // rim-lights: tear down or (re)create to match the new setting
      if (!MH.gfx.rim) {
        if (this.playerRim) { this.playerRim.setVisible(false); }
        for (const ent of this.entities.values()) if (ent.rim) ent.rim.setVisible(false);
      } else if (this.playerRim) {
        this.playerRim.setVisible(true);
      }
      // re-thin/enrich the whole room (clutter, wildlife, walls, particles) to
      // match the new quality immediately, preserving where the player stands
      if (this.layout && MH.state.lastPayload) {
        const px = this.player.x, py = this.player.y, suppress = this.exitSuppress;
        this._gradeKey = null;
        this.buildRoom(this.layout, 'none');
        this.player.setPosition(px, py);
        this.exitSuppress = suppress;
        const entry = (MH.state.lastPayload.rooms || []).find(r => r.vnum === this.layout.vnum);
        if (entry) this.syncEntities(entry);     // bring mobs/items straight back
        this.applyAtmosphere(MH.state.lastPayload);
      } else if (this.layout) {
        this._gradeKey = null; this.buildAtmosphere(this.layout, this.layout.theme);
      }
    }

    // Dynamic cinematic grade: a per-zone tonal curve (saturation/contrast via
    // the WebGL ColorMatrix) plus a soft colour cast (warm cities, cold caves,
    // green swamps…), both shifted by the time of day and the weather. This is
    // what gives each region its own mood without touching the pixel art.
    updateColorGrade(period, theme, sky) {
      const key = `${theme}|${period}|${sky}`;
      if (this._gradeKey === key) return;
      this._gradeKey = key;

      // --- per-zone base grade: [saturate, contrast, castColor, castAlpha] ---
      const ZONE = {
        swamp: [0.22, 0.06, 0x6a8a4a, 0.16],
        forest: [0.26, 0.05, 0x4c7a3c, 0.11],
        field: [0.22, 0.05, 0x6e8a4a, 0.08],
        hills: [0.20, 0.05, 0x7a8a4a, 0.08],
        cave: [-0.02, 0.13, 0x3a4a7a, 0.18],
        dungeon: [0.02, 0.12, 0x4a3a6a, 0.16],
        underground: [0.0, 0.12, 0x3a4a6a, 0.16],
        inside: [0.10, 0.05, 0x7a5a2a, 0.10],
        city: [0.16, 0.05, 0x8a6a2a, 0.08],
        desert: [0.20, 0.08, 0xaa7a3a, 0.13],
        mountain: [0.14, 0.07, 0x5a7aaa, 0.11],
        underwater: [0.04, 0.04, 0x2a7aaa, 0.18],
        water_swim: [0.10, 0.04, 0x2f86b4, 0.14],
        water_noswim: [0.10, 0.04, 0x2f86b4, 0.12],
        flying: [0.18, 0.05, 0x8ab4e8, 0.08],
        default: [0.15, 0.05, 0x000000, 0.0],
      };
      let [sat, con, cast, castA] = ZONE[theme] || ZONE.default;

      // --- time of day: warm dusk, cold night, soft dawn ---
      if (period === 'night' || period === 'midnight') {
        sat -= 0.05; con += 0.06; cast = 0x2a3a6e; castA = Math.max(castA, 0.09);
      } else if (period === 'evening' || period === 'dusk') {
        sat += 0.04; cast = 0x9a5a2a; castA = Math.max(castA, 0.14);
      } else if (period === 'dawn' || period === 'morning') {
        con -= 0.02; cast = 0xb47a5a; castA = Math.max(castA * 0.8, 0.10);
      }

      // --- weather: storms drain colour, fog flattens contrast ---
      if (sky === 'stormy') { sat -= 0.14; con += 0.04; cast = 0x44506a; castA = Math.max(castA, 0.16); }
      else if (sky === 'foggy') { sat -= 0.08; con -= 0.06; castA *= 0.7; }
      else if (sky === 'overcast') { sat -= 0.06; con -= 0.02; }

      // crispness pass: trim the colour wash and lift contrast a touch so the
      // pixel art reads sharp instead of hazy (mood stays, fog goes)
      castA *= 0.72;
      con += 0.05;

      // apply the tonal grade through the postFX ColorMatrix (WebGL only)
      const cm = this.gradeFx;
      if (cm && cm.reset) {
        cm.reset();
        cm.saturate(Phaser.Math.Clamp(sat, -0.9, 0.9), true);
        cm.contrast(Phaser.Math.Clamp(con, -0.5, 0.5), true);
        // a gentle brightness lift keeps rooms crisp and clear, never murky;
        // a touch less at night so dusk still reads as dusk
        const dark = period === 'night' || period === 'midnight';
        if (cm.brightness) cm.brightness(dark ? 1.04 : 1.1, true);
      }
      // tint the bloom so every glowing light/effect carries the zone's warmth
      if (this.bloomFx) {
        const warm = ['city', 'inside', 'desert'].includes(theme) || ['evening', 'dusk', 'dawn', 'morning'].includes(period);
        const cold = ['cave', 'dungeon', 'underground', 'mountain', 'underwater', 'water_swim', 'water_noswim'].includes(theme)
          || period === 'night' || period === 'midnight' || sky === 'stormy';
        const green = ['swamp', 'forest'].includes(theme);
        this.bloomFx.color = warm ? 0xfff0d8 : green ? 0xe8f4d8 : cold ? 0xd8e4ff : 0xffffff;
      }
      // rim-light colour tracks the zone's light so edges read warm or cold
      {
        const warm = ['city', 'inside', 'desert'].includes(theme) || ['evening', 'dusk', 'dawn', 'morning'].includes(period);
        const cold = ['cave', 'dungeon', 'underground', 'mountain', 'underwater', 'water_swim', 'water_noswim'].includes(theme)
          || period === 'night' || period === 'midnight';
        this.rimTint = warm ? 0xffe8c0 : cold ? 0xc8dcff : 0xfff2cc;
      }
      // apply the colour cast (works on every renderer); ease the alpha so
      // walking between zones cross-fades the grade instead of snapping
      if (this.gradeCast) {
        const fromA = this.gradeCast.fillAlpha || 0;
        this.tweens.killTweensOf(this.gradeCast);
        this.gradeCast.setFillStyle(cast, fromA);
        this.tweens.add({
          targets: this.gradeCast,
          fillAlpha: Phaser.Math.Clamp(castA, 0, 0.3),
          duration: 900, ease: 'sine.inOut',
        });
      }
    }

    // Misthollow's signature: a persistent low mist drifts through every
    // room — thin in cities, choking in swamps/crypts/the dark.
    updateSignatureMist() {
      const theme = (this.layout && this.layout.theme) || 'default';
      const dark = !!(this.layout && this.layout.dark);
      const swim = !!(this.layout && this.layout.swim);
      const key = theme + (dark ? 'D' : '') + (swim ? 'S' : '');
      if (this._mistKey === key) return;
      this._mistKey = key;
      if (this.mistLayer) { this.mistLayer.destroy(); this.mistLayer = null; }
      if (swim) return;  // underwater already has bubbles
      const heavy = dark || ['swamp', 'cave', 'dungeon', 'underground'].includes(theme);
      const light = ['inside', 'city'].includes(theme);
      const maxAlpha = heavy ? 0.1 : light ? 0.025 : 0.045;
      const tint = theme === 'swamp' ? 0x9ab69a : (dark || theme === 'cave') ? 0x8a90a8 : 0xc8d0dc;
      this.mistLayer = this.add.particles(0, 0, 'px_light', {
        x: { min: -30, max: this.pxW + 30 }, y: { min: this.pxH * 0.42, max: this.pxH - 4 },
        tint, scale: { start: 0.55, end: 1.15 }, alpha: { start: 0, end: maxAlpha },
        speedX: { min: 5, max: 15 }, speedY: { min: -2, max: 2 },
        lifespan: 11000, frequency: heavy ? 480 : 900, blendMode: 'SCREEN',
      }).setDepth(9);
    }

    // ---------- update loop ----------
    update() {
      // a thrown frame must never kill the rAF loop (a dead loop = total
      // freeze, the "stuck at the exit" bug) - contain, log, keep running
      try {
        this.updateInner();
      } catch (e) {
        if (!this._lastUpdateErr || Date.now() - this._lastUpdateErr > 2000) {
          this._lastUpdateErr = Date.now();
          console.error('[misthollow] update error (contained):', e);
        }
      }
    }

    updateInner() {
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
      // a window owns the screen: the world doesn't hear the keys
      if (MH.state.uiFrozen) { ax = 0; ay = 0; }

      // a move that never got an answer (lost line, eaten message) must not
      // wedge the input forever
      if (MH.state.pendingMove && Date.now() - MH.state.pendingMove.sentAt > 4000) MH.state.pendingMove = null;
      // keyboard can never stay wedged off while the game has focus -
      // unless a window deliberately froze the world
      if (!this.input.keyboard.enabled && !MH.state.uiFrozen) {
        const a = document.activeElement;
        if (!a || a === document.body || a.tagName === 'CANVAS') {
          this.input.keyboard.enabled = true;
          try { this.input.keyboard.enableGlobalCapture(); } catch (_) {}
        }
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
      if (this.wornAura) this.wornAura.setPosition(this.player.x, this.player.y + 4);
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
        // when you drive into a border wall that has an exit, slide along it
        // toward the gap - the whole wall funnels you to the door (no more
        // getting pinned in a corner far from a centered gap)
        const PULL = 90;
        if (ax < 0 && body.blocked.left && L.gaps.west) {
          vy = Math.abs(gapMidY - this.player.y) > 3 ? Math.sign(gapMidY - this.player.y) * PULL : 0;
        } else if (ax > 0 && body.blocked.right && L.gaps.east) {
          vy = Math.abs(gapMidY - this.player.y) > 3 ? Math.sign(gapMidY - this.player.y) * PULL : 0;
        } else if (ay < 0 && body.blocked.up && L.gaps.north) {
          vx = Math.abs(gapMidX - this.player.x) > 3 ? Math.sign(gapMidX - this.player.x) * PULL : 0;
        } else if (ay > 0 && body.blocked.down && L.gaps.south) {
          vx = Math.abs(gapMidX - this.player.x) > 3 ? Math.sign(gapMidX - this.player.x) * PULL : 0;
        }
        this.player.setVelocity(vx, vy);
        this.setFacing(ax, ay);
        this.playWalk();
      } else {
        this.player.setVelocity(0, 0);
        const pos = MH.state.player && MH.state.player.position;
        if (pos === 'sleeping' || pos === 'resting' || pos === 'sitting') {
          // show the recovery pose while idle (any movement re-stands you)
          this.player.anims.stop();
          this.player.setFrame(pos === 'sleeping' ? 'sleep' : 'rest');
        } else {
          this.player.anims.stop();
          this.player.setFrame(`${this.facing}0`);
        }
      }

      const now = Date.now();

      // exits: three independent triggers so geometry can never strand you.
      //  1) EDGE-PRESS: drive a cardinal into a border wall that has an exit
      //     that way - intent is unambiguous, fires from anywhere on the wall
      //  2) ZONE OVERLAP: walk onto an exit/feature zone (stairs, portals)
      //  3) DEAD-MAN'S SWITCH: pressing toward an existing exit for too long
      //     with no room change forces the move, bypassing every gate
      {
        const b = this.player.body;
        const L = this.layout;
        const T = TD().T;
        let wantExit = null;
        let force = false;
        if (L && L.gaps) {
          const atTop = b.blocked.up || this.player.y < T * 1.4;
          const atBot = b.blocked.down || this.player.y > this.pxH - T * 1.4;
          const atLeft = b.blocked.left || this.player.x < T * 1.4;
          const atRight = b.blocked.right || this.player.x > this.pxW - T * 1.4;
          if (ay < 0 && L.gaps.north && atTop) wantExit = 'north';
          else if (ay > 0 && L.gaps.south && atBot) wantExit = 'south';
          else if (ax < 0 && L.gaps.west && atLeft) wantExit = 'west';
          else if (ax > 0 && L.gaps.east && atRight) wantExit = 'east';
        }
        if (!wantExit) {
          const pb = new Phaser.Geom.Rectangle(b.x, b.y, b.width, b.height);
          for (const zone of this.exitZones.concat(this.featureZones || [])) {
            if (Phaser.Geom.Rectangle.Overlaps(zone.getBounds(), pb)) { wantExit = zone.exitDir; break; }
          }
        }
        // dead-man's switch: holding a direction with an exit but going
        // nowhere for 1.5s means SOMETHING wedged - break through it
        const pressedDir = ay < 0 ? 'north' : ay > 0 ? 'south' : ax < 0 ? 'west' : ax > 0 ? 'east' : null;
        if (manual && pressedDir && L && L.exits && Object.prototype.hasOwnProperty.call(L.exits, pressedDir)
            && !MH.state.inCombat && !locked) {
          if (this._pressDir !== pressedDir) { this._pressDir = pressedDir; this._pressSince = now; }
          else if (now - this._pressSince > 1500) {
            wantExit = pressedDir; force = true;
          }
        } else {
          this._pressDir = null;
        }
        // a direction the server just refused (class/level lock, exhaustion):
        // don't ram it again until the cooldown passes or you press elsewhere
        if (wantExit && wantExit === this._blockedDir && now < this._blockedUntil) {
          if (pressedDir && pressedDir !== this._blockedDir) this._blockedDir = null;
          wantExit = null;
        }
        if (wantExit) {
          if (MH.state.inCombat) {
            if (!this._gateFlash || now - this._gateFlash > 2500) {
              this._gateFlash = now;
              MH.bus.emit('flash', "You're fighting! Flee to escape, or finish it.");
            }
          } else if (!force && (locked || now <= this.exitSuppress)) {
            // in-flight or cooling down: silent, resolves within a second
          } else {
            if (force) { MH.state.pendingMove = null; this.exitSuppress = 0; this._pressSince = now; }
            this.requestMove(wantExit);
          }
        }
      }

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
        // sleepers/resters stay put in their pose until something wakes them
        if (ent.data && (ent.data.pose === 'sleeping' || ent.data.pose === 'resting')) {
          if (ent.sprite && !ent.sprite.anims.isPlaying) {
            const want = ent.data.pose === 'sleeping' ? 'sleep' : 'rest';
            if (ent.sprite.frame && ent.sprite.frame.name !== want) ent.sprite.setFrame(want);
          }
          continue;
        }
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
      if (this.playerShadow) { this.playerShadow.x = this.player.x; this.playerShadow.y = this.player.y + 9; this.playerShadow.setVisible(!this.dead); }

      // parallax: slide the overlay planes opposite the player's offset from the
      // room centre — far plane drifts gently, near plane more, for layered depth
      {
        const ox = this.player.x - this.pxW / 2, oy = this.player.y - this.pxH / 2;
        if (this.pxFar) this.pxFar.setPosition(-ox * 0.04, -oy * 0.04);
        if (this.pxNear) this.pxNear.setPosition(-ox * 0.11, -oy * 0.11);
      }
      // rim-light follows the player's current frame, nudged toward the light
      if (this.playerRim && (!MH.gfx || MH.gfx.rim)) {
        const r = this.playerRim, pl = this.player;
        r.setTexture(pl.texture.key, pl.frame.name);
        r.setFlipX(pl.flipX); r.setScale(pl.scaleX * 1.08, pl.scaleY * 1.08);
        r.setPosition(pl.x - 0.6, pl.y - 1.2);
        r.setTint(this.rimTint).setVisible(!this.dead);
      } else if (this.playerRim) {
        this.playerRim.setVisible(false);
      }

      // footstep dust gives weight to movement
      this.updateCritters(now, dt);
      this.reactToPlayer(now, dt);

      const moving = Math.abs(this.player.body.velocity.x) + Math.abs(this.player.body.velocity.y) > 10;
      if (moving && (!this._lastStep || now - this._lastStep > 260)) {
        this._lastStep = now;
        if (MH.sfx) MH.sfx.step();
        const puff = this.add.image(this.player.x, this.player.y + 9, 'px_poof')
          .setScale(0.6).setAlpha(0.35).setDepth(6);
        this.tweens.add({ targets: puff, scale: 1.3, alpha: 0, duration: 380, onComplete: () => puff.destroy() });
      }

      // labels + hp bars follow
      for (const ent of this.entities.values()) {
        if (ent.shadow && ent.sprite) { ent.shadow.x = ent.sprite.x; ent.shadow.y = ent.sprite.y + 9; ent.shadow.setVisible(ent.sprite.visible && !ent.leaving); }
        if (ent.rim && ent.sprite && (!MH.gfx || MH.gfx.rim)) {
          ent.rim.setTexture(ent.sprite.texture.key, ent.sprite.frame.name);
          ent.rim.setFlipX(ent.sprite.flipX);
          ent.rim.setScale(ent.sprite.scaleX * 1.08, ent.sprite.scaleY * 1.08);
          ent.rim.setPosition(ent.sprite.x - 0.6, ent.sprite.y - 1.2);
          ent.rim.setDepth(ent.sprite.depth - 0.1).setTint(this.rimTint).setVisible(ent.sprite.visible && !ent.leaving);
        } else if (ent.rim) {
          ent.rim.setVisible(false);
        }
        if (ent.label && ent.sprite) { ent.label.x = ent.sprite.x; ent.label.y = ent.sprite.y - (ent.data.boss ? 26 : 18); }
        if (ent.fightMark && ent.sprite) { ent.fightMark.x = ent.sprite.x; ent.fightMark.y = ent.sprite.y - 26; }
        if (ent.questMark && ent.sprite) { ent.questMark.x = ent.sprite.x; }
        if (ent.serviceMark && ent.sprite) { ent.serviceMark.x = ent.sprite.x + 9; }
        if (ent.hpbar && ent.sprite) this.drawHpBar(ent);
        if (ent.engageRing && ent.sprite) {
          const g = ent.engageRing;
          g.clear();
          const mine = this.target && this.target.key === ent.key;
          const a = mine ? 0.9 : 0.45 + 0.3 * Math.sin(now / 240);
          g.lineStyle(1.5, mine ? 0xe8c168 : 0xe05a4a, a);
          g.strokeEllipse(ent.sprite.x, ent.sprite.y + 9, 18, 8);
        }
      }
      // depth-sort actors by y so overlap reads correctly
      this.player.setDepth(10 + this.player.y / 1000);
      this.updatePlayerDoll(now);
      for (const ent of this.entities.values()) {
        if (ent.sprite && ent.kind !== 'item') ent.sprite.setDepth(10 + ent.sprite.y / 1000);
        if (ent.doll) {
          const s = ent.sprite;
          if (s.alpha !== 0) s.setAlpha(0);          // keep procedural sprite hidden
          if (ent.rim) ent.rim.setVisible(false);
          ent.doll.container.setPosition(s.x, s.y);
          ent.doll.container.setDepth(10 + s.y / 1000 + 0.01);
          const prev = ent._dollPrev || { x: s.x, y: s.y };
          const moving = Math.abs(s.x - prev.x) + Math.abs(s.y - prev.y) > 0.3;
          const facing = s.flipX ? 'left' : (ent.facing === 'u' ? 'up' : 'down');
          ent.doll.setAction(ent.data && ent.data.fighting ? 'attack' : (moving ? 'walk' : 'idle'), facing);
          ent.doll.update(now);
          ent._dollPrev = { x: s.x, y: s.y };
        } else if (ent.art) {
          const s = ent.sprite;
          if (s.alpha !== 0) s.setAlpha(0);
          if (ent.rim) ent.rim.setVisible(false);
          ent.art.x = s.x;
          ent.art.y = s.y - 6 + Math.sin(now / 600 + (ent.artPhase || 0)) * 1.5;   // follow + idle bob
          ent.art.setDepth(10 + s.y / 1000 + 0.01);
          ent.art.setFlipX(s.flipX);
        }
      }

      if (this.layout.dark && this.darkRT.visible) {
        this.darkRT.clear();
        this.darkRT.fill(0x000008, 0.92);
        const stamp = this.lightStamp;
        const carve = (x, y, radius, jitter) => {
          stamp.setVisible(true).setPosition(x, y).setScale((radius / 128) * jitter);
          this.darkRT.erase(stamp);
        };
        // the player carries a torch: a wide, gently breathing pool
        carve(this.player.x, this.player.y, 132, 0.97 + 0.03 * Math.sin(now / 280));
        // every brazier, candle and travel feature throws its own flickering light
        for (const ls of (this.lightSources || [])) {
          const flick = 0.86 + 0.14 * Math.sin(now / 90 + ls.seed) * Math.sin(now / 47 + ls.seed * 1.7);
          carve(ls.x, ls.y, ls.r, flick);
        }
        stamp.setVisible(false);
      }
    }

    setFacing(dx, dy) {
      if (Math.abs(dx) > Math.abs(dy)) { this.facing = 's'; this.player.setFlipX(dx < 0); }
      else if (dy > 0) this.facing = 'd';
      else if (dy < 0) this.facing = 'u';
    }
    playWalk() {
      this._walkFrame = this.time.now;   // doll movement signal
      const tex = this.playerTex();
      const anim = `${tex}_walk${this.facing}`;
      if (!this.player.anims.isPlaying || this.player.anims.currentAnim.key !== anim) this.player.play(anim);
    }
    // facing for the LPC doll: 'u'/'d' map directly; 's' splits by flipX
    lpcFacing() {
      if (this.facing === 'u') return 'up';
      if (this.facing === 'd') return 'down';
      return this.player.flipX ? 'left' : 'right';
    }
    // create/refresh the player's LPC paperdoll when gear/class changes; hide
    // the procedural sprite while the doll is active
    syncPlayerDoll(p) {
      if (!p || !MH.lpc || !MH.lpc.isReady()) return;
      const spec = { char_class: p.char_class, sex: p.sex || 'male', equipment: p.equipment || {} };
      const sig = MH.lpc.sig(spec);
      if (this.playerDoll && this._dollSig === sig) return;
      if (this.playerDoll) { this.playerDoll.destroy(); this.playerDoll = null; }
      this._dollSig = sig;
      this.playerDoll = MH.lpc.makeDoll(this, spec, 0.4, () => this.tintCharacters());
      this.playerDoll.container.setDepth(10);
      this.player.setAlpha(0);                 // keep physics body, hide the pixel art
      if (this.playerRim) this.playerRim.setVisible(false);
    }
    updatePlayerDoll(now) {
      const d = this.playerDoll;
      if (!d) return;
      // the doll is the only visible body — keep the procedural sprite + its
      // additive rim hidden every frame (several places reset player.alpha=1)
      if (this.player.alpha !== 0) this.player.setAlpha(0);
      if (this.playerRim) this.playerRim.setVisible(false);
      d.container.setPosition(this.player.x, this.player.y);
      d.container.setDepth(10 + this.player.y / 1000);
      let action = 'idle';
      if (this._atkFrame && now - this._atkFrame < 300) action = 'attack';
      else if (this._walkFrame && now - this._walkFrame < 130) action = 'walk';
      d.setAction(action, this.lpcFacing());
      d.update(now);
    }
  }

  MH.TopRoomScene = TopRoomScene;
})();
