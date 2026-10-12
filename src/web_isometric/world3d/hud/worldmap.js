// The whole world (the big map's World tab): every room you have explored, from the atlas
// (/atlas: all rooms with their world coordinates and zones) and your explored rooms
// (/explored), each a square in its zone's colour, zone names over their middles, and you.
// Drag to pan, the wheel zooms, hover for a room's name.

// what to draw, from the atlas and the rooms you know: {rooms, zones: [{id, name, x, y}], bounds}
export function worldView(atlas, explored, level = 0) {
  const known = new Set(explored || []);
  const rooms = ((atlas && atlas.rooms) || []).filter(r => known.has(r.vnum) && (r.z || 0) === level);
  const zinfo = new Map(((atlas && atlas.zones) || []).map(z => [z.id, z]));
  const sums = new Map();
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const r of rooms) {
    minX = Math.min(minX, r.x); maxX = Math.max(maxX, r.x); minY = Math.min(minY, r.y); maxY = Math.max(maxY, r.y);
    const s = sums.get(r.zone) || { x: 0, y: 0, n: 0 };
    s.x += r.x; s.y += r.y; s.n++;
    sums.set(r.zone, s);
  }
  const zones = [...sums.entries()].map(([id, s]) => ({ id, name: (zinfo.get(id) || {}).name || '', color: (zinfo.get(id) || {}).color || '#888',
    x: s.x / s.n, y: s.y / s.n, n: s.n }));
  return { rooms, zones, colors: new Map([...zinfo.values()].map(z => [z.id, z.color])),
    bounds: rooms.length ? { minX, maxX, minY, maxY } : null };
}

export function createWorldMap(canvas, { fetchAtlas, fetchExplored, here }) {
  let atlas = null, explored = [], view = null, zoom = 9, cx = 0, cy = 0, drag = null, hover = null, open = false;
  const ctx = canvas.getContext('2d');
  async function load() {
    try {
      if (!atlas) atlas = await fetchAtlas();
      explored = (await fetchExplored()).rooms || [];
    } catch (_) { /* drawn empty */ }
    const me = here();
    const meRoom = me && atlas ? atlas.rooms.find(r => r.vnum === me) : null;
    view = worldView(atlas, explored, meRoom ? meRoom.z || 0 : 0);
    if (meRoom) { cx = meRoom.x; cy = meRoom.y; }
    draw();
  }
  function toScreen(x, y) { return [canvas.width / 2 + (x - cx) * zoom, canvas.height / 2 + (y - cy) * zoom]; }
  function draw() {
    if (!open) return;
    const W = canvas.width = canvas.clientWidth * devicePixelRatio, H = canvas.height = canvas.clientHeight * devicePixelRatio;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = '#0b0d12'; ctx.fillRect(0, 0, W, H);
    if (!view || !view.rooms.length) {
      ctx.fillStyle = '#9a8f78'; ctx.font = `${14 * devicePixelRatio}px serif`; ctx.textAlign = 'center';
      ctx.fillText(view ? 'Explore to fill your map.' : 'Unrolling the map…', W / 2, H / 2);
      return;
    }
    const s = Math.max(2, zoom * 0.78);
    for (const r of view.rooms) {
      const [x, y] = toScreen(r.x, r.y);
      if (x < -s || y < -s || x > W + s || y > H + s) continue;
      ctx.fillStyle = view.colors.get(r.zone) || '#777';
      ctx.globalAlpha = hover && hover.vnum === r.vnum ? 1 : 0.78;
      ctx.fillRect(x - s / 2, y - s / 2, s, s);
    }
    ctx.globalAlpha = 1;
    ctx.font = `600 ${12 * devicePixelRatio}px serif`; ctx.textAlign = 'center';
    for (const z of view.zones) {
      if (z.n < 3 && zoom < 8) continue;
      const [x, y] = toScreen(z.x, z.y);
      ctx.fillStyle = 'rgba(0,0,0,.6)'; ctx.fillText(z.name, x + 1, y + 1);
      ctx.fillStyle = '#f3e3b8'; ctx.fillText(z.name, x, y);
    }
    const me = here();
    const meRoom = me && atlas ? atlas.rooms.find(r => r.vnum === me) : null;
    if (meRoom) {
      const [x, y] = toScreen(meRoom.x, meRoom.y);
      ctx.strokeStyle = '#fff'; ctx.lineWidth = 2 * devicePixelRatio;
      ctx.beginPath(); ctx.arc(x, y, Math.max(5, s) * 0.9, 0, Math.PI * 2); ctx.stroke();
    }
    if (hover) {
      const [x, y] = toScreen(hover.x, hover.y);
      ctx.font = `${12 * devicePixelRatio}px sans-serif`; ctx.textAlign = 'left';
      const label = `${hover.name}`;
      const w = ctx.measureText(label).width + 14 * devicePixelRatio;
      ctx.fillStyle = 'rgba(10,8,6,.88)'; ctx.fillRect(x + 10, y - 26 * devicePixelRatio, w, 20 * devicePixelRatio);
      ctx.fillStyle = '#f3e3b8'; ctx.fillText(label, x + 17, y - 12 * devicePixelRatio);
    }
  }
  canvas.addEventListener('pointerdown', e => { drag = { x: e.clientX, y: e.clientY, cx, cy }; canvas.setPointerCapture(e.pointerId); });
  canvas.addEventListener('pointermove', e => {
    if (drag) { cx = drag.cx - (e.clientX - drag.x) * devicePixelRatio / zoom; cy = drag.cy - (e.clientY - drag.y) * devicePixelRatio / zoom; draw(); return; }
    if (!view) return;
    const r = canvas.getBoundingClientRect();
    const wx = cx + ((e.clientX - r.left) * devicePixelRatio - canvas.width / 2) / zoom;
    const wy = cy + ((e.clientY - r.top) * devicePixelRatio - canvas.height / 2) / zoom;
    let best = null, bd = 0.8;
    for (const rm of view.rooms) { const d = Math.hypot(rm.x - wx, rm.y - wy); if (d < bd) { bd = d; best = rm; } }
    if (best !== hover) { hover = best; draw(); }
  });
  canvas.addEventListener('pointerup', () => { drag = null; });
  canvas.addEventListener('wheel', e => { e.preventDefault(); zoom = Math.min(30, Math.max(2, zoom * Math.exp(-e.deltaY * 0.0015))); draw(); }, { passive: false });
  return {
    show(on) { open = on; if (on) { load(); } },
    draw,
  };
}
