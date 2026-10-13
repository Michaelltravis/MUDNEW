// Ability icons (world3d/hud/icons.js): no two abilities of a class look alike — the same picture
// in the same colour (stepwise and tower echoes were both the mage's rune).   node --test tests/web/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { iconOf, ICON_OVERRIDE, PICTO } from '../../src/web_isometric/world3d/hud/icons.js';
import { RECIPES } from '../../src/web_isometric/world3d/abilityfx-table.js';
import { DRAW } from '../../src/web_isometric/world3d/glyphs.js';

const look = (id, cls) => {
  const { p, sc } = iconOf(id, cls, 'spell');
  return `${p.picto ? `picto:${p.picto}` : p.glyph ? `glyph:${p.glyph}` : 'sigil'} in ${sc.join(',')}`;
};

test('every class: each ability its own icon', () => {
  for (const cls of Object.keys(RECIPES)) {
    const seen = new Map();
    for (const id of Object.keys(RECIPES[cls])) {
      const k = look(id, cls);
      assert.ok(!seen.has(k), `${cls}: ${id} looks like ${seen.get(k)} (${k})`);
      seen.set(k, id);
    }
  }
});

test('stepwise and tower echoes are told apart; every override draws something real', () => {
  assert.notEqual(look('stepwise', 'mage'), look('tower_echoes', 'mage'));
  for (const [cls, ids] of Object.entries(ICON_OVERRIDE)) {
    for (const [id, art] of Object.entries(ids)) {
      assert.ok(art.picto ? PICTO[art.picto] : DRAW[art.glyph], `${cls}.${id}: ${JSON.stringify(art)} is drawable`);
      assert.ok(RECIPES[cls] && RECIPES[cls][id], `${cls}.${id} is an ability`);
    }
  }
});
