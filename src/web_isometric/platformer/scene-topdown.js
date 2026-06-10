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
        const z = Math.max(2, Math.floor(Math.min(this.scale.width / this.pxW, this.scale.height / this.pxH)));
        this.cameras.main.setZoom(z);
        this.cameras.main.centerOn(this.pxW / 2, this.pxH / 2);
      };
      fit();
      this.scale.on('resize', fit);

      this.solids = this.physics.add.staticGroup();
      this.tileLayer = this.add.layer();
      this.bgLayer = this.add.layer().setDepth(-10);

      this.player = this.physics.add.sprite(this.pxW / 2, this.pxH / 2, 'td_player_warrior', 'd0');
      this.player.setSize(11, 10).setOffset(6.5, 12);
      this.player.setDepth(10);
      this.player.setCollideWorldBounds(true);
      this.player.body.setAllowGravity(false);
      this.facing = 'd';
      this.physics.add.collider(this.player, this.solids);

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
      MH.bus.on('player.exp', e => this.fxExp(e));
      MH.bus.on('walk.step', dir => this.requestMove(dir));
      MH.bus.on('nav.goto', dir => this.navTo(dir));
      MH.bus.on('player.attack', () => this.tryAttack());
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
      if (this.weatherEmitter) { this.weatherEmitter.destroy(); this.weatherEmitter = null; }
      if (this.bubbleEmitter) { this.bubbleEmitter.destroy(); this.bubbleEmitter = null; }

      const th = layout.theme;

      // floor everywhere, then border/obstacles/water from the grid
      for (let y = 0; y < layout.H; y++) {
        for (let x = 0; x < layout.W; x++) {
          const cell = layout.grid[y * layout.W + x];
          const img = this.add.image(x * T, y * T, `td_${th}_floor`).setOrigin(0, 0);
          if ((x + y) % 2) img.setTint(0xf2f2f2);   // subtle checker
          this.bgLayer.add(img);
          if (cell === BLOCK) {
            const isBorder = x === 0 || y === 0 || x === layout.W - 1 || y === layout.H - 1;
            const ob = layout.obstacles && layout.obstacles.find(o =>
              x >= o.x && x < o.x + (o.big ? 2 : 1) && y >= o.y && y < o.y + (o.big ? 2 : 1));
            const key = isBorder ? `td_${th}_border` : `td_${th}_obst${ob ? ob.idx : 0}`;
            const blockImg = this.add.image(x * T, y * T, key).setOrigin(0, 0).setDepth(1);
            this.tileLayer.add(blockImg);
          } else if (cell === WATER) {
            const spr = this.add.sprite(x * T, y * T, `t_${th}_water`, '0').setOrigin(0, 0).setDepth(1).setAlpha(0.95);
            spr.play(`water_${th}`);
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

      // props, gravestones, prose
      for (const prop of layout.props) {
        const img = this.add.image(prop.x * T, (prop.y + 1) * T, `t_${th}_prop${prop.idx}`).setOrigin(0.25, 1).setDepth(3).setScale(0.8);
        this.tileLayer.add(img);
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
          fontFamily: 'Courier New', resolution: 3, fontSize: '7px', fontStyle: 'italic', color: '#e8c168',
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
        const img = this.add.image(fx * T, fy * T, texKey).setOrigin(0, 0).setDepth(2);
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
        const spr = this.add.sprite(p.x * T + T / 2, (p.y + 1) * T, 't_portal', '0').setOrigin(0.5, 1).setDepth(3).setScale(0.7);
        spr.play('portal_shimmer');
        this.tileLayer.add(spr);
        const zone = this.add.zone(p.x * T, p.y * T, T, T).setOrigin(0, 0);
        this.physics.add.existing(zone, true);
        zone.exitDir = p.name;
        this.featureZones.push(zone);
        const hint = this.add.text(p.x * T + T / 2, (p.y - 1.2) * T, p.name, {
          fontFamily: 'Courier New', resolution: 3, fontSize: '7px', color: '#b87cf0',
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
        const tx = this.add.text(40 + rng() * (this.pxW - 220), 40 + i * 80 + rng() * 30, frag, {
          fontFamily: 'Courier New', resolution: 3, fontSize: '8px', fontStyle: 'italic', color: '#ffffff',
        }).setAlpha(0.16).setDepth(4);
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
        const g = this.add.image(sx, sy, 't_grave').setOrigin(0.5, 1).setDepth(3).setScale(0.8);
        this.tileLayer.add(g);
        const slain = d.killer ? `${d.name}, slain by ${d.killer}` : d.name;
        const label = this.add.text(sx, sy - 18, `here lies ${slain}`, {
          fontFamily: 'Courier New', resolution: 3, fontSize: '7px', fontStyle: 'italic', color: '#8a90a4',
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
        ent.sprite = this.add.image(slot.x, slot.y, this.safeTex(MH.sprites.itemKey(spec.data.type), 'px_star')).setDepth(5);
        this.tweens.add({ targets: ent.sprite, y: slot.y - 3, duration: 900, yoyo: true, repeat: -1, ease: 'sine.inOut' });
        ent.sprite.setInteractive({ useHandCursor: true });
        ent.sprite.on('pointerdown', () => MH.sendCommand(`get ${MH.mobKeyword(spec.data.name)}`));
        return ent;
      }

      const tex = this.safeTex(spec.kind === 'player' ? MH.tdSprites.playerKey(spec.data.char_class) : MH.tdSprites.mobKey(spec.data.name), 'td_mob_citizen');
      ent.sprite = this.add.sprite(slot.x, slot.y, tex, 'd0').setDepth(8);
      ent.sprite.play(`${tex}_walkd`);
      ent.sprite.anims.pause();
      if (spec.data.boss) ent.sprite.setScale(1.5);
      ent.homeX = slot.x; ent.homeY = slot.y;

      const labelColor = spec.kind === 'player' ? '#6ca8e0' : (spec.data.hostile ? '#e06c6c' : (spec.data.shopkeeper ? '#e8c168' : '#c8ccd8'));
      ent.label = this.add.text(slot.x, slot.y - 18, this.shortName(spec.data.name), {
        fontFamily: 'Courier New', resolution: 3, fontSize: '7px', color: labelColor,
      }).setOrigin(0.5, 1).setDepth(9);
      ent.hpbar = this.add.graphics().setDepth(9);
      this.drawHpBar(ent);

      ent.sprite.setInteractive({ useHandCursor: true });
      ent.sprite.on('pointerdown', () => {
        if (spec.kind === 'mob') {
          if (spec.data.shopkeeper) MH.bus.emit('shop.open', spec.data);
          else this.attackEntity(ent);
        }
      });
      ent.sprite.on('pointerover', pointer => MH.bus.emit('mob.tip', { data: ent.data, kind: ent.kind, x: pointer.event.clientX, y: pointer.event.clientY }));
      ent.sprite.on('pointermove', pointer => MH.bus.emit('mob.tip', { data: ent.data, kind: ent.kind, x: pointer.event.clientX, y: pointer.event.clientY }));
      ent.sprite.on('pointerout', () => MH.bus.emit('mob.tip.hide'));

      if (spec.kind === 'mob' && !spec.data.shopkeeper) {
        if (spec.data.hostile) ent.stalker = true;
        else {
          ent.patrol = this.tweens.add({
            targets: ent.sprite, x: slot.x + 14, duration: 2400 + (MH.hashStr(key) % 1400),
            yoyo: true, repeat: -1, ease: 'sine.inOut', delay: MH.hashStr(key) % 1000,
          });
        }
      }
      return ent;
    }

    updateEntity(ent, data) {
      ent.data = data;
      this.drawHpBar(ent);
      // loud telegraph: red swords + red name over whoever is attacking YOU
      if (data.fighting && !ent.fightMark) {
        ent.fightMark = this.add.text(ent.sprite.x, ent.sprite.y - 26, '⚔', {
          fontFamily: 'Courier New', resolution: 3, fontSize: '12px', color: '#ff5050', stroke: '#000', strokeThickness: 2,
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
      const x = ent.sprite.x - 9, y = ent.sprite.y - 16;
      ent.hpbar.fillStyle(0x000000, 0.7).fillRect(x, y, 18, 2);
      ent.hpbar.fillStyle(frac > 0.5 ? 0x6fd685 : frac > 0.25 ? 0xe8c168 : 0xe06c6c, 1).fillRect(x, y, 18 * frac, 2);
    }
    destroyEntity(ent) {
      if (ent.patrol) ent.patrol.stop();
      ['sprite', 'label', 'hpbar', 'fightMark'].forEach(k => { if (ent[k]) ent[k].destroy(); });
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
      this.tweens.add({ targets: ent.sprite, x: ent.sprite.x + Math.cos(ang) * 5, y: ent.sprite.y + Math.sin(ang) * 5, duration: 70, yoyo: true });
      this.spark(ent.sprite.x, ent.sprite.y - 6, 0xffe080);
      const st = this.dmgStyle(e.dmg);
      if (st.shake) this.cameras.main.shake(90, st.shake);
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
      const atk = e && e.from ? this.findEntityByText(e.from) : null;
      if (atk && atk.sprite) {
        const ang = Math.atan2(this.player.y - atk.sprite.y, this.player.x - atk.sprite.x);
        this.player.x += Math.cos(ang) * 6;
        this.player.y += Math.sin(ang) * 6;
      }
      this.damageNumber(this.player.x, this.player.y - 18, e && e.dmg != null ? `-${e.dmg}` : '✦', '#e06c6c', st.size);
    }
    fxExp(e) {
      const t = this.add.text(this.player.x, this.player.y - 22, `+${e.amount} xp`, {
        fontFamily: 'Courier New', resolution: 3, fontSize: '9px', color: '#e8c168', stroke: '#000', strokeThickness: 2,
      }).setOrigin(0.5).setDepth(60);
      this.tweens.add({ targets: t, y: t.y - 18, alpha: 0, duration: 1400, ease: 'sine.out', onComplete: () => t.destroy() });
    }
    fxMobDeath(e) {
      const ent = this.findEntityByText(e.name) || this.target;
      if (ent && ent.sprite) {
        ent.sprite.setFrame('death');
        this.poof(ent.sprite.x, ent.sprite.y);
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
        fontFamily: 'Courier New', resolution: 3, fontSize: '8px', fontStyle: 'italic', color: '#c8d0e4',
      }).setAlpha(0).setDepth(45);
      this.tweens.add({ targets: t, alpha: 0.45, duration: 900, yoyo: true, hold: 3600, onComplete: () => t.destroy() });
    }
    bubbleOver(ent, text, color = '#dce4f0') {
      if (!ent || !ent.sprite) return;
      const bubble = this.add.text(ent.sprite.x, ent.sprite.y - 24, String(text).slice(0, 50), {
        fontFamily: 'Courier New', resolution: 3, fontSize: '7px', color, backgroundColor: '#10131ecc',
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
      const t = this.add.text(x + (Math.random() * 10 - 5), y, text, {
        fontFamily: 'Courier New', resolution: 3, fontSize: `${size}px`, color, stroke: '#000', strokeThickness: 2,
      }).setOrigin(0.5).setDepth(60).setScale(1.4);
      this.tweens.add({ targets: t, scale: 1, duration: 110 });
      this.tweens.add({ targets: t, y: y - 16, alpha: 0, duration: 800, delay: 110, onComplete: () => t.destroy() });
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

      // exits + feature tiles - use the small physics body, not the fat
      // sprite bounds, so grazing past a staircase doesn't teleport you
      if (!locked && Date.now() > this.exitSuppress) {
        const b = this.player.body;
        const pb = new Phaser.Geom.Rectangle(b.x, b.y, b.width, b.height);
        for (const zone of this.exitZones.concat(this.featureZones || [])) {
          if (Phaser.Geom.Rectangle.Overlaps(zone.getBounds(), pb)) {
            this.requestMove(zone.exitDir);
            break;
          }
        }
      }

      // stalking hostiles / fighters press in (2D)
      const dt = this.game.loop.delta / 1000;
      for (const ent of this.entities.values()) {
        if (ent.kind !== 'mob' || (!ent.stalker && !(ent.data && ent.data.fighting))) continue;
        if (!ent.sprite) continue;
        const dx = this.player.x - ent.sprite.x, dy = this.player.y - ent.sprite.y;
        const d = Math.hypot(dx, dy);
        const stop = ent.data.fighting ? 18 : 28;
        if (d > stop) {
          const speed = ent.data.fighting ? 48 : 30;
          ent.sprite.x += (dx / d) * speed * dt;
          ent.sprite.y += (dy / d) * speed * dt;
          const tex = ent.sprite.texture.key;
          const anim = Math.abs(dx) > Math.abs(dy) ? `${tex}_walks` : (dy > 0 ? `${tex}_walkd` : `${tex}_walku`);
          ent.sprite.setFlipX(Math.abs(dx) > Math.abs(dy) && dx < 0);
          if (!ent.sprite.anims.isPlaying || ent.sprite.anims.currentAnim.key !== anim) ent.sprite.play(anim);
        } else if (ent.sprite.anims.isPlaying) {
          ent.sprite.anims.stop();
        }
      }

      // labels + hp bars follow
      for (const ent of this.entities.values()) {
        if (ent.label && ent.sprite) { ent.label.x = ent.sprite.x; ent.label.y = ent.sprite.y - (ent.data.boss ? 26 : 18); }
        if (ent.fightMark && ent.sprite) { ent.fightMark.x = ent.sprite.x; ent.fightMark.y = ent.sprite.y - 26; }
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
