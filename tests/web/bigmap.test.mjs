// The big map (M): its zone tab zooms and pans, and shows any zone you have been to from the
// zone list (hud/minimap.js); the world tab zooms too.   node --test tests/web/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createMinimap, mapOfZone, middleOf, zoneIndex, ZOOM_MIN, ZOOM_MAX } from '../../src/web_isometric/world3d/hud/minimap.js';

const read = f => readFileSync(new URL(`../../${f}`, import.meta.url), 'utf8');

// a canvas and its window, enough for the map to draw into nothing
function fakeMap() {
  const on = {};
  const ctx = new Proxy({}, { get: (t, k) => (k in t ? t[k] : () => ({ addColorStop() {} })), set: (t, k, v) => { t[k] = v; return true; } });
  const cv = { width: 440, height: 270, style: {}, title: '', getContext: () => ctx,
    addEventListener: (k, f) => { on[k] = f; }, getBoundingClientRect: () => ({ left: 0, top: 0, width: 220, height: 135 }),
    setPointerCapture() {} };
  const text = {};
  const el = k => (text[k] = text[k] || { textContent: '', addEventListener() {}, firstElementChild: { style: {} }, classList: { toggle() {} } });
  const root = { querySelector: q => (q === 'canvas' ? cv : q === '.mm-north' ? null : el(q)) };
  return { root, on, text };
}
const zm = (zone, name, cells) => ({ zone, name, rooms: cells.map(([vnum, x, y]) => ({ vnum, name: `room ${vnum}`, cell: [x, y], exits: {}, flags: [] })) });

test('a zone to look at: its rooms in their cells, opened at its middle', () => {
  const z = mapOfZone(zm(31, 'Sewers', [[3101, 0, 0], [3102, 3, 0], [3103, 3, 2]]));
  assert.equal(z.num, 31);
  assert.equal(z.cells.get('3,2').vnum, 3103);
  assert.deepEqual(middleOf(z), { x: 2, y: 1.5 });
});

test('the zone list: zones you have set foot in and the one you stand in, by name', () => {
  const atlas = { zones: [{ id: 30, name: 'Midgaard' }, { id: 31, name: 'Sewers' }, { id: 32, name: 'Arachnos' }, { id: -1, name: 'Unknown' }],
    rooms: [{ vnum: 1, zone: 30 }, { vnum: 2, zone: 30 }, { vnum: 3, zone: 31 }, { vnum: 4, zone: 32 }, { vnum: 5, zone: -1 }] };
  assert.deepEqual(zoneIndex(atlas, [1, 2, 3, 5]).map(z => [z.name, z.n]), [['Midgaard', 2], ['Sewers', 1]]);
  assert.deepEqual(zoneIndex(atlas, [3], 32).map(z => z.name), ['Arachnos', 'Sewers'], 'where you stand, though not yet counted');
});

test('the big map zooms within bounds, looks at another zone, and comes home', () => {
  const { root, on, text } = fakeMap();
  const picked = [];
  const mm = createMinimap(root, r => picked.push(r.vnum), null, { cell: 1.7, browse: true });
  const mine = mapOfZone(zm(30, 'Midgaard', [[3001, 0, 0], [3002, 1, 0]]));
  mm.setZone(mine);
  for (let i = 0; i < 40; i++) mm.zoomBy(1.25);
  assert.equal(mm.zoom, ZOOM_MAX);
  for (let i = 0; i < 40; i++) mm.zoomBy(0.8);
  assert.equal(mm.zoom, ZOOM_MIN);
  assert.ok(on.wheel && on.pointerdown && on.pointermove, 'the wheel zooms and a drag pans');

  mm.browse(mapOfZone(zm(31, 'Sewers', [[3101, 0, 0]])), [3101]);
  assert.equal(mm.browsing(), 31);
  assert.equal(text['.mm-zone'].textContent, 'Sewers');
  assert.match(text['.mm-room'].textContent, /Looking at Sewers · you are in Midgaard/);
  mm.update({ x: 12, z: 7 }, 0, 0);
  on.click({ clientX: 110, clientY: 67 });
  assert.deepEqual(picked, [], "another zone's rooms are looked at, not walked to");

  mm.home();
  assert.equal(mm.browsing(), null);
  assert.equal(text['.mm-zone'].textContent, 'Midgaard');
  mm.browse(mapOfZone(zm(30, 'Midgaard', [])));
  assert.equal(mm.browsing(), null, 'your own zone is just home');
});

test('wired: the zone list, the zoom buttons, and the world map opening a zone', () => {
  const html = read('src/web_isometric/world3d/play.html'), main = read('src/web_isometric/world3d/main.js');
  assert.match(html, /class="bm-zones"/);
  assert.match(html, /class="bm-zoom"[^]*data-z="in"[^]*data-z="out"[^]*data-z="home"/);
  assert.match(main, /browse: true/);
  assert.match(main, /zoneIndex\(atlas, knownRooms, here\)/);
  assert.match(main, /fetchZonemap\(`zone=\$\{id\}`\)/);
  assert.match(read('src/web_isometric/world3d/hud/worldmap.js'), /focusZone\(id\)/);
});
