// The equipment kit (art3d/chars/equip.glb + equip.json, tools/art3d/build.mjs 'equip'): one
// rig, one material, every body part and piece, each hung where the manifest says, the palette
// as wide as its columns.   node --test tests/web/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ART = path.join(path.dirname(fileURLToPath(import.meta.url)), '../../src/web_isometric/art3d');
const GLB = path.join(ART, 'chars/equip.glb');
const buf = fs.readFileSync(GLB);
const jsonLen = buf.readUInt32LE(12);
const gltf = JSON.parse(buf.slice(20, 20 + jsonLen).toString());
const bin = buf.slice(20 + jsonLen + 8);
const manifest = JSON.parse(fs.readFileSync(path.join(ART, 'chars/equip.json'), 'utf8'));

const parentOf = new Map();
gltf.nodes.forEach((n, i) => (n.children || []).forEach(c => parentOf.set(c, i)));
const meshNodes = gltf.nodes.map((n, i) => ({ ...n, i })).filter(n => n.mesh != null);

test('one rig of 41 joints, in the manifest\'s order, and one material', () => {
  assert.equal(gltf.skins.length, 1);
  const joints = gltf.skins[0].joints.map(j => gltf.nodes[j].name);
  assert.equal(joints.length, 41);
  assert.deepEqual(joints, manifest.joints);
  assert.equal(gltf.materials.length, 1);
  assert.equal(gltf.materials[0].name, 'equip');
});

test('every model has a whole body, and the rogue a hooded head', () => {
  for (const model of ['knight', 'barbarian', 'mage', 'rogue']) {
    for (const part of ['Head', 'Body', 'ArmLeft', 'ArmRight', 'LegLeft', 'LegRight']) {
      const name = `${model}-${part}`;
      const n = meshNodes.find(x => x.name === name);
      assert.ok(n && n.skin === 0, `${name} is skinned to the rig`);
      assert.equal(manifest.models[model][part], name);
    }
  }
  assert.ok(meshNodes.some(n => n.name === 'rogue-HeadHooded' && n.skin === 0));
});

test('every piece hangs from a hand, the head or the chest, as the manifest says', () => {
  const BONES = new Set(['handslot.l', 'handslot.r', 'head', 'chest']);
  for (const n of meshNodes.filter(x => x.skin == null)) {
    const bone = gltf.nodes[parentOf.get(n.i)].name;
    assert.ok(BONES.has(bone), `${n.name} hangs from ${bone}`);
    assert.equal(manifest.pieces[n.name].bone, bone, n.name);
    assert.equal(manifest.pieces[n.name].type, 'prop');
  }
});

test('the manifest and the file agree, and every piece paints from real columns', () => {
  const inFile = new Set(meshNodes.map(n => n.name));
  assert.deepEqual(new Set(Object.keys(manifest.pieces)), inFile);
  for (const [name, p] of Object.entries(manifest.pieces)) {
    assert.ok(Object.keys(p.cols).length > 0, `${name} paints something`);
    for (const c of Object.keys(p.cols)) assert.ok(manifest.columns[c], `${name}: column ${c}`);
    assert.ok(p.tris > 20, `${name}: ${p.tris} triangles`);
  }
  assert.ok(Object.values(manifest.pieces).some(p => p.bone === 'chest' && p.model === 'kit'), 'the quiver');
});

test('the palette is as wide as its columns', () => {
  const img = gltf.images.find(i => i.name === 'equip_palette');
  const view = gltf.bufferViews[img.bufferView];
  const png = bin.slice(view.byteOffset || 0, (view.byteOffset || 0) + view.byteLength);
  assert.equal(png.toString('ascii', 1, 4), 'PNG');
  assert.equal(png.readUInt32BE(16), manifest.palette.cols * manifest.palette.w);
  assert.equal(png.readUInt32BE(20), manifest.palette.h);
  assert.equal(manifest.columns.length, manifest.palette.cols);
});
