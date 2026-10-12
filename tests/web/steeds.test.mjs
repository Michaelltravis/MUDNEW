// Riding in /play (Push 34): every mount the server knows has a steed the creature kit can build,
// and the controller and main loop use the payload's speed.
//   node --test tests/web/
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { STEEDS, steedSpec } from '../../src/web_isometric/world3d/steedlogic.js';
import { kinRecipe } from '../../src/web_isometric/world3d/kinrecipe.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const serverMounts = () => {
  const src = fs.readFileSync(path.join(ROOT, 'src/mounts.py'), 'utf8');
  const keys = new Set();
  for (const m of src.matchAll(/'key': '([a-z_]+)'/g)) keys.add(m[1]);
  for (const m of src.matchAll(/_faction_mount\('([a-z_]+)'/g)) keys.add(m[1]);
  keys.add('nightmare_steed');
  return [...keys];
};

test('every mount the server knows has a steed', () => {
  const missing = serverMounts().filter(k => !STEEDS[k]);
  assert.deepEqual(missing, []);
});

test("every steed's body is one the creature kit builds, with a saddle on its back", () => {
  for (const key of Object.keys(STEEDS)) {
    const s = steedSpec(key);
    const r = kinRecipe(s.body, s.words, 7, s.tint);
    assert.ok(r && r.plan, `${key}: the kit builds a ${s.body}`);
    assert.ok(s.back > 0.4 && s.back < 1, `${key}: its saddle sits on its back (${s.back})`);
    assert.ok(s.height >= 0.7 && s.height <= 1.2, `${key}: sized beside its rider (${s.height})`);
  }
  assert.equal(steedSpec('no_such_mount').body, 'horse', 'an unknown mount is drawn as a horse');
});

test('the hero runs as fast as the server says, and sits while riding', () => {
  const read = f => fs.readFileSync(path.join(ROOT, 'src/web_isometric/world3d', f), 'utf8');
  const ctl = read('controller.js'), main = read('main.js'), ents = read('entities.js');
  assert.match(ctl, /\* \(this\.speedMul \|\| 1\)/, 'the run is multiplied by the speed');
  assert.match(ctl, /this\.mounted\) this\.actor\.play\('Idle'/, 'a rider plays their idle (the legs are posed by steed.js)');
  assert.match(main, /riding\.pose\(/, 'the hero is posed astride each frame');
  assert.match(ents, /e\.riding\.pose\(/, 'and so is everyone else riding');
  const steed = read('steed.js');
  assert.match(steed, /export function ridePose/, 'the riding pose');
  assert.ok(!/Sit_Floor/.test(ctl + main + ents + read('demo.js')), 'no rider sits cross-legged any more');
  assert.match(main, /ctl\.speedMul = .*p\.speed/, "main sets the speed from the payload's");
  assert.match(main, /mountRider\(hero, key/, 'main seats the hero on their steed');
  assert.match(ents, /mountRider\(e\.actor, w\.data\.mount/, 'other players ride theirs too');
});
