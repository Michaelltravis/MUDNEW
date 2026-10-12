// /play's progression and travel windows: talents, the almanac, travel, the bank.
//   node --test tests/web/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { talentStates } from '../../src/web_isometric/world3d/hud/talents.js';
import { achievementGroups } from '../../src/web_isometric/world3d/hud/almanac.js';
import { travelRows } from '../../src/web_isometric/world3d/hud/travel.js';
import { goldAmount } from '../../src/web_isometric/world3d/hud/services.js';

const tl = (id, tier, o = {}) => ({ id, name: id, description: '', tier, max_rank: 3, requires: [], rank: 0, ...o });

test('talents: a tier opens at five points a tier in its tree; prerequisites and top ranks hold', () => {
  const data = { points_available: 2, trees: [{ name: 'Fire', points: 5, talents: [
    tl('spark', 1, { rank: 3 }), tl('burn', 1, { rank: 2 }), tl('blaze', 2), tl('inferno', 2, { requires: ['blaze'] }), tl('sun', 3),
  ] }] };
  const [fire] = talentStates(data);
  const st = Object.fromEntries(fire.tiers.flatMap(t => t.talents).map(t => [t.id, [t.state, t.why]]));
  assert.equal(st.spark[0], 'max');
  assert.equal(st.burn[0], 'open');
  assert.equal(st.blaze[0], 'open');                     // 5 points in the tree: tier 2 open
  assert.deepEqual(st.inferno, ['locked', 'needs blaze first']);
  assert.deepEqual(st.sun, ['locked', '10 points in Fire first']);
  assert.deepEqual(fire.tiers.map(t => t.tier), [1, 2, 3]);
  const broke = talentStates({ ...data, points_available: 0 })[0].tiers[0].talents.find(t => t.id === 'burn');
  assert.deepEqual([broke.state, broke.why], ['learned', 'no points to spend']);
});

test('achievements: grouped by category, nearest to done first, the earned ones last or hidden', () => {
  const list = [
    { name: 'A', category: 'combat', target: 10, progress: 9, unlocked: false },
    { name: 'B', category: 'combat', target: 10, progress: 2, unlocked: false },
    { name: 'C', category: 'combat', unlocked: true },
    { name: 'D', category: 'explore', target: 4, progress: 1, unlocked: false },
  ];
  const g = achievementGroups(list);
  assert.deepEqual(g.map(x => x.category), ['combat', 'explore']);
  assert.deepEqual(g[0].rows.map(r => r.name), ['A', 'B', 'C']);
  assert.equal(g[0].rows[0].pct, 0.9);
  assert.deepEqual(achievementGroups(list, { done: false })[0].rows.map(r => r.name), ['A', 'B']);
});

test('travel: a waypoint you are at, can\'t afford or are cooling down from is shown but closed', () => {
  const rows = travelRows({ gold: 100, cooldown: 0, waypoints: [
    { key: 'mid', name: 'Midgaard', cost: 0, here: true }, { key: 'far', name: 'Far', cost: 500 }, { key: 'near', name: 'Near', cost: 50 }] });
  assert.deepEqual(rows.map(r => [r.key, r.ok, r.why]), [['mid', false, 'you are here'], ['far', false, 'not enough gold'], ['near', true, '']]);
  assert.equal(travelRows({ gold: 100, cooldown: 30, waypoints: [{ key: 'near', cost: 50 }] })[0].why, 'ready in 30s');
});

test('the bank takes a whole amount up to what there is, or all', () => {
  assert.equal(goldAmount('250', 1000), 250);
  assert.equal(goldAmount('1,000', 1000), 1000);
  assert.equal(goldAmount('All', 5), 'all');
  assert.equal(goldAmount('all', 0), null);
  assert.equal(goldAmount('0', 10), null);
  assert.equal(goldAmount('11', 10), null);
  assert.equal(goldAmount('abc', 10), null);
});

test('the world map shows only rooms you have explored, on your level, zones named over their middles', async () => {
  const { worldView } = await import('../../src/web_isometric/world3d/hud/worldmap.js');
  const atlas = { zones: [{ id: 30, name: 'Midgaard', color: '#f00' }, { id: 31, name: 'Sewers', color: '#0f0' }],
    rooms: [{ vnum: 1, zone: 30, x: 0, y: 0, z: 0 }, { vnum: 2, zone: 30, x: 2, y: 0, z: 0 }, { vnum: 3, zone: 31, x: 9, y: 9, z: 0 },
      { vnum: 4, zone: 31, x: 0, y: 0, z: -1 }] };
  const v = worldView(atlas, [1, 2, 4]);
  assert.deepEqual(v.rooms.map(r => r.vnum), [1, 2]);            // 3 unexplored, 4 below
  assert.deepEqual(v.zones.map(z => [z.name, z.x, z.y]), [['Midgaard', 1, 0]]);
  assert.deepEqual(v.bounds, { minX: 0, maxX: 2, minY: 0, maxY: 0 });
  assert.deepEqual(worldView(atlas, [4], -1).rooms.map(r => r.vnum), [4]);
  assert.equal(worldView(atlas, []).bounds, null);
});

test('a warrior\'s abilities evolve by use, along the sworn doctrine', async () => {
  const { evolutionRows } = await import('../../src/web_isometric/world3d/hud/legend.js');
  const doc = { doctrine: 'iron_wall', abilities: [
    { ability: 'bash', usage: 60, evolved: 'skull_crack', thresholds: {
      25: { iron_wall: ['skull_crack', 'x'], berserker: ['b1', 'y'] }, 100: { iron_wall: ['fortress_bash', 'more'], berserker: ['b2', 'z'] } } },
    { ability: 'kick', usage: 30, evolved: null, thresholds: { 25: { iron_wall: ['iron_kick', 'k'] } } },
    { ability: 'strike', usage: 999, evolved: 'last', thresholds: { 25: { iron_wall: ['last', 'done'] } } },
  ] };
  const rows = evolutionRows(doc);
  assert.deepEqual(rows.map(r => [r.ability, r.next && r.next.name, r.next && r.next.at, r.ready]),
    [['bash', 'fortress_bash', 100, false], ['kick', 'iron_kick', 25, true], ['strike', null, null, false]]);
  assert.deepEqual(evolutionRows({ doctrine: null, abilities: doc.abilities }), []);
});
