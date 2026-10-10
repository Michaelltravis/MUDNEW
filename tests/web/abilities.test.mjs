// Your own action bar and the spellbook's bookkeeping (world3d/abilities.js).
//   node --test tests/web/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { SLOTS, rankOf, cleanBar, defaultBar, placeNew, putOnBar, takeOffBar, diffAbilities, costLine } from '../../src/web_isometric/world3d/abilities.js';

const ab = (id, o = {}) => ({ id, name: id, type: 'skill', pct: 50, level: 1, known: true, ...o });
const LIST = [ab('bash'), ab('kick', { level: 3 }), ab('cleave', { level: 5 }), ab('rally', { level: 9 }), ab('charge', { known: false, pct: 0, level: 20 })];

test('ranks by proficiency: learned at 50%, mastered by use at 85%, perfected by a trainer', () => {
  assert.equal(rankOf(50), 'Novice');
  assert.equal(rankOf(72), 'Adept');
  assert.equal(rankOf(85), 'Mastered');
  assert.equal(rankOf(100), 'Perfected');
  assert.equal(rankOf(0), 'Not learned');
});

test('a first bar follows the class order, then the level each ability came at', () => {
  const bar = defaultBar(LIST, ['cleave', 'bash']);
  assert.equal(bar.length, SLOTS);
  assert.deepEqual(bar.slice(0, 5), ['cleave', 'bash', 'kick', 'rally', null], 'unknown abilities stay off');
});

test("the server's bar keeps only what you know, once each, always 16 long", () => {
  const bar = cleanBar(['kick', 'charge', 'kick', 'ghost', null, 'bash'], LIST);
  assert.deepEqual(bar.slice(0, 6), ['kick', null, null, null, null, 'bash']);
  assert.equal(bar.length, SLOTS);
  assert.equal(cleanBar(null, LIST).every(x => x === null), true);
});

test('new abilities fill the first free slots; moving one swaps it with what was there', () => {
  const start = putOnBar(new Array(SLOTS).fill(null), 'bash', 1);
  const { bar, placed } = placeNew(start, ['kick', 'bash', 'cleave']);
  assert.deepEqual(placed, [{ id: 'kick', slot: 0 }, { id: 'cleave', slot: 2 }], 'already on the bar: left alone');
  const moved = putOnBar(bar, 'cleave', 0);
  assert.deepEqual(moved.slice(0, 3), ['cleave', 'bash', 'kick']);
  assert.deepEqual(takeOffBar(moved, 1).slice(0, 3), ['cleave', null, 'kick']);
  const full = new Array(SLOTS).fill('x').map((x, i) => `a${i}`);
  assert.deepEqual(placeNew(full, ['late']).placed, [], 'a full bar takes nothing');
});

test('between payloads: what was learned and what improved', () => {
  const next = LIST.map(a => a.id === 'kick' ? { ...a, pct: 53 } : a.id === 'charge' ? { ...a, known: true, pct: 50 } : a);
  assert.deepEqual(diffAbilities(LIST, next), { learned: ['charge'], improved: [{ id: 'kick', from: 50, to: 53 }] });
  assert.deepEqual(diffAbilities(null, LIST).learned.length, 4, 'the first payload learns everything (callers skip it)');
});

test('the cost line reads like a tooltip', () => {
  assert.equal(costLine({ cost: 15, res: 'mana', cd: 6, range: 14 }), '15 mana · 6 s cooldown · 14 m');
  assert.equal(costLine({ cd: 120, target: 'self' }), '2 min cooldown · yourself');
  assert.equal(costLine({ range: 2.5 }), 'melee');
});
