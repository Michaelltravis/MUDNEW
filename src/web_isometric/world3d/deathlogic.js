// Death traps, the pure part (tested in Node): which rooms kill, and the abyss carved in one's
// grid (deathtrap.js draws it; zone.js and main.js stop the hero at its edge).
const FLOOR = 0, BLOCK = 1;

// pure (tested in Node): does a room's flags say it kills?
export function isDeadly(flags) {
  return Array.isArray(flags) && flags.some(f => f === 'deathtrap' || f === 'death');
}

// the abyss's outline: a jagged ellipse in room-local metres, the same for a room every time
export function abyssOutline(W, H, rng, n = 30) {
  const rx = W * 0.3, rz = H * 0.28, pts = [];
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2, k = 0.86 + rng() * 0.22;
    pts.push([W / 2 + Math.cos(a) * rx * k, H / 2 + Math.sin(a) * rz * k]);
  }
  return pts;
}
export function inside(pts, x, y) {
  let c = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [xi, yi] = pts[i], [xj, yj] = pts[j];
    if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) c = !c;
  }
  return c;
}

// mark the abyss in a room's grid: its cells are BLOCK (you walk the ledge round it), but never
// the stairs or a portal; if that would cut one way in off from another, a smaller abyss is tried,
// then none. Returns the outline used (room-local metres), or null.
export function carveAbyss(layout, rng) {
  const { W, H, grid } = layout;
  const keep = [layout.stairsUp, layout.stairsDown, ...(layout.portals || [])].filter(Boolean);
  const base = abyssOutline(W, H, rng);
  for (const s of [1, 0.75, 0.5]) {
    const pts = base.map(([x, y]) => [W / 2 + (x - W / 2) * s, H / 2 + (y - H / 2) * s]);
    const cut = [];
    for (let y = 2; y < H - 2; y++) for (let x = 2; x < W - 2; x++) {
      if (grid[y * W + x] !== FLOOR || !inside(pts, x + 0.5, y + 0.5)) continue;
      if (keep.some(t => Math.abs(t.x - x) <= 1 && Math.abs(t.y - y) <= 1)) continue;
      grid[y * W + x] = BLOCK;
      cut.push(y * W + x);
    }
    if (connected(layout)) return pts;
    for (const i of cut) grid[i] = FLOOR;
  }
  return null;
}
// every way in (and the stairs) reachable from every other, over floor
function connected(layout) {
  const { W, H, grid } = layout;
  const g = layout.gaps || {};
  const mx = Math.floor(W / 2), my = Math.floor(H / 2);
  const want = [];
  if (g.north) want.push([mx, 0]);
  if (g.south) want.push([mx, H - 1]);
  if (g.west) want.push([0, my]);
  if (g.east) want.push([W - 1, my]);
  for (const t of [layout.stairsUp, layout.stairsDown]) if (t) want.push([t.x, t.y]);
  if (want.length < 2) return true;
  const ok = (x, y) => x >= 0 && y >= 0 && x < W && y < H && grid[y * W + x] !== BLOCK;
  const seen = new Uint8Array(W * H), q = [want[0]];
  seen[want[0][1] * W + want[0][0]] = 1;
  while (q.length) {
    const [x, y] = q.pop();
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const xx = x + dx, yy = y + dy;
      if (!ok(xx, yy) || seen[yy * W + xx]) continue;
      seen[yy * W + xx] = 1;
      q.push([xx, yy]);
    }
  }
  return want.every(([x, y]) => seen[y * W + x]);
}
