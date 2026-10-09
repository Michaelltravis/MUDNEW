// Towns, interiors and graveyards (owner's M1b order: towns and interiors after monsters).
//  - Streets ('city'): where a street borders an empty cell of the zone map, a row of
//    houses fills it, facing the street (shops, inns, smithies and temples by the street's
//    name); where it borders another room, a low town wall.
//  - Interiors ('inside' rooms named like a shop, inn, temple, bank, library, bedroom,
//    guild or hall): wood or stone floor, furniture along the walls and on roomgen's
//    obstacles, a rug, lamps; unnamed 'inside' rooms keep the dungeon look.
//  - Graveyards (outdoor rooms named so): graves in rows, fences, dead trees, lanterns.
// Pieces that stand on open floor are written into the room's grid as BLOCK so the hero
// walks around them (the server never sees this: it is furniture, not geometry).
import * as THREE from 'three';
import { trs } from './assets.js';

const BLOCK = 1, FLOOR = 0;
const CARD = { north: [0, -1], south: [0, 1], east: [1, 0], west: [-1, 0] };
const YAW = { north: 0, south: Math.PI, west: Math.PI / 2, east: -Math.PI / 2 };   // face into the room

export function interiorKind(layout) {
  const t = `${layout.name} ${layout.description}`.toLowerCase();
  if (/\b(temple|church|chapel|cathedral|shrine|altar|sanctuary|abbey|monastery|cloister)\b/.test(t)) return 'temple';
  if (/\b(tavern|inn|pub|bar|alehouse|taproom|common room|brewery)\b/.test(t)) return 'tavern';
  if (/\b(bank|vault|treasury|counting house|money ?changer)\b/.test(t)) return 'bank';
  if (/\b(library|study|archive|scriptorium|reading room)\b/.test(t)) return 'library';
  if (/\b(bedroom|bed ?chamber|sleeping|quarters|dormitory|guest room|nursery|bunks?)\b/.test(t)) return 'bedroom';
  if (/\b(throne|palace|great hall|audience|court)\b/.test(t)) return 'throne';
  if (/\b(shop|store|market|merchant|grocer|grocery|baker|bakery|general|armou?ry|weapon|smithy|forge|apothecary|herbalist|alchemist|jewell?er|tailor|outfitter|emporium|butcher|stable|pet)\b/.test(t)) return 'shop';
  if (/\b(guild|training|practice|academy|school|barracks|armory)\b/.test(t)) return 'guild';
  if (/\b(house|home|cottage|hut|kitchen|parlou?r|dining|living room|hall)\b/.test(t)) return 'house';
  return null;
}
export const isGraveyard = layout =>
  /\b(graveyard|cemetery|graves?|burial|boneyard|churchyard|tombstones?|mausoleum)\b/.test(`${layout.name} ${layout.description}`.toLowerCase());

// lanes from the room centre to each opening stay clear (roomgen keeps them too)
function laneTest(layout) {
  const { W, H, gaps } = layout;
  const mx = Math.floor(W / 2), my = Math.floor(H / 2);
  return (x, y) => ((gaps.north || gaps.south) && Math.abs(x - mx) <= 4)
    || ((gaps.east || gaps.west) && Math.abs(y - my) <= 3)
    || Math.abs(x - mx) <= 1 && Math.abs(y - my) <= 1;
}

// ---------------------------------------------------------------- streets
const LANDMARK = [
  [/\b(tavern|inn|pub|alehouse|bar)\b/, 'building_tavern'],
  [/\b(smith|smithy|forge|armou?r|weapon)\b/, 'building_blacksmith'],
  [/\b(temple|church|chapel|cathedral|shrine)\b/, 'building_church'],
  [/\b(market|bazaar|square|fair|plaza|merchant)\b/, 'building_market'],
  [/\b(gate|guard|barracks|tower|wall|garrison)\b/, 'building_tower_A'],
  [/\b(mill)\b/, 'building_windmill'],
];
const COLORS = ['blue', 'red', 'yellow', 'green'];

export function townStreet(c) {
  const { layout, ox, oz, kits, room, b, rng, runs, occ } = c;
  const T = kits.town;
  const pickLandmark = text => (LANDMARK.find(([re]) => re.test(String(text || '').toLowerCase())) || [])[1];
  let streetLandmark = pickLandmark(`${layout.name} ${layout.description}`);
  for (const run of runs) {
    const side = run.horiz ? (run.line === 0 ? 'north' : 'south') : (run.line === 0 ? 'west' : 'east');
    const [dx, dy] = CARD[side];
    const nb = room && room.zoneRef ? room.zoneRef.cells.get(`${room.cx + dx},${room.cy + dy}`) : null;
    const L = run.b - run.a + 1;
    // what lies beyond this edge decides what stands on it:
    //   nothing  -> whole houses built out into the empty cell
    //   a building (an 'inside' room) -> its shopfront, two tiles deep (both walls' width)
    //   anything else (another street, the fields) -> a low stone town wall
    const mode = !nb ? 'houses' : nb.data.sector === 'inside' ? 'facade' : 'wall';
    if (mode === 'wall' || !T) {
      const wall = occ(T ? T.get('wall_straight') : kits.dungeon.get('wall'));
      const n = Math.max(1, Math.round(L / 2.5)), w = L / n;
      for (let i = 0; i < n; i++) {
        const along = run.a + (i + 0.5) * w;
        const [x, z] = run.horiz ? [ox + along, oz + run.line + 0.5] : [ox + run.line + 0.5, oz + along];
        b.add(wall, trs(x, 0, z, run.horiz ? 0 : Math.PI / 2, T ? w / 2 : w / 4, T ? 1.5 : 0.5, T ? 1.25 : 1));
      }
      continue;
    }
    // the shop behind a facade names its front (the Weapon Shop gets a smithy front...)
    let landmark = mode === 'facade' ? pickLandmark(nb.data.name) : streetLandmark;
    const maxDepth = mode === 'facade' ? 2 : run.horiz ? 7 : 11;
    let cursor = run.a;
    const end = run.b + 1;
    while (end - cursor > 2.2) {
      let key;
      if (landmark) { key = landmark; landmark = null; if (mode === 'houses') streetLandmark = null; }
      else key = rng() < 0.55 ? 'building_home_A' : rng() < 0.75 ? 'building_home_B' : 'building_tavern';
      const model = T.get(`${key}_${COLORS[Math.floor(rng() * COLORS.length)]}`) || T.get(`${key}_blue`);
      if (!model) break;
      const size = new THREE.Vector3(); model.box.getSize(size);
      let s = 6;
      if (cursor + size.x * s > end) { s = (end - cursor) / size.x; if (s < 3.5) break; }
      // depth: whole houses keep their shape up to the room's half depth; facades are
      // pressed to two tiles so they never reach into a neighbour's floor
      const sz = Math.min(s, maxDepth / size.z);
      const w = size.x * s;
      const along = cursor + w / 2;
      const off = 1.0 - model.box.max.z * sz;        // front on the ring tile's inner edge
      let x, z;
      if (side === 'north') { x = ox + along; z = oz + off; }
      else if (side === 'south') { x = ox + along; z = oz + 15 - off; }
      else if (side === 'west') { x = ox + off; z = oz + along; }
      else { x = ox + 24 - off; z = oz + along; }
      b.add(occ(model), trs(x, 0, z, YAW[side], s, s, sz));
      cursor += w + 0.35;
    }
    if (end - cursor > 0.8) {
      const along = (cursor + end) / 2;
      const [x, z] = run.horiz ? [ox + along, oz + run.line + 0.5] : [ox + run.line + 0.5, oz + along];
      b.add(T.get('barrel'), trs(x, 0, z, rng() * 6.28, 4.5));
    }
  }
  // street furniture on roomgen's obstacles (they block in the grid already)
  for (const o of layout.obstacles || []) {
    const cx = ox + o.x + (o.big ? 1 : 0.5), cz = oz + o.y + (o.big ? 1 : 0.5);
    if (o.big) {
      const key = ['building_well_blue', 'crate_long_A', 'wheelbarrow', 'tent'][Math.floor(rng() * 4)];
      const s = key.startsWith('building_well') ? 2.6 : key === 'tent' ? 2.2 : 5;
      b.add(occ(T.get(key) || T.get('barrel')), trs(cx, 0, cz, Math.floor(rng() * 4) * Math.PI / 2, s));
    } else {
      const key = ['barrel', 'crate_A_big', 'sack', 'bucket_water', 'crate_B_small'][Math.floor(rng() * 5)];
      b.add(T.get(key), trs(cx, 0, cz, rng() * 6.28, 4.5));
    }
  }
}

// ---------------------------------------------------------------- interiors
const WALL_PIECES = {
  shop: ['shelf_B_large_decorated', 'cabinet_medium_decorated', 'shelf_B_large', 'cabinet_small_decorated'],
  tavern: ['shelf_A_big', 'cabinet_medium', 'lamp_standing'],
  bank: ['cabinet_medium_decorated', 'cabinet_small_decorated', 'pictureframe_large_A'],
  library: ['shelf_B_large_decorated', 'shelf_B_large_decorated', 'shelf_B_small_decorated'],
  bedroom: ['cabinet_small', 'lamp_standing', 'pictureframe_standing_A'],
  guild: ['shelf_A_big', 'cabinet_medium', 'pictureframe_large_B'],
  throne: ['lamp_standing', 'pictureframe_large_A', 'pictureframe_large_B'],
  house: ['shelf_A_big', 'cabinet_small_decorated', 'lamp_standing', 'pictureframe_medium'],
  temple: [],
};
const WOOD = new Set(['shop', 'tavern', 'library', 'bedroom', 'house', 'guild']);

// one wood per room (a mix of light and dark planks read as noise)
export function interiorFloorKey(kind, r, vnum = 0) {
  if (!WOOD.has(kind)) return null;
  return vnum % 3 === 0 ? 'floor_wood_small_dark' : 'floor_wood_small';
}

export function furnish(c, kind) {
  const { layout, ox, oz, kits, b, rng, occ, torches } = c;
  const F = kits.furniture, D = kits.dungeon, G = kits.graveyard, T = kits.town;
  const { W, H, grid } = layout;
  const lane = laneTest(layout);
  const at = (x, y) => grid[y * W + x];
  const block = (x, y) => { if (x > 0 && y > 0 && x < W - 1 && y < H - 1) grid[y * W + x] = BLOCK; };
  const MOUNTED = /^(shelf_A_|pictureframe_(large|medium|small))/;
  const put = (kit, key, x, z, yaw, s = 1, opts) => {
    const m = kit && kit.get(key);
    if (m) b.add(opts && opts.occ ? occ(m) : m, trs(x, MOUNTED.test(key) ? 1.3 : 0, z, yaw, s), opts);
    return !!m;
  };

  // along the north wall (the one the camera faces) and the side walls
  const wallPieces = WALL_PIECES[kind] || [];
  if (wallPieces.length) {
    for (let x = 2; x < W - 2; x += 3) {
      if (at(x, 1) !== FLOOR || at(x + 1, 1) !== FLOOR || lane(x, 1) || lane(x + 1, 1)) continue;
      const key = wallPieces[Math.floor(rng() * wallPieces.length)];
      const mounted = MOUNTED.test(key);
      put(F, key, ox + x + 1, oz + 1.05 + (mounted ? 0 : 0.3), 0, 0.85);
      if (!mounted) { block(x, 1); block(x + 1, 1); }
    }
    for (const [x, yaw] of [[1, Math.PI / 2], [W - 2, -Math.PI / 2]]) {
      for (let y = 3; y < H - 3; y += 4) {
        if (at(x, y) !== FLOOR || lane(x, y) || rng() < 0.4) continue;
        const key = wallPieces[Math.floor(rng() * wallPieces.length)];
        if (MOUNTED.test(key) || key.startsWith('pictureframe')) continue;
        put(F, key, ox + x + 0.5 + (x === 1 ? -0.2 : 0.2), oz + y + 0.5, yaw, 0.8);
        block(x, y);
      }
    }
  }

  // centrepieces on roomgen's obstacles (already blocked)
  for (const o of layout.obstacles || []) {
    const cx = ox + o.x + (o.big ? 1 : 0.5), cz = oz + o.y + (o.big ? 1 : 0.5);
    const yaw = Math.floor(rng() * 4) * Math.PI / 2;
    if (kind === 'tavern') {
      put(F, o.big ? 'table_medium' : 'table_small', cx, cz, yaw, o.big ? 0.8 : 0.7, { occ: false });
      for (const [sx, sz] of o.big ? [[-1.3, 0], [1.3, 0], [0, -1.3], [0, 1.3]] : [[-0.9, 0], [0.9, 0]])
        put(F, 'chair_stool_wood', cx + sx, cz + sz, rng() * 6.28, 0.75, { shadow: false });
      if (o.big && D) put(D, 'keg', cx + 0.6, cz - 0.6, 0, 0.35);
    } else if (kind === 'shop') {
      if (o.big) put(F, 'table_medium_long', cx, cz, yaw, 0.85);
      else put(D, ['barrel_small', 'box_large'][Math.floor(rng() * 2)], cx, cz, rng() * 6.28, 0.7);
    } else if (kind === 'bedroom') {
      put(F, o.big ? (rng() < 0.5 ? 'bed_double_A' : 'bed_single_A') : 'cabinet_small', cx, cz, yaw, o.big ? 0.7 : 0.8);
    } else if (kind === 'library') {
      put(F, o.big ? 'table_medium' : 'shelf_B_small_decorated', cx, cz, yaw, 0.8);
      if (o.big) put(F, 'book_set', cx, cz, rng() * 6.28, 0.8, { shadow: false });
    } else if (kind === 'bank') {
      put(F, o.big ? 'table_medium_long' : 'cabinet_small_decorated', cx, cz, yaw, 0.85);
      if (o.big && D) put(D, 'chest_gold', cx, cz + 1.2, Math.PI, 0.6);
    } else if (kind === 'temple' || kind === 'throne') {
      if (o.big) put(D, 'pillar_decorated', cx, cz, 0, 1, { occ: true });
      else put(G, 'candle_triple', cx, cz, 0, 0.9);
    } else if (kind === 'guild') {
      put(o.big ? F : T, o.big ? 'table_medium' : 'weaponrack', cx, cz, yaw, o.big ? 0.8 : 4.5);
    } else {
      put(F, o.big ? 'table_medium' : 'chair_A_wood', cx, cz, yaw, 0.8);
    }
  }

  // the middle of the room: a rug (temples: a runner up the aisle) and an altar or throne
  const mx = W / 2, my = H / 2;
  if (kind === 'temple' || kind === 'throne') {
    put(F, 'rug_rectangle_stripes_A', ox + mx, oz + my + 1, Math.PI / 2, 1.2, { shadow: false, receive: true });
    if (!layout.gaps.north) {
      if (kind === 'temple') put(G, 'shrine_candles', ox + mx, oz + 2.2, 0, 0.75);
      else put(F, 'armchair_pillows', ox + mx, oz + 2.2, 0, 1.0);
      block(Math.floor(mx), 2); block(Math.floor(mx) - 1, 2);
      torches.push(new THREE.Vector3(ox + mx, 1.6, oz + 2.6));
    }
    // banners on the north wall
    for (let x = 3; x < W - 3; x += 5) if (!layout.gaps.north || Math.abs(x - mx) > 5)
      put(D, ['banner_patternA_red', 'banner_patternB_blue', 'banner_shield_white'][x % 3], ox + x, oz + 0.8, 0, 0.65);
    // benches facing the altar on both sides of the aisle
    if (kind === 'temple') for (let y = 5; y < H - 3; y += 2) for (const x of [mx - 5, mx + 5]) {
      const tx = Math.floor(x), ty = Math.floor(y);
      if (at(tx, ty) !== FLOOR || at(tx + 1, ty) !== FLOOR || lane(tx, ty)) continue;
      put(G, 'bench', ox + x, oz + y, 0, 0.6);
      block(tx, ty); block(tx + 1, ty);
    }
  } else {
    const rug = ['rug_rectangle_A', 'rug_oval_A', 'rug_rectangle_B', 'rug_oval_B'][Math.floor(rng() * 4)];
    put(F, rug, ox + mx, oz + my, rng() < 0.5 ? 0 : Math.PI / 2, 1, { shadow: false });
  }
  // lamps in the corners light the room
  for (const [x, y] of [[1.6, 1.6], [W - 1.6, 1.6]]) {
    if (at(Math.floor(x), Math.floor(y)) !== FLOOR) continue;
    put(F, 'lamp_standing', ox + x, oz + y, 0, 0.7);
    block(Math.floor(x), Math.floor(y));
    torches.push(new THREE.Vector3(ox + x, 1.7, oz + y));
  }
  // small things on the props (walk-through)
  for (const p of layout.props || []) {
    const key = kind === 'library' ? 'book_set' : kind === 'tavern' ? 'chair_stool_wood' : kind === 'temple' ? 'candle_triple' : 'book_single';
    put(kind === 'temple' ? G : F, key, ox + p.x + 0.5, oz + p.y + 0.5, rng() * 6.28, 0.6, { shadow: false });
  }
}

// ---------------------------------------------------------------- graveyards
export function graveyard(c) {
  const { layout, ox, oz, kits, b, rng, occ, torches, runs } = c;
  const G = kits.graveyard;
  if (!G) return;
  const { W, H, grid } = layout;
  const lane = laneTest(layout);
  const at = (x, y) => grid[y * W + x];
  // rows of graves on open ground, each blocking its tile
  for (let y = 3; y < H - 3; y += 3) for (let x = 3; x < W - 3; x += 3) {
    if (at(x, y) !== FLOOR || lane(x, y) || rng() < 0.25) continue;
    const key = ['grave_A', 'grave_B', 'gravestone', 'gravemarker_A', 'gravemarker_B', 'grave_A_destroyed'][Math.floor(rng() * 6)];
    b.add(occ(G.get(key)), trs(ox + x + 0.5, 0, oz + y + 0.5, (rng() - 0.5) * 0.3, 0.55));
    grid[y * W + x] = BLOCK;
  }
  // a fence along the edge of the ground, lanterns by the ways in and out
  for (const run of runs) {
    const L = run.b - run.a + 1;
    const n = Math.max(1, Math.round(L / 2.2)), w = L / n;
    for (let i = 0; i < n; i++) {
      const along = run.a + (i + 0.5) * w;
      const [x, z] = run.horiz ? [ox + along, oz + run.line + 0.5] : [ox + run.line + 0.5, oz + along];
      b.add(G.get(rng() < 0.8 ? 'fence' : 'fence_broken'), trs(x, 0, z, run.horiz ? 0 : Math.PI / 2, w / 4, 0.6, 0.6));
    }
  }
  for (const [dir, g] of Object.entries(layout.gaps)) {
    const pts = dir === 'north' || dir === 'south'
      ? [[g.x0 - 0.5, dir === 'north' ? 1 : H - 1], [g.x1 + 1.5, dir === 'north' ? 1 : H - 1]]
      : [[dir === 'west' ? 1 : W - 1, g.y0 - 0.5], [dir === 'west' ? 1 : W - 1, g.y1 + 1.5]];
    for (const [x, y] of pts) {
      b.add(G.get('lantern_standing'), trs(ox + x, 0, oz + y, 0, 1.0), { shadow: false });
      torches.push(new THREE.Vector3(ox + x, 0.8, oz + y));
    }
  }
}
