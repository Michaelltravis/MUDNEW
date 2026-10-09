// Build the 3D client's art from the downloaded CC0 packs (see fetch.sh and
// docs/art/SOURCES.md). Usage:
//   cd tools/art3d && npm ci && node build.mjs <cache dir from fetch.sh>
// Output goes to src/web_isometric/art3d/. Three kinds of job:
//   char  - one rigged character, animations stripped (they live in the shared rig file)
//   anims - the shared animation set for every KayKit humanoid (same 41-joint rig)
//   kit   - many static models merged into ONE file: shared textures are stored once and
//           the client loads a whole kit with one request; each model is a top-level
//           node named after its key
import fs from 'node:fs';
import path from 'node:path';
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, prune, weld, resample, meshopt, textureCompress, mergeDocuments, unpartition } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
import sharp from 'sharp';

const CACHE = path.resolve(process.argv[2] || '.cache');
const OUT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../../src/web_isometric/art3d');

const ADV = 'kaykit-adventurers/addons/kaykit_character_pack_adventures/Characters/gltf';
const SKEL = 'kaykit-skeletons/addons/kaykit_character_pack_skeletons/Characters/gltf';
const DUN = 'kaykit-dungeon/addons/kaykit_dungeon_remastered/Assets/gltf';
const NAT = 'quaternius-nature/glTF';

const DUNGEON = ['wall', 'wall_corner', 'wall_doorway', 'wall_half', 'wall_broken', 'wall_arched',
  'wall_pillar', 'wall_endcap', 'floor_tile_large', 'floor_tile_small', 'floor_tile_small_broken_A',
  'floor_tile_small_weeds_A', 'floor_dirt_large', 'floor_dirt_large_rocky', 'pillar', 'pillar_decorated',
  'column', 'torch_mounted', 'torch_lit', 'barrel_large', 'barrel_small', 'box_large', 'box_stacked',
  'crates_stacked', 'chest', 'chest_gold', 'banner_patternA_red', 'banner_thin_red', 'rubble_large',
  'rubble_half', 'candle_lit', 'candle_triple', 'table_long_decorated_A', 'keg', 'stairs',
  'coin_stack_large', 'sword_shield'];
const NATURE = ['CommonTree_1', 'CommonTree_2', 'CommonTree_3', 'Pine_1', 'Pine_2', 'TwistedTree_1',
  'DeadTree_1', 'DeadTree_2', 'Bush_Common', 'Bush_Common_Flowers', 'Fern_1', 'Grass_Common_Short',
  'Grass_Common_Tall', 'Grass_Wispy_Tall', 'Flower_3_Group', 'Flower_4_Group', 'Mushroom_Common',
  'Rock_Medium_1', 'Rock_Medium_2', 'Rock_Medium_3', 'Pebble_Round_1', 'Pebble_Round_3',
  'RockPath_Round_Wide', 'Plant_1', 'Plant_7', 'Clover_1'];

const JOBS = [
  ...['Knight', 'Barbarian', 'Mage', 'Rogue', 'Rogue_Hooded'].map(n =>
    ({ kind: 'char', src: `${ADV}/${n}.glb`, out: `chars/${n.toLowerCase()}.glb` })),
  ...['Skeleton_Warrior', 'Skeleton_Minion', 'Skeleton_Mage', 'Skeleton_Rogue'].map(n =>
    ({ kind: 'char', src: `${SKEL}/${n}.glb`, out: `chars/${n.toLowerCase()}.glb` })),
  // the skeleton pack's set is a superset (95 clips) of the adventurers' (76), same rig
  { kind: 'anims', src: `${SKEL}/Skeleton_Warrior.glb`, out: 'chars/rig_anims.glb' },
  { kind: 'kit', out: 'kits/dungeon.glb', items: DUNGEON.map(k => ({ key: k, src: findFile(DUN, k) })) },
  // Quaternius meshes carry COLOR_0 as wind/shading masks for their own shader; glTF
  // multiplies it into the base colour, which paints the leaves red. Drop it.
  { kind: 'kit', out: 'kits/nature.glb', texture: 512, dropNormalMaps: true, dropVertexColors: true, greenLeaves: true,
    items: NATURE.map(k => ({ key: k, src: `${NAT}/${k}.gltf` })) },
];

function findFile(dir, key) {
  for (const f of [`${key}.gltf.glb`, `${key}.glb`]) if (fs.existsSync(path.join(CACHE, dir, f))) return `${dir}/${f}`;
  throw new Error(`missing ${dir}/${key}`);
}

const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({
  'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder,
});

async function finish(doc, job) {
  const tf = [dedup(), prune({ keepLeaves: false })];
  if (job.texture) {
    tf.push(textureCompress({ encoder: sharp, targetFormat: 'webp', resize: [job.texture, job.texture] }));
  }
  tf.push(meshopt({ encoder: MeshoptEncoder, level: 'medium' }), unpartition());
  await doc.transform(...tf);
  const out = path.join(OUT, job.out);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  await io.write(out, doc);
  return fs.statSync(out).size;
}

// Disposing an Animation alone leaves its samplers holding every keyframe accessor
// (a "mesh only" character stayed 2 MB); dispose the parts first.
function dropAnimation(a) {
  for (const c of a.listChannels()) c.dispose();
  for (const s of a.listSamplers()) s.dispose();
  a.dispose();
}

// The clips the client plays. The full set is 95; the rest (chairs, jumps, T-pose...) is
// dead weight in the one file every character needs before it can move.
const CLIPS = new Set(['Idle', 'Idle_B', 'Idle_Combat', 'Unarmed_Idle', '2H_Melee_Idle',
  'Walking_A', 'Walking_B', 'Walking_C', 'Walking_Backwards', 'Walking_D_Skeletons',
  'Running_A', 'Running_B', 'Running_C', 'Running_Strafe_Left', 'Running_Strafe_Right',
  '1H_Melee_Attack_Chop', '1H_Melee_Attack_Slice_Diagonal', '1H_Melee_Attack_Slice_Horizontal',
  '1H_Melee_Attack_Stab', '1H_Melee_Attack_Jump_Chop', '2H_Melee_Attack_Chop', '2H_Melee_Attack_Slice',
  '2H_Melee_Attack_Spin', '2H_Melee_Attack_Stab', 'Dualwield_Melee_Attack_Chop',
  'Dualwield_Melee_Attack_Slice', 'Dualwield_Melee_Attack_Stab', 'Unarmed_Melee_Attack_Punch_A',
  'Unarmed_Melee_Attack_Kick', '1H_Ranged_Aiming', '1H_Ranged_Shoot', '2H_Ranged_Aiming',
  '2H_Ranged_Shoot', 'Throw', 'Spellcast_Long', 'Spellcast_Raise', 'Spellcast_Shoot', 'Spellcasting',
  'Spellcast_Summon', 'Block', 'Blocking', 'Block_Hit', 'Block_Attack', 'Hit_A', 'Hit_B',
  'Dodge_Forward', 'Dodge_Backward', 'Dodge_Left', 'Dodge_Right', 'Death_A', 'Death_A_Pose',
  'Death_B', 'Death_B_Pose', 'Death_C_Skeletons', 'Cheer', 'Taunt', 'Interact', 'PickUp', 'Use_Item',
  'Sit_Floor_Down', 'Sit_Floor_Idle', 'Sit_Floor_StandUp', 'Lie_Down', 'Lie_Idle', 'Lie_StandUp',
  'Skeletons_Awaken_Floor', 'Skeletons_Awaken_Standing', 'Skeletons_Inactive_Floor_Pose',
  'Spawn_Ground_Skeletons']);

async function buildChar(job) {
  const doc = await io.read(path.join(CACHE, job.src));
  for (const a of doc.getRoot().listAnimations()) dropAnimation(a);
  await doc.transform(weld());
  return finish(doc, job);
}

async function buildAnims(job) {
  const doc = await io.read(path.join(CACHE, job.src));
  for (const n of doc.getRoot().listNodes()) { if (n.getMesh()) n.setMesh(null); n.setSkin(null); }
  for (const a of doc.getRoot().listAnimations()) if (!CLIPS.has(a.getName())) dropAnimation(a);
  await doc.transform(resample());
  return finish(doc, job);
}

async function buildKit(job) {
  const doc = await io.read(path.join(CACHE, job.items[0].src));
  const scene = doc.getRoot().getDefaultScene() || doc.getRoot().listScenes()[0];
  const wrap = (sc, key) => {
    const holder = doc.createNode(key);
    for (const child of sc.listChildren()) { sc.removeChild(child); holder.addChild(child); }
    return holder;
  };
  const first = wrap(scene, job.items[0].key);
  scene.addChild(first);
  for (const it of job.items.slice(1)) {
    const src = await io.read(path.join(CACHE, it.src));
    const map = mergeDocuments(doc, src);
    for (const sc of src.getRoot().listScenes()) {
      const merged = map.get(sc);
      scene.addChild(wrap(merged, it.key));
      merged.dispose();
    }
  }
  if (job.dropVertexColors) {
    for (const m of doc.getRoot().listMeshes()) for (const p of m.listPrimitives()) p.setAttribute('COLOR_0', null);
  }
  // the bushes share the twisted tree's autumn-red leaf atlas; a forest of red bushes
  // read as a bug, so their leaves are turned green (channel remix keeps the shading)
  for (const m of doc.getRoot().listMaterials()) {
    const tex = m.getBaseColorTexture();
    if (!job.greenLeaves || !tex || !/TwistedTree/i.test(m.getName())) continue;
    const img = await sharp(Buffer.from(tex.getImage()))
      .recomb([[0.25, 0.15, 0], [0.85, 0.25, 0], [0.1, 0.1, 0.2]]).png().toBuffer();
    tex.setImage(new Uint8Array(img)).setMimeType('image/png');
  }
  if (job.dropNormalMaps) {
    for (const m of doc.getRoot().listMaterials()) { m.setNormalTexture(null); m.setOcclusionTexture(null); }
  }
  await doc.transform(weld());
  return finish(doc, job);
}

// each source pack's licence travels with the built files
const LICENCES = {
  'kaykit-adventurers.txt': 'kaykit-adventurers/addons/kaykit_character_pack_adventures/LICENSE.txt',
  'kaykit-skeletons.txt': 'kaykit-skeletons/addons/kaykit_character_pack_skeletons/LICENSE.txt',
  'kaykit-dungeon-remastered.txt': 'kaykit-dungeon/addons/kaykit_dungeon_remastered/Assets/LICENSE.txt',
  'quaternius-stylized-nature-megakit.txt': 'quaternius-nature/License_Standard.txt',
};
fs.mkdirSync(path.join(OUT, 'licenses'), { recursive: true });
for (const [dst, src] of Object.entries(LICENCES)) fs.copyFileSync(path.join(CACHE, src), path.join(OUT, 'licenses', dst));

const only = process.argv[3];
for (const job of JOBS) {
  if (only && !job.out.includes(only)) continue;
  const size = job.kind === 'char' ? await buildChar(job) : job.kind === 'anims' ? await buildAnims(job) : await buildKit(job);
  console.log(`${job.out}  ${(size / 1024).toFixed(0)} KB`);
}
