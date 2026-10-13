// The spells on a character, shown while they last (world3d/wards.js), and one buff icon a spell
// (hud/buffs.js).   node --test tests/web/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { readFileSync } from 'node:fs';
import { register } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const THREE_URL = pathToFileURL(path.join(HERE, '../../src/web_isometric/vendor/three/three.module.min.js')).href;
register('data:text/javascript,' + encodeURIComponent(
  `export async function resolve(s, c, next) { return s === 'three' ? { url: ${JSON.stringify(THREE_URL)}, shortCircuit: true } : next(s, c); }`));
const THREE = await import('three');
const { WARDS, wardPlan, planKey, Wards } = await import('../../src/web_isometric/world3d/wards.js');
const { buffList } = await import('../../src/web_isometric/world3d/hud/buffs.js');

test('a plan: the strongest shell, two orbits at most, a ring, motes, flying', () => {
  const p = wardPlan(['shielded', 'sanctuary', 'stoneskin', 'fire_shield', 'ice_armor', 'prot_evil', 'bless', 'fly', 'nonsense']);
  assert.equal(p.shell, WARDS.sanctuary.shell, 'sanctuary outshines a shield');
  assert.deepEqual(p.orbits.map(o => o.kind), ['stone', 'flame']);
  assert.equal(p.ring, WARDS.prot_evil.ring);
  assert.equal(p.motes.length, 1);
  assert.equal(p.hover, true);
  assert.equal(planKey(['fly', 'nonsense', 'bless']), 'bless,fly');
  assert.equal(planKey(['nonsense']), '');
});

test('every ward the server sends has a look (map_system.WARD_FLAGS, WARD_NAMES)', () => {
  const src = readFileSync(path.join(HERE, '../../src/map_system.py'), 'utf8');
  const flags = src.match(/WARD_FLAGS = frozenset\(\{([^}]*)\}\)/)[1].match(/'([a-z_]+)'/g).map(s => s.slice(1, -1));
  const names = [...src.match(/WARD_NAMES = \{([^}]*)\}/)[1].matchAll(/: '([a-z_]+)'/g)].map(m => m[1]);
  for (const k of [...flags, ...names]) assert.ok(WARDS[k], `${k} is drawn`);
});

const body = () => {
  const root = new THREE.Group();
  const m = new THREE.Mesh(new THREE.BoxGeometry(0.6, 1.8, 0.4), new THREE.MeshStandardMaterial());
  m.position.y = 0.9;
  root.add(m);
  const scene = new THREE.Scene();
  scene.add(root);
  return { root, m };
};
const fx = { near: () => true, p: { emit() {} } };

test('worn while it lasts: a shell and orbit on the body, flying lifts it, and all of it goes when the spell ends', () => {
  const w = new Wards({ quality: { name: 'high' } }, fx);
  const a = body();
  w.update(0.1, 1, a, ['shielded', 'stoneskin', 'fly']);
  const parts = a.root.children.filter(c => /^ward_/.test(c.name)).map(c => c.name);
  assert.ok(parts.includes('ward_shell') && parts.includes('ward_stone') && parts.includes('ward_wind'), parts.join(','));
  assert.ok(a.m.position.y > 0.9 + 0.25, `flying lifts the body (${a.m.position.y.toFixed(2)})`);
  w.update(0.1, 1.1, a, ['stoneskin']);              // the shield and the flight end
  assert.ok(!a.root.children.some(c => c.name === 'ward_shell'), 'the shell is gone');
  assert.ok(Math.abs(a.m.position.y - 0.9) < 1e-6, 'back on the ground');
  w.update(0.1, 1.2, a, []);
  assert.equal(a.root.children.filter(c => /^ward_/.test(c.name)).length, 0, 'nothing left');
});

test('others are warded nearest first, within the budget; invisibility only shows on yourself', () => {
  const w = new Wards({ quality: { name: 'low' } }, fx);
  const hero = body();
  const others = Array.from({ length: 6 }, (_, i) => { const b = body(); b.root.position.x = i + 1; return [b, ['shielded', 'invisible']]; });
  w.update(0.1, 1, hero, ['invisible'], others);
  assert.equal(w.on.size, 4, 'the hero and the three nearest (low)');
  assert.ok(w.on.get(others[0][0]).plan.fade === false && w.on.get(hero).plan.fade === true);
  assert.ok(hero.m.material.transparent && hero.m.material.opacity < 0.5, 'you see yourself faint');
  w.update(0.1, 1.1, hero, [], others);
  assert.equal(hero.m.material.opacity, 1, 'and whole again');
});

test('mounting while flying: the saddle sets the height (steed.js takes the hover off)', () => {
  const src = readFileSync(path.join(HERE, '../../src/web_isometric/world3d/steed.js'), 'utf8');
  assert.match(src, /const hover = rider\.root\.userData\.wardLift \|\| 0;/);
  assert.match(src, /c\.position\.y - hover/);
});

test('one buff icon a spell: Armor\'s two affects show once, with the longer time', () => {
  const list = buffList([
    { name: 'armor', applies_to: 'ac', remaining: 90, duration: 150 },
    { name: 'armor', applies_to: 'armour_ward', remaining: 120, duration: 150 },
    { name: 'Bless', remaining: 10, duration: 24 }, { name: 'bless', remaining: 5, duration: 24 }, null, {}]);
  assert.deepEqual(list.map(a => [a.name, a.remaining]), [['armor', 120], ['Bless', 10]]);
});
