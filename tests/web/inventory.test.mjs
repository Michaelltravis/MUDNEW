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
const { slotsFor, dropCommand, removeCommand, moveCommands, partnerOf, keywordFor } = await import('../../src/web_isometric/world3d/hud/inventory.js');

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
