// Is this an upgrade? (world3d/gearcompare.js)
//   node --test tests/web/
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { avgDice, statsOf, score, wornFor, compare } from '../../src/web_isometric/world3d/gearcompare.js';

const sword = (dice, aff = []) => ({ type: 'weapon', slot: 'wield', damage_dice: dice, affects: aff });
const ring = (aff) => ({ type: 'worn', slot: 'finger', affects: aff });

test('dice average', () => {
  assert.equal(avgDice('2d6+3'), 10);
  assert.equal(avgDice('1d8'), 4.5);
  assert.equal(avgDice(''), 0);
});

test("an item's stats, named as the server names them", () => {
  assert.deepEqual(statsOf({ armor: 5, affects: [{ type: 'dex', value: 2 }, { location: 'max_mana', modifier: 30 }] }), { armour: 5, dex: 2, mana: 30 });
});

test('a harder-hitting sword is better for a warrior; a staff of wisdom for a cleric', () => {
  const eq = { wield: sword('1d8') };
  assert.ok(compare(sword('2d8'), eq, 'warrior').better);
  assert.ok(!compare(sword('1d6'), eq, 'warrior').better);
  const staff = sword('1d6', [{ type: 'wis', value: 4 }, { type: 'heal_power', value: 3 }]);
  assert.ok(compare(staff, eq, 'cleric').better, 'the wisdom and healing outweigh the damage for a cleric');
  assert.ok(score(staff, 'cleric') > score(staff, 'warrior'));
});

test('two ring fingers: it is weighed against the weaker ring; an empty finger is always worth filling', () => {
  const eq = { finger1: ring([{ type: 'str', value: 3 }]), finger2: ring([{ type: 'hp', value: 5 }]) };
  assert.equal(wornFor(ring([]), eq).slot, 'finger2');
  assert.ok(compare(ring([{ type: 'str', value: 1 }]), eq, 'warrior').better);
  assert.ok(compare(ring([{ type: 'dex', value: 1 }]), { finger1: eq.finger1, finger2: null }, 'thief').better);
});

test('the rows are the changes, the biggest first', () => {
  const c = compare(sword('2d6', [{ type: 'damroll', value: 2 }]), { wield: sword('1d6', [{ type: 'hitroll', value: 1 }]) }, 'warrior');
  assert.equal(c.rows[0].k, 'damage');
  assert.ok(c.rows.find(r => r.k === 'hitroll' && r.delta === -1));
});
