// The /play inventory's drag and drop (world3d/hud/inventory.js): which slots an item lights up,
// and the MUD commands a drop sends (equip.py on the server does the same sums).
//   node --test tests/web/
import { test } from 'node:test';
import assert from 'node:assert/strict';

globalThis.window = globalThis.window || globalThis;
if (typeof globalThis.addEventListener !== 'function') globalThis.addEventListener = () => {};
globalThis.localStorage = globalThis.localStorage || { getItem: () => null, setItem: () => {} };
globalThis.document = globalThis.document || { querySelector: () => null, addEventListener: () => {}, createElement: () => ({ getContext: () => null }) };
if (typeof globalThis.document.addEventListener !== 'function') globalThis.document.addEventListener = () => {};
const { slotsFor, dropCommand, removeCommand, moveCommands, partnerOf, keywordFor, matchesSearch } = await import('../../src/web_isometric/world3d/hud/inventory.js');

const ring = (name, slot = 'finger1') => ({ name, short: name, type: 'worn', slot });

test('the slots an item fits: a ring either finger whatever it says; weapons, lights, wands', () => {
  assert.deepEqual(slotsFor(ring('ring gold')), ['finger1', 'finger2']);
  assert.deepEqual(slotsFor(ring('ring gold', 'finger')), ['finger1', 'finger2']);
  assert.deepEqual(slotsFor({ name: 'amulet', type: 'worn', slot: 'neck1' }), ['neck1', 'neck2']);
  assert.deepEqual(slotsFor({ name: 'helm', type: 'armor', slot: 'head' }), ['head']);
  assert.deepEqual(slotsFor({ name: 'sword', type: 'weapon' }), ['wield', 'dual_wield']);
  assert.deepEqual(slotsFor({ name: 'torch', type: 'light' }), ['light']);
  assert.deepEqual(slotsFor({ name: 'ring', type: 'light', slot: 'finger' }), ['finger1', 'finger2'], 'a glowing ring is a ring');
  assert.deepEqual(slotsFor({ name: 'wand', type: 'wand' }), ['hold']);
  assert.deepEqual(slotsFor({ name: 'bread', type: 'food' }), []);
  assert.equal(partnerOf('finger1'), 'finger2');
  assert.equal(partnerOf('head'), null);
});

test('a drop sends the command with the slot; the second of two alike is 2.<word>', () => {
  const a = ring('ring silver'), b = ring('ring silver'), inv = [a, b];
  assert.equal(dropCommand(a, 'finger1', inv), 'wear ring finger1');
  assert.equal(dropCommand(b, 'finger2', inv), 'wear 2.ring finger2');
  assert.equal(dropCommand({ name: 'sword long', type: 'weapon' }, 'wield', []), 'wield sword wield');
  assert.equal(dropCommand({ name: 'torch', type: 'light' }, 'light', []), 'hold torch light');
  assert.equal(removeCommand('finger2'), 'remove finger2');
  assert.equal(keywordFor(b, inv), '2.ring');
});

test('a ring moved to the other finger, or the two swapped', () => {
  const a = ring('ring gold'), b = ring('ring ruby'), c = ring('ring jade');
  assert.deepEqual(moveCommands({ finger1: a }, [c], 'finger1', 'finger2'), ['remove finger1', 'wear 2.ring finger2']);
  assert.deepEqual(moveCommands({ finger1: a, finger2: b }, [], 'finger1', 'finger2'),
    ['remove finger1', 'remove finger2', 'wear ring finger2', 'wear ring finger1']);
});

test('the pack\'s search: every word typed, in the name, type, slot or rarity', () => {
  const ring = { name: 'a silver ring of warding', type: 'worn', slot: 'finger', rarity: 'rare' };
  const potion = { name: 'a potion of healing', type: 'potion', rarity: 'common' };
  assert.ok(matchesSearch(ring, ''), 'an empty search shows everything');
  assert.ok(matchesSearch(ring, 'ring') && matchesSearch(ring, 'RARE silver') && matchesSearch(ring, 'finger'));
  assert.ok(!matchesSearch(ring, 'potion') && !matchesSearch(ring, 'gold ring'), 'every word must match');
  assert.ok(matchesSearch(potion, 'potion heal') && !matchesSearch(null, 'x'));
});

test("gear the class isn't trained in (class_gear.py): greyed, no slot to drop it in, a line in the tooltip", async () => {
  const { barredBy, setGearRules, tooltip } = await import('../../src/web_isometric/world3d/hud/inventory.js');
  const mage = { armour: 0, shield: false, weapons: ['dagger', 'staff', 'thrown', 'wand'] };
  const thief = { armour: 1, shield: false, weapons: ['bow', 'claw', 'crossbow', 'dagger', 'mace', 'sword1', 'thrown', 'whip'] };
  const plate = { name: 'plate', type: 'armor', slot: 'body', gk: 'a:3' };
  const robe = { name: 'robe', type: 'armor', slot: 'body', gk: 'a:0' };
  const greatsword = { name: 'claymore', type: 'weapon', gk: 'w:sword:2' };
  const rapier = { name: 'rapier', type: 'weapon', gk: 'w:sword:1' };
  assert.equal(barredBy(plate, mage), 'plate armour');
  assert.equal(barredBy(robe, mage), null);
  assert.equal(barredBy(greatsword, thief), 'two-handed swords');
  assert.equal(barredBy(rapier, thief), null);
  assert.equal(barredBy({ name: 'shield', type: 'armor', slot: 'shield', gk: 's' }, mage), 'shields');
  assert.equal(barredBy(plate, null), null, 'no rules: anything goes');
  assert.deepEqual(slotsFor(plate, mage), []);
  assert.deepEqual(slotsFor(robe, mage), ['body']);
  setGearRules(mage);
  assert.match(tooltip(plate), /Not for your class: no plate armour/);
  assert.doesNotMatch(tooltip(robe), /Not for your class/);
  setGearRules(null);
});
