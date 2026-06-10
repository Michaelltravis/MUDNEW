// Misthollow platformer: Phaser scenes.
// BootScene forges all procedural textures; RoomScene runs one MUD room as a
// platforming chamber. The MUD server stays authoritative: crossing an exit
// sends the real movement command and the room only changes when map_data
// comes back with a new vnum.
(() => {
  const MH = window.MH = window.MH || {};
  const T = 16;
  const GAME_W = 60 * T, GAME_H = 34 * T;
  const OPPOSITE = { north: 'south', south: 'north', east: 'west', west: 'east', up: 'down', down: 'up' };
  // arriving after moving <dir>, which entry point of the new room do we use
  const ARRIVAL = { east: 'west', west: 'east', north: 'south', south: 'north', up: 'up', down: 'down' };

  function mobKeyword(name) {
    const words = String(name || '').toLowerCase().replace(/[^a-z' ]/g, '').split(/\s+/)
      .filter(w => w && !['a', 'an', 'the', 'some', 'of'].includes(w));
    return words[words.length - 1] || 'mob';
  }
  MH.mobKeyword = mobKeyword;

  // ================= Boot =================
  class BootScene extends Phaser.Scene {
    constructor() { super('Boot'); }
    create() {
      const txt = this.add.text(GAME_W / 2, GAME_H / 2, 'Forging the world…', {
        fontFamily: 'Courier New', fontSize: '18px', color: '#e8c168',
      }).setOrigin(0.5);
      this.time.delayedCall(30, () => {
        MH.sprites.generateAll(this);
        MH.tdSprites.generateAll(this);
        txt.destroy();
        if (/[?&]gallery=1/.test(window.location.search)) this.scene.start('Gallery');
        else if (/[?&]view=side/.test(window.location.search)) this.scene.start('Room');
        else this.scene.start('TopRoom');   // Zelda-style top-down is the default
      });
    }
  }

  // ================= Gallery (debug: ?gallery=1) =================
  class GalleryScene extends Phaser.Scene {
    constructor() { super('Gallery'); }
    create() {
      this.cameras.main.setBackgroundColor('#10131e');
      const keys = this.textures.getTextureKeys().filter(k => !['__DEFAULT', '__MISSING', '__WHITE', '__NORMAL'].includes(k)).sort();
      let x = 20, y = 20, rowH = 0;
      for (const key of keys) {
        const img = this.add.image(x, y, key).setOrigin(0, 0);
        const w = Math.max(img.width, 40);
        this.add.text(x, y + img.height + 2, key, { fontFamily: 'Courier New', fontSize: '8px', color: '#7a8094' });
        rowH = Math.max(rowH, img.height + 16);
        x += w + 14;
        if (x > GAME_W - 80) { x = 20; y += rowH; rowH = 0; }
      }
      this.cameras.main.setBounds(0, 0, GAME_W, y + 200);
      this.input.on('wheel', (_p, _o, _dx, dy) => this.cameras.main.scrollY += dy * 0.5);
    }
  }

  // ================= Room =================
  class RoomScene extends Phaser.Scene {
    constructor() {
      super('Room');
      this.layout = null;
      this.entities = new Map();   // key -> {sprite,label,hpbar,data,kind}
      this.target = null;
      this.lastVnum = null;
      this.queuedPayload = null;
    }

    create() {
      this.physics.world.setBounds(0, 0, GAME_W, GAME_H);
      this.cameras.main.setBounds(0, 0, GAME_W, GAME_H);

      this.solids = this.physics.add.staticGroup();
      this.platforms = this.physics.add.staticGroup();
      this.tileLayer = this.add.layer();
      this.bgLayer = this.add.layer().setDepth(-10);
      this.fxLayer = this.add.layer().setDepth(50);

      // player
      this.player = this.physics.add.sprite(GAME_W / 2, GAME_H / 2, 'player_warrior', 'idle0');
      this.player.setSize(12, 26).setOffset(6, 4);
      this.player.setDepth(10);
      this.player.setCollideWorldBounds(true);
      this.solidCollider = this.physics.add.collider(this.player, this.solids);
      this.platCollider = this.physics.add.collider(this.player, this.platforms, null, (pl, plat) =>
        pl.body.velocity.y >= 0 && pl.body.bottom <= plat.body.top + 6 && !this.dropThrough, this);

      this.keys = this.input.keyboard.addKeys({
        left: 'A', right: 'D', up: 'W', down: 'S', jump: 'SPACE',
        left2: 'LEFT', right2: 'RIGHT', up2: 'UP', down2: 'DOWN',
        attack: 'F',
      });
      this.input.keyboard.on('keydown-F', () => this.tryAttack());

      this.climbing = false;
      this.swimming = false;
      this.dead = false;
      this.dropThrough = false;

      // darkness overlay (re-armed per room when flags include 'dark')
      this.darkRT = this.add.renderTexture(0, 0, GAME_W, GAME_H).setOrigin(0, 0).setDepth(40).setVisible(false);
      const lightCanvas = document.createElement('canvas');
      lightCanvas.width = lightCanvas.height = 256;
      const lctx = lightCanvas.getContext('2d');
      const grad = lctx.createRadialGradient(128, 128, 10, 128, 128, 128);
      grad.addColorStop(0, 'rgba(255,255,255,1)');
      grad.addColorStop(1, 'rgba(255,255,255,0)');
      lctx.fillStyle = grad;
      lctx.fillRect(0, 0, 256, 256);
      this.textures.addCanvas('px_light', lightCanvas);

      this.nightTint = this.add.rectangle(0, 0, GAME_W, GAME_H, 0x101830, 0).setOrigin(0, 0).setDepth(42);
      this.weatherEmitter = null;

      // bus wiring
      MH.bus.on('map', payload => this.onMap(payload));
      MH.bus.on('combat.update', payload => this.onCombatUpdate(payload));
      MH.bus.on('combat.hit', e => this.fxHit(e));
      MH.bus.on('combat.miss', e => this.fxMiss(e));
      MH.bus.on('combat.taken', e => this.fxTaken(e));
      MH.bus.on('player.exp', e => this.fxExp(e));
      MH.bus.on('walk.step', dir => this.requestMove(dir));
      MH.bus.on('nav.goto', dir => this.navTo(dir));
      MH.bus.on('combat.cast', () => this.player.anims.play(`${this.playerTex()}_cast`, true));
      MH.bus.on('mob.death', e => this.fxMobDeath(e));
      MH.bus.on('player.death', () => this.fxPlayerDeath());
      MH.bus.on('level.up', () => this.fxLevelUp());
      MH.bus.on('move.blocked', e => this.onMoveBlocked(e));
      MH.bus.on('ui.typing', on => { this.input.keyboard.enabled = !on; });
      MH.bus.on('chat', e => this.fxChatBubble(e));
      MH.bus.on('ambient.candidate', e => this.fxAmbient(e));

      if (MH.state.lastPayload) this.onMap(MH.state.lastPayload);
    }

    playerTex() { return MH.sprites.playerKey(MH.state.player && MH.state.player.char_class); }

    // ---------- room construction ----------
    buildRoom(layout, entryDir) {
      this.layout = layout;
      this.dead = false;
      this.target = null;
      this.autoNav = null;
      MH.bus.emit('target.clear');

      this.tileLayer.removeAll(true);
      this.bgLayer.removeAll(true);
      this.solids.clear(true, true);
      this.platforms.clear(true, true);
      for (const ent of this.entities.values()) this.destroyEntity(ent);
      this.entities.clear();
      if (this.exitZones) this.exitZones.forEach(z => z.destroy());
      this.exitZones = [];
      if (this.doorSprites) this.doorSprites.forEach(d => d.destroy());
      this.doorSprites = [];

      const th = layout.theme;
      const themeDef = MH.THEMES[th];

      // sky gradient
      const sky = this.add.graphics();
      sky.fillGradientStyle(
        Phaser.Display.Color.HexStringToColor(themeDef.sky[0]).color,
        Phaser.Display.Color.HexStringToColor(themeDef.sky[0]).color,
        Phaser.Display.Color.HexStringToColor(themeDef.sky[1]).color,
        Phaser.Display.Color.HexStringToColor(themeDef.sky[1]).color, 1);
      sky.fillRect(0, 0, GAME_W, GAME_H);
      this.bgLayer.add(sky);

      // parallax silhouettes drift against player movement (camera is static)
      this.bgFar = this.add.tileSprite(0, GAME_H - 400, GAME_W, 400, `bg_${th}_far`).setOrigin(0, 0).setAlpha(0.8);
      this.bgNear = this.add.tileSprite(0, GAME_H - 400, GAME_W, 400, `bg_${th}_near`).setOrigin(0, 0).setAlpha(0.9);
      this.bgFar.setTileScale(2, 2);
      this.bgNear.setTileScale(2, 2);
      this.bgLayer.add(this.bgFar);
      this.bgLayer.add(this.bgNear);

      // floating room prose: short fragments of the description, ghosted
      // into the world. pure MUD heritage.
      if (layout.description) {
        const rng = MH.mulberry32(layout.vnum + 99);
        const frags = layout.description.replace(/\n/g, ' ').split(/(?<=[.!?])\s+/)
          .map(s => s.trim()).filter(s => s.length > 15 && s.length <= 70);
        Phaser.Utils.Array.Shuffle(frags);
        frags.slice(0, 3).forEach((frag, i) => {
          const tx = this.add.text(
            80 + rng() * (GAME_W - 360), 60 + i * 90 + rng() * 40, frag,
            { fontFamily: 'Courier New', fontSize: '11px', fontStyle: 'italic', color: '#ffffff' }
          ).setAlpha(0.13).setDepth(-4);
          this.tweens.add({ targets: tx, y: tx.y - 10, duration: 9000 + rng() * 4000, yoyo: true, repeat: -1, ease: 'sine.inOut' });
          this.bgLayer.add(tx);
        });
      }

      // sparse back-wall tiles for indoor-ish themes
      if (['inside', 'dungeon', 'cave', 'default'].includes(th)) {
        const rng = MH.mulberry32(layout.vnum + 7);
        for (let y = 2; y < 28; y += 1) {
          for (let x = 2; x < layout.W - 2; x += 1) {
            if (rng() < 0.92) {
              const img = this.add.image(x * T, y * T, `t_${th}_wall`).setOrigin(0, 0).setAlpha(0.55);
              this.bgLayer.add(img);
            }
          }
        }
      }

      // tiles + bodies (merge horizontal solid runs into single static bodies)
      const { grid, W: GW, H: GH } = layout;
      for (let y = 0; y < GH; y++) {
        let runStart = -1;
        for (let x = 0; x <= GW; x++) {
          const v = x < GW ? grid[y * GW + x] : EMPTY_CELL;
          const cell = x < GW ? v : 0;
          if (cell === MH.CELL.SOLID) {
            if (runStart < 0) runStart = x;
            const isTop = y === 0 || grid[(y - 1) * GW + x] !== MH.CELL.SOLID;
            const img = this.add.image(x * T, y * T, isTop ? `t_${th}_ground` : `t_${th}_fill`).setOrigin(0, 0);
            this.tileLayer.add(img);
          } else {
            if (runStart >= 0) {
              const zone = this.add.zone(runStart * T, y * T, (x - runStart) * T, T).setOrigin(0, 0);
              this.physics.add.existing(zone, true);
              this.solids.add(zone);
              runStart = -1;
            }
            if (x < GW) {
              if (cell === MH.CELL.PLAT) {
                const img = this.add.image(x * T, y * T, `t_${th}_plat`).setOrigin(0, 0);
                this.tileLayer.add(img);
              } else if (cell === MH.CELL.LADDER) {
                const img = this.add.image(x * T, y * T, `t_${th}_ladder`).setOrigin(0, 0);
                this.tileLayer.add(img);
              } else if (cell === MH.CELL.WATER) {
                const spr = this.add.sprite(x * T, y * T, `t_${th}_water`, '0').setOrigin(0, 0).setAlpha(0.85);
                spr.play(`water_${th}`);
                this.tileLayer.add(spr);
              }
            }
          }
        }
      }
      // platform bodies as merged runs
      for (const p of layout.platforms) {
        const zone = this.add.zone(p.x * T, p.y * T, p.w * T, 6).setOrigin(0, 0);
        this.physics.add.existing(zone, true);
        this.platforms.add(zone);
      }

      // props
      for (const prop of layout.props) {
        const img = this.add.image(prop.x * T, prop.y * T, `t_${th}_prop${prop.idx}`).setOrigin(0.25, 1).setDepth(2);
        this.tileLayer.add(img);
      }

      // exits: visuals + sensor zones
      this.buildExits(layout, th);

      // memorials for past deaths in this room
      this.placeGravestones(layout);

      // physics feel
      const grav = layout.lowGravity ? 220 : (layout.isUnderwater ? 120 : 900);
      this.physics.world.gravity.y = grav;

      // place player
      const entry = layout.entries[entryDir] || layout.entries.none;
      this.player.setTexture(this.playerTex(), 'idle0');
      this.player.setPosition(entry.x, entry.y);
      this.player.setVelocity(0, 0);
      this.player.setAlpha(1);
      this.player.clearTint();

      // darkness
      this.darkRT.setVisible(!!layout.dark);

      // entry transition
      this.cameras.main.fadeIn(170, 0, 0, 0);
    }

    buildExits(layout, th) {
      const addZone = (x, y, w, h, dir, mode) => {
        const zone = this.add.zone(x, y, w, h).setOrigin(0, 0);
        this.physics.add.existing(zone, true);
        zone.exitDir = dir;
        zone.exitMode = mode; // 'walk' | 'press-up' | 'press-down'
        this.exitZones.push(zone);
      };
      const doorInfo = dir => (layout.exits[dir] && layout.exits[dir].door) || null;
      // gently bouncing chevron so exits read at a glance
      const chevron = (x, y, glyph, dx = 0, dy = -3) => {
        const ch = this.add.text(x, y, glyph, {
          fontFamily: 'Courier New', fontSize: '12px', color: '#e8c168',
        }).setOrigin(0.5, 1).setDepth(4).setAlpha(0.75);
        this.tweens.add({ targets: ch, x: x + dx, y: y + dy, duration: 700, yoyo: true, repeat: -1, ease: 'sine.inOut' });
        this.tileLayer.add(ch);
      };
      // trailhead signpost when an exit crosses into another zone
      const signpost = (dir, x, y, anchor = 0.5) => {
        const zone = layout.exits[dir] && layout.exits[dir].to_zone;
        if (!zone) return;
        const post = this.add.text(x, y, `→ ${zone}`, {
          fontFamily: 'Courier New', fontSize: '8px', fontStyle: 'italic', color: '#e8c168',
          backgroundColor: '#10131ea8', padding: { x: 3, y: 1 },
        }).setOrigin(anchor, 1).setDepth(3).setAlpha(0.9);
        this.tileLayer.add(post);
      };
      const drawDoorIfClosed = (dir, x, y) => {
        const d = doorInfo(dir);
        if (d && d.state !== 'open') {
          const spr = this.add.image(x, y, `t_${th}_door`).setOrigin(0.5, 1).setDepth(3);
          spr.doorDir = dir;
          this.doorSprites.push(spr);
        }
        return d;
      };

      if (layout.eastGap) {
        const g = layout.eastGap;
        addZone((layout.W - 2) * T, g.y0 * T, 2 * T, (g.y1 - g.y0 + 1) * T, 'east', 'walk');
        drawDoorIfClosed('east', (layout.W - 1.5) * T, (g.y1 + 1) * T);
        signpost('east', (layout.W - 2.5) * T, (g.y0 - 0.5) * T, 1);
        chevron((layout.W - 2.8) * T, (g.y1 + 0.8) * T, '▶', 3, 0);
      }
      if (layout.westGap) {
        const g = layout.westGap;
        addZone(0, g.y0 * T, 2 * T, (g.y1 - g.y0 + 1) * T, 'west', 'walk');
        drawDoorIfClosed('west', 1.5 * T, (g.y1 + 1) * T);
        signpost('west', 2.5 * T, (g.y0 - 0.5) * T, 0);
        chevron(2.8 * T, (g.y1 + 0.8) * T, '◀', -3, 0);
      }
      if (layout.northDoor) {
        const d = layout.northDoor;
        const img = this.add.image(d.x * T, d.y * T, `t_${th}_doorN`).setOrigin(0.5, 1).setDepth(-5);
        this.bgLayer.add(img);
        this.add.existing(img);
        addZone((d.x - 1.2) * T, (d.y - 4) * T, 2.4 * T, 4 * T, 'north', 'press-up');
        drawDoorIfClosed('north', d.x * T, d.y * T);
        const hint = this.add.text(d.x * T, (d.y - 4.6) * T, 'W·north', { fontFamily: 'Courier New', fontSize: '8px', color: '#7a8094' }).setOrigin(0.5, 1).setDepth(3);
        this.tileLayer.add(hint);
        signpost('north', d.x * T, (d.y - 5.4) * T);
        chevron(d.x * T, (d.y - 4.7) * T, '▲');
      }
      if (layout.southDoor) {
        const d = layout.southDoor;
        const img = this.add.image(d.x * T, d.y * T + 4, `t_${th}_hatch`).setOrigin(0.5, 1).setDepth(4);
        this.tileLayer.add(img);
        addZone((d.x - 1.2) * T, (d.y - 3) * T, 2.4 * T, 3 * T, 'south', 'press-down');
        drawDoorIfClosed('south', d.x * T, d.y * T);
        const hint = this.add.text(d.x * T, (d.y - 3.4) * T, 'S·south', { fontFamily: 'Courier New', fontSize: '8px', color: '#7a8094' }).setOrigin(0.5, 1).setDepth(4);
        this.tileLayer.add(hint);
        signpost('south', d.x * T, (d.y - 4.2) * T);
        chevron(d.x * T, (d.y - 3.5) * T, '▼', 0, 3);
      }
      if (layout.ladder) {
        const l = layout.ladder;
        addZone(l.x * T - 4, 0, T + 8, 2.5 * T, 'up', 'walk'); // climbing past the top
        signpost('up', l.x * T + 10, 4.2 * T, 0);
        chevron(l.x * T + T / 2, 3.4 * T, '▲');
      }
      for (const p of (layout.portals || [])) {
        const spr = this.add.sprite(p.x * T, p.y * T, 't_portal', '0').setOrigin(0.5, 1).setDepth(3);
        spr.play('portal_shimmer');
        this.tileLayer.add(spr);
        addZone((p.x - 1.2) * T, (p.y - 3) * T, 2.4 * T, 3 * T, p.name, 'press-up');
        const hint = this.add.text(p.x * T, (p.y - 3.0) * T, `W·${p.name}`, {
          fontFamily: 'Courier New', fontSize: '8px', color: '#b87cf0',
        }).setOrigin(0.5, 1).setDepth(3);
        this.tileLayer.add(hint);
        signpost(p.name, p.x * T, (p.y - 3.8) * T);
      }
      if (layout.trapdoor) {
        const td = layout.trapdoor;
        const img = this.add.image(td.x * T, td.y * T, `t_${th}_trap`).setOrigin(0.5, 1).setDepth(2);
        this.tileLayer.add(img);
        addZone((td.x - 1) * T, (td.y - 2) * T, 2 * T, 2 * T, 'down', 'press-down');
        const hint = this.add.text(td.x * T, (td.y - 2.3) * T, 'S·down', { fontFamily: 'Courier New', fontSize: '8px', color: '#7a8094' }).setOrigin(0.5, 1).setDepth(3);
        this.tileLayer.add(hint);
        signpost('down', td.x * T, (td.y - 3.1) * T);
        chevron(td.x * T, (td.y - 2.4) * T, '▼', 0, 3);
      }
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
        ent.sprite = this.add.image(slot.x, slot.y + 8, MH.sprites.itemKey(spec.data.type)).setDepth(5);
        this.tweens.add({ targets: ent.sprite, y: slot.y + 4, duration: 900, yoyo: true, repeat: -1, ease: 'sine.inOut' });
        ent.sprite.setInteractive({ useHandCursor: true });
        ent.sprite.on('pointerdown', () => MH.sendCommand(`get ${mobKeyword(spec.data.name)}`));
        return ent;
      }

      const tex = spec.kind === 'player' ? MH.sprites.playerKey(spec.data.char_class) : MH.sprites.mobKey(spec.data.name);
      ent.sprite = this.add.sprite(slot.x, slot.y - 16, tex, 'idle0').setDepth(8);
      ent.sprite.play(`${tex}_idle`);
      if (spec.data.boss) ent.sprite.setScale(1.5);
      ent.homeX = slot.x;

      const labelColor = spec.kind === 'player' ? '#6ca8e0' : (spec.data.hostile ? '#e06c6c' : (spec.data.shopkeeper ? '#e8c168' : '#c8ccd8'));
      ent.label = this.add.text(slot.x, slot.y - 50, this.shortName(spec.data.name), {
        fontFamily: 'Courier New', fontSize: '9px', color: labelColor,
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
      ent.sprite.on('pointerover', pointer => {
        MH.bus.emit('mob.tip', { data: ent.data, kind: ent.kind, x: pointer.event.clientX, y: pointer.event.clientY });
      });
      ent.sprite.on('pointermove', pointer => {
        MH.bus.emit('mob.tip', { data: ent.data, kind: ent.kind, x: pointer.event.clientX, y: pointer.event.clientY });
      });
      ent.sprite.on('pointerout', () => MH.bus.emit('mob.tip.hide'));

      // hostile mobs stalk the player (cosmetic — real aggro is server-side);
      // everything else gets a gentle patrol
      if (spec.kind === 'mob' && !spec.data.shopkeeper) {
        if (spec.data.hostile) {
          ent.stalker = true;
        } else {
          ent.patrol = this.tweens.add({
            targets: ent.sprite, x: slot.x + 20, duration: 2200 + (MH.hashStr(key) % 1400),
            yoyo: true, repeat: -1, ease: 'sine.inOut', delay: MH.hashStr(key) % 1000,
            onUpdate: () => { ent.sprite.setFlipX(ent.sprite.x < (ent.prevX || ent.sprite.x)); ent.prevX = ent.sprite.x; },
          });
        }
      }
      return ent;
    }

    updateEntity(ent, data) {
      ent.data = data;
      this.drawHpBar(ent);
      if (this.target && this.target.key === ent.key) MH.bus.emit('target.update', data);
    }

    drawHpBar(ent) {
      if (!ent.hpbar) return;
      ent.hpbar.clear();
      const max = ent.data.maxHp || ent.data.max_hp;
      const hp = ent.data.hp;
      if (!max || hp == null) return;
      const frac = Math.max(0, Math.min(1, hp / max));
      const x = ent.sprite.x - 12, y = ent.sprite.y - 26;
      ent.hpbar.fillStyle(0x000000, 0.7).fillRect(x, y, 24, 3);
      ent.hpbar.fillStyle(frac > 0.5 ? 0x6fd685 : frac > 0.25 ? 0xe8c168 : 0xe06c6c, 1).fillRect(x, y, 24 * frac, 3);
    }

    destroyEntity(ent) {
      if (ent.patrol) ent.patrol.stop();
      ['sprite', 'label', 'hpbar'].forEach(k => { if (ent[k]) ent[k].destroy(); });
    }

    shortName(name) {
      const n = String(name || '');
      return n.length > 22 ? n.slice(0, 21) + '…' : n;
    }

    // ---------- combat ----------
    nearestMob(maxDist = 90) {
      let best = null, bestD = maxDist;
      for (const ent of this.entities.values()) {
        if (ent.kind !== 'mob' || ent.data.shopkeeper) continue;
        const d = Phaser.Math.Distance.Between(this.player.x, this.player.y, ent.sprite.x, ent.sprite.y);
        if (d < bestD) { best = ent; bestD = d; }
      }
      return best;
    }
    tryAttack() {
      if (this.dead || !this.layout) return;
      if (this.layout.peaceful) { MH.bus.emit('flash', 'A calm presence here forbids violence.'); return; }
      const ent = this.target && this.entities.has(this.target.key) ? this.entities.get(this.target.key) : this.nearestMob();
      if (!ent) { MH.bus.emit('flash', 'Nothing within reach to fight.'); return; }
      this.attackEntity(ent);
    }
    attackEntity(ent) {
      this.target = ent;
      MH.bus.emit('target.set', ent.data);
      MH.sendCommand(`kill ${mobKeyword(ent.data.name)}`);
      this.player.setFlipX(ent.sprite.x < this.player.x);
      this.player.anims.play(`${this.playerTex()}_attack`, true);
    }

    findEntityByText(text) {
      const lower = String(text || '').toLowerCase();
      for (const ent of this.entities.values()) {
        if (ent.kind !== 'mob') continue;
        const name = String(ent.data.name || '').toLowerCase();
        if (lower.includes(mobKeyword(name)) || name.includes(lower) || lower.includes(name)) return ent;
      }
      return null;
    }

    // ---------- FX ----------
    // damage tiers follow the server's get_damage_color thresholds
    dmgStyle(dmg) {
      if (dmg == null) return { color: '#ffe080', size: 12, shake: 0 };
      if (dmg <= 4) return { color: '#d8dce8', size: 10, shake: 0 };
      if (dmg <= 12) return { color: '#7ad68a', size: 12, shake: 0 };
      if (dmg <= 24) return { color: '#e8c168', size: 14, shake: 0 };
      if (dmg <= 48) return { color: '#ffd44a', size: 16, shake: 0.002 };
      if (dmg <= 80) return { color: '#ff6a4a', size: 19, shake: 0.004 };
      return { color: '#ff4ae0', size: 23, shake: 0.007 };
    }
    fxHit(e) {
      const ent = this.findEntityByText(e.target) || this.target;
      this.player.anims.play(`${this.playerTex()}_attack`, true);
      if (!ent || !ent.sprite) return;
      this.player.setFlipX(ent.sprite.x < this.player.x);
      ent.sprite.setTintFill(0xffffff);
      this.time.delayedCall(80, () => ent.sprite && ent.sprite.clearTint());
      // knockback nudge away from the player
      const dir = Math.sign(ent.sprite.x - this.player.x) || 1;
      this.tweens.add({ targets: ent.sprite, x: ent.sprite.x + dir * 7, duration: 70, yoyo: true });
      this.spark(ent.sprite.x, ent.sprite.y - 10, 0xffe080);
      const st = this.dmgStyle(e.dmg);
      if (st.shake) this.cameras.main.shake(90, st.shake);
      this.damageNumber(ent.sprite.x, ent.sprite.y - 30, e.dmg != null ? String(e.dmg) : 'hit', st.color, st.size);
    }
    fxMiss(e) {
      const ent = this.findEntityByText(e.target) || this.target;
      this.player.anims.play(`${this.playerTex()}_attack`, true);
      if (ent && ent.sprite) this.damageNumber(ent.sprite.x, ent.sprite.y - 30, 'miss', '#7a8094');
    }
    fxTaken(e) {
      this.player.setTintFill(0xff6060);
      this.time.delayedCall(90, () => this.player.clearTint());
      const st = this.dmgStyle(e && e.dmg);
      this.cameras.main.shake(80, Math.max(0.004, st.shake));
      // knockback away from the attacker if we can find them
      const atk = e && e.from ? this.findEntityByText(e.from) : null;
      const dir = atk && atk.sprite ? Math.sign(this.player.x - atk.sprite.x) || 1 : (this.player.flipX ? 1 : -1);
      if (this.player.body && !this.climbing) this.player.setVelocityX(dir * 90);
      this.damageNumber(this.player.x, this.player.y - 34, e && e.dmg != null ? `-${e.dmg}` : '✦', '#e06c6c', st.size);
    }
    fxExp(e) {
      const t = this.add.text(this.player.x, this.player.y - 44, `+${e.amount} xp`, {
        fontFamily: 'Courier New', fontSize: '12px', color: '#e8c168', stroke: '#000', strokeThickness: 2,
      }).setOrigin(0.5).setDepth(60);
      this.tweens.add({ targets: t, y: t.y - 30, alpha: 0, duration: 1400, ease: 'sine.out', onComplete: () => t.destroy() });
    }
    fxMobDeath(e) {
      const ent = this.findEntityByText(e.name) || this.target;
      if (ent && ent.sprite) {
        ent.sprite.play(`${ent.sprite.texture.key}_death`);
        this.poof(ent.sprite.x, ent.sprite.y);
      }
      if (this.target && ent === this.target) { this.target = null; MH.bus.emit('target.clear'); }
    }
    fxPlayerDeath() {
      this.dead = true;
      this.recordDeath();
      this.player.anims.play(`${this.playerTex()}_death`);
      this.cameras.main.fade(1200, 0, 0, 0, false, (_c, t) => {
        if (t === 1) {
          this.time.delayedCall(600, () => { MH.refreshState(); this.cameras.main.fadeIn(600); this.dead = false; });
        }
      });
      MH.bus.emit('flash', 'You have died. The realm reclaims you…');
    }
    fxLevelUp() {
      const emitter = this.add.particles(this.player.x, this.player.y - 10, 'px_star', {
        speed: { min: 40, max: 140 }, lifespan: 900, quantity: 24, scale: { start: 1.4, end: 0 }, emitting: false,
      }).setDepth(60);
      emitter.explode(24);
      this.time.delayedCall(1200, () => emitter.destroy());
    }
    bubbleOver(ent, text, color = '#dce4f0') {
      if (!ent || !ent.sprite) return;
      const bubble = this.add.text(ent.sprite.x, ent.sprite.y - 56, String(text).slice(0, 56), {
        fontFamily: 'Courier New', fontSize: '9px', color, backgroundColor: '#10131ecc',
        padding: { x: 4, y: 2 }, wordWrap: { width: 160 },
      }).setOrigin(0.5, 1).setDepth(60);
      this.tweens.add({ targets: bubble, y: bubble.y - 8, alpha: 0, delay: 2800, duration: 700, onComplete: () => bubble.destroy() });
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
    // ambient narrative: attribute to a room mob if named, else drift as ghost text
    fxAmbient(e) {
      const line = e.line.trim();
      if (!line || line.length > 110) return;
      if (/\d+\/\d+(hp|mp|mv)/i.test(line) || /^>/.test(line) || /^\[/.test(line)) return;
      const lower = line.toLowerCase();
      for (const ent of this.entities.values()) {
        if (ent.kind !== 'mob') continue;
        const kw = mobKeyword(ent.data.name);
        if (kw.length > 2 && lower.includes(kw)) { this.bubbleOver(ent, line, '#b8c0d4'); return; }
      }
      if (!/^(you hear|a |an |the |somewhere|in the distance|dust|wind|water|shadows)/i.test(line)) return;
      const rng = Math.random();
      const t = this.add.text(120 + rng * (GAME_W - 380), 90 + Math.random() * 160, line, {
        fontFamily: 'Courier New', fontSize: '10px', fontStyle: 'italic', color: '#c8d0e4',
      }).setAlpha(0).setDepth(45);
      this.tweens.add({ targets: t, alpha: 0.4, duration: 900, yoyo: true, hold: 3800, onComplete: () => t.destroy() });
    }
    // client-side death memorials, kept in localStorage
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
      // server-shared memorials win (everyone sees them); local log is the
      // fallback for older servers that don't send the key
      const stones = Array.isArray(layout.gravestones)
        ? layout.gravestones
        : this.deathLog().filter(d => d.vnum === layout.vnum);
      for (const d of stones) {
        const col = 6 + (MH.hashStr(String(d.ts) + (d.name || '')) % (layout.W - 12));
        const x = col * T + T / 2, y = layout.hm[col] * T;
        const g = this.add.image(x, y, 't_grave').setOrigin(0.5, 1).setDepth(2);
        this.tileLayer.add(g);
        const slain = d.killer ? `${d.name}, slain by ${d.killer}` : d.name;
        const label = this.add.text(x, y - 26, `here lies ${slain}`, {
          fontFamily: 'Courier New', fontSize: '8px', fontStyle: 'italic', color: '#8a90a4',
        }).setOrigin(0.5, 1).setAlpha(0.7).setDepth(2);
        this.tileLayer.add(label);
      }
    }
    spark(x, y, color) {
      const emitter = this.add.particles(x, y, 'px_white', {
        speed: { min: 40, max: 120 }, lifespan: 300, quantity: 8, scale: { start: 1, end: 0 }, tint: color, emitting: false,
      }).setDepth(60);
      emitter.explode(8);
      this.time.delayedCall(500, () => emitter.destroy());
    }
    poof(x, y) {
      const emitter = this.add.particles(x, y, 'px_poof', {
        speed: { min: 20, max: 70 }, lifespan: 500, quantity: 12, scale: { start: 1.2, end: 0 }, emitting: false,
      }).setDepth(60);
      emitter.explode(12);
      this.time.delayedCall(700, () => emitter.destroy());
    }
    damageNumber(x, y, text, color, size = 11) {
      const t = this.add.text(x + (Math.random() * 14 - 7), y, text, {
        fontFamily: 'Courier New', fontSize: `${size}px`, color, stroke: '#000', strokeThickness: 2,
      }).setOrigin(0.5).setDepth(60).setScale(1.4);
      this.tweens.add({ targets: t, scale: 1, duration: 110 });
      this.tweens.add({ targets: t, y: y - 24, alpha: 0, duration: 800, delay: 110, onComplete: () => t.destroy() });
    }

    // ---------- movement / exits ----------
    onMoveBlocked(e) {
      const pm = MH.state.pendingMove;
      MH.state.pendingMove = null;
      MH.bus.emit('flash', e.line);
      if (!pm) return;
      // bounce back toward room center
      const push = { east: -160, west: 160, north: 0, south: 0, up: 0, down: 0 }[pm.dir] || 0;
      this.player.setVelocityX(push);
      if (pm.dir === 'east' || pm.dir === 'west') this.player.x += push > 0 ? 24 : -24;
      // closed door? try opening it once
      const door = this.layout && this.layout.exits[pm.dir] && this.layout.exits[pm.dir].door;
      if (door && /closed/i.test(e.line)) MH.sendCommand(`open ${door.name} ${pm.dir}`);
    }

    // compass click / Shift+key: auto-run to the exit feature, then take it
    navTo(dir) {
      const L = this.layout;
      if (!L || this.dead) return;
      if (!Object.prototype.hasOwnProperty.call(L.exits || {}, dir)) {
        MH.bus.emit('flash', `There is no exit ${dir} here.`);
        return;
      }
      let x = null;
      if (dir === 'east') x = (L.W - 3) * T;
      else if (dir === 'west') x = 2.5 * T;
      else if (dir === 'north' && L.northDoor) x = L.northDoor.x * T;
      else if (dir === 'south' && L.southDoor) x = L.southDoor.x * T;
      else if (dir === 'up' && L.ladder) x = L.ladder.x * T + T / 2;
      else if (dir === 'down' && L.trapdoor) x = L.trapdoor.x * T;
      else {
        const p = (L.portals || []).find(pt => pt.name === dir);
        if (p) x = p.x * T;
      }
      if (x == null) { this.requestMove(dir); return; }
      this.autoNav = { dir, x };
    }

    requestMove(dir) {
      const st = MH.state;
      if (st.pendingMove && Date.now() - st.pendingMove.sentAt < 2500) return;
      st.pendingMove = { dir, sentAt: Date.now() };
      MH.sendCommand(dir);
    }

    // per-combat-round vitals push: update entity HP in place, no rebuild
    onCombatUpdate(payload) {
      if (!this.layout || payload.vnum !== this.layout.vnum) return;
      (payload.mobs || []).forEach((mob, i) => {
        const ent = this.entities.get(`mob:${mob.name}:${i}`);
        if (!ent) return;
        this.updateEntity(ent, Object.assign({}, ent.data, mob));
        // a mob actively fighting us becomes the target if we have none
        if (mob.fighting && !this.target) {
          this.target = ent;
          MH.bus.emit('target.set', ent.data);
        }
      });
      (payload.players || []).forEach(p => {
        const ent = this.entities.get(`pl:${p.name}`);
        if (ent) this.updateEntity(ent, Object.assign({}, ent.data, p));
      });
    }

    // ---------- map payload ----------
    onMap(payload) {
      const cur = payload.current_room;
      const player = payload.player;
      if (!player) return;

      // find this room's entry in rooms[] for entity lists
      const roomEntry = (payload.rooms || []).find(r => r.vnum === player.vnum) || { mobs: [], players: [], items: [] };
      const roomData = cur && cur.vnum === player.vnum
        ? Object.assign({}, cur, { doorsByDir: null })
        : { vnum: player.vnum, name: roomEntry.name, description: '', sector: roomEntry.sector, flags: roomEntry.flags || [], exits: {} };

      // when current_room is absent, synthesize exits from the rooms[] direction list
      if (!cur || cur.vnum !== player.vnum) {
        (roomEntry.exits || []).forEach(d => { roomData.exits[d] = { to_room: null, door: (roomEntry.doors || {})[d] || null }; });
      } else {
        // merge live door state from rooms[] (current_room carries door too, but rooms[] refreshes)
        for (const [d, ex] of Object.entries(roomData.exits || {})) {
          if (roomEntry.doors && roomEntry.doors[d]) ex.door = roomEntry.doors[d];
        }
      }

      if (this.lastVnum !== player.vnum) {
        const pm = MH.state.pendingMove;
        const entryDir = pm ? (ARRIVAL[pm.dir] || 'none') : 'none';
        MH.state.pendingMove = null;
        this.lastVnum = player.vnum;
        const layout = MH.generateRoom(roomData);
        this.buildRoom(layout, entryDir);
        MH.bus.emit('room.entered', { room: roomData, zoneName: roomEntry.zoneName });
      }
      this.syncEntities(roomEntry);
      this.applyAtmosphere(payload);
    }

    applyAtmosphere(payload) {
      const period = payload.time && payload.time.period;
      const outdoor = this.layout && !['inside', 'dungeon', 'cave', 'default'].includes(this.layout.theme);
      let alpha = 0, color = 0x101830;
      if (outdoor) {
        if (period === 'night' || period === 'midnight') { alpha = 0.38; }
        else if (period === 'evening' || period === 'dusk') { alpha = 0.22; color = 0x40280f; }
        else if (period === 'dawn' || period === 'morning') { alpha = 0.10; color = 0x402a20; }
      }
      this.nightTint.setFillStyle(color, alpha);

      const precip = payload.weather && payload.weather.precipitation;
      const wantRain = outdoor && precip && precip !== 'none';
      if (wantRain && !this.weatherEmitter) {
        const snow = /snow/i.test(precip);
        this.weatherEmitter = this.add.particles(0, -10, snow ? 'px_bubble' : 'px_rain', {
          x: { min: 0, max: GAME_W }, speedY: snow ? { min: 30, max: 60 } : { min: 280, max: 380 },
          speedX: snow ? { min: -15, max: 15 } : -30, lifespan: 2400, quantity: snow ? 2 : 5, alpha: 0.7,
        }).setDepth(45);
      } else if (!wantRain && this.weatherEmitter) {
        this.weatherEmitter.destroy();
        this.weatherEmitter = null;
      }
      if (this.layout && this.layout.isUnderwater && !this.bubbleEmitter) {
        this.bubbleEmitter = this.add.particles(0, GAME_H, 'px_bubble', {
          x: { min: 0, max: GAME_W }, speedY: { min: -50, max: -20 }, lifespan: 4000, quantity: 1, alpha: 0.5,
        }).setDepth(45);
      } else if (this.layout && !this.layout.isUnderwater && this.bubbleEmitter) {
        this.bubbleEmitter.destroy();
        this.bubbleEmitter = null;
      }
    }

    // ---------- update loop ----------
    update() {
      if (!this.layout || this.dead) return;
      const k = this.keys;
      // gamepad: left stick / dpad move, A jump, X attack, B = up-action, Y = down-action
      const pad = this.input.gamepad && this.input.gamepad.total ? this.input.gamepad.getPad(0) : null;
      let padLeft = false, padRight = false, padUp = false, padDown = false, padJump = false;
      if (pad) {
        const ax = pad.axes.length ? pad.axes[0].getValue() : 0;
        const ay = pad.axes.length > 1 ? pad.axes[1].getValue() : 0;
        padLeft = ax < -0.35 || pad.left;
        padRight = ax > 0.35 || pad.right;
        padUp = ay < -0.5 || pad.up || pad.B;
        padDown = ay > 0.5 || pad.down || pad.Y;
        padJump = pad.A && !this._padAHeld;
        this._padAHeld = pad.A;
        if (pad.X && !this._padXHeld) this.tryAttack();
        this._padXHeld = pad.X;
      }
      const left = k.left.isDown || k.left2.isDown || padLeft;
      const right = k.right.isDown || k.right2.isDown || padRight;
      const up = k.up.isDown || k.up2.isDown || padUp;
      const down = k.down.isDown || k.down2.isDown || padDown;
      const jump = Phaser.Input.Keyboard.JustDown(k.jump) || padJump;
      // edge-detect gamepad up/down for door/hatch interactions
      const padUpJust = padUp && !this._padUpHeld;
      const padDownJust = padDown && !this._padDownHeld;
      this._padUpHeld = padUp;
      this._padDownHeld = padDown;
      const body = this.player.body;
      const tex = this.playerTex();
      const locked = !!MH.state.pendingMove && Date.now() - MH.state.pendingMove.sentAt < 2500;

      // ladder check
      const tileX = Math.floor(this.player.x / T), tileY = Math.floor(this.player.y / T);
      const onLadder = this.layout.ladder && Math.abs(tileX - this.layout.ladder.x) <= 0 &&
        tileY >= 0 && tileY <= this.layout.ladder.bottomY + 1;
      const inWater = this.layout.isUnderwater ||
        (this.cellAt(tileX, tileY) === MH.CELL.WATER || this.cellAt(tileX, tileY + 1) === MH.CELL.WATER);

      if (onLadder && (up || down) && !this.climbing) { this.climbing = true; body.setAllowGravity(false); }
      if (!onLadder && this.climbing) { this.climbing = false; body.setAllowGravity(true); }

      // manual input cancels compass auto-run
      if (this.autoNav && (left || right || up || down || jump)) this.autoNav = null;

      const speed = inWater && !this.layout.isUnderwater ? 80 : 140;
      if (!locked && this.autoNav && !this.climbing) {
        // auto-run toward the chosen exit feature, hopping obstacles
        const dx = this.autoNav.x - this.player.x;
        if (Math.abs(dx) < 10) {
          const dir = this.autoNav.dir;
          this.autoNav = null;
          this.player.setVelocityX(0);
          this.requestMove(dir);
        } else {
          this.player.setVelocityX(Math.sign(dx) * speed);
          this.player.setFlipX(dx < 0);
          const grounded = body.blocked.down || body.touching.down || inWater;
          if ((body.blocked.left || body.blocked.right) && grounded) {
            this.player.setVelocityY(inWater ? -180 : -330);
          }
        }
      } else if (!locked) {
        if (this.climbing) {
          this.player.setVelocityX(left ? -60 : right ? 60 : 0);
          this.player.setVelocityY(up ? -90 : down ? 90 : 0);
          if (up || down) this.player.anims.play(`${tex}_climb`, true);
        } else {
          if (left) { this.player.setVelocityX(-speed); this.player.setFlipX(true); }
          else if (right) { this.player.setVelocityX(speed); this.player.setFlipX(false); }
          else this.player.setVelocityX(0);

          if (this.layout.isUnderwater) {
            if (up || jump) this.player.setVelocityY(-90);
            else if (down) this.player.setVelocityY(90);
          } else if (jump && (body.blocked.down || body.touching.down || inWater)) {
            this.player.setVelocityY(inWater ? -180 : -330);
          }
          // drop through one-way platforms
          this.dropThrough = down && !this.overlapZoneMode('press-down');
          if (this.dropThrough) this.time.delayedCall(200, () => { this.dropThrough = false; });
        }
      } else {
        this.player.setVelocityX(0);
      }

      // animation
      if (!this.player.anims.isPlaying || ['idle', 'walk', 'climb'].some(a => this.player.anims.currentAnim && this.player.anims.currentAnim.key.endsWith(a))) {
        if (this.climbing) { /* handled above */ }
        else if (!body.blocked.down && !inWater) this.player.setFrame('jump');
        else if (left || right || this.autoNav) this.player.anims.play(`${tex}_walk`, true);
        else this.player.anims.play(`${tex}_idle`, true);
      }

      // exit checks
      if (!locked) {
        for (const zone of this.exitZones) {
          if (!Phaser.Geom.Rectangle.Overlaps(zone.getBounds(), this.player.getBounds())) continue;
          if (zone.exitMode === 'walk') {
            if (zone.exitDir === 'up') {
              if (this.climbing && up) this.requestMove('up');
            } else if ((zone.exitDir === 'east' && right) || (zone.exitDir === 'west' && left)) {
              this.requestMove(zone.exitDir);
            }
          } else if (zone.exitMode === 'press-up' && (Phaser.Input.Keyboard.JustDown(k.up) || padUpJust)) {
            this.requestMove(zone.exitDir);
          } else if (zone.exitMode === 'press-down' && (Phaser.Input.Keyboard.JustDown(k.down) || padDownJust)) {
            this.requestMove(zone.exitDir);
          }
        }
      }

      // parallax drift against player movement
      if (this.bgFar) { this.bgFar.tilePositionX = this.player.x * 0.022; }
      if (this.bgNear) { this.bgNear.tilePositionX = this.player.x * 0.055; }

      // hostile mobs walk toward the player; fighting mobs press in close
      const dt = this.game.loop.delta / 1000;
      for (const ent of this.entities.values()) {
        if (!ent.stalker && !(ent.data && ent.data.fighting)) continue;
        if (!ent.sprite || ent.kind !== 'mob') continue;
        const dx = this.player.x - ent.sprite.x;
        const stop = ent.data.fighting ? 26 : 40;
        if (Math.abs(dx) > stop) {
          const speed = ent.data.fighting ? 55 : 32;
          ent.sprite.x += Math.sign(dx) * speed * dt;
          ent.sprite.setFlipX(dx < 0);
          const tex = ent.sprite.texture.key;
          if (!ent.sprite.anims.currentAnim || !ent.sprite.anims.currentAnim.key.endsWith('walk')) ent.sprite.play(`${tex}_walk`, true);
        } else if (ent.data.fighting) {
          // lunge animation while trading blows
          const tex = ent.sprite.texture.key;
          if (!ent.sprite.anims.isPlaying || ent.sprite.anims.currentAnim.key.endsWith('walk')) ent.sprite.play(`${tex}_attack`, true);
          ent.sprite.setFlipX(dx < 0);
        }
        // keep feet on the terrain as they cross the heightmap
        const tileX = Phaser.Math.Clamp(Math.floor(ent.sprite.x / T), 0, this.layout.W - 1);
        ent.sprite.y = (this.layout.hm[tileX] - 1) * T - 16;
      }

      // hp bars + labels follow sprites
      for (const ent of this.entities.values()) {
        if (ent.label && ent.sprite) { ent.label.x = ent.sprite.x; ent.label.y = ent.sprite.y - (ent.data.boss ? 60 : 44); }
        if (ent.hpbar && ent.sprite) this.drawHpBar(ent);
      }

      // darkness
      if (this.layout.dark && this.darkRT.visible) {
        this.darkRT.clear();
        this.darkRT.fill(0x000008, 0.88);
        this.darkRT.erase('px_light', this.player.x - 128, this.player.y - 128);
        for (const prop of this.layout.props) {
          if (this.layout.theme === 'dungeon' && prop.idx === 0) {
            this.darkRT.erase('px_light', prop.x * T - 110, prop.y * T - 140);
          }
        }
      }
    }

    cellAt(x, y) {
      if (!this.layout || x < 0 || y < 0 || x >= this.layout.W || y >= this.layout.H) return MH.CELL.SOLID;
      return this.layout.grid[y * this.layout.W + x];
    }
    overlapZoneMode(mode) {
      return this.exitZones.some(z => z.exitMode === mode && Phaser.Geom.Rectangle.Overlaps(z.getBounds(), this.player.getBounds()));
    }
  }

  const EMPTY_CELL = 0;

  MH.boot = function boot() {
    MH.game = new Phaser.Game({
      type: Phaser.AUTO,
      parent: 'game-root',
      width: GAME_W,
      height: GAME_H,
      pixelArt: true,
      backgroundColor: '#0b0c10',
      physics: { default: 'arcade', arcade: { gravity: { y: 900 }, debug: false } },
      input: { gamepad: true },
      scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH },
      scene: [BootScene, GalleryScene, RoomScene, MH.TopRoomScene],
    });
  };
})();
