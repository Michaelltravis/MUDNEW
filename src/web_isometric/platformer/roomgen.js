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
      W, H, T,
      grid, hm,
      pool, isUnderwater,
      lowGravity: sector === 'flying',
      dark: flags.includes('dark'),
      peaceful: flags.includes('peaceful'),
      eastGap, westGap, ladder, trapdoor, northDoor, southDoor,
      platforms, props, spawnSlots, entries,
      exits,
      pxW: W * T, pxH: H * T,
    };
  };
})();
