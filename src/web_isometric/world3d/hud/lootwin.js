// A corpse's loot window: walk to a corpse and click it, and what it holds opens here (the map
// payload sends a corpse's `contents` and `gold`, map_system.item_info). Take one thing, or all of
// it; each goes out as the MUD's own `get <thing> from <corpse>`, and the window follows the next
// payload (it closes once the corpse is empty or gone).
import { tooltip } from './inventory.js';
import { lootRows } from '../lootlogic.js';

const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const RARITY = { common: '#d8d0c0', uncommon: '#6fd06f', rare: '#5aa8ff', epic: '#c07aff', legendary: '#ffa640', set: '#5fe0c8' };

export function createLootWindow(root, { send, icon, sound, toast }) {
  const body = root.querySelector('.lw-body');
  const tip = document.getElementById('item-tip');
  let open = false, cur = null, busy = false;   // cur: {key, kw, item}
  root.querySelector('.lw-close').addEventListener('click', () => toggle(false));
  root.querySelector('.lw-all').addEventListener('click', () => take(`get all from ${cur ? cur.kw : 'corpse'}`));

  function take(cmd) {
    if (busy || !cur) return;
    busy = true;
    send(cmd);
    if (sound) sound.play(/gold/.test(cmd) ? 'coins' : 'leather');
    setTimeout(() => { busy = false; }, 300);
  }
  function place(e) {
    tip.style.left = `${Math.min(e.clientX + 16, innerWidth - 260)}px`;
    tip.style.top = `${Math.min(e.clientY + 12, innerHeight - tip.offsetHeight - 10)}px`;
  }
  function render() {
    if (!open || !cur) return;
    root.querySelector('.lw-who').textContent = String(cur.item.short || cur.item.name || 'Corpse').replace(/^the /, '').replace(/^./, c => c.toUpperCase());
    const rows = lootRows(cur.item, cur.kw);
    if (!rows.length) { body.innerHTML = '<span class="ch-none">Nothing left</span>'; return; }
    body.innerHTML = `<div class="sb-list lw-list">${rows.map((r, i) => {
      if (r.gold) return `<div class="sh-row lw-row" data-i="${i}"><div class="sh-ic lw-gold">◉</div>
        <div class="sb-main"><div class="sb-name" style="color:var(--gold-hi)">${r.gold.toLocaleString()} gold</div></div>
        <button class="tr-buy" data-i="${i}">Take</button></div>`;
      const it = r.item, rr = it.set_id ? 'set' : (it.rarity || 'common');
      return `<div class="sh-row lw-row" data-i="${i}"><div class="sh-ic" style="box-shadow:0 0 0 1px #000,0 0 0 2px ${RARITY[rr] || RARITY.common}"></div>
        <div class="sb-main"><div class="sb-name" style="color:${RARITY[rr] || RARITY.common}">${esc(it.short || it.name)}</div>
          <div class="sb-cost">${it.level ? `level ${it.level} · ` : ''}${esc(it.type || '')}${it.slot ? ` · ${esc(String(it.slot).replace(/\d$/, ''))}` : ''}</div></div>
        <button class="tr-buy" data-i="${i}">Take</button></div>`;
    }).join('')}</div>`;
    body.querySelectorAll('.lw-row').forEach(el => {
      const r = rows[+el.dataset.i];
      if (!r.item) return;
      el.querySelector('.sh-ic').appendChild(icon(r.item));
      el.addEventListener('mouseenter', e => { tip.innerHTML = tooltip(r.item); tip.classList.remove('hidden'); place(e); });
      el.addEventListener('mousemove', place);
      el.addEventListener('mouseleave', () => tip.classList.add('hidden'));
      el.addEventListener('dblclick', () => take(r.cmd));
    });
    body.querySelectorAll('.tr-buy').forEach(b => b.addEventListener('click', () => take(rows[+b.dataset.i].cmd)));
  }
  // open on a corpse ({key, kw, item} from lootlogic.groundItems)
  function show(g) {
    const rows = lootRows(g.item, g.kw);
    if (!rows.length) { if (toast) toast('The corpse is empty'); return; }
    cur = g;
    toggle(true);
  }
  // the next payload: the same corpse as it is now (null: gone)
  function follow(g) {
    if (!open) return;
    if (!g || !lootRows(g.item, g.kw).length) { toggle(false); return; }
    const was = JSON.stringify(cur && cur.item);
    cur = g;
    if (JSON.stringify(g.item) !== was) render();
  }
  function toggle(on = !open) {
    open = on;
    root.classList.toggle('hidden', !open);
    if (tip) tip.classList.add('hidden');
    if (open) render(); else cur = null;
  }
  return { show, follow, toggle, get open() { return open; }, get key() { return cur ? cur.key : null; } };
}
