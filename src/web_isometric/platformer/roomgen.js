// Misthollow: room vnum -> level layout. Two generators share this file:
//   generateRoom        - legacy side-view platformer chamber (?view=side)
//   generateRoomTopDown - Zelda-style top-down screen (the default view)
// Misthollow platformer: room vnum -> platforming chamber layout.
// Pure and deterministic: the same room always generates the same level.
// Side-view exit mapping:
//   east/west -> gaps in the right/left walls at floor level
//   north     -> background arched doorway (press W while overlapping)
//   south     -> foreground floor hatch (press S while overlapping)
//   up        -> ladder to an opening in the ceiling
//   down      -> grated trapdoor in the floor (press S on it)
(() => {
  const MH = window.MH = window.MH || {};
  const W = 60, H = 34, T = 16;

  const EMPTY = 0, SOLID = 1, PLAT = 2, LADDER = 3, WATER = 4;
  MH.CELL = { EMPTY, SOLID, PLAT, LADDER, WATER };

  function smoothHeightmap(rng, base, amp, step) {
    const hm = new Array(W);
    let y = base;
    for (let x = 0; x < W; x++) {
      if (x % step === 0 && x > 0) {
        y += Math.round((rng() - 0.5) * 2 * amp);
        y = Math.max(base - amp - 1, Math.min(base + 2, y));
      }
      hm[x] = y;
    }
    // flatten the outermost columns so wall exits line up with the floor
    for (let x = 0; x < 6; x++) { hm[x] = hm[6]; hm[W - 1 - x] = hm[W - 7]; }
    return hm;
  }

  MH.generateRoom = function generateRoom(roomData) {
    const vnum = Number(roomData.vnum) || 0;
    const sector = MH.themeForSector(roomData.sector || 'default');
    const rng = MH.mulberry32((vnum * 2654435761) >>> 0);
    const exits = roomData.exits || {};
    const has = dir => Object.prototype.hasOwnProperty.call(exits, dir);
    const flags = roomData.flags || [];

    const theme = sector;
    const grid = new Uint8Array(W * H);
    const at = (x, y) => grid[y * W + x];
    const set = (x, y, v) => { if (x >= 0 && x < W && y >= 0 && y < H) grid[y * W + x] = v; };

    // --- floor heightmap by terrain feel ---
    let base = 28, amp = 0, step = 6;
    if (sector === 'field' || sector === 'forest' || sector === 'swamp') { amp = 2; step = 7; }
    else if (sector === 'hills') { amp = 3; step = 6; }
    else if (sector === 'mountain') { amp = 4; step = 5; }
    const hm = smoothHeightmap(rng, base, amp, step);

    for (let x = 0; x < W; x++) {
      for (let y = hm[x]; y < H; y++) set(x, y, SOLID);
    }

    // --- water pool for watery sectors ---
    const isUnderwater = sector === 'underwater';
    let pool = null;
    if (!isUnderwater && (sector === 'water_swim' || sector === 'water_noswim' || sector === 'swamp')) {
      const px0 = 20 + Math.floor(rng() * 8);
      const px1 = px0 + 12 + Math.floor(rng() * 8);
      pool = { x0: px0, x1: px1 };
      for (let x = px0; x <= px1; x++) {
        const top = hm[x];
        for (let y = top; y < Math.min(H, top + 4); y++) set(x, y, WATER);
        for (let y = top + 4; y < H; y++) set(x, y, SOLID);
      }
    }
    if (isUnderwater) {
      for (let x = 0; x < W; x++) for (let y = 2; y < hm[x]; y++) if (at(x, y) === EMPTY) set(x, y, WATER);
    }

    // --- ceiling ---
    for (let x = 0; x < W; x++) { set(x, 0, SOLID); set(x, 1, SOLID); }

    // --- side walls with exit gaps ---
    const gapFor = x => {
      const fy = hm[x];
      return { y0: fy - 5, y1: fy - 1 };
    };
    const eastGap = has('east') ? gapFor(W - 3) : null;
    const westGap = has('west') ? gapFor(2) : null;
    for (let y = 2; y < H; y++) {
      if (!westGap || y < westGap.y0 || y > westGap.y1) { set(0, y, SOLID); set(1, y, SOLID); }
      if (!eastGap || y < eastGap.y0 || y > eastGap.y1) { set(W - 1, y, SOLID); set(W - 2, y, SOLID); }
    }
    // keep gap floors solid
    if (westGap) for (let x = 0; x < 2; x++) for (let y = hm[2]; y < H; y++) set(x, y, SOLID);
    if (eastGap) for (let x = W - 2; x < W; x++) for (let y = hm[W - 3]; y < H; y++) set(x, y, SOLID);

    // --- up exit: ladder + ceiling opening ---
    let ladder = null;
    if (has('up')) {
      const lx = 40 + Math.floor(rng() * 8);
      set(lx, 0, EMPTY); set(lx, 1, EMPTY); set(lx + 1, 0, EMPTY); set(lx + 1, 1, EMPTY);
      for (let y = 2; y < hm[lx]; y++) set(lx, y, LADDER);
      ladder = { x: lx, topY: 0, bottomY: hm[lx] - 1 };
    }

    // --- down exit: trapdoor in floor ---
    let trapdoor = null;
    if (has('down')) {
      let tx = 14 + Math.floor(rng() * 10);
      if (pool && tx >= pool.x0 - 2 && tx <= pool.x1 + 2) tx = pool.x1 + 4;
      trapdoor = { x: tx, y: hm[tx] };
    }

    // --- north / south background-foreground doors ---
    const doorAt = frac => {
      let dx = Math.floor(W * frac);
      if (pool && dx >= pool.x0 - 1 && dx <= pool.x1 + 1) dx = pool.x0 - 4;
      return { x: dx, y: hm[dx] };
    };
    const northDoor = has('north') ? doorAt(0.62) : null;
    const southDoor = has('south') ? doorAt(0.38) : null;

    // non-cardinal exits (gate/arch/portal/...) become shimmering portals
    const CARDINALS = ['north', 'south', 'east', 'west', 'up', 'down'];
    const portals = [];
    const portalNames = Object.keys(exits).filter(d => !CARDINALS.includes(d));
    portalNames.forEach((name, i) => {
      const spot = doorAt(0.25 + (i * 0.5) / Math.max(1, portalNames.length));
      // nudge off the cardinal doors
      let px = spot.x;
      if (southDoor && Math.abs(px - southDoor.x) < 4) px += 5;
      if (northDoor && Math.abs(px - northDoor.x) < 4) px -= 5;
      px = Math.max(5, Math.min(W - 6, px));
      portals.push({ name, x: px, y: hm[px] });
    });

    // --- one-way platforms in the air band ---
    const platforms = [];
    const nPlats = 2 + Math.floor(rng() * 3);
    for (let i = 0; i < nPlats; i++) {
      const pw = 4 + Math.floor(rng() * 5);
      const px = 6 + Math.floor(rng() * (W - 14 - pw));
      const py = 15 + Math.floor(rng() * 9);
      // skip if it would sit inside terrain or block the ladder column
      if (py >= hm[px] - 2 || py >= hm[px + pw] - 2) continue;
      if (ladder && px <= ladder.x + 1 && px + pw >= ladder.x - 1) continue;
      let clear = true;
      for (let x = px; x < px + pw; x++) if (at(x, py) !== EMPTY && at(x, py) !== WATER) { clear = false; break; }
      if (!clear) continue;
      for (let x = px; x < px + pw; x++) set(x, py, PLAT);
      platforms.push({ x: px, y: py, w: pw });
    }

    // --- props on the floor ---
    const props = [];
    const nProps = 2 + Math.floor(rng() * 4);
    for (let i = 0; i < nProps; i++) {
      let px = 5 + Math.floor(rng() * (W - 10));
      if (pool && px >= pool.x0 - 1 && px <= pool.x1 + 1) continue;
      if (northDoor && Math.abs(px - northDoor.x) < 3) continue;
      if (southDoor && Math.abs(px - southDoor.x) < 3) continue;
      if (trapdoor && Math.abs(px - trapdoor.x) < 3) continue;
      props.push({ idx: Math.floor(rng() * 3), x: px, y: hm[px] });
    }

    // --- deterministic spawn slots along the floor ---
    const spawnSlots = [];
    for (let i = 0; i < 8; i++) {
      let sx = 8 + Math.floor(((i + 0.5) / 8) * (W - 16));
      if (pool && sx >= pool.x0 && sx <= pool.x1) sx = pool.x0 - 2 - (i % 3);
      spawnSlots.push({ x: sx * T + T / 2, y: (hm[sx] - 1) * T });
    }

    // --- entry points: where the player appears arriving FROM a direction ---
    const floorPx = x => ({ x: x * T + T / 2, y: (hm[x] - 2) * T });
    const entries = {
      west: floorPx(4),                 // came in heading east? no: entered THROUGH west wall
      east: floorPx(W - 5),
      north: northDoor ? floorPx(northDoor.x) : floorPx(Math.floor(W / 2)),
      south: southDoor ? floorPx(southDoor.x) : floorPx(Math.floor(W / 2)),
      up: trapdoor ? floorPx(trapdoor.x) : floorPx(Math.floor(W / 2)),     // arrived going up => appear at trapdoor
      down: ladder ? floorPx(ladder.x) : floorPx(Math.floor(W / 2)),      // arrived going down => appear at ladder top area
      none: floorPx(Math.floor(W / 2)),
    };

    return {
      vnum, theme, sector, flags,
      description: roomData.description || '',
      gravestones: roomData.gravestones,   // server-shared memorials, if provided
      W, H, T,
      grid, hm,
      pool, isUnderwater,
      lowGravity: sector === 'flying',
      dark: flags.includes('dark'),
      peaceful: flags.includes('peaceful'),
      eastGap, westGap, ladder, trapdoor, northDoor, southDoor, portals,
      platforms, props, spawnSlots, entries,
      exits,
      pxW: W * T, pxH: H * T,
    };
  };
})();

// ===================== Zelda-style top-down generator =====================
// One MUD room = one screen. The four cardinal exits are gaps in the border
// ring; up/down are staircase tiles; named passages are portal tiles.
(() => {
  const MH = window.MH = window.MH || {};
  const W = 30, H = 17, T = 16;
  const FLOOR = 0, BLOCK = 1, WATER = 4;
  MH.TD = { W, H, T, FLOOR, BLOCK, WATER };

  function floodReachable(grid, sx, sy) {
    const seen = new Uint8Array(W * H);
    const q = [[sx, sy]];
    seen[sy * W + sx] = 1;
    while (q.length) {
      const [x, y] = q.pop();
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nx = x + dx, ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
        const i = ny * W + nx;
        if (seen[i] || grid[i] === BLOCK || grid[i] === WATER) continue;
        seen[i] = 1;
        q.push([nx, ny]);
      }
    }
    return seen;
  }

  MH.generateRoomTopDown = function generateRoomTopDown(roomData) {
    const vnum = Number(roomData.vnum) || 0;
    const sector = MH.themeForSector(roomData.sector || 'default');
    const rng = MH.mulberry32(((vnum * 2654435761) ^ 0x5eada) >>> 0);
    const exits = roomData.exits || {};
    const has = dir => Object.prototype.hasOwnProperty.call(exits, dir);
    const flags = roomData.flags || [];
    const swim = sector === 'underwater' || sector === 'water_swim';

    const grid = new Uint8Array(W * H); // FLOOR
    const at = (x, y) => grid[y * W + x];
    const set = (x, y, v) => { if (x >= 0 && y >= 0 && x < W && y < H) grid[y * W + x] = v; };

    // border ring with edge gaps where exits exist
    for (let x = 0; x < W; x++) { set(x, 0, BLOCK); set(x, H - 1, BLOCK); }
    for (let y = 0; y < H; y++) { set(0, y, BLOCK); set(W - 1, y, BLOCK); }
    const midX = Math.floor(W / 2), midY = Math.floor(H / 2);
    const gaps = {};
    if (has('north')) { gaps.north = { x0: midX - 2, x1: midX + 2 }; for (let x = midX - 2; x <= midX + 2; x++) set(x, 0, FLOOR); }
    if (has('south')) { gaps.south = { x0: midX - 2, x1: midX + 2 }; for (let x = midX - 2; x <= midX + 2; x++) set(x, H - 1, FLOOR); }
    if (has('west'))  { gaps.west  = { y0: midY - 2, y1: midY + 2 }; for (let y = midY - 2; y <= midY + 2; y++) set(0, y, FLOOR); }
    if (has('east'))  { gaps.east  = { y0: midY - 2, y1: midY + 2 }; for (let y = midY - 2; y <= midY + 2; y++) set(W - 1, y, FLOOR); }

    // staircase / portal feature tiles
    const stairsUp = has('up') ? { x: W - 8, y: 4 } : null;
    const stairsDown = has('down') ? { x: 7, y: 4 } : null;
    const CARDINALS = ['north', 'south', 'east', 'west', 'up', 'down'];
    const portalNames = Object.keys(exits).filter(d => !CARDINALS.includes(d));
    const portals = portalNames.map((name, i) => ({
      name, x: 9 + ((i * 7) % (W - 18)), y: H - 5,
    }));

    // water pond blocks passage in non-swimmable water rooms
    if (sector === 'water_noswim') {
      const cx = midX + Math.floor(rng() * 4) - 2, cy = midY + Math.floor(rng() * 2) - 1;
      for (let y = cy - 2; y <= cy + 2; y++) {
        for (let x = cx - 3; x <= cx + 3; x++) {
          if (x > 1 && x < W - 2 && y > 1 && y < H - 2) set(x, y, WATER);
        }
      }
    }

    // points of interest that must stay mutually reachable
    const pois = [];
    if (gaps.north) pois.push([midX, 1]);
    if (gaps.south) pois.push([midX, H - 2]);
    if (gaps.west) pois.push([1, midY]);
    if (gaps.east) pois.push([W - 2, midY]);
    if (stairsUp) pois.push([stairsUp.x, stairsUp.y]);
    if (stairsDown) pois.push([stairsDown.x, stairsDown.y]);
    portals.forEach(p => pois.push([p.x, p.y]));
    pois.push([midX, midY]);

    // entry tiles are POIs too: the player materializes there, so nothing
    // may block them and they must stay reachable
    const px = (x, y) => ({ x: x * T + T / 2, y: y * T + T / 2 });
    const entries = {
      north: px(midX, 1.6),
      south: px(midX, H - 2.6),
      west: px(1.6, midY),
      east: px(W - 2.6, midY),
      up: stairsDown ? px(stairsDown.x + 1.4, stairsDown.y) : px(midX, midY),
      down: stairsUp ? px(stairsUp.x - 1.4, stairsUp.y) : px(midX, midY),
      none: px(midX, midY),
    };
    for (const p of portals) entries[p.name] = px(midX, midY);
    for (const e of Object.values(entries)) {
      pois.push([Math.floor(e.x / T), Math.floor(e.y / T)]);
    }

    // clear POI tiles in case the pond landed on one
    pois.forEach(([x, y]) => { if (at(x, y) === WATER) set(x, y, FLOOR); });

    const allReachable = () => {
      const seen = floodReachable(grid, midX, midY);
      return pois.every(([x, y]) => seen[y * W + x]);
    };
    if (!allReachable()) {
      // pond cut something off: drain it
      for (let i = 0; i < grid.length; i++) if (grid[i] === WATER) grid[i] = FLOOR;
    }

    // scattered obstacles, kept only when they don't break connectivity
    const obstacles = [];
    const tries = 8 + Math.floor(rng() * 8);
    for (let i = 0; i < tries; i++) {
      const big = rng() < 0.35;
      const ox = 2 + Math.floor(rng() * (W - 5));
      const oy = 2 + Math.floor(rng() * (H - 5));
      const cells = [];
      for (let dy = 0; dy < (big ? 2 : 1); dy++) {
        for (let dx = 0; dx < (big ? 2 : 1); dx++) cells.push([ox + dx, oy + dy]);
      }
      // skip near feature tiles and gap corridors
      const nearPoi = pois.some(([px, py]) => cells.some(([cx, cy]) => Math.abs(cx - px) <= 1 && Math.abs(cy - py) <= 1));
      // keep the straight lanes to each exit clear: holding a direction
      // key must always carry you from the center to the gap (Zelda feel)
      const inLane = cells.some(([cx, cy]) =>
        ((gaps.east || gaps.west) && Math.abs(cy - midY) <= 1) ||
        ((gaps.north || gaps.south) && Math.abs(cx - midX) <= 1));
      if (nearPoi || inLane || cells.some(([cx, cy]) => at(cx, cy) !== FLOOR)) continue;
      cells.forEach(([cx, cy]) => set(cx, cy, BLOCK));
      if (!allReachable()) {
        cells.forEach(([cx, cy]) => set(cx, cy, FLOOR));
        continue;
      }
      obstacles.push({ x: ox, y: oy, big, idx: Math.floor(rng() * 2) });
    }

    // deterministic spawn slots on reachable floor
    const seen = floodReachable(grid, midX, midY);
    const spawnSlots = [];
    let guard = 0;
    while (spawnSlots.length < 8 && guard++ < 300) {
      const sx = 2 + Math.floor(rng() * (W - 4));
      const sy = 2 + Math.floor(rng() * (H - 4));
      if (at(sx, sy) === FLOOR && seen[sy * W + sx]) {
        spawnSlots.push({ x: sx * T + T / 2, y: sy * T + T / 2 });
      }
    }
    while (spawnSlots.length < 8) spawnSlots.push({ x: midX * T + T / 2, y: midY * T + T / 2 });

    // decorative props (non-blocking); zone themes get richer, named sets
    const zoneKey = MH.zoneThemeKey ? MH.zoneThemeKey(roomData.zone) : null;
    const zoneTheme = zoneKey && MH.ZONE_THEMES ? MH.ZONE_THEMES[zoneKey] : null;
    const props = [];
    const nProps = zoneTheme ? 5 + Math.floor(rng() * 5) : 3 + Math.floor(rng() * 3);
    for (let i = 0; i < nProps; i++) {
      const px = 2 + Math.floor(rng() * (W - 4));
      const py = 2 + Math.floor(rng() * (H - 4));
      if (at(px, py) === FLOOR && !pois.some(([qx, qy]) => Math.abs(qx - px) <= 1 && Math.abs(qy - py) <= 1)
          && !props.some(p => Math.abs(p.x - px) <= 1 && Math.abs(p.y - py) <= 1)) {
        const prop = { idx: Math.floor(rng() * 3), x: px, y: py };
        if (zoneTheme) {
          // first props lean on the theme's signature pieces, rest random
          const list = zoneTheme.props;
          prop.name = list[i < 2 ? i % list.length : Math.floor(rng() * list.length)];
          prop.scale = 0.8 + rng() * 0.4;
        }
        props.push(prop);
      }
    }

    return {
      topdown: true,
      vnum, theme: sector, sector, flags, zoneKey,
      description: roomData.description || '',
      gravestones: roomData.gravestones,
      W, H, T, grid, gaps,
      stairsUp, stairsDown, portals, obstacles, props, spawnSlots, entries,
      exits, swim,
      dark: flags.includes('dark'),
      peaceful: flags.includes('peaceful'),
      pxW: W * T, pxH: H * T,
    };
  };
})();
