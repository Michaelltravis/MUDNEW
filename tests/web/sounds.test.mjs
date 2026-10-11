// Sound for /play (world3d/soundtable.js, audio.js): every sound is playable, every file it
// names was built, every combat event and blow has a sound or an explicit silence, and every
// name the game asks for exists.
//   node --test tests/web/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { SOUNDS, FILES, EVENTS, LANDS, SCHOOLS, schoolOf, MUSIC, BEDS, musicFor, bedFor, surfaceFor, VOICES } from '../../src/web_isometric/world3d/soundtable.js';

const W3D = path.join(path.dirname(fileURLToPath(import.meta.url)), '../../src/web_isometric/world3d');
const AUDIO = path.join(W3D, 'audio');

// audio.js builds its engine on import: a page's window/document are enough for that
globalThis.window = globalThis.window || { addEventListener() {}, removeEventListener() {} };
globalThis.document = globalThis.document || { addEventListener() {}, hidden: false };
const { SYNTHS } = await import('../../src/web_isometric/world3d/audio.js');

test('every sound is one recorded file, one synth, or layers of other sounds', () => {
  for (const [name, d] of Object.entries(SOUNDS)) {
    const kinds = ['file', 'synth', 'layers'].filter(k => d[k]);
    assert.equal(kinds.length, 1, `${name}: ${kinds.join('+') || 'nothing'}`);
    if (d.file) assert.ok(FILES[d.file], `${name}: no recorded file "${d.file}"`);
    if (d.synth) assert.equal(typeof SYNTHS[d.synth], 'function', `${name}: no synth "${d.synth}"`);
    if (d.layers) for (const l of d.layers) assert.ok(SOUNDS[l] && !SOUNDS[l].layers, `${name}: layer "${l}" missing or nested`);
    if (d.vol != null) assert.ok(d.vol > 0 && d.vol <= 1, `${name}: volume ${d.vol}`);
    if (d.bus) assert.ok(['sfx', 'ui', 'amb'].includes(d.bus), `${name}: bus ${d.bus}`);
  }
});

test('every recorded file was built (tools/audio/build.py), with as many variants as the table says', () => {
  const built = JSON.parse(fs.readFileSync(path.join(AUDIO, 'files.json'), 'utf8'));
  assert.deepEqual(Object.keys(FILES).sort(), Object.keys(built.sfx).sort(), 'soundtable FILES and audio/files.json list the same keys');
  for (const [k, n] of Object.entries(FILES)) {
    assert.equal(built.sfx[k], n, `${k}: ${n} variants in the table, ${built.sfx[k]} built`);
    for (let i = 1; i <= n; i++) assert.ok(fs.statSync(path.join(AUDIO, 'sfx', `${k}_${i}.mp3`)).size > 500, `${k}_${i}.mp3`);
  }
  for (const m of MUSIC) assert.ok(fs.statSync(path.join(AUDIO, 'music', `${m}.mp3`)).size > 100000, `music/${m}.mp3`);
  assert.ok(fs.readFileSync(path.join(AUDIO, 'CREDITS.md'), 'utf8').includes('CC0'), 'the credits are there');
});

test('every combat event and every blow has a sound or an explicit silence', () => {
  // combat_events.py: the kinds the server sends
  for (const k of ['attack', 'ability', 'spell', 'dmg', 'heal', 'buff', 'debuff', 'windup', 'resolve', 'cancel', 'death', 'stun', 'oor', 'fizzle', 'move']) {
    assert.ok(k in EVENTS, `event "${k}" has no entry`);
    if (EVENTS[k]) assert.ok(SOUNDS[EVENTS[k]], `event "${k}" names a missing sound`);
  }
  for (const r of ['hit', 'crit', 'miss', 'dodge', 'parry', 'block', 'resist', 'immune']) assert.ok(SOUNDS[LANDS[r]], `result "${r}"`);
  for (const s of ['fire', 'frost', 'lightning', 'arcane', 'holy', 'shadow', 'necrotic', 'nature', 'poison', 'sound', 'physical', 'blood']) {
    const imp = SCHOOLS[schoolOf(s)].impact;
    if (imp) assert.ok(SOUNDS[imp], `school ${s}: impact ${imp}`);
  }
});

test('every name the game plays exists in the table', () => {
  const files = ['combat.js', 'fxdirector.js', 'main.js', 'gallery.js', 'hud/hud.js', 'hud/inventory.js'];
  const asked = new Set();
  for (const f of files) {
    const src = fs.readFileSync(path.join(W3D, f), 'utf8');
    for (const m of src.matchAll(/(?:sound\.play|this\.sfx|sfx)\(\s*'([a-z_]+)'/g)) asked.add(m[1]);
    // names chosen in a table or a ternary, then played: 'name' : 'name' / { verb: 'name' }
    for (const m of src.matchAll(/sound\.play\(\{([^}]+)\}/g)) for (const n of m[1].matchAll(/'([a-z_]+)'/g)) asked.add(n[1]);
  }
  for (const n of ['hurt', 'hit_blade', 'hit', 'shot', 'bolt', 'swing', 'hero_death', 'death', 'door_open', 'door_close', 'lock', 'step_water', 'shatter_big']) asked.add(n);
  assert.ok(asked.size > 30, `found ${asked.size} names`);
  for (const n of asked) assert.ok(SOUNDS[n], `"${n}" is played but not in soundtable.js`);
});

test('every zone look has music, a room tone and footsteps', () => {
  const keys = Object.keys(BEDS).concat([null, 'unknown']);
  const themes = ['inside', 'city', 'field', 'forest', 'hills', 'mountain', 'water_swim', 'water_noswim', 'underwater', 'flying', 'desert', 'swamp', 'cave', 'dungeon'];
  for (const zoneKey of keys) for (const theme of themes) {
    const look = { theme, zoneKey, interior: theme === 'inside' ? 'tavern' : null };
    assert.ok(MUSIC.includes(musicFor(look)), `music for ${theme}/${zoneKey}`);
    assert.ok(BEDS[bedFor(look)], `bed for ${theme}/${zoneKey}`);
    assert.ok(SOUNDS[surfaceFor(look)], `footsteps for ${theme}/${zoneKey}`);
  }
  assert.equal(musicFor({ theme: 'inside', interior: 'tavern' }), 'inn', 'a tavern plays the inn tune');
  assert.equal(musicFor({ theme: 'field', zoneKey: 'necropolis' }), 'dark');
  assert.equal(surfaceFor({ theme: 'field', snowy: true }), 'step_snow');
  for (const q of ['low', 'medium', 'high']) assert.ok(VOICES[q] >= 8, `voices at ${q}`);
});

test('every synth plays on a stand-in audio context and says how long it rings', () => {
  const param = () => ({ value: 0, setValueAtTime() {}, exponentialRampToValueAtTime(v) { assert.ok(v > 0, 'exponential ramps must stay above 0'); },
    linearRampToValueAtTime() {}, setTargetAtTime() {}, cancelScheduledValues() {} });
  const node = () => ({ connect() {}, disconnect() {}, start() {}, stop() {}, frequency: param(), gain: param(), Q: param(), pan: param(),
    playbackRate: param(), type: '', buffer: null });
  const ctx = { currentTime: 0, sampleRate: 48000, createOscillator: node, createGain: node, createBiquadFilter: node, createBufferSource: node,
    createBuffer: (ch, n, sr) => ({ sampleRate: sr, getChannelData: () => new Float32Array(n) }) };
  for (const [name, fn] of Object.entries(SYNTHS)) {
    for (const opts of [{}, { tier: 0 }, { tier: 2 }, { school: 'frost' }, { school: 'nobody' }]) {
      const secs = fn(ctx, node(), opts);
      assert.ok(secs > 0 && secs < 4, `${name} ${JSON.stringify(opts)} rings ${secs}s`);
    }
  }
});
