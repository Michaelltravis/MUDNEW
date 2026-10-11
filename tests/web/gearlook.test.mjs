// Heroes dressed in what they wear (world3d/gearlook.js plans, procgear.js shapes) against the
// equipment kit's manifest (art3d/chars/equip.json).   node --test tests/web/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { planLook, swingClips, starterLook, kitIndex, CLASS_BASE, PROC } from '../../src/web_isometric/world3d/gearlook.js';
import { buildProc, SHAPES } from '../../src/web_isometric/world3d/procgear.js';

const ART = path.join(path.dirname(fileURLToPath(import.meta.url)), '../../src/web_isometric/art3d');
const kit = kitIndex(JSON.parse(fs.readFileSync(path.join(ART, 'chars/equip.json'), 'utf8')));
const CLASSES = Object.keys(CLASS_BASE);
const names = plan => plan.props.map(p => p.name);
const torso = plan => names(plan).find(n => n.endsWith('-Body'));

test("every class's starting look keeps its silhouette, and every piece it names is in the kit", () => {
  for (const cls of CLASSES) {
    const plan = planLook(starterLook(cls), cls, kit);
    assert.equal(torso(plan), `${CLASS_BASE[cls].model}-Body`, cls);
    for (const n of names(plan)) assert.ok(kit.pieces[n], `${cls}: ${n} is in the kit`);
    for (const pr of plan.procs) { assert.ok(SHAPES[pr.shape], `${cls}: ${pr.shape} can be built`); assert.ok(kit.pieces[pr.piece], `${pr.piece} lends its mount`); }
    const parts = names(plan).filter(n => /-(Head|HeadHooded|Body|ArmLeft|ArmRight|LegLeft|LegRight)$/.test(n));
    assert.equal(parts.length, 6, `${cls}: a whole body (${parts})`);
  }
});

test('armour two steps from the class changes the body; one step does not', () => {
  assert.equal(torso(planLook({ v: 1, sig: 'a', body: { w: 3, m: 'steel', t: 2 } }, 'mage', kit)), 'knight-Body', 'a mage in plate');
  assert.equal(torso(planLook({ v: 1, sig: 'b', body: { w: 0, c: 'red', t: 2 } }, 'warrior', kit)), 'mage-Body', 'a warrior in robes');
  assert.equal(torso(planLook({ v: 1, sig: 'c', body: { w: 3, m: 'steel', t: 2 } }, 'warrior', kit)), 'barbarian-Body', 'a warrior in plate stays a warrior');
  const legs = planLook({ v: 1, sig: 'd', body: { w: 0, t: 1 }, legs: { w: 3, m: 'iron', t: 1 } }, 'mage', kit);
  assert.ok(names(legs).includes('knight-LegLeft') && torso(legs) === 'mage-Body', 'plate greaves under robes');
});

test('a hood, a helm, a hat: the head', () => {
  assert.ok(names(planLook(starterLook('ranger'), 'ranger', kit)).includes('rogue-HeadHooded'), 'a ranger goes hooded');
  const helmed = names(planLook({ v: 1, sig: 'e', head: { k: 'helm', m: 'iron', t: 1 } }, 'ranger', kit));
  assert.ok(helmed.includes('rogue-Head') && helmed.includes('knight-Knight_Helmet'), 'a helmed ranger shows a face and a helm');
  assert.ok(names(planLook({ v: 1, sig: 'f', head: { k: 'hat', c: 'blue', t: 1 } }, 'mage', kit)).includes('mage-Mage_Hat'));
  const bare = names(planLook({ v: 1, sig: 'g', body: { w: 2, m: 'iron', t: 1 } }, 'warrior', kit));
  assert.ok(!bare.some(n => /Helmet|Hat|Cape/.test(n)), 'nothing worn, nothing drawn');
});

test('colours follow the gear: material, tier, cloth, set', () => {
  const remapOf = (plan, name) => plan.props.find(p => p.name === name).remap;
  const col = name => kit.col(name);
  const steel = remapOf(planLook({ v: 1, sig: 'h', body: { w: 3, m: 'gold', t: 3 } }, 'paladin', kit), 'knight-Body');
  assert.ok(Object.values(steel).includes(col('gold')) && Object.values(steel).includes(col('gold~dark')), 'gold plate is gold');
  const worn = remapOf(planLook({ v: 1, sig: 'i', body: { w: 2, m: 'iron', t: 0 } }, 'paladin', kit), 'knight-Body');
  assert.ok(Object.values(worn).includes(col('iron~worn')), 'tier 0 is worn');
  const set = remapOf(planLook({ v: 1, sig: 'j', back: { k: 'cloak', v: 'knight', s: 'chaos_weave', t: 3 } }, 'paladin', kit), 'knight-Knight_Cape');
  assert.ok(Object.values(set).includes(col('set_chaos_weave')), 'a set cloak in the set colours');
  const cls = remapOf(planLook(starterLook('cleric'), 'cleric', kit), 'knight-Body');
  assert.ok(Object.values(cls).some(c => kit.columns[c].name.startsWith('class_cleric')), "no colour of its own: the class's");
  // every remap points at a column that exists, and the authored ramps have their variants
  for (const cls2 of CLASSES) for (const p of planLook(starterLook(cls2), cls2, kit).props) for (const to of Object.values(p.remap || {})) assert.ok(kit.columns[to], `${cls2} ${p.name} -> ${to}`);
  for (const m of ['steel', 'iron', 'gold', 'mithril', 'red', 'class_mage', 'set_frostlords_mantle']) for (const v of ['', '~worn', '~dark', '~worn~dark']) {
    if (/~dark/.test(v) && !/steel|iron|gold|mithril|red|class|set/.test(m)) continue;
    assert.ok(kit.col(m + v) != null, `${m + v} in the palette`);
  }
});

test('the swing follows the hand: two hands, two blades, a bow, a staff, nothing', () => {
  assert.ok(swingClips({ main: { k: 'sword', h: 2 } }, 'paladin', false).every(c => c.startsWith('2H_Melee')));
  assert.ok(swingClips({ main: { k: 'dagger', h: 1 }, off: { k: 'dagger', h: 1 } }, 'thief', false).every(c => c.startsWith('Dualwield')));
  assert.ok(swingClips({ main: { k: 'sword', h: 1 }, off: { k: 'shield' } }, 'warrior', false).every(c => c.startsWith('1H_Melee')));
  assert.deepEqual(swingClips({ main: { k: 'bow', h: 2 } }, 'ranger', true), ['2H_Ranged_Shoot']);
  assert.deepEqual(swingClips({ main: { k: 'sword', h: 1 } }, 'ranger', true), ['Throw'], 'a ranger with no bow throws');
  assert.deepEqual(swingClips({ main: { k: 'staff', h: 2 } }, 'mage', true), ['Spellcast_Shoot']);
  assert.ok(swingClips({}, 'warrior', false).every(c => c.startsWith('Unarmed')));
  assert.equal(planLook({ v: 1, sig: 'k', main: { k: 'axe', h: 2, m: 'steel', t: 1 } }, 'warrior', kit).idle, '2H_Melee_Idle');
});

test('shapes built in code are whole, and painted from real palette columns', () => {
  const N = kit.N;
  const paint = role => (kit.col({ wood: 'wood', wood_dark: 'wood_dark', wood_pale: 'wood_pale', metal: 'steel', metal_dark: 'steel~dark', leather: 'leather', string: 'white', hole: 'black', gem: 'gem_red' }[role]) + 0.5) / N;
  for (const shape of new Set(Object.values(PROC))) {
    const g = buildProc(shape, { t: 1 }, paint);
    const verts = g.position.length / 3;
    assert.ok(verts > 30 && verts < 3000, `${shape}: ${verts} vertices`);
    assert.ok(g.index.every(i => i < verts), `${shape}: indices in range`);
    assert.ok([...g.position, ...g.normal, ...g.uv].every(Number.isFinite), `${shape}: finite`);
    for (let i = 0; i < g.uv.length; i += 2) {
      const c = g.uv[i] * N - 0.5;
      assert.ok(Math.abs(c - Math.round(c)) < 1e-4 && kit.columns[Math.round(c)], `${shape}: u on a column centre`);
    }
  }
});
