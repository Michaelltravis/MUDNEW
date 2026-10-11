// Which body each creature gets (world3d/looks.js), case by case and over every creature in
// the world (tools/qc_bestiary.mjs).   node --test tests/web/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { creatureLook, subjectOf } from '../../src/web_isometric/world3d/looks.js';
import { loadMobs, suspects, lookLabel } from '../../tools/qc_bestiary.mjs';

const ART = path.join(path.dirname(fileURLToPath(import.meta.url)), '../../src/web_isometric/art3d');
const look = (short, o = {}) => creatureLook({ short, name: o.name || short.split(' ').pop(), ...o });
const body = l => l.beast ? (l.beast.mob || l.beast.proc || l.beast.prop[1]) : l.model;

test('the head noun decides: a blob is a slime, a giant hornet a hornet, a goat herder a person', () => {
  assert.equal(body(look('the green gelatinous blob', { name: 'green' })), 'slime');
  assert.equal(body(look('the giant hornet')), 'bee');
  assert.ok(look('the giant hornet').beast.h > 0.6, 'a giant hornet is bigger than a hornet');
  assert.ok(!look('the goat herder').beast, 'the goat herder is a person');
  assert.ok(!look('the vampire hunter').beast && !/skeleton/.test(look('the vampire hunter').model), 'hunts vampires, is not one');
  assert.equal(body(look('a goblin mushroom farmer')), 'greendemon');
  assert.equal(body(look('King of the Goblins', { name: 'king' })), 'greendemon');
  assert.equal(body(look('the Spider Queen')), 'spider');
  assert.equal(body(look('the fire elemental')), 'ghost');
  assert.equal(body(look('the giant lizard')), 'lizard');
  assert.ok(look('the giant lizard').beast.h > 1, 'the giant lizard entry, not a garden lizard');
});

test('things that are not animals: props, constructs, statues', () => {
  assert.deepEqual(look('the mimic').beast.prop, ['dungeon', 'chest']);
  assert.ok(look('the dancing sword').beast.prop && look('the dancing sword').beast.fly > 0);
  const golem = look('the bronze golem');
  assert.equal(golem.model, 'knight');
  assert.ok(!golem.loadout.some(i => /Sword|Axe|Staff|Knife|Crossbow/.test(i)), 'golems carry no weapons');
  assert.equal(golem.tint, 0xb08850, 'bronze');
  assert.equal(golem.flat, true, 'bronze all over, not a tinted costume');
  assert.equal(look('the statue of Indra', { name: 'statue' }).still, true);
  assert.equal(look('the Black Rook', { name: 'black' }).tint, 0x45454d);
  assert.equal(look('a possessed suit of armor', { name: 'armor' }).model, 'knight');
});

test('people are dressed for their trade, the same way every time', () => {
  assert.deepEqual(look('the baker', { shopkeeper: true }).loadout, [], 'no baker with an axe');
  assert.ok(look('the cityguard').loadout.includes('1H_Sword'));
  assert.equal(look("the mages' guildmaster", { trainer: true }).model, 'mage');
  assert.equal(look('an orc shaman').model, 'mage');
  assert.ok(look('an orc shaman').tint !== undefined, 'green skin');
  const a = creatureLook({ short: 'a villager', name: 'villager', pv: 3040 });
  const b = creatureLook({ short: 'a villager', name: 'villager', pv: 3040, id: 99 });
  assert.deepEqual(a, b, 'stable per creature type, whatever its id');
});

test('the dead: dressed by what they were', () => {
  assert.equal(look('a skeletal warrior').model, 'skeleton_warrior');
  assert.equal(look('an ancient lich').model, 'skeleton_mage');
  assert.equal(look('a rotting zombie').model, 'skeleton_minion');
  assert.equal(look('a vampire spawn').model, 'rogue_hooded');
  assert.equal(look('the undead giant').beast.tint, 0x9ab08a, 'an undead giant is a rotten giant');
});

test('adjectives size and colour the body', () => {
  assert.ok(look('the baby dragon').beast.h < look('the red dragon').beast.h * 0.6);
  assert.equal(look('the red dragon').beast.tint, 0xc84030);
  assert.ok(look('the massive Minotaur').beast.h < 4, 'a massive minotaur still fits through a door');
  assert.equal(look('the large, grey wolf', { name: 'wolf' }).beast.tint, 0x9a9aa0);
  assert.ok(look('the large, grey wolf', { name: 'wolf' }).beast.h > 1, 'large');
});

test('a person whose room line names a creature takes that body', () => {
  assert.deepEqual(subjectOf('A massive rat-man standing here.'), ['massive', 'rat-man']);
  assert.deepEqual(subjectOf('A shifty-looking smuggler eyes you suspiciously.'), ['shifty-looking', 'smuggler']);
  assert.equal(body(look('the Sewer King', { name: 'sewer king', long: 'A massive rat-man standing here.' })), 'rat');
  assert.equal(look('the Ancient Guardian', { name: 'guardian', long: 'A towering stone golem stands watch, runes glowing.' }).model, 'knight');
  assert.ok(!look('a shifty smuggler', { long: 'A shifty-looking smuggler eyes you suspiciously.' }).beast);
});

// every model, weapon and prop a look names must exist in the art
function glbJson(file) {
  const b = fs.readFileSync(file);
  return JSON.parse(b.slice(20, 20 + b.readUInt32LE(12)).toString());
}

test('every creature in the world gets a body that exists, and no creature is drawn as a person', { skip: !fs.existsSync(path.join(ART, 'mobs/index.json')) }, () => {
  const mobs = loadMobs();
  assert.ok(mobs.length > 800, `${mobs.length} creatures`);
  const bad = suspects(mobs);
  assert.deepEqual(bad.map(({ m, look }) => `${m.pv} ${m.short} -> ${lookLabel(look)}`), []);
  const mobModels = new Set(Object.keys(JSON.parse(fs.readFileSync(path.join(ART, 'mobs/index.json'), 'utf8'))));
  const accessories = {}, kitModels = {};
  const accOf = model => accessories[model] || (accessories[model] = new Set(glbJson(path.join(ART, `chars/${model}.glb`)).nodes
    .filter(n => n.mesh != null && n.skin == null).map(n => n.name)));
  const kitOf = kit => kitModels[kit] || (kitModels[kit] = new Set((j => j.scenes[0].nodes.map(i => j.nodes[i].name))(glbJson(path.join(ART, `kits/${kit}.glb`)))));
  const procs = new Set(['rat', 'spider', 'snake', 'lizard', 'rabbit', 'slime']);
  for (const m of mobs) {
    const l = creatureLook(m), where = `${m.pv} ${m.short}`;
    if (l.beast) {
      const b = l.beast;
      assert.ok(b.h > 0.1 && b.h < 6, `${where}: height ${b.h}`);
      if (b.mob) assert.ok(mobModels.has(b.mob), `${where}: no creature model ${b.mob}`);
      else if (b.proc) assert.ok(procs.has(b.proc), `${where}: no body ${b.proc}`);
      else assert.ok(kitOf(b.prop[0]).has(b.prop[1]), `${where}: no prop ${b.prop}`);
    } else {
      assert.ok(fs.existsSync(path.join(ART, `chars/${l.model}.glb`)), `${where}: no character ${l.model}`);
      for (const item of l.loadout || []) {
        // a list may name the gear of several models ("Knight_Cape" or "Mage_Cape"): one must fit
        if (!accOf(l.model).has(item)) assert.ok(['Knight_Cape', 'Mage_Cape', 'Knife', '1H_Axe', 'Barbarian_Round_Shield'].includes(item), `${where}: ${l.model} has no ${item}`);
      }
      assert.ok(!l.scale || (l.scale > 0.3 && l.scale < 3), `${where}: scale ${l.scale}`);
    }
  }
});
