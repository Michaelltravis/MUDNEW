// The Blender-made models keep the house rules (docs/art/STYLE3D.md, tools/art3d/qc_models.mjs):
// one skinned mesh, one material, within budget, every clip.   node --test tests/web/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { checkAll, checkBody, BUDGET } from '../../tools/art3d/qc_models.mjs';

// a .glb holding only this JSON (no binary chunk needed for the checks)
function glb(json) {
  let s = Buffer.from(JSON.stringify(json));
  if (s.length % 4) s = Buffer.concat([s, Buffer.alloc(4 - (s.length % 4), 0x20)]);
  const h = Buffer.alloc(20);
  h.writeUInt32LE(0x46546c67, 0); h.writeUInt32LE(2, 4); h.writeUInt32LE(20 + s.length, 8);
  h.writeUInt32LE(s.length, 12); h.writeUInt32LE(0x4e4f534a, 16);
  return Buffer.concat([h, s]);
}
const good = (tris = 900, clips = ['Idle', 'Walk', 'Bite_Front', 'HitRecieve', 'Death']) => ({
  meshes: [{ primitives: [{ attributes: { POSITION: 0 }, indices: 1 }] }], skins: [{ joints: [0] }],
  nodes: [{ mesh: 0, skin: 0 }], materials: [{}], accessors: [{ count: 600 }, { count: tris * 3 }],
  animations: clips.map(name => ({ name })),
});

test('the checks: a good body passes; too many triangles, a missing clip, two materials do not', () => {
  const entry = { kind: 'creature', height: 1.1 };
  assert.deepEqual(checkBody('ok', entry, glb(good())), []);
  assert.match(checkBody('fat', entry, glb(good(BUDGET.creature + 1))).join(), /over the creature budget/);
  assert.deepEqual(checkBody('boss', { kind: 'boss', height: 3 }, glb(good(BUDGET.creature + 1))), [], 'a boss may have more');
  assert.match(checkBody('mute', entry, glb(good(900, ['Idle', 'Walk']))).join(), /missing clips Bite_Front, HitRecieve, Death/);
  const two = good(); two.materials.push({});
  assert.match(checkBody('two', entry, glb(two)).join(), /2 materials/);
  assert.match(checkBody('flat', { kind: 'creature', height: 0 }, glb(good())).join(), /height/);
});

test('every Blender model in art3d/bodies keeps the rules', () => {
  const { bad } = checkAll();
  assert.deepEqual(bad, []);
});
