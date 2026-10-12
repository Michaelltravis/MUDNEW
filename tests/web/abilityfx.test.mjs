// Every ability's own look (world3d/abilityfx.js + abilityfx-table.js), checked against the
// server's class books (tests/web/fixtures/abilitybook.json, written by
// tools/dump_abilitybook.py) without a running server.
//   node --test tests/web/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { RECIPES } from '../../src/web_isometric/world3d/abilityfx-table.js';
import { THEMES, CLIPS, parse, validate, signature, timeline, recipeFor } from '../../src/web_isometric/world3d/abilityfx.js';

const BOOK = JSON.parse(readFileSync(new URL('./fixtures/abilitybook.json', import.meta.url)));
const active = cls => [...BOOK.classes[cls].filter(r => !r.passive), ...(BOOK.extras[cls] || [])];

test('every class has a theme and a table', () => {
  for (const cls of Object.keys(BOOK.classes)) {
    assert.ok(THEMES[cls], `${cls} has a theme`);
    assert.ok(RECIPES[cls], `${cls} has a recipe table`);
  }
});

test('every ability a class can use has its own line (book, talents and extras)', () => {
  const missing = [];
  for (const cls of Object.keys(BOOK.classes)) for (const a of active(cls)) if (!RECIPES[cls][a.id]) missing.push(`${cls}:${a.id}`);
  assert.deepEqual(missing, []);
});

test('no line is left over from an ability the class no longer has', () => {
  const stale = [];
  for (const [cls, table] of Object.entries(RECIPES)) {
    const ids = new Set(active(cls).map(a => a.id));
    for (const id of Object.keys(table)) if (!ids.has(id)) stale.push(`${cls}:${id}`);
  }
  assert.deepEqual(stale, []);
});

test('every line parses, names clips the rig has and known effects', () => {
  const bad = [];
  for (const [cls, table] of Object.entries(RECIPES)) {
    for (const [id, line] of Object.entries(table)) {
      const problems = validate(line, BOOK.clips);
      if (problems.length) bad.push(`${cls}:${id}: ${problems.join(', ')}`);
    }
  }
  assert.deepEqual(bad, []);
  for (const clip of Object.values(CLIPS)) assert.ok(BOOK.clips.includes(clip), `the rig has ${clip}`);
});

test('no two abilities of a class look alike (clip, motion, cast, travel, land, aura)', () => {
  for (const [cls, table] of Object.entries(RECIPES)) {
    const seen = new Map();
    for (const [id, line] of Object.entries(table)) {
      const sig = signature(line);
      assert.ok(!seen.has(sig), `${cls}: ${id} looks like ${seen.get(sig)} (${sig})`);
      seen.set(sig, id);
    }
  }
});

test('a spell or skill several classes know looks different in each', () => {
  const by = new Map();
  for (const [cls, table] of Object.entries(RECIPES)) for (const [id, line] of Object.entries(table)) {
    if (!by.has(id)) by.set(id, []);
    by.get(id).push([cls, signature(line)]);
  }
  for (const [id, list] of by) {
    const sigs = new Set(list.map(([, s]) => s));
    assert.equal(sigs.size, list.length, `${id} is shared by ${list.map(([c]) => c).join(', ')} and must differ`);
  }
});

test('each class shows its own sigil and colours, and its marks are varied', () => {
  for (const [cls, table] of Object.entries(RECIPES)) {
    const lines = Object.values(table).map(parse);
    const sigils = lines.filter(r => [r.cast, r.land, r.aura].some(t => t && t.kind === 'sigil')).length;
    assert.ok(sigils >= 2, `${cls} draws its sigil (${THEMES[cls].sigil}) in at least two abilities (${sigils})`);
    const clips = new Set(lines.map(r => r.clip));
    assert.ok(clips.size >= Math.min(6, lines.length / 2), `${cls} uses varied clips (${clips.size})`);
  }
  const cores = new Set(Object.entries(THEMES).filter(([c]) => c !== 'creature').map(([, t]) => t.core));
  assert.equal(cores.size, 9, 'nine classes, nine core colours');
});

test('aimed abilities travel or land on their target; self abilities stay on their user', () => {
  const odd = [];
  for (const cls of Object.keys(BOOK.classes)) {
    for (const a of active(cls)) {
      const r = parse(RECIPES[cls][a.id]);
      if (a.target === 'enemy' && !r.travel && !r.land && !r.motion) odd.push(`${cls}:${a.id} (enemy) shows nothing at the target`);
      if (a.target === 'self' && r.travel && ['arrow', 'arrows', 'bolt', 'chain'].includes(r.travel.kind) && a.id !== 'charge_release') odd.push(`${cls}:${a.id} (self) shoots`);
      if (!r.cast && !r.travel && !r.land && !r.aura) odd.push(`${cls}:${a.id} has no effect at all`);
    }
  }
  assert.deepEqual(odd, []);
});

test('timeline: a blow lands after it is released; a bolt after its flight', () => {
  const fb = parse(RECIPES.mage.fireball), strike = parse(RECIPES.warrior.strike), leap = parse(RECIPES.warrior.heroic_leap);
  const a = timeline(fb, 10), b = timeline(fb, 2);
  assert.ok(a.land > a.release && a.land > b.land, 'a farther fireball lands later');
  assert.ok(timeline(strike, 2).land < 0.6, 'a strike lands quickly');
  assert.ok(timeline(leap, 8).release >= 0.5, 'a leap comes down after its arc');
});

test('recipeFor: the class line, else one from what the event says (creatures, unknowns)', () => {
  const r = recipeFor(RECIPES, 'Fireball', 'Mage', { k: 'spell', school: 'fire' });
  assert.equal(r.known, true);
  assert.equal(r.clip, 'shoot');
  const mob = recipeFor(RECIPES, 'fireball', null, { k: 'spell', school: 'fire' });
  assert.equal(mob.known, false);
  assert.equal(mob.cls, 'creature');
  assert.equal(mob.land.kind, 'blast');
  const odd = recipeFor(RECIPES, 'some_new_trick', 'warrior', { k: 'ability', shape: 'nova:6' });
  assert.equal(odd.land.kind, 'nova');
  assert.deepEqual(validate('cheer | rings | - | nova | - | physical'), []);
  assert.ok(validate('dance | - | - | nova | - | ').length, 'an unknown clip is caught');
  assert.ok(validate('cheer | - | - | explode | - | ').length, 'an unknown effect is caught');
});
