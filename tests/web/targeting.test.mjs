// Auto-targeting and how commands name a target (world3d/targeting.js), and the right-click
// menu (world3d/hud/verbs.js).   node --test tests/web/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { isHostile, shouldRetarget, retargetOnDeath, refFor, abilityCommand } from '../../src/web_isometric/world3d/targeting.js';
import { verbsFor } from '../../src/web_isometric/world3d/hud/verbs.js';

const NOW = 1_000_000;
const mob = (id, o = {}) => {
  const { data, ...rest } = o;
  return { key: `m${id}`, kind: 'mob', vnum: 10, ...rest, data: { id, name: 'grey wolf', hp: 20, maxHp: 20, ...data } };
};

test('hostile: the aggressive flag, fighting you, or having hit you lately', () => {
  assert.equal(isHostile(mob(1)), false);
  assert.equal(isHostile(mob(1, { data: { flags: ['aggressive'] } })), true);
  assert.equal(isHostile(mob(1, { data: { fighting: true } })), true);
  assert.equal(isHostile(mob(1, { aggroAt: NOW - 1000 }), NOW), true);
  assert.equal(isHostile({ kind: 'player', data: { name: 'Bob', fighting: true } }), false);
});

test('an attacker becomes the target unless you are busy with a live foe', () => {
  const att = mob(2, { aggroAt: NOW });
  assert.equal(shouldRetarget(null, att, 10, NOW), true, 'no target');
  assert.equal(shouldRetarget({ kind: 'mob', vnum: 10, data: { name: 'shopkeeper', shopkeeper: true } }, att, 10, NOW), true, 'a shopkeeper');
  assert.equal(shouldRetarget({ kind: 'player', vnum: 10, data: { name: 'Bob' } }, att, 10, NOW), true, 'another player');
  assert.equal(shouldRetarget(mob(3, { vnum: 11 }), att, 10, NOW), true, 'a creature in another room');
  assert.equal(shouldRetarget(mob(3, { data: { hp: 0, maxHp: 20 } }), att, 10, NOW), true, 'a dead one');
  assert.equal(shouldRetarget(mob(3, { data: { fighting: true } }), att, 10, NOW), false, 'your foe stays your foe');
  assert.equal(shouldRetarget(mob(3, { aggroAt: NOW - 2000 }), att, 10, NOW), false, 'one that just hit you');
  assert.equal(shouldRetarget(mob(3, { pickedAt: NOW - 1000, data: { flags: ['aggressive'] } }), att, 10, NOW), false, 'picked by hand a moment ago');
  assert.equal(shouldRetarget(mob(3), att, 10, NOW), true, 'an idle creature you clicked earlier');
  assert.equal(shouldRetarget(att, att, 10, NOW), false, 'already the target');
});

test('when the target dies, the creature that hit you last takes its place', () => {
  const a = mob(4, { aggroAt: NOW - 5000 }), b = mob(5, { aggroAt: NOW - 1000 }), c = mob(6, { aggroAt: NOW - 500, vnum: 99 });
  assert.equal(retargetOnDeath([a, b, c], 10, NOW), b);
  assert.equal(retargetOnDeath([mob(7, { aggroAt: NOW - 9000 })], 10, NOW), null, 'too long ago');
});

test('commands name a creature by its id and a player by name; skills keep their underscores', () => {
  assert.equal(refFor(mob(12)), '#12');
  assert.equal(refFor({ kind: 'player', data: { name: 'Gauntlet' } }), 'gauntlet');
  assert.equal(abilityCommand({ id: 'order_verdict' }, '#12'), 'order_verdict #12');
  assert.equal(abilityCommand({ id: 'holy_smite' }, '#3'), 'holy_smite #3');
  assert.equal(abilityCommand({ id: 'magic_missile', spell: true }, '#3'), "cast 'magic missile' #3");
  assert.equal(abilityCommand({ id: 'rally' }, null), 'rally');
});

test('right-click menus: creature, shopkeeper, player, door, yourself, the ground', () => {
  const labels = v => v.items.map(i => i.label);
  const m = verbsFor({ kind: 'mob', ent: mob(12, { data: { flags: ['aggressive'], level: 5 } }) }, { skills: [{ id: 'bash', label: 'bash' }] });
  assert.deepEqual(labels(m), ['Attack', 'bash', 'Target', 'Consider', 'Look']);
  assert.equal(m.items.find(i => i.label === 'Consider').cmd, 'consider #12');
  const shop = verbsFor({ kind: 'mob', ent: mob(13, { data: { name: 'the baker', shopkeeper: true } }) });
  assert.deepEqual(labels(shop).slice(0, 2), ['Talk', 'Shop']);
  assert.equal(shop.items[0].cmd, 'talk baker');
  const pl = verbsFor({ kind: 'player', ent: { kind: 'player', vnum: 10, data: { name: 'Bob', level: 7 } } }, { room: 10 });
  assert.ok(labels(pl).includes('Invite to group'));
  assert.equal(pl.items.find(i => i.label === 'Invite to group').cmd, 'group invite Bob');
  const far = verbsFor({ kind: 'player', ent: { kind: 'player', vnum: 11, data: { name: 'Bob' } } }, { room: 10 });
  assert.ok(!far.items.find(i => /^Invite/.test(i.label)).cmd, 'in another room: greyed, walk closer');
  const mate = verbsFor({ kind: 'player', ent: { kind: 'player', vnum: 10, data: { name: 'Bob', groupmate: true } } }, { room: 10 });
  assert.ok(labels(mate).includes('In your group'));
  assert.ok(labels(verbsFor({ kind: 'self' }, { inGroup: true })).includes('Leave group'));
  const door = verbsFor({ kind: 'door', door: { dir: 'east', info: { label: 'oak door', closed: true, locked: true, has_key: true } } });
  assert.equal(door.title, 'Oak door');
  assert.equal(door.items[0].act, 'door:unlockopen');
  const self = verbsFor({ kind: 'self' }, { posture: 'standing', inCombat: false });
  assert.ok(labels(self).includes('Rest') && !labels(self).includes('Stand up'));
  assert.deepEqual(labels(verbsFor({ kind: 'ground', point: { x: 1, z: 2 } })), ['Walk here']);
});
