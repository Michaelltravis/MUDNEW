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
  function drawNeighbour(scene, room, ox, oy, dir) {
    const atlasExits = room.exits || {};
    const exits = {}; for (const d of Object.keys(atlasExits)) exits[d] = { to_room: atlasExits[d] };
    const layout = MH.generateRoomTopDown({ vnum: room.vnum, name: room.name, sector: room.sector, exits, flags: [] });
    const { W, H, T, grid } = layout;
    const { BLOCK, WATER } = MH.TD || { BLOCK: 1, WATER: 2 };
    const pal = palette(room);
    const g = scene.add.graphics().setDepth(-9);
    const rng = MH.mulberry32 ? MH.mulberry32((room.vnum * 7919) >>> 0) : Math.random;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const c = grid[y * W + x];
      const col = c === BLOCK ? pal.border : c === WATER ? pal.water : (rng() < 0.5 ? pal.floor : pal.f2);
      g.fillStyle(col, 1); g.fillRect(ox + x * T, oy + y * T, T, T);
    }
    // distance haze: the next room is seen, not visited
    g.fillStyle(0x06080c, 0.42); g.fillRect(ox, oy, W * T, H * T);
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
          const img = scene.add.image(ox, oy, key).setOrigin(0, 0).setDisplaySize(W * T, H * T).setDepth(-8.5).setTint(0x9aa0b4);
          scene.bgLayer.add(img);
          g.setVisible(false);
          label.setDepth(-8).setAlpha(0.85);
        } catch (e) { console.warn('peek paint', room.vnum, e); }
      });
      pumpQueue(scene);
    }
    const label = scene.add.text(ox + W * T / 2, oy + H * T / 2, room.name || '', {
      fontFamily: 'sans-serif', fontSize: '7px', color: '#d8d0c0', backgroundColor: 'rgba(6,8,12,0.55)', padding: { x: 3, y: 1 },
    }).setOrigin(0.5).setAlpha(0.8).setDepth(-8);
    scene.bgLayer.add(label);
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
    setTimeout(step, 250);
  }

  // called from buildRoom once the real room is painted
  function render(scene, layout) {
    const cur = layout && layout.vnum;
    if (!cur) return;
    scene._peekQueue = [];                       // drop neighbours queued for the room we left
    for (const k of (scene._peekKeys || [])) {   // and free their canvases, except the one we now stand in
      if (k !== `paint_${cur}` && scene.textures.exists(k)) { try { scene.textures.remove(k); } catch (_) {} }
    }
    scene._peekKeys = [];
    loadAtlas().then(a => {
      if (!scene.layout || scene.layout.vnum !== cur) return;   // moved on while the atlas loaded
      const here = a.rooms[cur]; if (!here) return;
      for (const [dir, vnum] of Object.entries(here.exits || {})) {
        const off = OFF[dir]; if (!off) continue;
        const room = a.rooms[vnum]; if (!room) continue;
        try { drawNeighbour(scene, room, off[0] * scene.pxW, off[1] * scene.pxH, dir); } catch (e) { console.warn('peek', vnum, e); }
      }
    });
  }
  MH.worldPeek = { render, loadAtlas };
})();
