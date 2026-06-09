// QC harness: generate every real room and assert playability invariants.
const fs = require('fs');
const path = require('path');

// shims so the browser modules load in node
global.window = {};
const spritesSrc = fs.readFileSync('src/web_isometric/platformer/sprites.js', 'utf8');
const mb = spritesSrc.match(/function mulberry32[\s\S]*?\n  \}/)[0];
const MH = global.window.MH = {};
eval('MH.mulberry32 = ' + mb.replace('function mulberry32', 'function'));
const THEMES = ['inside','city','dungeon','cave','forest','field','hills','mountain','desert','swamp','water_swim','water_noswim','underwater','flying','default'];
MH.themeForSector = s => THEMES.includes(s) ? s : 'default';
eval(fs.readFileSync('src/web_isometric/platformer/roomgen.js', 'utf8'));

const CELL = MH.CELL;
const JUMP_TILES = 3;          // safe jumpable step-up (physics allows ~3.7)

// load all rooms from zone files
const zoneDir = 'world/zones';
const rooms = [];
for (const f of fs.readdirSync(zoneDir).filter(f => f.endsWith('.json'))) {
  const data = JSON.parse(fs.readFileSync(path.join(zoneDir, f), 'utf8'));
  const list = data.rooms || data; // tolerate either shape
  for (const r of (Array.isArray(list) ? list : Object.values(list))) {
    if (r && r.vnum != null) rooms.push(r);
  }
}
console.log(`loaded ${rooms.length} rooms`);

// column-walk reachability: from column a, can we reach column b?
// movement model: walk along floor, step up <= JUMP_TILES, fall any height,
// ladders climb their column, water columns are swimmable (vertical freedom).
function reachableColumns(layout) {
  const { W, H, hm, grid } = layout;
  const cellAt = (x, y) => (x < 0 || x >= W || y < 0 || y >= H) ? CELL.SOLID : grid[y * W + x];
  // effective standing height per column = top of terrain (hm), water = passable
  const isWaterCol = x => cellAt(x, hm[x]) === CELL.WATER;
  const reach = new Array(W).fill(false);
  // start from every entry column (they're all on the floor)
  const starts = Object.values(layout.entries).map(e => Math.max(2, Math.min(W - 3, Math.floor(e.x / layout.T))));
  const queue = [...new Set(starts)];
  queue.forEach(x => reach[x] = true);
  while (queue.length) {
    const x = queue.shift();
    for (const nx of [x - 1, x + 1]) {
      if (nx < 2 || nx > W - 3 || reach[nx]) continue;
      const dh = hm[x] - hm[nx];   // positive = nx is LOWER? hm smaller = higher ground
      // moving onto nx: step up if hm[nx] < hm[x] (need hm[x]-hm[nx] <= JUMP)
      const stepUp = hm[x] - hm[nx];
      const ok = stepUp <= JUMP_TILES || isWaterCol(x) || isWaterCol(nx);
      if (ok) { reach[nx] = true; queue.push(nx); }
    }
  }
  return reach;
}

const failures = {};
function fail(kind, vnum, detail) {
  (failures[kind] = failures[kind] || []).push({ vnum, detail });
}

const DIRS = ['north', 'south', 'east', 'west', 'up', 'down'];
let checked = 0;
for (const r of rooms) {
  const roomData = { vnum: r.vnum, sector: r.sector_type || '', flags: r.flags || [], exits: r.exits || {} };
  let a, b;
  try {
    a = MH.generateRoom(roomData);
    b = MH.generateRoom(roomData);
  } catch (e) {
    fail('crash', r.vnum, e.message);
    continue;
  }
  checked++;
  // determinism
  if (Buffer.from(a.grid).compare(Buffer.from(b.grid)) !== 0) fail('nondeterministic', r.vnum, '');
  // exit features exist
  const ex = roomData.exits;
  if (ex.east && !a.eastGap) fail('missing-exit', r.vnum, 'east');
  if (ex.west && !a.westGap) fail('missing-exit', r.vnum, 'west');
  if (ex.north && !a.northDoor) fail('missing-exit', r.vnum, 'north');
  if (ex.south && !a.southDoor) fail('missing-exit', r.vnum, 'south');
  if (ex.up && !a.ladder) fail('missing-exit', r.vnum, 'up');
  if (ex.down && !a.trapdoor) fail('missing-exit', r.vnum, 'down');
  // feature positions inside bounds
  for (const [name, feat] of [['north', a.northDoor], ['south', a.southDoor], ['trapdoor', a.trapdoor]]) {
    if (feat && (feat.x < 2 || feat.x > a.W - 3)) fail('feature-oob', r.vnum, `${name}@${feat.x}`);
  }
  // entries stand in open space
  for (const [dir, e] of Object.entries(a.entries)) {
    const tx = Math.floor(e.x / a.T), ty = Math.floor(e.y / a.T);
    const cell = a.grid[ty * a.W + tx];
    if (cell === CELL.SOLID) fail('entry-in-wall', r.vnum, `${dir}@${tx},${ty}`);
  }
  // spawn slots in open space
  a.spawnSlots.forEach((s, i) => {
    const tx = Math.floor(s.x / a.T), ty = Math.floor(s.y / a.T);
    if (tx < 0 || tx >= a.W || ty < 0 || ty >= a.H) { fail('spawn-oob', r.vnum, `slot${i}`); return; }
    if (a.grid[ty * a.W + tx] === CELL.SOLID) fail('spawn-in-wall', r.vnum, `slot${i}@${tx},${ty}`);
  });
  // reachability of every exit feature column
  const reach = reachableColumns(a);
  const need = [];
  if (a.eastGap) need.push(['east', a.W - 3]);
  if (a.westGap) need.push(['west', 2]);
  if (a.northDoor) need.push(['north', a.northDoor.x]);
  if (a.southDoor) need.push(['south', a.southDoor.x]);
  if (a.ladder) need.push(['up', Math.max(2, Math.min(a.W - 3, a.ladder.x))]);
  if (a.trapdoor) need.push(['down', a.trapdoor.x]);
  for (const [dir, col] of need) {
    const c = Math.max(2, Math.min(a.W - 3, col));
    if (!reach[c]) fail('exit-unreachable', r.vnum, `${dir}@col${c} sector=${roomData.sector}`);
  }
}

console.log(`checked ${checked} rooms`);
let total = 0;
for (const [kind, list] of Object.entries(failures)) {
  total += list.length;
  const sample = list.slice(0, 6).map(f => `${f.vnum}${f.detail ? '(' + f.detail + ')' : ''}`).join(', ');
  console.log(`FAIL ${kind}: ${list.length}  e.g. ${sample}`);
}
if (!total) console.log('ALL CHECKS PASSED');
process.exit(total ? 1 : 0);
