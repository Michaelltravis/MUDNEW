// Check the Blender-made models (art3d/bodies, built by `node build.mjs blend`) keep the rules of
// docs/art/STYLE3D.md: one skinned mesh, one material, within the triangle budget for its kind,
// every clip the game needs. Needs nothing installed (it reads the .glb's own JSON).
//   node tools/art3d/qc_models.mjs        (tests/web/models.test.mjs runs the same checks)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const BUDGET = { creature: 3000, boss: 8000, prop: 1500, steed: 3000 };     // = blender/mhb/export.py
export const REQUIRED = ['Idle', 'Walk', 'Bite_Front', 'HitRecieve', 'Death'];    // = blender/mhb/clips.py
export const BODIES = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../src/web_isometric/art3d/bodies');

// the JSON chunk of a .glb
export function glbJson(buf) {
  if (buf.readUInt32LE(0) !== 0x46546c67) throw new Error('not a .glb');
  const len = buf.readUInt32LE(12), type = buf.readUInt32LE(16);
  if (type !== 0x4e4f534a) throw new Error('first chunk is not JSON');
  return JSON.parse(buf.subarray(20, 20 + len).toString('utf8'));
}

// what is wrong with one model ([] when nothing)
export function checkBody(name, entry, buf) {
  const bad = [];
  let g;
  try { g = glbJson(buf); } catch (e) { return [`${name}: ${e.message}`]; }
  const kind = entry.kind || 'creature';
  const budget = BUDGET[kind] ?? BUDGET.creature;
  const meshes = g.meshes || [], skins = g.skins || [], mats = g.materials || [];
  if (meshes.length !== 1) bad.push(`${name}: ${meshes.length} meshes (one skinned mesh wanted)`);
  if (skins.length !== 1) bad.push(`${name}: ${skins.length} skins (one wanted)`);
  if (!(g.nodes || []).some(n => n.mesh != null && n.skin != null)) bad.push(`${name}: the mesh is not skinned`);
  if (mats.length > 1) bad.push(`${name}: ${mats.length} materials (one palette material wanted)`);
  let tris = 0;
  for (const m of meshes) for (const p of m.primitives || []) {
    const acc = p.indices != null ? g.accessors[p.indices] : g.accessors[p.attributes.POSITION];
    tris += Math.floor(acc.count / 3);
  }
  if (tris > budget) bad.push(`${name}: ${tris} triangles, over the ${kind} budget of ${budget}`);
  const clips = (g.animations || []).map(a => a.name);
  const missing = REQUIRED.filter(c => !clips.includes(c));
  if (missing.length) bad.push(`${name}: missing clips ${missing.join(', ')}`);
  if (entry.anims && entry.anims.join() !== clips.join()) bad.push(`${name}: index.json lists clips ${entry.anims.join(', ')} but the file has ${clips.join(', ')}`);
  if (!(entry.height > 0.2)) bad.push(`${name}: height ${entry.height} (stand it up, feet at 0)`);
  return bad;
}

export function checkAll(dir = BODIES) {
  const file = path.join(dir, 'index.json');
  if (!fs.existsSync(file)) return { checked: 0, bad: [] };
  const index = JSON.parse(fs.readFileSync(file, 'utf8'));
  const bad = [];
  for (const [name, entry] of Object.entries(index)) {
    const glb = path.join(dir, `${name}.glb`);
    if (!fs.existsSync(glb)) { bad.push(`${name}: listed in index.json but ${name}.glb is missing`); continue; }
    bad.push(...checkBody(name, entry, fs.readFileSync(glb)));
  }
  return { checked: Object.keys(index).length, bad };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const { checked, bad } = checkAll();
  for (const b of bad) console.log('✗', b);
  console.log(`${checked} models checked, ${bad.length} problems`);
  process.exit(bad.length ? 1 : 0);
}
