// Scrolling combat text (world3d/sctlogic.js): numbers in the colour of their harm.
//   node --test tests/web/
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { SCHOOL_CSS, titleOf, harmColour } from '../../src/web_isometric/world3d/sctlogic.js';

test('a wound is drawn in its school\'s colour', () => {
  assert.equal(harmColour('fire'), SCHOOL_CSS.fire);
  assert.equal(harmColour('frost'), SCHOOL_CSS.frost);
  assert.notEqual(SCHOOL_CSS.fire, SCHOOL_CSS.frost);
  for (const s of ['fire', 'frost', 'lightning', 'arcane', 'holy', 'shadow', 'nature', 'poison', 'necrotic', 'blood']) assert.ok(SCHOOL_CSS[s], s);
});

test("a physical blow is cream, or a glowing weapon's element", () => {
  assert.equal(harmColour(null), SCHOOL_CSS.physical);
  assert.equal(harmColour('physical', { main: { e: 'fire', t: 4 } }), SCHOOL_CSS.fire, 'a glowing fire blade burns orange');
  assert.equal(harmColour('physical', { main: { e: 'fire', t: 2 } }), SCHOOL_CSS.physical, 'a weak enchantment does not');
  assert.equal(harmColour('frost', { main: { e: 'fire', t: 5 } }), SCHOOL_CSS.frost, "the spell's school wins over the weapon");
});

test('ability names are titled', () => {
  assert.equal(titleOf('pyroblast'), 'Pyroblast');
  assert.equal(titleOf('meteor_storm'), 'Meteor Storm');
  assert.equal(titleOf(''), '');
});
