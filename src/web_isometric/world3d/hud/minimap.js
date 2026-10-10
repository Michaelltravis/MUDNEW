// Minimap from the zone map: every room as a tile in its cell, the rooms you have explored
// brighter, shared openings as bridges, passages as dots, the hero as an arrow. Click a
// room to walk there (main.js plans the route through open exits and stairs).
const SECTOR = {
  inside: '#8a8a96', dungeon: '#6f6a78', cave: '#6a6052', city: '#c7ab7c', forest: '#4f8a46', field: '#86a85a',
  hills: '#7e9a5c', mountain: '#8a857a', desert: '#d6bd86', swamp: '#56664a', water_swim: '#3f7fb0',
  water_noswim: '#2f66a0', underwater: '#2a5a8a', flying: '#a8c8e8', default: '#7d8a70',
};
const CW = 22, CH = 14;      // css px per cell (keeps the 24:15 room shape)

export function createMinimap(root, onPick, onNorth = null) {
  const cv = root.querySelector('canvas');
  const ctx = cv.getContext('2d');
  const S = 2;   // the canvas is drawn at twice its CSS size (it is hidden at creation, so not measured)
  let zone = null, explored = new Set(), hero = { x: 0, z: 0, yaw: 0, cam: 0 }, room = null, dirty = true, last = 0;
  let guild = null;            // {vnum, room, trainer}: where your class's trainer stands
  let questMark = null;        // the room your marquee quest sends you to (a gold diamond)
  const north = root.querySelector('.mm-north');
  if (north) north.addEventListener('click', e => { e.stopPropagation(); if (onNorth) onNorth(); });
  const W = () => cv.width, H = () => cv.height;

  function toScreen(cx, cy) {
    return [(cx - hero.x / 24) * CW * S + W() / 2, (cy - hero.z / 15) * CH * S + H() / 2];
  }
  function draw() {
    ctx.clearRect(0, 0, W(), H());
    if (!zone) return;
    const cw = CW * S, ch = CH * S, pad = 2.2 * S;
    for (const r of zone.rooms.values()) {
      const [x, y] = toScreen(r.cx, r.cy);
      if (x < -cw || y < -ch || x > W() + cw || y > H() + ch) continue;
      const seen = explored.has(r.vnum) || r === room;
      ctx.globalAlpha = seen ? 0.95 : 0.32;
      ctx.fillStyle = SECTOR[r.data.sector] || SECTOR.default;
      ctx.beginPath(); ctx.roundRect(x + pad, y + pad, cw - pad * 2, ch - pad * 2, 3 * S); ctx.fill();
      // openings: little bridges across the shared edge; passages: dots on the edge
      for (const [d, e] of Object.entries(r.data.exits)) {
        if (d === 'east' && e.kind === 'open') { ctx.fillRect(x + cw - pad - 1, y + ch / 2 - 2 * S, pad * 2 + 2, 4 * S); continue; }
        if (d === 'south' && e.kind === 'open') { ctx.fillRect(x + cw / 2 - 2 * S, y + ch - pad - 1, 4 * S, pad * 2 + 2); continue; }
        if (e.kind === 'open' || !seen) continue;
        ctx.fillStyle = e.kind === 'zone' ? '#ffd27a' : '#bfe0ff';
        if (d === 'up' || d === 'down') {
          // stairs: ▲ on the right of the room, ▼ on the left (where they stand in the room)
          const px = d === 'up' ? x + cw * 0.7 : x + cw * 0.3, py = y + ch / 2, s = 3.2 * S;
          ctx.beginPath();
          if (d === 'up') { ctx.moveTo(px, py - s); ctx.lineTo(px + s, py + s * 0.8); ctx.lineTo(px - s, py + s * 0.8); }
          else { ctx.moveTo(px, py + s); ctx.lineTo(px + s, py - s * 0.8); ctx.lineTo(px - s, py - s * 0.8); }
          ctx.closePath(); ctx.fill();
          ctx.strokeStyle = 'rgba(0,0,0,.6)'; ctx.lineWidth = 0.8 * S; ctx.stroke();
        } else {
          const px = d === 'east' ? x + cw - pad : d === 'west' ? x + pad : x + cw / 2;
          const py = d === 'north' ? y + pad : d === 'south' ? y + ch - pad : y + ch / 2;
          ctx.beginPath(); ctx.arc(px, py, 2.2 * S, 0, Math.PI * 2); ctx.fill();
        }
        ctx.fillStyle = SECTOR[r.data.sector] || SECTOR.default;
      }
    }
    ctx.globalAlpha = 1;
    // your guild's trainer: a gold star
    const gr = guild && zone.rooms.get(guild.vnum);
    if (gr) {
      const [x, y] = toScreen(gr.cx, gr.cy);
      ctx.font = `${11 * S}px sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.lineWidth = 2.4 * S; ctx.strokeStyle = 'rgba(0,0,0,.75)'; ctx.fillStyle = '#ffd86a';
      ctx.strokeText('★', x + cw / 2, y + ch / 2); ctx.fillText('★', x + cw / 2, y + ch / 2);
    }
    // the marquee quest's next place: a gold diamond
    const qr = questMark != null && zone.rooms.get(questMark);
    if (qr) {
      const [x, y] = toScreen(qr.cx, qr.cy);
      ctx.font = `bold ${12 * S}px sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.lineWidth = 2.6 * S; ctx.strokeStyle = 'rgba(0,0,0,.8)'; ctx.fillStyle = '#ffb84a';
      ctx.strokeText('◆', x + cw / 2, y + ch / 2); ctx.fillText('◆', x + cw / 2, y + ch / 2);
    }
    if (room) {
      const [x, y] = toScreen(room.cx, room.cy);
      ctx.strokeStyle = '#f3d999'; ctx.lineWidth = 1.6 * S;
      ctx.beginPath(); ctx.roundRect(x + pad, y + pad, cw - pad * 2, ch - pad * 2, 3 * S); ctx.stroke();
    }
    // where the camera looks: a soft wedge from the hero (the map itself stays north up)
    ctx.save();
    ctx.translate(W() / 2, H() / 2);
    ctx.rotate(-hero.cam);                       // yaw 0 looks north (up the map)
    const g = ctx.createRadialGradient(0, 0, 0, 0, 0, 34 * S);
    g.addColorStop(0, 'rgba(243,217,153,.38)'); g.addColorStop(1, 'rgba(243,217,153,0)');
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.moveTo(0, 0); ctx.arc(0, 0, 34 * S, -Math.PI / 2 - 0.55, -Math.PI / 2 + 0.55); ctx.closePath(); ctx.fill();
    ctx.restore();
    // the hero: an arrow pointing the way they face
    ctx.save();
    ctx.translate(W() / 2, H() / 2);
    ctx.rotate(-hero.yaw + Math.PI);
    ctx.fillStyle = '#fff'; ctx.strokeStyle = '#000'; ctx.lineWidth = 1 * S;
    ctx.beginPath(); ctx.moveTo(0, -5 * S); ctx.lineTo(3.6 * S, 4 * S); ctx.lineTo(0, 2 * S); ctx.lineTo(-3.6 * S, 4 * S); ctx.closePath();
    ctx.fill(); ctx.stroke();
    ctx.restore();
  }

  cv.addEventListener('click', e => {
    if (!zone) return;
    const r = cv.getBoundingClientRect();
    const sx = (e.clientX - r.left) * S, sy = (e.clientY - r.top) * S;
    const cx = Math.floor((sx - W() / 2) / (CW * S) + hero.x / 24);
    const cy = Math.floor((sy - H() / 2) / (CH * S) + hero.z / 15);
    const target = zone.cells.get(`${cx},${cy}`);
    if (target) onPick(target);
  });

  return {
    setZone(z) {
      zone = z; dirty = true;
      root.querySelector('.mm-zone').textContent = z ? z.name : '';
    },
    setExplored(list) { explored = new Set(list); dirty = true; },
    setGuild(g) {
      const v = g && g.vnum;
      if (v === (guild && guild.vnum)) return;
      guild = g || null; dirty = true;
      cv.title = g ? `★ ${g.trainer} (${g.room}) trains you` : '';
    },
    setQuestMark(vnum) { if (vnum === questMark) return; questMark = vnum; dirty = true; },
    setRoom(r) { room = r; dirty = true; root.querySelector('.mm-room').textContent = r ? r.name : ''; },
    setTime(t) {
      if (!t) return;
      const h = t.hour != null ? t.hour : null;
      root.querySelector('.mm-time').textContent = h == null ? '' : `${String(h).padStart(2, '0')}:00${t.period ? ' · ' + t.period : ''}`;
    },
    // camYaw: the camera's turn (0 = north up); the compass needle and the view wedge follow it
    update(pos, yaw, camYaw = 0) {
      if (Math.abs(pos.x - hero.x) > 0.05 || Math.abs(pos.z - hero.z) > 0.05 || Math.abs(yaw - hero.yaw) > 0.05
        || Math.abs(camYaw - hero.cam) > 0.02) dirty = true;
      if (north && Math.abs(camYaw - hero.cam) > 0.002) {
        north.firstElementChild.style.transform = `rotate(${camYaw}rad)`;
        const turned = Math.abs(Math.atan2(Math.sin(camYaw), Math.cos(camYaw))) > 0.05;
        north.classList.toggle('turned', turned);
      }
      hero = { x: pos.x, z: pos.z, yaw, cam: camYaw };
      const now = performance.now();
      if (dirty && now - last > 80) { draw(); dirty = false; last = now; }
    },
  };
}
