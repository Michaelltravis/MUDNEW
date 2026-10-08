// Misthollow: continuous-world step 1 — neighbour peek.
// The MUD room graph stays authoritative (one room = one screen of play), but
// the rooms behind each exit are pre-rendered at their offsets as dimmed,
// cheap ground so the camera (which now follows the player) sees the next
// space through the opening instead of a black void. Layouts come from the
// same deterministic generator the real room uses, so what you glimpse is
// what you get when you walk through.
(() => {
  const MH = window.MH = window.MH || {};
  const OFF = { north: [0, -1], south: [0, 1], east: [1, 0], west: [-1, 0] };
  let atlas = null, atlasPromise = null;

  function loadAtlas() {
    if (atlasPromise) return atlasPromise;
    atlasPromise = fetch(MH.urls && MH.urls.state ? '/atlas' : '/atlas').then(r => r.json()).then(a => {
      atlas = { rooms: {}, zones: {} };
      for (const r of a.rooms || []) atlas.rooms[r.vnum] = r;
      for (const z of a.zones || []) atlas.zones[z.id] = z;
      return atlas;
    }).catch(() => (atlas = { rooms: {}, zones: {} }));
    return atlasPromise;
  }

  // flat colours for a neighbour cell grid from the zone theme / sector palette
  function palette(room) {
    const zt0 = MH.ZONE_THEMES && MH.zoneThemeKey ? MH.ZONE_THEMES[MH.zoneThemeKey(room.zone)] : null;
    const sector = MH.themeForSector ? MH.themeForSector(room.sector || 'default') : 'default';
    const zt = MH.roomPalette ? MH.roomPalette(zt0, sector) : zt0;
    const hex = c => (typeof c === 'string' && c[0] === '#') ? parseInt(c.slice(1), 16) : (typeof c === 'number' ? c : 0x50463c);
    return {
      floor: hex(zt && zt.floor), f2: hex(zt && (zt.f2 || zt.floor)),
      border: hex(zt && (zt.borderCol || '#2a2420')), water: hex(zt && (zt.water || '#2b4b6a')),
    };
  }

  // draw one neighbour room's layout as flat cells into bgLayer at (ox, oy)
  function drawNeighbour(scene, room, ox, oy, dist) {
    const atlasExits = room.exits || {};
    const exits = {}; for (const d of Object.keys(atlasExits)) exits[d] = { to_room: atlasExits[d] };
    // same inputs as the live build (zone → theme + props, description →
    // furniture, flags → darkness), so the peeked room IS the room you enter
    const layout = MH.generateRoomTopDown({ vnum: room.vnum, name: room.name, sector: room.sector, exits,
      flags: room.flags || [], description: room.description || '', zone: room.zone });
    const { W, H, T, grid } = layout;
    const { BLOCK, WATER } = MH.TD || { BLOCK: 1, WATER: 2 };
    const pal = palette(room);
    (scene._peekOffsets = scene._peekOffsets || {})[room.vnum] = { ox, oy, layout };   // for far entities
    // adjacent rooms are the same ground you are standing on: no tint, no seam;
    // only the outer ring recedes into haze
    const HAZE = dist > 1 ? 0xc4c8d4 : 0xffffff;
    const hazeTween = (obj) => { if (dist > 1) scene.tweens.addCounter({ from: 0, to: 1, duration: 900, delay: 700, onUpdate: t => { const v = t.getValue(); const c = Math.round(0xff - (0xff - 0xc4) * v), c2 = Math.round(0xff - (0xff - 0xc8) * v), c3 = Math.round(0xff - (0xff - 0xd4) * v); if (obj.active) obj.setTint((c << 16) | (c2 << 8) | c3); } }); };
    // walls, props and furniture: a cached static snapshot is parked at the
    // offset at once; an unvisited room is pre-rendered in the deferred queue
    const parkStatic = (rt, bright) => {
      if (!rt || !rt.active) return;
      rt.setPosition(ox, oy).setVisible(true);
      if (bright) { rt.setTint(0xffffff); hazeTween(rt); } else rt.setTint(HAZE);
    };
    const queueStatic = () => {
      const cached = scene.staticRT ? scene.staticRT(room.vnum) : null;
      if (cached) { parkStatic(cached, scene._justLeft === room.vnum); return; }
      if (!scene.prerenderStatic) return;
      const curVnum0 = scene.layout && scene.layout.vnum;
      scene._peekQueue = scene._peekQueue || [];
      scene._peekQueue.push(() => {   // after this room's ground paint, which was queued first
        if (!scene.layout || scene.layout.vnum !== curVnum0) return;
        try { parkStatic(scene.prerenderStatic(layout), false); } catch (e) { console.warn('peek static', room.vnum, e); }
      });
      pumpQueue(scene);
    };
    // a painting of this room already in the texture cache (the room we just
    // left, or one painted on a previous visit) is used at once: no flat flash
    const ready = `paint_${room.vnum}`;
    if (scene.textures.exists(ready)) {
      const img = scene.add.image(ox, oy, ready).setOrigin(0, 0).setDisplaySize(W * T, H * T).setDepth(-8.5);
      // the room just left stays at full brightness through the crossing and
      // only then settles into distance haze, so leaving never reads as a cut
      if (ready === scene._prevPaintKey) { img.setTint(0xffffff); hazeTween(img); }
      else img.setTint(HAZE);
      scene.bgLayer.add(img);
      (scene._peekKeys = scene._peekKeys || []).push(ready);
      queueStatic();
      return img;
    }
    const g = scene.add.graphics().setDepth(-9);
    const rng = MH.mulberry32 ? MH.mulberry32((room.vnum * 7919) >>> 0) : Math.random;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const c = grid[y * W + x];
      const col = c === BLOCK ? pal.border : c === WATER ? pal.water : (rng() < 0.5 ? pal.floor : pal.f2);
      g.fillStyle(col, 1); g.fillRect(ox + x * T, oy + y * T, T, T);
    }
    // distance haze: the next room is seen, not visited
    if (dist > 1) { g.fillStyle(0x06080c, 0.22); g.fillRect(ox, oy, W * T, H * T); }
    scene.bgLayer.add(g);
    // step 2: the real painterly ground, deferred so the room you are in
    // renders first; one neighbour per tick, dropped if you have moved on
    const curVnum = scene.layout && scene.layout.vnum;
    if (MH.painter && MH.painter.enabled && curVnum) {
      scene._peekQueue = scene._peekQueue || [];
      scene._peekQueue.push(() => {
        if (!scene.layout || scene.layout.vnum !== curVnum || !scene.bgLayer) return;
        try {
          const key = MH.painter.paint(scene, layout, layout.theme);
          if (!key) return;
          (scene._peekKeys = scene._peekKeys || []).push(key);
          const img = scene.add.image(ox, oy, key).setOrigin(0, 0).setDisplaySize(W * T, H * T).setDepth(-8.5).setTint(HAZE);
          scene.bgLayer.add(img);
          g.setVisible(false);
          label.setDepth(-8).setAlpha(0.85);
        } catch (e) { console.warn('peek paint', room.vnum, e); }
      });
      pumpQueue(scene);
    }
    // no name label: the critic read it as a placeholder; the HUD names the room on arrival
    const label = { setDepth() { return this; }, setAlpha() { return this; } };
    queueStatic();
    return g;
  }

  function pumpQueue(scene) {
    if (scene._peekPumping) return;
    scene._peekPumping = true;
    const step = () => {
      const job = scene._peekQueue && scene._peekQueue.shift();
      if (!job) { scene._peekPumping = false; return; }
      try { job(); } catch (_) {}
      setTimeout(step, 120);
    };
    setTimeout(step, 60);
  }

  // called from buildRoom once the real room is painted: stitched-zone step 1.
  // Every room of the zone within RADIUS map cells of the current one is drawn
  // at its atlas offset (same z level), nearest first, so the world reads as
  // one map: the destination is visible well before arrival and an edge with no
  // exit still shows the room that sits beyond it rather than void.
  const RADIUS = 2;
  function render(scene, layout) {
    const cur = layout && layout.vnum;
    if (!cur) return;
    scene._peekQueue = [];                       // drop neighbours queued for the room we left
    for (const k of (scene._peekKeys || [])) {   // and free their canvases, except the one we now stand in
      if (k !== `paint_${cur}` && k !== scene._prevPaintKey && k !== scene._lastPaintKey && scene.textures.exists(k)) { try { scene.textures.remove(k); } catch (_) {} }
    }
    scene._peekKeys = [];
    { const mine = scene.staticRT && scene.staticRT(cur); if (mine) mine.setVisible(false); }
    loadAtlas().then(a => {
      if (!scene.layout || scene.layout.vnum !== cur) return;   // moved on while the atlas loaded
      const here = a.rooms[cur]; if (!here) return;
      const placed = [];
      for (const room of Object.values(a.rooms)) {
        if (room.vnum === cur || room.zone !== here.zone || room.z !== here.z) continue;
        const dx = room.x - here.x, dy = room.y - here.y;
        if (Math.abs(dx) > RADIUS || Math.abs(dy) > RADIUS) continue;
        placed.push({ room, dx, dy, d: Math.abs(dx) + Math.abs(dy) });
      }
      // direct neighbours by exit always count, even when the atlas coordinate
      // solver had to slide them (collisions): they are drawn by exit direction
      for (const [dir, vnum] of Object.entries(here.exits || {})) {
        const off = OFF[dir]; const room = a.rooms[vnum];
        if (!off || !room || placed.some(p => p.room.vnum === vnum)) continue;
        placed.push({ room, dx: off[0], dy: off[1], d: 1 });
      }
      placed.sort((p, q) => p.d - q.d);
      // static snapshots: keep the ones in range (and ours, hidden under the
      // live room), free the rest; every kept one is re-parked below
      if (scene.pruneStaticRTs) {
        const keep = new Set(placed.map(p => p.room.vnum)); keep.add(cur);
        scene.pruneStaticRTs(keep);
        const mine = scene.staticRT(cur); if (mine) mine.setVisible(false);
      }
      // the camera may roam over everything that is drawn
      try {
        let x0 = 0, y0 = 0, x1 = scene.pxW, y1 = scene.pxH;
        for (const p of placed) { x0 = Math.min(x0, p.dx * scene.pxW); y0 = Math.min(y0, p.dy * scene.pxH); x1 = Math.max(x1, (p.dx + 1) * scene.pxW); y1 = Math.max(y1, (p.dy + 1) * scene.pxH); }
        scene.cameras.main.setBounds(x0, y0, x1 - x0, y1 - y0);
      } catch (_) {}
      const seen = new Set();
      for (const p of placed) {
        const key = `${p.dx},${p.dy}`; if (seen.has(key)) continue; seen.add(key);
        try { drawNeighbour(scene, p.room, p.dx * scene.pxW, p.dy * scene.pxH, p.d); } catch (e) { console.warn('peek', p.room.vnum, e); }
      }
      scene._justLeft = null;
      if (scene.syncFarEntities) { try { scene.syncFarEntities(); } catch (e) { console.warn('far entities', e); } }
    });
  }
  MH.worldPeek = { render, loadAtlas };
})();
